#!/bin/bash
# SH3 project play menu; SH3_DIAGNOSTICS=1 enables optional recording.
export SH3_PORT_ROOT=${SH3_PORT_ROOT:-"$(cd "$(dirname "$0")" && pwd)/sh3"}
export SH3_DIAGNOSTICS=${SH3_DIAGNOSTICS:-0}
case "$SH3_DIAGNOSTICS" in 0|1) ;; *) exit 3 ;; esac
if [ "$SH3_DIAGNOSTICS" = 0 ]; then
    # A previous experiment's environment must never drive a player's session.
    for name in ${!SH3_@}; do
        case "$name" in
            SH3_PORT_ROOT|SH3_DIAGNOSTICS|SH3_PACKAGE_DIR|SH3_SYSFS_ROOT|SH3_SERVICE_WAIT) ;;
            *) unset "$name" ;;
        esac
    done
    export SH3_QUIET=1
fi
export SH3_DIRECT_PLAY=1 SH3_FPS_LIMIT=30 SH3_INTERNAL_RESOLUTION=320x240
export SH3_GL_BACKEND=gles SH3_SHOW=1 SH3_PERFORMANCE_GOVERNORS=cpu,gpu,dmc
exec bash "$SH3_PORT_ROOT/preflight/ports/Silent Hill 3 Game.sh"
