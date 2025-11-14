#!/bin/bash

START_FILE="starting_requirements.txt"
OUT_FILE="requirements.txt"
TMP_DIR="$(mktemp -d)"
QUEUE="$TMP_DIR/queue.txt"
SEEN="$TMP_DIR/seen.txt"

# Normalize starting list
grep -v '^\s*#' "$START_FILE" | grep -v '^\s*$' > "$QUEUE"
> "$SEEN"

process_dep() {
    local dep="$1"
    echo "Processing $dep"

    # Fetch its requirements.txt
    url="https://raw.githubusercontent.com/adafruit/${nover}/refs/heads/main/requirements.txt"
    req_file="$TMP_DIR/${dep}.txt"

    if curl -s -f "$url" -o "$req_file"; then
        # Filter out comments/blanks
        new_deps=$(grep -v '^\s*#' "$req_file" | grep -v '^\s*$')
        for nd in $new_deps; do
                echo "$nd" >> "$QUEUE"
        done
    else
        echo "WARNING: Could not fetch requirements for $dep" >&2
    fi
}

# BFS-style processing of dependency graph
while read -r dep; do

    # Ignore "." dependencies
    if [[ "$dep" == "." ]]; then
        continue
    fi

    # replace "-" with "_" so we can fetch data from the github repo
    underscore_dep="${dep//-/_}"

    # remove any version information
    nover=$(echo "$underscore_dep" | sed 's/[<>=!~].*$//')

    # normalize to lowercase
    lower_dep="${nover,,}"

    norm_dep="$lower_dep"

    # If already processed, skip
    if grep -qx "$norm_dep" "$SEEN"; then
        continue
    fi

    echo "$norm_dep" >> "$SEEN"
    process_dep "$norm_dep"

done < "$QUEUE"

# Save final list
sort -u "$SEEN" | sed -E 's/_circuitpython//Ig' > "$OUT_FILE"

echo "Resolved transitive dependencies written to $OUT_FILE"
echo "Temporary directory: $TMP_DIR"