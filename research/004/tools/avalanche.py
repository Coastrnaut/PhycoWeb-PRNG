"""Feature 004: the avalanche test (research R4, R13; data-model sections 5 and 7).

For each flipped bit of a set, N_a test states go through rounds 1 to R, and the difference of the two
runs is counted bit by bit, for Π and Π⁻¹. Two further sets test related inputs: each key and nonce bit
flipped in instantiation states, forward only, and the rotational pairs, the difference between Π^r(rot_k x)
and rot_k(Π^r x) for each k, both ways. Each difference bit is counted over the N_a states and over the
first 2^13 of them, and it fires if either count lies at or beyond its integer critical counts, so that a
bit that never flips fires.

Every run is cross-checked against the exact dependency matrices: where they show a bit independent of a
flipped bit, it must never flip. Any disagreement is a tool defect, exit 3 (research R4).

Run on its known results by scripts/validate_tool.py, one record per size: `avalanche-planted-n4` and so
on. At each round count from 1 to R every bit of the expected set must fire, the planted bits and every bit
the matrices show independent; any other firing is reported and decides nothing below R, and at R exactly
that set must fire. Analysis code: the model never imports it. This tool makes no security claim.
"""
import sys
import time
from fractions import Fraction
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
for place in (str(ROOT / "research/004/tools"), str(ROOT / "research/004"), str(ROOT)):
    if place not in sys.path:
        sys.path.insert(0, place)

import bias  # noqa: E402
import dependency  # noqa: E402
import ir  # noqa: E402
from protocol import devinputs_v3  # noqa: E402
from protocol.evidence import ToolFailure  # noqa: E402

CODE = ("research/004/tools/bias.py", "research/004/tools/dependency.py", bias.TABLE_REL,
        "research/004/ir.py", "protocol/seedsets.py", "phycoweb/model_v2.py", "phycoweb/lut.py")
HEAVY = ("avalanche-planted-n8", "avalanche-planted-n16", "avalanche-planted-second-n8",
         "avalanche-planted-second-n16")
W = 32
N_A = bias.N_A
N_FIRST = bias.N_A_FIRST
RELATED_BITS = 384
DELTA_A = {4: Fraction(443, 10000), 8: Fraction(451, 10000), 16: Fraction(465, 10000)}
LEAST_POWER = Fraction(9, 10)
KIND = {"widths": [32], "operations": "any list, its difference bits counted per round",
        "model": "the two-sided binomial test at integer critical counts, with the matrices' cross-check",
        "uses": [{"use": "the flip set, the related-key and related-nonce set and the rotational pairs at "
                         "4×4, 8×8 and 16×16 with w = 32", "covered_by": ["avalanche-planted"]}]}


def flip_set(n: int, w: int = W) -> List[int]:
    """F: every state bit at 4×4, and the 2w bits of each node on the main diagonal above it, as state
    bit numbers, lane · w + bit."""
    if n == 4:
        return list(range(2 * n * n * w))
    return [ir.lane(n, i, i, kind) * w + bit for i in range(n) for kind in (0, 1) for bit in range(w)]


def s_a(n: int, w: int = W) -> int:
    return (2 * len(flip_set(n, w)) + RELATED_BITS + 2 * (w - 1)) * (2 * n * n * w)


def two_counts(difference: np.ndarray, w: int) -> Tuple[np.ndarray, np.ndarray]:
    """The ones of a difference over the first 2^13 states and over all of them, a row per lane."""
    early = bias.ones(difference[:, :N_FIRST], w)
    return early, early + bias.ones(difference[:, N_FIRST:], w)


def trajectory(chosen: "ir.Loaded", states: np.ndarray, rows: Sequence[Optional[Sequence[int]]]) -> List[np.ndarray]:
    """The states after each round, computed once for every flip of a direction."""
    out = []
    for row in rows:
        states = bias.one_round(chosen, states, row)
        out.append(states)
    return out


def difference_counts(chosen: "ir.Loaded", base: Sequence[np.ndarray], second: np.ndarray,
                      rows: Sequence[Optional[Sequence[int]]], w: int) -> Tuple[np.ndarray, np.ndarray]:
    """The ones of the difference from `base`, the first input's trajectory, after each round, over the
    first 2^13 states and over all of them, two arrays of (round, lane, bit)."""
    early = np.zeros((len(rows), second.shape[0], w), dtype=np.int64)
    whole = early.copy()
    b = second
    for r, row in enumerate(rows):
        b = bias.one_round(chosen, b, row)
        early[r], whole[r] = two_counts(base[r] ^ b, w)
    return early, whole


