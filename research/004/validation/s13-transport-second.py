"""Second known result of `s13-transport` (research R12, R13): a planted transport difference on a stated list.

S13(b) adds 2 and -2 alternately to the pressure lanes of `phyco-v2`, and every transport sum, a word that
reads those pressures through a sum, stays as it was. This list holds the same mechanism, by itself. At
n = 4 and w = 32, every vein takes its own pressure and then its east neighbour's, for each class in turn:

    V(x) add P(x), then V(x) add P(east x)

and no pressure is written. The difference adds +2 to the pressures of class 0 and -2 to those of class 1.
A node and its east neighbour lie in different classes, so that each vein is handed +2 and -2, in one
order or the other, and comes out as it was, on every state and after every round, since the pressures
stay as they are and keep the difference. So the difference, taken as an addition modulo 2^w, comes out
unchanged on every test state, after one round and after a full call of ROUNDS rounds. What must match is
exactly that: it is kept, on every test state, at both round counts, and the veins' difference is 0.
"""
import ir

TOOL = "invariants"
KNOWN_ID = "s13-transport-second"
SECOND_OF = "s13-transport"
SOURCE = "self-written: derived by hand in this file's docstring"
N, W = 4, 32
ROUNDS = 4
P, V = ir.PRESSURE, ir.VEIN
STEP = 2


def build(n, w):
    phases = []
    for colour in range(ir.colours(n)):
        nodes = ir.nodes_of(n, colour)
        phases.append(ir.Phase(colour, tuple(
            ir.Mix(ir.lane(n, i, j, V), "add", ir.Lane(ir.lane(n, i, j, P))) for i, j in nodes)))
        phases.append(ir.Phase(colour, tuple(
            ir.Mix(ir.lane(n, i, j, V), "add", ir.Lane(ir.lane(n, i, j + 1, P))) for i, j in nodes)))
    return ir.Program("transport", n, w, tuple(phases))


def difference(n, w):
    """{lane: word added}, +2 on class 0's pressures and -2 on class 1's."""
    out = {}
    for i in range(n):
        for j in range(n):
            out[ir.lane(n, i, j, P)] = (STEP if ir.colour(n, i, j) == 0 else -STEP) % (1 << w)
    return out
