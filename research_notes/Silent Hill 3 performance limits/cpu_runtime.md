# Silent Hill 3 R36S: current CPU, runtime and build limits

Research date: 2026-11-15. Research only; no runtime, script, test, spec, build, device or tracker changes. Documentation adds no executable behavior, so TDD does not apply. Future implementation retains installed launcher → actual game → frontend boundary and observed RED–GREEN–REFACTOR cycles; numerical replacements additionally need independent original-x86 evidence. [Project rules](../../AGENTS.md), [canonical spec](../../docs/specs/silent-hill-3-r36s.md), [issue 13](https://github.com/ktodorow/sh3-nx-r36s/issues/13).

Baseline qualification: initial sections analyze November14 performance-policy runs. November15 repeat exposed different CPU/GPU/DMC governors; final addendum supersedes any assumption that current launch automatically reproduces earlier clocks. Neither governor owner nor supported stock maxima are established by five-second frequency samples. [Fresh policy evidence](measurement_plan.md).

## What does current evidence establish about CPU limit and missing critical path?

### Takeaway

Current producer spends about28.7ms CPU per frame at either resolution; true640 incurs extra backpressure while producer draw work stays nearly unchanged. This establishes substantial resolution-dependent work downstream, without identifying whether worker driver CPU, GPU execution, display synchronization or lost overlap causes it. Old42ms CPU /13FPS evidence cannot describe current binary. [Final comparison](../../reports/issue-13-performance.md), [measurement notes](measurement_plan.md), [profiler source](../../src/d3d8/profile.c:90).

### Cited Findings

- Frozen build `20261114T044419879221Z`, runtime SHA256 `2ac6b9c02579ff37d20a920edde36a203458aeded0806f9e86ffecf4bc512ff9`, contains O3, bounded LTO, renderer caches, owned async uploads/deletes, program cache and repaired elapsed-tick pacing. Final matched park route75–180s gives640internal/640output23.196638FPS versus320internal/640output29.990378FPS capped30. Average640 completion interval is therefore43.1097ms;30FPS requires33.3333ms, roughly9.7764ms less average interval or29.3% more throughput. This arithmetic is a target gap, not attribution or a speedup forecast. [Build commands](../../.port-cache/builds/20261114T044419879221Z/compile_commands.json), [build identity](../../.port-cache/builds/20261114T044419879221Z/artifacts/runtime/artifacts.sha256), [final report](../../reports/issue-14-renderer-caches.md:1137).
- Same matched window, fresh CSV analysis: producer CPU p50 about28.70ms640 /28.66ms320; producer accumulated draw wall time about3.35ms both; producer Present p50 about13.70ms640 /0.024ms320; actual worker SDL swap p50 about29.49ms640 /12.44ms320. These medians overlap and come from distinct scopes; do not add them to reconstruct frame. No `.gpu.csv` exists for either pair. [640 producer CSV](../../r36s-dumps/sh3/20261114T055246314042Z-4068d8/launcher/frame-times.csv), [640 worker completions](../../r36s-dumps/sh3/20261114T055246314042Z-4068d8/launcher/frame-times.csv.presents.csv), [320 producer CSV](../../r36s-dumps/sh3/20261114T050230071532Z-0ddc92/launcher/frame-times.csv), [320 worker completions](../../r36s-dumps/sh3/20261114T050230071532Z-0ddc92/launcher/frame-times.csv.presents.csv).
- `profile_present()` uses `CLOCK_THREAD_CPUTIME_ID` on producer, between successive producer Presents. It measures on-CPU execution, including producer renderer preparation and profiling overhead; excludes CPU consumed by GL worker and all other threads. Draw timers measure producer-side wall duration around draw preparation/recording, potentially including queue waits; they do not measure completed GL or GPU time. [Frame profiler](../../src/d3d8/profile.c:11), [draw timer](../../src/d3d8/profile.c:36), [producer CPU interval](../../src/d3d8/profile.c:90).
- Existing PC sampler binds CPU-time timer to calling producer TID, samples PC and one LR every10ms of its CPU time, stores at most32768 records, and writes through orderly exit. It has no full stack, absolute sample timestamp, worker registration or late-window trigger. Full current640/320 runs contain8649/11044 samples, reported dropped1/6 and no write failure; these short runs do not hit buffer limit. Earlier long-run buffer saturation remains relevant to late soak attribution only. [Sampler](../../src/d3d8/profile_cpu.c:1), [640 sampler output](../../r36s-dumps/sh3/20261114T055246314042Z-4068d8/launcher/frame-times.csv.samples), [320 sampler output](../../r36s-dumps/sh3/20261114T050230071532Z-0ddc92/launcher/frame-times.csv.samples), [historical soak limitation](../../reports/issue-14-renderer-caches.md).
- GL worker owns one context. Producer records into three minimum8MiB command chunks; publication occurs at swap, synchronous command, or capacity pressure. Worker executes published commands in order; swap submission waits only when more than one frame would remain ahead. Worker signals actual swap completion before existing absolute-phase30FPS sleep, so restoring this overlap is already implemented. [Worker and chunk state](../../src/d3d8/gl_thread.c:1), [sync command](../../src/d3d8/gl_thread.c:122), [swap and pacing](../../src/d3d8/gl_thread.c:396), [observed overlap RED/GREEN](../../reports/issue-14-renderer-caches.md:969).
- Queue sync timing starts before queued barrier is published and includes draining preceding work plus condition wait. It is not duration of named GL function alone. Current640 shutdown totals include51 texture-generation waits444.923ms,61 texture-allocation waits46.916ms,47 program-binary waits48.262ms and one readback38.592ms;320 totals are372.143/38.064/49.367/14.066ms respectively. All are startup-inclusive and cannot establish recurrent warm bottleneck. [Queue implementation](../../src/d3d8/gl_thread.c:122), [640 runtime log](../../r36s-dumps/sh3/20261114T055246314042Z-4068d8/launcher/stderr.txt), [320 runtime log](../../r36s-dumps/sh3/20261114T050230071532Z-0ddc92/launcher/stderr.txt).
- Optional GPU timing already exists. Historical native diagnostic reports query p50 about0.892ms while actual SDL swap p50 about36.739ms, with slower diagnostic throughput than immediately preceding query-off candidate. Region ends before SDL swap; small query values cannot prove unused GPU capacity. Ordinary acceptance leaves query disabled. [GPU experiment](../../reports/issue-14-renderer-caches.md:594), [timing placement](../../src/d3d8/gl_thread.c:423).
- Timer repair previously raised hospital floor21→29FPS without reducing producer CPU: same slow segment changed CPU median32.737→33.270ms. Native 15-minute final hospital later passed specified cadence floor at320internal; true640 final comparison still fails. Timing/queue wait policy can move cadence without changing arithmetic cost; previous gain does not license further game-clock changes. [Timer evidence](../../reports/issue-14-renderer-caches.md:1067), [final hospital and640 evidence](../../reports/issue-14-renderer-caches.md:1163).

### Inferences

- First experiment should record common-clock frame timeline: producer work start/end; each chunk publish and sequence; worker start/end plus worker CPU delta; every synchronous wait begin/end with queue depth; swap entry/return; deliberate pacing; actual completion identity. This can distinguish worker on-CPU driver work, producer starvation, queued work and blocked swap. Retain one-frame bound and current30FPS policy. Existing producer/swap CSVs cannot answer this alone. [Source basis](../../src/d3d8/gl_thread.c:1), [current scopes](../../src/d3d8/profile.c:90).
- Whole-frame publication can leave worker/GPU idle until producer finishes recording when no earlier barrier fills/publishes a chunk. Earlier publication is therefore a conditional overlap candidate, with measurement prerequisite: actual repeated idle gaps followed by unsent work. Blindly shrinking chunks could add wakeups, lock contention and driver submission overhead. If worker already has queued work through slow frames, reject this hypothesis. [Publication basis](../../src/d3d8/gl_thread.c:1).
- About28.7ms producer CPU leaves only about4.6ms nominal margin inside33.33ms, but is neither proven producer floor nor proven whole-frame critical path. A CPU optimization may add margin without improving640 if worker remains limiting. Conversely producer acceleration can help if submission starvation is measured. Capped320 throughput cannot estimate unconstrained CPU ceiling. [Current CSVs](../../r36s-dumps/sh3/20261114T055246314042Z-4068d8/launcher/frame-times.csv), [queue contract](../../src/d3d8/gl_thread.c:433).
- Attribute current640 gap downstream before prioritizing old x87 microbenchmarks. Distinguish busy worker driver code from blocked swap using worker CPU clock plus samples. More threads alone do not change single-context ordering or prove spare-core parallelism applies. [Worker ownership](../../src/d3d8/gl_thread.c:44), [producer-only sampler](../../src/d3d8/profile_cpu.c:73).

### Gaps

- No current common-clock producer/worker/driver/GPU/display timeline; no direct panel-present timestamps; no warm frame-level queue-barrier totals. Worker lifetime `%CPU` from existing monitoring cannot substitute for interval CPU measurements. [Measurement notes](measurement_plan.md).
- No actual late-scene per-thread stack sample on final hospital soak. No current critical-path proof that faster producer arithmetic alone raises640 throughput. [Sampler limitation](../../src/d3d8/profile_cpu.c:1), [final report](../../reports/issue-13-performance.md).

## Which CPU functions remain hot on exact current build, and what can safely replace them?

### Takeaway

Fresh exact-build producer samples still identify matrix, wrapped field/geometry routines, integer conversion and signed-byte filtering. They offer concrete native-kernel candidates, with several percent of producer CPU each. Standalone `round24` hotspot ranking from older build is stale; present samples never land in its remaining out-of-line copies. These samples do not measure worker or establish enough whole-frame savings for640. [Current640 samples](../../r36s-dumps/sh3/20261114T055246314042Z-4068d8/launcher/frame-times.csv.samples), [current320 samples](../../r36s-dumps/sh3/20261114T050230071532Z-0ddc92/launcher/frame-times.csv.samples).

### Cited Findings

Current symbolization performed read-only against retained debug ELF. Runtime SHA256 matches above; debug SHA256 `776a191a13cf7c8473f60c67122dd2dd716582737044d2ed5317d71a5b026f89`. Both share GNU build ID `0a288023bd2de46f50d59ccbe9b70593c411ce63`; executable `.gnu_debuglink` CRC `0x264fe273` equals independently calculated debug-file CRC. ELF64 little-endian `.symtab` contains12854 defined nonempty function intervals. Each sampled module offset mapped only if inside `[st_value, st_value+st_size)`. External modules retained separately. Frame IDs joined to producer CSV; selected `75000 <= elapsed_ms < 180000`. No build, installed executable, dependency download or device access used. [Runtime ELF identity](../../.port-cache/builds/20261114T044419879221Z/artifacts/runtime/elf.txt), [matched debug ELF](../../.port-cache/builds/20261114T044419879221Z/artifacts/runtime/sh3.debug), [raw640 input](../../r36s-dumps/sh3/20261114T055246314042Z-4068d8/launcher/frame-times.csv.samples), [raw320 input](../../r36s-dumps/sh3/20261114T050230071532Z-0ddc92/launcher/frame-times.csv.samples).

Selected640 has7034 samples (6662 executable,119SDL,170libc,20libm,63vDSO), corresponding to70.340529s summed producer CPU. Selected320 has9052 (8603 executable,102SDL,259libc,31libm,57vDSO), corresponding to90.527476s CPU. Near10ms-per-sample agreement is consistency check, not independent measurement of sampling overhead. Selected640 frames1975–4409 correspond75.035–179.964s;320 frames2112–5260 correspond75.027–179.995s. Percentages below divide by all selected producer samples, not just executable samples. [640 frame CPU](../../r36s-dumps/sh3/20261114T055246314042Z-4068d8/launcher/frame-times.csv), [320 frame CPU](../../r36s-dumps/sh3/20261114T050230071532Z-0ddc92/launcher/frame-times.csv), [sampler assignment](../../src/d3d8/profile.c:116).

| Current leaf/function interval | 640 samples / share | 320 samples / share | Source-level meaning established |
| --- | ---: | ---: | --- |
| `sub_00648639` |513 /7.29%|782 /8.64%|4×4 matrix products, precise per-operation rounding, alias-dependent scratch. [Source](../../src/recomp/gen/recomp_0040.c:21436) |
| `sub_00478AC0` |402 /5.72%|551 /6.09%|Repeated coordinate floor/integer conversion, wrapped8×8×8 float-field reads/writes at `0xBCC7A0` / `0xBCCFA0`; broader semantic owner unproven. [Source](../../src/recomp/gen/recomp_0010.c:19987) |
| `sub_00479E30` |316 /4.49%|387 /4.28%|Updates records with stride `0x60`, float/integer transforms and projected vertex/color output. Effect identity unproven. [Source](../../src/recomp/gen/recomp_0010.c:22303) |
| `sub_00662C40` |289 /4.11%|424 /4.68%|Consumes x87 stack value,64-bit integer conversion and sign/fraction correction; not matrix work. [Source](../../src/recomp/gen/recomp_0042.c:11835) |
| `sub_004464E0` |287 /4.08%|400 /4.42%|Signed-byte neighborhood filter with16-bit scratch, arithmetic shifts and endpoint handling. [Source](../../src/recomp/gen/recomp_0006.c:19322) |
| `sub_00648491` |202 /2.87%|252 /2.78%|Related generated numeric routine; exact replacement contract still needed. [Source file](../../src/recomp/gen/recomp_0040.c) |
| `sub_004F3300` |190 /2.70%|215 /2.38%|Function identity only; semantic owner not established. [Current samples](../../r36s-dumps/sh3/20261114T055246314042Z-4068d8/launcher/frame-times.csv.samples) |
| `sub_004F26D0` |185 /2.63%|213 /2.35%|Function identity only; semantic owner not established. [Current samples](../../r36s-dumps/sh3/20261114T055246314042Z-4068d8/launcher/frame-times.csv.samples) |
| `shader_bind_for_draw` |220 /3.13%|173 /1.91%|Producer-side renderer preparation remains visible after state caches. [Current samples](../../r36s-dumps/sh3/20261114T055246314042Z-4068d8/launcher/frame-times.csv.samples) |
| `draw_setup` |156 /2.22%|202 /2.23%|Producer-side draw preparation. [Current samples](../../r36s-dumps/sh3/20261114T055246314042Z-4068d8/launcher/frame-times.csv.samples) |
| `upload_pixels` |71 /1.01%|192 /2.12%|Producer pixel preparation/copy; already-owned async upload does not eliminate preparation. Different realized route progression/call counts constrain cross-resolution share comparisons. [Current samples](../../r36s-dumps/sh3/20261114T055246314042Z-4068d8/launcher/frame-times.csv.samples), [async upload source](../../src/d3d8/gl_thread.c:285) |

- Remaining ELF has23 `recomp_fp_round24.lto_priv.*` copies,132bytes each. Neither selected current run samples their PC ranges. This does not prove helper cost zero: inline expansion, cold-path outlining, changed call frequency or sampled attribution can hide it inside callers. Old helper sample share must not be added to current matrix share. [Exact debug ELF](../../.port-cache/builds/20261114T044419879221Z/artifacts/runtime/sh3.debug), [current helper](../../third_party/xboxrecomp/templates/runtime/recomp_types.h:273), [historical CPU roadmap](../Silent%20Hill%203%20optimization%20roadmap/cpu_runtime.md).
- Stored LR is not reliable inclusive stack:372 of402 current640 field-routine PC samples have LR inside same routine, which can reflect last nested call's return address rather than recursion or true caller. For signed filter, all287640 /400320 sampled LRs locate `sub_00446B30`, whose source repeatedly invokes row filter. For integer helper,640 LRs locate `sub_00479E30`101 times, `sub_00478AC0`70, `sub_0047ABB0`38, among other sites. This is provenance, not inclusive cost or full call count. [Current sampler](../../src/d3d8/profile_cpu.c:20), [row driver](../../src/recomp/gen/recomp_0006.c:20448), [integer-helper call sites](../../src/recomp/gen/recomp_0010.c:19987).
- Matrix evaluates four multiply results and three sums per output with `RECOMP_FP_PC` after each, manipulates thread-local x87 stack and preserves special alias paths with guest scratch. Ordinary-range helper is already float conversion; exceptional magnitudes preserve wider exponent via `frexp`/`ldexp`. Replacing whole helper by float cast or using fused/reassociated matrix multiply changes semantics. [Matrix](../../src/recomp/gen/recomp_0040.c:21436), [helper](../../third_party/xboxrecomp/templates/runtime/recomp_types.h:273).
- Current oracle captures x87 top plus64 stack bytes, but Python loader skips those64 bytes, restores only integer state/segments, and does not capture/restore guest FP control word. It prints mismatches without explicit failing exit on any mismatch. It cannot yet prove numerical replacement correct independently. [Capture](../../src/runtime/rt_core.c:259), [replay](../../tools/oracle.py:22), [result handling](../../tools/oracle.py:95).
- Manual function routing already supports exact guest-VA overrides; flat dispatch already exists. Unconditional thread-local volatile crash-ring writes remain in ordinary indirect-call macros even when feedback instrumentation is disabled. These are possible measured costs, not permission to remove crash evidence globally or replace dispatch again. [Manual seam](../../src/game/sh3.c:185), [ICALL macros](../../third_party/xboxrecomp/templates/runtime/recomp_types.h:982), [historical dispatch review](../Silent%20Hill%203%20optimization%20roadmap/cpu_runtime.md).

### Inferences

- Start numerical work with oracle correctness, then one scalar-native kernel preserving original operation order, guest memory/register/FPU effects and alias behavior. Only after scalar win and equivalence add NEON lanes across independent outputs, maintaining each lane's multiply/add sequence and explicit exceptional/control fallback. Representative real inputs plus adversarial original-x86 cases must cover signs/zeros, ties, integer boundaries, NaN/infinity, exceptional exponents, PC/RC modes and aliasing. Existing double-backed x87 approximation should remain explicit; new optimization must not silently worsen it. [Oracle gap](../../tools/oracle.py:22), [matrix semantics](../../src/recomp/gen/recomp_0040.c:21436), [project numerical requirements](../Silent%20Hill%203%20optimization%20roadmap/cpu_runtime.md).
- Matrix is best isolated first candidate by current leaf rank and compact contract, but eliminating its entire observed7.29% producer leaf work would illustrate only about2.1ms of28.7ms producer CPU, assuming same workload and no other changes. Real optimization saves less of this own work; downstream throughput gain remains unknown. A matrix-only story cannot substantiate full9.78ms average completion gap. [Fresh samples above](../../r36s-dumps/sh3/20261114T055246314042Z-4068d8/launcher/frame-times.csv.samples).
- Wrapped field + geometry + conversion form another concrete cluster, potentially larger than matrix alone. First capture exact owners/controls/input ranges and conversion call frequency; then specialize hot complete caller region, avoiding repeated emulated-stack traffic and floor→integer helper boundaries while preserving bit results. Do not replace global conversion with C cast: exceptional range, signed64 result split, rounding policy and x87 stack effects matter. Do not label cluster fog or disable it until provenance independently established. [Field source](../../src/recomp/gen/recomp_0010.c:19987), [geometry source](../../src/recomp/gen/recomp_0010.c:22303), [conversion source](../../src/recomp/gen/recomp_0042.c:11835).
- Filter candidate has simpler integer oracle than matrix but still requires signed-byte extension,16-bit wrap, arithmetic right shifts, edges, dimensions, overlap and row order. Its clear current parent identifies row/plane batching seam. Native scalar then vectorized row loop may cut translated bookkeeping; visual effect and temporal update cannot be dropped. [Filter](../../src/recomp/gen/recomp_0006.c:19322), [parent](../../src/recomp/gen/recomp_0006.c:20448).
- GPU offload is later architecture option only for proven render-only batches whose outputs remain GPU-resident. Matrix currently writes guest memory synchronously and has varied callers; dispatch/readback per matrix adds synchronization and cannot serve CPU consumers transparently. Broad parallel simulation or indiscriminate offload is unsupported by present call contracts. [Matrix contract](../../src/recomp/gen/recomp_0040.c:21436).

### Gaps

- PC function intervals do not resolve inline source lines or full inclusive call tree. No worker samples or repeated-current-run confidence intervals; route progresses differently when slower. Parent function names alone do not prove effects/collision/audio ownership. [Sampler](../../src/d3d8/profile_cpu.c:1).
- No independently validated numeric oracle, actual control/range distribution, call counts, scalar-native timing or NEON prototype on current native hardware. These are next measurements, not existing optimization gains. [Oracle](../../tools/oracle.py:1), [original roadmap](../Silent%20Hill%203%20optimization%20roadmap/cpu_runtime.md).

## What remains in compiler, PMU and comparable-port research?

### Takeaway

Current build already targets Cortex-A35 with O3 and bounded LTO; repeating these as new fixes would waste work. Remaining compiler experiments should answer measured instruction/code-layout limits, with profile training on real representative routes. PMU is useful conditional capability, never assumed from core type or absence of installed `perf`. [Build guide](../../docs/agents/builds.md), [current compile commands](../../.port-cache/builds/20261114T044419879221Z/compile_commands.json).

### Cited Findings

- Exact current69 compile commands use GCC12.2, `-mcpu=cortex-a35 -O3 -g -DNDEBUG -fwrapv -fno-strict-aliasing -flto=2`; saved native build repeats wrap/noalias at link. O3 previously produced bounded improvement in some scenes; LTO alone did not establish faster hospital result. No global fast-math, FMA reassociation or host-native tuning needed. Reuse existing project Docker ARM64 environment; no new environment justified by present ABI. [Compile commands](../../.port-cache/builds/20261114T044419879221Z/compile_commands.json), [native builder](../../scripts/build/native.sh:1), [build guide](../../docs/agents/builds.md), [bounded LTO result](../../reports/issue-14-renderer-caches.md:1043).
- GCC profile-use can alter function layout, inlining, branches, cloning and loop decisions, and reports profile/source mismatches. Instrumented profile updates need thread-safe mode when shared; `-fprofile-update=atomic` / `prefer-atomic` exist, profile path normalization matters, and detached/unjoined threads can still corrupt output. Sampling AutoFDO requires supported perf data; it is not automatically usable here. [GCC12 optimize options](https://gcc.gnu.org/onlinedocs/gcc-12.2.0/gcc/Optimize-Options.html), [GCC12 instrumentation](https://gcc.gnu.org/onlinedocs/gcc-12.2.0/gcc/Instrumentation-Options.html).
- Linux `perf_event_open` supports per-thread monitoring without installed `perf` frontend. Existence of `perf_event_paranoid` indicates kernel interface; event-source sysfs and actual successful opens establish available counters. Permission, event support, enabled/running time and multiplexing all require checks. Modern `CAP_PERFMON` dates Linux5.8 and is not assumption for recorded4.4.189 kernel. [Linux perf interface](https://man7.org/linux/man-pages/man2/perf_event_open.2.html), [device kernel record](../../reports/issue-13-performance.md).
- Linux v4.4 source has generic ARMv8 PMUv3 driver plus A53/A57 device bindings, maps cycles, instructions, branch misses and generic cache metrics; generic `CACHE_MISSES` there maps L1D refills, not universal last-level misses. This source does not establish downstream R36S kernel configuration, PMU device-tree wiring, permissions or each raw event. Cortex-A35-specific stall events cannot be inferred from A53 examples. [Linux v4.4 PMU source](https://github.com/torvalds/linux/blob/v4.4/arch/arm64/kernel/perf_event.c#L79), [driver bindings](https://github.com/torvalds/linux/blob/v4.4/arch/arm64/kernel/perf_event.c#L609).
- Current official PortMaster build guide recommends Ubuntu22.04/glibc2.35, or older baseline for older firmware; binary requires device glibc at least build baseline. Project Debian12/glibc2.36 against recorded device2.41 already passes actual native ABI gates. FNA/Mono advice does not tune native generated C. [Official build guide](https://portmaster.games/contribute/porting/build-environments/), [official FNA guide](https://portmaster.games/contribute/porting/engines/fna/), [project ABI evidence](../../docs/agents/builds.md).

Current primary sources checked2026-11-15; external instructions treated as untrusted research and none executed:

| Source / exact reference | Useful finding and applicability |
| --- | --- |
| SH3 default head `ff483a6f95b94a4f7924f6fbe4cb47169f2adb98` | Unchanged since prior roadmap. Maintainer confirms LinuxARM64 builds but has no ARM Linux device result himself; no ready R36S CPU patch in read issue. Same native recompiler ancestry; Switch runtime/GPU differs. [Commit](https://github.com/cutarev/sh3-nx/commit/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98), [full first-hand issue5](https://github.com/cutarev/sh3-nx/issues/5) |
| SH2 default head `7e69609f3a063fbe24c41d6aa560f14ede578746` | Unchanged since prior roadmap. Maintainer reverted60FPS after timing/gameplay problems; Switch overclock result cannot establish R36S30 or justify game-speed edits. [Commit](https://github.com/cutarev/sh2-nx/commit/7e69609f3a063fbe24c41d6aa560f14ede578746), [full issue13](https://github.com/cutarev/sh2-nx/issues/13) |
| Cuphead current head `1b7e7b019dabeb4226a1b4be5bfdd854895242f5`; prior inspected launcher `a2e39b5bc192e7bee2d2655a324355c0b9b994b7/pm/cuphead/Cuphead.sh` | Recent porter release identifies muOS/H700 idle288MHz during long setup. Useful lesson: capture clocks/state. Earlier SH3 runs sampled1512/520 throughout; November15 policy change makes capability/restore investigation relevant, not blind import of another firmware's settings. Unity Android/Mono setup and texture encoding differ from SH3 native runtime. [Current commit](https://github.com/wild1walker/portmaster-cuphead/commit/1b7e7b019dabeb4226a1b4be5bfdd854895242f5), [first-hand release](https://github.com/wild1walker/portmaster-cuphead/releases), [pinned launcher](https://github.com/wild1walker/portmaster-cuphead/blob/a2e39b5bc192e7bee2d2655a324355c0b9b994b7/pm/cuphead/Cuphead.sh) |
| Delver current remote head `1ed02aa970d062fdc524d0d4aac52e34fe2e4e2b`; spec-linked inspected baseline `9083f5e9c23b63fdc67ae2ce4cbeb374692d10be` with local R36S work | Applicable launcher/frontend and native-GLES integration patterns already recorded; Java17/libGDX/LWJGL differs from static-recompiled SH3. New remote commit concerns campaign lifecycle, not evidence of CPU speed fix. User-supplied local reference and its uncommitted work left untouched. [Current commit](https://github.com/ktodorow/delverengine-mp/commit/1ed02aa970d062fdc524d0d4aac52e34fe2e4e2b), [full working-port applicability](../Silent%20Hill%203%20R36S%20feasibility/working_port_patterns.md) |
| SH3proxy first-hand timer analysis, wiki last edited2017-08-06 | Original SH3 integral animation increments and divisors-of60 pacing can create step drops. Supports measuring clock/waits; current bounded repair already passed behavior tests. Windows hook implementation is not drop-in native Linux/A35 code and no spin policy adopted. [Full author explanation](https://github.com/07151129/sh3proxy/wiki/On-FixJitter-and-lag-compensation), [current repaired behavior](../../reports/issue-14-renderer-caches.md:1067) |

### Inferences

- Optional PMU probe should request own-thread user-space counters, begin with cycles+instructions, report all errors/availability and time enabled/running. If supported, add verified L1I refills/ITLB versus L1D/cache events and branch misses in separate small groups. Pair counters with exact frame windows and worker/producer identity; otherwise instruction growth, code-cache pressure and data-copy stalls remain conjecture. Do not install system tools, alter permissions, replace kernel/firmware or assume unsupported raw events. Saved host/device workflow and Docker ARM64 helper still required before any future probe. [Perf contract](https://man7.org/linux/man-pages/man2/perf_event_open.2.html), [kernel event meaning](https://github.com/torvalds/linux/blob/v4.4/arch/arm64/kernel/perf_event.c#L79), [device workflow](../../scripts/README.md).
- PGO is bounded later experiment: train actual native device across park combat, warm hospital, distinct levels and transitions; orderly stop, retain raw profiles; apply same sources, toolchain and explicit semantic flags, reject missing/mismatch profiles. Compare new profile-use binary with currentO3/LTO through same real routes, both resolutions and hot cadence; training binary speed is not candidate speed. If instrumenting entire1.6M-line generated source is too disruptive, GCC file filtering can narrow measured hot translation units while recording untrained coverage gaps. [GCC training controls](https://gcc.gnu.org/onlinedocs/gcc-12.2.0/gcc/Instrumentation-Options.html), [existing build discipline](../../docs/agents/builds.md).
- If PMU/disassembly identifies instruction fetch pressure, compare selective no-inline/cold outlining or profile-guided layout against currentLTO. If it identifies data misses/copy cycles, focus data preparation and payload copies instead. Blind global `always_inline`, newest compiler, `-Ofast` or repeatedO3 are not research answers. Preserve exact semantics and measure whole-frame result; no guaranteed compiler gain. [GCC optimization tradeoffs](https://gcc.gnu.org/onlinedocs/gcc-12.2.0/gcc/Optimize-Options.html), [current flags](../../scripts/build/native.sh:1).

### Gaps

- No actual current device PMU open result inspected; old notes report unavailable `perf` command, which does not settle kernel PMU access. No reliable R36S per-event stall breakdown or current assembly-line attribution. [Prior measurement research](../Silent%20Hill%203%20optimization%20roadmap/measurement_acceptance.md).
- Current upstream/default refs checked through read-only GitHub API after browser API URLs failed; no new reference clone or downloaded executable used. No reproducible independent SH3/RK332630FPS CPU result found in searched primary sources. Searches included PortMaster profiling/native CPU, SH3 performance/recomp issues, SH2 FPS/math, Cortex-A35 PMU/Linux, and current official build/FNA guides. [SH3 issue evidence](https://github.com/cutarev/sh3-nx/issues/5), [prior search/applicability record](../Silent%20Hill%203%20optimization%20roadmap/cpu_runtime.md).

## Which interventions deserve first experiments and clear rejection rules?

### Takeaway

Measure present critical path first; then optimize measured worker/queue or producer kernels, one bounded behavior per slice. Current640 has measurable target gap, not demonstrated immutable hardware ceiling. A valid negative result identifies what failed to help under recorded conditions; it does not prove every approach impossible. [Current evidence](../../reports/issue-13-performance.md), [canonical acceptance](../../docs/specs/silent-hill-3-r36s.md).

### Cited Findings

- Full old CPU roadmap and renderer implementation addenda show already completed changes: O3/LTO, hot renderer caches, async sampler/upload/delete ownership, uniform bounds, snapshot rotation, binary cache, actual swap completion accounting, release-before-throttle overlap and overdue timer consumption. Historical proposed order predates these implementations and needs revision. [CPU roadmap and addenda](../Silent%20Hill%203%20optimization%20roadmap/cpu_runtime.md), [full renderer history](../../reports/issue-14-renderer-caches.md).
- Existing required behavior includes actual game speed, collision/fire cadence, preserved essential visual effects, audio/lifecycle and actual sustained R36S acceptance. New fixture or microbenchmark pass cannot substitute. [Spec](../../docs/specs/silent-hill-3-r36s.md), [issue9 evidence](https://github.com/ktodorow/sh3-nx-r36s/issues/9), [issue6 evidence](https://github.com/ktodorow/sh3-nx-r36s/issues/6).

### Inferences

| Priority | Minimal experiment | What would justify follow-up | Reject or defer when |
| --- | --- | --- | --- |
| P0: common-clock critical-path capture | Short matched true640/320; per-frame producer/worker CPU, chunk publication/queue depth, waits, actual completion; diagnostic-off control. Retain input/state/clocks and output640. [Source seam](../../src/d3d8/gl_thread.c:1) | Repeat slow-frame timeline identifies producer starvation, worker CPU, recurring barrier or downstream swap wait. | Observer changes cadence materially, phases lack frame identity, or only startup totals available. Repair measurement first. |
| P1a: publish overlap, conditional | If P0 finds unsent ready work while worker idle, publish at measured dependency-safe render boundary using existing ordered chunks; same bound/context. [Queue seam](../../src/d3d8/gl_thread.c:1) | Repeated640 completion improvement, no extra CPU/buffer churn, input-latency/behavior intact. | Worker already busy, added wakeups cost more, or latency/ordering/pixels worsen. Completion-before-pacing fix is already done. |
| P1b: worker CPU/remaining barrier, conditional | Target one repeated warmed output/allocation barrier or driver preparation site from P0, preserving return/dependency semantics; reuse existing ownership design. [Barrier seam](../../src/d3d8/gl_thread.c:122) | Critical-path wait shortens while correct returned objects/readbacks and textures remain. | Only startup shader/gen totals support hypothesis, or wait merely shifts to next call. Common subimage/deletes already async. |
| P1c: exact scalar matrix | Fix original-x86 FP oracle, capture representative inputs/control/alias cases, then override one VA with scalar-native same-order operations. [Manual seam](../../src/game/sh3.c:185), [matrix](../../src/recomp/gen/recomp_0040.c:21436) | Bit/state equivalence plus lower native producer cost and real frame margin; only then test NEON. | Oracle incomplete, rare exception/alias mismatch, code size worsens cadence, or upstream worker limit prevents640 gain. Retain only justified margin gain. |
| P2a: field/conversion caller kernel | Attribute field owner, sample counts/ranges, prove complete region, eliminate emulated-stack/conversion boundaries with exact result checks. [Field](../../src/recomp/gen/recomp_0010.c:19987), [integer conversion](../../src/recomp/gen/recomp_0042.c:11835) | Original-x86 equivalence across boundary values and consistent native cost reduction. | Needs skipping visual effect, approximate math, changed update rate or unvalidated global C cast. |
| P2b: signed filter row | Exact integer oracle plus scalar-native one-row replacement; later independent-lane NEON with same endpoints/alias order. [Row driver](../../src/recomp/gen/recomp_0006.c:20448) | Lower measured current native cost without pixel/guest-memory change. | Work belongs only to loads, shares scratch across unsafe parallel calls, or normal route cost too small. |
| P3: PGO/layout | Capability check PMU if available; representative real training, same source/ABI, test profile-use artifact. [GCC](https://gcc.gnu.org/onlinedocs/gcc-12.2.0/gcc/Instrumentation-Options.html) | Repeat whole-route benefit with diagnostics off and no uncovered-scene regression. | Profiles mismatched/unrepresentative, code growth harms tails, or gain only in training microbenchmark. |
| P4: dispatch/crash-ring or broad simulation parallelism | Revisit only if current inclusive profile/counters show material indirect-call/bookkeeping or separable independent workload. [ICALL](../../third_party/xboxrecomp/templates/runtime/recomp_types.h:982) | Correctness/diagnostics maintained and cost reduction survives real routes. | Based on old binary sample rank, assumes guest global state thread safe, or removes required debugging evidence for tiny unmeasured gain. |

Every accepted candidate must return to true640 warmed and first-visit routes, sustained hot heavy scene, tail/window floor, game-clock ratio, actual action state, visible fog/flashlight/transparency and audio continuity. Preserve320 comparison as control; it is not fulfillment of true640 criterion. No accepted setting can silently redefine resolution to claim native640. [Spec and current acceptance limits](../../docs/specs/silent-hill-3-r36s.md), [performance report](../../reports/issue-13-performance.md).

### Gaps

- No new implementation or measurement capability passes created by this research. Recommendations are conditional experiments; none carries speedup guarantee or closes issue13. [Research scope](../../AGENTS.md).
- Project CCE `session_recall` and `context_search` used before exploration. Retrieval mostly returned300-character headers, cached historical dumps and missing generated-source bodies; `expand_chunk("src/d3d8/gl_thread.c:1")` returned `Chunk not found`. Exact known-source reads supplied current code. After exact new-function search failed to return source, scoped exact-name `rg` located generated bodies. No external instructions followed, no clone needed, no device access and no private configuration values recorded. [Project CCE rules](../../AGENTS.md).

## Critical-gap addendum: can a reversible stock-policy comparison explain fresh slowdown?

### Takeaway

Fresh repeat is not directly comparable with November14 baseline: same binary now starts under demand-based CPU/GPU/DMC governors. Establish policy ownership and current supported limits before any write. A later, reversible governor-only experiment can test available performance at unchanged stock limits; it cannot establish30FPS feasibility by itself. No governor write, helper invocation or script change performed in this research. [Fresh measurements](measurement_plan.md), [canonical scope](../../docs/specs/silent-hill-3-r36s.md).

### Cited Findings

- November15 query-off run reports17.6796FPS; monitoring begins before runtime with CPU `ondemand` at1248MHz, GPU `simple_ondemand` at400MHz and DMC `dmc_ondemand` at528MHz. Twenty samples show CPU1008–1512MHz, GPU400MHz eighteen times/480MHz twice, DMC528MHz throughout and maximum sampled59.545°C. November14 matched pair already had `performance` governors before game start and1512/520/786MHz samples. Different boot identity and uptime establish intervening reboot; they do not identify previous policy writer. [Fresh monitoring](../../r36s-dumps/sh3/20261115T110310292115Z-0bbfb4/service/performance.txt), [earlier640 monitoring](../../r36s-dumps/sh3/20261114T055246314042Z-4068d8/service/performance.txt), [measurement audit](measurement_plan.md).
- Existing monitor deliberately reads clocks; it never sets them. It captures CPU policy minimum/maximum but not supported governors, GPU/DMC limits or available OPP lists. Reviewed project launcher/service/recovery paths and fresh helpers reveal no governor setter; `pm_platform_helper` name alone establishes no power-management capability. Historical1512/520/786MHz observations are **not verified current stock maxima**. [Monitor contract](../../scripts/device/monitor-game.sh:2), [captured attributes](../../scripts/device/monitor-game.sh:18), [helper review and ownership gap](measurement_plan.md).
- Linux CPU `performance` governor requests current policy maximum. Shared policy may cover multiple cores; selecting it remains device-wide while active. Supported governors come from `scaling_available_governors`; `scaling_cur_freq` may show requested rather than actual hardware rate, and thermal limits remain relevant. Linux4.4 implementation targets `policy->max`, not an arbitrary higher frequency. [CPUFreq contract](https://docs.kernel.org/admin-guide/pm/cpufreq.html), [kernel4.4 implementation](https://github.com/torvalds/linux/blob/v4.4/drivers/cpufreq/cpufreq_performance.c).
- Linux4.4 devfreq `performance` requests configured maximum, or driver-resolved maximum when unspecified. Generic devfreq supports governor selection and available-frequency reporting, but target driver and downstream kernel determine implementation; GPU and DMC cannot be assumed interchangeable. Available-frequency listing is not necessarily restricted by current policy min/max. Do not write an observed numeric frequency or infer available governor from CPU support. [Kernel4.4 devfreq governor](https://github.com/torvalds/linux/blob/v4.4/drivers/devfreq/governor_performance.c), [devfreq sysfs ABI](https://github.com/torvalds/linux/blob/v4.4/Documentation/ABI/testing/sysfs-class-devfreq), [driver contract](https://docs.kernel.org/driver-api/devfreq.html).
- Official dArkOS revision `08889b80df3aaa3fcd6a082305188c47869ab82b` demonstrates three-governor performance selection, but `perfmax` also changes permissions, terminal/audio and state; `perfnorm` writes fixed defaults rather than captured originals. Its suspend helper supplies save/restore precedent, not complete cleanup proof for this port. Do **not** invoke these helpers blindly or infer they set previous run's policy. PortMaster helper reviewed separately supplies no clock-setting capability; exact firmware/helper fingerprint remains prerequisite. Cuphead's first-hand demand-governor slowdown is relevant motivation, different H700/firmware remains incompatible as direct policy proof. [Pinned perfmax](https://github.com/christianhaitian/dArkOS/blob/08889b80df3aaa3fcd6a082305188c47869ab82b/scripts/perfmax#L89), [pinned perfnorm](https://github.com/christianhaitian/dArkOS/blob/08889b80df3aaa3fcd6a082305188c47869ab82b/scripts/perfnorm#L54), [pinned suspend helper](https://github.com/christianhaitian/dArkOS/blob/08889b80df3aaa3fcd6a082305188c47869ab82b/scripts/sleep_governors.sh#L18), [PortMaster/helper applicability](gpu_renderer.md), [Cuphead first-hand release](https://github.com/wild1walker/portmaster-cuphead/releases).
- Spec requires matched thermal state and recorded clocks, excludes overclocking, firmware replacement and unrelated-port changes. It does not explicitly prohibit temporary selection of supported governors within unchanged verified stock limits. Current research scope still authorizes no writes; future script implementation must satisfy launcher-boundary RED–GREEN–REFACTOR and real device cleanup evidence. [Comparison rule](../../docs/specs/silent-hill-3-r36s.md:124), [scope exclusions](../../docs/specs/silent-hill-3-r36s.md:146), [project workflow](../../AGENTS.md).

### Inferences

1. **Read-only prerequisite:** saved host/device probe should collect unique resolved CPU policy paths, affected CPUs, scaling driver, available governors/frequencies, hardware and policy min/max; GPU/DMC device names, drivers, available governors/frequencies and min/max where present; boot/firmware fingerprints, thermal state and exact installed power helpers/services. Record absence explicitly. Inspect frontend launch, startup and suspend/resume policy writers without invoking them. Support and ownership require evidence before experiment, especially downstream `dmc_ondemand`. [Attribute semantics](https://docs.kernel.org/admin-guide/pm/cpufreq.html), [devfreq ABI](https://github.com/torvalds/linux/blob/v4.4/Documentation/ABI/testing/sysfs-class-devfreq), [project access workflow](../../scripts/README.md).
2. **Proposed session contract, not implemented API:** `begin_stock_performance_session(run_dir, expected_boot_id, approved_policy_paths)` snapshots exact original governors and limits, validates advertised `performance` support and approved existing stock caps, journals each owned change, then writes only selected governor attributes. No min/max, OPP, voltage, boost, thermal, permissions or persistent configuration writes. If existing limits or stock provenance remain unknown, fail before applying. A whole-device policy change needs exclusive diagnostic session; it is not process-local. [Linux governor behavior](https://github.com/torvalds/linux/blob/v4.4/drivers/cpufreq/cpufreq_performance.c), [scope](../../docs/specs/silent-hill-3-r36s.md).
3. **Exact restoration:** paired `end_stock_performance_session(...)` restores captured values, not guessed defaults; handles partial application, launch failure, normal exit, TERM and forced game exit through existing independent supervisor cleanup. Verify governors restored and all limits unchanged; collect restoration status separately from game status. Shell trap alone cannot cover SIGKILL or power loss. Validate ownership/boot before restoration; never replay stale snapshot after reboot or silently overwrite another active policy writer. An external governor change invalidates comparison instead of triggering an endless enforcement loop. [Existing lifecycle boundary](../../scripts/README.md), [required failure/cleanup behavior](../../docs/specs/silent-hill-3-r36s.md).
4. **Minimal causal comparison:** after query experiment finishes, start a new same-binary, same-input, same-query-off control/performance/control series with comparable temperatures and logged before/during/after policies. Joint CPU/GPU/DMC performance session tests reproducibility of earlier operating conditions; individual supported governor changes are needed to attribute cause. Keep unchanged numerical limits. Recovery toward23.2FPS would explain part of fresh slowdown, not satisfy true64030FPS. Reject experiment if unsupported policy, changed caps, competing writer, failed cleanup, throttling mismatch or observer differences remain. [Baseline](../../reports/issue-13-performance.md), [fresh confounder](measurement_plan.md).
5. **Required future tests:** through existing launcher-facing boundary, observe RED then GREEN for unchanged limits, unsupported-policy refusal, exact restoration after normal/failure/partial/terminated launch, and useful restoration-failure reporting. External sysfs/helper fixtures test lifecycle contract only. Actual device before/during/after readback plus frontend return must pass before claims of safe stock-session behavior or acceptance benefit. [Confirmed test boundary](../../docs/specs/silent-hill-3-r36s.md), [project TDD rule](../../AGENTS.md).

### Gaps

- Current stock tables, GPU/DMC caps, available governors and original policy owner remain unproved. Parent holds further run until read-only ownership/capability review; this research neither assumes writes authorized nor prescribes arbitrary frequency values. No promise that governor selection reaches30FPS, eliminates worker wait or improves sustained hot behavior. [Measurement handoff](measurement_plan.md), [renderer limit caveat](gpu_renderer.md).
- Focused CCE recall/search again returned cached monitoring headers instead of setter provenance; exact scoped search of project scripts/tests/docs supplied fallback. No project governor writes found in those reviewed paths; absence does not prove no external firmware service owns policy. [Monitor source](../../scripts/device/monitor-game.sh:2), [retrieval rule](../../AGENTS.md).

## Runtime attribution implementation, 2026-11-15 (local)

First diagnostic slice retains agreed installed-launcher → real-game → frontend
boundary. Existing full room210 checkpoint test injects20ms sleep at actual SDL
swap boundary through forwarding observer. New assertions require positive
worker CPU, a separately reported swap CPU subset, and at least15ms difference
between injected swap wall and on-CPU cost. Correct RED observed against2ac6:
`.port-cache/optimization-uniforms/worker-cpu-red`,1failure/63.303s, specifically
missing `worker_cpu_ms`; scene load, original report, SDL completions and cleanup
already passed. No device evidence inferred from Docker test.

Minimal candidate adds `worker_cpu_ms` and `swap_cpu_ms` to existing buffered
`.presents.csv`; original columns and frame/room/dimension identity retained.
Worker CPU uses `CLOCK_THREAD_CPUTIME_ID` between successive actual swap returns,
including its driver/queue/profiler CPU but excluding sleeping/blocked time.
Swap CPU is nested subset around actual `SDL_GL_SwapWindow`; do not add it to
worker total or call either GPU execution. First completion has zero interval
CPU. Added CPU-clock reads occur only when frame profiling active. Explicit
`SH3_GL_THREAD=0` instead reports presenting producer's interval CPU; classify
only after checking enabled worker in run log. [Linux per-thread CPU clock contract](https://man7.org/linux/man-pages/man3/clock_gettime.3.html).

O3/bounded-LTO build `20261115T112806405240Z` exits0, runtime SHA256
`787ca300fd6bf8d23e8cc6579cfc9d0228fc10c6c37b89336416c0fb012894c7`,
debug SHA256 `c87a7a458c1175f45568456537cc58f89ea64788251b8953c02d7da74ef76c55`,
GNU build ID `ee0aa4efafae3a3f55e68c4d84dc6ea7161808c3`.
GREEN `.port-cache/optimization-uniforms/worker-cpu-green`,1PASS/62.983s.
Post-GREEN review retains existing worker-owned buffered report and snapshots;
no shared FILE, guest read, new GPU operation, queue depth or pacing change.
Header comment clarifies nested CPU scopes and synchronous-mode interpretation.
REFACTOR regreen `.port-cache/optimization-uniforms/worker-cpu-refactor`,
1PASS/62.977s. Frozen build released for same-binary default/performance device
pair before next candidate changes; those runs establish hardware evidence.

Second diagnostic slice tests validated `SH3_SWAP_INTERVAL` through same installed
launcher and actual SDL boundary. Forwarding observer preserves SDL calls and
records requested interval, set return code and getter result independently.
RED `.port-cache/optimization-uniforms/swap-interval-red`,1test/101.746s,
7expected subcase failures: explicit0 reached SDL as1, default1 lacked status
report, invalid/unprofiled values still started guest. First0 case retained
clean `ExitProcess(0)`, proving setup already worked. Minimal candidate validates
exact0/1 plus nonempty `SH3_PROFILE` before guest startup, returns2 on invalid
settings, and reports actual set/get once after context creation. Default1,
30FPS pacing, graphics workload and player options unchanged. Set success/get0
alone still does not prove immediate hardware scanout or completed GPU workload.

Candidate build `20261115T114001775304Z` exits0, O3/`-flto=2` with Cortex-A35,
`-fwrapv` and `-fno-strict-aliasing` retained. Runtime SHA256
`485f25039e3e190c501610cf02a4245e1acd948997cd811f7c5faa596d691eeb`,
debug SHA256 `a2deeb22fc3e577c31b480af7f5e32d778110e64ca8fc10236805df313fe3a1c`,
GNU build ID `32bba08410dbacf57c4fb77930e663e171b424bd`.
GREEN `.port-cache/optimization-uniforms/swap-interval-green`,1PASS/31.294s.
Review retains main startup validation plus existing context owner's single
SDL configuration; no new context, queue seam, persistent option or game effect.
REFACTOR regreen `.port-cache/optimization-uniforms/swap-interval-refactor`,
1PASS/31.283s. Actual forwarding Mesa boundary reported0/result0/effective0 and
1/result0/effective1, matching native once-only log. Invalid/unprofiled cases
showed only useful configuration error before guest/GL activity and returned
frontend. Hardware swap semantics still require actual R36S runs.

First actual worker-instrumented default-policy run
`r36s-dumps/sh3/20261115T113712423917Z-c04191`, frozen787ca300 binary, room210
warm55–95s:678 completions, unique frame IDs,678/678 producer joins and exact
room/dimension matches. Mean completion59.05256ms (16.935FPS), worker
CPU12.826759ms, swap wall45.960785ms, nested swap CPU0.612524ms. Swap off-CPU
45.348261ms; outside swap worker wall13.091775ms versus CPU12.214235ms,
leaving0.87754ms off-CPU outside swap. Producer CPU30.462066ms, present
backpressure28.14617ms, draw3.583686ms. Completionp95=65.0168ms,p99=66.33238ms
(linear sample quantiles). Most current wait lies inside actual SDL swap; this
distinguishes blocked worker from CPU execution but cannot split GPU, display,
kernel wait and descheduling. Worker and producer CPU overlap; swap CPU is
nested, not additive. Producer30FPS CPU headroom only2.871ms. Derived statistics
retained `.port-cache/runtime-attribution/20261115T113712423917Z-c04191.json`.
Run reports execution/collection/frontend cleanup0 and source preserved; this
performance remains below acceptance, pending same-binary stock-policy pair.

Query-scope source review: worker calls `profile_gpu_begin()` before each chunk;
active query survives further chunks until `swap_now()` ends it before SDL swap.
`gl_swap_window()` records swap then publishes, making swap final command in
chunk; next frame opens next chunk. No obvious queued draw gap after query end
in reviewed source. Region still excludes SDL/EGL swap work and lacks calibrated
GPU-completion coverage on vendor driver. CCE query found current
`src/d3d8/profile_gpu.c:1` preview; expanding that exact ID returned `Chunk not
found`, so known current file plus worker publish/swap paths read directly.
No query implementation change selected from this review.

Rechecked current official [PortMaster native-port guide](https://portmaster.games/contribute/porting/what-can-be-ported/),
[SDL set](https://wiki.libsdl.org/SDL2/SDL_GL_SetSwapInterval) and
[get](https://wiki.libsdl.org/SDL2/SDL_GL_GetSwapInterval) contracts, plus current
[Cuphead first-hand release](https://github.com/wild1walker/portmaster-cuphead/releases).
No directly matching independent SH3/RK3326 worker-CPU fix found. Cuphead's H700
Unity/setup policy remains different and supplies no SH3 performance proof.
SDL0 means immediate request,1 retrace synchronization; set result must accompany
effective getter because getter0 can also mean unsupported/unknown context.
CCE again returned cached headers; exact current
`expand_chunk("src/d3d8/gl_thread.c:1")` returned `Chunk not found`, so known
current source/test paths reviewed directly. No downloaded instructions executed.

## Same-binary critical-path results and validation, 2026-11-15

Independent completion→producer joins use actual frame IDs, unique rows and
exact room210/internal640×480 metadata for55–95s. Quantiles use linear sample
interpolation; lead's nearest-rank figures differ slightly. Derived files live
under `.port-cache/runtime-attribution/<run-id>.json`; raw evidence remains
under `r36s-dumps/sh3/<run-id>/`.

| Frozen787ca300 run/policy | Joined completions | Mean completion / FPS | Worker CPU | Swap wall / nested CPU | Producer CPU / present backpressure |
| --- | ---: | ---: | ---: | ---: | ---: |
| `20261115T113712423917Z-c04191`, default CPU/GPU/DMC |678|59.052560ms /16.93516|12.826759ms|45.960785 /0.612524ms|30.462066 /28.146170ms|
| `20261115T114326258503Z-d74edc`, stock performance CPU/GPU/DMC |857|46.649840ms /21.43698|11.224186ms|35.195089 /0.442784ms|28.316957 /18.132118ms|
| `20261115T114935059499Z-3b9030`, performance CPU/DMC, default GPU |711|56.314828ms /17.75355|11.091466ms|45.027373 /0.427363ms|28.052212 /27.916281ms|

Full-performance run has CPU1512/GPU520/DMC786MHz in22 captured samples,
unchanged stock limits and all three governors restored. CPU+DMC-only contrast
has CPU1512/DMC786MHz in21 samples; GPU400MHz20times/480MHz once. Thus holding
CPU/DMC at same observed clocks while GPU400→520MHz associates with17.75→21.44FPS
and45.03→35.20ms swap wall, while worker CPU stays11.09→11.22ms and nested swap
CPU0.43→0.44ms. This supports GPU-frequency-sensitive downstream bottleneck;
it does not distinguish shader ALU, texture, tiler, memory or presentation
mechanism. Animated draws are similar, not identical (median372versus377).
Full-policy comparison alone cannot isolate individual clock domains.

Actual deployed SHA256 and payload ELF build ID verify all three used frozen
787ca300. Original `3b9030` host scene-identity metadata incorrectly identified
current mutable485f package; actual `device/runtime.sha256`, deployed ELF build
ID `ee0aa4efafae3a3f55e68c4d84dc6ea7161808c3` and retained deployment payload
identify787ca300. Lead owns selector identity correction/erratum. Contrast run
game/service collection succeeded, source preserved, CPU/DMC restored and
frontend active; outer collection124 missed firmware-after, separately repaired
by lead. Preserve original status/metadata rather than relabel failure as zero.

Full-policy completionp95/p99/max=50.9682/54.17204/58.747ms. Outside swap,
worker wall11.454751ms versus CPU10.781402ms leaves only0.673349ms off-CPU;
swap off-CPU34.752304ms dominates. CPU+DMC-only swap off-CPU44.600010ms.
Neither swap wall nor off-CPU remainder is direct GPU execution time.
Producer and worker CPU overlap, and swap CPU nests inside worker CPU.
Full-policy46.65ms completion remains above33.333ms target despite26.6% FPS
gain over default. These static warm runs are not moving/sustained acceptance.

Final485f checkpoint regression passes1test/62.941s at
`.port-cache/optimization-uniforms/worker-cpu-final`, retaining independent
20ms-sleep CPU/wall oracle. Full ARM64 suite
`.port-cache/runtime-tests/20261115T114824329223Z` ran196tests/302.276s:
109PASS,86explicit skips,1fixture failure. Passing modules include35graphics,
7actual native-game launcher/lifecycle cases,34frontend lifecycle cases,
5runtime,24preflight,2performance-report and2build cases. Counter build CLI
fixture expected unavailable-Docker42 but instead reached absent external Git
inside Docker; counter owner reproduced RED with same mount layout, corrected
test-only external Git stub, then focused ARM64 module regreen1PASS/1explicit
native-build skip. Evidence
`.port-cache/issue-13-limits/gpu-counter-build-arm64-layout-{red,green}.txt`.
Actual official counter native build passed independently. New timed-counter
session fixtures also pass4ARM64 cases. No false all196-pass claim or redundant
game rebuild follows this isolated fixture correction.

## Exact native Options mapping, 2026-11-15

This is read-only source/UI research plus normal game menu automation in
isolated state copies, not new product behavior; implementation TDD does not
apply. Existing installed launcher, SH3_KEYS/PEEK/capture and native485f runtime
run only inside explicit Linux ARM64 Docker. Owner and original checkpoint
mount read-only; no guest write/poke or physical-device access. Evidence and
replay recipe: `.port-cache/graphics-map-20261115/`.

Cold start0/0 and1/1 seeds prove **lensflare_ztest1=Low, shadow1=No** for
recognized owner executableSHA1`d851669ef609b3164e3581aa8dcfbfaec866cb79`.
`cold-0.png` displays High/Yes, `cold-1.png` displays Low/No. Both actual640×480
output/backbuffer, separate fresh states, clean ExitProcess0. Loaded UI dword
BCC1B8 is0for0/0 and00010100for1/1; backupBCC1D4 is00000000 versus01010000.
No numeric quality-order assumption needed. External Windows graphical-fixer
documentation claiming inverse shadow values does not override this exact
recognized-build evidence.

Loader `recomp_0029.c:sub_005E4310` loops two key entries from71E5FC at16-byte
stride, reads parsed value through005EF950 and writes low byte directly to
BCC1B9/BCC1BA plus backupsBCC1D6/BCC1D7. UI renderer005E40F0 uses two labels
per binary field. Apply `recomp_0030.c:sub_005E5BF0` forwards those bytes directly
through005F04B0; cancel restores backups. Shadow consumers00685C10/00685CB0/
00685DA0 skip shadow draw branch for parsed value1. Lensflare consumer0049FAC0
returns early for1 before depth/occlusion work; do not describe Low as proof all
flare rendering removed. [Current generated code](../../src/recomp/gen/recomp_0029.c),
[apply/get/set](../../src/recomp/gen/recomp_0030.c),
[shadow consumers](../../src/recomp/gen/recomp_0046.c),
[flare consumer](../../src/recomp/gen/recomp_0012.c).

Actual Configuration page exposes Resolution, Screen Mode, Rendering Resolution,
Gamma Correction, Lensflare Quality and Real-Time Shadow. Original rendering
table71E640 supports256×256,512×256,512×512,1024×512,1024×1024,2048×1024,
2048×2048,4096×2048,4096×4096. Original UI displays512×512 for injected640×480
INI rendering value; it is not proof current backend renders512×512. Runtime
override and per-frame measured dimensions must establish acceptance640×480.
Saving through UI can replace unsupported table value with512×512; prepared
benchmark seed should copy data.sys/data.001, retaining explicit scene640×480
configuration/override, then verify actual completion dimensions.

Actual Extra Options page (`seedpages-1.png`) from **same room210 checkpoint**
displays Blood Color Normal, Blood Volume Normal, Walk/Run Control Normal,
Map Zoom Out, **Noise Effect On, Display Mode Normal**, Low Health Indicator Off.
Original data.sysSHA256`c41228448305e3b3fd582af23f7cbaf9c7de9e5632a400582ac0c8c17cc7d34d`
and data.001SHA256`fa2d9fd1b7c1e2af9b9b771b2a996f988f5b82bdd8cda41d045975f31b787515`
remain unchanged. Thus earlier1/1 benchmark is verified Low/No but **not yet
lowest supported standard graphics profile**, because Noise was On.

Noise UI `recomp_0030.c:sub_005E54E0` toggles byteBCC1AE0/1; apply005E5BF0
calls0060CCE0. Persistent setter writes game-option70E66CF then0042BBA0 writes
renderer72D277. Nonzero00435950 enables renderer state transitions0→1/2→4;
zero00435970 transitions1→0/4or5→2 via0042B540. Consumer0042BC50 switches
effect render path using state72D270 and Noise72D277; zero bypasses noise
variants but retains unrelated effect-state handling. This is supported game
option, not arbitrary visual bypass. [UI/apply](../../src/recomp/gen/recomp_0030.c),
[persistent options](../../src/recomp/gen/recomp_0033.c),
[renderer state](../../src/recomp/gen/recomp_0004.c),
[noise transition helpers](../../src/recomp/gen/recomp_0005.c).

Display UI005E5600 togglesBCC1AF; persistent0060CF20 writes70E66B3.
Nonzero00426D30 sets16-bit+2 flag in both objects72D148/72D150; zero00426D50
clears flags. Composite consumer004274C0 reads active object flag; nonzero
selects stage0 MAG/MIN filter1(point), zero normally2(linear), with another
game predicate able to choose point. Same composite draw remains; evidence
supports sampler choice, not removed full-screen pass. Backend maps tss16/17
>=2 toGL_LINEAR,1toGL_NEAREST. Separate actual UI probe
`seeddisplay-v2-1-frame01740.png` confirms alternate **Sharp** (byte1), versus
Normal0. Apply updates saved70E66B3 to1 and cleanly exits0. Sharp is supported
alternative sampling look, not automatically quality rank; same composite pass
remains. [Display/render consumer](../../src/recomp/gen/recomp_0004.c),
[actual sampler mapping](../../src/d3d8/d3d8_shader.c:927),
[Microsoft D3D8 enum](https://learn.microsoft.com/en-us/previous-versions/windows/embedded/ms886612%28v%3Dmsdn.10%29).

No Soft Shadow, shadow-map resolution, texture quality, DOF or fog-quality control
appears on captured Configuration/Extra Options pages. Windows enhancement
wrapper ShadowRes/DOFRes/Fog values are not established standard guest controls
for this runtime. Hidden/unsupported keys remain unmapped; do not invent INI
quality reductions or change Blood/gameplay semantics. Current low seed keeps
DisplayNormal and all Blood/control/indicator options unchanged to isolate Noise.

CCE source queries for exact generated function names/addresses returned
unrelated conformance noise code and cached dumps rather than requested bodies;
scoped exact-name/address rg and known-current generated source used as fallback.
Official PortMaster guide rechecked, primary upstream sh3-nx and Windows-wrapper
source compared only for applicability. First-hand WidescreenFixes issue285
discusses noise/fog cost and image changes, but supplies no RK3326 proof; actual
native comparison remains required.
[Upstream sh3-nx](https://github.com/cutarev/sh3-nx),
[Windows options-fixer claim](https://github.com/WindyAlexia301/sh3pc-graphical-options-fixer/blob/main/HOW%20TO%20USE.md),
[wrapper config](https://github.com/ThirteenAG/WidescreenFixesPack/blob/master/data/SilentHill3.WidescreenFix/scripts/SilentHill3.WidescreenFix.ini),
[first-hand discussion](https://github.com/ThirteenAG/WidescreenFixesPack/issues/285).

Clock-correlation limitation: producer/completion elapsed_ms directly uses
SDL_GetTicks64, initialized by first SDL tick/performance/init call, not profile
start or host wrapper exec. Runtime logs no paired OS-clock sample. Official
SDL Unix implementation normally uses CLOCK_MONOTONIC_RAW, whereas counter
wrapper stores MONOTONIC; process-start bracket is approximate. Associate broad
steady windows only with explicit epoch uncertainty until paired clock sample
exists. No additional C/build change selected while current native pair runs.
[SDL ticks contract](https://wiki.libsdl.org/SDL2/SDL_GetTicks64),
[official Unix timer source](https://github.com/libsdl-org/SDL/blob/SDL2/src/timer/unix/SDL_systimer.c).

### Isolated supported NoiseOff state, verified cold reload

Existing SH3_KEYS navigation edited only isolated copy of original data.sys.
Correct Extra Options sequence is existing initial title/options keys through
36:D, then39:D,42:D;45/47/49/51:S selects Noise,53:Left toggles Off,
56/58/60:S selects Exit,62:Return opens save confirmation,65:Return applies.
70-second deadline cleanly exits native game. This is existing launcher-driven
normal UI behavior, not runtime patch or guest-memory write. First draft selected
wrong tab and was discarded entirely (`seednoise-1`); only corrected
`seednoise-v2-1` supplies prepared seed. Original source mounted read-only and
all source hashes unchanged.

Cold replay `verifynoise-1`,48seconds, reopens Extra Options from saved isolated
state and displays **Noise Effect Off, Display Mode Normal**, Blood Color/Volume
Normal, Walk/Run Normal, Map Zoom Out, Low Health Indicator Off. PEEK matches
UI0x00BCC1AE=0, saved0x070E66CF=0 and renderer0x0072D277=0; clean
ExitProcess0/frontend return. Aligned existing PEEK reads0x070E66CC,
0x070E66B0 and0x0072D274; target Noise/Display/renderer byte is each
`(word >> 24) & 255`. PEEK reads/logs guest32-bit dwords, not single bytes.
Before/after/cold identities and screenshot retained:
`.port-cache/graphics-map-20261115/{seednoise-v2-1/option-save-identity.json,verifynoise-1/identity.json,verifynoise-1.png}`.

Prepared source `.port-cache/graphics-map-20261115/seednoise-v2-1/port/state`:
data.sysSHA256`05913dcaec295588f206338deafc80efed9209dec892e4e3e7af436f27105640`;
data.001 remains original
`fa2d9fd1b7c1e2af9b9b771b2a996f988f5b82bdd8cda41d045975f31b787515`.
Native system-option serialization rewrites encoded data.sys; raw changed-byte
count is not option-level diff proof. Normal UI state/consumer/cold reload prove
semantic change; unchanged data.001 proves saved game progress preserved.
For actual benchmark copy **only data.sys/data.001**, retain benchmark's1/1
disp.ini, warmed cache and explicit640×480 override. UI save otherwise substitutes
its supported512×512 Rendering Resolution entry. OriginalOn/Normal and prepared
Off/Normal seeds remain separate. Lead owns all device deployment and measurement.

### Independent moving On/Normal control

Final485f moving/control run `20261115T120025683855Z-5dd767` has2463 unique
completion rows75–180s,2463/2463 producer joins, allroom210/internal640×480.
Elapsed-span FPS `(N-1)/(last-first)`=23.450746, matching lead23.45075;
reciprocal mean completion42.644011ms=23.449952FPS because first interval
crosses window boundary. Quantile p95/p99/max50.5129/53.27522/74.812ms;
complete one/five-second floors18/20FPS. WorkerCPU11.255824ms;
swapwall30.629274ms/nestedCPU0.448948ms/offCPU30.180326ms.
Outside swap worker wall12.014737ms versusCPU10.806876ms. ProducerCPU28.948799ms
(p99=31.021409,max36.512588), present backpressure13.263928ms,draw3.390516ms.
Producer some-frame CPU budget misses remain despite mean headroom4.3845ms.
Raw retained; independent recipe/result
`.port-cache/runtime-attribution/analyze.py` and`20261115T120025683855Z-5dd767.json`.

Scene-identity confirms same original data.sys c4122844 anddata.001fa2d9fd1 as
UI survey, runtime485f2503; source preserved. Lead verifies41live PEEK samples,
40changing positions,health100, actualhandgun consumption/reload, fullstock
policies, requested1/result0/effective1. Recovery run
`20261115T120815248161Z-a63fad` completes outer evidence and firmware/seed
preservation checks0; preserve initial collection status separately. This is
moving/combat evidence in one room, not multi-level or stable30FPS acceptance.

### Supported Sharp alternative and isolated multi-level handoff

Separate normal UI edit starts from verified NoiseOff/Normal system state,
selects next Extra Options row Display Mode, changes Normal to Sharp, applies
through ordinary save confirmation and cleanly exits. Cold replay
`verifyboth-1.png` displays Noise Effect Off/Display Mode Sharp with other
displayed settings unchanged; loaded saved noise70E66CF=0, display70E66B3=1,
renderer noise72D277=0. Both execution statuses0; original NoiseOn/Normal and
prepared NoiseOff/Normal source hashes unchanged. No guest-memory writes.

Sharp source `.port-cache/graphics-map-20261115/seeddisplay-low-1/port/state`:
data.sys SHA256
`9986bc30e0c461f42e0541852303fef3e079554bff797724b8d5c5a745462793`;
data.001 remains `fa2d9fd1b7c1e2af9b9b771b2a996f988f5b82bdd8cda41d045975f31b787515`.
Normal edit/cold evidence retained in `seeddisplay-low-1/option-save-identity.json`
and `verifyboth-1/identity.json` under same ignored graphics-map directory.
Sharp changes supported sampling choice; no claim it removes composite pass or
automatically represents lower graphics quality. Device measurements pending.

Existing public archive rechecked locally without new download:
`.port-cache/optimization-saves/20261113-normal/source.zip`, SHA256
`5bf9878a05ec68fb6f09fd88d5db42762c12d9b22ee817936a5507acf948de21`.
[Source page](https://www.silenthillmemories.net/sh3/save_games_en.htm),
[exact archive](https://www.silenthillmemories.net/sh3/saves/sh3_pc_save_normal_ending_beginner_easy.zip).
Page credits SilentRain, labels Beginner action/Easy riddle/Normal ending.
Difficulty claim is source attribution, not worst-case campaign coverage.
Only reviewed 9952-byte save payloads copied; no external code executed.

Task-owned seed root
`.port-cache/issue-13-limits/multilevel-low-20261115T123000Z/` contains
`mall-normal`, `hospital-normal`, `church-normal` and optional matching `-sharp`
variants. Each uses exact public payload remapped to `savedata/data.001`, verified
NoiseOff/Normal05913dca or NoiseOff/Sharp9986bc30 system state, known measured
`disp.ini`27a40ce6 (Low flare1/No shadows1/output640×480/render640×480), and
retained corresponding prior native level caches. Actual runtime dimensions and
loaded option/room evidence still required on each new combined seed; prior320
acceptance and cached shaders do not prove new640 acceptance/warm coverage.

| Area / public slot | Previously verified room | Exact data.001 SHA256 | Prior native source run |
| --- | --- | --- | --- |
| Mall /006 |18 |`2b36e767b04b322a213bcd4d32516e19db41a2688c5fdedb709da8595ffaf61f` |`20261114T051822455921Z-bab6a5` |
| Hospital /024 |160 |`cce9537a3861dde794c870250b13441e4c5c5c4a5139e784b748f656299e402b` |`20261114T051236207262Z-4ed67b` |
| Church /028 |240 |`b92fed0e0defbb65e58c8164cdf716b4cf8f80248cabbaad46acf7bd367a296d` |`20261114T052509963498Z-f9bc5c` |

Mall/hospital program-cache SHA256
`c5e2eec2f5356cbeb12cacc4533c634d3986e284c2febab67dac140081ab0c0b`,
GL-cache `407f0c2c4abdb530e8a47da201fb5363c8c7476230a092c501d71c441e1096c1`;
church program-cache
`bf5773feefbbc67c1657a680e0be9dc49a9d97138bc698277359c43f11524768`,
GL-cache `b6f987c8b36e6d6989fd98150ecf654557308a219ed264d88af0c2cc80219cf4`.
Full source/destination hashes, prior identity, provenance, controls and explicit
unverified items in seed-root `manifest.json`. Read-only copy recipe
`.port-cache/runtime-attribution/prepare-multilevel.py` compares archive and
retained native payloads before copying and verifies all source hashes afterward.
Pure research data preparation adds no product behavior; TDD does not apply.
Original archive, saved state, retained sessions preserved. Device lead owns
scene configuration, scripted execution and actual hardware acceptance.

### Matched moving NoiseOff/Normal result

Native `20261115T121637292450Z-d498a8` completes all execution/collection stages0,
source preserved. Its scene identity exactly matches On/Normal5dd767 runtime485,
plan hash, original data.001fa2d9fd1, disp27a40ce6, program-cache18aa0144 and
GL-cache06a34b1c; only data.sys changes from proven On c4122844 to proven Off
05913dca. Both retain full stock CPU/GPU/DMC policy, interval1 and 30FPS limiter.
Same moving route means comparable workload, not frame-identical GPU commands.

Independent75–180s join has2716/2716 unique completions and producer matches,
allroom210/internal640×480. Span FPS25.869708 versus23.450746 On (+10.3151%);
mean completion38.656137ms versus42.644011ms (−3.987874ms).
p95/p99/max45.8805/47.6543/68.295ms; complete1s/5s floors21/22.6FPS.
WorkerCPU10.626712ms, swapwall27.351750ms/nestedCPU0.454086ms/offCPU26.897663ms.
Outside swap workerwall11.304387ms versusCPU10.172626ms.
ProducerCPU28.350181ms, p99=30.486676ms,max35.460250ms; present9.462113ms.
Mean remaining gap to33.333ms budget5.322804ms, requiring15.97% more throughput;
below25FPS floor remains. NoiseOff materially helps but does not pass owner goal.
Swap wall still cannot be called GPU execution time; CPU and worker overlap.
Recipe/result `.port-cache/runtime-attribution/analyze.py` and
`20261115T121637292450Z-d498a8.json`; raw evidence retained unchanged.

### Sharp result and active Configuration-state check

Native Sharp control `20261115T122823159512Z-004cca` completes all stages0,
source preserved. Independent75–180s join:2645/2645 unique frames, allroom210,
internal640×480. Span25.195830FPS versus NoiseOff/Normal25.869708FPS;
mean39.691425ms, p95/p99/max47.5842/50.42768/71.034ms, complete1s/5s
floors19/21.8FPS. WorkerCPU10.798657ms; swapwall28.395765ms/nestedCPU0.452827ms;
producerCPU28.497530ms,present10.705497ms. Single pair shows no Sharp improvement;
small difference does not establish intrinsic regression without repeats.
Keep Normal for subsequent controls. Same runtime/data.001/disp/caches/input keys;
plan differs by added diagnostic PEEK addresses, and data.sys is verified Sharp.
No claim of identical full plan hash or identical frame command sequence.

All44 PEEK observations75–180s show actual saved Noise=0, Display=1 and renderer
Noise=0, decoded from high bytes of aligned words0x070E66CC/0x070E66B0/0x0072D274.
Menu scratch word0x00BCC1B8 remains0, so flare/shadow menu bytes are0 while game
runs. Those bytes are **not active renderer settings**: menu-entry005E4310
copies parsed values into0x00BCC1B9/BA only when Options opens. Automated gameplay
route never opens Options; early title and later gameplay samples both show0.
Thus0/0 scratch does not show selected1/1 configuration reverted.

Bounded exact current-source trace:

- Startup004028D5 calls005F09F0; opens `disp.ini` through005F1200, reads lines
  through005F0790, splits key/value and stores string via005F06B0 in configuration
  tree rooted0x00BCC600 with sentinel0x00BCC604.
- Render getter005EF950 queries that same tree, returns0 for missing entry,
  otherwise converts node value string at payload+0x11 to integer. Flare0049FAC0
  requests key pointer0x00691250 and returns early at1. Shadow00685C10/CB0/DA0
  request0x006942AC and skip corresponding path at1.
- Original recognized executable SHA1
  `d851669ef609b3164e3581aa8dcfbfaec866cb79` read-only PE/rdata inspection confirms
  0x00691250=`lensflare_ztest`,0x006942AC=`shadow`,0x0069881C=`disp.ini`,
  0x00698828=`rt`; menu table0x0071E5FC/0x0071E60C points to those exact keys.
- Only direct integer setter005F04B0 callers found are Options apply/cancel
  loops. Config reset005F0950 is reached from startup005F09F0; no direct Load
  reset found. Other string setters handle config parser and display hardware
  values, not evidence that saved game data resets flare/shadow.

Sharp collected `launcher/session/savedata/disp.ini` SHA256
`27a40ce6f83f520e5ac9a8b2511796ee7a63ea9166439db42e4f69420f31e600`
equals scene seed and retains both1 plus both640×480 fields. Log records actual
disp read at startup and clean retained file. Source/menu mapping supports Low
flare/No shadow; active dynamic tree values themselves remain unsampled. No new
runtime build or fragile heap walker introduced; scratch-state ambiguity does
not block counter/multi-level queue. Source inspection and evidence analysis
change no executable behavior, so no TDD cycle needed.

CCE queries for exact getter/loader names again returned cached dumps and
unrelated tooling. Exact scoped rg/current generated-source fallback used;
string proof `.port-cache/runtime-attribution/config-key-proof.json`, full frame
join `20261115T122823159512Z-004cca.json`. Relevant current source:
[menu copies](../../src/recomp/gen/recomp_0029.c:48417),
[getter](../../src/recomp/gen/recomp_0030.c:27375),
[parser](../../src/recomp/gen/recomp_0030.c:30369),
[startup load](../../src/recomp/gen/recomp_0030.c:30757),
[flare consumer](../../src/recomp/gen/recomp_0012.c:16896),
[shadow consumer](../../src/recomp/gen/recomp_0046.c:3581).

Producer CPU-tail crosscheck on same joined windows: On1/2463, Off/Normal2/2716,
Off/Sharp1/2645 frames exceed33.333ms threadCPU. Off/Normal fraction0.07364%,
max35.46025ms; rare producer overruns cannot by themselves explain sustained
25.87FPS mean. Mean28.350ms/p99 30.487ms indicates current steady gap remains
asynchronous renderer/presentation path. Does not exclude producer wall stalls,
cross-thread contention or other levels. Ignored result
`.port-cache/runtime-attribution/producer-cpu-budget-tails.json`.

### Heavy-room tail attribution, NoiseOff/Normal

Read-only exact-frame join of native `20261115T121637292450Z-d498a8`,75–180s,
separates sustained slow rendering from largest isolated hitch. Reproducible
recipe `.port-cache/runtime-attribution/tail-analysis.py`; complete joined rows,
neighbor frames, stderr event lines and summaries in
`.port-cache/runtime-attribution/d498a8-tail-attribution.json`.
Linear(N−1) p95/p99 thresholds45.8805/47.6543ms. Quantile thresholds interpolate
two frames; following table gives actual nearest-rank frames and max instead.

| Actual completion | Wall / swap wall | Worker / nested swap CPU | Same-frame producer CPU / draw / Present | Draws / buffer bytes |
| --- | --- | --- | --- | --- |
| p95 frame4547 @172.933s |45.885 /33.221ms |11.255998 /.455582ms |28.711959 /3.059 /15.787ms |392 /140300 |
| p99 frame2119 @79.930s |47.660 /36.768ms |11.217791 /.401625ms |29.943377 /3.751 /17.156ms |418 /141532 |
| max frame2170 @82.184s |68.295 /31.721ms |13.921833 /.429334ms |35.460250 /42.016 /.049ms |386 /139404 |

All136 frames at/above p95 average47.108390ms completion,33.504324ms swap wall,
11.142555ms worker CPU and29.315841ms producer CPU. Their outside-swap wall
13.604066ms consists of10.703665ms worker CPU plus2.900401ms off CPU. Worst28
at/above p99 average49.383393ms,31.801ms swap wall,11.083136ms worker CPU and
29.315563ms producer CPU; outside-swap off CPU rises to6.934216ms. Thus long
tail includes non-swap dependency/wait intervals; labeling entire tail GPU
execution or producer CPU saturation would be unsupported.

Longest consecutive complete1s bins below25FPS occur75–83s, counts
23/22/24/23/21/22/24/24.183 joined frames average43.754798ms, of which swap wall
32.871760ms/nestedCPU.462888ms; outside-swap wall10.883038ms versusCPU10.336494ms
and offCPU.546544ms. ProducerCPU29.098420ms, draw3.394732ms, Present13.751153ms,
386.37draws and140257bytes mean. Excluding max2170 still leaves43.619962ms,
swap32.878082ms and outside offCPU.422725ms. Isolated hitch therefore does not
explain sustained8s deficit. Comparison155–165s averages34.491841ms, swap
23.214509ms, workerCPU10.610488ms, producerCPU28.472271ms,360.21draws and
140654bytes. Scene/camera-dependent render/presentation pressure explains
steady contrast better than producer CPU or upload-byte growth; no claim of
frame-identical work or GPU-stage attribution.

Frame2170 is different:36.574ms outside swap versus13.492499ms worker CPU,
leaving23.081501ms outside-swap off CPU. Its producer wall73.250ms versusCPU
35.460250ms; accumulated producer draw42.016ms versus neighboring~3.1ms;
Present.049ms versus~8–15ms nearby. Draw count386 and139404bytes match adjacent
workload closely. Worker swap31.721ms also matches preceding31.496ms and
following31.726ms. Current evidence localizes hitch to producer draw / queue
dependency interval rather than exceptional swap duration. Exact internal wait
or syscall remains unobserved; draw wall can include queue backpressure and
descheduling, not only driver work.

Current [run_swap/pacer](../../src/d3d8/gl_thread.c:394) completes profile record,
signals producer, then sleeps toward phase deadline before next queued commands.
Completion-to-completion wall therefore includes previous frame pacing,
waiting for producer/chunks and scheduling as well as command execution.
Current deadline recurrence replayed from all recorded swap starts/ends requests
zero sleep immediately after2169, before max2170. Simple single-period residual
from2169 swap31.496ms is only1.837333ms (at most2ms rounded request before overhead).
Replay is analytical, not measured wakeup: profile/lock overhead, actual sleep
and descheduling remain unobserved. This excludes asserting23.08ms was intended
pacer sleep; does not prove OS scheduler or a particular queue call caused it.

Nearby PEEK observations keep room210 and health100, show normal moving positions,
and guest heap216MB; no loading/room transition or death recorded. Entire stderr
contains no ALSA recovery, ends47 program binaries restored/0miss/0write/0reject,
CPU sample drops1/write_failed0. No timestamped per-IO/syscall trace exists, so
absence of logged IO/audio/cache events does not prove those subsystems never
stall. All36 coarsely sampled policies retain CPU1512/GPU520/DMC786MHz; thermal
max72.083°C, MemAvailable minimum552752kB, SwapFree494272–494288kB. Existing
SDL/monitor absolute epoch gap prevents exact frame-to-monitor assignment.
Monitor itself and profiling overhead remain possible rare-hitch contributors;
no unmeasured intrinsic-stutter claim. Source CCE query returned compressed
profile.c only; exact current gl_thread.c/profile.c fallback used. Pure evidence
analysis changes no product behavior; no new build/test required.

### Actual mall640 route, independent check

Native `20261115T123732242048Z-5f8010`, full stock clocks, runtime485, NoiseOff/
Normal, interval1. Independent48–160s join3360/3360 unique frames, all room18 and
640×480, span29.99991FPS; every complete1s/5s bin30FPS. Mean33.333583ms,
p95/p99/max34.6343/36.04764/54.762ms. ProducerCPU13.790152ms, workerCPU7.895279ms,
swapwall10.160834ms/nestedCPU.424055ms. Scripted movement remains alive with
47 distinct positions/56 observations; health197.200012 constant, loaded Noise/
Display/renderer Noise all0;49 program restores/0miss. Raw stderr19 ALSA underrun
lines fall between PEEK timestamps11.281–41.282s, before warm48s; no logged warm
underrun. These prove this bounded mall route reaches target, not every mall
room or owner audio acceptance. Result
`.port-cache/runtime-attribution/20261115T123732242048Z-5f8010.json`.


### Active-counter controls and hospital640, independent joins

Same final485 NoiseOff/Normal/full-stock moving heavy-room route with counter
sidecar: `20261115T124320804106Z-652b71`,75–180s. All2720 completion IDs unique,
2720 producer joins/metadata matches, room210 true640×480. Span25.90683FPS,
mean38.602461ms; p95/p99/max45.401/47.80249/71.651ms; complete1s/5s floors22/22.4.
WorkerCPU10.884064ms; swap26.875952ms/nestedCPU.456941ms; producerCPU28.321568ms,
draw2.982147ms, Present9.645969ms. Whole-window OFF25.869708 versus ON25.90683
shows no broad average penalty in this pair; does not prove zero local probe
perturbation or exact cadence mapping. GPU-counter owner independently validates
~71.10% GPU-pending,98.49% core/GPU-active,86.09% fragment/GPU-active, conditional
ALU73.56% and filtering23.00%. Approximately29% nonpending gaps mean full GPU
saturation cannot be claimed; frequency-sensitive critical path still established.
Exact metric definitions, sample validity and clock uncertainty remain in
`gpu_counter_probe.md`.

Requested swap0 native run `20261115T124856641519Z-e4e5b8` records
`gl_swap_interval requested=0 result=0 effective=1`. All2607 warm75–180s frames
join, room210 true640×480; span24.82425FPS, mean40.285067ms,
p95/p99/max49.2905/52.57386/82.003ms, floors19/20.4. WorkerCPU10.71413ms;
swap28.786954ms/nestedCPU.465478ms; producerCPU28.331533ms. These are raw actual
Set/Get observations; comparison cannot certify VSYNC was disabled or quantify
its causal cost. Exact deployed SDL provider provenance and setter/getter/swap
source audit separate cached interval reporting from hardware behavior.

Hospital `20261115T125746122373Z-3572b6`,48–160s, independently joins3360/3360
unique room160640×480 frames: span29.99991FPS, mean33.333271ms,
p95/p99/max34.6418/35.5033/48.11ms, all complete1s/5s30FPS. ProducerCPU14.891117ms
(p9933.112487/max38.180625), workerCPU9.356931ms, swap8.471626ms/nestedCPU.409456ms;
draws296.589 mean/max575, upload323415.467bytes mean/max355244. Target reached
in this bounded hospital route; not every hospital room. Independent outputs
`.port-cache/runtime-attribution/20261115T124320804106Z-652b71.json`,
`20261115T124856641519Z-e4e5b8.json` and `20261115T125746122373Z-3572b6.json`.
No executable behavior changed for these read-only joins; no TDD applicable.


Church `20261115T130244860301Z-7500f4`,48–160s exact join3358/3358 unique room240
frames and true640×480: span29.98285FPS, mean33.352283ms,
p95/p99/max34.3763/35.5803/48.106ms; complete1s/5s floors29/29.8. Joined producer
CPU16.684712ms (p9933.554649/max36.283916), workerCPU7.965901ms;
swap11.494697ms/nestedCPU.424547ms. Joined frame counts differ from separately
windowed producer rows at edges; these means use worker completion IDs. Lead
reports all exit stages0,56 alive observations/47 positions,health200,59 program
restores/0miss,no ALSA log, all32 clock samples fullstock,max68.076°C. Bounded
church route meets stated brief25 floor; no all-church/worst-case inference.
Result `.port-cache/runtime-attribution/20261115T130244860301Z-7500f4.json`.


### Bounded queued-GL diagnostic, TDD and measurement contract

New trace is diagnostic-only, through already agreed installed launcher→actual
ARM64 game→frontend seam. `SH3_GL_TRACE=1` requires nonempty `SH3_PROFILE`;
`SH3_GL_DRAIN=1` additionally requires trace1. Other present values fail2 before
guest/save access. Requires ordinary queued mode (`SH3_GL_THREAD` unset/1);
explicit single-thread0 is outside this diagnostic's supported scope. Default
playback and profiling without trace issue no new GL drain or diagnostic clock
reads/file I/O. Existing default interval1 and30FPS pacing unchanged.

First trace RED14.705s: actual game/GL sleep/frontend0 succeeded; requested
`.gl.csv` missing. Earlier30s setup timeout lacked standard intro Return and was
not behavioral RED. First GREEN attempt exposed external-observer placement:
initial glGenTextures runs on setup thread before worker start; correct trace
therefore omitted that setup sleep. Observer now selects first distinct GL-call
thread, proving real worker sleep rather than moving queue start or fabricating
telemetry. Same trace binary GREEN30.670s; fixture refactor makes queued mode
explicit and requires enclosing sync event share frame/job and actual interval;
REFACTOR regreen30.778s. Evidence directories
`.port-cache/optimization-uniforms/trace-command-{red-replay,green-replay,refactor}`.
Independent20ms oracle observed worker GL20.269708ms/CPU.084917ms and enclosing
producer wait20.348209ms/CPU.015625ms in frame1/job1. Both32768-event owner buffers
reported dropped0; actual completion ID joined. Invalid/profile-off cases also
pass. These prove telemetry boundary behavior, not native82s hitch attribution.

Intermediate trace build `.port-cache/builds/20261115T130854880411Z`, nativeARM64
status0, existing Docker image0b2fe029d90c/O3/LTO semanticflags unchanged.
RuntimeSHA256 `df595ad7210996bba1595a035e6e54c3e91ed64a070875821203bd09d4b0fa26`,
debug `cb04bff3f3f5204bb32e33895e9f3c88136e987adf28e2a8ee5eee6112094f6b`,
BuildID `ed280f827b1e548eeec5316917c50416d2952f1d`. Full LTO relink measured5m30;
intermediate never deployed. Drain slice RED14.667s against this runtime:
real clean SDL boundaries all finish0, failing required once-before-each-swap
oracle. Final drain/exit-anchor build follows; no result yet claimed here.

Trace keeps independent per-owner memory buffers, writes only after worker
joins, reports overflow counts explicitly. `.gl.csv` fields:
`lane,frame,elapsed_ms,event,api,wall_ms,cpu_ms,job,start_counter,end_counter,module,handler_offset`.
Each≥1ms driver command gets worker event plus exact current-ELF handler offset;
synchronous commands also retain API name. Every glReadPixels records even if
fast. Slow producer sync/backpressure and worker idle retain wall/threadCPU.
Every dispatch chunk records before current Swap/pacer; nested command/sync/chunk
scopes must not be added. Pacer sleep has own event. Chunk job serials and actual
Swap frame sequence support completion joins without racing producer guest
metadata. No per-draw file output or worker-shared append lock introduced.

Optional preSwap driver glFinish drains previously queued GL commands, recording
own wall/threadCPU event before existing SDL swap clocks start. Finish wall can
include driver execution, waiting and descheduling; it is not pure GPU time.
Remaining SDL swap may include previous pageflip, EGL, GBM-lock and display waits.
Forced drain changes overlap and is diagnostic, never acceptance optimization.
Independent next test injects20ms Finish and20ms SDL sleeps, checks exactly one
Finish before each real Swap, separate intervals/threadCPU, joined frames and
zero extra Finish calls with drain absent. [Khronos completion contract](https://raw.githubusercontent.com/KhronosGroup/OpenGL-Refpages/main/es3.0/glFinish.xml).

Startup and end anchors pair RAW/MONOTONIC/REALTIME brackets with SDL ticks,
performance counter/frequency; end anchor occurs after worker joins before trace
I/O. Context follows existing `SDL_Init(...SDL_INIT_TIMER)` and context creation;
trace does not initialize SDL timer earlier. Actual game ExitProcess uses exit,
not SDL_Quit; worker stop registered later executes before trace close. Exact
captured firmware SDL uses gettimeofday/frequency1e6, not presumed RAW. Historical
RAW→SDL placement bounds invalid; new paired values required. No claim startup
fixture establishes native steady frame overlap. Full exact provider proof and
source pins in [GPU audit](gpu_counter_probe.md).

Research refreshed before drain choice: current official PortMaster native/GPU
guides; first-hand SDL issue16003 (SDL3/Allwinner/lima, different provider); same
RK3326/G31 Strikers `fb1f0ced9d6fca453dbc029b7b43fd6c636127fe` uses drains but
different SDL3 shim/contexts. No synchronization code transplanted. Official
Khronos XHTML fetch rejected content type; official raw XML read instead.
PortMaster page timed out on refresh; previously read official guide and GPU
agent source audit retained applicability. No fetched instructions executed.
CCE current gl_thread/profile previews expanded as `Chunk not found`; scoped
known-file fallback used, unchanged queue/pacing behavior retained.

GPU-query observer audit: SH3_PROFILE alone never enables queries. Explicit
SH3_GPU_PROFILE unset/empty/0 returns before GL lookups/query/disjoint checks;
all current matched moving/level/static controls have unset/false, no GPU CSV
and no enabled log. Query-availability calls cannot explain their current waits.
Existing profile does retain per-draw/per-frame clocks, threadCPU, buffered CSV,
120-frame flushes, producer-targeted10ms-CPU signal sampler and sync census.
Full profiling-disabled actual mean-cadence/tail overhead remains unquantified;
no zero-cost claim. Existing profile-unset route+PEEK60-frame timestamps can
provide coarse no-new-C mean check, not actual-completion p95/p99 evidence.


### Software-cap0 resolution control, independent joins

Frozen485 static/fullstock/NoiseOffNormal pair uses explicit softwareFPS0 and
requested swap0; captured native SDL forcibly keeps interval1, so neither result
is unconstrained display/CPU throughput.55–95s completion IDs and producer
metadata join exactly in both, room210, true640 or320 as requested.

| Run / dimensions | SpanFPS / mean completion | WorkerCPU / swap wall / nested swapCPU | ProducerCPU / Present | p95 /p99 /max completion | Complete1s /5s floor |
| --- | --- | --- | --- | --- | --- |
| `20261115T130925612420Z-cc0b12`,640×480,856frames |21.37981 /46.783401ms |10.752086 /35.023314 /.443495ms |27.954675 /6.104069ms |51.1035 /55.41675 /56.115ms |19 /20.4 |
| `20261115T131314003359Z-9f2184`,320×240,1198frames |29.93772 /33.401925ms |10.65749 /13.032795 /.424047ms |27.855051 /.035169ms |34.19015 /34.998 /52.18ms |29 /29.8 |

Both buffers139964bytes every joined frame; draw counts374.495 versus367.376
mean. Same fixed pose is not identical animation/draw stream. Similar producer
and workerCPU, with22ms shorter Swap at320, reinforces resolution-sensitive
renderer/presentation bottleneck. Near30 at320 does not establish CPU ceiling;
remaining SDL/display/original-game rate limits unresolved. No changed resolution
counts as true640 fulfillment. Independent JSON outputs saved under
`.port-cache/runtime-attribution/` using corresponding run IDs.

### DMC-frequency causal control, independent join

`20261115T131715482349Z-410c67`,75–180s:2518/2518 unique completion IDs join
producer metadata, room210 true640×480. Frozen485/NoiseOffNormal/same moving
route; CPU1512/GPU520 in all36 samples, only DMC remains528 versus786 in matched
`d498a8`. Span23.98193FPS versus25.86971; mean41.702347ms,
p95/p99/max51.82075/53.86026/79.515ms; complete1s/5s floors18/19.
Joined producerCPU29.981365ms, workerCPU12.180870ms, swap28.529272ms with
nestedCPU.667981ms; producer draw3.124143ms/Present11.462596ms. These compare
with28.350181/10.626712/27.351750/.454086ms in full-DMC baseline. DMC-sensitive
critical path includes increased producer and worker CPU time; this control
does not establish pure GPU bandwidth saturation or locate particular memory
consumer. Low sampled external GPU handshake stalls do not rule out CPU-side
memory contention. Lead confirms all exit stages0, native identity,59 firmware
preservation checks and restoration;42 alive observations/41 positions. Five
ALSA reports include warm brackets79.536/129.850/162.999s. Independent output
`.port-cache/runtime-attribution/20261115T131715482349Z-410c67.json`.

### Final trace/drain candidate and focused validation

Final nativeARM64/O3/LTO build `20261115T132039539344Z` status0 reuses same
Docker image and semantic flags; no renderer/gameplay optimization added.
RuntimeSHA256 `1738d4ad3b98aa38729c8f59a561ffe0be2147ff29251974c5cacd272ddb082d`,
debugSHA256 `9e69f9988682d68122822db606a46e67111d29ec992f6799006b3867d138ec98`,
BuildID `63f7a416c27f5caed6d647ff87ea18dd8e3a53ca`. Immutable package retained at
`.port-cache/builds/20261115T132039539344Z/artifacts/runtime`; frozen485 primary
acceptance packages preserved. Final candidate trace-off matched device control
still required to quantify layout/control change versus485.

Drain first GREEN attempt14.787s exposed fixture's unjustified per-Swap35ms
upper bound: one measured SDL Swap50.630ms despite separate Finish21.274ms.
Runtime unchanged. External SDL observer now independently measures actual Swap
wall; comparison median error<2ms catches inclusion of distinct20ms Finish while
allowing driver/scheduler tails. Corrected GREEN31.407s:188 exact Finish/Swap and
completion-frame matches; median reported-vs-observer Swap error.053042ms,
median drain22.756209ms, both owner buffers dropped0. CPU timing excludes injected
20ms waits; drain-off and invalid-control/early-exit checks pass. REFACTOR review
retains explicit preSwap scope and owner-local buffers; regreen31.227s. Final
trace test regreen30.859s also passes against same173 artifact. Evidence
`.port-cache/optimization-uniforms/{drain-green-boundary,drain-refactor,trace-final-regreen}`.
These Docker results validate telemetry interface and preservation; native
trace-off/trace/drain moving-route comparisons remain separate device evidence.

### Supported graphics minimum: Blood Volume Little, actual UI and cold reload

Remaining standard Extra Options were surveyed through actual game, rather than
assuming numeric ordering. Captured menu lists Blood Color, Blood Volume,
Walk/Run, Map, Noise Effect, Display Mode, Low Health Effect and Exit. Blood
Volume labels are **Little / Normal / Much**, with values0/1/2. Existing matched
controls retained Normal1. Little0 is supported lower blood-effect setting;
Blood Color changes palette, not demonstrated workload. Walk/Run and Map are
input/map preferences, Low Health Effect already Off. Display Normal/Sharp
changes linear/point sampling of same composite pass; Sharp remains alternative
look and measured no gain, not automatic minimum. NoiseOff, LensFlareLow and
ShadowNo remain verified. No standard texture/DOF/fog/soft-shadow toggle was
found; hidden wrapper keys remain unmapped rather than certified minimum.

Known generated-source fallback after unrelated/stale CCE hits:
`sub_005E5130` Extra UI uses temporaryBCC1AB; apply `sub_005E5BF0` calls
`sub_0060CC40`, storing persistent byte0x070E66CB; getter `sub_0060CC50`.
Blood-effect consumers `sub_005B9A90` and `sub_005BA050` scale parameters by
selected volume. First consumer selects50/80/100 for0/1/2 and100/100/150 for
another effect parameter. This proves supported effect reduction, not exact
saved draw count. BloodColor setter/getter0060CC20/0060CC30 use0x070E66CA;
`sub_005A12D0` selects one of four palette pointers with unchanged surrounding
control flow. No performance gain claimed from alternate blood colors.

Actual UI automation saved in ignored
`.port-cache/graphics-map-20261115/{blood-replay.py,blood-session.py}`. It changes
BloodNormal→Little with normal key input and OptionsApply, no guest write hook.
First70s attempt ended before serialized settings; independent cold reload
correctly showed Normal, so excluded. Second85s attempt serialized Little but
old outer82s deadline reported1. That outer failure is retained, not represented
as clean shutdown. Independent48s cold reload `verifyblood-v2-1` then exited0,
returned frontend and displayed Little/NoiseOff/DisplayNormal with persistent
word0x070E66C8=00000F0F (blood byte0). Screenshot inspected at
`.port-cache/graphics-map-20261115/verifyblood-v2-1.png`.

Isolated quality-only seed
`.port-cache/issue-13-limits/seed-blood-little-20261115T135000Z` copies only that
serialized data.sys onto verified true640/1/1 baseline. UI replay's own512²
disp.ini is not transferred. Identity manifest `blood-little-identity.json`
preserves failed-attempt history and cold-reload proof. All owner/original seeds
remain unchanged; device lead owns separate cold-cache copies.

| Seed item | SHA256 |
| --- | --- |
| New data.sys, Little/NoiseOff/Normal | `c41256a3920705ed09996ceb11bb474c8e437de524eff52819c4adc782c573d0` |
| Unchanged room210 data.001 | `fa2d9fd1b7c1e2af9b9b771b2a996f988f5b82bdd8cda41d045975f31b787515` |
| Unchanged true640/LowFlare/NoShadow disp.ini | `27a40ce6f83f520e5ac9a8b2511796ee7a63ea9166439db42e4f69420f31e600` |
| Unchanged program cache | `18aa01444714fbc1acb41ffbcdcc141da02138f62b5023fe12b0e2faab68d8c4` |
| Unchanged GL cache | `06a34b1c4626beb59feaacd676c4719f3e0b3562dd846b47c26e20b48e2c821d` |

### Final173 regression and observer control, independent joins

Final173 existing GLES suite passes35 tests in124.812s, no skips, covering pixel
oracles, queued uploads, context/resource identity, RHW/copy/presentation metadata,
uniform caches and threading. Evidence
`.port-cache/optimization-uniforms/final173-gles-regression`. No broad suite
repeat is needed solely for subsequent diagnostic conditional.

Same75–120s room210 moving window, true640, BloodNormal/NoiseOffNormal,
full stock policy, software30 cap, firmwareforced interval1:

| Candidate / run | Unique joined completions | SpanFPS | WorkerCPU / Swap wall / nested SwapCPU | ProducerCPU / draw / Present | Draws / uploaded bytes |
| --- | --- | --- | --- | --- | --- |
| Frozen485 `d498a8` |1109 |24.65071 |10.637961 /29.358002 /.455518ms |28.544063 /3.064665 /11.468697ms |374.955816 /140178.809739 |
|173 trace-off `5917d6` |1067 |23.72210 |10.808196 /30.551149 /.449752ms |28.313926 /3.088452 /13.482664ms |370.314902 /140218.230553 |
|173 full trace `83a5af` |740 |16.43793 |29.432996 /28.997296 /.390594ms |27.729471 /3.150420 /32.562351ms |368.231081 /140169.686486 |

Frozen485→173 trace-off differs−3.77% in this single moving pair. Both18 alive
observations/18 positions/health100, but actual camera positions and animation
stream vary. No proof that trace-off control/layout costs exactly3.77%, and no
zero-overhead claim. Trace-off completion mean42.161199ms, p95/p99/max
50.867/54.8153/69.020ms, complete1s/5s floors18/19.6. Frozen485 matching window
mean40.567771, p95/p99/max46.356/48.41868/68.295, floors21/22.6.

Full trace is materially intrusive: **+18.624800ms workerCPU/frame**, −30.71%
FPS versus same173 trace-off. Its completion mean60.841984ms, p95/p99/max
67.7033/70.14104/94.734ms, floors14/14.8. Both lane dropped counts0,2482 producer
and6216 worker retained events,855750-byte CSV; buffer loss does not explain
slowdown. Full mode reads THREAD_CPU on *every* command start and SDL counter
at start/end, even though only≥1ms events receive second CPU clock/retention.
CSV flush happens after worker join. Thus few retained async rows do not imply
low observer cost. Do not use this run's timings as ordinary gameplay ceiling.

Fulltrace still provides bounded hypothesis identity: sole ReadPixels at51.127s,
frame1325/job3046, worker31.074ms/CPU1.321249ms and producer31.569ms. It does not
coincide first-turn82s hitch in this perturbed run. At82.199s frame1806 producer
sync glCreateProgram waits70.867ms/CPU.142333ms, job3548; next worker
glProgramBinary1.027ms/CPU.979708 at82.200s. Queued resource creation is stronger
hitch candidate than ReadPixels at82s, but exact normal cost remains unmeasured.
Extraction `.port-cache/runtime-attribution/173-fulltrace-readback-turn.json`
retains paired counters, module offsets, readback and turn-frame events.
Matching173 debugELF Docker addr2line resolves slow async80.846s offset19e53f0
to run_glVertexAttribPointer (gl_thread.c199),4.064ms wall/.052792CPU. Other
retained offsets resolve run_glCreateProgram19e5d10, run_glProgramBinary19e5980,
run_glReadPixels19e57a0. This isolated perturbed4ms async event does not explain
82s70ms producer wait; symbol identity included in extraction JSON.

Current source already has program prewarming: shader_bind_for_draw calls
progcache_warmup, which builds cached records whose guest shader hash handles
exist. Pending records become eligible after progcache_shader_created, but build
waits until next draw because game may create shaders on loading thread without
GL context. `build` first calls synchronous glCreateProgram, then
program_binary_load, link-status check and uniform-location queries. Actual
fulltrace log has47 cached records,16 built up front,47 binary restores and0
misses. Thus remaining31 cached programs were created later; binary hit does
not mean program-object setup was all paid at startup. Safe next research is
remaining eligible program setup during loading/prewarm phase, preserving shader
lifecycle/context/order. Do not reimplement existing warmup, attribute70.867ms
wait to shader compiler, or assume scheduling that setup removes mean render
deficit. CCE returned current-file compressed preview but expand_chunk failed
`Chunk not found`; scoped d3d8_shader.c/program_binary.c fallback reviewed.

Concrete unvalidated two-stage design, distinct from existing warmup: binary
records already retain exact vertex/fragment GLSL strings plus binary payload,
format, checksum and provider fingerprint. Native program creation/loading and
uniform-location queries could therefore occur before guest shader handles
exist, keyed by those stable source identities. Later attach object to Prog/key
once guest shader hashes resolve. Current build assigns constant_count from
vs_of(k->vs), so guest-specific metadata must wait rather than inventing handles
or parsing constants differently. Requires bounded extra native objects/memory,
same worker/context, fingerprint/fallback handling, correct binding-cache reset
and pixel/lifecycle tests. Driver may still defer work until first actual use.
This is source-admitted design candidate, not implemented fix or quantified gain;
coarse capture must first establish ordinary hitch's queue class.

### Producer CPU hotspot attribution includes inlined instructions

Exact frozen485 d498a8,75–180s:7699 samples,7301 game-module PCs. DWARF
innermost frame attributes1182 (15.3526% of all samples) to recomp_fp_round24.
Exact173 trace-off5917d6,75–120s:3021 samples,2863 game-module PCs;498
(16.4846%) innermost round24. These are **inlined instructions**, not standalone
helper-call frequency. Matching debugELF `addr2line -f -i` resolves173PC0x17dd608
to recomp_types.h274 inline into sub_00648639 at recomp_0040.c21555;485
PC0x17dd50c similarly resolves round24.h276 then same guest function. This does
not contradict earlier2ac6 post-LTO zero standalone-call classification.
Renderer-source PCs300/3021 and784/7699 respectively≈10%; samples measure
producer thread CPU only, excluding worker, GPU and blocked presentation time.
No numeric shortcut/optimization is justified without independent precision
oracle. Exact identities/inline chains retained in
`.port-cache/runtime-attribution/{173,485}-producer-hotspots.txt` and run-specific
`*-samples.json`; sample helper is read-only analysis, so TDD not applicable.

### Coarse trace response to measured observer cost: bounded TDD slice

User-authorized diagnostic only, default gameplay unchanged. New opt-in
`SH3_GL_TRACE_COARSE=1` requires nonemptySH3_PROFILE and SH3_GL_TRACE=1. It
retains worker chunk wall/CPU, sync command identity including every ReadPixels,
producer waits, worker idle, pacer and optional drain. Async commands execute
without individual trace clock reads; enclosing chunk still measures their cost.
Full trace remains available explicitly and mode is logged. Current code
retrieval again returned stale/unrelated CCE chunks; scoped current
gl_thread.c/rt_core.c fallback used, rather than trusting indexed old source.

Actual173 launcher→game RED14.719s: independent worker glClear sleep20.534ms
and sync glGenTextures21.330ms executed, ExitProcess0/frontend restored, coarse
mode missing. Old full mode retained injected async command20.568458ms despite
requested coarse. RED evidence `.port-cache/optimization-uniforms/coarse-red`.
Minimal implementation changes one dispatch conditional, startup mode log and
pre-guest flag validation. Single nativeO3/LTO build20261115T135522858288Z
passes0. RuntimeSHA256
`becbc930874e09b528adab3d9b885fc5272718522475ec14ba6156f7ffb27b68`,
debugSHA256 `0b085784f40334bb65b10eecfd25c32f14da968b435392d06fbf49b0c7b14889`,
BuildID `3fb27c01011a3612d1763f6be70b4361fa94435c`; retained immutable package
`.port-cache/builds/20261115T135522858288Z/artifacts/runtime`. No other new
runtime behavior or build planned.

GREEN17.317s: external glClear20.542ms lies fully within one worker chunk
50.738750ms/CPU.130083ms, while zero async-command rows are retained.
Synchronous GenTextures30.150875ms/CPU.054916ms remains individually captured
with matching producer wait/job/frame and actual completion. Both buffers
dropped0. Six invalid/dependency cases return2 before save/device creation.
REFACTOR review retains minimal owner-buffer/conditional design; regreen17.147s.
Evidence `.port-cache/optimization-uniforms/{coarse-green,coarse-refactor}`.
Existing fulltrace30.891s, drain31.238s and actual default-profile checkpoint
62.986s regressions all pass on samebecb artifact, no skips. Full mode logs full;
diagnostic-off default preserves room210 true640 metadata, CPU/Swap sleep oracle,
no capture/GPU queries, owner state and frontend return. Evidence
`.port-cache/optimization-uniforms/{coarse-final-fulltrace-regreen,coarse-final-drain-regreen,coarse-final-default-checkpoint}`.
Final READY sent to device lead; no more runtime features/builds planned. Native
coarse observer/drain comparisons are completed below. Docker setup sleeps are
validation oracles, not estimates of device GL costs. Ordinary threaded mode
is required; SH3_GL_THREAD=0 with requested trace is unsupported diagnostic use.

Fresh blocker searches checked current official
[PortMaster FNA guide](https://portmaster.games/contribute/porting/engines/fna/),
[working Cuphead measurement recipe,1b7e7b0](https://github.com/wild1walker/portmaster-cuphead/blob/1b7e7b019dabeb4226a1b4be5bfdd854895242f5/docs/technical.md#tests-and-measurements),
[same-SoC Strikers shim,fb1f0ce](https://github.com/jbcgames/smstrikers-rk3326/blob/fb1f0ced9d6fca453dbc029b7b43fd6c636127fe/smstrikers-port/extern/aurora/lib/webgpu/sdl2shim_present.cpp)
and [Linux per-thread CPU clock contract](https://man7.org/linux/man-pages/man3/clock_gettime.3.html).
Cuphead alternating unattended configurations support observer controls;
Unity/Mono and Strikers' SDL3 shim/context design differ. Official guide's
render-target examples motivate causal profiling, not copying settings or
graphics cuts. No exact PortMaster/RK3326 per-GL THREAD_CPU overhead workaround
found in bounded searches (`PortMaster profiling clock_gettime overhead`,
`RK3326 GL thread CPU profiling overhead`, `R36S Strikers glFinish perf`).
Kernel clock contract does not establish actual syscall/vDSO cost on this
firmware. Coarse choice follows measured18.625ms cost, not guessed clock latency.

### BloodLittle173 fixed640 cold/warm, independent joins and program census

Lead owns isolated cache stripping/roundtrip and device preservation evidence.
No new settings/build; same173/BloodLittle/NoiseOffNormal/LowFlare/NoShadow,
true640, full stock1512/520/786. "Cold" here clears application program caches;
it does not claim empty kernel file/page cache or cold hardware state.

| Run |55–95s joins / SpanFPS | Mean completion / p95 / p99 / max | WorkerCPU / Swap / nestedCPU | ProducerCPU / draw / Present |
| --- | --- | --- | --- | --- |
| `20261115T134954008713Z-507725`, cold caches |920/920 /22.98994 |43.496684 /47.8939 /48.98844 /54.504ms |10.866900 /31.766082 /.456692ms |27.486725 /3.055641 /15.809012ms |
| `20261115T135726264524Z-899c2e`, resulting caches |905/905 /22.63962 |44.176566 /49.2296 /50.71996 /56.976ms |10.918557 /33.038450 /.449474ms |27.541001 /3.059598 /16.408355ms |

Both room210 and metadata/dimensions match exactly on joined IDs; steady-window
warmth does not improve this fixed640 mean. First room frames differ materially:
cold1229@47.505s completion2293.356ms/workerCPU1717.890121ms, followed by
699.142ms/worker626.864005ms; warm1248@48.851s completion693.925ms/workerCPU
154.614236ms, followed by64.077ms/worker15.405251ms. First room208 draws and
3,100,664 uploaded buffer bytes match. ProducerCPU remains563.716140 versus
554.547011ms, showing substantial loading CPU persists despite warm programs.
These are overlapping producer/worker lanes and must not be added as serial time.

Native launcher stdout records whole-run synchronous producer queue waits:

| API | Cold calls / total wait | Warm calls / total wait |
| --- | --- | --- |
| glCompileShader |62 /558.606ms |0 |
| glLinkProgram |31 /2289.936ms |0 |
| glCreateProgram |31 /235.913ms |31 /16.019ms |
| glProgramBinary |0 |31 /32.870ms |
| glGetUniformLocation |930 /29.750ms |930 /26.512ms |

Cold0restore/31miss/31writes versus warm31restore/0miss/0writes; warm31 records,
13 built up front29ms. This validates removed compile/link path and reduced
first-use workerCPU. Queue totals include previous work, contain no command
timestamps and are not pure driver execution; cannot attribute entire first-room
stall to particular operation or exclude asset/page-cache effects. Census saved
`.port-cache/runtime-attribution/173-cold-warm640-program-census.json`; per-window
JSONs include run ID and55–95s bounds. Matched320 results follow below.

Completed matched173/BloodLittle320 pair, independent55–95s joins:

| Run | Joins / SpanFPS | Mean / p95 / p99 / max completion | Complete1s/5s floor | WorkerCPU / Swap / nestedCPU | ProducerCPU |
| --- | --- | --- | --- | --- | --- |
| `20261115T140116608881Z-ea97cb`, cold caches |1197/1197 /29.93967 |33.399370 /34.1838 /35.5528 /86.504ms |28 /29.6 |10.689502 /13.715019 /.407983ms |27.571551ms |
| `20261115T140511267080Z-93a47a`, resulting caches |1200/1200 /30.00050 |33.332237 /34.3311 /35.84539 /39.810ms |30 /30 |10.819448 /13.135762 /.427187ms |27.771342ms |

Both room210 and internal320×240 metadata match, uploaded buffers139964bytes
every warmed frame. Similar≈27.5ms producer/≈10.8ms worker CPU at both
resolutions, with much shorter320 Swap, reinforces resolution-sensitive
renderer/presentation deficit. Software30 cap and forced interval1 remain;
near30 does not measure unconstrained CPU ceiling or fulfill640 requirement.

Cold320 first room1225@47.723s:2357.974ms/worker1731.127994ms, then697.491ms/
worker627.937911ms. Warm1247@45.966s:709.242ms/worker153.226505ms, then65.983ms/
worker16.461085ms. First frame208 draws and3,100,664bytes match; producer CPU
561.661624 versus557.330087ms again persists. Whole-run cold60CompileShader
wait554.254ms/30LinkProgram2312.405ms→warm30ProgramBinary31.541ms, no compile
or link calls;30restore/0miss and12 of30 keys built up front28ms. Exact cause
limits from640 census apply. Output
`.port-cache/runtime-attribution/173-cold-warm320-loading-program-census.json`.

Lead confirms all four execution/collection/preservation/restore checks pass.
Cold320 has five ALSA underrun reports, one bracketed by sparse observations
73.652–75.706s. Its warm-window worst frame2028@75.336s is86.504ms with
Swap67.113ms/SwapCPU.352042ms and workerCPU10.676751ms. Same broad bracket is
temporal association only, not proof that audio or scheduler caused stall.
Warm320 has no logged ALSA underrun and39.810ms maximum in measured window.

### Finalbecb minimum-profile moving control before coarse/drain attribution

`20261115T140929993471Z-d958cc`, finalbecb/BloodLittle/NoiseOffNormal/LowFlare/
NoShadow, original warmed47-program caches, true640, software30 cap, forced
SDLinterval1 and full stock policy. Lead verifies exact deployedSHA, all exit
stages0, owner/firmware preservation, governor restoration and frontend return.
This quality/cache state differs from earlier173/BloodNormal moving controls;
upcoming coarse/drain comparisons use same finalbecb seed and binary.

Independent75–120s:1144/1144 unique completion IDs join producer metadata,
room210. Span25.4248599FPS, mean39.334863ms, p95/p99/max
45.13225/46.24726/67.410ms, complete1s/5s floors21/23.2. ProducerCPU
28.392005ms/draw3.154042ms/Present10.495112ms; workerCPU10.855826ms/
Swap28.012106ms/nestedSwapCPU.454123ms. Draws373.252622, buffers140194.069930
bytes mean. No final30FPS or sustained25-floor acceptance.

Recurring first A-turn remains: frame2170 producer@82.190s wall72.238ms,
CPU35.728002ms, draw41.654ms, Present.050ms; same completed frame@82.225s
67.410ms with Swap30.314ms, workerCPU14.396082ms, nestedSwapCPU.445375ms.
This establishes recurrence without detailed trace; coarse case will classify
queue/dispatch/wait intervals rather than infer scheduler or slow GL call.
Independent output
`.port-cache/runtime-attribution/20261115T140929993471Z-d958cc-75000-120000.json`.

### Warm first-room producer CPU: bounded frame-tagged samples

Existing173 warm-cache captures permit sampling exact first-room producer frame,
without another device run or runtime change. At640,899c2e frame1248 ends
48.836s with554.547011ms producer CPU; at320,93a47a frame1247 ends45.954s
with557.330087ms producer CPU. Each frame carries56 CPU samples. The ignored
summary JSON selectors48.836–48.837s and45.954–45.955s select these **whole
frame tags**, not1ms slices of loading work. Worker completion ends15/12ms
later and must not select producer samples by that later timestamp.

| First-room producer sample attribution |640 frame1248 |320 frame1247 |
| --- | --- | --- |
| Total / native runtime / libc samples |56 /45 /11 |56 /45 /11 |
| Recompiled guest `sub_*` innermost PCs |33 |33 |
| `upload_pixels` |6 |4 |
| Guest string/token cluster `0063EA88` / `0063F980` / `0063FE98` / `006407CF` |6 /3 /2 /0 |4 /4 /5 /2 |

Matching173 debug ELF resolves all `upload_pixels` samples to
`src/d3d8/d3d8_res.c:285–288`, the RGBA scratch conversion/channel-swizzle loop.
These samples identify producer texture preparation, not driver execution or
blocked file I/O. Other renderer-source PCs total7/56 and5/56, respectively.
Generated `recomp_0039.c` confirms string scanning for `_`, character/newline
handling and `#` branches in this anonymous guest cluster; its precise semantic
owner remains unproved. Do not rename it decompression, asset parsing or shader
assembly solely from these PCs. `sub_00667A7F` adds5/4 samples but remains
semantically unclassified. This loading lane differs from the steady-state
round24 hotspot: no round24 sample at640 and one at320.

`profile_cpu.c` uses a10ms `CLOCK_THREAD_CPUTIME_ID` signal timer aimed at the
producer OS thread; `profile_present` advances `sample_frame` for next frame.
Whole-run logs report3617 samples/3 dropped and4934/7, writes successful;
frame-specific loss cannot be recovered. PC DWARF attribution includes inlined
sites; saved link register is a caller hint, not a full call stack. Small56-sample
frames support path candidates rather than precise timing percentages. Blocking
I/O, worker CPU and GPU/display waits remain outside this sampler. No collected
I/O trace separates asset reads/page-cache effects from CPU preparation.

CCE exact function queries returned older artifacts or unrelated chunks rather
than current function source; bounded fallback read current known sampler,
`d3d8_res.c` and generated function bodies. Data-only ARM64 Docker `addr2line`
used matching173 debugSHA; no compile or new diagnostic seam. Saved summaries:
`.port-cache/runtime-attribution/20261115T135726264524Z-899c2e-samples.json` and
`.port-cache/runtime-attribution/20261115T140511267080Z-93a47a-samples.json`.

### Native coarse trace: observer bound and recurring program-setup bubble

`20261115T143222756103Z-14a5a0` uses exactbecb minimum-profile moving seed,
same120s route and75–120s window as trace-offd958cc. All stages0 and source
preserved; lead checks deployed identity, three restored stock policies and
frontend return. Earlier4b1e0c attempt failed before game due device ENOSPC;
it provides no native runtime failure or performance evidence.

| Same-package minimum-profile moving case |Trace off d958cc |Coarse14a5a0 |
| --- | --- | --- |
| Unique completion/producer joins |1144/1144 |1075/1075 |
| Span FPS / complete1s/5s floor |25.42486 /21 /23.2 |23.89162 /20 /20.8 |
| Mean / p95 / p99 / max completion ms |39.334863 /45.13225 /46.24726 /67.410 |41.863555 /48.8331 /51.42262 /76.017 |
| Producer CPU / worker CPU ms |28.392005 /10.855826 |28.239214 /11.059507 |
| Swap wall / nested CPU ms |28.012106 /.454123 |29.581927 /.446771 |

Coarse logs mode explicitly, producer3113/worker6856 events and **zero drops
both lanes**; no async per-command rows. Full-trace additional18.6ms worker CPU
collapse is removed: coarse worker CPU differs by+.203681ms. Yet measured
coarse FPS is6.03% lower than off in this single moving pair. Different pose/
animation/draw mix and run conditions confound exact observer attribution;
neither zero-cost nor unperturbed absolute latency is established. Qualitative
ordered event attribution remains useful.

Recurring first-turn frame2146: producer79.354ms, CPU35.806753ms, draw49.014ms,
Present.050ms; same completion76.017ms, workerCPU15.137794ms, Swap31.267ms/
CPU.370125ms. Producer `glCreateProgram` job3888 waits40.108ms/CPU.152251ms.
Worker enters that published chunk **31.376ms after producer wait begins**;
previous frame2145 Swap32.713ms overlaps this queue delay. Chunk3888 then
takes8.614ms/CPU5.428208ms including preceding queued draw commands and call.
Actual worker `glCreateProgram` row is absent with zero drops, bounding that
observed command below1ms trace threshold. This is not40ms shader compilation.
Following `glProgramBinary` worker call is1.030ms/CPU.980000ms; producer waits
1.200ms. Exactbecb debug ELF resolves offsets19e5d50/19e59c0 to respective
`run_glCreateProgram`/`run_glProgramBinary` wrappers, lines366/239.

Frame2146 crosses67 dispatch chunks,20.242ms total chunk wall/13.199077ms CPU;
these contain individual commands and overlap producer waits. Later worker
ready-chunk idle intervals3.069ms and18.459ms show producer feed gaps during
same first-use setup frame. Its3.093ms pacer event occurs **after** that frame's
completion and belongs inside following inter-completion interval; do not add it
to same frame's completion wall. Across joined warm IDs, dispatch wall11.495194ms
per frame, recorded idle.020026ms and pacer.677839ms;171 pacer events total728.677ms.
Pacing explains only bounded portion of this observed warm deficit, not entire
Swap. Producer waits, worker chunks, commands and frame CPU are nested or
overlapping; do not add CPU lanes or command/chunk totals to frame totals.

Sole readback occurs51.074s, frame1363/job3084: worker30.092ms/CPU1.241331ms,
producer30.520ms. Exact handler19e57e0 resolves `run_glReadPixels`, line226.
It is outside82s turn, so cannot explain recurring hitch. Cached-program lazy
handle creation exposes prior-frame queue wait plus many synchronous setup
roundtrips; two-stage early native-handle preparation described above remains
an unimplemented design candidate, not another claim that existing#14 cache
warmup was absent.

Actual clock anchors report performance frequency1,000,000. Start/end perf span
120.053014s versus MONOTONIC120.053013s and REALTIME120.053013s; endpoint
agreement shows no material endpoint wall-clock step in this run. RAW span
120.055666s differs and must not be substituted for SDL gettimeofday clock.
Fine event ordering uses common saved performance counters, while SDL tick
labels retain millisecond quantization. Endpoint agreement alone cannot prove
absence of an intermediate clock adjustment.

CCE current `gl_thread.c` expansion again returned `Chunk not found`; bounded
fallback read exact known current queue/trace scopes. Source threshold1ms and
zero drops support missing synchronous-call bound; intentionally unobserved
async commands have no such per-call bound. Analysis is read-only research,
not executable behavior change. Saved independent join JSON and
`.port-cache/runtime-attribution/becb-coarse-observer-hitch.json` retain clocks,
complete hitch events, matching debugSHA and observer comparison.

### Final pre-Swap drain: deferred completion wait, with explicit pacing confound

`20261115T143559336520Z-331517`, samebecb/minimum-profile seed/route/stock
clocks, adds only coarse pre-Swap `glFinish`. Lead verifies all stages0, exact
native identity, source/firmware preservation, policy restoration and frontend
return; no game remains running. Trace producer2518/worker9354 events, both
drop counts0. Same75–120s window:622/622 unique joined true640 room210 frames,
span13.839674FPS, mean72.263796ms, p95/p99/max79.79585/81.18297/106.317ms,
complete1s/5s floors12/12.6. This is an intentionally perturbed diagnostic,
not acceptance performance or ordinary GPU cost.

All622 completion IDs have their own drain event. `glFinish` wall mean
28.659817ms, p50/p95/p99/max27.389/35.43665/36.36886/37.704ms; nested thread
CPU mean.242400ms. Following SDL Swap falls to.300027ms wall/.218754ms CPU
versus coarse-control29.581927ms/.446771ms. A large deferred graphics
completion/synchronization wait can therefore move before Swap, rather than
being entirely unavoidable SDL call overhead. `glFinish` wall includes blocked
completion and scheduling, not pure GPU active execution. Altered buffer/timing
state prevents assigning exact ordinary-frame GPU versus pageflip/display
shares from this contrast alone.

Crucial observer interaction: `swap_now` takes/returns Swap-start counter **after**
diagnostic drain; existing `pace_frame(start)` then phases its deadline from this
later point. Recorded pacer adds33.076947ms per joined frame versus.677839ms in
coarse control. Its additional32.399108ms explains almost all30.400241ms mean
frame increase after smaller dispatch/Swap changes. This13.84FPS result must
not be called a doubled graphics workload, isolated pipeline serialization cost,
or rendering limit.

| Diagnostic phase wall per joined ID |Coarse |Coarse + drain |
| --- | --- | --- |
| Dispatch chunks |11.495194ms |10.065215ms |
| Explicit drain |Absent |28.659817ms |
| SDL Swap |29.581927ms |.300027ms |
| Recorded post-completion pacer |.677839ms |33.076947ms |
| Recorded ready-chunk idle |.020026ms |.034778ms |
| Worker CPU, nested phase CPU included |11.059507ms |10.416601ms |

Phase rows illustrate window balance, not exact same-frame addition: post-
completion pacer contributes next interval; edge/clock/logging gaps remain.
Producer CPU27.451830ms/draw3.200723ms/Present44.017759ms; blocked producer
Present follows worker completion, not independent extra graphics execution.

First-turn frame1953 recurs at82.3s: producer144.995ms/CPU35.612789ms/draw
115.056ms, completion106.317ms/worker15.174250ms/Swap.267ms. Producer
`glCreateProgram` wait106.018ms/CPU.256667ms starts100.644ms before worker
enters chunk3695; preceding frame includes33.555ms drain and34.210ms pacer.
Chunk3695 itself5.260ms/CPU5.261958ms; actual Create call again below1ms
retention threshold with zero drops. Next Binary command1.090ms/CPU1.038333ms.
Later worker ready-chunk gaps3.094/18.538ms recur. Thus added diagnostic
pacing enlarges already-established queued first-use setup bubble; it does
not turn Create into100ms shader compilation. Sole ReadPixels remains startup
51.180s, worker30.632ms/CPU1.241627ms, outside first turn.

Start/end paired anchors and exact provider log retained. SDL perf span
120.149788s, MONOTONIC120.149788s, REALTIME120.149788s agree at endpoints;
SDL clock remains gettimeofday, not RAW. Raw trace/order and independent
frame joins saved in `.port-cache/runtime-attribution/becb-coarse-drain-phases.json`
and run-specific75–120s JSON. No further runtime change, provider replacement,
new diagnostic feature or hardware run follows this bounded attribution.

### Runtime handoff: measured remaining budget and bounded next work

Finalbecb trace-off minimum-profile moving mean39.334863ms requires removing
6.001530ms/frame to reach33.333333ms:15.26% less frame time or18.00% greater
throughput. Hard fixed-pose warm640 minimum-profile173 mean44.176566ms
requires10.843233ms/frame,24.55% less frame time or32.53% greater throughput.
Different binary/cache-route contexts remain explicit; these are measured
workload budgets, not a physical SoC ceiling. Moving1s/5s floors21/23.2 and
67.410ms maximum also show why average-only improvement cannot establish
smoothness. Three other bounded640 levels approach30, so failure is workload
dependent, not universal incompatibility with640 output.

Actionable work follows separate measured limits:

- Steady heavy-room critical path includes≈11ms worker CPU/dispatch plus long
  deferred graphics/presentation wait, alongside≈28ms overlapping producer
  CPU. Resolution, GPU clock and DMC controls identify graphics/memory
  sensitivity; counter-active gaps and forced SDL interval1 prevent declaring
  full GPU saturation or pure shader/bandwidth/display ceiling. Future pass-
  scoped work needs validated GPU coverage and default-off controls, preserving
  actual supported minimum profile, pixels and gameplay.
- Recurring first-turn setup waits behind previous frame and crosses many
  synchronous chunks despite binary-cache hits. Validate two-stage cached
  native-handle preparation with bounded memory/lifecycle and late guest
  metadata attachment; existing ready-key#14 warmup already operates. Both
  coarse and drain bound actual Create call below1ms and Binary≈1ms, so
  optimizing GLSL compilation alone would miss this queued warm-cache hitch.
- Cold caches add large first-use worker CPU, reduced by working binary cache;
  warm loading still consumes≈0.56s producer CPU. Existing56-sample frame
  captures implicate CPU texture conversion plus anonymous guest parser paths,
  not an identified file-I/O bottleneck. Exact asset/I/O attribution remains
  unmeasured, and faster storage must not be promised as the cure.

Full per-command trace has material clock-observer cost and is unsuitable for
ordinary performance claims. Coarse trace removes its CPU collapse but retains
single-pair≈6% mean perturbation/route uncertainty. Drain adds a demonstrated
pacing interaction; its13.84FPS is not a shipping regression. Ordinary PROFILE
mean control, detailed trace and hardware-counter observer bounds are distinct.
Exact SDL provider, clock correction and old retracted RAW frame-placement
claims remain recorded above and in renderer notes.

No further C edits/builds follow finalbecb. Relevant native launcher behavioral
validation remains coarse RED→GREEN→refactor regreen, existing full trace and
drain regreen, default checkpoint, plus previously passed17335-case GLES
suite; exact paths/identities recorded above. Read-only analysis and note edits
need no behavioral TDD; CSV unique IDs, metadata equality, matching debugELFs,
zero trace drops and final `git diff --check` validate research handoff. Changes
remain local/uncommitted; issue closure and640 stable30 acceptance remain open.
