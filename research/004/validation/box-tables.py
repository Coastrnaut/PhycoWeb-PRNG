"""Known result `box-tables` of the exhaustive tables, at w = 4 and 8 (research R12; data-model section 7).

The further known result that R12 gives as its example, for the tool's uses on boxes of 8 and 16 bits: the
difference and linear tables of the box (x, y) -> (x + y mod 2^w, y), whose entries the formulas of Lipmaa and
Moriai and of Wallen give exactly. What must match is every entry, 2^16 and 2^16 at w = 4, 2^32 and 2^32 at w = 8.

An input of the box is x + 2^w y, and so is an output, a difference and a mask: x holds the low w bits.

Differences. Take the input difference (a, b) and the output difference c of the addition. y does not change, so
only the output differences (c, b) occur. Lipmaa and Moriai, 2001, Algorithm 2, with all words of w bits and
eq(p, q, r) = (not p xor q) and (not p xor r): the chance that (x + y) xor ((x xor a) + (y xor b)) = c is 0 where
eq(2a, 2b, 2c) and (a xor b xor c xor 2b) is not 0, and otherwise 2^-k, with k the Hamming weight of
(not eq(a, b, c)) with its top bit cleared. So the entry at (a, b), (c, b) counts 2^(2w - k) of the 2^(2w) inputs,
or none.

Masks. The sum of signs at output mask u + 2^w m and input mask v + 2^w n is the sum over all inputs of
(-1)^(u.(x + y) xor m.y xor v.x xor n.y), so 2^(2w) times the correlation of u.(x + y) with v.x xor t.y, for
t = n xor m. Wallen, 2003, with p = u xor v and q = u xor t, and z the word whose bit i is the xor of the bits above
bit i of u xor v xor t: the correlation is 0 where p or q holds a bit outside z, and otherwise
(-1)^wt(p and q) 2^-wt(z).

Each formula was checked against a whole count of every triple at w = 3 and 4, the second at w = 2 too, signs
included, before this file was fixed.
"""
from typing import NamedTuple

import numpy as np

TOOL = "exhaustive tables"
KNOWN_ID = "box-tables"
SECOND_OF = "none"
SOURCE = "self-written: the formulas of Lipmaa and Moriai, 2001, and Wallen, 2003, as this file's docstring states them"
WIDTHS = (4, 8)


class Tables(NamedTuple):
    w: int
    counts: np.ndarray   # (a, b, c): the inputs of 2^(2w) that give output difference c
    sums: np.ndarray     # (u, v, t): the sum of signs of u.(x + y) xor v.x xor t.y


def box(w: int) -> np.ndarray:
    """The box as a lookup of 2^(2w) entries."""
    size = 1 << w
    x = np.arange(size ** 2, dtype=np.uint32) & (size - 1)
    y = np.arange(size ** 2, dtype=np.uint32) >> w
    return ((x + y) & (size - 1)) | (y << w)


def words(w: int):
    size = 1 << w
    word = np.arange(size, dtype=np.uint32)
    return word.reshape(size, 1, 1), word.reshape(1, size, 1), word.reshape(1, 1, size), size - 1


def weight(values: np.ndarray) -> np.ndarray:
    return np.bitwise_count(values).astype(np.int32)


def difference_counts(w: int) -> np.ndarray:
    a, b, c, mask = words(w)

    def eq(p, q, r):
        return (~p ^ q) & (~p ^ r) & np.uint32(mask)

    def twice(p):
        return (p << 1) & np.uint32(mask)

    possible = (eq(twice(a), twice(b), twice(c)) & (a ^ b ^ c ^ twice(b))) == 0
    k = weight(~eq(a, b, c) & np.uint32(mask >> 1))
    return np.where(possible, np.left_shift(np.int32(1), 2 * w - k), 0)


def sign_sums(w: int) -> np.ndarray:
    u, v, t, mask = words(w)
    above = (u ^ v ^ t) >> 1
    for step in (1, 2, 4):
        above = above ^ (above >> step)
    p, q = u ^ v, u ^ t
    outside = ((p | q) & ~above & np.uint32(mask)) != 0
    sign = 1 - 2 * (weight(p & q) & 1)
    return np.where(outside, 0, sign * np.left_shift(np.int32(1), 2 * w - weight(above)))


def tables(w: int) -> Tables:
    return Tables(w, difference_counts(w), sign_sums(w))


def difference_row(known: Tables, difference: int) -> np.ndarray:
    """The entries of an input difference, one per output difference."""
    size = 1 << known.w
    a, b = difference & (size - 1), difference >> known.w
    row = np.zeros(size ** 2, dtype=np.int64)
    row[b << known.w:(b + 1) << known.w] = known.counts[a, b]
    return row


def linear_row(known: Tables, mask: int) -> np.ndarray:
    """The sums of signs of an output mask, one per input mask."""
    size = 1 << known.w
    u, m = mask & (size - 1), mask >> known.w
    return known.sums[u][:, np.arange(size) ^ m].T.ravel().astype(np.int64)
