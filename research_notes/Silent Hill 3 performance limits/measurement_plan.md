# Measuring Silent Hill 3 R36S performance limits

Issue [#13](https://github.com/ktodorow/sh3-nx-r36s/issues/13), research and saved-workflow diagnostics, 2026-11-15. Initial baseline uses candidate SHA256 `2ac6b9c02579ff37d20a920edde36a203458aeded0806f9e86ffecf4bc512ff9`, input profile `d851669ef609b3164e3581aa8dcfbfaec866cb79`. User subsequently extends scope to actual unattended movement, public-save levels, opt-in worker attribution and reversible stock-policy experiments, recorded below. All new changes remain local/unpublished; no game-math, driver, frequency-limit, OPP, voltage or thermal-control changes. Issue remains open.

## Current scope and evidence status,2026-11-15

Issue13 is profiling/limit identification work: lowest supported graphics mapping,
matched warm/cold scenes and identities, full frame-time/dip/CPU/GPU/memory/I/O/
synchronization evidence, and separation of limiting domains. Its text explicitly
allows measurement work to pass while30FPS capability remains unpassed.
Canonical full-port AC07 still targets30FPS,640internal first/320conditional,
640output and original speed; owner accepts brief25 dips but rejects15–20
stretches, with exact allowed duration still unset. No mean-FPS waiver invented.
Campaign/media/physical audiovisual acceptance remains separate. Live issue13
body and all comments reread2026-11-15; stillOPEN, no tracker write/publication.

Latest frozen485/NoiseOffNormal/Lowflare/NoShadow/full stock controls:

| Automated live route, true640 | Completion FPS | Min complete1s/5s | Run |
| --- | ---: | ---: | --- |
| Hard owner checkpoint,room210,counterOFF |25.86971|21/22.6|`d498a8`|
| Public mall,room18 |29.99991|30/30|`5f8010`|
| Public hospital,room160 |29.99991|30/30|`3572b6`|
| Public church,room240 |29.98285|29/29.8|`7500f4`|

Full UTC run IDs,75–180 versus48–160 windows, seed/plan/cache/native hashes,
live positions/health/options, audio/cache/clock limits and restoration/collection
proof are preserved in chronological sections below and immutable raw runs.
Public saves from cited SilentHillMemories/SilentRain archive remain isolated;
owner save sources preserved. Three added loaded-room routes pass scoped warm
render floor; hard room210 remains below owner floor. No campaign-wide or30FPS
640 acceptance claimed. Stock-clock contrast and resolution pair establish GPU/
presentation-sensitive critical path; sampled GPU pending~71–73% is not immutable
hardware saturation. Actual captured SDL forces interval1 and uses gettimeofday;
prior RAW→SDL temporal envelopes explicitly withdrawn below. Final buffered coarse
trace and preSwap drain controls completed below. They identify queued synchronous
work and a diagnostic pacing interaction; baseline GPU-versus-display split
remains unresolved rather than proving an immutable hardware ceiling.

New frozen173 minimum-setting fixed640 cache pair now records Blood Little,
NoiseOff and DisplayNormal on actual device. Cold application-cache loading has
a2.293s first-room completion stall; its warmed55–95s plateau22.98994FPS versus
binary-restored warm run22.63962FPS. Startup cache benefit does not solve sustained
frame budget. The full per-command173 trace itself adds18.625ms workerCPU per
frame and lowers throughput30.7%; its timings are perturbed. Separate coarse
candidate's matched observer controls now quantify its remaining perturbation.
Final becb/BloodLittle moving trace-off control is25.42486FPS in75–120s,
with19/45 complete1s bins below25 and longest8s stretch. Coarse trace lowers
throughput to23.89162FPS while adding0.204ms workerCPU;6.03% throughput difference
remains material and includes route/preflight/thermal variation. Drain control
falls to13.83967FPS because it moves deferred work before Swap and triggers about
33.08ms limiter sleep per completion. Its72.264ms interval is not GPU execution
time. Coarse timings cannot be treated as zero-observer ordinary play.

NoiseOffNormal hardroom full75–180s moving mean38.656ms needs about5.323ms/13.8%
less critical-path time to reach33.333ms. Selected75–120s moving window instead
averages40.568ms/24.65071FPS,about7.234ms over budget; fixed-pose640 with optional
pacer0/forcedSDLinterval1 is21.37981FPS,about46.77ms/13.44ms over budget. These
are distinct scene/window deficits;5.323ms reduction is insufficient evidence
for every representative view. ProducerCPU28.350ms in full moving window already
leaves about5ms of that budget. Overlapping lane costs must not be added. Controlled GPU
frequency400→520MHz at heldCPU/DMC improves fixed-scene throughput20.75%;
heldCPU/GPU with DMC786→528MHz lowers moving throughput7.30%, with route/audio
variation retained. Current sampled memory leaves about540MiB available, without
new major faults in hardroom warm control. Per-process I/O interface absent even
for actual UID0 (`/proc/self/io` ENOENT); installed kernel config files unavailable.
System sampled-span iowait low, not proof isolated loading stalls absent.

Earlier2ac6 figures and initial gaps below are historical baselines retained for
traceability, not latest frozen485 outcome or superseding current measurements.

## Historical initial2ac6 raw evidence

### Takeaway

Current true640×480 combat route needs roughly **9.78ms less elapsed time per completed frame** to reach30FPS: about23% frame-time reduction, or29% throughput improvement. This is target-budget arithmetic, not an optimization projection or immutable hardware limit. Current320×240 already reaches30FPS cap; its uncapped headroom is unknown.

### Cited Findings

Recomputed directly from current raw CSVs and logs, using runtime-relative interval `[75,180)` seconds. Actual worker SDL-return timestamps, rather than producer submissions, determine completion FPS. Endpoint formula is `1000*(N-1)/(last_elapsed_ms-first_elapsed_ms)`. p50 is median; p95/p99 use sorted element `floor((N-1)*q)`; no stall clipping. Complete wall-clock1s/5s bins include zero-completion bins and exclude partially observed edges. Existing implementation and reproducible saved command: [performance.py](../../scripts/host/performance.py), `python3 scripts/host/performance.py r36s-dumps/sh3/<run-id> --start 75 --end 180`. That command writes ignored summary beside original raw files.

| Raw metric,75–180s | True640×480 |320×240 internal /640×480 output |
| --- | ---: | ---: |
| Run ID |`20261114T055246314042Z-4068d8`|`20261114T050230071532Z-0ddc92`|
| Completion samples |2435|3149|
| Endpoint completion FPS |23.196638|29.990378|
| Arithmetic mean completion interval,ms |43.112208|33.343834|
| Completion interval p50 /p95 /p99,ms |42.656 /51.373 /53.331|33.326 /34.226 /35.315|
| Maximum completion interval,ms |82.274|60.180|
| Lowest complete1s /5s FPS |19 /19.8|29 /29.8|
| Producer CPU mean /p50 /p95,ms |28.887281 /28.696791 /30.249041|28.748008 /28.661791 /30.363083|
| Producer draw mean /p50 /p95,ms |3.394200 /3.349 /3.616|3.336856 /3.300 /3.626|
| Producer Present mean /p50 /p95,ms |13.886012 /13.704 /22.061|0.242478 /0.024 /1.297|
| Worker actual SDL swap mean /p50 /p95,ms |31.148860 /29.489 /39.628|12.666609 /12.443 /14.409|
| Mean submitted draws/frame |374.802|366.046|
| Mean uploaded buffer bytes/frame |140261|140287|

Raw inputs for each run: `launcher/frame-times.csv`, `launcher/frame-times.csv.presents.csv`, `launcher/frame-times.csv.samples`, `launcher/stdout.txt`, `scene-identity.json`, `runtime-health-summary.json`, `service/performance.txt`; existing `performance-summary.json` agrees with recomputation. Both have same executable, identical five original seed inputs, room210,30FPS cap, warm47-program cache, A8R8G8B8, shadow1/lensflare_ztest1 and640×480 output. Both report source preserved, orderly exit and frontend return. Neither contains `.gpu.csv`. [Current report](../../reports/issue-13-performance.md), [cache/renderer history](../../reports/issue-14-renderer-caches.md).

640 run has68 of105 complete1s bins below25FPS, including28 consecutive bins `[75,103)`;20 bins at20FPS or lower, longest8 consecutive bins `[75,83)`.320 has no complete1s bin below25FPS. These are sustained slow stretches, separate from occasional large stalls. Whole-second bins do not measure exact continuous dip onset/duration. Both reports retain every requested-window stall.

Warmed pair game-clock/wall ratios are1.000329 and1.000031; timer near60Hz.640 has41/41 live observations and40 distinct player positions;320 has52/52 and47 positions. Actual ammunition changes prove firing/reload. All36/37 coarse monitor frequency samples show CPU1512MHz and GPU520MHz; maxima75°C and71.25°C. Both restore47 program binaries with zero source misses/cache writes/rejections and no logged ALSA recovery. These controls establish active play and matching configuration, not perfectly identical workload or heat. Raw records above plus [CPU analysis](cpu_runtime.md).

### Inferences

- `1000/23.196638 =43.109696ms`; target `1000/30 =33.333333ms`. Difference9.776363ms,22.6779% elapsed reduction,29.3291% throughput gain. Arithmetic raw interval mean43.112208ms gives9.778874ms and22.6824%; keep rounded≈43.11/9.78/23%/29% when comparing different estimators.
- Resolution affects exposed critical path substantially. Fixed640 output alone cannot explain entire difference, because output resolution stays unchanged. Source-target work, dependent GPU completion, driver synchronization and page-flip scheduling remain candidates.
- Producer CPU≈28.7ms already consumes substantial33.33ms budget. It is **producer-thread CPU**, not total process CPU or renderer-worker CPU. Producer draw, Present, worker swap and CPU measurements overlap; adding their means/medians would double-count concurrent/nested work.
- Identical wall-clock inputs do not guarantee identical game-time camera/AI/render work after performance changes. Current mean draw counts differ≈2.4%. Capped320 cannot supply uncapped CPU/GPU floor or justify fitting two-point pixel-cost/Amdahl model. New fixed-camera triplet narrows one comparison, followed by event-matched gameplay validation.

### Gaps

No current-pair direct GPU measurement, worker CPU attribution, per-frame upload execution time, calibrated memory-bandwidth counter, exact wait ownership or scanout latency. No demonstrated “hardware ceiling.” Owner accepts brief25FPS dips and rejects15–20FPS stretches; exact allowed dip duration remains unsettled. Do not silently invent duration waiver or certify target from mean FPS.

## Do prerequisite rendering and timing capabilities pass actual saved evidence?

### Takeaway

Existing raw rendering/timing evidence passes its actual assertions. Current executable has verified native graphics primitives and clean lifecycle. Historical full-scene/timing checks provide scoped regression support; they do not establish current true640 performance acceptance or independent Windows/D3D scene equivalence.

### Cited Findings

Reran host-interpreted evidence tests without compiling, contacting device or regenerating measurements:

```sh
SH3_GLES_EVIDENCE=r36s-dumps/sh3/20261114T045123906063Z-4d0905 PYTHONPATH=tests python3 -m unittest test_gles_evidence.GraphicsEvidenceTests -v
SH3_TIMING_EVIDENCE=r36s-dumps/sh3/20261113T153402195172Z-62d223:r36s-dumps/sh3/20261113T153756765133Z-36d407 PYTHONPATH=tests python3 -m unittest test_timing_evidence -v
SH3_GAME_EVIDENCE=r36s-dumps/sh3/20261112T221140610647Z-db57be SH3_GAME_SERVICE_EVIDENCE=r36s-dumps/sh3/20261112T221140610647Z-db57be PYTHONPATH=tests python3 -m unittest test_game_evidence.GameSessionEvidenceTests test_game_evidence.FrontendSessionEvidenceTests -v
```

Results: **27 native graphics cases PASS**, **1 timing-pair case PASS**, **2 actual gameplay/frontend cases PASS**. Graphics record uses current2ac6 binary, Mali-G31 GLES3.2/KMSDRM, actual ordered worker/context lifecycle and saved pixel samples, including palette alpha, depth/stencil and sampler behavior. Host tests also check orderly cleanup, source preservation and firmware-library consistency. These checks read actual recorded device evidence; fixture behavior is not substituted. [Rendering report](../../reports/issue-06-scenes.md), [timing report](../../reports/issue-09-audio-timing.md), [evidence tests](../../tests/test_gles_evidence.py).

Timing pair uses older candidate, separately640 and320 internal with640 output: live room210, recorded held-input interval, game clock ratios1.000744/1.000350, measured movement595.010/610.005 units/s against existing600±60 reference, expected source hashes and frontend cleanup. Recheck verifies saved facts, not new device execution. Current pair independently preserves clock ratio; no new movement-distance oracle was fabricated. [Timing tests](../../tests/test_timing_evidence.py).

Full-scene rendering records cover five historical640 scenes: park cold/warm, hospital, mirror and opening (`20261112T221140610647Z-db57be`, `221608193726Z-29dd1b`, `222027055578Z-35280e`, `222420259797Z-181f5f`, `222825787345Z-7f44ef`; latter four share date prefix20261112T). They support actual scene loading/orientation and known regressions. Desktop Mesa reference can share compatibility-layer defects; it is not independent original Windows/D3D oracle. Full current-binary campaign/scene correctness remains separate acceptance work. [Rendering report](../../reports/issue-06-scenes.md).

### Inferences

Prerequisites permit diagnostic measurements through existing launcher→game→frontend boundary. They do not authorize changing fog, alpha, simulation clocks or scene semantics to buy FPS without corresponding correctness checks.

### Gaps

Actual graphics primitive pass is narrower than all-game visual equivalence. Automated no-ALSA-line result is narrower than listening acceptance. Historic timing candidate must not be mistaken for exact current-binary full movement/collision/fire revalidation; existing current build history documents separate checks.

## What can existing timer queries measure, and what changed in saved workflow?

### Takeaway

Binary already implements opt-in asynchronous GLES elapsed queries. Saved scene parser previously failed to forward opt-in, so bounded script-only TDD slice exposes it without rebuilding binary. Query result is time for its instrumented command region; correctness, coverage of present/tilestore and observer cost require triangulation.

### Cited Findings

Worker starts elapsed query before first queued command chunk, keeps it open across chunks and ends it immediately **before** `SDL_GL_SwapWindow`. Thus SDL/driver internal present commands lie outside region. Driver-dependent tile↔system-memory transfers may be excluded from elapsed query by EXT specification. Availability checks, delayed reads and disjoint handling avoid simply blocking on fresh query, but do not prove negligible observer cost. [GPU source audit](gpu_renderer.md), [Khronos EXT_disjoint_timer_query](https://registry.khronos.org/OpenGL/extensions/EXT/EXT_disjoint_timer_query.txt).

Historical actual query run `20261113T223112187035Z-7965b3` exposes64 counter bits,3476 rows, zero skipped slots and one disjoint discard.55–95s has824 samples, mean0.888596ms/p990.970312ms while worker swap mean36.739ms and completion20.60076FPS. This older observation does not establish full GPU headroom; query region may omit expensive work and enabling queries may change pipeline ordering. Current pair has no query data.

Local saved workflow changes:

- `scripts/device/runtime.sh`: validates `gpu_profile` is strict JSON boolean; forwards `SH3_GPU_PROFILE=0/1` through existing detached game boundary. Absent field explicitly disables inherited enable flag.
- `scripts/scenes.json`: matched `profile-gpu-off-640` and `profile-gpu-on-640`,100s, fixed checkpoint/camera,30FPS,640internal/output, no captures, frame profiling enabled. Only diagnostic boolean differs.
- `scripts/README.md`: records commands, immutable seed,55–95s comparison and query attribution limits before device work.
- Existing frontend fixture checks runtime-process environment, cleanup and early invalid-plan rejection. Existing host CLI fixture checks deployed plan; neither fabricates GPU CSV or proves hardware query validity.

Observed RED→GREEN→review/refactor cycles: missing runtime forwarding fails before minimal forwarding; missing scene choices fail before manifest additions; non-boolean value reaches game before strict validation, then fails before service/game start. Final interpreted checks:26 frontend cases PASS in DockerARM64,11 host CLI cases PASS, shell syntax and scene JSON PASS. Default/off test injects inherited `SH3_GPU_PROFILE=1` and observes actual fixture runtime value0. Logs under ignored `.port-cache/issue-13-limits/`: `gpu-forward-red.txt`, `gpu-forward-green.txt`, `gpu-forward-refactor.txt`, `gpu-scenes-red.txt`, `gpu-scenes-green.txt`, `gpu-boolean-red.txt`, `gpu-boolean-green.txt`, `gpu-forward-final-regressions.txt`, `gpu-scenes-final-regressions.txt`. Existing image reused; no compiled test artifacts or runtime build. Applied `mattpocock-skills:tdd` plus testing/mocking references to scripts/tests. Pure research paragraphs need source/raw-data validation, not executable TDD.

Fresh saved inventory `20261115T105850400561Z-de8c0e` passes preparation/deployment/execution/collection0. Installed helper SHA manifest exactly matches current verified native GLES run. Read fresh control/device-info/functions/ArkOS module/Dialog/mapper before launching. Successful headless path does not invoke pugwash dialog process. Existing launcher overrides broad helper input cleanup; frontend/service wrapper owns recovery. Helpers are untrusted inspected data, not task instructions. Package2ac6 and profile d851 identities verified before run; originals and previous runs preserved.

### Inferences

Triplet would answer whether current query path is available and whether enabling it visibly changes cadence. Off/on/off brackets drift but single middle run cannot deliver statistically established observer-overhead percentage. Fresh first off run exposed different power policy, so planned triplet was paused after already-active on run; do not mechanically complete invalid comparison. Small query plus long swap leaves present/queue/tilestore cost unresolved. Missing/invalid results must fail attribution rather than be interpreted as zero GPU time.

### Gaps

No existing swap-interval scene can disable current runtime's hardcoded `SDL_GL_SetSwapInterval(1)`. A genuine swap0 diagnostic requires separate bounded C/TDD/build work and actual returned-mode logging. `SDL_GL_GetSwapInterval()` reports actual context mode with documented ambiguity when unsupported; record set return code too. [SDL SetSwapInterval](https://wiki.libsdl.org/SDL2/SDL_GL_SetSwapInterval), [SDL GetSwapInterval](https://wiki.libsdl.org/SDL2/SDL_GL_GetSwapInterval).

## Which experiments identify each limit, in what order?

### Takeaway

First separate missing attribution from real saturation. Then optimize only measured expensive work, one reversible change per matched comparison, keeping30FPS timing, visual effects and640 output/true internal resolution. Existing ordered worker, async owned uploads, state/uniform/program caches, prewarm and DISCARD texture rotation already exist; repeating their descriptions is not new optimization work.

### Cited Findings

| Order / hypothesis | Smallest useful experiment | Diagnosis signature / decision | Workflow status |
| --- | --- | --- | --- |
|0. Workload/identity | Freeze executable/profile hash, five seed files, settings1/1, camera/pose, room, health, clock, capture-off and target dimensions. Compare equivalent game-time events for routes. | Reject attribution when changed state/menu/death, new shader misses, thermal downclock or divergent events explain result. Keep failures, loading and cold-cache traces. |Existing scene identities, PEEK and saved reports; named fixed-camera triplet added locally.|
|1. Power-policy control, then query validity/observer | Inspect before/after frontend policy and available stock governors/frequencies; source-review firmware owner. Only after reversible session-scoped plan/test, matched-policy current-binary640 off/on/off100s;55–95s warm window. Count rows, skips, disjoints, query precision; compare actual completion and producer/worker timings, clocks and fixed pose. | Reject historical/new comparison across changed governor/frequency. Large on-only slowdown or missing query coverage invalidates full-frame GPU attribution. Tiny query with long swap remains unresolved. |Fresh default-policy off/on exploratory pair recorded below. Third run paused on policy confounder. No runtime build or policy writes.|
|2. Present versus scene GPU | Same SDL/KMSDRM/context/native640 diagnostic with controlled clear/blit/known fragment-work increments; compare elapsed queries and actual swap/worker CPU. Separately bounded swap0/1 A/B with set result + actual mode; preserve normal play vsync1. | Calibrated query scales with added shader work. Swap0 removes wait without reducing GPU workload → present scheduling likely. Positive workload increases swap but query barely changes → coverage/driver behavior suspect. Swap0 still slow cannot alone name GPU bottleneck. |Proposed later runtime diagnostic slice through existing launcher boundary, TDD and DockerARM64 build required. No production vsync/driver policy change now.|
|3. Producer versus renderer-worker CPU | Measure per-thread monotonic utime/stime deltas during identical window; correlate queue waits/wakeups with actual SDL-return timeline. Enable hardware PMU/perf only if actual kernel/permissions support it. | Producer CPU and completion tail fall together after hotspot fix → useful CPU win. Worker CPU saturated with producer blocked → focus translation/driver submission. Long wall wait with both CPUs idle → synchronization/I/O/GPU/present needs next discriminator. |Current producer10ms CPU PC/LR sampler exists. Saved monitor has process stat + lifetime `ps -L %CPU`, not warmed per-TID deltas. Minimal monitor enhancement needed for worker attribution.|
|4. Resolution/work dependency | After query calibration, paired uncapped diagnostic at320/480/640 internal where supported, same640 output and same pose/draws; keep correctness and game-time speed checks. Add render-target area/pass/clear/blit counters before choosing work reduction. | Repeatable pixel-work scaling with stable CPU suggests fill/bandwidth path. Resolution-independent RT/pass cost suggests resolves/sync/fixed work. Capped samples reject uncapped slope estimate. |Current supported scene resolutions320/640; intermediate requires approved mapping/new diagnostic, not assume. Existing CPU/draw/buffer counters insufficient for render-target traffic.|
|5. Upload/resource/IO stalls | Correlate CPU wall/CPU-time gaps with ordered command type, copied bytes, driver execution duration, allocation/delete and host reads; distinguish prewarm/new-level events. | High CPU draw-wall but small thread CPU with matching queue/resource operation → blocking dependency. Disk bytes/wait spikes on hitch → asset/IO path. High GPU work on upload → bandwidth/format path. |Aggregate queue counters and bytes exist; they include startup. Narrow timestamped worker operation/IO delta instrumentation proposed; avoid logging every call to disk in hot path.|
|6. App caches versus driver cache | Fresh isolated session with both app caches absent; warm app-key cache only; warm compiled-program cache; repeat same-driver launch. Do not clear global OS/driver cache. | New program creation/source compilation aligns with stalls; warm removes them → first-use cache problem. Warm47restores/0misses plus unchanged stall rejects shader compilation as that warmed-window cause. |Existing isolated seed/import workflow; filename `sh3-gl-cache.bin` is app-owned stored GL program binaries, separate from opaque driver-internal cache. Globally cold driver test needs bounded separate protocol, never claim from deleting app file alone.|
|7. Memory/audio | Track RSS/PSS/HWM, MemAvailable/swap/major faults, per-thread allocations/IO at outliers; listen separately during representative combat/streaming. Compare sustained first/last windows and openAL/ALSA errors. | Rising retained memory/paging correlates with tails → memory pressure/leak candidate. Flat RSS does not rule GPU allocations/bandwidth. Logged recovery requires audio follow-up even if FPS passes. |Current5s memory/process fields and audio logs exist; no process PSS/per-thread fault deltas/full GPU memory. Exact-binary15min320 evidence exists, true640 long route still pending.|
|8. Heat/sustained play | After useful candidate passes fixed pose and movement/combat, matched15min warm/hot true640 route, identical power/governors/ambient/start conditions; log thermal transitions and CPU/GPU/DMC clocks. | Early gain disappears when clocks fall → sustained thermal limit under those conditions. Full clocks plus failure rejects simple downclock explanation, not bandwidth/efficiency problems. |Existing sustained route and5s clock sampling reusable. No overclock, thermal-limit bypass or firmware change.|
|9. Acceptance breadth | Matched original park firing, room210→211 doorway/enemies, hospital160, church240, mall149/walkway217, fog/flashlight/transparency/UI/inventory/map/cutscene/audio and ordinary persistent-player launch. | Report averages, p95/p99/max, all complete1s/5s minima and consecutive dips; separately retain transitions/cache-cold visits. Stable clock, visual correctness and accepted drop duration required. |Existing routes/checkpoints are scoped evidence; exact640 coverage and owner duration clarification still needed. Room labels remain observed IDs when mapping uncertain.|

[CPU implementation and sampling bounds](cpu_runtime.md), [GPU/presentation analysis](gpu_renderer.md), [prior measurement acceptance](../Silent%20Hill%203%20optimization%20roadmap/measurement_acceptance.md), [actual routes and failures](../Silent%20Hill%203%20optimization%20roadmap/unattended_routes.md), [saved workflow](../../scripts/README.md).

Use paired randomized/ABBA comparisons after first discriminating probe: same immutable seed and event/camera window; alternate order, retain all runs, compare scatter before claiming gain. Predeclare windows/metrics; do not move window to hide startup or hitch. Separate a fixed-pose isolation result from gameplay result and cold-cache result. A single off/on/off triplet is diagnostic evidence, not repeated optimization acceptance.

### Inferences

Current-pair producer samples stay below32768 cap:6408649 records/1drop,32011044/6drops,10ms producer-CPU interval, writer-success flags. Warmed75–180s has7034/9052 samples; no renderer-worker stacks. Prior15min sampler saturation makes late PCs unavailable, while per-frame timing and monitor keep running. PC+LR are sparse leaf/caller observations, not inclusive flamegraph. See exact ELF/debuglink verification and rankings in CPU notes; do not reuse old42ms/13FPS evidence for this binary.

Startup-inclusive queue totals are not warmed attribution:640 has51 texture generations/444.923ms total wait,61 `glTexImage2D`/46.916ms,1410 uniform lookups/38.682ms; corresponding320 counts match. Existing aggregate counters lack event timestamps. Query only matching warm region and operation-time evidence before changing allocation or uniform work.

Current full-run coarse GPU-load observations average46.14 versus25.46 (36/37 samples; driver sysfs integer load), but include startup and lack independent counter calibration. They do not prove fragment occupancy or GPU idle time. `ps -L %CPU` is lifetime average, not5s per-thread utilization. Existing monitor has wall/uptime but no per-frame/monitor shared exact monotonic anchor. Avoid subtracting these sampled values from frame budget.

### Gaps

Lowest acceptable dip duration and how to treat rare first-visit transition pauses remain owner decisions. Until specified, present full distribution and classify observed25/20/15FPS durations; do not invent hard p99 or allowed-stall threshold. No fixed optimization gain budget is allocated to unmeasured hypotheses.

## What is exact lowest-supported graphics configuration?

### Takeaway

Verified measured configuration exists; complete lowest-supported preset does not yet exist. Establish setting semantics and independent pixels before calling lower numeric option lower quality or counting removed essential effects as successful optimization.

### Cited Findings

| Control | Verified current mapping | Supported conclusion / remaining check |
| --- | --- | --- |
|Output |`size=640x480`, launcher output640×480|Panel/output always640×480; output alone is not true640 render acceptance.|
|Internal resolution |`resolution=640x480` versus`320x240`|Actual framebuffer/internal-size observations establish current pair.320 is fallback profile, separate target.|
|Framebuffer format |`format=D3DFMT_A8R8G8B8` in matched sessions|Renderer advertises other formats including R5G6B5; that does not establish approved lower preset or correct precision/alpha semantics.|
|Shadow |`shadow=1`; guest flag VA`006942AC`, setter/getter path`005EF950`; functions`00685C10`,`00685CB0`,`00685D30`,`00685DA0` early-return when1|Certain shadow paths skipped under1; full UI label/coverage and other shadow passes not independently mapped. Do not infer all shadows off or universal quality order.|
|Lens-flare depth test |`lensflare_ztest=1`; VA`00691250`, function`0049FAC0` early-return when1|Specific path skipped, not proof all lens flare removed. Verify UI setting and image behavior.|
|Brightness |`gamma_b=1`,`gamma_g=1`,`gamma_r=1`|Preserved; no darkness/fog shortcut credited.|
|Fog /flashlight /alpha /post effects /texture quality /AA /frame skip |No complete approved lowest-setting mapping found|Preserve story-critical visibility, fog, core light, transparency, correct depth/reflections/fades, readable UI/map/text, simulation/audio. Survey guest/UI semantics separately.|

[GPU audit](gpu_renderer.md), [current report configuration](../../reports/issue-13-performance.md), [native rendering prerequisite](../../reports/issue-06-scenes.md). Existing measured1/1 is operationally reproducible, not comprehensive quality-floor proof.

### Inferences

Next settings survey should use isolated copies and one option change per known scene, record exact guest control/branch/UI label, compare reference/native pixels including flashlight/fog/alpha/UI, then measure. If existing setting has unsafe visual loss, reject it even when FPS improves. Renderer architecture work can reduce redundant work while keeping these semantics; measure pass/dependency cost first.

### Gaps

No evidence yet that another supported format or missing quality switch saves required≈9.78ms. Do not promise target from unverified “lowest” setting.

## What current external examples are applicable?

### Takeaway

Comparable successful ports support measurement-driven reduction of hidden render-target/resource costs and repeatable launcher/state handling. Their FPS gains are not SH3 forecasts. Different FNA/Java/C++ runtimes, SoCs, ABIs and drivers require local tests.

### Cited Findings

Current official PortMaster FNA guide gives first-hand Blossom Tales case: oversized targets, redundant final target, batching and audio-memory changes investigated separately. It reports large improvement after game-specific work. Relevant SH3 question is actual target sizes, passes, clear/blit/resolve traffic and idle waits. Its per-bind flush description is engine/example guidance, not proof every SH3 framebuffer bind causes physical flush. Do not transfer FNA/Mono fast-math or content patch to native compatibility runtime. [Official FNA performance guide](https://portmaster.games/contribute/porting/engines/fna/#performance-on-a-handheld-gpu), accessed2026-11-15.

Official launcher templates still use control discovery, `get_controls`, platform helper and finish cleanup, matching reusable saved workflow. Current installed helper hashes, not website alone, determine what actual run executes. [Official script templates](https://portmaster.games/contribute/porting/script-templates/).

Pinned current upstream refs checked2026-11-15: [sh3-nx ff483a6](https://github.com/cutarev/sh3-nx/tree/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98), [sh2-nx 7e69609](https://github.com/cutarev/sh2-nx/tree/7e69609f3a063fbe24c41d6aa560f14ede578746), [Cuphead1b7e7b0](https://github.com/wild1walker/portmaster-cuphead/tree/1b7e7b019dabeb4226a1b4be5bfdd854895242f5), [Delver port1ed02aa](https://github.com/ktodorow/delverengine-mp/tree/1ed02aa970d062fdc524d0d4aac52e34fe2e4e2b). Consult full applicability/pinned files in [working-port patterns](../Silent%20Hill%203%20R36S%20feasibility/working_port_patterns.md), [CPU notes](cpu_runtime.md) and [GPU notes](gpu_renderer.md). Cuphead resolution scaling for RK3326 establishes a fallback technique; it does not meet true640 SH3 criterion. Delver's runtime/content pipeline differs and does not establish SH3 throughput.

First-hand upstream [sh3-nx issue1](https://github.com/cutarev/sh3-nx/issues/1) traces transparent hair cards to palette-alpha handling and confirms fix. Current renderer already includes this class of correctness work; preserve alpha tests rather than remove transparency. This is a regression reference, not newly discovered speed fix.

### Inferences

PortMaster guidance makes hidden fixed presentation/pass/resource costs credible hypotheses. Current real swap-versus-producer evidence and fresh timer coverage check decide which deserves implementation. No external example can substitute for matched actual-device experiment.

### Gaps

Searches2026-11-15: `site:portmaster.games FNA performance render targets stutter`; `site:github.com/cutarev/sh3-nx stutter shader performance`; `site:github.com PortMaster RK3326 profiler CPU GPU Mali`. No primary-source, matched SH3/R36S true640 stable30 fix found. This no-match is search scope, not impossibility proof. CCE current-file searches repeatedly returned stale `.port-cache/sh3-source-*` copies; requested source expansion for scene manifest failed. Exact known current paths inspected after documenting retrieval limit; no stale chunk treated as current implementation. No reference clones downloaded or external scripts executed.

## Fresh current-binary query experiment and next controlled measurement

### Takeaway

First off run found lower automatic power policy after reboot. Already-active on run retained; **third control canceled** after discovering policy mismatch. Every run uses same original immutable640 session from `20261114T055246314042Z-4068d8/launcher/session`; no seed chaining and no persistent player-state mutation. Both use same2ac6 binary. No governor writes, new executable build or further device runs.

### Cited Findings

Fresh helper review: `20261115T105850400561Z-de8c0e`. First off run: `20261115T110310292115Z-0bbfb4`, all host phases0, source preserved, service/launcher ExitProcess0, frontend evidence case PASS.55–95s:707 completions,17.679613FPS; interval mean56.569779ms, p50/p95/p99/max57.657/63.526/64.719/70.949ms; minimum complete1s15FPS/5s16.2FPS. All11 PEEK observations live room210, same one position; true640×480.45 binary restores, zero misses/writes/rejections. No query-enabled message or GPU CSV, as requested.

Current off run monitor begins before runtime: CPU governor `ondemand`, GPU `simple_ondemand`, DMC `dmc_ondemand`.20 samples: CPU1008–1512MHz, mostly1200–1296; GPU400MHz18samples/480MHz2samples; DMC528MHz throughout; maximum59.545°C. Earlier current pair had performance governors and1512/520/786MHz throughout. Boot identity differs; first monitor uptime54,730s old640 versus2,232s new. No exact boot IDs published. New lower FPS is not current-binary regression or valid direct comparison against older route; pose and power policy both differ.

Full source review: current `ports/Silent Hill 3 Game.sh`, `game-session.sh`, `restore-frontend.sh`, `Silent Hill 3 Performance.sh`, fresh control/device-info/functions/ArkOS module contain no governor writes. Performance menu selects FPS/resolution only; monitor is read-only. Current saved frontend inventory records systemd service state, but not ExecStart/ExecStop/unit content or available stock governor/frequency lists. Pre-runtime monitor already sees lower policy; previous pre-runtime monitor already saw performance policy. Evidence is consistent with previously inherited global policy resetting at reboot; exact firmware owner not yet established.

On run `20261115T111023699412Z-f0d458` was already active when policy mismatch identified. It completed with all host phases0, source preserved, service/launcher ExitProcess0 and frontend evidence case PASS. Exact five seed hashes match off run; output settings preserve A8R8G8B8/shadow1/lensflare_ztest1/gamma1 and true640 internal/output. Both have11/11 live observations at identical coordinates, health100; camera matrices are not directly sampled. Both restore45 binaries, zero misses/writes/rejections. No screenshot captures. Measured game-clock/wall ratio from PEEK endpoints≈1.001153 off and1.000105 on; timer/wall≈1.000186/1.000119. Stationary scene is isolation workload, not movement/combat acceptance.

|55–95s raw metric |Queries off|Queries on|
| --- | ---: | ---: |
|Run ID|`20261115T110310292115Z-0bbfb4`|`20261115T111023699412Z-f0d458`|
|Actual completions /FPS|707 /17.679613|714 /17.858485|
|Completion interval mean /p50 /p95 /p99 /max,ms|56.569779 /57.657 /63.526 /64.719 /70.949|55.999825 /56.1045 /58.750 /61.910 /66.258|
|Minimum complete1s /5s FPS|15 /16.2|16 /17.4|
|Producer CPU mean /p50 /p95,ms|30.326890 /30.212291 /31.767167|30.395080 /30.336396 /31.701250|
|Producer draw mean /p50 /p95,ms|3.611864 /3.550 /3.914|3.540487 /3.5205 /3.790|
|Producer Present mean /p50 /p95,ms|25.087362 /26.178 /32.229|25.129546 /25.2535 /28.161|
|Worker SDL swap mean /p50 /p95,ms|44.320795 /45.476 /51.023|41.965497 /42.1185 /44.602|
|Draws/frame mean /buffer bytes/frame|370.400 /140124|373.402 /140124|
|GPU elapsed samples, selected CSV elapsed window|None requested|715|
|GPU elapsed mean /p50 /p95 /p99 /max,ms|Not measured|1.025450 /1.027390 /1.089284 /1.131431 /1.218826|

On stdout reports `gpu_profile=enabled counter_bits=64 queries=8 delayed_frames=3`, then `gpu_profile=stopped skipped=0 disjoint_discarded=1`. Whole run has2193 GPU rows,2194 completion rows. GPU CSV `elapsed_ms` is saved worker query-end timestamp immediately after `glEndQuery`, before SDL swap; delayed polling writes saved timestamp, not retrieval time. Query and completion CSV windows therefore retain different row populations;715 GPU rows are not asserted to be exact same714 completion frames. Frame-ID join below permits exact correlation. No missing query row is treated as zero. Query-on monitor: CPU1008–1512MHz, GPU400MHz21/21 samples, DMC528MHz21/21, governors remain automatic, maximum62.5°C. Off GPU briefly480MHz while on stays400; CPU samples also vary. **No observer-overhead estimate or query performance-win claim** from this pair. [Query timestamp source](../../src/d3d8/profile_gpu.c).

On stderr contains one ALSA underrun during initialization before program-cache prewarm/load; no listening verdict. Whole-run disjoint discard is explicit; no assumption about which exact phase caused it without event timestamp. Off has no query-enabled message/GPU CSV. Full raw provenance for both runs: `status.json`, `scene-identity.json`, `launcher/stdout.txt`, `launcher/stderr.txt`, `launcher/frame-times.csv`, `launcher/frame-times.csv.presents.csv`, on-only `launcher/frame-times.csv.gpu.csv`, `service/performance.txt`, `service/frontend-game.txt`, `service/frontend-restored.txt`. Derived local analysis `.port-cache/issue-13-limits/current-query-analysis.json` preserves selected statistics; original data remain unchanged. Saved commands and55–95s interval documented in [scripts README](../../scripts/README.md).

### Inferences

New evidence exposes launch reproducibility gap: benchmark environment previously inherited performance policy, whereas current public menu does not own that policy. Approximately1ms query alongside≈42ms swap reproduces incomplete attribution on exact current binary. It does not prove GPU idle/headroom, and automatic clocks prevent estimating causal query overhead. No hardware-ceiling conclusion.

Concrete next experiment, proposed work through existing launcher→game→frontend boundary:

1. Extend saved read-only inventory/monitor to capture installed frontend unit/ExecStart/ExecStop and invoked policy helpers, CPU/GPU/DMC available governors/frequencies/current bounds and before-stop/after-stop/after-start values. Inspect helpers before running. Identify firmware policy owner and confirm reviewed stock operating bounds; current probe lacks these capabilities.
2. Only then add opt-in session-scoped stock-performance selection through saved plan/service. Record original policies before changing anything; leave min/max frequencies, voltage, DTB, thermal controls and permanent configuration unchanged. Fail before game on unsupported policy/readback error; roll back partial changes. Recovery trap and existing privileged ExecStopPost restore recorded policies after normal exit, startup failure, timeout and termination, with final readback plus frontend return. Observed RED/GREEN/refactor through existing launcher boundary must verify normal restoration, partial-failure rollback, termination recovery and absent-option preservation. Fixture passes cannot certify hardware restoration.
3. Reuse unchanged2ac6 binary and same immutable fixed-pose seed/settings. First compare default policy versus confirmed stock-performance under paired randomized/ABBA100s runs,55–95s, query-off. Log actual frequencies, not just requested governor. Attribute combined policy effect only; single-domain CPU/GPU/DMC comparisons follow only when needed, with same restore guarantees. Then repeat query off/on/off at matched stable policy; validate query coverage with positive GPU-workload/presentation control before optimizing a purported GPU bottleneck.

Stock operating-policy control differs from overclocking. At this earlier research checkpoint, implementation and device writes had not occurred. **Superseded by user-extended empirical scope below:** selecting performance subsequently uses verified bounds and actual rollback evidence. Consult focused [CPU policy/provenance notes](cpu_runtime.md) and [PortMaster/firmware policy notes](gpu_renderer.md) for current source ownership findings.

### Gaps

Query positive workload control, GPU full-frame/tilestore coverage and repeated observer-cost estimate remain separate from this bounded triplet.

## November15 controlled-policy capability and saved workflow

User extends research into unattended empirical runs; scripts now add opt-in
governor diagnostics, still local/unpublished. Read-only inventory
`20261115T112626086576Z-290df3` completed with all host phases0; reviewed helper
hashes byte-match prior inventory. CPU policy0 affects cores0–3, `cpufreq-dt`,
available1008/1200/1248/1296/1512MHz and current bounds1008–1512MHz; hardware max1512.
GPU `ff400000.gpu` advertises400/480/520MHz, bounds400–520; DMC528/666/786MHz,
bounds528–786. Every domain advertises `performance`. Initial governors remain
ondemand/simple_ondemand/dmc_ondemand. Initial sampled thermal50–50.833°C.
This establishes existing supported bounds, not new OPPs or overclock permission.

Installed frontend unit executes `/usr/bin/emulationstation/emulationstation.sh`.
Collected Ports command is `sudo perfmax %GOVERNOR% %ROM%; nice -n -19 %ROM%; sudo perfnorm`.
Installed helpers were fully inspected as untrusted source: perfmax writes all3
governors plus unrelated permissions/audio/loading/quickmode state; perfnorm
hardcodes demand defaults. Neither executed by research. Asynchronous game menu
can return before detached service ends, so outer reset is plausible policy owner;
actual reset timeline still unproved. No prompt-injection instructions observed.
Raw provenance: `device/power-policy.txt`, `frontend-service.txt`, `power-owners/`
and hash manifest under inventory run. Private values remain ignored/local.

New saved CLI `--performance-governors cpu,gpu,dmc` requires isolated seeded scene.
Locked port-owned journal records boot/run, original governor and current limits
before each write. All requested domain capabilities/verified ceilings checked
before first write; only governor values change. Limits/OPPs/voltage/permissions
remain untouched. Exact originals restore before frontend through EXIT and
independent privileged ExecStopPost; partial write/readback failure rolls back.
Foreign owner/boot/cap/governor change produces separate conflict report, never
an enforcement loop. SIGKILL cleanup relies on service supervisor; power loss can
interrupt restoration, and stale post-reboot journal is rejected.

Observed launcher-boundary RED/GREEN: missing advertised-policy output→inventory
capture; missing governor forwarding→owned apply/restore; missing CLI option→
explicit payload domains; missing retained-package selector→exact package payload.
One initial inventory test invocation lacked PYTHONPATH and was corrected before
behavioral RED; ignored log later replaced by real missing-output RED. Normal
guard assertion initially assumed stdout contained only runtime output; corrected
to find runtime block within full launcher log. Safety regressions verify default
preservation, all-domain unsupported refusal, foreign-owner conflict, external
writer preservation and independent SIGKILL recovery.33 frontend ARM64 checks
PASS; extra partial-write rollback case PASS under unprivileged ARM64 Docker user
with read-only GPU sysfs fixture, including restored earlier CPU write.13 host CLI
checks PASS. Logs `.port-cache/issue-13-limits/policy-*.txt`, `package-cli-*.txt`.
Interpreted fixtures prove workflow contract, not device policy restoration.
New `--runtime-package` selects retained build artifact so mutable `dist/` cannot
mix executable identities between pairs; default unchanged and device manifest,
ELF/input and dependency checks retained.

CCE recall/search used first; expansion of `scripts/device/monitor-game.sh:1`
failed `Chunk not found`, and results mixed current headers with ignored historic
cache/dumps. Known current saved-workflow paths then inspected directly. Focused
new-blocker searches repeated official PortMaster/firmware/comparable Cuphead
sources, including [official packaging](https://github.com/christianhaitian/PortMaster/blob/main/docs/packaging.md),
[dArkOS](https://github.com/christianhaitian/dArkOS), [first-hand Cuphead release](https://github.com/wild1walker/portmaster-cuphead/releases).
Cuphead muOS/H700 powersave setup issue supports clock capture, not R36S policy
equivalence or periodic forcing. No downloaded external scripts executed.

## November15 same-binary stock-policy measurements

User requests empirical limits without physical input; automatic map movement and
multiple public-save levels remain required next work. First fixed-pose pair
isolates power policy before moving runs. Frozen worker-attribution package
`.port-cache/builds/20261115T112806405240Z/artifacts/runtime`, SHA256
`787ca300fd6bf8d23e8cc6579cfc9d0228fc10c6c37b89336416c0fb012894c7`,
BuildID `ee0aa4efafae3a3f55e68c4d84dc6ea7161808c3`, adds opt-in profiled
worker/swap CPU clocks. Native real-checkpoint RED/GREEN and refactor regreen pass;
normal profiling-off path avoids added CPU-clock reads. Both runs use same frozen
package, `profile-gpu-off-640`, exact immutable five-file seed from
`20261114T055246314042Z-4068d8/launcher/session`, true640 internal/output,
30FPS limiter, no screenshots or GPU elapsed queries, room210, health100 and
identical sampled player pose. These are stationary attribution intervals,
**not movement acceptance**. No speed gain is attributed to changing binaries.

|55–95s metric|Default policy|Stock performance CPU/GPU/DMC|
|---|---:|---:|
|Run ID|`20261115T113712423917Z-c04191`|`20261115T114326258503Z-d74edc`|
|Completed presentations /endpoint FPS|678 /16.935160|857 /21.436980|
|Minimum complete1s /5s FPS|15 /15.8|19 /20.0|
|Completion interval mean /p50,ms|59.0526 /59.904|46.6498 /46.121|
|Completion p95 /p99 /max,ms|65.012 /66.331 /70.467|50.968 /54.154 /58.747|
|Producer CPU mean /p50,ms|30.4617 /30.4354|28.3171 /28.2733|
|Producer draw mean /p50,ms|3.5835 /3.5610|3.3480 /3.3380|
|Producer Present mean /p50,ms|28.1443 /28.6980|18.1280 /17.6390|
|Worker CPU mean /p50,ms|12.8268 /12.7776|11.2242 /11.1536|
|Worker SDL swap wall mean /p50,ms|45.9608 /46.8505|35.1951 /35.0370|
|Worker SDL swap CPU mean /p50,ms|0.6125 /0.6122|0.4428 /0.4331|

Default monitor: CPU1008–1512MHz (1200 most common); GPU400MHz19/21,
480MHz2/21; DMC528MHz21/21. Stock-performance run: all22 sampled CPU/GPU/DMC
values1512/520/786MHz and all governors performance; no sampled frequency fall.
Stock monitor temperatures peak CPU70°C/GPU68.846°C; earlier inventory reads
CPU73.333°C/GPU69.615°C, so monitor peak is not whole-run maximum. Default
monitor peak CPU59.090°C/GPU59.545°C. Temperature and sequential ordering remain
pair limitations, and observations are not an ABBA thermal study.

Every host stage, launcher and service status0; source-preserved true, all five
seed hashes and59 firmware-library hashes verify. Frontend restored active.
Stock run `service/power-applied.json` records original
ondemand/simple_ondemand/dmc_ondemand governors and unchanged bounds;
`power-restore.json` status restored/errors[] means exact original governor
readback succeeded before frontend restart. All min/max values match initial
inventory; no frequency cap/OPP was changed.45 program binaries restore with zero
misses. Raw files remain under each ignored run, including profiles, scene/source
identities, monitor and restoration records; `performance-summary.json` records
55–95s derivation through saved `scripts/host/performance.py`.

Inference: combined supported stock policy raises throughput26.58%, but640
still fails25FPS floor and30FPS goal in this scene. Worker swap consumes35.20ms
wall versus0.44ms CPU under full policy; downstream graphics/presentation wait
still dominates completion. CPU time alone is not frame critical path. Cannot
yet distinguish shader/tile processing, bandwidth, synchronization and display
back-pressure. GPU-specific frequency contrast is next; counter access and
explicit swap interval pairs follow before causal label or hardware ceiling.

### GPU-only governor contrast

Run `20261115T114935059499Z-3b9030` reuses exact787ca300 package, seed, fixed
query-off640 scene and55–95s window, changing selected governor subset to
CPU+DMC. Actual21 samples hold CPU1512/DMC786MHz; GPU governor remains
simple_ondemand,400MHz20/21 samples and480MHz1/21.711 completions,
17.753550FPS, minimum complete1s/5s16/16.8; p95/p99/max60.478/62.322/65.755ms.
Producer CPU mean28.0525ms, worker CPU11.0915ms; worker swap wall45.0274ms
versus CPU0.4274ms. Compare full policy21.436980FPS/swap35.1951ms: selecting
GPU performance alone gives20.75% higher throughput under these held CPU/DMC
settings, with essentially unchanged producer/worker CPU work. This establishes
GPU-frequency-sensitive downstream wait, not yet shader-versus-bandwidth or
presentation attribution. Automatic GPU frequency is sampled, not perfectly fixed.

Execution0, launcher/service collections0, source-preserved true, both launcher
and service exits0, frontend active. Exact CPU/DMC originals restore with errors[];
unselected GPU policy is unchanged. **Outer device collection timed out124**;
profiles and restoration records are complete, but firmware-after record and final
outer exit-status file are missing/truncated. Collection failure remains explicit;
saved retry will recover evidence without replaying scene. No claim that all
firmware checks passed for this run until recovered. Native runtime hash already
collected and matches frozen787ca300. This failure is transfer, not game failure.

### Runtime identity metadata correction

GPU contrast `3b9030` host scene identity incorrectly labels runtime485f250 because
old `scene_identity()` inspected mutable `dist/` instead of explicit retained
package. Raw file is preserved. Actual collected `device/runtime.sha256` proves
787ca300, matching default/full-policy fixed pair and deployed retained package.
This is metadata error, not mixed measured executable. Selected-package host
fixture now uses different retained/dist bytes, observes hash mismatch RED, then
asserts both deployment payload and scene identity equal selected artifact GREEN.
Fresh source records corrected behavior; earlier raw metadata is never rewritten.

### Hardware-counter capability actually passes

Saved inventory `20261115T115644217332Z-7217f4` has all host stages0. Official
unchanged Arm example d24032c7be930f784af9942998da5b5cd7fa9ea7b53844628c6091edb1251ad9
verifies and exits0, with ten complete sample rows, Bifrost family, one reported
shader core,128-bit reported bus and complete supported-counter descriptions.
`device/gpu-counter/{stdout.txt,stderr.txt,capability.json,inventory.txt}` retain
full output; stderr empty. This counts advertised shader cores, not marketing
execution-engine count. `/dev/mali0` mode660/root:video already readable/writable
through existing video/render group memberships. No permission writes or elevated probe needed.
Debugfs denied and kernel config unreadable, explicitly recorded, without blocking
supported ioctl reader. Frontend active during capability test: **frontend
baseline, not GPU idle or game utilization**. Hardware activity attribution needs
subsequent timed samples beside real game. Helper requires all ten complete rows
and metadata; native exit0 alone does not pass capability.

### Final diagnostic binary: moving640 swap1 control

Frozen final worker/swap-override diagnostic package
`.port-cache/builds/20261115T114001775304Z/artifacts/runtime`, SHA256
`485f25039e3e190c501610cf02a4245e1acd948997cd811f7c5faa596d691eeb`,
BuildID `32bba08410dbacf57c4fb77930e663e171b424bd`. Original immutable On seed,
`performance-swap1-640`,180s/full stock1512/520/786MHz,30FPS limiter, no frame
captures/counters. Run `20261115T120025683855Z-5dd767` execution0; launcher/service
collections0 and both exits0; original outer collection124 retained. Saved
collection-only retry `20261115T120815248161Z-a63fad` completes0 without replay,
and recovers actual device485f250 hash, outer exit0,59 firmware checks and all
five immutable seed checks. Original raw failure is not overwritten; retry raw
metadata is under retry `device/`. Current collection-only retry uses longer
300s deadline, not metadata-only fetch.

75–180s has2463 completions/23.450750FPS; minimum complete1s/5s18/20;
p95/p99/max50.503/53.268/74.812ms. Producer CPU mean28.9482ms, draw3.3904ms;
worker CPU11.2558ms, SDL swap wall30.6293ms versus CPU0.4489ms. Native log
`gl_swap_interval requested=1 result=0 effective=1` proves actual requested
interval accepted.41 room210 PEEK observations, all health100,40 distinct
positions. Ammunition loaded6→2→reload10 with reserve30→20 confirms repeated
actual firing/reload beyond scheduled inputs. Automatic route therefore exercises
live motion and combat, not menu or stationary-only coverage. Exact three original
governors restored/errors[] and frontend active; no caps changed. This moving
result still fails25FPS floor/30FPS goal; no full-campaign or listening claim.

Current supported graphics semantics independently confirmed by native cold UI:
1/1 equals Lensflare Low/Real-Time Shadow No, while baseline Noise Effect remains
On and Display Mode Normal. Noise Off via normal exposed UI is next single-variable
comparison; original On checkpoint remains immutable. No unsupported byte patch
or renderer change is inferred from numeric setting names.

### Recovered GPU contrast metadata; original transfer failure preserved

Collection-only retry `20261115T121111765093Z-46ccaf` recovered original
`20261115T114935059499Z-3b9030` outer directory with collection0 and no new
execution/deployment. Retained `device/runtime.sha256` proves787ca300,
`device/execution-status.txt` is0, all59 firmware checks areOK. Original service
restoration shows errors[] and frontend active. This completes metadata gap in
GPU-frequency contrast above; original host collection124 remains untouched.
Shared scene identity now accepts selected immutable executable directly; extra
CLI RED test removes mutable `dist/runtime/sh3` entirely, reproduces missing-file
dependency, then GREEN and full host24-test regreen pass. Earlier raw erratum
remains documented rather than rewritten.

### Supported Noise Off: matched moving640 empirical gain

`20261115T121637292450Z-d498a8`, all host phases0, five source files preserved,
actual native485f250, service/launcher/outer exits0, exact three governors
restored/errors[],59 firmware checksOK, frontend active. Same180s moving/combat
route, stock1512/520/786MHz, swap1 accepted, true640/internal+output,30FPS limiter,
no captures or counters. Only settings data.sys changes from preceding immutable
On control; data.001, disp.ini and both retained caches match. Noise Off/Display
Normal seed came from ordinary exposed UI edit/apply and independent cold reload
(`.port-cache/graphics-map-20261115/verifynoise-1.png`), data.sys
`05913dcaec295588f206338deafc80efed9209dec892e4e3e7af436f27105640`.
No unsupported renderer/guest patch used. Existing run lacks direct loaded-option
PEEK words, so next runs add aligned read-only observations for loaded Noise/Display
and shadow/flare flags; seed UI proof and exact delta are retained independently.

|Matched moving room210,75–180s|Noise On/Normal5dd767|Noise Off/Normald498a8|
|---|---:|---:|
|Completions / spanFPS|2463 /23.45075|2716 /25.86971|
|Minimum complete1s /5sFPS|18 /20|21 /22.6|
|Producer CPU mean ms|28.9482|28.3502|
|Worker CPU mean ms|11.2558|10.6267|
|SDL swap wall /nested CPU mean ms|30.6293 /.4489|27.3517 /.4541|

Off gains10.315% FPS, but mean38.656ms remains5.323ms over33.333ms budget;
minimum1s/5s still fails25FPS floor. Local saved `performance-summary.json` uses
existing `scripts/host/performance.py --start75 --end180` method (actual invocation
uses separated option arguments). Floor-index p95/p99/max45.879/47.622/68.295ms;
independent interpolated percentiles differ slightly by method.45/45 live PEEK
observations,44 distinct positions, health100, movement in every30s subwindow;
ammunition reaches0 then reload10 and reserve30→20, establishing actual combat.
All36 coarse frequency samples hold1512/520/786; maximum sampled thermal72.083°C.
No audio-listening or campaign-wide acceptance inferred.

### Lean evidence collection and targeted counter capability

Repeated outer SCP directory timeouts retained before changing workflow. Saved
`archive-evidence.sh` now snapshots completed outer/launcher/service evidence after
checks, preserving originals, excluding only redundant `payload/runtime/sh3`.
Native SHA/ABI/package metadata and frozen original package stay available. Tar
does not dereference links. Host validates every member path/type before any
extraction; rejects absolute/traversal paths and special files; copies regular
files/directories into fresh destinations, skips all symbolic/hard links and
records targets/modes in `*-archive-manifest.json`. Raw archives retained.
TDD: saved snapshot missing-script RED→ARM64 GREEN→regreen; host good archive
and invalid traversal/absolute/FIFO RED→GREEN,23-test host regression and focused
regreen PASS. Subsequent shared identity/option-observation slices full24PASS.
Logs under `.port-cache/issue-13-limits/archive-{device,host}-*.txt`.
Legacy `--retry-collection` remains300s directory-only fallback for earlier runs,
not sidecar trees. No raw original failures/status overwritten.

Actual targeted inventory `20261115T122612842321Z-a34300`: all phases0, new archive
collection/extraction0; exact reviewed targeted native
`e230c8a7e853e293e4baf4f971c1f6adce198e211e81df953307f57fa9c2fe6d` verifies,
exits0 with strict ten legacy sample rows plus ten TARGETED_SAMPLE JSON records
and TARGETED_CONSTANTS. Full raw stdout/stderr, supported list, mode/driver
inventory and capability.json retained. Constants report one shader core, two
execution engines per core, oneL2 slice,128-bit bus. Actual driver interval bounds
and MONOTONIC/RAW anchors are recorded. Frontend active: capability/control only,
not idle or game-load claim. Active game counters still pending.

Aligned loaded-option observations added via CLI RED→GREEN→regreen, preserving
no-capture behavior:070E66CC high byte=Noise,070E66B0 high byte=Display,
0072D274 high byte=rendererNoise;00BCC1B8 bytes1/2=flare/shadow respectively.
These read existing public PEEK API; no memory writes. Next Sharp/NoiseOff moving
control uses same485/full stock/swap1 and verified ordinary UI seed9986bc30,
retaining explicit640/1/1 and original caches. Sharp is supported point-filter
look alternative; quality preference is not assumed.

Targeted inventory independent validation: ten contiguous intervals100.407–
100.829ms, aggregate1.005330084s; each driver end lies inside corresponding
CLOCK_MONOTONIC_RAW request window. All ten metrics finite; interval/cycle bounds
pass sanity. Individual API read requests0.157–0.463ms. Baseline available policy
reads400MHz automatic; no fixed-clock busy percentage claimed for frontend run.

Sidecar timing/lifecycle extension: opt-in counter game sessions schedule three
unchanged helper invocations at100/125/150s from wrapper MONOTONIC anchor and
record whole launcher before/after MONOTONIC+RAW clock bracket in service
`launcher-clock.json`. Initial SDL Unix-source RAW-epoch assumption was later
disproved by exact deployed ELF: actual SDL ticks/perf use gettimeofday. Existing
RAW/MONOTONIC bracket therefore cannot establish SDL warm-window envelopes or
per-frame association; those provisional claims are withdrawn. Use independent
whole-run off/on cadence and sampler's exact driver intervals/fixed-frequency
boundaries until new candidate's REALTIME bridge is recorded. No new
game binary or clocks added to ordinary path. Native ARM64 frontend test first
skipped because owner mount omitted; corrected setup then observed missing-clock
RED, minimal GREEN. Full relevant lifecycle/probe/session/archive regreen follows.

### Display Sharp contrast: no measured improvement

`20261115T122823159512Z-004cca`, counterOFF/swap1/full stock/final485; all host
phases0 including three new archive transfers, source preserved, exact governors
restored/errors[],frontend active,59 firmwareOK. SameNoiseOff route/true640, only
settings data.sys changes to independently UI-verified Sharp
`9986bc30e0c461f42e0541852303fef3e079554bff797724b8d5c5a745462793`. Added four
read-only option observation dwords; no added rendering/screenshot diagnostic.
75–180s:25.19583FPS,min complete1s/5s19/21.8,p95/p99/max47.577/50.412/71.034ms.
ProducerCPU28.4975,workerCPU10.7987,swapwall28.3958/nestedCPU.4528ms.44/44 live
observations,41 distinctpositions,health100; all44 loaded option words confirm
Noise0/Display1/rendererNoise0. Sharp therefore provides no speed gain over
Normal25.86971 in this sample; retain Normal for counter/swap/level campaign.
Do not claim Sharp is inherently faster or lower quality: it is supported point
filtering look alternative.

Important observation discrepancy: BCC1B8 bytes1/2 are0/0 during this actual run,
rather than expected1/1 from prior cold Options label mapping. Runtime source/UI
agent is checking whether these are reset UI menu-state bytes versus active
renderer controls. True640/disp1/1 retained; **lowest complete graphics profile
not certified from that file alone**. Preserve this raw finding pending resolution.

Sidecar lifecycle/clock regreen completed47tests,46PASS/1expected privileged
read-only-sysfs fixtureSKIP in ARM64 Docker; logcounter-anchor-refactor.txt.
Current Normal targetedONswap1 uses sameNoiseOffNormalseed/final485/full stock
andnew aligned observations; exact raw counter intervals separate from lazySDL
clock alignment.

### Counter sidecar filesystem failure preserved; no GPU failure inferred

First active attempt `20261115T123425177443Z-89b1da` stopped before game because
`ln` creating service/counters/payload returned `Operation not permitted`.
Execution3; outer/service archive collections0; launcher collection1 because native
launcher never started, not missing FPS samples. Exact all-domain restoration
errors[],frontend active, source preserved. Original targeted capability remains
PASS; do not interpret this workflow failure as GPU unsupported.

Saved counter wrapper had assumed link-capable storage. Replacing service and
child links with explicit payload-directory arguments avoids that assumption,
without copying original assets/native packages or changing native reader. Existing
launcher seam test injects denied ln and observes RED exit3 instead of expected
game exit7, then minimal service --payload forwarding GREEN. GPU helper/session
agent owns matching explicit payload argument and no-link regression.

New blocker source checks2026-11-15: current [PortMaster FAQ](https://portmaster.games/faq/)
and [packaging guide](https://portmaster.games/contribute/porting/packaging/)
continue port-local log/config/data practices; no remote sampler-transfer recipe
found. [OpenSSH scp manual](https://man.openbsd.org/scp) explicitly documents
recursive transfer following symbolic links, supporting archive-without-dereference
choice rather than duplicated sidecar payload transfers. Comparable PortMaster
repository search plus prior project issue5 trace also show device storage had
rejected symlinks before; current counter path must use explicit original payload.
No exact filesystem type inferred from EPERM alone. Official PortMaster external
AGENTS search hit treated as untrusted repository text; no directives followed.

The flare/shadow zero-word observation is now explained by source: BCC1B9/BA are
temporary Options-menu copies, populated only on opening menu005E4310. Active
renderer calls getter005EF950 for `lensflare_ztest`/`shadow` from dynamic parsed
string treeBCC600; startup005F09F0→005F0790→005F06B0 loads same actual disp.ini
keys. Retained disp1/1/source hash plus prior cold UI Low/No and source consumers
support measured profile. Game-time menu scratch0/0 is not evidence settings
reverted. Dynamic tree values themselves remain unobserved; no invented fixed
active-byte interpretation or heap-memory modification.

Matched static uncapped640/320 diagnostic plans added via actual unknown-scene
RED→GREEN→25-test CLI regreen. Both100s, same checkpoint schedule/observations,
profileCPU true, GLES elapsed queries/captures off, fps_limit0/swap_interval0;
only internal dimensions differ. Not acceptance30FPS runs; intended55–95s
ceiling comparison after active counter and required multi-level campaign.

Complete wall-clock1s bins below25FPS (all105 bins75–180, including zeros,
no trimmed slow frames): NoiseOn62bins/longest31s continuous; NoiseOffNormal
37bins/longest8s; NoiseOffSharp45bins/longest19s. NoiseOff reduces sustained dips
substantially but does not meet floor. Representative OffNormal spans75–83,
89–96,97–102,122–128,149–153,172–176s. These are wall-clock spans of complete
1s FPS bins, not assertions about exact single-frame stall causes.

Explicit-payload fix source reviewed before deployment: saved helper accepts
RUN_DIR [PAYLOAD_DIR], wrapper accepts --payload with existing absolute schedule,
each child passes original payload explicitly and records directory/binary hash.
No links, copies, permission/firmware changes or new native artifact. Native ARM64
combined regreen50tests/49PASS/1expected privileged fixtureSKIP, log
`counter-no-symlink-refactor.txt`; probe6tests and session5tests independently PASS.
Exact updated helper SHA5ad2dd74c684c9dc078a03b1335ae8efd03bae537e529b691d600e08d0b2956d;
wrapper SHA328a688ea83aa90cfff9682d67e5b8136f746039ad3dd17f0cd3c7062943689b.

Relevant primary [Knulli exFAT porting guide](https://github.com/knulli-cfw/knulli.org/blob/main/docs/guides/portmaster-and-exfat.md)
and firsthand [PortMaster bind-directories compatibility work](https://github.com/beniamino38/portmaster-bind-directories)
confirm symlink assumptions are known storage compatibility issue across ports;
our one-off sampler needs no directory bind at all. Exact local failure above,
not another firmware's success, determines required fix. Focused searches
`site:github.com/PortsMaster/PortMaster-New/issues symlink exfat Operation not permitted`
and `site:github.com/PortsMaster/PortMaster-GUI/issues symlink fat32` returned no
matching official issue; related primary guide/repo preserved here.

### Additional actual level: mall18, true640 moving pass in warm window

`20261115T123732242048Z-5f8010`, final485/full stock1512/520/786,30FPS limiter,
NoiseOff/DisplayNormal/disp1/1; actual loaded Noise/Display/rendererNoise all0 in
56/56 warm observations. Compatible public archive SHA5bf9878a05ec68fb6f09fd88d5db42762c12d9b22ee817936a5507acf948de21,
slot6 exact9952bytes, prior native mall warm cache retained; provenance/hash manifest
`.port-cache/issue-13-limits/multilevel-low-20261115T123000Z/manifest.json`.
No extra commercial assets downloaded. Seed immutable/source preserved. All host
phases0/outer+launcher+service exits0,actual485 deviceSHA,59firmwareOK,all3 exact
governors restored/errors[],frontend active.49 program binary restores,0 misses/
writes/rejections; this run verifies cache reuse rather than presuming it.

48–160s actual completion640x480:29.99991FPS, every complete1s and5s bin30,
p95/p99/max34.634/36.046/54.762ms; producerCPU13.7902,workerCPU7.8953,swapwall
10.1608/nestedCPU.4241ms.56/56 live room18 observations,47 positions,motion in
every sampled30s subwindow, health197.200012constant. No transition or weapon-use
claim inferred from route keys alone. All32 monitor samples1512/520/786,maximum
sampled thermal70.416°C. Warm resolution/floor criteria pass for this room/route;
not campaign-wide pass.

19 ALSA recover/underrun lines are separately bounded by surrounding PEEK
timestamps: one11.281–13.284s,ten23.282–25.282s,six25.282–27.283s,one29.282–
31.283s,one39.282–41.282s. All precede48–160s warm window; no logged warm
underrun. Loading/menu/startup audio remains limitation; no listening-based sound
continuity claim. FPS trace retains loading and slowframes; summary does not trim
render spikes. Existing raw stderr and performance-summary.json preserve bounds.

### Actual targeted counters beside moving640; observer qualification retained

`20261115T124320804106Z-652b71` counterON/swap1, NoiseOff/Normal, final485/full
stock, all host/launcher/service phases0, immutable seed preserved,actual485SHA,
59firmwareOK, all3exactgovernorsrestored/errors[],frontendactive. No-symlink
explicit payload flow works on actual storage; wrapper finished0 with all3 child
helpers native0/strictusable, each tencomplete rows, payloadverified. All six
start/end boundary reads1512/520/786 and coarse monitor retained.45 directloaded
Noise/Display/rendererNoise reads0/0/0;45liveobservations/43positions,health100,
47programbinaryrestores,0misses/writes/rejections. NativeSwaprequested1/result0/
effective1.

75–180s:25.90683FPS versus counterOFF25.86971 (+0.14% sample difference);
minimumcomplete1s/5s22/22.4,p95/p99/max45.401/47.779/71.651ms. ProducerCPU
28.3216,workerCPU10.8841,swapwall26.8760/nestedCPU.4569ms. Single-pair broad
cadence similarity does not establish zero sampler overhead or repeatability bound.

All30 TARGETED_SAMPLE records independently validated: each tencontiguous actual
driver intervals with end inside pairedRAW request window, finite/nonnegative
metrics,520MHz+2%sanityPASS; aggregate3.013087583s. Aggregate GPU-pending cycles
normalize to71.096%wall at520MHz (threegroups74.121/72.902/66.265%). AmongGPU
pending cycles:tiler4.315%,shaderfragment86.091%,programmablecore98.494%.
ConditionalALUissue73.556%,texturefilterissue23.001%; read/writeexternalhandshake
stall2.309/1.731%,externaltraffic581.260/186.219MB/s decimal. OfficialG31formulas
and all raw sums/constants remain in GPU notes plus ignored analysisJSON
`.port-cache/issue-13-limits/gpu-counter-active-652b71-analysis.json`.

This is fragment/ALU-heavy GPU-dependent critical phase, corroborating measured
GPU-frequency sensitivity; GPU is not continuously pending in sampled bursts.
Do not infer immutable hardware ceiling, proven DRAM saturation, exact per-pass
attribution or guaranteed no feed/display/synchronization headroom. Device-global
counters are not per-game-context counters. Three~1sbursts do not cover whole105s
workload or all worstframes.

Historical provisional RAW→SDL envelope is invalid: exact captured SDL library
uses gettimeofday for ticks/perf, not upstream Unix RAW path. Raw launcher bracket
spans184.413s and last completion is180.293SDLseconds, but comparing them does not
prove origin or individual burst alignment without cross-clock bridge/clock-step
bounds. Withdraw previously computed96.383–101.507/121.268–126.393/146.261–151.386
SDLsecond envelopes. Counter raw intervals, stage/unit ratios and fixed520 reads
remain independently valid. No exact100ms completion-row join claimed.

One ALSA recover/underrun line bracketed148.466–151.017SDLseconds;
counterOFFd498a8 has no such line. Prior inferred overlap with third counter burst
is withdrawn because clock bridge was unproven. Preserve possible observer audio/
frame-tail perturbation; one event alone does not establish sampler causality.
Do not use meanFPS similarity to claim observer has no audio/tail impact.
MatchedNoiseOffNormalcounterONswap0 request follows with same settings/source/clock
controls; actual provider readback below determines whether interval changed.

### Actual swap0 request: captured SDL forces interval1

`20261115T124856641519Z-e4e5b8` completed all host/launcher/service phases0,
source immutable, actual485 deviceSHA,59firmwareOK,all3 exact governor restores/
errors[],frontendactive. Three counter helpers each verified/native0/strict10
samples, sidecar0. Native logs `gl_swap_interval requested=0 result=0 effective=1`.
Set-call success does not establish interval0 capability. Earlier652b71 was
requested1/result0/effective1. Subsequent disassembly of exact captured SDL SHA
f06e06… proves KMS setter overwrites every request with1 and getter reads same
cached value, not stub. Both runs therefore actual interval1; disabled-VSync
capability failed on installed provider. Preserve raw requested/set/get results;
Docker's effective0 capability does not prove handheld capability.

75–180s true640 room210:24.82425FPS, minimumcomplete1s/5s19/20.4,
p95/p99/max49.287/52.462/82.003ms; producerCPU28.3315,workerCPU10.7141,
swapwall28.7870/nestedCPU.4655ms.43liveobservations/42positions,health100,
direct Noise/Display/rendererNoise0/0/0.47programrestores,0misses/writes/rejections,
no ALSA recovery line. All36 monitor reads1512/520/786,maximum sampled73.333°C.
Independent30counter intervals validate timing/fixed520 sanity; GPU pending
72.9578%,conditionalALU76.7521%,filter23.0161%,tiler/GPU3.9688%,externalread/
writehandshake1.6475/1.5492%. Raw sums/constants retained in ignored
`gpu-counter-active-e4e5b8-analysis.json`. Do not attribute cadence difference
from652b71 to established interval change; repeat/route/load variation and
observer effects remain possible.
82.244s longest completion remains separate tail event for joined producer/worker
analysis. Native/software path headroom remains open rather than declaring
continuously saturated GPU or hardware ceiling.

### Additional actual level: hospital160 warm moving640 pass

`20261115T125746122373Z-3572b6`, public slot24/room160, final485, full stock,
NoiseOff/Normal/disp1/1,30FPS limiter,counterOFF. All host/launcher/service phases0,
source preserved,actual485SHA,59firmwareOK,all3exactgovernorsrestored/errors[],
frontendactive.56/56 live room160 observations,44positions,motion in every sampled
30s subwindow,health199.399994constant;direct Noise/Display/rendererNoise0/0/0.
51programrestores,0misses/writes/rejections,noALSA recovery line anywhere in run.

48–160s true640:29.99991FPS,every complete1s/5s bin30,p95/p99/max34.641/35.491/
48.110ms. ProducerCPU14.89125,workerCPU9.35693,swapwall8.47163/nestedCPU.40946ms.
All32 coarse reads1512/520/786,maximum sampled66.153°C. Pass applies to this
loaded warm room and automated route, not all hospital transitions or campaign.
Public archive/seed provenance remains manifest quoted for mall; slot24 hashes
retained in this run's scene-identity.json. Church240 follows with same controls.

### Additional actual level: church240 warm moving640 pass

`20261115T130244860301Z-7500f4`, publicslot28/actualroom240, final485/full stock/
NoiseOffNormal/disp1/1/30FPS/counterOFF. All host/launcher/service phases0,
immutable source,actual485SHA,59firmwareOK,all3governorsrestored/errors[],
frontendactive.56liveobservations/47positions,motion in all sampled30s subwindows,
health200constant,directNoise/Display/rendererNoise0/0/0.59programrestores,
0misses/writes/rejections,noALSA recovery line. All32 policy reads1512/520/786,
maximum sampled68.076°C.

48–160s true640:29.98285FPS,mincomplete1s/5s29/29.8,p95/p99/max34.376/35.576/
48.106ms. Individual-window producerCPU16.6841,workerCPU7.9659,swapwall11.4947/
nestedCPU.42455ms; boundary frame counts differ3359producer/3358completion, so
frame-ID join required for exact lane-pair comparisons. Three added distinct
public-save routes now measured at true640 with actual live movement; room210
remains harder than mall18/hospital160/church240. These bounded loaded-room
routes do not prove campaign transitions, cold shader coverage or universal30.

### Read-only exact SDL provider capture for offline semantics audit

Existing saved inventory extended within same boundary. Observed native ARM64
RED missingcapture→GREEN→3 inventory regressionsPASS; logs
`.port-cache/issue-13-limits/sdl-provider-{red,green,refactor}.txt`.
Only exact SDL2 SONAME candidates from existing ldconfig observations considered,
resolved within system/PortMaster library roots; ELF64/LE/AArch64 header and
20byte–32MiB bounds checked. Read-only source bytes copied into run evidence,
source/target/SHA/size/ABI retained; no install, library replacement or permission
change. Fixture source/alias preserved. TDD proves capture behavior, not SDL
semantics or handheld capability.

Actual inventory`20261115T130739207517Z-4fa06c` all execution/collection0,
59firmwareOK,frontendactive. Captured2,338,880bytes from
`/lib/aarch64-linux-gnu/libSDL2-2.0.so.0` resolving
`/usr/lib/aarch64-linux-gnu/libSDL2-2.0.so.0.3200.10`, SHA
`f06e06daaf7681aece218f65fec74e351cc07e1ebf0e280b0d66d5de64241de7`, exact
match to prior actual game dependency evidence. ELF remains ignored private
artifact `device/sdl-provider/library.so`, metadata`identity.json`; never public
binary. Offline disassembly/source matching delegated to GPU researcher. No
conclusion from forced-interval upstream patch until actual ELF path audited.

Exact captured ELF audit subsequently completed using readelf/ARM64 objdump.
Installed KMS setter at0x177dec unconditionally loads1 at0x177dfc and overwrites
input at0x177e00, storing EGL cached interval at0x177e48; getter0x143878–0x1438b8
reads same cache+32. Revision string is SDL-release-2.32.10-0-g5d2495703.
This matches public [RK3326 forced-interval patch](https://github.com/christianhaitian/rk3326_core_builds/blob/04a465f9536fe8ced4f1a5cd0c6f284e62b5bc90/patches/sdl2-patch-0001-egl.patch)
against upstreamSDL5d249570393f7a37e037abf22cd6012a4cc56a71. Setter success0 with
request0/getter1 is actual forced interval1, not stub getter. SDL KMS swap retains
prior-flip poll/EGLswap/GBMfrontbufferlock/pageflip stages; current swap wall time
cannot be equated exclusively with GPU execution.

Actual timer counter0x1b5b90 calls gettimeofday, seconds×1e6+usec; frequency
0x1b5c60 returns1e6; ticks0x1b5a8c subtracts lazy realtime origin. This disproves
earlier generic Unix RAW-clock assumption. Existing counter RAW/MONOTONIC→SDL
envelope and audio overlap claims above withdrawn; independent hardware interval
metrics remain valid. Audit raw text in ignored
`.port-cache/issue-13-limits/sdl-source-audit/actual-sdl-{readelf,objdump,rodata,strings}.txt`,
detailed source/offset analysis in GPU research notes. No library modified.

### Matched resolution diagnostic: software limit0, provider still interval1

Frozen485/NoiseOffNormal/disp1/1/fullstock/same immutable fixed checkpoint/caches/
camera/keys.640 run`20261115T130925612420Z-cc0b12`,320 run
`20261115T131314003359Z-9f2184`. Both all host/launcher/service phases0,source
preserved,actual485SHA,59firmwareOK,all3governorsrestored/errors[],frontendactive.
Plan `fps_limit=0` removes native optional30 limiter; request0/set0/get1 remains
forced interval1 on proven SDL. Do not label either VSync disabled or unconstrained
CPU ceiling. Both output640x480, actual internal completion dimensions640x480 and
320x240 respectively. Both static live room210/oneposition/health100, direct
Noise/Display/rendererNoise0/0/0,45programrestores0miss/write/reject,noALSA.

55–95s640:21.37981FPS,mincomplete1s/5s19/20.4,p95/p99/max51.094/55.329/56.115ms.
856producer/completion frames,producerCPU27.9540,draw2.9914,Present6.1000,
workerCPU10.7521,swapwall35.0233/nestedCPU.4435ms.20/20policyreads1512/520/786,
maximum sampled70°C.

55–95s320:29.93772FPS,mincomplete1s/5s29/29.8,p95/p99/max34.190/34.998/52.180ms.
1198producer/completion frames,producerCPU27.8551,draw2.9705,Present.03517,
workerCPU10.6575,swapwall13.0328/nestedCPU.42405ms.21/21policyreads1512/520/786,
maximum sampled68.846°C. Resolution change yields+40.03% observed throughput,
almost unchanged lane CPU cost and~21.99ms lower swap wall wait. This establishes
resolution-sensitive renderer/presentation critical path on actual hardware;
near30 result does not prove absolute CPU limit because game/display pacing may
remain. Dynamic room210 route is different workload from this fixed camera.

### Saved buffered-trace and preSwap-drain diagnostic handoff

Native researcher owns C implementation and immutable candidate build. Existing
owned saved launcher boundary forwards only explicit `SH3_GL_TRACE=1` and
`SH3_GL_DRAIN=1`. Scene booleans strict; trace requires profile, drain requires
trace/profile, absent fields clear ambient enables. Each forwarding/type/dependency
behavior observed RED→minimalGREEN→reviewedREFACTORregreen; logs
`.port-cache/issue-13-limits/gl-{trace,drain}-*.txt`. Full ARM64 frontend45tests,
44PASS/1expected privileged fixtureSKIP,10.523s (`gl-diagnostics-refactor.txt`).
No fixture result proves actual GL attribution or runtime candidate compatibility.

Three matched120s true640 movement/combat plans: `performance-traceoff-640`,
`performance-trace-640`, `performance-drain-640`; fps30,swaprequest1,countersOFF,
identical checkpoint/route/PEEK,75–120warm window retaining82s turn hitch and later
turns. PreSwap glFinish perturbs pipeline intentionally; this is diagnostic,
not proposed product behavior. Public hostCLI RED unknown scene→GREEN followed
26host testsPASS21.278s (`gl-diagnostic-scenes-host-refactor.txt`). Initial Docker
GREEN attempt failed setup because image intentionally lacks git; interpreted
host-CLI fixtures rerun on actual host with real git. One misplaced test-tail
assertion corrected before GREEN; no runtime failure inferred from either setup
error. Device queue remains frozen485 through DMC control; no new candidate
deployment before native GREEN/stable artifact handoff.


### DMC frequency isolation: moving true640 with CPU/GPU held stock max

`20261115T131715482349Z-410c67`, frozen485, exact NoiseOffNormal checkpoint/
route/30FPS/swap1/counterOFF controls of d498a8. Only CPU/GPU performance guard
selected; DMC kept original dmc_ondemand. All host/launcher/service phases0,
source preserved,actual485SHA,59firmwareOK,CPU/GPU exact restores/errors[],frontend
active. All36 coarse samples CPU1512/GPU520/DMC528; maximum70°C. Earlier fullstock
DMC786 control had all36 samples1512/520/786,maximum72.083°C. Samples do not rule
out sub-five-second variation, but no sampled thermal frequency collapse.

75–180s:2518 completions,23.98193FPS,mincomplete1s/5s18/19,p50/p95/p99/max39.761/
51.820/53.842/79.515ms. ProducerCPU29.98144,workerCPU12.18087,swapwall28.52927/
nestedCPU.66798ms;42liveobservations/41positionsroom210,health100,Noise/Display/
rendererNoise0/0/0.47programrestores,0misses/writes/rejections. Five ALSA recover
lines after PEEK times23.269,43.358,79.536,129.850,162.999s (next-PEEK bounds
retained in raw log); three within warm interval. Fullstock d498a8 has no ALSA.

Relative to same-profile786MHz run25.86971FPS,528MHz throughput is7.30% lower;
producerCPU rises28.350→29.981ms,workerCPU10.627→12.181ms,swapwall27.352→28.529ms.
This establishes measured DMC-frequency sensitivity, not saturated DRAM bandwidth
or immutable hardware ceiling. Single matched run per policy cannot exclude
route/audio scheduling variation. Restore policy affects only selected CPU/GPU;
DMC governor/caps were never written.

### Memory and I/O limits from retained five-second observations

Fullstock hardroom d498a8 resident peak317440KiB,minimum MemAvailable552752KiB,
SwapFree494272–494288KiB,process major faults0 throughout; no observed memory
pressure ceiling. DMC528 contrast resident318388KiB,available551052KiB,11major
faults already at first native sample and unchanged thereafter. Full sampled-span
system iowait approximately.157% in both runs. Hospital/church resident peaks
273992/288872KiB and minimum available596636/584232KiB. These are bounded routes,
not heap/GPU-allocation lifetime proof.

Device `/proc/PID/io` files absent in every monitor sample, with exact errors
retained; per-process physical read/write counters unavailable. Existing
`/proc/PID/stat`,RSS/systemmemory/CPU and dirty/writeback observations remain
valid; low full-span iowait does not exclude isolated loading or storage stalls.
Ignored local summaries`<run>-memory-summary.json` retain extrema/fault/cpu deltas.
No source/library/permission/kernel change made to expose unavailable counters.

### Ordinary profiler observer control preparation

Existing `d3d8.c` PEEK emits sixty-frame counts and SDL wall timestamps outside
profiler condition. New matched120s `performance-profileoff-640` retains same
keys/PEEK/seed/fullstock/30FPS,clears profile/trace/drain and omits profile-only
swap override (native unchanged default1). Public hostCLI observed RED unknown
scene→GREEN→reviewedREFACTOR2PASS; separate RED→GREEN→refactor removes invalid
profile-only override. Evidence`profileoff-{scene,default-swap}-{red,green,refactor}.txt`.
Cadence from PEEK spans is coarse and may differ from SDL-completion row cadence;
no per-frame percentiles or CPU attribution available with profiler disabled.
Device control started`20261115T132758976620Z-c42c5b`; no result assumed before
collection. CCE queries for PEEK repeatedly returned ignored caches/generated
chunks; bounded direct source lookup found actual already-owned d3d8.c observer.

### Exact issue13 acceptance gaps after warm multi-level campaign

Fresh full issue13 body/comments reviewed. Current485/NoiseOffNormal scenes all
retain seed shader/program caches; zero misses establish warm restores, not a
cold/warm pair. Historical2ac6 first-visit1.231s pause/ALSA is retained as prior
runtime evidence, not equivalent current cold acceptance. Current cold/warm pair
still missing. Lowest-profile mapping covers exposed flareLow/shadowNo/NoiseOff,
Normal-versus-Sharp sampling; BloodNormal retained and wider supported-choice
survey still needs explicit disposition. Four loaded-room routes establish
actual motion/health/combat coverage, not full campaign transitions. New buffered
trace/drain must distinguish critical GPU work from display/synchronization;
per-process storage counters unavailable as above. Issue13 measurement acceptance
can pass independently of30FPS capability, but blanket acceptance not claimed
while these stated gaps remain.


### Ordinary profiler disabled: actual coarse moving640 control

`20261115T132758976620Z-c42c5b` all host/launcher/service phases0,actual485,
source preserved,59firmwareOK,all3exact governor restores/errors[],frontendactive.
No frame CSV or CPU-sample completion log generated; native ordinary default
swap requested1/result0/effective1. Same NoiseOffNormal checkpoint/keys/fullstock/
30FPS true640;19PEEK observations in75–120,allroom210/19positions/health100/
NoiseDisplayRenderer0. All25 policy reads1512/520/786,max68.461°C,noALSA recovery.
47programrecords/16upfront38ms,zero cachemiss/write/rejection output.

Sixty-frame PEEK endpoints frame2040→3120 at77.079→119.945s give25.19479FPS.
Profiled485 d498a8 same nominal75–120 has18PEEK samples76.390→118.070s,
24.47217FPS (1109actualcompletionrows24.650707FPS). Coarse off sample~2.95%higher,
but different endpoint coverage/thermal/routevariation prevents precise profiler
cost subtraction; do not claim instrumentationfree25.87FPS or zero observer cost.
Upcoming173traceoff comparison additionally changes executable; preserve this
caveat. Full hostCLI regression27PASS22.027s after added scene/defaultswap tests,
`profileoff-full-host-refactor.txt`.


### Bounded application-cache pair preparation

Two matched100s `profile-cache-640` / `profile-cache-320` plans keep fixed original
checkpoint/camera/keys,640x480output,30FPS limiter/swap1/query+traceOFF,55–95warm
window and direct optionsPEEK. Public hostCLI observed unknownsceneRED→GREEN→
reviewedREFACTOR3PASS4.259s; cold seed fixture proves absent caches not deployed
and unchanged save bytes retained. Logs`cache-scenes-{red,green,refactor}.txt`.
Actual pairs use frozen173 trace-off and the subsequently verified Blood Little
seed. Full per-command trace proved too expensive; its drain case is held while
a separate coarse-trace candidate is built. Cold/warm pairs retain one package.

Cold definition limited to both PORT-LOCAL shader-key and compiled-program caches
absent in isolated copy. Corresponding warm copy retains exact original noncache
save/settings and replaces only caches with files generated by completed cold
session. Original source preserved. Vendor/system driver cache and OS pagecache
not globally purged, no firstboot cold claim. Actual missing-cache/sourcecompile/
write versus restore counts, loading tails and audio must be collected before
accepting this bounded comparison. No fixture result passes device cache behavior.


Uncapped optional-pacer forwarding audited against actual retained payloads:
cc0b12/9f2184`device/scene-values.txt` line7 is numeric0; deployed runtime.sh
unconditionally exports that field, and installed Game.sh allowlist tests variable presence (`${!name+x}`),
forwarding string0 unchanged. Actual native stdout in launcher/service has NO`frame_limit=30`
line, while same485d498a8 positivecontrol prints it. Frozen native pace_frame
sets period only for exactstring30 and returns early otherwise; no default30.
Thus optional native30pacer inactive, independent of forcedSDLinterval1 and
remaining guest/display pacing. No extra run or C change needed for this check.


### Final native diagnostic candidate and actual trace-off control

Frozen package `.port-cache/builds/20261115T132039539344Z/artifacts/runtime`,
SHA1738d4ad3b98aa38729c8f59a561ffe0be2147ff29251974c5cacd272ddb082d,
BuildID63f7a416c27f5caed6d647ff87ea18dd8e3a53ca,debugSHA
9e69f9988682d68122822db606a46e67111d29ec992f6799006b3867d138ec98.
O3/boundedLTO,recognized original inputSHA1d851669ef609b3164e3581aa8dcfbfaec866cb79.
Native TRACE finalregreen30.859s,drainGREEN31.407/refactor31.227s PASS. Initial
fixed35ms fixture Swap bound failed under Mesa50.630ms scheduling; replaced by
independent exact external Swap-wall oracle, no runtime change/relink. No hardware
performance conclusion drawn from fixture timing failure or passes.

Actual `20261115T133805641460Z-5917d6`,120s traceOFF/NoiseOffNormal/BloodNormal,
exact existing moving checkpoint/caches/keys/fullstock/cap30/swap1/countersOFF.
All phases0,actual173SHA,source preserved,59firmwareOK,all3exact restores/errors[],
frontendactive. No .gl.csv or trace anchors generated as intended.1067 completions
in75–120:23.72210FPS,mincomplete1s/5s18/19.6,p95/p99/max50.846/54.800/69.020ms;
producerCPU28.31241,workerCPU10.80820,swapwall30.55115/nestedCPU.44975ms.
18live observations/18positionsroom210,health100,Noise/Display/rendererNoise0/0/0.
All25 coarse reads1512/520/786,max67.307°C;47binaryrestores0miss/write/reject,
no ALSA recoveries;native frame_limit30/request1/result0/effective1.

Matched-window485 d498a8 is24.65071FPS,not its broader75–18025.86971. Changed
executable, route evolution and thermal variation prevent attributing difference
entirely to diagnostic branch overhead. Same173 traceON and trace+drain controls
follow; frozen485 profile-off PEEK estimate also carries this binary caveat.
HostCLI28testsPASS25.410s after cold pair additions; shellsyntax/diffcheck clean.


### Material trace observer cost discovered on actual hardware

`20261115T134236875830Z-83a5af`,same173120sroute/seed/fullstock/cap30/swap1,
TRACEon/drainOFF/counterOFF,all phases0/actual173/sourcepreserved/59firmwareOK/
all3restores/errors[]/frontendactive. Buffered trace855750bytes;producer2482events,
worker6216events,bothdropped0. Twelve live positionsroom210/health100;all24 coarse
reads1512/520/786,max66.923°C. No sampled frequency collapse explains slowdown.

75–120740completions:16.43793FPS,mincomplete1s/5s14/14.8,p95/p99/max67.702/
69.919/94.734ms. Same173 traceOFF23.72210FPS:trace lowers throughput30.7%.
ProducerCPU27.72863ms versus28.31241OFF;workerCPU29.432996versus10.808196,
**+18.625ms per frame**. Swapwall28.99730/nestedCPU.39059ms versus30.55115/
.44975msOFF. This isolates a large observer-induced worker CPU load; cannot
present tracecommand wallcosts/GPU starvation as ordinary baseline limits.
Native researcher assessing per-fast-command timing/CPU-clock overhead before
continuing causal drain comparison. Device restored while assessment occurs.
Original trace and failed-cost experiment preserved, not rewritten or hidden.

Actual anchors now prove installed SDL path and clock bridge:videoKMSDRM,
SDL2.32.10,library/lib/aarch64-linux-gnu/libSDL2-2.0.so.0,performancefrequency1e6.
StartupSDLticks257,REALTIMEbefore1794750240187523008ns/perf1794750240187524;
endSDLticks120319,REALTIMEbefore1794750360249044744ns/perf1794750360249047.
PairedRAW/MONOTONIC/REALTIMEbounds retained. Clock validity does not make
large-cost trace representative of instrumentation-off frame behavior.
Aligned BloodPEEK70E66C8 added only newcacheplans via observedRED→GREEN→
reviewedREFACTOR2PASS3.497s; currentthreecausalplans retain BloodNormal.

### Verified minimum-setting application-cache pairs: first actual cold640

Blood amount's actual lowest UI label is **Little**, stored value0 at
`70E66CB`; aligned `70E66C8` PEEK exposes that high byte. Native menu edit/apply
and a separate clean cold reload verified Little / NoiseOff / DisplayNormal.
Seed `.port-cache/issue-13-limits/seed-blood-little-20261115T135000Z` changes only
`data.sys` to `c41256a3920705ed09996ceb11bb474c8e437de524eff52819c4adc782c573d0`.
Checkpoint `data.001` remains `fa2d9fd1b7c1e2af9b9b771b2a996f988f5b82bdd8cda41d045975f31b787515`;
true640 configuration remains `27a40ce6f83f520e5ac9a8b2511796ee7a63ea9166439db42e4f69420f31e600`.
Original warmed caches remain18aa0144… /06a34b1c… in this source. Native UI-helper
write exceeded its82s wrapper deadline, followed by independently successful
cold-reload proof; `blood-little-identity.json` retains this provenance caveat.
No source or original owner state changed.

Isolated copies and source/cache manifests live under
`.port-cache/issue-13-limits/cache-pairs-173-20261115T135000Z`.
Cold640 `20261115T134954008713Z-507725` uses frozen173,100s fixed camera/pose,
true640 internal/output, cap30, request1/result0/effective1, all stock governors,
queries/trace/counters/captures OFF. Both port-local caches absent at launch;
actual native program report **restored0 / missed31 / written31 / rejected0**.
Collected generated caches SHA256 `124e2d24c0a01bd56f5035146f2bef5f0165d7b169cccef6d84c5137c146a77f`
and `0ca5d8f62dea7b32420ccf332798cfd63a03bd26c7d4726ff613b39b7a0bc5bc`.
Only these two files replace original caches in corresponding warm640 copy;
original noncache bytes and source hashes verified unchanged.

Cold64055–95s:920 joined producer/completion rows, **22.98994FPS**;
completion p50/p95/p99/max43.755/47.893/48.969/54.504ms, minimum complete1s/5s
21/22.0. Producer CPU27.48627ms, workerCPU10.86690ms, swapwall31.76608ms with
nested CPU0.45669ms. Sixteen live observations all room210, identical fixed pose,
health100; Noise/Display/rendererNoise/Blood high bytes all0. All21 sampled
CPU/GPU/DMC frequencies1512/520/786; thermal-zone maxima69.615/71.666°C.
No logged ALSA recovery. First room completion at47.505s has **2293.356ms** wall,
followed by699.142ms at48.204s; these loading/first-use stalls remain separate
from55–95s warm distribution. Program-cache absence and writes are observed;
without command tracing, do not assign the entire stall exclusively to compilation.
All host/launcher/service phases0, actual173 SHA, source preserved,59 firmware
checks OK, exact restoration of all3 governors with errors[], frontendactive.
Derived raw-preserving statistics: run-local `frame-summary.json`.

### Coarse trace saved-workflow preparation

Full trace's observed worker cost requires a cheaper observer before causal
attribution. Runtime owner adds opt-in `SH3_GL_TRACE_COARSE=1`; saved workflow
forwards only strict boolean plan enable with TRACE+PROFILE and clears ambient
inherited enables. Existing launcher boundary retained. Four vertical observed
RED→GREEN→reviewedREFACTOR slices cover forwarding, type rejection, dependency
rejection and default-off cleanup. Full ARM64 frontend fixture regression:
49 tests,48 pass and1 expected privileged/read-only-sysfs skip,11.509s.
Logs `.port-cache/issue-13-limits/coarse-{forward,type,dependency,default}-*.txt`.
Public CLI coarse-plan test observed unknown-choice RED, then minimal matching
120s coarse/coarse+drain plans GREEN. Same route, cap30, request1, capturesOFF,
75–120 window; observer-off plan unchanged. Native build/actual observer cost
remain pending; no fixture result establishes native speed.

The forthcoming new-candidate trio will use verified BloodLittle source with its
original warmed caches for all3 cases, countersOFF. The173 BloodNormal full-trace
failure remains a distinct historical experiment, not a cross-binary causal pair.
CCE recall returned relevant prior decisions, but scoped code search continued to
rank generated ignored run/cache copies; exact current owned files inspected for
this bounded forwarding/config change.
Coarse-plan reviewed refactor regression:29 host CLI tests PASS27.751s,
`coarse-scenes-refactor.txt`; shell syntax, JSON and `git diff --check` pass.

Warm640 `20261115T135726264524Z-899c2e` confirms **restored31 / missed0 /
written0 / rejected0** with only those generated caches changed. Same173,
checkpoint, fixed pose, true640, exact cap30/swap1/stock controls and minimum
options. All statuses0, source preserved,59 firmware checks OK, exact3-governor
restores/errors[], frontendactive.55–95s905 completion rows: **22.63962FPS**,
p50/p95/p99/max43.789/49.216/50.671/56.976ms; minimum complete1s/5s20/20.4.
ProducerCPU27.54089ms, workerCPU10.91856ms, swapwall33.03845/nestedCPU0.44947ms.
Fifteen live observations all fixed room210/health100 and Noise/Display/renderer/
Blood bytes0. All21 policy reads1512/520/786, both thermal maxima70.416°C;
no logged ALSA recovery. Warm loading still has693.925ms room210 completion at
48.851s despite zero source misses, so binary caching removes a large cold stall
but does not remove all loading work. Warm throughput did not improve over the
preceding cold run's already-warmed55–95s plateau; do not conflate startup cache
benefit with sustained frame-rate gain or claim strict same-temperature ordering.
First-room CPU split strengthens cache attribution without assigning every stall:
cold frame1229 producerCPU563.716ms, draw1846.897ms,208 draws/3,100,664 uploaded
buffer bytes; workerCPU1717.890ms, completion2293.356ms, swap2.097ms. Next cold
frame1230 workerCPU626.864ms/completion699.142ms. Warm first-room frame1248 has
same208 draws/3,100,664 bytes and producerCPU554.547ms, but workerCPU154.614ms,
completion693.925ms/swap11.033ms. Large first-use worker CPU cost falls alongside
observed binary restores, while roughly0.55s producer CPU loading work persists.
Warm producer/completion timestamp windows differ by one queued frame at each
edge; all905 completion IDs match full producer metadata, not a missing-frame
claim. Raw producer and worker lane durations overlap and must not be summed.
Whole-run queue census independently supports that cache distinction: cold640
`CompileShader`62calls/558.606ms producer queue wait, `LinkProgram`31/2289.936ms,
`CreateProgram`31/235.913ms; warm640 no CompileShader/LinkProgram entries,
`ProgramBinary`31/32.870ms and `CreateProgram`31/16.019ms. These stdout totals
measure producer wait for queued operations across the whole run, not isolated
worker GL execution or a localization of every first-room stall.

Cold320 `20261115T140116608881Z-ea97cb`, same173/BloodLittle fixed100s pair:
actual internal320x240/output640x480, cap30/request1/effective1, cache
**restored0 / missed30 / written30 / rejected0**.55–95s1197 completions,
**29.93967FPS**, p50/p95/p99/max33.336/34.183/35.550/86.504ms,
minimum complete1s/5s28/29.6. ProducerCPU27.57139ms, workerCPU10.68950ms,
swapwall13.71502/nestedCPU0.40798ms. All warm completion IDs match full producer
room/dimension metadata; independent elapsed windows differ at queued boundaries.
Twenty fixed-position live observations room210/health100/NoiseDisplayRendererBlood0.
All21 policy reads1512/520/786, thermal-zone maxima72.916/69.230°C. First room
completion2357.974ms at47.723s, then697.491ms; cold startup tail persists at lower
internal resolution. Five logged ALSA recoveries:2 bounded33.981–35.980s,
1 at39.980–42.038s,1 in warm73.652–75.706s,1 during shutdown after99.708s.
Audio observations remain part of this run's limits, not silently discarded.
All host/launcher/service phases0, actual173SHA, source preserved,59firmwareOK,
exact all3 governor restores/errors[], frontendactive. Original BloodLittle seed
unchanged; warm320 copy replaces only this cold session's generated cache pair.

### Bounded per-process I/O capability check

Current game monitors retain repeated **ENOENT** for `/proc/PID/io`, while same
live PID's stat/status/threads remain readable; no EACCES reported. Existing
inventory now records caller UID, proc mount options, self-io read status, a
noninteractive root self-io read with its actual UID, and only selected installed
kernel CONFIG flags. No kernel setting, permission or installed tool changes.
One external-cat-boundary fixture observed missing-report RED→minimalGREEN→
reviewedREFACTOR; full ARM64 frontend50 tests,49 pass/1 expected sysfs-root skip,
11.138s. Logs `io-capability-{red,green,refactor}.txt`. Actual target root/config
result recorded below; missing I/O cannot be assigned a directly verified
kernel CONFIG value because neither installed config path is readable/present.

[Linux4.4 proc source](https://github.com/torvalds/linux/blob/v4.4/fs/proc/base.c)
guards both `io` entries with CONFIG_TASK_IO_ACCOUNTING and separately returns
EACCES on denied ptrace read access. [First-hand matching ENOENT report](https://github.com/VictoriaMetrics/metrics/issues/42)
describes absent `/proc/self/io` when accounting is not built. Neither source
proves this exact installed kernel configuration. Current [PortMaster templates](https://portmaster.games/contribute/porting/script-templates/)
retain per-port logs/normal helper lifecycle but supply no I/O-accounting fix.
Targeted comparable searches `wild1walker/portmaster-cuphead proc io` and
`PortsMaster proc performance io` found no applicable port-level accounting
solution; no other port's success claimed as this device's capability pass.
Matched coarse OFF/ON/drain minimum-option observation slice also observed public
CLI unknown-choice RED, then GREEN and reviewed full30-test host regression PASS
28.094s. Three new plans add aligned `70E66C8`; prior173 historical plan bytes
remain unchanged. Evidence `coarse-blood-scenes-{red,green,refactor}.txt`.
Native coarse candidate now READY after actual ARM64 GREEN17.317s/refactor17.147s,
full-trace30.891s, drain31.238s and real-checkpoint/default-profile62.986s checks.
Frozen package `.port-cache/builds/20261115T135522858288Z/artifacts/runtime`,
runtimeSHA `becbc930874e09b528adab3d9b885fc5272718522475ec14ba6156f7ffb27b68`,
debugSHA `0b085784f40334bb65b10eecfd25c32f14da968b435392d06fbf49b0c7b14889`,
BuildID `3fb27c01011a3612d1763f6be70b4361fa94435c`. SameO3/boundedLTO/input.
Actual observer control remains required before attributing hardware limits.

Warm320 `20261115T140511267080Z-93a47a` completes bounded cache matrix:
**restored30 / missed0 / written0 / rejected0**,1200 joined producer/completion
rows in55–95s, **30.00050FPS**, p50/p95/p99/max33.3165/34.331/35.844/39.810ms,
minimum complete1s/5s30/30.0. ProducerCPU27.77134ms, workerCPU10.81945ms,
swapwall13.13576/nestedCPU0.42719ms. Twenty fixed-position observations all
room210/health100/NoiseDisplayRendererBlood0; all21 policy reads1512/520/786,
thermal-zone maxima72.083/68.846°C. No ALSA recoveries. First-room completion
still709.242ms at45.966s; binary restores solve neither all loading CPU work nor
necessarily the steady-state bottleneck. All host/launcher/service phases0,
actual173SHA, source preserved,59firmwareOK, exact3 restores/errors[], frontendactive.

| Frozen173 fixed minimum-setting room210,55–95s | FPS | Min1s/5s | p95/p99/max ms | First-room longest completion | Native binary cache |
| --- | ---: | ---: | --- | ---: | --- |
|640 cold `507725`|22.98994|21/22.0|47.893/48.969/54.504|2293.356ms|0restore/31miss/31write|
|640 warm `899c2e`|22.63962|20/20.4|49.216/50.671/56.976|693.925ms|31restore/0miss/0write|
|320 cold `ea97cb`|29.93967|28/29.6|34.183/35.550/86.504|2357.974ms|0restore/30miss/30write|
|320 warm `93a47a`|30.00050|30/30.0|34.331/35.844/39.810|709.242ms|30restore/0miss/0write|

All output640x480, same checkpoint/camera/noncache bytes, BloodLittle/NoiseOff/
DisplayNormal/Lowflare/NoShadow, optional cap30 and forced SDL interval1. Internal
resolution differs only as named. This establishes actual application-cache pairs
and lower-resolution frame-budget headroom in this fixed view; not firstboot,
OS/vendor cache cold, full-campaign smoothness, VSync-off or immutable CPU ceiling.
Percentile derivation retains every warm outlier, median p50 and lower-index p95/p99;
loading tails and five cold320 audio recoveries remain separately recorded.
Output-size audit for all four cache runs uses retained actual configuration and
native geometry, beyond physical KMS size: collected `disp.ini` has
`resolution=640x480` or`320x240` as named and **`size=640x480`** in every run;
native **`CreateDevice 640x480`** and `output: requested640x480 drawable640x480`
prove game output/backbuffer and physical drawable. Completion CSV independently
proves internal640x480 or320x240. Thus320 tests lower Internal Resolution while
retaining640 Output Resolution/backbuffer; not both game settings320.
Data-only audit `.port-cache/issue-13-limits/cache-matrix-resolution-proof.json`.


### Final coarse candidate matched minimum-setting movement controls

First trace-off control `20261115T140929993471Z-d958cc` uses frozen **becbc930**
(package/build/debug identity above), verified BloodLittle/NoiseOff/DisplayNormal,
Lowflare/NoShadow, true internal/output640x480, cap30/swaprequest1, no GPU counter,
query or captures, original warmed47-cache seed (18aa0144/06a34b1c), same120s
movement/combat route. Plan SHA256
`b055df0b461ba59f9d0628ae0ef421c0296a870c541a26d151facb4a8aeab2ba`.
Source sys/001/disp hashes remain c41256a3/fa2d9fd1/27a40ce6. This is a new
matched BloodLittle trio; prior173/BloodNormal full-trace pair is historical
observer-failure evidence, not this candidate's baseline.

75–120s:1144 completions, **25.424860FPS**, mean39.334863ms,
p50/p95/p99/max39.095/45.128/46.237/67.410ms, minimum complete1s/5s21/23.2.
ProducerCPU28.389962ms, workerCPU10.855826ms, swapwall28.012106ms with
nestedCPU0.454123ms. All completion IDs/room/dimensions match full producer rows;
independent producer/completion elapsed windows differ at one queued boundary.
Nineteen scoped75–120s PEEKs show19 distinct positions, room210/health100 and
actual loaded Noise/Display/renderer/Blood bytes0. Native47binary restores,
zero misses/writes/rejections, no ALSA recovery. First-room754.398ms completion
at45.939s remains outside warm window; no loading-stall clipping claim.
All24 sampled domain clocks1512/520/786, thermal-zone maxima72.500/72.083°C.
Host/local/execute/all3collections/launcher/service0, actual deployed becb SHA,
source preserved,59 firmware hashes unchanged, exact all3 governors restored
with errors[], frontendactive. Execution log closed14:13:17.494UTC and final
collection/status14:13:23.358UTC: about5.86s collection, without earlier recursive
SCP124 failure. Run-local `frame-summary.json` is separate data-only derivation;
original raw files unchanged. Coarse and coarse+drain same-seed controls follow.

Actual bounded I/O audit in this run: callerUID1000, proc mounted normally with
no hidepid option; both user `/proc/self/io` and a separately checked actual
sudoUID0 self-io return **ENOENT**, status1. Neither `/proc/config.gz` nor
`/boot/config-4.4.189` available. Therefore per-process byte accounting cannot
be read from this device's current proc interface even as root; permission
escalation does not fix it. Linux4.4 source makes missing TASK_IO_ACCOUNTING a
plausible build explanation, but installed config value remains unverified.
Retained `device/io-capability.txt` plus `.stderr.txt` preserve exact statuses.
Systemwide sampled iowait remains available; it cannot localize single loading
stalls or substitute for missing per-process byte counters.


### Measured evidence-storage failure and bounded recovery

First coarse attempt `20261115T141555131159Z-4b1e0c` returned execution3,
collection1 **before game/service launch**. Original missing archives retained;
collection-only retry `20261115T141756851341Z-0a5f91` recovered original tree,
collection0. It ended while copying prior completed launch history, followed by
zero-byte outer status/frontend files and no game launch. No performance sample
or GPU capability failure inferred. `20261115T142120766883Z-1c98af` then failed
preparation with explicit **No space left on device**. Saved host capacity
`20261115T142253320457Z-b31d80` and saved-script repeat
`20261115T142441817410Z-4319b0` measured `/dev/mmcblk1p1` total/used
**122,132,480KiB**, available**0**,100%; inode accounting reports0/0/unsupported.
This is evidence-storage exhaustion during prolonged diagnostics, not a gameplay
RAM limit or failed native candidate. Original failed runs/statuses untouched.

Capacity reporting observed RED at public saved-entry boundary when run mkdir
fails, then minimalGREEN/reviewedREFACTOR (ARM64 frontend51tests,50pass/1expected
skip,10.707s). A full card cannot deploy that entry; host CLI now streams saved
`scripts/device/capacity.sh` before any device mkdir and captures output locally.
External SSH boundary RED→GREEN→saved-source refactor; full host31tests PASS
27.007s. No direct SSH or unsaved command execution used.

Reviewed explicit allowlist `.port-cache/issue-13-limits/payload-cleanup-plan.json`
contains20 exact current-task `/runs/<UTC-id>/payload/runtime/sh3` copies only,
retained in independently rehashed immutable local787/485/173/becb packages.
Public `inventory --reclaim-payloads` RED initially rejected unsupported behavior;
GREEN/refactor covers foreign paths, changed hash, active process, symlink,
changed local retention and two-member atomic validation before any deletion.
Host full32tests PASS30.005s; focused ARM64 guard regression2tests PASS0.973s.
Initial Docker test lacked external Git fixture; corrected fixture only, not
product code or hardware claim. No new native build, overclock or firmware change.

Actual saved recovery **`20261115T143014131290Z-d30f92`**, all statuses0:
all20 device namespace/regular-single-link/nonsymlink/hash/identity checks and
inactive-runtime checks passed before first unlink. Flushed host validation and
removal journal `reclaim.stdout.txt` records every exact path/hash/size; reviewed
plan retained in `reclaim-plan.json`. Exactly **644,664,432bytes** redundant native
payload copies removed. All20 immutable local copies rehashed after recovery,
matching plan. Available space becomes**631,424KiB**, filesystem cluster rounding
retained; inode totals unsupported. Installed `/runtime/sh3`, every run directory,
original game/source, logs, saves, manifests and prior evidence preserved.
No broad wildcard, game deletion or old-history cleanup performed.

Prior inventory copied all completed originals into every new snapshot. New
`previous-launches.sha256` instead references explicit original logs/state/cache/
service paths and hashes; original history stays on device and in previously
collected host runs. Current persistent-state and top-level port logs still
copied. Observed missing-manifest RED→minimalGREEN→reviewedREFACTOR; ARM64 full
frontend52tests,51pass/1expected skip,11.068s. Evidence
`history-manifest-{red,green,refactor}.txt`. This avoids cumulative duplicate
snapshots during remaining two fixed-scope diagnostics. Coarse/drain candidate,
seed, movement, clocks and analysis windows unchanged by storage repair.


Coarse control **`20261115T143222756103Z-14a5a0`** completes after storage repair:
same frozen becb, sys/001/disp/cache source hashes,120s route, actual minimum
BloodLittle/NoiseOff/DisplayNormal, true internal/output640,cap30/swaprequest1.
Plan SHA256 `4abcc8d7e0a5e5c464de0f7842605deceebd9edf5f5694b87a7ba14757b7165e`.
75–120s1075 completions, **23.891620FPS**, mean41.863555ms,
p50/p95/p99/max42.884/48.831/51.400/76.017ms, minimum complete1s/5s20/20.6.
All completion IDs and room/dimensions match full producer metadata; queued
window-boundary edge IDs differ. ProducerCPU28.238836ms, workerCPU11.059507ms,
swapwall29.581927ms with nestedCPU0.446771ms. Versus same-binary OFF d958cc,
workerCPU adds**0.203681ms**, far below earlier full-trace18.625ms, but throughput
is**6.03% lower**. No zero-observer claim: route/camera evolution, temperatures,
and preflight history-copy versus reference workflow also vary. Full trace's
30.7% collapse is avoided; exact ordinary-frame causal timing remains qualified.

Native modecoarse, producer3113/worker6856 events, **dropped0 both lanes**;
984,121byte trace, paired REALTIME/RAW/MONOTONIC/SDL/performance anchors at startup
and exit; actual KMSDRM/SDL2.32.10/performance-frequency1MHz. Eighteen scoped
75–120 observations show18 distinct positions/room210/health100 and all loaded
Noise/Display/renderer/Blood high bytes0. Native47restores/0miss/write/reject,
no ALSA recovery. All24 clocks1512/520/786, both thermal maxima67.307°C.
Host/launcher/service/all collections0, actual becb SHA, source preserved,
59 firmware hashes unchanged, exact3 governor restoration/errors[],frontendactive.
New historical reference manifest397,208bytes; every original retained.

OFF d958cc dip audit:19/45 complete1s bins below25, longest8s[75,83), then6s
[87,93); no bins at20 or less. Coarse14a5a0 has29/45 below25, longest18s[75,93),
three20-completion bins[79,82). Mean OFF39.334863ms exceeds33.333333ms budget by
**6.001529ms**, producer mean headroom**4.943372ms**. This is the new minimum
moving-window deficit, distinct from prior485/BloodNormal full105s mean5.323ms.
OFF game60Hz counter4577→7125 over SDL76.563→119.021s gives game/wall ratio
**1.000204**, ammunition6→2 with reserve30 unchanged; original speed and active
firing demonstrated in scoped route, not full campaign. Whole-second dip bins
are aggregate spans, not exact continuous instantaneous-FPS boundaries.

Final coarse+drain **`20261115T143559336520Z-331517`** completes same becb/
BloodLittle/NoiseOff/DisplayNormal/source-cache/true640/full-stock120s trio.
Plan SHA256 `f214bc7ebcb598c724d4aac15ec8967b2cb29979f43e264c4fac61d5b74dd638`.
75–120s622 completions, **13.839674FPS**, mean72.263796ms,
p50/p95/p99/max71.405/79.774/81.070/106.317ms, minimum complete1s/5s12/12.6.
All completion IDs match full producer room/dimension metadata; independent
timestamp windows differ at queued boundaries. ProducerCPU27.450737ms,
workerCPU10.416601ms; Swap wall0.300027ms/nestedCPU0.218754ms.
Ten scoped live observations give10 distinct poses, room210/health100 and loaded
Noise/Display/renderer/Blood high bytes0. Native47restores/0miss/write/reject.
First room715.467ms at45.838s remains outside warm slice. One ALSA recovery lies
between63.501–65.489s PEEK observations, before selected warm75–120s window.
All24 sampled domain clocks1512/520/786, thermal maxima66.538/64.583°C.
Native coarse/preSwap-drain mode, producer2518/worker9354 GL events, dropped0 both
lanes;1,287,693byte trace and paired clocks at startup/exit. CPU sampler separately
reports6 dropped samples; zero GL-event drops does not mean zero CPU-sample loss.

**Drain/pacer confound, source and actual event accounting:** driver `glFinish`
occurs before Swap timing starts in `swap_now`; its returned post-drain Swap-start
timestamp anchors `pace_frame`. Deadline resets when more than one period late.
This diagnostic therefore changes pacing behavior as well as GPU synchronization.
Joined-frame event totals divided by622 completions give worker dispatch10.0652ms,
drain28.6598ms, Swap0.3000ms, pacer33.0769ms, idle0.0348ms: approximately72.137ms
versus measured72.264ms mean interval. Pacer adds32.3991ms relative to coarse-only
0.6778ms per completion. Elapsed-window grouping has618 sleep events, mean33.3446ms
per sleep; joined-frame grouping has617 due boundary attribution. Neither is an
extra GPU pass or evidence that ordinary rendering needs72ms. Drain itself uses
only0.2424ms CPU and relocates deferred completion wait; it cannot isolate pure
GPU execution from previous work or establish what an unforced presentation
backend would achieve. Same-numbered pacer follows completion and can affect next
interval. Command events nest inside chunks; producer and worker overlap.
Independent data-only accounting and exact debug mapping:
`.port-cache/runtime-attribution/becb-coarse-drain-phases.json` and
`becb-coarse-observer-hitch.json`; simpler elapsed-group summaries remain beside
raw runs as `gl-event-summary.json`. Quantiles in this note use original
lower-index convention; independent sibling summaries may use interpolation.

Recurring turn hitch now has concrete queue attribution. Coarse frame2146,
82.273s completion76.017ms, producer draw49.014ms, includes synchronous queued
`glCreateProgram`40.108ms producer wait but only0.152ms producer CPU. Worker enters
its matching chunk31.376ms after submission; chunk8.614ms, then binary restore
1.200ms producer/1.030ms worker. All47 cache records restore without source miss.
Thus long producer wait is principally queue availability plus enclosing work,
not evidence of40ms shader source compilation. Coarse+drain same turn frame1953
has106.018ms CreateProgram wait,100.644ms to matching worker entry and1.289ms binary
restore, further enlarged by diagnostic pipeline/pacing change. A captured
`glReadPixels` pair occurs at51.074–51.075s, outside warm slice: worker30.092ms/
1.241msCPU and producer30.520ms wait. No warm readback event was recorded in the
zero-drop coarse trace; deliberately omitted async command timings cannot be
reconstructed. These observations narrow hitch mechanisms but do not split every
ordinary Swap into exact GPU/display/GBM/pageflip components.

| Same frozen becb minimum options, moving75–120s | FPS | Min1s/5s | Producer/workerCPU ms | Swap wall ms | Diagnostic interpretation |
| --- | ---: | ---: | --- | ---: | --- |
| OFF `d958cc` |25.42486|21/23.2|28.390/10.856|28.012|Ordinary profiled baseline;19/45 bins below25|
| Coarse `14a5a0` |23.89162|20/20.6|28.239/11.060|29.582|6.03% slower observed; queued hitch attribution, no zero-overhead claim|
| Coarse+drain `331517` |13.83967|12/12.6|27.451/10.417|0.300|28.660ms preSwap wait plus33.077ms paced sleep per completion; intentionally perturbed|

Final331517 host/local/capacity/prepare/deploy/execute/all three collections,
launcher and service statuses0. Actual deployed becb SHA matches retained package;
source preserved,59 firmware-library hashes unchanged, exact CPU ondemand/GPU
simple_ondemand/DMC dmc_ondemand governors restored with unchanged min/max caps,
restoration errors[], frontendactive and `device/runtime-pids-after.txt` empty.
No active game, sampler, device command or build remains from this lane.
Final preparation capacity568,448KiB available; device entry after deployment
530,560KiB. Filesystem percentage rounds100% despite positive free blocks; inode
accounting unsupported. No further reclamation or device runs performed.

### Final workflow validation and acceptance boundary

Final saved host CLI **32tests PASS31.330s**; network-disabled reusable
Linux/arm64 frontend workflow **52tests,51PASS/1expected root-readonly-sysfs skip,
12.086s**; evidence archive **1test PASS0.018s**. Unprivileged partial-write guard
case passed earlier; privileged fixture skip does not replace actual policy
acceptance. Logs `.port-cache/issue-13-limits/final-{device-cli,frontend-session,
evidence-archive}.txt`. These tests cover workflow semantics, identity, safe
collection/cleanup and restoration; actual handheld evidence above establishes
capability. Native final becb focused GREEN/refactor/fulltrace/drain/checkpoint
results remain separately retained by runtime owner. No additional product
behavior changed during documentation/data analysis, so no new TDD slice applies.
Final `git diff --check`, saved shell syntax, Python AST and scene JSON checks pass.
Data-only `.port-cache/issue-13-limits/final-device-evidence-index.json` independently
checks10 measured runs' native/scene identities, statuses, source preservation,
59 firmware hashes, restoration journals and exit results; final no-PID/frontend
and capacity proof plus all20 rehashed immutable cleanup retentions included.

| Issue13 measurement requirement | Actual evidence and remaining boundary |
| --- | --- |
| Minimum supported graphics and native identity | Actual UI+cold reload Little/NoiseOff/Normal; Lowflare/NoShadow mapping; loaded minimum bytes observed; immutable build/seed/plan/cache identities. Sharp alternative measured separately, no gain. |
| Matched cold/warm640 and320,640output | Four frozen173/BloodLittle fixed pairs above; actual misses/writes versus restores, output/backbuffer proof, full loading/audio tails retained. Application-cache cold only. |
| Representative unattended gameplay | Owner combat route plus public mall18/hospital160/church240; live poses, rooms, health/ammunition and source preservation. Added levels measured BloodNormal; final minimum Little route measured separately. No campaign/transition or physical audiovisual certification. |
| Frame budget, distributions and sustained dips | Completion IDs/timestamps, mean/percentiles/max, complete1s/5s floors and spans; warm/cold/loading separated. Hard640 remains below desired floor. |
| CPU/GPU/memory/I/O/synchronization domains | Producer/worker/swap CPU versus wall, GPU-frequency/DMC contrasts, actual hardware counters, memory/fault telemetry and bounded root I/O capability audit; shader-cache and queue/pacer attribution. Per-process byte accounting absent; exact ordinary GPU-versus-display split unresolved. |
| Controlled clocks, heat and recovery | All supported stock domains sampled; governors restored with exact caps/ownership checks, firmware/source hashes, frontend return/no PID; no overclock or library replacement. Five-second samples cannot exclude every sub-sample thermal transition. |
| Thirty-FPS result distinguished from profiling result | Three added warm levels near30, hard minimum true640 moving25.42486 with8s below25 and fixed64022.64–22.99;320fixed warm30.00050. Profiling evidence identifies limits; does not pass full-port640/30FPS smoothness or prove hardware impossibility. |

Issue remains OPEN and all task-owned changes local/uncommitted. No publication,
commit, push or tracker update performed. Subsequent implementation should target
measured presentation/queue behavior, supported NoiseOff policy and cold-cache
loading, then retain same minimum-setting controls; improvements remain proposals
until independent performance acceptance proves them.
