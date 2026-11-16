/* Observe presentation copies at real GL/SDL boundaries; forward every call. */
#define _GNU_SOURCE
#include <SDL2/SDL.h>
#include <SDL2/SDL_opengl.h>
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void *(*lookup)(const char *);
static PFNGLBINDFRAMEBUFFERPROC bind_framebuffer;
static PFNGLBLITFRAMEBUFFERPROC blit_framebuffer;
static void (*gen_textures)(GLsizei, GLuint *);
static void (*clear)(GLbitfield);
static void (*finish)(void);
static SDL_threadID setup_thread;
static GLuint draw_framebuffer;
static unsigned screen_blits, offscreen_blits;
static unsigned finish_calls;
static double finish_ms;

static void observe_finish(void) {
    Uint64 start = SDL_GetPerformanceCounter();
    const char *delay = getenv("SH3_TEST_FINISH_MS");
    if (delay) SDL_Delay((Uint32)strtoul(delay, NULL, 10));
    finish();
    finish_ms = 1000.0 * (SDL_GetPerformanceCounter() - start) / SDL_GetPerformanceFrequency();
    finish_calls++;
}

static void observe_gen_textures(GLsizei count, GLuint *names) {
    static int delayed;
    if (!setup_thread) setup_thread = SDL_ThreadID();
    if (!delayed && SDL_ThreadID() != setup_thread && getenv("SH3_TEST_GL_MS")) {
        delayed = 1;
        Uint64 start = SDL_GetPerformanceCounter();
        SDL_Delay((Uint32)strtoul(getenv("SH3_TEST_GL_MS"), NULL, 10));
        gen_textures(count, names);
        fprintf(stderr, "gl_block_boundary api=glGenTextures wall_ms=%.3f\n",
                1000.0 * (SDL_GetPerformanceCounter() - start) / SDL_GetPerformanceFrequency());
        return;
    }
    gen_textures(count, names);
}

static void observe_clear(GLbitfield mask) {
    static int delayed;
    const char *delay = getenv("SH3_TEST_ASYNC_GL_MS");
    if (!delayed && setup_thread && SDL_ThreadID() != setup_thread && delay) {
        delayed = 1;
        Uint64 start = SDL_GetPerformanceCounter();
        SDL_Delay((Uint32)strtoul(delay, NULL, 10));
        clear(mask);
        Uint64 end = SDL_GetPerformanceCounter();
        fprintf(stderr, "gl_block_boundary api=glClear wall_ms=%.3f start_counter=%llu end_counter=%llu\n",
                1000.0 * (end - start) / SDL_GetPerformanceFrequency(),
                (unsigned long long)start, (unsigned long long)end);
        return;
    }
    clear(mask);
}

int SDL_GL_SetSwapInterval(int interval) {
    static int (*set_interval)(int);
    if (!set_interval) set_interval = dlsym(RTLD_NEXT, "SDL_GL_SetSwapInterval");
    int result = set_interval(interval);
    fprintf(stderr, "swap_interval_boundary requested=%d result=%d effective=%d\n",
            interval, result, SDL_GL_GetSwapInterval());
    return result;
}

static void observe_bind(GLenum target, GLuint framebuffer) {
    if (target == GL_FRAMEBUFFER || target == GL_DRAW_FRAMEBUFFER)
        draw_framebuffer = framebuffer;
    bind_framebuffer(target, framebuffer);
}
static void observe_blit(GLint sx0, GLint sy0, GLint sx1, GLint sy1,
                         GLint dx0, GLint dy0, GLint dx1, GLint dy1,
                         GLbitfield mask, GLenum filter) {
    if (draw_framebuffer) offscreen_blits++; else screen_blits++;
    blit_framebuffer(sx0, sy0, sx1, sy1, dx0, dy0, dx1, dy1, mask, filter);
}
void *SDL_GL_GetProcAddress(const char *name) {
    if (!lookup) lookup = dlsym(RTLD_NEXT, "SDL_GL_GetProcAddress");
    void *function = lookup(name);
    if (!function) return NULL;
    if (!strcmp(name, "glBindFramebuffer")) {
        bind_framebuffer = function; return observe_bind;
    }
    if (!strcmp(name, "glBlitFramebuffer")) {
        blit_framebuffer = function; return observe_blit;
    }
    if (!strcmp(name, "glGenTextures")) {
        gen_textures = function; return observe_gen_textures;
    }
    if (!strcmp(name, "glClear")) {
        clear = function; return observe_clear;
    }
    if (!strcmp(name, "glFinish")) {
        finish = function; return observe_finish;
    }
    return function;
}
void SDL_GL_SwapWindow(SDL_Window *window) {
    static void (*swap)(SDL_Window *);
    if (!swap) swap = dlsym(RTLD_NEXT, "SDL_GL_SwapWindow");
    Uint64 start = SDL_GetPerformanceCounter();
    const char *delay = getenv("SH3_TEST_SWAP_MS");
    if (delay) SDL_Delay((Uint32)strtoul(delay,NULL,10));
    swap(window);
    double swap_ms = 1000.0 * (SDL_GetPerformanceCounter() - start) / SDL_GetPerformanceFrequency();
    fprintf(stderr, "presentation_boundary screen=%u offscreen=%u finish=%u finish_ms=%.3f swap_ms=%.3f\n",
            screen_blits, offscreen_blits, finish_calls, finish_ms, swap_ms);
    screen_blits = offscreen_blits = 0;
    finish_calls = 0; finish_ms = 0;
}
