#!/usr/bin/env python3
"""Feature 004: every measurement of a candidate (contracts/cli.md; data-model sections 5 to 7; research
R4, R7, R12, R13).

    evidence_v3.py --candidate ID --kind KIND [--size N] [--width W] [--rounds R] [--project] --out-dir DIR
    evidence_v3.py --kind control --test frequency|avalanche --size N [--project] --out-dir DIR
    evidence_v3.py --reproduce RECORD [--owner-request "WORDS (DATE)"]
    evidence_v3.py --aborted RECORD

KIND is inverse, bijectivity, dependency, frequency, avalanche, symmetry, invariant, degree, bound (with
--bound-kind differential|linear --method M), cross-check (with --tool NAME) or rotation-ranking. The
counts are research R4's and R13's, and no option lowers them. Each run projects first against its budget row, takes the
heavy-run lock, writes one record with its raw outputs and appends an `evidence` entry to the candidate
log, every run started writing a record, `inconclusive` if it was aborted.

Statistical evidence is not evidence of security. This script makes no security claim.
"""
import argparse
import gzip
import hashlib
import importlib.util
import json
import math
import multiprocessing
import os
import shutil
import queue
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[1]
for place in (str(ROOT), str(ROOT / "scripts"), str(ROOT / "research/004"), str(ROOT / "research/004/tools"),
              str(ROOT / "research/004/tools/trails")):
    if place not in sys.path:
        sys.path.insert(0, place)

import numpy as np  # noqa: E402

from protocol import candidates, devinputs_v3, evidence  # noqa: E402
from protocol.evidence import NONE, Refused, ToolFailure  # noqa: E402

import active_sbox  # noqa: E402
import arx_search_known  # noqa: E402
import avalanche  # noqa: E402
import bias  # noqa: E402
import bijectivity  # noqa: E402
import degree  # noqa: E402
import dependency  # noqa: E402
import gen_constants_v3  # noqa: E402
import invariants  # noqa: E402
import ir  # noqa: E402
import long_trail  # noqa: E402
import symmetry  # noqa: E402
import tables  # noqa: E402

SCRIPT = "scripts/evidence_v3.py"
KINDS = ("inverse", "bijectivity", "dependency", "frequency", "avalanche", "symmetry", "invariant", "degree",
         "bound", "cross-check", "rotation-ranking")
ROWS = {"inverse": "structural", "bijectivity": "structural", "dependency": "structural", "symmetry": "structural",
        "invariant": "structural", "degree": "structural", "frequency": "statistics", "avalanche": "statistics",
        "control": "statistics", "bound": "trails", "cross-check": "trails", "rotation-ranking": "trails"}
# Each row's kinds in research R7's fixed order; the trail row's runs depend on the amounts chosen.
ROW_ORDER = {"structural": ("inverse", "bijectivity", "dependency", "symmetry", "invariant", "degree"),
             "statistics": ("frequency", "avalanche")}
NO_TABLE = ("dependency", "degree")
TRAIL_KINDS = ("bound", "cross-check", "rotation-ranking")
BIAS_KINDS = ("frequency", "avalanche")
TOOL_PATHS = {"bijectivity": "research/004/tools/bijectivity.py", "dependency": "research/004/tools/dependency.py",
              "frequency": "research/004/tools/bias.py", "avalanche": "research/004/tools/avalanche.py",
              "control": "research/004/tools/bias.py", "symmetry": "research/004/tools/symmetry.py",
              "invariant": "research/004/tools/invariants.py", "degree": "research/004/tools/degree.py"}
TOOL_NAMES = {"bijectivity": "bijectivity", "dependency": "dependency", "frequency": "bias", "avalanche": "avalanche",
              "control": "bias", "symmetry": "symmetry", "invariant": "invariants", "degree": "degree"}
TRAIL_PATHS = {"ARX search": "research/004/tools/trails/arx_search.c",
               "active-S-box counting": "research/004/tools/trails/active_sbox.py",
               "long-trail active-box counting": "research/004/tools/trails/long_trail.py",
               "exhaustive tables": "research/004/tools/trails/tables.py"}
MODULES = {"bijectivity": bijectivity, "dependency": dependency, "bias": bias, "avalanche": avalanche,
           "symmetry": symmetry, "invariants": invariants, "degree": degree, "ARX search": arx_search_known,
           "active-S-box counting": active_sbox, "long-trail active-box counting": long_trail,
           "exhaustive tables": tables}
ARX_BINARY = "research/004/tools/trails/build/arx_search"
ARX_MAKE = "research/004/tools/trails/arx_search.mk"
CODE = list(dict.fromkeys(
    [SCRIPT, "protocol/evidence.py", "protocol/disclaimer.py", "protocol/candidates.py", "protocol/devinputs_v3.py",
     "research/004/ir.py", "research/004/tools/symmetry.py", "research/004/tools/invariants.py",
     "research/004/tools/dependency.py", "research/004/tools/degree.py", "research/004/tools/bijectivity.py",
     "research/004/tools/bias.py", "research/004/tools/avalanche.py", bias.TABLE_REL, "scripts/gen_constants_v3.py"]
    + list(TRAIL_PATHS.values())[1:] + ["research/004/tools/trails/arx_search_known.py"] + list(gen_constants_v3.CODE)
    + [rel for module in (bias, avalanche, invariants, symmetry, dependency, degree, bijectivity) for rel in module.CODE]))
SCOPE = ("single trails under the usual independence assumptions; clustering into differentials and linear hulls, and "
         "key-dependent effects, open for feature 005")
BIAS_SCOPE = "the inputs, counts and thresholds of research R4, at the round counts measured"
NO_CONSTANT = ("the matrices read no constant value, so they cover one permutation for every call type")
INSTANCE_HOURS = 8.0
CROSS_WIDTHS = (4, 8)
SEARCH_RANGE = 64
RANK_ROUNDS = 2
RANK_SIZE = 4
PRODUCTION_WIDTH = 32
MEASURE = "min(W_D, W_L) at the search width, at 4×4, over 2 rounds of Π (protocol change log, seq 520)"
TIE_ORDER = "the numbers of an assignment in the order the candidate's log entry states them, first set first, lexicographically"
POLL_SECONDS = 2.0
CAP_MARGIN = 1.1
WIDTH_LIMITATION = ("no exact confirmation exists at this width without a further tool: the bound stands as the solver "
                    "reports it, within its tolerances (research R12)")
MAPPED_STATEMENT = "the states of a control are taken as research R4's states, and it reads no constant"
TEST_STATES = 2 ** 10
FIXED_STATES = 16
FREQUENCY_N = bias.N
PROBE_INPUTS = 2 ** 10
WORKERS = max(1, (os.cpu_count() or 2) - 2)
FLIP_CHUNK = 64
GROUP_CHUNK = 64
FLIPS, RELATED, ROTATIONS = "flip set", "related keys and nonces", "rotational pairs"
DISAGREEMENT = "the dependency matrices show independent flipped"
PROBE_SECONDS = 60.0
RATIO_OF_A_ROUND = 6.0
BITS_EXPONENT = 1.7
SMALLEST_STATES = ((4, 4), (4, 8))
DEFECTS_REL = "research/004/validation/defects"


def _follow_feature() -> None:
    """A defect note goes under the active feature's paths (feature 005, research R9)."""
    global DEFECTS_REL
    DEFECTS_REL = evidence.FEATURES[evidence.FEATURE]["research"] + "/validation/defects"


evidence.on_feature(_follow_feature)
OUTPUT_FIELDS = ("raw_counts", "p_values", "failure_locations", "solver", "budget", "hours_used")
RUN_HERE = """
import importlib.util, sys
spec = importlib.util.spec_from_file_location("evidence_v3", "scripts/evidence_v3.py")
module = importlib.util.module_from_spec(spec)
sys.modules["evidence_v3"] = module
spec.loader.exec_module(module)
getattr(module, sys.argv[1])(*sys.argv[2:])
"""


# ----------------------------------------------------------------------------------- the subject

@dataclass
class Subject:
    """One variant of one candidate: its list, its table and what names them."""
    candidate: str
    n: int
    w: int
    rounds: int
    c: int
    variant: str
    loaded: Any
    table: List[List[int]]
    table_rel: str

    @property
    def program(self) -> "ir.Program":
        return self.loaded.program

    @property
    def variant_id(self) -> str:
        return f"{self.candidate}/{self.variant}"


def module_rel(candidate: str) -> str:
    return candidates.module_rel(candidate)


def guard_candidate(candidate: str) -> None:
    """The candidate has a `proposed` entry, and its module is a hash the log holds (data-model section 3)."""
    log = candidates.entries()
    if not candidates.of_event(log, "proposed", candidate):
        raise Refused(f"{candidate} is not in the candidate log")
    path = evidence.REPO.path(module_rel(candidate))
    if not path.exists():
        raise Refused(f"{module_rel(candidate)} does not exist")
    evidence.guard_oplist(evidence.sha256(path.read_bytes()))


def amounts_module(candidate: str):
    """The candidate's module as loaded, for its stated boxes and amounts."""
    ir.candidate_modules(evidence.REPO.path(candidates.CANDIDATES_REL))
    return sys.modules[candidate.replace("-", "_")]


def build_list(candidate: str, n: int, w: int) -> "ir.Loaded":
    builds = ir.candidate_modules(evidence.REPO.path(candidates.CANDIDATES_REL))
    if candidate not in builds:
        raise Refused(f"{module_rel(candidate)} does not exist")
    return ir.load(builds[candidate](n, w))


def table_named(candidate: str, n: int, w: int, rounds: int) -> Tuple[str, str]:
    """The table of (n, w, R), the one file of that name, whatever its capacity: a table is written
    before the first record that reads it (research R15)."""
    base = evidence.REPO.path(f"{candidates.CANDIDATES_REL}/{candidate}/constants")
    found = sorted(base.glob(f"n{n}-w{w}-R{rounds}-c*.json")) if base.exists() else []
    if len(found) != 1:
        raise Refused(f"{candidate} has no table at n{n}-w{w}-R{rounds}: gen_constants_v3.py writes it first")
    return found[0].stem, evidence.rel_to_repo(found[0])


def subject_of(candidate: str, n: int, w: int, rounds: int) -> Subject:
    variant, rel = table_named(candidate, n, w, rounds)
    held = json.loads(evidence.REPO.path(rel).read_bytes().decode("utf-8"))
    table = [[int(word, 16) for word in row] for row in held["table"]]
    c = int(variant.rsplit("-c", 1)[1])
    return Subject(candidate, n, w, rounds, c, variant, build_list(candidate, n, w), table, rel)


def plain_subject(candidate: str, n: int, w: int, rounds: int = 0) -> Subject:
    """A subject that reads no constant, a dependency, degree or trail run, which covers every R."""
    return Subject(candidate, n, w, rounds, 0, f"n{n}-w{w}", build_list(candidate, n, w), [], "")


def latest_rounds(candidate: str, n: int, w: int) -> int:
    base = evidence.REPO.path(f"{candidates.CANDIDATES_REL}/{candidate}/constants")
    held = sorted(int(path.stem.split("-R")[1].split("-")[0]) for path in base.glob(f"n{n}-w{w}-R*-c*.json"))
    if not held:
        raise Refused(f"{candidate} has no table at ({n}, {w})")
    return held[-1]


def table_field(subject: Subject) -> Dict:
    return {"path": subject.table_rel, "sha256": evidence.sha256(evidence.REPO.path(subject.table_rel).read_bytes()),
            "sha256_kind": "raw"}


def state_inputs(n: int, w: int, count: int) -> Dict:
    return {"namespace": "dev", "kind": "state", "n": n, "w": w, "index_range": [0, count - 1],
            "fingerprint": devinputs_v3.fingerprint("dev", "state", n, w)}


def tool_sha(kind: str) -> str:
    return evidence.sha256(evidence.REPO.path(TOOL_PATHS[kind]).read_bytes())


def citation_of(kind: str, w: int) -> Optional[Dict]:
    """What a counted record holds in `validation`, None where the tool has no `re-found` record of its exact hash or the width lies
    outside its validated kind, and the result is `not evaluated`. An inverse test runs the interpreter and no counted tool."""
    if kind not in TOOL_NAMES:
        return {"tool": NONE}
    name = TOOL_NAMES[kind]
    if w not in MODULES[name].KIND["widths"]:
        return None
    return evidence.validation_citation(name, tool_sha(kind))


# ----------------------------------------------------------------------------- the initial state

def key_bits(c: int) -> int:
    return min(c, 256)


