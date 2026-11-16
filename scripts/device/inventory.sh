#!/bin/bash
# Read-only target observations. No helpers sourced, packages installed or display opened.
set -u
# Non-login SSH sessions omit administrative paths; ldconfig -p is read-only.
PATH="$PATH:/usr/sbin:/sbin"
export PATH
PORT_ROOT=$1
RUN_DIR=$2
mkdir -p "$RUN_DIR/helpers" "$RUN_DIR/existing-logs" || exit 3
probe() {
    printf '\n[%s]\n' "$1"
    shift
    if command -v "$1" >/dev/null 2>&1; then
        "$@"
        printf 'probe-exit=%s\n' "$?"
    else
        printf 'missing-tool=%s\n' "$1"
    fi
}
copy_state() {
    local source=$1 destination=$2 path relative
    for path in "$source/sh3.ini" "$source/sh3-progs.bin" "$source/sh3-gl-cache.bin" \
        "$source/savedata/disp.ini" "$source/savedata/key.ini" \
        "$source/savedata/data.sys" "$source"/savedata/data.[0-9][0-9][0-9]; do
        [ -f "$path" ] || continue
        relative=${path#"$source/"}
        mkdir -p "$destination/$(dirname "$relative")" || return 3
        cp -p "$path" "$destination/$relative" || return 3
        sha256sum "$path" >> "$destination/source.sha256" || return 3
    done
}
if [ -r /proc/sys/kernel/random/boot_id ]; then
    cat /proc/sys/kernel/random/boot_id > "$RUN_DIR/boot-id.txt"
fi
copy_state "$PORT_ROOT/state" "$RUN_DIR/persistent-state" || exit 3
{
    probe kernel uname -srvm
    probe machine uname -m
    probe bitness getconf LONG_BIT
    probe libc getconf GNU_LIBC_VERSION
    probe loader ldd --version
    for path in /etc/os-release /etc/arkos-release /etc/darkos-release \
        /boot/arkos-version /boot/darkos-version "$HOME/.config/.VERSION"; do
        if [ -f "$path" ]; then printf '\n[%s]\n' "$path"; cat "$path"; fi
    done
    for path in /proc/device-tree/compatible /proc/device-tree/model; do
        if [ -r "$path" ]; then printf '\n[%s]\n' "$path"; tr '\000' '\n' < "$path"; fi
    done
    probe memory awk '/MemTotal|MemAvailable|SwapTotal/ {print}' /proc/meminfo
    probe packages dpkg-query -W libc6:arm64 libsdl2-2.0-0:arm64
    probe python python3 --version
    probe cpu-profiler perf --version
    probe cpu-profiler-permission perf stat -e cpu-clock -- true
    if [ -r /proc/sys/kernel/perf_event_paranoid ]; then
        printf '\n[perf-event-paranoid]\n'; cat /proc/sys/kernel/perf_event_paranoid
    fi
    printf '\n[graphics-nodes]\n'
    ls -l /dev/mali0 /dev/dri 2>/dev/null || true
} > "$RUN_DIR/identity.txt" 2> "$RUN_DIR/identity.stderr.txt"
{
    probe monitor-uid id -u
    probe proc-mount awk '$2 == "/proc" {print}' /proc/mounts
    probe self-io cat /proc/self/io
    probe root-self-io sudo -n sh -c 'printf "uid="; id -u; cat /proc/self/io; status=$?; printf "io-read-exit=%s\n" "$status"; exit "$status"'
    printf '\n[kernel-io-config]\n'
    for path in /proc/config.gz "/boot/config-$(uname -r)"; do
        if [ -r "$path" ]; then
            printf '[%s]\n' "$path"
            case "$path" in
                *.gz) gzip -cd "$path" ;;
                *) cat "$path" ;;
            esac | grep -E '^(# )?CONFIG_(TASK_IO_ACCOUNTING|TASK_XACCT|TASKSTATS|IKCONFIG|IKCONFIG_PROC)(=| )' || true
        else
            printf 'unavailable=%s\n' "$path"
        fi
    done
} > "$RUN_DIR/io-capability.txt" 2> "$RUN_DIR/io-capability.stderr.txt"
{
    if command -v ldconfig >/dev/null; then
        ldconfig -p | grep -E 'lib(EGL|GLES|GL\.|mali|Mali|SDL2|c\.so)'
        ldconfig -p | awk '/lib(EGL|GLES|GL\.|mali|Mali|SDL2|c\.so)/ {print $NF}' | sort -u |
        while IFS= read -r path; do
            [ -f "$path" ] || continue
            printf '\n[library %s]\n' "$path"
            probe resolved readlink -f "$path"
            probe file file -L "$path"
            probe hash sha256sum "$path"
        done
    else
        echo 'missing-tool=ldconfig'
    fi
} > "$RUN_DIR/libraries.txt" 2> "$RUN_DIR/libraries.stderr.txt"
# Retain one existing AArch64 SDL provider for offline source/disassembly checks.
# Evidence copy only; no library installation, replacement or permission changes.
python3 - "$PORT_ROOT" "$RUN_DIR" <<'PY' > "$RUN_DIR/sdl-provider-capture.txt" 2> "$RUN_DIR/sdl-provider-capture.stderr.txt"
import hashlib
import json
import os
from pathlib import Path
import re
import sys

