#!/usr/bin/env python3
"""Unattended SH3 deployment, saved device execution and failure-safe collection."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tarfile
import tempfile
import uuid


ROOT = Path(__file__).resolve().parents[2]
FILES = ["scripts/device/inventory.sh", "scripts/device/run.sh",
         "scripts/device/play-ready.py",
         "scripts/device/capacity.sh",
         "scripts/device/reclaim-payloads.py",
         "scripts/device/archive-evidence.sh",
         "scripts/device/gpu-counter-probe.sh",
         "scripts/device/gpu-counter-session.py",
         "scripts/device/check-data.sh", "scripts/device/runtime.sh", "scripts/required-data.txt",
         "scripts/scenes.json",
         "scripts/device/monitor-game.sh",
         "ports/Silent Hill 3.sh", "ports/Silent Hill 3 Runtime Diagnostics.sh",
         "ports/Silent Hill 3 Graphics Diagnostics.sh", "ports/Silent Hill 3 Game.sh",
         "ports/Silent Hill 3 Play.sh",
         "ports/Silent Hill 3 Performance.sh",
         "ports/game-session.sh", "ports/restore-frontend.sh", "ports/performance-governors.py"]


def config():
    values = {}
    for line in (ROOT / ".env").read_text().splitlines():
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
                 "build/check", ".port-cache/check", "r36s-dumps/check", ".cache/check"]:
        if subprocess.run(["git", "check-ignore", "-q", path], cwd=ROOT).returncode != 0:
            raise ValueError("Required private-artifact ignore coverage missing")


def extract_evidence(archive_path, destination):
    """Copy validated regular evidence; retain link metadata without following links."""
    with tarfile.open(archive_path, 'r:gz') as archive:
        members = archive.getmembers()
        manifest = []
        seen = set()
        for member in members:
            path = PurePosixPath(member.name)
            if (path.is_absolute() or '..' in path.parts or
                    not (member.isfile() or member.isdir() or member.issym() or member.islnk()) or
                    (str(path) == '.' and not member.isdir()) or path in seen):
                raise ValueError('Unsafe evidence archive member')
            seen.add(path)
            manifest.append({'name': member.name, 'mode': member.mode, 'size': member.size,
                             'link_target': member.linkname,
                             'skipped_link': member.issym() or member.islnk()})
        destination.mkdir()
        for member in members:
            target = destination.joinpath(*PurePosixPath(member.name).parts)
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            elif member.isfile():
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.extractfile(member) as source, target.open('xb') as output:
                    shutil.copyfileobj(source, output)
        destination.with_name(destination.name + '-archive-manifest.json').write_text(
            json.dumps(manifest, indent=2) + '\n')


def main():
    from scenes import SCENES, scene_identity, seed_hashes

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["inventory", "preflight", "runtime", "gles", "game"])
    parser.add_argument("--reviewed-helpers", type=Path,
                        help="Prior collected inventory directory whose helpers were reviewed")
    parser.add_argument("--hash-data", action="store_true", help="Record complete asset SHA-256 identities during preflight")
    parser.add_argument("--scene", choices=SCENES, help="Replay shared desktop/device scene plan")
    parser.add_argument('--runtime-package', type=Path, help='Retained native package for matched candidate measurements')
    parser.add_argument('--performance-governors', help='Opt-in isolated diagnostic domains: cpu,gpu,dmc')
    parser.add_argument('--gpu-counter-probe', type=Path, help='Reviewed native counter probe for isolated diagnostics')
    parser.add_argument('--retry-collection', help='Collect prior run into fresh evidence without device execution')
    parser.add_argument('--reclaim-payloads', type=Path,
                        help='Remove explicit unused payload copies after local and device SHA validation')
    parser.add_argument('--play-action', choices=['inspect', 'clean', 'install', 'verify'],
                        help='SH3-only play preparation; stream evidence without device run logs')
    parser.add_argument('--play-settings', type=Path, help='Fresh, game-created data.sys for personal play install')
    parser.add_argument("--seed-session", type=Path, help="Copy explicit checkpoint into isolated scene session")
    parser.add_argument("--physical-controls", action="store_true",
                        help="Run handheld input check through game menu, without scripted keys or captures")
    parser.add_argument("--physical-profile", choices=["320x240", "640x480"],
                        help="Measure isolated handheld gameplay at selected internal resolution, without captures")
    parser.add_argument("--persistent-state", action="store_true",
                        help="Run physical check with ordinary persistent player state")
    parser.add_argument("--import-session", type=Path,
                        help="Copy collected player state on first persistent launch only")
    parser.add_argument("--prime-program-cache", type=Path,
                        help="Prime missing player program cache from measured same-device cache; preserve existing state")
    args = parser.parse_args()
    if args.play_action and (args.action != 'inventory' or args.retry_collection or args.reclaim_payloads or
                            args.gpu_counter_probe or args.scene or
                            (args.runtime_package and args.play_action != 'install')):
        parser.error('--play-action requires standalone inventory action')
    if bool(args.play_settings) != (args.play_action == 'install'):
        parser.error('--play-action install requires --play-settings; other actions cannot use it')
    if args.reclaim_payloads and (args.action != 'inventory' or args.retry_collection or
            args.gpu_counter_probe or args.runtime_package or args.scene):
        parser.error('--reclaim-payloads requires standalone inventory action')
    if args.retry_collection and (args.action != 'inventory' or args.gpu_counter_probe or
            not re.fullmatch(r'\d{8}T\d{12}Z-[0-9a-f]{6}', args.retry_collection)):
        parser.error('--retry-collection requires inventory and valid prior run ID without probe')
    counter_probe = args.gpu_counter_probe.read_bytes() if args.gpu_counter_probe else None
    if counter_probe is not None:
        counter_scene = (args.action == 'game' and args.scene and args.seed_session and
                         SCENES[args.scene].get('profile') is True and
                         not args.persistent_state and not args.import_session)
        if args.action != 'inventory' and not counter_scene:
            parser.error('--gpu-counter-probe requires inventory or isolated profiled seeded game scene')
        if (counter_probe[:6] != b'\x7fELF\x02\x01' or
                int.from_bytes(counter_probe[18:20], 'little') != 183):
            parser.error('Counter probe must be ELF64 little-endian AArch64')
    if args.runtime_package and args.action not in {'runtime', 'gles', 'game'} and args.play_action != 'install':
        parser.error('--runtime-package requires native runtime, graphics or game action')
    if args.performance_governors:
        domains = args.performance_governors.split(',')
        if (args.action != 'game' or not args.scene or not args.seed_session or
                len(set(domains)) != len(domains) or not set(domains) <= {'cpu', 'gpu', 'dmc'} or
                args.persistent_state or args.import_session):
            parser.error('--performance-governors requires isolated seeded game scene and cpu,gpu,dmc domains')
    if args.prime_program_cache and args.action != "game":
        parser.error("--prime-program-cache requires game action")
    primed_cache = None
    if args.prime_program_cache:
        try:
            if not 8 < args.prime_program_cache.stat().st_size <= 32 * 1024 * 1024:
                parser.error("Invalid compiled program cache size")
            primed_cache = args.prime_program_cache.read_bytes()
        except OSError:
            parser.error("Invalid compiled program cache file")
        if (int.from_bytes(primed_cache[:4], "little") != 0x53484231 or
                not 0 < int.from_bytes(primed_cache[4:8], "little") <= len(primed_cache) - 8):
            parser.error("Invalid compiled program cache header")
    if args.physical_profile:
        args.physical_controls = True
        if args.persistent_state or args.import_session:
            parser.error("--physical-profile uses isolated state; omit persistent/import options")
    if args.persistent_state:
        args.physical_controls = True
    if args.import_session and not args.persistent_state:
        parser.error("--import-session requires --persistent-state")
    if args.hash_data and args.action != "preflight" and args.play_action != 'inspect':
        parser.error("--hash-data requires preflight action")
    if args.physical_controls and (args.action != "game" or args.scene or args.seed_session):
        parser.error("--physical-controls requires game action without scene replay")
    if (args.scene or args.seed_session) and args.action != "game":
        parser.error("Scene replay requires game action")
    if args.seed_session and not args.scene:
        parser.error("--seed-session requires --scene")
    if args.scene and SCENES[args.scene]["seed"] and not args.seed_session:
        parser.error("Selected scene requires --seed-session")
    if args.seed_session:
        args.seed_session = args.seed_session.resolve()
        for name in ("savedata/data.001", "savedata/data.sys"):
            if not (args.seed_session / name).is_file():
                parser.error("Missing collected checkpoint files")
    imported = {}
    if args.import_session:
        args.import_session = args.import_session.resolve()
        names = ["sh3.ini", "sh3-progs.bin", "sh3-gl-cache.bin", "savedata/data.sys", "savedata/disp.ini", "savedata/key.ini"]
        names += [str(p.relative_to(args.import_session)) for p in
                  sorted((args.import_session / "savedata").glob("data.[0-9][0-9][0-9]"))]
        imported = {name: hashlib.sha256((args.import_session / name).read_bytes()).hexdigest()
                    for name in names if (args.import_session / name).is_file()}
        if "savedata/data.sys" not in imported or not any(re.fullmatch(r"savedata/data\.\d{3}", n) for n in imported):
            parser.error("Import requires collected save slot and data.sys")
    check_ignores()
    cfg = config()
    port = cfg.get("R36S_PORT", "")
    host = cfg.get("R36S_HOST", "")
    tcp = cfg.get("R36S_SSH_PORT") or "22"
    if port != "sh3":
        raise ValueError("R36S_PORT must match documented SH3 package folder: sh3")
    reclaim_plan = None
    reclaim_entries = []
    if args.reclaim_payloads:
        reclaim_plan = json.loads(args.reclaim_payloads.read_text())
        entries = reclaim_plan['files']
        if reclaim_plan.get('port') != port or not 0 < len(entries) <= 64:
            raise ValueError('Invalid retained payload plan')
        seen = set()
        for entry in entries:
            prefix = f'/roms2/ports/{port}/'
            path = entry['path']
            relative = path.removeprefix(prefix)
            if (not path.startswith(prefix) or path in seen or not re.fullmatch(
                    r'runs/\d{8}T\d{12}Z-[0-9a-f]{6}/payload/runtime/sh3', relative)):
                raise ValueError('Foreign or duplicate payload path')
            seen.add(path)
            retained = ROOT / entry['retained']
            if (not re.fullmatch(r'\.port-cache/builds/[^/]+/artifacts/runtime/sh3', entry['retained']) or
                    retained.resolve(strict=True) != retained or
                    hashlib.sha256(retained.read_bytes()).hexdigest() != entry['sha256'] or
                    retained.stat().st_size != entry['bytes']):
                raise ValueError('Retained immutable payload copy does not match')
            reclaim_entries.append({'path': relative, 'sha256': entry['sha256']})
    if not re.fullmatch(r"[A-Za-z0-9_.@-]+", host) or host.startswith("-"):
        raise ValueError("Invalid SSH destination in private config")
    if not tcp.isdigit() or not 1 <= int(tcp) <= 65535:
        raise ValueError("Invalid R36S_SSH_PORT")
    review = None
    if args.action in {"preflight", "runtime", "gles", "game"} or args.play_action == 'install':
        if not args.reviewed_helpers:
            raise ValueError("Run inventory and review helpers before preflight")
        review = (args.reviewed_helpers / "device" / "portmaster-files.sha256").read_bytes()
        if not review.strip():
            raise ValueError("Reviewed inventory has no PortMaster helpers")
    runtime_files = []
    if args.action in {"runtime", "gles", "game"} or args.play_action == 'install':
        package = args.runtime_package.resolve() if args.runtime_package else ROOT / "dist/runtime"
        binary = (package / "sh3").read_bytes()
        if binary[:6] != b"\x7fELF\x02\x01" or int.from_bytes(binary[18:20], "little") != 183:
            raise ValueError("Runtime must be ELF64 little-endian AArch64")
        build = json.loads((package / "build-inputs.json").read_text())
        selected = Path(cfg.get("SH3_GAME_DIR") or ROOT / "SILENT HILL 3") / "sh3.exe"
        if hashlib.sha1(selected.read_bytes()).hexdigest() != build["input_sha1"]:
            raise ValueError("Runtime generated from different owner input")
        runtime_files = ["sh3", "build-inputs.json", "packages.txt", "compiler.txt", "libc.txt",
                         "python.txt", "elf.txt", "readelf.txt", "artifacts.sha256"]
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ-") + uuid.uuid4().hex[:6]
    out = ROOT / "r36s-dumps" / port / run_id
    out.mkdir(parents=True)
    scene = scene_identity(args.scene, args.seed_session, package / 'sh3') if args.scene else None
    if scene:
        (out / "scene-identity.json").write_text(json.dumps(scene, indent=2) + "\n")
    remote = f"/roms2/ports/{port}/runs/{args.retry_collection or run_id}"
    remote_payload = remote + "/payload"
    statuses = {"run_id": run_id, "action": args.action, "execution": "not-attempted",
                "collection": "not-attempted"}
    if args.retry_collection:
        statuses['retry_collection_of'] = args.retry_collection
    if args.physical_controls:
        statuses["physical_controls"] = True
    if args.physical_profile:
        statuses["physical_profile"] = args.physical_profile
    if args.persistent_state:
        statuses["persistent_state"] = True
    if args.performance_governors:
        statuses['performance_governors'] = args.performance_governors
    if counter_probe is not None:
        statuses['gpu_counter_probe_sha256'] = hashlib.sha256(counter_probe).hexdigest()
    private = [v for k, v in cfg.items() if v and
               (k in {"R36S_HOST", "R36S_SSH_PASSWORD", "SH3_GAME_DIR"} or k.startswith("REFERENCE_"))]
    # SSH errors usually omit user@ prefix; redact endpoint components as well.
    private.append(host.rsplit("@", 1)[-1])
    private.sort(key=len, reverse=True)

    def scrub(data):
        for value in private:
            data = data.replace(value, "[private]")
        return data

    def save(name, data):
        (out / name).write_text(scrub(data))

    ssh_cache = ROOT / ".port-cache" / "ssh"
    ssh_cache.mkdir(parents=True, exist_ok=True)
    askpass = ROOT / "scripts/host/ssh-askpass.sh"
    askpass.chmod(0o700)
    env = {**os.environ, "SSH_ASKPASS": str(askpass), "SSH_ASKPASS_REQUIRE": "force",
           "DISPLAY": "sh3-askpass:0", "R36S_SSH_PASSWORD": cfg.get("R36S_SSH_PASSWORD", "")}
    options = ["-o", "StrictHostKeyChecking=accept-new", "-o", "ConnectTimeout=10",
               "-o", "NumberOfPasswordPrompts=1", "-o", "LogLevel=ERROR",
               "-o", f"UserKnownHostsFile={ssh_cache / 'known_hosts'}"]

    def command(name, argv, timeout=60, input_data=None):
        process = subprocess.Popen(argv, cwd=ROOT, env=env,
                                   stdin=subprocess.PIPE if input_data is not None else subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   start_new_session=True)
        try:
            stdout, stderr = process.communicate(input=input_data, timeout=timeout)
            code = process.returncode
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            stdout, stderr = process.communicate()
            code = 124
        save(name + ".stdout.txt", stdout.decode(errors="replace"))
        save(name + ".stderr.txt", stderr.decode(errors="replace"))
        statuses[name] = code
        return code

    def ssh(name, script, timeout=60, input_data=None):
        return command(name, ["ssh", *options, "-p", tcp, host, script], timeout, input_data)

    def collect_archive(name, suffix, destination):
        archive_path = out / (destination.name + '.evidence.tar.gz')
        code = command(name, ['scp', *options, '-P', tcp,
                             host + ':' + remote + suffix + '.evidence.tar.gz',
                             str(archive_path)], timeout=120)
        if code == 0:
            try:
                extract_evidence(archive_path, destination)
            except (ValueError, OSError, tarfile.TarError) as error:
                save(name + '.extract.stderr.txt', type(error).__name__ + ': ' + str(error) + '\n')
                code = 3
                statuses[name] = code
        return code

    identity = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in FILES}
    for name in ["scripts/host/r36s.py", "scripts/host/ssh-askpass.sh", "scripts/host/scenes.py"]:
        identity[name] = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    save("source-identity.json", json.dumps({"base_commit": commit, "files": identity}, indent=2) + "\n")
    if imported:
        save("import-identity.json", json.dumps({"files": imported}, indent=2) + "\n")
    if primed_cache is not None:
        save("program-cache-identity.json", json.dumps({"sha256": hashlib.sha256(primed_cache).hexdigest()}, indent=2) + "\n")
    data_root = Path(cfg.get("SH3_GAME_DIR") or ROOT / "SILENT HILL 3").expanduser()
    result = subprocess.run(["bash", str(ROOT / "scripts/device/check-data.sh"), str(data_root)],
                            capture_output=True, text=True,
                            env={**os.environ, "SH3_DATA_HASHES": "1" if args.hash_data else "0"})
    save("local-data.stdout.txt", result.stdout)
    save("local-data.stderr.txt", result.stderr)
    statuses["local-data"] = result.returncode
    if reclaim_plan is not None:
        save('reclaim-plan.json', json.dumps(reclaim_plan, indent=2) + '\n')
        capacity_command = shlex.join(['bash', '-s', '--', f'/roms2/ports/{port}'])
        capacity_source = (ROOT / 'scripts/device/capacity.sh').read_bytes()
        ssh('capacity', capacity_command, input_data=capacity_source)
        statuses['execution'] = ssh('reclaim', shlex.join([
            'python3', '-', f'/roms2/ports/{port}', json.dumps(reclaim_entries)]),
            input_data=(ROOT / 'scripts/device/reclaim-payloads.py').read_bytes())
        ssh('capacity-after', capacity_command, input_data=capacity_source)
        statuses['collection'] = 0  # All maintenance output streamed directly into host evidence.
        save('status.json', json.dumps(statuses, indent=2) + '\n')
        print('Evidence:', out.relative_to(ROOT))
        print('Payload reclamation:', statuses['execution'])
        return 0 if statuses['execution'] == 0 else 3
    if args.play_action:
        play_source = (ROOT / 'scripts/device/play-ready.py').read_bytes()
        play_args = ['python3', '-', f'/roms2/ports/{port}', args.play_action,
                     '1' if args.hash_data else '0']
        if args.play_action == 'install':
            stage = f'/roms2/ports/{port}/.play-install-{run_id}'
            code = ssh('play-prepare', shlex.join(['python3', '-', f'/roms2/ports/{port}', 'stage', run_id]),
                       input_data=play_source)
            with tempfile.TemporaryDirectory(prefix='sh3-play-', dir=ROOT / '.port-cache') as temporary:
                payload = Path(temporary) / 'payload'
                selected_files = ['ports/Silent Hill 3 Play.sh', 'ports/Silent Hill 3 Game.sh',
                                  'ports/Silent Hill 3.sh', 'ports/game-session.sh',
                                  'ports/restore-frontend.sh', 'ports/performance-governors.py',
                                  'scripts/device/check-data.sh', 'scripts/required-data.txt']
                for name in selected_files:
                    target = payload / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes((ROOT / name).read_bytes())
                (payload / 'runtime').mkdir()
                for name in ['sh3', 'build-inputs.json']:
                    (payload / 'runtime' / name).write_bytes((package / name).read_bytes())
                (payload / 'data.sys').write_bytes(args.play_settings.read_bytes())
                (payload / 'reviewed-helpers.sha256').write_bytes(review)
                manifest = {str(p.relative_to(payload)): hashlib.sha256(p.read_bytes()).hexdigest()
                            for p in payload.rglob('*') if p.is_file()}
                (payload / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
                save('play-install-identity.json', json.dumps(manifest, indent=2) + '\n')
                if code == 0:
                    code = command('play-deploy', ['scp', *options, '-P', tcp, '-r', str(payload),
                                                  host + ':' + stage + '/'], timeout=120)
                if code == 0:
                    play_args[-1] = stage + '/payload'
                    code = ssh('play', shlex.join(play_args), timeout=600, input_data=play_source)
            statuses['execution'] = code
        else:
            statuses['execution'] = ssh('play', shlex.join(play_args),
                timeout=600 if args.hash_data else 120, input_data=play_source)
        statuses['collection'] = 0  # Maintenance stdout/stderr streamed directly to host.
        save('status.json', json.dumps(statuses, indent=2) + '\n')
        print('Evidence:', out.relative_to(ROOT))
        print('Play maintenance:', args.play_action, statuses['execution'])
        return 0 if statuses['execution'] == 0 else 3
    # No original assets are deployed by this preflight-only workflow.
    try:
        with tempfile.TemporaryDirectory(prefix="sh3-payload-", dir=ROOT / ".port-cache") as temp:
            payload = Path(temp) / "payload"
            for name in FILES:
                dest = payload / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes((ROOT / name).read_bytes())
            if runtime_files:
                runtime = payload / "runtime"
                runtime.mkdir()
                for name in runtime_files:
                    (runtime / name).write_bytes((package / name).read_bytes())
            if counter_probe is not None:
                counters = payload / 'gpu-counter'
                counters.mkdir()
                (counters / 'api-example').write_bytes(counter_probe)
                (counters / 'api-example').chmod(0o755)
                (counters / 'SHA256SUMS').write_text(hashlib.sha256(counter_probe).hexdigest() + '  api-example\n')
            if review:
                (payload / "reviewed-helpers.sha256").write_bytes(review)
            if args.hash_data:
                (payload / "hash-data").touch()
            if args.physical_controls:
                (payload / "physical-controls").touch()
            if args.performance_governors:
                (payload / 'performance-governors').write_text(args.performance_governors + '\n')
            if args.physical_profile:
                (payload / "physical-profile").write_text(args.physical_profile + "\n")
            if args.persistent_state:
                (payload / "persistent-state").touch()
            if primed_cache is not None:
                cache = payload / "performance-cache/sh3-gl-cache.bin"
                cache.parent.mkdir()
                cache.write_bytes(primed_cache)
            for name in imported:
                dest = payload / "import-state" / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(args.import_session / name, dest)
            if scene:
                (payload / "scene-plan.json").write_text(json.dumps(scene["plan"], indent=2) + "\n")
                if args.seed_session:
                    for name in scene["seed_sha256"]:
                        dest = payload / "scene-seed" / name
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        dest.write_bytes((args.seed_session / name).read_bytes())
            if args.retry_collection:
                statuses['execution'] = 'collection-only'
            else:
                capacity_path = f"/roms2/ports/{port}"
                ssh('capacity', shlex.join(['bash', '-s', '--', capacity_path]),
                    input_data=(ROOT / 'scripts/device/capacity.sh').read_bytes())
                code = ssh("prepare", "mkdir -p " + shlex.quote(f"/roms2/ports/{port}/runs") +
                           " && mkdir " + shlex.quote(remote))
                if code == 0:
                    code = command("deploy", ["scp", *options, "-P", tcp, "-r", str(payload),
                                              host + ":" + remote + "/"], timeout=120)
                if code == 0:
                    script = shlex.join(["bash", remote_payload + "/scripts/device/run.sh",
                                         args.action, f"/roms2/ports/{port}", run_id, remote_payload])
                    execution_limit = 600 if args.hash_data else 280 if args.action == "game" else 120
                    if scene:
                        execution_limit = scene["plan"]["seconds"] + 180
                    if args.physical_controls:
                        execution_limit = 1080
                    statuses["execution"] = ssh("execute", script, timeout=execution_limit)
                else:
                    statuses["execution"] = "deployment-failed"
    finally:
        # Always attempt collection, including after preparation/deployment/execution failure.
        if args.retry_collection:
            statuses["collection"] = command(
                "collect", ["scp", *options, "-P", tcp, "-r", host + ":" + remote + "/",
                            str(out / "device")], timeout=300)
        else:
            statuses['collection-format'] = 'tar.gz-v1'
            statuses["collection"] = collect_archive('collect', '', out / 'device')
        if args.action in {"preflight", "runtime", "gles", "game"}:
            statuses["launcher-collection"] = collect_archive('collect-launcher', '-launch', out / 'launcher')
        if args.action == "game":
            statuses["service-collection"] = collect_archive('collect-service', '-launch-service', out / 'service')
        if scene:
            scene["source_preserved"] = not args.seed_session or seed_hashes(args.seed_session) == scene["seed_sha256"]
            (out / "scene-identity.json").write_text(json.dumps(scene, indent=2) + "\n")
            statuses["source-preserved"] = scene["source_preserved"]
        if imported:
            statuses["source-preserved"] = all((args.import_session / name).is_file() and
                hashlib.sha256((args.import_session / name).read_bytes()).hexdigest() == digest
                for name, digest in imported.items())
        if primed_cache is not None:
            statuses["program-cache-source-preserved"] = (args.prime_program_cache.is_file() and
                hashlib.sha256(args.prime_program_cache.read_bytes()).digest() == hashlib.sha256(primed_cache).digest())
            statuses["source-preserved"] = (statuses.get("source-preserved", True) and
                                             statuses["program-cache-source-preserved"])
        save("status.json", json.dumps(statuses, indent=2) + "\n")
    print("Evidence:", out.relative_to(ROOT))
    print("Local data:", statuses["local-data"], "Execution:", statuses["execution"],
          "Collection:", statuses["collection"])
    return 0 if (statuses["execution"] in (0, 'collection-only') and statuses["collection"] == 0 and
                 statuses.get("launcher-collection", 0) == 0 and
                 statuses.get("service-collection", 0) == 0 and
                 statuses.get("source-preserved", True)) else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ValueError as error:
        print("Workflow configuration:", str(error), file=sys.stderr)
        sys.exit(3)
    except OSError as error:
        # Configuration errors do not echo raw values or command lines.
        print("Workflow failed:", type(error).__name__, file=sys.stderr)
        sys.exit(3)
