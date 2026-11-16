/* Optional CPU-side timings. GPU drain requires explicit SH3_GL_DRAIN diagnostic. */
#pragma once
#include <stdint.h>

uint64_t profile_stamp(void);
void profile_draw_end(uint64_t start);
void profile_buffer_upload(uint32_t bytes);
void profile_present(uint64_t start, uint64_t swap_start);
/* Capture guest metadata on producer; only worker owns completion report. */
typedef struct ProfileSwap {
    int enabled, frame;
    uint32_t room, width, height;
} ProfileSwap;
ProfileSwap profile_swap_snapshot(void);
/* On-CPU time of caller, not elapsed time or GPU work. Swap CPU is nested in
 * completion-owner CPU; queued mode reports worker, synchronous mode producer. */
double profile_thread_ms(void);
void profile_swap_end(ProfileSwap frame, uint64_t start, double cpu_start);
void profile_cpu_start(const char *path);
void profile_cpu_frame(int frame);

/* Diagnostic timeline: owner-local buffers, written only after GL worker joins.
 * Chunk/command/sync intervals nest; do not sum them as independent CPU lanes. */
typedef struct ProfileSpan { uint64_t counter; double cpu; } ProfileSpan;
int profile_trace_start(void);
ProfileSpan profile_trace_begin(void);
void profile_trace_end(ProfileSpan span, int worker, int frame, const char *event,
                       const char *api, uintptr_t handler, uint64_t job, int always);
