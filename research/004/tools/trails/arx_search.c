/* Feature 004: a branch-and-bound search for the optimal differential and linear trails of an ARX box (research R12; FR-038).
 *
 *     arx_search --source-sha256
 *     arx_search differential W ROUNDS STEP...       the optimal weight of 1 to ROUNDS rounds, with a trail of each
 *     arx_search linear W ROUNDS STEP...
 *     arx_search check-differential W STEP... -- X0 Y0 X1 Y1 ...    the weight of each round of a stated trail
 *     arx_search check-linear W STEP... -- X0 Y0 X1 Y1 ...
 *
 * A box is two words of W bits and a list of steps, the same steps as research/004/validation/internal-trails.py states: rot:i:r,
 * add:i:j:r, sub:i:j:r and xor:i:j:r, word i becoming word i rotated, or combined with word j rotated left by r. A round is the
 * whole list. A check takes a box of one addition in the round and hexadecimal words.
 *
 * All arithmetic is on whole numbers. A weight is exact: the models are those of Lipmaa and Moriai, 2001, for the difference of an
 * addition, and of Wallen, 2003, for its correlation, each walked bit by bit. A subtraction has the same tables of weights
 * as an addition, each model being symmetric in its three words. The search is Matsui's: for r rounds it asks whether a trail of weight
 * at most B exists, for B rising from the bound the shorter rounds give, a walk dropping out as soon as what it has spent and
 * the optimum of the rounds left exceed B. So the first B with a trail is the optimum, and the search has exhausted every lower B.
 *
 * Masks need one thing more. A search of masks walks the rounds from the last to the first, and at the first addition it meets the mask
 * of the word that the addition only reads is free and costs nothing there. Its cost falls at the next addition, whose output mask
 * it decides, so the walk takes that output mask instead, by what it costs, and solves for the free word. A box where it does not
 * decide that mask is walked over every value of the free word, at W <= 8, and is refused above that.
 *
 * Analysis code: the model never reads it. This tool makes no security claim.
 */
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifndef SOURCE_SHA256
#define SOURCE_SHA256 "unknown"
#endif

#define MOST_STEPS 64
#define MOST_ROUNDS 64

typedef enum { ROT, ADD, SUB, XOR } Kind;

typedef struct {
    Kind kind;
    int i, j, r;
} Step;

static int W;
static uint64_t MASK;
static Step steps[MOST_STEPS];
static int count, additions, first_add = -1, last_add = -1;
static int optimum[MOST_ROUNDS + 1];
static int R, limit;
static uint64_t nodes;
static uint64_t path[MOST_ROUNDS + 1][2];

static void fail(const char *text) {
    fprintf(stderr, "arx_search: %s\n", text);
    exit(3);
}

static uint64_t rotl(uint64_t x, int r) {
    return r == 0 ? x : ((x << r) | (x >> (W - r))) & MASK;
}

static uint64_t rotr(uint64_t x, int r) {
    return r == 0 ? x : ((x >> r) | (x << (W - r))) & MASK;
}

static int bit_of(uint64_t x, int i) {
    return (int)((x >> i) & 1);
}

static int carries(const Step *step) {
    return step->kind == ADD || step->kind == SUB;
}

/* ------------------------------------------------------------------------------- the closed forms, for a stated trail */

static int ones(uint64_t x) {
    int n = 0;
    while (x) {
        x &= x - 1;
        n++;
    }
    return n;
}

static int difference_k(uint64_t a, uint64_t b, uint64_t c) {
    uint64_t twice_a = (a << 1) & MASK, twice_b = (b << 1) & MASK, twice_c = (c << 1) & MASK;
    uint64_t shifted = (~twice_a ^ twice_b) & (~twice_a ^ twice_c) & MASK;
    if (shifted & (a ^ b ^ c ^ twice_b)) {
        return -1;
    }
    return ones(~((~a ^ b) & (~a ^ c)) & (MASK >> 1));
}

static int correlation_k(uint64_t u, uint64_t v, uint64_t t) {
    uint64_t z = 0;
    int bit = 0;
    for (int i = W - 1; i > 0; i--) {
        bit ^= bit_of(u ^ v ^ t, i);
        z |= (uint64_t)bit << (i - 1);
    }
    if (((u ^ v) | (u ^ t)) & ~z & MASK) {
        return -1;
    }
    return ones(z);
}

