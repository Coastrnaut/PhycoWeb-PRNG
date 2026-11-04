"""Second known result of `bijectivity-maps` (research R12, R13): another pair, its count by enumeration.

The known permutation is the stated list below over ROUNDS rounds, of the two forms of research R11, with
a rotation update and a subtraction, which `bijectivity-maps` does not hold: 2^32 ones.

The map with collisions replaces lane 0 by (lane 0 and rotl(lane 0, 1)), on 4 bits, and keeps the other
seven lanes, whose 28 bits are free. By hand, x -> x and rotl(x, 1):

    0000 -> 0000   0001 -> 0000   0010 -> 0000   0011 -> 0010
    0100 -> 0000   0101 -> 0000   0110 -> 0100   0111 -> 0110
    1000 -> 0000   1001 -> 0001   1010 -> 0000   1011 -> 0011
    1100 -> 1000   1101 -> 1001   1110 -> 1100   1111 -> 1111

which reaches 10 values: 0000, 0001, 0010, 0011, 0100, 0110, 1000, 1001, 1100 and 1111. So the bitmap
holds 10 · 2^28 ones.
"""
import numpy as np

import ir

TOOL = "bijectivity"
KNOWN_ID = "bijectivity-maps-second"
SECOND_OF = "bijectivity-maps"
SOURCE = "self-written: derived by hand in this file's docstring"
N, W = 2, 4
ROUNDS = 2
P, V = ir.PRESSURE, ir.VEIN
PERMUTATION_ONES = 2 ** 32
COLLISION_ONES = 10 * 2 ** 28
MASK = 0xF


def permutation(n=N, w=W):
    phases = []
    for colour in range(ir.colours(n)):
        nodes = ir.nodes_of(n, colour)
        phases.append(ir.Phase(colour, tuple(ir.Rot(ir.lane(n, i, j, P), 1) for i, j in nodes)))
        phases.append(ir.Phase(colour, tuple(
            ir.Mix(ir.lane(n, i, j, V), "sub", ir.Lane(ir.lane(n, i, j, P))) for i, j in nodes)))
    return ir.Program("permutation", n, w, tuple(phases))


def collisions(states):
    """The stated map, on a uint64 batch of one row per lane."""
    out = states.copy()
    word = states[0]
    turned = ((word << np.uint64(1)) | (word >> np.uint64(3))) & np.uint64(MASK)
    out[0] = word & turned
    return out
