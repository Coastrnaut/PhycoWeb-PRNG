"""Known result `invariants-planted` of the invariant checks (research R13; data-model section 7).

Stated lists at 4×4 with a planted conserved sum modulo 2^w and a planted kept XOR, at 3×3 with a planted
colour-class form, and one with none. A form is written (op, kind, region): op is `sum` or `xor`, kind
is `pressure` or `vein`, and region is `all` or a colour class. What must match, exactly, is the set of
forms kept on every test state, after one round and after a full call of ROUNDS rounds, at w = 8, 16
and 32. A planted form also raises the rate of forms it shares bits with, such as the sum and the XOR over
one region, whose low bits agree, so that a probabilistic firing on a planted list, at w = 8 above all, is
reported and decides nothing here; on `none` nothing is kept and nothing fires. Below, x runs over a
class, east(x) and south(x) are its neighbours, F(v) = rotl(v, 1) and G(p) = rotl(p, 3).

`conserved-sum`, n = 4. For each class c in turn, P(x) add F(V(east x)), then P(x) sub F(V(south x)); then
for each class, V(x) xor G(P(x)). No V changes in the first four phases, and east and south each carry
class c one to one onto the other class, so that the sum over x of what is added equals the sum of what
is taken away. So the sums of P over class 0, over class 1 and over the whole state are kept. No other
form is: each V changes by a rotation of a pressure, and each P by words that do not cancel in XOR.

`kept-xor`, n = 4. For each class, P(x) xor (F(V(east x)) xor F(V(south x))); then for each class, V(x) add
G(P(x)). The same count, with each word of the other class entering twice, keeps the XORs of P over each
class and over the state, and nothing else.

`colour-class`, n = 3, where c(i, j) = (i + j) mod 3 and east and south both carry class 0 one to one
onto class 1. Class 0: P(x) xor (F(V(east x)) xor F(V(south x))). Classes 1 and 2: P(x) add F(V(east x)),
each word entering once. Then, for each class, V(x) xor G(P(x)). After one round only the XOR of P over
class 0, call it Q, is kept. Q then enters the XOR of V over class 0, which changes by rotl(Q, 3) in every
round, the same word each time, so that an even number of rounds cancels: after the full call of 4 rounds
that form is kept as well, and after one round it is not.

`none`, n = 4. For each class, P(x) add F(V(east x)); then for each class, V(x) xor G(P(x)). Every form's
change is uniform on uniform states after one round: for fixed P the map from V to the change of P is
one to one, the same holds for V's change given a uniform P, and the lanes are independent. So a form
holds on one test state in 2^w, its chance rate, and none is kept.
"""
import ir

TOOL = "invariants"
KNOWN_ID = "invariants-planted"
SECOND_OF = "none"
SOURCE = "self-written: derived by hand in this file's docstring"
WIDTHS = (8, 16, 32)
ROUNDS = 4
P, V = ir.PRESSURE, ir.VEIN


def f(n, i, j):
    return ir.Rotl(ir.Lane(ir.lane(n, i, j, V)), 1)


def g(n, i, j):
    return ir.Rotl(ir.Lane(ir.lane(n, i, j, P)), 3)


def veins_take_pressures(n, op):
    return tuple(ir.Phase(colour, tuple(ir.Mix(ir.lane(n, i, j, V), op, g(n, i, j))
                                        for i, j in ir.nodes_of(n, colour)))
                 for colour in range(ir.colours(n)))


def conserved_sum(n, w):
    phases = []
    for colour in range(ir.colours(n)):
        nodes = ir.nodes_of(n, colour)
        phases.append(ir.Phase(colour, tuple(ir.Mix(ir.lane(n, i, j, P), "add", f(n, i, j + 1))
                                             for i, j in nodes)))
        phases.append(ir.Phase(colour, tuple(ir.Mix(ir.lane(n, i, j, P), "sub", f(n, i + 1, j))
                                             for i, j in nodes)))
    return ir.Program("conserved-sum", n, w, tuple(phases) + veins_take_pressures(n, "xor"))


def twice(n, i, j):
    return ir.Xor(f(n, i, j + 1), f(n, i + 1, j))


def kept_xor(n, w):
    phases = tuple(ir.Phase(colour, tuple(ir.Mix(ir.lane(n, i, j, P), "xor", twice(n, i, j))
                                          for i, j in ir.nodes_of(n, colour)))
                   for colour in range(ir.colours(n)))
    return ir.Program("kept-xor", n, w, phases + veins_take_pressures(n, "add"))


def colour_class(n, w):
    phases = [ir.Phase(0, tuple(ir.Mix(ir.lane(n, i, j, P), "xor", twice(n, i, j))
                                for i, j in ir.nodes_of(n, 0)))]
    for colour in (1, 2):
        phases.append(ir.Phase(colour, tuple(ir.Mix(ir.lane(n, i, j, P), "add", f(n, i, j + 1))
                                             for i, j in ir.nodes_of(n, colour))))
    return ir.Program("colour-class", n, w, tuple(phases) + veins_take_pressures(n, "xor"))


def none(n, w):
    phases = tuple(ir.Phase(colour, tuple(ir.Mix(ir.lane(n, i, j, P), "add", f(n, i, j + 1))
                                          for i, j in ir.nodes_of(n, colour)))
                   for colour in range(ir.colours(n)))
    return ir.Program("none", n, w, phases + veins_take_pressures(n, "xor"))


SUMS = (("sum", "pressure", "all"), ("sum", "pressure", 0), ("sum", "pressure", 1))
XORS = (("xor", "pressure", "all"), ("xor", "pressure", 0), ("xor", "pressure", 1))
CLASS_0 = (("xor", "pressure", 0),)
CASES = (
    ("conserved-sum", 4, conserved_sum, {1: SUMS, ROUNDS: SUMS}),
    ("kept-xor", 4, kept_xor, {1: XORS, ROUNDS: XORS}),
    ("colour-class", 3, colour_class, {1: CLASS_0, ROUNDS: CLASS_0 + (("xor", "vein", 0),)}),
    ("none", 4, none, {1: (), ROUNDS: ()}),
)
