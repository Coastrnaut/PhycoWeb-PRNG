"""Second known result of `costmodel-examples` (research R5, R12, R13): counts at other sizes and widths.

The same table of R5 and the same fields, counted by hand on other stated lists, at (n, w) = (8, 16) with
R = 24 and r = 1024, and at (2, 8) with R = 16 and r = 32. `cost` is L · n² · P · R / r.

    thirteen-inputs (8, 16)  P xor eight rotations of V(x) and four neighbours: k = 13, ceil(12 / 5) = 3,
                             so 3w LUTs and 3 levels.
    seventeen-inputs (8, 16) P xor twelve rotations of V(x) and four neighbours: k = 17, ceil(16 / 5) = 4.
    two-sets (8, 16)         for each class, V add rotl(P, 3), then V sub rotl(P, 5), both reading the same
                             word: two additions of one word each, 2w LUTs, and two additions on a path
                             through the vein, one chain per phase.
    three-levels (8, 16)     for each class, V(x) add (P(x) xor P(east x)), then P(x) xor (not V(x) and
                             rotl(V(x), 1)), then P(x) add V(south x): w + w, then w, then w, so 4w LUTs, with
                             2, 1 and 1 levels per class and P = 6. A round holds four addition phases, and
                             one path passes through all of them: V(x) of class 0, P(x) from it and its own
                             addition, V(y) of class 1 reading P(x) for y west of x, and P(y) from V(y) with
                             its own addition. So the most additions on a path is 4.
    two-by-two (2, 8)        the arx-box of `costmodel-examples` at 2×2: P = 4, 2w LUTs, one addition on any
                             path, and two distinct neighbours only.
"""
from fractions import Fraction

import ir

TOOL = "costmodel"
KNOWN_ID = "costmodel-examples-second"
SECOND_OF = "costmodel-examples"
SOURCE = "self-written: counted by hand in this file's docstring"
P, V = ir.PRESSURE, ir.VEIN


def word(n, i, j, kind):
    return ir.Lane(ir.lane(n, i, j, kind))


def each_class(n, update):
    return tuple(ir.Phase(colour, tuple(update(i, j) for i, j in ir.nodes_of(n, colour)))
                 for colour in range(ir.colours(n)))


def many_rotations(n, count):
    def update(i, j):
        expr = word(n, i, j, V)
        for t in range(1, count):
            expr = ir.Xor(expr, ir.Rotl(word(n, i, j, V), t))
        for near in (word(n, i, j + 1, V), word(n, i + 1, j, V), word(n, i, j - 1, V),
                     word(n, i - 1, j, V)):
            expr = ir.Xor(expr, near)
        return ir.Mix(ir.lane(n, i, j, P), "xor", expr)
    return each_class(n, update)


def thirteen_inputs(n, w):
    return many_rotations(n, 8)


def seventeen_inputs(n, w):
    return many_rotations(n, 12)


def two_sets(n, w):
    phases = []
    for colour in range(ir.colours(n)):
        nodes = ir.nodes_of(n, colour)
        phases.append(ir.Phase(colour, tuple(ir.Mix(ir.lane(n, i, j, V), "add",
                                                    ir.Rotl(word(n, i, j, P), 3))
                                             for i, j in nodes)))
        phases.append(ir.Phase(colour, tuple(ir.Mix(ir.lane(n, i, j, V), "sub",
                                                    ir.Rotl(word(n, i, j, P), 5))
                                             for i, j in nodes)))
    return tuple(phases)


def three_levels(n, w):
    phases = []
    for colour in range(ir.colours(n)):
        nodes = ir.nodes_of(n, colour)
        phases.append(ir.Phase(colour, tuple(
            ir.Mix(ir.lane(n, i, j, V), "add", ir.Xor(word(n, i, j, P), word(n, i, j + 1, P)))
            for i, j in nodes)))
        phases.append(ir.Phase(colour, tuple(
            ir.Mix(ir.lane(n, i, j, P), "xor",
                   ir.And(ir.Not(word(n, i, j, V)), ir.Rotl(word(n, i, j, V), 1)))
            for i, j in nodes)))
        phases.append(ir.Phase(colour, tuple(
            ir.Mix(ir.lane(n, i, j, P), "add", word(n, i + 1, j, V)) for i, j in nodes)))
    return tuple(phases)


def two_by_two(n, w):
    phases = []
    for colour in range(ir.colours(n)):
        nodes = ir.nodes_of(n, colour)
        phases.append(ir.Phase(colour, tuple(ir.Mix(ir.lane(n, i, j, V), "add", word(n, i, j, P))
                                             for i, j in nodes)))
        phases.append(ir.Phase(colour, tuple(ir.Mix(ir.lane(n, i, j, P), "xor",
                                                    ir.Rotl(word(n, i, j, V), 7))
                                             for i, j in nodes)))
    return tuple(phases)


def expected(n, w, rounds, rate, luts, chains, phases, depth):
    return {"n": n, "w": w, "rounds": rounds, "rate": rate, "luts": Fraction(luts), "chains": chains,
            "phases": phases, "depth": depth, "flip_flops": 2 * w,
            "cost": Fraction(luts) * n * n * phases * rounds / rate}


EXAMPLES = (
    ("thirteen-inputs", thirteen_inputs, expected(8, 16, 24, 1024, 48, 0, 2, (3, 3))),
    ("seventeen-inputs", seventeen_inputs, expected(8, 16, 24, 1024, 64, 0, 2, (4, 4))),
    ("two-sets", two_sets, expected(8, 16, 24, 1024, 32, 2, 4, (1, 1, 1, 1))),
    ("three-levels", three_levels, expected(8, 16, 24, 1024, 64, 4, 6, (2, 1, 1, 2, 1, 1))),
    ("two-by-two", two_by_two, expected(2, 8, 16, 32, 16, 1, 4, (1, 1, 1, 1))),
)


def build(name, builder, n, w):
    return ir.Program(name, n, w, builder(n, w))
