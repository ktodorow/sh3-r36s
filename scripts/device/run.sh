#!/bin/bash
# Saved remote entry. All task commands remain reviewable in repository scripts.
set -u
ACTION=$1
PORT_ROOT=$2
RUN_ID=$3
PAYLOAD=$4
RUN_DIR="$PORT_ROOT/runs/$RUN_ID"
# Keep capacity diagnostics in host-captured output even if evidence storage is full.
bash "$PAYLOAD/scripts/device/capacity.sh" "$PORT_ROOT"
mkdir -p "$RUN_DIR" || exit 3
exec > "$RUN_DIR/execution.stdout.txt" 2> "$RUN_DIR/execution.stderr.txt"
finish() {
    status=$?
    trap - EXIT
    ps -C emulationstation -o pid=,stat=,comm= > "$RUN_DIR/frontend-after.txt" 2>/dev/null || true
    pgrep -x sh3 > "$RUN_DIR/runtime-pids-after.txt" 2>/dev/null || true
    awk -v root="$PORT_ROOT" 'index($2,root)==1 {print}' /proc/mounts > "$RUN_DIR/port-mounts-after.txt"
    if [ -s "$RUN_DIR/firmware-libraries-before.sha256" ]; then
        sha256sum -c "$RUN_DIR/firmware-libraries-before.sha256" > "$RUN_DIR/firmware-libraries-after.txt" 2>&1 || status=3
    fi
    if [ -s "$RUN_DIR/existing-logs-before.sha256" ]; then
        sha256sum -c "$RUN_DIR/existing-logs-before.sha256" > "$RUN_DIR/existing-logs-after.txt" 2>&1
    fi
    printf '%s\n' "$status" > "$RUN_DIR/execution-status.txt"
    for evidence in "$RUN_DIR" "${RUN_DIR}-launch" "${RUN_DIR}-launch-service"; do
        if [ -d "$evidence" ]; then
            bash "$PAYLOAD/scripts/device/archive-evidence.sh" "$evidence" || status=3
        fi
    done
    exit "$status"
}
trap finish EXIT
bash "$PAYLOAD/scripts/device/inventory.sh" "$PORT_ROOT" "$RUN_DIR" || exit 3
awk 'length($1)==64 && $1 !~ /[^0-9a-f]/ && $2 ~ /^\// {print}' "$RUN_DIR/libraries.txt" \
    > "$RUN_DIR/firmware-libraries-before.sha256"
if [ "$ACTION" = inventory ]; then
    if [ -f "$PAYLOAD/gpu-counter/api-example" ]; then
        bash "$PAYLOAD/scripts/device/gpu-counter-probe.sh" "$RUN_DIR" || true
    fi
    exit 0
fi
case "$ACTION" in preflight|runtime|gles|game) ;; *) echo 'Unknown action' >&2; exit 3 ;; esac
if [ ! -s "$PAYLOAD/reviewed-helpers.sha256" ] || \
    ! cmp -s "$PAYLOAD/reviewed-helpers.sha256" "$RUN_DIR/portmaster-files.sha256"; then
    echo 'Installed PortMaster helpers differ from reviewed inventory; refusing to source.' >&2
    exit 3
fi
MENU="$(dirname "$PORT_ROOT")/Silent Hill 3 Preflight.sh"
if [ -e "$MENU" ] && ! grep -q '^# SH3 project preflight launcher;' "$MENU"; then
    echo 'Existing menu entry belongs to another installation; preserved.' >&2
    exit 3
fi
if [ -e "$PORT_ROOT/preflight" ] && [ ! -f "$PORT_ROOT/preflight/.sh3-preflight-owned" ]; then
    echo 'Existing preflight directory is not project-owned; preserved.' >&2
    exit 3
fi
mkdir -p "$PORT_ROOT/preflight/scripts/device" "$PORT_ROOT/preflight/ports" || exit 3
cp "$PAYLOAD/scripts/device/check-data.sh" "$PORT_ROOT/preflight/scripts/device/" || exit 3
cp "$PAYLOAD/scripts/device/monitor-game.sh" "$PORT_ROOT/preflight/scripts/device/" || exit 3
cp "$PAYLOAD/scripts/required-data.txt" "$PORT_ROOT/preflight/scripts/" || exit 3
cp "$PAYLOAD/ports/Silent Hill 3.sh" "$PORT_ROOT/preflight/ports/" || exit 3
cp "$PAYLOAD/ports/game-session.sh" "$PAYLOAD/ports/restore-frontend.sh" \
    "$PAYLOAD/ports/performance-governors.py" "$PORT_ROOT/preflight/ports/" || exit 3
touch "$PORT_ROOT/preflight/.sh3-preflight-owned" || exit 3
cp "$PAYLOAD/ports/Silent Hill 3.sh" "$MENU" || exit 3
chmod +x "$MENU" || exit 3
if [ "$ACTION" = runtime ] || [ "$ACTION" = gles ] || [ "$ACTION" = game ]; then
    bash "$PAYLOAD/scripts/device/runtime.sh" "$PORT_ROOT" "$RUN_ID" "$PAYLOAD" "$RUN_DIR" "$ACTION"
    exit $?
fi
# Launcher owns its own new evidence directory; outer inventory remains preserved.
if [ -f "$PAYLOAD/hash-data" ]; then export SH3_DATA_HASHES=1; fi
SH3_PORT_ROOT="$PORT_ROOT" SH3_RUN_ID="${RUN_ID}-launch" SH3_PREFLIGHT_HEADLESS=1 bash "$MENU"
