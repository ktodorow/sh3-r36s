# Silent Hill 3 — R36S port

Native port of the PC version of **Silent Hill 3** for R36S, maintained by [ktodorow](https://github.com/ktodorow).

> **No game files are included. You need your own copy of the PC game;** add your `sh3.exe` and complete `data/` folder after installing the port.
>
> **Unofficial fan project.** I am not employed by or connected in any way to Konami.

## Current release and features

Download [R36S 30 FPS preview](https://github.com/ktodorow/sh3-r36s/releases/tag/v0.1.0-r36s-30fps): **`sh3-r36s-30fps.zip`**.

- **30 FPS cap**, **320×240 internal → 640×480 output**, 4:3.
- Direct launch, R36S controls and button remapping.
- Persistent saves/settings and shader caches in `sh3/state/`; diagnostics off by default.

**Preview limits:** original FMVs are skipped; stutters and frame drops can occur. Full campaign testing remains in progress.

## Install and run

Requires a **full [PortMaster](https://portmaster.games/installation.html) installation**.

1. Extract `sh3-r36s-30fps.zip` into **`/roms2/ports/`**, placing `Silent Hill 3.sh` and `sh3/` directly there.
2. Copy your PC `sh3.exe` and complete `data/` folder into **`/roms2/ports/sh3/gamedata/`**.
3. Refresh the game list and launch **Ports → Silent Hill 3**.

Transfer through the SD card or an FTP server. For FTP setup, see the [R36S Handheld Wiki](https://handhelds.wiki/R36S_Handheld_Wiki).

Keep `sh3/gamedata/` and `sh3/state/` when updating. Exit with **Select+Start** before powering off.

## Controls

Physical R36S labels: A right, B below, X above, Y left.

| R36S control | Action |
| --- | --- |
| A | Action / confirm; attack while holding R2 |
| B | Flashlight / cancel |
| X | Dash |
| Y | Map |
| L1 / R1 | Strafe left / right |
| L2 | Search view |
| R2 | Ready weapon |
| Start | Inventory |
| Select | Pause / skip where supported |
| Select + Start | Exit game and return to frontend |
| Left stick / d-pad | Move / navigate menus |
| Right stick | Camera |
| L3 / R3 | Supplies / zoom |

Remap in **Options → Button Config**.

## Development and branches

Build your own port using your own supported PC `sh3.exe`: [Docker build guide](https://github.com/ktodorow/sh3-r36s/blob/dev/DEVELOPING.md).

This release was built from `sh3.exe` SHA-1 **`d851669ef609b3164e3581aa8dcfbfaec866cb79`**; this identifies the executable I used.

- **[dev](https://github.com/ktodorow/sh3-r36s/tree/dev):** build and runtime files.
- **[research](https://github.com/ktodorow/sh3-r36s/tree/research):** reports, research, tests and device tools.

## Credits

Thanks to **[cutarev](https://github.com/cutarev/sh3-nx)** for the original port, recompiler, runtime and renderer foundations.

Shout-out to **[PortMaster](https://portmaster.games/)**!

See [CREDITS.md](CREDITS.md) for code attribution and license notices.
