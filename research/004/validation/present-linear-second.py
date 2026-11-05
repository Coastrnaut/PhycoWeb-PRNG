"""Second known result of `present-linear` (research R12; data-model section 7): a smaller SPN, its minima by exhaustion.

Four PRESENT S-boxes on 16 bits, with PRESENT's bit permutation at this size: bit i moves to 4i mod 15, bit 15 staying, so that
each S-box's four outputs go to four S-boxes. DIFFERENTIAL and LINEAR are the minima of active S-boxes over r rounds, from any
non-zero start, that `minima` below finds: the shortest path over all 2^16 states, round by round and S-box by S-box, on the
S-box's two tables, with no solver. So the counter's model must agree, at each r, with a whole search of the state.
"""
from typing import Dict

import numpy as np

TOOL = "active-S-box counting"
KNOWN_ID = "present-linear-second"
SECOND_OF = "present-linear"
SOURCE = "self-written: a shortest path over all 2^16 states, `minima` in this file"
SBOX = (0xC, 0x5, 0x6, 0xB, 0x9, 0x0, 0xA, 0xD, 0x3, 0xE, 0xF, 0x8, 0x4, 0x7, 0x1, 0x2)
BITS = 16
BOXES = tuple(tuple(4 * s + i for i in range(4)) for s in range(4))
PERMUTATION = tuple((4 * i) % 15 for i in range(15)) + (15,)
ROUNDS = 8
DIFFERENTIAL = {1: 1, 2: 2, 3: 4, 4: 6, 5: 7, 6: 8, 7: 10, 8: 12}
LINEAR = {r: r for r in range(1, ROUNDS + 1)}
FAR = 10 ** 6


def allowed(kind: str) -> np.ndarray:
    table = np.zeros((16, 16), dtype=bool)
    for a in range(16):
        for b in range(16):
            if kind == "differential":
                table[a, b] = any(SBOX[x] ^ SBOX[x ^ a] == b for x in range(16))
            else:
                table[a, b] = sum((-1) ** (bin(a & x).count("1") + bin(b & SBOX[x]).count("1")) for x in range(16)) != 0
    return table


def through_boxes(best: np.ndarray, table: np.ndarray) -> np.ndarray:
    index = np.arange(best.size)
    for bits in BOXES:
        low = bits[0]
        kept = index & ~(15 << low)
        nibble = (index >> low) & 15
        new = np.full(best.size, FAR, dtype=np.int64)
        for a in range(16):
            sources = np.flatnonzero(nibble == a)
            cost = best[sources] + (1 if a else 0)
            for b in np.flatnonzero(table[a]):
                np.minimum.at(new, kept[sources] | (int(b) << low), cost)
        best = new
    return best


def minima(kind: str, rounds: int = ROUNDS) -> Dict[int, int]:
    table = allowed(kind)
    index = np.arange(1 << BITS)
    moved = np.zeros(1 << BITS, dtype=np.int64)
    for i in range(BITS):
        moved |= ((index >> i) & 1) << PERMUTATION[i]
    best = np.zeros(1 << BITS, dtype=np.int64)
    best[0] = FAR
    out = {}
    for r in range(1, rounds + 1):
        best = through_boxes(best, table)
        new = np.full(1 << BITS, FAR, dtype=np.int64)
        new[moved] = best
        new[0] = FAR
        best = new
        out[r] = int(best.min())
    return out
