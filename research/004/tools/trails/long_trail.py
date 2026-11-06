"""Feature 004: MILP counting of active boxes through long trails (research R12; FR-038), with scipy's HiGHS at R12's fixed settings.

A step is a box on every branch, and a layer between two steps holds what the box is not. Each branch of the next step is a copy of
one branch, with at most one output of a linear map added to it. The map is known only by `relation`, the pairs of patterns of
active branches that it may take and give. `feistel` makes the layer of SPARKLE's section 2.1.2, for differences and for masks, and
`copies` a layer that adds nothing.

A truncated trail says which branches are active at each step and which outputs of the map are active after it. A chain, a long trail
in the paper's word, is a run of active branches, one per step, each a copy of the one before with nothing active added: where an
active output reaches a branch, the chain ends and the branch, if still active, starts another. A chain of t steps costs the box's
bound of t steps, and a chain longer than the bounds costs the largest sum over the ways of cutting it: `chain_costs`. A trail costs
the sum over its chains, and its bound is the least over every trail allowed. Bounds are whole numbers, in any unit: the bound of a
box's weights, or 1 for one step to count active boxes alone.

The model holds a binary for each branch at each step, one for each output after each step, and one for each branch at each place of
its chain, of which an active branch takes exactly one. A chain's cost is added place by place. A branch that starts a chain could
take a late place, which never gains, since the largest cutting gives costs where c(s + t) - c(s) is at least c(t). So the least
objective is the least over the trails, and the sum over a span of steps is at least the cost of that span's own trail, which is what
lets each count bound every span of its size in the longer counts (Matsui's lemma).

The objective takes only whole values, so a count is never read from a float (R12). A run minimises it, and its solution, rounded to
whole numbers, is checked against the layer's tables and walked chain by chain, which gives the count k and the trail that holds it. The
best solution found is no bound: that is the second run's, limited to k - 1 on the objective, whose status must be infeasible, or
else k must be the sum of the counts of two shorter spans of steps. The two runs are one search instance of R7, within its 8 h, and a
run stopped at its time limit gives no count. The solver's dual bound stands in the record beside the count, unread.

Every record states that its status rests on HiGHS's built-in tolerances. Analysis code: the model never imports it. This tool makes no
security claim.
"""
import importlib.util
import itertools
import sys
import time
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
OPTIMAL, LIMIT, INFEASIBLE = 0, 1, 2
KINDS = ("differential", "linear")
ONE_TO_ONE = frozenset({((0,), (0,)), ((1,), (1,))})
LIMITATION = "its status rests on the built-in feasibility and integrality tolerances of HiGHS in scipy 1.15.3"
KIND = {"widths": [8, 16, 32], "operations": "boxes of 2w bits between layers of Feistel type, each next branch a copy of one branch with at "
                                              "most one output of a linear map added, the map known by the patterns of branches it may give",
        "model": "MILP on truncated trails and on the place of each branch in its chain, from the box's bounds as whole numbers",
        "limitations": [LIMITATION],
        "uses": [{"use": "a Feistel layer with a map of branches, boxes on 32-bit words, differences", "covered_by": ["sparkle-box"]},
                 {"use": "a Feistel layer with a map of branches, boxes on 32-bit words, masks", "covered_by": ["sparkle-box-second"]},
                 {"use": "a Feistel layer, differences and masks, at the D4 width, w = 8 and w = 16", "covered_by": ["long-trail-feistel"]}]}

Pattern = Tuple[int, ...]


class Layer(NamedTuple):
    branches: int
    fed: Tuple[int, ...]
    relation: FrozenSet[Tuple[Pattern, Pattern]]
    source: Tuple[int, ...]
    added: Tuple[Optional[int], ...]


class Local(NamedTuple):
    """A layer whose outputs each have a small map of their own, so that a torus of any size has a model. A map names its inputs as
    (ahead, branch), ahead being 1 for the branch as the next step has it, which a layer of two phases needs, and `relation` holds the
    pairs (pattern of its inputs, value of its output) that it may take and give."""
    branches: int
    source: Tuple[int, ...]
    added: Tuple[Optional[int], ...]
    maps: Tuple[Tuple[Tuple[Tuple[int, int], ...], FrozenSet[Tuple[Pattern, int]]], ...]


class Model(NamedTuple):
    matrix: object
    low: List[float]
    high: List[float]
    cost: np.ndarray
    columns: int
    active: List[List[int]]
    outputs: List[List[int]]


