#!/bin/bash
# Idempotent recovery, also called as privileged service ExecStopPost after crashes.
set -u
unset LD_LIBRARY_PATH LD_PRELOAD
PORT_ROOT=$1
RUN_ID=$2
case "$RUN_ID" in ''|*[!A-Za-z0-9_-]*) echo 'Invalid recovery run ID' >&2; exit 3 ;; esac
SERVICE_DIR=${SH3_CONTROL_DIR:-"$PORT_ROOT/runs/${RUN_ID}-service"}
privilege=()
if [ "$(id -u)" -ne 0 ]; then privilege=(sudo -n); fi
power_status=0
if [ -f "$PORT_ROOT/.performance-policy-owner.json" ]; then
    "${privilege[@]}" env "SH3_DIAGNOSTICS=${SH3_DIAGNOSTICS:-1}" \
        python3 "$PORT_ROOT/preflight/ports/performance-governors.py" end \
        "$PORT_ROOT" "$RUN_ID" || power_status=3
fi
[ -f "$SERVICE_DIR/frontend-stopped" ] || exit "$power_status"
"${privilege[@]}" systemctl reset-failed emulationstation.service || true
"${privilege[@]}" systemctl start emulationstation.service || exit 3
for attempt in {1..30}; do
    if systemctl is-active --quiet emulationstation.service && pgrep -x emulationstatio >/dev/null; then
        echo 'Frontend restored.'
        if [ "${SH3_DIAGNOSTICS:-1}" = 1 ]; then
            free -k > "$SERVICE_DIR/memory-restored.txt"
            systemctl show emulationstation.service -p ActiveState -p MainPID > "$SERVICE_DIR/frontend-restored.txt"
        fi
        rm "$SERVICE_DIR/frontend-stopped"
        if [ "${SH3_DIAGNOSTICS:-1}" = 0 ] && [ "$power_status" -eq 0 ]; then
            case "$SERVICE_DIR" in
                /tmp/sh3-r36s-[0-9]*-"$RUN_ID".??????)
                    [ ! -L "$SERVICE_DIR" ] && rm -rf -- "$SERVICE_DIR" ;;
            esac
        fi
        exit "$power_status"
    fi
    sleep 1
done
echo 'Frontend restore failed; recovery marker retained.' >&2
exit 3
