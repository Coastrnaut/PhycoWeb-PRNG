"""Feature 004: exact structural dependency through an operation list (research R13; data-model section 5).

Each bit of a word holds the set of input bits it depends on. XOR, AND, OR and NOT unite the sets,
rotations and shifts move them, a bit a shift brings in holds none, and bit i of an addition or subtraction
holds what bits 0 ... i of both operands hold. A phase reads the values at its start. R_f and R_b are the
first round counts at which every output bit depends on every input bit, for Π and Π⁻¹. This is structural:
it over-approximates actual dependence, so that full dependency is necessary and not sufficient for full
diffusion, which the avalanche test observes.

A matrix is an array of (lane, bit, word), a row of 64-bit words per state bit, and `start` may hold any
input bits, the key and nonce bits of an instantiation among them. No constant's value is read.

Run on its known results by scripts/validate_tool.py (`dependency-small` and its second; R13). Analysis
code: the model never imports it. This tool makes no security claim.
"""
import sys
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional, Sequence, Tuple

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
for place in (str(ROOT / "research/004"), str(ROOT)):
    if place not in sys.path:
        sys.path.insert(0, place)

import ir  # noqa: E402

CODE = ("research/004/ir.py",)
FORWARD, INVERSE = "forward", "inverse"
LIMIT = 256
KIND = {"widths": [4, 8, 16, 32],
        "operations": "XOR, AND, OR, NOT, rotations, shifts, addition and subtraction of words",
        "model": "exact structural dependency, per round and direction, at 2×2, 3×3 and 4×4",
        "uses": [{"use": "R_f, R_b and the matrices at every supported size",
                  "covered_by": ["dependency-small"]}]}


# ------------------------------------------------------------------------------------- matrices

def words_for(bits: int) -> int:
    return (bits + 63) // 64


