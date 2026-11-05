"""Feature 004: the operation-count cost model (research R5; spec FR-020, FR-022, FR-026).

LUTs, carry chains and depth are counted from a candidate's operation list on 6-input LUTs, with no
packing or fusion between listed operations:

    a rotation or shift by a constant, wiring, a register stage     0 LUTs, 0 chains
    a bitwise function of k input bits per output bit               w · max(1, ceil((k - 1) / 5)) LUTs
    an addition or subtraction modulo 2^w of two words              w LUTs, one chain of w bits

A constant's bits count as inputs of the function they enter, and the ROM that holds them is not
counted. k is the largest count of distinct input bits over the output bits, the update's own word
included when the update is an XOR. L is the LUTs of one round over n², so an update counts once, at
the node that computes it. `chains` is the most additions on a dependency path within one round;
`depth` the LUT levels of each phase's longest path; and the cost per output bit is L · n² · P · R / r
in LUT-cycles.

The implied throughput is reported beside the goal of 10⁸ words per second at 200 MHz. It decides
nothing, and no figure here is a measurement of hardware: post-route numbers belong to feature 008.

Run on its known results by scripts/validate_tool.py (`costmodel-examples` and its second; R13).
Analysis code: the model never imports it. This tool makes no security claim.
"""
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

ROOT = Path(__file__).resolve().parents[3]
for place in (str(ROOT / "research/004"), str(ROOT)):
    if place not in sys.path:
        sys.path.insert(0, place)

import ir  # noqa: E402

CODE = ("research/004/ir.py",)
LUT_INPUTS = 6
GOAL_WORDS_PER_SECOND = 10 ** 8
CLOCK_HZ = 200_000_000
WORD_BITS = 32
FUNCTIONS = (ir.Xor, ir.And, ir.Or, ir.Not)
SINGLE = (ir.Rotl, ir.Shl, ir.Shr, ir.Not)
FIELDS = ("luts", "chains", "phases", "flip_flops", "cost")
KIND = {"widths": [8, 16, 32],
        "operations": "rotations, shifts, bitwise functions, additions, subtractions and constants",
        "model": "the table of research R5 on 6-input LUTs, with no packing or fusion",
        "uses": [{"use": "L and the chains per round in the D4 score and its tie-breaks",
                  "covered_by": ["costmodel-examples"]},
                 {"use": "the cost per output bit and the depth of FR-026's figures",
                  "covered_by": ["costmodel-examples"]}]}


# ------------------------------------------------------------------------------- input bits

def input_bits(expr: Any, place: int, w: int) -> Set[Tuple[str, int, int]]:
    """The input bits that output bit `place` of `expr` depends on, read off the expression, so that
    a bit two terms read counts once, and a bit that cancels still counts."""
    kind = type(expr)
    if kind is ir.Lane:
        return {("lane", expr.index, place)}
    if kind is ir.Constant:
        return {("constant", expr.index, place)}
    if kind is ir.Not:
        return input_bits(expr.value, place, w)
    if kind is ir.Rotl:
        return input_bits(expr.value, (place - expr.amount) % w, w)
    if kind is ir.Shl:
        return input_bits(expr.value, place - expr.amount, w) if place >= expr.amount else set()
    if kind is ir.Shr:
        return input_bits(expr.value, place + expr.amount, w) if place + expr.amount < w else set()
    return input_bits(expr.left, place, w) | input_bits(expr.right, place, w)


def fan_in(expr: Any, w: int) -> int:
    return max(len(input_bits(expr, place, w)) for place in range(w))


def is_wiring(expr: Any) -> bool:
    """A word, rotated or shifted any number of times, reaches its adder through wires alone."""
    kind = type(expr)
    if kind in (ir.Lane, ir.Constant):
        return True
    return kind in (ir.Rotl, ir.Shl, ir.Shr) and is_wiring(expr.value)


