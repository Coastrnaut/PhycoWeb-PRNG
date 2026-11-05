"""Feature 004: MILP counting of active S-boxes (research R12; FR-038), with scipy's HiGHS at R12's fixed settings.

A layer is a state of bits, S-boxes that each take some of its bits, and a bit permutation: a round is the S-boxes and then the
permutation. `spn` makes a layer in the manner of PRESENT, and `columns` a layer of words of w bits, one S-box per bit position of
the group of words, each word rotated by its own amount.

The model holds a binary for each bit of the difference, or the mask, before each round and after the last, and one for each
S-box of each round, active where its input is not 0. An S-box's input and output together take only the patterns of its
difference table, or its linear table; the rest are cut away by whole cubes, each cube one inequality, a greedy cover
of the forbidden patterns by the largest cubes that hold none of the allowed ones. A trail starts from a non-zero input.

The count over r rounds is a whole number, never read from a float (R12). A run minimises it, and its solution, rounded to whole
numbers, is checked S-box by S-box against the table, which gives the count k and a trail that holds it. The best solution found
is no bound: that is the second run's, limited to k - 1 on the count, whose status must be infeasible, or else k must be the sum of
the counts of two shorter spans of rounds. The two runs are one search instance of R7, within its 8 h, and a run stopped at its
time limit gives no count. The solver's dual bound stands in the record beside the count, unread, since HiGHS reports it off by
about 10^-13 either way, and differently per platform. `minima` counts each r in turn, and each count bounds every span of r
consecutive rounds of the longer counts that follow (Matsui's lemma), since those rounds are themselves a trail of r rounds: a span
holds at least that count, which holds no trail back and cuts the solver's work by a large factor.

Every record states that its status rests on HiGHS's built-in tolerances. Analysis code: the model never imports it. This tool
makes no security claim.
"""
import importlib.util
import sys
import time
from functools import lru_cache
from pathlib import Path
from typing import Callable, Dict, FrozenSet, List, NamedTuple, Optional, Sequence, Tuple

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_matrix, csr_matrix, vstack

ROOT = Path(__file__).resolve().parents[4]
for place in (str(ROOT / "research/004"), str(ROOT)):
    if place not in sys.path:
        sys.path.insert(0, place)

from protocol.evidence import ToolFailure  # noqa: E402

SETTINGS = {"mip_rel_gap": 0, "time_limit": 8 * 3600}
MOST_SBOX_BITS = 5
OPTIMAL, LIMIT, INFEASIBLE = 0, 1, 2
HEAVY = ("present-5r",)
PROBE_ROUNDS = 4
LAST_ROUND_RATIO = 64.0
KINDS = ("differential", "linear")
LIMITATION = "its status rests on the built-in feasibility and integrality tolerances of HiGHS in scipy 1.15.3"
KIND = {"widths": [8, 16, 32], "operations": "bijective S-boxes of up to 5 bits under a bit permutation or under a rotation of each word",
        "model": "MILP on bit-level differences and masks, with cuts from the S-box's two tables",
        "limitations": [LIMITATION],
        "uses": [{"use": "4-bit S-boxes under a bit permutation, differences", "covered_by": ["present-5r"]},
                 {"use": "4-bit S-boxes under a bit permutation, masks", "covered_by": ["present-linear"]},
                 {"use": "a Boolean candidate's layer at w = 8, at w = 16 and at w = 32", "covered_by": ["rotation-layer"]}]}


class Layer(NamedTuple):
    bits: int
    boxes: Tuple[Tuple[int, ...], ...]
    sbox: Tuple[int, ...]
    permutation: Tuple[int, ...]


class Model(NamedTuple):
    matrix: object
    low: List[float]
    high: List[float]
    cost: np.ndarray
    columns: int


def sbox_bits(sbox: Sequence[int]) -> int:
    size = len(sbox)
    bits = size.bit_length() - 1
    if not 1 <= bits <= MOST_SBOX_BITS or size != 1 << bits or sorted(sbox) != list(range(size)):
        raise ToolFailure(f"an S-box is a bijection of 1 to {MOST_SBOX_BITS} bits: not {tuple(sbox)[:8]}")
    return bits