def outputs_of(layer) -> int:
    if isinstance(layer, Local):
        return len(layer.maps)
    return len(next(iter(layer.relation))[1])


def xor_relation(inputs: int) -> FrozenSet[Tuple[Pattern, int]]:
    """The output of a sum of bijections of each input: inactive where no input is active, active where one is, and free where two or
    more may cancel."""
    out = set()
    for pattern in itertools.product((0, 1), repeat=inputs):
        active = sum(pattern)
        out.update((pattern, value) for value in ((0,) if active == 0 else (1,) if active == 1 else (0, 1)))
    return frozenset(out)


def check_local(layer: Local) -> Local:
    """Every branch goes on into exactly one, each output reaches at most one branch, and a map that reads ahead reads a branch whose own
    output comes before it, so that the layer's phases have an order."""
    if sorted(layer.source) != list(range(layer.branches)) or len(layer.added) != layer.branches:
        raise ToolFailure("each branch goes on into exactly one branch of the next step, with one added output named")
    named = [item for item in layer.added if item is not None]
    if len(set(named)) != len(named) or not all(0 <= item < len(layer.maps) for item in named):
        raise ToolFailure("an output reaches at most one branch, and only outputs that exist are named")
    for number, (inputs, relation) in enumerate(layer.maps):
        for ahead, branch in inputs:
            if not 0 <= branch < layer.branches or ahead not in (0, 1):
                raise ToolFailure(f"map {number} reads what no step holds: {(ahead, branch)}")
            if ahead and (layer.added[branch] is None or layer.added[branch] >= number):
                raise ToolFailure(f"map {number} reads ahead a branch that no earlier map reaches: {branch}")
        if any(len(given) != len(inputs) or value not in (0, 1) for given, value in relation):
            raise ToolFailure(f"map {number}: a pattern holds one place per input and one output")
        if ((0,) * len(inputs), 0) not in relation:
            raise ToolFailure(f"map {number}: no input gives no output")
    return layer


def check(layer):
    """A layer in which every branch goes on into exactly one, each output named exists, and no input gives no output but nothing."""
    if isinstance(layer, Local):
        return check_local(layer)
    if sorted(layer.source) != list(range(layer.branches)):
        raise ToolFailure("each branch goes on into exactly one branch of the next step")
    if len(layer.added) != layer.branches or not all(0 <= bit < layer.branches for bit in layer.fed):
        raise ToolFailure("a layer names one added output per branch, and only its own branches go into the map")
    if not layer.relation:
        raise ToolFailure("a map takes at least nothing to nothing")
    width = outputs_of(layer)
    if any(len(given) != len(layer.fed) or len(taken) != width for given, taken in layer.relation):
        raise ToolFailure("a pattern holds one place per input and one per output of the map")
    if not all(item is None or 0 <= item < width for item in layer.added):
        raise ToolFailure(f"a layer adds outputs below {width}")
    if ((0,) * len(layer.fed), (0,) * width) not in layer.relation:
        raise ToolFailure("no input gives no output")
    return layer


def feistel(h: int, kind: str, relation: FrozenSet[Tuple[Pattern, Pattern]]) -> Layer:
    """SPARKLE's layer on h left and h right branches, indices mod h. For differences, new left j = right (j + 1) xor M(left) (j + 1) and new
    right j = left j. For masks, by the transpose of the inverse, new left j = right (j + 1) and new right j = left j xor M(right) j."""
    if kind not in KINDS:
        raise ToolFailure(f"a kind of trail is one of {KINDS}: not {kind}")
    source = tuple(h + (j + 1) % h for j in range(h)) + tuple(range(h))
    if kind == "differential":
        return check(Layer(2 * h, tuple(range(h)), frozenset(relation), source,
                           tuple((j + 1) % h for j in range(h)) + (None,) * h))
    return check(Layer(2 * h, tuple(range(h, 2 * h)), frozenset(relation), source, (None,) * h + tuple(range(h))))


def copies(branches: int) -> Layer:
    """Branches that only move, each to the next, with nothing added: every active branch stays one chain."""
    return check(Layer(branches, (), frozenset({((), ())}), tuple((j - 1) % branches for j in range(branches)), (None,) * branches))


