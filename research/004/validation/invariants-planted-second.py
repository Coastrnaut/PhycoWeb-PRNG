"""Second known result of `invariants-planted` (research R12, R13): the same forms, on the vein lanes.

Forms are written as in `invariants-planted`: (op, kind, region). What must match, exactly, is the set of
forms kept on every test state, after one round and after a full call of ROUNDS rounds, at w = 8, 16 and
32, a probabilistic firing on a planted list being reported and deciding nothing, as there. Below,
F(p) = rotl(p, 5) and G(v) = rotl(v, 3).

`vein-sum`, n = 4. For each class, V(x) add F(P(east x)), then V(x) sub F(P(south x)); then for each class,
P(x) xor G(V(x)). The count of `conserved-sum` with the kinds exchanged keeps the sums of V over each class
and over the state, and nothing else.

`vein-xor`, n = 4. For each class, V(x) xor (F(P(east x)) xor F(P(south x))); then for each class, P(x) add
G(V(x)). The XORs of V over each class and over the state are kept, and nothing else.

`colour-sum`, n = 3. Class 1, whose east and south both carry it one to one onto class 2: V(x) add
F(P(east x)), then V(x) sub F(P(south x)). Classes 0 and 2: V(x) xor F(P(east x)). Then, for each class,
P(x) xor G(V(x)). Only the sum of V over class 1 is kept.

`none`, n = 4. For each class, V(x) xor F(P(east x)); then for each class, P(x) add G(V(x)). As for the
`none` of `invariants-planted`, with the kinds exchanged: every form's change is uniform on uniform
states after one round, and none is kept.
"""
import ir

TOOL = "invariants"
KNOWN_ID = "invariants-planted-second"
SECOND_OF = "invariants-planted"
SOURCE = "self-written: derived by hand in this file's docstring"
WIDTHS = (8, 16, 32)
ROUNDS = 4
P, V = ir.PRESSURE, ir.VEIN


def f(n, i, j):
    return ir.Rotl(ir.Lane(ir.lane(n, i, j, P)), 5)


def g(n, i, j):
    return ir.Rotl(ir.Lane(ir.lane(n, i, j, V)), 3)


def pressures_take_veins(n, op):
    return tuple(ir.Phase(colour, tuple(ir.Mix(ir.lane(n, i, j, P), op, g(n, i, j))
                                        for i, j in ir.nodes_of(n, colour)))
                 for colour in range(ir.colours(n)))


def paired_sum(n, colour):
    nodes = ir.nodes_of(n, colour)
    return (ir.Phase(colour, tuple(ir.Mix(ir.lane(n, i, j, V), "add", f(n, i, j + 1))
                                   for i, j in nodes)),
            ir.Phase(colour, tuple(ir.Mix(ir.lane(n, i, j, V), "sub", f(n, i + 1, j))
                                   for i, j in nodes)))


def vein_sum(n, w):
    phases = paired_sum(n, 0) + paired_sum(n, 1)
    return ir.Program("vein-sum", n, w, phases + pressures_take_veins(n, "xor"))


def vein_xor(n, w):
    phases = tuple(ir.Phase(colour, tuple(
        ir.Mix(ir.lane(n, i, j, V), "xor", ir.Xor(f(n, i, j + 1), f(n, i + 1, j)))
        for i, j in ir.nodes_of(n, colour))) for colour in range(ir.colours(n)))
    return ir.Program("vein-xor", n, w, phases + pressures_take_veins(n, "add"))


def alone(n, colour):
    return ir.Phase(colour, tuple(ir.Mix(ir.lane(n, i, j, V), "xor", f(n, i, j + 1))
                                  for i, j in ir.nodes_of(n, colour)))


def colour_sum(n, w):
    phases = paired_sum(n, 1) + (alone(n, 0), alone(n, 2))
    return ir.Program("colour-sum", n, w, phases + pressures_take_veins(n, "xor"))


def none(n, w):
    phases = tuple(alone(n, colour) for colour in range(ir.colours(n)))
    return ir.Program("none", n, w, phases + pressures_take_veins(n, "add"))


SUMS = (("sum", "vein", "all"), ("sum", "vein", 0), ("sum", "vein", 1))
XORS = (("xor", "vein", "all"), ("xor", "vein", 0), ("xor", "vein", 1))
CLASS_1 = (("sum", "vein", 1),)
CASES = (
    ("vein-sum", 4, vein_sum, {1: SUMS, ROUNDS: SUMS}),
    ("vein-xor", 4, vein_xor, {1: XORS, ROUNDS: XORS}),
    ("colour-sum", 3, colour_sum, {1: CLASS_1, ROUNDS: CLASS_1}),
    ("none", 4, none, {1: (), ROUNDS: ()}),
)