/* ------------------------------------------------------------------------------------------------- differences */

static int forward(int round, int step, uint64_t x0, uint64_t x1, int weight);

typedef struct {
    int round, step, weight, room;
    uint64_t a, b, other;
} Outputs;

/* The output differences of an addition, bit by bit from the lowest. Where a, b and c agreed at the bit below, c is forced here;
 * elsewhere it is free. A bit below the top where they do not all agree costs 1. */
static int walk_outputs(const Outputs *w, int bit, uint64_t c, int spent, int equal, int below) {
    if (bit == W) {
        const Step *t = &steps[w->step];
        uint64_t x[2];
        x[t->i] = c;
        x[t->j] = w->other;
        return forward(w->round, w->step + 1, x[0], x[1], w->weight + spent);
    }
    int p = bit_of(w->a, bit), q = bit_of(w->b, bit);
    for (int pass = 0; pass < 2; pass++) {
        int r = pass == 0 ? p : !p;
        if (equal && r != (p ^ q ^ below)) {
            continue;
        }
        int same = p == q && q == r;
        int cost = !same && bit < W - 1;
        if (spent + cost <= w->room && walk_outputs(w, bit + 1, c | ((uint64_t)r << bit), spent + cost, same, q)) {
            return 1;
        }
    }
    return 0;
}

/* The least weight of any output difference of (a, b). */
static int least_output(uint64_t a, uint64_t b) {
    int equal = 1, below = 0, cost = 0;
    for (int bit = 0; bit < W; bit++) {
        int p = bit_of(a, bit), q = bit_of(b, bit);
        int same = equal ? (p == q && q == (p ^ q ^ below)) : p == q;
        if (!same && bit < W - 1) {
            cost++;
        }
        equal = same;
        below = q;
    }
    return cost;
}

static int forward(int round, int step, uint64_t x0, uint64_t x1, int weight) {
    uint64_t x[2] = {x0, x1};
    nodes++;
    for (;;) {
        for (; step < count; step++) {
            const Step *t = &steps[step];
            if (t->kind == ROT) {
                x[t->i] = rotl(x[t->i], t->r);
            } else if (t->kind == XOR) {
                x[t->i] ^= rotl(x[t->j], t->r);
            } else {
                Outputs walk = {round, step, weight, limit - weight - optimum[R - round - 1], x[t->i], rotl(x[t->j], t->r), x[t->j]};
                if (walk.room < 0 || least_output(walk.a, walk.b) > walk.room) {
                    return 0;
                }
                return walk_outputs(&walk, 0, 0, 0, 1, 0);
            }
        }
        path[round + 1][0] = x[0];
        path[round + 1][1] = x[1];
        if (++round == R) {
            return 1;
        }
        step = 0;
    }
}

/* The first addition's (a, b, c) of the first round, every triple that the room allows; its two words are the whole state. */
static int walk_start(int bit, uint64_t a, uint64_t b, uint64_t c, int spent, int equal, int below, int room) {
    if (bit == W) {
        if ((a | b) == 0) {
            return 0;
        }
        const Step *t = &steps[first_add];
        uint64_t x[2], y[2];
        x[t->i] = c;
        x[t->j] = rotr(b, t->r);
        y[t->i] = a;
        y[t->j] = x[t->j];
        for (int s = first_add - 1; s >= 0; s--) {
            if (steps[s].kind == ROT) {
                y[steps[s].i] = rotr(y[steps[s].i], steps[s].r);
            } else {
                y[steps[s].i] ^= rotl(y[steps[s].j], steps[s].r);
            }
        }
        path[0][0] = y[0];
        path[0][1] = y[1];
        return forward(0, first_add + 1, x[0], x[1], spent);
    }
    for (int choice = 0; choice < 4; choice++) {
        int p = choice & 1, q = (choice >> 1) & 1;
        for (int pass = 0; pass < 2; pass++) {
            int r = pass == 0 ? p : !p;
            if (equal && r != (p ^ q ^ below)) {
                continue;
            }
            int same = p == q && q == r;
            int cost = !same && bit < W - 1;
            if (spent + cost <= room &&
                walk_start(bit + 1, a | ((uint64_t)p << bit), b | ((uint64_t)q << bit), c | ((uint64_t)r << bit), spent + cost, same, q, room)) {
                return 1;
            }
        }
    }
    return 0;
}

