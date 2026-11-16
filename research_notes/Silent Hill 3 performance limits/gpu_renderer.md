# GPU, renderer and presentation limits — issue #13

**Chronology:** This note records initial source audit and historical `2ac6` baseline. Its “current” wording, missing measurements and candidate experiments describe that phase. Later [device measurements](measurement_plan.md), [CPU/queue attribution](cpu_runtime.md), [hardware-counter/SDL audit](gpu_counter_probe.md) and [final report](../../reports/Silent%20Hill%203%20performance%20limits.md) supersede those gaps and budgets. Original audit retained below for provenance.

Research date: 2026-11-15. Source audit: `d4e49600b1022c954baac1965767bb3a5d61b80a`. Research only; no runtime changes, builds, device execution or new performance claims. TDD does not apply to research notes. Future behavior changes require existing launcher → game → frontend test boundary, observed RED–GREEN–REFACTOR, then actual R36S evidence.

## What does current evidence establish?

### Takeaway

True 640×480 remains an optimization target with an unclassified bottleneck. Latest controlled pair identifies extra resolution-dependent work or waiting; it does not identify an immutable GPU limit. First useful experiment must explain **producer Present backpressure and actual worker swap**, rather than apply another generic cache.

### Cited Findings

- Final tested executable SHA256 `2ac6b9c02579ff37d20a920edde36a203458aeded0806f9e86ffecf4bc512ff9`, build `20261114T044419879221Z`, produced 29.990378 FPS at 320×240 internal/640×480 output and 23.196638 FPS at 640×480 internal/output. Matched room 210, five byte-matched seed files, shadow/flare 1/1, warm cache, equipment/fire/reload/movement, 30 FPS cap, 75–180 s analysis window. Native-640 p50/p95/p99/max completion interval: 42.656/51.373/53.331/82.274 ms; 320: 33.326/34.226/35.315/60.180 ms. Runs `20261114T050230071532Z-0ddc92` and `20261114T055246314042Z-4068d8`. [Current issue-14 report](../../reports/issue-14-renderer-caches.md).
- Current 640 run restored 47 program binaries, with zero program misses/rejections and zero logged ALSA recoveries. Warm native-640 deficit is not explained by first-visit compilation in this run. Park transition/death/new-game run still exposes separate cold program creation stalls. [Current report, final matched and park sections](../../reports/issue-14-renderer-caches.md).
- Measurement researcher independently recomputed current raw pair: producer thread CPU p50 approximately 28.70 ms at 640 versus 28.66 ms at 320; producer draw p50 approximately 3.35 ms at both; producer Present p50 approximately 13.70 versus 0.024 ms; actual worker SDL swap p50 approximately 29.49 versus 12.44 ms. These are overlapping pipeline stages, not additive component times. Neither current run contains `.gpu.csv`. [Measurement notes](measurement_plan.md).
- Raw sysfs GPU-load samples exist, but their window includes loading and lacks calibrated correspondence with GPU occupancy. Whole-run medians 59% at 640 and 35% at 320 are suggestive of more GPU activity, not proof of saturation. Current matched runs sampled full CPU/GPU clocks, but 640 was hotter; counterbalancing remains necessary. [Measurement notes](measurement_plan.md).

### Inferences

- Observed mean native frame period is approximately 43.11 ms. Reaching 33.33 ms requires about 9.78 ms less observed interval, or 22.7%; this arithmetic is a target gap, **not an attribution or forecast**. Tails also need improvement. GPU, worker CPU, producer CPU, presentation and limiter overlap prevent treating those numbers as a serial budget.
- Both runs have 640×480 output. A fixed scanout workload alone cannot explain difference. Internal rendering, framebuffer materialization and reading a larger source during final blit can still differ. A slow `SDL_GL_SwapWindow` may contain completion waiting, present scheduling, driver work or several of these.
- Capped 320 cannot establish uncapped producer or GPU floor. Historical 42 ms producer CPU and approximately 13 FPS values belong to superseded binaries; do not use them to rule out 640×480.

### Gaps

No current correlated GPU execution/counter trace, worker CPU timeline, effective swap-interval record, default-framebuffer/EGL-format record, KMS presentation trace, render-pass census or independently validated query coverage. No complete lowest-supported graphics preset established by 1/1 shadow/flare pair. No full-campaign native-640 acceptance.

## What exactly happens around Present?

### Takeaway

