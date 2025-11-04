import time
import displayio
import gc
from adafruit_matrixportal.matrixportal import MatrixPortal
from adafruit_matrixportal.matrix import Matrix

# xxx remove this file once I get it so you can play the train on demand

# xxx code for the board that all it does is play an animation from the
# train.bmp sprite sheet of a train going by in order to try out that animation
# to see how it looks on the board.

# xxx doc At one point in time I had the train engine, three box cars, and a
# caboose. This was having issues playing the full animation on the board. Some
# of the initial frames of the animation just wouldn't play. Not sure why, I
# reduced it down to only two box cars and that seemed to fix the issue. So my
# guess is that I might have been running out of RAM and as a result some of the
# initial frames for the box car were getting overwritten or something.
# 
# So for now we can only have the train engine, two box cars, and a caboose. If
# we really wanted more cars I could probably do it by trying to save on memory
# by just loading a minimal 16 frame smokeSpriteSrc.bmp sprite sheet and a still
# image of the train and then animate them by cycling the sprite sheet and
# translating the images across the screen. I would prefer to avoid that though
# since it is more complicated code that needs to be running on the board and
# prefer the simpler approach of just playing the full sprite sheet.


WIDTH=64
HEIGHT=32
FRAME_DURATION = 0.1

matrix = Matrix(bit_depth=4)
sprite_group = displayio.Group()
matrix.display.root_group = sprite_group

bitmap = displayio.OnDiskBitmap('/train.bmp')
sprite = displayio.TileGrid(
    bitmap,
    pixel_shader=bitmap.pixel_shader,
    tile_width=WIDTH,
    tile_height=HEIGHT,
)
sprite.flip_x = True

sprite_group.append(sprite)

frame_count = int(bitmap.height / HEIGHT)

current_frame = 0

while True:
    time.sleep(FRAME_DURATION)
    current_frame = current_frame + 1
    if current_frame >= frame_count:
        current_frame = 0
    sprite_group[0][0] = current_frame