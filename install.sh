#!/bin/bash

CWD=$(dirname -- "$0")
SCRIPT_DIR=$(dirname -- "$0")

TARGET=/run/media/anitschk/CIRCUITPY

if [ ! -f "$SCRIPT_DIR/settings.toml" ]; then
  echo "Error: File '$SCRIPT_DIR/settings.toml' not found." >&2
  echo "This file is ignored by .gitignore because it contains secrets." >&2
  echo "It must be recreated in the root directory of the project before running the install.sh script." >&2
  echo "See README.md settings.toml section." >&2
  exit 1
fi

# Circuit python ships with a hello world code.py, but we use a main.py to work
# around some issues (See notes in README.md). So remove code.py if it exists.
rm -f $TARGET/code.py

# For some reason that I do not understand using rsync to try to copy files
# across to the device results in "[Errno 5] Input/output error" on the device.
# I really don't know why. So we will just live with doing a cp for every file.
# 
# I did some digging online and the best I can figure out is that rsync changes
# too many files too quickly and the board usb drive emulation software can't
# keep up and it results in IO errors. I did a little more digging and it looks
# like it actually has to do with how rsync copies over temporary files. If I
# add the --inplace flag it seems to fix this issue.
rsync -av --inplace \
    $SCRIPT_DIR/README.md  \
    \
    $SCRIPT_DIR/application.py  \
    $SCRIPT_DIR/collections_extra.py  \
    $SCRIPT_DIR/display.py  \
    $SCRIPT_DIR/main.py  \
    $SCRIPT_DIR/time_conversion.py  \
    $SCRIPT_DIR/train_predictor.py  \
    $SCRIPT_DIR/logging_extra.py  \
    \
    $SCRIPT_DIR/background.bmp  \
    $SCRIPT_DIR/train.bmp  \
    \
    $SCRIPT_DIR/fonts \
    \
    $SCRIPT_DIR/settings.toml \
    \
    \
    \
    $TARGET
