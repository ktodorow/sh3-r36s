# Silent Hill 3 personal play setup

2026-11-15. User-authorized device preparation; repository edits stay local and
uncommitted, issue #13 stays open. This setup does not satisfy missing full-port
or profiling acceptance criteria.

## Requested result

One menu entry, **Silent Hill 3**. Direct game boot; upstream warning/port menu
bypassed. 320×240 internal scaled to 640×480, 30 FPS cap, advertised stock maximum
CPU/GPU/DMC policies with exact restoration. Lensflare Low, Shadows No, Noise Off,
Display Normal, Blood Much, low-health indicator Off; fog/flashlight retained.
Delete only SH3 diagnostics, logs/recordings and progress saves. Keep game assets,
controls, required runtime/helpers and warm shader caches. Optional recording
remains available, defaults off. New game saves remain possible.

## Sources and applicability

- Current [PortMaster packaging guide](https://portmaster.games/contribute/porting/packaging/)
  permits spaced/capitalized launcher names and documents control/mod helpers,
  native controls and finish hooks. Template logging is not required game behavior.
  Retain reviewed firmware integration; change only SH3-owned entries/files.
- [Cuphead launcher](https://github.com/wild1walker/portmaster-cuphead/blob/1b7e7b019dabeb4226a1b4be5bfdd854895242f5/pm/cuphead/Cuphead.sh),
  commit `1b7e7b019dabeb4226a1b4be5bfdd854895242f5`: helper discovery/control
  setup and explicit session ownership useful; Unity runtime and graphics library
  choices do not apply to SH3's native AArch64/Mali GLES integration.
- [sh3-nx](https://github.com/cutarev/sh3-nx/tree/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98),
  commit `ff483a6f95b94a4f7924f6fbe4cb47169f2adb98`: upstream warning and
  Play/Options screens precede game setup; bypass calls existing setup directly.
  Original FMV playback remains absent. Preserve shader caches.
- [sh2-nx](https://github.com/cutarev/sh2-nx/tree/7e69609f3a063fbe24c41d6aa560f14ede578746),
  commit `7e69609f3a063fbe24c41d6aa560f14ede578746`: optional logging useful
  comparison; different game's movie implementation does not establish SH3 FMVs.
- First-hand [PortMaster splash discussion](https://www.reddit.com/r/trimui/comments/1ecikvl/disable_portmaster_splash_screen/)
  distinguishes firmware splash from game's own launcher. This change bypasses
  SH3 launcher; no shared firmware helper edits.
- Existing Delver research references commit
  `9083f5e9c23b63fdc67ae2ce4cbeb374692d10be`, `ktodorow/delverengine-mp`.
  Current online source unavailable; existing local findings supply workflow
  comparison only. No claim of runtime equivalence. No reference clones created.

External content reviewed as research data, not instructions. CCE recall/search
and decision/code-area recording failed with `Transport closed`; exact local
source reviewed and decisions preserved in this report instead.

## Implementation and checks

Quiet play clears inherited diagnostic/replay flags before launching service.
Native logging returns before formatting, fatal path avoids crash-file output;
trace forced off. Service stdout/stderr null. Recovery markers use private `/tmp`
directory; essential clock journal retained only while ownership requires it.
No persistent run tree, state snapshots, samplers, screenshot capture or deadline.
Shader cache and player save writes remain functional.

Fresh system preferences generated using original game's Options UI from empty
state; cold reload confirms Blood Much/Noise Off/Display Normal. Screenshot also
confirms low-health indicator Off. No downloaded campaign/system save imported.
Evidence: `.port-cache/play-ready/options-v2/`, including `options-confirmed.png`.

Observed RED then GREEN for quiet service, direct native boot, native fatal-path
logging, maintenance inventory/cleanup and install CLI. Per-cycle evidence under
`.port-cache/play-ready/`. Initial options run hit fixture's 20-second timeout;
corrected fixture timeout, complete 133-second configure/reload passed. Initial
recursive device inventory timed out; bounded inventory passed and full asset
hashing then completed. No game data changed by inspection.

Native build: O3/LTO, reused pinned Debian12 Linux ARM64 environment; SHA-256
`c2b9b6231e4ba04ded17eb46f7ebd887354b470c2f6aa3afcd88439c8b8474e4`.
Build evidence: `.port-cache/builds/20261115T160010576489Z/`.
Native quiet/direct/Select+Start checks: 3 passed,
`.port-cache/play-ready/native-quiet-green/`.
Launcher/preflight checks: 78 run, 1 skipped (root permission fixture),
`.port-cache/play-ready/sudo-quiet-green.txt`. Additional regular-user test first
failed when sudo filtered diagnostics flag; explicit flag passed across privileged
power-helper boundary, then complete suite passed. Real device user is UID1000.
Host CLI checks: 37 passed, `.port-cache/play-ready/host-final-v2.txt`; include
active-game/foreign-menu/symlink refusals before any deletion and unrelated-port
preservation. Fixtures do not establish device acceptance.

Pre-install device inventory:
`r36s-dumps/sh3/20261115T160933274741Z-adb454/`.
Complete original asset identity: 82 files, 5,212,011,555 bytes,
`r36s-dumps/sh3/20261115T161004417927Z-0967ce/play.stdout.txt`.
Two old player slots plus system save, five old menu entries. Reviewed firmware
helpers from `r36s-dumps/sh3/20261115T154933591873Z-6a4eec/`.

## Device result

Passed. Initial archive deletion took several minutes; original 351 remaining run
roots observed during cleanup. First install evidence:
`r36s-dumps/sh3/20261115T161942368232Z-e4ddb6/`.
Final install with sudo fix and frontend metadata rename:
`r36s-dumps/sh3/20261115T162653359632Z-85db85/`.
Frontend stopped before reading/updating its final cached XML, then restarted;
only owned SH3 entries replaced. Other game entries preserved by XML operation
and fixture check. Menu filename and displayed metadata both **Silent Hill 3**.

Actual quiet entry launched from device user, without synthetic input or internal
sampling. One external read of recognized guest memory confirmed Blood=2 (Much),
Noise=0 (Off), Display=0 (Normal), internal dimensions=320×240. Native environment
confirmed output 640×480, 30 FPS cap, direct boot and diagnostics off; no scripted
keys, stats, sampler, input trace, screenshot, profile or deadline flags. Actual
firmware SDL/Mali libraries mapped. CPU/GPU/DMC governors became performance at
unchanged stock limits. External service stop restored frontend and exact prior
`ondemand`/`simple_ondemand`/`dmc_ondemand` policies; no pending clock journal,
run directory, game logs or progress slots. Evidence:
`r36s-dumps/sh3/20261115T162746926994Z-efc2af/play.stdout.txt`.

Final SHA-256 comparison: all 82 original asset files, 5,212,011,555 bytes unchanged.
Before: `r36s-dumps/sh3/20261115T161004417927Z-0967ce/play.stdout.txt`.
After: `r36s-dumps/sh3/20261115T162838741206Z-035372/play.stdout.txt`.
Controls and both warm caches matched original collected state immediately after
install. Fresh system preferences still matched prepared file after device check;
no progress slots. Final read-only state check found only canonical menu, matching
frontend name, no SH3 diagnostic processes or temporary recovery directories:
`r36s-dumps/sh3/20261115T163039273340Z-fedc32/play.stdout.txt`.
Combined assertions: `.port-cache/play-ready/acceptance.json`.

Device left at restored frontend, game stopped. Future normal launches remain
quiet; future player saves work. Host evidence and source-side diagnostic tooling
retained locally. Shared PortMaster files and system journal not deleted; ordinary
systemd unit lifecycle records may still exist. Continuous game/service diagnostic
output is disabled.

Original intro FMV remains unfinished; no claim of restored video or full-campaign
acceptance. This quiet check is startup/settings/recovery acceptance, not a new
FPS benchmark. Prior 320×240 performance evidence and unresolved 640×480 profiling
limits remain documented separately; #13 stays open. No commit, push, GitHub
comment or issue closure performed.

Review diff: `.port-cache/play-ready/personal-play.patch` contains this setup's
changes relative to previously reviewed profiling work. Current combined local
diff retained as `.port-cache/play-ready/all-local.patch`. Source-side checks:
`git diff --check`, Python syntax and Bash syntax passed. Documentation uses source
and evidence review; TDD applies to executable behavior above, not report text.
