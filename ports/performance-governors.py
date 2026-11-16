#!/usr/bin/env python3
"""Opt-in, owned governor-only diagnostic; never changes limits or permissions."""
import fcntl
import json
import os
from pathlib import Path
import re
import sys


def write_json(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def write_report(path, value):
    if os.environ.get('SH3_DIAGNOSTICS') != '0':
        write_json(path, value)


def restore(port, run, journal):
    report = port / 'runs' / (run + '-service') / 'power-restore.json'
    if not journal.exists():
        return 0
    state = json.loads(journal.read_text())
    if state['run'] != run or state['boot'] != Path('/proc/sys/kernel/random/boot_id').read_text().strip():
        write_report(report, {'status': 'ownership-conflict'})
        return 3
    errors = []
    for entry in reversed(state['changed']):
        governor = Path(entry['governor'])
        try:
            if any(Path(path).read_text().strip() != value for path, value in entry['limits'].items()):
                raise ValueError('frequency limits changed externally')
            current = governor.read_text().strip()
            if current not in ('performance', entry['original']):
                raise ValueError('governor changed externally: ' + current)
            if current != entry['original']:
                governor.write_text(entry['original'] + '\n')
            if governor.read_text().strip() != entry['original']:
                raise ValueError('restoration readback mismatch')
        except (OSError, ValueError) as error:
            errors.append({'path': str(governor), 'error': str(error)})
    write_report(report, {'status': 'conflict' if errors else 'restored', 'errors': errors,
                        'policies': state['changed']})
    if not errors:
        journal.unlink()
    return 3 if errors else 0


def begin(port, run, domains, sysfs, journal):
    if journal.exists():
        raise ValueError('another governor diagnostic owns pending recovery')
    selected = domains.split(',')
    if not selected or len(set(selected)) != len(selected) or not set(selected) <= {'cpu', 'gpu', 'dmc'}:
        raise ValueError('invalid diagnostic governor domains')
    entries = []
    for domain in selected:
        if domain == 'cpu':
            directories = sorted((sysfs / 'devices/system/cpu/cpufreq').glob('policy*'))
            prefix, ceiling = 'scaling_', 1512000
        else:
            directories = [p for p in (sysfs / 'class/devfreq').glob('*')
                           if ('gpu' in p.name if domain == 'gpu' else p.name == 'dmc')]
            prefix, ceiling = '', 520000000 if domain == 'gpu' else 786000000
        if not directories:
            raise ValueError('missing advertised domain: ' + domain)
        for directory in directories:
            directory = directory.resolve()
            governor = directory / (prefix + 'governor')
            available = (directory / (prefix + 'available_governors')).read_text().split()
            original = governor.read_text().strip()
            if 'performance' not in available or original not in available:
                raise ValueError('unsupported governor: ' + str(directory))
            limits = {str(directory / (prefix + name)): (directory / (prefix + name)).read_text().strip()
                      for name in ('min_freq', 'max_freq')}
            frequencies = [int(v) for v in (directory / (prefix + 'available_frequencies')).read_text().split()]
            minimum, maximum = (int(v) for v in limits.values())
            if not frequencies or not 0 < minimum <= maximum <= max(frequencies) <= ceiling:
                raise ValueError('unverified frequency limits: ' + str(directory))
            if domain == 'cpu' and int((directory / 'cpuinfo_max_freq').read_text()) > ceiling:
                raise ValueError('unverified CPU hardware maximum')
            entries.append({'domain': domain, 'governor': str(governor), 'original': original,
                            'limits': limits, 'available_frequencies': frequencies})
    state = {'run': run, 'boot': Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
             'changed': []}
    # Validate all domains first, journal before each possible write for crash recovery.
    write_json(journal, state)
    try:
        for entry in entries:
            if any(Path(path).read_text().strip() != value for path, value in entry['limits'].items()):
                raise ValueError('frequency limits changed before apply')
            governor = Path(entry['governor'])
            if governor.read_text().strip() != entry['original']:
                raise ValueError('governor changed before apply')
            state['changed'].append(entry)
            write_json(journal, state)
            governor.write_text('performance\n')
            if governor.read_text().strip() != 'performance':
                raise ValueError('performance governor readback mismatch')
        write_report(port / 'runs' / (run + '-service') / 'power-applied.json', state)
    except (OSError, ValueError):
        restore(port, run, journal)
        raise


def main():
    action, root, run, *options = sys.argv[1:]
    if action not in ('begin', 'end') or not re.fullmatch(r'[A-Za-z0-9_-]+', run):
        return 3
    port = Path(root)
    with (port / '.performance-policy.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        journal = port / '.performance-policy-owner.json'
        try:
            if action == 'end':
                return restore(port, run, journal)
            begin(port, run, options[0], Path(options[1]), journal)
            return 0
        except (OSError, ValueError, KeyError) as error:
            write_report(port / 'runs' / (run + '-service') / 'power-error.json', {'error': str(error)})
            print('Governor diagnostic failed: ' + str(error), file=sys.stderr)
            return 3


if __name__ == '__main__':
    sys.exit(main())
