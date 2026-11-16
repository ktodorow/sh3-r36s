#define _GNU_SOURCE
#include "d3d8.h"
#include "profile.h"
#include <dlfcn.h>
#include <time.h>

static FILE *report;
static int checked;
static double counter_ms, previous_cpu;
static uint64_t previous_frame, draw_ticks, buffer_bytes;
static unsigned draws;

enum { TRACE_CAPACITY = 32768 };
typedef struct TraceEvent {
    ProfileSpan start;
    uint64_t end, elapsed, job;
    double cpu;
    const char *event, *api;
    uintptr_t handler;
    int frame;
} TraceEvent;
typedef struct TraceLane { TraceEvent *events; unsigned used, dropped; } TraceLane;
static TraceLane trace_lanes[2];
static FILE *trace_report;
static void trace_clock(const char *label);

static void trace_close(void) {
    if (!trace_report) return;
    /* Worker cleanup registered later, so it has joined before this anchor.
     * Game exit has no SDL_Quit call: timer remains live throughout correlation. */
    trace_clock("profile_clock_end");
    for (unsigned lane = 0; lane < 2; lane++) {
        TraceLane *owner = &trace_lanes[lane];
        const char *name = lane ? "worker" : "producer";
        for (unsigned i = 0; i < owner->used; i++) {
            const TraceEvent *e = &owner->events[i];
            Dl_info info = {0};
            if (e->handler) dladdr((void *)e->handler, &info);
            fprintf(trace_report, "%s,%d,%llu,%s,%s,%.6f,%.6f,%llu,%llu,%llu,%s,%llx\n",
                    name, e->frame, (unsigned long long)e->elapsed, e->event, e->api,
                    (e->end - e->start.counter) * counter_ms, e->cpu - e->start.cpu,
                    (unsigned long long)e->job, (unsigned long long)e->start.counter,
                    (unsigned long long)e->end, info.dli_fname ? info.dli_fname : "-",
                    (unsigned long long)(e->handler - (uintptr_t)info.dli_fbase));
        }
        rt_log("profile_gl_trace lane=%s events=%u dropped=%u", name, owner->used, owner->dropped);
        free(owner->events);
        owner->events = NULL;
    }
    if (fclose(trace_report)) rt_log("profile: GL trace report write failed");
    trace_report = NULL;
}

static uint64_t clock_ns(clockid_t clock) {
    struct timespec t;
    clock_gettime(clock, &t);
    return (uint64_t)t.tv_sec * 1000000000 + t.tv_nsec;
}

static void trace_clock(const char *label) {
    uint64_t raw0 = clock_ns(CLOCK_MONOTONIC_RAW), mono0 = clock_ns(CLOCK_MONOTONIC);
    uint64_t real0 = clock_ns(CLOCK_REALTIME);
    uint64_t ticks = SDL_GetTicks64(), counter = SDL_GetPerformanceCounter();
    uint64_t real1 = clock_ns(CLOCK_REALTIME);
    uint64_t mono1 = clock_ns(CLOCK_MONOTONIC), raw1 = clock_ns(CLOCK_MONOTONIC_RAW);
    rt_log("%s raw_before_ns=%llu monotonic_before_ns=%llu realtime_before_ns=%llu sdl_ticks_ms=%llu perf_counter=%llu perf_frequency=%llu realtime_after_ns=%llu monotonic_after_ns=%llu raw_after_ns=%llu", label,
           (unsigned long long)raw0, (unsigned long long)mono0, (unsigned long long)real0, (unsigned long long)ticks,
           (unsigned long long)counter, (unsigned long long)SDL_GetPerformanceFrequency(),
           (unsigned long long)real1, (unsigned long long)mono1, (unsigned long long)raw1);
}

int profile_trace_start(void) {
    /* Caller already created SDL video/context: do not move timer epoch earlier
     * than ordinary startup or change scripted-input schedule initialization. */
    if (!profile_stamp()) return 0;
    const char *path = getenv("SH3_PROFILE");
    char *name = malloc(strlen(path) + sizeof ".gl.csv");
    if (!name) rt_fatal("GL trace allocation failed");
    strcpy(name, path); strcat(name, ".gl.csv");
    trace_report = fopen(name, "w");
    free(name);
    if (!trace_report) rt_fatal("cannot open requested GL trace report");
    static char buffer[65536];
    setvbuf(trace_report, buffer, _IOFBF, sizeof buffer);
    fputs("lane,frame,elapsed_ms,event,api,wall_ms,cpu_ms,job,start_counter,end_counter,module,handler_offset\n", trace_report);
    for (unsigned lane = 0; lane < 2; lane++) {
        trace_lanes[lane].events = calloc(TRACE_CAPACITY, sizeof(TraceEvent));
        if (!trace_lanes[lane].events) rt_fatal("GL trace allocation failed");
    }
    /* Registered before worker cleanup so exit flush cannot race either owner. */
    atexit(trace_close);
    trace_clock("profile_clock");
    SDL_version version;
    SDL_GetVersion(&version);
    Dl_info info = {0};
    dladdr((void *)SDL_GetVersion, &info);
    rt_log("profile_gl_provider video=%s sdl=%u.%u.%u library=%s",
           SDL_GetCurrentVideoDriver(), version.major, version.minor, version.patch,
           info.dli_fname ? info.dli_fname : "unknown");
    return 1;
}

