"""Feature 005: the re-check of `split` bounds and of trails (spec FR-016, FR-019, FR-020; data-model
sections 2 and 3; tasks T019, T020). Standard library and protocol/ only.

A trail's weight follows by exact integer arithmetic from its characteristic and the candidate's
committed operation list alone. A nonlinear operation is one of:

    a two-input addition or subtraction modulo 2^w    Mix(dst, add|sub, F), F reading a lane
    an addition or subtraction of a committed constant    Mix(dst, add|sub, F), F reading none
    an S-box                                           a bitwise function that is not linear

and an S-box is recorded in one of two ways. Where the candidate's module declares SBOX_UPDATES = k,
k updates in turn, one per phase, form one invertible map per bit position, and that map is the
S-box, recorded at its first update, before it, and after its last. Otherwise each update's function
F is the S-box, per bit position, over the bits it reads, an addition that follows F being its own
operation. In both, bit j of a recorded value is place j of the S-box: the written bit first, then
the bits read in the order the expression names them, a later update adding its new places.

A value is written "0x" and hexadecimal digits; a state as its lanes' words in lane order, separated
by one space; a weight as a rational, "p/q" or a whole number. An operation that the characteristic
does not record is inactive: its inputs are zero, and so is its output. A difference passes a linear
step through the step's map and a mask through its transpose; within a phase every update reads the
values at the phase's start.

The exact weights (spec FR-020): the differential probability and the squared correlation of a
two-input addition or subtraction, and of an addition of a constant c, a subtraction being the
addition of -c, each by the carry's automaton over the bits; an S-box's from its table. Each is
checked against an exhaustive count at w = 8 by tests/test_protocol_005.py.

Analysis code only. This module makes no security claim.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from protocol import oplist
from protocol.evidence import NONE, Refused

KINDS = ("differential", "linear")
THRESHOLD = Fraction(1, 1 << 128)
FINDING = "confirmed vulnerability"
ESTABLISHED = "no weakness identified within the analysis performed"


class Disagreement(Exception):
    """What the re-check recomputed differs from what the record holds."""


# ------------------------------------------------------------------------- the exact weights

def _majority(a: int, b: int, c: int) -> int:
    return (a & b) | (a & c) | (b & c)


def add_count(w: int, alpha: int, beta: int, gamma: int, sub: bool = False) -> int:
    """The number of pairs (x, y) of w-bit words, out of 4^w, with
    (x ^ alpha) op (y ^ beta) = (x op y) ^ gamma, op addition or subtraction modulo 2^w. The state
    is the pair of carries; a subtraction adds the complement with a carry in."""
    carry = int(sub)
    states = {(carry, carry): 1}
    for i in range(w):
        a, b, g = (alpha >> i) & 1, (beta >> i) & 1, (gamma >> i) & 1
        later: Dict[Tuple[int, int], int] = {}
        for (c, d), count in states.items():
            for x in (0, 1):
                for y in (0, 1):
                    first, second = y ^ carry, y ^ b ^ carry
                    if (x ^ first ^ c) ^ (x ^ a ^ second ^ d) != g:
                        continue
                    key = (_majority(x, first, c), _majority(x ^ a, second, d))
                    later[key] = later.get(key, 0) + count
        states = later
    return sum(states.values())


def add_constant_count(w: int, c: int, alpha: int, beta: int) -> int:
    """The number of w-bit words x, out of 2^w, with (x ^ alpha) + c = (x + c) ^ beta modulo 2^w:
    the two carries over the bits of c."""
    states = {(0, 0): 1}
    for i in range(w):
        a, b, k = (alpha >> i) & 1, (beta >> i) & 1, (c >> i) & 1
        later: Dict[Tuple[int, int], int] = {}
        for (p, q), count in states.items():
            for x in (0, 1):
                if (x ^ k ^ p) ^ (x ^ a ^ k ^ q) != b:
                    continue
                key = (_majority(x, k, p), _majority(x ^ a, k, q))
                later[key] = later.get(key, 0) + count
        states = later
    return sum(states.values())


def add_sum(w: int, u: int, v: int, t: int, sub: bool = False) -> int:
    """The sum over the 4^w pairs (x, y) of (-1)^(u.x ^ v.y ^ t.(x op y)): the correlation is the
    sum over 4^w, and its square the weight. The state is the carry."""
    carry = int(sub)
    states = {carry: 1}
    for i in range(w):
        a, b, g = (u >> i) & 1, (v >> i) & 1, (t >> i) & 1
        later: Dict[int, int] = {}
        for c, total in states.items():
            for x in (0, 1):
                for y in (0, 1):
                    second = y ^ carry
                    sign = (a & x) ^ (b & y) ^ (g & (x ^ second ^ c))
                    key = _majority(x, second, c)
                    later[key] = later.get(key, 0) + (-total if sign else total)
        states = later
    return sum(states.values())


def add_constant_sum(w: int, c: int, u: int, t: int) -> int:
    """The sum over the 2^w words x of (-1)^(u.x ^ t.(x + c))."""
    states = {0: 1}
    for i in range(w):
        a, g, k = (u >> i) & 1, (t >> i) & 1, (c >> i) & 1
        later: Dict[int, int] = {}
        for p, total in states.items():
            for x in (0, 1):
                sign = (a & x) ^ (g & (x ^ k ^ p))
                key = _majority(x, k, p)
                later[key] = later.get(key, 0) + (-total if sign else total)
        states = later
    return sum(states.values())


def parity(value: int) -> int:
    return bin(value).count("1") & 1


def table_count(table: Sequence[int], a: int, b: int) -> int:
    """The entry of an S-box's difference table: the inputs x with S(x) ^ S(x ^ a) = b."""
    return sum(1 for x in range(len(table)) if table[x] ^ table[x ^ a] == b)


