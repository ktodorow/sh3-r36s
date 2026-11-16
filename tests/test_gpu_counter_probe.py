"""Saved diagnostic RUN_DIR boundary; payload fixtures do not prove Mali access."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]


class GpuCounterProbeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="gpu-counter-probe-")
        self.addCleanup(self.temp.cleanup)
        self.run = Path(self.temp.name)
        self.payload = self.run / "payload/gpu-counter"
        self.payload.mkdir(parents=True)

    def payload_script(self, text):
        binary = self.payload / "api-example"
        binary.write_text("#!/bin/sh\n" + text)
        binary.chmod(0o755)
        digest = hashlib.sha256(binary.read_bytes()).hexdigest()
        (self.payload / "SHA256SUMS").write_text(digest + "  api-example\n")

    def probe(self):
        return subprocess.run(["bash", str(REPO / "scripts/device/gpu-counter-probe.sh"),
                               str(self.run)], capture_output=True, text=True, timeout=20)

    def test_native_failure_preserves_error_exit_and_inventory_without_capability_pass(self):
        self.payload_script("printf 'Mali GPU device 0 is missing\\n'\n"
                            "printf 'native startup failure\\n' >&2\nexit 255\n")
        result = self.probe()
        self.assertEqual(result.returncode, 255, result.stdout + result.stderr)
        output = self.run / "gpu-counter"
        self.assertEqual((output / "exit-status.txt").read_text().strip(), "255")
        self.assertEqual((output / "stdout.txt").read_text(), "Mali GPU device 0 is missing\n")
        self.assertEqual((output / "stderr.txt").read_text(), "native startup failure\n")
        self.assertIn("/dev/mali0", (output / "inventory.txt").read_text())
        summary = json.loads((output / "capability.json").read_text())
        self.assertIs(summary["usable_samples"], False)
        self.assertEqual(summary["native_exit_status"], 255)

    def test_explicit_payload_directory_runs_without_run_payload_link_or_copy(self):
        self.payload_script("printf 'external payload reached\\n'\nexit 255\n")
        original = (self.payload / "api-example").read_bytes()
        source = self.run / "source payload"
        (self.run / "payload").rename(source)
        result = subprocess.run(["bash", str(REPO / "scripts/device/gpu-counter-probe.sh"),
                                 str(self.run), str(source)],
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 255, result.stdout + result.stderr)
        self.assertEqual((self.run / "gpu-counter/stdout.txt").read_text(), "external payload reached\n")
        self.assertFalse((self.run / "payload").exists())
        self.assertFalse(any(path.is_symlink() for path in self.run.rglob("*")))
        self.assertEqual((source / "gpu-counter/api-example").read_bytes(), original)

    def test_ten_complete_native_samples_and_available_counters_establish_capability(self):
        native = (" GPU Device 0:\n    Product Family:  Bifrost\n"
                  "    Number of Cores: 2\n    Bus Width:       128\n"
                  " GPU 0 Supported counters:\n----------------\n"
                  "    GPU active cycles\n    Fragment active cycles\n"
                  "    External bus read bytes\n Sample Capture:\n----------------\n")
        native += ("GPU Active cycles [12000] ; Fragment Active Cycles [9000] ; "
                   "Geometry Sample Cull Rate [nan]\n") * 10
        self.payload_script("cat <<'DATA'\n" + native + "DATA\n")
        result = self.probe()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        output = self.run / "gpu-counter"
        self.assertEqual((output / "stdout.txt").read_text(), native)
        summary = json.loads((output / "capability.json").read_text())
        self.assertIs(summary["usable_samples"], True)
        self.assertEqual(summary["complete_samples"], 10)
        self.assertEqual(summary["product_family"], "Bifrost")
        self.assertEqual(summary["shader_cores"], 2)
        self.assertEqual(summary["bus_width"], 128)
        self.assertEqual(summary["supported_counters"],
                         ["GPU active cycles", "Fragment active cycles", "External bus read bytes"])

    def test_wrong_payload_hash_never_executes_native_probe(self):
        marker = self.run / "executed"
        self.payload_script("touch '" + str(marker) + "'\n")
        (self.payload / "SHA256SUMS").write_text("0" * 64 + "  api-example\n")
        result = self.probe()
        self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
        self.assertFalse(marker.exists(), "mismatched payload must not run")
        output = self.run / "gpu-counter"
        summary = json.loads((output / "capability.json").read_text())
        self.assertIs(summary["payload_verified"], False)
        self.assertIsNone(summary["native_exit_status"])
        self.assertIs(summary["usable_samples"], False)
        self.assertIn("FAILED", (output / "verification.stdout.txt").read_text())

    def test_zero_exit_with_nine_complete_samples_does_not_pass(self):
        native = (" Product Family: Bifrost\n Number of Cores: 2\n Bus Width: 128\n"
                  " GPU 0 Supported counters:\n    GPU active cycles\n Sample Capture:\n")
        native += ("GPU Active cycles [0] ; Fragment Active Cycles [0] ; "
                   "Geometry Sample Cull Rate [nan]\n") * 9
        native += "GPU Active cycles [0] ; invalid counter reading\n"
        self.payload_script("cat <<'DATA'\n" + native + "DATA\n")
        result = self.probe()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        summary = json.loads((self.run / "gpu-counter/capability.json").read_text())
        self.assertIs(summary["usable_samples"], False)
        self.assertEqual(summary["complete_samples"], 9)
        self.assertEqual(summary["classification"], "incomplete-samples")

    def test_hung_native_probe_stops_and_retains_timeout_status(self):
        self.payload_script("printf 'started\\n'\nsleep 30\n")
        result = self.probe()
        self.assertEqual(result.returncode, 124, result.stdout + result.stderr)
        output = self.run / "gpu-counter"
        self.assertEqual((output / "stdout.txt").read_text(), "started\n")
        self.assertEqual((output / "exit-status.txt").read_text().strip(), "124")
        summary = json.loads((output / "capability.json").read_text())
        self.assertEqual(summary["native_exit_status"], 124)
        self.assertIs(summary["usable_samples"], False)


if __name__ == "__main__":
    unittest.main()
