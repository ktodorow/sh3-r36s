"""Opt-in frame costs observed through installed launcher and real checkpoint."""
import csv
from collections import Counter
import os
from pathlib import Path
import re
import shutil
from statistics import median
import subprocess
import time
import unittest

from test_preflight import LauncherFixture, REPO


@unittest.skipUnless(os.environ.get('SH3_ROUTE_TEST'), 'requires isolated opening checkpoint in ARM64 Docker')
class RouteTransitionTests(LauncherFixture):
    def test_opening_route_reaches_next_live_monster_room(self):
        from scenes import SCENES
        plan = SCENES['explore-route-320']
        runtime = self.port / 'runtime/sh3'
        runtime.parent.mkdir()
        shutil.copyfile(os.environ['SH3_RUNTIME_BINARY'], runtime)
        runtime.chmod(0o755)
        out = Path('/evidence/door-route')
        out.mkdir()
        env = {**os.environ, 'SH3_MODE': 'game', 'SH3_PORT_ROOT': str(self.port),
               'SH3_DATA_DIR': '/owner', 'SH3_SEED_SESSION': '/seed',
               'SH3_RUN_ID': 'door-route', 'SH3_PACKAGE_DIR': str(REPO),
               'XDG_DATA_HOME': str(self.root / 'xdg'), 'SH3_GL_BACKEND': 'desktop',
               'SDL_VIDEODRIVER': 'offscreen', 'SDL_AUDIODRIVER': 'dummy',
               'LIBGL_ALWAYS_SOFTWARE': '1', 'SH3_KEYS': plan['keys'],
               'SH3_PEEK': plan['peek'], 'SH3_QUIT_AFTER': str(plan['seconds']),
               'SH3_INTERNAL_RESOLUTION': plan['internal_resolution'],
               'SH3_FPS_LIMIT': str(plan['fps_limit'])}
        for key in ('SH3_SHOT', 'SH3_SHOT_EVERY', 'SH3_PRESENT_DUMP', 'SH3_PROFILE',
                    'SH3_GPU_PROFILE', 'LD_PRELOAD'):
            env.pop(key, None)
        result = subprocess.run(['bash', str(REPO / 'ports/Silent Hill 3.sh')], env=env,
                                capture_output=True, text=True, timeout=plan['seconds'] + 25)
        (out / 'stdout.txt').write_text(result.stdout)
        (out / 'stderr.txt').write_text(result.stderr)
        shutil.copytree(self.port / 'runs/door-route', out / 'launcher')
        logs = (out / 'launcher/stderr.txt').read_text()
        self.assertEqual(result.returncode, 0, logs[-4000:])
        self.assertIn('ExitProcess(0)', logs)
        rooms = {}
        for line in logs.splitlines():
            stamp = re.match(r'peek frame \d+:.*wall_ms=(\d+)', line)
            if not stamp or int(stamp[1]) < 48000:
                continue
            values = {int(k, 16): int(v, 16) for k, v in
                      re.findall(r'([0-9A-F]{8})=([0-9A-F]{8})', line)}
            room = values.get(0x72D2C0)
            rooms.setdefault(room, []).append(values)
        self.assertIn(210, rooms, 'opening checkpoint was not loaded')
        self.assertIn(211, rooms, 'route did not open door into next monster room')
        live = [v for v in rooms[211] if 0 < v[0x898660] < 0x7F800000]
        self.assertGreater(len(live), 20, 'insufficient live monster-room coverage')
        self.assertGreater(len({(v[0x8984E0], v[0x8984E8]) for v in live}), 10,
                           'player did not move through monster room')