static int search_differences(void) {
    int room = limit - optimum[R - 1];
    return room >= 0 && walk_start(0, 0, 0, 0, 0, 1, 0, room);
}

/* ------------------------------------------------------------------------------------------------------- masks */

static int backward(int depth, int step, uint64_t x0, uint64_t x1, int weight);

typedef struct {
    int depth, step, weight, room;
    uint64_t u, m;
} Inputs;

/* The input masks of an addition from its output mask u, bit by bit from the top. z starts at 0; where it is 0 both input masks equal u
 * and z takes u's bit; where it is 1 the bit costs 1, the input masks are free, and z becomes 1 xor u xor v xor t there. */
static int walk_inputs(const Inputs *w, int bit, uint64_t v, uint64_t t, int spent, int z) {
    if (bit < 0) {
        const Step *s = &steps[w->step];
        uint64_t x[2];
        x[s->i] = v;
        x[s->j] = w->m ^ rotr(t, s->r);
        return backward(w->depth, w->step - 1, x[0], x[1], w->weight + spent);
    }
    int p = bit_of(w->u, bit);
    if (!z) {
        return walk_inputs(w, bit - 1, v | ((uint64_t)p << bit), t | ((uint64_t)p << bit), spent, p);
    }
    if (spent + 1 > w->room) {
        return 0;
    }
    for (int choice = 0; choice < 4; choice++) {
        int a = (choice ^ p ^ 1) & 1, b = (choice >> 1) & 1;
        if (walk_inputs(w, bit - 1, v | ((uint64_t)a << bit), t | ((uint64_t)b << bit), spent + 1, 1 ^ p ^ a ^ b)) {
            return 1;
        }
    }
    return 0;
}

/* The least exponent of any input masks of u. */
static int least_input(uint64_t u) {
    int z = 0, cost = 0;
    for (int bit = W - 1; bit >= 0; bit--) {
        if (z) {
            cost++;
            z = 0;
        } else {
            z = bit_of(u, bit);
        }
    }
    return cost;
}

static int backward(int depth, int step, uint64_t x0, uint64_t x1, int weight) {
    uint64_t x[2] = {x0, x1};
    nodes++;
    for (;;) {
        for (; step >= 0; step--) {
            const Step *t = &steps[step];
            if (t->kind == ROT) {
                x[t->i] = rotr(x[t->i], t->r);
            } else if (t->kind == XOR) {
                x[t->j] ^= rotr(x[t->i], t->r);
            } else {
                Inputs walk = {depth, step, weight, limit - weight - optimum[R - depth - 1], x[t->i], x[t->j]};
                if (walk.room < 0 || least_input(walk.u) > walk.room) {
                    return 0;
                }
                return walk_inputs(&walk, W - 1, 0, 0, 0, 0);
            }
        }
        path[R - depth - 1][0] = x[0];
        path[R - depth - 1][1] = x[1];
        if (++depth == R) {
            return 1;
        }
        step = count - 1;
    }
}

/* What decides the free word: the steps from the last addition back to the addition before it, in this round or, with one addition in a
 * round, in the round before. */
static int next_add, next_wraps, solvable;
static uint64_t inverse[64];
static uint64_t end_u, end_m;

static void walk_masks_back(uint64_t x[2], int from, int to) {
    for (int s = from; s > to; s--) {
        if (steps[s].kind == ROT) {
            x[steps[s].i] = rotr(x[steps[s].i], steps[s].r);
        } else {
            x[steps[s].j] ^= rotr(x[steps[s].i], steps[s].r);
        }
    }
}

static void to_next_add(uint64_t x[2]) {
    if (next_wraps) {
        walk_masks_back(x, last_add - 1, -1);
        walk_masks_back(x, count - 1, next_add);
    } else {
        walk_masks_back(x, last_add - 1, next_add);
    }
}

