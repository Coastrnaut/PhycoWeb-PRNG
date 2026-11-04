"""Feature 004: operation lists (spec FR-018 to FR-020; research R11, R14).

A candidate is written once as an operation list, from which every tool derives what it needs, so
that its evaluation, inverse, dependency, cost and trail models describe one object. Two forms exist:

    Mix(dst, op, F)    dst <- dst op F(srcs), op in xor, add, sub, dst not among srcs
    Rot(dst, k)        dst <- rotl(dst, k), k fixed

Each is invertible whatever F is, so a list of them is bijective by construction wherever the phase
rule holds. F is built from rotations, shifts, bitwise functions and round constants: it holds no
addition and no value of its own, the constants coming only from the table the constant rule writes,
and every amount is a fixed integer, so nothing in a list can read data to choose an operation. A
round is a sequence of phases, each one colour class, whose updates read no lane that another update
of the phase writes. `load` checks all of this at the list's size, and both interpreters take only
what it returned.

Import this module as `ir`, with research/004 on the path, so that candidates and tools share one
copy of the forms. Analysis code only: the model never imports it. This module makes no security
claim.
"""
import hashlib
import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from protocol.devinputs_v3 import PAIRS  # noqa: E402
from protocol.evidence import Refused  # noqa: E402

CANDIDATES = ROOT / "research/004/candidates"
PRESSURE, VEIN = 0, 1
OPERATORS = ("xor", "add", "sub")
UNDO = {"xor": "xor", "add": "sub", "sub": "add"}
MAX_CHANNELS = 4
EXPLORATION_N = range(2, 17)
EXPLORATION_W = (8, 16, 32)


class ListRefused(Refused):
    """An operation list that breaks a rule of research R11: exit 2, before any test."""


# ---------------------------------------------------------------------------- the grid

def lane(n: int, i: int, j: int, kind: int) -> int:
    """A lane's place in the state: nodes row by row, each its pressure lane, then its vein. The
    coordinates wrap, which is where a list's neighbourhood is resolved for its size."""
    return 2 * (n * (i % n) + (j % n)) + kind


