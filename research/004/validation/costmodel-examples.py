"""Known result `costmodel-examples` of the cost model (research R5, R13; data-model section 7).

Each example applies one row of R5's table to a stated list, counted by hand at n = 4, w = 32, for one
output rate r = 768 and R = 32 rounds. What must match is every number, exactly. The counts, per node and
round, with k the input bits per output bit of one bitwise function, dst included when the update is an
XOR, and constant bits among them:

    rotation or shift by a constant, wiring, a register stage     0 LUTs, 0 chains
    bitwise, k <= 6                                               w LUTs
    bitwise, k > 6                                                w · ceil((k - 1) / 5) LUTs
    addition or subtraction of two words                          w LUTs, one chain of w bits

`luts` is L, the LUTs per node and round; `chains` the most additions on a dependency path within a round;
`phases` is P; `depth` holds the LUT levels of each phase's longest path, ceil((k - 1) / 5) for a bitwise
function and one more for each dependent operation; `flip_flops` is 2w per node; and `cost` is the cost per
output bit, L · n² · P · R / r. Round constants held in ROM are not counted, though a constant's bits count
as inputs of the function they enter.

    rotations          Rot at every node, one phase per class: nothing to count.
    xor-two            P xor rotl(V, 5): k = 2, one function.
    six-inputs         P xor V(x), V(east), V(south), V(west), V(north): k = 6, the largest of one LUT.
    seven-inputs       the same with rotl(V(x), 1): k = 7, ceil(6 / 5) = 2 levels and 2w LUTs.
    twelve-inputs      P with seven rotations of V(x) and four neighbours: k = 12, ceil(11 / 5) = 3.
    chi-row            P xor (not V and rotl(V, 1)): k = 3.
    shifted            P xor ((V >> 3) xor (V << 5)): k = 3; the shifts cost nothing.
    addition           V add P: the addition alone, F being one word.
    subtraction        V sub rotl(P, 9): a subtraction counts as an addition, a rotation as nothing.
    addition-function  V add (rotl(P, 3) xor P(east)): F is a function with k = 2, w LUTs, then w for
                       the addition, 2w in all, two levels, one chain.
    dependent          class 0: V add P; class 1: V add V(east). A class 1 vein reads a class 0 vein
                       written one phase before, so that a path holds two additions in one round.
    arx-box            for each class, V add P, then P xor rotl(V, 7): P = 4, 2w LUTs, and one addition
                       on any path, since no later phase of the round reads what these write.
    food               P xor a constant at the three food nodes (0,0), (0,1), (1,2): k = 2 at three nodes
                       of sixteen, so L = 3w / 16 = 6.
"""
from fractions import Fraction

import ir

TOOL = "costmodel"
KNOWN_ID = "costmodel-examples"
SECOND_OF = "none"
SOURCE = "self-written: counted by hand in this file's docstring"
N, W = 4, 32
R, RATE = 32, 768
P, V = ir.PRESSURE, ir.VEIN


def each_class(n, update):
    """One phase per class, `update(i, j)` at each of its nodes."""
    return tuple(ir.Phase(colour, tuple(update(i, j) for i, j in ir.nodes_of(n, colour)))
                 for colour in range(ir.colours(n)))


def word(n, i, j, kind):
    return ir.Lane(ir.lane(n, i, j, kind))


def fold(first, *others):
    expr = first
    for other in others:
        expr = ir.Xor(expr, other)
    return expr


def neighbours(n, i, j):
    return (word(n, i, j + 1, V), word(n, i + 1, j, V), word(n, i, j - 1, V), word(n, i - 1, j, V))


def rotations(n, w):
    return each_class(n, lambda i, j: ir.Rot(ir.lane(n, i, j, P), 7))


def xor_two(n, w):
    return each_class(n, lambda i, j: ir.Mix(ir.lane(n, i, j, P), "xor",
                                             ir.Rotl(word(n, i, j, V), 5)))


def six_inputs(n, w):
    return each_class(n, lambda i, j: ir.Mix(ir.lane(n, i, j, P), "xor",
                                             fold(word(n, i, j, V), *neighbours(n, i, j))))


def seven_inputs(n, w):
    return each_class(n, lambda i, j: ir.Mix(
        ir.lane(n, i, j, P), "xor",
        fold(word(n, i, j, V), ir.Rotl(word(n, i, j, V), 1), *neighbours(n, i, j))))