def table_sum(table: Sequence[int], a: int, b: int) -> int:
    """The entry of an S-box's correlation table: the sum of (-1)^(a.x ^ b.S(x))."""
    return sum(-1 if parity(a & x) ^ parity(b & table[x]) else 1 for x in range(len(table)))


def classify(weight: Fraction) -> str:
    """Above 2^-128 a finding of the rounds the trail covers; at or below it, none (spec FR-020)."""
    return FINDING if weight > THRESHOLD else NONE


# -------------------------------------------------------------------------- values as text

def hexadecimal(value: int) -> str:
    return f"0x{value:x}"


def number(text: Any) -> int:
    if not isinstance(text, str) or not text.startswith("0x"):
        raise Disagreement(f"{text!r} is no value written 0x and hexadecimal digits")
    return int(text, 16)


def state_text(state: Sequence[int], w: int) -> str:
    digits = (w + 3) // 4
    return " ".join(f"{word:0{digits}x}" for word in state)


def state_of(text: Any, lanes: int, w: int) -> List[int]:
    words = text.split(" ") if isinstance(text, str) else []
    if len(words) != lanes:
        raise Disagreement(f"a state of {len(words)} words where the list has {lanes} lanes")
    out = [int(word, 16) for word in words]
    if any(word >> w for word in out):
        raise Disagreement("a state word is beyond the width")
    return out


def rational(value: Fraction) -> str:
    return str(value)


# ----------------------------------------------------------------- S-boxes over updates in turn

@dataclass
class Network:
    """One invertible map per bit position, made by updates in turn (spec FR-019)."""
    members: List[Tuple[int, int]]
    places: List[Tuple[int, int]]
    last_phase: int
    number: int = 0
    tables: Dict[Tuple[int, ...], List[int]] = field(default_factory=dict)


def bitwise(update: Any) -> bool:
    """An update whose function is a bitwise one that is not linear, added by XOR."""
    return type(update) is oplist.Mix and update.op == "xor" and not oplist.is_linear(update.expr)


