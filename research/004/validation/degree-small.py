"""Known result `degree-small` of the degree derivation (research R13; data-model sections 5 and 7).

A stated small list holding an ARX-box spread over two phases and a bitwise S-box, with its degree counted
by hand by R13's bottom-up rule: input lanes 1 and a constant 0; XOR, NOT, rotations and shifts the largest
of their arguments; AND and OR the sum of their arguments' degrees, 2 for two lanes; addition and
subtraction w - 1 times the larger operand's, a subtraction counting as an addition; an update its
result's; a phase the largest of its updates', a lane it does not write counting 1; a round the product of
its phases'; r rounds the product of the rounds', capped at b - 1. The upper bound uses the same rules with
w for addition and subtraction.

With a = P(0,0), b = V(0,0), c = P(0,1) and d = V(0,1), four phases:

    0  b add a                                    addition of two lanes: w - 1; bound w
    1  a xor rotl(b, 1)                           1
    2  c xor (not d and rotl(d, 1))               AND of two degree-1 words: 2
    3  d xor (rotl(c, 1) and (rotl(c, 2) or c))   OR of two is 2, AND with a third adds 1: 3

so that a round counts 6(w - 1) by the rule and 6w by the bound, and Π⁻¹, whose phases are the same updates
undone and reversed, counts the same. The count d(r) = min((6(w - 1))^r, b - 1):

    (n, w) = (2, 4),  b = 32:     d(1) = 18,   d(2) = 31,   d(3) = 31;     bound 24, 31, 31
    (n, w) = (2, 8),  b = 64:     d(1) = 42,   d(2) = 63,   d(3) = 63;     bound 48, 63, 63
    (n, w) = (4, 32), b = 1024:   d(1) = 186,  d(2) = 1023, d(3) = 1023;   bound 192, 1023, 1023

The inside-out count is the largest r1 + r2, r1 and r2 at least 1, with max(d(r1), d(r2)) at most the limit,
at the cost 2^(max + 1). The rule's limit is 126, for a target of 2^128. At w = 4 the cap of 31 lies under
it at every round count, so that the count would be unbounded and says nothing: the validation at 2×2
states a limit of its own, 20, under a state of 32 bits. d(1) = 18 is within it and d(2) = 31 is not, so
that the largest pair is (1, 1), r1 + r2 = 2, at the cost 2^19. At (2, 8) the limit is 50: the pair (1, 1),
at the cost 2^43. At (4, 32) the limit is 126, and d(1) = 186 lies above it: no pair, and no round count at
which d is at most 126.

The exact degree from the truth table is reported beside the count and decides nothing, at w = 4 and 8; the
one check on it is that the bound is at least that degree.
"""
import ir

TOOL = "degree"
KNOWN_ID = "degree-small"
SECOND_OF = "none"
SOURCE = "self-written: counted by hand in this file's docstring"
PAIRS = ((2, 4), (2, 8), (4, 32))
EXACT_WIDTHS = (4, 8)
ROUNDS = (1, 2, 3)
P, V = ir.PRESSURE, ir.VEIN
LIMITS = {(2, 4): 20, (2, 8): 50, (4, 32): 126}
COUNTS = {(2, 4): (18, 31, 31), (2, 8): (42, 63, 63), (4, 32): (186, 1023, 1023)}
BOUNDS = {(2, 4): (24, 31, 31), (2, 8): (48, 63, 63), (4, 32): (192, 1023, 1023)}
ROUND_DEGREES = {(2, 4): 18, (2, 8): 42, (4, 32): 186}
INSIDE_OUT = {(2, 4): (2, 19), (2, 8): (2, 43), (4, 32): None}


def build(n, w):
    a, b = ir.lane(n, 0, 0, P), ir.lane(n, 0, 0, V)
    c, d = ir.lane(n, 0, 1, P), ir.lane(n, 0, 1, V)
    return ir.Program("small", n, w, (
        ir.Phase(ir.colour(n, 0, 0), (ir.Mix(b, "add", ir.Lane(a)),)),
        ir.Phase(ir.colour(n, 0, 0), (ir.Mix(a, "xor", ir.Rotl(ir.Lane(b), 1)),)),
        ir.Phase(ir.colour(n, 0, 1), (
            ir.Mix(c, "xor", ir.And(ir.Not(ir.Lane(d)), ir.Rotl(ir.Lane(d), 1))),)),
        ir.Phase(ir.colour(n, 0, 1), (
            ir.Mix(d, "xor", ir.And(ir.Rotl(ir.Lane(c), 1),
                                    ir.Or(ir.Rotl(ir.Lane(c), 2), ir.Lane(c)))),))))
