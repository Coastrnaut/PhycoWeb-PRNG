"""Known result `internal-trails` of the exhaustive tables, at w = 4 (research R12; data-model section 7).

The further known result for the tool's use in the cross-checks between kinds: an exhaustive search over a box's
internal trails at w = 4, over r rounds of the box. What must match is the optimal weight at each r from 1 to
ROUNDS, differential and linear, exactly.

A box is two words of W bits, word 0 and word 1, and ROUND is its list of steps in order:

    ("rot", i, r)       word i becomes rotl(word i, r)
    ("add", i, j, r)    word i becomes word i + rotl(word j, r) mod 2^W
    ("sub", i, j, r)    word i becomes word i - rotl(word j, r) mod 2^W
    ("xor", i, j, r)    word i becomes word i xor rotl(word j, r)

The box here is the round of `box-tables-second` at w = 4, (x, y) -> (s, rotl(y, 2) xor s) with
s = rotr(x, 1) + y: word 0 is x and word 1 is y. Its one addition makes a table entry of the box one trail.

A differential trail gives the difference after each step, from a non-zero difference into the first round, and
its weight is the sum over its additions of k, the chance of each being 2^-k. A linear trail gives the mask
before each step, from a non-zero mask out of the last round, and its weight is the sum over its additions of k,
the magnitude of each correlation being 2^-k, so that the trail's correlation has magnitude 2^-weight. The formulas
for k are those of Lipmaa and Moriai, 2001, and Wallen, 2003, as `box-tables` states them.

DIFFERENTIAL and LINEAR are the optimal weights that `differential` and `linear` below enumerate over every trail,
state by state and addition by addition, on those formulas. The tool counts each addition's tables exhaustively,
so that the two agree only if each is right. In the one-addition box a table entry is one trail, so a chain of
table entries over r rounds has the weight of a trail: the floor of the cross-checks equals DIFFERENTIAL here,
and twice LINEAR, the weights of the floor being of squared correlations.
"""
from typing import Dict, Optional, Tuple

TOOL = "exhaustive tables"
KNOWN_ID = "internal-trails"
SECOND_OF = "none"
SOURCE = "self-written: a plain enumeration over the formulas, `differential` and `linear` in this file"
W = 4
MASK = (1 << W) - 1
ROUND = (("rot", 0, 3), ("add", 0, 1, 0), ("rot", 1, 2), ("xor", 1, 0, 0))
ONE_ADDITION = True
ROUNDS = 8
DIFFERENTIAL = {1: 0, 2: 1, 3: 2, 4: 4, 5: 6, 6: 6, 7: 7, 8: 8}
LINEAR = {1: 0, 2: 0, 3: 1, 4: 2, 5: 2, 6: 3, 7: 3, 8: 4}


def rotl(value: int, amount: int) -> int:
    amount %= W
    return ((value << amount) | (value >> (W - amount))) & MASK


def rotr(value: int, amount: int) -> int:
    return rotl(value, W - amount)


def weight_of_bits(value: int) -> int:
    return bin(value).count("1")


def difference_k(a: int, b: int, c: int) -> Optional[int]:
    def eq(p, q, r):
        return (~p ^ q) & (~p ^ r) & MASK

    def twice(p):
        return (p << 1) & MASK

    if eq(twice(a), twice(b), twice(c)) & (a ^ b ^ c ^ twice(b)):
        return None
    return weight_of_bits(~eq(a, b, c) & (MASK >> 1))


def correlation_k(u: int, v: int, t: int) -> Optional[int]:
    above = 0
    bit = 0
    for i in range(W - 1, 0, -1):
        bit ^= ((u ^ v ^ t) >> i) & 1
        above |= bit << (i - 1)
    if ((u ^ v) | (u ^ t)) & ~above & MASK:
        return None
    return weight_of_bits(above)


def keep(best: Dict[Tuple[int, int], int], state: Tuple[int, int], k: int) -> None:
    if k < best.get(state, 1 << 30):
        best[state] = k


def replaced(state: Tuple[int, int], word: int, value: int) -> Tuple[int, int]:
    return (value, state[1]) if word == 0 else (state[0], value)


def difference_step(best: Dict, step: Tuple) -> Dict:
    new: Dict[Tuple[int, int], int] = {}
    for state, k in best.items():
        if step[0] == "rot":
            keep(new, replaced(state, step[1], rotl(state[step[1]], step[2])), k)
        elif step[0] == "xor":
            keep(new, replaced(state, step[1], state[step[1]] ^ rotl(state[step[2]], step[3])), k)
        else:
            a, b = state[step[1]], rotl(state[step[2]], step[3])
            for c in range(MASK + 1):
                extra = difference_k(a, b, c)
                if extra is not None:
                    keep(new, replaced(state, step[1], c), k + extra)
    return new


def mask_step(best: Dict, step: Tuple) -> Dict:
    """The masks before a step, from the masks after it."""
    new: Dict[Tuple[int, int], int] = {}
    for state, k in best.items():
        if step[0] == "rot":
            keep(new, replaced(state, step[1], rotr(state[step[1]], step[2])), k)
        elif step[0] == "xor":
            keep(new, replaced(state, step[2], state[step[2]] ^ rotr(state[step[1]], step[3])), k)
        else:
            u, m = state[step[1]], state[step[2]]
            for v in range(MASK + 1):
                for t in range(MASK + 1):
                    extra = correlation_k(u, v, t)
                    if extra is not None:
                        keep(new, replaced(replaced(state, step[1], v), step[2], m ^ rotr(t, step[3])), k + extra)
    return new


def non_zero() -> Dict[Tuple[int, int], int]:
    return {(p, q): 0 for p in range(MASK + 1) for q in range(MASK + 1) if p or q}


def differential(rounds: int) -> Dict[int, int]:
    best = non_zero()
    out = {}
    for r in range(1, rounds + 1):
        for step in ROUND:
            best = difference_step(best, step)
        out[r] = min(best.values())
    return out


def linear(rounds: int) -> Dict[int, int]:
    best = non_zero()
    out = {}
    for r in range(1, rounds + 1):
        for step in reversed(ROUND):
            best = mask_step(best, step)
        out[r] = min(best.values())
    return out