def chain_costs(box: Sequence[int], longest: int) -> Tuple[int, ...]:
    """The cost of a chain of each length up to `longest`, index 0 unused: the largest sum of the box's bounds over the ways of cutting it."""
    if not box or not all(type(value) is int and value >= 0 for value in box):
        raise ToolFailure(f"a box's bounds are whole numbers, for one step and up: not {tuple(box)}")
    costs = [0] * (longest + 1)
    for t in range(1, longest + 1):
        costs[t] = max(box[k - 1] + costs[t - k] for k in range(1, min(t, len(box)) + 1))
    return tuple(costs)


def cuts_of(layer, active: List[List[int]], outputs: List[List[int]], r: int) -> List[Tuple[List[int], FrozenSet[Pattern]]]:
    """The binaries of each map after step r, with the patterns that they may hold."""
    if isinstance(layer, Local):
        return [([active[r + ahead][branch] for ahead, branch in inputs] + [outputs[r][number]],
                 frozenset(given + (value,) for given, value in relation))
                for number, (inputs, relation) in enumerate(layer.maps)]
    return [([active[r][b] for b in layer.fed] + outputs[r], frozenset(given + taken for given, taken in layer.relation))]


def build(layer, costs: Sequence[int], rounds: int, floors: Dict[int, int]) -> Model:
    """The model of `rounds` steps, `floors` holding the count of each shorter span."""
    check(layer)
    width = outputs_of(layer)
    count = 0
    rows: List[int] = []
    cols: List[int] = []
    vals: List[float] = []
    low: List[float] = []
    high: List[float] = []

    def column() -> int:
        nonlocal count
        count += 1
        return count - 1

    def add(terms: Sequence[Tuple[int, int]], lowest: float, highest: float = np.inf) -> None:
        for name, value in terms:
            rows.append(len(low))
            cols.append(name)
            vals.append(value)
        low.append(lowest)
        high.append(highest)

    active = [[column() for _ in range(layer.branches)] for _ in range(rounds)]
    outputs = [[column() for _ in range(width)] for _ in range(rounds - 1)]
    places = [[{t: column() for t in range(1, r + 2)} for _ in range(layer.branches)] for r in range(rounds)]
    for r in range(rounds):
        add([(active[r][b], 1) for b in range(layer.branches)], 1)
        for b in range(layer.branches):
            add([(name, 1) for name in places[r][b].values()] + [(active[r][b], -1)], 0, 0)
    for r in range(rounds - 1):
        for names, allowed in cuts_of(layer, active, outputs, r):
            for pair in itertools.product((0, 1), repeat=len(names)):
                if pair not in allowed:
                    add([(name, -1 if bit else 1) for name, bit in zip(names, pair)], 1 - sum(pair))
        for j in range(layer.branches):
            came, reached, added = active[r][layer.source[j]], active[r + 1][j], layer.added[j]
            before, after = places[r][layer.source[j]], places[r + 1][j]
            if added is None:
                add([(reached, 1), (came, -1)], 0, 0)
                for t, name in before.items():
                    add([(after[t + 1], 1), (name, -1)], 0)
                continue
            mixed = outputs[r][added]
            add([(came, 1), (mixed, 1), (reached, -1)], 0)
            add([(mixed, 1), (reached, 1), (came, -1)], 0)
            add([(reached, 1), (came, 1), (mixed, -1)], 0)
            for t, name in before.items():
                add([(after[t + 1], 1), (name, -1), (mixed, 1)], 0)
    cost = np.zeros(count)
    spent: List[Dict[int, int]] = [{} for _ in range(rounds)]
    for r in range(rounds):
        for b in range(layer.branches):
            for t, name in places[r][b].items():
                if costs[t] != costs[t - 1]:
                    spent[r][name] = costs[t] - costs[t - 1]
                    cost[name] = costs[t] - costs[t - 1]
    for span, value in sorted(floors.items()):
        for start in range(rounds - span + 1):
            terms = [item for r in range(start, start + span) for item in spent[r].items()]
            if terms:
                add(terms, value)
    matrix = coo_matrix((vals, (rows, cols)), shape=(len(low), count)).tocsr()
    return Model(matrix, low, high, cost, count, active, outputs)


