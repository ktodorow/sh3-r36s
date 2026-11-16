# Repository independence and R36S preview release

Date: 2026-11-16. Requested directly by owner; no implementation issue selected.

## Authorization and scope

Owner requests R36S identity, public repository independence with issue history
preserved, upload of existing uncommitted changes, two branch layouts, one public
30 FPS preview release, player installation guide, developer guide and credits.
Latest explicit upload/release instructions authorize commit/push/publication.
No unrelated issue closure authorized. Original Full port acceptance remains open.

## Branch arrangement

`research` preserves all current non-private source, specs, reports, research,
tests, probes and saved host/device workflows, plus R36S cleanup and release work.
`dev` retains source, required vendored code-generation dependency, Docker build,
packaging, runtime helpers and player/developer guides. Generated game C, original
PC game files, credentials, raw device dumps, caches and build artifacts remain
ignored/local. Git history retains all original authorship. No force-push or
rewriting upstream authors into owner commits.

Active console-only toolchain, build targets, deployment helpers and conditional
runtime branches removed. Linux preprocessing compared seven affected C files
against pre-cleanup snapshot: active tokens unchanged. Generic C `switch`, input
"Hat Switch", XBE intermediate machinery and historical research references are
not retired console targets and remain where needed.

## Player profile and evidence origin

Referenced local session `01a1dec9-79e1-7dc2-ad13-9b0d240e0749` inspected. Its final
handoff confirms personal device **Silent Hill 3** entry, direct launch,
320×240 internal → 640×480 output, 30 FPS cap, Blood Much, quiet diagnostics,
clean saves, frontend/power recovery and all 82 game-asset hashes preserved.
See [personal setup report](Silent%20Hill%203%20personal%20play%20setup.md) and
[performance limits](Silent%20Hill%203%20performance%20limits.md). This task does
not execute another device run. Public build removes private embedded diagnostic
samples and is a newly built package; do not describe its binary hash as identical
to installed personal binary. No game progress, original `data.sys` or shader
cache distributed. Player can set personal graphics choices in original Options.

README describes preview limits, original FMVs skipped, first-visit stutter,
30 FPS cap rather than guaranteed all-scene floor, and incomplete campaign checks.
Release built for original-CD `sh3.exe` SHA-1
`d851669ef609b3164e3581aa8dcfbfaec866cb79`. Other supported profile requires its
own build; installed runtime marker rejects mismatched original executable.

## Validation

Existing launcher and saved build CLI boundaries retained. TDD does not apply
to prose/branch operations; docs receive link/layout/requirements checks.
Observed RED → GREEN for device-independent build, release configuration,
recognized-but-mismatched input rejection, and real ARM64 fixture ZIP creation.
Refactor review retained explicit archive allowlist and existing runtime lifecycle.
Fixture results prove packaging/failure handling, not fresh R36S acceptance.

Private local evidence: `.port-cache/repo-restructure/20261116T100120Z/`
(original working snapshot and Linux preprocessor comparison),
`.port-cache/repo-restructure/host-tests.*.txt` (host regression), and
`.port-cache/builds/<UTC-id>/` (production build identity and logs).
Host discovery: 258 tests, 77 passes, 173 skips, 8 failures in Linux-only GPU probe fixtures on macOS (missing timeout utility and /var versus /private/var path aliases). These research-only checks need Linux container validation; no device capability inferred. Syntax checks passed for 13 Python and 20 shell scripts. Final native build/test/release verification recorded in final handoff. Raw logs stay
local, not public ZIP. Existing device evidence remains untouched.

## Fork detachment handoff

Owner chose GitHub Support, keeping same repository/name and existing 19 issues
and comments. Official guide warns direct **Leave fork network** loses issue/PR
and other metadata. Do not use destructive direct detach or delete/recreate.

GitHub Support cannot be submitted from this session: no browser available;
explicit in-app browser creation also returned "Browser is not available: iab".
Repository remains public fork until GitHub Support completes detachment.

Submit at [GitHub Support](https://support.github.com/contact):

> Subject: Detach ktodorow/sh3-r36 while preserving issue history
>
> I own https://github.com/ktodorow/sh3-r36, currently a public fork of
> https://github.com/cutarev/sh3-nx. Please detach it from the fork network and
> keep it as an independent public repository with the same owner/name and URL.
> Please preserve all 19 issues and their comments, Git history and authorship,
> branches, tags, releases, stars and repository settings. I chose Support rather
> than Leave fork network because retaining issue history matters. Upstream
> authors remain credited in README and commit history. Please advise before
> taking any action that would lose existing metadata.

## Sources and applicability

- [GitHub detaching a fork](https://docs.github.com/en/pull-requests/how-tos/work-with-forks/detaching-a-fork): Support route preserves requested identity/history; direct route warning reviewed 2026-11-16.
- [PortMaster packaging](https://portmaster.games/contribute/porting/packaging/): player folder/launcher/licensing patterns; this is manual preview ZIP, not catalogue submission.
- [PortMaster installation](https://portmaster.games/installation.html): installed firmware helpers required separately.
- [PortMaster help](https://portmaster.games/faq.html): game-data placement and active Ports-folder guidance; actual tested two-card path `/roms2/ports/` from project evidence.
- [cutarev/sh3-nx](https://github.com/cutarev/sh3-nx): original recompiler/runtime/renderer foundations and known FMV omission. Reviewed source baseline `ff483a6f95b94a4f7924f6fbe4cb47169f2adb98`; upstream credit preserved.
- [dArkOSRE PortMaster guide](https://github.com/southoz/dArkOSRE-R36/wiki/PortMaster): current firmware integration reference, not proof this preview works on all variants.
- Current searches: `PortMaster R36S dArkOS systemd launch game`, `PortsMaster PortMaster-New Cuphead .sh control.txt`, `PortMaster-New Delver.sh`. No new matching first-hand SH3 release-install report found. Existing Cuphead/Delver comparisons remain in feasibility research; no engine-specific dependencies copied.
