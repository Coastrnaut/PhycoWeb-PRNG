"""Feature 004: the frequency test and the uniform controls' counts (research R4), and their validation.

The ones in each bit of a state are counted, and a bit fires if its count lies at or beyond two integer
critical counts, derived once by exact integer arithmetic and committed in critical_counts.json, so that
a verdict compares integers. scipy computes the p-values, which are reported and decide nothing.

    python research/004/tools/bias.py --table     appends to the table the entries this file names

Run on its known results by scripts/validate_tool.py (`s12`, `s14`, `s15` and their seconds; R4, R13).
Analysis code: the model never imports it. Statistical evidence is not evidence of security, and this
tool makes no security claim.
"""
import argparse
import functools
import hashlib
import json
import math
import sys
from array import array
from fractions import Fraction
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[3]
for place in (str(ROOT / "research/004"), str(ROOT)):
    if place not in sys.path:
        sys.path.insert(0, place)

import ir  # noqa: E402
from phycoweb.model_v2 import M32, PhycoWebEngineV2  # noqa: E402
from protocol import devinputs_v3, seedsets  # noqa: E402

MODEL_ID = "phyco-v2"
TABLE_REL = "research/004/tools/critical_counts.json"
CENSUS_REL = "research/security/vein-class-census.json"
PROBES_REL = "research/security/step-probes.json"
CODE = (TABLE_REL, CENSUS_REL, PROBES_REL, "research/004/ir.py", "protocol/seedsets.py",
        "phycoweb/model_v2.py", "phycoweb/lut.py")
W = 32
N = 2 ** 20
N_A = 2 ** 13
BATCH = 2 ** 16
SIZES = (4, 8, 16)
FLIPS = {4: 1024, 8: 512, 16: 1024}
DELTA = {4: 0.0030, 8: 0.0031, 16: 0.0033}
TARGET = Fraction(5, 1000)
AVALANCHE_ROUNDS = 128
STEPS = 200_000
EDGE_SEEDS = ((0, 0, 0, 0), (65535, 65535, 65535, 65535))
STARTS = 2 ** 14
DESCENT_STEPS = 16
EDGE = 1 << 31
S15_BOUND = 2 ** 128 * (2 ** 31 + 1) ** 4
VEIN_S = 32
TAIL = 0.005
PLANTED_FIRES = (82, 97)
MOST_UNPLANTED = 3
FAMILIES = (("class 5", range(0, 100)), ("second", range(100, 200)))
KIND = {"widths": [32], "operations": "ones per bit of 32-bit words",
        "model": "the two-sided binomial test at integer critical counts",
        "uses": [{"use": "the frequency test at 4×4, 8×8 and 16×16 with w = 32",
                  "covered_by": ["s14", "the two synthetic families"]},
                 {"use": "the uniform controls' counts at those sizes",
                  "covered_by": ["s14", "the two synthetic families"]}]}


# ----------------------------------------------------------------------------- critical counts

@functools.lru_cache(maxsize=None)
def central_binomial(n: int) -> int:
    """C(n, n/2) for even n, the product of its prime powers by Legendre's formula: exact, and quick
    where a step-by-step product would pass half a million times through million-bit integers."""
    half = n // 2
    sieve = np.ones(n + 1, dtype=bool)
    sieve[:2] = False
    for p in range(2, math.isqrt(n) + 1):
        if sieve[p]:
            sieve[p * p::p] = False
    factors = []
    for p in map(int, np.nonzero(sieve)[0]):
        exponent, power = 0, p
        while power <= n:
            exponent += n // power - 2 * (half // power)
            power *= p
        if exponent:
            factors.append(p ** exponent)
    while len(factors) > 1:
        factors = [factors[i] * factors[i + 1] if i + 1 < len(factors) else factors[i]
                   for i in range(0, len(factors), 2)]
    return factors[0]


def critical(n: int, level: Fraction) -> Tuple[int, int]:
    """The largest c with twice P(X <= c) at most `level`, X binomial(n, 1/2), and n - c. n is even.
    The sum runs outward from the centre, about 12 standard deviations of terms in all, against half
    a million from the tail at n = 2^20; every step is integer arithmetic."""
    if n % 2:
        raise ValueError("n is even here")
    total = 1 << n
    k = n // 2
    term = central_binomial(n)
    inside = term
    while (total - inside) * level.denominator > level.numerator * total:
        term = term * k // (n - k + 1)
        k -= 1
        inside += 2 * term
    return k - 1, n - k + 1


