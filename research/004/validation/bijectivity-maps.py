"""Known result `bijectivity-maps` of the exhaustive bijectivity check (research R13; data-model section 7).

At 2×2 with w = 4 the state is 8 lanes of 4 bits, 32 bits, and the tool takes all 2^32 inputs into a
bitmap of outputs. What must match is the bitmap's count of ones, exactly.

The known permutation is the stated list below over ROUNDS rounds, made of the two forms of research R11
and so bijective by construction: 2^32 ones.

The map with collisions cannot be an operation list, so it is stated on the batch of lanes. It replaces
lane 0 by (lane 0 and lane 1) and keeps the other seven. For a value b of lane 1, the outputs of
(a and b) are the submasks of b, 2^popcount(b) of them, so that the two lanes together reach the sum over
b of 2^popcount(b), which is (1 + 2)^4 = 81 pairs of the 256. The other six lanes are free. So the bitmap
holds 81 · 2^24 ones, fewer than 2^32.
"""
import ir

TOOL = "bijectivity"
KNOWN_ID = "bijectivity-maps"
SECOND_OF = "none"
SOURCE = "self-written: derived by hand in this file's docstring"
N, W = 2, 4
ROUNDS = 2
P, V = ir.PRESSURE, ir.VEIN
PERMUTATION_ONES = 2 ** 32
COLLISION_ONES = 81 * 2 ** 24


def permutation(n=N, w=W):
    phases = []
    for colour in range(ir.colours(n)):
        nodes = ir.nodes_of(n, colour)
        phases.append(ir.Phase(colour, tuple(
            ir.Mix(ir.lane(n, i, j, V), "add", ir.Rotl(ir.Lane(ir.lane(n, i, j, P)), 1))
            for i, j in nodes)))
        phases.append(ir.Phase(colour, tuple(
            ir.Mix(ir.lane(n, i, j, P), "xor", ir.Rotl(ir.Lane(ir.lane(n, i, j, V)), 3))
            for i, j in nodes)))
    return ir.Program("permutation", n, w, tuple(phases))


def collisions(states):
    """The stated map, on a uint64 batch of one row per lane."""
    out = states.copy()
    out[0] = states[0] & states[1]
    return out