def solve(model: Model, seconds: float, limit: Optional[int] = None):
    """One run at R12's settings, `seconds` being what is left of the search instance's time limit. It minimises the objective, or, with a
    `limit` on it, it looks for any solution."""
    matrix, low, high, cost = model.matrix, model.low, model.high, model.cost
    if limit is not None:
        matrix = vstack([matrix, csr_matrix(model.cost)]).tocsr()
        low, high, cost = low + [-np.inf], high + [limit], np.zeros(model.columns)
    return milp(cost, constraints=LinearConstraint(matrix, low, high), integrality=np.ones(model.columns), bounds=Bounds(0, 1),
                options=dict(SETTINGS, time_limit=seconds))


def trail_of(model: Model, point: np.ndarray) -> Tuple[Tuple[Pattern, ...], Tuple[Pattern, ...]]:
    """The pattern of branches at each step and of outputs after each step, each binary of a solution rounded to a whole number."""
    whole = np.rint(point).astype(np.int64)
    return (tuple(tuple(int(whole[name]) for name in row) for row in model.active),
            tuple(tuple(int(whole[name]) for name in row) for row in model.outputs))


def map_holds(layer, before: Pattern, after: Pattern, mixed: Pattern) -> bool:
    if isinstance(layer, Local):
        return all((tuple((after if ahead else before)[branch] for ahead, branch in inputs), mixed[number]) in relation
                   for number, (inputs, relation) in enumerate(layer.maps))
    return (tuple(before[b] for b in layer.fed), mixed) in layer.relation


def held(layer, steps: Sequence[Pattern], outputs: Sequence[Pattern]) -> None:
    """A stated truncated trail, in whole numbers, against the tables of the layer, or a tool failure."""
    if len(outputs) != len(steps) - 1:
        raise ToolFailure("a trail states the map's outputs after each step but the last")
    for r, step in enumerate(steps):
        if not any(step):
            raise ToolFailure(f"step {r} holds no active branch")
    for r, (before, after, mixed) in enumerate(zip(steps, steps[1:], outputs)):
        if not map_holds(layer, before, after, mixed):
            raise ToolFailure(f"the map may not give {mixed} after step {r}")
        for j in range(layer.branches):
            came, reached = before[layer.source[j]], after[j]
            added = 0 if layer.added[j] is None else mixed[layer.added[j]]
            if came + added + reached == 1:
                raise ToolFailure(f"branch {j} of step {r + 1} cannot be {reached} from {came} with {added} added")


def chain_lengths(layer, steps: Sequence[Pattern], outputs: Sequence[Pattern]) -> Tuple[int, ...]:
    """The length of each chain of a stated truncated trail, sorted."""
    alive = {b: 1 for b in range(layer.branches) if steps[0][b]}
    ended: List[int] = []
    for after, mixed in zip(steps[1:], outputs):
        following: Dict[int, int] = {}
        for j in range(layer.branches):
            if not after[j]:
                continue
            added = layer.added[j]
            unmixed = added is None or not mixed[added]
            following[j] = alive.pop(layer.source[j]) + 1 if unmixed and layer.source[j] in alive else 1
        ended.extend(alive.values())
        alive = following
    return tuple(sorted(ended + list(alive.values())))


def counted(layer, costs: Sequence[int], steps: Sequence[Pattern], outputs: Sequence[Pattern]) -> int:
    """The cost of a stated truncated trail in whole numbers, over its chains, once it has been checked against the layer's tables."""
    held(layer, steps, outputs)
    return sum(costs[length] for length in chain_lengths(layer, steps, outputs))


