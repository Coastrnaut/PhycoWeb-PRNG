/*
 * seed_search: the FUT-SEC-8 demonstration tool of feature 004 (spec FR-001, FR-002; research R2;
 * contracts/cli.md). Built in WSL by fast/seed_search.mk.
 *
 *   seed_search --source-sha256
 *   seed_search --check-vectors FILE [FILE ...]
 *   seed_search --s0 S0 --s1 S1 --words W1 W2 W3 [--threads 32] [--progress SECONDS]
 *
 * It holds its own copy of phyco-v2's design-1.0 step, so that fast/phyco_stream.c, whose hash
 * feature 003's freeze records, stays unchanged; --check-vectors shows that the copy agrees with
 * the golden model. The sweep tries every (s2, s3) with the given s0 and s1, drops a candidate at
 * its first mismatching word, and prints one JSON object. Analysis tooling only; phyco-v2 is an
 * experimental generator, not suitable for generating secrets.
 */
#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <inttypes.h>
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include "lut_table.h"

#ifndef SOURCE_SHA256
#error "SOURCE_SHA256 comes from fast/seed_search.mk"
#endif

/* The first s2 values searched. A test builds a small value in a directory of its own. */
#ifndef S2_COUNT
#define S2_COUNT 65536u
#endif

#define S3_COUNT 65536u
#define WORDS_PER_FILE 10000u
#define MAX_THREADS 4096
#define MAX_MATCHES 1024
#define DEFAULT_THREADS 32
#define EXIT_MISMATCH 1
#define EXIT_REFUSED 2
#define EXIT_TOOL 3

/* BEGIN phyco-v2 */
#define WARMUP 256
#define SIGN 0x80000000u
#define THRESH 0x4D000000u
#define X1 0x5A5A5A5Au
#define X3 0xA5A5A5A5u

typedef struct {
    uint32_t P[4], D[4];
    uint8_t phase_a, phase_b;
} state_t;

static inline uint32_t sext16(uint16_t v) { return (v & 0x8000u) ? (0xFFFF0000u | v) : v; }

/* Step 3: arithmetic right shift by SHIFT[cls], SHIFT = (1, 2, 3, 4), literal shifts only. */
static inline uint32_t flux(uint32_t d, uint32_t cls)
{
    int neg = (d & SIGN) != 0;
    switch (cls) {
    case 0: return neg ? ((d >> 1) | 0x80000000u) : (d >> 1);
    case 1: return neg ? ((d >> 2) | 0xC0000000u) : (d >> 2);
    case 2: return neg ? ((d >> 3) | 0xE0000000u) : (d >> 3);
    default: return neg ? ((d >> 4) | 0xF0000000u) : (d >> 4);
    }
}

/* Step 5: rotate node k left by ROT[k], ROT = (5, 11, 19, 27). */
static inline uint32_t peristalsis(int k, uint32_t t)
{
    switch (k) {
    case 0: return (t << 5) | (t >> 27);
    case 1: return (t << 11) | (t >> 21);
    case 2: return (t << 19) | (t >> 13);
    default: return (t << 27) | (t >> 5);
    }
}

static inline uint32_t rotl8(uint32_t v) { return (v << 8) | (v >> 24); }
static inline uint32_t rotl16(uint32_t v) { return (v << 16) | (v >> 16); }

static inline void step(state_t *s)
{
    uint32_t p[4], Q[4], nd[4], np[4];
    int k, fire1, fire3;
    s->phase_a = (uint8_t)(s->phase_a + INC_A);
    s->phase_b = (uint8_t)(s->phase_b + INC_B);
    p[0] = s->P[0] + sext16(PERTURBATION_LUT[s->phase_a]);
    p[1] = s->P[1];
    p[2] = s->P[2] + sext16(PERTURBATION_LUT[(uint8_t)(s->phase_b + COS_OFFSET)]);
    p[3] = s->P[3];
    for (k = 0; k < 4; k++)
        Q[k] = flux(p[k] - p[(k + 1) & 3], s->D[k] >> 30);
    for (k = 0; k < 4; k++) {
        uint32_t a = (Q[k] & SIGN) ? (~Q[k] + 1u) : Q[k];
        nd[k] = s->D[k] + (a >> 2) - (s->D[k] >> 4);
    }
    for (k = 0; k < 4; k++)
        np[k] = peristalsis(k, (p[k] - Q[k] + Q[(k - 1) & 3]) ^ nd[k]);
    fire1 = s->D[0] > THRESH;
    fire3 = s->D[2] > THRESH;
    if (fire1)
        np[1] ^= X1;
    if (fire3)
        np[3] ^= X3;
    for (k = 0; k < 4; k++) {
        s->P[k] = np[k];
        s->D[k] = nd[k];
    }
}

