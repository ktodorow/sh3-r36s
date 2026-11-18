#!/bin/bash
# Read-only game-file checks; executable identity is not a launch requirement.
DATA_DIR=$1
check_executable() {
    if [ ! -f "$DATA_DIR/sh3.exe" ]; then
        echo 'Missing sh3.exe. Supply your PC executable with data/ in gamedata/.' >&2
        return 2
    fi
    if [ ! -s "$DATA_DIR/sh3.exe" ]; then
        echo 'Empty sh3.exe. Supply your PC executable with data/ in gamedata/.' >&2
        return 2
    fi
    echo 'Game executable present.'
}
check_executable
status=$?
manifest="$(dirname "$0")/../required-data.txt"
if [ ! -r "$manifest" ]; then
    echo "Required-data manifest unavailable; preflight cannot verify completeness." >&2
    exit 3
fi
while IFS= read -r path; do
    case "$path" in ""|\#*) continue ;; esac
    if [ ! -f "$DATA_DIR/$path" ] || [ ! -s "$DATA_DIR/$path" ]; then
        echo "Missing or empty required data: $path" >&2
        [ "$status" -ne 0 ] || status=2
    else
        printf "data-file\t%s\t%s\n" "$path" "$(wc -c < "$DATA_DIR/$path" | tr -d ' ')"
        if [ "${SH3_DATA_HASHES:-0}" = 1 ]; then
            if command -v sha256sum >/dev/null; then
                digest=$(sha256sum "$DATA_DIR/$path")
            elif command -v shasum >/dev/null; then
                digest=$(shasum -a 256 "$DATA_DIR/$path")
            else
                echo 'SHA-256 tool missing; data identity cannot be recorded.' >&2
                exit 3
            fi
            hash_status=$?
            [ "$hash_status" -eq 0 ] || exit 3
            printf 'data-sha256\t%s\t%s\n' "$path" "${digest%% *}"
        fi
    fi
done < "$manifest"
[ "$status" -ne 0 ] || echo "Game executable and required-data paths present; gameplay remains untested."
exit "$status"
