/*
 * phyco_stream: high-throughput word streams for the feature-003 batteries (FR-007, FR-008;
 * research R4; contracts/cli.md).
 *
 *   phyco_stream phyco-v2|lut-v1 S0 S1 S2 S3 [--words N] [--reverse] [--hex]
 *   phyco_stream os [--words N] [--reverse] [--hex]
 *
 * phyco-v2 mirrors phycoweb/model_v2.py (design.md 1.0) and lut-v1 mirrors phycoweb/model.py
 * (feature 001) word for word; the Python models stay the golden models (Principle II). "os"
 * is the positive control (Linux getrandom). Output: unsigned 32-bit words, little-endian.
 * Analysis tooling only; experimental generators, not suitable for generating secrets.
 */
#define _GNU_SOURCE
#include <errno.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/random.h>
#include <unistd.h>

#include "lut_table.h"

/* BEGIN phyco-v2 (test_fast_stream bans multiplication, division and modulo in this block) */
#define V2_WARMUP 256
#define V2_SIGN 0x80000000u
#define V2_THRESH 0x4D000000u
#define V2_X1 0x5A5A5A5Au
#define V2_X3 0xA5A5A5A5u

static uint32_t v2_P[4], v2_D[4];
static uint8_t v2_phase_a, v2_phase_b;

static uint32_t v2_sext16(uint16_t v) { return (v & 0x8000u) ? (0xFFFF0000u | v) : v; }

/* Step 3: arithmetic right shift by SHIFT[cls], SHIFT = (1, 2, 3, 4), literal shifts only. */
static uint32_t v2_flux(uint32_t d, uint32_t cls)
{
    int neg = (d & V2_SIGN) != 0;
    switch (cls) {
    case 0: return neg ? ((d >> 1) | 0x80000000u) : (d >> 1);
    case 1: return neg ? ((d >> 2) | 0xC0000000u) : (d >> 2);
    case 2: return neg ? ((d >> 3) | 0xE0000000u) : (d >> 3);
    default: return neg ? ((d >> 4) | 0xF0000000u) : (d >> 4);
    }
}

/* Step 5: rotate node k left by ROT[k], ROT = (5, 11, 19, 27). */
static uint32_t v2_peristalsis(int k, uint32_t t)
{
    switch (k) {
    case 0: return (t << 5) | (t >> 27);
    case 1: return (t << 11) | (t >> 21);
    case 2: return (t << 19) | (t >> 13);
    default: return (t << 27) | (t >> 5);
    }
}

static uint32_t v2_rotl8(uint32_t v) { return (v << 8) | (v >> 24); }
static uint32_t v2_rotl16(uint32_t v) { return (v << 16) | (v >> 16); }

static void v2_step(void)
{
    uint32_t p[4], Q[4], nd[4], np[4];
    int k, fire1, fire3;
    v2_phase_a = (uint8_t)(v2_phase_a + INC_A);
    v2_phase_b = (uint8_t)(v2_phase_b + INC_B);
    p[0] = v2_P[0] + v2_sext16(PERTURBATION_LUT[v2_phase_a]);
    p[1] = v2_P[1];
    p[2] = v2_P[2] + v2_sext16(PERTURBATION_LUT[(uint8_t)(v2_phase_b + COS_OFFSET)]);
    p[3] = v2_P[3];
    for (k = 0; k < 4; k++)
        Q[k] = v2_flux(p[k] - p[(k + 1) & 3], v2_D[k] >> 30);
    for (k = 0; k < 4; k++) {
        uint32_t a = (Q[k] & V2_SIGN) ? (~Q[k] + 1u) : Q[k];
        nd[k] = v2_D[k] + (a >> 2) - (v2_D[k] >> 4);
    }
    for (k = 0; k < 4; k++)
        np[k] = v2_peristalsis(k, (p[k] - Q[k] + Q[(k - 1) & 3]) ^ nd[k]);
    fire1 = v2_D[0] > V2_THRESH;
    fire3 = v2_D[2] > V2_THRESH;
    if (fire1)
        np[1] ^= V2_X1;
    if (fire3)
        np[3] ^= V2_X3;
    for (k = 0; k < 4; k++) {
        v2_P[k] = np[k];
        v2_D[k] = nd[k];
    }
}