def frequency_level(s: int) -> Fraction:
    return TARGET / s


def avalanche_level(s_a: int) -> Fraction:
    return TARGET / (AVALANCHE_ROUNDS * s_a)


def state_bits(n: int) -> int:
    return 2 * W * n * n


def table_entries() -> List[Dict]:
    """Every (N, S) and (N_a, S_A) of R4, and the count of the vein lanes that S14 reads."""
    out = []

    def entry(test: str, n: int, s: int, level: Fraction) -> None:
        low, high = critical(n, level)
        out.append({"test": test, "n": n, "s": s, "level_numerator": level.numerator,
                    "level_denominator": level.denominator, "low": low, "high": high})

    for size in SIZES:
        entry("frequency", N, 4 * state_bits(size), frequency_level(4 * state_bits(size)))
    for size in SIZES:
        s_a = (2 * FLIPS[size] + 384 + 2 * (W - 1)) * state_bits(size)
        entry("avalanche", N_A, s_a, avalanche_level(s_a))
    entry("vein-lanes", vein_count(), VEIN_S, frequency_level(VEIN_S))
    return out


def vein_count() -> int:
    return 3 * STEPS * 4


def read_table(root: Path = ROOT) -> Dict:
    return json.loads((root / TABLE_REL).read_bytes().decode("utf-8"))


def table_text(entries: Sequence[Dict]) -> bytes:
    body = {"description": "integer critical counts of research R4, appended to and never changed",
            "entries": list(entries)}
    return (json.dumps(body, indent=1) + "\n").encode("utf-8")


def write_table() -> int:
    """Append the entries the file does not hold; those it holds never change (R4)."""
    path = ROOT / TABLE_REL
    held = json.loads(path.read_bytes().decode("utf-8"))["entries"] if path.exists() else []
    known = {(e["test"], e["n"], e["s"]) for e in held}
    added = [e for e in table_entries() if (e["test"], e["n"], e["s"]) not in known]
    path.write_bytes(table_text(held + added))
    print(f"{TABLE_REL}: {len(held) + len(added)} entries, {len(added)} added")
    return 0


def entry_for(test: str, n: int, s: int, table: Optional[Dict] = None) -> Dict:
    for entry in (table or read_table())["entries"]:
        if (entry["test"], entry["n"], entry["s"]) == (test, n, s):
            return entry
    raise ValueError(f"no critical counts for {test} at ({n}, {s})")


def fires(counts: np.ndarray, entry: Dict) -> np.ndarray:
    """The verdict, integers only: a count at or beyond either critical value."""
    return (counts <= entry["low"]) | (counts >= entry["high"])


def p_values(counts: np.ndarray, n: int) -> np.ndarray:
    """Two-sided, twice the smaller tail, at most 1. Reported only: a verdict never reads them."""
    below = stats.binom.cdf(counts, n, 0.5)
    above = stats.binom.sf(counts - 1, n, 0.5)
    return np.minimum(1.0, 2.0 * np.minimum(below, above))


# -------------------------------------------------------------------------------------- counting

def ones(states: np.ndarray, w: int = W) -> np.ndarray:
    """Ones in each lane and bit of a batch, one row per lane, one column per bit, bit 0 first."""
    out = np.zeros((states.shape[0], w), dtype=np.int64)
    for bit in range(w):
        out[:, bit] = np.count_nonzero((states >> np.uint64(bit)) & np.uint64(1), axis=1)
    return out


def test_order(counts: np.ndarray) -> np.ndarray:
    """R4's bit order: lanes in index order and each lane's bits most significant first."""
    return counts[:, ::-1].ravel()


def rows_of(table: Sequence[Sequence[int]], rounds: int, backward: bool) -> List[Optional[Sequence[int]]]:
    """One row per round; Π⁻¹ reads the table from its end, round 1 of it undoing the last round."""
    if not table:
        return [None] * rounds
    return [table[len(table) - 1 - r] if backward else table[r] for r in range(rounds)]