def networks(program: oplist.Program, span: int) -> Dict[Tuple[int, int], Network]:
    """Each S-box that `span` updates in turn form, by each of its (update, bit) members. A list
    whose updates do not form such maps, or in which another update reads or writes a bit of an
    S-box in its turn, is refused: its trails have no weight defined (data-model section 3)."""
    w = program.w
    listed = oplist.updates(program)
    by_phase: Dict[int, List[Tuple[int, Any]]] = {}
    for index, phase, update in listed:
        by_phase.setdefault(phase, []).append((index, update))
    member_of: Dict[Tuple[int, int], Network] = {}
    owner: Dict[Tuple[int, Tuple[int, int]], Network] = {}
    count = 0
    for index, phase, update in listed:
        if not bitwise(update):
            continue
        for bit in range(w):
            if (index, bit) in member_of:
                continue
            places = [(update.dst, bit)]
            places += [p for p in oplist.leaves(update.expr, bit, w) if p not in places]
            members = [(index, bit)]
            for step in range(1, span):
                found = [(i, q) for i, u in by_phase.get(phase + step, ()) if bitwise(u)
                         for lane, q in places if lane == u.dst]
                if len(found) != 1:
                    raise Refused(f"{program.name}: update {index}, bit {bit}: {len(found)} updates "
                                  f"continue its S-box in phase {phase + step}")
                members.append(found[0])
                later = by_phase[phase + step]
                expr = next(u.expr for i, u in later if i == found[0][0])
                places += [p for p in oplist.leaves(expr, found[0][1], w) if p not in places]
            count += 1
            network = Network(members, places, phase + span - 1, count)
            for member in members:
                if member in member_of:
                    raise Refused(f"{program.name}: update {member[0]}, bit {member[1]} is in two S-boxes")
                member_of[member] = network
            for step in range(span):
                for place in places:
                    if owner.setdefault((phase + step, place), network) is not network:
                        raise Refused(f"{program.name}: lane {place[0]}, bit {place[1]} is in two "
                                      f"S-boxes in phase {phase + step}")
    for index, phase, update in listed:
        for bit in range(w):
            if type(update) is oplist.Rot:
                touched = [(update.dst, bit), (update.dst, (bit - update.amount) % w)]
            else:
                touched = [(update.dst, bit)] + oplist.leaves(update.expr, bit, w)
            mine = member_of.get((index, bit))
            for place in touched:
                held = owner.get((phase, place))
                if held is not None and held is not mine:
                    raise Refused(f"{program.name}: update {index}, bit {bit} touches lane {place[0]}, "
                                  f"bit {place[1]}, a bit of an S-box in its turn")
    return member_of


# ------------------------------------------------------------------------------- the walk

Chooser = Callable[[Tuple[int, Any], List[int], int, Optional[int], Callable[[List[int], int], Fraction]],
                   Tuple[List[int], int]]


