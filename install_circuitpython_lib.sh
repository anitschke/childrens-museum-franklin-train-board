#!/bin/bash -e

BUNDLE_VERSION="20251008"
DEST="/run/media/anitschk/CIRCUITPY"

ZIP_BASE_NAME="adafruit-circuitpython-bundle-10.x-mpy-$BUNDLE_VERSION"
ZIP_URL="https://github.com/adafruit/Adafruit_CircuitPython_Bundle/releases/download/$BUNDLE_VERSION/$ZIP_BASE_NAME.zip"
TEMP_DIR="/tmp/circuitpython_bundle"

mkdir -p "$TEMP_DIR"

rm -f "$TEMP_DIR/bundle.zip"
rm -rf "$TEMP_DIR/$ZIP_BASE_NAME"
curl -L "$ZIP_URL" -o "$TEMP_DIR/bundle.zip"
unzip -q "$TEMP_DIR/bundle.zip" -d "$TEMP_DIR"

# Build a single case-insensitive regex from requirements.txt
REQ_REGEX="$(cat requirements.txt | sed -E 's/(.*)/.*\/\1.mpy|.*\/\1/' | paste -sd'|' -)"

# Delete top-level lib entries that do NOT match the regex
find "$TEMP_DIR/$ZIP_BASE_NAME/lib" -maxdepth 1 -mindepth 1 \
    -regextype posix-extended \
    ! -iregex "$REQ_REGEX" \
    -exec rm -rf {} +

rsync -avu --delete "$TEMP_DIR/$ZIP_BASE_NAME/lib" "$DEST"