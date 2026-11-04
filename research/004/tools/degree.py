"""Feature 004: the degree derivation (research R13; data-model sections 5 and 7).

The rule's count, bottom-up over each phase's input lanes, each of degree 1: a constant has degree 0; XOR,
NOT, a rotation and a shift take the largest degree of their arguments; a bitwise function takes the
largest sum of its arguments' degrees over the monomials of its algebraic normal form, its truth table's
degree, so 2 for AND or OR of two lanes; addition and subtraction take w - 1 times the larger of their
operands' degrees; an update takes its result's degree, and a rotation update 1; a phase the largest of
its updates' degrees, a lane it does not write counting 1; a round the product of its phases'; and r rounds
the product of the rounds', capped at b - 1.

That count is the rule's, not an upper bound: the top bit of a sum of two variable words has degree w. So
an upper bound stands beside it, by the same rules with w for addition and subtraction. The inside-out
count is the largest r1 + r2 with both counts within the limit, at the cost 2^(max + 1).

The exact degree comes from a truth table, for a part of the state of at most 16 bits. It is reported
beside the count and never replaces it.

Run on its known results by scripts/validate_tool.py (`degree-small` and its second; R13). Analysis code:
the model never imports it. This tool makes no security claim.
"""
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
for place in (str(ROOT / "research/004"), str(ROOT)):
    if place not in sys.path:
        sys.path.insert(0, place)

import ir  # noqa: E402

CODE = ("research/004/ir.py",)
LIMIT = 126
MOST_LEAVES = 16
MOST_TABLE_BITS = 16
BOOLEAN = (ir.And, ir.Or, ir.Xor, ir.Not)
KIND = {"widths": [4, 8, 32],
        "operations": "XOR, AND, OR, NOT, rotations, shifts, addition and subtraction of words",
        "model": "the bottom-up count of research R13, with its bound and its inside-out count",
        "uses": [{"use": "the `degree` record at each claimable size, w = 32",
                  "covered_by": ["degree-small"]},
                 {"use": "the exact degree beside the count, at w = 4 and 8",
                  "covered_by": ["degree-small"]}]}


# ------------------------------------------------------------------------------- bitwise functions

def anf_monomials(table: np.ndarray, variables: int) -> np.ndarray:
    """The monomials of a truth table's algebraic normal form, by the Möbius transform: an index's bits
    name the variables of its monomial."""
    out = table.astype(np.uint8).copy()
    for i in range(variables):
        step = 1 << i
        rows = out.reshape(-1, 2 * step)
        rows[:, step:] ^= rows[:, :step]
    return np.nonzero(out)[0]


def table_degree(table: np.ndarray, variables: int) -> int:
    held = anf_monomials(table, variables)
    return int(np.bitwise_count(held.astype(np.uint64)).max()) if held.size else 0


def leaf_of(expr: Any, turn: Tuple[Any, ...] = ()) -> Tuple[Any, ...]:
    """A leaf's name: what it reads and what moved it, so that one bit read twice is one variable. A
    rotation's amounts add up, whichever order they stand in."""
    kind = type(expr)
    if kind is ir.Rotl:
        return leaf_of(expr.value, turn + (("rotl", expr.amount),))
    if kind in (ir.Shl, ir.Shr):
        return leaf_of(expr.value, turn + ((kind.__name__, expr.amount),))
    total = sum(amount for name, amount in turn if name == "rotl")
    rest = tuple(item for item in turn if item[0] != "rotl")
    return (kind.__name__, expr.index, total, rest)


def strip(expr: Any) -> Any:
    """Under a rotation or a shift, the expression it moves."""
    while type(expr) in (ir.Rotl, ir.Shl, ir.Shr):
        expr = expr.value
    return expr


def collect(expr: Any, turn: Tuple[Any, ...], leaves: Dict[Tuple[Any, ...], Tuple[int, int]]) -> None:
    """Every leaf of a bitwise function, a rotation or shift above a function going down to its leaves."""
    kind = type(expr)
    if kind in (ir.Rotl, ir.Shl, ir.Shr):
        name = "rotl" if kind is ir.Rotl else kind.__name__
        collect(expr.value, turn + ((name, expr.amount),), leaves)
    elif kind is ir.Not:
        collect(expr.value, turn, leaves)
    elif kind in (ir.Xor, ir.And, ir.Or):
        collect(expr.left, turn, leaves)
        collect(expr.right, turn, leaves)
    else:
        key = leaf_of(expr, turn)
        if key not in leaves:
            leaves[key] = (len(leaves), 0 if kind is ir.Constant else 1)