static void v2_init(const uint32_t s[4])
{
    int i;
    v2_P[0] = (s[0] << 16) | s[1];
    v2_P[1] = (s[1] << 16) | s[2];
    v2_P[2] = (s[2] << 16) | s[3];
    v2_P[3] = (s[3] << 16) | s[0];
    v2_D[0] = 0x00010000u;
    v2_D[1] = 0x00020000u;
    v2_D[2] = 0x00040000u;
    v2_D[3] = 0x00080000u;
    v2_phase_a = 0;
    v2_phase_b = 0;
    for (i = 0; i < V2_WARMUP; i++)
        v2_step();
}

static uint32_t v2_next(void)
{
    v2_step();
    return (v2_P[0] + v2_rotl16(v2_P[2])) ^ v2_rotl8(v2_P[1] + v2_rotl16(v2_P[3]));
}
/* END phyco-v2 */

/* lut-v1 (feature 001), including its recorded flux multiplication (spec 001 Open Issue 1),
 * reproduced only for the negative control. P and D hold 16-bit values. */
static int64_t v1_P[4], v1_D[4];
static uint8_t v1_phase_a, v1_phase_b;

/* Wrap to signed 32-bit two's complement (phycoweb/model.py wrap32). */
static int64_t v1_wrap32(int64_t x)
{
    uint32_t u = (uint32_t)((uint64_t)x & 0xFFFFFFFFu);
    return (u & 0x80000000u) ? (int64_t)u - 0x100000000LL : (int64_t)u;
}

/* Floor division by 2^n, as Python's >> on negative ints. */
static int64_t v1_asr(int64_t x, int n) { return x >= 0 ? x >> n : -(((-x) + ((1LL << n) - 1)) >> n); }

static void v1_init(const uint32_t s[4])
{
    int k;
    for (k = 0; k < 4; k++) {
        v1_P[k] = s[k];
        v1_D[k] = 256;
    }
    v1_phase_a = 0;
    v1_phase_b = 0;
}

static uint32_t v1_next(void)
{
    static const int CH[4][2] = {{0, 1}, {1, 2}, {2, 3}, {3, 0}};
    int64_t Q[4];
    int k;
    v1_phase_a = (uint8_t)(v1_phase_a + INC_A);
    v1_phase_b = (uint8_t)(v1_phase_b + INC_B);
    v1_P[0] = (v1_P[0] + PERTURBATION_LUT[v1_phase_a]) & 0xFFFF;
    v1_P[2] = (v1_P[2] + PERTURBATION_LUT[(uint8_t)(v1_phase_b + COS_OFFSET)]) & 0xFFFF;
    for (k = 0; k < 4; k++)
        Q[k] = v1_asr(v1_wrap32(v1_D[k] * (v1_P[CH[k][0]] - v1_P[CH[k][1]])), 8);
    for (k = 0; k < 4; k++) {
        int64_t growth = v1_asr(v1_wrap32(Q[k] < 0 ? -Q[k] : Q[k]), 2);
        v1_D[k] = (v1_D[k] + growth - (v1_D[k] >> 4)) & 0xFFFF;
        if (v1_D[k] == 0)
            v1_D[k] = 1;
    }
    if (v1_D[0] > 4096 || v1_D[2] > 4096) {
        v1_P[1] ^= 0x5A5A;
        v1_P[3] ^= 0xA5A5;
    }
    return ((uint32_t)(v1_D[0] & 0xFF) << 24) | ((uint32_t)(v1_D[1] & 0xFF) << 16) |
           ((uint32_t)(v1_D[2] & 0xFF) << 8) | (uint32_t)(v1_D[3] & 0xFF);
}

/* Positive control: buffered Linux getrandom. */
static uint32_t os_buf[4096];
static size_t os_pos = 4096;

