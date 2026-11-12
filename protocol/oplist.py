"""Feature 005: a standard-library reader of operation lists (spec FR-019, FR-020; tasks T019, T020).

The forms are those of research/004/ir.py, field for field: a candidate's module, which says
`import ir`, is read here with this module standing in that name, so that the re-check takes the
committed operation list without research/004/ir.py or numpy and runs in any environment.

    Mix(dst, op, F)    dst <- dst op F(srcs), op in xor, add, sub
    Rot(dst, k)        dst <- rotl(dst, k)

Beside the scalar evaluation, which equals `ir`'s, it gives what a trail's re-check needs of a list:
each update by its index in the list's order, the linear part of an expression and its transpose,
and an expression bit by bit, with the bits it reads. It checks no rule of research R11: the loader
of research/004/ir.py does, before any run. Analysis code only. This module makes no security claim.
"""
from __future__ import annotations

import sys
import types
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from protocol.evidence import Refused

PRESSURE, VEIN = 0, 1
OPERATORS = ("xor", "add", "sub")


# ---------------------------------------------------------------------------- the grid

def lane(n: int, i: int, j: int, kind: int) -> int:
    return 2 * (n * (i % n) + (j % n)) + kind


def node_of(n: int, index: int) -> Tuple[int, int]:
    return (index // 2) // n, (index // 2) % n


def neighbours(n: int, i: int, j: int) -> Set[Tuple[int, int]]:
    return {((i + 1) % n, j), ((i - 1) % n, j), (i, (j + 1) % n), (i, (j - 1) % n)}


def colours(n: int) -> int:
    return 3 if n % 2 else 2


def colour(n: int, i: int, j: int) -> int:
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


UNARY = (Rotl, Shl, Shr, Not)
BINARY = (Xor, And, Or)


# ------------------------------------------------------------------------- reading a list

def read(source: bytes, name: str, n: int, w: int) -> Tuple[Program, types.ModuleType]:
    """The list a candidate's module builds at n and w, from the module's bytes, with the module
    itself for what it declares. `import ir` inside it finds this module."""
    module = types.ModuleType("oplist_" + name.replace("-", "_"))
    missing = object()
    saved = sys.modules.get("ir", missing)
    sys.modules["ir"] = sys.modules[__name__]
    try:
        exec(compile(source, name, "exec"), module.__dict__)
    finally:
        if saved is missing:
            del sys.modules["ir"]
        else:
            sys.modules["ir"] = saved
    build = getattr(module, "build", None)
    if build is None:
        raise Refused(f"{name} holds no build(n, w)")
    program = build(n, w)
    if type(program) is not Program:
        raise Refused(f"{name}: build(n, w) gives no operation list of these forms")
    return program, module


def updates(program: Program) -> List[Tuple[int, int, Any]]:
    """Each update as (its index in the list's order, its phase's index, the update)."""
    out, index = [], 0
    for number, phase in enumerate(program.phases):
        for update in phase.updates:
            out.append((index, number, update))
            index += 1
    return out


# ---------------------------------------------------------------------- the scalar evaluation

def rotl(value: int, amount: int, w: int) -> int:
    amount %= w
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
    """Each update reads the values at the phase's start."""
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


def permute(program: Program, state: Sequence[int], constants: Sequence[Sequence[int]] = (),
            rounds: Optional[int] = None) -> List[int]:
    """The list applied once per row of the constant table, or `rounds` times with no table."""
    out = list(state)
    rows = list(constants) if constants else [()] * (1 if rounds is None else rounds)
    for row in rows:
        for phase in program.phases:
            apply_phase(phase, out, row, program.w)
    return out


# ------------------------------------------------------------------ what a trail's re-check reads

def lanes_read(expr: Any) -> Set[int]:
    kind = type(expr)
    if kind is Lane:
        return {expr.index}
    if kind is Constant:
        return set()
    if kind in UNARY:
        return lanes_read(expr.value)
    return lanes_read(expr.left) | lanes_read(expr.right)


def is_linear(expr: Any) -> bool:
    """Whether the expression is linear over GF(2) in the lanes it reads, up to a constant."""
    kind = type(expr)
    if kind in (Lane, Constant):
        return True
    if kind in UNARY:
        return is_linear(expr.value)
    return kind is Xor and is_linear(expr.left) and is_linear(expr.right)


def constant_inside(expr: Any, under: bool = False) -> bool:
    """Whether a constant stands under a bitwise function that is not linear, where its value, and
    not only a sign, changes a transition's weight."""
    kind = type(expr)
    if kind is Lane:
        return False
    if kind is Constant:
        return under
    if kind in UNARY:
        return constant_inside(expr.value, under)
    below = under or kind in (And, Or)
    return constant_inside(expr.left, below) or constant_inside(expr.right, below)


def reads_constant(expr: Any) -> bool:
    kind = type(expr)
    if kind is Lane:
        return False
    if kind is Constant:
        return True
    if kind in UNARY:
        return reads_constant(expr.value)
    return reads_constant(expr.left) or reads_constant(expr.right)


def linear(expr: Any, delta: Sequence[int], w: int) -> int:
    """The linear part of a linear expression applied to the lanes' differences."""
    kind = type(expr)
    if kind is Lane:
        return delta[expr.index]
    if kind is Constant:
        return 0
    if kind is Not:
        return linear(expr.value, delta, w)
    if kind is Rotl:
        return rotl(linear(expr.value, delta, w), expr.amount, w)
    if kind is Shl:
        return (linear(expr.value, delta, w) << expr.amount) & ((1 << w) - 1)
    if kind is Shr:
        return linear(expr.value, delta, w) >> expr.amount
    if kind is Xor:
        return linear(expr.left, delta, w) ^ linear(expr.right, delta, w)
    raise Refused("an expression that is not linear has no linear part")


def transpose(expr: Any, mask: int, into: Dict[int, int], w: int) -> None:
    """The transpose of a linear expression's map: the mask on its value, carried to the lanes it
    reads and added into `into`."""
    kind = type(expr)
    if kind is Lane:
        into[expr.index] = into.get(expr.index, 0) ^ mask
    elif kind is Constant:
        return
    elif kind is Not:
        transpose(expr.value, mask, into, w)
    elif kind is Rotl:
        transpose(expr.value, rotl(mask, w - expr.amount % w, w), into, w)
    elif kind is Shl:
        transpose(expr.value, mask >> expr.amount, into, w)
    elif kind is Shr:
        transpose(expr.value, (mask << expr.amount) & ((1 << w) - 1), into, w)
    elif kind is Xor:
        transpose(expr.left, mask, into, w)
        transpose(expr.right, mask, into, w)
    else:
        raise Refused("an expression that is not linear has no transpose")


def leaves(expr: Any, bit: int, w: int) -> List[Tuple[int, int]]:
    """The (lane, bit) places that bit `bit` of the expression reads, each once, in the order the
    expression names them from the left."""
    out: List[Tuple[int, int]] = []

    def walk(node: Any, i: int) -> None:
        kind = type(node)
        if kind is Lane:
            if (node.index, i) not in out:
                out.append((node.index, i))
        elif kind is Constant:
            return
        elif kind is Not:
            walk(node.value, i)
        elif kind is Rotl:
            walk(node.value, (i - node.amount) % w)
        elif kind is Shl:
            if i - node.amount >= 0:
                walk(node.value, i - node.amount)
        elif kind is Shr:
            if i + node.amount < w:
                walk(node.value, i + node.amount)
        else:
            walk(node.left, i)
            walk(node.right, i)

    walk(expr, bit)
    return out


def bit_of(expr: Any, bit: int, values: Dict[Tuple[int, int], int], row: Sequence[int], w: int) -> int:
    """Bit `bit` of the expression, the bits it reads given by place; a constant no table gives
    reads 0, which `constant_inside` shows to be a sign only."""
    kind = type(expr)
    if kind is Lane:
        return values[(expr.index, bit)]
    if kind is Constant:
        return (row[expr.index] >> bit) & 1 if row else 0
    if kind is Not:
        return 1 ^ bit_of(expr.value, bit, values, row, w)
    if kind is Rotl:
        return bit_of(expr.value, (bit - expr.amount) % w, values, row, w)
    if kind is Shl:
        return bit_of(expr.value, bit - expr.amount, values, row, w) if bit - expr.amount >= 0 else 0
    if kind is Shr:
        return bit_of(expr.value, bit + expr.amount, values, row, w) if bit + expr.amount < w else 0
    left, right = bit_of(expr.left, bit, values, row, w), bit_of(expr.right, bit, values, row, w)
    if kind is Xor:
        return left ^ right
    return left & right if kind is And else left | right
