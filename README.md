# Silent Hill 3 — R36S port

Native Linux ARM64 port of the PC version of **Silent Hill 3** for R36S, maintained by [ktodorow](https://github.com/ktodorow). Built on [cutarev’s sh3-nx](https://github.com/cutarev/sh3-nx) and its recompiler, runtime and renderer foundations. Huge thanks to cutarev for making this project possible.

> **No game files are included. You need your own copy of the PC game;** copy its supported `sh3.exe` and complete `data/` folder into `sh3/gamedata/` after installing the release ZIP.
>
> **Unofficial fan project.** I am not affiliated with, employed by, endorsed by, or otherwise involved with Konami. Silent Hill 3 and its trademarks belong to their respective owners.

## Current release and features

Download [R36S 30 FPS release](https://github.com/ktodorow/sh3-r36/releases/latest). Use the **`sh3-r36s-30fps.zip`** asset, not GitHub’s automatic source-code ZIP.

- **30 FPS locked profile:** gameplay capped at 30 FPS, **320×240 internal rendering scaled to 640×480 output**, with original 4:3 presentation. A cap is not a guarantee: demanding scenes, loading and first shader compilation can still cause drops. The 640×480 internal comparison mode remains in source; it is not the release profile.
- **Native execution:** PC x86 code translated ahead of time to C and compiled for Linux AArch64. SDL2 handles input/audio; Direct3D 8 is translated to hardware OpenGL ES. No emulator or Wine required.
- **Direct launch:** select **Silent Hill 3** in Ports to enter the game, without the port’s extra splash/options menu.
- **R36S controls:** both sticks, digital triggers, button remapping, and Select+Start exit to frontend.
- **Persistent saves/settings and shader caches:** stored under `sh3/state/`. Fresh installs include no progress saves or prebuilt shader caches.
- **Quiet play:** diagnostic recording, frame capture and profiling off by default. Stock CPU/GPU/memory performance governors selected during play; previous policies restored on exit. Frequency limits are not raised.

This is a **preview**, not a completed campaign certification. Original prerecorded FMVs are currently skipped; real-time cutscenes use the game renderer. First visits may stutter while shaders compile. Campaign-wide progression, sustained performance and all audio cases remain under development. The inherited Office Building bathroom black-screen issue may require pressing a button to continue.

## Requirements

- R36S with **64-bit dArkOS**, working PortMaster installation, firmware SDL2 and Mali GLES drivers, Python 3, systemd and passwordless `sudo` for the normal frontend user. This launcher was developed on dArkOS with kernel 4.4.189 and glibc 2.41. Other firmware and R36S clones have not been verified.
- Approximately 5 GB for your installed PC game data, plus space for port, saves and caches.
- Release executable profile: `sh3.exe`, **3,338,240 bytes**, SHA-1 **`d851669ef609b3164e3581aa8dcfbfaec866cb79`** (original-CD input used for this R36S build). A different executable must not be renamed or patched to bypass validation. Developers can build from either recognized input profile; see [developer guide](DEVELOPING.md).

Install/update [PortMaster](https://portmaster.games/installation.html) first. This ZIP uses PortMaster’s installed control/firmware helpers; it does not bundle PortMaster or claim an official catalogue submission.

## Install and run

Both transfer methods produce this layout in your device’s Ports folder. On the tested two-card setup that folder is **`/roms2/ports/`**. On a single-card setup it may be `/roms/ports/`; use the folder your frontend actually scans.

```text
ports/
├── Silent Hill 3.sh              # launcher from release ZIP
└── sh3/
    ├── runtime/sh3               # native executable from release ZIP
    ├── preflight/                # required launcher helpers from release ZIP
    ├── gamedata/
    │   ├── sh3.exe               # supply from your PC installation
    │   └── data/                 # supply complete folder, including movies/sound
    └── state/                   # created on first run; saves/settings/caches
```

### SD-card transfer

1. Shut down the R36S and insert its games SD card into your computer. Open the `ports` folder on the games partition (often named EASYROMS).
2. Extract `sh3-r36s-30fps.zip` **inside `ports`**. Place `Silent Hill 3.sh` and `sh3/` directly there, without an extra ZIP-name folder.
3. From your installed PC game, copy `sh3.exe` and the **entire `data` folder** into `ports/sh3/gamedata/`. Keep lowercase filenames and folder structure. Do not create `gamedata/data/data/` or copy your whole installation one level too deep.
4. Safely eject the card, return it to the R36S, and boot. Refresh the frontend’s game list if needed, then open **Ports → Silent Hill 3**.

### FTP / SFTP transfer

1. Connect the R36S and computer to the same network. Enable the firmware’s remote/file-transfer service and find the device IP in its network settings.
2. In FileZilla, WinSCP or another file-transfer client, connect using **your device’s configured credentials**. Prefer **SFTP, port 22**, when SSH is enabled. Choose FTP only if your firmware has an FTP server enabled, using that server’s configured port.
3. Extract the release ZIP on your computer. Upload `Silent Hill 3.sh` and `sh3/` to `/roms2/ports/` (or your active Ports folder).
4. Upload your PC `sh3.exe` and complete `data/` folder to `/roms2/ports/sh3/gamedata/`. Wait for all transfers to finish; partial game archives cannot run.
5. Refresh the game list and select **Ports → Silent Hill 3** on the handheld.

The archive includes executable permissions. If your transfer client removes them on a Linux-formatted card, enable Execute for `Silent Hill 3.sh` and `sh3/runtime/sh3` in its file-permissions dialog. FAT/exFAT permissions follow firmware mount settings.

On first launch, shader caches are built locally, so give the game time to start. For the personal play preset, use the game’s Options: **Lensflare Low, Shadows No, Noise Off, Display Normal, Blood Much, Low-health indicator Off**. Confirm changes in the game. The launcher enforces 320×240 internal / 640×480 output on every normal launch. Do not change rendering resolution expecting it to persist in this fixed profile.

### Saves, updates and troubleshooting

- Exit with **Select+Start** and wait for frontend to return before powering off. Back up `sh3/state/` to preserve progress and settings.
- When updating, replace launcher/runtime/helpers from the new ZIP; keep your `gamedata/` and `state/` folders. The ZIP contains no save files to overwrite yours.
- Immediate return to Ports usually means a missing/mismatched executable, incomplete `data/`, unsupported firmware, missing PortMaster, or lost executable permissions. Check layout and hash above first. Never delete your saves to fix an installation error.
- Normal play writes no diagnostic logs. For an explicit troubleshooting run, change `SH3_DIAGNOSTICS` default from `0` to `1` in `Silent Hill 3.sh`, reproduce once, then restore `0`. Run evidence is written under `sh3/runs/`; review it before sharing. Research branch contains additional tools for developers.

## Controls

Defaults below use **physical R36S labels**, with A on the right, B below, X above and Y on the left. Firmware button swaps or a saved custom mapping can change these.

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

Remap game actions in **Options → Button Config**. Mapping persists in `sh3/state/savedata/key.ini`; preserve it when updating.

## Development and branches

[Developer guide](DEVELOPING.md) covers native ARM64 Docker builds and packaging.

- **[dev](https://github.com/ktodorow/sh3-r36/tree/dev):** source, required build dependencies, Docker recipe, release packaging and runtime helpers.
- **[research](https://github.com/ktodorow/sh3-r36/tree/research):** same R36S baseline plus project specs, reports, research, tests, device probes and saved host/device workflows. Private game data, credentials and raw device dumps remain local.

## Credits

- **[cutarev](https://github.com/cutarev)** — original [sh3-nx](https://github.com/cutarev/sh3-nx) author. Recompiler integration, Windows compatibility layer, renderer and game fixes provided the foundation for this R36S port; also created [sh2-nx](https://github.com/cutarev/sh2-nx).
- **[PortMaster](https://portmaster.games/)** team and contributors — handheld port ecosystem, controller/firmware helpers, packaging guidance and working port examples. Thanks to the Cuphead and Delver port contributors for useful launcher and diagnostic patterns.
- **[sp00nznet](https://github.com/sp00nznet/xboxrecomp)** — xboxrecomp x86-to-C lifter; **[ThirteenAG](https://github.com/ThirteenAG/WidescreenFixesPack)** — widescreen fixes adapted by upstream; **[Ligux01](https://github.com/Ligux01)** — upstream recompiler flag fix.
- **SDL2, Mesa, Linux, Debian, dArkOS and their contributors** — platform, input, audio, graphics and build foundations.
- **Konami and Team Silent** — original game and creative work. All original game rights remain with their owners.
- **Everyone who contributed code, testing, bug reports and porting knowledge**, including upstream contributors retained in Git history. R36S adaptation and maintenance by **ktodorow**.

See [CREDITS.md](CREDITS.md) for dependency notices. This fan project is not endorsed by Konami or PortMaster.
