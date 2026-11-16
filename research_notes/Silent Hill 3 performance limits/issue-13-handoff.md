# Issue #13 research handoff — local draft

Prepared 2026-11-15 for [issue #13: Profile correct representative gameplay at 640×480](https://github.com/ktodorow/sh3-r36/issues/13). **Not posted. Changes remain local and uncommitted. Keep issue open.** Base reviewed commit: `d4e49600b1022c954baac1965767bb3a5d61b80a`.

## Measured outcome

Actual unattended R36S movement/combat and public-save routes completed. Final minimum-profile park room 210 reaches **25.42486 FPS at 640×480 Internal and Output**, 75–120 s, with **39.095 / 45.128 / 46.237 / 67.410 ms p50/p95/p99/max**, minimum complete 1 s/5 s **21/23.2 FPS**, 19/45 one-second bins below 25 and longest below-25 span eight seconds. Mean 39.334863 ms needs **6.001530 ms** reduction to reach 33.333333 ms. Harder fixed minimum-profile warm 640 view reaches **22.63962 FPS**, mean 44.176566 ms: **10.843233 ms** remaining. Neither passes requested smooth true-640 30 FPS. These are current software/configuration limits, not a physical hardware ceiling.

Earlier frozen `485` public-save mall 18, hospital 160 and church 240 routes reach **29.99991 / 29.99991 / 29.98285 FPS**, true 640×480, with alive movement. Those routes use Blood Normal; final minimum park uses Blood Little and final `becb` executable. They establish workload dependence, not same-binary full-campaign acceptance. [Full report](../../reports/Silent%20Hill%203%20performance%20limits.md), [device evidence](measurement_plan.md), [runtime attribution](cpu_runtime.md).

## Literal issue acceptance coverage

| Existing issue requirement | Completed evidence | Residual boundary / status |
| --- | --- | --- |
| Survey supported graphics and define exact lowest profile without losing gameplay/story essentials | Native UI, guest-code mapping and independent cold reload establish **Lensflare Low, Shadow No, Noise Off, Display Normal, Blood Little**. Flare/shadow encoded 1/1; scratch options bytes explicitly distinguished from active state. Sharp measured as alternative with no gain. Native supported controls surveyed. | Profile mapping established. Essential fog/flashlight/transparency retained; complete paired audiovisual/effect/story acceptance not certified. Do not infer a visual pass from settings bytes alone. |
| Warmed matched scenes, cold/warm caches, build/data identities, fixed save/camera and comparable thermal conditions, 640×480 Output | Four exact frozen `173` minimum-profile fixed-view cases: Internal 640/320 × application-cache cold/warm. Output, actual backbuffer and drawable verified 640×480 in every case. Cold misses/writes and warm restores confirmed; warm cache derived only from corresponding cold case; other seed bytes unchanged. Build/seed/plan hashes, thermal samples and all stock clocks retained. | Application caches cold only; no global driver/OS cache purge. Samples document heat rather than proving identical temperatures or excluding every sub-sample transition. No cross-epoch or unequal-window performance equivalence claimed. |
| Frame distributions/dips, loading/shader stalls, audio, per-thread CPU, GPU/render work, uploads/I/O/sync, memory and hot clocks | Completion p50/p95/p99/max and complete-bin floors; CPU/wall split for producer/worker/swap; cold/warm program census, loading CPU samples, turn queue attribution; real Arm counters; GPU/DMC/Noise controls; upload scope, memory/fault/temperature telemetry and ALSA event windows. | Process byte accounting unavailable even as root; low global I/O wait is not an I/O clearance. Counter samples short and observers perturbed. Physical audio listening, full campaign and final true-640 soak remain broader capability gaps. |
| Separate CPU, GPU, memory, I/O and synchronization limits before choosing optimization | Resolution/GPU/DMC interventions establish graphics and memory-frequency sensitivity; CPU stages overlap; sampled RAM shows headroom; queue wait and diagnostic pacer costs identified. `glFinish` relocates deferred completion wait. | **Unqualified AC pass withheld:** ordinary GPU execution versus display/GBM/page-flip waiting remains unseparated, and process I/O cost remains unmeasured. Candidate priorities are justified experiments, not all-domain attribution completion. |

Issue sentence “Profiling can pass as measurement work while 30 FPS capability remains unpassed” permits a failed FPS result; it does **not** waive remaining measurement requirements. Current result supports a useful research handoff, not blanket acceptance or automatic closure. Closure under unchanged wording needs remaining attribution; alternatively owner must explicitly accept a bounded measurement scope. Full-port AC06/07/08/12/13 remain distinct from this research handoff. No publication, commit, push, tracker update or closure occurred.

## Evidence that changes the optimization choice

| Finding | Exact interpretation | Next action |
| --- | --- | --- |
| GPU stock-max contrast **+20.75%**, DMC 786→528 **−7.30%**, Noise Off **+10.315%** in respective matching earlier contexts | Graphics and memory-frequency sensitivity; supported quality control matters. Percentages cannot be combined across contexts. Guard remains opt-in diagnostic. | Preserve native minimum profile and actual stock domains during comparisons; implement owned game-lifetime shipping policy only with restoration acceptance. |
| Warm fixed 640 **22.63962** versus warm fixed 320 **30.00050**, both 640 Output; producer approximately 27.5–27.8 ms and worker approximately 10.8–10.9 ms | Native pixel/deferred graphics path constrains throughput; concurrent CPU lanes are not additive. 320 is an attribution control, not requested true-640 completion. | Reduce measured graphics/presentation critical path by roughly 6–11 ms, retaining essential pixels. |
| Warm binary caches eliminate source compile/link; first room **2.29–2.36 s cold → 0.69–0.71 s warm** | Existing binary cache helps loading substantially but does not recover steady 640 performance. Approximately 555 ms producer loading CPU remains. | Profile proven RGBA conversion and guest parsing separately; no unproved decompression or I/O claim. |
| Coarse first turn: queued Create wait **40.108 ms**, matching worker chunk begins **31.376 ms** later; actual Create <1 ms, Binary **1.030 ms**; previous Swap **32.713 ms** overlaps | First-use queue availability and synchronous round trips, not 40 ms shader compilation. Sole ReadPixels occurs at 51.074 s loading, not 82 s turn. | **Unimplemented two-stage cached native-program preparation**, then guest metadata attachment. Existing ready-key prewarm is already implemented. Require lifecycle/cache fallback/pixel/memory tests and observer-off tail gain. |
| Full trace adds **18.625 ms worker CPU**, approximately **−30.7% FPS**; coarse adds approximately **0.204 ms worker CPU**, yet **−6.03% FPS** in one final pair | Full trace rejected baseline; coarse useful attribution with material observed throughput difference and route/preflight/thermal limits. Zero event drops do not prove zero observer cost. | Keep trace-off/counter-off controls; calibrate clocks and quantify each observer before using timings as baseline. |
| Drain result **13.83967 FPS** with Finish **28.660 ms**, Swap **0.300 ms** and pacer **33.077 ms** per completion | Intentionally perturbed diagnostic. Added pacer approximately 32.399 ms explains most frame increase; 72.264 ms is not physical GPU time or shipping regression. | Design presentation/GPU attribution that preserves pacing or accounts for it; no further inference from drained FPS. |
| Actual SDL 2.32.10 forces effective interval 1 even when 0 requested; actual performance timer is gettimeofday/1 MHz | Existing request-0 cases did not disable vsync. Historical RAW-to-SDL per-frame/counter/audio associations withdrawn. | Controlled port-local SDL stage/fallback diagnostic, preserving ABI/firmware behavior. Same-board fallback is relevant but not a proven speed fix; no provider replacement performed. |
| Arm native counters work: 236 metrics; independent approximately 3 s samples GPU pending **71.10/72.96%**, conditional ALU **73.56/76.75%**, texture approximately **23%** | Real measured activity, concurrent denominators; no additive utilization or physical saturation conclusion. | Use calibrated longer matched data if a future pass/shader optimization depends on those counters. |
| Approximately 310 MiB RSS, >540 MiB available, stable warm major faults; `/proc/PID/io` and root/self I/O absent | No observed sampled RAM capacity ceiling; process I/O unresolved. Missing kernel config prevents exact config-flag claim. | Measure conversion/loading and available I/O alternatives without treating low system I/O wait as a process pass. |

Translated math remains a secondary candidate: inlined `round24` sites occupy 15–16% of producer PC samples; the earlier out-of-line-zero result describes a different attribution method. Finish independent numeric oracle before native/NEON kernels, preserve rounding/FP state and reject fast-math/reassociation. Existing caches, asynchronous uploads, DISCARD copy removal, FBO cache, ready-key prewarm and `-O3`/bounded LTO are already present; do not propose them as new work. [Source, methods and pinned research](cpu_runtime.md), [counter and exact SDL source audit](gpu_counter_probe.md), [initial renderer audit with chronology notice](gpu_renderer.md).

## Reproduction identities and retained raw evidence

| Epoch | Executable SHA256 | Used for |
| --- | --- | --- |
| Historical `2ac6` | `2ac6b9c02579ff37d20a920edde36a203458aeded0806f9e86ffecf4bc512ff9` | Published earlier #13/#14 comparison; preserve as history |
| Frozen `787` | `787ca300fd6bf8d23e8cc6579cfc9d0228fc10c6c37b89336416c0fb012894c7` | Default/stock-domain GPU control |
| Frozen `485` | `485f25039e3e190c501610cf02a4245e1acd948997cd811f7c5faa596d691eeb` | Noise/Display, DMC, public-save rooms and hardware counters |
| Frozen `173` | `1738d4ad3b98aa38729c8f59a561ffe0be2147ff29251974c5cacd272ddb082d` | Exact minimum fixed camera cold/warm matrix; rejected full-command observer |
| Final `becb` | `becbc930874e09b528adab3d9b885fc5272718522475ec14ba6156f7ffb27b68` | Minimum moving OFF, coarse and coarse+drain controls |

Final Build ID `3fb27c01011a3612d1763f6be70b4361fa94435c`; debug SHA256 `0b085784f40334bb65b10eecfd25c32f14da968b435392d06fbf49b0c7b14889`. Final minimum seed `data.sys` SHA256 `c41256a3920705ed09996ceb11bb474c8e437de524eff52819c4adc782c573d0`, unchanged `data.001` SHA256 `fa2d9fd1b7c1e2af9b9b771b2a996f988f5b82bdd8cda41d045975f31b787515`, `disp.ini` SHA256 `27a40ce6f83f520e5ac9a8b2511796ee7a63ea9166439db42e4f69420f31e600`. Raw settings/saves remain ignored; identities are sufficient for shared documentation.

| Case | Full retained run ID |
| --- | --- |
| Final minimum moving, trace/counters/drain OFF | `20261115T140929993471Z-d958cc` |
| Final minimum moving, coarse | `20261115T143222756103Z-14a5a0` |
| Final minimum moving, coarse+drain | `20261115T143559336520Z-331517` |
| Fixed minimum 640 cold / warm | `20261115T134954008713Z-507725` / `20261115T135726264524Z-899c2e` |
| Fixed minimum 320 cold / warm, Output 640 | `20261115T140116608881Z-ea97cb` / `20261115T140511267080Z-93a47a` |
| Mall / hospital / church | `20261115T123732242048Z-5f8010` / `20261115T125746122373Z-3572b6` / `20261115T130244860301Z-7500f4` |
| Exact SDL/root-I/O provider inventory | `20261115T130739207517Z-4fa06c` |
| Verified owned redundant-payload cleanup | `20261115T143014131290Z-d30f92` |

Local-only raw roots: `r36s-dumps/sh3/<run-id>/`, `.port-cache/runtime-attribution/`, `.port-cache/issue-13-limits/`. Independent index `.port-cache/issue-13-limits/final-device-evidence-index.json` validates the ten final/cache/multilevel runs’ actual executable/scene identities, all status-zero exits, source preservation, unchanged 59 firmware hashes and exact restore journals. It also checks final frontend-active/no-PID state and all 20 immutable retained cleanup executables. `.port-cache/issue-13-limits/cache-matrix-resolution-proof.json` checks dimensions. `.port-cache/runtime-attribution/becb-coarse-observer-hitch.json` and `becb-coarse-drain-phases.json` retain calibrated hitch/drain accounting. Per-run `75000-120000.json` joins retain final moving frame details. [Saved workflow and route catalog](../../scripts/README.md).

Failure/retry history remains intact. ENOSPC interrupted a coarse attempt before game execution; exact task-owned redundant payload cleanup reclaimed **644,664,432 bytes**, recovering **631,424 KiB** available. No installed runtime, saves, logs or run directories removed. Final drain entry had 530,560 KiB available; frontend active and no runtime PID after all exact policy restores. Previous collection timeouts retain both original failure and successful scripted collection retry; one earlier scene-identity metadata erratum remains documented and actual device SHA is authoritative.

## Validation and review boundary

| Validation | Retained result / evidence |
| --- | --- |
| Saved host CLI | **32 PASS**, 31.330 s; `.port-cache/issue-13-limits/final-device-cli.txt` |
| ARM64 frontend workflow | **51 PASS + 1 expected root-readonly-sysfs SKIP / 52**, 12.086 s; `.port-cache/issue-13-limits/final-frontend-session.txt` |
| ARM64 evidence archive | **1 PASS**, 0.018 s; `.port-cache/issue-13-limits/final-evidence-archive.txt` |
| Final `becb` actual-game focused checks | **4 unique cases, 5 PASS executions**, no skips: coarse GREEN 17.317 s and REFACTOR repeat 17.147 s, full trace 30.891 s, drain 31.238 s, default checkpoint 62.986 s; `.port-cache/optimization-uniforms/{coarse-green,coarse-refactor,coarse-final-fulltrace-regreen,coarse-final-drain-regreen,coarse-final-default-checkpoint}` |
| Earlier frozen `173` GLES regression | **35 PASS**, 124.812 s; `.port-cache/optimization-uniforms/final173-gles-regression`; separate binary, not 35 tests of final `becb` |
| Documentation synthesis | TDD not applicable; validate source links, units, identities, privacy and three-context-line local diff. Root static shell/Python/scene checks and `git diff --check` pass; final review artifact `.port-cache/issue-13-limits/local-review.patch`. |

Focused current checks do not establish every historical broad-suite test passing. Earlier full `485` ARM64 run retained 109 passes, 86 explicit skips and one external-Git-fixture failure; focused fixture handling was checked separately. Host/container tests establish their documented behavior, not handheld physical audiovisual compatibility.

No outstanding game, sampler, device run or build remains from this campaign. No more device testing is required to review this handoff. Next implementation should select one ranked candidate, use required behavioral RED–GREEN–REFACTOR at existing launcher/game/frontend boundary, then rerun observer-off fixed and moving controls with same identities and actual clocks. **Current approval boundary is publication of reviewed work with #13 remaining open. Closure requires its remaining acceptance to pass or explicit owner acceptance of revised bounded scope.**