static inline void init(state_t *s, uint32_t s0, uint32_t s1, uint32_t s2, uint32_t s3)
{
    int i;
    s->P[0] = (s0 << 16) | s1;
    s->P[1] = (s1 << 16) | s2;
    s->P[2] = (s2 << 16) | s3;
    s->P[3] = (s3 << 16) | s0;
    s->D[0] = 0x00010000u;
    s->D[1] = 0x00020000u;
    s->D[2] = 0x00040000u;
    s->D[3] = 0x00080000u;
    s->phase_a = 0;
    s->phase_b = 0;
    for (i = 0; i < WARMUP; i++)
        step(s);
}

static inline uint32_t next_word(state_t *s)
{
    step(s);
    return (s->P[0] + rotl16(s->P[2])) ^ rotl8(s->P[1] + rotl16(s->P[3]));
}
/* END phyco-v2 */

/* ------------------------------------------------------------------------------- vector check */

/* One golden file: the seed in its header, then every word regenerated and compared. Returns 1 if
 * all 10,000 words match; the mismatches and the words read go to the JSON line. */
static int check_file(const char *path, int first)
{
    FILE *f = fopen(path, "r");
    char line[256], model[64], format[64];
    unsigned s0, s1, s2, s3, count;
    uint32_t words = 0, mismatches = 0;
    int ok = 0;
    state_t st;

    if (f == NULL) {
        fprintf(stderr, "cannot read %s: %s\n", path, strerror(errno));
    } else if (fgets(line, sizeof line, f) == NULL
               || sscanf(line, "# model=%63s seed=%u,%u,%u,%u count=%u format=%63s", model, &s0, &s1,
                         &s2, &s3, &count, format) != 7
               || strcmp(model, "phyco-v2") != 0 || strcmp(format, "u32-hex") != 0
               || count != WORDS_PER_FILE || s0 > 65535u || s1 > 65535u || s2 > 65535u
               || s3 > 65535u) {
        fprintf(stderr, "%s: not a phyco-v2 vector file of %u words\n", path, WORDS_PER_FILE);
    } else {
        ok = 1;
        init(&st, s0, s1, s2, s3);
        while (fgets(line, sizeof line, f) != NULL) {
            char *end;
            unsigned long value = strtoul(line, &end, 16);
            if (end == line || (*end != '\n' && *end != '\r' && *end != '\0'))
                continue;
            words++;
            if (words > WORDS_PER_FILE || (uint32_t)value != next_word(&st))
                mismatches++;
        }
    }
    if (f != NULL)
        fclose(f);
    printf("%s{\"file\": \"%s\", \"words\": %" PRIu32 ", \"mismatches\": %" PRIu32 "}",
           first ? "" : ", ", path, words, mismatches);
    return ok && words == WORDS_PER_FILE && mismatches == 0;
}

static int check_vectors(int count, char **paths)
{
    int i, all = 1;
    printf("{\"files\": [");
    for (i = 0; i < count; i++)
        if (!check_file(paths[i], i == 0))
            all = 0;
    printf("]}\n");
    return all ? 0 : EXIT_MISMATCH;
}

/* ------------------------------------------------------------------------------------- sweep */

typedef struct {
    uint32_t s0, s1, words[3];
    uint64_t after_one, after_two, after_three, steps;
    uint32_t matches[MAX_MATCHES];
    uint32_t held;
    int overflow;
} job_t;