class Walk:
    """One list, one kind of trail: a round's characteristic followed operation by operation. With
    `choose` it builds a characteristic instead, for the tests and for a tool's own use: `choose`
    gives the free inputs and the output of each active operation."""

    def __init__(self, program: oplist.Program, kind: str, span: Optional[int] = None):
        if kind not in KINDS:
            raise Refused(f"trail_kind {kind!r} is not one of {KINDS}")
        self.program, self.kind, self.w = program, kind, program.w
        self.lanes = 2 * program.n ** 2
        self.mask = (1 << program.w) - 1
        self.listed = oplist.updates(program)
        self.by_index = {index: update for index, _, update in self.listed}
        self.member_of = networks(program, span) if span else {}
        self.leaves: Dict[Tuple[int, int], List[Tuple[int, int]]] = {}
        self.weight = Fraction(1)

    # -- one operation

    def step(self, entries: Optional[Dict], built: List[Dict], choose: Optional[Chooser],
             key: Tuple[int, Any], fixed: List[int], free: int, weigh: Callable[[List[int], int], Fraction],
             required: bool = False, output: Optional[int] = None) -> Optional[Tuple[List[int], int]]:
        name = f"operation {key[0]}" + ("" if key[1] is None else f", position {key[1]}")
        if entries is None:
            if not required and not any(fixed):
                return None
            inputs, out = choose(key, list(fixed), free, output, weigh)
            weight = weigh(inputs, out)
            if weight == 0:
                raise Refused(f"{name}: the chosen transition has weight 0")
            built.append({"op_index": key[0], "position": NONE if key[1] is None else key[1],
                          "inputs": [hexadecimal(v) for v in inputs], "output": hexadecimal(out),
                          "weight": rational(weight)})
        else:
            entry = entries.pop(key, None)
            if entry is None:
                if required or any(fixed):
                    raise Disagreement(f"{name} is active and the characteristic does not record it")
                return None
            inputs = [number(v) for v in entry.get("inputs", ())]
            out = number(entry.get("output"))
            if len(inputs) != len(fixed) + free or inputs[:len(fixed)] != list(fixed):
                raise Disagreement(f"{name}: the recorded inputs {entry.get('inputs')} differ from "
                                   f"{[hexadecimal(v) for v in fixed]}, which the operation list gives")
            if output is not None and out != output:
                raise Disagreement(f"{name}: the recorded output {entry.get('output')} differs from "
                                   f"{hexadecimal(output)}")
            weight = weigh(inputs, out)
            if weight == 0:
                raise Disagreement(f"{name}: the recorded transition is impossible")
            try:
                recorded = Fraction(entry.get("weight"))
            except (TypeError, ValueError, ZeroDivisionError):
                raise Disagreement(f"{name}: the weight {entry.get('weight')!r} is no rational")
            if recorded != weight:
                raise Disagreement(f"{name}: the recorded weight {entry.get('weight')} differs from "
                                   f"{rational(weight)}")
        self.weight *= weight
        return inputs, out

    # -- tables

    def places_of(self, index: int, bit: int) -> List[Tuple[int, int]]:
        key = (index, bit)
        if key not in self.leaves:
            self.leaves[key] = oplist.leaves(self.by_index[index].expr, bit, self.w)
        return self.leaves[key]

    def function_table(self, index: int, bit: int, row: Sequence[int]) -> List[int]:
        places, expr = self.places_of(index, bit), self.by_index[index].expr
        return [oplist.bit_of(expr, bit, {p: (x >> j) & 1 for j, p in enumerate(places)}, row, self.w)
                for x in range(1 << len(places))]

    def network_table(self, network: Network, row: Sequence[int]) -> List[int]:
        key = tuple(row)
        if key not in network.tables:
            table = []
            for x in range(1 << len(network.places)):
                values = {p: (x >> j) & 1 for j, p in enumerate(network.places)}
                for index, bit in network.members:
                    update = self.by_index[index]
                    values[(update.dst, bit)] ^= oplist.bit_of(update.expr, bit, values, row, self.w)
                table.append(sum(values[p] << j for j, p in enumerate(network.places)))
            if sorted(table) != list(range(len(table))):
                raise Refused(f"{self.program.name}: the updates of an S-box form no invertible map")
            network.tables[key] = table
        return network.tables[key]

    def pack(self, state: Sequence[int], places: Sequence[Tuple[int, int]]) -> int:
        return sum(((state[lane] >> bit) & 1) << j for j, (lane, bit) in enumerate(places))

    # -- one round

    def round(self, state: Sequence[int], row: Sequence[int], entries: Optional[Dict],
              choose: Optional[Chooser] = None) -> Tuple[List[int], List[Dict]]:
        """The state after one pass of the list, with the operations built where `entries` is None."""
        state, built = list(state), []
        differential = self.kind == "differential"
        w, mask = self.w, self.mask
        pending: Dict[int, int] = {}
        position = 0
        for number_of_phase, phase in enumerate(self.program.phases):
            start = position
            position += len(phase.updates)
            written = {update.dst for update in phase.updates}
            for update in phase.updates:
                if type(update) is oplist.Mix and oplist.lanes_read(update.expr) & written:
                    raise Refused(f"{self.program.name}: an update of phase {number_of_phase} reads "
                                  "a lane that the phase writes")
            new: Dict[int, int] = {}
            carried: Dict[int, int] = {}
            finishing: List[Network] = []
            for offset, update in enumerate(phase.updates):
                index = start + offset
                if type(update) is oplist.Rot:
                    new[update.dst] = oplist.rotl(state[update.dst], update.amount, w)
                    continue
                expr, held = update.expr, state[update.dst]
                straight = oplist.is_linear(expr)
                if not row and oplist.constant_inside(expr):
                    raise Refused(f"operation {index} holds a constant under a bitwise function, and "
                                  "the record names no constant table")
                if not straight and update.op == "xor" and self.member_of:
                    for bit in range(w):
                        network = self.member_of[(index, bit)]
                        if network.members[0] == (index, bit):
                            table = self.network_table(network, row)
                            size = len(network.places)
                            if differential:
                                weigh = lambda i, o, t=table, s=size: Fraction(table_count(t, i[0], o), 1 << s)
                            else:
                                weigh = lambda i, o, t=table, s=size: Fraction(table_sum(t, i[0], o) ** 2, 1 << (2 * s))
                            found = self.step(entries, built, choose, (index, bit),
                                              [self.pack(state, network.places)], 0, weigh)
                            if found is not None:
                                pending[network.number] = found[1]
                        if network.members[-1] == (index, bit) and network.number in pending:
                            finishing.append(network)
                    continue
                # The value of F: its difference, or the mask on it, bit by bit where F is not linear.
                if differential:
                    if straight:
                        value = oplist.linear(expr, state, w)
                    else:
                        value = 0
                        for bit in range(w):
                            places = self.places_of(index, bit)
                            if not places:
                                continue
                            table = None
                            a = self.pack(state, places)
                            if a:
                                table = self.function_table(index, bit, row)
                            weigh = lambda i, o, t=table, s=len(places): Fraction(table_count(t, i[0], o), 1 << s)
                            found = self.step(entries, built, choose, (index, bit), [a], 0, weigh)
                            if found is not None:
                                if found[1] > 1:
                                    raise Disagreement(f"operation {index}, position {bit}: the output of a "
                                                       "function of one bit is 0 or 1")
                                value |= found[1] << bit
                    if update.op == "xor":
                        new[update.dst] = held ^ value
                    elif oplist.lanes_read(expr):
                        sub = update.op == "sub"
                        weigh = lambda i, o, s=sub: Fraction(add_count(w, i[0], i[1], o, s), 1 << (2 * w))
                        found = self.step(entries, built, choose, (index, None), [held, value], 0, weigh)
                        new[update.dst] = found[1] if found else 0
                    else:
                        c = self.constant(index, update, row)
                        weigh = lambda i, o, k=c: Fraction(add_constant_count(w, k, i[0], o), 1 << w)
                        found = self.step(entries, built, choose, (index, None), [held], 0, weigh)
                        new[update.dst] = found[1] if found else 0
                    continue
                # Masks: the mask on the written lane, then the mask on F's value, carried to its lanes.
                if update.op == "xor":
                    new[update.dst] = on_value = held
                elif oplist.lanes_read(expr):
                    sub = update.op == "sub"
                    weigh = lambda i, o, s=sub: Fraction(add_sum(w, i[0], i[1], o, s) ** 2, 1 << (4 * w))
                    found = self.step(entries, built, choose, (index, None), [held], 1, weigh)
                    on_value = found[0][1] if found else 0
                    new[update.dst] = found[1] if found else 0
                else:
                    c = self.constant(index, update, row)
                    weigh = lambda i, o, k=c: Fraction(add_constant_sum(w, k, i[0], o) ** 2, 1 << (2 * w))
                    found = self.step(entries, built, choose, (index, None), [held], 0, weigh)
                    new[update.dst] = found[1] if found else 0
                    continue
                if straight:
                    oplist.transpose(expr, on_value, carried, w)
                    continue
                for bit in range(w):
                    places = self.places_of(index, bit)
                    if not places:
                        continue
                    if not (on_value >> bit) & 1:
                        found = self.step(entries, built, choose, (index, bit), [], 1,
                                          lambda i, o: Fraction(int(i[0] == 0 and o == 0)), output=0) \
                            if entries is not None and (index, bit) in entries else None
                        continue
                    table = self.function_table(index, bit, row)
                    weigh = lambda i, o, t=table, s=len(places): Fraction(table_sum(t, i[0], o) ** 2, 1 << (2 * s))
                    found = self.step(entries, built, choose, (index, bit), [], 1, weigh, required=True, output=1)
                    for j, (lane, place) in enumerate(places):
                        if (found[0][0] >> j) & 1:
                            carried[lane] = carried.get(lane, 0) ^ (1 << place)
            for lane, value in carried.items():
                state[lane] ^= value
            for lane, value in new.items():
                state[lane] = value & mask
            for network in finishing:
                out = pending.pop(network.number)
                for j, (lane, bit) in enumerate(network.places):
                    state[lane] = (state[lane] & ~(1 << bit)) | (((out >> j) & 1) << bit)
        if pending:
            raise Refused(f"{self.program.name}: an S-box does not end within the round")
        return state, built

    def constant(self, index: int, update: Any, row: Sequence[int]) -> int:
        """The constant an update adds, a subtraction being the addition of its negative."""
        if oplist.reads_constant(update.expr) and not row:
            raise Refused(f"operation {index} adds a committed constant, and the record names no "
                          "constant table")
        c = oplist.evaluate(update.expr, [0] * self.lanes, row, self.w)
        return (-c) & self.mask if update.op == "sub" else c