def check(layer: Layer) -> Layer:
    """A layer whose S-boxes take each bit at most once, of the S-box's size, under a true permutation."""
    bits = sbox_bits(layer.sbox)
    taken = [bit for box in layer.boxes for bit in box]
    if any(len(box) != bits for box in layer.boxes) or len(set(taken)) != len(taken) or \
            not all(0 <= bit < layer.bits for bit in taken):
        raise ToolFailure("each S-box takes its own bits of the state")
    if sorted(layer.permutation) != list(range(layer.bits)):
        raise ToolFailure("a layer's linear part here is a bit permutation")
    return layer


def spn(sbox: Sequence[int], boxes: int, permutation: Sequence[int]) -> Layer:
    """S-box j takes the j-th group of bits, lowest first."""
    bits = sbox_bits(sbox)
    return check(Layer(boxes * bits, tuple(tuple(bits * j + i for i in range(bits)) for j in range(boxes)), tuple(sbox),
                       tuple(permutation)))


def columns(sbox: Sequence[int], words: int, w: int, amounts: Sequence[int]) -> Layer:
    """Words of w bits, word j holding bits jw to jw + w - 1; S-box i takes bit i of each word; word j rotates by amounts[j]."""
    if len(amounts) != words or not all(0 <= amount < w for amount in amounts):
        raise ToolFailure(f"one amount below {w} per word: not {tuple(amounts)}")
    permutation = [0] * (words * w)
    for j in range(words):
        for i in range(w):
            permutation[j * w + i] = j * w + (i + amounts[j]) % w
    return check(Layer(words * w, tuple(tuple(j * w + i for j in range(words)) for i in range(w)), tuple(sbox), tuple(permutation)))


def parity(value: int) -> int:
    return bin(value).count("1") & 1


@lru_cache(maxsize=None)
def patterns(sbox: Tuple[int, ...], kind: str) -> FrozenSet[int]:
    """The allowed (input, output) of an S-box, input in the low bits: differences, or masks of a non-zero correlation."""
    size = len(sbox)
    bits = size.bit_length() - 1
    if kind == "differential":
        return frozenset(a | ((sbox[x] ^ sbox[x ^ a]) << bits) for a in range(size) for x in range(size))
    if kind == "linear":
        return frozenset(a | (b << bits) for a in range(size) for b in range(size)
                         if sum(1 - 2 * (parity(a & x) ^ parity(b & sbox[x])) for x in range(size)) != 0)
    raise ToolFailure(f"a kind of trail is one of {KINDS}: not {kind}")


@lru_cache(maxsize=None)
def cuts(sbox: Tuple[int, ...], kind: str) -> Tuple[Tuple[int, int], ...]:
    """Cubes (mask, value), each the points p with p & mask == value, that cover every forbidden pattern and hold no allowed one:
    the largest such cubes, chosen greedily."""
    allowed = np.array(sorted(patterns(sbox, kind)))
    width = 2 * (len(sbox).bit_length() - 1)
    empty = []
    for mask in range(1 << width):
        value = mask
        while True:
            if not ((allowed & mask) == value).any():
                empty.append((mask, value))
            if value == 0:
                break
            value = (value - 1) & mask
    largest = [(m, v) for m, v in empty if not any(m2 != m and (m2 & m) == m2 and (v & m2) == v2 for m2, v2 in empty)]
    left = set(range(1 << width)) - set(allowed.tolist())
    chosen = []
    while left:
        best = max(largest, key=lambda cube: sum(1 for point in left if point & cube[0] == cube[1]))
        chosen.append(best)
        left -= {point for point in left if point & best[0] == best[1]}
    return tuple(chosen)


