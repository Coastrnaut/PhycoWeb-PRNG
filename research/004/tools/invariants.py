"""Feature 004: the invariant checks (research R13; data-model section 5).

The sums modulo 2^w and the XORs of the pressure lanes and of the vein lanes, over the whole state and
over each colour class of the size's schedule, after one round and after a full call. A form that
keeps its value on every test state fails the check. A form that holds on more test states than its
chance rate, 2^-w, allows by a binomial test at the bias rule's level, fails as a probabilistic invariant.
The critical count is derived by exact integer arithmetic, so that the verdict compares integers.

The difference mode takes an input difference, as an addition to the lanes, and reports whether it
comes out unchanged and whether the successors coincide, beside each other.

Run on its known results by scripts/validate_tool.py (`s13-decay`, `s13-transport`, the stated lists and
their seconds; R13). Analysis code: the model never imports it. This tool makes no security claim.
"""
import functools
import importlib.util
import json
import math
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[3]
for place in (str(ROOT / "research/004"), str(ROOT)):
    if place not in sys.path:
        sys.path.insert(0, place)

import ir  # noqa: E402
from phycoweb.model_v2 import M32, PhycoWebEngineV2  # noqa: E402
from protocol import devinputs_v3, seedsets  # noqa: E402

PROBES_REL = "research/security/step_probes.py"
RECORDED_REL = "research/security/step-probes.json"
CODE = (PROBES_REL, RECORDED_REL, "research/004/ir.py", "protocol/seedsets.py", "phycoweb/model_v2.py",
        "phycoweb/lut.py")
OPS = ("sum", "xor")
KINDS = (("pressure", ir.PRESSURE), ("vein", ir.VEIN))
TEST_STATES = 2 ** 10
ROUND_COUNTS = 2
TARGET = Fraction(5, 1000)
EVEN_FORMS = 12
TAIL = 0.005
SHARE_STATES = 2 ** 14
KIND = {"widths": [8, 16, 32],
        "operations": "sums modulo 2^w and XORs of lanes, and additions to lanes as input differences",
        "model": "forms kept on every test state, and the binomial test against the chance rate 2^-w",
        "uses": [{"use": "the invariant checks at n = 3, 4, 8 and 16",
                  "covered_by": ["invariants-planted", "s13-decay", "s13-transport"]}]}


# ---------------------------------------------------------------------------------------- forms

def regions(n: int) -> Tuple[Any, ...]:
    return ("all",) + tuple(range(ir.colours(n)))


def forms(n: int) -> List[Tuple[str, str, Any]]:
    return [(op, kind, region) for op in OPS for kind, _ in KINDS for region in regions(n)]


def lanes_of(n: int, kind: int, region: Any) -> List[int]:
    return [ir.lane(n, i, j, kind) for i in range(n) for j in range(n)
            if region == "all" or ir.colour(n, i, j) == region]


def form_values(states: np.ndarray, n: int, w: int) -> Dict[Tuple[str, str, Any], np.ndarray]:
    """Each form's value on each state of a batch, one row per lane."""
    mask = np.uint64((1 << w) - 1)
    values = {}
    for kind_name, kind in KINDS:
        for region in regions(n):
            picked = states[lanes_of(n, kind, region)]
            values[("sum", kind_name, region)] = picked.sum(axis=0, dtype=np.uint64) & mask
            values[("xor", kind_name, region)] = np.bitwise_xor.reduce(picked, axis=0)
    return values


def level_of(form: Tuple[str, str, Any], n: int) -> Fraction:
    """R13: 0.005 over the forms and round counts tested. At odd n the colour forms are a new set
    tested in addition, over all the check's forms, and the forms already stated keep their level."""
    if n % 2 and form[2] != "all":
        return TARGET / (len(forms(n)) * ROUND_COUNTS)
    return TARGET / (EVEN_FORMS * ROUND_COUNTS)


@functools.lru_cache(maxsize=None)
def critical_count(states: int, w: int, level: Fraction) -> int:
    """The smallest c with P(X >= c) at most `level`, X binomial(states, 2^-w), in integers: the tail
    is summed down from `states`, each term C(states, k) · (2^w - 1)^(states - k), over 2^(w · states)."""
    other = (1 << w) - 1
    total = level.numerator << (w * states)
    k = states
    term = 1
    tail = 0
    while k >= 0:
        if (tail + term) * level.denominator > total:
            return k + 1
        tail += term
        term = term * k * other // (states - k + 1)
        k -= 1
    return 0


def above_chance(count: int, states: int, w: int, level: Fraction) -> bool:
    return count >= critical_count(states, w, level)