def one_round(loaded: "ir.Loaded", state: np.ndarray, row: Optional[Sequence[int]]) -> np.ndarray:
    return ir.permute_batch(loaded, state, [row] if row is not None else (), None if row else 1)


def frequency_counts(loaded: "ir.Loaded", batches: Iterable[np.ndarray],
                     table: Sequence[Sequence[int]], rounds: int) -> Dict[str, np.ndarray]:
    """One input set through rounds 1 to `rounds` of Π, and separately of Π⁻¹: the ones after every
    round, as arrays of (round, lane, bit), in batches of 2^16 at most."""
    program = loaded.program
    lanes = 2 * program.n ** 2
    inverse = ir.Loaded(ir.invert(program))
    out = {"forward": np.zeros((rounds, lanes, program.w), dtype=np.int64),
           "inverse": np.zeros((rounds, lanes, program.w), dtype=np.int64)}
    for batch in batches:
        for name, chosen, backward in (("forward", loaded, False), ("inverse", inverse, True)):
            state = batch
            for r, row in enumerate(rows_of(table, rounds, backward)):
                state = one_round(chosen, state, row)
                out[name][r] += ones(state, program.w)
    return out


def fired_bits(counts: np.ndarray, entry: Dict) -> List[List[int]]:
    """[position, count] of each bit that fires, positions in R4's bit order."""
    flat = test_order(counts) if counts.ndim == 2 else counts
    return [[int(p), int(flat[p])] for p in np.nonzero(fires(flat, entry))[0]]


def control_counts(batches: Iterable[np.ndarray], w: int = W) -> np.ndarray:
    """A uniform control of the frequency test: the ones of the control states themselves."""
    total = None
    for batch in batches:
        counted = ones(batch, w)
        total = counted if total is None else total + counted
    return total


def control_differences(states: np.ndarray) -> np.ndarray:
    """A uniform control of the avalanche test: XOR difference i is state 2i xor state 2i + 1."""
    return states[:, 0::2] ^ states[:, 1::2]


def batches_of(states: np.ndarray, size: int = BATCH) -> Iterable[np.ndarray]:
    for start in range(0, states.shape[1], size):
        yield states[:, start:start + size]


# ------------------------------------------------------------------------------- synthetic counts

def planted_position(family: str, j: int, s: int) -> int:
    return j % s if family == "class 5" else (j - 100) * s // 100


def draw_set(seed: int, s: int, planted: int, delta: float, n: int = N) -> np.ndarray:
    """One binomial(n, 1/2) count per tested bit, in the test's bit order, the planted bit's at
    1/2 + delta (R3, class 5)."""
    chance = np.full(s, 0.5)
    chance[planted] += delta
    return np.random.Generator(np.random.PCG64(seed)).binomial(n, chance)


def set_text(counts: np.ndarray) -> bytes:
    """Decimal text, one count per line in the test's bit order, each line ending in LF."""
    return "".join(f"{int(c)}\n" for c in counts).encode("ascii")


def run_family(family: str, indices: Iterable[int], size: int, entry: Dict,
               keep: Callable[[str, bytes], None]) -> Dict:
    s = 4 * state_bits(size)
    seeds = devinputs_v3.load("dev", "synthetic", ("dev",), 200, n=size)
    summaries = []
    for j in indices:
        planted = planted_position(family, j, s)
        counts = draw_set(seeds[j], s, planted, DELTA[size])
        text = set_text(counts)
        keep(f"synthetic-n{size}-{j}.txt", text)
        fired = [[int(p), int(counts[p])] for p in np.nonzero(fires(counts, entry))[0]]
        summaries.append({"j": j, "sha256": hashlib.sha256(text).hexdigest(), "planted": planted,
                          "planted_count": int(counts[planted]),
                          "planted_fires": any(p == planted for p, _ in fired),
                          "unplanted": [item for item in fired if item[0] != planted]})
    return summarise(family, size, summaries)


def summarise(family: str, size: int, sets: List[Dict]) -> Dict:
    fired = sum(1 for item in sets if item["planted_fires"])
    unplanted = sum(1 for item in sets if item["unplanted"])
    return {"family": family, "size": size, "sets": sets, "planted_fired": fired,
            "sets_with_unplanted": unplanted, "holds": family_holds(fired, unplanted)}