def build(layer: Layer, kind: str, rounds: int, floors: Dict[int, int]) -> Model:
    """The model of `rounds` rounds, `floors` holding the count of each shorter span."""
    check(layer)
    bits, boxes = layer.bits, len(layer.boxes)
    stride = bits + boxes
    columns_of = rounds * stride + bits
    rows: List[int] = []
    cols: List[int] = []
    vals: List[float] = []
    low: List[float] = []
    high: List[float] = []

    def add(terms: Sequence[Tuple[int, int]], lowest: float, highest: float = np.inf) -> None:
        for column, value in terms:
            rows.append(len(low))
            cols.append(column)
            vals.append(value)
        low.append(lowest)
        high.append(highest)

    def state(r: int, bit: int) -> int:
        return r * stride + bit

    def active(r: int, box: int) -> int:
        return r * stride + bits + box

    cubes = cuts(layer.sbox, kind)
    for r in range(rounds):
        for index, box in enumerate(layer.boxes):
            ins = [state(r, bit) for bit in box]
            outs = [state(r + 1, layer.permutation[bit]) for bit in box]
            for x in ins:
                add([(active(r, index), 1), (x, -1)], 0)
            add([(x, 1) for x in ins] + [(active(r, index), -1)], 0)
            names = ins + outs
            for mask, value in cubes:
                terms, ones = [], 0
                for place, name in enumerate(names):
                    if mask >> place & 1:
                        if value >> place & 1:
                            terms.append((name, -1))
                            ones += 1
                        else:
                            terms.append((name, 1))
                add(terms, 1 - ones)
    add([(state(0, bit), 1) for bit in range(bits)], 1)
    for span, count in sorted(floors.items()):
        for start in range(rounds - span + 1):
            add([(active(r, box), 1) for r in range(start, start + span) for box in range(boxes)], count)
    cost = np.zeros(columns_of)
    for r in range(rounds):
        for box in range(boxes):
            cost[active(r, box)] = 1
    matrix = coo_matrix((vals, (rows, cols)), shape=(len(low), columns_of)).tocsr()
    return Model(matrix, low, high, cost, columns_of)


def solve(model: Model, seconds: float, limit: Optional[int] = None):
    """One run at R12's settings, `seconds` being what is left of the search instance's time limit. It minimises the count, or, with a
    `limit` on the count, it looks for any solution."""
    matrix, low, high, cost = model.matrix, model.low, model.high, model.cost
    if limit is not None:
        matrix = vstack([matrix, csr_matrix(model.cost)]).tocsr()
        low, high, cost = low + [-np.inf], high + [limit], np.zeros(model.columns)
    return milp(cost, constraints=LinearConstraint(matrix, low, high), integrality=np.ones(model.columns), bounds=Bounds(0, 1),
                options=dict(SETTINGS, time_limit=seconds))


def trail_of(layer: Layer, rounds: int, point: np.ndarray) -> Tuple[int, ...]:
    """The state before each round and after the last, each bit of a solution rounded to a whole number."""
    stride = layer.bits + len(layer.boxes)
    whole = np.rint(point).astype(np.int64)
    return tuple(sum(int(whole[r * stride + bit]) << bit for bit in range(layer.bits)) for r in range(rounds + 1))


def counted(layer: Layer, kind: str, trail: Sequence[int]) -> int:
    """The active S-boxes of a stated trail, in whole numbers, each S-box of each round checked against the table its model was
    built from. A trail that does not hold is a tool failure."""
    if trail[0] == 0:
        raise ToolFailure("a trail starts from a non-zero input")
    allowed = patterns(layer.sbox, kind)
    bits = sbox_bits(layer.sbox)
    total = 0
    for before, after in zip(trail, trail[1:]):
        middle = before_permutation(layer, after)
        for box in layer.boxes:
            given, taken = box_values(layer, before, box), box_values(layer, middle, box)
            if given | (taken << bits) not in allowed:
                raise ToolFailure(f"the table refuses {given} to {taken}")
            total += given != 0
    return total


