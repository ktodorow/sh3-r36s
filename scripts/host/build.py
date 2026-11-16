#!/usr/bin/env python3
"""Build selected owner input in reusable, pinned native Linux ARM64 Docker image."""
import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile

ROOT = Path(__file__).resolve().parents[2]


def config():
    values = {}
    path = ROOT / ".env"
    for line in path.read_text().splitlines() if path.is_file() else []:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, sep, value = line.removeprefix("export ").partition("=")
        if not sep or not re.fullmatch(r"[A-Z_][A-Z0-9_]*", key.strip()):
            raise ValueError("Invalid .env assignment; shell evaluation is disabled")
        parts = shlex.split(value, comments=True)
        if len(parts) > 1:
            raise ValueError("Quote configuration values containing spaces")
        values[key.strip()] = parts[0] if parts else ""
    return values


def check_ignores():
    for path in [".env", "SILENT HILL 3/sh3.exe", "game/sh3.exe", "tmpRepo/check",
                 "build/check", "dist/check", ".port-cache/check", "r36s-dumps/check", ".cache/check"]:
        if subprocess.run(["git", "check-ignore", "-q", path], cwd=ROOT).returncode != 0:
            raise ValueError("Required private-artifact ignore coverage missing")


def package_release(runtime, input_sha1, epoch, commit):
    """Allowlisted player files only; never archive a working installation."""
    files = {
        "Silent Hill 3.sh": ROOT / "ports/Silent Hill 3 Play.sh",
        "sh3/runtime/sh3": runtime / "sh3",
        "sh3/README.md": ROOT / "README.md",
        "sh3/CREDITS.md": ROOT / "CREDITS.md",
        "sh3/licenses/xboxrecomp-MIT.txt": ROOT / "third_party/xboxrecomp/LICENSE",
        "sh3/preflight/scripts/build/check-data.sh": ROOT / "scripts/build/check-data.sh",
        "sh3/preflight/scripts/required-data.txt": ROOT / "scripts/required-data.txt",
    }
    for name in ["Silent Hill 3 Game.sh", "Silent Hill 3.sh", "game-session.sh",
                 "restore-frontend.sh", "performance-governors.py"]:
        files["sh3/preflight/ports/" + name] = ROOT / "ports" / name
    content = {name: path.read_bytes() for name, path in files.items()}
    content["sh3/runtime/input.sha1"] = (input_sha1 + "\n").encode()
    content["sh3/gamedata/README.txt"] = (
        "No game files are included. You need your own copy of the PC game;\n"
        "copy matching sh3.exe and complete data/ folder here. See ../README.md.\n"
    ).encode()
    content["sh3/release.json"] = (json.dumps({
        "title": "Silent Hill 3", "architecture": "linux-aarch64", "source_commit": commit,
        "input_sha1": input_sha1, "fps_limit": 30, "internal_resolution": "320x240",
        "output_resolution": "640x480", "diagnostic_samples": False,
        "binary_sha256": hashlib.sha256(content["sh3/runtime/sh3"]).hexdigest(),
    }, indent=2) + "\n").encode()
    dest = ROOT / "dist/release"
    dest.mkdir(parents=True, exist_ok=True)
    archive = dest / "sh3-r36s-30fps.zip"
    temporary = archive.with_suffix(".zip.tmp")
    timestamp = datetime.fromtimestamp(int(epoch), timezone.utc).timetuple()[:6]
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as package:
        for name, data in sorted(content.items()):
            info = zipfile.ZipInfo(name, timestamp)
            info.create_system = 3
            executable = name.endswith((".sh", ".py")) or name == "sh3/runtime/sh3"
            info.external_attr = (0o100755 if executable else 0o100644) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            package.writestr(info, data)
    temporary.replace(archive)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (dest / "SHA256SUMS").write_text(digest + "  " + archive.name + "\n")
    print("Release package:", archive.relative_to(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--optimization", choices=("O2", "O3"), default="O2",
                        help="Bounded compiler comparison; O2 remains default")
    parser.add_argument("--lto", action="store_true",
                        help="Compare link-time optimization with two bounded compiler jobs")
    parser.add_argument("--release", action="store_true",
                        help="Build and ZIP player runtime without private diagnostic shader samples")
    args = parser.parse_args()
    check_ignores()
    cfg = config()
    game = Path(cfg.get("SH3_GAME_DIR") or ROOT / "SILENT HILL 3").expanduser().resolve()
    validation = subprocess.run(["bash", "scripts/build/check-data.sh", str(game)],
                                cwd=ROOT, capture_output=True, text=True)
    if validation.returncode:
        print(validation.stdout + validation.stderr, end="")
        return validation.returncode
    source = (game / "sh3.exe").read_bytes()
    input_sha1 = hashlib.sha1(source).hexdigest()
    evidence = ROOT / ".port-cache/builds" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    evidence.mkdir(parents=True)
    dockerfile = ROOT / "scripts/build/Dockerfile"
    recipe = hashlib.sha256(dockerfile.read_bytes()).hexdigest()
    image = "sh3-r36s-build:" + recipe[:16]
    (evidence / "build-inputs.json").write_text(json.dumps({
        "input_sha1": input_sha1, "input_size": len(source), "recipe_sha256": recipe,
        "optimization": args.optimization, "lto": args.lto,
        "diagnostic_shader_samples": not args.release,
    }, indent=2) + "\n")
    probe = subprocess.run(["docker", "image", "inspect", image], capture_output=True, text=True)
    if probe.returncode:
        with (evidence / "image.stdout.txt").open("w") as stdout, (evidence / "image.stderr.txt").open("w") as stderr:
            status = subprocess.run(["docker", "build", "--platform", "linux/arm64", "-t", image,
                                     "-f", str(dockerfile), str(dockerfile.parent)], stdout=stdout, stderr=stderr).returncode
        if status:
            (evidence / "exit-status.txt").write_text(str(status) + "\n")
            print("Image build failed. Evidence:", evidence.relative_to(ROOT))
            return status
    info = json.loads(subprocess.check_output(["docker", "image", "inspect", image]))[0]
    if info["Os"] != "linux" or info["Architecture"] != "arm64":
        raise ValueError("Build image must be Linux ARM64")
    out = ROOT / "build/arm64"
    out.mkdir(parents=True, exist_ok=True)
    source_cache = out / "source-inputs.json"
    previous_inputs = json.loads(source_cache.read_text()) if source_cache.is_file() else {}
    paths = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT).decode().split("\0")
    inputs = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths
              if p and (p == "CMakeLists.txt" or p.startswith(("src/", "tools/", "assets/", "third_party/", "scripts/build/", "scripts/host/"))) and (ROOT / p).is_file()}
    identity = {"input_sha1": input_sha1, "input_size": len(source), "image_id": info["Id"],
                "optimization": args.optimization, "lto": args.lto,
                "diagnostic_shader_samples": not args.release,
                "recipe_sha256": recipe, "source": inputs,
                "base_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()}
    generation = {p: digest for p, digest in inputs.items()
                  if p.startswith(("tools/", "third_party/")) or p == "src/game/sh3.c"}
    generation.update(input_sha1=input_sha1, image_id=info["Id"])
    trace = ROOT / "build/trace.json"
    if trace.is_file():
        generation["trace_sha256"] = hashlib.sha256(trace.read_bytes()).hexdigest()
    identity["generation_key"] = hashlib.sha256(json.dumps(generation, sort_keys=True).encode()).hexdigest()
    (evidence / "build-inputs.json").write_text(json.dumps(identity, indent=2) + "\n")
    epoch = subprocess.check_output(["git", "show", "-s", "--format=%ct", "HEAD"], cwd=ROOT, text=True).strip()
    # Snapshot excludes private config and original game data. Selected EXE mounts read-only.
    with tempfile.TemporaryDirectory(prefix="sh3-source-", dir=ROOT / ".port-cache") as temp:
        stage = Path(temp)
        snapshot_inputs = {}
        snapshot_mtime = time.time_ns()
        for name, digest in inputs.items():
            dest = stage / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, dest)
            if hashlib.sha256(dest.read_bytes()).hexdigest() != digest:
                raise ValueError("Source changed while creating build snapshot")
            previous = previous_inputs.get(name, {})
            mtime = previous.get("mtime_ns", snapshot_mtime) if previous.get("sha256") == digest else snapshot_mtime
            os.utime(dest, ns=(mtime, mtime))
            snapshot_inputs[name] = {"sha256": digest, "mtime_ns": mtime}
        for name in ["build", "dist", "src/recomp/gen", "owner"]:
            (stage / name).mkdir(parents=True, exist_ok=True)
        (stage / "owner/sh3.exe").touch()
        generated = ROOT / "src/recomp/gen"
        generated.mkdir(parents=True, exist_ok=True)
        artifacts = evidence / "artifacts"
        artifacts.mkdir()
        argv = ["docker", "run", "--rm", "--platform", "linux/arm64", "--label", "org.sh3-r36s.build=native-arm64",
                "--mount", f"type=bind,src={stage},dst=/work,readonly",
                "--mount", f"type=bind,src={game / 'sh3.exe'},dst=/work/owner/sh3.exe,readonly",
                "--mount", f"type=bind,src={ROOT / 'build'},dst=/work/build",
                "--mount", f"type=bind,src={generated},dst=/work/src/recomp/gen",
                "--mount", f"type=bind,src={artifacts},dst=/work/dist",
                "-e", "SH3_EXE=/work/owner/sh3.exe", "-e", f"SOURCE_DATE_EPOCH={epoch}",
                "-e", "SH3_GENERATION_KEY=" + identity["generation_key"],
                "-e", "SH3_OPTIMIZATION=" + args.optimization,
                "-e", "SH3_LTO=" + ("1" if args.lto else "0"),
                "-e", "SH3_DIAGNOSTIC_SAMPLES=" + ("0" if args.release else "1"),
                "-e", "SH3_BUILD_JOBS=" + os.environ.get("SH3_BUILD_JOBS", "2"), image,
                "bash", "scripts/build/native.sh"]
        # Failed/interrupted compilation can replace some cached objects. Only
        # a complete successful build may reuse this snapshot's source times.
        source_cache.unlink(missing_ok=True)
        with (evidence / "build.stdout.txt").open("w") as stdout, (evidence / "build.stderr.txt").open("w") as stderr:
            status = subprocess.run(argv, stdout=stdout, stderr=stderr).returncode
    if status == 0:
        source_cache.write_text(json.dumps(snapshot_inputs, indent=2) + "\n")
        shutil.copy2(source_cache, evidence / source_cache.name)
    (evidence / "exit-status.txt").write_text(str(status) + "\n")
    for name in ["packages.txt", "compiler.txt", "libc.txt", "python.txt", "generation.stdout.txt", "generation.stderr.txt"]:
        if (out / name).is_file():
            shutil.copy2(out / name, evidence / name)
    for name in ["generated.sha256", "generation-key.txt", "recomp/summary.json", "recomp.log", "disasm.log", "abi.log", "arm64/compile_commands.json"]:
        if (ROOT / "build" / name).is_file():
            shutil.copy2(ROOT / "build" / name, evidence / Path(name).name)
    if hashlib.sha1((game / "sh3.exe").read_bytes()).hexdigest() != input_sha1:
        raise ValueError("Original input changed during build")
    if status == 0:
        dest = ROOT / "dist/runtime"
        package = evidence / "artifacts/runtime"
        for name in ["build-inputs.json", "packages.txt", "compiler.txt", "libc.txt", "python.txt"]:
            shutil.copy2(evidence / name, package / name)
        dest.parent.mkdir(exist_ok=True)
        if dest.exists():
            dest.rename(dest.with_name("runtime-previous-" + evidence.name))
        shutil.copytree(package, dest)
        if args.release:
            package_release(dest, input_sha1, epoch, identity["base_commit"])
    print("Build status:", status, "Evidence:", evidence.relative_to(ROOT))
    return status


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print("Build workflow failed:", type(error).__name__, file=sys.stderr)
        sys.exit(3)
