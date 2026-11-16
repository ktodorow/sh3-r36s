#!/bin/bash
# Optional counter capability diagnostic; only its own run output is writable.
set -u
RUN_DIR=${1:?run directory required}
OUT="$RUN_DIR/gpu-counter"
PAYLOAD="${2:-$RUN_DIR/payload}/gpu-counter"
mkdir -p "$OUT" || exit 3
{
    uname -srvm
    id
    for path in /dev/mali0 /dev/dri/renderD128; do
        printf '\n[node %s]\n' "$path"
        stat -L -c '%n type=%F mode=%a uid=%u gid=%g device=%t:%T' "$path"
        if [ -r "$path" ]; then echo readable=yes; else echo readable=no; fi
        if [ -w "$path" ]; then echo writable=yes; else echo writable=no; fi
    done
    for path in /sys/module/mali_kbase/version /sys/module/mali/version \
        /sys/module/mali_kbase/parameters/* /sys/module/mali/parameters/*; do
        [ -f "$path" ] && [ -r "$path" ] || continue
        printf '\n[%s]\n' "$path"
        cat "$path"
    done
    for path in /sys/class/misc/mali0/device/driver /sys/kernel/debug/mali0 \
        /sys/kernel/debug/mali /sys/kernel/debug/mali_kbase; do
        printf '\n[driver path %s]\n' "$path"
        ls -ld "$path"
        [ ! -L "$path" ] || readlink -f "$path"
    done
    if [ -r /proc/config.gz ]; then
        printf '\n[/proc/config.gz Mali configuration]\n'
        gzip -cd /proc/config.gz | grep -E '(^CONFIG_MALI|^# CONFIG_MALI)'
    elif [ -r "/boot/config-$(uname -r)" ]; then
        printf '\n[boot Mali configuration]\n'
        grep -E '(^CONFIG_MALI|^# CONFIG_MALI)' "/boot/config-$(uname -r)"
    else
        echo 'kernel-config=not-readable'
    fi
} > "$OUT/inventory.txt" 2> "$OUT/inventory.stderr.txt"
(
    cd "$PAYLOAD" || exit 3
    # Accept one local artifact only; reject manifest paths outside payload.
    awk 'NF != 2 || $2 != "api-example" || length($1) != 64 || $1 ~ /[^0-9a-fA-F]/ {exit 1}
         END {if (NR != 1) exit 1}' SHA256SUMS || exit 3
    sha256sum --check --strict SHA256SUMS
) > "$OUT/verification.stdout.txt" 2> "$OUT/verification.stderr.txt"
verification=$?
printf '%s\n' "$verification" > "$OUT/verification-exit-status.txt"
if [ "$verification" -eq 0 ]; then
    timeout --signal=TERM --kill-after=1s 10s "$PAYLOAD/api-example" \
        > "$OUT/stdout.txt" 2> "$OUT/stderr.txt"
    status=$?
else
    : > "$OUT/stdout.txt"
    echo 'Payload verification failed; native probe not executed.' > "$OUT/stderr.txt"
    status=3
fi
printf '%s\n' "$status" > "$OUT/exit-status.txt"
python3 - "$OUT" "$status" "$verification" <<'PY'
import json
from pathlib import Path
import re
import sys

out = Path(sys.argv[1])
status = int(sys.argv[2])
verified = int(sys.argv[3]) == 0
text = (out / "stdout.txt").read_text(errors="replace")
number = r"(?:[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[-+]?\d+)?|[-+]?nan|[-+]?inf)"
sample = re.compile(r"^GPU Active cycles \[\d+\] ; (?:Fragment Active Cycles|Shader Core Active) "
                    r"\[\d+\] ; Geometry Sample Cull Rate \[" + number + r"\]$", re.I)
lines = text.splitlines()
complete = sum(bool(sample.fullmatch(line)) for line in lines)
supported = []
collecting = False
for line in lines:
    value = line.strip()
    if value == "GPU 0 Supported counters:":
        collecting = True
    elif value == "Sample Capture:":
        collecting = False
    elif collecting and value and not value.startswith("---"):
        supported.append(value)
def metadata(label, numeric=False):
    match = re.search(r"^\s*" + re.escape(label) + r":\s*(.+)$", text, re.M)
    if not match:
        return None
    value = match.group(1).strip()
    return int(value) if numeric and value.isdigit() else (None if numeric else value)
family = metadata("Product Family")
cores = metadata("Number of Cores", True)
bus = metadata("Bus Width", True)
usable = verified and status == 0 and complete == 10 and bool(supported) and bool(family) and bool(cores) and bool(bus)
summary = {"native_exit_status": status if verified else None, "payload_verified": verified,
           "usable_samples": usable,
           "complete_samples": complete, "product_family": family,
           "shader_cores": cores, "bus_width": bus, "supported_counters": supported,
           "classification": "payload-invalid" if not verified else "usable-samples" if usable else
                             ("probe-failed" if status else "incomplete-samples")}
(out / "capability.json").write_text(json.dumps(summary, indent=2) + "\n")
PY
exit "$status"
