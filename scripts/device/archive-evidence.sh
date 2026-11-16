#!/bin/bash
# Snapshot owned run after exit; preserve sources and do not follow payload links.
set -euo pipefail
RUN_DIR=$(realpath -- "${1:?run directory required}")
[ -d "$RUN_DIR" ] || exit 3
ARCHIVE="${RUN_DIR}.evidence.tar.gz"
tar --create --gzip --file="$ARCHIVE.tmp" --directory="$RUN_DIR" \
    --exclude='./payload/runtime/sh3' .
mv -- "$ARCHIVE.tmp" "$ARCHIVE"