def identity(n: int, w: int) -> np.ndarray:
    """Each state bit depends on itself alone; input bit number lane · w + bit."""
    bits = 2 * n * n * w
    out = np.zeros((2 * n * n, w, words_for(bits)), dtype=np.uint64)
    for lane in range(2 * n * n):
        for bit in range(w):
            number = lane * w + bit
            out[lane, bit, number // 64] = np.uint64(1) << np.uint64(number % 64)
    return out


def full_rows(bits: int) -> np.ndarray:
    """One row holding every input bit."""
    row = np.full(words_for(bits), np.uint64(0xFFFFFFFFFFFFFFFF), dtype=np.uint64)
    if bits % 64:
        row[-1] = np.uint64((1 << (bits % 64)) - 1)
    return row


def evaluate(expr: Any, state: np.ndarray, w: int) -> np.ndarray:
    """The sets of each bit of an expression, an array of (bit, word)."""
    kind = type(expr)
    if kind is ir.Lane:
        return state[expr.index]
    if kind is ir.Constant:
        return np.zeros_like(state[0])
    if kind is ir.Not:
        return evaluate(expr.value, state, w)
    if kind is ir.Rotl:
        return np.roll(evaluate(expr.value, state, w), expr.amount, axis=0)
    if kind is ir.Shl:
        value = evaluate(expr.value, state, w)
        out = np.zeros_like(value)
        out[expr.amount:] = value[:w - expr.amount]
        return out
    if kind is ir.Shr:
        value = evaluate(expr.value, state, w)
        out = np.zeros_like(value)
        out[:w - expr.amount] = value[expr.amount:]
        return out
    return evaluate(expr.left, state, w) | evaluate(expr.right, state, w)


def apply_phase(phase: "ir.Phase", state: np.ndarray, w: int) -> None:
    """Each update reads the values at the phase's start."""
    written = []
    for update in phase.updates:
        if type(update) is ir.Rot:
            written.append((update.dst, np.roll(state[update.dst], update.amount, axis=0)))
            continue
        united = state[update.dst] | evaluate(update.expr, state, w)
        if update.op == "xor":
            written.append((update.dst, united))
        else:
            written.append((update.dst, np.bitwise_or.accumulate(united, axis=0)))
    for dst, value in written:
        state[dst] = value


def rounds_of(program: "ir.Program", start: np.ndarray) -> Iterator[np.ndarray]:
    """The matrix after each round, without end."""
    state = start.copy()
    while True:
        for phase in program.phases:
            apply_phase(phase, state, program.w)
        yield state.copy()


def direction_of(program: "ir.Program", direction: str) -> "ir.Program":
    return program if direction == FORWARD else ir.invert(program)


def matrix(program: "ir.Program", direction: str, rounds: int) -> np.ndarray:
    n, w = program.n, program.w
    walk = rounds_of(direction_of(program, direction), identity(n, w))
    for _ in range(rounds - 1):
        next(walk)
    return next(walk)


def holds_every(state: np.ndarray, bits: int) -> bool:
    return bool((state == full_rows(bits)).all())


def missing_pairs(state: np.ndarray, bits: int) -> int:
    """How many (output bit, input bit) pairs have no dependency."""
    ones = int(np.unpackbits(state.reshape(-1).view(np.uint8)).sum())
    return state.shape[0] * state.shape[1] * bits - ones


def walk(program: "ir.Program", direction: str, start: np.ndarray,
         limit: int) -> Iterator[Tuple[int, np.ndarray]]:
    """Round count and matrix, until the matrix stops changing or `limit` is reached."""
    previous = start
    for rounds, state in enumerate(rounds_of(direction_of(program, direction), start), start=1):
        yield rounds, state
        if rounds >= limit or bool((state == previous).all()):
            return
        previous = state


def first_full(program: "ir.Program", direction: str, limit: int = LIMIT,
               start: Optional[np.ndarray] = None, symbols: Optional[int] = None) -> Optional[int]:
    """R_f or R_b: the first round count at which every bit depends on every one of the `symbols`
    input bits, the whole state's by default, or None if that is not reached."""
    n, w = program.n, program.w
    bits = 2 * n * n * w if symbols is None else symbols
    begin = identity(n, w) if start is None else start
    for rounds, state in walk(program, direction, begin, limit):
        if holds_every(state, bits):
            return rounds
    return None


def margin(program: "ir.Program", start: np.ndarray, symbols: int, rounds_before_output: int,
           limit: int = LIMIT) -> Dict:
    """The propagation through instantiate: `start` holds the input bits each lane takes at key and
    nonce loading, `symbols` of them, and the call's rounds run before the first output. The margin
    is over R_f (R13)."""
    reached = first_full(program, FORWARD, limit, start, symbols)
    forward = first_full(program, FORWARD, limit)
    return {"every_bit_reached_after": reached, "rounds_before_first_output": rounds_before_output,
            "r_f": forward,
            "holds": reached is not None and reached <= rounds_before_output,
            "margin_over_r_f": None if forward is None else rounds_before_output - forward}


def as_sets(state: np.ndarray, w: int) -> Dict[Tuple[int, int], set]:
    """The matrix as {(lane, bit): {(lane, bit), ...}}, for comparison entry by entry."""
    out = {}
    for lane in range(state.shape[0]):
        for bit in range(w):
            held = np.unpackbits(state[lane, bit].view(np.uint8), bitorder="little")
            out[(lane, bit)] = {(int(number) // w, int(number) % w) for number in np.nonzero(held)[0]}
    return out


def dependent_bits(state: np.ndarray, flipped: int) -> np.ndarray:
    """A boolean array of (lane, bit): the output bits that depend on one input bit, which the
    avalanche test's cross-check reads."""
    word, bit = flipped // 64, flipped % 64
    return ((state[:, :, word] >> np.uint64(bit)) & np.uint64(1)).astype(bool)


def report(program: "ir.Program", limit: int = LIMIT) -> Dict:
    """R_f and R_b, and each round's count of pairs without dependency, in both directions."""
    n, w = program.n, program.w
    bits = 2 * n * n * w
    out: Dict[str, Any] = {}
    for direction in (FORWARD, INVERSE):
        counts = []
        first = None
        for rounds, state in walk(program, direction, identity(n, w), limit):
            counts.append(missing_pairs(state, bits))
            if holds_every(state, bits):
                first = rounds
                break
        out[direction] = {"first_full": first, "pairs_without_dependency": counts}
    return out


# ----------------------------------------------------------------------------------- known results

def differences(found: Dict, wanted: Dict) -> int:
    return sum(1 for key in wanted if found.get(key) != wanted[key]) + \
        sum(1 for key in found if key not in wanted)


def re_find_small(known, keep) -> Dict:
    rows = []
    for name, rounds_list in known.CASES:
        for n, w in known.PAIRS:
            program = ir.load(known.BUILD[name](n, w)).program
            for direction in (FORWARD, INVERSE):
                for rounds in rounds_list:
                    found = as_sets(matrix(program, direction, rounds), w)
                    wanted = known.expected(name, n, w, direction, rounds)
                    rows.append({"list": name, "n": n, "w": w, "direction": direction, "rounds": rounds,
                                 "entries": sum(len(v) for v in wanted.values()),
                                 "differences": differences(found, wanted)})
                seen = first_full(program, direction)
                rows.append({"list": name, "n": n, "w": w, "direction": direction,
                             "first_full": seen, "wanted": known.FIRST_FULL[name],
                             "differences": int(seen != known.FIRST_FULL[name])})
    return {"found": {"rows": rows}, "re_found": not any(row["differences"] for row in rows),
            "validated_kind": KIND}


def re_find_sweep(known, keep) -> Dict:
    rows = []
    for n, w in known.PAIRS:
        program = ir.load(known.sweep(n, w)).program
        length = 2 * n * n
        wanted_first = known.first_full(n)
        for direction, chosen in ((FORWARD, (1, 2, 3)), (INVERSE, (1, 2, length - 1, length))):
            for rounds in chosen:
                found = as_sets(matrix(program, direction, rounds), w)
                wanted = known.expected(n, w, direction, rounds)
                rows.append({"list": "sweep", "n": n, "w": w, "direction": direction, "rounds": rounds,
                             "entries": sum(len(v) for v in wanted.values()),
                             "differences": differences(found, wanted)})
            seen = first_full(program, direction)
            rows.append({"list": "sweep", "n": n, "w": w, "direction": direction, "first_full": seen,
                         "wanted": wanted_first[direction],
                         "differences": int(seen != wanted_first[direction])})
    return {"found": {"rows": rows}, "re_found": not any(row["differences"] for row in rows),
            "validated_kind": KIND}


RUNS = {"dependency-small": re_find_small, "dependency-small-second": re_find_sweep}


def validation(known_id: str, known, keep: Optional[Callable[[str, bytes], None]]) -> Dict:
    return RUNS[known_id](known, keep)
