import time
import displayio
import gc
from train_predictor import Direction


ARRIVAL_TIMES_FONT='fonts/6x10.bdf'

class DisplayMode:
    ARRIVAL_TIMES = 1
    TRAIN = 2

# xxx doc
class DisplayDependencies:
    def __init__(self,  matrix_portal, time_conversion):
        self.matrix_portal = matrix_portal
        self.time_conversion = time_conversion

# xxx doc
# xxx test

class Display:
    def __init__(self, dependencies : DisplayDependencies, text_scroll_delay, train_frame_duration):
        self._matrix_portal = dependencies.matrix_portal
        self._time_conversion = dependencies.time_conversion

        self._mode = None
        self._text_scroll_delay = text_scroll_delay
        self._train_frame_duration = train_frame_duration
        
        self._arrival_time_indices = None
    
    def render_arrival_times(self, trains):
        assert(len(trains)== 3, "expecting three train objects to be provided to render_arrival_times")

        if self._mode != DisplayMode.ARRIVAL_TIMES:
            self._initialize_arrival_times()

        times = [self._format_train_time(t) for t in trains]

        self._matrix_portal.set_text(times[0], self._arrival_time_indices[0])
        self._matrix_portal.set_text(times[1], self._arrival_time_indices[1])
        self._matrix_portal.set_text(times[2], self._arrival_time_indices[2])

    def _format_train_time(self, train):
        if train is None:
            return ""
        return self._time_conversion.relative_time_from_now(train.time)


    def _initialize_arrival_times(self):
        self._matrix_portal.remove_all_text()

        self._matrix_portal.set_background('/background.bmp')
        self._matrix_portal.add_text( text_font=ARRIVAL_TIMES_FONT, text_position=(15, 3), text="Children's Museum of Franklin", is_data=False, scrolling=True)
        
        self._arrival_time_indices = [
            self._matrix_portal.add_text( text_font=ARRIVAL_TIMES_FONT, text_position=(16, 11), text="?min", is_data=False),
            self._matrix_portal.add_text( text_font=ARRIVAL_TIMES_FONT, text_position=(16, 19), text="?min", is_data=False),
            self._matrix_portal.add_text( text_font=ARRIVAL_TIMES_FONT, text_position=(16, 27), text="?min", is_data=False),
        ]
        self._mode = DisplayMode.ARRIVAL_TIMES

    def scroll_text(self):
        self._matrix_portal.scroll_text(self._text_scroll_delay)

    def render_train(self, direction):
        self._mode = DisplayMode.TRAIN
        self._render_train(direction)

        # After we have rendered the train replace the root group to make sure
        # we remove any existing train animation and then run the GC to free up
        # all the memory from the animation.
        self._matrix_portal.display.root_group = displayio.Group()
        gc.collect()
    
    def _render_train(self, direction):
        self._matrix_portal.remove_all_text()

        # Now that wae have removed all text replace the root group to make sure
        # there is nothing else being displayed.
        sprite_group = displayio.Group()
        self._matrix_portal.display.root_group = sprite_group
        gc.collect()

        WIDTH=64
        HEIGHT=32

        bitmap = displayio.OnDiskBitmap('/train.bmp')
        sprite = displayio.TileGrid(
            bitmap,
            pixel_shader=bitmap.pixel_shader,
            tile_width=WIDTH,
            tile_height=HEIGHT,
        )

        # The train animation is setup for an outbound train by default. So if
        # we want to render an inbound train we need to flip the sprite
        if (direction == Direction.IN_BOUND):
            sprite.flip_x = True

        sprite_group.append(sprite)

        frame_count = int(bitmap.height / HEIGHT)
        current_frame = 0
        while True:
            time.sleep(self._train_frame_duration)
            current_frame = current_frame + 1
            if current_frame >= frame_count:
                return

            # Advance to the next frame by using __setitem__ on the
            # sprite_group.
            sprite_group[0][0] = current_frame