def twelve_inputs(n, w):
    return each_class(n, lambda i, j: ir.Mix(
        ir.lane(n, i, j, P), "xor",
        fold(word(n, i, j, V), *(ir.Rotl(word(n, i, j, V), t) for t in range(1, 7)),
             *neighbours(n, i, j))))


def chi_row(n, w):
    return each_class(n, lambda i, j: ir.Mix(
        ir.lane(n, i, j, P), "xor",
        ir.And(ir.Not(word(n, i, j, V)), ir.Rotl(word(n, i, j, V), 1))))


def shifted(n, w):
    return each_class(n, lambda i, j: ir.Mix(
        ir.lane(n, i, j, P), "xor",
        ir.Xor(ir.Shr(word(n, i, j, V), 3), ir.Shl(word(n, i, j, V), 5))))


def addition(n, w):
    return each_class(n, lambda i, j: ir.Mix(ir.lane(n, i, j, V), "add", word(n, i, j, P)))


def subtraction(n, w):
    return each_class(n, lambda i, j: ir.Mix(ir.lane(n, i, j, V), "sub",
                                             ir.Rotl(word(n, i, j, P), 9)))


def addition_function(n, w):
    return each_class(n, lambda i, j: ir.Mix(
        ir.lane(n, i, j, V), "add", ir.Xor(ir.Rotl(word(n, i, j, P), 3), word(n, i, j + 1, P))))


def dependent(n, w):
    return (ir.Phase(0, tuple(ir.Mix(ir.lane(n, i, j, V), "add", word(n, i, j, P))
                              for i, j in ir.nodes_of(n, 0))),
            ir.Phase(1, tuple(ir.Mix(ir.lane(n, i, j, V), "add", word(n, i, j + 1, V))
                              for i, j in ir.nodes_of(n, 1))))


def arx_box(n, w):
    phases = []
    for colour in range(ir.colours(n)):
        nodes = ir.nodes_of(n, colour)
        phases.append(ir.Phase(colour, tuple(ir.Mix(ir.lane(n, i, j, V), "add", word(n, i, j, P))
                                             for i, j in nodes)))
        phases.append(ir.Phase(colour, tuple(ir.Mix(ir.lane(n, i, j, P), "xor",
                                                    ir.Rotl(word(n, i, j, V), 7))
                                             for i, j in nodes)))
    return tuple(phases)


def food(n, w):
    return (ir.Phase(0, (ir.Mix(ir.lane(n, 0, 0, P), "xor", ir.Constant(0)),)),
            ir.Phase(1, (ir.Mix(ir.lane(n, 0, 1, P), "xor", ir.Constant(1)),
                         ir.Mix(ir.lane(n, 1, 2, P), "xor", ir.Constant(2)))))


def expected(luts, chains, phases, depth):
    """`cost` follows from the rest: L · n² · P · R / r."""
    return {"luts": Fraction(luts), "chains": chains, "phases": phases, "depth": depth,
            "flip_flops": 2 * W, "cost": Fraction(luts) * N * N * phases * R / RATE}


EXAMPLES = (
    ("rotations", rotations, expected(0, 0, 2, (0, 0))),
    ("xor-two", xor_two, expected(W, 0, 2, (1, 1))),
    ("six-inputs", six_inputs, expected(W, 0, 2, (1, 1))),
    ("seven-inputs", seven_inputs, expected(2 * W, 0, 2, (2, 2))),
    ("twelve-inputs", twelve_inputs, expected(3 * W, 0, 2, (3, 3))),
    ("chi-row", chi_row, expected(W, 0, 2, (1, 1))),
    ("shifted", shifted, expected(W, 0, 2, (1, 1))),
    ("addition", addition, expected(W, 1, 2, (1, 1))),
    ("subtraction", subtraction, expected(W, 1, 2, (1, 1))),
    ("addition-function", addition_function, expected(2 * W, 1, 2, (2, 2))),
    ("dependent", dependent, expected(W, 2, 2, (1, 1))),
    ("arx-box", arx_box, expected(2 * W, 1, 4, (1, 1, 1, 1))),
    ("food", food, expected(Fraction(3 * W, N * N), 0, 2, (1, 1))),
)


def build(name, builder, n=N, w=W):
    return ir.Program(name, n, w, builder(n, w))
