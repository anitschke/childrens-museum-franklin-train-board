#!/bin/bash

#xxx doc

# Generates a vertical sprite sheet where each frame is a 64x32 crop
# of the train image shifted one pixel at a time.
# Adds black padding before and after so the train starts and ends offscreen.

INPUT="trainSrc.bmp"
OUTPUT="train.bmp"
WIDTH=64
HEIGHT=32

# Get source width
IMG_WIDTH=$(identify -format "%w" "$INPUT")

# Create padded version (black on both sides) of the train so it looks like it
# will appear and disappear fully.
PADDED_WIDTH=$((IMG_WIDTH + 2 * WIDTH))
TMPDIR=$(mktemp -d)
PADDED="$TMPDIR/padded.bmp"

echo "Creating padded image (${PADDED_WIDTH}px wide)..."
convert -size ${PADDED_WIDTH}x${HEIGHT} xc:black \
    "$INPUT" -geometry +${WIDTH}+0 -composite "$PADDED"

# Compute frame count (train fully slides across view)
NUM_FRAMES=$((PADDED_WIDTH - WIDTH + 1))
echo "Generating $NUM_FRAMES frames..."

for ((i=0; i<NUM_FRAMES; i++)); do
  FRAME=$(printf "%04d.bmp" "$i")
  convert "$PADDED" -crop "${WIDTH}x${HEIGHT}+$i+0" +repage "$TMPDIR/$FRAME"
done

echo "deleting padded version before building the final sprite sheet"
rm "$PADDED"

echo "Stacking frames vertically into $OUTPUT..."
convert -append "$TMPDIR"/*.bmp "$OUTPUT"

# Clean up
rm -rf "$TMPDIR"
echo "Done! Sprite sheet saved to $OUTPUT"
