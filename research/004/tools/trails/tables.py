"""Feature 004: exhaustive difference and linear tables of a box or S-box of up to 16 bits (research R12; FR-022, FR-038).

A box is a lookup: an array of 2^b entries of b bits or fewer, for b up to 16. Its difference table has at row a and
column c the number of inputs x with box[x] xor box[x xor a] = c. Its linear table has at row b and column a the sum
over the inputs of (-1)^(b.box[x] xor a.x), so a row is an output mask and a column an input mask. At 16 bits a table
holds 2^32 entries, so each comes a row at a time and no table need be held.

Three more things come from the tables, each for the cross-checks between kinds (R12):

    chain, difference_floor and linear_floor   the best product of one-round entries over r rounds, from a non-zero
                                               row, a floor, since a table entry sums every trail through a box's
                                               additions. A weight is kept as a multiple of 2^-16, rounded down.
    differential_trails and linear_trails      the exhaustive search over a box's internal trails, on the tables of
                                               addition and subtraction at the box's word width, counted here. A box
                                               is a list of steps on two words, as research/004/validation/
                                               internal-trails.py states them.
    box_of                                     the lookup of such a list.

Run on its known results by scripts/validate_tool.py. Analysis code: the model never imports it. This tool makes no
security claim.
"""
import hashlib
import math
import sys
from functools import lru_cache
from pathlib import Path
from typing import Callable, Dict, Iterator, Optional, Sequence, Tuple

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
for place in (str(ROOT / "research/004"), str(ROOT)):
    if place not in sys.path:
        sys.path.insert(0, place)

from protocol.evidence import ToolFailure  # noqa: E402

MOST_BITS = 16
MOST_WORD = 8
UNITS = 1 << 16
FAR = 1 << 40
KIND = {"widths": [4, 8], "operations": "a lookup of up to 16 bits: a 4-bit S-box, or a box of two words of w bits, "
                                        "of addition, subtraction, xor and rotations",
        "model": "exhaustive tables, and an exhaustive search over a box's internal trails on tables of its operations",
        "uses": [{"use": "the tables of a 4-bit S-box or of a Boolean candidate's nonlinear layer at w = 4",
                  "covered_by": ["present-tables"]},
                 {"use": "the tables and the floor of a box of 8 bits at w = 4", "covered_by": ["box-tables"]},
                 {"use": "the tables and the floor of a box of 16 bits at w = 8", "covered_by": ["box-tables"]},
                 {"use": "the search over a box's internal trails at w = 4, in the cross-checks between kinds",
                  "covered_by": ["internal-trails"]}]}


# ----------------------------------------------------------------------------------------- tables

def bits_of(box: np.ndarray) -> int:
    """The input bits of a lookup; anything else is a tool defect."""
    if box.ndim != 1 or not np.issubdtype(box.dtype, np.integer):
        raise ToolFailure("a box is a one-dimensional array of integers")
    size = int(box.size)
    bits = size.bit_length() - 1
    if size < 2 or size != 1 << bits or bits > MOST_BITS:
        raise ToolFailure(f"a box has 2^b entries for b from 1 to {MOST_BITS}: not {size}")
    if int(box.min()) < 0 or int(box.max()) >= size:
        raise ToolFailure(f"a box of {bits} bits holds values below 2^{bits}")
    return bits


def difference_row(box: np.ndarray, difference: int) -> np.ndarray:
    size = box.size
    return np.bincount(box ^ box[np.arange(size) ^ difference], minlength=size)


def difference_rows(box: np.ndarray) -> Iterator[np.ndarray]:
    bits_of(box)
    for difference in range(box.size):
        yield difference_row(box, difference)


def difference_table(box: np.ndarray) -> np.ndarray:
    return np.stack(list(difference_rows(box)))


def walsh(values: np.ndarray) -> np.ndarray:
    """The sums over x of values[x] (-1)^(a.x), one per a, in place on a copy, one pass per bit."""
    out = values.astype(np.int32)
    half = 1
    while half < out.size:
        blocks = out.reshape(-1, 2, half)
        low = blocks[:, 0].copy()
        high = blocks[:, 1]
        blocks[:, 0] = low + high
        blocks[:, 1] = low - high
        half *= 2
    return out