/* Read by the main thread; the workers only add to them. */
static uint32_t next_s2;
static uint32_t rows_done;

/* BEGIN worker */
static void *worker(void *arg)
{
    job_t *job = arg;
    for (;;) {
        uint32_t s2 = __atomic_fetch_add(&next_s2, 1u, __ATOMIC_RELAXED);
        uint32_t s3;
        if (s2 >= S2_COUNT)
            return NULL;
        for (s3 = 0; s3 < S3_COUNT; s3++) {
            state_t st;
            init(&st, job->s0, job->s1, s2, s3);
            job->steps += WARMUP + 1;
            if (next_word(&st) != job->words[0])
                continue;
            job->after_one++;
            job->steps++;
            if (next_word(&st) != job->words[1])
                continue;
            job->after_two++;
            job->steps++;
            if (next_word(&st) != job->words[2])
                continue;
            job->after_three++;
            if (job->held < MAX_MATCHES)
                job->matches[job->held++] = (s2 << 16) | s3;
            else
                job->overflow = 1;
        }
        __atomic_fetch_add(&rows_done, 1u, __ATOMIC_RELEASE);
    }
}
/* END worker */

static double now_seconds(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return (double)t.tv_sec + (double)t.tv_nsec / 1e9;
}

static int by_value(const void *a, const void *b)
{
    uint32_t x = *(const uint32_t *)a, y = *(const uint32_t *)b;
    return (x > y) - (x < y);
}

/* Only the main thread writes: the workers update counters that it reads (research R2). */
static void wait_with_progress(int every, double started)
{
    struct timespec nap = {0, 50000000L};
    double next = started + every;
    for (;;) {
        uint32_t done = __atomic_load_n(&rows_done, __ATOMIC_ACQUIRE);
        double t = now_seconds();
        if (done >= S2_COUNT || t >= next) {
            fprintf(stderr, "progress: %" PRIu32 " of %u s2 values in %.0f s\n", done, S2_COUNT,
                    t - started);
            fflush(stderr);
            next = t + every;
        }
        if (done >= S2_COUNT)
            return;
        nanosleep(&nap, NULL);
    }
}

static int sweep(uint32_t s0, uint32_t s1, const uint32_t words[3], int threads, int progress)
{
    pthread_t *ids = calloc((size_t)threads, sizeof *ids);
    job_t *jobs = calloc((size_t)threads, sizeof *jobs);
    static uint32_t all[MAX_MATCHES];
    uint64_t one = 0, two = 0, three = 0, steps = 0;
    uint32_t held = 0, i;
    double started, seconds;
    int t, overflow = 0;

    if (ids == NULL || jobs == NULL) {
        fprintf(stderr, "out of memory\n");
        return EXIT_TOOL;
    }
    started = now_seconds();
    for (t = 0; t < threads; t++) {
        jobs[t].s0 = s0;
        jobs[t].s1 = s1;
        memcpy(jobs[t].words, words, sizeof jobs[t].words);
        if (pthread_create(&ids[t], NULL, worker, &jobs[t]) != 0) {
            fprintf(stderr, "cannot start thread %d\n", t);
            return EXIT_TOOL;
        }
    }
    if (progress > 0)
        wait_with_progress(progress, started);
    for (t = 0; t < threads; t++)
        pthread_join(ids[t], NULL);
    seconds = now_seconds() - started;

    for (t = 0; t < threads; t++) {
        one += jobs[t].after_one;
        two += jobs[t].after_two;
        three += jobs[t].after_three;
        steps += jobs[t].steps;
        overflow |= jobs[t].overflow;
        for (i = 0; i < jobs[t].held && held < MAX_MATCHES; i++)
            all[held++] = jobs[t].matches[i];
    }
    if (overflow || held != three) {
        fprintf(stderr, "more than %d three-word matches\n", MAX_MATCHES);
        return EXIT_TOOL;
    }
    qsort(all, held, sizeof all[0], by_value);

    printf("{\"s0\": %" PRIu32 ", \"s1\": %" PRIu32 ", \"words\": [\"%08" PRIX32 "\", \"%08" PRIX32
           "\", \"%08" PRIX32 "\"], ", s0, s1, words[0], words[1], words[2]);
    printf("\"candidates\": %" PRIu64 ", \"after_one\": %" PRIu64 ", \"after_two\": %" PRIu64
           ", \"after_three\": %" PRIu64 ", \"three_word_matches\": [",
           (uint64_t)S2_COUNT << 16, one, two, three);
    for (i = 0; i < held; i++)
        printf("%s[%" PRIu32 ", %" PRIu32 "]", i ? ", " : "", all[i] >> 16, all[i] & 0xFFFFu);
    printf("], \"total_steps\": %" PRIu64 ", \"seconds\": %.6f, \"steps_per_second\": %.6f, "
           "\"threads\": %d}\n", steps, seconds, (double)steps / seconds, threads);
    free(ids);
    free(jobs);
    return 0;
}

