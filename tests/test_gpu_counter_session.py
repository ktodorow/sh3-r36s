"""Timed optional diagnostic boundary; external payload fixtures never prove GPU access."""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts/device/gpu-counter-session.py"


class GpuCounterSessionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="gpu-counter-session-")
        self.addCleanup(self.temp.cleanup)
        self.run = Path(self.temp.name)
        self.helper = self.run / "payload/scripts/device/gpu-counter-probe.sh"
        self.helper.parent.mkdir(parents=True)

    def test_explicit_payload_directory_runs_without_links_or_copies_and_records_identity(self):
        self.helper.write_text("#!/bin/sh\nmkdir -p \"$1/gpu-counter\"\n"
                               "printf '%s\\n' \"$2\" > \"$1/payload-directory.txt\"\n"
                               "printf '{\"usable_samples\":false,\"native_exit_status\":255}\\n' "
                               "> \"$1/gpu-counter/capability.json\"\nexit 255\n")
        binary = self.run / "payload/gpu-counter/api-example"
        binary.parent.mkdir()
        binary.write_bytes(b"reviewed external reader fixture\n")
        digest = hashlib.sha256(binary.read_bytes()).hexdigest()
        source = self.run / "source payload"
        (self.run / "payload").rename(source)
        before = {str(path.relative_to(source)): path.read_bytes()
                  for path in source.rglob("*") if path.is_file()}
        result = subprocess.run([sys.executable, str(SCRIPT), "--payload", str(source),
                                 str(self.run), "0", ".02"],
                                capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        output = self.run / "gpu-counter-active"
        summary = json.loads((output / "session.json").read_text())
        self.assertEqual(summary["payload"], {"directory": str(source), "binary_sha256": digest})
        self.assertEqual(len(summary["samples"]), 2)
        for index in (1, 2):
            child = output / f"sample-{index:03d}"
            self.assertEqual((child / "payload-directory.txt").read_text().strip(), str(source))
            self.assertFalse((child / "payload").exists())
            self.assertEqual(summary["samples"][index - 1]["helper_exit_status"], 255)
        self.assertFalse(any(path.is_symlink() for path in output.rglob("*")))
        self.assertFalse(any(path.name == "api-example" for path in output.rglob("*")))
        self.assertEqual({str(path.relative_to(source)): path.read_bytes()
                          for path in source.rglob("*") if path.is_file()}, before)

    def test_three_absolute_offsets_retain_boundary_clocks_frequencies_and_native_results(self):
        self.helper.write_text("#!/bin/sh\nmkdir -p \"$1/gpu-counter\"\n"
                               "printf '255\\n' > \"$1/gpu-counter/exit-status.txt\"\n"
                               "printf '{\"usable_samples\":false,\"native_exit_status\":255}\\n' "
                               "> \"$1/gpu-counter/capability.json\"\nexit 255\n")
        result = subprocess.run([sys.executable, str(SCRIPT), str(self.run), "0", ".05", ".1"],
                                capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        summary = json.loads((self.run / "gpu-counter-active/session.json").read_text())
        self.assertEqual(summary["status"], "finished")
        self.assertEqual(summary["payload"]["directory"], str(self.run / "payload"))
        self.assertEqual(len(summary["samples"]), 3)
        for index, sample in enumerate(summary["samples"], 1):
            self.assertEqual(sample["helper_exit_status"], 255)
            self.assertIs(sample["capability"]["usable_samples"], False)
            self.assertGreaterEqual(sample["start"]["monotonic_ns"], summary["anchor"]["monotonic_ns"])
            self.assertGreaterEqual(sample["end"]["monotonic_ns"], sample["start"]["monotonic_ns"])
            for boundary in (sample["start"], sample["end"]):
                self.assertTrue(boundary["utc"].endswith("+00:00"))
                self.assertEqual(set(boundary["frequencies"]), {"cpu", "gpu", "dmc"})
            child = self.run / f"gpu-counter-active/sample-{index:03d}"
            self.assertFalse((child / "payload").exists())
            self.assertTrue((child / "gpu-counter/capability.json").is_file())
        self.assertFalse(any(path.is_symlink() for path in (self.run / "gpu-counter-active").rglob("*")))

    def test_parent_termination_stops_helper_and_timeout_native_process_group(self):
        self.helper.write_text("#!/bin/sh\nprintf '%s\\n' $$ > \"$1/helper.pid\"\n"
                               "timeout --kill-after=1s 30s sh -c '"
                               "echo $$ > \"$1/native.pid\"; sleep 30; echo unexpected' sh \"$1\"\n")
        wrapper = subprocess.Popen([sys.executable, str(SCRIPT), str(self.run), "0"],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        child = self.run / "gpu-counter-active/sample-001"
        pids = []
        try:
            deadline = time.monotonic() + 3
            while not (child / "native.pid").is_file() and time.monotonic() < deadline:
                time.sleep(.02)
            self.assertTrue((child / "native.pid").is_file(), "fixture did not start native process")
            pids = [int((child / name).read_text()) for name in ("helper.pid", "native.pid")]
            wrapper.terminate()
            stdout, stderr = wrapper.communicate(timeout=4)
            self.assertEqual(wrapper.returncode, 143, stdout + stderr)
            for pid in pids:
                status = Path(f"/proc/{pid}/stat")
                alive = status.exists() and status.read_text().rsplit(")", 1)[1].split()[0] != "Z"
                self.assertFalse(alive, f"sampler process {pid} survived parent termination")
            summary = json.loads((self.run / "gpu-counter-active/session.json").read_text())
            self.assertEqual(summary["status"], "terminated")
        finally:
            if wrapper.poll() is None:
                wrapper.kill()
                wrapper.communicate(timeout=2)
            for pid in pids:
                try:
                    os.killpg(os.getpgid(pid), signal.SIGKILL)
                except ProcessLookupError:
                    pass

    def test_invalid_offsets_never_start_probe(self):
        marker = self.run / "executed"
        self.helper.write_text("#!/bin/sh\ntouch '" + str(marker) + "'\n")
        for offsets in (("0", ".01", ".02", ".03"), ("-1",), ("181",), ("nan",)):
            with self.subTest(offsets=offsets):
                result = subprocess.run([sys.executable, str(SCRIPT), str(self.run), *offsets],
                                        capture_output=True, text=True, timeout=3)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertFalse(marker.exists(), "invalid schedule must not execute payload")
                self.assertFalse((self.run / "gpu-counter-active").exists())

    def test_parent_termination_before_first_offset_starts_no_sampler(self):
        self.helper.write_text("#!/bin/sh\nexit 99\n")
        wrapper = subprocess.Popen([sys.executable, str(SCRIPT), str(self.run)],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            summary_path = self.run / "gpu-counter-active/session.json"
            deadline = time.monotonic() + 3
            while not summary_path.is_file() and time.monotonic() < deadline:
                time.sleep(.02)
            self.assertTrue(summary_path.is_file())
            wrapper.terminate()
            stdout, stderr = wrapper.communicate(timeout=2)
            self.assertEqual(wrapper.returncode, 143, stdout + stderr)
            summary = json.loads(summary_path.read_text())
            self.assertEqual(summary["status"], "terminated")
            self.assertEqual(summary["samples"], [])
        finally:
            if wrapper.poll() is None:
                wrapper.kill()
                wrapper.communicate(timeout=2)


if __name__ == "__main__":
    unittest.main()