def linear_row(box: np.ndarray, mask: int) -> np.ndarray:
    return walsh(1 - 2 * (np.bitwise_count((box & mask).astype(np.uint32)).astype(np.int32) & 1))


def linear_rows(box: np.ndarray) -> Iterator[np.ndarray]:
    bits_of(box)
    for mask in range(box.size):
        yield linear_row(box, mask)


def linear_table(box: np.ndarray) -> np.ndarray:
    return np.stack(list(linear_rows(box)))


# --------------------------------------------------------------------------------------- the floor

@lru_cache(maxsize=None)
def weight_units(count: int, bits: int, squared: bool = False) -> int:
    """-log2 of count / 2^bits, or of its square, in units of 2^-16, rounded down and never up (R12), decided exactly
    on whole numbers: the largest k with count^f * 2^(k / 2^16) <= 2^(bits f), f being 1 or 2, raised to 2^16."""
    if count <= 0:
        raise ToolFailure("an entry of 0 has no weight")
    factor = 2 if squared else 1
    if count & (count - 1) == 0:
        return (bits - (count.bit_length() - 1)) * factor * UNITS
    power = count ** (UNITS * factor)
    limit = 1 << (bits * UNITS * factor)
    k = max(int(UNITS * factor * (bits - math.log2(count))) - 2, 0)
    while (power << (k + 1)) <= limit:
        k += 1
    return k


class Weights:
    """Weights in units, by entry: a lookup of the magnitudes that have come up, each worked out once."""

    def __init__(self, bits: int, squared: bool):
        self.bits = bits
        self.squared = squared
        self.table = np.full(max((1 << bits) + 1, 2), -1, dtype=np.int64)
        self.table[0] = FAR

    def of(self, row: np.ndarray) -> np.ndarray:
        magnitudes = np.abs(row).astype(np.int64)
        if magnitudes.size and int(magnitudes.max()) >= self.table.size:
            self.table = np.concatenate((self.table, np.full(int(magnitudes.max()) + 1 - self.table.size, -1, dtype=np.int64)))
        out = self.table[magnitudes]
        if (out < 0).any():
            for count in np.unique(magnitudes[out < 0]).tolist():
                self.table[count] = weight_units(int(count), self.bits, self.squared)
            out = self.table[magnitudes]
        return out


def chain(row: Callable[[int], np.ndarray], size: int, bits: int, rounds: int, squared: bool = False) -> Dict[int, int]:
    """The least weight, in units, of a chain of r entries for each r up to `rounds`, a chain starting at any non-zero
    row and each next row being the last entry's column; the zero row is never entered."""
    weights = Weights(bits, squared)
    best = np.zeros(size, dtype=np.int64)
    best[0] = FAR
    out = {}
    for r in range(1, rounds + 1):
        new = np.full(size, FAR, dtype=np.int64)
        for start in np.flatnonzero(best < FAR).tolist():
            new = np.minimum(new, best[start] + weights.of(row(start)))
        new[0] = FAR
        new[new > FAR] = FAR
        best = new
        out[r] = int(best.min())
    return out


def difference_floor(box: np.ndarray, rounds: int) -> Dict[int, int]:
    bits = bits_of(box)
    return chain(lambda index: difference_row(box, index), box.size, bits, rounds)


def linear_floor(box: np.ndarray, rounds: int) -> Dict[int, int]:
    """The floor on the squared correlation: a chain from an output mask through input masks."""
    bits = bits_of(box)
    return chain(lambda index: linear_row(box, index), box.size, bits, rounds, squared=True)


# ------------------------------------------------------------------------------- a box's internal trails

def rotl(value, amount: int, w: int):
    mask = (1 << w) - 1
    amount %= w
    return ((value << amount) | (value >> (w - amount))) & mask if amount else value & mask


def rotr(value, amount: int, w: int):
    return rotl(value, w - amount, w)