def build(program: oplist.Program, kind: str, state: Sequence[int], rows: Sequence[Sequence[int]],
          choose: Chooser, span: Optional[int] = None) -> Tuple[List[Dict], Fraction]:
    """A characteristic over one round per row, from a state and a chooser, with its weight."""
    walk = Walk(program, kind, span)
    out, state = [], list(state)
    for number_of_round, row in enumerate(rows, 1):
        after, operations = walk.round(state, row, None, choose)
        out.append({"round": number_of_round, "state_in": state_text(state, program.w),
                    "operations": operations, "state_out": state_text(after, program.w)})
        state = after
    return out, walk.weight


def recompute(program: oplist.Program, kind: str, characteristic: Any, rows: Sequence[Sequence[int]],
              span: Optional[int] = None) -> Fraction:
    """A trail's weight from its characteristic and the operation list, every transition checked."""
    walk = Walk(program, kind, span)
    if not isinstance(characteristic, list) or len(characteristic) != len(rows) or not rows:
        raise Disagreement(f"a characteristic of {len(characteristic) if isinstance(characteristic, list) else 0} "
                           f"rounds where the record covers {len(rows)}")
    previous: Optional[List[int]] = None
    for number_of_round, (entry, row) in enumerate(zip(characteristic, rows), 1):
        if entry.get("round") != number_of_round:
            raise Disagreement(f"round {entry.get('round')!r} where round {number_of_round} stands")
        state = state_of(entry.get("state_in"), walk.lanes, walk.w)
        if previous is not None and state != previous:
            raise Disagreement(f"round {number_of_round} starts from another state than round "
                               f"{number_of_round - 1} ends in")
        entries: Dict[Tuple[int, Any], Dict] = {}
        for operation in entry.get("operations") or ():
            place = operation.get("position")
            key = (operation.get("op_index"), None if place == NONE else place)
            if key in entries:
                raise Disagreement(f"round {number_of_round}: operation {key[0]} is recorded twice")
            entries[key] = operation
        try:
            after, _ = walk.round(state, row, entries)
        except Disagreement as exc:
            raise Disagreement(f"round {number_of_round}: {exc}")
        if entries:
            key = sorted(entries, key=lambda k: (k[0], -1 if k[1] is None else k[1]))[0]
            raise Disagreement(f"round {number_of_round}: operation {key[0]} is recorded, and the "
                               "operation list has no nonlinear operation there")
        if after != state_of(entry.get("state_out"), walk.lanes, walk.w):
            raise Disagreement(f"round {number_of_round}: the state at its end is "
                               f"{state_text(after, walk.w)}")
        previous = after
    return walk.weight


