import time
import displayio
import gc
from train_predictor import Direction

# xxx add a splash screen that displays at startup. Display name of board. and
# version.
#
# might be difficult due to the way I am initialling board. I'll have to make
# sure I make it so it only shows the splash screen before we to init.

ARRIVAL_TIMES_FONT='fonts/6x10.bdf'
ERROR_FONT='fonts/4x6.bdf'

class DisplayMode:
    ARRIVAL_TIMES = 1
    TRAIN = 2
    ERROR = 3

# xxx doc
class DisplayDependencies:
    def __init__(self,  matrix_portal, time_conversion, logger):
        self.matrix_portal = matrix_portal
        self.time_conversion = time_conversion
        self.logger = logger

# xxx doc
# xxx test

class Display:
    def __init__(self, dependencies : DisplayDependencies, text_scroll_delay, train_frame_duration):
        self._matrix_portal = dependencies.matrix_portal
        self._time_conversion = dependencies.time_conversion
        self._logger = dependencies.logger

        self._mode = None
        self._text_scroll_delay = text_scroll_delay
        self._train_frame_duration = train_frame_duration
        
        self._arrival_time_indices = None

        # xxx doc important we init train after arrival times so it shows up on top
        self._initialize_arrival_times()
        self._initialize_train()
        gc.collect()
    def _set_mode(self, mode):
        if mode == DisplayMode.ARRIVAL_TIMES:
            self._tLogo.hidden = False
            self._train_sprite_group.hidden = True
        if mode == DisplayMode.TRAIN:
            self._tLogo.hidden = True
            self._train_sprite_group.hidden = False
        if mode == DisplayMode.ERROR:
            self._tLogo.hidden = True
            self._train_sprite_group.hidden = True
        self._mode = mode

    def render_arrival_times(self, trains):
        self._logger.debug("rendering arrival times")
        self._set_mode(DisplayMode.ARRIVAL_TIMES)

        assert(len(trains)== 3, "expecting three train objects to be provided to render_arrival_times")

        times = [self._format_train_time(t) for t in trains]

        self._matrix_portal.set_text(times[0], self._arrival_time_indices[0])
        self._matrix_portal.set_text(times[1], self._arrival_time_indices[1])
        self._matrix_portal.set_text(times[2], self._arrival_time_indices[2])

    def _format_train_time(self, train):
        if train is None:
            return ""
        return self._time_conversion.relative_time_from_now(train.time)

    def _initialize_arrival_times(self):
        self._logger.debug("initializing arrival times")
        self._matrix_portal.add_text( text_font=ARRIVAL_TIMES_FONT, text_position=(15, 3), text="Children's Museum of Franklin", is_data=False, scrolling=True)
        
        self._arrival_time_indices = [
            self._matrix_portal.add_text( text_font=ARRIVAL_TIMES_FONT, text_position=(16, 11), text="?min", is_data=False),
            self._matrix_portal.add_text( text_font=ARRIVAL_TIMES_FONT, text_position=(16, 19), text="?min", is_data=False),
            self._matrix_portal.add_text( text_font=ARRIVAL_TIMES_FONT, text_position=(16, 27), text="?min", is_data=False),
        ]

        # When we add the tLogo on the left side of the screen we want the
        # scrolling "Children's Museum of Franklin" to scroll UNDER the T
        # instead of on top of it. With displayio items added to a group last
        # stack on TOP of other layers. So we need to add the tLogo AFTER the
        # text so it stacks on top of the text. We also set the third color
        # palette color as transparent so the text can scroll partly on top of
        # the logo.
        tLogo = displayio.OnDiskBitmap('/background.bmp')
        palette = tLogo.pixel_shader
        palette.make_transparent(3)
        self._tLogo = displayio.TileGrid(
                tLogo,
                pixel_shader=palette,
            )
        self._matrix_portal.display.root_group.append(self._tLogo)

        self._mode = DisplayMode.ARRIVAL_TIMES
        gc.collect()

    def scroll_text(self):
        self._matrix_portal.scroll_text(self._text_scroll_delay)
    
    def _initialize_train(self):
        self._logger.debug("initializing train")
        WIDTH=64
        HEIGHT=32

        bitmap = displayio.OnDiskBitmap('/train.bmp')
        self._train_sprite = displayio.TileGrid(
            bitmap,
            pixel_shader=bitmap.pixel_shader,
            tile_width=WIDTH,
            tile_height=HEIGHT,
        )

        self._train_sprite_group = displayio.Group()
        self._train_sprite_group.append(self._train_sprite)
        self._matrix_portal.display.root_group.append(self._train_sprite_group)

        self._train_frame_count = int(bitmap.height / HEIGHT)

    def render_train(self, direction):
        self._logger.debug("rendering train")
        self._set_mode(DisplayMode.TRAIN)

        # The train animation is setup for an outbound train by default. So if
        # we want to render an inbound train we need to flip the sprite
        if (direction == Direction.IN_BOUND):
            self._train_sprite.flip_x = True

        current_frame = 0
        while True:
            time.sleep(self._train_frame_duration)
            current_frame = current_frame + 1
            if current_frame >= self._train_frame_count:
                return

            # Advance to the next frame by using __setitem__ on the
            # sprite_group.
            self._train_sprite_group[0][0] = current_frame

    def render_error(self):
        self._set_mode(DisplayMode.ERROR)
        self._matrix_portal.remove_all_text()
        self._matrix_portal.add_text(text_font=ERROR_FONT, text_position=(1, 15), text_wrap=17, text="ERROR Restarting in 1min. Contact Andrew.B.Nitschke@gmail.com")
