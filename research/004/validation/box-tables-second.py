"""Second known result of `box-tables` (research R12; data-model section 7): another box, by another route.

The box here is a round in the manner of SPECK, at w = 4 with (ALPHA, BETA) = (1, 2) and at w = 8 with (3, 1), an
input and an output being x + 2^w y as in `box-tables`:

    (x, y) -> (s, rotl(y, BETA) xor s), where s = rotr(x, ALPHA) + y mod 2^w

Its entries do not come from the closed formulas of `box-tables`. Addition is counted through its carries, bit
by bit from the lowest, by a small automaton, and the two tables of addition then pass through the rotations.

Differences. Two additions run side by side, on (x, y) and on (x xor a, y xor b), with carries e and f. At one
bit, given a, b and c there, each of the four (x, y) either fails the output difference c or moves the pair of
carries (e, f) on. The count of (a, b, c) over w bits is the number of paths from carries (0, 0), the top carries
being free. So with s = rotr(x, ALPHA), an input difference (a, b) gives (c, rotl(b, BETA) xor c) with the count of
(rotr(a, ALPHA), b, c), and nothing else, since rotr is a bijection of x.

Masks. One addition with carry e: at one bit, given the masks u, v and t there, each of the four (x, y) adds the
sign (-1)^(u s xor v x xor t y), with s = x xor y xor e, and moves the carry on. The sum of signs over w bits is the
signed count of paths from carry 0, the top carry being free. An output mask (u, m) and an input mask (v, n) read:

    u.s xor m.(rotl(y, BETA) xor s) xor v.x xor n.y
        = (u xor m).s xor rotr(v, ALPHA).rotr(x, ALPHA) xor (n xor rotr(m, BETA)).y

since p.rotl(q, r) = rotr(p, r).q for all words. So the entry is the sum at (u xor m, rotr(v, ALPHA), n xor
rotr(m, BETA)).

The floor of the cross-checks (research R12) is the best product of one-round entries over r rounds, from a non-zero
start. This round has one addition, so each entry is one trail and its weight a whole number: 2w - log2 of the
entry for a difference, and twice that for a mask, the weight being of the squared correlation. FLOOR_DIFFERENTIAL
and FLOOR_SQUARED are what `chain_weights` below gives at w = 8, going through every row of each table once per
round, a search that shares no code with the tool's. `internal-trails` states the same at w = 4.
"""
from typing import Callable, Dict, NamedTuple

import numpy as np

TOOL = "exhaustive tables"
KNOWN_ID = "box-tables-second"
SECOND_OF = "box-tables"
SOURCE = "self-written: the carries' automaton and the rotations, as this file's docstring states them"
WIDTHS = (4, 8)
AMOUNTS = {4: (1, 2), 8: (3, 1)}
FLOOR_WIDTH = 8
FLOOR_ROUNDS = 4
FLOOR_DIFFERENTIAL = {1: 0, 2: 1, 3: 3, 4: 6}
FLOOR_SQUARED = {1: 0, 2: 0, 3: 2, 4: 6}


class Tables(NamedTuple):
    w: int
    counts: np.ndarray   # (a, b, c): the inputs of 2^(2w) that give output difference c from the addition
    sums: np.ndarray     # (u, v, t): the sum of signs of u.(x + y) xor v.x xor t.y


def rotl(value, amount, w):
    return ((value << amount) | (value >> (w - amount))) & ((1 << w) - 1)


def rotr(value, amount, w):
    return rotl(value, w - amount, w)


def box(w: int) -> np.ndarray:
    size = 1 << w
    alpha, beta = AMOUNTS[w]
    x = np.arange(size ** 2, dtype=np.uint32) & (size - 1)
    y = np.arange(size ** 2, dtype=np.uint32) >> w
    s = (rotr(x, alpha, w) + y) & (size - 1)
    return s | ((rotl(y, beta, w) ^ s) << w)


