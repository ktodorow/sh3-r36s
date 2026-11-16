# Developer guide

`dev` contains native Linux ARM64 source, required generator dependencies,
build/package scripts and player runtime helpers. `research` preserves specs,
reports, tests, experiments and device orchestration. Build and release from
`dev`; use `research` when working on profiling or device acceptance.

## Prerequisites and private inputs

Install Git, Python 3.10+ and Docker with Linux ARM64 support (native ARM64 or
Docker Desktop emulation). All C compilation runs inside Docker. No console
SDK/toolchain is needed.

```sh
git clone --branch dev https://github.com/ktodorow/sh3-r36s.git
cd sh3-r36s
cp .env.example .env
```

Set `SH3_GAME_DIR='/absolute/path/to/your/PC installation'` in ignored `.env`.
The folder must contain `sh3.exe` and complete `data/`. Do not commit game files,
recompiled generated C, `.env`, build outputs, caches or device dumps.

Supported input executables are 3,338,240 bytes:

| Profile | SHA-1 |
| --- | --- |
| Original-CD input used for public R36S build | `d851669ef609b3164e3581aa8dcfbfaec866cb79` |
| Original upstream input | `aa2aca6dba19bf510c9c2e92eefdc15e98266581` |

Generated code and binary must match selected input. Neither arbitrary patched
executables nor mixing generated output between profiles is supported.

## Build with Docker

Recommended build command:

```sh
python3 scripts/host/build.py --release
```

This reuses a compatible image or builds it automatically, then invokes
`docker run --rm --platform linux/arm64` with a read-only source snapshot and
read-only selected executable. Only generated-code, build and artifact folders
are writable. It does not connect to a device. Build runs from repository root.

To prepare the exact reusable Docker environment explicitly:

```sh
docker build --platform linux/arm64 \
  -t sh3-r36s-build:e6a3402e8f1b23bd \
  -f scripts/build/Dockerfile scripts/build
python3 scripts/host/build.py --release
```

Image tag is first 16 hex digits of Dockerfile SHA-256; wrapper recalculates it
if recipe changes. Base is pinned Debian bookworm (glibc 2.36), older than tested
R36S glibc 2.41. Compiler uses Cortex-A35, `-fwrapv` and
`-fno-strict-aliasing`; O2 is default. `--optimization O3` and `--lto` are
comparison options, not the published play profile. `SH3_BUILD_JOBS` controls
parallel compiler jobs (default 2).

Pipeline validates input/data, patches an ignored working copy, translates x86
to C using vendored xboxrecomp, and compiles native AArch64 runtime with SDL2.
Desktop GL comparison backend remains alongside handheld GLES backend. Original
executable is preserved. `--release` disables embedding private game-derived
shader/geometry diagnostic samples; keep it for anything distributed publicly.
A build without this flag is for private research only.

Outputs:

- `dist/runtime/sh3`: stripped native executable; `sh3.debug` remains local.
- `dist/release/sh3-r36s-30fps.zip` and `SHA256SUMS`: installable player package.
- `.port-cache/builds/<UTC-id>/`: input/source hashes, compiler/package versions,
  logs and artifact evidence. Keep local; inspect before sharing.

ZIP includes single **Silent Hill 3** frontend launcher, native binary,
profile marker, required lifecycle/control/data-check helpers and player docs.
It excludes original game files, saved progress, private diagnostic samples,
shader caches, debug symbols, reports, credentials and device deployment tools.
The launcher reads firmware PortMaster helpers and keeps player state in
`sh3/state/`. See [installation guide](README.md#install-and-run).

## Source map

| Path | Purpose |
| --- | --- |
| `src/game/` | Manual game replacements and timing/controller defaults |
| `src/runtime/`, `src/win32/` | Guest memory, threads and Windows API compatibility |
| `src/d3d8/` | D3D8 translation, GLES/desktop GL, shaders and presentation |
| `tools/regen.sh`, `tools/*.py` | Input patching and static recompilation |
| `third_party/xboxrecomp/` | Vendored generator dependency and licenses |
| `ports/` | Player launcher and required on-device lifecycle helpers |
| `scripts/build/` | Docker recipe, native build and read-only data validation |
| `scripts/host/build.py`, `scripts/host/clean-build.py` | Local build/package and scoped cleanup |

Generated `src/recomp/gen/` is ignored. Names such as XBE/Xbox in generator are
intermediate-format machinery required to translate the PC executable.

## Verification and cleanup

Research branch retains launcher/build regression tests and their documented
boundaries. Run host fixtures there with `python3 -m unittest discover -s tests`.
Compile executable tests only in same Linux ARM64 Docker environment. Desktop or
fixture passes do not establish R36S compatibility; new binaries still need
actual device launch, graphics, controls, save and frontend-recovery checks.
Current release is preview: complete campaign and original FMVs remain open.

```sh
python3 scripts/host/clean-build.py
# Optional: also remove unused resources owned by this project.
python3 scripts/host/clean-build.py --docker
```

Cleanup preserves source, final `dist` artifacts and evidence. Do not use global
Docker prune or delete player data as a build fix.
