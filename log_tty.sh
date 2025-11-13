#!/bin/bash

LOG_FILE="tty.log"
MAX_LINES_CHECK_SIZE=10000
MAX_LINES_TRIM_SIZE=9000

stdbuf -oL cat /dev/ttyACM0 | while IFS= read -r line; do
    echo "$line" >> "$LOG_FILE"

    # Count lines and trim if necessary
    CURRENT_LINES=$(wc -l < "$LOG_FILE")
    if (( CURRENT_LINES > MAX_LINES_CHECK_SIZE )); then
        tail -n "$MAX_LINES_TRIM_SIZE" "$LOG_FILE" > "$LOG_FILE.tmp" && mv "$LOG_FILE.tmp" "$LOG_FILE"
    fi
done < /dev/ttyACM0  # Or wherever your TTY output is coming from
