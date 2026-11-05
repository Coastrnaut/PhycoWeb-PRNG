"""Second known result of `internal-trails`, at w = 4 (research R12; data-model section 7): a box of three operations with a carry.

ROUND reads as in `internal-trails`, on two words of 4 bits:

    x becomes x + rotl(y, 3);   y becomes y xor rotl(x, 2);   y becomes y - rotl(x, 1);   x becomes x xor rotl(y, 1)

Two operations of the four carry, an addition and a subtraction, so that one table entry of the box sums several
internal trails and a chain of entries may lie below the best trail: the floor of the cross-checks is at or below
DIFFERENTIAL here, and at or below twice LINEAR.

A subtraction's chances come from its addition's. For s = p - q mod 2^W, p = s + q, so the pairs (p, q) and (s, q)
are the same inputs read two ways. The inputs that take the difference (a, b) on (p, q) to c on s are the inputs
that take (c, b) on (s, q) to a on s + q, so the chance of a subtraction at (a, b, c) is the addition's at (c, b, a).
In the same way the correlation of u.(p - q) with v.p xor t.q is the correlation of v.(s + q) with u.s xor t.q, so
a subtraction at (u, v, t) is the addition at (v, u, t).

The enumeration below walks one trail at a time over the formulas of `internal-trails`, depth first from each
non-zero start, and cuts a walk that cannot beat the best found, so it shares no state table with the tool's search
or with the first file's. DIFFERENTIAL and LINEAR are what it gives.
"""
from typing import Dict, Optional, Tuple

TOOL = "exhaustive tables"
KNOWN_ID = "internal-trails-second"
SECOND_OF = "internal-trails"
SOURCE = "self-written: a walk over every trail on the formulas, `differential` and `linear` in this file"
W = 4
MASK = (1 << W) - 1
ROUND = (("add", 0, 1, 3), ("xor", 1, 0, 2), ("sub", 1, 0, 1), ("xor", 0, 1, 1))
ONE_ADDITION = False
ROUNDS = 8
DIFFERENTIAL = {1: 1, 2: 3, 3: 6, 4: 9, 5: 12, 6: 14, 7: 17, 8: 20}
LINEAR = {1: 0, 2: 1, 3: 3, 4: 3, 5: 5, 6: 6, 7: 8, 8: 9}


def rotl(value: int, amount: int) -> int:
    amount %= W
    return ((value << amount) | (value >> (W - amount))) & MASK


def rotr(value: int, amount: int) -> int:
    return rotl(value, W - amount)


def bits(value: int) -> int:
    return bin(value).count("1")


def add_difference(a: int, b: int, c: int) -> Optional[int]:
    equal = (~a ^ b) & (~a ^ c) & MASK
    doubled = (~(a << 1) ^ (b << 1)) & (~(a << 1) ^ (c << 1)) & MASK
    if doubled & (a ^ b ^ c ^ (b << 1)) & MASK:
        return None
    return bits(~equal & (MASK >> 1))


def add_correlation(u: int, v: int, t: int) -> Optional[int]:
    above = 0
    for i in range(W - 2, -1, -1):
        above |= (((above >> (i + 1)) ^ ((u ^ v ^ t) >> (i + 1))) & 1) << i
    if ((u ^ v) | (u ^ t)) & ~above & MASK:
        return None
    return bits(above)


def set_word(state: Tuple[int, int], word: int, value: int) -> Tuple[int, int]:
    return (value, state[1]) if word == 0 else (state[0], value)


def forward(state: Tuple[int, int], index: int):
    """Each (state, k) that a difference may become at one step."""
    kind, i, j, r = ROUND[index]
    if kind == "xor":
        yield set_word(state, i, state[i] ^ rotl(state[j], r)), 0
        return
    a, b = state[i], rotl(state[j], r)
    for c in range(MASK + 1):
        k = add_difference(a, b, c) if kind == "add" else add_difference(c, b, a)
        if k is not None:
            yield set_word(state, i, c), k


def backward(state: Tuple[int, int], index: int):
    """Each (state, k) that a mask may have been before one step."""
    kind, i, j, r = ROUND[index]
    if kind == "xor":
        yield set_word(state, j, state[j] ^ rotr(state[i], r)), 0
        return
    u, m = state[i], state[j]
    for v in range(MASK + 1):
        for t in range(MASK + 1):
            k = add_correlation(u, v, t) if kind == "add" else add_correlation(v, u, t)
            if k is not None:
                yield set_word(set_word(state, i, v), j, m ^ rotr(t, r)), k


def walk(moves, order, rounds: int) -> int:
    """The least weight of a trail of `rounds` rounds, from any non-zero start, by a depth-first walk."""
    best = [1 << 30]
    seen: Dict[Tuple[int, Tuple[int, int]], int] = {}
    steps = len(ROUND) * rounds

    def down(place: int, state: Tuple[int, int], k: int) -> None:
        if k >= best[0]:
            return
        if place == steps:
            best[0] = k
            return
        key = (place, state)
        if seen.get(key, 1 << 30) <= k:
            return
        seen[key] = k
        for following, extra in moves(state, order[place % len(ROUND)]):
            down(place + 1, following, k + extra)

    for p in range(MASK + 1):
        for q in range(MASK + 1):
            if p or q:
                down(0, (p, q), 0)
    return best[0]


def differential(rounds: int) -> Dict[int, int]:
    order = tuple(range(len(ROUND)))
    return {r: walk(forward, order, r) for r in range(1, rounds + 1)}


def linear(rounds: int) -> Dict[int, int]:
    order = tuple(reversed(range(len(ROUND))))
    return {r: walk(backward, order, r) for r in range(1, rounds + 1)}
