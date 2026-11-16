"""Installed game menu lifecycle; service manager is external fixture boundary."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import unittest
from unittest.mock import patch

from test_preflight import LauncherFixture, REPO


OWNER = Path(os.environ.get("SH3_GAME_DATA", REPO / "SILENT HILL 3"))


@unittest.skipUnless((OWNER / "sh3.exe").is_file(), "requires original owner game data")
@unittest.skipUnless(Path("/proc/self/cgroup").is_file(), "requires Linux session boundary")
class FrontendSessionTests(LauncherFixture):
    def setUp(self):
        super().setUp()
        for name in ["sh3.exe", "data"]:
            (self.data / name).symlink_to(OWNER / name, target_is_directory=name == "data")
        installed = self.port / "preflight/ports"
        installed.mkdir(parents=True)
        for name in ["Silent Hill 3.sh", "Silent Hill 3 Game.sh", "game-session.sh", "restore-frontend.sh", "performance-governors.py"]:
            source = REPO / "ports" / name
            if source.exists():
                shutil.copyfile(source, installed / name)
        self.menu = self.root / "Silent Hill 3 Game.sh"
        shutil.copyfile(REPO / "ports/Silent Hill 3 Game.sh", self.menu)
        self.commands = self.root / "bin"
        self.commands.mkdir()
        self.state = self.root / "frontend-state"
        self.state.write_text("active")
        self.trace = self.root / "service-trace"
        self.write_command("systemctl", '''#!/usr/bin/env python3
from pathlib import Path
import sys
root = Path(__file__).resolve().parent.parent
state = root / 'frontend-state'
action = sys.argv[1]
if action == 'is-active':
    sys.exit(0 if state.read_text() == 'active' else 3)
if action in ['stop', 'start']:
    with (root / 'service-trace').open('a') as trace: trace.write(action + '\\n')
    state.write_text('inactive' if action == 'stop' else 'active')
''')
        self.write_command("pgrep", '''#!/bin/sh
root="$(dirname "$(dirname "$0")")"
[ "$(cat "$root/frontend-state")" = active ] && { echo 123; exit 0; }
exit 1
''')
        self.write_command("sudo", '#!/bin/sh\n[ "$1" = -n ] && shift\nexec "$@"\n')
        self.write_command("systemd-run", '''#!/usr/bin/env python3
import json, os, shlex, signal, subprocess, sys, time
from pathlib import Path
root = Path(__file__).resolve().parent.parent
args = sys.argv[1:]
(root / 'unit-request.json').write_text(json.dumps(args))
env = {}
for arg in args:
    if arg.startswith('--setenv='):
        key, value = arg[len('--setenv='):].split('=', 1)
        env[key] = value
command = args[args.index('/bin/bash'):]
if (root / 'crash-service').exists():
    child = subprocess.Popen(command, env=env, start_new_session=True)
    for attempt in range(200):
        if (root / 'service-trace').exists() and 'runtime' in (root / 'service-trace').read_text(): break
        time.sleep(0.01)
    os.killpg(child.pid, signal.SIGKILL)
    status = child.wait()
else:
    scale_path = root / 'watchdog-clock-scale'
    if scale_path.exists():
        limit = next(arg.split('=', 2)[2] for arg in args if arg.startswith('--property=RuntimeMaxSec='))
        child = subprocess.Popen(command, env=env, start_new_session=True)
        try:
            status = child.wait(timeout=float(limit) * float(scale_path.read_text()))
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            child.wait()
            status = 124
    else:
        status = subprocess.run(command, env=env).returncode
recovery = next(arg.split('=', 2)[2] for arg in args if arg.startswith('--property=ExecStopPost='))
restored = subprocess.run(shlex.split(recovery.lstrip('+')), env=env).returncode
sys.exit((128 - status if status < 0 else status) or restored)
''')
        runtime = self.port / "runtime/sh3"
        runtime.parent.mkdir()
        runtime.write_text('''#!/bin/sh
root="$(dirname "$(dirname "$(dirname "$0")")")"
[ "$(cat "$root/frontend-state")" = inactive ] || exit 9
printf 'runtime\\n' >> "$root/service-trace"
exit 7
''')
        runtime.chmod(0o755)

    def write_command(self, name, contents):
        path = self.commands / name
        path.write_text(contents)
        path.chmod(0o755)

    def launch_menu(self):
        return subprocess.run(["bash", str(self.menu)], cwd="/", capture_output=True, text=True,
                              timeout=20, env={**os.environ,
                                  "PATH": f"{self.commands}:{os.environ['PATH']}",
                                  "XDG_DATA_HOME": str(self.root / "xdg"),
                                  "SH3_PACKAGE_DIR": str(REPO), "SH3_RUN_ID": "service-fixture",
                                  "SH3_SERVICE_WAIT": "1"})

    def test_game_runs_outside_frontend_service_and_failure_restores_frontend(self):
        result = self.launch_menu()
        self.assertEqual(result.returncode, 7, result.stdout + result.stderr)
        self.assertEqual(self.trace.read_text().splitlines(), ["stop", "runtime", "start"])
        self.assertEqual(self.state.read_text(), "active")
        self.assertEqual(self.save.read_bytes(), b"owner save remains unchanged")
        request = json.loads((self.root / "unit-request.json").read_text())
        self.assertIn("--unit=sh3-r36s-game", request)
        self.assertTrue(any("ExecStopPost=" in arg for arg in request), "crash recovery required")
        self.assertFalse(list(self.port.glob("runs/*/frontend-stopped")))

    def power_fixture(self):
        root = self.root / 'sys'
        entries = []
        for directory, governor, minimum, maximum, cpu in [
                ('devices/system/cpu/cpufreq/policy0', 'ondemand', 1008000, 1512000, True),
                ('class/devfreq/ff400000.gpu', 'simple_ondemand', 400000000, 520000000, False),
                ('class/devfreq/dmc', 'dmc_ondemand', 528000000, 786000000, False)]:
            path = root / directory
            path.mkdir(parents=True)
            prefix = 'scaling_' if cpu else ''
            for name, value in {prefix + 'governor': governor,
                                prefix + 'min_freq': minimum, prefix + 'max_freq': maximum,
                                prefix + 'available_governors': governor + ' performance',
                                prefix + 'available_frequencies': f'{minimum} {maximum}'}.items():
                (path / name).write_text(str(value) + '\n')
            if cpu:
                (path / 'cpuinfo_min_freq').write_text(str(minimum) + '\n')
                (path / 'cpuinfo_max_freq').write_text(str(maximum) + '\n')
            entries.append((path / (prefix + 'governor'), governor + '\n'))
        return root, entries

    def test_opt_in_stock_policies_apply_only_for_game_and_restore_after_runtime_failure(self):
        sysfs, entries = self.power_fixture()
        original = {p: p.read_bytes() for p in sysfs.rglob('*') if p.is_file()}
        runtime = self.port / 'runtime/sh3'
        runtime.write_text('#!/bin/sh\ncat ' + ' '.join(str(path) for path, _ in entries) + '\nexit 7\n')
        with patch.dict(os.environ, {'SH3_PERFORMANCE_GOVERNORS': 'cpu,gpu,dmc', 'SH3_SYSFS_ROOT': str(sysfs)}):
            result = self.launch_menu()
        self.assertEqual(result.returncode, 7, result.stdout + result.stderr)
        self.assertIn('performance\n' * 3, (self.port / 'runs/service-fixture/stdout.txt').read_text())
        self.assertEqual({p: p.read_bytes() for p in original}, original)
        self.assertEqual(self.state.read_text(), 'active')
        report = json.loads((self.port / 'runs/service-fixture-service/power-restore.json').read_text())
        self.assertEqual(report['status'], 'restored')

    def test_default_launch_preserves_policies_without_creating_recovery_owner(self):
        sysfs, entries = self.power_fixture()
        original = {p: p.read_bytes() for p in sysfs.rglob('*') if p.is_file()}
        with patch.dict(os.environ, {'SH3_SYSFS_ROOT': str(sysfs)}):
            result = self.launch_menu()
        self.assertEqual(result.returncode, 7, result.stdout + result.stderr)
        self.assertEqual({p: p.read_bytes() for p in original}, original)
        self.assertFalse((self.port / '.performance-policy-owner.json').exists())
        self.assertFalse((self.port / 'runs/service-fixture-service/power-applied.json').exists())

    def test_unsupported_domain_rejects_all_changes_and_returns_frontend_before_game(self):
        sysfs, entries = self.power_fixture()
        (entries[-1][0].parent / 'available_governors').write_text('dmc_ondemand\n')
        original = {p: p.read_bytes() for p in sysfs.rglob('*') if p.is_file()}
        with patch.dict(os.environ, {'SH3_PERFORMANCE_GOVERNORS': 'cpu,gpu,dmc', 'SH3_SYSFS_ROOT': str(sysfs)}):
            result = self.launch_menu()
        self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
        self.assertEqual(self.trace.read_text().splitlines(), ['stop', 'start'])
        self.assertEqual({p: p.read_bytes() for p in original}, original)
        self.assertEqual(self.state.read_text(), 'active')

    @unittest.skipIf(os.geteuid() == 0, 'read-only sysfs fixture needs unprivileged Docker user')
    def test_partial_policy_write_failure_rolls_back_prior_domain_before_frontend(self):
        sysfs, entries = self.power_fixture()
        original = {p: p.read_bytes() for p in sysfs.rglob('*') if p.is_file()}
        entries[1][0].chmod(0o444)
        with patch.dict(os.environ, {'SH3_PERFORMANCE_GOVERNORS': 'cpu,gpu,dmc', 'SH3_SYSFS_ROOT': str(sysfs)}):
            result = self.launch_menu()
        self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
        self.assertEqual({p: p.read_bytes() for p in original}, original)
        self.assertEqual(self.trace.read_text().splitlines(), ['stop', 'start'])
        report = json.loads((self.port / 'runs/service-fixture-service/power-restore.json').read_text())
        self.assertEqual(report['status'], 'restored')
        self.assertFalse((self.port / '.performance-policy-owner.json').exists())

    def test_independent_stop_post_restores_policies_when_session_is_killed(self):
        sysfs, entries = self.power_fixture()
        original = {p: p.read_bytes() for p in sysfs.rglob('*') if p.is_file()}
        (self.root / 'crash-service').touch()
        runtime = self.port / 'runtime/sh3'
        runtime.write_text(runtime.read_text().replace('exit 7', 'sleep 30'))
        with patch.dict(os.environ, {'SH3_PERFORMANCE_GOVERNORS': 'cpu,gpu,dmc', 'SH3_SYSFS_ROOT': str(sysfs)}):
            result = self.launch_menu()
        self.assertEqual(result.returncode, 137, result.stdout + result.stderr)
        self.assertEqual({p: p.read_bytes() for p in original}, original)
        self.assertEqual(self.state.read_text(), 'active')
        self.assertEqual(json.loads((self.port / 'runs/service-fixture-service/power-restore.json').read_text())['status'],
                         'restored')

    def test_external_policy_change_is_reported_and_preserved_during_frontend_recovery(self):
        sysfs, entries = self.power_fixture()
        runtime = self.port / 'runtime/sh3'
        runtime.write_text('#!/bin/sh\nprintf "powersave\\n" > ' + str(entries[1][0]) + '\nexit 0\n')
        with patch.dict(os.environ, {'SH3_PERFORMANCE_GOVERNORS': 'cpu,gpu,dmc', 'SH3_SYSFS_ROOT': str(sysfs)}):
            result = self.launch_menu()
        self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
        self.assertEqual(entries[0][0].read_text(), entries[0][1])
        self.assertEqual(entries[1][0].read_text(), 'powersave\n')
        self.assertEqual(entries[2][0].read_text(), entries[2][1])
        self.assertEqual(self.state.read_text(), 'active')
        self.assertEqual(json.loads((self.port / 'runs/service-fixture-service/power-restore.json').read_text())['status'],
                         'conflict')

    def test_existing_policy_owner_blocks_second_session_and_keeps_its_journal(self):
        sysfs, entries = self.power_fixture()
        journal = self.port / '.performance-policy-owner.json'
        original = json.dumps({'run': 'different-session',
                               'boot': Path('/proc/sys/kernel/random/boot_id').read_text().strip(), 'changed': []})
        journal.write_text(original)
        with patch.dict(os.environ, {'SH3_PERFORMANCE_GOVERNORS': 'cpu,gpu,dmc', 'SH3_SYSFS_ROOT': str(sysfs)}):
            result = self.launch_menu()
        self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
        self.assertEqual(journal.read_text(), original)
        self.assertEqual([path.read_text() for path, value in entries], [value for path, value in entries])
        self.assertEqual(self.state.read_text(), 'active')

    def test_performance_menu_selects_measured_graphics_and_keeps_player_progress(self):
        self.menu = self.root / "Silent Hill 3 Performance.sh"
        source = REPO / "ports/Silent Hill 3 Performance.sh"
        if source.is_file():
            shutil.copyfile(source, self.menu)
        savedata = self.port / "state/savedata"
        savedata.mkdir(parents=True)
        (savedata / "data.001").write_bytes(b"player progress")
        (savedata / "data.sys").write_bytes(b"player index")
        (savedata / "disp.ini").write_text(
            "resolution=640x480\nshadow=0\nlensflare_ztest=0\ngamma_r=0.85\nsize=640x480\n")
        (savedata / "key.ini").write_bytes(b"player controls")
        runtime = self.port / "runtime/sh3"
        runtime.write_text('''#!/bin/sh
printf 'limit=%s output=%s keys=%s deadline=%s\\n' "$SH3_FPS_LIMIT" "$SH3_OUTPUT_RESOLUTION" "${SH3_KEYS:-}" "${SH3_QUIT_AFTER:-}"
cat savedata/data.001 savedata/disp.ini
exit 7
''')
        result = self.launch_menu()
        self.assertEqual(result.returncode, 7, result.stdout + result.stderr)
        log = (self.port / "runs/service-fixture/stdout.txt").read_text()
        self.assertIn("limit=30 output=640x480 keys= deadline=\n", log)
        self.assertIn("player progress", log)
        self.assertIn("resolution=320x240\n", log)
        self.assertIn("shadow=1\n", log)
        self.assertIn("lensflare_ztest=1\n", log)
        self.assertIn("gamma_r=0.85\n", log)
        self.assertIn("size=640x480\n", log)
        self.assertNotIn("shadow=0\n", log)
        self.assertNotIn("lensflare_ztest=0\n", log)
        self.assertEqual((savedata / "data.001").read_bytes(), b"player progress")
        self.assertEqual((savedata / "data.sys").read_bytes(), b"player index")
        self.assertEqual((savedata / "key.ini").read_bytes(), b"player controls")
        self.assertEqual(self.state.read_text(), "active")
        request = json.loads((self.root / "unit-request.json").read_text())
        self.assertFalse(any(arg.startswith("--property=RuntimeMaxSec=") for arg in request))

    def test_quiet_play_also_restores_policies_when_sudo_filters_environment(self):
        self.write_command('id', '#!/bin/sh\n[ "$1" = -u ] && { echo 1000; exit; }\nexec /usr/bin/id "$@"\n')
        self.write_command('sudo', '#!/bin/sh\n[ "$1" = -n ] && shift\nunset SH3_DIAGNOSTICS\nexec "$@"\n')
        self.test_play_menu_is_quiet_without_replays_and_restores_frontend_and_stock_policies()

    def test_play_menu_is_quiet_without_replays_and_restores_frontend_and_stock_policies(self):
        source = REPO / 'ports/Silent Hill 3 Play.sh'
        if source.exists():
            self.menu = self.root / source.name
            shutil.copyfile(source, self.menu)
        sysfs, _ = self.power_fixture()
        original = {p: p.read_bytes() for p in sysfs.rglob('*') if p.is_file()}
        savedata = self.port / 'state/savedata'
        savedata.mkdir(parents=True)
        (savedata / 'data.001').write_bytes(b'new player progress')
        (savedata / 'key.ini').write_bytes(b'player controls')
        (self.port / 'state/sh3-gl-cache.bin').write_bytes(b'warm shaders')
        observed = self.root / 'game-environment.json'
        runtime = self.port / 'runtime/sh3'
        runtime.write_text('#!/usr/bin/env python3\nimport json, os\nfrom pathlib import Path\n'
                           f'Path({str(observed)!r}).write_text(json.dumps(dict(os.environ)))\n'
                           "print('runtime diagnostic')\nraise SystemExit(7)\n")
        with patch.dict(os.environ, {'SH3_SYSFS_ROOT': str(sysfs), 'SH3_KEYS': '1:RETURN',
                                    'SH3_MONITOR': '1', 'SH3_PROFILE': '1', 'SH3_STATS': '1',
                                    'SH3_INPUT_LOG': '1', 'SH3_QUIT_AFTER': '1'}):
            result = self.launch_menu()
        self.assertEqual(result.returncode, 7, result.stdout + result.stderr)
        self.assertEqual(self.state.read_text(), 'active')
        self.assertEqual({p: p.read_bytes() for p in original}, original)
        self.assertEqual((savedata / 'data.001').read_bytes(), b'new player progress')
        self.assertEqual((savedata / 'key.ini').read_bytes(), b'player controls')
        self.assertEqual((self.port / 'state/sh3-gl-cache.bin').read_bytes(), b'warm shaders')
        self.assertFalse((self.port / 'runs').exists(), 'ordinary play must not record runs or snapshots')
        self.assertFalse((self.port / '.performance-policy-owner.json').exists())
        env = json.loads(observed.read_text())
        self.assertEqual(env.get('SH3_QUIET'), '1')
        self.assertEqual(env.get('SH3_DIRECT_PLAY'), '1')
        self.assertEqual(env.get('SH3_FPS_LIMIT'), '30')
        self.assertEqual(env.get('SH3_INTERNAL_RESOLUTION'), '320x240')
        self.assertEqual(env.get('SH3_OUTPUT_RESOLUTION'), '640x480')
        for key in ['SH3_KEYS', 'SH3_MONITOR', 'SH3_PROFILE', 'SH3_STATS', 'SH3_INPUT_LOG', 'SH3_QUIT_AFTER']:
            self.assertNotIn(key, env, key)
        self.assertFalse(Path(env['SH3_CONTROL_DIR']).exists(), 'transient recovery state must be removed')
        request = json.loads((self.root / 'unit-request.json').read_text())
        self.assertIn('--property=StandardOutput=null', request)
        self.assertIn('--property=StandardError=null', request)
        self.assertFalse(any(arg.startswith('--property=RuntimeMaxSec=') for arg in request))

    def test_saved_persistent_workflow_imports_player_slots_instead_of_diagnostic_seed(self):
        payload = self.root / "payload"
        (payload / "runtime").mkdir(parents=True)
        (payload / "ports").mkdir()
        source = payload / "import-state/savedata"
        source.mkdir(parents=True)
        (source / "data.001").write_bytes(b"player first slot")
        (source / "data.002").write_bytes(b"player second slot")
        (source / "data.sys").write_bytes(b"player index")
        (payload / "persistent-state").touch()
        (payload / "physical-controls").touch()
        shutil.copyfile(REPO / "ports/Silent Hill 3 Game.sh", payload / "ports/Silent Hill 3 Game.sh")
        shutil.copyfile(REPO / "ports/Silent Hill 3 Performance.sh", payload / "ports/Silent Hill 3 Performance.sh")
        runtime = payload / "runtime/sh3"
        runtime.write_text('#!/bin/sh\ncat savedata/data.002\nexit 7\n')
        (payload / "runtime/artifacts.sha256").write_text(hashlib.sha256(runtime.read_bytes()).hexdigest() + '  sh3\n')
        (self.port / "runtime/.sh3-runtime-owned").touch()
        previous = self.port / "runs/old/session/savedata"
        previous.mkdir(parents=True)
        (previous / "data.001").write_bytes(b"diagnostic checkpoint")
        (previous / "data.sys").write_bytes(b"diagnostic index")
        (previous.parent.parent / "exit-status.txt").write_text("0\n")
        for name in ["readelf", "ldd"]:
            self.write_command(name, '#!/bin/sh\nexit 0\n')
        pgrep = self.commands / "pgrep"
        pgrep.write_text(pgrep.read_text().replace('root=', '[ "$2" = sh3 ] && exit 1\nroot=', 1))
        run = self.port / "runs/deploy"
        run.mkdir(parents=True)
        result = subprocess.run(["bash", str(REPO / "scripts/device/runtime.sh"), str(self.port),
                                 "deploy", str(payload), str(run), "game"],
                                capture_output=True, text=True, timeout=20,
                                env={**os.environ, "PATH": f"{self.commands}:{os.environ['PATH']}",
                                     "XDG_DATA_HOME": str(self.root / "xdg"), "SH3_PACKAGE_DIR": str(REPO)})
        self.assertEqual(result.returncode, 7, result.stdout + result.stderr)
        self.assertIn("player second slot", (self.port / "runs/deploy-launch/stdout.txt").read_text())
        self.assertEqual((self.port / "state/savedata/data.002").read_bytes(), b"player second slot")
        self.assertEqual((source / "data.001").read_bytes(), b"player first slot")
        self.assertEqual((previous / "data.001").read_bytes(), b"diagnostic checkpoint")
        self.assertEqual(self.state.read_text(), "active")

    def test_previously_inactive_frontend_is_left_inactive(self):
        self.state.write_text("inactive")
        result = self.launch_menu()
        self.assertEqual(result.returncode, 7, result.stdout + result.stderr)
        self.assertEqual(self.trace.read_text().splitlines(), ["runtime"])
        self.assertEqual(self.state.read_text(), "inactive")

    def test_explicit_game_deadline_also_bounds_waiting_at_launcher(self):
        with patch.dict(os.environ, {"SH3_QUIT_AFTER": "900"}):
            result = self.launch_menu()
        self.assertEqual(result.returncode, 7, result.stdout + result.stderr)
        request = json.loads((self.root / "unit-request.json").read_text())
        self.assertIn("--property=RuntimeMaxSec=990", request)
        self.assertEqual(self.state.read_text(), "active")

    def test_delayed_startup_leaves_full_game_interval_and_profile_flush_before_watchdog(self):
        # External service fixture runs its clock at 50x speed. Thirty-five seconds
        # of initialization reproduces the collected startup exceeding old margin.
        (self.root / "watchdog-clock-scale").write_text("0.02")
        runtime = self.port / "runtime/sh3"
        runtime.write_text('''#!/usr/bin/env python3
import os, time
from pathlib import Path
time.sleep(35 * 0.02)
time.sleep(int(os.environ['SH3_QUIT_AFTER']) * 0.02)
Path(os.environ['SH3_PROFILE']).write_text('complete game interval; profile flushed\\n')
''')
        report = self.root / "frame-times.csv.samples"
        with patch.dict(os.environ, {"SH3_QUIT_AFTER": "1", "SH3_PROFILE": str(report)}):
            result = self.launch_menu()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(report.read_text(), "complete game interval; profile flushed\n")
        self.assertEqual(self.state.read_text(), "active")

    def run_timing_scene(self, frame_profile=False, scene_name=None, fps_limit=None,
                         compiled_cache=False, prime_cache=None, gpu_profile=None,
                         expected_status=7, swap_interval=None, counter_probe=False, gl_trace=None,
                         gl_drain=None, gl_trace_coarse=None):
        payload = self.root / "payload"
        (payload / "runtime").mkdir(parents=True)
        (payload / "ports").mkdir()
        seed = payload / "scene-seed/savedata"
        seed.mkdir(parents=True)
        (seed / "data.001").write_bytes(b"timing checkpoint")
        (seed / "data.sys").write_bytes(b"checkpoint index")
        if prime_cache is not None:
            cache = payload / 'performance-cache/sh3-gl-cache.bin'
            cache.parent.mkdir()
            cache.write_bytes(prime_cache)
        if compiled_cache:
            (seed.parent / "sh3-gl-cache.bin").write_bytes(b"compiled checkpoint programs")
        if counter_probe:
            (payload / 'gpu-counter').mkdir()
            (payload / 'gpu-counter/api-example').touch()
            scripts = payload / 'scripts/device'
            scripts.mkdir(parents=True)
            (scripts / 'gpu-counter-session.py').write_text(
                'import os,sys,time\nfrom pathlib import Path\n'
                'out=Path(sys.argv[1]); out.mkdir(exist_ok=True)\n'
                '(out/"offsets.json").write_text(__import__("json").dumps(sys.argv[2:]))\n'
                '(out/"counter.pid").write_text(str(os.getpid()))\n'
                'while True: time.sleep(.1)\n')
        plan = {
            "keys": "", "seconds": 900, "capture_every": 0,
            "peek": "72C7F0,70E66F4", "internal_resolution": "320x240", "profile": frame_profile}
        if scene_name:
            plan = json.loads((REPO / "scripts/scenes.json").read_text())[scene_name]
        if fps_limit is not None:
            plan["fps_limit"] = fps_limit
        if gpu_profile is not None:
            plan["gpu_profile"] = gpu_profile
        if swap_interval is not None:
            plan['swap_interval'] = swap_interval
        if gl_trace is not None:
            plan['gl_trace'] = gl_trace
        if gl_drain is not None:
            plan['gl_drain'] = gl_drain
        if gl_trace_coarse is not None:
            plan['gl_trace_coarse'] = gl_trace_coarse
        (payload / "scene-plan.json").write_text(json.dumps(plan))
        shutil.copyfile(REPO / "ports/Silent Hill 3 Game.sh", payload / "ports/Silent Hill 3 Game.sh")
        shutil.copyfile(REPO / "ports/Silent Hill 3 Performance.sh", payload / "ports/Silent Hill 3 Performance.sh")
        runtime = payload / "runtime/sh3"
        runtime.write_text('''#!/bin/sh
cat savedata/disp.ini
printf 'capture=%s keys=%s peek=%s\n' "${SH3_SHOT+set}" "$SH3_KEYS" "$SH3_PEEK"
printf 'fps_limit=%s\n' "$SH3_FPS_LIMIT"
printf 'gpu_profile=%s\n' "${SH3_GPU_PROFILE:-}"
printf 'swap_interval=%s\n' "${SH3_SWAP_INTERVAL-unset}"
printf 'gl_trace=%s\n' "${SH3_GL_TRACE-unset}"
printf 'gl_drain=%s\n' "${SH3_GL_DRAIN-unset}"
printf 'gl_trace_coarse=%s\n' "${SH3_GL_TRACE_COARSE-unset}"
if [ -f sh3-gl-cache.bin ]; then cat sh3-gl-cache.bin; fi
if [ -n "${SH3_PROFILE:-}" ]; then printf 'frame,wall_ms\n1,33.33\n' > "$SH3_PROFILE"; fi
exit 7
''')
        if counter_probe:
            runtime.write_text(runtime.read_text().replace('exit 7\n',
                'attempt=0\nwhile [ ! -f "$SH3_PORT_ROOT/runs/${SH3_RUN_ID}-service/counters/counter.pid" ] && '
                '[ "$attempt" -lt 100 ]; do sleep .01; attempt=$((attempt + 1)); done\nexit 7\n'))
        (payload / "runtime/artifacts.sha256").write_text(hashlib.sha256(runtime.read_bytes()).hexdigest() + '  sh3\n')
        (self.port / "runtime/.sh3-runtime-owned").touch()
        for name in ["readelf", "ldd"]:
            self.write_command(name, '#!/bin/sh\nexit 0\n')
        pgrep = self.commands / "pgrep"
        pgrep.write_text(pgrep.read_text().replace('root=', '[ "$2" = sh3 ] && exit 1\nroot=', 1))
        run = self.port / "runs/deploy"
        run.mkdir(parents=True)
        result = subprocess.run(["bash", str(REPO / "scripts/device/runtime.sh"), str(self.port),
                                 "deploy", str(payload), str(run), "game"],
                                capture_output=True, text=True, timeout=20,
                                env={**os.environ, "PATH": f"{self.commands}:{os.environ['PATH']}",
                                     "XDG_DATA_HOME": str(self.root / "xdg"), "SH3_PACKAGE_DIR": str(REPO)})
        self.assertEqual(result.returncode, expected_status, result.stdout + result.stderr)
        if expected_status != 7:
            return result
        log = (self.port / "runs/deploy-launch/stdout.txt").read_text()
        self.assertIn("resolution=" + plan['internal_resolution'] + "\n", log)
        self.assertIn("capture= keys=" + plan['keys'] + " peek=" + plan['peek'] + "\n", log)
        if fps_limit is not None:
            self.assertIn(f"fps_limit={fps_limit}\n", log)
        if compiled_cache:
            self.assertIn('compiled checkpoint programs', log)
            self.assertEqual((seed.parent / 'sh3-gl-cache.bin').read_bytes(), b'compiled checkpoint programs')
        self.assertEqual((seed / "data.001").read_bytes(), b"timing checkpoint")
        self.assertEqual(self.state.read_text(), "active")
        return self.port / "runs/deploy-launch/frame-times.csv"

    def test_timing_scene_keeps_requested_profile_without_frame_capture(self):
        with patch.dict(os.environ, {'SH3_GPU_PROFILE': '1'}):
            report = self.run_timing_scene()
        self.assertFalse(report.exists(), "ordinary timing plan unexpectedly enabled profiling")
        observed = [line for line in (report.parent / 'stdout.txt').read_text().splitlines()
                    if line.startswith('gpu_profile=')]
        self.assertEqual(observed, ['gpu_profile=0'])

    def test_profile_scene_collects_detached_report_without_frame_capture(self):
        report = self.run_timing_scene(frame_profile=True)
        self.assertTrue(report.is_file(), "profile scene did not retain runtime report in collected launch")
        self.assertEqual(report.read_text(), "frame,wall_ms\n1,33.33\n")

    def test_requested_thirty_fps_scene_reaches_detached_runtime(self):
        self.run_timing_scene(frame_profile=True, fps_limit=30)

    def test_query_diagnostic_scene_reaches_detached_runtime(self):
        report = self.run_timing_scene(frame_profile=True, fps_limit=30, gpu_profile=True)
        observed = [line for line in (report.parent / 'stdout.txt').read_text().splitlines()
                    if line.startswith('gpu_profile=')]
        self.assertEqual(observed, ['gpu_profile=1'])

    def test_swap_diagnostic_scene_reaches_detached_runtime(self):
        report = self.run_timing_scene(frame_profile=True, fps_limit=30, swap_interval=0)
        observed = [line for line in (report.parent / 'stdout.txt').read_text().splitlines()
                    if line.startswith('swap_interval=')]
        self.assertEqual(observed, ['swap_interval=0'])

    def test_gl_trace_scene_reaches_detached_runtime_only_when_explicit(self):
        report = self.run_timing_scene(frame_profile=True, gl_trace=True)
        observed = [line for line in (report.parent / 'stdout.txt').read_text().splitlines()
                    if line.startswith('gl_trace=')]
        self.assertEqual(observed, ['gl_trace=1'])
        self.assertEqual(self.state.read_text(), 'active')

    def test_coarse_gl_trace_reaches_detached_runtime_when_explicit(self):
        report = self.run_timing_scene(frame_profile=True, gl_trace=True, gl_trace_coarse=True)
        observed = [line for line in (report.parent / 'stdout.txt').read_text().splitlines()
                    if line.startswith(('gl_trace=', 'gl_trace_coarse='))]
        self.assertEqual(observed, ['gl_trace=1', 'gl_trace_coarse=1'])
        self.assertEqual(self.state.read_text(), 'active')

    def test_coarse_gl_trace_rejects_non_boolean_before_starting_game(self):
        result = self.run_timing_scene(frame_profile=True, gl_trace=True,
                                       gl_trace_coarse='1', expected_status=1)
        self.assertIn('Invalid coarse GL trace', result.stderr)
        self.assertFalse((self.root / 'unit-request.json').exists())
        self.assertEqual(self.state.read_text(), 'active')

    def test_coarse_gl_trace_requires_trace_before_starting_game(self):
        result = self.run_timing_scene(frame_profile=True, gl_trace_coarse=True, expected_status=1)
        self.assertIn('Coarse GL trace requires GL trace', result.stderr)
        self.assertFalse((self.root / 'unit-request.json').exists())
        self.assertEqual(self.state.read_text(), 'active')

    def test_coarse_gl_trace_absent_clears_inherited_enable(self):
        with patch.dict(os.environ, {'SH3_GL_TRACE_COARSE': '1'}):
            report = self.run_timing_scene(frame_profile=True, gl_trace=True)
        observed = [line for line in (report.parent / 'stdout.txt').read_text().splitlines()
                    if line.startswith(('gl_trace=', 'gl_trace_coarse='))]
        self.assertEqual(observed, ['gl_trace=1', 'gl_trace_coarse=unset'])
        self.assertEqual(self.state.read_text(), 'active')

    def test_gl_trace_rejects_non_boolean_before_starting_game(self):
        result = self.run_timing_scene(frame_profile=True, gl_trace='1', expected_status=1)
        self.assertIn('Invalid GL trace', result.stderr)
        self.assertFalse((self.root / 'unit-request.json').exists())
        self.assertEqual(self.state.read_text(), 'active')

    def test_gl_trace_requires_frame_profile_before_starting_game(self):
        result = self.run_timing_scene(gl_trace=True, expected_status=1)
        self.assertIn('GL trace requires frame profile', result.stderr)
        self.assertFalse((self.root / 'unit-request.json').exists())
        self.assertEqual(self.state.read_text(), 'active')

    def test_gl_drain_scene_reaches_detached_runtime_with_trace_and_frame_profile(self):
        report = self.run_timing_scene(frame_profile=True, gl_trace=True, gl_drain=True)
        observed = [line for line in (report.parent / 'stdout.txt').read_text().splitlines()
                    if line.startswith(('gl_trace=', 'gl_drain='))]
        self.assertEqual(observed, ['gl_trace=1', 'gl_drain=1'])
        self.assertEqual(self.state.read_text(), 'active')

    def test_gl_drain_rejects_non_boolean_before_starting_game(self):
        result = self.run_timing_scene(frame_profile=True, gl_trace=True, gl_drain='1', expected_status=1)
        self.assertIn('Invalid GL drain', result.stderr)
        self.assertFalse((self.root / 'unit-request.json').exists())
        self.assertEqual(self.state.read_text(), 'active')

    def test_gl_drain_requires_trace_before_starting_game(self):
        result = self.run_timing_scene(frame_profile=True, gl_drain=True, expected_status=1)
        self.assertIn('GL drain requires GL trace', result.stderr)
        self.assertFalse((self.root / 'unit-request.json').exists())
        self.assertEqual(self.state.read_text(), 'active')

    def test_explicit_counter_sidecar_starts_with_game_and_stops_before_frontend_return(self):
        self.run_timing_scene(frame_profile=True, counter_probe=True)
        marker = self.port / 'runs/deploy-launch-service/counters/counter.pid'
        self.assertTrue(marker.is_file(), 'explicit counter diagnostic never started')
        pid = int(marker.read_text())
        self.assertFalse(Path(f'/proc/{pid}').exists(), 'counter sidecar survived game exit')
        self.assertEqual(self.state.read_text(), 'active')

    def test_counter_diagnostic_records_launcher_clock_bracket_and_warm_offsets(self):
        self.run_timing_scene(frame_profile=True, counter_probe=True)
        service = self.port / 'runs/deploy-launch-service'
        clocks = json.loads((service / 'launcher-clock.json').read_text())
        self.assertGreater(clocks['before']['monotonic_ns'], 0)
        self.assertGreater(clocks['after']['monotonic_ns'], clocks['before']['monotonic_ns'])
        arguments = json.loads((service / 'counters/offsets.json').read_text())
        self.assertEqual(arguments[:3], ['100', '125', '150'])

    def test_counter_diagnostic_uses_explicit_payload_on_storage_without_symlinks(self):
        self.write_command('ln', '#!/bin/sh\necho "Operation not permitted" >&2\nexit 1\n')
        self.run_timing_scene(frame_profile=True, counter_probe=True)
        service = self.port / 'runs/deploy-launch-service'
        arguments = json.loads((service / 'counters/offsets.json').read_text())
        self.assertEqual(arguments[3], '--payload')
        self.assertTrue((Path(arguments[4]) / 'gpu-counter/api-example').is_file())
        self.assertFalse((service / 'counters/payload').exists())

    def test_query_diagnostic_rejects_non_boolean_before_starting_game(self):
        result = self.run_timing_scene(frame_profile=True, gpu_profile='1', expected_status=1)
        self.assertIn('Invalid GPU profile', result.stderr)
        self.assertFalse((self.root / 'unit-request.json').exists())
        self.assertEqual(self.state.read_text(), 'active')

    def test_saved_deployment_installs_performance_menu_that_reaches_detached_runtime(self):
        self.run_timing_scene(frame_profile=True, fps_limit=30)
        self.menu = self.root / "Silent Hill 3 Performance.sh"
        result = self.launch_menu()
        self.assertEqual(result.returncode, 7, result.stdout + result.stderr)
        log = (self.port / "runs/service-fixture/stdout.txt").read_text()
        self.assertIn("resolution=320x240\n", log)
        self.assertIn("fps_limit=30\n", log)
        self.assertIn("capture= keys= peek=\n", log)
        self.assertEqual(self.state.read_text(), "active")

    def test_performance_cache_prime_reaches_ordinary_runtime_without_replacing_player_progress(self):
        savedata = self.port / 'state/savedata'
        savedata.mkdir(parents=True)
        (savedata / 'data.001').write_bytes(b'player progress')
        self.run_timing_scene(fps_limit=30, prime_cache=b'known compiled programs')
        self.menu = self.root / 'Silent Hill 3 Performance.sh'
        result = self.launch_menu()
        self.assertEqual(result.returncode, 7, result.stdout + result.stderr)
        log = (self.port / 'runs/service-fixture/stdout.txt').read_text()
        self.assertIn('known compiled programs', log)
        self.assertEqual((savedata / 'data.001').read_bytes(), b'player progress')
        self.assertEqual(self.state.read_text(), 'active')
        self.assertIn('result=primed\n', (self.port / 'runs/deploy/program-cache-prime.txt').read_text())

    def test_performance_cache_prime_preserves_existing_player_cache(self):
        cache = self.port / 'state/sh3-gl-cache.bin'
        cache.parent.mkdir()
        cache.write_bytes(b'existing player programs')
        self.run_timing_scene(fps_limit=30, prime_cache=b'known compiled programs')
        self.assertEqual(cache.read_bytes(), b'existing player programs')
        self.assertIn('result=preserved\n', (self.port / 'runs/deploy/program-cache-prime.txt').read_text())

    def test_performance_cache_prime_does_not_create_player_state_before_first_import(self):
        self.run_timing_scene(fps_limit=30, prime_cache=b'known compiled programs')
        self.assertFalse((self.port / 'state').exists())
        self.assertIn('result=state-absent\n', (self.port / 'runs/deploy/program-cache-prime.txt').read_text())

    def test_checkpoint_compiled_programs_reach_detached_runtime(self):
        self.run_timing_scene(compiled_cache=True)

    def test_clean_profile_scene_keeps_checkpoint_schedule_without_frame_profiler(self):
        report = self.run_timing_scene(scene_name='profile-clean-320')
        self.assertFalse(report.exists(), 'clean comparison unexpectedly enabled frame profiler')
        request = json.loads((self.root / 'unit-request.json').read_text())
        self.assertIn('--property=RuntimeMaxSec=190', request)
        self.assertIn('--setenv=SH3_QUIT_AFTER=100', request)
        self.assertIn('--setenv=SH3_KEYS=10:Return+0.4,30:Down+0.2,32:Return+0.4,34:Return+0.4,36:Return+0.4', request)

    def test_saved_entry_reports_storage_when_run_directory_cannot_be_created(self):
        self.write_command('mkdir', '#!/bin/sh\nexit 3\n')
        self.write_command('df', '#!/bin/sh\nprintf "capacity %s\\n" "$1"\n')
        result = subprocess.run(['bash', str(REPO / 'scripts/device/run.sh'), 'inventory',
                                 str(self.port), 'no-space', str(REPO)],
                                capture_output=True, text=True, timeout=20,
                                env={**os.environ, 'PATH': f"{self.commands}:{os.environ['PATH']}"})
        self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
        self.assertIn('capacity -Pk\n', result.stdout)
        self.assertIn('capacity -Pi\n', result.stdout)
        self.assertFalse((self.port / 'runs/no-space').exists())

    def test_inventory_references_completed_history_without_recopying_snapshots(self):
        originals = {}
        for run_id in ('completed-first', 'completed-second'):
            launch = self.port / 'runs' / run_id
            for name, data in [('run-id.txt', run_id.encode()), ('exit-status.txt', b'0\n'),
                               ('stderr.txt', b'original log'), ('session/savedata/data.000', b'quick save'),
                               ('session/sh3-gl-cache.bin', b'program cache')]:
                path = launch / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
                originals[path] = data
        out = self.root / 'inventory'
        result = subprocess.run(['bash', str(REPO / 'scripts/device/inventory.sh'), str(self.port), str(out)],
                                capture_output=True, text=True, timeout=20,
                                env={**os.environ, 'PATH': f"{self.commands}:{os.environ['PATH']}",
                                     'XDG_DATA_HOME': str(self.root / 'xdg')})
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        manifest = out / 'previous-launches.sha256'
        self.assertTrue(manifest.is_file(), 'missing original-history hash references')
        for path, data in originals.items():
            self.assertIn(hashlib.sha256(data).hexdigest() + '  ' + str(path), manifest.read_text())
            self.assertEqual(path.read_bytes(), data)
        self.assertFalse((out / 'previous-launches').exists(), 'repeated inventory must not duplicate history')

    def test_inventory_collects_every_owned_save_slot_and_current_state_without_changing_sources(self):
        previous = self.port / "runs/completed"
        state = self.port / "state"
        contents = {"savedata/data.000": b"quick", "savedata/data.001": b"first",
                    "savedata/data.002": b"second", "savedata/data.sys": b"index",
                    "savedata/key.ini": b"mapping", "sh3.ini": b"cores=1\n",
                    "sh3-gl-cache.bin": b"compiled driver programs"}
        for base in [previous / "session", state]:
            (base / "savedata").mkdir(parents=True)
            for name, value in contents.items():
                (base / name).write_bytes(value)
        (state / "sh3-progs.bin").write_bytes(b"warm cache")
        (previous / "run-id.txt").write_text("completed\n")
        (previous / "exit-status.txt").write_text("0\n")
        out = self.root / "inventory"
        result = subprocess.run(["bash", str(REPO / "scripts/device/inventory.sh"), str(self.port), str(out)],
                                capture_output=True, text=True, timeout=20,
                                env={**os.environ, "PATH": f"{self.commands}:{os.environ['PATH']}",
                                     "XDG_DATA_HOME": str(self.root / "xdg")})
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for name, value in contents.items():
            self.assertIn(hashlib.sha256(value).hexdigest() + '  ' + str(previous / 'session' / name),
                          (out / 'previous-launches.sha256').read_text())
            self.assertEqual((out / "persistent-state" / name).read_bytes(), value)
            self.assertEqual((previous / "session" / name).read_bytes(), value)
            self.assertEqual((state / name).read_bytes(), value)
        self.assertEqual((out / "persistent-state/sh3-progs.bin").read_bytes(), b"warm cache")
        self.assertRegex((out / "boot-id.txt").read_text(), r"^[0-9a-f-]{36}\n$")

    def test_inventory_records_available_cpu_profiler_without_installing_tools(self):
        self.write_command("perf", '#!/bin/sh\nprintf "profiler-probe: %s\\n" "$*"\nexit 0\n')
        out = self.root / "inventory"
        result = subprocess.run(["bash", str(REPO / "scripts/device/inventory.sh"), str(self.port), str(out)],
                                capture_output=True, text=True, timeout=20,
                                env={**os.environ, "PATH": f"{self.commands}:{os.environ['PATH']}",
                                     "XDG_DATA_HOME": str(self.root / "xdg")})
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        log = (out / "identity.txt").read_text()
        self.assertIn("profiler-probe: --version\n", log)
        self.assertIn("profiler-probe: stat -e cpu-clock -- true\n", log)

    def test_inventory_preserves_missing_io_accounting_for_user_and_root(self):
        self.write_command('cat', '#!/bin/sh\n'
                           'case "$1" in /proc/*/io) printf "cat: %s: No such file or directory\\n" "$1" >&2; exit 1;; esac\n'
                           'exec /bin/cat "$@"\n')
        out = self.root / 'inventory'
        result = subprocess.run(['bash', str(REPO / 'scripts/device/inventory.sh'), str(self.port), str(out)],
                                capture_output=True, text=True, timeout=20,
                                env={**os.environ, 'PATH': f"{self.commands}:{os.environ['PATH']}",
                                     'XDG_DATA_HOME': str(self.root / 'xdg')})
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        log = (out / 'io-capability.txt').read_text()
        errors = (out / 'io-capability.stderr.txt').read_text()
        self.assertIn('[monitor-uid]\n' + str(os.getuid()) + '\n', log)
        self.assertIn('[self-io]\nprobe-exit=1\n', log)
        self.assertIn('[root-self-io]\nuid=0\nio-read-exit=1\nprobe-exit=1\n', log)
        self.assertIn('[proc-mount]\n', log)
        self.assertIn('[kernel-io-config]', log)
        self.assertEqual(errors.count('/proc/self/io: No such file or directory'), 2)

    def test_inventory_retains_resolved_aarch64_sdl_provider_without_changing_source(self):
        library = self.pm / 'libs/libSDL2-2.0.so.0.3200.10'
        library.parent.mkdir()
        contents = bytearray(64)
        contents[:6] = b'\x7fELF\x02\x01'
        contents[18:20] = (183).to_bytes(2, 'little')
        library.write_bytes(contents)
        alias = library.with_name('libSDL2-2.0.so.0')
        alias.symlink_to(library.name)
        self.write_command('ldconfig', '#!/bin/sh\nprintf "libSDL2-2.0.so.0 (libc6,AArch64) => %s\\n" ' + str(alias) + '\n')
        out = self.root / 'inventory'
        result = subprocess.run(['bash', str(REPO / 'scripts/device/inventory.sh'), str(self.port), str(out)],
                                capture_output=True, text=True, timeout=20,
                                env={**os.environ, 'PATH': f"{self.commands}:{os.environ['PATH']}",
                                     'XDG_DATA_HOME': str(self.root / 'xdg')})
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((out / 'sdl-provider/library.so').read_bytes(), contents)
        identity = json.loads((out / 'sdl-provider/identity.json').read_text())
        self.assertEqual(identity['source'], str(alias))
        self.assertEqual(identity['resolved'], str(library))
        self.assertEqual(identity['sha256'], hashlib.sha256(contents).hexdigest())
        self.assertEqual(identity['elf'], {'class': 64, 'endian': 'little', 'machine': 183})
        self.assertEqual(library.read_bytes(), contents)
        self.assertTrue(alias.is_symlink())

    def test_inventory_records_advertised_policies_and_limits_without_changing_them(self):
        sysfs = self.root / 'sys'
        fields = {
            'devices/system/cpu/cpufreq/policy0/scaling_governor': 'ondemand\n',
            'devices/system/cpu/cpufreq/policy0/scaling_available_governors': 'ondemand performance\n',
            'devices/system/cpu/cpufreq/policy0/scaling_max_freq': '1512000\n',
            'devices/system/cpu/cpufreq/policy0/cpuinfo_max_freq': '1512000\n',
            'class/devfreq/ff300000.gpu/governor': 'simple_ondemand\n',
            'class/devfreq/ff300000.gpu/available_governors': 'simple_ondemand performance\n',
            'class/devfreq/ff300000.gpu/max_freq': '520000000\n',
            'class/devfreq/ff300000.gpu/available_frequencies': '200000000 400000000 520000000\n',
            'class/thermal/thermal_zone0/temp': '60000\n',
        }
        for name, value in fields.items():
            path = sysfs / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(value)
        out = self.root / 'inventory'
        result = subprocess.run(['bash', str(REPO / 'scripts/device/inventory.sh'), str(self.port), str(out)],
                                capture_output=True, text=True, timeout=20,
                                env={**os.environ, 'PATH': f"{self.commands}:{os.environ['PATH']}",
                                     'SH3_SYSFS_ROOT': str(sysfs), 'XDG_DATA_HOME': str(self.root / 'xdg')})
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        log = (out / 'power-policy.txt').read_text()
        for name, value in fields.items():
            self.assertIn('[' + str(sysfs / name) + ']\n' + value, log)
            self.assertEqual((sysfs / name).read_text(), value)

    def test_opt_in_input_trace_reaches_detached_runtime(self):
        runtime = self.port / "runtime/sh3"
        runtime.write_text(runtime.read_text().replace("exit 7", 'printf "input-log=%s\\n" "$SH3_INPUT_LOG"\nexit 7'))
        with patch.dict(os.environ, {"SH3_INPUT_LOG": "1"}):
            result = self.launch_menu()
        self.assertEqual(result.returncode, 7, result.stdout + result.stderr)
        log = (self.port / "runs/service-fixture/stdout.txt").read_text()
        self.assertIn("input-log=1\n", log)
        self.assertEqual(self.state.read_text(), "active")

    def test_opt_in_frame_profile_survives_detached_service(self):
        runtime = self.port / "runtime/sh3"
        runtime.write_text(runtime.read_text().replace("exit 7", 'printf "frame,wall_ms\\n1,33.33\\n" > "$SH3_PROFILE"\nexit 7'))
        report = self.root / "frame-times.csv"
        with patch.dict(os.environ, {"SH3_PROFILE": str(report)}):
            result = self.launch_menu()
        self.assertEqual(result.returncode, 7, result.stdout + result.stderr)
        self.assertTrue(report.is_file(), "detached runtime lost requested frame report")
        self.assertEqual(report.read_text(), "frame,wall_ms\n1,33.33\n")
        self.assertEqual(self.state.read_text(), "active")

    def test_physical_controls_mode_removes_scripted_input_and_capture(self):
        runtime = self.port / "runtime/sh3"
        runtime.write_text(runtime.read_text().replace("exit 7", '''printf 'input-log=%s stats=%s backend=%s deadline=%s\\n' "$SH3_INPUT_LOG" "${SH3_STATS+set}" "$SH3_GL_BACKEND" "$SH3_QUIT_AFTER"
printf 'keys=%s peek=%s shot=%s capture=%s dump=%s monitor=%s profile=%s\\n' "${SH3_KEYS+set}" "${SH3_PEEK+set}" "${SH3_SHOT+set}" "${SH3_SHOT_EVERY+set}" "${SH3_PRESENT_DUMP+set}" "${SH3_MONITOR+set}" "${SH3_PROFILE+set}"
exit 7'''))
        with patch.dict(os.environ, {"SH3_PHYSICAL_CONTROLS": "1", "SH3_KEYS": "1:Return",
                                    "SH3_PEEK": "72D2C0", "SH3_SHOT": "/unused",
                                    "SH3_SHOT_EVERY": "1", "SH3_PRESENT_DUMP": "/unused.ppm",
                                    "SH3_MONITOR": "1", "SH3_STATS": "1", "SH3_PROFILE": "/unused.csv"}):
            result = self.launch_menu()
        self.assertEqual(result.returncode, 7, result.stdout + result.stderr)
        log = (self.port / "runs/service-fixture/stdout.txt").read_text()
        self.assertIn("input-log=1 stats= backend=gles deadline=900\n", log)
        self.assertIn("keys= peek= shot= capture= dump= monitor= profile=\n", log)
        self.assertEqual(self.state.read_text(), "active")

    def test_opt_in_handheld_profile_keeps_frame_report_without_scripted_input_or_captures(self):
        report = self.root / 'handheld.csv'
        runtime = self.port / 'runtime/sh3'
        runtime.write_text(runtime.read_text().replace('exit 7', '''cat savedata/disp.ini
printf 'keys=%s shot=%s stats=%s gpu=%s\\n' "${SH3_KEYS+set}" "${SH3_SHOT+set}" "${SH3_STATS+set}" "$SH3_GPU_PROFILE"
if [ -n "${SH3_PROFILE:-}" ]; then printf 'frame,wall_ms\\n1,33.33\\n' > "$SH3_PROFILE"; fi
exit 7'''))
        with patch.dict(os.environ, {'SH3_PHYSICAL_CONTROLS':'1','SH3_PHYSICAL_PROFILE':'1',
                                    'SH3_PROFILE':str(report),'SH3_GPU_PROFILE':'0',
                                    'SH3_INTERNAL_RESOLUTION':'320x240','SH3_KEYS':'1:Return',
                                    'SH3_SHOT':'/unused','SH3_STATS':'1'}):
            result = self.launch_menu()
        self.assertEqual(result.returncode,7,result.stdout+result.stderr)
        self.assertTrue(report.is_file(),'handheld performance mode discarded frame report')
        self.assertEqual(report.read_text(),'frame,wall_ms\n1,33.33\n')
        log = (self.port / 'runs/service-fixture/stdout.txt').read_text()
        self.assertIn('resolution=320x240\n',log)
        self.assertIn('keys= shot= stats= gpu=0\n',log)
        settings = (self.port / 'runs/service-fixture-service/physical-controls.txt').read_text()
        self.assertIn('performance_sampler=1\n',settings)
        self.assertEqual(self.state.read_text(),'active')

    def test_saved_handheld_profile_records_requested_resolution_without_scripted_input_or_capture(self):
        payload = self.root / "payload"
        (payload / "runtime").mkdir(parents=True)
        (payload / "ports").mkdir()
        (payload / "physical-controls").touch()
        (payload / "physical-profile").write_text("320x240\n")
        shutil.copyfile(REPO / "ports/Silent Hill 3 Game.sh", payload / "ports/Silent Hill 3 Game.sh")
        shutil.copyfile(REPO / "ports/Silent Hill 3 Performance.sh", payload / "ports/Silent Hill 3 Performance.sh")
        runtime = payload / "runtime/sh3"
        runtime.write_text('''#!/bin/sh
cat savedata/disp.ini
printf 'keys=%s peek=%s shot=%s stats=%s gpu=%s\\n' "${SH3_KEYS+set}" "${SH3_PEEK+set}" "${SH3_SHOT+set}" "${SH3_STATS+set}" "$SH3_GPU_PROFILE"
if [ -n "${SH3_PROFILE:-}" ]; then printf 'frame,wall_ms\\n1,33.33\\n' > "$SH3_PROFILE"; fi
exit 7
''')
        (payload / "runtime/artifacts.sha256").write_text(hashlib.sha256(runtime.read_bytes()).hexdigest() + '  sh3\n')
        (self.port / "runtime/.sh3-runtime-owned").touch()
        monitor = self.port / "preflight/scripts/device/monitor-game.sh"
        monitor.parent.mkdir(parents=True)
        shutil.copyfile(REPO / "scripts/device/monitor-game.sh", monitor)
        for name in ["readelf", "ldd"]:
            self.write_command(name, '#!/bin/sh\nexit 0\n')
        pgrep = self.commands / "pgrep"
        pgrep.write_text(pgrep.read_text().replace('root=', '[ "$2" = sh3 ] && exit 1\nroot=', 1))
        run = self.port / "runs/deploy"
        run.mkdir(parents=True)
        result = subprocess.run(["bash", str(REPO / "scripts/device/runtime.sh"), str(self.port),
                                 "deploy", str(payload), str(run), "game"],
                                capture_output=True, text=True, timeout=20,
                                env={**os.environ, "PATH": f"{self.commands}:{os.environ['PATH']}",
                                     "XDG_DATA_HOME": str(self.root / "xdg"), "SH3_PACKAGE_DIR": str(REPO)})
        self.assertEqual(result.returncode, 7, result.stdout + result.stderr)
        launch = self.port / "runs/deploy-launch"
        self.assertTrue((launch / "frame-times.csv").is_file(), "saved handheld workflow discarded frame report")
        self.assertEqual((launch / "frame-times.csv").read_text(), "frame,wall_ms\n1,33.33\n")
        log = (launch / "stdout.txt").read_text()
        self.assertIn("resolution=320x240\n", log)
        self.assertIn("keys= peek= shot= stats= gpu=0\n", log)
        probe = (run / "game-probe.txt").read_text()
        self.assertIn("performance_sampler=1\n", probe)
        self.assertIn("internal_resolution=320x240\n", probe)
        self.assertIn("state_mode=isolated\n", probe)
        self.assertEqual(self.state.read_text(), "active")

    def test_checkpoint_and_requested_render_profile_reach_detached_game(self):
        seed = self.root / "seed-session/savedata"
        seed.mkdir(parents=True)
        (seed / "data.001").write_text("checkpoint one\n")
        (seed / "data.sys").write_text("checkpoint index\n")
        runtime = self.port / "runtime/sh3"
        runtime.write_text(runtime.read_text().replace("exit 7", '''cat savedata/data.001
cat savedata/disp.ini
printf '%s\\n' "$SH3_PEEK"
exit 7'''))
        with patch.dict(os.environ, {"SH3_SEED_SESSION": str(seed.parent),
                                    "SH3_INTERNAL_RESOLUTION": "640x480",
                                    "SH3_PEEK": "72BFD0,72BFD4"}):
            result = self.launch_menu()
        self.assertEqual(result.returncode, 7, result.stdout + result.stderr)
        log = (self.port / "runs/service-fixture/stdout.txt").read_text()
        self.assertIn("checkpoint one\n", log)
        self.assertIn("resolution=640x480\n", log)
        self.assertIn("72BFD0,72BFD4\n", log)
        self.assertEqual((seed / "data.001").read_text(), "checkpoint one\n")
        self.assertEqual(self.state.read_text(), "active")

    def test_service_stop_post_restores_frontend_when_session_cannot_run_exit_trap(self):
        (self.root / "crash-service").touch()
        runtime = self.port / "runtime/sh3"
        runtime.write_text(runtime.read_text().replace("exit 7", "sleep 30"))
        result = self.launch_menu()
        self.assertEqual(result.returncode, 137, result.stdout + result.stderr)
        self.assertEqual(self.trace.read_text().splitlines(), ["stop", "runtime", "start"])
        self.assertEqual(self.state.read_text(), "active")
        self.assertFalse(list(self.port.glob("runs/*/frontend-stopped")))


if __name__ == "__main__":
    unittest.main()
