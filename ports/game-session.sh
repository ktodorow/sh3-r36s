#!/bin/bash
# Detached native session; stop frontend only after recovery is armed.
set -u
PORT_ROOT=$SH3_PORT_ROOT
RUN_ID=$SH3_RUN_ID
SERVICE_DIR=${SH3_CONTROL_DIR:-"$PORT_ROOT/runs/${RUN_ID}-service"}
privilege=()
monitor=
counters=
if [ "$(id -u)" -ne 0 ]; then privilege=(sudo -n); fi
cleanup() {
    local status=$? counter_status=0
    trap - EXIT
    if [ -n "$counters" ]; then
        kill "$counters" 2>/dev/null || true
        wait "$counters" 2>/dev/null; counter_status=$?
        printf '%s\n' "$counter_status" > "$SERVICE_DIR/counter-exit-status.txt"
    fi
    if [ -n "$monitor" ]; then kill "$monitor" 2>/dev/null || true; wait "$monitor" 2>/dev/null || true; fi
    if ! bash "$PORT_ROOT/preflight/ports/restore-frontend.sh" "$PORT_ROOT" "$RUN_ID"; then
        if [ "$status" -eq 0 ]; then status=3; fi
    fi
    if [ "${SH3_DIAGNOSTICS:-1}" = 1 ]; then printf '%s\n' "$status" > "$SERVICE_DIR/exit-status.txt"; fi
    exit "$status"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM HUP
if [ ! -r "/proc/$$/cgroup" ] || grep -q 'emulationstation.service' "/proc/$$/cgroup"; then
    echo 'Game still belongs to frontend process group; refusing to stop frontend.' >&2
    exit 3
fi
if [ "${SH3_DIAGNOSTICS:-1}" = 1 ]; then
    cat "/proc/$$/cgroup" > "$SERVICE_DIR/cgroup.txt"
    free -k > "$SERVICE_DIR/memory-before.txt"
fi
if systemctl is-active --quiet emulationstation.service; then
    touch "$SERVICE_DIR/frontend-stopped" || exit 3
    "${privilege[@]}" systemctl stop emulationstation.service || exit 3
    if systemctl is-active --quiet emulationstation.service || pgrep -x emulationstatio >/dev/null; then
        echo 'Frontend remains running; game not started.' >&2
        exit 3
    fi
    echo 'Frontend stopped for native game.'
fi
if [ "${SH3_DIAGNOSTICS:-1}" = 1 ]; then
    free -k > "$SERVICE_DIR/memory-game.txt"
    systemctl show emulationstation.service -p ActiveState -p MainPID > "$SERVICE_DIR/frontend-game.txt"
fi
if [ -n "${SH3_PERFORMANCE_GOVERNORS:-}" ]; then
    "${privilege[@]}" env "SH3_DIAGNOSTICS=${SH3_DIAGNOSTICS:-1}" \
        python3 "$PORT_ROOT/preflight/ports/performance-governors.py" begin \
        "$PORT_ROOT" "$RUN_ID" "$SH3_PERFORMANCE_GOVERNORS" "${SH3_SYSFS_ROOT:-/sys}" || exit 3
fi
if [ "${SH3_MONITOR:-0}" = 1 ]; then
    bash "$PORT_ROOT/preflight/scripts/device/monitor-game.sh" "$SERVICE_DIR" &
    monitor=$!
fi
if [ -n "${SH3_GPU_COUNTER_PAYLOAD:-}" ]; then
    mkdir "$SERVICE_DIR/counters" || exit 3
    python3 "$SH3_GPU_COUNTER_PAYLOAD/scripts/device/gpu-counter-session.py" "$SERVICE_DIR/counters" 100 125 150 \
        --payload "$SH3_GPU_COUNTER_PAYLOAD" \
        > "$SERVICE_DIR/counter.stdout.txt" 2> "$SERVICE_DIR/counter.stderr.txt" &
    counters=$!
fi
launcher_clock() {
    python3 - "$SERVICE_DIR/launcher-clock.json" "$1" <<'PY'
import json
from pathlib import Path
import sys
import time
path = Path(sys.argv[1])
record = json.loads(path.read_text()) if path.exists() else {}
record[sys.argv[2]] = {'monotonic_ns': time.monotonic_ns(),
                      'raw_ns': time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW)}
path.write_text(json.dumps(record, indent=2) + '\n')
PY
}
if [ -n "$counters" ]; then launcher_clock before || exit 3; fi
bash "$PORT_ROOT/preflight/ports/Silent Hill 3.sh"
game_status=$?
if [ -n "$counters" ]; then launcher_clock after || game_status=3; fi
exit "$game_status"