def node_of(n: int, index: int) -> Tuple[int, int]:
    return (index // 2) // n, (index // 2) % n


def neighbours(n: int, i: int, j: int) -> Set[Tuple[int, int]]:
    """The torus's direct neighbours; at 2×2 opposite neighbours coincide, so there are two."""
    return {((i + 1) % n, j), ((i - 1) % n, j), (i, (j + 1) % n), (i, (j - 1) % n)}


def colours(n: int) -> int:
    return 3 if n % 2 else 2


def colour(n: int, i: int, j: int) -> int:
    """Two colours for even n; for odd n, (f(i) + f(j)) mod 3, f a proper 3-colouring of the n-cycle:
    k mod 2 for k < n - 1, and 2 at n - 1 (spec FR-018)."""
    if n % 2 == 0:
        return (i + j) % 2

    def f(k: int) -> int:
        k %= n
        return 2 if k == n - 1 else k % 2

    return (f(i) + f(j)) % 3


def nodes_of(n: int, wanted: int) -> List[Tuple[int, int]]:
    return [(i, j) for i in range(n) for j in range(n) if colour(n, i, j) == wanted]


# ------------------------------------------------------------------------- the forms

@dataclass(frozen=True)
class Lane:
    index: int


@dataclass(frozen=True)
class Constant:
    """Word `index` of the round's row of the constant table."""
    index: int


@dataclass(frozen=True)
class Rotl:
    value: Any
    amount: int


@dataclass(frozen=True)
class Shl:
    value: Any
    amount: int


@dataclass(frozen=True)
class Shr:
    value: Any
    amount: int


@dataclass(frozen=True)
class Xor:
    left: Any
    right: Any


@dataclass(frozen=True)
class And:
    left: Any
    right: Any


@dataclass(frozen=True)
class Or:
    left: Any
    right: Any


@dataclass(frozen=True)
class Not:
    value: Any


@dataclass(frozen=True)
class Mix:
    dst: int
    op: str
    expr: Any


@dataclass(frozen=True)
class Rot:
    dst: int
    amount: int


@dataclass(frozen=True)
class Phase:
    colour: int
    updates: Tuple[Any, ...]


@dataclass(frozen=True)
class Program:
    name: str
    n: int
    w: int
    phases: Tuple[Phase, ...]


@dataclass(frozen=True)
class Loaded:
    """What the loader passed, and all an interpreter takes."""
    program: Program


UNARY = (Rotl, Shl, Shr, Not)
BINARY = (Xor, And, Or)


# ------------------------------------------------------------------------- reads and writes

def expression_reads(expr: Any) -> Set[int]:
    if type(expr) is Lane:
        return {expr.index}
    if type(expr) is Constant:
        return set()
    if type(expr) in UNARY:
        return expression_reads(expr.value)
    return expression_reads(expr.left) | expression_reads(expr.right)


def reads(update: Any) -> Set[int]:
    """Every lane an update reads, the one it writes included: its old value enters the new one."""
    if type(update) is Mix:
        return expression_reads(update.expr) | {update.dst}
    return {update.dst}


def constants_used(expr: Any) -> Set[int]:
    if type(expr) is Constant:
        return {expr.index}
    if type(expr) is Lane:
        return set()
    if type(expr) in UNARY:
        return constants_used(expr.value)
    return constants_used(expr.left) | constants_used(expr.right)


def last_constant(program: Program) -> int:
    """The largest column of the constant table the list reads, or -1 for a list that reads none."""
    used: Set[int] = {-1}
    for phase in program.phases:
        for update in phase.updates:
            if type(update) is Mix:
                used |= constants_used(update.expr)
    return max(used)


# ------------------------------------------------------------------------------ the loader

def refuse(program: Program, text: str) -> None:
    raise ListRefused(f"{program.name} at n={program.n}, w={program.w}: {text}")


def guard_amount(program: Program, amount: Any) -> None:
    if type(amount) is not int or not 0 < amount < program.w:
        refuse(program, f"amount {amount!r}: every amount is a fixed integer, 1 to w - 1")


def guard_lane(program: Program, index: Any) -> None:
    if type(index) is not int or not 0 <= index < 2 * program.n ** 2:
        refuse(program, f"lane {index!r} is outside the state")


def guard_expression(program: Program, expr: Any) -> None:
    kind = type(expr)
    if kind is Lane:
        guard_lane(program, expr.index)
    elif kind is Constant:
        if type(expr.index) is not int or expr.index < 0:
            refuse(program, f"constant index {expr.index!r}")
    elif kind in (Rotl, Shl, Shr):
        guard_amount(program, expr.amount)
        guard_expression(program, expr.value)
    elif kind is Not:
        guard_expression(program, expr.value)
    elif kind in BINARY:
        guard_expression(program, expr.left)
        guard_expression(program, expr.right)
    else:
        refuse(program, f"expression {expr!r}: F holds rotations, shifts, bitwise functions, lanes "
                        "and the table's constants")


def guard_update(program: Program, update: Any) -> None:
    kind = type(update)
    if kind is Mix:
        guard_lane(program, update.dst)
        if update.op not in OPERATORS:
            refuse(program, f"operator {update.op!r}")
        guard_expression(program, update.expr)
        if update.dst in expression_reads(update.expr):
            refuse(program, f"dst {update.dst} is among the sources of its own update")
    elif kind is Rot:
        guard_lane(program, update.dst)
        guard_amount(program, update.amount)
    else:
        refuse(program, f"{update!r} is neither form")


def guard_neighbours(program: Program, update: Any) -> None:
    n = program.n
    node = node_of(n, update.dst)
    near = neighbours(n, *node) | {node}
    for index in reads(update):
        if node_of(n, index) not in near:
            refuse(program, f"lane {index} is no direct neighbour of node {node}")


def guard_channels(program: Program, phase: Phase, number: int) -> None:
    """A channel is one word passed from a node to a neighbour in one phase (spec FR-018), so that
    a word two updates of a node read is one channel, and a node's own lanes are none."""
    received: Dict[Tuple[int, int], Set[int]] = {}
    for update in phase.updates:
        node = node_of(program.n, update.dst)
        for index in reads(update):
            if node_of(program.n, index) != node:
                received.setdefault(node, set()).add(index)
    for node, words in received.items():
        if len(words) > MAX_CHANNELS:
            refuse(program, f"phase {number}: node {node} receives {len(words)} channels")


def guard_phase_rule(program: Program, phase: Phase, number: int) -> None:
    """Within a phase no update reads a lane that another update writes (research R11)."""
    writers: Dict[int, List[int]] = {}
    for place, update in enumerate(phase.updates):
        writers.setdefault(update.dst, []).append(place)
    for place, update in enumerate(phase.updates):
        for index in reads(update):
            if any(other != place for other in writers.get(index, ())):
                refuse(program, f"phase {number}: an update reads a lane that another writes, "
                                f"lane {index}")


def guard_size(program: Program, exploration: bool) -> None:
    n, w = program.n, program.w
    if type(n) is int and type(w) is int:
        if (n, w) in PAIRS or (exploration and n in EXPLORATION_N and w in EXPLORATION_W):
            return
    refuse(program, "no supported (n, w)")


def load(program: Program, exploration: bool = False) -> Loaded:
    """The checks of research R11 at this size; a list that breaks one is refused, before any test.

    R11 calls a phase a colour class, which this reads strictly: every lane a phase writes lies in a
    node of its class. `exploration` admits an n from 2 to 16 outside the supported pairs, never
    evidence (R14)."""
    guard_size(program, exploration)
    if not program.phases:
        refuse(program, "a list holds at least one phase")
    classes = colours(program.n)
    for number, phase in enumerate(program.phases):
        if type(phase.colour) is not int or not 0 <= phase.colour < classes:
            refuse(program, f"phase {number}: colour {phase.colour!r}")
        for update in phase.updates:
            guard_update(program, update)
            if colour(program.n, *node_of(program.n, update.dst)) != phase.colour:
                refuse(program, f"phase {number}: lane {update.dst} is outside the phase's colour")
            guard_neighbours(program, update)
        guard_phase_rule(program, phase, number)
        guard_channels(program, phase, number)
    return Loaded(program)


def check_every_size(build: Callable[[int, int], Program]) -> List[Loaded]:
    """One list at every supported (n, w); the size that breaks a rule names itself."""
    return [load(build(n, w)) for n, w in PAIRS]


# ------------------------------------------------------------------- what both interpreters take

def guard_loaded(loaded: Any) -> Program:
    if type(loaded) is not Loaded:
        raise ListRefused("an interpreter takes a list the loader passed")
    return loaded.program


def table_of(program: Program, constants: Sequence[Sequence[int]],
             rounds: Optional[int]) -> List[Sequence[int]]:
    """One row per round: the table's, or an empty row for a list that reads no constant."""
    last = last_constant(program)
    if rounds is not None and (type(rounds) is not int or rounds < 1):
        refuse(program, f"rounds {rounds!r}")
    if not constants:
        if last >= 0:
            refuse(program, "the list reads a constant and no table was given")
        return [()] * (1 if rounds is None else rounds)
    if rounds is not None and rounds != len(constants):
        refuse(program, f"{rounds} rounds and a table of {len(constants)} rows")
    for row in constants:
        if len(row) <= last:
            refuse(program, f"a row of the constant table has {len(row)} words, and the list reads "
                            f"column {last}")
        if any(type(word) is not int or not 0 <= word < 1 << program.w for word in row):
            refuse(program, "a word of the constant table is beyond the width")
    return list(constants)


# ---------------------------------------------------------------------- the scalar interpreter

def rotl(value: int, amount: int, w: int) -> int:
    return ((value << amount) | (value >> (w - amount))) & ((1 << w) - 1)


def evaluate(expr: Any, state: Sequence[int], row: Sequence[int], w: int) -> int:
    kind = type(expr)
    if kind is Lane:
        return state[expr.index]
    if kind is Constant:
        return row[expr.index]
    if kind is Rotl:
        return rotl(evaluate(expr.value, state, row, w), expr.amount, w)
    mask = (1 << w) - 1
    if kind is Shl:
        return (evaluate(expr.value, state, row, w) << expr.amount) & mask
    if kind is Shr:
        return evaluate(expr.value, state, row, w) >> expr.amount
    if kind is Not:
        return evaluate(expr.value, state, row, w) ^ mask
    left, right = evaluate(expr.left, state, row, w), evaluate(expr.right, state, row, w)
    if kind is Xor:
        return left ^ right
    return left & right if kind is And else left | right


def apply_phase(phase: Phase, state: List[int], row: Sequence[int], w: int) -> None:
    """Each update reads the values at the phase's start, as the hardware does."""
    mask = (1 << w) - 1
    written = []
    for update in phase.updates:
        if type(update) is Rot:
            written.append((update.dst, rotl(state[update.dst], update.amount, w)))
            continue
        value = evaluate(update.expr, state, row, w)
        if update.op == "xor":
            written.append((update.dst, state[update.dst] ^ value))
        elif update.op == "add":
            written.append((update.dst, (state[update.dst] + value) & mask))
        else:
            written.append((update.dst, (state[update.dst] - value) & mask))
    for dst, value in written:
        state[dst] = value


def permute(loaded: Loaded, state: Sequence[int], constants: Sequence[Sequence[int]] = (),
            rounds: Optional[int] = None) -> List[int]:
    """Π on Python integers, the state in lane order; one pass per row of the constant table."""
    program = guard_loaded(loaded)
    if len(state) != 2 * program.n ** 2:
        refuse(program, f"a state of {len(state)} lanes")
    if any(not 0 <= word < 1 << program.w for word in state):
        refuse(program, "a state word is beyond the width")
    out = list(state)
    for row in table_of(program, constants, rounds):
        for phase in program.phases:
            apply_phase(phase, out, row, program.w)
    return out


# ----------------------------------------------------------------------- the batch interpreter

def as_word(value: int) -> np.uint64:
    return np.uint64(value)


def rotl_batch(value: np.ndarray, amount: int, w: int) -> np.ndarray:
    return ((value << as_word(amount)) | (value >> as_word(w - amount))) & as_word((1 << w) - 1)


def evaluate_batch(expr: Any, state: np.ndarray, row: Sequence[int], w: int) -> Any:
    kind = type(expr)
    if kind is Lane:
        return state[expr.index]
    if kind is Constant:
        return as_word(row[expr.index])
    if kind is Rotl:
        return rotl_batch(evaluate_batch(expr.value, state, row, w), expr.amount, w)
    mask = as_word((1 << w) - 1)
    if kind is Shl:
        return (evaluate_batch(expr.value, state, row, w) << as_word(expr.amount)) & mask
    if kind is Shr:
        return evaluate_batch(expr.value, state, row, w) >> as_word(expr.amount)
    if kind is Not:
        return evaluate_batch(expr.value, state, row, w) ^ mask
    left = evaluate_batch(expr.left, state, row, w)
    right = evaluate_batch(expr.right, state, row, w)
    if kind is Xor:
        return left ^ right
    return left & right if kind is And else left | right


def apply_phase_batch(phase: Phase, state: np.ndarray, row: Sequence[int], w: int) -> None:
    mask = as_word((1 << w) - 1)
    written = []
    for update in phase.updates:
        if type(update) is Rot:
            written.append((update.dst, rotl_batch(state[update.dst], update.amount, w)))
            continue
        value = evaluate_batch(update.expr, state, row, w)
        if update.op == "xor":
            written.append((update.dst, (state[update.dst] ^ value) & mask))
        elif update.op == "add":
            written.append((update.dst, (state[update.dst] + value) & mask))
        else:
            written.append((update.dst, (state[update.dst] - value) & mask))
    for dst, value in written:
        state[dst] = value


def permute_batch(loaded: Loaded, states: np.ndarray, constants: Sequence[Sequence[int]] = (),
                  rounds: Optional[int] = None) -> np.ndarray:
    """Π on numpy arrays of explicit uint64, one row per lane, masked to w bits after each step."""
    program = guard_loaded(loaded)
    if states.dtype != np.uint64:
        refuse(program, f"the batch takes dtype uint64, not {states.dtype}")
    if states.shape[0] != 2 * program.n ** 2:
        refuse(program, f"a batch of {states.shape[0]} lanes")
    if (states >> as_word(program.w)).any():
        refuse(program, "a state word is beyond the width")
    out = states.copy()
    for row in table_of(program, constants, rounds):
        for phase in program.phases:
            apply_phase_batch(phase, out, row, program.w)
    return out


# ------------------------------------------------------------------------------ the inverse

def undo(update: Any, w: int) -> Any:
    if type(update) is Rot:
        return Rot(update.dst, w - update.amount)
    return Mix(update.dst, UNDO[update.op], update.expr)


def invert(program: Program) -> Program:
    """The inverse list, generated: the phases in reverse, each update undone. The phase rule keeps
    each update's sources unwritten in its phase, so a phase undoes itself in any order."""
    phases = tuple(Phase(phase.colour, tuple(undo(update, program.w) for update in phase.updates))
                   for phase in reversed(program.phases))
    return Program(program.name, program.n, program.w, phases)


def permute_inverse(loaded: Loaded, state: Sequence[int], constants: Sequence[Sequence[int]] = (),
                    rounds: Optional[int] = None) -> List[int]:
    program = guard_loaded(loaded)
    return permute(Loaded(invert(program)), state, list(reversed(constants)), rounds)


def permute_batch_inverse(loaded: Loaded, states: np.ndarray,
                          constants: Sequence[Sequence[int]] = (),
                          rounds: Optional[int] = None) -> np.ndarray:
    program = guard_loaded(loaded)
    return permute_batch(Loaded(invert(program)), states, list(reversed(constants)), rounds)


# -------------------------------------------------------------------------------- candidates

def oplist_sha256(path: Path) -> str:
    """The hash of a candidate's module, which the candidate log's `oplist_sha256` holds."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def candidate_modules(directory: Path = CANDIDATES) -> Dict[str, Callable[[int, int], Program]]:
    """Each candidate module's `build(n, w)`, by the module's name."""
    found: Dict[str, Callable[[int, int], Program]] = {}
    for path in sorted(Path(directory).glob("cand-*.py")):
        name = path.stem.replace("-", "_")
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        build = getattr(module, "build", None)
        if build is None:
            raise ListRefused(f"{path.name} holds no build(n, w)")
        found[path.stem] = build
    return found