def check_steps(steps: Sequence[Tuple], w: int) -> None:
    """A list of bijective steps on two words, as internal-trails.py states them; anything else is a tool defect."""
    if not steps:
        raise ToolFailure("a box has at least one step")
    for step in steps:
        kind = step[0]
        if kind == "rot":
            good = len(step) == 3 and step[1] in (0, 1) and 0 <= step[2] < w
        elif kind in ("add", "sub", "xor"):
            good = len(step) == 4 and step[1] in (0, 1) and step[2] in (0, 1) and step[1] != step[2] and 0 <= step[3] < w
        else:
            good = False
        if not good:
            raise ToolFailure(f"not a step of a box at w = {w}: {step}")


def box_of(steps: Sequence[Tuple], w: int) -> np.ndarray:
    """The lookup of a list of steps, an input and an output being word 0 + 2^w word 1."""
    check_steps(steps, w)
    size = 1 << w
    words = [np.arange(size ** 2, dtype=np.int64) & (size - 1), np.arange(size ** 2, dtype=np.int64) >> w]
    for step in steps:
        if step[0] == "rot":
            words[step[1]] = rotl(words[step[1]], step[2], w)
        else:
            other = rotl(words[step[2]], step[3], w)
            if step[0] == "add":
                words[step[1]] = (words[step[1]] + other) & (size - 1)
            elif step[0] == "sub":
                words[step[1]] = (words[step[1]] - other) & (size - 1)
            else:
                words[step[1]] = words[step[1]] ^ other
    return words[0] | (words[1] << w)


@lru_cache(maxsize=None)
def operation_tables(kind: str, w: int) -> Tuple[np.ndarray, np.ndarray]:
    """The tables of an addition or a subtraction of two words, by whole count over the 2^(2w) pairs: counts[a, b, c] of
    pairs that take the difference (a, b) to c, and sums[u, v, t], the sum of signs of u.out xor v.p xor t.q."""
    size = 1 << w
    p = np.arange(size ** 2, dtype=np.int64) & (size - 1)
    q = np.arange(size ** 2, dtype=np.int64) >> w
    out = (p + q if kind == "add" else p - q) & (size - 1)
    counts = np.zeros((size, size, size), dtype=np.int64)
    sums = np.zeros((size, size, size), dtype=np.int64)
    for b in range(size):
        for a in range(size):
            counts[a, b] = difference_row(out, a | (b << w))[:size]
    for u in range(size):
        sums[u] = linear_row(out, u).reshape(size, size).T
    return counts, sums


def exponents(entries: np.ndarray, bits: int) -> np.ndarray:
    """k for each entry 2^(bits - k), FAR for an entry of 0: an addition's chances and correlations are powers of two,
    and an entry that is not one is a tool defect."""
    magnitudes = np.abs(entries).astype(np.int64)
    there = magnitudes > 0
    if (magnitudes[there] & (magnitudes[there] - 1)).any():
        raise ToolFailure("an operation's entry is no power of two")
    out = np.full(magnitudes.shape, FAR, dtype=np.int64)
    out[there] = bits - np.rint(np.log2(magnitudes[there])).astype(np.int64)
    return out


def check_width(w: int) -> None:
    if not 2 <= w <= MOST_WORD:
        raise ToolFailure(f"a search over internal trails runs at word widths 2 to {MOST_WORD}: not {w}")


def seated(best: np.ndarray, word: int) -> np.ndarray:
    """The state array with `word` on its first axis."""
    return best if word == 0 else best.T


def difference_step(best: np.ndarray, step: Tuple, w: int) -> np.ndarray:
    """The least weight of each difference after a step, from each before it."""
    size = 1 << w
    words = np.arange(size)
    view = seated(best, step[1])
    new = np.full((size, size), FAR, dtype=np.int64)
    if step[0] == "rot":
        new[rotl(words, step[2], w), :] = view
    elif step[0] == "xor":
        for other in range(size):
            new[words ^ rotl(other, step[3], w), other] = view[:, other]
    else:
        table = exponents(operation_tables(step[0], w)[0], 2 * w)
        for other in range(size):
            new[:, other] = (view[:, other][:, None] + table[:, rotl(other, step[3], w), :]).min(axis=0)
    return seated(np.minimum(new, FAR), step[1])


