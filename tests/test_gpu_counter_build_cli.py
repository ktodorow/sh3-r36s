"""Counter research build uses confirmed host-build CLI; Docker is external."""
import json
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]


class GpuCounterBuildCliTests(unittest.TestCase):
    @unittest.skipUnless(os.environ.get("SH3_GPU_COUNTER_SOURCE"), "requires reviewed pinned clone and ARM64 Docker")
    def test_targeted_variant_preserves_official_probe_and_reports_real_missing_device(self):
        previous = {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in (REPO / ".port-cache/gpu-counter-builds").glob("*/artifacts/api-example")}
        game = REPO / "dist/runtime/sh3"
        previous_game = hashlib.sha256(game.read_bytes()).hexdigest() if game.is_file() else None
        result = subprocess.run(["python3", str(REPO / "scripts/host/build-gpu-counters.py"),
                                 "--source", os.environ["SH3_GPU_COUNTER_SOURCE"], "--variant", "targeted"],
                                cwd=REPO, capture_output=True, text=True, timeout=600)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        evidence = REPO / result.stdout.strip().split("Evidence: ")[-1]
        artifact = evidence / "artifacts/gpu-counter-targeted"
        header = artifact.read_bytes()[:64]
        self.assertEqual(header[:6], b"\x7fELF\x02\x01")
        self.assertEqual(int.from_bytes(header[18:20], "little"), 183)
        image = json.loads((evidence / "build-inputs.json").read_text())["image"]
        result = subprocess.run(["docker", "run", "--rm", "--platform", "linux/arm64", "--network", "none",
                                 "--mount", f"type=bind,src={artifact.parent},dst=/artifact,readonly",
                                 image, "/artifact/gpu-counter-targeted"],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 255, result.stdout + result.stderr)
        self.assertIn("GPU device 0 is missing", result.stderr)
        for path, digest in previous.items():
            self.assertEqual(hashlib.sha256(Path(path).read_bytes()).hexdigest(), digest)
        self.assertEqual(hashlib.sha256(game.read_bytes()).hexdigest() if game.is_file() else None, previous_game)

    @unittest.skipUnless(os.environ.get("SH3_GPU_COUNTER_SOURCE"), "requires reviewed pinned clone and ARM64 Docker")
    def test_reviewed_counter_example_builds_aarch64_without_replacing_game(self):
        game = REPO / "dist/runtime/sh3"
        previous_game = game.read_bytes() if game.is_file() else None
        result = subprocess.run(["python3", str(REPO / "scripts/host/build-gpu-counters.py"),
                                 "--source", os.environ["SH3_GPU_COUNTER_SOURCE"]], cwd=REPO,
                                capture_output=True, text=True, timeout=600)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        evidence = REPO / result.stdout.strip().split("Evidence: ")[-1]
        artifact = evidence / "artifacts/api-example"
        header = artifact.read_bytes()[:64]
        self.assertEqual(header[:6], b"\x7fELF\x02\x01", "counter probe must be ELF64 little endian")
        self.assertEqual(int.from_bytes(header[18:20], "little"), 183, "counter probe must be AArch64")
        self.assertEqual(game.read_bytes() if game.is_file() else None, previous_game)

    def test_unavailable_docker_keeps_failed_probe_identity_and_existing_artifacts(self):
        (REPO / ".port-cache").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="gpu-build-cli-", dir=REPO / ".port-cache") as temp:
            root = Path(temp)
            for name in ["scripts/host/build-gpu-counters.py", "scripts/host/r36s.py",
                         "scripts/build/Dockerfile", ".gitignore"]:
                source = REPO / name
                if source.exists():
                    dest = root / name
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(source, dest)
            final = root / "dist/runtime/sh3"
            final.parent.mkdir(parents=True)
            final.write_bytes(b"existing game artifact")
            commands = root / "bin"
            commands.mkdir()
            docker = commands / "docker"
            docker.write_text('#!/bin/sh\nprintf "Docker daemon unavailable\\n" >&2\nexit 42\n')
            docker.chmod(0o755)
            # Git is host tooling; reusable runtime container intentionally lacks it.
            git = commands / "git"
            git.write_text('#!/bin/sh\n[ "$1" = check-ignore ] && exit 0\nexit 99\n')
            git.chmod(0o755)
            env = {**os.environ, "PATH": f"{commands}:{os.environ['PATH']}",
                   "GIT_DIR": str(REPO / ".git"), "GIT_WORK_TREE": str(root),
                   "GIT_OPTIONAL_LOCKS": "0"}
            result = subprocess.run(["python3", str(root / "scripts/host/build-gpu-counters.py"),
                                     "--source", str(root / "tmpRepo/upstream")],
                                    cwd=root, env=env, capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 42, result.stderr)
            runs = list((root / ".port-cache/gpu-counter-builds").iterdir())
            self.assertEqual(len(runs), 1)
            run = runs[0]
            self.assertEqual((run / "exit-status.txt").read_text().strip(), "42")
            identity = json.loads((run / "build-inputs.json").read_text())
            self.assertEqual(identity["source_commit"], "847a04a1597d132a3746e9c6374d3977cea89a6d")
            self.assertEqual(identity["platform"], "linux/arm64")
            self.assertIn("Docker daemon unavailable", (run / "image.stderr.txt").read_text())
            self.assertEqual(final.read_bytes(), b"existing game artifact")


if __name__ == "__main__":
    unittest.main()