def flipped(states: np.ndarray, number: int, w: int) -> np.ndarray:
    out = states.copy()
    out[number // w] ^= np.uint64(1) << np.uint64(number % w)
    return out


def rotated(states: np.ndarray, k: int, w: int) -> np.ndarray:
    mask = np.uint64((1 << w) - 1)
    return ((states << np.uint64(k)) | (states >> np.uint64(w - k))) & mask


def rotational_counts(chosen: "ir.Loaded", states: np.ndarray, k: int,
                      rows: Sequence[Optional[Sequence[int]]], w: int) -> Tuple[np.ndarray, np.ndarray]:
    """The ones of Π^r(rot_k x) xor rot_k(Π^r x) after each round, by the same two counts."""
    early = np.zeros((len(rows), states.shape[0], w), dtype=np.int64)
    whole = early.copy()
    a, b = rotated(states, k, w), states
    for r, row in enumerate(rows):
        a, b = bias.one_round(chosen, a, row), bias.one_round(chosen, b, row)
        early[r], whole[r] = two_counts(a ^ rotated(b, k, w), w)
    return early, whole


def lanes_mask(lanes: Sequence[int], shape: Tuple[int, int]) -> np.ndarray:
    out = np.zeros(shape, dtype=bool)
    out[list(lanes)] = True
    return out


class Tally:
    """One path's results: bits of the expected set that did not fire, firings outside it, by round."""

    def __init__(self, path: str, rounds: int, first: Dict, whole: Dict):
        self.path, self.rounds, self.first, self.whole = path, rounds, first, whole
        self.tests = 0
        self.missed = 0
        self.other_by_round = [0] * rounds
        self.lines: List[str] = []

    def add(self, tag: str, r: int, early: np.ndarray, whole: np.ndarray, expected: np.ndarray) -> None:
        """A bit fires if either count does, each at its own critical values (R4)."""
        fired = bias.fires(early, self.first) | bias.fires(whole, self.whole)
        self.tests += 1
        self.missed += int(np.count_nonzero(expected & ~fired))
        other = fired & ~expected
        self.other_by_round[r] += int(np.count_nonzero(other))
        for lane, bit in zip(*np.nonzero(other)):
            self.lines.append(f"{self.path} {tag} round {r + 1} lane {lane} bit {bit} "
                              f"counts {early[lane, bit]} {whole[lane, bit]}\n")

    def summary(self) -> Dict:
        return {"path": self.path, "tests": self.tests, "expected_bits_that_did_not_fire": self.missed,
                "other_firings_by_round": self.other_by_round,
                "other_firings_at_r": self.other_by_round[-1],
                "holds": self.missed == 0 and self.other_by_round[-1] == 0}


def cross_check(counts: np.ndarray, independent: np.ndarray, tag: str) -> None:
    """R4: a bit the matrices show independent of the flipped bit must never flip."""
    if counts[independent].any():
        raise ToolFailure(f"a difference bit the dependency matrices show independent flipped, {tag}")


def run_flips(loaded: "ir.Loaded", states: np.ndarray, numbers: Sequence[int], rows_of_direction: Dict,
              matrices: Dict[str, List[np.ndarray]], planted: Callable[[int], Sequence[int]],
              tally: Tally, directions: Sequence[str]) -> None:
    """Each flipped bit in each direction, each round's count judged against its expected set."""
    program = loaded.program
    inverse = ir.Loaded(ir.invert(program))
    w = program.w
    shape = (states.shape[0], w)
    lists = {direction: loaded if direction == dependency.FORWARD else inverse for direction in directions}
    base = {direction: trajectory(lists[direction], states, rows_of_direction[direction]) for direction in directions}
    for number in numbers:
        other = flipped(states, number, w)
        mask = lanes_mask(planted(number // w), shape)
        for direction in directions:
            early, whole = difference_counts(lists[direction], base[direction], other, rows_of_direction[direction], w)
            for r in range(whole.shape[0]):
                independent = ~dependency.dependent_bits(matrices[direction][r], number)
                tag = f"{direction} bit {number}"
                cross_check(whole[r], independent, f"{tag}, round {r + 1}")
                tally.add(tag, r, early[r], whole[r], independent | mask)


def run_rotations(loaded: "ir.Loaded", states: np.ndarray, planted: Sequence[int], tally: Tally,
                  rows_of_direction: Dict) -> None:
    program = loaded.program
    inverse = ir.Loaded(ir.invert(program))
    w = program.w
    mask = lanes_mask(planted, (states.shape[0], w))
    for k in range(1, w):
        for direction, chosen in ((dependency.FORWARD, loaded), (dependency.INVERSE, inverse)):
            early, whole = rotational_counts(chosen, states, k, rows_of_direction[direction], w)
            for r in range(whole.shape[0]):
                tally.add(f"{direction} k {k}", r, early[r], whole[r], mask)


def matrices_of(program: "ir.Program", rounds: int, directions: Sequence[str]) -> Dict[str, List[np.ndarray]]:
    out = {}
    for direction in directions:
        walk = dependency.rounds_of(dependency.direction_of(program, direction),
                                    dependency.identity(program.n, program.w))
        out[direction] = [next(walk) for _ in range(rounds)]
    return out


def words_of(raw: bytes) -> List[int]:
    return [int.from_bytes(raw[i:i + 4], "big") for i in range(0, len(raw), 4)]


def instantiation_states(known, n: int, count: int) -> np.ndarray:
    keys = devinputs_v3.load("dev", "key", ("dev",), count)
    nonces = devinputs_v3.load("dev", "nonce", ("dev",), count)
    return np.array([known.instantiation_state(n, words_of(keys[i]), words_of(nonces[i]))
                     for i in range(count)], dtype=np.uint64).T


def input_bits(known, n: int) -> List[int]:
    """The state bit each of the 384 key and nonce bits lands on, from the loader itself."""
    bits = []
    for words, place in ((8, "key"), (4, "nonce")):
        for word in range(words):
            key, nonce = [0] * 8, [0] * 4
            (key if place == "key" else nonce)[word] = 1
            state = known.instantiation_state(n, key, nonce)
            lane = [index for index, value in enumerate(state) if value][0]
            bits += [lane * W + bit for bit in range(W)]
    return bits


def verdict_code(entry: Dict) -> Dict:
    """Every count 0 to N_a of one difference bit: it must fire exactly at or beyond the two critical
    values of the table."""
    counts = np.arange(entry["n"] + 1)
    fired = bias.fires(counts, entry)
    wanted = (counts <= entry["low"]) | (counts >= entry["high"])
    return {"counts": int(counts.size), "low": entry["low"], "high": entry["high"],
            "holds": bool((fired == wanted).all()) and not bool(fired[entry["low"] + 1:entry["high"]].any())}


def power(entry: Dict, delta: Fraction) -> Fraction:
    """The chance that a bit of frequency 1/2 + delta fires, exactly."""
    p = Fraction(1, 2) + delta
    top, bottom = p.numerator, p.denominator
    n, low, high = entry["n"], entry["low"], entry["high"]
    other = bottom - top
    term = other ** n
    total = 0
    for k in range(n + 1):
        if k <= low or k >= high:
            total += term
        term = term * (n - k) * top // ((k + 1) * other)
    return Fraction(total, bottom ** n)


def re_find(known, size: int, keep) -> Dict:
    n = size
    rounds = known.rounds(n)
    first = bias.entry_for("avalanche", N_FIRST, s_a(n))
    entry = bias.entry_for("avalanche", N_A, s_a(n))
    states = bias_states(n)
    forward, inverse = dependency.FORWARD, dependency.INVERSE
    rows = {forward: [None] * rounds, inverse: [None] * rounds}

    unmixed = ir.load(known.unmixed(n))
    flips = Tally("flip set", rounds, first, entry)
    run_flips(unmixed, states, flip_set(n), rows, matrices_of(unmixed.program, rounds, (forward, inverse)),
              lambda lane: known.planted_bits("unmixed", n), flips, (forward, inverse))

    closed = ir.load(known.closed(n))
    related = Tally("related keys and nonces", rounds, first, entry)
    run_flips(closed, instantiation_states(known, n, N_A), input_bits(known, n), rows,
              matrices_of(closed.program, rounds, (forward,)),
              lambda lane: known.planted_bits("closed", n, lane), related, (forward,))

    commuting = ir.load(known.commuting(n))
    rotational = Tally("rotational pairs", rounds, first, entry)
    run_rotations(commuting, states, known.planted_bits("commuting", n), rotational, rows)

    tallies = (flips, related, rotational)
    keep(f"other-firings-n{n}.txt", "".join(line for t in tallies for line in t.lines).encode("ascii"))
    code = [verdict_code(first), verdict_code(entry)]
    strength = power(entry, DELTA_A[n])
    threshold = Fraction(entry["level_numerator"], entry["level_denominator"])
    found = {"size": n, "rounds": rounds, "n_a": N_A, "s_a": s_a(n),
             "critical": {"over the first 2^13": [first["low"], first["high"]],
                          "over N_a": [entry["low"], entry["high"]]},
             "paths": [t.summary() for t in tallies], "verdict_code": code,
             "power": {"delta": float(DELTA_A[n]), "value": float(strength)},
             "chance_of_a_false_firing_per_flipped_bit_at_most": float(2 * threshold * 2 * n * n * W)}
    held = all(t.summary()["holds"] for t in tallies) and all(item["holds"] for item in code) \
        and strength >= LEAST_POWER
    return {"found": found, "re_found": held, "validated_kind": KIND}


def bias_states(n: int) -> np.ndarray:
    values = devinputs_v3.load("dev", "state", ("dev",), N_A, n=n, w=W)
    return np.array([list(values[i]) for i in range(N_A)], dtype=np.uint64).T


def size_of(known_id: str) -> int:
    return int(known_id.rsplit("-n", 1)[1])


def validation(known_id: str, known, keep: Optional[Callable[[str, bytes], None]]) -> Dict:
    return re_find(known, size_of(known_id), keep)


def inputs(known_id: str) -> Dict:
    n = size_of(known_id)
    return {"sets": [{"namespace": "dev", "kind": "state", "n": n, "w": W, "index_range": [0, N_A - 1],
                      "fingerprint": devinputs_v3.fingerprint("dev", "state", n, W)},
                     {"namespace": "dev", "kind": "key", "index_range": [0, N_A - 1],
                      "fingerprint": devinputs_v3.fingerprint("dev", "key")},
                     {"namespace": "dev", "kind": "nonce", "index_range": [0, N_A - 1],
                      "fingerprint": devinputs_v3.fingerprint("dev", "nonce")}]}


def projection(known_id: str) -> Tuple[float, Dict]:
    """Two flipped bits run as a record runs them, with their cross-check and tally, and the whole
    record's flips, with its three trajectories and its dependency matrices, at most a few minutes."""
    import importlib.util
    n = size_of(known_id)
    stem = known_id.rsplit("-n", 1)[0]
    path = ROOT / "research/004/validation" / f"{stem}.py"
    spec = importlib.util.spec_from_file_location("avalanche_" + stem.replace("-", "_"), path)
    known = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = known
    spec.loader.exec_module(known)
    rounds = known.rounds(n)
    loaded = ir.load(known.unmixed(n))
    states = bias_states(n)
    forward = dependency.FORWARD
    started = time.monotonic()
    matrices = matrices_of(loaded.program, rounds, (forward,))
    tables = time.monotonic() - started
    started = time.monotonic()
    trajectory(loaded, states, [None] * rounds)
    once = time.monotonic() - started
    tally = Tally("projection", rounds, bias.entry_for("avalanche", N_FIRST, s_a(n)),
                  bias.entry_for("avalanche", N_A, s_a(n)))
    started = time.monotonic()
    run_flips(loaded, states, flip_set(n)[:2], {forward: [None] * rounds}, matrices, lambda lane: (), tally, (forward,))
    per_flip = (time.monotonic() - started - once) / 2
    flips = 2 * len(flip_set(n)) + RELATED_BITS + 2 * (W - 1)
    seconds = per_flip * flips + 3 * once + 3 * tables
    return seconds / 3600.0, {"seconds_per_flip": per_flip, "flips": flips, "seconds_per_trajectory": once,
                              "seconds_per_matrix_set": tables}
