"""Saved run snapshot; binary identity stays in metadata, links are not followed."""
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]


class EvidenceArchiveTests(unittest.TestCase):
    def test_snapshot_keeps_results_and_symlink_metadata_without_duplicate_native_binary(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run = root / 'run'
            binary = run / 'payload/runtime/sh3'
            binary.parent.mkdir(parents=True)
            binary.write_bytes(b'redundant retained native package')
            (run / 'runtime.sha256').write_text('verified native identity\n')
            (run / 'firmware-libraries-after.txt').write_text('firmware: OK\n')
            (run / 'counter').mkdir()
            (run / 'counter/payload').symlink_to(run / 'payload', target_is_directory=True)
            before = {p: p.read_bytes() for p in run.rglob('*') if p.is_file()}
            result = subprocess.run(['bash', str(REPO / 'scripts/device/archive-evidence.sh'), str(run)],
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            with tarfile.open(str(run) + '.evidence.tar.gz') as archive:
                members = {str(Path(m.name)): m for m in archive.getmembers()}
                self.assertNotIn('payload/runtime/sh3', members)
                self.assertTrue(members['counter/payload'].issym())
                self.assertEqual(archive.extractfile(members['runtime.sha256']).read(), b'verified native identity\n')
                self.assertEqual(archive.extractfile(members['firmware-libraries-after.txt']).read(), b'firmware: OK\n')
            self.assertEqual({p: p.read_bytes() for p in before}, before)
