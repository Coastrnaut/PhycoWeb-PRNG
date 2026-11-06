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
import argparse
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple

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
CAPACITY = 384
SOURCE = "research/004/tools/costmodel.py"
STATED_REQUESTS = (2 ** 19, 4096 * 32)
REQUESTS_PER_INSTANTIATION = 1024
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


# ------------------------------------------------------------------------- the self-test's run

def lanes_computed(program: "ir.Program") -> Set[int]:
    return {update.dst for phase in program.phases for update in phase.updates}


def self_test_calls(k: int, input_blocks: int = 1) -> int:
    """The calls of Π of the self-test's sequence: instantiate with an empty string, p + 5 calls; a request of k blocks and its forget;
    a reseed of p + 1 calls; and a second request (design document, section "Calls")."""
    return (input_blocks + 5) + (k + 1) + (input_blocks + 1) + (k + 1)


def least_k(program: "ir.Program", rate: int) -> Dict:
    """The least whole blocks for which every structure takes part, as spec FR-059 reads the model's run: every lane and node is
    computed in a call of Π and every ROM entry is read by one, the absorption tree takes each kind of word in instantiate and the
    reseed, the output tree gives a whole block, and each counter runs through a call and to its request's last block. One block meets
    all of that unless the list leaves a lane unwritten, which no number of blocks would mend."""
    lanes = 2 * program.n ** 2
    computed = lanes_computed(program)
    if len(computed) != lanes:
        return {"least_k": None, "structure": f"lanes no update writes: {sorted(set(range(lanes)) - computed)}", "calls": None}
    return {"least_k": 1, "structure": "none: one whole block meets every item", "calls": self_test_calls(1), "rate": rate}


# ----------------------------------------------------------------------------------- the cost record

def cycles_per_call(phases: int, rounds: int, rate: int, interface: int, start_tree: int, output_tree: int) -> Dict:
    """FR-020's per-call counts that the list, P, R and the trees fix, each for a stated public length, the empty string and input."""
    call = phases * rounds + start_tree
    return {"call of Π": call, "instantiate, one block of input": 6 * call + ceiling(rate, interface),
            "generate of one block with its forget": 2 * call + output_tree + ceiling(rate, interface),
            "reseed, one block of input": 2 * call + ceiling(rate, interface)}


def cost_fields(loaded: "ir.Loaded", rounds: int, rate: int, trees: Dict, interface: int = WORD_BITS) -> Dict:
    """Every figure a `cost` record holds for one variant (spec FR-020, FR-026): the model's, the implied throughput at the two stated
    requests, each block of input cycles and the self-test's least k."""
    counted = count(loaded, rounds, rate)
    start, output = trees["start"]["latency_cycles"], trees["output"]["latency_cycles"]
    share = Fraction(6 * (counted["phases"] * rounds + start), REQUESTS_PER_INSTANTIATION)
    stated = {str(bits): throughput(rate, counted["phases"], rounds, interface, bits, start, output, instantiate_share=share)
              for bits in STATED_REQUESTS}
    return {"figures": record_fields(counted), "throughput": stated, "requests_per_instantiation": REQUESTS_PER_INSTANTIATION,
            "cycles_per_call": cycles_per_call(counted["phases"], rounds, rate, interface, start, output),
            "self_test": least_k(loaded.program, rate)}


def write_record(candidate: str, size: int, rounds: int, command: Sequence[str]) -> Path:
    """One `cost` record of one claimable size at one R, from the operation list, P and R (data-model section 9)."""
    from protocol import candidates, evidence
    log = candidates.entries()
    held = candidates.of_event(log, "proposed", candidate)
    if not held:
        raise evidence.Refused(f"{candidate} is not in the candidate log")
    module = candidates.module_rel(candidate)
    evidence.guard_oplist(evidence.sha256(evidence.REPO.path(module).read_bytes()))
    loaded = ir.load(ir.candidate_modules(evidence.REPO.path(candidates.CANDIDATES_REL))[candidate](size, WORD_BITS))
    rate = 2 * size * size * WORD_BITS - CAPACITY
    tool = evidence.sha256(evidence.REPO.path(SOURCE).read_bytes())
    citation = evidence.validation_citation("costmodel", tool)
    fields = {"validation": citation or evidence.NONE, "candidate": candidate}
    if citation is not None:
        fields.update(cost_fields(loaded, rounds, rate, held[0]["parameters"]["trees"][str(size)]))
    code = [SOURCE, "protocol/evidence.py", "protocol/disclaimer.py", "protocol/devinputs_v3.py", "protocol/candidates.py", "research/004/ir.py", module]
    run = evidence.Run("cost", candidate=candidate, model_id=candidate, variant_id=f"{candidate}/n{size}-w{WORD_BITS}-R{rounds}-c{CAPACITY}",
                       code_files=code, argv=command, config={"size": size, "width": WORD_BITS, "rounds": rounds})
    with run:
        return run.finish("pass" if citation is not None else "not evaluated", fields=fields)


def main(argv: Optional[List[str]] = None) -> int:
    from protocol import evidence
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--size", type=int, required=True)
    parser.add_argument("--rounds", type=int, required=True)
    args = parser.parse_args(argv)
    command = [SOURCE] + list(sys.argv[1:] if argv is None else argv)

    def body() -> int:
        path = write_record(args.candidate, args.size, args.rounds, command)
        print(f"{evidence.rel_to_repo(path)}: {args.candidate} at {args.size}×{args.size}, R = {args.rounds}")
        return evidence.EXIT_OK

    return evidence.main_guard(body)


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


if __name__ == "__main__":
    raise SystemExit(main())
