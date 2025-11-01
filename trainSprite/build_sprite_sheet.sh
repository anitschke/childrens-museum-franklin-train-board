#!/bin/bash

# Generates a vertical sprite sheet where each frame is a 64x32 crop
# of the train image shifted one pixel at a time, with animated smoke.

INPUT="trainSrc.bmp"
SMOKE_SPRITE_SHEET="smokeSpriteSrc.bmp"
OUTPUT="../train.bmp"
GIF_OUTPUT="train.gif"
GIF_OUTPUT_SCALED="trainScaled.gif"
WIDTH=64
HEIGHT=32

# --- SMOKE CONFIGURATION ---
SMOKE_FRAME_HEIGHT=$HEIGHT   # Assume smoke frames are 32px high
# ---------------------------

# Get source width
IMG_WIDTH=$(identify -format "%w" "$INPUT")

# Create padded version (black on both sides) of the train
PADDED_WIDTH=$((IMG_WIDTH + 2 * WIDTH))
TMPDIR=$(mktemp -d)
PADDED="$TMPDIR/padded.bmp"

echo "Creating padded image (${PADDED_WIDTH}px wide)..."
magick -size ${PADDED_WIDTH}x${HEIGHT} xc:black \
    "$INPUT" -geometry +${WIDTH}+0 -composite "$PADDED"

# --- Extract Smoke Frames and Count ---
echo "Extracting smoke frames..."
# Get total height of the smoke sheet
SMOKE_SHEET_HEIGHT=$(identify -format "%h" "$SMOKE_SPRITE_SHEET")
SMOKE_FRAME_WIDTH=$(identify -format "%w" "$SMOKE_SPRITE_SHEET")
# Calculate number of frames in the smoke sheet
NUM_SMOKE_FRAMES=$((SMOKE_SHEET_HEIGHT / SMOKE_FRAME_HEIGHT))
echo "Found $NUM_SMOKE_FRAMES smoke frames."

# Extract and save each smoke frame temporarily
for ((s=0; s<NUM_SMOKE_FRAMES; s++)); do
    SMOKE_FRAME_NAME=$(printf "smoke_%04d.png" "$s")
    # Crop each smoke frame and save as PNG (which supports transparency)
    magick "$SMOKE_SPRITE_SHEET" -crop "${SMOKE_FRAME_WIDTH}x${SMOKE_FRAME_HEIGHT}+0+$((s * SMOKE_FRAME_HEIGHT))" +repage "$TMPDIR/$SMOKE_FRAME_NAME"
done
# -------------------------------------

# Compute frame count (train fully slides across view)
NUM_FRAMES=$((PADDED_WIDTH - WIDTH + 1))
echo "Generating $NUM_FRAMES frames..."

for ((i=0; i<NUM_FRAMES; i++)); do
  FRAME=$(printf "%04d.bmp" "$i")
  CURRENT_TRAIN_FRAME="$TMPDIR/train_$FRAME" # Temporary train frame
  FINAL_FRAME="$TMPDIR/$FRAME"              # Final frame with smoke

  # 1. Generate the base train frame
  magick "$PADDED" -crop "${WIDTH}x${HEIGHT}+$i+0" +repage "$CURRENT_TRAIN_FRAME"

  # 2. Determine which smoke frame to use (loops the smoke animation)
  SMOKE_FRAME_INDEX=$((i % NUM_SMOKE_FRAMES))
  SMOKE_FRAME_NAME=$(printf "smoke_%04d.png" "$SMOKE_FRAME_INDEX")
  CURRENT_SMOKE_FRAME="$TMPDIR/$SMOKE_FRAME_NAME"

  # 3. Composite the smoke onto the train frame
  # We use black (or 'null') as the color to avoid replacing, but since ImageMagick
  # composite operations don't have a direct "don't replace black" mode,
  # the most common method for this kind of "don't overwrite" transparency is:
  # a. Set the smoke image's black pixels to be transparent (via -transparent black).
  # b. Composite the now-transparent smoke frame onto the train frame.

  # The smoke sprite sheet is setup relative to the train. So we need to offset
  # the smoke by the frame number since we are moving the train by the initial
  # offset of the frame width minus one pixel per frame
  SMOKE_OFFSET_X=$(($WIDTH-$i))

  magick "$CURRENT_TRAIN_FRAME" \
      "$CURRENT_SMOKE_FRAME" -transparent black \
      -geometry +${SMOKE_OFFSET_X}+0 \
      -composite "$FINAL_FRAME"

    # remove the temporary frame
    rm "$CURRENT_TRAIN_FRAME"
done

# Finally add one final black frame at the very end to make sure we don't have
# any lingering smoke left over
FINAL_BLACK_FRAME="$TMPDIR/zzz_final_black.bmp"
magick -size ${WIDTH}x${HEIGHT} xc:black "$FINAL_BLACK_FRAME"

echo "Deleting padded version before building the final sprite sheet"
rm "$PADDED"

# xxx There is something in here that we should be able to do to produce a
# smaller image size. If I just open the generated .bmp in GIMP and then resave
# it then I get something about half the size. So need to look into what other
# options I have to make it smaller since we are starting to get close to
# filling up the flash memory on the board.

# xxx doc
echo "Stacking frames vertically into $OUTPUT..."
magick convert -type Palette -append "$TMPDIR"/*.bmp "$TMPDIR"/train_full_color.bmp
magick convert "$TMPDIR"/train_full_color.bmp  -colors 16 "$OUTPUT"
rm "$TMPDIR"/train_full_color.bmp

echo "Stacking frames vertically into $GIF_OUTPUT..."
magick -delay 5 -loop 0 -dispose Background -background black "$TMPDIR"/*.bmp "$GIF_OUTPUT"

echo "Stacking frames vertically into $GIF_OUTPUT_SCALED..."
magick -delay 5 -loop 0 -dispose Background -background black "$TMPDIR"/*.bmp -filter point -scale $((WIDTH * 8))x$((HEIGHT * 8)) "$GIF_OUTPUT_SCALED"

# Clean up
rm -rf "$TMPDIR"
echo "Done! Sprite sheet saved to $OUTPUT"