def carry(p: int, q: int, r: int) -> int:
    return (p & q) | (p & r) | (q & r)


def difference_step() -> np.ndarray:
    """One bit: (a, b, c, e, f, e', f'), how many (x, y) move the carries (e, f) to (e', f')."""
    step = np.zeros((2,) * 7, dtype=np.int64)
    for a, b, c, e, f, x, y in np.ndindex(*(2,) * 7):
        one, other = x ^ y ^ e, (x ^ a) ^ (y ^ b) ^ f
        if one ^ other == c:
            step[a, b, c, e, f, carry(x, y, e), carry(x ^ a, y ^ b, f)] += 1
    return step


def sign_step() -> np.ndarray:
    """One bit: (u, v, t, e, e'), the signed count of (x, y) that move the carry e to e'."""
    step = np.zeros((2,) * 5, dtype=np.int64)
    for u, v, t, e, x, y in np.ndindex(*(2,) * 6):
        step[u, v, t, e, carry(x, y, e)] += (-1) ** (u & (x ^ y ^ e) ^ v & x ^ t & y)
    return step


def grow(paths: np.ndarray, step: np.ndarray, words: int, states: int) -> np.ndarray:
    """Paths over i bits, indexed by the `words` words of i bits and the state, extended by one higher bit."""
    size = paths.shape[0]
    moved = np.zeros((2 * size,) * words + (states,), dtype=np.int64)
    for high in np.ndindex(*(2,) * words):
        place = tuple(slice(bit * size, (bit + 1) * size) for bit in high)
        moved[place] = paths @ step[high]
    return moved


def tables(w: int) -> Tables:
    paths = np.zeros((1, 1, 1, 4), dtype=np.int64)
    paths[0, 0, 0, 0] = 1
    step = difference_step().reshape(2, 2, 2, 4, 4)
    for _ in range(w):
        paths = grow(paths, step, 3, 4)
    counts = paths.sum(axis=-1)
    signed = np.zeros((1, 1, 1, 2), dtype=np.int64)
    signed[0, 0, 0, 0] = 1
    for _ in range(w):
        signed = grow(signed, sign_step(), 3, 2)
    return Tables(w, counts, signed.sum(axis=-1))


def difference_row(known: Tables, difference: int) -> np.ndarray:
    w = known.w
    size = 1 << w
    alpha, beta = AMOUNTS[w]
    a, b = difference & (size - 1), difference >> w
    row = np.zeros(size ** 2, dtype=np.int64)
    c = np.arange(size)
    row[c | ((rotl(b, beta, w) ^ c) << w)] = known.counts[rotr(a, alpha, w), b]
    return row


def linear_row(known: Tables, mask: int) -> np.ndarray:
    w = known.w
    size = 1 << w
    alpha, beta = AMOUNTS[w]
    u, m = mask & (size - 1), mask >> w
    word = np.arange(size)
    v = rotr(word, alpha, w)
    t = word ^ rotr(m, beta, w)
    return known.sums[u ^ m][v][:, t].T.ravel()


def chain_weights(w: int, rounds: int, row: Callable[[Tables, int], np.ndarray], factor: int) -> Dict[int, int]:
    """The least sum of factor * (2w - log2 of an entry) along a chain of `rounds` rows, each next row being a column
    of the last, from any non-zero row."""
    known = tables(w)
    size = 1 << (2 * w)
    far = 1 << 40
    best = np.zeros(size, dtype=np.int64)
    best[0] = far
    out = {}
    for r in range(1, rounds + 1):
        new = np.full(size, far, dtype=np.int64)
        for start in np.flatnonzero(best < far):
            entries = np.abs(row(known, int(start)))
            weights = np.full(size, far, dtype=np.int64)
            there = entries > 0
            weights[there] = factor * (2 * w - np.rint(np.log2(entries[there])).astype(np.int64))
            new = np.minimum(new, best[start] + weights)
        new[0] = far
        best = new
        out[r] = int(best.min())
    return out