ProfileSpan profile_trace_begin(void) {
    return (ProfileSpan){SDL_GetPerformanceCounter(), profile_thread_ms()};
}

void profile_trace_end(ProfileSpan span, int worker, int frame, const char *event,
                       const char *api, uintptr_t handler, uint64_t job, int always) {
    if (!span.counter) return;
    uint64_t end = SDL_GetPerformanceCounter();
    if (!always && (end - span.counter) * counter_ms < 1.0) return;
    TraceLane *owner = &trace_lanes[worker != 0];
    if (owner->used == TRACE_CAPACITY) { owner->dropped++; return; }
    owner->events[owner->used++] = (TraceEvent){span, end, SDL_GetTicks64(), job,
        profile_thread_ms(), event, api, handler, frame};
}

double profile_thread_ms(void) {
    struct timespec t;
    clock_gettime(CLOCK_THREAD_CPUTIME_ID, &t);
    return t.tv_sec * 1000.0 + t.tv_nsec / 1000000.0;
}

uint64_t profile_stamp(void) {
    if (!checked) {
        checked = 1;
        const char *path = getenv("SH3_PROFILE");
        if (path && *path) {
            report = fopen(path, "w");
            if (!report) rt_log("profile: cannot open requested report");
            else {
                static char buffer[65536];
                setvbuf(report, buffer, _IOFBF, sizeof buffer);
                counter_ms = 1000.0 / SDL_GetPerformanceFrequency();
                fputs("frame,elapsed_ms,wall_ms,cpu_ms,draw_ms,present_ms,swap_ms,draws,buffer_bytes,room,internal_w,internal_h\n", report);
                profile_cpu_start(path);
            }
        }
    }
    return report ? SDL_GetPerformanceCounter() : 0;
}

void profile_draw_end(uint64_t start) {
    if (!start) return;
    draw_ticks += SDL_GetPerformanceCounter() - start;
    draws++;
}

void profile_buffer_upload(uint32_t bytes) {
    if (report) buffer_bytes += bytes;
}

ProfileSwap profile_swap_snapshot(void) {
    if (!report) return (ProfileSwap){0};
    return (ProfileSwap){1, rt_frame, MEM32(0x72D2C0), MEM32(0x72BFD0), MEM32(0x72BFD4)};
}

void profile_swap_end(ProfileSwap frame, uint64_t start, double cpu_start) {
    if (!start) return;
    uint64_t end = SDL_GetPerformanceCounter();
    double cpu = profile_thread_ms();
    uint64_t elapsed = SDL_GetTicks64();
    static FILE *presents;
    static int initialized;
    static uint64_t previous;
    static double milliseconds, previous_cpu;
    if (!initialized) {
        initialized = 1;
        const char *path = getenv("SH3_PROFILE");
        char *name = malloc(strlen(path) + sizeof ".presents.csv");
        if (name) {
            strcpy(name, path);
            strcat(name, ".presents.csv");
            presents = fopen(name, "w");
            free(name);
        }
        if (!presents) rt_log("profile: cannot open swap completion report");
        else {
            static char buffer[65536];
            setvbuf(presents, buffer, _IOFBF, sizeof buffer);
            milliseconds = 1000.0 / SDL_GetPerformanceFrequency();
            fputs("frame,elapsed_ms,wall_ms,swap_ms,room,internal_w,internal_h,worker_cpu_ms,swap_cpu_ms\n", presents);
        }
    }
    if (!presents) return;
    fprintf(presents, "%d,%llu,%.6f,%.6f,%u,%u,%u,%.6f,%.6f\n", frame.frame,
            (unsigned long long)elapsed, previous ? (end - previous) * milliseconds : 0,
            (end - start) * milliseconds, frame.room, frame.width, frame.height,
            previous ? cpu - previous_cpu : 0, cpu - cpu_start);
    previous = end;
    previous_cpu = cpu;
    if (frame.frame % 120 == 0) fflush(presents);
    if (ferror(presents)) {
        rt_log("profile: swap completion report write failed");
        fclose(presents);
        presents = NULL;
    }
}

void profile_present(uint64_t start, uint64_t swap_start) {
    if (!start) return;
    uint64_t end = SDL_GetPerformanceCounter();
    double cpu = profile_thread_ms();
    if (previous_frame) {
        fprintf(report, "%d,%llu,%.6f,%.6f,%.6f,%.6f,%.6f,%u,%llu,%u,%u,%u\n",
                rt_frame, (unsigned long long)SDL_GetTicks64(),
                (end - previous_frame) * counter_ms, cpu - previous_cpu, draw_ticks * counter_ms,
                (end - start) * counter_ms, (end - swap_start) * counter_ms,
                draws, (unsigned long long)buffer_bytes,
                MEM32(0x72D2C0), MEM32(0x72BFD0), MEM32(0x72BFD4));
        /* Bound evidence lost on abnormal exit without flushing every frame. */
        if (rt_frame % 120 == 0) fflush(report);
        if (ferror(report)) {
            rt_log("profile: report write failed");
            fclose(report);
            report = NULL;
        }
    }
    previous_frame = end;
    previous_cpu = cpu;
    draw_ticks = buffer_bytes = draws = 0;
    profile_cpu_frame(rt_frame + 1);
}
