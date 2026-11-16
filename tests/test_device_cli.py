"""Saved host workflow; SSH/SCP process fixtures never establish device acceptance."""
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tarfile
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]


@unittest.skipUnless((REPO / "SILENT HILL 3/sh3.exe").is_file(), "requires ignored owner installation")
class DeviceCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="device-cli-", dir=REPO / ".port-cache")
        self.addCleanup(self.temp.cleanup)
        root = self.root = Path(self.temp.name)
        spec = importlib.util.spec_from_file_location("device_workflow", REPO / "scripts/host/r36s.py")
        workflow = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(workflow)
        for name in [*workflow.FILES, "scripts/host/r36s.py", "scripts/host/scenes.py",
                     "scripts/host/ssh-askpass.sh", ".gitignore"]:
            dest = root / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPO / name, dest)
        (root / ".env").write_text("R36S_PORT=sh3\nR36S_HOST=fixture.invalid\nSH3_GAME_DIR=" +
                                   shlex.quote(str(REPO / "SILENT HILL 3")) + "\n")
        runtime = root / "dist/runtime"
        runtime.mkdir(parents=True)
        binary = bytearray(20)
        binary[:6] = b"\x7fELF\x02\x01"
        binary[18:20] = (183).to_bytes(2, "little")
        (runtime / "sh3").write_bytes(binary)
        owner = REPO / "SILENT HILL 3/sh3.exe"
        (runtime / "build-inputs.json").write_text(json.dumps({"input_sha1": hashlib.sha1(owner.read_bytes()).hexdigest()}))
        for name in ["packages.txt", "compiler.txt", "libc.txt", "python.txt", "elf.txt", "readelf.txt", "artifacts.sha256"]:
            (runtime / name).touch()
        review = root / "review/device"
        review.mkdir(parents=True)
        (review / "portmaster-files.sha256").write_text("fixture reviewed helpers\n")
        source = self.source = root / "player"
        (source / "savedata").mkdir(parents=True)
        contents = self.contents = {"savedata/data.001": b"first slot", "savedata/data.002": b"second slot",
                    "savedata/data.sys": b"index", "savedata/key.ini": b"mapping",
                    "sh3.ini": b"cores=1\n", "sh3-progs.bin": b"cache",
                    "sh3-gl-cache.bin": b"compiled driver programs"}
        for name, value in contents.items():
            (source / name).write_bytes(value)
        (source / "unrelated.txt").write_text("leave out")
        commands = root / "bin"
        commands.mkdir()
        (commands / "ssh").write_text('#!/bin/sh\nprintf "called\\n" >> "$FIXTURE_ROOT/connection-attempts.txt"\nexit 0\n')
        (commands / "scp").write_text('''#!/usr/bin/env python3
import hashlib, json, os, pathlib, shutil, sys
source = pathlib.Path(sys.argv[-2])
root = pathlib.Path(os.environ['FIXTURE_ROOT'])
if source.is_dir():
    files = {str(p.relative_to(source)): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in source.rglob('*') if p.is_file()}
    (root / 'deployed.json').write_text(json.dumps(files))
    (root / 'deployed-modes.json').write_text(json.dumps({str(p.relative_to(source)): p.stat().st_mode & 0o777
                                                        for p in source.rglob('*') if p.is_file()}))
    if (root / 'archive-fixture.tar.gz').is_file(): sys.exit(0)
else:
    with (root / 'collection-attempts.txt').open('a') as out:
        out.write('attempted\\n')
    if str(source).endswith('.evidence.tar.gz') and (root / 'archive-fixture.tar.gz').is_file():
        shutil.copyfile(root / 'archive-fixture.tar.gz', sys.argv[-1])
        sys.exit(0)
sys.exit(42)
''')
        for command in commands.iterdir():
            command.chmod(0o755)

    def run_workflow(self, *options, action="game"):
        return subprocess.run(["python3", str(self.root / "scripts/host/r36s.py"), action,
                                 *options, "--reviewed-helpers", str(self.root / "review")], cwd=self.root,
                                env={**os.environ, "PATH": f"{self.root / 'bin'}:{os.environ['PATH']}",
                                     "FIXTURE_ROOT": str(self.root), "GIT_DIR": str(REPO / ".git"),
                                     "GIT_WORK_TREE": str(self.root), "GIT_OPTIONAL_LOCKS": "0"},
                                capture_output=True, text=True, timeout=20)

    def test_play_inspection_streams_owned_cleanup_inventory_without_device_writes(self):
        device = self.root / 'device/ports/sh3'
        for relative, contents in {'gamedata/sh3.exe': b'owner game',
                                   'gamedata/data/movie/opening.000': b'original movie',
                                   'state/savedata/data.001': b'progress to clear',
                                   'state/sh3-gl-cache.bin': b'keep cache',
                                   'runs/old/stderr.txt': b'old diagnostics',
                                   '../Other Port.sh': b'unrelated port'}.items():
            path = device / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(contents)
        before = {str(p): p.read_bytes() for p in device.parent.rglob('*') if p.is_file()}
        (self.root / 'bin/ssh').write_text('''#!/usr/bin/env python3
from pathlib import Path
import os, shlex, subprocess, sys
root = Path(os.environ['FIXTURE_ROOT'])
args = shlex.split(sys.argv[-1])
args[2] = str(root / 'device/ports/sh3')
sys.exit(subprocess.run(args, input=sys.stdin.buffer.read()).returncode)
''')
        result = self.run_workflow('--play-action', 'inspect', '--hash-data', action='inventory')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        run = next((self.root / 'r36s-dumps/sh3').iterdir())
        report = json.loads((run / 'play.stdout.txt').read_text())
        self.assertNotIn('files', next(p for p in report['entries'] if p['path'] == 'runs'),
                         'inspection must list run directory without walking prior diagnostic trees')
        self.assertIn('state/savedata/data.001', report['saves'])
        self.assertIn('runs', report['diagnostics'])
        self.assertNotIn('state/sh3-gl-cache.bin', report['diagnostics'])
        self.assertEqual(report['assets']['gamedata/data/movie/opening.000']['sha256'],
                         hashlib.sha256(b'original movie').hexdigest())
        self.assertEqual({str(p): p.read_bytes() for p in device.parent.rglob('*') if p.is_file()}, before)

    def test_play_cleanup_clears_only_sh3_progress_logs_and_owned_extra_menus(self):
        device = self.root / 'device/ports/sh3'
        keep = {'gamedata/sh3.exe': b'owner executable',
                'gamedata/data/movie/opening.000': b'original movie',
                'runtime/sh3': b'installed native', 'runtime/.sh3-runtime-owned': b'',
                'state/sh3-gl-cache.bin': b'warm driver cache',
                'state/sh3-progs.bin': b'warm program cache',
                'state/savedata/key.ini': b'controls', 'state/savedata/disp.ini': b'graphics',
                'state/savedata/unrelated.dat': b'preserve unknown state',
                '../Other Port.sh': b'unrelated launcher',
                '../other-game/savedata/data.001': b'unrelated save'}
        remove = {'state/savedata/data.001': b'progress', 'state/savedata/data.sys': b'old index',
                  'gamedata/savedata/data.002': b'legacy progress',
                  'runs/old/session/savedata/data.001': b'checkpoint',
                  'runs/old/profile.csv': b'performance capture', 'sh3-crash.log': b'crash report',
                  '../Silent Hill 3 Game.sh': b'#!/bin/bash\n# SH3 project game menu; old\n'}
        for relative, contents in {**keep, **remove}.items():
            path = device / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(contents)
        (self.root / 'bin/pgrep').write_text('#!/bin/sh\nexit 1\n')
        (self.root / 'bin/pgrep').chmod(0o755)
        (self.root / 'bin/ssh').write_text('''#!/usr/bin/env python3
from pathlib import Path
import os, shlex, subprocess, sys
root = Path(os.environ['FIXTURE_ROOT'])
args = shlex.split(sys.argv[-1])
args[2] = str(root / 'device/ports/sh3')
sys.exit(subprocess.run(args, input=sys.stdin.buffer.read()).returncode)
''')
        result = self.run_workflow('--play-action', 'clean', action='inventory')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual({name: (device / name).read_bytes() for name in keep}, keep)
        self.assertFalse([name for name in remove if (device / name).exists()])
        self.assertFalse((device / 'runs').exists())

    def test_play_install_leaves_one_named_menu_fresh_options_and_only_runtime_helpers(self):
        device = self.root / 'device/ports/sh3'
        keep = {'gamedata/sh3.exe': (REPO / 'SILENT HILL 3/sh3.exe').read_bytes(),
                'gamedata/data/movie/opening.000': b'original movie',
                'state/sh3-gl-cache.bin': b'warm driver cache',
                'state/sh3-progs.bin': b'warm program cache',
                'state/savedata/key.ini': b'controls',
                '../Other Port.sh': b'unrelated launcher',
                '../other-game/savedata/data.001': b'unrelated progress'}
        old = {'runtime/sh3': b'old runtime', 'runtime/.sh3-runtime-owned': b'',
               'runtime/elf.txt': b'old diagnostics', 'preflight/.sh3-preflight-owned': b'',
               'preflight/scripts/device/monitor-game.sh': b'old monitor',
               'state/savedata/data.001': b'old progress', 'state/savedata/data.sys': b'old index',
               'runs/old/stderr.txt': b'old logs',
               '../Silent Hill 3 Game.sh': b'#!/bin/bash\n# SH3 project game menu; old\n'}
        for name, contents in {**keep, **old}.items():
            path = device / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(contents)
        helpers = self.root / 'firmware/PortMaster/control.txt'
        helpers.parent.mkdir(parents=True)
        helpers.write_text('# reviewed firmware helper\n')
        (self.root / 'review/device/portmaster-files.sha256').write_text(
            hashlib.sha256(helpers.read_bytes()).hexdigest() + '  ' + str(helpers) + '\n')
        settings = self.root / 'fresh-options/data.sys'
        settings.parent.mkdir()
        settings.write_bytes(b'fresh original options, blood much, no progression')
        gamelist = device.parent / 'gamelist.xml'
        gamelist.write_text('<gameList><game><path>./Other Port.sh</path><name>Keep other name</name>'
                            '<playcount>7</playcount></game><game><path>./Silent Hill 3 Game.sh</path>'
                            '<name>Silent Hill 3 Game</name></game></gameList>')
        (self.root / 'bin/systemctl').write_text('#!/bin/sh\nprintf "%s\\n" "$1" >> "$FIXTURE_ROOT/frontend-actions"\nexit 0\n')
        (self.root / 'bin/systemctl').chmod(0o755)
        (self.root / 'bin/sudo').write_text('#!/bin/sh\n[ "$1" = -n ] && shift\nexec "$@"\n')
        (self.root / 'bin/sudo').chmod(0o755)
        (self.root / 'bin/pgrep').write_text('#!/bin/sh\nexit 1\n')
        (self.root / 'bin/pgrep').chmod(0o755)
        (self.root / 'bin/ssh').write_text('''#!/usr/bin/env python3
from pathlib import Path
import os, shlex, subprocess, sys
root = Path(os.environ['FIXTURE_ROOT'])
args = [a.replace('/roms2/ports/sh3', str(root / 'device/ports/sh3'))
        for a in shlex.split(sys.argv[-1])]
sys.exit(subprocess.run(args, input=sys.stdin.buffer.read()).returncode)
''')
        (self.root / 'bin/scp').write_text('''#!/usr/bin/env python3
from pathlib import Path
import os, shutil, sys
root = Path(os.environ['FIXTURE_ROOT'])
source = Path(sys.argv[-2])
target = Path(sys.argv[-1].split(':', 1)[1].replace('/roms2/ports/sh3', str(root / 'device/ports/sh3')))
shutil.copytree(source, target / source.name)
''')
        result = self.run_workflow('--play-action', 'install', '--play-settings', str(settings),
                                   '--runtime-package', str(self.root / 'dist/runtime'), action='inventory')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual({name: (device / name).read_bytes() for name in keep}, keep)
        self.assertEqual((device / 'runtime/sh3').read_bytes(), (self.root / 'dist/runtime/sh3').read_bytes())
        self.assertEqual((device / 'state/savedata/data.sys').read_bytes(), settings.read_bytes())
        self.assertEqual([p.name for p in device.parent.glob('Silent Hill 3*.sh')], ['Silent Hill 3.sh'])
        self.assertEqual((device.parent / 'Silent Hill 3.sh').read_bytes(),
                         (REPO / 'ports/Silent Hill 3 Play.sh').read_bytes())
        self.assertEqual({p.name for p in (device / 'runtime').iterdir()}, {'sh3', '.sh3-runtime-owned'})
        self.assertEqual({p.name for p in (device / 'preflight/ports').iterdir()},
                         {'Silent Hill 3.sh', 'Silent Hill 3 Game.sh', 'game-session.sh',
                          'restore-frontend.sh', 'performance-governors.py'})
        display = (device / 'state/savedata/disp.ini').read_text()
        for value in ['resolution=320x240', 'size=640x480', 'shadow=1', 'lensflare_ztest=1']:
            self.assertIn(value, display)
        self.assertIn('trace=0', (device / 'state/sh3.ini').read_text())
        self.assertFalse(list((device / 'state/savedata').glob('data.[0-9][0-9][0-9]')))
        self.assertFalse((device / 'runs').exists())
        self.assertFalse(list(device.glob('.play-install-*')))
        self.assertFalse((device / 'preflight/scripts/device/monitor-game.sh').exists())
        import xml.etree.ElementTree as ET
        games = ET.parse(gamelist).getroot().findall('game')
        self.assertEqual([(g.findtext('path'), g.findtext('name')) for g in games],
                         [('./Other Port.sh', 'Keep other name'), ('./Silent Hill 3.sh', 'Silent Hill 3')])
        self.assertEqual(games[0].findtext('playcount'), '7')
        self.assertEqual((self.root / 'frontend-actions').read_text().splitlines(), ['is-active', 'stop', 'start'])

    def test_play_cleanup_rejects_active_game_foreign_menu_and_symlink_before_any_removal(self):
        device = self.root / 'device/ports/sh3'
        for name in ['runtime/.sh3-runtime-owned', 'state/savedata/data.001', 'runs/old/log.txt']:
            path = device / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'preserve until complete cleanup batch is safe')
        (self.root / 'bin/pgrep').write_text('#!/bin/sh\nexit 1\n')
        (self.root / 'bin/pgrep').chmod(0o755)
        (self.root / 'bin/ssh').write_text('''#!/usr/bin/env python3
from pathlib import Path
import os, shlex, subprocess, sys
root = Path(os.environ['FIXTURE_ROOT'])
args = [a.replace('/roms2/ports/sh3', str(root / 'device/ports/sh3'))
        for a in shlex.split(sys.argv[-1])]
sys.exit(subprocess.run(args, input=sys.stdin.buffer.read()).returncode)
''')
        foreign = device.parent / 'Silent Hill 3 Game.sh'
        link = device / 'state/savedata/data.002'
        other = device.parent / 'other-game-save'
        other.write_bytes(b'unrelated progress')
        for defect in ['active', 'foreign', 'symlink']:
            with self.subTest(defect=defect):
                (self.root / 'bin/pgrep').write_text('#!/bin/sh\nexit ' + ('0' if defect == 'active' else '1') + '\n')
                if defect == 'foreign': foreign.write_bytes(b'foreign launcher')
                if defect == 'symlink': link.symlink_to(other)
                result = self.run_workflow('--play-action', 'clean', action='inventory')
                self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
                self.assertTrue((device / 'state/savedata/data.001').is_file())
                self.assertTrue((device / 'runs/old/log.txt').is_file())
                self.assertEqual(other.read_bytes(), b'unrelated progress')
                if foreign.exists(): foreign.unlink()
                if link.is_symlink(): link.unlink()

    def test_play_verification_refuses_missing_menu_without_mutating_device(self):
        device = self.root / 'device/ports/sh3'
        device.mkdir(parents=True)
        (device / 'keep.txt').write_text('existing data')
        (self.root / 'bin/pgrep').write_text('#!/bin/sh\nexit 1\n')
        (self.root / 'bin/pgrep').chmod(0o755)
        (self.root / 'bin/ssh').write_text('''#!/usr/bin/env python3
from pathlib import Path
import os, shlex, subprocess, sys
root = Path(os.environ['FIXTURE_ROOT'])
args = [a.replace('/roms2/ports/sh3', str(root / 'device/ports/sh3'))
        for a in shlex.split(sys.argv[-1])]
sys.exit(subprocess.run(args, input=sys.stdin.buffer.read()).returncode)
''')
        result = self.run_workflow('--play-action', 'verify', action='inventory')
        self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
        run = next((self.root / 'r36s-dumps/sh3').iterdir())
        refusal = json.loads((run / 'play.stderr.txt').read_text())
        self.assertIn('play menu missing', refusal['reason'])
        self.assertEqual([p.name for p in device.iterdir()], ['keep.txt'])

    def test_reclaim_only_retained_exact_payloads_and_rejects_unsafe_batches(self):
        device = self.root / 'device-sh3'
        run_id = '20261115T140929993471Z-d958cc'
        relative = 'runs/' + run_id + '/payload/runtime/sh3'
        target = device / relative
        target.parent.mkdir(parents=True)
        first_relative = 'runs/20261115T140929993471Z-d958cd/payload/runtime/sh3'
        first = device / first_relative
        first.parent.mkdir(parents=True)
        installed = device / 'runtime/sh3'
        installed.parent.mkdir()
        installed.write_bytes(b'installed runtime remains')
        retained = self.root / '.port-cache/builds/retained/artifacts/runtime/sh3'
        retained.parent.mkdir(parents=True)
        retained.write_bytes(b'retained native payload')
        digest = hashlib.sha256(retained.read_bytes()).hexdigest()
        manifest = self.root / 'reclaim.json'
        (self.root / 'bin/pgrep').write_text('#!/bin/sh\n[ -f "$FIXTURE_ROOT/active-game" ]\n')
        (self.root / 'bin/pgrep').chmod(0o755)
        (self.root / 'bin/ssh').write_text('''#!/usr/bin/env python3
from pathlib import Path
import os, shlex, subprocess, sys
root = Path(os.environ['FIXTURE_ROOT'])
args = shlex.split(sys.argv[-1])
source = sys.stdin.buffer.read()
if args[:2] == ['python3', '-']:
    args[2] = str(root / 'device-sh3')
    sys.exit(subprocess.run(args, input=source).returncode)
print('fixture capacity available')
''')
        for scenario in ('foreign', 'changed', 'active', 'symlink', 'retention', 'valid'):
            with self.subTest(scenario=scenario):
                retained.write_bytes(b'retained native payload')
                first.write_bytes(retained.read_bytes())
                if target.is_symlink(): target.unlink()
                target.write_bytes(b'changed' if scenario == 'changed' else retained.read_bytes())
                if scenario == 'symlink':
                    target.unlink()
                    target.symlink_to(installed)
                if scenario == 'retention': retained.write_bytes(b'changed local copy')
                active = self.root / 'active-game'
                if active.exists(): active.unlink()
                if scenario == 'active': active.touch()
                relative_path = 'runtime/sh3' if scenario == 'foreign' else relative
                manifest.write_text(json.dumps({'port': 'sh3', 'files': [
                    {'path': '/roms2/ports/sh3/' + name, 'sha256': digest,
                     'retained': str(retained.relative_to(self.root)), 'bytes': 23}
                    for name in (first_relative, relative_path)]}))
                result = self.run_workflow('--reclaim-payloads', str(manifest), action='inventory')
                self.assertEqual(result.returncode, 0 if scenario == 'valid' else 3,
                                 result.stdout + result.stderr)
                self.assertEqual(target.exists(), scenario != 'valid')
                self.assertEqual(first.exists(), scenario != 'valid', 'invalid later member must preserve entire batch')
                self.assertEqual(installed.read_bytes(), b'installed runtime remains')
                self.assertEqual(retained.read_bytes(),
                                 b'changed local copy' if scenario == 'retention' else b'retained native payload')
                if scenario == 'valid':
                    runs = [p for p in (self.root / 'r36s-dumps/sh3').iterdir()
                            if (p / 'reclaim.stdout.txt').is_file()]
                    self.assertTrue(any('"removed"' in (p / 'reclaim.stdout.txt').read_text() for p in runs))
                    self.assertTrue(any((p / 'reclaim-plan.json').is_file() for p in runs))

    def test_capacity_report_is_collected_before_full_device_blocks_preparation(self):
        (self.root / 'bin/ssh').write_text('''#!/usr/bin/env python3
from pathlib import Path
import os, sys
root = Path(os.environ['FIXTURE_ROOT'])
script = sys.argv[-1]
with (root / 'requests.txt').open('a') as log: log.write(script + '\\n')
if script.startswith('bash -s -- '):
    assert 'df -Pk' in sys.stdin.read()
    print('Filesystem 1024-blocks Used Available Capacity Mounted on')
    print('/dev/fixture 100 100 0 100% /roms2')
    sys.exit(0)
print('mkdir: No space left on device', file=sys.stderr)
sys.exit(1)
''')
        result = self.run_workflow(action='inventory')
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        run = next((self.root / 'r36s-dumps/sh3').iterdir())
        self.assertTrue((run / 'capacity.stdout.txt').is_file(), 'lost capacity report before failed device mkdir')
        self.assertIn('/dev/fixture 100 100 0 100%', (run / 'capacity.stdout.txt').read_text())
        self.assertIn('No space left on device', (run / 'prepare.stderr.txt').read_text())
        self.assertTrue((self.root / 'requests.txt').read_text().splitlines()[0].startswith('bash -s -- '))

    def test_persistent_import_deploys_all_player_slots_and_collects_failed_deployment(self):
        root, source, contents = self.root, self.source, self.contents
        result = self.run_workflow("--persistent-state", "--import-session", str(source))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        deployed = json.loads((root / "deployed.json").read_text())
        self.assertIn("persistent-state", deployed)
        self.assertIn("physical-controls", deployed)
        self.assertNotIn("scene-seed/savedata/data.001", deployed)
        self.assertNotIn("import-state/unrelated.txt", deployed)
        for name, value in contents.items():
            self.assertEqual(deployed["import-state/" + name], hashlib.sha256(value).hexdigest())
            self.assertEqual((source / name).read_bytes(), value)
        status = json.loads(next((root / "r36s-dumps/sh3").glob("*/status.json")).read_text())
        self.assertEqual(status["execution"], "deployment-failed")
        self.assertEqual(status["collection"], 42)
        self.assertTrue(status["source-preserved"])
        self.assertEqual((root / "collection-attempts.txt").read_text().splitlines(), ["attempted"] * 3)

    def test_handheld_profile_deploys_selected_resolution_and_collects_failed_deployment(self):
        for resolution in ("320x240", "640x480"):
            with self.subTest(resolution=resolution):
                result = self.run_workflow("--physical-profile", resolution)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                deployed = json.loads((self.root / "deployed.json").read_text())
                self.assertIn("physical-controls", deployed)
                self.assertEqual(deployed.get("physical-profile"),
                                 hashlib.sha256((resolution + "\n").encode()).hexdigest())
                self.assertNotIn("persistent-state", deployed)
                self.assertFalse(any(name.startswith("import-state/") for name in deployed))
                statuses = sorted((self.root / "r36s-dumps/sh3").glob("*/status.json"))
                status = json.loads(statuses[-1].read_text())
                self.assertEqual(status["physical_profile"], resolution)
                self.assertEqual(status["execution"], "deployment-failed")
                self.assertEqual(status["collection"], 42)
        self.assertEqual((self.root / "collection-attempts.txt").read_text().splitlines(), ["attempted"] * 6)

    def test_handheld_profile_rejects_conflicting_state_and_replay_before_deployment(self):
        for conflict in (("--persistent-state",), ("--import-session", str(self.source)),
                         ("--scene", "profile-static-320")):
            with self.subTest(conflict=conflict):
                result = self.run_workflow("--physical-profile", "320x240", *conflict)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn("requires game action without scene replay" if "--scene" in conflict
                              else "uses isolated state", result.stderr)
                self.assertFalse((self.root / "deployed.json").exists())
                self.assertFalse((self.root / "collection-attempts.txt").exists())

    def test_unattended_route_deploys_movement_combat_and_frame_profile_without_capture(self):
        result = self.run_workflow("--scene", "performance-route-320", "--seed-session", str(self.source))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        identity_path = next((self.root / "r36s-dumps/sh3").glob("*/scene-identity.json"))
        identity = json.loads(identity_path.read_text())
        plan = identity["plan"]
        self.assertEqual(plan["internal_resolution"], "320x240")
        self.assertEqual(plan["fps_limit"], 30)
        self.assertIs(plan["profile"], True)
        self.assertEqual(plan["capture_every"], 0)
        self.assertGreaterEqual(plan["seconds"], 180)
        for action in (":S+", ":W+", ":A+", ":D+", ":B+", ":Space+"):
            self.assertIn(action, plan["keys"], "route must exercise walking, turning and attacks")
        deployed = json.loads((self.root / "deployed.json").read_text())
        self.assertIn("scene-plan.json", deployed)
        self.assertNotIn("physical-controls", deployed)
        self.assertEqual(deployed["scene-seed/sh3-gl-cache.bin"],
                         hashlib.sha256(self.contents["sh3-gl-cache.bin"]).hexdigest())
        self.assertEqual(deployed["scene-seed/savedata/data.001"],
                         hashlib.sha256(self.contents["savedata/data.001"]).hexdigest())
        self.assertEqual((self.source / "savedata/data.001").read_bytes(),
                         self.contents["savedata/data.001"])

    def test_gl_diagnostic_routes_keep_matched_turns_and_explicit_profile_flags(self):
        plans = []
        for name, trace, drain in [('performance-traceoff-640', False, False),
                                   ('performance-trace-640', True, False),
                                   ('performance-drain-640', True, True)]:
            result = self.run_workflow('--scene', name, '--seed-session', str(self.source))
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            identity = json.loads(sorted((self.root / 'r36s-dumps/sh3').glob('*/scene-identity.json'))[-1].read_text())
            plan = identity['plan']
            self.assertEqual((plan['seconds'], plan['fps_limit'], plan['swap_interval']), (120, 30, 1))
            self.assertEqual((plan['profile'], plan['gl_trace'], plan['gl_drain']), (True, trace, drain))
            self.assertEqual((plan['internal_resolution'], plan['capture_every']), ('640x480', 0))
            self.assertEqual([(s['after_seconds'], s['before_seconds']) for s in plan['stages']], [(75, 120)])
            for turn in ('82:A+2', '91:D+2', '114:A+2'):
                self.assertIn(turn, plan['keys'])
            plans.append(plan)
        self.assertEqual(len({p['keys'] for p in plans}), 1)
        self.assertEqual(len({p['peek'] for p in plans}), 1)

    def test_coarse_routes_retain_same_turns_and_explicit_drain_control(self):
        reference = json.loads((REPO / 'scripts/scenes.json').read_text())['performance-traceoff-640']
        for name, drain in [('performance-coarse-640', False),
                            ('performance-coarse-drain-640', True)]:
            result = self.run_workflow('--scene', name, '--seed-session', str(self.source))
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            identity = json.loads(sorted((self.root / 'r36s-dumps/sh3').glob('*/scene-identity.json'))[-1].read_text())
            plan = identity['plan']
            self.assertEqual((plan['seconds'], plan['fps_limit'], plan['swap_interval']), (120, 30, 1))
            self.assertEqual((plan['profile'], plan['gl_trace'], plan['gl_trace_coarse'], plan['gl_drain']),
                             (True, True, True, drain))
            self.assertEqual((plan['internal_resolution'], plan['capture_every']), ('640x480', 0))
            self.assertEqual(plan['keys'], reference['keys'])
            self.assertEqual(plan['peek'], reference['peek'] + ',70E66C8')
            self.assertEqual([(s['after_seconds'], s['before_seconds']) for s in plan['stages']], [(75, 120)])

    def test_minimum_quality_coarse_trio_observes_loaded_blood_byte(self):
        plans = []
        for name, trace, drain in [('performance-coarseoff-640', False, False),
                                   ('performance-coarse-640', True, False),
                                   ('performance-coarse-drain-640', True, True)]:
            result = self.run_workflow('--scene', name, '--seed-session', str(self.source))
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            identity = json.loads(sorted((self.root / 'r36s-dumps/sh3').glob('*/scene-identity.json'))[-1].read_text())
            plan = identity['plan']
            self.assertEqual((plan['profile'], plan['gl_trace'], plan['gl_trace_coarse'], plan['gl_drain']),
                             (True, trace, trace, drain))
            self.assertTrue(all(address in plan['peek'] for address in
                                ('70E66C8', '70E66CC', '70E66B0', '72D274', '898660', '72D2C0')))
            plans.append(plan)
        self.assertEqual(len({p['keys'] for p in plans}), 1)
        self.assertEqual(len({p['peek'] for p in plans}), 1)

    def test_profile_disabled_route_retains_matched_120_second_peek_cadence(self):
        result = self.run_workflow('--scene', 'performance-profileoff-640',
                                   '--seed-session', str(self.source))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        identity = json.loads(next((self.root / 'r36s-dumps/sh3').glob('*/scene-identity.json')).read_text())
        plan = identity['plan']
        self.assertEqual((plan['seconds'], plan['fps_limit']), (120, 30))
        self.assertNotIn('swap_interval', plan, 'native override requires profiler; ordinary default is1')
        self.assertEqual((plan['profile'], plan['gl_trace'], plan['gl_drain']), (False, False, False))
        self.assertEqual((plan['internal_resolution'], plan['capture_every']), ('640x480', 0))
        reference = json.loads((REPO / 'scripts/scenes.json').read_text())['performance-traceoff-640']
        self.assertEqual(plan['keys'], reference['keys'])
        self.assertEqual(plan['peek'], reference['peek'])
        self.assertIn('898660', plan['peek'])

    def test_fixed_cache_plans_allow_cold_seed_without_changing_save_or_camera(self):
        for cache in ('sh3-progs.bin', 'sh3-gl-cache.bin'):
            (self.source / cache).unlink()
        plans = []
        for size in ('640', '320'):
            result = self.run_workflow('--scene', 'profile-cache-' + size,
                                       '--seed-session', str(self.source))
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            identity = json.loads(sorted((self.root / 'r36s-dumps/sh3').glob('*/scene-identity.json'))[-1].read_text())
            plan = identity['plan']
            self.assertEqual((plan['seconds'], plan['fps_limit'], plan['swap_interval']), (100, 30, 1))
            self.assertEqual((plan['profile'], plan['gpu_profile']), (True, False))
            self.assertEqual(plan['internal_resolution'], '640x480' if size == '640' else '320x240')
            self.assertEqual([(s['after_seconds'], s['before_seconds']) for s in plan['stages']], [(55, 95)])
            self.assertTrue(all(address in plan['peek'] for address in ('70E66CC', '70E66B0', '72D274', '70E66C8')))
            self.assertNotIn(':S+', plan['keys'], 'fixed camera/pose cache comparison')
            deployed = json.loads((self.root / 'deployed.json').read_text())
            self.assertNotIn('scene-seed/sh3-progs.bin', deployed)
            self.assertNotIn('scene-seed/sh3-gl-cache.bin', deployed)
            self.assertEqual(deployed['scene-seed/savedata/data.001'],
                             hashlib.sha256(self.contents['savedata/data.001']).hexdigest())
            plans.append(plan)
        self.assertEqual(plans[0]['keys'], plans[1]['keys'])
        self.assertEqual(plans[0]['peek'], plans[1]['peek'])

    def test_full_resolution_route_deploys_paced_movement_and_combat_for_fallback_comparison(self):
        result = self.run_workflow("--scene", "performance-route-640", "--seed-session", str(self.source))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        identity_path = next((self.root / "r36s-dumps/sh3").glob("*/scene-identity.json"))
        identity = json.loads(identity_path.read_text())
        plan = identity["plan"]
        self.assertEqual(plan["internal_resolution"], "640x480")
        self.assertEqual(plan["fps_limit"], 30)
        self.assertIs(plan["profile"], True)
        self.assertEqual(plan["capture_every"], 0)
        self.assertGreaterEqual(plan["seconds"], 180)
        for action in (":S+", ":W+", ":A+", ":D+", ":B+", ":Space+"):
            self.assertIn(action, plan["keys"])
        for address in ("72D2C0", "8984E0", "8984E8", "898660", "72BFD0", "72BFD4"):
            self.assertIn(address, plan["peek"], "comparison needs actual scene, movement and render size")
        deployed = json.loads((self.root / "deployed.json").read_text())
        self.assertIn("scene-plan.json", deployed)
        self.assertNotIn("physical-controls", deployed)
        self.assertEqual(deployed["scene-seed/savedata/data.001"],
                         hashlib.sha256(self.contents["savedata/data.001"]).hexdigest())
        self.assertTrue(identity["source_preserved"])

    def test_governor_diagnostic_deploys_explicit_domains_with_isolated_scene(self):
        result = self.run_workflow('--scene', 'profile-gpu-off-640', '--seed-session', str(self.source),
                                   '--performance-governors', 'cpu,gpu,dmc')
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        deployed = json.loads((self.root / 'deployed.json').read_text())
        self.assertEqual(deployed['performance-governors'], hashlib.sha256(b'cpu,gpu,dmc\n').hexdigest())
        self.assertIn('ports/performance-governors.py', deployed)
        status = json.loads(next((self.root / 'r36s-dumps/sh3').glob('*/status.json')).read_text())
        self.assertEqual(status['performance_governors'], 'cpu,gpu,dmc')

    def test_explicit_retained_runtime_package_deploys_exact_candidate(self):
        package = self.root / 'retained-runtime'
        shutil.copytree(self.root / 'dist/runtime', package)
        binary = (package / 'sh3').read_bytes() + b'retained native candidate'
        (package / 'sh3').write_bytes(binary)
        (self.root / 'dist/runtime/sh3').unlink()
        result = self.run_workflow('--scene', 'profile-gpu-off-640', '--seed-session', str(self.source),
                                   '--runtime-package', str(package))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        deployed = json.loads((self.root / 'deployed.json').read_text())
        self.assertEqual(deployed['runtime/sh3'], hashlib.sha256(binary).hexdigest())
        identity = json.loads(next((self.root / 'r36s-dumps/sh3').glob('*/scene-identity.json')).read_text())
        self.assertEqual(identity['runtime_sha256'], hashlib.sha256(binary).hexdigest())

    def test_counter_inventory_deploys_explicit_native_probe_with_verified_identity(self):
        probe = self.root / 'reviewed-counter-probe'
        binary = (self.root / 'dist/runtime/sh3').read_bytes() + b'observational counter probe'
        probe.write_bytes(binary)
        result = self.run_workflow('--gpu-counter-probe', str(probe), action='inventory')
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        deployed = json.loads((self.root / 'deployed.json').read_text())
        digest = hashlib.sha256(binary).hexdigest()
        self.assertIn('scripts/device/gpu-counter-probe.sh', deployed)
        self.assertEqual(deployed['gpu-counter/api-example'], digest)
        modes = json.loads((self.root / 'deployed-modes.json').read_text())
        self.assertTrue(modes['gpu-counter/api-example'] & 0o111, 'native diagnostic must be executable')
        self.assertEqual(deployed['gpu-counter/SHA256SUMS'],
                         hashlib.sha256((digest + '  api-example\n').encode()).hexdigest())
        status = json.loads(next((self.root / 'r36s-dumps/sh3').glob('*/status.json')).read_text())
        self.assertEqual(status['gpu_counter_probe_sha256'], digest)

    def test_counter_probe_rejects_wrong_abi_or_unseeded_game_before_device_access(self):
        probe = self.root / 'counter-probe'
        for action, binary in [('inventory', b'#!/bin/sh\nexit 0\n'),
                               ('game', (self.root / 'dist/runtime/sh3').read_bytes())]:
            with self.subTest(action=action):
                probe.write_bytes(binary)
                result = self.run_workflow('--gpu-counter-probe', str(probe), action=action)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertFalse((self.root / 'deployed.json').exists())
                self.assertFalse((self.root / 'collection-attempts.txt').exists())

    def test_counter_sidecar_deploys_only_for_isolated_profiled_game_scene(self):
        probe = self.root / 'counter-probe'
        probe.write_bytes((self.root / 'dist/runtime/sh3').read_bytes())
        result = self.run_workflow('--scene', 'performance-swap1-640', '--seed-session', str(self.source),
                                   '--gpu-counter-probe', str(probe))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        deployed = json.loads((self.root / 'deployed.json').read_text())
        self.assertIn('gpu-counter/api-example', deployed)
        self.assertIn('scripts/device/gpu-counter-session.py', deployed)

    def test_inventory_entry_preserves_counter_failure_without_losing_system_inventory(self):
        payload = self.root / 'probe-payload'
        scripts = payload / 'scripts/device'
        scripts.mkdir(parents=True)
        shutil.copyfile(REPO / 'scripts/device/archive-evidence.sh', scripts / 'archive-evidence.sh')
        (scripts / 'inventory.sh').write_text('#!/bin/bash\nprintf "" > "$2/libraries.txt"\n')
        (scripts / 'gpu-counter-probe.sh').write_text(
            '#!/bin/bash\nmkdir -p "$1/gpu-counter"\nprintf "255\\n" > "$1/gpu-counter/exit-status.txt"\nexit 255\n')
        (payload / 'gpu-counter').mkdir()
        (payload / 'gpu-counter/api-example').touch()
        port = self.root / 'probe-port'
        result = subprocess.run(['bash', str(REPO / 'scripts/device/run.sh'), 'inventory',
                                 str(port), 'counter-entry', str(payload)], capture_output=True,
                                text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        run = port / 'runs/counter-entry'
        self.assertEqual((run / 'execution-status.txt').read_text(), '0\n')
        self.assertEqual((run / 'gpu-counter/exit-status.txt').read_text(), '255\n')

    def test_collection_retry_fetches_original_run_without_deploying_or_executing(self):
        original = '20261115T114935059499Z-3b9030'
        result = self.run_workflow('--retry-collection', original, action='inventory')
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertFalse((self.root / 'deployed.json').exists())
        self.assertFalse((self.root / 'connection-attempts.txt').exists())
        self.assertEqual((self.root / 'collection-attempts.txt').read_text(), 'attempted\n')
        status = json.loads(next((self.root / 'r36s-dumps/sh3').glob('*/status.json')).read_text())
        self.assertEqual(status['retry_collection_of'], original)
        self.assertEqual(status['execution'], 'collection-only')
        self.assertEqual(status['collection'], 42)

    def test_archive_collection_restores_regular_evidence_and_records_unfollowed_links(self):
        archive = self.root / 'archive-fixture.tar.gz'
        with tarfile.open(archive, 'w:gz') as output:
            item = tarfile.TarInfo('./execution-status.txt')
            item.size = 2
            output.addfile(item, io.BytesIO(b'0\n'))
            link = tarfile.TarInfo('./counter/payload')
            link.type = tarfile.SYMTYPE
            link.linkname = '/roms2/ports/sh3/runs/original/payload'
            output.addfile(link)
        result = self.run_workflow(action='inventory')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        run = next((self.root / 'r36s-dumps/sh3').glob('*/status.json')).parent
        self.assertEqual((run / 'device/execution-status.txt').read_text(), '0\n')
        self.assertFalse((run / 'device/counter/payload').exists())
        manifest = json.loads((run / 'device-archive-manifest.json').read_text())
        self.assertTrue(any(item['name'] == './counter/payload' and item['skipped_link'] for item in manifest))

    def test_archive_collection_rejects_path_escape_and_special_files_before_extraction(self):
        archive = self.root / 'archive-fixture.tar.gz'
        for name, kind in [('../escaped.txt', tarfile.REGTYPE), ('/escaped.txt', tarfile.REGTYPE),
                           ('pipe', tarfile.FIFOTYPE)]:
            with self.subTest(name=name):
                with tarfile.open(archive, 'w:gz') as output:
                    item = tarfile.TarInfo(name)
                    item.type = kind
                    output.addfile(item)
                result = self.run_workflow(action='inventory')
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                run = sorted((self.root / 'r36s-dumps/sh3').glob('*/status.json'))[-1].parent
                self.assertEqual(json.loads((run / 'status.json').read_text())['collection'], 3)
                self.assertFalse((run / 'device').exists())

    def test_gpu_diagnostic_scenes_deploy_matched_full_resolution_without_capture(self):
        for scene, enabled in [('profile-gpu-off-640', False), ('profile-gpu-on-640', True)]:
            with self.subTest(scene=scene):
                result = self.run_workflow('--scene', scene, '--seed-session', str(self.source))
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                identity_path = sorted((self.root / 'r36s-dumps/sh3').glob('*/scene-identity.json'))[-1]
                identity = json.loads(identity_path.read_text())
                plan = identity['plan']
                self.assertEqual(plan['internal_resolution'], '640x480')
                self.assertEqual(plan['fps_limit'], 30)
                self.assertEqual(plan['seconds'], 100)
                self.assertEqual(plan['capture_every'], 0)
                self.assertIs(plan['profile'], True)
                self.assertIs(plan['gpu_profile'], enabled)
                self.assertEqual(plan['keys'],
                                 '10:Return+0.4,30:Down+0.2,32:Return+0.4,34:Return+0.4,36:Return+0.4')
                for address in ('72D2C0', '8984E0', '8984E8', '898660', '72BFD0', '72BFD4',
                                '72C7F0', '72C7F4', 'BCC630', '70E66F4', '72C7E8', '72C7F8'):
                    self.assertIn(address, plan['peek'])
                self.assertTrue(identity['source_preserved'])
                self.assertEqual((self.source / 'savedata/data.001').read_bytes(),
                                 self.contents['savedata/data.001'])

    def test_swap_diagnostic_scenes_deploy_same_paced_scene_with_explicit_interval(self):
        for interval in (0, 1):
            result = self.run_workflow('--scene', f'profile-swap{interval}-640', '--seed-session', str(self.source))
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            identity = json.loads(sorted((self.root / 'r36s-dumps/sh3').glob('*/scene-identity.json'))[-1].read_text())
            plan = identity['plan']
            self.assertEqual(plan['swap_interval'], interval)
            self.assertEqual(plan['internal_resolution'], '640x480')
            self.assertEqual(plan['fps_limit'], 30)
            self.assertEqual(plan['capture_every'], 0)
            self.assertIs(plan['profile'], True)
            self.assertIs(plan['gpu_profile'], False)

    def test_moving_swap_diagnostics_keep_same_full_resolution_route_with_explicit_interval(self):
        plans = []
        for interval in (0, 1):
            result = self.run_workflow('--scene', f'performance-swap{interval}-640', '--seed-session', str(self.source))
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            plan = json.loads(sorted((self.root / 'r36s-dumps/sh3').glob('*/scene-identity.json'))[-1].read_text())['plan']
            self.assertEqual(plan['swap_interval'], interval)
            self.assertEqual(plan['internal_resolution'], '640x480')
            self.assertEqual(plan['fps_limit'], 30)
            self.assertEqual(plan['capture_every'], 0)
            self.assertIs(plan['profile'], True)
            for action in (':S+', ':W+', ':A+', ':D+', ':B+', ':Space+'):
                self.assertIn(action, plan['keys'])
            plans.append(plan)
        for key in ('keys', 'seconds', 'peek', 'stages'):
            self.assertEqual(plans[0][key], plans[1][key])

    def test_low_profile_routes_record_noise_display_and_menu_option_words(self):
        for scene in ('performance-swap0-640', 'performance-swap1-640', 'traverse-route-640'):
            result = self.run_workflow('--scene', scene, '--seed-session', str(self.source))
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            identity = json.loads(sorted((self.root / 'r36s-dumps/sh3').glob('*/scene-identity.json'))[-1].read_text())
            for address in ('70E66CC', '70E66B0', '72D274', 'BCC1B8'):
                self.assertIn(address, identity['plan']['peek'])

    def test_uncapped_resolution_diagnostics_deploy_matched_static_workload(self):
        plans = []
        for resolution in ('640', '320'):
            result = self.run_workflow('--scene', f'profile-uncapped-{resolution}', '--seed-session', str(self.source))
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            plan = json.loads(sorted((self.root / 'r36s-dumps/sh3').glob('*/scene-identity.json'))[-1].read_text())['plan']
            self.assertEqual(plan['internal_resolution'], '640x480' if resolution == '640' else '320x240')
            self.assertEqual(plan['fps_limit'], 0)
            self.assertEqual(plan['swap_interval'], 0)
            self.assertEqual(plan['capture_every'], 0)
            self.assertEqual(plan['seconds'], 100)
            self.assertIs(plan['profile'], True)
            self.assertIs(plan['gpu_profile'], False)
            plans.append(plan)
        for key in ('keys', 'peek', 'stages'):
            self.assertEqual(plans[0][key], plans[1][key])

    def test_program_cache_prime_deploys_only_compiled_programs_without_importing_progress(self):
        cache = self.root / "measured-programs.bin"
        contents = (0x53484231).to_bytes(4, "little") + (4).to_bytes(4, "little") + b"Mali"
        cache.write_bytes(contents)
        result = self.run_workflow("--scene", "traverse-route-320", "--seed-session", str(self.source),
                                   "--prime-program-cache", str(cache))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        deployed = json.loads((self.root / "deployed.json").read_text())
        self.assertEqual(deployed["performance-cache/sh3-gl-cache.bin"], hashlib.sha256(contents).hexdigest())
        self.assertFalse(any(name.startswith("import-state/") for name in deployed))
        self.assertNotIn("persistent-state", deployed)
        self.assertEqual(cache.read_bytes(), contents)

    def test_program_cache_prime_rejects_invalid_or_oversized_files_before_device_access(self):
        cache = self.root / "invalid-programs.bin"
        for contents in (b"", b"wrong cache", (0x53484231).to_bytes(4, "little") +
                         (100).to_bytes(4, "little") + b"short", None):
            with self.subTest(contents=contents):
                if contents is None:
                    with cache.open("wb") as out:
                        out.truncate(32 * 1024 * 1024 + 1)
                else:
                    cache.write_bytes(contents)
                result = self.run_workflow("--prime-program-cache", str(cache))
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn("Invalid compiled program cache", result.stderr)
                self.assertFalse((self.root / "deployed.json").exists())
                self.assertFalse((self.root / "collection-attempts.txt").exists())

    def test_cross_level_route_uses_checkpoint_load_and_movement_without_inventory_assumptions(self):
        result = self.run_workflow("--scene", "traverse-route-320", "--seed-session", str(self.source))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        identity_path = next((self.root / "r36s-dumps/sh3").glob("*/scene-identity.json"))
        plan = json.loads(identity_path.read_text())["plan"]
        self.assertEqual(plan["fps_limit"], 30)
        self.assertIs(plan["profile"], True)
        self.assertEqual(plan["capture_every"], 0)
        for action in (":Return+", ":S+", ":W+", ":A+", ":D+", ":B+", ":Space+"):
            self.assertIn(action, plan["keys"])
        self.assertNotIn(":I+", plan["keys"], "save-specific inventory layout must not drive generic route")
        self.assertIn("8984E0", plan["peek"], "route needs actual player motion evidence")
        self.assertIn("72D2C0", plan["peek"], "route needs actual loaded room evidence")

    def test_full_resolution_cross_level_route_measures_movement_without_inventory_assumptions(self):
        result = self.run_workflow('--scene', 'traverse-route-640', '--seed-session', str(self.source))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        identity = json.loads(next((self.root / 'r36s-dumps/sh3').glob('*/scene-identity.json')).read_text())
        plan = identity['plan']
        self.assertEqual(plan['internal_resolution'], '640x480')
        self.assertEqual(plan['fps_limit'], 30)
        self.assertEqual(plan['capture_every'], 0)
        self.assertIs(plan['profile'], True)
        self.assertGreaterEqual(plan['seconds'], 160)
        for action in (':Return+', ':S+', ':W+', ':A+', ':D+', ':B+', ':Space+'):
            self.assertIn(action, plan['keys'])
        self.assertNotIn(':I+', plan['keys'])
        for address in ('72D2C0', '8984E0', '8984E8', '898660', '72BFD0', '72BFD4'):
            self.assertIn(address, plan['peek'])
        self.assertTrue(identity['source_preserved'])

    def test_sustained_route_keeps_active_inputs_and_profile_through_fifteen_minutes(self):
        result = self.run_workflow("--scene", "sustained-route-320", "--seed-session", str(self.source))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        identity_path = next((self.root / "r36s-dumps/sh3").glob("*/scene-identity.json"))
        plan = json.loads(identity_path.read_text())["plan"]
        self.assertGreaterEqual(plan["seconds"], 900)
        self.assertEqual(plan["fps_limit"], 30)
        self.assertIs(plan["profile"], True)
        self.assertEqual(plan["capture_every"], 0)
        self.assertNotIn(":I+", plan["keys"])
        late = [event for event in plan["keys"].split(',') if float(event.split(':')[0]) >= 840]
        for action in (":W+", ":S+", ":A+", ":D+", ":B+", ":Space+"):
            self.assertTrue(any(action in event for event in late), 'late run lacks ' + action)
        for address in ("72D2C0", "8984E0", "8984E8", "898660"):
            self.assertIn(address, plan["peek"], 'sustained verdict needs room, movement and live-state evidence')
        self.assertTrue(json.loads(identity_path.read_text())["source_preserved"])
        self.assertEqual((self.source / "savedata/data.001").read_bytes(),
                         self.contents["savedata/data.001"])

    def test_exploration_route_attempts_long_walks_and_doors_without_readied_weapon(self):
        result = self.run_workflow("--scene", "explore-route-320", "--seed-session", str(self.source))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        identity_path = next((self.root / "r36s-dumps/sh3").glob("*/scene-identity.json"))
        identity = json.loads(identity_path.read_text())
        plan = identity["plan"]
        self.assertEqual(plan["internal_resolution"], "320x240")
        self.assertEqual(plan["fps_limit"], 30)
        self.assertIs(plan["profile"], True)
        self.assertEqual(plan["capture_every"], 0)
        events = [event.split(':', 1)[1].split('+') for event in plan["keys"].split(',')]
        self.assertTrue(any(key in ('W', 'S') and float(hold) >= 10 for key, hold in events),
                        'exploration must reach beyond short back-and-forth traversal')
        self.assertGreaterEqual(sum(key == 'Space' for key, hold in events), 4,
                                'door interaction needs repeated action attempts')
        self.assertNotIn(':B+', plan['keys'], 'ready weapon changes action from door interaction to attack')
        self.assertNotIn(':I+', plan['keys'], 'generic exploration cannot assume inventory layout')
        for address in ("72D2C0", "8984E0", "8984E8", "898660"):
            self.assertIn(address, plan["peek"])
        self.assertTrue(identity["source_preserved"])


if __name__ == "__main__":
    unittest.main()