# ------------------------------------------------------------------- a record's re-check

def table_rows(record: Dict, show: Callable[[str], Optional[bytes]], sha256: Callable[[bytes], str],
               rounds: int) -> List[Sequence[int]]:
    """The rows of the constant table the record names by SHA-256, one per round of the trail, or
    empty rows where it names none."""
    named = record.get("constants", NONE)
    if named in (NONE, None):
        return [()] * rounds
    blob = show(named.get("path", ""))
    if blob is None:
        raise Disagreement(f"the constant table {named.get('path')} is not committed")
    if sha256(blob) != named.get("sha256"):
        raise Disagreement(f"the constant table {named.get('path')} has another SHA-256 than the record names")
    table = [[int(word, 16) for word in row] for row in json.loads(blob.decode("utf-8"))["table"]]
    first = int(record.get("first_round", 1))
    if first < 1 or first - 1 + rounds > len(table):
        raise Disagreement(f"rounds {first} to {first - 1 + rounds} are beyond the constant table's {len(table)} rows")
    return table[first - 1:first - 1 + rounds]


def trail_found(record: Dict, source: Optional[bytes], rows: Callable[[int], List[Sequence[int]]],
                log2: Callable[[str], float]) -> Dict:
    """What the re-check recomputes of a `trail` record, for comparison with its fields: its weight,
    the weight's -log2 and its class; `transitions` holds a disagreement's text."""
    try:
        if source is None:
            raise Disagreement(f"the operation list of {record.get('candidate')} is not committed")
        rounds = record.get("rounds")
        if type(rounds) is not int or rounds < 1:
            raise Disagreement(f"rounds {rounds!r}")
        program, module = oplist.read(source, str(record.get("candidate")), record["size"], record["width"])
        weight = recompute(program, record.get("trail_kind"), record.get("characteristic"), rows(rounds),
                           getattr(module, "SBOX_UPDATES", None))
    except (Disagreement, Refused) as exc:
        return {"transitions": str(exc)}
    try:
        same = Fraction(record.get("weight")) == weight
    except (TypeError, ValueError, ZeroDivisionError):
        same = False
    text = record["weight"] if same else rational(weight)
    return {"weight": text, "weight_log2": log2(text), "classification": classify(weight)}


