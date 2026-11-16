#!/usr/bin/env python3
"""Run at most three optional counter capability samples beside controlled game."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import time


def boundary():
    frequencies = {"cpu": {}, "gpu": {}, "dmc": {}}
    paths = list(Path("/sys/devices/system/cpu/cpufreq").glob("policy*/scaling_cur_freq"))
    paths += list(Path("/sys/class/devfreq").glob("*/cur_freq"))
    for path in paths:
        name = str(path)
        domain = None
        if "cpufreq" in name:
            domain = "cpu"
        elif "gpu" in name or "mali" in name:
            domain = "gpu"
        elif "dmc" in name:
            domain = "dmc"
        if domain:
            try:
                frequencies[domain][name] = path.read_text().strip()
            except OSError as error:
                frequencies[domain][name] = {"error": error.errno}
    return {"monotonic_ns": time.monotonic_ns(), "utc": datetime.now(timezone.utc).isoformat(),
            "frequencies": frequencies}


def session_groups(session):
    groups = set()
    for path in Path("/proc").glob("[0-9]*/stat"):
        try:
            fields = path.read_text().rsplit(")", 1)[1].split()
            if int(fields[3]) == session and fields[0] != "Z":
                groups.add(int(fields[2]))
        except (OSError, ValueError, IndexError):
            continue
    return groups


def stop_reader(process):
    # GNU timeout creates another process group inside helper's new session.
    # Stop both groups, including native reader, without touching game session.
    signalled = set()
    deadline = time.monotonic() + 1
    while time.monotonic() < deadline:
        groups = session_groups(process.pid)
        if not groups:
            break
        for group in groups - signalled:
            try:
                os.killpg(group, signal.SIGTERM)
            except ProcessLookupError:
                pass
        signalled |= groups
        time.sleep(.02)
    for group in session_groups(process.pid):
        try:
            os.killpg(group, signal.SIGKILL)
        except ProcessLookupError:
            pass
    process.wait(timeout=1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--payload", type=Path, help="existing payload directory; defaults to RUN_DIR/payload")
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("offsets", nargs="*", type=float)
    args = parser.parse_args()
    offsets = args.offsets or [80, 110, 145]
    if len(offsets) > 3 or any(not math.isfinite(value) or value < 0 or value > 180 for value in offsets):
        parser.error("require at most three finite absolute offsets between 0 and 180 seconds")
    offsets = sorted(offsets)
    run = args.run_dir.resolve()
    payload = (args.payload or run / "payload").resolve()
    binary = payload / "gpu-counter/api-example"
    try:
        digest = hashlib.sha256(binary.read_bytes()).hexdigest()
    except OSError:
        digest = None  # Saved helper preserves missing/unreadable payload failure.
    output = run / "gpu-counter-active"
    output.mkdir()
    summary = {"anchor": boundary(), "offsets_seconds": offsets, "samples": [], "status": "running"}
    summary["payload"] = {"directory": str(payload), "binary_sha256": digest}

    def save():
        temporary = output / "session.json.tmp"
        temporary.write_text(json.dumps(summary, indent=2) + "\n")
        temporary.replace(output / "session.json")

    stopping = False

    def terminate(signum, frame):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, terminate)
    signal.signal(signal.SIGINT, terminate)
    save()
    for index, offset in enumerate(offsets, 1):
        target = summary["anchor"]["monotonic_ns"] + int(offset * 1e9)
        while not stopping and time.monotonic_ns() < target:
            time.sleep(max(0, min(.1, (target - time.monotonic_ns()) / 1e9)))
        if stopping:
            break
        child = output / f"sample-{index:03d}"
        child.mkdir()
        sample = {"scheduled_offset_seconds": offset, "start": boundary()}
        helper = payload / "scripts/device/gpu-counter-probe.sh"
        with (child / "helper.stdout.txt").open("w") as stdout, (child / "helper.stderr.txt").open("w") as stderr:
            process = subprocess.Popen(["bash", str(helper), str(child), str(payload)], stdout=stdout, stderr=stderr,
                                       start_new_session=True)
            deadline = time.monotonic() + 12
            while process.poll() is None and not stopping and time.monotonic() < deadline:
                time.sleep(.02)
            if process.poll() is None:
                stop_reader(process)
        sample["end"] = boundary()
        sample["helper_exit_status"] = process.returncode
        capability = child / "gpu-counter/capability.json"
        sample["capability"] = json.loads(capability.read_text()) if capability.is_file() else None
        summary["samples"].append(sample)
        save()
        if stopping:
            break
    summary["status"] = "terminated" if stopping else "finished"
    save()
    return 143 if stopping else 0


if __name__ == "__main__":
    raise SystemExit(main())