@unittest.skipUnless(os.environ.get('SH3_PROFILE_TEST'), 'requires owner checkpoint in ARM64 Docker')
class GameProfileTests(LauncherFixture):
    def test_coarse_gl_trace_preserves_sync_and_chunk_costs_without_async_command_observation(self):
        runtime = self.port / 'runtime/sh3'
        runtime.parent.mkdir()
        shutil.copyfile(os.environ['SH3_RUNTIME_BINARY'], runtime)
        runtime.chmod(0o755)
        out = Path('/evidence/gl-coarse')
        out.mkdir()
        observer = out / 'gl-coarse.so'
        subprocess.run(['cc', '-shared', '-fPIC', str(REPO / 'tests/presentation-cost.c'),
                        '-o', str(observer), '-lSDL2', '-ldl'], check=True)

        def launch(name, coarse, trace='1', profiled=True, seconds=14):
            report = out / f'{name}.csv'
            env = {**os.environ, 'SH3_MODE': 'game', 'SH3_PORT_ROOT': str(self.port),
                   'SH3_DATA_DIR': '/owner', 'SH3_RUN_ID': name,
                   'SH3_PACKAGE_DIR': str(REPO), 'SH3_SESSION_ISOLATED': '1',
                   'XDG_DATA_HOME': str(self.root / 'xdg'), 'SH3_GL_BACKEND': 'desktop',
                   'SDL_VIDEODRIVER': 'offscreen', 'SDL_AUDIODRIVER': 'dummy',
                   'LIBGL_ALWAYS_SOFTWARE': '1', 'SH3_GPU_PROFILE': '0',
                   'SH3_INTERNAL_RESOLUTION': '320x240', 'SH3_FPS_LIMIT': '30',
                   'SH3_GL_THREAD': '1', 'SH3_KEYS': '10:Return+0.4',
                   'SH3_QUIT_AFTER': str(seconds), 'LD_PRELOAD': str(observer),
                   'SH3_TEST_GL_MS': '20', 'SH3_TEST_ASYNC_GL_MS': '20'}
            for key in ('SH3_SHOT', 'SH3_SHOT_EVERY', 'SH3_PRESENT_DUMP', 'SH3_PEEK',
                        'SH3_PROFILE', 'SH3_GL_TRACE', 'SH3_GL_DRAIN', 'SH3_GL_TRACE_COARSE',
                        'SH3_SWAP_INTERVAL', 'SH3_SEED_SESSION', 'SH3_TEST_SWAP_MS',
                        'SH3_TEST_FINISH_MS'):
                env.pop(key, None)
            if coarse is not None:
                env['SH3_GL_TRACE_COARSE'] = coarse
            if trace is not None:
                env['SH3_GL_TRACE'] = trace
            if profiled:
                env['SH3_PROFILE'] = str(report)
            result = subprocess.run(['bash', str(REPO / 'ports/Silent Hill 3.sh')], env=env,
                                    capture_output=True, text=True, timeout=seconds + 20)
            (out / f'{name}-stdout.txt').write_text(result.stdout)
            (out / f'{name}-stderr.txt').write_text(result.stderr)
            shutil.copytree(self.port / f'runs/{name}', out / name)
            self.assertIn('frontend ready', result.stdout)
            return result, report, (out / name / 'stderr.txt').read_text()

        result, report, logs = launch('coarse-on', '1')
        self.assertEqual(result.returncode, 0, logs[-3000:])
        self.assertIn('ExitProcess(0)', logs)
        delayed = re.findall(r'gl_block_boundary api=glClear wall_ms=([\d.]+) start_counter=(\d+) end_counter=(\d+)', logs)
        self.assertEqual(len(delayed), 1, 'independent asynchronous GL sleep oracle did not execute')
        wall, start, end = delayed[0]
        self.assertGreaterEqual(float(wall), 20)
        synchronous = re.findall(r'gl_block_boundary api=glGenTextures wall_ms=([\d.]+)', logs)
        self.assertEqual(len(synchronous), 1, 'independent synchronous GL sleep oracle did not execute')
        self.assertGreaterEqual(float(synchronous[0]), 20)
        with Path(str(report) + '.gl.csv').open() as stream:
            events = list(csv.DictReader(stream))
        self.assertIn('profile_gl_trace_mode=coarse', logs)
        self.assertFalse(any(e['event'] == 'command' and e['api'] == 'async' for e in events),
                         'coarse trace still observes individual asynchronous commands')
        enclosing = [e for e in events if e['lane'] == 'worker' and e['event'] == 'chunk'
                     and int(e['start_counter']) <= int(start) and int(e['end_counter']) >= int(end)]
        self.assertEqual(len(enclosing), 1, 'asynchronous driver stall missing from enclosing chunk')
        self.assertGreaterEqual(float(enclosing[0]['wall_ms']), 19)
        blocked = [e for e in events if e['lane'] == 'worker' and e['event'] == 'command'
                   and e['api'] == 'glGenTextures' and float(e['wall_ms']) >= 19]
        self.assertEqual(len(blocked), 1, 'coarse trace lost blocked synchronous GL call')
        self.assertLess(float(blocked[0]['cpu_ms']), float(blocked[0]['wall_ms']) - 15)
        waiting = [e for e in events if e['lane'] == 'producer' and e['event'] == 'sync'
                   and e['api'] == 'glGenTextures' and e['frame'] == blocked[0]['frame']
                   and e['job'] == blocked[0]['job']]
        self.assertTrue(waiting, 'coarse trace lost producer sync identity')
        with Path(str(report) + '.presents.csv').open() as stream:
            frames = {r['frame'] for r in csv.DictReader(stream)}
        self.assertIn(enclosing[0]['frame'], frames)
        self.assertIn(blocked[0]['frame'], frames)
        self.assertRegex(logs, r'profile_gl_trace lane=worker events=\d+ dropped=0')
        self.assertRegex(logs, r'profile_gl_trace lane=producer events=\d+ dropped=0')
        for index, (value, trace, profiled) in enumerate([
                ('0', '1', True), ('', '1', True), ('2', '1', True),
                ('1', None, True), ('1', '1', False), ('1', None, False)]):
            with self.subTest(coarse=value, trace=trace, profiled=profiled):
                result, report, logs = launch(f'coarse-invalid-{index}', value, trace, profiled, 1)
                self.assertEqual(result.returncode, 2, logs[-2000:])
                self.assertIn('SH3_GL_TRACE_COARSE requires SH3_PROFILE, SH3_GL_TRACE=1 and value 1', logs)
                self.assertNotIn('save:', logs)
                self.assertNotIn('CreateDevice', logs)
                self.assertFalse(Path(str(report) + '.gl.csv').exists())
        self.assertEqual(self.save.read_bytes(), b'owner save remains unchanged')

    def test_profile_only_gpu_drain_is_separate_from_actual_swap_wait(self):
        runtime = self.port / 'runtime/sh3'
        runtime.parent.mkdir()
        shutil.copyfile(os.environ['SH3_RUNTIME_BINARY'], runtime)
        runtime.chmod(0o755)
        out = Path('/evidence/gl-drain')
        out.mkdir()
        observer = out / 'gl-drain.so'
        subprocess.run(['cc', '-shared', '-fPIC', str(REPO / 'tests/presentation-cost.c'),
                        '-o', str(observer), '-lSDL2', '-ldl'], check=True)

        def launch(name, drain, trace='1', profiled=True, seconds=14):
            report = out / f'{name}.csv'
            env = {**os.environ, 'SH3_MODE': 'game', 'SH3_PORT_ROOT': str(self.port),
                   'SH3_DATA_DIR': '/owner', 'SH3_RUN_ID': name,
                   'SH3_PACKAGE_DIR': str(REPO), 'SH3_SESSION_ISOLATED': '1',
                   'XDG_DATA_HOME': str(self.root / 'xdg'), 'SH3_GL_BACKEND': 'desktop',
                   'SDL_VIDEODRIVER': 'offscreen', 'SDL_AUDIODRIVER': 'dummy',
                   'LIBGL_ALWAYS_SOFTWARE': '1', 'SH3_GPU_PROFILE': '0',
                   'SH3_INTERNAL_RESOLUTION': '320x240', 'SH3_FPS_LIMIT': '30',
                   'SH3_GL_THREAD': '1', 'SH3_KEYS': '10:Return+0.4',
                   'SH3_QUIT_AFTER': str(seconds), 'LD_PRELOAD': str(observer),
                   'SH3_TEST_FINISH_MS': '20', 'SH3_TEST_SWAP_MS': '20'}
            for key in ('SH3_SHOT', 'SH3_SHOT_EVERY', 'SH3_PRESENT_DUMP', 'SH3_PEEK',
                        'SH3_PROFILE', 'SH3_GL_TRACE', 'SH3_GL_DRAIN', 'SH3_TEST_GL_MS',
                        'SH3_SWAP_INTERVAL', 'SH3_SEED_SESSION', 'SH3_GL_TRACE_COARSE',
                        'SH3_TEST_ASYNC_GL_MS'):
                env.pop(key, None)
            if drain is not None:
                env['SH3_GL_DRAIN'] = drain
            if trace is not None:
                env['SH3_GL_TRACE'] = trace
            if profiled:
                env['SH3_PROFILE'] = str(report)
            result = subprocess.run(['bash', str(REPO / 'ports/Silent Hill 3.sh')], env=env,
                                    capture_output=True, text=True, timeout=seconds + 20)
            (out / f'{name}-stdout.txt').write_text(result.stdout)
            (out / f'{name}-stderr.txt').write_text(result.stderr)
            shutil.copytree(self.port / f'runs/{name}', out / name)
            self.assertIn('frontend ready', result.stdout)
            return result, report, (out / name / 'stderr.txt').read_text()

        result, report, logs = launch('drain-on', '1')
        self.assertEqual(result.returncode, 0, logs[-3000:])
        self.assertIn('ExitProcess(0)', logs)
        boundaries = re.findall(r'presentation_boundary screen=1 offscreen=\d+ finish=(\d+) finish_ms=([\d.]+) swap_ms=([\d.]+)', logs)
        self.assertGreater(len(boundaries), 10)
        self.assertTrue(all(int(calls) == 1 for calls, _, _ in boundaries),
                        'diagnostic did not finish GL exactly once before each real SDL swap')
        self.assertTrue(all(float(wall) >= 20 for _, wall, _ in boundaries))
        with Path(str(report) + '.gl.csv').open() as stream:
            events = list(csv.DictReader(stream))
        drains = [e for e in events if e['event'] == 'drain' and e['api'] == 'glFinish']
        with Path(str(report) + '.presents.csv').open() as stream:
            presents = list(csv.DictReader(stream))
        self.assertEqual(len(drains), len(boundaries))
        self.assertEqual([e['frame'] for e in drains], [r['frame'] for r in presents])
        for drain, present in zip(drains, presents):
            self.assertEqual(drain['lane'], 'worker')
            self.assertGreaterEqual(float(drain['wall_ms']), 19)
            self.assertLess(float(drain['cpu_ms']), float(drain['wall_ms']) - 15,
                            'independent GPU-drain sleep counted as CPU')
            self.assertGreaterEqual(float(present['swap_ms']), 19)
        # Compare to measured external Swap, whose scheduling/driver cost can exceed20ms.
        # Including the distinct Finish delay would shift this median by at least20ms.
        swap_errors = [abs(float(present['swap_ms']) - float(boundary[2]))
                       for present, boundary in zip(presents, boundaries)]
        self.assertLess(median(swap_errors), 2,
                        'separate drain sleep leaked into SDL swap interval')
        self.assertRegex(logs, r'profile_clock_end raw_before_ns=\d+ monotonic_before_ns=\d+ realtime_before_ns=\d+ sdl_ticks_ms=\d+ perf_counter=\d+ perf_frequency=\d+ realtime_after_ns=\d+ monotonic_after_ns=\d+ raw_after_ns=\d+')

        result, report, logs = launch('drain-off', None)
        self.assertEqual(result.returncode, 0, logs[-3000:])
        self.assertNotRegex(logs, r'presentation_boundary .* finish=[1-9]')
        with Path(str(report) + '.gl.csv').open() as stream:
            self.assertFalse(any(e['event'] == 'drain' for e in csv.DictReader(stream)))
        for index, (value, trace, profiled) in enumerate([
                ('0', '1', True), ('', '1', True), ('2', '1', True),
                ('1', None, True), ('1', None, False)]):
            with self.subTest(drain=value, trace=trace, profiled=profiled):
                result, report, logs = launch(f'drain-invalid-{index}', value, trace, profiled, 1)
                self.assertEqual(result.returncode, 2, logs[-2000:])
                self.assertIn('SH3_GL_DRAIN requires SH3_PROFILE, SH3_GL_TRACE=1 and value 1', logs)
                self.assertNotIn('save:', logs)
                self.assertNotIn('CreateDevice', logs)
                self.assertFalse(Path(str(report) + '.gl.csv').exists())
        self.assertEqual(self.save.read_bytes(), b'owner save remains unchanged')

    def test_opt_in_gl_trace_localizes_blocked_driver_and_producer_wait(self):
        runtime = self.port / 'runtime/sh3'
        runtime.parent.mkdir()
        shutil.copyfile(os.environ['SH3_RUNTIME_BINARY'], runtime)
        runtime.chmod(0o755)
        out = Path('/evidence/gl-trace')
        out.mkdir()
        observer = out / 'gl-trace.so'
        subprocess.run(['cc', '-shared', '-fPIC', str(REPO / 'tests/presentation-cost.c'),
                        '-o', str(observer), '-lSDL2', '-ldl'], check=True)

        def launch(name, trace, profiled=True, seconds=14):
            report = out / f'{name}.csv'
            env = {**os.environ, 'SH3_MODE': 'game', 'SH3_PORT_ROOT': str(self.port),
                   'SH3_DATA_DIR': '/owner', 'SH3_RUN_ID': name,
                   'SH3_PACKAGE_DIR': str(REPO), 'SH3_SESSION_ISOLATED': '1',
                   'XDG_DATA_HOME': str(self.root / 'xdg'), 'SH3_GL_BACKEND': 'desktop',
                   'SDL_VIDEODRIVER': 'offscreen', 'SDL_AUDIODRIVER': 'dummy',
                   'LIBGL_ALWAYS_SOFTWARE': '1', 'SH3_GPU_PROFILE': '0',
                   'SH3_GL_THREAD': '1',
                   'SH3_INTERNAL_RESOLUTION': '320x240', 'SH3_FPS_LIMIT': '30',
                   'SH3_QUIT_AFTER': str(seconds), 'LD_PRELOAD': str(observer),
                   'SH3_TEST_GL_MS': '20'}
            for key in ('SH3_SHOT', 'SH3_SHOT_EVERY', 'SH3_PRESENT_DUMP', 'SH3_PEEK',
                        'SH3_PROFILE', 'SH3_GL_TRACE', 'SH3_GL_DRAIN', 'SH3_KEYS',
                        'SH3_SWAP_INTERVAL', 'SH3_SEED_SESSION', 'SH3_TEST_SWAP_MS',
                        'SH3_GL_TRACE_COARSE', 'SH3_TEST_ASYNC_GL_MS'):
                env.pop(key, None)
            if trace is not None:
                env['SH3_GL_TRACE'] = trace
            if profiled:
                env['SH3_PROFILE'] = str(report)
            env['SH3_KEYS'] = '10:Return+0.4'
            before = time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW)
            result = subprocess.run(['bash', str(REPO / 'ports/Silent Hill 3.sh')], env=env,
                                    capture_output=True, text=True, timeout=seconds + 20)
            after = time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW)
            (out / f'{name}-stdout.txt').write_text(result.stdout)
            (out / f'{name}-stderr.txt').write_text(result.stderr)
            shutil.copytree(self.port / f'runs/{name}', out / name)
            logs = (out / name / 'stderr.txt').read_text()
            self.assertIn('frontend ready', result.stdout)
            return result, report, logs, before, after

        result, report, logs, before, after = launch('trace-on', '1')
        self.assertEqual(result.returncode, 0, logs[-3000:])
        self.assertIn('ExitProcess(0)', logs)
        self.assertIn('profile_gl_trace_mode=full', logs)
        delayed = re.findall(r'gl_block_boundary api=glGenTextures wall_ms=([\d.]+)', logs)
        self.assertEqual(len(delayed), 1, 'independent GL sleep oracle did not execute')
        self.assertGreaterEqual(float(delayed[0]), 20)
        trace_path = Path(str(report) + '.gl.csv')
        self.assertTrue(trace_path.is_file(), 'requested GL critical-path trace missing')
        with trace_path.open() as stream:
            events = list(csv.DictReader(stream))
        blocked = [e for e in events if e['lane'] == 'worker' and e['event'] == 'command'
                   and e['api'] == 'glGenTextures' and float(e['wall_ms']) >= 19]
        self.assertEqual(len(blocked), 1, 'trace did not isolate delayed real GL driver call')
        self.assertLess(float(blocked[0]['cpu_ms']), float(blocked[0]['wall_ms']) - 15,
                        'blocked GL sleep was counted as thread CPU')
        waiting = [e for e in events if e['lane'] == 'producer' and e['event'] == 'sync'
                   and e['api'] == 'glGenTextures' and e['job'] == blocked[0]['job']
                   and e['frame'] == blocked[0]['frame'] and float(e['wall_ms']) >= 19]
        self.assertTrue(waiting, 'producer sync wait lacks API and timeline identity')
        self.assertLess(float(waiting[0]['cpu_ms']), float(waiting[0]['wall_ms']) - 15)
        self.assertLessEqual(int(waiting[0]['start_counter']), int(blocked[0]['start_counter']))
        self.assertGreaterEqual(int(waiting[0]['end_counter']), int(blocked[0]['end_counter']))
        self.assertTrue(any(e['event'] == 'chunk' and float(e['wall_ms']) >= 19 for e in events))
        with Path(str(report) + '.presents.csv').open() as stream:
            frames = {r['frame'] for r in csv.DictReader(stream)}
        self.assertIn(blocked[0]['frame'], frames, 'trace frame cannot join actual completion')
        anchors = re.findall(
            r'profile_clock raw_before_ns=(\d+) monotonic_before_ns=(\d+) realtime_before_ns=(\d+) '
            r'sdl_ticks_ms=(\d+) perf_counter=(\d+) perf_frequency=(\d+) realtime_after_ns=(\d+) '
            r'monotonic_after_ns=(\d+) raw_after_ns=(\d+)', logs)
        self.assertEqual(len(anchors), 1, 'SDL/RAW/MONOTONIC epoch cannot be correlated')
        raw0, mono0, real0, ticks, counter, frequency, real1, mono1, raw1 = map(int, anchors[0])
        self.assertLessEqual(before, raw0)
        self.assertLessEqual(raw0, raw1)
        self.assertLessEqual(raw1, after)
        self.assertLess(raw1 - raw0, 10_000_000, 'clock correlation bracket too broad')
        self.assertLessEqual(mono0, mono1)
        self.assertLessEqual(real0, real1)
        self.assertGreater(real0, 1_000_000_000_000_000_000)
        self.assertGreater(counter, 0)
        self.assertGreater(frequency, 0)
        self.assertLess(ticks, 14_000)
        self.assertRegex(logs, r'profile_gl_provider video=offscreen sdl=\d+\.\d+\.\d+ library=\S+')
        self.assertRegex(logs, r'profile_gl_trace lane=worker events=\d+ dropped=0')
        self.assertRegex(logs, r'profile_gl_trace lane=producer events=\d+ dropped=0')

        result, report, logs, _, _ = launch('trace-off', None, False)
        self.assertEqual(result.returncode, 0, logs[-3000:])
        self.assertFalse(Path(str(report) + '.gl.csv').exists())
        self.assertNotIn('profile_clock', logs)
        self.assertNotIn('profile_gl_trace', logs)
        self.assertNotIn('profile_gl_provider', logs)
        for index, (value, profiled) in enumerate([('0', True), ('', True), ('2', True), ('1', False)]):
            with self.subTest(trace=value, profiled=profiled):
                result, report, logs, _, _ = launch(f'trace-invalid-{index}', value, profiled, 1)
                self.assertEqual(result.returncode, 2, logs[-2000:])
                self.assertIn('SH3_GL_TRACE requires SH3_PROFILE and value 1', logs)
                self.assertNotIn('save:', logs)
                self.assertNotIn('CreateDevice', logs)
                self.assertFalse(Path(str(report) + '.gl.csv').exists())
        self.assertEqual(self.save.read_bytes(), b'owner save remains unchanged')

    def test_profiled_swap_override_records_driver_status_and_rejects_invalid_settings(self):
        runtime = self.port / 'runtime/sh3'
        runtime.parent.mkdir()
        shutil.copyfile(os.environ['SH3_RUNTIME_BINARY'], runtime)
        runtime.chmod(0o755)
        out = Path('/evidence/swap-interval')
        out.mkdir()
        observer = out / 'swap-interval.so'
        subprocess.run(['cc', '-shared', '-fPIC', str(REPO / 'tests/presentation-cost.c'),
                        '-o', str(observer), '-lSDL2', '-ldl'], check=True)
        settings = [('0', True), ('1', True), ('2', True), ('-1', True),
                    ('fast', True), ('', True), ('0', False)]
        for index, (interval, profiled) in enumerate(settings):
            with self.subTest(interval=interval, profiled=profiled):
                name = f'swap-{index}'
                report = out / f'{name}.csv'
                env = {**os.environ, 'SH3_MODE': 'game', 'SH3_PORT_ROOT': str(self.port),
                       'SH3_DATA_DIR': '/owner', 'SH3_RUN_ID': name,
                       'SH3_PACKAGE_DIR': str(REPO), 'SH3_SESSION_ISOLATED': '1',
                       'XDG_DATA_HOME': str(self.root / 'xdg'), 'SH3_GL_BACKEND': 'desktop',
                       'SDL_VIDEODRIVER': 'offscreen', 'SDL_AUDIODRIVER': 'dummy',
                       'LIBGL_ALWAYS_SOFTWARE': '1', 'SH3_GPU_PROFILE': '0',
                       'SH3_INTERNAL_RESOLUTION': '320x240', 'SH3_FPS_LIMIT': '30',
                       'SH3_KEYS': '10:Return+0.4', 'SH3_QUIT_AFTER': '14',
                       'SH3_SWAP_INTERVAL': interval, 'LD_PRELOAD': str(observer)}
                for key in ('SH3_SHOT', 'SH3_SHOT_EVERY', 'SH3_PRESENT_DUMP', 'SH3_PEEK',
                            'SH3_PROFILE', 'SH3_TEST_SWAP_MS', 'SH3_SEED_SESSION'):
                    env.pop(key, None)
                if profiled:
                    env['SH3_PROFILE'] = str(report)
                result = subprocess.run(['bash', str(REPO / 'ports/Silent Hill 3.sh')], env=env,
                                        capture_output=True, text=True, timeout=30)
                (out / f'{name}-stdout.txt').write_text(result.stdout)
                (out / f'{name}-stderr.txt').write_text(result.stderr)
                shutil.copytree(self.port / f'runs/{name}', out / name)
                logs = (out / name / 'stderr.txt').read_text()
                self.assertIn('frontend ready', result.stdout)
                observed = re.findall(
                    r'swap_interval_boundary requested=(-?\d+) result=(-?\d+) effective=(-?\d+)', logs)
                if interval in ('0', '1') and profiled:
                    self.assertEqual(result.returncode, 0, logs[-3000:])
                    self.assertIn('ExitProcess(0)', logs)
                    self.assertEqual(len(observed), 1, 'missing actual SDL swap configuration')
                    requested, status, effective = observed[0]
                    self.assertEqual(requested, interval, 'diagnostic swap request ignored')
                    self.assertIn(f'gl_swap_interval requested={requested} result={status} effective={effective}',
                                  logs, 'native report does not match actual SDL result')
                    with Path(str(report) + '.presents.csv').open() as stream:
                        self.assertGreater(len(list(csv.DictReader(stream))), 10)
                    self.assertNotIn('capture frame', logs)
                else:
                    self.assertEqual(result.returncode, 2, logs[-3000:])
                    self.assertIn('SH3_SWAP_INTERVAL requires SH3_PROFILE and value 0 or 1', logs)
                    self.assertEqual(observed, [], 'invalid setting reached real GL context')
                    self.assertNotIn('save:', logs, 'invalid setting started guest file access')
                    self.assertNotIn('CreateDevice', logs, 'invalid setting started game rendering')
        self.assertEqual(self.save.read_bytes(), b'owner save remains unchanged')

    def test_near_budget_checkpoint_does_not_latch_to_twenty_fps(self):
        runtime = self.port / 'runtime/sh3'
        runtime.parent.mkdir()
        shutil.copyfile(os.environ['SH3_RUNTIME_BINARY'], runtime)
        runtime.chmod(0o755)
        out = Path('/evidence/frame-budget')
        out.mkdir()
        observer = out / 'frame-budget.so'
        subprocess.run(['cc', '-shared', '-fPIC', str(REPO / 'tests/frame-budget.c'),
                        '-o', str(observer), '-lSDL2', '-ldl'], check=True)
        report = out / 'frames.csv'
        env = {**os.environ, 'SH3_MODE': 'game', 'SH3_PORT_ROOT': str(self.port),
               'SH3_DATA_DIR': '/owner', 'SH3_SEED_SESSION': '/seed',
               'SH3_RUN_ID': 'frame-budget', 'SH3_PACKAGE_DIR': str(REPO),
               'XDG_DATA_HOME': str(self.root / 'xdg'), 'SH3_GL_BACKEND': 'desktop',
               'SDL_VIDEODRIVER': 'offscreen', 'SDL_AUDIODRIVER': 'dummy',
               'LIBGL_ALWAYS_SOFTWARE': '1', 'SH3_PROFILE': str(report),
               'SH3_GPU_PROFILE': '0', 'SH3_INTERNAL_RESOLUTION': '320x240',
               'SH3_KEYS': '10:Return+0.4,30:Down+0.2,32:Return+0.4,34:Return+0.4,36:Return+0.4',
               'SH3_QUIT_AFTER': '64', 'SH3_FPS_LIMIT': '30',
               'LD_PRELOAD': str(observer)}
        for key in ('SH3_SHOT', 'SH3_SHOT_EVERY', 'SH3_PRESENT_DUMP', 'SH3_PEEK'):
            env.pop(key, None)
        result = subprocess.run(['bash', str(REPO / 'ports/Silent Hill 3.sh')], env=env,
                                capture_output=True, text=True, timeout=80)
        (out / 'stdout.txt').write_text(result.stdout)
        (out / 'stderr.txt').write_text(result.stderr)
        shutil.copytree(self.port / 'runs/frame-budget', out / 'launcher')
        logs = (out / 'launcher/stderr.txt').read_text()
        self.assertEqual(result.returncode, 0, logs[-3000:])
        self.assertIn('ExitProcess(0)', logs)
        delayed = re.findall(r'frame_budget delayed_input_polls=(\d+) delay_ms=32', logs)
        self.assertEqual(len(delayed), 1, 'missing actual input-latency observation')
        self.assertGreater(int(delayed[0]), 200, 'near-budget workload did not run')
        measured = re.findall(r'frame_budget .* observed_mean_ms=([\d.]+) observed_max_ms=([\d.]+)', logs)
        self.assertEqual(len(measured), 1, 'missing calibrated external delay')
        self.assertGreaterEqual(float(measured[0][0]), 32)
        self.assertLessEqual(float(measured[0][0]), 33, 'injected delay exceeds stated workload')
        with Path(str(report) + '.presents.csv').open() as stream:
            active = [r for r in csv.DictReader(stream)
                      if 52000 <= int(r['elapsed_ms']) < 60000]
        self.assertTrue(active)
        self.assertEqual({r['room'] for r in active}, {'210'}, 'checkpoint not active')
        windows = Counter(int(r['elapsed_ms']) // 1000 for r in active)
        self.assertEqual(set(windows), set(range(52, 60)))
        self.assertGreaterEqual(min(windows.values()), 25,
                                'timer adds 20FPS cap to near-budget gameplay')

    def test_paced_menu_prepares_input_while_completed_swap_is_throttled(self):
        runtime = self.port / 'runtime/sh3'
        runtime.parent.mkdir()
        shutil.copyfile(os.environ['SH3_RUNTIME_BINARY'], runtime)
        runtime.chmod(0o755)
        out = Path('/evidence/pacing-overlap')
        out.mkdir()
        observer = out / 'pacing-overlap.so'
        subprocess.run(['cc', '-shared', '-fPIC', str(REPO / 'tests/pacing-overlap.c'),
                        '-o', str(observer), '-lSDL2', '-ldl'], check=True)
        env = {**os.environ, 'SH3_MODE': 'game', 'SH3_PORT_ROOT': str(self.port),
               'SH3_DATA_DIR': '/owner', 'SH3_RUN_ID': 'pacing-overlap',
               'SH3_PACKAGE_DIR': str(REPO), 'XDG_DATA_HOME': str(self.root / 'xdg'),
               'SH3_GL_BACKEND': 'desktop', 'SDL_VIDEODRIVER': 'offscreen',
               'SDL_AUDIODRIVER': 'dummy', 'LIBGL_ALWAYS_SOFTWARE': '1',
               'SH3_KEYS': '10:Return+0.4', 'SH3_QUIT_AFTER': '28',
               'SH3_INTERNAL_RESOLUTION': '320x240', 'SH3_FPS_LIMIT': '30',
               'SH3_GL_THREAD': '1', 'LD_PRELOAD': str(observer)}
        for key in ('SH3_SHOT', 'SH3_SHOT_EVERY', 'SH3_PRESENT_DUMP', 'SH3_PEEK',
                    'SH3_PROFILE', 'SH3_GPU_PROFILE'):
            env.pop(key, None)
        result = subprocess.run(['bash', str(REPO / 'ports/Silent Hill 3.sh')], env=env,
                                capture_output=True, text=True, timeout=45)
        (out / 'stdout.txt').write_text(result.stdout)
        (out / 'stderr.txt').write_text(result.stderr)
        shutil.copytree(self.port / 'runs/pacing-overlap', out / 'launcher')
        logs = (out / 'launcher/stderr.txt').read_text()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr + logs[-2000:])
        self.assertIn('ExitProcess(0)', logs)
        matches = [tuple(map(int, match)) for match in re.findall(
            r'pacing_overlap sleeps=(\d+) productive=(\d+) input_polls=(\d+) total_polls=(\d+)', logs)
                   if int(match[0])]
        self.assertEqual(len(matches), 1)
        sleeps, productive, polls, total_polls = matches[0]
        self.assertGreater(sleeps, 50, 'observer missed actual render-worker throttle')
        self.assertGreater(total_polls, 50, 'observer missed real game input')
        self.assertGreaterEqual(productive / sleeps, 0.8,
                                'CPU waits for throttle after SDL has already completed swap')

    def test_thirty_fps_profile_paces_actual_menu_completions_without_capture(self):
        runtime = self.port / 'runtime/sh3'
        runtime.parent.mkdir()
        shutil.copyfile(os.environ['SH3_RUNTIME_BINARY'], runtime)
        runtime.chmod(0o755)
        out = Path('/evidence/paced-menu')
        out.mkdir()
        report = out / 'paced-frame-times.csv'
        env = {**os.environ, 'SH3_MODE': 'game', 'SH3_PORT_ROOT': str(self.port),
               'SH3_DATA_DIR': '/owner', 'SH3_RUN_ID': 'paced-menu',
               'SH3_PACKAGE_DIR': str(REPO), 'XDG_DATA_HOME': str(self.root / 'xdg'),
               'SH3_GL_BACKEND': 'desktop', 'SDL_VIDEODRIVER': 'offscreen',
               'SDL_AUDIODRIVER': 'dummy', 'LIBGL_ALWAYS_SOFTWARE': '1',
               'SH3_PROFILE': str(report), 'SH3_GPU_PROFILE': '0',
               'SH3_KEYS': '10:Return+0.4', 'SH3_QUIT_AFTER': '28',
               'SH3_INTERNAL_RESOLUTION': '320x240', 'SH3_FPS_LIMIT': '30'}
        for key in ('SH3_SHOT', 'SH3_SHOT_EVERY', 'SH3_PRESENT_DUMP', 'SH3_PEEK', 'LD_PRELOAD'):
            env.pop(key, None)
        result = subprocess.run(['bash', str(REPO / 'ports/Silent Hill 3.sh')], env=env,
                                capture_output=True, text=True, timeout=45)
        (out / 'paced-stdout.txt').write_text(result.stdout)
        (out / 'paced-stderr.txt').write_text(result.stderr)
        shutil.copytree(self.port / 'runs/paced-menu', out / 'launcher')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        logs = (out / 'launcher/stderr.txt').read_text()
        self.assertIn('ExitProcess(0)', logs)
        self.assertNotIn('capture frame', logs)
        with Path(str(report) + '.presents.csv').open() as stream:
            completed = [r for r in csv.DictReader(stream)
                         if r['room'] == '0' and 15000 < float(r['elapsed_ms']) < 26000]
        self.assertGreater(len(completed), 100, 'real game menu did not remain active')
        intervals = [float(b['elapsed_ms']) - float(a['elapsed_ms'])
                     for a, b in zip(completed, completed[1:])]
        fps = 1000 * len(intervals) / sum(intervals)
        self.assertLessEqual(fps, 30.5, '30FPS profile wastes work rendering menu above target')
        self.assertGreaterEqual(fps, 28.5, 'pacing introduces avoidable menu slowdown')
        windows = Counter(int(float(r['elapsed_ms']) // 1000) for r in completed)
        self.assertLessEqual(max(windows.values()), 31, 'late frame caused catch-up burst')

    def test_checkpoint_reports_frame_costs_without_capturing_pixels(self):
        runtime = self.port / 'runtime/sh3'
        runtime.parent.mkdir()
        shutil.copyfile(os.environ['SH3_RUNTIME_BINARY'], runtime)
        runtime.chmod(0o755)
        out = Path('/evidence')
        report = out / 'frame-times.csv'
        observer = out / 'input-cost.so'
        subprocess.run(['cc', '-shared', '-fPIC', str(REPO / 'tests/input-cost.c'),
                        '-o', str(observer), '-lSDL2', '-ldl'], check=True)
        swap_observer = out / 'swap-cost.so'
        subprocess.run(['cc', '-shared', '-fPIC', str(REPO / 'tests/presentation-cost.c'),
                        '-o', str(swap_observer), '-lSDL2', '-ldl'], check=True)
        env = {**os.environ, 'SH3_MODE': 'game', 'SH3_PORT_ROOT': str(self.port),
               'SH3_SEED_SESSION': '/seed', 'SH3_DATA_DIR': '/owner',
               'SH3_RUN_ID': 'profile', 'SH3_PACKAGE_DIR': str(REPO),
               'XDG_DATA_HOME': str(self.root / 'xdg'), 'SH3_GL_BACKEND': 'desktop',
               'SDL_VIDEODRIVER': 'offscreen', 'SDL_AUDIODRIVER': 'dummy',
               'LIBGL_ALWAYS_SOFTWARE': '1', 'SH3_PROFILE': str(report),
               'SH3_PEEK': '72D2C0',
               'LD_PRELOAD': str(observer) + ':' + str(swap_observer), 'SH3_TEST_SWAP_MS': '20',
               'SH3_KEYS': '10:Return+0.4,30:Down+0.2,32:Return+0.4,34:Return+0.4,36:Return+0.4',
               'SH3_QUIT_AFTER': '62', 'SH3_INTERNAL_RESOLUTION': '640x480'}
        for key in ('SH3_SHOT', 'SH3_SHOT_EVERY', 'SH3_PRESENT_DUMP', 'SH3_GPU_PROFILE', 'SH3_SWAP_INTERVAL'):
            env.pop(key, None)
        with (out / 'game-stdout.txt').open('w') as stdout, (out / 'game-stderr.txt').open('w') as stderr:
            result = subprocess.run(['bash', str(REPO / 'ports/Silent Hill 3.sh')], env=env,
                                    stdout=stdout, stderr=stderr, timeout=75)
        run = self.port / 'runs/profile'
        shutil.copytree(run, out / 'launcher')
        logs = (run / 'stderr.txt').read_text()
        self.assertEqual(result.returncode, 0, logs[-4000:])
        defaults = re.findall(r'swap_interval_boundary requested=1 result=(-?\d+) effective=(-?\d+)', logs)
        self.assertEqual(len(defaults), 1, 'default swap request changed from retrace synchronization')
        status, effective = defaults[0]
        self.assertIn(f'gl_swap_interval requested=1 result={status} effective={effective}', logs)
        self.assertNotIn('gpu_profile=enabled', (run / 'stdout.txt').read_text(),
                         'frame-cadence profiling unexpectedly enabled costly GPU queries')
        self.assertFalse(Path(str(report) + '.gpu.csv').exists())
        self.assertIn('frontend ready', (out / 'game-stdout.txt').read_text())
        self.assertIn('save: open C:\\SH3\\savedata\\data.001 access 80000000 disposition 3 -> ok', logs)
        self.assertNotIn('capture frame', logs)
        self.assertTrue(report.is_file(), 'requested per-frame costs missing')
        with report.open() as stream:
            rows = list(csv.DictReader(stream))
        active = [row for row in rows if row['room'] == '210' and float(row['elapsed_ms']) > 50000]
        self.assertGreater(len(active), 10, 'missing warmed real-checkpoint frames')
        sparse = re.findall(r'peek frame (\d+):[^\n]*wall_ms=(\d+)', logs)
        self.assertGreater(len(sparse), 10, 'sparse scene observations lack native wall timestamps')
        by_frame = {int(row['frame']): row for row in rows}
        previous_wall = -1
        for frame, wall in sparse:
            wall = int(wall)
            self.assertGreater(wall, previous_wall)
            previous_wall = wall
            self.assertIn(int(frame), by_frame)
            self.assertLess(abs(wall - float(by_frame[int(frame)]['elapsed_ms'])), 500,
                            'sparse observation uses a different clock than native frame report')
        for row in active:
            wall = float(row['wall_ms'])
            self.assertGreater(wall, 0)
            self.assertGreaterEqual(float(row['cpu_ms']), 0)
            self.assertLessEqual(float(row['cpu_ms']), wall * 1.1 + 1)
            self.assertGreater(float(row['draw_ms']), 0)
            self.assertLessEqual(float(row['draw_ms']) + float(row['present_ms']), wall + 0.1)
            self.assertLessEqual(float(row['swap_ms']), float(row['present_ms']) + 0.1)
            self.assertGreater(int(row['draws']), 0)
            self.assertEqual((int(row['internal_w']), int(row['internal_h'])), (640, 480))
        completed = Path(str(report) + '.presents.csv')
        self.assertTrue(completed.is_file(), 'missing actual SDL swap completion timings')
        with completed.open() as stream:
            presents = list(csv.DictReader(stream))
        swaps = re.findall(r'presentation_boundary screen=1 offscreen=\d+', logs)
        self.assertEqual(len(presents), len(swaps), 'completion log does not match actual SDL swaps')
        active_presents = [row for row in presents if row['room']=='210' and float(row['elapsed_ms'])>50000]
        self.assertGreater(len(active_presents), 10)
        frames = [int(row['frame']) for row in presents]
        self.assertEqual(frames, sorted(set(frames)))
        for row in active_presents:
            self.assertGreaterEqual(float(row['swap_ms']), 19,
                                    'timing missed delay at actual worker SDL boundary')
            self.assertGreater(float(row['wall_ms']), 0)
            self.assertGreater(float(row.get('worker_cpu_ms', 0)), 0,
                               'completion report omits render-worker CPU time')
            self.assertGreaterEqual(float(row.get('swap_cpu_ms', -1)), 0,
                                    'completion report omits on-CPU swap cost')
            self.assertLess(float(row['swap_cpu_ms']), float(row['swap_ms']) - 15,
                            'blocked SDL sleep was counted as render-worker CPU')
            self.assertLessEqual(float(row['swap_cpu_ms']), float(row['worker_cpu_ms']) + 0.1)
            self.assertLessEqual(float(row['worker_cpu_ms']), float(row['wall_ms']) * 1.1 + 1)
            self.assertEqual((int(row['internal_w']),int(row['internal_h'])), (640,480))
        for previous, current in zip(presents,presents[1:]):
            self.assertGreaterEqual(int(current['elapsed_ms']),int(previous['elapsed_ms']))
        samples = Path(str(report) + '.samples')
        self.assertTrue(samples.is_file(), 'requested CPU hotspot samples missing')
        with samples.open() as stream:
            costs = list(csv.DictReader(stream))
        self.assertGreater(len(costs), 10, 'CPU sampler did not observe running game')
        self.assertTrue(any(row['module'].endswith('/sh3') for row in costs), 'native game code not sampled')
        self.assertTrue(all(int(row['pc'], 16) > 0 and int(row['offset'], 16) >= 0 for row in costs))
        self.assertTrue(all(row.get('caller_module') for row in costs), 'CPU samples omit caller location')
        self.assertTrue(any(row['caller_module'].endswith('/sh3') for row in costs),
                        'CPU sampler did not retain native caller locations')
        calls = re.findall(r'input_boundary polls=(\d+) names=(\d+)', logs)
        self.assertEqual(len(calls), 1, 'missing real keyboard boundary observation')
        polls, names = map(int, calls[0])
        self.assertGreater(polls, 10)
        # Five fixed events plus generous margin for SDL's own initialization.
        self.assertLessEqual(names, 128,
                             'scripted input repeatedly decodes unchanged schedule at every poll')