def rows_for(table: Sequence[Sequence[int]], rounds: int) -> Sequence[Sequence[int]]:
    return table[:rounds] if table else ()


def check(loaded: "ir.Loaded", states: np.ndarray, table: Sequence[Sequence[int]],
          round_counts: Sequence[int]) -> Dict[int, Dict]:
    """Per round count: how many test states each form holds on, those kept on all of them, and those
    above their chance rate but not kept."""
    program = loaded.program
    n, w, m = program.n, program.w, states.shape[1]
    before = form_values(states, n, w)
    out = {}
    for rounds in round_counts:
        rows = rows_for(table, rounds)
        after = form_values(ir.permute_batch(loaded, states, rows, None if rows else rounds), n, w)
        held = {form: int(np.count_nonzero(before[form] == after[form])) for form in before}
        kept = [form for form, count in held.items() if count == m]
        over = [form for form, count in held.items()
                if count < m and above_chance(count, m, w, level_of(form, n))]
        out[rounds] = {"held": held, "kept": kept, "above_chance": over}
    return out


def test_states(n: int, w: int, count: int = TEST_STATES) -> np.ndarray:
    values = devinputs_v3.load("dev", "state", ("dev",), count, n=n, w=w)
    return np.array([list(values[i]) for i in range(count)], dtype=np.uint64).T


def difference_kept(loaded: "ir.Loaded", states: np.ndarray, delta: Dict[int, int],
                    table: Sequence[Sequence[int]], rounds: int) -> Dict:
    """An input difference, added to its lanes: on how many states it comes out unchanged, and on how
    many the two successors coincide."""
    program = loaded.program
    mask = np.uint64((1 << program.w) - 1)
    shift = np.zeros(states.shape[0], dtype=np.uint64)
    for lane, value in delta.items():
        shift[lane] = np.uint64(value)
    other = (states + shift[:, None]) & mask
    rows = rows_for(table, rounds)
    how = None if rows else rounds
    first = ir.permute_batch(loaded, states, rows, how)
    second = ir.permute_batch(loaded, other, rows, how)
    moved = (second - first) & mask
    return {"states": int(states.shape[1]),
            "unchanged": int(np.count_nonzero((moved == shift[:, None]).all(axis=0))),
            "coinciding": int(np.count_nonzero((first == second).all(axis=0)))}


def interval(fraction: float, n: int) -> Tuple[int, int]:
    """The binomial interval around a recorded fraction at n, at most 0.005 in each tail."""
    return int(stats.binom.ppf(TAIL, n, fraction)), int(stats.binom.ppf(1 - TAIL, n, fraction))


def in_interval(count: int, fractions: Iterable[float], n: int) -> bool:
    return all(low <= count <= high for low, high in (interval(f, n) for f in fractions))


# ---------------------------------------------------------------------------------------- phyco-v2

def probes():
    """research/security/step_probes.py, which holds the transport difference and the model's parts."""
    name = "step_probes"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, ROOT / PROBES_REL)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]


def recorded() -> Dict:
    return json.loads((ROOT / RECORDED_REL).read_bytes().decode("utf-8"))


def decay_mode() -> Dict:
    """S13(a): each vein state 16m + 15 beside 16m + 16, within one class, stepped once."""
    p = probes()
    engine = PhycoWebEngineV2(list(p.DEV[0]))
    tested = same = with_partner = 0
    for _ in range(p.DECAY_STEPS):
        engine.compute_block()
        partner = False
        for k in range(4):
            low = engine.D[k] | 0xF
            if (low >> 30) != ((low + 1) >> 30):
                continue
            partner |= (engine.D[k] & 0xF) in (0x0, 0xF)
            a, b = p.clone(engine), p.clone(engine)
            a.D[k], b.D[k] = low, low + 1
            a.compute_block()
            b.compute_block()
            tested += 1
            same += p.state(a) == p.state(b)
        with_partner += partner
    return {"steps": p.DECAY_STEPS, "pairs_tested": tested, "identical_successors": same,
            "states_with_a_partner": with_partner}


def re_find_decay(known, keep) -> Dict:
    found = decay_mode()
    wanted = recorded()["s13_vein_decay"]
    shares = (wanted["share_with_a_partner"], wanted["expected_share"])
    held = found["pairs_tested"] > 0 and found["identical_successors"] == found["pairs_tested"] \
        and in_interval(found["states_with_a_partner"], shares, found["steps"])
    return {"found": found, "re_found": held, "validated_kind": KIND}


