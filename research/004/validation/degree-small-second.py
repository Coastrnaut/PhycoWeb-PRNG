"""Second known result of `degree-small` (research R12, R13): a list whose inside-out count needs several rounds.

Counted by hand by the rule that `degree-small` states. With a = P(0,0), b = V(0,0), c = P(0,1) and d = V(0,1):

    `sbox`, two phases:  0  c xor (a and b)            AND of two lanes: 2
                         1  a xor (not c and d)         2

which holds no addition, so a round counts 2 · 2 = 4 by the rule and by the bound, and the count is
d(r) = min(4^r, b - 1). At (2, 4), b = 32: d(1), d(2), d(3) = 4, 16, 31, the same for the bound. With the
stated limit 20, d(1) and d(2) are within it, so that the largest pair is (2, 2), r1 + r2 = 4, at the cost
2^(16 + 1) = 2^17. At (2, 8), b = 64: 4, 16, 63, the limit 40 giving the same pair at the same cost.

    `arx`, one phase:    0  b sub rotl(a, 1)           a subtraction counts as an addition: w - 1; bound w

so a round counts w - 1, d(r) = min((w - 1)^r, b - 1). At (2, 4): 3, 9, 27, then 31 from r = 4, with the bound
4, 16, 31, 31. With the limit 20 the largest pair is (2, 2), r1 + r2 = 4, at the cost 2^10. At (2, 8): 7, 49,
63, 63, with the bound 8, 63, 63, 63; with the limit 50 the largest pair is (2, 2), at the cost 2^50. At
(4, 32), b = 1024: 31, 961, 1023, 1023, with the bound 32, 1023, 1023, 1023; with the rule's limit 126 only
d(1) is within it, so the largest pair is (1, 1), r1 + r2 = 2, at the cost 2^32, and r = 1 is the one round
count with d at most 126. By the bound, r = 1 as well.
"""
import ir

TOOL = "degree"
KNOWN_ID = "degree-small-second"
SECOND_OF = "degree-small"
SOURCE = "self-written: counted by hand in this file's docstring"
P, V = ir.PRESSURE, ir.VEIN
ROUNDS = (1, 2, 3, 4)


def sbox(n, w):
    a, b = ir.lane(n, 0, 0, P), ir.lane(n, 0, 0, V)
    c, d = ir.lane(n, 0, 1, P), ir.lane(n, 0, 1, V)
    return ir.Program("sbox", n, w, (
        ir.Phase(ir.colour(n, 0, 1), (ir.Mix(c, "xor", ir.And(ir.Lane(a), ir.Lane(b))),)),
        ir.Phase(ir.colour(n, 0, 0), (ir.Mix(a, "xor", ir.And(ir.Not(ir.Lane(c)), ir.Lane(d))),))))


def arx(n, w):
    a, b = ir.lane(n, 0, 0, P), ir.lane(n, 0, 0, V)
    return ir.Program("arx", n, w, (
        ir.Phase(ir.colour(n, 0, 0), (ir.Mix(b, "sub", ir.Rotl(ir.Lane(a), 1)),)),))


def entry(limit, counts, bounds, inside_out):
    return {"limit": limit, "counts": counts, "bounds": bounds, "inside_out": inside_out}


CASES = (
    ("sbox", sbox, 2, 4, entry(20, (4, 16, 31, 31), (4, 16, 31, 31), (4, 17))),
    ("sbox", sbox, 2, 8, entry(40, (4, 16, 63, 63), (4, 16, 63, 63), (4, 17))),
    ("arx", arx, 2, 4, entry(20, (3, 9, 27, 31), (4, 16, 31, 31), (4, 10))),
    ("arx", arx, 2, 8, entry(50, (7, 49, 63, 63), (8, 63, 63, 63), (4, 50))),
    ("arx", arx, 4, 32, entry(126, (31, 961, 1023, 1023), (32, 1023, 1023, 1023), (2, 32))),
)