def levels(k: int) -> int:
    """The LUT levels of a bitwise function of k input bits per output bit."""
    return max(1, -(-(k - 1) // (LUT_INPUTS - 1)))


# ---------------------------------------------------------------------------------- updates

def is_addition(update: Any) -> bool:
    return type(update) is ir.Mix and update.op in ("add", "sub")


def update_figures(update: Any, w: int) -> Tuple[int, int]:
    """(LUTs, LUT levels) of one listed operation."""
    if type(update) is ir.Rot:
        return 0, 0
    if update.op == "xor":
        depth = levels(1 + fan_in(update.expr, w))
        return w * depth, depth
    if is_wiring(update.expr):
        return w, 1
    depth = levels(fan_in(update.expr, w))
    return w * depth + w, depth + 1


def chains_per_round(program: "ir.Program") -> int:
    """The most additions on a dependency path within one round. Each update takes the longest path
    among what it reads, its own lane included, and adds one if it is an addition; a phase's writes
    land together, as the phase rule lets them."""
    paths: Dict[int, int] = {}
    for phase in program.phases:
        written = {update.dst: max(paths.get(lane, 0) for lane in ir.reads(update))
                   + is_addition(update) for update in phase.updates}
        paths.update(written)
    return max(paths.values(), default=0)


def count(loaded: "ir.Loaded", rounds: int, rate: int) -> Dict:
    """Every figure of R5 for one list, at R = `rounds` and r = `rate`."""
    program = ir.guard_loaded(loaded)
    for name, value in (("rounds", rounds), ("rate", rate)):
        if type(value) is not int or value < 1:
            raise ir.ListRefused(f"{name} {value!r}: a positive integer")
    n, w = program.n, program.w
    figures = [[update_figures(update, w) for update in phase.updates] for phase in program.phases]
    luts = Fraction(sum(item[0] for phase in figures for item in phase), n * n)
    phases = len(program.phases)
    return {"name": program.name, "n": n, "w": w, "rounds": rounds, "rate": rate, "luts": luts,
            "chains": chains_per_round(program),
            "chains_per_phase": [int(any(is_addition(update) for update in phase.updates))
                                 for phase in program.phases],
            "phases": phases, "depth": [max((item[1] for item in phase), default=0)
                                        for phase in figures],
            "flip_flops": 2 * w, "cost": luts * n * n * phases * rounds / rate}


def record_fields(found: Dict) -> Dict:
    """The figures as a record holds them: each fraction written exactly, as a string."""
    return {key: str(value) if isinstance(value, Fraction) else value
            for key, value in found.items()}


# ------------------------------------------------------------------------------- throughput

def ceiling(value: int, unit: int) -> int:
    return -(-value // unit)


def call_cycles(rate: int, phases: int, rounds: int, interface: int, start_tree: int = 0,
                output_tree: int = 0) -> int:
    """P·R + ⌈r/i⌉ + t_s + t_o, a call of Π with its block taken at i bits per cycle."""
    return phases * rounds + ceiling(rate, interface) + start_tree + output_tree


def rate_per_call(rate: int, phases: int, rounds: int, interface: int, start_tree: int = 0,
                  output_tree: int = 0) -> Fraction:
    """Bits per cycle, before forget calls: the upper bound beside each request's rate."""
    return Fraction(rate, call_cycles(rate, phases, rounds, interface, start_tree, output_tree))


def words_per_second(bits_per_cycle: Fraction) -> Fraction:
    return bits_per_cycle * CLOCK_HZ / WORD_BITS


def request_cycles(bits: int, rate: int, phases: int, rounds: int, interface: int,
                   start_tree: int = 0, output_tree: int = 0, clearing: int = 0,
                   instantiate_share: Fraction = Fraction(0)) -> Fraction:
    """One request of `bits` bits: its output calls, each with both trees, its words taken at i bits
    per cycle, its forget call with the start tree, the clearing at its end, and its share of
    instantiate's calls over the stated requests per instantiation (spec FR-026)."""
    calls = ceiling(bits, rate)
    return (calls * (phases * rounds + start_tree + output_tree) + ceiling(bits, interface)
            + phases * rounds + start_tree + clearing + instantiate_share)


def throughput(rate: int, phases: int, rounds: int, interface: int, bits: int, start_tree: int = 0,
               output_tree: int = 0, clearing: int = 0,
               instantiate_share: Fraction = Fraction(0)) -> Dict:
    """FR-026's figures for one stated request, as exact fractions in strings, beside the goal,
    which is reported and never an eligibility rule."""
    cycles = request_cycles(bits, rate, phases, rounds, interface, start_tree, output_tree,
                            clearing, instantiate_share)
    before = rate_per_call(rate, phases, rounds, interface, start_tree, output_tree)
    return {"request_bits": bits, "interface_bits_per_cycle": interface,
            "start_tree_latency": start_tree, "output_tree_latency": output_tree,
            "bits_per_cycle_before_forget": str(before),
            "bits_per_round_cycle": str(Fraction(rate, phases * rounds)),
            "rate_before_forget": str(words_per_second(before)),
            "throughput_implied": str(words_per_second(Fraction(bits) / cycles)),
            "throughput_goal": GOAL_WORDS_PER_SECOND}


# -------------------------------------------------------------------------------- validation

def re_found(found: Dict, want: Dict) -> bool:
    return all(found[name] == want[name] for name in FIELDS) \
        and tuple(found["depth"]) == tuple(want["depth"])


def compare(loaded: "ir.Loaded", rounds: int, rate: int, want: Dict) -> Dict:
    found = count(loaded, rounds, rate)
    return dict(record_fields(found), re_found=re_found(found, want))


def re_find_first(known, keep) -> Dict:
    rows = [compare(ir.load(known.build(label, builder)), known.R, known.RATE, want)
            for label, builder, want in known.EXAMPLES]
    return {"found": {"rows": rows}, "re_found": all(row["re_found"] for row in rows),
            "validated_kind": KIND}


def re_find_second(known, keep) -> Dict:
    rows = [compare(ir.load(known.build(label, builder, want["n"], want["w"])), want["rounds"],
                    want["rate"], want) for label, builder, want in known.EXAMPLES]
    return {"found": {"rows": rows}, "re_found": all(row["re_found"] for row in rows),
            "validated_kind": KIND}


RUNS = {"costmodel-examples": re_find_first, "costmodel-examples-second": re_find_second}


def validation(known_id: str, known, keep: Optional[Callable[[str, bytes], None]]) -> Dict:
    return RUNS[known_id](known, keep)