def mask_step(best: np.ndarray, step: Tuple, w: int) -> np.ndarray:
    """The least weight of each mask before a step, from each after it."""
    size = 1 << w
    words = np.arange(size)
    view = seated(best, step[1])
    new = np.full((size, size), FAR, dtype=np.int64)
    if step[0] == "rot":
        new[rotr(words, step[2], w), :] = view
    elif step[0] == "xor":
        for mask in range(size):
            new[mask, words ^ rotr(mask, step[3], w)] = view[mask, :]
    else:
        table = exponents(operation_tables(step[0], w)[1], 2 * w)
        shifted = rotr(words, step[3], w)
        for other in range(size):
            reached = (view[:, other][:, None, None] + table).min(axis=0)
            for t in range(size):
                target = other ^ int(shifted[t])
                new[:, target] = np.minimum(new[:, target], reached[:, t])
    return seated(np.minimum(new, FAR), step[1])


def trails(steps: Sequence[Tuple], w: int, rounds: int, move: Callable, order: Sequence[Tuple]) -> Dict[int, int]:
    check_width(w)
    check_steps(steps, w)
    size = 1 << w
    best = np.zeros((size, size), dtype=np.int64)
    best[0, 0] = FAR
    out = {}
    for r in range(1, rounds + 1):
        for step in order:
            best = move(best, step, w)
        out[r] = int(best.min())
    return out


def differential_trails(steps: Sequence[Tuple], w: int, rounds: int) -> Dict[int, int]:
    """The least weight of a trail of differences over r rounds, for each r, from any non-zero difference."""
    return trails(steps, w, rounds, difference_step, tuple(steps))


def linear_trails(steps: Sequence[Tuple], w: int, rounds: int) -> Dict[int, int]:
    """The least weight of a trail of masks over r rounds, each addition's being k where its correlation has magnitude
    2^-k, for each r, from any non-zero mask out of the last round."""
    return trails(steps, w, rounds, mask_step, tuple(reversed(steps)))


# ------------------------------------------------------------------------------------- the validation

def digest_of(table: np.ndarray) -> str:
    return hashlib.sha256(table.astype("<i4").tobytes()).hexdigest()


def re_find_present(known, keep) -> Dict:
    box = np.array(known.SBOX, dtype=np.uint16)
    difference, sums = difference_table(box), linear_table(box)
    printed = np.array(known.DIFFERENCE, dtype=np.int64)
    eighths = np.array(known.EIGHTHS, dtype=np.int64)
    if printed.shape != (16, 16) or eighths.shape != (15, 15):
        raise ToolFailure(f"the printed tables have shapes {printed.shape} and {eighths.shape}")
    wrong_difference = int(np.count_nonzero(difference != printed))
    wrong_linear = int(np.count_nonzero(sums[1:, 1:] != 4 * eighths))
    found = {"difference_entries": int(printed.size), "linear_entries": int(eighths.size),
             "difference_differing": wrong_difference, "linear_differing": wrong_linear,
             "difference_sha256": digest_of(difference), "linear_sha256": digest_of(sums)}
    return {"found": found, "re_found": wrong_difference == 0 and wrong_linear == 0, "validated_kind": KIND}


