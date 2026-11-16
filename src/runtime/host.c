/* Linux threads, guest address window, crash handlers and backtraces. */
#include "host.h"
#include "rt.h"
#include <pthread.h>

struct HostThread {
    void (*fn)(void *);
    void *arg;
    pthread_t pt;
    int wake[2];
};

static __thread HostThread *self;
HostThread *host_thread_self(void) { return self; }

#include <signal.h>
#include <unistd.h>
#include <errno.h>
#include <sys/mman.h>
#include <execinfo.h>

/* SIGUSR2 parks a thread in this handler until host_thread_resume writes a byte to its pipe. A resume
 * may land before the pause it answers: its byte is already there. */
static void on_pause(int sig) {
    (void)sig;
    char c;
    while (self && read(self->wake[0], &c, 1) < 0 && errno == EINTR) {}
}

static void alt_stack(void);
void host_use_single_core(int core) { (void)core; }

static void *thread_entry(void *p) {
    self = p;
    alt_stack();
    self->fn(self->arg);
    return NULL;
}

static HostThread *new_thread(void) {
    HostThread *t = calloc(1, sizeof *t);
    if (pipe(t->wake)) rt_fatal("pipe");
    static int installed;
    if (!installed++) {
        struct sigaction sa = {.sa_handler = on_pause, .sa_flags = SA_RESTART};
        sigaction(SIGUSR2, &sa, NULL);
    }
    return t;
}

HostThread *host_thread_start(void (*fn)(void *), void *arg, size_t stack) {
    HostThread *t = new_thread();
    t->fn = fn;
    t->arg = arg;
    pthread_attr_t a;
    pthread_attr_init(&a);
    pthread_attr_setstacksize(&a, stack);
    if (pthread_create(&t->pt, &a, thread_entry, t)) rt_fatal("pthread_create failed");
    pthread_detach(t->pt);
    return t;
}

HostThread *host_thread_adopt(void) {
    self = new_thread();
    self->pt = pthread_self();
    return self;
}

void host_thread_exit(void) { pthread_exit(NULL); }

void host_thread_pause(HostThread *t) {
    if (t == self) on_pause(SIGUSR2);
    else pthread_kill(t->pt, SIGUSR2);
}

void host_thread_resume(HostThread *t) {
    if (write(t->wake[1], "", 1) < 0) rt_log("resume: wake failed");
}

void host_thread_signal(HostThread *t, int sig) { pthread_kill(t->pt, sig); }

void *host_arena_reserve(void) {
    void *p = mmap(NULL, 1ull << 32, PROT_NONE, MAP_PRIVATE | MAP_ANONYMOUS | MAP_NORESERVE, -1, 0);
    if (p == MAP_FAILED) rt_fatal("cannot reserve the 4 GB guest arena");
    return p;
}

void host_arena_commit(uint32_t va, uint32_t len) {
    uintptr_t lo = va & ~0xFFFu, hi = ((uintptr_t)va + len + 0xFFF) & ~(uintptr_t)0xFFF;
    if (mprotect((uint8_t *)g_xbox_mem_offset + lo, hi - lo, PROT_READ | PROT_WRITE))
        rt_fatal("cannot commit guest memory %08X", va);
}

static void (*crash_cb)(uintptr_t);
static void on_signal(int sig, siginfo_t *si, void *uc) {
    (void)sig;
    (void)uc;
    crash_cb((uintptr_t)si->si_addr);
}

/* Each thread gets an alternate signal stack, so a stack overflow still reaches the handler. */
static void alt_stack(void) {
    stack_t ss = {.ss_sp = malloc(1 << 16), .ss_size = 1 << 16};
    sigaltstack(&ss, NULL);
}

void host_crash_handlers(void (*on_crash)(uintptr_t addr)) {
    crash_cb = on_crash;
    alt_stack();
    struct sigaction sa = {.sa_sigaction = on_signal, .sa_flags = SA_SIGINFO | SA_ONSTACK};
    sigaction(SIGSEGV, &sa, NULL);
    sigaction(SIGBUS, &sa, NULL);
    sigaction(SIGFPE, &sa, NULL);
    sigaction(SIGILL, &sa, NULL);
    sigaction(SIGABRT, &sa, NULL);  /* glibc's heap checks (double free...) end here */
}

void host_backtrace(int fd) {
    void *bt[48];
    backtrace_symbols_fd(bt, backtrace(bt, 48), fd);
}
