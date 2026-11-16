#!/usr/bin/env python3
"""Remove only an explicit, already retained batch of unused native payload copies."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys


def inactive():
    result = subprocess.run(['pgrep', '-x', 'sh3'], capture_output=True)
    if result.returncode != 1:
        raise ValueError('runtime active or process check unavailable')


def identity(path):
    value = path.lstat()
    return value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns


def main():
    root = Path(sys.argv[1])
    entries = json.loads(sys.argv[2])
    if root.resolve(strict=True) != root or not 0 < len(entries) <= 64:
        raise ValueError('invalid payload root or batch')
    inactive()
    checked = []
    seen = set()
    for entry in entries:
        relative = PurePosixPath(entry['path'])
        if not re.fullmatch(r'runs/\d{8}T\d{12}Z-[0-9a-f]{6}/payload/runtime/sh3', str(relative)):
            raise ValueError('foreign payload path')
        path = root / relative
        if path in seen or path.resolve(strict=True) != path:
            raise ValueError('duplicate or symlink payload')
        seen.add(path)
        value = path.lstat()
        if not stat.S_ISREG(value.st_mode) or value.st_nlink != 1:
            raise ValueError('payload is not one regular file')
        before = identity(path)
        with path.open('rb') as source:
            checksum = hashlib.sha256()
            for chunk in iter(lambda: source.read(1024 * 1024), b''):
                checksum.update(chunk)
            digest = checksum.hexdigest()
        if digest != entry['sha256'] or identity(path) != before:
            raise ValueError('payload hash or identity changed')
        checked.append((path, before, digest))
    inactive()
    for path, before, digest in checked:
        if path.resolve(strict=True) != path or identity(path) != before:
            raise ValueError('payload changed before batch removal')
    print(json.dumps({'status': 'validated', 'files': [
        {'path': str(path), 'sha256': digest, 'bytes': before[2]}
        for path, before, digest in checked]}), flush=True)
    for path, before, digest in checked:
        path.unlink()
        print(json.dumps({'status': 'removed', 'path': str(path),
                          'sha256': digest, 'bytes': before[2]}), flush=True)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({'status': 'refused', 'reason': str(error)}), file=sys.stderr)
        sys.exit(3)