static uint32_t os_next(void)
{
    if (os_pos == 4096) {
        unsigned char *b = (unsigned char *)os_buf;
        size_t got = 0;
        while (got < sizeof os_buf) {
            ssize_t n = getrandom(b + got, sizeof os_buf - got, 0);
            if (n < 0) {
                if (errno == EINTR)
                    continue;
                perror("getrandom");
                exit(3);
            }
            got += (size_t)n;
        }
        os_pos = 0;
    }
    return os_buf[os_pos++];
}

static uint32_t reverse32(uint32_t v)
{
    v = ((v >> 1) & 0x55555555u) | ((v & 0x55555555u) << 1);
    v = ((v >> 2) & 0x33333333u) | ((v & 0x33333333u) << 2);
    v = ((v >> 4) & 0x0F0F0F0Fu) | ((v & 0x0F0F0F0Fu) << 4);
    v = ((v >> 8) & 0x00FF00FFu) | ((v & 0x00FF00FFu) << 8);
    return (v >> 16) | (v << 16);
}

static int write_all(const unsigned char *buf, size_t len)
{
    while (len) {
        ssize_t n = write(1, buf, len);
        if (n < 0) {
            if (errno == EINTR)
                continue;
            return errno == EPIPE ? 1 : -1;
        }
        buf += n;
        len -= (size_t)n;
    }
    return 0;
}

static int usage(void)
{
    fprintf(stderr, "usage: phyco_stream phyco-v2|lut-v1 S0 S1 S2 S3 [--words N] [--reverse] [--hex]\n"
                    "       phyco_stream os [--words N] [--reverse] [--hex]\n");
    return 2;
}

int main(int argc, char **argv)
{
    uint32_t (*next)(void);
    uint32_t seed[4];
    unsigned long long words = 0, done = 0;
    int reverse = 0, hex = 0, i, argi;
    static unsigned char out[1 << 16];
    size_t fill = 0;

    if (argc < 2)
        return usage();
    if (strcmp(argv[1], "os") == 0) {
        next = os_next;
        argi = 2;
    } else if (strcmp(argv[1], "phyco-v2") == 0 || strcmp(argv[1], "lut-v1") == 0) {
        if (argc < 6)
            return usage();
        for (i = 0; i < 4; i++) {
            char *end;
            long v;
            errno = 0;
            v = strtol(argv[2 + i], &end, 10);
            if (errno || *end || end == argv[2 + i] || v < 0 || v > 65535) {
                fprintf(stderr, "seed values must be integers in 0..65535\n");
                return 2;
            }
            seed[i] = (uint32_t)v;
        }
        if (argv[1][0] == 'p') {
            v2_init(seed);
            next = v2_next;
        } else {
            v1_init(seed);
            next = v1_next;
        }
        argi = 6;
    } else {
        return usage();
    }
    for (; argi < argc; argi++) {
        if (strcmp(argv[argi], "--reverse") == 0) {
            reverse = 1;
        } else if (strcmp(argv[argi], "--hex") == 0) {
            hex = 1;
        } else if (strcmp(argv[argi], "--words") == 0 && argi + 1 < argc) {
            char *end;
            errno = 0;
            words = strtoull(argv[++argi], &end, 10);
            if (errno || *end || words == 0)
                return usage();
        } else {
            return usage();
        }
    }
    signal(SIGPIPE, SIG_IGN);
    for (;;) {
        uint32_t w;
        if (words && done == words)
            break;
        w = next();
        if (reverse)
            w = reverse32(w);
        done++;
        if (hex) {
            if (printf("%08X\n", (unsigned)w) < 0)
                return errno == EPIPE ? 0 : 3;
            continue;
        }
        out[fill++] = (unsigned char)(w & 0xFF);
        out[fill++] = (unsigned char)((w >> 8) & 0xFF);
        out[fill++] = (unsigned char)((w >> 16) & 0xFF);
        out[fill++] = (unsigned char)(w >> 24);
        if (fill == sizeof out) {
            int r = write_all(out, fill);
            if (r)
                return r > 0 ? 0 : 3;
            fill = 0;
        }
    }
    if (hex)
        return fflush(stdout) == 0 ? 0 : (errno == EPIPE ? 0 : 3);
    if (fill) {
        int r = write_all(out, fill);
        if (r)
            return r > 0 ? 0 : 3;
    }
    return 0;
}
