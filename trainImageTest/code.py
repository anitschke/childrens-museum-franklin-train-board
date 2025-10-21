import time
import displayio
import gc
from adafruit_matrixportal.matrixportal import MatrixPortal
from adafruit_matrixportal.matrix import Matrix

# xxx code for the board that all it does is play an animation from the
# train.bmp sprite sheet of a train going by in order to try out that animation
# to see how it looks on the board.


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

sprite_group.append(sprite)

frame_count = int(bitmap.height / HEIGHT)

current_frame = 0

while True:
    time.sleep(FRAME_DURATION)
    current_frame = current_frame + 1
    if current_frame >= frame_count:
        current_frame = 0
    sprite_group[0][0] = current_frame