Current renderer already removed DISCARD front-image copy. Remaining offscreen-to-window path has an explicit dependency on game color output. Trace that path before optimizing it.

### Cited Findings

Current [`dev_Present`](https://github.com/ktodorow/sh3-r36/blob/d4e49600b1022c954baac1965767bb3a5d61b80a/src/d3d8/d3d8.c#L332) performs:

1. Read drawable size; bind game backbuffer for reading.
2. Bind default framebuffer 0 for drawing; disable scissor; clear default color black.
3. Blit game backbuffer to centered aspect-preserving window rectangle, flip Y, use `GL_LINEAR` even at 1:1 dimensions.
4. Retain front image, then queue actual SDL swap. Screenshot/readback paths are optional and must remain disabled in timing runs.
5. Pump events and bind game targets for next frame.

[`res_snapshot_front`](https://github.com/ktodorow/sh3-r36/blob/d4e49600b1022c954baac1965767bb3a5d61b80a/src/d3d8/d3d8_res.c#L545) already rotates texture names for `swap_effect == 1` (DISCARD). Only COPY-style branch does extra front-FBO blit. Immutable attachment-tuple FBO cache is also already implemented at [`target_framebuffer`](https://github.com/ktodorow/sh3-r36/blob/d4e49600b1022c954baac1965767bb3a5d61b80a/src/d3d8/d3d8_res.c#L351).

[`gl_context_open`](https://github.com/ktodorow/sh3-r36/blob/d4e49600b1022c954baac1965767bb3a5d61b80a/src/d3d8/d3d8.c#L132) calls `SDL_GL_SetSwapInterval(1)` without recording return value/effective interval. [`gl_prepare_context`](https://github.com/ktodorow/sh3-r36/blob/d4e49600b1022c954baac1965767bb3a5d61b80a/src/d3d8/gl.c#L148) sets profile/version, not explicit default-FB channel/depth/stencil sizes. Actual chosen EGL/window configuration must be measured, not inferred from game A8R8G8B8 setting.

[`publish`, `record`, `synchronize`](https://github.com/ktodorow/sh3-r36/blob/d4e49600b1022c954baac1965767bb3a5d61b80a/src/d3d8/gl_thread.c#L74) use three reusable command chunks, initially at least 8 MiB each. A chunk becomes visible when published by a synchronous API, capacity boundary or frame submission. Synchronous wrapper wait includes older queued work. It is not necessarily time inside named driver function. Swap completion releases producer before intentional pacing; at most one frame can remain ahead. [Worker implementation](https://github.com/ktodorow/sh3-r36/blob/d4e49600b1022c954baac1965767bb3a5d61b80a/src/d3d8/gl_thread.c), [CPU analysis](cpu_runtime.md).

Arm's framebuffer guide explains preservation and inferred offscreen render-pass boundaries: revisiting partially rendered targets can cause stores/reloads; full clears can avoid initial loads; invalidating dead attachments must happen before their producing pass is flushed. Guide is architectural motivation, not proof of this driver's behavior. [Arm, framebuffer handling](https://developer.arm.com/community/arm-community-blogs/b/mobile-graphics-and-gaming-blog/posts/mali-performance-2-how-to-correctly-handle-framebuffers).

### Inferences

- Default color clear may be cheap metadata and may prevent reading old tiles. Removing it can make performance worse. Clear plus blit is not sufficient evidence of two expensive physical passes.
- `GL_LINEAR` versus `GL_NEAREST` at exact 1:1 flipped coordinates is a small, falsifiable driver-path experiment. No predicted gain. Noninteger scaling and bars must retain expected filtering/layout.
- DISCARD permits discarding backbuffer contents; it does not automatically establish shared depth/stencil lifetime. Blind end-of-frame depth invalidation can corrupt next-frame depth use or auxiliary passes. Need actual read/write lifetime proof before this optimization.
- Direct rendering into window could eliminate intermediate materialization, but default-FB origin, readback/front image, surface lifetime, arbitrary D3D targets, reset and lost-context behavior make this a larger experiment. Do not start there without measured copy/presentation cost.

### Smallest discriminating Present sequence

| Order | Experiment | What observation means | Correctness / rejection gate |
|---|---|---|---|
| 1 | Reuse final binary for same-scene query off/on/off. Next instrumentation slice adds correlated producer frame ID, publish time, worker chunk begin/end, worker CPU time and actual SDL swap begin/end; record effective swap interval, drawable/default-FB/EGL properties. Keep that new binary fixed across its own controls. Existing `.swap.csv` and queue counters stay available. | Worker CPU consumes frame budget → driver/submission limit. Worker sleeps while GPU counters busy → GPU/dependency wait. Worker and GPU idle until vblank/pageflip → presentation scheduling. Long producer wait after late worker publication → pipeline bubble candidate. | Instrumentation must not change rendered frames, game-clock/wall rate or audio. Reject contaminated performance conclusions if instrumentation shifts cadence outside matched control variation. Numeric counter availability alone is not validation. |
| 2 | Short diagnostic interval 1 versus 0, with effective value checked. Keep native dimensions, scene, game timing and audio; repeat 1 after 0. Retain ordinary v-sync run as acceptance reference. | If waits collapse while useful GPU work/counters and rendered workload stay similar, vblank/queue policy contributes. If native workload remains above budget, disabling v-sync did not remove render limit. | Tearing/uncapped pacing are diagnostic only. Do not ship interval 0 to claim smoothness. Avoid changing fixed-step logic or treating faster simulation as improvement. |
| 3 | Native-640 minimal Present calibration using same SDL backend, EGL config, offscreen color format and final clear/blit/swap. Add independently controlled offscreen fragment workload while preserving final output dimensions. | Establishes baseline presentation period, scaling response of query/counters and location of added GPU work. A query that ignores added fragment work cannot classify game bottleneck. | Native ARM64/Linux build only, existing Docker ABI and host/device workflow. Synthetic results establish measurement response, not SH3 acceptance. No speculative hardware ceiling from microbenchmark. |
| 4 | If transfer/dependency dominates, diagnostic game build keeps offscreen rendering identical but swaps an already complete constant/previous image instead of sampling current backbuffer. Separately test 1:1 LINEAR/NEAREST final blit; do not combine. | Removing dependency to current backbuffer changes wait → current image readiness/final transfer implicated. Same-image filter A/B changes cost → blit path candidate. No change lowers priority of these paths. | Frozen/late image branch is a diagnostic ablation, never performance acceptance. Filter branch must match orientation, exact 640 coverage, alpha, bars, captures and front-buffer behavior. No benefit means revert. |
| 5 | Only after proof of full coverage: A/B default color clear on/off. Only after depth lifetime proof: A/B invalidation of dead depth/stencil before first pass-ending bind. | Counter/store decrease plus end-to-end improvement supports removable traffic. API-call count decrease without interval benefit does not. | Never invalidate game color retained for front-buffer reads, shared depth still consumed, or any attachment later read before clear. Exercise UI, fades, fog, flashlight, shadows, water/reflective surfaces and room/reset transitions. |

Experiments 2–5 are proposals, not existing script options or completed tests. Current monitor has no precise worker/GPU trace. CPU researcher owns publish/timeline instrumentation; measurement researcher owns matching, observer overhead and interval controls.

## Can existing GPU query be trusted?

### Takeaway

Extension and query counter support were demonstrated on actual R36S. End-to-end GPU attribution was not. Reuse and validate existing instrumentation; do not create duplicate profiler or read its sub-millisecond result as spare capacity.

### Cited Findings

[`profile_gpu.c`](https://github.com/ktodorow/sh3-r36/blob/d4e49600b1022c954baac1965767bb3a5d61b80a/src/d3d8/profile_gpu.c) is opt-in through `SH3_GPU_PROFILE`. It verifies extension/functions/counter bits, uses eight delayed queries, polls availability before 64-bit result retrieval and rejects disjoint results. It avoids per-frame blocking `glFinish`. Worker begins elapsed query before executing commands in first chunk; subsequent begins are no-ops until current query ends. End occurs **immediately before** actual `SDL_GL_SwapWindow`, so SDL/EGL-internal commands are not explicitly inside measured API interval. [Worker query and swap boundaries](https://github.com/ktodorow/sh3-r36/blob/d4e49600b1022c954baac1965767bb3a5d61b80a/src/d3d8/gl_thread.c).

Historical query validation run `20261113T223112187035Z-7965b3` reported 64 counter bits, 3476 rows, zero skipped queries, one disjoint discard. In warm 55–95 s, 824 rows gave mean 0.888596 ms raw GPU elapsed versus worker swap p50 about 36.739 ms. Query-enabled run ran 20.60076 FPS versus preceding no-query run 21.7564 FPS on earlier intermediate build; report explicitly leaves coverage and perturbation unresolved. Final cadence runs disable GPU queries. [Issue-14 GPU diagnostic sections](../../reports/issue-14-renderer-caches.md).

Khronos extension issue 18 discusses tiler behavior: elapsed implementations can account for binning/tile processing yet omit tile/system-memory transfers; timestamps may be coarse. Specification permits this; it does **not** prove particular R36S driver omits transfers. Async queries avoid CPU waiting but can still affect submission/driver work. [EXT_disjoint_timer_query specification](https://registry.khronos.org/OpenGL/extensions/EXT/EXT_disjoint_timer_query.txt).

### Inferences

Validate using at least two known workloads, such as same geometry with increased fragment work and increased geometry with small pixel coverage, and compare delayed query, wall completions and independent GPU activity/counters. Keep query off/on/off controls. If raw query increases monotonically but still cannot account for swap-dependent work, restrict interpretation to measured command segment. No glFinish-in-every-pass acceptance run: serialization changes bottleneck.

Fence/timestamp or a one-off finish before/after final transfer may help localize a dependency if counters unavailable, but perturbs overlap. Label such runs diagnostic and compare shares rather than claiming ordinary frame-time savings. First prefer nonblocking markers and validated counters.

### Gaps

No verified current query result. No evidence yet that query bug, omitted transfer, deferred target flush, SDL internals or vblank independently explains discrepancy. Do not turn a plausible tiler explanation into fact.

## Are Arm tools viable on kernel 4.4 and proprietary r13p0?

### Takeaway

Yes as capability experiments. Kernel age alone does not exclude tools, but installed driver interface and kernel configuration must actually pass.

### Cited Findings

[Arm libGPUCounters](https://github.com/ARM-software/libGPUCounters/tree/847a04a1597d132a3746e9c6374d3977cea89a6d), inspected commit `847a04a1597d132a3746e9c6374d3977cea89a6d`, targets Bifrost-and-later commercial-driver GPUs. Its [device handle](https://github.com/ARM-software/libGPUCounters/blob/847a04a1597d132a3746e9c6374d3977cea89a6d/backend/device/src/device/handle.cpp) opens `/dev/mali0`. [Interface types](https://github.com/ARM-software/libGPUCounters/blob/847a04a1597d132a3746e9c6374d3977cea89a6d/backend/device/src/device/kbase_version.hpp) and [vinstr setup](https://github.com/ARM-software/libGPUCounters/blob/847a04a1597d132a3746e9c6374d3977cea89a6d/backend/device/src/device/hwcnt/sampler/vinstr/setup.hpp#L76) explicitly retain pre-R21 Job Manager counter-setup ioctl path. Not proof target's exact vendor fork accepts it. [G31 counter reference](https://github.com/ARM-software/libGPUCounters/blob/847a04a1597d132a3746e9c6374d3977cea89a6d/docs/mali-g31_counter_reference.html).

[Gator README](https://github.com/ARM-software/gator/blob/f0774012f36dbdb543e082d3e14ca9db20d0432d/README.md#purpose), inspected commit `f0774012f36dbdb543e082d3e14ca9db20d0432d`, supports Linux 3.4+ subject to correct configuration, uses perf/ftrace/debugfs/sysfs and provides ARM64 Linux binaries. Available counters depend on platform and permissions. Current marketing tool/Android support tables do not establish R36S compatibility or incompatibility.

Arm describes [Mali Offline Compiler static shader analysis](https://developer.arm.com/community/arm-community-blogs/b/mobile-graphics-and-gaming-blog/posts/mali-gpu-tools-a-case-study-part-3-static-analysis-with-the-mali-offline-shader-compiler). Static cycle/resource estimates omit scene/runtime effects such as cache misses. G31-target analysis on actual dumped hot shaders can prioritize arithmetic, load/store, varying and precision work; it cannot certify current r13p0 generated code or end-to-end gain.

### Smallest next experiment

Saved device capability probe should enumerate existing Mali device/interface permissions, PMUs, tracepoints and counter reader availability; collect a short idle/load contrast with sampler if usable. Record exact driver/lib hashes, kernel config availability, reader errors and overhead. Start with GPU busy/fragment/tiler activity, external reads/writes, texture behavior and job/dependency scheduling categories exposed by G31 definitions. Never treat unsupported counter as zero. If kernel/driver interface fails, preserve exact error and move to controlled workload scaling plus worker/presentation trace; do not replace firmware/driver as first step.

Any sampler executable must be built in project-compatible ARM64 Docker environment and deployed by saved host/device scripts. No such probe, package install or build happened during this research.

## Which remaining optimizations deserve tests after attribution?

### Takeaway

Rank by evidence. Present/driver/GPU discrimination first. Then select one proven hot pass, hazard or shader. No numerical gain forecast justified yet.

### Ranked candidates and rejection rules

| Priority | Candidate and evidence needed | Smallest functional change | Independent correctness and decision rule |
|---|---|---|---|
| 1 | Remove avoidable presentation cost only if preceding experiments identify it. | Exact 1:1 filter choice, proven redundant clear, dead-attachment invalidate or equivalent final-transfer path, one at a time. | Same true internal/output 640, visual captures from deterministic paused/static scenes, front-buffer semantics/reset/transition checks; warmed repeated cadence and tails improve beyond control variability. Reject any missing frame/effect or gained game speed. |
| 2 | Render-target locality if census shows A→B→A with depth/color reload, oversized auxiliary targets, or copy-to-sampled target dependencies. FBO caching alone does not reduce logical render-pass switches. | Render directly into final sampled texture/mip or consolidate one dependency-safe auxiliary pass. Preserve draw order wherever blend/depth/guest semantics require it. | Replay original draw/pass ordering reference and captured scenes spanning flashlight/shadow/fog/alpha effects. Counter/validated pass time and actual completion improvement both required. Do not assume every bind forces resolve on this driver. |
| 3 | Driver/streamed-resource stall if worker CPU API histogram or trace shows buffer update/allocation/readback waiting. Common texture-subimage payload copying and asynchronous deletion are already implemented. | One bounded ring/orphan/dirty-range experiment only for measured hazardous buffer; or avoid one proven unnecessary synchronous query/readback. | Source-buffer ownership plus GPU completion before reuse; memory bounded over 15 min, room transitions/reload/reset without geometry corruption. Reject if stalls simply move later, frames in flight/input delay grow, or RSS increases unboundedly. |
| 4 | Hot fragment/varying work if pixel-only workload response, pass census or counters shows fragment/load-store pressure. Current generator emits highp defaults; RHW depth emulation writes `gl_FragDepth`; alpha-test/texkill paths can discard. These behaviors preserve legacy rendering. | One hot program's provably redundant operation or narrower safe precision. Consider opaque-alpha-test elision only with texture/palette/opcode/alpha-function proof, not texture opacity alone. | Compare shader output against independent rendering reference across alpha, palette changes, depth-clamp boundaries, fog and lighting; avoid using own generated shader as sole oracle. Static `malioc` result is prioritization only. Extra shader variants must not recreate compile stutter/program-switch cost. |
| 5 | Texture decode/upload if measured recurrent bytes/CPU stalls, not merely large asset size. | One proven unchanged upload removed or one equivalent supported format conversion, retaining all required dirty/palette invalidation. | Current [`res_upload_dirty`](https://github.com/ktodorow/sh3-r36/blob/d4e49600b1022c954baac1965767bb3a5d61b80a/src/d3d8/d3d8_res.c#L418) already avoids clean levels and tracks palette index/version; no blanket upload cache needed. Preserve P8 alpha, compressed decode and mip completeness; measure game-clock, tails and memory. |

Current shader source anchors: [`build`](https://github.com/ktodorow/sh3-r36/blob/d4e49600b1022c954baac1965767bb3a5d61b80a/src/d3d8/d3d8_shader.c#L546), RHW depth comments at 559, alpha-test generation at 589, fragment depth at 594, translated texkill at 311. A CPU reduction and GPU regression can cancel; measure whole frame. Required fog, darkness, flashlight, shadows, transparency and post-effects cannot be dropped and counted as accepted optimization. Reduced scissor/flat shader/feature disable are diagnostic ablations only.

### Already implemented — do not propose again

Sampler/state/attribute/program/viewport/constant caches; active-sampler mask; sampler bind-once; nonpoint `gl_PointSize` omission; bounded vertex constant arrays; DISCARD front-texture rotation; immutable FBO cache; ordered GL worker; owned sampler and texture-upload payloads; program binary cache with driver/source fingerprint; release-before-pacing; corrected overdue timer; queued resource deletion; O3/bounded LTO. Current code/report must be checked before assuming any old proposal remains missing. [Complete issue-14 implementation and chronology](../../reports/issue-14-renderer-caches.md).

## Which comparable ports genuinely inform this investigation?

### Cited Findings

- Current upstream [sh3-nx README, `ff483a6f95b94a4f7924f6fbe4cb47169f2adb98`](https://github.com/cutarev/sh3-nx/blob/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98/README.md) describes AOT CPU recompilation, SDL/OpenGL D3D8 layer and cached first-area shader compilation. [sh2-nx, `7e69609f3a063fbe24c41d6aa560f14ede578746`](https://github.com/cutarev/sh2-nx/blob/7e69609f3a063fbe24c41d6aa560f14ede578746/README.md#settings) separately scales screen-sized render targets; that is useful diagnostic precedent but does not meet this task's true-640 internal criterion. Their Switch/Mesa performance is not RK3326/libMali evidence. No Switch build targets used here.
- Current [PortMaster FNA guide](https://portmaster.games/contribute/porting/engines/fna/#performance-on-a-handheld-gpu) reports a real handheld case where oversized targets, final 1:1 copy and immediate sprite submission caused avoidable work. Relevant lesson: inspect actual allocated dimensions, pass dependencies and same-output alternatives. FNA/Mono game and unspecified Mali differ from SH3/native C/r13p0, so no FPS transfer or universal claim that every target bind resolves.
- First-hand [Halo G31 renderer notes, `e2b0db53e079df7f7cc807e570d3097f9da43edd`](https://github.com/kirklandsig/halo-ce-anbernic-rg35xx/blob/e2b0db53e079df7f7cc807e570d3097f9da43edd/docs/MALI-G31-NOTES.md) distinguish driver draw cost, target copies/stalls, delayed readback, shader output cost and measured negative experiments. They also document buffer-corruption hazards from mixing unsynchronized writes with driver renaming. H700/A53, 648 MHz G31 and r20p0 framebuffer SDL differ from RK3326/A35, 520 MHz and r13p0 KMSDRM. Their timer queries are unavailable; ours are advertised and execute. Their shader/sampler/thread fixes partly overlap work already done here. Use their falsification method and hazard awareness, not their timings or hardware conclusion.
- [Cuphead current measurement section, `1b7e7b019dabeb4226a1b4be5bfdd854895242f5`](https://github.com/wild1walker/portmaster-cuphead/blob/1b7e7b019dabeb4226a1b4be5bfdd854895242f5/docs/technical.md#tests-and-measurements) uses alternating configurations and deterministic screenshots. Good method reference, different Unity runtime and assets. Delver project-specific [working patterns](../Silent%20Hill%203%20R36S%20feasibility/working_port_patterns.md) establish native-GLES integration and measurement patterns, with a 512×384 world-render example that cannot prove this port's 640 target. Public `ktodorow/delverengine-mp` URL returned 404 during current research; local user-owned findings remain historical context.

### Search and retrieval audit

Current official PortMaster guide and primary upstream/Arm/Khronos pages inspected; pinned commit IDs above. Searches included `site:portmaster.games Mali profiling FNA render target copies`, `site:developer.arm.com Mali G31 performance counters Streamline Linux gator proprietary driver`, `site:github.com/cutarev/sh3-nx performance shader slow`, `site:github.com PortMaster Mali G31 glFinish performance`, G31 early-depth/forward-pixel-kill and offline-compiler searches. No first-hand same-binary SH3 R36S hardware-counter or final-Present attribution report found beyond this repository's runs.

Old Mali Offline Compiler landing URL redirected to one-line support redirect; used Arm's detailed primary static-analysis article instead. A guessed `JeodC/PortMaster-Cuphead` URL returned 404; correct `wild1walker/portmaster-cuphead` fetched at pinned current commit. No clones, downloaded executable helpers or third-party scripts executed. No prompt-injection instructions observed in research content; external prose and commands treated as data.

Project CCE `session_recall` and `context_search` used first. Several current-code searches returned stale `.port-cache` builds or header-only 300-character chunks; `expand_chunk` returned `Chunk not found` on matching GPU profiler result. Exact known current files subsequently inspected using `git show HEAD:<path>` at pinned source commit. One guessed `src/runtime/graphics.c` path did not exist; CCE then located current `src/win32/user32.c` and known `src/d3d8/gl.c`/`d3d8.c` context initialization. Source conclusions above come from exact current source, not stale cache previews.