static void prepare_masks(void) {
    next_wraps = additions == 1;
    next_add = last_add;
    if (!next_wraps) {
        for (int s = last_add - 1; s >= 0; s--) {
            if (carries(&steps[s])) {
                next_add = s;
                break;
            }
        }
    }
    const Step *t = &steps[last_add];
    uint64_t rows[64], units[64];
    for (int k = 0; k < W; k++) {
        rows[k] = 0;
        units[k] = (uint64_t)1 << k;
    }
    for (int k = 0; k < W; k++) {
        uint64_t x[2] = {0, 0};
        x[t->j] = (uint64_t)1 << k;
        to_next_add(x);
        uint64_t image = x[steps[next_add].i];
        for (int row = 0; row < W; row++) {
            rows[row] |= (uint64_t)bit_of(image, row) << k;
        }
    }
    solvable = 1;
    for (int k = 0; k < W; k++) {
        int pivot = -1;
        for (int row = k; row < W; row++) {
            if (bit_of(rows[row], k)) {
                pivot = row;
                break;
            }
        }
        if (pivot < 0) {
            solvable = 0;
            return;
        }
        uint64_t swap = rows[k];
        rows[k] = rows[pivot];
        rows[pivot] = swap;
        swap = units[k];
        units[k] = units[pivot];
        units[pivot] = swap;
        for (int row = 0; row < W; row++) {
            if (row != k && bit_of(rows[row], k)) {
                rows[row] ^= rows[k];
                units[row] ^= units[k];
            }
        }
    }
    for (int k = 0; k < W; k++) {
        inverse[k] = units[k];
    }
}

static uint64_t solve(uint64_t target) {
    uint64_t out = 0;
    for (int k = 0; k < W; k++) {
        if (ones(inverse[k] & target) & 1) {
            out |= (uint64_t)1 << k;
        }
    }
    return out;
}

static int from_start(uint64_t u, uint64_t v, uint64_t t, uint64_t n, int spent) {
    if ((v | n) == 0) {
        return 0;
    }
    const Step *s = &steps[last_add];
    end_u = u;
    end_m = n ^ rotr(t, s->r);
    uint64_t x[2];
    x[s->i] = v;
    x[s->j] = n;
    return backward(0, last_add - 1, x[0], x[1], spent);
}

typedef struct {
    uint64_t u, v, t, known;
    int spent, room;
} Targets;

/* Each output mask of the next addition with its least exponent within the room, bit by bit from the top. */
static int walk_targets(const Targets *w, int bit, uint64_t target, int cost, int z) {
    if (bit < 0) {
        return from_start(w->u, w->v, w->t, solve(target ^ w->known), w->spent);
    }
    if (z) {
        if (cost + 1 > w->room) {
            return 0;
        }
        return walk_targets(w, bit - 1, target, cost + 1, 0) ||
               walk_targets(w, bit - 1, target | ((uint64_t)1 << bit), cost + 1, 0);
    }
    return walk_targets(w, bit - 1, target, cost, 0) || walk_targets(w, bit - 1, target | ((uint64_t)1 << bit), cost, 1);
}

static int after_first(uint64_t u, uint64_t v, uint64_t t, int spent) {
    const Step *s = &steps[last_add];
    if (R == 1 && additions == 1) {
        return from_start(u, v, t, v == 0 ? 1 : 0, spent);
    }
    int room = limit - spent - optimum[next_wraps ? R - 2 : R - 1];
    if (room < 0) {
        return 0;
    }
    if (solvable) {
        uint64_t x[2] = {0, 0};
        x[s->i] = v;
        to_next_add(x);
        Targets walk = {u, v, t, x[steps[next_add].i], spent, room};
        return walk_targets(&walk, W - 1, 0, 0, 0);
    }
    if (W > 8) {
        fail("a free word that the next addition does not decide, above w = 8");
    }
    for (uint64_t n = 0; n <= MASK; n++) {
        if (from_start(u, v, t, n, spent)) {
            return 1;
        }
    }
    return 0;
}