/* ----------------------------------------------------------------------------------- arguments */

/* A decimal integer from 0 to `limit`, with nothing beside it. */
static int parse_decimal(const char *text, unsigned long limit, unsigned long *out)
{
    char *end;
    if (*text < '0' || *text > '9')
        return 0;
    errno = 0;
    *out = strtoul(text, &end, 10);
    return errno == 0 && *end == '\0' && *out <= limit;
}

/* One to eight hex digits, with nothing beside them. */
static int parse_word(const char *text, uint32_t *out)
{
    size_t n = strlen(text), i;
    if (n < 1 || n > 8)
        return 0;
    for (i = 0; i < n; i++)
        if (!((text[i] >= '0' && text[i] <= '9') || (text[i] >= 'a' && text[i] <= 'f')
              || (text[i] >= 'A' && text[i] <= 'F')))
            return 0;
    *out = (uint32_t)strtoul(text, NULL, 16);
    return 1;
}

static int usage(void)
{
    fprintf(stderr, "usage: seed_search --source-sha256\n"
                    "       seed_search --check-vectors FILE [FILE ...]\n"
                    "       seed_search --s0 S0 --s1 S1 --words W1 W2 W3 [--threads 32] "
                    "[--progress SECONDS]\n");
    return EXIT_REFUSED;
}

int main(int argc, char **argv)
{
    unsigned long s0 = 0, s1 = 0, threads = DEFAULT_THREADS, progress = 0;
    uint32_t words[3];
    int have_s0 = 0, have_s1 = 0, have_words = 0, i;

    if (argc == 2 && strcmp(argv[1], "--source-sha256") == 0) {
        puts(SOURCE_SHA256);
        return 0;
    }
    if (argc >= 3 && strcmp(argv[1], "--check-vectors") == 0)
        return check_vectors(argc - 2, argv + 2);
    for (i = 1; i < argc; i++) {
        int more = argc - i - 1;
        if (strcmp(argv[i], "--s0") == 0 && more >= 1 && parse_decimal(argv[i + 1], 65535ul, &s0)) {
            have_s0 = 1;
            i += 1;
        } else if (strcmp(argv[i], "--s1") == 0 && more >= 1
                   && parse_decimal(argv[i + 1], 65535ul, &s1)) {
            have_s1 = 1;
            i += 1;
        } else if (strcmp(argv[i], "--words") == 0 && more >= 3 && parse_word(argv[i + 1], &words[0])
                   && parse_word(argv[i + 2], &words[1]) && parse_word(argv[i + 3], &words[2])) {
            have_words = 1;
            i += 3;
        } else if (strcmp(argv[i], "--threads") == 0 && more >= 1
                   && parse_decimal(argv[i + 1], MAX_THREADS, &threads) && threads >= 1) {
            i += 1;
        } else if (strcmp(argv[i], "--progress") == 0 && more >= 1
                   && parse_decimal(argv[i + 1], 86400ul, &progress) && progress >= 1) {
            i += 1;
        } else {
            return usage();
        }
    }
    if (!have_s0 || !have_s1 || !have_words)
        return usage();
    return sweep((uint32_t)s0, (uint32_t)s1, words, (int)threads, (int)progress);
}