def evaluate(expr: Any, turn: Tuple[Any, ...], leaves: Dict, size: int) -> np.ndarray:
    """The function's truth table over its leaves, as an array of 2^k booleans."""
    kind = type(expr)
    if kind in (ir.Rotl, ir.Shl, ir.Shr):
        name = "rotl" if kind is ir.Rotl else kind.__name__
        return evaluate(expr.value, turn + ((name, expr.amount),), leaves, size)
    if kind is ir.Not:
        return ~evaluate(expr.value, turn, leaves, size)
    if kind is ir.Xor:
        return evaluate(expr.left, turn, leaves, size) ^ evaluate(expr.right, turn, leaves, size)
    if kind is ir.And:
        return evaluate(expr.left, turn, leaves, size) & evaluate(expr.right, turn, leaves, size)
    if kind is ir.Or:
        return evaluate(expr.left, turn, leaves, size) | evaluate(expr.right, turn, leaves, size)
    position = leaves[leaf_of(expr, turn)][0]
    return ((np.arange(size) >> position) & 1).astype(bool)


def is_xor_only(expr: Any) -> bool:
    kind = type(expr)
    if kind in (ir.Rotl, ir.Shl, ir.Shr, ir.Not):
        return is_xor_only(expr.value)
    if kind is ir.Xor:
        return is_xor_only(expr.left) and is_xor_only(expr.right)
    return kind not in (ir.And, ir.Or)


def expression_degree(expr: Any) -> int:
    """F's degree: the largest sum of its leaves' degrees over the monomials of its normal form, a
    constant's degree 0. A function of XORs alone needs no table, and may have many leaves."""
    leaves: Dict[Tuple[Any, ...], Tuple[int, int]] = {}
    collect(expr, (), leaves)
    if is_xor_only(expr):
        return max((degree for _, degree in leaves.values()), default=0)
    if len(leaves) > MOST_LEAVES:
        raise ValueError(f"a bitwise function of {len(leaves)} leaves")
    size = 1 << len(leaves)
    table = evaluate(expr, (), leaves, size)
    degrees = np.zeros(len(leaves), dtype=np.int64)
    for position, degree in leaves.values():
        degrees[position] = degree
    held = anf_monomials(table, len(leaves))
    best = 0
    for monomial in held:
        chosen = [p for p in range(len(leaves)) if int(monomial) >> p & 1]
        best = max(best, int(degrees[chosen].sum()))
    return best


# ------------------------------------------------------------------------------------- the count

def update_degree(update: Any, addition: int) -> int:
    """`addition` is what one addition multiplies by: w - 1 for the rule, w for its bound."""
    if type(update) is ir.Rot:
        return 1
    inner = expression_degree(update.expr)
    return max(1, inner) if update.op == "xor" else addition * max(1, inner)


def phase_degrees(program: "ir.Program", addition: int) -> List[int]:
    """Each phase: the largest of its updates' degrees, a lane it does not write counting 1."""
    return [max([1] + [update_degree(u, addition) for u in phase.updates]) for phase in program.phases]


def round_degree(program: "ir.Program", addition: int) -> int:
    out = 1
    for degree in phase_degrees(program, addition):
        out *= degree
    return out


def capped(per_round: int, rounds: int, cap: int) -> int:
    """The product of the per-round counts, capped at b - 1, which needs no search."""
    out = 1
    for _ in range(rounds):
        out = min(out * per_round, cap)
    return out


def counts(program: "ir.Program", addition: int, rounds: Sequence[int]) -> List[int]:
    cap = 2 * program.n ** 2 * program.w - 1
    per_round = round_degree(program, addition)
    return [capped(per_round, r, cap) for r in rounds]


def within(values: Sequence[int], rounds: Sequence[int], limit: int) -> List[int]:
    return [r for r, value in zip(rounds, values) if value <= limit]


def inside_out(forward: Sequence[int], backward: Sequence[int], rounds: Sequence[int],
               limit: int) -> Optional[Tuple[int, int]]:
    """The largest r1 + r2 with both counts within the limit, and the exponent of its cost; None if
    no pair is within it. Counts never fall as rounds rise, so that one pair has the largest sum."""
    best = None
    for r1, d1 in zip(rounds, forward):
        for r2, d2 in zip(rounds, backward):
            top = max(d1, d2)
            if top <= limit and (best is None or r1 + r2 > best[0]):
                best = (r1 + r2, top + 1)
    return best


def record_fields(program: "ir.Program", rounds: Sequence[int], limit: int = LIMIT) -> Dict:
    """What a `degree` record holds for one direction and its inverse (data-model section 5)."""
    w = program.w
    inverse = ir.invert(program)
    forward, backward = counts(program, w - 1, rounds), counts(inverse, w - 1, rounds)
    bound_f, bound_b = counts(program, w, rounds), counts(inverse, w, rounds)
    return {"phase_counts": {"forward": phase_degrees(program, w - 1),
                             "inverse": phase_degrees(inverse, w - 1)},
            "rounds": list(rounds), "counts": {"forward": forward, "inverse": backward},
            "marked": "the rule's count, not an upper bound",
            "upper_bounds": {"forward": bound_f, "inverse": bound_b},
            "rounds_with_bound_within_limit": {"forward": within(bound_f, rounds, limit),
                                               "inverse": within(bound_b, rounds, limit)},
            "rounds_within_limit": {"forward": within(forward, rounds, limit),
                                    "inverse": within(backward, rounds, limit)},
            "inside_out": inside_out(forward, backward, rounds, limit), "limit": limit}


