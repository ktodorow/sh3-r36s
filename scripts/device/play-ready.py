#!/usr/bin/env python3
"""SH3-only personal-play maintenance. Output streams to host evidence."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET


def digest(path):
    checksum = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            checksum.update(block)
    return checksum.hexdigest()


def maintenance_processes(root):
    result = []
    for proc in Path('/proc').glob('[0-9]*'):
        try:
            args = proc.joinpath('cmdline').read_bytes().decode().split('\0')
            if (int(proc.name) == os.getpid() or Path(args[0]).name not in ('python3', 'bash', 'sh3', 'api-example') or
                    not any(a == str(root) or a.startswith(str(root) + '/') or
                            a == str(root.parent / 'Silent Hill 3.sh') for a in args)):
                continue
            directories = []
            for fd in (proc / 'fd').iterdir():
                target = os.readlink(fd)
                if target.startswith(str(root)):
                    directories.append(target)
            result.append({'pid': int(proc.name), 'argv': [a for a in args if a],
                           'wchan': proc.joinpath('wchan').read_text().strip(),
                           'io': proc.joinpath('io').read_text(), 'open_paths': directories})
        except (OSError, UnicodeError):
            continue
    return result


def inspect(root, hash_assets=False):
    print('play-inspect: top-level entries', file=sys.stderr, flush=True)
    entries = []
    for path in sorted(root.iterdir()):
        entries.append({'path': path.name, 'symlink': path.is_symlink(),
                        'directory': path.is_dir(),
                        'bytes': path.stat().st_size if path.is_file() else None})
    print('play-inspect: saves and layouts', file=sys.stderr, flush=True)
    saves = []
    for directory in [root / 'state/savedata', root / 'gamedata/savedata', root / 'savedata']:
        saves.extend(str(p.relative_to(root)) for p in sorted(directory.glob('data.*')) if p.is_file())
    diagnostics = [p.name for p in sorted(root.iterdir())
                   if p.name == 'runs' or p.suffix == '.log']
    assets = {}
    print('play-inspect: asset identities', file=sys.stderr, flush=True)
    for path in [root / 'gamedata/sh3.exe', *sorted((root / 'gamedata/data').rglob('*'))]:
        if path.is_file():
            value = path.stat()
            assets[str(path.relative_to(root))] = {'bytes': value.st_size, 'mtime_ns': value.st_mtime_ns}
            if hash_assets or path.name == 'sh3.exe':
                assets[str(path.relative_to(root))]['sha256'] = digest(path)
    menus = {p.name: {'sha256': digest(p), 'header': p.read_text(errors='replace').splitlines()[:3]}
             for p in sorted(root.parent.glob('Silent Hill 3*.sh')) if p.is_file()}
    layouts = {name: sorted(p.name for p in (root / name).iterdir())
               for name in ['runtime', 'state', 'state/savedata', 'gamedata', 'preflight',
                            'preflight/ports', 'preflight/scripts/device'] if (root / name).is_dir()}
    state_files = {str(p.relative_to(root)): {'bytes': p.stat().st_size, 'sha256': digest(p)}
                   for p in [root / 'state/savedata/data.sys', root / 'state/savedata/key.ini',
                             root / 'state/sh3-gl-cache.bin', root / 'state/sh3-progs.bin'] if p.is_file()}
    gamelist = root.parent / 'gamelist.xml'
    metadata = [{'path': game.findtext('path'), 'name': game.findtext('name')}
                for game in ET.parse(gamelist).getroot().findall('game')
                if 'Silent Hill 3' in (game.findtext('path') or '')] if gamelist.is_file() else []
    return {'entries': entries, 'saves': saves, 'diagnostics': diagnostics,
            'assets': assets, 'menus': menus, 'layouts': layouts,
            'state_files': state_files, 'menu_metadata': metadata, 'user_id': os.geteuid(),
            'maintenance': maintenance_processes(root),
            'temporary_controls': sorted(str(p) for p in Path('/tmp').glob('sh3-r36s-*')),
            'run_entries': sorted(p.name for p in (root / 'runs').iterdir()) if (root / 'runs').is_dir() else []}


def inactive():
    result = subprocess.run(['pgrep', '-x', 'sh3'], capture_output=True)
    if result.returncode != 1:
        raise ValueError('game active or process check unavailable')


def clean(root):
    inactive()
    if (root / '.performance-policy-owner.json').exists():
        raise ValueError('pending clock recovery must finish before cleanup')
    if not (root / 'runtime/.sh3-runtime-owned').is_file():
        raise ValueError('runtime ownership marker missing')
    targets = []
    for directory in [root / 'state/savedata', root / 'gamedata/savedata', root / 'savedata']:
        if directory.exists():
            if directory.resolve() != directory:
                raise ValueError('save directory is a symlink')
            targets.extend(p for p in directory.iterdir()
                           if re.fullmatch(r'data\.(?:[0-9]{3}|sys)', p.name))
    for directory in [root, root / 'state', root / 'gamedata']:
        targets.extend(p for name in ['sh3.log', 'sh3-crash.log']
                       if (p := directory / name).exists())
    if (root / 'runs').exists():
        targets.append(root / 'runs')
    markers = {'Silent Hill 3 Game.sh': '# SH3 project game menu;',
               'Silent Hill 3 Performance.sh': '# SH3 project performance menu;',
               'Silent Hill 3 Preflight.sh': '# SH3 project preflight launcher;',
               'Silent Hill 3 Runtime Diagnostics.sh': '# SH3 project runtime diagnostics menu;',
               'Silent Hill 3 Graphics Diagnostics.sh': '# SH3 project graphics diagnostics menu;'}
    for name, marker in markers.items():
        path = root.parent / name
        if path.exists():
            if not any(line.startswith(marker) for line in path.read_text().splitlines()[:3]):
                raise ValueError('foreign SH3 menu preserved: ' + name)
            targets.append(path)
    # Validate complete batch before any removal; never follow a selected symlink.
    for path in targets:
        if path.resolve(strict=True) != path:
            raise ValueError('cleanup target is a symlink: ' + str(path))
        if path.is_dir() and path != root / 'runs':
            raise ValueError('unexpected cleanup directory')
    inactive()
    removed = []
    for path in targets:
        relative = str(path.relative_to(root)) if path.is_relative_to(root) else '../' + path.name
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
        removed.append(relative)
    return {'status': 'cleaned', 'removed': removed, 'remaining': inspect(root)}


def stage_directory(root, run_id):
    if not re.fullmatch(r'\d{8}T\d{12}Z-[0-9a-f]{6}', run_id):
        raise ValueError('invalid install identity')
    path = root / ('.play-install-' + run_id)
    inactive()
    path.mkdir()
    return {'status': 'staged', 'path': str(path)}


def update_menu_metadata(root):
    gamelist = root.parent / 'gamelist.xml'
    if not gamelist.is_file():
        return
    privilege = [] if os.geteuid() == 0 else ['sudo', '-n']
    def systemctl(*args):
        return subprocess.run([*privilege, 'systemctl', *args], capture_output=True)
    active = systemctl('is-active', '--quiet', 'emulationstation.service').returncode == 0
    if active and systemctl('stop', 'emulationstation.service').returncode:
        raise ValueError('frontend stop failed before SH3 menu metadata update')
    try:
        # Frontend saves cached metadata on stop; read its final version now.
        tree = ET.parse(gamelist)
        document = tree.getroot()
        names = ['Silent Hill 3.sh', 'Silent Hill 3 Game.sh', 'Silent Hill 3 Performance.sh',
                 'Silent Hill 3 Preflight.sh', 'Silent Hill 3 Runtime Diagnostics.sh',
                 'Silent Hill 3 Graphics Diagnostics.sh']
        paths = {value for name in names for value in [name, './' + name, str(root.parent / name)]}
        for game in list(document.findall('game')):
            if game.findtext('path') in paths:
                document.remove(game)
        game = ET.SubElement(document, 'game')
        ET.SubElement(game, 'path').text = './Silent Hill 3.sh'
        ET.SubElement(game, 'name').text = 'Silent Hill 3'
        destination = gamelist.resolve(strict=True)
        temporary = destination.with_name(destination.name + '.sh3-new')
        tree.write(temporary, encoding='utf-8', xml_declaration=True)
        temporary.chmod(destination.stat().st_mode & 0o777)
        os.replace(temporary, destination)
    finally:
        if active and systemctl('start', 'emulationstation.service').returncode:
            raise ValueError('frontend restart failed after SH3 menu metadata update')


def install(root, stage):
    inactive()
    if (stage.name != 'payload' or stage.parent.parent != root or
            not re.fullmatch(r'\.play-install-\d{8}T\d{12}Z-[0-9a-f]{6}', stage.parent.name) or
            stage.resolve(strict=True) != stage):
        raise ValueError('install payload outside owned stage')
    manifest = json.loads((stage / 'manifest.json').read_text())
    required = {'ports/Silent Hill 3 Play.sh', 'ports/Silent Hill 3 Game.sh', 'ports/Silent Hill 3.sh',
                'ports/game-session.sh', 'ports/restore-frontend.sh', 'ports/performance-governors.py',
                'scripts/device/check-data.sh', 'scripts/required-data.txt', 'runtime/sh3',
                'runtime/build-inputs.json', 'data.sys', 'reviewed-helpers.sha256'}
    if set(manifest) != required:
        raise ValueError('unexpected install payload')
    for name, expected in manifest.items():
        path = stage / name
        if path.resolve(strict=True) != path or digest(path) != expected:
            raise ValueError('install checksum or path mismatch: ' + name)
    binary = (stage / 'runtime/sh3').read_bytes()[:20]
    if binary[:6] != b'\x7fELF\x02\x01' or int.from_bytes(binary[18:20], 'little') != 183:
        raise ValueError('runtime is not native AArch64')
    build = json.loads((stage / 'runtime/build-inputs.json').read_text())
    if hashlib.sha1((root / 'gamedata/sh3.exe').read_bytes()).hexdigest() != build['input_sha1']:
        raise ValueError('runtime owner input mismatch')
    helper_lines = (stage / 'reviewed-helpers.sha256').read_text().splitlines()
    if not helper_lines:
        raise ValueError('missing reviewed firmware helpers')
    for line in helper_lines:
        checksum, filename = line.split(maxsplit=1)
        path = Path(filename.lstrip(' *'))
        if ('PortMaster' not in path.parts or not path.is_absolute() or digest(path) != checksum):
            raise ValueError('firmware helpers differ from reviewed inventory')
    for name in ['runtime', 'preflight', 'state', 'state/savedata']:
        path = root / name
        if path.exists() and (path.resolve(strict=True) != path or not path.is_dir()):
            raise ValueError('install destination is not a real directory: ' + name)
    if not (root / 'preflight/.sh3-preflight-owned').is_file():
        raise ValueError('preflight ownership marker missing')
    menu = root.parent / 'Silent Hill 3.sh'
    if menu.exists() and (menu.is_symlink() or '# SH3 project play menu;' not in menu.read_text()):
        raise ValueError('foreign Silent Hill 3 menu preserved')
    for name in ['runtime/sh3', 'state/savedata/data.sys', 'state/savedata/disp.ini', 'state/sh3.ini']:
        if (root / name).is_symlink():
            raise ValueError('install target is a symlink: ' + name)
    # Build complete replacement before removing old SH3-only diagnostics/saves.
    next_preflight = stage / 'next-preflight'
    for name in required:
        if name.startswith(('ports/', 'scripts/')) and not name.endswith(' Play.sh'):
            target = next_preflight / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(stage / name, target)
            target.chmod(0o755 if target.suffix in ('.sh', '.py') else 0o644)
    (next_preflight / '.sh3-preflight-owned').touch()
    cleanup = clean(root)
    previous = stage / 'previous-preflight'
    os.replace(root / 'preflight', previous)
    try:
        os.replace(next_preflight, root / 'preflight')
    except OSError:
        os.replace(previous, root / 'preflight')
        raise
    binary_path = root / 'runtime/sh3'
    os.replace(stage / 'runtime/sh3', binary_path)
    binary_path.chmod(0o755)
    for name in ['artifacts.sha256', 'build-inputs.json', 'compiler.txt', 'elf.txt', 'libc.txt',
                 'packages.txt', 'python.txt', 'readelf.txt']:
        path = root / 'runtime' / name
        if path.is_file() or path.is_symlink():
            path.unlink()
    savedata = root / 'state/savedata'
    savedata.mkdir(parents=True, exist_ok=True)
    os.replace(stage / 'data.sys', savedata / 'data.sys')
    (savedata / 'disp.ini').write_text('format=D3DFMT_A8R8G8B8\ngamma_b=1\ngamma_g=1\n'
                                     'gamma_r=1\nlensflare_ztest=1\nmode=fullscreen\n'
                                     'resolution=320x240\nshadow=1\nsize=640x480\n')
    (root / 'state/sh3.ini').write_text('resolution=640x480\ncores=3\ntrace=0\nlog=0\n')
    os.replace(stage / 'ports/Silent Hill 3 Play.sh', menu)
    menu.chmod(0o755)
    update_menu_metadata(root)
    shutil.rmtree(stage.parent)
    return {'status': 'installed', 'runtime_sha256': digest(binary_path),
            'removed': cleanup['removed'], 'remaining': inspect(root)}


def guest_options(pid):
    """One external read of recognized owner image; no injected runtime sampling."""
    maps = Path('/proc') / str(pid) / 'maps'
    with (maps.parent / 'mem').open('rb', buffering=0) as memory:
        for line in maps.read_text().splitlines():
            extent, permissions, *_ = line.split()
            low, high = (int(v, 16) for v in extent.split('-'))
            if permissions[:3] != '---' or high - low < 0x40000000:
                continue
            base = high - 0x100000000
            if base < 0:
                continue
            try:
                memory.seek(base + 0x400000)
                if memory.read(2) != b'MZ':
                    continue
            except OSError:
                continue
            values = {}
            for name, va in [('blood', 0x70E66C8), ('noise', 0x70E66CC), ('display', 0x70E66B0),
                             ('internal_width', 0x72BFD0), ('internal_height', 0x72BFD4)]:
                memory.seek(base + va)
                value = int.from_bytes(memory.read(4), 'little')
                values[name] = value >> 24 if name in ('blood', 'noise', 'display') else value
            return values
    raise ValueError('recognized 4 GB owner arena unavailable')


def power_governors():
    paths = list(Path('/sys/devices/system/cpu/cpufreq').glob('policy*/scaling_governor'))
    paths += list(Path('/sys/class/devfreq').glob('*/governor'))
    return {str(p): p.read_text().strip() for p in paths}


def verify(root):
    menu = root.parent / 'Silent Hill 3.sh'
    if not menu.is_file() or '# SH3 project play menu;' not in menu.read_text():
        raise ValueError('play menu missing or not project-owned')
    inactive()
    privilege = [] if os.geteuid() == 0 else ['sudo', '-n']
    def systemctl(*arguments):
        return subprocess.run([*privilege, 'systemctl', *arguments], capture_output=True, text=True)
    if systemctl('is-active', '--quiet', 'emulationstation.service').returncode:
        raise ValueError('frontend must be active before play verification')
    before = power_governors()
    result = {'status': 'checking', 'power_before': before}
    try:
        launch = subprocess.run(['bash', str(menu)], capture_output=True, text=True, timeout=15)
        if launch.returncode:
            raise ValueError('play entry failed to start service')
        pid = None
        for _ in range(30):
            found = subprocess.run(['pgrep', '-x', 'sh3'], capture_output=True, text=True)
            if found.returncode == 0 and len(found.stdout.split()) == 1:
                pid = int(found.stdout.strip())
                break
            time.sleep(1)
        if pid is None:
            raise ValueError('native game did not start')
        time.sleep(20)
        proc = Path('/proc') / str(pid)
        environment = dict(v.split('=', 1) for v in proc.joinpath('environ').read_bytes().decode().split('\0') if '=' in v)
        result['play_environment'] = {k: v for k, v in environment.items() if k.startswith('SH3_')}
        expected = {'SH3_QUIET': '1', 'SH3_DIAGNOSTICS': '0', 'SH3_DIRECT_PLAY': '1',
                    'SH3_INTERNAL_RESOLUTION': '320x240', 'SH3_OUTPUT_RESOLUTION': '640x480',
                    'SH3_FPS_LIMIT': '30'}
        if any(environment.get(k) != v for k, v in expected.items()):
            raise ValueError('ordinary play environment differs from requested profile')
        forbidden = ['SH3_KEYS', 'SH3_QUIT_AFTER', 'SH3_MONITOR', 'SH3_PROFILE', 'SH3_GPU_PROFILE',
                     'SH3_STATS', 'SH3_INPUT_LOG', 'SH3_PEEK', 'SH3_SHOT', 'SH3_PRESENT_DUMP']
        if any(k in environment for k in forbidden):
            raise ValueError('diagnostic or scripted-play flag reached native game')
        result['options'] = guest_options(pid)
        if result['options'] != {'blood': 2, 'noise': 0, 'display': 0,
                                 'internal_width': 320, 'internal_height': 240}:
            raise ValueError('live native settings differ from requested player options')
        result['cwd'] = str(proc.joinpath('cwd').resolve())
        result['runtime_sha256'] = digest(proc / 'exe')
        result['loaded_graphics'] = [line for line in proc.joinpath('maps').read_text().splitlines()
                                     if any(name in line for name in ['libSDL2', 'libEGL', 'libGLES', 'libmali'])]
        result['power_game'] = power_governors()
        result['status'] = 'verified'
    finally:
        stopped = systemctl('stop', 'sh3-r36s-game.service')
        result['stop_status'] = stopped.returncode
        result['frontend_active'] = systemctl('is-active', '--quiet', 'emulationstation.service').returncode == 0
        result['power_after'] = power_governors()
        result['no_run_directory'] = not (root / 'runs').exists()
        result['no_game_logs'] = not any(root.glob('**/sh3*.log'))
        result['no_clock_journal'] = not (root / '.performance-policy-owner.json').exists()
        result['no_progress_slots'] = not any((root / 'state/savedata').glob('data.[0-9][0-9][0-9]'))
        print(json.dumps(result, indent=2), file=sys.stderr, flush=True)
    inactive()
    if (not result['frontend_active'] or result['power_after'] != before or
            not all(result[k] for k in ['no_run_directory', 'no_game_logs', 'no_clock_journal', 'no_progress_slots'])):
        raise ValueError('play cleanup or stock power restoration failed')
    return result


def main():
    root, action = Path(sys.argv[1]), sys.argv[2]
    if root.name != 'sh3' or root.resolve(strict=True) != root:
        raise ValueError('SH3 root must be a real, non-symlink directory')
    if action not in ('inspect', 'clean', 'stage', 'install', 'verify'):
        raise ValueError('unknown play maintenance action')
    if action == 'stage':
        result = stage_directory(root, sys.argv[3])
    elif action == 'install':
        result = install(root, Path(sys.argv[3]))
    elif action == 'verify':
        result = verify(root)
    else:
        result = clean(root) if action == 'clean' else inspect(root, len(sys.argv) > 3 and sys.argv[3] == '1')
    print(json.dumps(result, indent=2), flush=True)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({'status': 'refused', 'reason': str(error)}), file=sys.stderr)
        sys.exit(3)