port, run = map(Path, sys.argv[1:])
roots = [Path('/usr/lib'), Path('/lib'), Path('/opt/system/Tools/PortMaster'),
         Path('/opt/tools/PortMaster'), Path('/roms2/ports/PortMaster'),
         Path('/roms/ports/PortMaster'), port.parent / 'PortMaster',
         Path(os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local/share'))) / 'PortMaster']
roots = [root.resolve() for root in roots]
candidates = re.findall(r'^\[library (.+)\]$', (run / 'libraries.txt').read_text(), re.M)
for candidate in candidates:
    source = Path(candidate)
    if source.name != 'libSDL2-2.0.so.0':
        continue
    resolved = source.resolve(strict=True)
    if not any(resolved.is_relative_to(root) for root in roots):
        print('skipped SDL provider outside recorded system/PortMaster library roots')
        continue
    if not 20 <= resolved.stat().st_size <= 32 * 1024 * 1024:
        continue
    data = resolved.read_bytes()
    if data[:6] != b'\x7fELF\x02\x01' or int.from_bytes(data[18:20], 'little') != 183:
        continue
    destination = run / 'sdl-provider'
    destination.mkdir()
    (destination / 'library.so').write_bytes(data)
    identity = {'source': str(source), 'resolved': str(resolved),
                'sha256': hashlib.sha256(data).hexdigest(), 'size': len(data),
                'elf': {'class': 64, 'endian': 'little', 'machine': 183}}
    (destination / 'identity.json').write_text(json.dumps(identity, indent=2) + '\n')
    print(json.dumps(identity))
    break
else:
    print('no eligible AArch64 SDL provider found')
PY
cat /proc/bus/input/devices > "$RUN_DIR/controllers.txt" 2> "$RUN_DIR/controllers.stderr.txt"
SYSFS_ROOT=${SH3_SYSFS_ROOT:-/sys}
{
    for directory in "$SYSFS_ROOT"/devices/system/cpu/cpufreq/policy* \
        "$SYSFS_ROOT"/class/devfreq/* "$SYSFS_ROOT"/class/thermal/thermal_zone*; do
        [ -d "$directory" ] || continue
        printf '\n[device %s]\n' "$directory"
        readlink -f "$directory"
        for name in affected_cpus related_cpus scaling_driver scaling_governor \
            scaling_available_governors scaling_available_frequencies scaling_cur_freq \
            scaling_min_freq scaling_max_freq cpuinfo_min_freq cpuinfo_max_freq \
            name governor available_governors available_frequencies cur_freq min_freq max_freq load type temp; do
            path="$directory/$name"
            if [ -r "$path" ]; then printf '[%s]\n' "$path"; cat "$path"; fi
        done
        if [ -L "$directory/device/driver" ]; then readlink -f "$directory/device/driver"; fi
    done
} > "$RUN_DIR/power-policy.txt" 2> "$RUN_DIR/power-policy.stderr.txt"
# Preserve only policy-related installed source/config, never execute firmware helpers.
mkdir -p "$RUN_DIR/power-owners"
for path in /etc/emulationstation/es_systems.cfg "$HOME/.emulationstation/es_systems.cfg" \
    /usr/local/bin/perfmax /usr/local/bin/perfnorm /usr/bin/perfmax /usr/bin/perfnorm \
    /usr/bin/emulationstation.sh /usr/bin/emulationstation /usr/bin/emulationstation/emulationstation.sh; do
    [ -f "$path" ] || continue
    case "$path" in
        *.cfg) ;;
        *) [ "$(head -c 2 "$path")" = '#!' ] || continue ;;
    esac
    destination="$RUN_DIR/power-owners$path"
    mkdir -p "$(dirname "$destination")" || exit 3
    cp -p "$path" "$destination" || exit 3
    sha256sum "$path" >> "$RUN_DIR/power-owners.sha256"
done
mkdir -p "$RUN_DIR/input-configs"
input_index=0
for path in "$HOME/.emulationstation/es_input.cfg" "$HOME/.config/emulationstation/es_input.cfg" \
    /etc/emulationstation/es_input.cfg; do
    if [ -f "$path" ]; then
        cp -p "$path" "$RUN_DIR/input-configs/es-input-$input_index.cfg" || exit 3
        input_index=$((input_index + 1))
    fi
done
ps -C emulationstation -o pid=,stat=,comm= > "$RUN_DIR/frontend-before.txt" 2>/dev/null || true
{
    probe systemd systemctl --version
    probe frontend-service systemctl show emulationstation.service \
        -p Id -p LoadState -p ActiveState -p SubState -p MainPID -p ControlGroup -p KillMode -p Restart \
        -p FragmentPath -p ExecStart -p ExecStop -p ExecStopPost
    probe frontend-unit systemctl cat emulationstation.service
    printf '\n[probe-cgroup]\n'
    cat "/proc/$$/cgroup"
    probe detached-launcher command -v systemd-run
    probe noninteractive-privilege sudo -n true
} > "$RUN_DIR/frontend-service.txt" 2> "$RUN_DIR/frontend-service.stderr.txt"
awk -v root="$PORT_ROOT" 'index($2,root)==1 {print}' /proc/mounts > "$RUN_DIR/port-mounts-before.txt"
: > "$RUN_DIR/portmaster-files.sha256"
for pm in /opt/system/Tools/PortMaster /opt/tools/PortMaster \
    "${XDG_DATA_HOME:-$HOME/.local/share}/PortMaster" /roms2/ports/PortMaster /roms/ports/PortMaster; do
    [ -f "$pm/control.txt" ] || continue
    if [ -f "$pm/gamecontrollerdb.txt" ]; then
        mkdir -p "$RUN_DIR/input-configs/$(basename "$(dirname "$pm")")"
        cp -p "$pm/gamecontrollerdb.txt" "$RUN_DIR/input-configs/$(basename "$(dirname "$pm")")/" || exit 3
    fi
    # Preserve original paths in checksum record; copy only code/metadata, never settings/secrets.
    find -L "$pm" -maxdepth 1 -type f \( -name control.txt -o -name funcs.txt \
        -o -name 'mod_*.txt' -o -name device_info.txt -o -name mapper.txt \
        -o -name PortMasterDialog.txt -o -name mapper.py -o -name pugwash \) -print |
    sort | while IFS= read -r path; do
        sha256sum "$path" >> "$RUN_DIR/portmaster-files.sha256"
        dest="$RUN_DIR/helpers$path"
        mkdir -p "$(dirname "$dest")"
        cp -p "$path" "$dest"
    done
done
for name in log.txt sh3.log sh3-crash.log; do
    if [ -f "$PORT_ROOT/$name" ]; then
        sha256sum "$PORT_ROOT/$name"
        cp -p "$PORT_ROOT/$name" "$RUN_DIR/existing-logs/$name"
    fi
done > "$RUN_DIR/existing-logs-before.sha256"
# Reference completed originals instead of duplicating all history into every new run.
python3 - "$PORT_ROOT" "$RUN_DIR/previous-launches.sha256" <<'PY_HISTORY' || exit 3
import hashlib
from pathlib import Path
import sys

port, output = map(Path, sys.argv[1:])
with output.open('w') as manifest:
    for record in sorted((port / 'runs').glob('*/run-id.txt')):
        launch = record.parent
        if not (launch / 'exit-status.txt').is_file():
            continue
        paths = [launch / name for name in
                 ('run-id.txt', 'stdout.txt', 'stderr.txt', 'data.stderr.txt', 'exit-status.txt')]
        state = launch / 'session'
        paths += [state / name for name in ('sh3.ini', 'sh3-progs.bin', 'sh3-gl-cache.bin',
                  'savedata/disp.ini', 'savedata/key.ini', 'savedata/data.sys')]
        paths += sorted((state / 'savedata').glob('data.[0-9][0-9][0-9]'))
        service = launch.with_name(launch.name + '-service')
        paths += [service / name for name in ('stdout.txt', 'stderr.txt', 'exit-status.txt',
                  'cgroup.txt', 'frontend-game.txt', 'frontend-restored.txt', 'memory-before.txt',
                  'memory-game.txt', 'memory-restored.txt', 'performance.txt',
                  'performance.stderr.txt', 'frontend-stopped')]
        for path in paths:
            if path.is_file():
                checksum = hashlib.sha256()
                with path.open('rb') as source:
                    for chunk in iter(lambda: source.read(1024 * 1024), b''):
                        checksum.update(chunk)
                manifest.write(checksum.hexdigest() + '  ' + str(path) + '\n')
PY_HISTORY
echo 'Target observations collected; active SDL backend and GLES operations untested.'