# -------------------------------------------------------------------------------- the exact degree

def groups_of(program: "ir.Program") -> List[List[int]]:
    """The lanes that act on each other, joined by each update's reads and write; a lane no update
    touches stands in no group."""
    parent: Dict[int, int] = {}

    def find(lane: int) -> int:
        parent.setdefault(lane, lane)
        while parent[lane] != lane:
            parent[lane] = parent[parent[lane]]
            lane = parent[lane]
        return lane

    for phase in program.phases:
        for update in phase.updates:
            for lane in ir.reads(update):
                parent[find(lane)] = find(update.dst)
    groups: Dict[int, List[int]] = {}
    for lane in list(parent):
        groups.setdefault(find(lane), []).append(lane)
    return sorted(sorted(group) for group in groups.values())


def exact_degree(program: "ir.Program", rounds: int) -> Optional[int]:
    """The largest degree of any output bit, from the truth table of each group of lanes, at most
    16 bits a group; None if a group is larger. Constants are taken as 0."""
    loaded = ir.load(program, exploration=True)
    w = program.w
    constants = [tuple([0] * (ir.last_constant(program) + 1))] * rounds \
        if ir.last_constant(program) >= 0 else ()
    best = 0
    for group in groups_of(program):
        bits = len(group) * w
        if bits > MOST_TABLE_BITS:
            return None
        inputs = np.arange(1 << bits, dtype=np.uint64)
        states = np.zeros((2 * program.n ** 2, inputs.size), dtype=np.uint64)
        for place, lane in enumerate(group):
            states[lane] = (inputs >> np.uint64(place * w)) & np.uint64((1 << w) - 1)
        out = ir.permute_batch(loaded, states, constants, None if constants else rounds)
        for lane in group:
            for bit in range(w):
                table = ((out[lane] >> np.uint64(bit)) & np.uint64(1)).astype(np.uint8)
                best = max(best, table_degree(table, bits))
    return best


# ----------------------------------------------------------------------------------- known results

def compare(program: "ir.Program", rounds: Sequence[int], limit: int, wanted_counts: Sequence[int],
            wanted_bounds: Sequence[int], wanted_inside: Optional[Sequence[int]],
            exact: bool) -> Dict:
    fields = record_fields(program, rounds, limit)
    found = {"list": program.name, "n": program.n, "w": program.w, **fields}
    good = fields["counts"]["forward"] == list(wanted_counts) \
        and fields["counts"]["inverse"] == list(wanted_counts) \
        and fields["upper_bounds"]["forward"] == list(wanted_bounds) \
        and fields["upper_bounds"]["inverse"] == list(wanted_bounds) \
        and (fields["inside_out"] is None) == (wanted_inside is None) \
        and (wanted_inside is None or tuple(fields["inside_out"]) == tuple(wanted_inside))
    if exact:
        degrees = [exact_degree(program, r) for r in rounds]
        found["exact_degrees"] = degrees
        good = good and all(degree is None or bound >= degree
                            for degree, bound in zip(degrees, wanted_bounds))
    found["re_found"] = good
    return found


def re_find_small(known, keep) -> Dict:
    rows = []
    for pair in known.PAIRS:
        n, w = pair
        program = ir.load(known.build(n, w)).program
        rows.append(compare(program, known.ROUNDS, known.LIMITS[pair], known.COUNTS[pair],
                            known.BOUNDS[pair], known.INSIDE_OUT[pair], w in known.EXACT_WIDTHS))
    return {"found": {"rows": rows}, "re_found": all(row["re_found"] for row in rows),
            "validated_kind": KIND}


def re_find_second(known, keep) -> Dict:
    rows = []
    for _, builder, n, w, entry in known.CASES:
        program = ir.load(builder(n, w)).program
        rows.append(compare(program, known.ROUNDS, entry["limit"], entry["counts"], entry["bounds"],
                            entry["inside_out"], w <= 8))
    return {"found": {"rows": rows}, "re_found": all(row["re_found"] for row in rows),
            "validated_kind": KIND}


RUNS = {"degree-small": re_find_small, "degree-small-second": re_find_second}


def validation(known_id: str, known, keep: Optional[Callable[[str, bytes], None]]) -> Dict:
    return RUNS[known_id](known, keep)