def largest_sum(rounds: int, floors: Dict[int, int]) -> Optional[Tuple[int, int, int]]:
    """The largest sum of the counts of two shorter spans that together make `rounds`, with the two spans."""
    sums = [(floors[s] + floors[rounds - s], s, rounds - s) for s in range(1, rounds // 2 + 1)
            if s in floors and rounds - s in floors]
    return max(sums) if sums else None


def text_of(patterns: Sequence[Pattern]) -> List[str]:
    return ["".join(str(bit) for bit in pattern) for pattern in patterns]


def minimum(layer, costs: Sequence[int], rounds: int, floors: Dict[int, int]) -> Dict:
    """The count over `rounds` steps, with each status and the trail that holds it (R12). A run stopped at its time limit gives no count,
    and a tool failure's record says `inconclusive` (R7, R12)."""
    model = build(layer, costs, rounds, floors)
    started = time.monotonic()
    result = solve(model, SETTINGS["time_limit"])
    if result.status != OPTIMAL or result.x is None:
        raise ToolFailure(f"{rounds} steps: status {result.status}, {result.message}: no count")
    steps, outputs = trail_of(model, result.x)
    count = counted(layer, costs, steps, outputs)
    row = {"status": int(result.status), "message": str(result.message),
           "dual_bound": None if result.mip_dual_bound is None else float(result.mip_dual_bound),
           "count": count, "steps": text_of(steps), "outputs": text_of(outputs)}
    shorter = largest_sum(rounds, floors)
    if shorter is not None and count < shorter[0]:
        raise ToolFailure(f"{rounds} steps: a solution of {count} lies below the sum {shorter[0]} of two shorter counts")
    if shorter is not None and count == shorter[0]:
        return dict(row, sum_of=list(shorter[1:]))
    left = SETTINGS["time_limit"] - (time.monotonic() - started)
    if left <= 0:
        raise ToolFailure(f"{rounds} steps: no time left of the search instance: no count")
    below = solve(model, left, count - 1)
    if below.status != INFEASIBLE:
        raise ToolFailure(f"{rounds} steps: status {below.status} with a limit of {count - 1}, {below.message}: no count")
    return dict(row, below={"limit": count - 1, "status": int(below.status), "message": str(below.message)})


def minima(layer, box: Sequence[int], rounds: int) -> Dict[int, Dict]:
    """Each r from 1 to `rounds`, each count bounding every span of its size in the counts after it."""
    costs = chain_costs(box, rounds)
    out: Dict[int, Dict] = {}
    floors: Dict[int, int] = {}
    for r in range(1, rounds + 1):
        out[r] = minimum(layer, costs, r, floors)
        floors[r] = out[r]["count"]
    return out


def counts_of(found: Dict[int, Dict]) -> Dict[int, int]:
    return {r: row["count"] for r, row in found.items()}


def as_rows(found: Dict[int, Dict]) -> Dict[str, Dict]:
    return {str(r): row for r, row in found.items()}


def first_known():
    """The known result `sparkle-box`, whose `relation` its second reads."""
    spec = importlib.util.spec_from_file_location("sparkle_box", ROOT / "research/004/validation/sparkle-box.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def re_find_sparkle(known, keep) -> Dict:
    relation = getattr(known, "relation", None) or first_known().relation
    found: Dict = {}
    held_all = True
    for size, h in known.HALVES.items():
        rows = minima(feistel(h, known.KIND, relation(h)), known.BOX, known.ROUNDS[size])
        found[str(size)] = as_rows(rows)
        held_all = held_all and counts_of(rows) == {r: known.BOUNDS[size][r] for r in range(1, known.ROUNDS[size] + 1)}
    return {"found": found, "re_found": held_all, "validated_kind": KIND}


def re_find_feistel(known, keep) -> Dict:
    found: Dict = {}
    held_all = True
    for w in known.WIDTHS:
        for kind, box in known.BOXES[w].items():
            rows = minima(feistel(1, kind, ONE_TO_ONE), box, known.ROUNDS)
            found[f"w{w} {kind}"] = as_rows(rows)
            held_all = held_all and counts_of(rows) == known.MINIMA[w][kind]
    return {"found": found, "re_found": held_all, "validated_kind": KIND}


def re_find_copies(known, keep) -> Dict:
    found: Dict = {}
    held_all = True
    for w in known.WIDTHS:
        for kind, box in known.BOXES[w].items():
            rows = minima(copies(known.BRANCHES), box, known.ROUNDS)
            found[f"w{w} {kind}"] = as_rows(rows)
            held_all = held_all and counts_of(rows) == known.MINIMA[w][kind]
    layer = feistel(1, known.EXAMPLE_KIND, ONE_TO_ONE)
    steps = known.EXAMPLE
    outputs = [tuple(step[b] for b in layer.fed) for step in steps[:-1]]
    held(layer, steps, outputs)
    lengths = chain_lengths(layer, steps, outputs)
    found["example"] = list(lengths)
    return {"found": found, "re_found": held_all and lengths == tuple(known.EXAMPLE_LENGTHS), "validated_kind": KIND}


RUNS: Dict[str, Callable] = {"sparkle-box": re_find_sparkle, "sparkle-box-second": re_find_sparkle, "long-trail-feistel": re_find_feistel,
                             "long-trail-feistel-second": re_find_copies}


def validation(known_id: str, known, keep: Optional[Callable[[str, bytes], None]]) -> Dict:
    return RUNS[known_id](known, keep)