def variant_word(n: int, w: int, c: int, rounds: int) -> int:
    """V = n + 2⁸·w + 2¹⁶·(c/8) + 2²⁴·R, the design document's section "Layout"."""
    return n + (w << 8) + ((c // 8) << 16) + (rounds << 24)


def lanes_of(data: bytes, w: int) -> List[int]:
    step = w // 8
    return [int.from_bytes(data[at:at + step], "big") for at in range(0, len(data), step)]


def initial_state(key: bytes, nonce: bytes, subject: Subject) -> List[int]:
    """The state instantiate gives to its first call of Π: the key in the first lanes, the nonce in
    the next, 0 elsewhere, and the variant word in the last 32 bits."""
    n, w = subject.n, subject.w
    k = key_bits(subject.c)
    state = [0] * (2 * n * n)
    words = lanes_of(key[:k // 8], w) + lanes_of(nonce[:k // 16], w)
    state[:len(words)] = words
    word = variant_word(n, w, subject.c, subject.rounds)
    if w == 32:
        state[-1] = word
    elif w == 16:
        state[-2:] = [word >> 16, word & 0xFFFF]
    return state


def instantiation_batch(subject: Subject, first: int, count: int, same_key: bool) -> np.ndarray:
    """States `first` to `first + count - 1` of a set: key i with nonce i, or key 0 with nonce i."""
    keys = devinputs_v3.load("dev", "key", ("dev",), first + count)
    nonces = devinputs_v3.load("dev", "nonce", ("dev",), first + count)
    rows = [initial_state(keys[0 if same_key else i], nonces[i], subject) for i in range(first, first + count)]
    return np.array(rows, dtype=np.uint64).T


# ----------------------------------------------------------------------------- what a record holds

def json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def kept_output(run: evidence.Run, name: str, value: Any) -> Dict:
    """Up to 10 MB compressed an output is committed, and above it stays local-only (research R16)."""
    data = json_bytes(value)
    large = len(gzip.compress(data, compresslevel=9, mtime=0)) > evidence.MAX_COMMITTED_BYTES
    return cite(run.output(name, data, local=large))


def cite(entry: Dict) -> Dict:
    return {"path": entry["path"], "sha256": entry["sha256"], "sha256_kind": entry["sha256_kind"]}


def finding_result(status: str, kind: str, outcome: str, fields: Dict, inputs: Any, finding: Any = NONE) -> Dict:
    return {"status": status, "classification": evidence.classify(kind, outcome), "fields": dict(fields, finding=finding),
            "inputs": inputs}


# ------------------------------------------------------------------------------ structural kinds

def run_inverse(subject: Subject, run: evidence.Run) -> Dict:
    loaded, table = subject.loaded, subject.table
    n, w = subject.n, subject.w
    fixed = np.array([state for _, state in gen_constants_v3.reference_inputs(n, w)], dtype=np.uint64).T
    states = np.concatenate((fixed, invariants.test_states(n, w, TEST_STATES)), axis=1)
    there = ir.permute_batch_inverse(loaded, ir.permute_batch(loaded, states, table), table)
    back = ir.permute_batch(loaded, ir.permute_batch_inverse(loaded, states, table), table)
    wrong = {"inverse of forward": int(np.count_nonzero((there != states).any(axis=0))),
             "forward of inverse": int(np.count_nonzero((back != states).any(axis=0)))}
    status, outcome = evidence.verdict_inverse(wrong)
    return finding_result(status, "inverse", outcome, {
        "states": int(states.shape[1]), "mismatches": wrong, "constants": table_field(subject)},
        dict(state_inputs(n, w, TEST_STATES), constructed=FIXED_STATES),
        NONE if status == "pass" else f"Π⁻¹ does not undo Π on {sum(wrong.values())} of the test states")


def run_bijectivity(subject: Subject, run: evidence.Run) -> Dict:
    if (subject.n, subject.w) != (2, 4):
        raise Refused("the exhaustive bijectivity runs at 2×2 with w = 4")
    found = bijectivity.sweep(lambda states: ir.permute_batch(subject.loaded, states, subject.table))
    status, outcome = evidence.verdict_bijectivity(found["inputs"], found["ones"])
    return finding_result(status, "bijectivity", outcome, dict(found, constants=table_field(subject)),
                          "every state of 32 bits",
                          NONE if status == "pass" else f"{found['ones']} distinct outputs of {found['inputs']} inputs")


def loading_start(n: int, w: int, symbols: int) -> np.ndarray:
    """The input bits each state bit takes at key and nonce loading: the first `symbols` bits of the state hold them, and the rest
    is constant, so that it holds none."""
    start = dependency.identity(n, w)
    for lane in range(start.shape[0]):
        for bit in range(w):
            if lane * w + bit >= symbols:
                start[lane, bit] = 0
    return start


def through_instantiate(subject: Subject) -> Any:
    """Where every state bit depends on every key and nonce bit, in rounds of Π from key loading. The round rule sets it against the
    p + 6 calls of R rounds each before the first output, computing the margin over R_f at each R (research R13)."""
    if subject.n not in evidence.CLAIMABLE_SIZES:
        return NONE
    symbols = avalanche.RELATED_BITS
    reached = dependency.first_full(subject.program, dependency.FORWARD, dependency.LIMIT,
                                    loading_start(subject.n, subject.w, symbols), symbols)
    return {"symbols": symbols, "every_bit_reached_after": reached}


def run_dependency(subject: Subject, run: evidence.Run) -> Dict:
    program = subject.program
    report = dependency.report(program)
    status, outcome, incomplete = evidence.verdict_dependency(report)
    for direction in (dependency.FORWARD, dependency.INVERSE):
        walk = dependency.rounds_of(dependency.direction_of(program, direction), dependency.identity(program.n, program.w))
        for r in range(len(report[direction]["pairs_without_dependency"])):
            state = next(walk)
            run.output(f"matrix-{direction}-{r + 1}.json.gz", json_bytes(
                {"direction": direction, "round": r + 1, "shape": list(state.shape), "hex": state.tobytes().hex()}), local=True)
    fields = {"r_f": report[dependency.FORWARD]["first_full"], "r_b": report[dependency.INVERSE]["first_full"],
              "per_round": report, "incomplete_rounds": incomplete, "reads_no_constant": NO_CONSTANT,
              "through_instantiate": through_instantiate(subject)}
    return finding_result(status, "dependency", outcome, fields, NONE,
                          f"incomplete diffusion at round counts up to {incomplete}" if incomplete else NONE)


def run_symmetry(subject: Subject, run: evidence.Run) -> Dict:
    found = symmetry.check(subject.program, subject.table)
    words = [word for row in subject.table for word in row]
    related = {name: len(items) for name, items in symmetry.relations(words, subject.w).items()} \
        if subject.w > 8 else "repeats at this width are the rule's, recorded in the table"
    fixed = {name: len(items) for name, items in found["fixed"].items()}
    turned = {k: v for k, v in found["word_rotations"].items() if v}
    composed = {k: len(v) for k, v in found["composed"].items() if v}
    status, outcome = evidence.verdict_symmetry(fixed, turned, composed, related)
    return finding_result(status, "symmetry", outcome, {
        "fixed": fixed, "word_rotations": turned, "composed": composed, "relations": related, "joined": found["joined"],
        "constants": table_field(subject),
        "joined_statement": "the placements were checked with the round constants as one pattern" if found["joined"] else NONE},
        NONE, NONE if status == "pass" else "a symmetry keeps a constant pattern, or constants of one call are related")


def transport_differences(n: int, w: int) -> Dict[str, Dict[int, int]]:
    """The S13 transport mode: 2 and -2 alternately on the pressure lanes, in lane order and by the checkerboard."""
    mask = (1 << w) - 1
    nodes = [(i, j) for i in range(n) for j in range(n)]
    return {"in lane order": {ir.lane(n, i, j, ir.PRESSURE): (2 if at % 2 == 0 else -2) & mask for at, (i, j) in enumerate(nodes)},
            "by the checkerboard": {ir.lane(n, i, j, ir.PRESSURE): (2 if (i + j) % 2 == 0 else -2) & mask for i, j in nodes}}


def run_invariant(subject: Subject, run: evidence.Run) -> Dict:
    n, w = subject.n, subject.w
    states = invariants.test_states(n, w, TEST_STATES)
    counts = (1, subject.rounds)
    found = invariants.check(subject.loaded, states, subject.table, counts)
    rows = {str(r): {"kept": [invariants.readable(form) for form in item["kept"]],
                     "above_chance": [invariants.readable(form) for form in item["above_chance"]],
                     "held": {invariants.readable(form): count for form, count in item["held"].items()}}
            for r, item in found.items()}
    differences = {name: {str(r): invariants.difference_kept(subject.loaded, states, delta, subject.table, r) for r in counts}
                   for name, delta in transport_differences(n, w).items()}
    status, outcome, fired = evidence.verdict_invariant(rows, differences)
    return finding_result(status, "invariant", outcome, {
        "round_counts": rows, "differences": differences, "rounds_fired": fired, "constants": table_field(subject)},
        state_inputs(n, w, TEST_STATES),
        NONE if status == "pass" else f"a form or difference held at round counts {fired}")


def degree_rounds(program: "ir.Program") -> List[int]:
    """Round counts up to the first at which the rule's count passes the limit in both directions, or reaches its cap of b - 1 where
    that lies within the limit, as at a research size."""
    inverse = ir.invert(program)
    wanted = min(degree.LIMIT + 1, 2 * program.n ** 2 * program.w - 1)
    top = 1
    while top < dependency.LIMIT and min(degree.counts(program, program.w - 1, [top])[0],
                                         degree.counts(inverse, program.w - 1, [top])[0]) < wanted:
        top += 1
    return list(range(1, top + 1))


def run_degree(subject: Subject, run: evidence.Run) -> Dict:
    fields = degree.record_fields(subject.program, degree_rounds(subject.program))
    status, outcome, raised = evidence.verdict_degree(fields)
    return finding_result(status, "degree", outcome, dict(fields, rounds_fired=raised), NONE,
                          f"the rule's count is within {degree.LIMIT} at round counts up to {max(raised)}" if raised else NONE)


# ----------------------------------------------------------------------------- statistical kinds

def worker_map(function: Callable, jobs: Sequence, workers: int) -> List:
    """The results in the order of `jobs`, each fixed by its job, whatever the number of workers (spec FR-053)."""
    if workers == 1:
        return [function(job) for job in jobs]
    with multiprocessing.get_context("spawn" if os.name == "nt" else "fork").Pool(workers) as pool:
        return pool.map(function, jobs, chunksize=1)


def frequency_worker(job: Tuple[Subject, int, int, bool]) -> Dict[str, np.ndarray]:
    """One batch's counts in a process of its own."""
    subject, first, count, same_key = job
    return bias.frequency_counts(subject.loaded, [instantiation_batch(subject, first, count, same_key)],
                                 subject.table, subject.rounds)


def frequency_jobs(subject: Subject, same_key: bool, total: int) -> List[Tuple]:
    return [(subject, first, min(bias.BATCH, total - first), same_key) for first in range(0, total, bias.BATCH)]


def summed(results: Sequence[Dict[str, np.ndarray]]) -> Dict[str, np.ndarray]:
    return {name: sum(result[name] for result in results) for name in ("forward", "inverse")}


def smallest_p(flat: np.ndarray, total: int) -> float:
    """The p-value of the count farthest from half, the smallest of a set of counts; reported only."""
    far = int(flat[np.argmax(np.abs(2 * flat.astype(np.int64) - total))])
    return float(bias.p_values(np.array([far]), total)[0])


def extremes(rows: np.ndarray) -> List[List[int]]:
    """Each round's least and largest count, from which the re-check recomputes the verdict."""
    return [[int(row.min()), int(row.max())] for row in rows]


def tested_pairs(candidate: str, this: Sequence[Tuple[str, int, int]]) -> Tuple[int, List[float]]:
    """N, the pairs of a size and a round count r tested with 2r above the R in force, and each size's a of the avalanche test, up to
    and with this record (research R4, False firing)."""
    pairs = set()
    measured: Dict[int, int] = {}
    runs = list(this)
    for kind in BIAS_KINDS:
        for _, record in evidence.iter_records(kind, f"candidates/{candidate}"):
            config = record.get("config", {})
            if evidence.is_finished(record):
                runs.append((kind, config["size"], config["rounds"]))
    for kind, size, rounds in runs:
        pairs.update((size, r) for r in range(1, rounds + 1) if 2 * r > rounds)
        if kind == "avalanche":
            measured[size] = max(measured.get(size, 0), rounds)
    return len(pairs), [2.0 if m <= bias.AVALANCHE_ROUNDS else m / 64.0 for _, m in sorted(measured.items())]


def stated_chance(candidate: str, kind: str, subject: Subject) -> float:
    pairs, sizes = tested_pairs(candidate, [(kind, subject.n, subject.rounds)])
    return evidence.false_firing_chance(pairs, sizes)


def exclusions_field(run: evidence.Run) -> List[Dict]:
    return list(run.extra.get("exclusions_and_reruns", []))


def run_frequency(subject: Subject, run: evidence.Run) -> Dict:
    s = 4 * 2 * subject.n ** 2 * subject.w
    entry = bias.entry_for("frequency", FREQUENCY_N, s)
    raw: Dict[str, Dict] = {}
    summaries: Dict[str, Dict] = {}
    small: Dict[str, Dict] = {}
    locations: List[Dict] = []
    for name, same_key in (("key i, nonce i", False), ("key 0, nonce i", True)):
        counts = summed(worker_map(frequency_worker, frequency_jobs(subject, same_key, FREQUENCY_N), run.workers))
        raw[name], summaries[name], small[name] = {}, {}, {}
        for direction, table in counts.items():
            ordered = np.stack([bias.test_order(table[r]) for r in range(table.shape[0])])
            raw[name][direction] = ordered.tolist()
            summaries[name][direction] = extremes(ordered)
            small[name][direction] = [smallest_p(ordered[r], FREQUENCY_N) for r in range(ordered.shape[0])]
            for r in range(ordered.shape[0]):
                locations += [{"set": name, "direction": direction, "round": r + 1, "position": position, "count": count}
                              for position, count in bias.fired_bits(ordered[r], entry)]
    fired = evidence.frequency_rounds_fired(summaries, entry["low"], entry["high"])
    status, outcome, raises = evidence.verdict_bias(fired, subject.rounds)
    chance = stated_chance(subject.candidate, "frequency", subject)
    fields = {"sample_size": {"n": FREQUENCY_N, "sets": 2},
              "test_parameters": {"s": s, "threshold": "0.005/S", "critical": [entry["low"], entry["high"]],
                                  "table": {"path": bias.TABLE_REL, "sha256": evidence.sha256(
                                      evidence.REPO.path(bias.TABLE_REL).read_bytes()), "sha256_kind": "raw"}},
              "raw_counts": kept_output(run, "counts.json.gz", raw),
              "p_values": cite(run.output("p-values.json.gz", json_bytes(small), deterministic=False, compared="values")),
              "failure_locations": kept_output(run, "failure-locations.json.gz", locations), "summaries": summaries,
              "rounds_fired": fired, "raises": raises, "exclusions_and_reruns": exclusions_field(run), "scope": BIAS_SCOPE,
              "constants": table_field(subject)}
    return finding_result(status, "frequency", outcome, fields, {
        "sets": ["key i with nonce i", "key 0 with nonce i"], "index_range": [0, FREQUENCY_N - 1], "namespace": "dev",
        "kind": ["key", "nonce"]},
        f"fires at round counts {fired}, a chance of a false firing of {chance:.4f}" if fired else NONE)


class Hashed:
    """A file that hashes what passes into it, so that a worker's large output needs no second reading."""

    def __init__(self, path: Path):
        self.file = open(path, "wb")
        self.digest = hashlib.sha256()
        self.size = 0

    def write(self, data: bytes) -> int:
        self.digest.update(data)
        self.size += len(data)
        return self.file.write(data)

    def flush(self) -> None:
        self.file.flush()

    def close(self) -> None:
        self.file.close()


class Part:
    """One worker's raw counts, a gzip-compressed JSON array written as they come, its header as research R16 states."""

    def __init__(self, path: Path):
        self.path = path
        self.raw = Hashed(path)
        self.stream = gzip.GzipFile(filename="", mode="wb", compresslevel=9, fileobj=self.raw, mtime=0)
        self.plain = hashlib.sha256()
        self.items = 0

    def add(self, item: Any) -> None:
        data = (b"[" if self.items == 0 else b",\n") + json_bytes(item)
        self.plain.update(data)
        self.stream.write(data)
        self.items += 1

    def close(self) -> Dict:
        data = b"]" if self.items else b"[]"
        self.plain.update(data)
        self.stream.write(data)
        self.stream.close()
        self.raw.close()
        return {"file": self.path.name, "sha256": self.raw.digest.hexdigest(), "bytes": self.raw.size,
                "uncompressed_sha256": self.plain.hexdigest()}


class Counted(avalanche.Tally):
    """The tally of a path through the validated loops, which also keeps what the record holds: each count, every fired bit, and each
    round's least and largest count. A bit that never flips fires, the expected set among them, so every firing counts here (research
    R4). The lines of firings outside the expected set go into `failure_locations` with the rest."""

    def __init__(self, path: str, rounds: int, first: Dict, whole: Dict, sink: Optional[Part], total: Tuple[int, int]):
        super().__init__(path, rounds, first, whole)
        self.sink = sink
        self.counts = {"first": [[total[0], 0] for _ in range(rounds)], "whole": [[total[1], 0] for _ in range(rounds)]}
        self.fired = [0] * rounds
        self.located: List[Dict] = []
        self.farthest = [0] * rounds

    def add(self, tag: str, r: int, early: np.ndarray, whole: np.ndarray, expected: np.ndarray) -> None:
        super().add(tag, r, early, whole, expected)
        self.lines.clear()
        for name, counts in (("first", early), ("whole", whole)):
            row = self.counts[name][r]
            row[0], row[1] = min(row[0], int(counts.min())), max(row[1], int(counts.max()))
        order_whole = bias.test_order(whole)
        fired = bias.test_order(bias.fires(early, self.first) | bias.fires(whole, self.whole))
        count = int(np.count_nonzero(fired))
        self.fired[r] += count
        self.farthest[r] = max(self.farthest[r], int(np.abs(2 * order_whole - avalanche.N_A).max()))
        if count:
            self.located.append({"path": self.path, "tag": tag, "round": r + 1, "fired": np.packbits(fired).tobytes().hex()})
        if self.sink is not None:
            self.sink.add({"tag": tag, "round": r + 1, "first": bias.test_order(early).tolist(), "whole": order_whole.tolist()})


def bias_entries(n: int) -> Tuple[Dict, Dict]:
    return (bias.entry_for("avalanche", avalanche.N_FIRST, avalanche.s_a(n)),
            bias.entry_for("avalanche", avalanche.N_A, avalanche.s_a(n)))


def stored_matrices(directory: str, directions: Sequence[str], rounds: int) -> Dict[str, List[np.ndarray]]:
    """The dependency matrices, read in place, so that the workers share one copy of them."""
    return {direction: [np.load(Path(directory) / f"{direction}-{r}.npy", mmap_mode="r") for r in range(rounds)]
            for direction in directions}


def store_matrices(subject: Subject, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    forward, inverse = dependency.FORWARD, dependency.INVERSE
    for direction, matrices in avalanche.matrices_of(subject.program, subject.rounds, (forward, inverse)).items():
        for r, matrix in enumerate(matrices):
            np.save(directory / f"{direction}-{r}.npy", matrix)


def avalanche_worker(job: Tuple) -> Dict:
    """One part of one path, its raw counts in a file of its own."""
    subject, path, numbers, part, directory = job
    sink = Part(Path(directory) / f"counts-{part:04d}.json.gz") if directory else None
    tally = avalanche_part(subject, path, numbers, sink, directory)
    kept = sink.close() if sink else NONE
    return {"path": path, "part": kept, "summary": tally.summary(), "counts": tally.counts, "fired": tally.fired,
            "located": tally.located, "farthest": tally.farthest}


def avalanche_part(subject: Subject, path: str, numbers: Sequence[int], sink: Optional[Part], directory: str) -> Counted:
    n, rounds = subject.n, subject.rounds
    first, whole = bias_entries(n)
    tally = Counted(path, rounds, first, whole, sink, (avalanche.N_FIRST, avalanche.N_A))
    forward, inverse = dependency.FORWARD, dependency.INVERSE
    rows = {forward: bias.rows_of(subject.table, rounds, False), inverse: bias.rows_of(subject.table, rounds, True)}
    nothing = lambda lane: ()  # noqa: E731
    if path == FLIPS:
        matrices = stored_matrices(directory, (forward, inverse), rounds) if directory \
            else avalanche.matrices_of(subject.program, rounds, (forward, inverse))
        avalanche.run_flips(subject.loaded, avalanche.bias_states(n), numbers, rows, matrices, nothing, tally, (forward, inverse))
    elif path == RELATED:
        states = instantiation_batch(subject, 0, avalanche.N_A, False)
        matrices = stored_matrices(directory, (forward,), rounds) if directory \
            else avalanche.matrices_of(subject.program, rounds, (forward,))
        avalanche.run_flips(subject.loaded, states, numbers, rows, matrices, nothing, tally, (forward,))
    else:
        avalanche.run_rotations(subject.loaded, avalanche.bias_states(n), (), tally, rows)
    return tally


def avalanche_jobs(subject: Subject, directory: str) -> List[Tuple]:
    flips = avalanche.flip_set(subject.n, subject.w)
    related = list(range(key_bits(subject.c) * 3 // 2))
    jobs = [(FLIPS, flips[at:at + FLIP_CHUNK]) for at in range(0, len(flips), FLIP_CHUNK)]
    jobs += [(RELATED, related[at:at + FLIP_CHUNK]) for at in range(0, len(related), FLIP_CHUNK)]
    jobs += [(ROTATIONS, list(range(1, subject.w)))]
    return [(subject, path, numbers, part, directory) for part, (path, numbers) in enumerate(jobs)]


def merged_paths(results: Sequence[Dict], rounds: int) -> Dict[str, Dict]:
    """One row per path, in the order of `results`, each round's least and largest count over its parts."""
    out: Dict[str, Dict] = {}
    for result in results:
        summary = result["summary"]
        row = out.setdefault(result["path"], {
            "tests": 0, "expected_bits_that_did_not_fire": 0, "other_firings_by_round": [0] * rounds, "fired_by_round": [0] * rounds,
            "first": [[avalanche.N_FIRST, 0] for _ in range(rounds)], "whole": [[avalanche.N_A, 0] for _ in range(rounds)]})
        row["tests"] += summary["tests"]
        row["expected_bits_that_did_not_fire"] += summary["expected_bits_that_did_not_fire"]
        for r in range(rounds):
            row["other_firings_by_round"][r] += summary["other_firings_by_round"][r]
            row["fired_by_round"][r] += result["fired"][r]
            for name in ("first", "whole"):
                row[name][r] = [min(row[name][r][0], result["counts"][name][r][0]), max(row[name][r][1], result["counts"][name][r][1])]
    return out


def adopted_parts(run: evidence.Run, results: Sequence[Dict], directory: Path) -> List[Dict]:
    return [cite(run.adopt(result["part"]["file"], directory / result["part"]["file"], result["part"])) for result in results]


def dependency_cited(candidate: str, n: int) -> Optional[str]:
    """The finished `dependency` record of the candidate at that size, the latest."""
    found = [record for _, record in evidence.iter_records("dependency", f"candidates/{candidate}")
             if record.get("config", {}).get("size") == n and evidence.is_finished(record)]
    return max(found, key=lambda record: record["created_utc"])["record_id"] if found else None


def run_avalanche(subject: Subject, run: evidence.Run, cited: Optional[str] = None) -> Dict:
    n, w, rounds = subject.n, subject.w, subject.rounds
    cited = cited or dependency_cited(subject.candidate, n)
    if cited is None:
        raise Refused(f"an avalanche run needs the candidate's dependency record at {n}×{n}")
    first, whole = bias_entries(n)
    run.tmp.mkdir(parents=True, exist_ok=True)
    directory = run.tmp / "workers"
    store_matrices(subject, directory)
    try:
        results = worker_map(avalanche_worker, avalanche_jobs(subject, str(directory)), run.workers)
    except ToolFailure as exc:
        if DISAGREEMENT not in str(exc):
            raise
        return {"status": "inconclusive", "classification": NONE, "exit_status": evidence.EXIT_TOOL,
                "inputs": state_inputs(n, w, avalanche.N_A),
                "fields": {"tool_defect": {"kind": "a disagreement between avalanche counts and dependency matrices", "evidence": str(exc)},
                           "dependency": cited, "disagreements": 1, "exclusions_and_reruns": exclusions_field(run),
                           "constants": table_field(subject)}}
    paths = merged_paths(results, rounds)
    fired = evidence.avalanche_rounds_fired(paths, (first["low"], first["high"]), (whole["low"], whole["high"]))
    status, outcome, raises = evidence.verdict_bias(fired, rounds)
    small = [smallest_p(np.array([(avalanche.N_A + max(result["farthest"][r] for result in results)) // 2]), avalanche.N_A)
             for r in range(rounds)]
    chance = stated_chance(subject.candidate, "avalanche", subject)
    located = [item for result in results for item in result["located"]]
    fields = {"sample_size": {"n_a": avalanche.N_A, "n_first": avalanche.N_FIRST, "flips": len(avalanche.flip_set(n, w)),
                              "related_bits": avalanche.RELATED_BITS, "rotations": w - 1},
              "test_parameters": {"s_a": avalanche.s_a(n), "threshold": "0.005/(128·S_A)", "critical_first": [first["low"], first["high"]],
                                  "critical_whole": [whole["low"], whole["high"]], "table": {
                                      "path": bias.TABLE_REL, "sha256": evidence.sha256(evidence.REPO.path(bias.TABLE_REL).read_bytes()),
                                      "sha256_kind": "raw"}},
              "raw_counts": adopted_parts(run, results, directory),
              "p_values": cite(run.output("p-values.json.gz", json_bytes(small), deterministic=False, compared="values")),
              "failure_locations": kept_output(run, "failure-locations.json.gz", located), "paths": paths, "rounds_fired": fired,
              "raises": raises, "dependency": cited, "disagreements": 0, "exclusions_and_reruns": exclusions_field(run),
              "scope": BIAS_SCOPE, "constants": table_field(subject)}
    return finding_result(status, "avalanche", outcome, fields, {
        "sets": [state_inputs(n, w, avalanche.N_A), "the first 8,256 instantiation states"]},
        f"fires at round counts {fired}, a chance of a false firing of {chance:.4f}" if fired else NONE)


# ---------------------------------------------------------------------------------- trail bounds

def tool_hash(tool: str) -> Tuple[str, Optional[str]]:
    source = evidence.sha256(evidence.REPO.path(TRAIL_PATHS[tool]).read_bytes())
    if tool != "ARX search":
        return source, None
    return source, evidence.sha256(evidence.REPO.path(ARX_BINARY).read_bytes())


def boxes_of(candidate: str, w: int, assignment: Optional[Sequence] = None) -> Tuple[Tuple[Tuple, ...], ...]:
    """Each distinct box of an ARX candidate, as the search takes it."""
    module = amounts_module(candidate)
    chosen = module.AMOUNTS if assignment is None else assignment
    return tuple(dict.fromkeys(module.box_steps(index, w, chosen) for index in range(len(chosen))))


def box_bounds(candidate: str, kind: str, w: int, rounds: int) -> Dict:
    """Each distinct box's optimal weights over 1 to `rounds` rounds of the box, the search's."""
    found = {}
    for index, steps in enumerate(boxes_of(candidate, w)):
        result = arx_search_known.search(kind, w, rounds, steps)
        found[f"box {index}"] = {"steps": [list(step) for step in steps],
                                 "weights": {str(r): item["weight"] for r, item in result.items()},
                                 "walks": {str(r): item["walks"] for r, item in result.items()}}
    return found


def rational(weight: Fraction) -> str:
    """A multiple of 2⁻¹⁶, rounded down, as data-model section 6 asks."""
    return f"{math.floor(weight * 65536)}/65536"


def reached_cap(exc: ToolFailure) -> bool:
    """Whether a tool stopped at the search instance's 8 h, which gives no bound and is no defect (research R7)."""
    text = str(exc)
    return any(words in text for words in ("8 h cap", "no time left", " status 1,", " status 1 with"))


def box_method(subject: Subject, kind: str, rounds: int, args: argparse.Namespace) -> Dict:
    found = box_bounds(subject.candidate, kind, subject.w, rounds)
    least = min(row["weights"][str(rounds)] for row in found.values())
    return {"bound": rational(Fraction(2 * least if kind == "linear" else least)), "boxes": found, "solver": NONE,
            "weight_kept": "a linear weight is twice the search's correlation exponent, the squared correlation's (spec FR-022)"}


def coupling(program: "ir.Program") -> List[Dict[Tuple[int, int], set]]:
    """Each phase that reads another node: the other nodes each node it writes reads."""
    phases = []
    for phase in program.phases:
        reads: Dict[Tuple[int, int], set] = {}
        for update in phase.updates:
            node = ir.node_of(program.n, update.dst)
            for lane in ir.reads(update):
                other = ir.node_of(program.n, lane)
                if other != node:
                    reads.setdefault(node, set()).add(other)
        if reads:
            phases.append(reads)
    return phases


def branch_layer(program: "ir.Program", kind: str) -> "long_trail.Local":
    """The layer between boxes, read from the list: a node is a branch, and each phase that reads other nodes gives each node it
    writes one output, a sum of bijections of its neighbours' branches. For masks, by the transpose of the inverse, a phase's sources
    gain from the nodes that read them. A branch a phase changed is read, in a later phase, as the next step has it."""
    n = program.n

    def index(node: Tuple[int, int]) -> int:
        return n * node[0] + node[1]

    maps: List = []
    added: List[Optional[int]] = [None] * (n * n)
    changed: set = set()
    for reads in coupling(program):
        if kind == "linear":
            turned: Dict[Tuple[int, int], set] = {}
            for node, others in reads.items():
                for other in others:
                    turned.setdefault(other, set()).add(node)
            reads = turned
        for node in sorted(reads):
            if added[index(node)] is not None:
                raise ToolFailure(f"node {node} gains twice in one layer: the counter's layer gives a branch one output")
            added[index(node)] = len(maps)
            inputs = tuple((1 if other in changed else 0, index(other)) for other in sorted(reads[node]))
            maps.append((inputs, long_trail.xor_relation(len(inputs))))
        changed |= set(reads)
    return long_trail.check(long_trail.Local(n * n, tuple(range(n * n)), tuple(added), tuple(maps)))


def box_costs(candidate: str, kind: str, w: int) -> Tuple[Tuple[int, ...], str]:
    """The smallest of the K boxes' bounds at each number of steps, the latest box record's, in weights of probability or of squared
    correlation, whose exponent a linear search gives (spec FR-022)."""
    found = None
    for _, record in evidence.iter_records("bound", f"candidates/{candidate}"):
        if record.get("method") == "branch-and-bound" and record.get("bound_kind") == kind and record.get("width") == w \
                and record.get("status") == "pass" and (found is None or record["created_utc"] > found["created_utc"]):
            found = record
    if found is None:
        raise Refused(f"{candidate} has no box bound of kind {kind} at w = {w}")
    scale = 2 if kind == "linear" else 1
    steps = found["rounds"]
    return tuple(scale * min(row["weights"][str(t)] for row in found["boxes"].values()) for t in range(1, steps + 1)), \
        found["record_id"]


def active_box_method(subject: Subject, kind: str, rounds: int, args: argparse.Namespace) -> Dict:
    box, source = box_costs(subject.candidate, kind, subject.w)
    layer = branch_layer(subject.program, kind)
    found = long_trail.minima(layer, box, rounds)
    return {"bound": str(found[rounds]["count"]), "counts": long_trail.as_rows(found), "box": list(box), "box_record": source,
            "solver": dict(long_trail.SETTINGS, statement=long_trail.LIMITATION)}


def boolean_layer(candidate: str, n: int, w: int, assignment: Optional[Sequence] = None) -> "active_sbox.Cycle":
    """A Boolean candidate's S-box layers in turn, read from its stated pairs and amounts: bit i of a node's lanes meets bit i - u of its
    partner's. No bit moves, so a layer's permutation is the identity. A pairing of the nodes needs an even n."""
    if n % 2:
        raise Refused("a Boolean candidate's S-boxes partition the state at an even n only")
    module = amounts_module(candidate)
    chosen = module.AMOUNTS if assignment is None else assignment
    bits = 2 * n * n * w

    def bit(node: Tuple[int, int], kind: int, place: int) -> int:
        return ir.lane(n, node[0], node[1], kind) * w + place

    layers = []
    for t in range(len(module.PARTNERS)):
        boxes = []
        for node in ir.nodes_of(n, 0):
            partner = module.partner_of(n, node[0], node[1], t, 0)
            amount = module.amount_of(module.pair_set(n, node, partner), t, w, chosen)
            for place in range(w):
                other = (place - amount) % w
                boxes.append((bit(node, ir.PRESSURE, place), bit(partner, ir.VEIN, other), bit(node, ir.VEIN, place),
                              bit(partner, ir.PRESSURE, other)))
        layers.append(active_sbox.Layer(bits, tuple(boxes), tuple(module.SBOX), tuple(range(bits))))
    return active_sbox.check(active_sbox.Cycle(tuple(layers)))


def sbox_weight(sbox: Sequence[int], kind: str) -> int:
    """The least weight of an active S-box: of its largest difference entry, or of its largest squared correlation."""
    array = np.array(sbox, dtype=np.int64)
    size = len(sbox)
    if kind == "differential":
        largest = max(int(tables.difference_row(array, given).max()) for given in range(1, size))
        return int(math.log2(size / largest))
    largest = max(abs(sum(1 - 2 * (bin((given & x) ^ (taken & int(array[x]))).count("1") & 1) for x in range(size)))
                  for given in range(1, size) for taken in range(size))
    return 2 * int(math.log2(size / largest))


def active_sbox_method(subject: Subject, kind: str, rounds: int, args: argparse.Namespace) -> Dict:
    layer = boolean_layer(subject.candidate, subject.n, subject.w)
    found = active_sbox.minima(layer, kind, rounds)
    weight = sbox_weight(layer.layers[0].sbox, kind)
    count = found[rounds]["count"]
    return {"bound": str(count * weight), "active_sboxes": count, "weight_per_sbox": weight, "counts": active_sbox.as_rows(found),
            "solver": dict(active_sbox.SETTINGS, statement=active_sbox.LIMITATION)}


CROSS_SECONDS = [INSTANCE_HOURS * 3600.0]
METHODS = {"branch-and-bound": {"tool": "ARX search", "run": box_method},
           "active-box count": {"tool": "long-trail active-box counting", "run": active_box_method},
           "active-S-box count": {"tool": "active-S-box counting", "run": active_sbox_method}}


def plain(value: Any) -> Any:
    """Amounts as a record holds them, in lists."""
    return json.loads(json.dumps(value))


def amounts_checked(record: Dict, candidate: str) -> Any:
    """The amounts a cross-check ran on. A record with no `amounts` ran before the field existed, on the first of its candidate's space."""
    return record.get("amounts", plain(space_of(candidate)[0]))


def cross_check_cited(candidate: str, tool: str, width: int) -> Any:
    """A bound from the ARX search or the active-S-box counter cites the cross-check of that candidate and that tool's exact hash. A
    production-width search needs the cross-check of the amounts it runs on, and a reduced-width search comes before they are chosen
    (data-model section 6; research R7)."""
    if tool not in ("ARX search", "active-S-box counting"):
        return NONE
    source, _ = tool_hash(tool)
    held = [record for _, record in evidence.iter_records("cross-check", f"candidates/{candidate}")
            if record.get("tool") == tool and record.get("tool_sha256") == source and record.get("status") == "pass"]
    if width == PRODUCTION_WIDTH:
        stated = plain(amounts_module(candidate).AMOUNTS)
        held = [record for record in held if amounts_checked(record, candidate) == stated]
    return max(held, key=lambda record: record["created_utc"])["record_id"] if held else NONE


def run_bound(subject: Subject, run: evidence.Run, args: argparse.Namespace, tool: str, citation: Optional[Dict], cross: Any) -> Dict:
    kind, method = args.bound_kind, args.method
    n, w, rounds = subject.n, subject.w, args.rounds or 1
    fields: Dict[str, Any] = {"bound_kind": kind, "rounds": rounds, "width": w, "size": n, "method": method, "tool": tool,
                              "validation": citation or NONE, "scope": SCOPE, "cross_check": cross, "bound": NONE}
    if citation is None:
        return {"status": "not evaluated", "classification": NONE, "fields": fields, "inputs": NONE}
    try:
        result = METHODS[method]["run"](subject, kind, rounds, args)
    except ToolFailure as exc:
        if not reached_cap(exc):
            raise
        return {"status": "inconclusive", "classification": NONE, "inputs": NONE,
                "fields": dict(fields, capped=True, cap_reached=str(exc), solver=NONE)}
    fields.update(result)
    return {"status": "pass", "classification": evidence.classify("bound", "established"), "fields": fields, "inputs": NONE,
            "limitations": [WIDTH_LIMITATION] if w >= 16 else []}


class Climb:
    """One search running on, each r's weight kept as the binary prints it, so that a search stopped at the cap keeps what it reached."""

    def __init__(self, kind: str, w: int, steps: Sequence, rounds: int):
        arguments = [arx_search_known.program(), kind, str(w), str(rounds)] + [arx_search_known.step_text(step) for step in steps]
        self.process = subprocess.Popen(arguments, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        self.weights: Dict[int, int] = {}
        self.reader = threading.Thread(target=self.read, daemon=True)
        self.reader.start()

    def read(self) -> None:
        for line in self.process.stdout:
            fields = line.split()
            if fields and fields[0] == "optimal":
                self.weights[int(fields[1])] = int(fields[2])

    def done(self) -> bool:
        return self.process.poll() is not None

    def reached(self) -> int:
        r = 0
        while r + 1 in self.weights:
            r += 1
        return r

    def stop(self) -> None:
        if not self.done():
            self.process.kill()
        self.process.wait()
        self.reader.join()


def cross_tables(job: Tuple) -> Dict:
    """One box's exhaustive values at one width and kind, each r up to the run's: a floor, and at w = 4 the internal-trail search."""
    w, steps, name, rounds = job
    box = tables.box_of(steps, w)
    floor = tables.difference_floor(box, rounds) if name == "differential" else tables.linear_floor(box, rounds)
    exact = None
    if w == 4:
        exact = tables.differential_trails(steps, w, rounds) if name == "differential" else tables.linear_trails(steps, w, rounds)
    return {"floor": floor, "exact": exact}


def table_round_seconds(candidate: str) -> float:
    """The widest box's slowest table over one round, which sets how much of the cap the tables need, the searches having the rest."""
    box = tables.box_of(boxes_of(candidate, CROSS_WIDTHS[-1])[0], CROSS_WIDTHS[-1])
    started = time.monotonic()
    tables.linear_floor(box, 1)
    return time.monotonic() - started


def arx_cross_check(subject: Subject, run: evidence.Run, args: argparse.Namespace) -> Dict:
    """Research R12's two checks on each distinct box. One run of them is one instance, within its 8 h (seq 522): the searches climb
    together, up to the top of their range or until what is left of the cap only just holds the tables to the r they have all reached,
    and the tables then run to that r. The search's value and the exhaustive ones stand beside each other at every r from 1."""
    tool = "ARX search"
    source, binary = tool_hash(tool)
    cap = CROSS_SECONDS[0]
    started = time.monotonic()
    top = min(args.rounds or SEARCH_RANGE, SEARCH_RANGE)
    plan = [(w, index, steps, name) for w in CROSS_WIDTHS for index, steps in enumerate(boxes_of(subject.candidate, w)) for name in long_trail.KINDS]
    per_round = table_round_seconds(subject.candidate)
    climbs = [Climb(name, w, steps, top) for w, _, steps, name in plan]
    try:
        while True:
            reached = min(climb.reached() for climb in climbs)
            left = cap - (time.monotonic() - started)
            if reached >= top or all(climb.done() for climb in climbs) or left <= per_round * (reached + 1) * CAP_MARGIN:
                break
            time.sleep(POLL_SECONDS)
    finally:
        for climb in climbs:
            climb.stop()
    failed = [climb.process.returncode for climb in climbs if climb.process.returncode not in (0, -9, 1, 137)]
    if failed:
        raise ToolFailure(f"arx_search exited {failed[0]}")
    fields = {"tool": tool, "tool_sha256": source, "binary_sha256": binary, "rounds": reached, "cap_hours": cap / 3600.0,
              "amounts": plain(amounts_module(subject.candidate).AMOUNTS),
              "reached": {f"box {index} at w = {w}, {name}": climb.reached() for (w, index, _, name), climb in zip(plan, climbs)}}
    if reached < 1:
        return {"status": "inconclusive", "classification": NONE, "inputs": NONE, "fields": dict(fields, capped=True, rows=[])}
    held = worker_map(cross_tables, [(w, steps, name, reached) for w, _, steps, name in plan], run.workers)
    rows: List[Dict] = []
    for (w, index, _, name), climb, table in zip(plan, climbs, held):
        scale = 2 if name == "linear" else 1
        for r in range(1, reached + 1):
            weight, exact = climb.weights[r], None if table["exact"] is None else table["exact"][r]
            rows.append({"box": index, "width": w, "kind": name, "r": r, "search": weight, "floor_units": table["floor"][r], "exhaustive": exact,
                         "equal": None if exact is None else exact == weight, "above_floor": weight * scale * tables.UNITS >= table["floor"][r]})
    return {"status": evidence.verdict_cross_check(rows), "classification": NONE, "inputs": NONE, "fields": dict(fields, rows=rows)}


def deliver(function: Callable, job: Any, out: Any) -> None:
    try:
        out.put(("done", function(job)))
    except Exception as exc:  # noqa: BLE001
        out.put(("failed", f"{type(exc).__name__}: {exc}"))


def limited(function: Callable, job: Any, seconds: float) -> Any:
    """A result in a process of its own, or None where it does not finish in time: the process is stopped there."""
    context = multiprocessing.get_context("spawn" if os.name == "nt" else "fork")
    out = context.Queue()
    process = context.Process(target=deliver, args=(function, job, out))
    process.start()
    try:
        state, value = out.get(timeout=max(0.0, seconds))
    except queue.Empty:
        return None
    finally:
        process.terminate()
        process.join()
    if state == "failed":
        raise ToolFailure(value)
    return value


def boolean_round(job: Tuple) -> List[Dict]:
    """One r: the counter's minimum and the exhaustive minimum, in both kinds."""
    root, candidate, r = job
    evidence.use_repo(Path(root))
    layer = boolean_layer(candidate, 4, 4)
    pairs = [(item.boxes, item.permutation) for item in layer.layers]
    rows = []
    for kind in long_trail.KINDS:
        counted, exact = active_sbox.minima(layer, kind, r)[r]["count"], tables.layers_minimum(layer.layers[0].sbox, pairs, kind, r)[r]
        rows.append({"kind": kind, "r": r, "counter": counted, "exhaustive": exact, "equal": counted == exact})
    return rows


def boolean_cross_check(subject: Subject, args: argparse.Namespace) -> Dict:
    """The counter's minimum over r rounds at 4×4 equals the exhaustive minimum from the candidate's own layers at w = 4, every trail
    walked, for each r up to the largest that finishes within one run's 8 h (research R12; seq 522)."""
    tool = "active-S-box counting"
    source, _ = tool_hash(tool)
    cap = CROSS_SECONDS[0]
    started = time.monotonic()
    rows: List[Dict] = []
    r = 0
    while r < (args.rounds or SEARCH_RANGE):
        found = limited(boolean_round, (str(evidence.REPO.root), subject.candidate, r + 1), cap - (time.monotonic() - started))
        if found is None:
            break
        rows += found
        r += 1
    fields = {"tool": tool, "tool_sha256": source, "rows": rows, "rounds": r, "cap_hours": cap / 3600.0,
              "amounts": plain(amounts_module(subject.candidate).AMOUNTS)}
    if r < 1:
        return {"status": "inconclusive", "classification": NONE, "inputs": NONE, "fields": dict(fields, capped=True)}
    return {"status": evidence.verdict_cross_check(rows), "classification": NONE, "inputs": NONE, "fields": fields}


def run_cross_check(subject: Subject, run: evidence.Run, args: argparse.Namespace) -> Dict:
    """Research R12's checks on a candidate's own boxes or layers."""
    if args.tool == "active-S-box counting":
        return boolean_cross_check(subject, args)
    if args.tool != "ARX search":
        raise Refused(f"research R12 asks for no cross-check of {args.tool}")
    return arx_cross_check(subject, run, args)


# ------------------------------------------------------------------------------- the rotation search

def is_arx(candidate: str) -> bool:
    return hasattr(amounts_module(candidate), "box_steps")


def space_of(candidate: str) -> List[Tuple]:
    """Every assignment of the recorded space, in the tie order of the ranking entry (seq 520)."""
    module = amounts_module(candidate)
    numbers = list(module.GENERATORS)
    if is_arx(candidate):
        sets = [(g, h) for g in numbers for h in numbers]
        return [(first, second) for first in sets for second in sets if first != second]
    return [(g, numbers[(at + 1) % len(numbers)]) for at, g in enumerate(numbers)]


def one_call(job: Tuple) -> Dict[str, Optional[int]]:
    """One set's box over one call, in both kinds, the linear weight twice the search's exponent: None for a search at its cap."""
    root, candidate, w, chosen = job
    evidence.use_repo(Path(root))
    steps = amounts_module(candidate).box_steps(0, w, (chosen,))
    found: Dict[str, Optional[int]] = {}
    for kind in long_trail.KINDS:
        try:
            weight = arx_search_known.search(kind, w, 1, steps)[1]["weight"]
        except ToolFailure as exc:
            if not reached_cap(exc):
                raise
            weight = None
        found[kind] = None if weight is None else (2 * weight if kind == "linear" else weight)
    return found


def arx_ranking(subject: Subject, run: evidence.Run) -> Dict:
    """Each set's box searched over one call, and each assignment at the count of its weakest box in each kind (seq 520)."""
    candidate, w = subject.candidate, subject.w
    assignments = space_of(candidate)
    sets = sorted({chosen for assignment in assignments for chosen in assignment})
    root = str(evidence.REPO.root)
    found = dict(zip(sets, worker_map(one_call, [(root, candidate, w, chosen) for chosen in sets], run.workers)))
    layers = {kind: branch_layer(subject.program, kind) for kind in long_trail.KINDS}
    counts: Dict[Tuple[str, int], Dict] = {}

    def weight(kind: str, assignment: Tuple) -> Optional[int]:
        values = [found[chosen][kind] for chosen in assignment]
        if None in values:
            return None
        key = (kind, min(values))
        if key not in counts:
            counts[key] = long_trail.minima(layers[kind], (min(values),), RANK_ROUNDS)[RANK_ROUNDS]
        return counts[key]["count"]

    entries = []
    for assignment in assignments:
        w_d, w_l = weight("differential", assignment), weight("linear", assignment)
        entries.append({"assignment": [list(chosen) for chosen in assignment], "W_D": w_d, "W_L": w_l,
                        "measure": None if w_d is None or w_l is None else min(w_d, w_l)})
    return {"sets": {f"{g},{h}": found[(g, h)] for g, h in sets}, "entries": evidence.ranked(entries),
            "counts": {f"{kind}, box {value}": row for (kind, value), row in sorted(counts.items())},
            "solver": dict(long_trail.SETTINGS, statement=long_trail.LIMITATION)}


def boolean_point(job: Tuple) -> Optional[int]:
    """One assignment's weight in one kind, the count over the ranking's rounds times an active S-box's weight: None at the cap."""
    root, candidate, n, w, assignment, kind = job
    evidence.use_repo(Path(root))
    layer = boolean_layer(candidate, n, w, assignment)
    try:
        return active_sbox.minima(layer, kind, RANK_ROUNDS)[RANK_ROUNDS]["count"] * sbox_weight(layer.layers[0].sbox, kind)
    except ToolFailure as exc:
        if not reached_cap(exc):
            raise
        return None


def boolean_ranking(subject: Subject, run: evidence.Run) -> Dict:
    root = str(evidence.REPO.root)
    assignments = space_of(subject.candidate)
    jobs = [(root, subject.candidate, subject.n, subject.w, assignment, kind) for assignment in assignments for kind in long_trail.KINDS]
    held = worker_map(boolean_point, jobs, run.workers)
    entries = []
    for at, assignment in enumerate(assignments):
        w_d, w_l = held[2 * at], held[2 * at + 1]
        entries.append({"assignment": list(assignment), "W_D": w_d, "W_L": w_l,
                        "measure": None if w_d is None or w_l is None else min(w_d, w_l)})
    return {"sets": {}, "entries": evidence.ranked(entries), "solver": dict(active_sbox.SETTINGS, statement=active_sbox.LIMITATION)}


def ranking_tools(candidate: str) -> List[str]:
    return ["ARX search", "long-trail active-box counting"] if is_arx(candidate) else ["active-S-box counting"]


def run_ranking(subject: Subject, run: evidence.Run, cross: Any, citations: Dict) -> Dict:
    found = arx_ranking(subject, run) if is_arx(subject.candidate) else boolean_ranking(subject, run)
    top = found["entries"][0]
    fields = dict(found, size=subject.n, width=subject.w, rounds=RANK_ROUNDS, measure=MEASURE, tie_order=TIE_ORDER, tool=ranking_tools(subject.candidate),
                  validation=citations, cross_check=cross, chosen=NONE if top["measure"] is None else top["assignment"],
                  budget={"cap_hours": INSTANCE_HOURS, "hours_used": (time.monotonic() - run.clock) / 3600.0})
    return {"status": "pass" if top["measure"] is not None else "inconclusive", "classification": NONE, "fields": fields, "inputs": NONE}


def run_rotation(args: argparse.Namespace, command: List[str], code: List[str], row: str) -> int:
    """The search of research R15 over the recorded space, at the width of --width, 16 first (seq 520, 521)."""
    candidate, n, w = args.candidate, RANK_SIZE, args.width or 16
    if args.size not in (None, RANK_SIZE):
        raise Refused("the ranking stands at 4×4")
    tools = ranking_tools(candidate)
    if tools[0] == "ARX search":
        code = code + [TRAIL_PATHS["ARX search"], ARX_BINARY, ARX_MAKE]
    citations = {}
    for tool in tools:
        source, binary = tool_hash(tool)
        evidence.guard_trail_tools(tool, source, binary)
        citations[tool] = evidence.validation_citation(tool, source, binary)
        if citations[tool] is None:
            raise Refused(f"the ranking needs a validated tool: {tool} has no re-found record of its exact hash")
    cross = cross_check_cited(candidate, tools[0], w)
    if cross == NONE and not args.project:
        raise Refused(f"{tools[0]}'s results on {candidate} count once its cross-check has passed (research R12)")
    subject = plain_subject(candidate, n, w, RANK_ROUNDS)
    started = time.monotonic()
    seconds = ranking_seconds(subject, tools, args.workers)
    extra = {"probe": dict(probe_of("rotation-ranking", n), width=w, bound_kind=NONE, method=NONE)}
    path = evidence.write_projection(run=f"rotation search of {candidate} at w = {w}", row=f"{candidate}/{row}", inputs=NONE,
                                     measured_speed={"seconds_of_the_run": seconds, "workers": args.workers}, projected_hours=seconds / 3600.0,
                                     time_hours=(time.monotonic() - started) / 3600.0, argv=command, code_files=code, extra=extra)
    hours = seconds / 3600.0
    if args.project:
        print(f"{evidence.rel_to_repo(path)}: {hours:.3f} h projected")
        return evidence.EXIT_OK
    evidence.guard_candidate_row(candidate, row, hours, reserved_trails(candidate, extra["probe"]))
    run = evidence.Run("rotation-ranking", candidate=candidate, model_id=candidate, variant_id=subject.variant_id, code_files=code, argv=command,
                       heavy=True, projected_hours=hours, workers=args.workers, namespace="dev", config={"size": n, "width": w, "rounds": RANK_ROUNDS})
    run.extra["exclusions_and_reruns"] = repeats(candidate, "rotation-ranking", lambda record: record.get("width") == w)
    return carried_out(run, candidate, row, hours, lambda: run_ranking(subject, run, cross, citations))


RUNS = {"inverse": run_inverse, "bijectivity": run_bijectivity, "dependency": run_dependency, "symmetry": run_symmetry,
        "invariant": run_invariant, "degree": run_degree, "frequency": run_frequency, "avalanche": run_avalanche}


# ---------------------------------------------------------------------------------- projections

def probe_of(kind: str, size: int, test: Optional[str] = None) -> Dict:
    return {"kind": kind, "size": size, "test": test or NONE}


def latest_probe(candidate: str, row: str, kind: str, size: int) -> Optional[Dict]:
    held = [record for _, record in evidence.iter_records("projection", "projections")
            if record.get("row") == f"{candidate}/{row}" and record.get("probe") == probe_of(kind, size)]
    return max(held, key=lambda record: record["created_utc"]) if held else None


def run_finished(candidate: str, kind: str, size: int) -> bool:
    return any(record.get("config", {}).get("size") == size and evidence.is_finished(record)
               for _, record in evidence.iter_records(kind, f"candidates/{candidate}"))


def needed_after(row: str, kind: str, size: int) -> List[Tuple[str, int]]:
    """The runs the row still needs beside this one: its own kind at every larger claimable size, and every other kind of the row at
    every claimable size, the exhaustive bijectivity at its one size (research R7)."""
    out = []
    for other in ROW_ORDER.get(row, ()):
        sizes = (2,) if other == "bijectivity" else evidence.CLAIMABLE_SIZES
        for at in sizes:
            if other == kind and (at == size or size == 2 or at < size):
                continue
            out.append((other, at))
    return out


def reserved_hours(candidate: str, row: str, kind: str, size: int) -> float:
    """The probes of every run the row still needs. A probe that does not exist comes first, its time counted against the row. The
    trail row's later runs depend on the amounts chosen, so its reservation counts the probes that exist."""
    total = 0.0
    for other, at in needed_after(row, kind, size):
        if run_finished(candidate, other, at):
            continue
        probe = latest_probe(candidate, row, other, at)
        if probe is None:
            raise Refused(f"the probe of {other} at {at}×{at} comes first: --project writes it")
        total += float(probe["projected_hours"])
    if row == "statistics":
        for test in BIAS_KINDS:
            for at in evidence.CLAIMABLE_SIZES:
                if control_held(test, at) is None:
                    total += control_projection(test, at)
    return total


def control_projection(test: str, size: int) -> float:
    held = [record for _, record in evidence.iter_records("projection", "projections")
            if record.get("row") == evidence.FEATURE_ROW and record.get("probe") == probe_of("control", size, test)]
    return float(max(held, key=lambda record: record["created_utc"])["projected_hours"]) if held else 0.0


def scaled_time(step: Callable[[], Any], scale: float) -> float:
    started = time.perf_counter()
    step()
    return (time.perf_counter() - started) * scale


def probe_seconds(kind: str, subject: Subject, workers: int) -> float:
    """At most a minute of the run's own work on its first inputs, scaled up to the run's counts (research R7). Each output of it is
    discarded unread."""
    n, w = subject.n, subject.w
    if kind == "frequency":
        return scaled_time(lambda: frequency_worker((subject, 0, PROBE_INPUTS, False)), 2.0 * FREQUENCY_N / PROBE_INPUTS / max(1, workers))
    if kind == "avalanche":
        flips = len(avalanche.flip_set(n, w))
        turns = (flips + avalanche.RELATED_BITS / 2.0 + w - 1) / max(1, workers)
        return scaled_time(lambda: avalanche_part(subject, FLIPS, avalanche.flip_set(n, w)[:1], None, ""), turns)
    if kind == "bijectivity":
        return bijectivity.time_batches(lambda states: ir.permute_batch(subject.loaded, states, subject.table)) \
            * 2 ** 32 / bijectivity.BATCH
    if kind == "inverse":
        states = invariants.test_states(n, w, FIXED_STATES)
        return scaled_time(lambda: ir.permute_batch_inverse(subject.loaded, ir.permute_batch(subject.loaded, states, subject.table),
                                                            subject.table), 2.0 * (TEST_STATES + FIXED_STATES) / FIXED_STATES)
    if kind == "invariant":
        states = invariants.test_states(n, w, FIXED_STATES)
        return scaled_time(lambda: invariants.check(subject.loaded, states, subject.table, (1,)),
                           (1.0 + subject.rounds) * TEST_STATES / FIXED_STATES)
    if kind == "symmetry":
        return scaled_time(lambda: symmetry.check(subject.program, subject.table[:1]), float(subject.rounds))
    if kind == "dependency":
        program = subject.program
        return scaled_time(lambda: dependency.first_full(program, dependency.FORWARD, 1), 2.0 * 3 * n)
    return scaled_time(lambda: degree.record_fields(subject.program, [1]), 8.0)


def write_probe(kind: str, subject: Subject, candidate: str, row: str, seconds: float, workers: int, command: List[str],
                code: List[str], started: float, test: Optional[str] = None) -> Path:
    return evidence.write_projection(
        run=f"{kind} of {candidate} at {subject.n}×{subject.n}, w = {subject.w}", row=f"{candidate}/{row}",
        inputs="the first inputs of the run it projects", measured_speed={"seconds_of_the_run": seconds, "workers": workers},
        projected_hours=seconds / 3600.0, time_hours=(time.monotonic() - started) / 3600.0, argv=command, code_files=code,
        extra={"probe": probe_of(kind, subject.n, test)})


# --------------------------------------------------------------------------------- the run itself

def append_evidence(candidate: str, path: Path, row: str, hours: float) -> Dict:
    record = json.loads(path.read_bytes().decode("utf-8"))
    return candidates.append({"candidate_id": candidate, "event": "evidence", "evidence": [record["record_id"]],
                              "budget_used_h": {row: hours}})


def finish(run: evidence.Run, result: Dict, candidate: Optional[str]) -> Path:
    fields = dict(result["fields"], candidate=candidate)
    run.inputs = result["inputs"]
    return run.finish(result["status"], fields=fields, classification=result["classification"], exit_status=exit_of(result),
                      limitations=result.get("limitations", ()))


def exit_of(result: Dict) -> int:
    return result.get("exit_status", evidence.EXIT_VERDICT if result["status"] == "fail" else evidence.EXIT_OK)


def defect_note(record_id: str) -> Optional[Dict]:
    path = evidence.REPO.path(f"{DEFECTS_REL}/{record_id}.json")
    return json.loads(path.read_bytes().decode("utf-8")) if path.exists() else None


def repeats(candidate: str, kind: str, same: Callable[[Dict], bool]) -> List[Dict]:
    """A run made again names what it makes again: a run ended from outside, or one with a recorded tool defect, the one re-run of its
    kind per candidate across all sizes (research R7)."""
    held = [record for _, record in evidence.iter_records(kind, f"candidates/{candidate}")]
    spent = any(item.get("why") == "tool defect" for record in held for item in record.get("exclusions_and_reruns") or ())
    out = []
    for record in held:
        if not same(record):
            continue
        if record.get("ended_outside", NONE) != NONE:
            out.append({"record_id": record["record_id"], "why": "ended from outside"})
            continue
        if any(item.get("record_id") == record["record_id"] for later in held for item in later.get("exclusions_and_reruns") or ()):
            continue
        note = defect_note(record["record_id"])
        if note is None:
            raise Refused(f"{record['record_id']} has this run's result: a run is made again only after a recorded tool defect")
        if spent:
            raise Refused(f"the one re-run of {kind} for {candidate} is spent")
        out.append({"record_id": record["record_id"], "why": "tool defect", "defect": note})
    return out


def guard_control(candidate: str, kind: str, n: int) -> None:
    """No test of a kind starts at a size before its control has run there, and nothing follows a control that fired or one that the
    candidate's row could not hold (research R4, R7)."""
    held = control_held(kind, n)
    if held is None or held.get("ended_outside", NONE) != NONE:
        raise Refused(f"the {kind} test at {n}×{n} waits for its uniform control")
    if held.get("fires"):
        raise Refused(f"the {kind} control at {n}×{n} fired: that size's bias evidence is inconclusive for every candidate")
    if candidate in held.get("not_charged", ()):
        raise Refused(f"{candidate}'s row could not hold the {kind} control at {n}×{n}: it takes no test of that kind there")


def not_evaluated(kind: str) -> Dict:
    return {"status": "not evaluated", "classification": NONE, "fields": {"validation": NONE}, "inputs": NONE}


def run_candidate(args: argparse.Namespace, command: List[str]) -> int:
    kind, candidate = args.kind, args.candidate
    guard_candidate(candidate)
    row = ROWS[kind]
    code = CODE + [module_rel(candidate)]
    if kind in TRAIL_KINDS:
        return run_trail_kind(args, command, code, row)
    if args.size is None:
        raise Refused("a run names --size")
    n, w = args.size, args.width or 32
    if kind in BIAS_KINDS:
        evidence.guard_order_of_us1()
    evidence.guard_order_of_sizes(candidate, kind, n, args.project)
    if kind in NO_TABLE:
        subject = plain_subject(candidate, n, w, args.rounds or 0)
    else:
        subject = subject_of(candidate, n, w, args.rounds or latest_rounds(candidate, n, w))
    workers = args.workers if kind in BIAS_KINDS else 1
    if not args.project:
        if kind in BIAS_KINDS:
            guard_control(candidate, kind, n)
        if kind == "avalanche" and dependency_cited(candidate, n) is None:
            raise Refused(f"an avalanche run needs the candidate's dependency record at {n}×{n}")
    started = time.monotonic()
    seconds = probe_seconds(kind, subject, workers)
    path = write_probe(kind, subject, candidate, row, seconds, workers, command, code, started)
    hours = seconds / 3600.0
    left = evidence.row_hours(candidate, row) - evidence.candidate_row_used(candidate, row)
    if args.project:
        print(f"{evidence.rel_to_repo(path)}: {hours:.3f} h projected, {left:.3f} h left")
        return evidence.EXIT_OK
    evidence.guard_candidate_row(candidate, row, hours, reserved_hours(candidate, row, kind, n))
    again = repeats(candidate, kind, lambda record: record.get("variant_id") == subject.variant_id)
    cited = [subject.table_rel] if subject.table_rel else []
    run = evidence.Run(kind, candidate=candidate, model_id=candidate, variant_id=subject.variant_id, code_files=code, argv=command,
                       heavy=True, projected_hours=hours, workers=workers, namespace="dev",
                       config={"size": n, "width": w, "rounds": subject.rounds}, cited=cited)
    run.extra["exclusions_and_reruns"] = again
    return carried_out(run, candidate, row, hours, lambda: measured(kind, subject, run))


def measured(kind: str, subject: Subject, run: evidence.Run) -> Dict:
    """A kind's run, or `not evaluated` for a tool without a validation of its exact hash and width."""
    citation = citation_of(kind, subject.w)
    if citation is None:
        return not_evaluated(kind)
    result = RUNS[kind](subject, run)
    result["fields"]["validation"] = citation
    return result


def carried_out(run: evidence.Run, candidate: str, row: str, hours: float, work: Callable[[], Dict]) -> int:
    """The run inside its lock, and its `evidence` entry, an aborted run's included, so that its hours are charged."""
    try:
        with run:
            run.begin(hours)
            result = work()
            path = finish(run, result, candidate)
    except Exception:
        if run.record_path is not None:
            append_evidence(candidate, run.record_path, row, evidence.run_hours_used(json.loads(run.record_path.read_bytes().decode("utf-8"))))
        raise
    append_evidence(candidate, path, row, evidence.run_hours_used(json.loads(path.read_bytes().decode("utf-8"))))
    print(f"{evidence.rel_to_repo(path)}: {result['status']}")
    return exit_of(result)


def trail_seconds(subject: Subject, args: argparse.Namespace, tool: str, rounds: int) -> float:
    """A timing of one instance's first round within a minute in all (research R7), scaled by a stated ratio per further round, a search
    of two box calls or more projecting its cap, and the cap above it all. A box search shares the minute among its boxes, and a count
    is count_seconds's."""
    cap = INSTANCE_HOURS * 3600.0
    if tool == "ARX search":
        boxes = len(boxes_of(subject.candidate, subject.w))
        if rounds > 1:
            return cap * boxes
        saved = arx_search_known.INSTANCE_SECONDS
        arx_search_known.INSTANCE_SECONDS = PROBE_SECONDS / boxes
        started = time.monotonic()
        try:
            box_bounds(subject.candidate, args.bound_kind or "differential", subject.w, 1)
        except ToolFailure as exc:
            if not reached_cap(exc):
                raise
            return cap
        finally:
            arx_search_known.INSTANCE_SECONDS = saved
        return time.monotonic() - started
    seconds = count_seconds(subject, args, tool)
    return min(cap, seconds * RATIO_OF_A_ROUND ** (rounds - 1))


def state_bits(n: int, w: int) -> int:
    return 2 * n * n * w


def count_probe(job: Tuple) -> float:
    """One r = 1 count of a candidate's own layers, in a process of its own, timed there. What it found is discarded unread."""
    root, candidate, n, w, kind = job
    evidence.use_repo(Path(root))
    started = time.monotonic()
    active_sbox.minima(boolean_layer(candidate, n, w), kind, 1)
    return time.monotonic() - started


def count_seconds(subject: Subject, args: argparse.Namespace, tool: str) -> float:
    """A minute in all (research R7), which the solver's own limit does not hold, so that an S-box count's states are timed from the
    smallest up, each in what is left of the minute and stopped there. The largest that finished is scaled by the state's bits, and
    the cap stands where none did."""
    started = time.monotonic()
    if tool != "active-S-box counting":
        try:
            with solver_minute(tool):
                probe_count(subject, args, tool)
        except ToolFailure as exc:
            if not reached_cap(exc):
                raise
            return INSTANCE_HOURS * 3600.0
        return time.monotonic() - started
    timed = None
    for n, w in sorted(set(SMALLEST_STATES) | {(subject.n, subject.w)}, key=lambda state: state_bits(*state)):
        left = PROBE_SECONDS - (time.monotonic() - started)
        seconds = limited(count_probe, (str(evidence.REPO.root), subject.candidate, n, w, args.bound_kind or "differential"), left) \
            if left > 0 else None
        if seconds is None:
            break
        timed = seconds, state_bits(n, w)
    if timed is None:
        return INSTANCE_HOURS * 3600.0
    return timed[0] * (state_bits(subject.n, subject.w) / timed[1]) ** BITS_EXPONENT


def ranking_seconds(subject: Subject, tools: Sequence[str], workers: int) -> float:
    """The ranking's hours from one point's first search, each search an instance of R7's."""
    points = len(space_of(subject.candidate))
    args = argparse.Namespace(bound_kind="differential")
    if tools[0] == "ARX search":
        return trail_seconds(subject, args, tools[0], 1) * 64 * 2 / max(1, workers)
    return count_seconds(subject, args, tools[0]) * RANK_ROUNDS * RATIO_OF_A_ROUND * points * 2 / max(1, workers)


class solver_minute:
    """The solver's limit held at a minute for a probe of one instance."""

    def __init__(self, tool: str):
        self.module = long_trail

    def __enter__(self) -> None:
        self.saved = dict(self.module.SETTINGS)
        self.module.SETTINGS["time_limit"] = PROBE_SECONDS

    def __exit__(self, *exc: Any) -> None:
        self.module.SETTINGS.update(self.saved)


def probe_count(subject: Subject, args: argparse.Namespace, tool: str) -> None:
    if tool == "long-trail active-box counting":
        long_trail.minima(branch_layer(subject.program, args.bound_kind or "differential"), (1,), 1)


def later_searches(candidate: str) -> List[Dict]:
    """The production-width searches the trail row still needs, each by what names its probe: the box searches and each count at every
    claimable size, since R_bound comes from a bound computed at that size (research R7, R12)."""
    out = []
    methods = (("branch-and-bound", (RANK_SIZE,)), ("active-box count", evidence.CLAIMABLE_SIZES)) if is_arx(candidate) \
        else (("active-S-box count", evidence.CLAIMABLE_SIZES),)
    for method, sizes in methods:
        for size in sizes:
            for kind in long_trail.KINDS:
                out.append(dict(probe_of("bound", size), width=32, bound_kind=kind, method=method))
    return out


def search_ended(candidate: str, probe: Dict) -> bool:
    return any(record.get("method") == probe["method"] and record.get("bound_kind") == probe["bound_kind"] and record.get("width") == probe["width"]
               and record.get("size") == probe["size"] and (record.get("status") == "pass" or evidence.reached_cap(record))
               for _, record in evidence.iter_records("bound", f"candidates/{candidate}"))


def chosen_cross_checked(candidate: str) -> bool:
    """Whether the cross-check of the chosen amounts stands. Before a ranking names them it cannot, and where the ranking keeps the first
    amounts the first cross-check is that one (research R7)."""
    rankings = [record for _, record in evidence.iter_records("rotation-ranking", f"candidates/{candidate}") if record.get("status") == "pass"]
    if not rankings:
        return False
    chosen = max(rankings, key=lambda record: record["created_utc"])["chosen"]
    tool = ranking_tools(candidate)[0]
    source, _ = tool_hash(tool)
    return any(record.get("tool") == tool and record.get("tool_sha256") == source and record.get("status") == "pass"
               and amounts_checked(record, candidate) == chosen for _, record in evidence.iter_records("cross-check", f"candidates/{candidate}"))


def reserved_trails(candidate: str, this: Dict) -> float:
    """The probes of the searches the row still needs, this run's left out, and the cap of the cross-check of the chosen amounts until it
    stands. A probe that does not exist comes first (research R7)."""
    total = 0.0
    held = [record for _, record in evidence.iter_records("projection", "projections") if record.get("row") == f"{candidate}/trails"]
    for probe in later_searches(candidate):
        if probe == this or search_ended(candidate, probe):
            continue
        found = [record for record in held if record.get("probe") == probe]
        if not found:
            raise Refused(f"the probe of {probe['method']}, {probe['bound_kind']}, at {probe['size']}×{probe['size']} and w = 32 comes first: --project writes it")
        total += float(max(found, key=lambda record: record["created_utc"])["projected_hours"])
    if this.get("kind") != "cross-check" and not chosen_cross_checked(candidate):
        total += INSTANCE_HOURS
    return total


def row_refusal(candidate: str, row: str, hours: float, probe: Dict) -> Optional[str]:
    """Why the row refuses a search, or None. A climb ends at such a refusal, so the search's projection record holds it (research R6); a
    probe that does not exist yet is no refusal of the row, and it raises."""
    reserved = reserved_trails(candidate, probe)
    try:
        evidence.guard_candidate_row(candidate, row, hours, reserved)
    except Refused as exc:
        return str(exc)
    return None


def run_trail_kind(args: argparse.Namespace, command: List[str], code: List[str], row: str) -> int:
    candidate, n, w = args.candidate, args.size or 4, args.width or 16
    if args.kind == "rotation-ranking":
        return run_rotation(args, command, code, row)
    if args.kind == "bound" and (not args.bound_kind or args.method not in METHODS):
        raise Refused("a bound needs --bound-kind differential|linear and a --method the script knows")
    if args.kind == "cross-check" and args.tool not in TRAIL_PATHS:
        raise Refused(f"--tool names one of {tuple(TRAIL_PATHS)}")
    evidence.guard_order_of_sizes(candidate, args.kind, n, args.project)
    tool = METHODS[args.method]["tool"] if args.kind == "bound" else args.tool
    if tool == "ARX search":
        code = code + [TRAIL_PATHS[tool], ARX_BINARY, ARX_MAKE]
    rounds = args.rounds or 1
    if args.method == "branch-and-bound" and w != PRODUCTION_WIDTH and rounds != 1:
        raise Refused("at a reduced width a box's bound is over one call, the ranking's measure (research R6)")
    subject = plain_subject(candidate, n, w, rounds)
    search = {"bound_kind": args.bound_kind, "rounds": rounds, "width": w, "size": n}
    source, binary = tool_hash(tool)
    citation, cross = None, NONE
    if args.kind == "bound":
        evidence.guard_trail_tools(tool, source, binary, candidate, search)
        citation = evidence.validation_citation(tool, source, binary)
        if citation is None:
            raise Refused(f"a bound needs a validated tool: {tool} has no re-found record of its exact hash")
        cross = cross_check_cited(candidate, tool, w)
        if tool in ("ARX search", "active-S-box counting") and cross == NONE and not args.project:
            raise Refused(f"{tool}'s results on {candidate} count once its cross-check has passed (research R12)")
        if w not in MODULES[tool].KIND["widths"]:
            citation = None
    started = time.monotonic()
    seconds = trail_seconds(subject, args, tool, rounds) if args.kind == "bound" else CROSS_SECONDS[0]
    hours = seconds / 3600.0
    extra = {"probe": dict(probe_of(args.kind, n), width=w, bound_kind=args.bound_kind or NONE, method=args.method or NONE), "rounds": rounds}
    refused = None if args.project else row_refusal(candidate, row, hours, extra["probe"])
    if refused is not None:
        extra["refused"] = refused
    path = evidence.write_projection(run=f"{args.kind} of {candidate} at {n}×{n}, w = {w}", row=f"{candidate}/{row}", inputs=NONE,
                                     measured_speed={"seconds_of_the_run": seconds}, projected_hours=hours,
                                     time_hours=(time.monotonic() - started) / 3600.0, argv=command, code_files=code, extra=extra)
    if args.project:
        print(f"{evidence.rel_to_repo(path)}: {hours:.3f} h projected")
        return evidence.EXIT_OK
    if refused is not None:
        raise Refused(refused)

    def same(record: Dict) -> bool:
        if args.kind == "bound":
            return all(record.get(name) == search[name] for name in evidence.SEARCH_FIELDS) and record.get("method") == args.method
        return record.get("tool") == tool and record.get("tool_sha256") == source

    again = repeats(candidate, args.kind, same)
    workers = min(args.workers, 2 * len(CROSS_WIDTHS) * 2) if args.kind == "cross-check" and tool == "ARX search" else 1
    run = evidence.Run(args.kind, candidate=candidate, model_id=candidate, variant_id=subject.variant_id, code_files=code, argv=command,
                       heavy=True, projected_hours=hours, workers=workers, namespace="dev", config={"size": n, "width": w, "rounds": rounds})
    run.extra["exclusions_and_reruns"] = again

    def work() -> Dict:
        if args.kind == "cross-check":
            return run_cross_check(subject, run, args)
        result = run_bound(subject, run, args, tool, citation, cross)
        result["fields"]["budget"] = {"cap_hours": INSTANCE_HOURS, "hours_used": (time.monotonic() - run.clock) / 3600.0}
        return result

    return carried_out(run, candidate, row, hours, work)


# ------------------------------------------------------------- probes for the projection table

PROBE_LIMIT_HOURS = 4.0
PROBE_ROUNDS = 66
PROBE_CAPACITY = 384
PROBE_DESIGNS = {"cand-A1": "ARX", "cand-B1": "Boolean"}
PROBE_GROUPS = {"structural": ("inverse", "dependency", "symmetry", "invariant", "degree"), "bias": ("frequency", "avalanche")}
PROBE_METHODS = {"cand-A1": "active-box count", "cand-B1": "active-S-box count"}
PROBE_SHARE = "probes"
REFERENCE = evidence.FEATURES["004"]
FINISHED, REACHED_LIMIT, PROBE_REFUSED = "finished", "reached the probe limit", "refused"
PROBE_STATEMENT = "every output other than the timing is discarded unread"


class ProbeRun:
    """What a kind's run asks of its Run, for a probe: one worker, a directory of its own, and every output discarded unread."""

    workers = 1

    def __init__(self, tmp: Path):
        self.tmp = tmp
        self.extra: Dict[str, Any] = {"exclusions_and_reruns": []}

    def output(self, name: str, data: bytes, **_: Any) -> Dict:
        return {"path": name, "sha256": NONE, "sha256_kind": "raw"}

    def adopt(self, name: str, path: Path, part: Dict) -> Dict:
        return {"path": name, "sha256": NONE, "sha256_kind": "raw"}


def reference_rel(design: str) -> str:
    return f"{REFERENCE['research']}/candidates/{design}.py"


def guard_reference(design: str) -> Dict:
    """A probe's operation list is a reference design's, committed and as feature 004's candidate log holds it: the list is read and
    never written (feature 005, FR-005; research R5)."""
    if design not in PROBE_DESIGNS:
        raise Refused(f"a probe runs on a reference design, one of {tuple(PROBE_DESIGNS)}")
    rel = reference_rel(design)
    blob = evidence.show(rel)
    if blob is None or evidence.REPO.path(rel).read_bytes() != blob:
        raise Refused(f"{rel} is not committed as it stands")
    digest = evidence.sha256(blob)
    held = [entry for entry, _ in evidence.check_chain(f"{REFERENCE['research']}/candidates.jsonl")
            if entry.get("candidate_id") == design and entry.get("oplist_sha256") == digest]
    if not held:
        raise Refused(f"feature 004's candidate log holds no entry of {design} with the list's SHA-256")
    return {"path": rel, "sha256": digest, "sha256_kind": "raw"}


def reference_module(design: str):
    """A reference design's module, loaded from feature 004's directory under the name its tools look for."""
    name = design.replace("-", "_")
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, evidence.REPO.path(reference_rel(design)))
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]


def probe_subject(design: str, n: int, rounds: int, tmp: Optional[Path]) -> Subject:
    """The reference design at n and w = 32; with `tmp`, its constant table of `rounds` rows by the inherited rule, written there
    for the run to name and never under feature 004's paths."""
    loaded = ir.load(reference_module(design).build(n, PRODUCTION_WIDTH))
    if tmp is None:
        return Subject(design, n, PRODUCTION_WIDTH, rounds, 0, f"n{n}-w{PRODUCTION_WIDTH}", loaded, [], "")
    entries, _ = gen_constants_v3.guard_refused_list(evidence.REPO.root)
    polynomial = gen_constants_v3.chosen_polynomial(entries)
    read = gen_constants_v3.read_table(polynomial, rounds, ir.last_constant(loaded.program) + 1, PRODUCTION_WIDTH)
    variant = f"n{n}-w{PRODUCTION_WIDTH}-R{rounds}-c{PROBE_CAPACITY}"
    tmp.mkdir(parents=True, exist_ok=True)
    path = tmp / f"{variant}.json"
    path.write_bytes(gen_constants_v3.table_file(variant, loaded.program, rounds, polynomial, read))
    return Subject(design, n, PRODUCTION_WIDTH, rounds, PROBE_CAPACITY, variant, loaded, read["table"], evidence.rel_to_repo(path))


def reference_box_costs(design: str, kind: str) -> Tuple[int, ...]:
    """The reference design's box bounds at w = 32, from feature 004's committed box record, read and never written."""
    found = None
    base = evidence.REPO.path(f"{REFERENCE['rep']}/candidates/{design}")
    for path in sorted(base.glob("bound-*.json")):
        record = json.loads(path.read_bytes().decode("utf-8"))
        if record.get("method") == "branch-and-bound" and record.get("bound_kind") == kind and record.get("width") == PRODUCTION_WIDTH \
                and record.get("status") == "pass" and (found is None or record["created_utc"] > found["created_utc"]):
            found = record
    if found is None:
        raise Refused(f"feature 004 holds no box bound of {design}, kind {kind}, at w = {PRODUCTION_WIDTH}")
    scale = 2 if kind == "linear" else 1
    return tuple(scale * min(row["weights"][str(t)] for row in found["boxes"].values()) for t in range(1, found["rounds"] + 1))


def probe_work(job: Tuple) -> float:
    """One kind of a probe, the run itself, in a process of its own: its seconds, every other output discarded unread."""
    design, kind, n, rounds, bound_kind, tmp, seconds = job
    started = time.monotonic()
    reference_module(design)
    if kind == "bound":
        subject = probe_subject(design, n, 0, None)
        for module in (long_trail, active_sbox):
            module.SETTINGS["time_limit"] = seconds + 600.0
        if PROBE_DESIGNS[design] == "ARX":
            long_trail.minima(branch_layer(subject.program, bound_kind), reference_box_costs(design, bound_kind), rounds)
        else:
            active_sbox.minima(boolean_layer(design, n, PRODUCTION_WIDTH), bound_kind, rounds)
        return time.monotonic() - started
    directory = Path(tmp)
    subject = probe_subject(design, n, 0, None) if kind in NO_TABLE else probe_subject(design, n, rounds, directory)
    run = ProbeRun(directory / kind)
    if kind == "avalanche":
        run_avalanche(subject, run, cited="a probe: the dependency matrices are computed here and no record is cited")
    else:
        RUNS[kind](subject, run)
    return time.monotonic() - started


def table_probes() -> List[Dict]:
    return [record for _, record in evidence.iter_records("projection", "projections") if isinstance(record.get("table_probe"), dict)]


def probes_used() -> float:
    return sum(float(record.get("time_hours", 0.0)) for record in table_probes())


def probes_share() -> float:
    """The probes' share of the feature-wide row: the projection table's once it exists, the approved option's before (FR-005)."""
    table = evidence.projection_table()
    if table is not None:
        return float(table["feature_wide_row"]["probes_share_h"])
    return float(evidence.approved_option()["feature_wide_needs_h"][PROBE_SHARE])


def plan_need(design: str, n: int, bound_kind: str, rounds: int) -> float:
    for search in evidence.approved_option()["climbs"][f"{design} {n}x{n} {bound_kind}"]["searches"]:
        if search["r"] == rounds:
            return float(search["need_h"])
    raise Refused(f"the approved option lists no {bound_kind} search of {design} at {n}×{n}, r = {rounds}")


def run_probe(args: argparse.Namespace, command: List[str]) -> int:
    """A probe for the projection table (research R5; contracts/cli.md): the run itself on a reference design's committed operation
    list, up to 4 h at one thread, written as a `projection` record charged to the feature-wide row."""
    if evidence.FEATURE == "004":
        raise Refused("--probe runs under PHYCOWEB_FEATURE=005")
    if candidates.of_event(candidates.entries(), "proposed"):
        raise Refused("the candidate log holds a `proposed` entry: the probes come before the first")
    design, group = args.candidate, args.kind
    if group not in tuple(PROBE_GROUPS) + ("bound",):
        raise Refused(f"a probe's --kind is one of {tuple(PROBE_GROUPS) + ('bound',)}")
    n = args.size
    if n not in evidence.CLAIMABLE_SIZES:
        raise Refused(f"a probe names --size, one of {evidence.CLAIMABLE_SIZES}")
    named = guard_reference(design)
    if group == "bound":
        if not args.bound_kind or not args.rounds:
            raise Refused("a search probe names --bound-kind and --rounds")
        rounds, kinds = args.rounds, ("bound",)
        projected = min(PROBE_LIMIT_HOURS, plan_need(design, n, args.bound_kind, rounds))
        code = CODE + [named["path"], TRAIL_PATHS[METHODS[PROBE_METHODS[design]]["tool"]]]
    else:
        if (args.rounds or PROBE_ROUNDS) != PROBE_ROUNDS:
            raise Refused(f"a structural or bias probe runs at --rounds {PROBE_ROUNDS}, R_max + Δ (research R5)")
        rounds, kinds, projected = PROBE_ROUNDS, PROBE_GROUPS[group], PROBE_LIMIT_HOURS
        code = CODE + [named["path"]]
    probe = {"design": design, "family": PROBE_DESIGNS[design], "kind": group, "size": n, "width": PRODUCTION_WIDTH, "rounds": rounds,
             "bound_kind": args.bound_kind or NONE, "method": PROBE_METHODS[design] if group == "bound" else NONE}
    used, share = probes_used(), probes_share()

    def record(result: str, hours: Dict[str, float], elapsed: float) -> Path:
        extra = {"table_probe": probe, "result": result, "hours_by_kind": hours, "limit_hours": PROBE_LIMIT_HOURS,
                 "parallelism": {"threads": 1, "workers": 1}, "design": named, "share": {"name": PROBE_SHARE, "hours": share, "used_before": used}}
        if result == FINISHED:
            extra["probe_hours"] = elapsed
        return evidence.write_projection(
            run=f"probe: {group} of {design} at {n}×{n}, w = {PRODUCTION_WIDTH}" + (f", {args.bound_kind}, r = {rounds}" if group == "bound" else f", R = {rounds}"),
            row=evidence.FEATURE_ROW, inputs="the reference design's committed operation list", measured_speed={"hours_by_kind": hours},
            projected_hours=projected, time_hours=elapsed, statement=PROBE_STATEMENT, argv=command, code_files=code, extra=extra)

    if used + projected > share:
        path = record(PROBE_REFUSED, {}, 0.0)
        raise Refused(f"{evidence.rel_to_repo(path)}: the probe, {projected:.3f} h, would take the probes past their {share:.1f} h share, "
                      f"{used:.3f} h used: its run keeps the plan's projection")
    evidence.guard_feature_row([projected])
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ[name] = "1"
    tmp = evidence.REPO.path(evidence.LOCAL_REL) / "probes" / f"{design}-{group}-n{n}"
    hours: Dict[str, float] = {}
    result = FINISHED
    started = time.monotonic()
    with evidence.HeavyRunLock(" ".join(command)):
        try:
            for kind in kinds:
                left = PROBE_LIMIT_HOURS * 3600.0 - (time.monotonic() - started)
                before = time.monotonic()
                done = limited(probe_work, (design, kind, n, rounds, args.bound_kind, str(tmp), left), left) if left > 0 else None
                if done is None:
                    result = REACHED_LIMIT
                    break
                hours[kind] = (time.monotonic() - before) / 3600.0
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    elapsed = (time.monotonic() - started) / 3600.0
    path = record(result, hours, elapsed)
    print(f"{evidence.rel_to_repo(path)}: {result}, {elapsed:.3f} h")
    return evidence.EXIT_OK


# ------------------------------------------------------------------------- --aborted and controls

def aborted(args: argparse.Namespace) -> int:
    """No run: the `evidence` entry of a record that clear_lock.py wrote, its hours in its row."""
    path = Path(args.aborted)
    path = path if path.is_absolute() else evidence.REPO.path(args.aborted)
    if not path.exists():
        raise Refused(f"{args.aborted} does not exist")
    record = json.loads(path.read_bytes().decode("utf-8"))
    if record.get("status") != "inconclusive" or "scripts/clear_lock.py" not in (record.get("code_sha256") or {}):
        raise Refused(f"{args.aborted} is no record that clear_lock.py wrote")
    candidate = path.parent.name
    log = candidates.entries()
    if any(record["record_id"] in (entry.get("evidence") or ()) for entry in log):
        raise Refused(f"{record['record_id']} has its entry")
    append_evidence(candidate, path, ROWS[record["kind"]], evidence.run_hours_used(record))
    print(f"{candidates.LOG}: the evidence entry of {record['record_id']}")
    return evidence.EXIT_OK


def control_directory() -> str:
    return "controls"


def control_held(test: str, size: int) -> Optional[Dict]:
    """The latest record of a control, which a run ended from outside leaves to be made again: the one that no run made again names,
    the latest of those, since a run made again names the record it makes again (research R7)."""
    held = [record for _, record in evidence.iter_records("control", control_directory())
            if record.get("test") == test and record.get("size") == size]
    named = {item.get("record_id") for record in held for item in record.get("exclusions_and_reruns") or ()}
    standing = [record for record in held if record["record_id"] not in named] or held
    return max(standing, key=lambda record: record["created_utc"]) if standing else None


def control_states(n: int, first: int, count: int) -> np.ndarray:
    values = devinputs_v3.load("control", "state", ("control",), first + count, n=n, w=bias.W)
    return np.array([list(values[i]) for i in range(first, first + count)], dtype=np.uint64).T


def control_frequency_part(job: Tuple[int, int, int]) -> np.ndarray:
    n, first, count = job
    return bias.ones(control_states(n, first, count), bias.W)


def control_frequency(run: evidence.Run, n: int) -> Tuple[Dict, Dict]:
    """Two sets of 2²⁰ control states, states 0 to 2²⁰ - 1 and 2²⁰ to 2²¹ - 1, counted as the frequency test counts them."""
    s = 4 * 2 * n * n * bias.W
    entry = bias.entry_for("frequency", FREQUENCY_N, s)
    raw, summaries, small = {}, {}, {}
    locations: List[Dict] = []
    for name, base in (("first set", 0), ("second set", FREQUENCY_N)):
        jobs = [(n, base + first, min(bias.BATCH, FREQUENCY_N - first)) for first in range(0, FREQUENCY_N, bias.BATCH)]
        ordered = bias.test_order(sum(worker_map(control_frequency_part, jobs, run.workers)))
        raw[name] = ordered.tolist()
        summaries[name] = [int(ordered.min()), int(ordered.max())]
        small[name] = smallest_p(ordered, FREQUENCY_N)
        locations += [{"set": name, "position": position, "count": count} for position, count in bias.fired_bits(ordered, entry)]
    fields = {"sample_size": {"n": FREQUENCY_N, "sets": 2}, "summaries": summaries,
              "test_parameters": {"s": s, "threshold": "0.005/S", "critical": [entry["low"], entry["high"]]},
              "raw_counts": kept_output(run, "counts.json.gz", raw),
              "p_values": cite(run.output("p-values.json.gz", json_bytes(small), deterministic=False, compared="values")),
              "failure_locations": kept_output(run, "failure-locations.json.gz", locations),
              "fires": evidence.control_fired([summaries[name] for name in sorted(summaries)], [(entry["low"], entry["high"])])}
    return fields, {"namespace": "control", "kind": "state", "n": n, "w": bias.W, "index_range": [0, 2 * FREQUENCY_N - 1]}


def control_groups(n: int) -> int:
    return len(avalanche.flip_set(n, bias.W)) + avalanche.RELATED_BITS + bias.W - 1


def control_avalanche_part(job: Tuple[int, int, int, int, str]) -> Dict:
    """Some groups of N_a differences, difference i being state 2i xor state 2i + 1, each judged as the test judges its counts."""
    n, part, start, stop, directory = job
    first, whole = bias_entries(n)
    sink = Part(Path(directory) / f"counts-{part:04d}.json.gz")
    rows = {"first": [avalanche.N_FIRST, 0], "whole": [avalanche.N_A, 0]}
    located = []
    farthest = 0
    for group in range(start, stop):
        differences = bias.control_differences(control_states(n, 2 * group * avalanche.N_A, 2 * avalanche.N_A))
        early, full = bias.ones(differences[:, :avalanche.N_FIRST], bias.W), bias.ones(differences, bias.W)
        fired = bias.test_order(bias.fires(early, first) | bias.fires(full, whole))
        early_flat, full_flat = bias.test_order(early), bias.test_order(full)
        sink.add({"group": group, "first": early_flat.tolist(), "whole": full_flat.tolist()})
        for name, flat in (("first", early_flat), ("whole", full_flat)):
            rows[name] = [min(rows[name][0], int(flat.min())), max(rows[name][1], int(flat.max()))]
        farthest = max(farthest, int(np.abs(2 * full_flat.astype(np.int64) - avalanche.N_A).max()))
        if fired.any():
            located.append({"group": group, "fired": np.packbits(fired).tobytes().hex()})
    return {"part": sink.close(), "rows": rows, "located": located, "farthest": farthest}


def control_avalanche(run: evidence.Run, n: int) -> Tuple[Dict, Dict]:
    """N_a·(|F| + 384 + w - 1) XOR differences, N_a for each flipped bit, key or nonce bit and rotation amount."""
    groups = control_groups(n)
    first, whole = bias_entries(n)
    run.tmp.mkdir(parents=True, exist_ok=True)
    directory = run.tmp / "workers"
    directory.mkdir(parents=True, exist_ok=True)
    jobs = [(n, part, at, min(at + GROUP_CHUNK, groups), str(directory)) for part, at in enumerate(range(0, groups, GROUP_CHUNK))]
    results = worker_map(control_avalanche_part, jobs, run.workers)
    rows = {name: [min(result["rows"][name][0] for result in results), max(result["rows"][name][1] for result in results)]
            for name in ("first", "whole")}
    located = [item for result in results for item in result["located"]]
    small = smallest_p(np.array([(avalanche.N_A + max(result["farthest"] for result in results)) // 2]), avalanche.N_A)
    fields = {"sample_size": {"n_a": avalanche.N_A, "n_first": avalanche.N_FIRST, "groups": groups}, "summaries": rows,
              "test_parameters": {"s_a": avalanche.s_a(n), "threshold": "0.005/(128·S_A)", "critical_first": [first["low"], first["high"]],
                                  "critical_whole": [whole["low"], whole["high"]]},
              "raw_counts": adopted_parts(run, results, directory),
              "p_values": cite(run.output("p-values.json.gz", json_bytes(small), deterministic=False, compared="values")),
              "failure_locations": kept_output(run, "failure-locations.json.gz", located),
              "fires": evidence.control_fired([rows["first"], rows["whole"]], [(first["low"], first["high"]), (whole["low"], whole["high"])])}
    return fields, {"namespace": "control", "kind": "state", "n": n, "w": bias.W, "index_range": [0, 2 * groups * avalanche.N_A - 1]}


def rows_charged(hours: float) -> Tuple[List[str], List[str]]:
    """Every entered candidate's statistics row is charged the control in full, but one with a closing decision, and one whose row
    cannot hold it, which takes no test of that kind at that size (research R4, R7; ANA-074)."""
    log = candidates.entries()
    charged, spared = [], []
    for candidate in sorted({entry["candidate_id"] for entry in candidates.of_event(log, "entered-d4")}):
        if set(candidates.decisions(log, candidate)) & set(evidence.CLOSING_DECISIONS):
            continue
        held = hours <= evidence.row_hours(candidate, "statistics") - evidence.candidate_row_used(candidate, "statistics")
        (charged if held else spared).append(candidate)
    return charged, spared


CONTROLS = {"frequency": control_frequency, "avalanche": control_avalanche}


def control_state_count(test: str, n: int) -> int:
    return 2 * FREQUENCY_N if test == "frequency" else 2 * avalanche.N_A * control_groups(n)


def run_control(args: argparse.Namespace, command: List[str]) -> int:
    if args.test is None or args.size not in evidence.CLAIMABLE_SIZES:
        raise Refused("a control names --test and a claimable --size")
    n, test = args.size, args.test
    held = control_held(test, n)
    again: List[Dict] = []
    if held is not None:
        if held.get("ended_outside", NONE) != NONE:
            again = [{"record_id": held["record_id"], "why": "ended from outside"}]
        elif defect_note(held["record_id"]) is not None:
            again = [{"record_id": held["record_id"], "why": "tool defect", "defect": defect_note(held["record_id"])}]
        else:
            raise Refused(f"the {test} control at {n}×{n} has its record")
    if evidence.validation_citation("bias", tool_sha("control")) is None:
        raise Refused("the bias test has no re-found record of its exact hash")
    started = time.monotonic()
    bias.ones(control_states(n, 0, 2 ** 8), bias.W)
    per_state = (time.monotonic() - started) / 2 ** 8
    hours = per_state * control_state_count(test, n) / max(1, args.workers) / 3600.0
    path = evidence.write_projection(run=f"the {test} control at {n}×{n}", row=evidence.FEATURE_ROW, inputs="the first control states",
                                     measured_speed={"seconds_per_state": per_state, "workers": args.workers}, projected_hours=hours,
                                     time_hours=(time.monotonic() - started) / 3600.0, argv=command, code_files=CODE,
                                     extra={"probe": probe_of("control", n, test)})
    if args.project:
        print(f"{evidence.rel_to_repo(path)}: {hours:.3f} h projected")
        return evidence.EXIT_OK
    charged, spared = rows_charged(hours)
    # A control that dies holding the lock is found, named and charged as a finished one is (research R7, "Runs ended from outside").
    found_by = {"test": test, "size": n, "not_charged": spared, "charged": charged, "exclusions_and_reruns": again}
    run = evidence.Run("control", directory=control_directory(), code_files=CODE, argv=command, heavy=True, projected_hours=hours,
                       workers=args.workers, namespace="control", config={"size": n, "test": test}, described=found_by)
    with run:
        run.begin(hours)
        fields, inputs = CONTROLS[test](run, n)
        run.inputs = inputs
        fires = fields["fires"]
        path = run.finish("inconclusive" if fires else "pass", exit_status=evidence.EXIT_OK, fields=dict(
            fields, test=test, size=n, not_charged=spared, charged=charged, exclusions_and_reruns=again,
            validation=evidence.validation_citation("bias", tool_sha("control")), statement=MAPPED_STATEMENT,
            finding="that size's bias evidence is inconclusive for every candidate, and the feature recommends stopping" if fires else NONE))
    print(f"{evidence.rel_to_repo(path)}: {'fired' if fires else 'pass'}")
    return evidence.EXIT_OK


# --------------------------------------------------------------------------------------- --reproduce

def remeasure(text: str, out: str, out_dir: str, local_dir: str, binary: str) -> None:
    """The run of a reproduction, in its worktree: everything is read from that commit. Each output goes where the original's did."""
    original = json.loads(text)
    kind, candidate, config = original["kind"], original.get("candidate"), original["config"]
    if binary != NONE:
        arx_search_known.BINARY = binary
    holder = evidence.Run(kind, candidate=candidate, directory="reproduced", code_files=(), writes_evidence=False,
                          workers=original["parallelism"]["workers"])
    if kind == "control":
        fields, inputs = CONTROLS[config["test"]](holder, config["size"])
        result = {"status": "inconclusive" if fields["fires"] else "pass", "classification": NONE, "inputs": inputs,
                  "fields": dict(fields, test=config["test"], size=config["size"])}
    elif kind == "rotation-ranking":
        subject = plain_subject(candidate, config["size"], config["width"], config["rounds"])
        result = run_ranking(subject, holder, original["cross_check"], original["validation"])
    elif kind in TRAIL_KINDS:
        args = argparse.Namespace(bound_kind=original.get("bound_kind"), method=original.get("method"), tool=original.get("tool"),
                                  rounds=original["rounds"] if kind == "cross-check" else config["rounds"])
        subject = plain_subject(candidate, config["size"], config["width"], config["rounds"])
        result = run_cross_check(subject, holder, args) if kind == "cross-check" else run_bound(
            subject, holder, args, original["tool"], original["validation"], original["cross_check"])
        if kind == "bound":
            result["fields"]["budget"] = {"cap_hours": INSTANCE_HOURS}
    else:
        subject = plain_subject(candidate, config["size"], config["width"]) if kind in NO_TABLE \
            else subject_of(candidate, config["size"], config["width"], config["rounds"])
        holder.extra["exclusions_and_reruns"] = original.get("exclusions_and_reruns", [])
        result = measured(kind, subject, holder)
    for source, final in holder.moves:
        local = final.startswith(evidence.LOCAL_REL)
        target = Path(local_dir if local else out_dir) / final.rsplit("/", 1)[-1]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    shutil.rmtree(holder.tmp, ignore_errors=True)
    fields = dict(result["fields"], kind=kind, candidate=candidate, inputs=result["inputs"], model_id=original.get("model_id"),
                  variant_id=original.get("variant_id"), exit_status=exit_of(result), assertions=[], status=result["status"],
                  classification=result["classification"], outputs=holder.outputs)
    Path(out).write_bytes(evidence.pretty(fields))


def reproduce_in(place: evidence.Place, original: Dict) -> Dict:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "fields.json"
        binary = str(place.binaries[ARX_BINARY]) if ARX_BINARY in place.binaries else NONE
        done = subprocess.run([sys.executable, "-X", "utf8", "-c", RUN_HERE, "remeasure", json.dumps(original), str(out),
                               str(place.out), str(place.local), binary], cwd=place.worktree, capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
        if done.returncode != 0:
            raise ToolFailure(f"the run exited {done.returncode}: {done.stderr.strip()[-400:]}")
        return json.loads(out.read_bytes().decode("utf-8"))


def reproduce(args: argparse.Namespace, command: List[str]) -> int:
    path = Path(args.reproduce)
    path = path if path.is_absolute() else evidence.REPO.path(args.reproduce)
    if not path.exists():
        raise Refused(f"{args.reproduce} does not exist")
    original = json.loads(path.read_bytes().decode("utf-8"))
    if original.get("kind") not in KINDS + ("control",):
        raise Refused(f"{args.reproduce} is no record of this script")

    def run(place: evidence.Place) -> Dict:
        return dict(reproduce_in(place, original), code_sha256=original["code_sha256"])

    def projection(worktree: Path) -> Tuple[float, Any]:
        hours = evidence.run_hours_used(original)
        return hours, {"hours_of_the_original": hours}

    extra = tuple(key for key in original if key not in COMMON_KEYS and key not in OUTPUT_FIELDS)
    return evidence.reproduce(evidence.Reproduction(record_path=path, run=run, heavy=bool(original.get("heavy_run")),
                                                    owner_request=args.owner_request, project=projection, extra=extra,
                                                    code_files=CODE, argv=command))


COMMON_KEYS = ("record_id", "created_utc", "outputs", "hours", "heavy_run", "limitations", "exit_status", "assertions",
               "status", "classification", "kind", "model_id", "variant_id", "protocol_seq", "protocol_line_sha256",
               "protocol_line_sha256_kind", "code_sha256", "versions", "environment", "platform", "parallelism",
               "command", "config", "inputs", "analyst", "reviewer", "review_status", "ended_outside", "disclaimer",
               "design_version", "design_sha256", "design_sha256_kind", "spec_sha256", "spec_sha256_kind", "research_sha256",
               "research_sha256_kind", "git_head", "git_dirty", "dirty_paths", "candidate", "not_charged", "charged", "exclusions_and_reruns")


def guard_out_dir(args: argparse.Namespace) -> None:
    """A record has one place, which the command names (cli contract)."""
    wanted = f"{evidence.REP_REL}/" + ("controls" if args.kind == "control" else f"candidates/{args.candidate}")
    given = Path(args.out_dir or "")
    given = given if given.is_absolute() else evidence.REPO.path(str(given))
    if given != evidence.REPO.path(wanted):
        raise Refused(f"--out-dir names {wanted}")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--candidate")
    parser.add_argument("--kind", choices=KINDS + ("control", "structural", "bias"))
    parser.add_argument("--probe", action="store_true", help="feature 005: a probe for the projection table (research R5)")
    parser.add_argument("--test", choices=BIAS_KINDS)
    parser.add_argument("--size", type=int)
    parser.add_argument("--width", type=int)
    parser.add_argument("--rounds", type=int)
    parser.add_argument("--project", action="store_true")
    parser.add_argument("--out-dir")
    parser.add_argument("--bound-kind", choices=long_trail.KINDS)
    parser.add_argument("--method")
    parser.add_argument("--tool")
    parser.add_argument("--workers", type=int, default=WORKERS)
    parser.add_argument("--reproduce")
    parser.add_argument("--owner-request")
    parser.add_argument("--aborted")
    args = parser.parse_args(argv)
    command = [SCRIPT] + list(sys.argv[1:] if argv is None else argv)

    def body() -> int:
        if args.reproduce:
            return reproduce(args, command)
        if args.aborted:
            return aborted(args)
        if args.probe:
            return run_probe(args, command)
        if args.kind is None:
            raise Refused("a run names --kind")
        if args.kind != "control" and not args.candidate:
            raise Refused("a run names --candidate")
        guard_out_dir(args)
        if args.kind == "control":
            return run_control(args, command)
        return run_candidate(args, command)

    return evidence.main_guard(body)


if __name__ == "__main__":
    raise SystemExit(main())
