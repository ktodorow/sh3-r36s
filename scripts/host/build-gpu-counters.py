#!/usr/bin/env python3
"""Build reviewed Arm counter example separately from game package; no downloads."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from r36s import ROOT, check_ignores

COMMIT = "847a04a1597d132a3746e9c6374d3977cea89a6d"
URL = "https://github.com/ARM-software/libGPUCounters"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path,
                        help="Reviewed, unchanged pinned clone under project tmpRepo")
    parser.add_argument("--variant", choices=["official", "targeted"], default="official")
    args = parser.parse_args()
    check_ignores()
    evidence = ROOT / ".port-cache/gpu-counter-builds" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    evidence.mkdir(parents=True)
    image = "sh3-r36s-build:" + hashlib.sha256((ROOT / "scripts/build/Dockerfile").read_bytes()).hexdigest()[:16]
    identity = {"source_url": URL, "source_commit": COMMIT,
                "platform": "linux/arm64", "image": image, "variant": args.variant}
    (evidence / "build-inputs.json").write_text(json.dumps(identity, indent=2) + "\n")
    with (evidence / "image.stdout.txt").open("w") as stdout, (evidence / "image.stderr.txt").open("w") as stderr:
        status = subprocess.run(["docker", "image", "inspect", image], stdout=stdout, stderr=stderr).returncode
    if status == 0:
        try:
            info = json.loads((evidence / "image.stdout.txt").read_text())[0]
            if info["Os"] != "linux" or info["Architecture"] != "arm64":
                raise ValueError("Build image must be Linux ARM64")
            source = args.source.expanduser().resolve(strict=True)
            if not source.is_relative_to((ROOT / "tmpRepo").resolve()):
                raise ValueError("Counter source must be task-owned clone inside project tmpRepo")
            commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip()
            if commit != COMMIT or subprocess.check_output(["git", "status", "--porcelain"], cwd=source):
                raise ValueError("Counter source must match unchanged reviewed upstream pin")
            paths = subprocess.check_output(["git", "ls-files", "-z"], cwd=source).decode().split("\0")
            hashes = {p: hashlib.sha256((source / p).read_bytes()).hexdigest() for p in paths if p}
            build_script = ROOT / "scripts/build/gpu-counters.sh"
            identity.update(image_id=info["Id"], source=hashes,
                            source_path=str(source.relative_to(ROOT)),
                            build_script_sha256=hashlib.sha256(build_script.read_bytes()).hexdigest())
            (evidence / "build-inputs.json").write_text(json.dumps(identity, indent=2) + "\n")
            argv = ["docker", "run", "--rm", "--platform", "linux/arm64", "--network", "none",
                    "--label", "org.sh3-r36s.build=native-arm64",
                    "--mount", f"type=bind,src={source},dst=/source,readonly",
                    "--mount", f"type=bind,src={build_script},dst=/build-counter-example.sh,readonly",
                    "--mount", f"type=bind,src={evidence},dst=/out"]
            if args.variant == "targeted":
                probe = ROOT / "scripts/probes/gpu-counter-targeted.cpp"
                identity["probe_sha256"] = hashlib.sha256(probe.read_bytes()).hexdigest()
                (evidence / "build-inputs.json").write_text(json.dumps(identity, indent=2) + "\n")
                argv += ["--mount", f"type=bind,src={probe},dst=/gpu-counter-targeted.cpp,readonly"]
            argv += [image, "bash", "/build-counter-example.sh", args.variant]
            with (evidence / "build.stdout.txt").open("w") as stdout, (evidence / "build.stderr.txt").open("w") as stderr:
                status = subprocess.run(argv, stdout=stdout, stderr=stderr).returncode
            if any(hashlib.sha256((source / p).read_bytes()).hexdigest() != digest for p, digest in hashes.items()):
                raise ValueError("Reviewed source changed during build")
        except (OSError, ValueError, subprocess.CalledProcessError) as error:
            (evidence / "validation.stderr.txt").write_text(str(error) + "\n")
            status = 3
    (evidence / "exit-status.txt").write_text(str(status) + "\n")
    print("Counter build status:", status, "Evidence:", evidence.relative_to(ROOT))
    return status


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print("Counter build failed:", type(error).__name__, file=sys.stderr)
        sys.exit(3)