/* The last addition's (u, v, t), every triple that the room allows. */
static int walk_triples(int bit, uint64_t u, uint64_t v, uint64_t t, int spent, int z, int room) {
    if (bit < 0) {
        return after_first(u, v, t, spent);
    }
    if (!z) {
        for (int p = 0; p < 2; p++) {
            uint64_t one = (uint64_t)p << bit;
            if (walk_triples(bit - 1, u | one, v | one, t | one, spent, p, room)) {
                return 1;
            }
        }
        return 0;
    }
    if (spent + 1 > room) {
        return 0;
    }
    for (int choice = 0; choice < 8; choice++) {
        int p = choice & 1, a = (choice >> 1) & 1, b = (choice >> 2) & 1;
        if (walk_triples(bit - 1, u | ((uint64_t)p << bit), v | ((uint64_t)a << bit), t | ((uint64_t)b << bit), spent + 1,
                         1 ^ p ^ a ^ b, room)) {
            return 1;
        }
    }
    return 0;
}

static int search_masks(void) {
    int room = limit - optimum[R - 1];
    if (room < 0 || !walk_triples(W - 1, 0, 0, 0, 0, 0, room)) {
        return 0;
    }
    uint64_t x[2];
    const Step *s = &steps[last_add];
    x[s->i] = end_u;
    x[s->j] = end_m;
    for (int k = last_add + 1; k < count; k++) {
        if (steps[k].kind == ROT) {
            x[steps[k].i] = rotl(x[steps[k].i], steps[k].r);
        } else {
            x[steps[k].j] ^= rotr(x[steps[k].i], steps[k].r);
        }
    }
    path[R][0] = x[0];
    path[R][1] = x[1];
    return 1;
}

/* ------------------------------------------------------------------------------------------------- the two modes */

static void search(int (*round_search)(void), int rounds) {
    optimum[0] = 0;
    for (int r = 1; r <= rounds; r++) {
        int low = optimum[r - 1];
        for (int s = 1; s < r; s++) {
            if (optimum[s] + optimum[r - s] > low) {
                low = optimum[s] + optimum[r - s];
            }
        }
        R = r;
        nodes = 0;
        for (limit = low;; limit++) {
            if (round_search()) {
                break;
            }
            if (limit > (W + 1) * additions * r) {
                fail("no trail at any weight");
            }
        }
        optimum[r] = limit;
        printf("optimal %d %d %" PRIu64 "\ntrail %d", r, limit, nodes, r);
        for (int k = 0; k <= r; k++) {
            printf(" %" PRIx64 " %" PRIx64, path[k][0], path[k][1]);
        }
        printf("\n");
        fflush(stdout);
    }
}

/* The states at the addition of a round of one addition: from the state before it through the steps ahead of it, and from the state after
 * it back through the steps behind it. */
static void check_differences(const uint64_t *trail, int states) {
    const Step *t = &steps[first_add];
    for (int r = 0; r + 1 < states; r++) {
        uint64_t x[2] = {trail[2 * r], trail[2 * r + 1]}, y[2] = {trail[2 * r + 2], trail[2 * r + 3]};
        for (int s = 0; s < first_add; s++) {
            if (steps[s].kind == ROT) {
                x[steps[s].i] = rotl(x[steps[s].i], steps[s].r);
            } else {
                x[steps[s].i] ^= rotl(x[steps[s].j], steps[s].r);
            }
        }
        for (int s = count - 1; s > first_add; s--) {
            if (steps[s].kind == ROT) {
                y[steps[s].i] = rotr(y[steps[s].i], steps[s].r);
            } else {
                y[steps[s].i] ^= rotl(y[steps[s].j], steps[s].r);
            }
        }
        int k = x[t->j] == y[t->j] ? difference_k(x[t->i], rotl(x[t->j], t->r), y[t->i]) : -1;
        printf("round %d %d\n", r + 1, k);
    }
}