def family_holds(fired: int, unplanted: int) -> bool:
    return PLANTED_FIRES[0] <= fired <= PLANTED_FIRES[1] and unplanted <= MOST_UNPLANTED


# --------------------------------------------------------------------------------- phyco-v2's veins

def recorded(rel: str, root: Path = ROOT) -> Dict:
    return json.loads((root / rel).read_bytes().decode("utf-8"))


def vein_values() -> np.ndarray:
    """Every vein value after every step, from the first development seed and the two edge seeds,
    as step_probes.py and vein_class_census.py sampled them."""
    values = array("I")
    for seed in [seedsets.load("dev", allow=("dev",))[0]] + list(EDGE_SEEDS):
        engine = PhycoWebEngineV2(list(seed))
        for _ in range(STEPS):
            engine.compute_block()
            values.extend(engine.D)
    return np.frombuffer(values, dtype=np.uint32).astype(np.uint64)


def descent() -> Dict:
    """S12 and S15's count: DESCENT_STEPS steps from uniform starting states, the veins read after."""
    states = devinputs_v3.load("dev", "state", ("dev",), STARTS, n=2, w=W)
    above = off_edge = bit31 = 0
    largest = 0
    for i in range(STARTS):
        words = list(states[i])
        engine = PhycoWebEngineV2.__new__(PhycoWebEngineV2)
        engine.P, engine.D = words[0::2], words[1::2]
        engine.phase_a = engine.phase_b = engine.disruptions = engine.step_count = 0
        for _ in range(DESCENT_STEPS):
            engine.compute_block()
        for word in engine.D:
            largest = max(largest, word)
            above += word > EDGE
            bit31 += word >> 31
            off_edge += bool(word >> 31) and word != EDGE
    return {"starts": STARTS, "steps": DESCENT_STEPS, "veins_above_2_31": above, "bit31_set": bit31,
            "bit31_off_the_edge": off_edge, "largest": largest}


def re_find_s12(known, keep) -> Dict:
    values = vein_values()
    wanted = recorded(CENSUS_REL)["totals"]
    classes = [int(np.count_nonzero((values >> np.uint64(30)) == c)) for c in range(4)]
    after = descent()
    found = {"vein_values": int(values.size), "class_counts": classes,
             "bit31_set": int(np.count_nonzero(values >> np.uint64(31))), "descent": after}
    held = classes == wanted["class_counts"] and found["bit31_set"] == wanted["bit31_set"] \
        and found["vein_values"] == wanted["vein_values"] and after["bit31_off_the_edge"] == 0 \
        and after["veins_above_2_31"] == 0
    return {"found": found, "re_found": held, "validated_kind": KIND}


def interval(fraction: float, n: int) -> Tuple[int, int]:
    """The binomial interval around a recorded fraction at n, at most 0.005 in each tail."""
    return int(stats.binom.ppf(TAIL, n, fraction)), int(stats.binom.ppf(1 - TAIL, n, fraction))


def re_find_s14(known, keep) -> Dict:
    values = vein_values()
    wanted = recorded(PROBES_REL)["s14_bit_bias"]
    counts = ones(values.reshape(1, -1))[0][::-1]
    total = int(values.size)
    entry = entry_for("vein-lanes", total, VEIN_S)
    bounds = [interval(f, total) for f in wanted["d_ones_frequency_bit31_to_bit0"]]
    inside = [low <= int(c) <= high for c, (low, high) in zip(counts, bounds)]
    differ = int(np.count_nonzero(((values >> np.uint64(30)) ^ (values >> np.uint64(29))) & np.uint64(1)))
    span = [f"0x{int(values.min()):08X}", f"0x{int(values.max()):08X}"]
    fired = [31 - int(p) for p in np.nonzero(fires(counts, entry))[0]]
    table = read_table()
    families = []
    for size in SIZES:
        chosen = entry_for("frequency", N, 4 * state_bits(size), table)
        families += [run_family(name, indices, size, chosen, keep) for name, indices in FAMILIES]
    found = {"vein_values": total, "d_range": span, "ones_bit31_to_bit0": [int(c) for c in counts],
             "intervals": bounds, "bits_that_fire": fired, "bit30_differs_from_bit29": differ,
             "numpy": np.__version__, "families": families}
    held = all(inside) and span == wanted["d_range"] and int(counts[0]) == 0 and differ == total \
        and {31, 30, 29, 28, 27} <= set(fired) and all(family["holds"] for family in families)
    return {"found": found, "re_found": held, "validated_kind": KIND}


