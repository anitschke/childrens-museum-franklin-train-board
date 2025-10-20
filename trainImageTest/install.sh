#!/bin/bash

CWD=$(dirname -- "$0")
SCRIPT_DIR=$(dirname -- "$0")

TARGET=/run/media/anitschk/CIRCUITPY

cp $SCRIPT_DIR/code.py $TARGET
cp $SCRIPT_DIR/train.bmp $TARGET