def transport_mode() -> Dict:
    """S13(b): with all four veins in class 1, the transport difference added to the pressures."""
    p = probes()
    engine = PhycoWebEngineV2(list(p.DEV[0]))
    probed = unchanged = coinciding = 0
    for _ in range(p.ALT_STEPS):
        engine.compute_block()
        if any(d >> 30 != 1 for d in engine.D):
            continue
        a, b = p.clone(engine), p.clone(engine)
        b.P = [(x + y) & M32 for x, y in zip(b.P, p.V2)]
        unchanged += p.flux_and_transport(a)[1] == p.flux_and_transport(b)[1]
        a.compute_block()
        b.compute_block()
        probed += 1
        coinciding += p.state(a) == p.state(b)
    return {"steps": p.ALT_STEPS, "all_class_1_states": probed, "transport_unchanged": unchanged,
            "identical_successors": coinciding}


def re_find_transport(known, keep) -> Dict:
    found = transport_mode()
    wanted = recorded()["s13_alternating_mode"]
    shares = (wanted["share_identical"], wanted["expected_share"])
    held = found["all_class_1_states"] > 0 \
        and found["transport_unchanged"] == found["all_class_1_states"] \
        and in_interval(found["identical_successors"], shares, found["all_class_1_states"])
    return {"found": found, "re_found": held, "validated_kind": KIND}


# -------------------------------------------------------------------------------- the stated results

def readable(form: Tuple[str, str, Any]) -> str:
    return "/".join(str(part) for part in form)


def re_find_planted(known, keep) -> Dict:
    """Every list at every width: its kept forms exactly, and on `none` nothing above chance."""
    results = []
    held = True
    for label, n, build, wanted in known.CASES:
        for w in known.WIDTHS:
            loaded = ir.load(build(n, w))
            out = check(loaded, test_states(n, w), (), (1, known.ROUNDS))
            for rounds in (1, known.ROUNDS):
                kept, over = out[rounds]["kept"], out[rounds]["above_chance"]
                held = held and set(kept) == set(wanted[rounds])
                if label == "none":
                    held = held and not over
                results.append({"list": label, "n": n, "w": w, "rounds": rounds,
                                "kept": sorted(map(readable, kept)),
                                "above_chance": sorted(map(readable, over))})
    return {"found": {"lists": results}, "re_found": held, "validated_kind": KIND}


def re_find_transport_second(known, keep) -> Dict:
    loaded = ir.load(known.build(known.N, known.W))
    states = test_states(known.N, known.W)
    delta = known.difference(known.N, known.W)
    out = [dict(difference_kept(loaded, states, delta, (), rounds), rounds=rounds)
           for rounds in (1, known.ROUNDS)]
    held = all(item["unchanged"] == item["states"] for item in out)
    return {"found": {"rounds": out}, "re_found": held, "validated_kind": KIND}


def re_find_decay_second(known, keep) -> Dict:
    values = devinputs_v3.load("dev", "state", ("dev",), SHARE_STATES, n=2, w=known.W)
    words = [list(values[i])[:known.WORDS] for i in range(SHARE_STATES)]
    pairs = [known.pair(word >> known.SHIFT) for state in words for word in state]
    pairs = [pair for pair in pairs if pair[1] < 1 << known.W]
    merged = sum(known.decay(a) == known.decay(b) for a, b in pairs)
    with_partner = sum(1 for state in words if known.has_partner(state))
    held = merged == len(pairs) > 0 and in_interval(with_partner, (known.SHARE,), SHARE_STATES)
    return {"found": {"pairs_tested": len(pairs), "merged": merged, "states": SHARE_STATES,
                      "states_with_a_partner": with_partner},
            "re_found": held, "validated_kind": KIND}


RUNS = {"s13-decay": re_find_decay, "s13-transport": re_find_transport,
        "invariants-planted": re_find_planted, "invariants-planted-second": re_find_planted,
        "s13-transport-second": re_find_transport_second, "s13-decay-second": re_find_decay_second}


def validation(known_id: str, known, keep: Optional[Callable[[str, bytes], None]]) -> Dict:
    return RUNS[known_id](known, keep)


def model_id(known_id: str) -> Optional[str]:
    return "phyco-v2" if known_id in ("s13-decay", "s13-transport") else None


def inputs(known_id: str) -> Dict:
    if known_id in ("s13-decay", "s13-transport"):
        return {"namespace": "feature-002/dev", "kind": "seed", "index_range": [0, 0],
                "fingerprint": seedsets.FINGERPRINTS["dev"]}
    return {"namespace": "dev", "kind": "state", "index_range": [0, TEST_STATES - 1],
            "sizes": "each list's own (n, w)"}