def re_find_s15(known, keep) -> Dict:
    after = descent()
    range_top = EDGE if after["bit31_off_the_edge"] == 0 and after["veins_above_2_31"] == 0 else M32
    bound = 2 ** 128 * (range_top + 1) ** 4
    found = dict(after, range_top=range_top, bound=str(bound))
    return {"found": found, "re_found": bound == S15_BOUND, "validated_kind": KIND}


# -------------------------------------------------------------------- the stated maps of the seconds

def stated_words(count: int = STARTS) -> List[List[int]]:
    """Four 32-bit words per test state, read from the state kind at 2×2."""
    states = devinputs_v3.load("dev", "state", ("dev",), count, n=2, w=W)
    return [list(states[i])[:4] for i in range(count)]


def re_find_s12_second(known, keep) -> Dict:
    edges = [[value, known.h(value)] for value, _ in known.EDGE]
    outputs = [word for state in stated_words() for word in known.step(state)]
    outputs += [word for _, word in edges]
    off = sum(1 for word in outputs if word >> 31 and word != known.TOP)
    held = off == 0 and all(known.h(value) == want for value, want in known.EDGE)
    return {"found": {"bit31_off_the_edge": off, "edge": edges}, "re_found": held,
            "validated_kind": KIND}


def re_find_s14_second(known, keep) -> Dict:
    outputs = np.array([known.step(state) for state in stated_words()], dtype=np.uint64).ravel()
    counts = ones(outputs.reshape(1, -1))[0]
    total = int(outputs.size)
    bounds = {bit: interval(f, total) for bit, f in known.FREQUENCY.items()}
    held = all(bounds[bit][0] <= int(counts[bit]) <= bounds[bit][1] for bit in bounds)
    return {"found": {"words": total, "ones_bit0_to_bit31": [int(c) for c in counts]},
            "re_found": held, "validated_kind": KIND}


def re_find_s15_second(known, keep) -> Dict:
    words = [word for state in stated_words() for word in state] + list(known.EDGE)
    after = [known.after(word, known.STEPS) for word in words]
    top = max(after)
    off = sum(1 for word in after if word >> 28 and word != known.LIMIT)
    bound = 2 ** 128 * (top + 1) ** 4
    held = off == 0 and top <= known.LIMIT and bound == known.BOUND \
        and known.after(known.EDGE[0], known.STEPS - 1) > known.LIMIT
    return {"found": {"largest": top, "bit28_off_the_edge": off, "bound": str(bound)},
            "re_found": held, "validated_kind": KIND}


RUNS = {"s12": re_find_s12, "s14": re_find_s14, "s15": re_find_s15, "s12-second": re_find_s12_second,
        "s14-second": re_find_s14_second, "s15-second": re_find_s15_second}


def validation(known_id: str, known, keep: Callable[[str, bytes], None]) -> Dict:
    return RUNS[known_id](known, keep)


def inputs(known_id: str) -> Dict:
    states = {"namespace": "dev", "kind": "state", "n": 2, "w": W, "index_range": [0, STARTS - 1],
              "fingerprint": devinputs_v3.fingerprint("dev", "state", 2, W)}
    seeds = {"namespace": "feature-002/dev", "kind": "seed", "index_range": [0, 0],
             "fingerprint": seedsets.FINGERPRINTS["dev"], "edge_seeds": [list(s) for s in EDGE_SEEDS]}
    if known_id == "s12":
        return {"sets": [seeds, states]}
    if known_id == "s14":
        synthetic = [{"namespace": "dev", "kind": "synthetic", "n": size, "index_range": [0, 199],
                      "fingerprint": devinputs_v3.fingerprint("dev", "synthetic", size)}
                     for size in SIZES]
        return {"sets": [seeds] + synthetic}
    return {"sets": [states]}


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--table", action="store_true", required=True)
    parser.parse_args(argv)
    return write_table()


if __name__ == "__main__":
    sys.exit(main())