def established(record: Dict, bound_of: Callable[[Dict], Optional[str]]) -> Optional[Fraction]:
    """A bound record's established weight: a searched record's while it reads `pass` and is not
    capped, by the re-check's own reading of its rows; a `split` record's own."""
    if record.get("kind") != "bound" or record.get("status") != "pass" or record.get("capped") is True:
        return None
    text = record.get("bound") if record.get("method") == "split" else bound_of(record)
    try:
        return None if text in (None, NONE) else Fraction(text)
    except (TypeError, ValueError, ZeroDivisionError):
        return None


SAME = ("candidate", "bound_kind", "size", "width")


def split_found(record: Dict, records: Dict[str, Tuple[bytes, Dict]], sha256: Callable[[bytes], str],
                bound_of: Callable[[Dict], Optional[str]], defect: Callable[[str], bool],
                depth: int = 0) -> Dict:
    """What the re-check recomputes of a `split` bound: the sum of its two parts' weights, each part
    read from its committed bytes. `sum` holds a disagreement's text (data-model section 2)."""

    def wrong(text: str) -> Dict:
        return {"sum": text}

    parts = record.get("parts")
    rounds = record.get("rounds")
    if not isinstance(parts, list) or len(parts) != 2:
        return wrong("a split bound has two parts")
    if type(rounds) is not int or rounds < 2:
        return wrong(f"rounds {rounds!r}: a split bound covers at least 2")
    total, covered = Fraction(0), 0
    for part in parts:
        name = part.get("record_id")
        held = records.get(name)
        if held is None:
            return wrong(f"the part {name} is not committed")
        blob, other = held
        if part.get("sha256_kind") != "raw" or sha256(blob) != part.get("sha256"):
            return wrong(f"the part {name} has another SHA-256 than the record names")
        if any(other.get(key) != record.get(key) for key in SAME):
            return wrong(f"the part {name} is of another candidate, kind, size or width")
        if defect(name):
            return wrong(f"the part {name} no longer stands: a tool defect is recorded against it")
        weight = established(other, bound_of)
        if weight is None:
            return wrong(f"the part {name} is not an established bound: status {other.get('status')}")
        if other.get("method") == "split":
            if depth > 64:
                return wrong(f"the part {name}: sums nested beyond 64")
            below = split_found(other, records, sha256, bound_of, defect, depth + 1)
            if "sum" in below:
                return wrong(f"the part {name} no longer stands: {below['sum']}")
            if Fraction(below["bound"]) != weight:
                return wrong(f"the part {name} no longer stands: its own sum is {below['bound']}")
        try:
            stated = Fraction(part.get("bound"))
        except (TypeError, ValueError, ZeroDivisionError):
            return wrong(f"the part {name}: its bound {part.get('bound')!r} is no rational")
        if other.get("rounds") != part.get("rounds") or stated != weight:
            return wrong(f"the part {name} holds {rational(weight)} over {other.get('rounds')} rounds, "
                         f"and the record states {part.get('bound')} over {part.get('rounds')}")
        total += weight
        covered += other["rounds"]
    if covered != rounds:
        return wrong(f"the parts cover {covered} rounds, and the record {rounds}")
    # The splits compared and the searched bound, among the records that existed when it was written.
    earlier = [other for _, other in records.values()
               if all(other.get(key) == record.get(key) for key in SAME)
               and other.get("record_id") != record.get("record_id")
               and str(other.get("created_utc", "")) <= str(record.get("created_utc", ""))]
    best: Dict[int, Fraction] = {}
    searched: Optional[Fraction] = None
    for other in earlier:
        weight = established(other, bound_of)
        if weight is None or defect(other.get("record_id", "")):
            continue
        r = other.get("rounds")
        best[r] = max(best.get(r, weight), weight)
        if r == rounds and other.get("method") != "split":
            searched = weight if searched is None else max(searched, weight)
    sums = [best[r] + best[rounds - r] for r in range(1, rounds // 2 + 1) if r in best and rounds - r in best]
    found: Dict[str, Any] = {"status": "pass", "classification": ESTABLISHED, "alternatives": len(sums),
                             "searched": NONE if searched is None else rational(searched)}
    try:
        same = Fraction(record.get("bound")) == total
    except (TypeError, ValueError, ZeroDivisionError):
        same = False
    found["bound"] = record["bound"] if same else rational(total)
    if record.get("searched", NONE) != NONE and searched is not None:
        try:
            if Fraction(record["searched"]) == searched:
                found["searched"] = record["searched"]
        except (TypeError, ValueError, ZeroDivisionError):
            pass
    if sums and max(sums) != total:
        return dict(found, sum=f"the largest sum of two established bounds is {rational(max(sums))}")
    if searched is not None and searched >= total:
        return dict(found, sum=f"the searched bound {rational(searched)} is no smaller than the sum")
    return found