def largest_sum(rounds: int, floors: Dict[int, int]) -> Optional[Tuple[int, int, int]]:
    """The largest sum of the counts of two shorter spans that together make `rounds`, with the two spans."""
    sums = [(floors[s] + floors[rounds - s], s, rounds - s) for s in range(1, rounds // 2 + 1)
            if s in floors and rounds - s in floors]
    return max(sums) if sums else None


def minimum(layer: Layer, kind: str, rounds: int, floors: Dict[int, int]) -> Dict:
    """The count over `rounds` rounds, with each status and the trail that holds it (R12). A run stopped at its time limit gives no
    count, and a tool failure's record says `inconclusive` (R7, R12)."""
    model = build(layer, kind, rounds, floors)
    started = time.monotonic()
    result = solve(model, SETTINGS["time_limit"])
    if result.status != OPTIMAL or result.x is None:
        raise ToolFailure(f"{kind}, {rounds} rounds: status {result.status}, {result.message}: no count")
    trail = trail_of(layer, rounds, result.x)
    count = counted(layer, kind, trail)
    row = {"status": int(result.status), "message": str(result.message),
           "dual_bound": None if result.mip_dual_bound is None else float(result.mip_dual_bound),
           "count": count, "trail": [format(state, "x") for state in trail]}
    shorter = largest_sum(rounds, floors)
    if shorter is not None and count < shorter[0]:
        raise ToolFailure(f"{kind}, {rounds} rounds: a solution of {count} lies below the sum {shorter[0]} of two shorter counts")
    if shorter is not None and count == shorter[0]:
        return dict(row, sum_of=list(shorter[1:]))
    left = SETTINGS["time_limit"] - (time.monotonic() - started)
    if left <= 0:
        raise ToolFailure(f"{kind}, {rounds} rounds: no time left of the search instance: no count")
    below = solve(model, left, count - 1)
    if below.status != INFEASIBLE:
        raise ToolFailure(f"{kind}, {rounds} rounds: status {below.status} with a limit of {count - 1}, {below.message}: no count")
    return dict(row, below={"limit": count - 1, "status": int(below.status), "message": str(below.message)})


def minima(layer: Layer, kind: str, rounds: int) -> Dict[int, Dict]:
    """Each r from 1 to `rounds`, each count bounding every span of its size in the counts after it."""
    out: Dict[int, Dict] = {}
    floors: Dict[int, int] = {}
    for r in range(1, rounds + 1):
        out[r] = minimum(layer, kind, r, floors)
        floors[r] = out[r]["count"]
    return out


def box_values(layer: Layer, state: int, box: Tuple[int, ...]) -> int:
    return sum(((state >> bit) & 1) << place for place, bit in enumerate(box))


def before_permutation(layer: Layer, state: int) -> int:
    return sum(((state >> layer.permutation[bit]) & 1) << bit for bit in range(layer.bits))


def admitted(layer: Layer, kind: str, trail: Sequence[int]) -> Optional[Tuple[int, ...]]:
    """The active S-boxes of each round of a stated trail, the state before each round and after the last, if every constraint of
    the model holds at that point, and None if any does not."""
    rounds = len(trail) - 1
    model = build(layer, kind, rounds, {})
    bits, boxes = layer.bits, len(layer.boxes)
    stride = bits + boxes
    point = np.zeros(model.columns)
    counts = []
    for r, state in enumerate(trail):
        for bit in range(bits):
            point[r * stride + bit] = (state >> bit) & 1
        if r < rounds:
            active = [box_values(layer, state, box) != 0 for box in layer.boxes]
            for index, flag in enumerate(active):
                point[r * stride + bits + index] = flag
            counts.append(sum(active))
    held = model.matrix @ point
    if (held < np.array(model.low)).any() or (held > np.array(model.high)).any():
        return None
    return tuple(counts)


def weight_of(layer: Layer, trail: Sequence[int]) -> int:
    """The weight of a stated differential trail, by the S-box's difference table: an entry of 2^e of 2^b inputs weighs b - e."""
    bits = sbox_bits(layer.sbox)
    size = 1 << bits
    total = 0
    for before, after in zip(trail, trail[1:]):
        middle = before_permutation(layer, after)
        for box in layer.boxes:
            a, b = box_values(layer, before, box), box_values(layer, middle, box)
            if a == 0 and b == 0:
                continue
            entry = sum(1 for x in range(size) if layer.sbox[x] ^ layer.sbox[x ^ a] == b)
            if entry == 0:
                raise ToolFailure(f"the table refuses {a} to {b}")
            total += bits - (entry.bit_length() - 1)
    return total


def layer_of(known, w: Optional[int] = None) -> Layer:
    if hasattr(known, "WIDTHS"):
        return columns(known.SBOX, known.WORDS, w, known.AMOUNTS)
    return spn(known.SBOX, len(known.PERMUTATION) // 4, known.PERMUTATION)


def counts_of(found: Dict[int, Dict]) -> Dict[int, int]:
    return {r: row["count"] for r, row in found.items()}


def as_rows(found: Dict[int, Dict]) -> Dict[str, Dict]:
    return {str(r): row for r, row in found.items()}


def re_find_minimum(known, keep) -> Dict:
    found = minima(layer_of(known), "differential", known.ROUNDS)
    return {"found": {"rounds": as_rows(found)}, "re_found": found[known.ROUNDS]["count"] == known.MINIMUM, "validated_kind": KIND}


def re_find_characteristics(known, keep) -> Dict:
    layer = layer_of(known)
    iterative = admitted(layer, "differential", known.ITERATIVE)
    other = admitted(layer, "differential", known.OTHER)
    weight = weight_of(layer, known.OTHER) if other is not None else None
    held = iterative == tuple(known.ITERATIVE_ACTIVE) and other == tuple(known.OTHER_ACTIVE) and weight == known.OTHER_WEIGHT
    found = {"iterative_active": iterative, "other_active": other, "other_weight": weight}
    return {"found": found, "re_found": held, "validated_kind": KIND}


def re_find_linear(known, keep) -> Dict:
    found = minima(layer_of(known), "linear", known.ROUNDS)
    wanted = {r: known.MINIMA[r] for r in range(1, known.ROUNDS + 1)}
    return {"found": {"rounds": as_rows(found)}, "re_found": counts_of(found) == wanted, "validated_kind": KIND}


def re_find_spn(known, keep) -> Dict:
    layer = spn(known.SBOX, len(known.BOXES), known.PERMUTATION)
    found: Dict = {}
    held = True
    for kind, stated in (("differential", known.DIFFERENTIAL), ("linear", known.LINEAR)):
        rows = minima(layer, kind, known.ROUNDS)
        found[kind] = as_rows(rows)
        held = held and counts_of(rows) == {r: stated[r] for r in range(1, known.ROUNDS + 1)}
    return {"found": found, "re_found": held, "validated_kind": KIND}


def re_find_layers(known, keep) -> Dict:
    found: Dict = {}
    held = True
    for w in known.WIDTHS:
        for kind, stated in (("differential", known.DIFFERENTIAL), ("linear", known.LINEAR)):
            rows = minima(layer_of(known, w), kind, known.ROUNDS)
            found[f"w{w} {kind}"] = as_rows(rows)
            held = held and counts_of(rows) == {r: stated[r] for r in range(1, known.ROUNDS + 1)}
    return {"found": found, "re_found": held, "validated_kind": KIND}


RUNS: Dict[str, Callable] = {"present-5r": re_find_minimum, "present-5r-second": re_find_characteristics,
                             "present-linear": re_find_linear, "present-linear-second": re_find_spn,
                             "rotation-layer": re_find_layers, "rotation-layer-second": re_find_layers}


def validation(known_id: str, known, keep: Optional[Callable[[str, bytes], None]]) -> Dict:
    return RUNS[known_id](known, keep)


def present():
    """The known result `present-5r`, for the projection, which is given no module."""
    spec = importlib.util.spec_from_file_location("present_5r", ROOT / "research/004/validation/present-5r.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def projection(known_id: str) -> Tuple[float, Dict]:
    """The counts of PRESENT's differences up to 4 rounds, timed, and the fifth by the ratio LAST_ROUND_RATIO, from the two runs of its
    count as this form's runs took them on the way to option A of R12's floor: 616 s to minimise and 506 s limited to 9, against 17.7 s
    up to 4 rounds."""
    if known_id not in HEAVY:
        raise ToolFailure(f"{known_id} is no heavy run")
    started = time.monotonic()
    minima(layer_of(present()), "differential", PROBE_ROUNDS)
    seconds = time.monotonic() - started
    return seconds * LAST_ROUND_RATIO / 3600.0, {"seconds_up_to_the_probe": seconds, "ratio": LAST_ROUND_RATIO}