static void check_masks(const uint64_t *trail, int states) {
    const Step *t = &steps[first_add];
    for (int r = 0; r + 1 < states; r++) {
        uint64_t x[2] = {trail[2 * r], trail[2 * r + 1]}, y[2] = {trail[2 * r + 2], trail[2 * r + 3]};
        for (int s = 0; s < first_add; s++) {
            if (steps[s].kind == ROT) {
                x[steps[s].i] = rotl(x[steps[s].i], steps[s].r);
            } else {
                x[steps[s].j] ^= rotr(x[steps[s].i], steps[s].r);
            }
        }
        walk_masks_back(y, count - 1, first_add);
        printf("round %d %d\n", r + 1, correlation_k(y[t->i], x[t->i], rotl(x[t->j] ^ y[t->j], t->r)));
    }
}

static void read_step(const char *text) {
    char name[8];
    int a = 0, b = 0, c = 0;
    if (count == MOST_STEPS) {
        fail("too many steps");
    }
    Step *s = &steps[count];
    if (sscanf(text, "%7[a-z]:%d:%d:%d", name, &a, &b, &c) == 4) {
        s->kind = strcmp(name, "add") == 0 ? ADD : strcmp(name, "sub") == 0 ? SUB : strcmp(name, "xor") == 0 ? XOR : ROT;
        if (s->kind == ROT && strcmp(name, "rot") == 0) {
            fail("a rotation has a word and an amount");
        }
        if (strcmp(name, "add") != 0 && strcmp(name, "sub") != 0 && strcmp(name, "xor") != 0) {
            fail("no such step");
        }
        s->i = a;
        s->j = b;
        s->r = c;
        if ((a != 0 && a != 1) || (b != 0 && b != 1) || a == b || c < 0 || c >= W) {
            fail("a step on two words of the box, with an amount below W");
        }
    } else if (sscanf(text, "rot:%d:%d", &a, &b) == 2) {
        s->kind = ROT;
        s->i = a;
        s->j = 1 - a;
        s->r = b;
        if ((a != 0 && a != 1) || b < 0 || b >= W) {
            fail("a rotation of a word of the box, by an amount below W");
        }
    } else {
        fail("no such step");
    }
    if (carries(s)) {
        if (first_add < 0) {
            first_add = count;
        }
        last_add = count;
        additions++;
    }
    count++;
}

static void read_width(const char *text) {
    W = atoi(text);
    if (W < 2 || W > 63) {
        fail("a word of 2 to 63 bits");
    }
    MASK = ((uint64_t)1 << W) - 1;
}

int main(int argc, char **argv) {
    if (argc == 2 && strcmp(argv[1], "--source-sha256") == 0) {
        printf("%s\n", SOURCE_SHA256);
        return 0;
    }
    if (argc < 5) {
        fprintf(stderr, "usage: arx_search --source-sha256 | differential|linear W ROUNDS STEP... | check-differential|check-linear W STEP... -- WORDS\n");
        return 2;
    }
    int checks = strncmp(argv[1], "check-", 6) == 0;
    const char *kind = checks ? argv[1] + 6 : argv[1];
    if (strcmp(kind, "differential") != 0 && strcmp(kind, "linear") != 0) {
        fail("no such mode");
    }
    read_width(argv[2]);
    int place = checks ? 3 : 4;
    for (; place < argc && strcmp(argv[place], "--") != 0; place++) {
        read_step(argv[place]);
    }
    if (additions == 0) {
        fail("a box with no addition has no weight");
    }
    if (checks) {
        static uint64_t trail[2 * (MOST_ROUNDS + 1)];
        int words = 0;
        if (additions != 1) {
            fail("a check takes a box of one addition in the round");
        }
        for (place++; place < argc; place++) {
            if (words == 2 * (MOST_ROUNDS + 1)) {
                fail("too long a trail");
            }
            trail[words++] = strtoull(argv[place], NULL, 16);
        }
        if (words < 4 || words % 2) {
            fail("a trail is pairs of words, at least two");
        }
        if (strcmp(kind, "differential") == 0) {
            check_differences(trail, words / 2);
        } else {
            check_masks(trail, words / 2);
        }
        return 0;
    }
    int rounds = atoi(argv[3]);
    if (rounds < 1 || rounds > MOST_ROUNDS) {
        fail("rounds from 1 to 64");
    }
    if (strcmp(kind, "differential") == 0) {
        search(search_differences, rounds);
    } else {
        prepare_masks();
        search(search_masks, rounds);
    }
    return 0;
}
