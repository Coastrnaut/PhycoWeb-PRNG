/*
 * testu01_driver: run a TestU01 battery on 32-bit words read from stdin (feature 003 T020;
 * research R7; contracts/cli.md).
 *
 *   testu01_driver smallcrush|crush|bigcrush --name NAME --pvalues OUT.jsonl < words
 *
 * Words are little-endian u32, as written by phyco_stream. The full TestU01 text report goes to
 * stdout (swrite_Basic = TRUE). After the battery, one JSON line with every statistic the
 * battery computed (bbattery_NTests, bbattery_TestNames, bbattery_pVal; entries with
 * pVal < 0 were not run and are left out) is written to OUT.jsonl. Exit 0 on completion, 2 on
 * bad usage, 3 if stdin ends before the battery finishes or on I/O error.
 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "TestU01.h"

static unsigned char in_buf[1 << 16];
static size_t in_len = 0, in_pos = 0;
static unsigned long long words_read = 0;

static unsigned int next_word(void)
{
    unsigned int w;
    if (in_pos + 4 > in_len) {
        size_t rest = in_len - in_pos;
        memmove(in_buf, in_buf + in_pos, rest);
        in_len = rest + fread(in_buf + rest, 1, sizeof in_buf - rest, stdin);
        in_pos = 0;
        if (in_len < 4) {
            fprintf(stderr, "testu01_driver: input ended after %llu words\n", words_read);
            exit(3);
        }
    }
    w = (unsigned int)in_buf[in_pos] | ((unsigned int)in_buf[in_pos + 1] << 8) |
        ((unsigned int)in_buf[in_pos + 2] << 16) | ((unsigned int)in_buf[in_pos + 3] << 24);
    in_pos += 4;
    words_read++;
    return w;
}

static void json_string(FILE *f, const char *s)
{
    fputc('"', f);
    for (; *s; s++) {
        if (*s == '"' || *s == '\\')
            fprintf(f, "\\%c", *s);
        else if ((unsigned char)*s < 0x20)
            fprintf(f, "\\u%04x", (unsigned char)*s);
        else
            fputc(*s, f);
    }
    fputc('"', f);
}

static int usage(void)
{
    fprintf(stderr, "usage: testu01_driver smallcrush|crush|bigcrush --name NAME --pvalues OUT.jsonl\n");
    return 2;
}

int main(int argc, char **argv)
{
    const char *battery, *name = NULL, *out_path = NULL;
    unif01_Gen *gen;
    FILE *out;
    int i, first = 1;

    if (argc != 6)
        return usage();
    battery = argv[1];
    for (i = 2; i + 1 < argc; i += 2) {
        if (strcmp(argv[i], "--name") == 0)
            name = argv[i + 1];
        else if (strcmp(argv[i], "--pvalues") == 0)
            out_path = argv[i + 1];
        else
            return usage();
    }
    if (!name || !out_path)
        return usage();
    if (strcmp(battery, "smallcrush") && strcmp(battery, "crush") && strcmp(battery, "bigcrush"))
        return usage();
    out = fopen(out_path, "w");
    if (!out) {
        perror(out_path);
        return 3;
    }

    swrite_Basic = TRUE;
    gen = unif01_CreateExternGenBits((char *)name, next_word);
    if (strcmp(battery, "smallcrush") == 0)
        bbattery_SmallCrush(gen);
    else if (strcmp(battery, "crush") == 0)
        bbattery_Crush(gen);
    else
        bbattery_BigCrush(gen);
    unif01_DeleteExternGenBits(gen);

    fprintf(out, "{\"battery\": ");
    json_string(out, battery);
    fprintf(out, ", \"n_tests\": %d, \"words_read\": %llu, \"tests\": [", bbattery_NTests,
            words_read);
    for (i = 0; i < bbattery_NTests; i++) {
        if (bbattery_pVal[i] < 0.0)
            continue;
        fprintf(out, "%s{\"index\": %d, \"name\": ", first ? "" : ", ", i);
        json_string(out, bbattery_TestNames[i] ? bbattery_TestNames[i] : "");
        fprintf(out, ", \"p\": %.17g}", bbattery_pVal[i]);
        first = 0;
    }
    fprintf(out, "]}\n");
    if (fclose(out) != 0) {
        perror(out_path);
        return 3;
    }
    return 0;
}