def re_find_conditions(known, keep) -> Dict:
    box = np.array(known.SBOX, dtype=np.uint16)
    inverse = np.array(known.INVERSE, dtype=np.uint16)
    difference, sums = difference_table(box), linear_table(box)
    single = range(4)
    active = {(i, o) for i in single for o in single if int(sums[1 << o, 1 << i]) != 0}
    conditions = {
        "1": int(difference[1:, 1:].max()) <= known.MOST_INPUTS,
        "2": all(int(difference[1 << i, 1 << o]) == 0 for i in single for o in single),
        "3": int(np.abs(sums[1:, 1:]).max()) <= known.MOST_SUM,
        "4": active == set(known.SINGLE_BIT_PAIRS)
        and all(abs(int(sums[1 << o, 1 << i])) == known.SINGLE_BIT_SUM for i, o in active),
        "5": int(np.count_nonzero(np.abs(sums[1:, 1:]) == known.MOST_SUM)) == known.COUNT_AT_MOST_SUM,
        "the inverse is the inverse": bool((inverse[box] == np.arange(16)).all()),
        "the inverse's difference table is the transpose": bool((difference_table(inverse) == difference.T).all()),
        "the inverse's linear table is the transpose": bool((linear_table(inverse) == sums.T).all())}
    return {"found": {"conditions": conditions}, "re_found": all(conditions.values()), "validated_kind": KIND}


def compare_box(known, w: int) -> Dict:
    """Every row of the box's two tables against the file's, a row at a time."""
    box, expected = known.box(w), known.tables(w)
    bits_of(box)
    size = box.size
    wrong_difference = wrong_linear = 0
    difference_hash, linear_hash = hashlib.sha256(), hashlib.sha256()
    for index in range(size):
        row = difference_row(box, index)
        wrong_difference += int(np.count_nonzero(row != known.difference_row(expected, index)))
        difference_hash.update(row.astype("<i4").tobytes())
        row = linear_row(box, index)
        wrong_linear += int(np.count_nonzero(row != known.linear_row(expected, index)))
        linear_hash.update(row.astype("<i4").tobytes())
    return {"difference_entries": size ** 2, "linear_entries": size ** 2, "difference_differing": wrong_difference,
            "linear_differing": wrong_linear, "difference_sha256": difference_hash.hexdigest(),
            "linear_sha256": linear_hash.hexdigest()}


def re_find_boxes(known, keep) -> Dict:
    found: Dict = {}
    held = True
    for w in known.WIDTHS:
        result = compare_box(known, w)
        found[f"w{w}"] = result
        held = held and result["difference_differing"] == 0 and result["linear_differing"] == 0
    if hasattr(known, "FLOOR_WIDTH"):
        box = known.box(known.FLOOR_WIDTH)
        difference = difference_floor(box, known.FLOOR_ROUNDS)
        linear = linear_floor(box, known.FLOOR_ROUNDS)
        found["difference_floor"], found["linear_floor"] = difference, linear
        held = held and difference == {r: k * UNITS for r, k in known.FLOOR_DIFFERENTIAL.items()} \
            and linear == {r: k * UNITS for r, k in known.FLOOR_SQUARED.items()}
    return {"found": found, "re_found": bool(held), "validated_kind": KIND}


def re_find_trails(known, keep) -> Dict:
    rounds = range(1, known.ROUNDS + 1)
    differential = differential_trails(known.ROUND, known.W, known.ROUNDS)
    linear = linear_trails(known.ROUND, known.W, known.ROUNDS)
    box = box_of(known.ROUND, known.W)
    low, squared = difference_floor(box, known.ROUNDS), linear_floor(box, known.ROUNDS)
    held = differential == known.DIFFERENTIAL and linear == known.LINEAR
    if known.ONE_ADDITION:
        held = held and all(low[r] == differential[r] * UNITS and squared[r] == 2 * linear[r] * UNITS for r in rounds)
    else:
        held = held and all(low[r] <= differential[r] * UNITS and squared[r] <= 2 * linear[r] * UNITS for r in rounds)
    found = {"differential": differential, "linear": linear, "difference_floor": low, "linear_floor": squared}
    return {"found": found, "re_found": bool(held), "validated_kind": KIND}


RUNS = {"present-tables": re_find_present, "present-tables-second": re_find_conditions, "box-tables": re_find_boxes,
        "box-tables-second": re_find_boxes, "internal-trails": re_find_trails, "internal-trails-second": re_find_trails}


def validation(known_id: str, known, keep: Optional[Callable[[str, bytes], None]]) -> Dict:
    return RUNS[known_id](known, keep)
