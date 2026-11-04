"""Known result `dependency-small` of the dependency propagation (research R13; data-model section 7).

Two stated small lists and their dependency matrices, derived by hand from the rules of R13: XOR, AND,
OR and NOT unite bit sets, rotations and shifts move them, a bit a shift brings in depends on nothing,
and bit i of an addition or subtraction depends on bits 0..i of both operands. What must match is
every entry, in both directions, at every size and width below, 2×2 included beside the 3×3 and 4×4
that R13 names. A bit is written (lane, bit), bit 0 the least significant. Neither list reaches full
dependency, since most lanes are never written, so that R_f and R_b do not exist on them.

`rules` holds every operation the rules name, over one round. With a = P(0,0), b = V(0,0), c = P(0,1),
d = V(0,1) and e = P(1,0), Π computes, each phase reading the values at its start:

    a1 = a xor rotl(d, 3)               b1 = b add (e >> 2)
    c1 = c xor (not a1 and (b1 << 1))   d1 = rotl(d, 1)     e1 = e sub (a1 or rotl(b1, 3))

so that, k running over bits 0..i and every index taken mod w,

    a1[i] : a[i], d[i-3]
    b1[i] : b[0..i], and e[j] for 2 <= j <= i + 2, j < w
    c1[i] : c[i], a1[i], and for i >= 1 b1[i-1]; bit 0 of the shifted word depends on nothing
    d1[i] : d[i-1]
    e1[i] : e[0..i], and a1[k] and b1[k-3] for every k

Π⁻¹ undoes the second phase and then the first, from the outputs, written a, b, c, d, e again:

    c' = c xor (not a and (b << 1))     d' = rotl(d, w - 1)     e' = e add (a or rotl(b, 3))
    a' = a xor rotl(d', 3)              b' = b sub (e' >> 2)

    c'[i] : c[i], a[i], and for i >= 1 b[i-1]
    d'[i] : d[i+1]
    e'[i] : e[0..i], and a[k] and b[k-3] for every k
    a'[i] : a[i], d'[i-3], which is d[i-2]
    b'[i] : b[0..i], and e'[j+2] for every j <= i with j + 2 < w

`chain` shows the rounds compose. With x = P(0,0), y = V(0,1) and z = P(1,1), Π is
x1 = x xor rotl(y, 1), then y1 = y add z, and with t = (i - 1) mod w:

    round 1        x[i] : x[i], y[t]                y[i] : y[0..i], z[0..i]
    round r >= 2   x[i] : x[i], y[0..t], z[0..t]    y[i] : y[0..i], z[0..i]

since round 2 adds y1[t] to x, and y only adds z again. Π⁻¹ computes y' = y sub z first, then
x' = x xor rotl(y', 1), so its matrices are those of round 2 from round 1 on. Lanes that no update
writes depend on their own bit alone.
"""
import ir

TOOL = "dependency"
KNOWN_ID = "dependency-small"
SECOND_OF = "none"
SOURCE = "self-written: derived by hand in this file's docstring"
PAIRS = ((2, 4), (2, 8), (2, 16), (2, 32), (3, 8), (3, 16), (3, 32), (4, 8), (4, 16), (4, 32))
P, V = ir.PRESSURE, ir.VEIN
FORWARD, INVERSE = "forward", "inverse"
CASES = (("rules", (1,)), ("chain", (1, 2, 3)))
FIRST_FULL = {"rules": None, "chain": None}


def rules(n, w):
    a, b = ir.lane(n, 0, 0, P), ir.lane(n, 0, 0, V)
    c, d = ir.lane(n, 0, 1, P), ir.lane(n, 0, 1, V)
    e = ir.lane(n, 1, 0, P)
    return ir.Program("rules", n, w, (
        ir.Phase(ir.colour(n, 0, 0), (
            ir.Mix(a, "xor", ir.Rotl(ir.Lane(d), 3)),
            ir.Mix(b, "add", ir.Shr(ir.Lane(e), 2)))),
        ir.Phase(ir.colour(n, 0, 1), (
            ir.Mix(c, "xor", ir.And(ir.Not(ir.Lane(a)), ir.Shl(ir.Lane(b), 1))),
            ir.Rot(d, 1),
            ir.Mix(e, "sub", ir.Or(ir.Lane(a), ir.Rotl(ir.Lane(b), 3)))))))


def chain(n, w):
    x, y, z = ir.lane(n, 0, 0, P), ir.lane(n, 0, 1, V), ir.lane(n, 1, 1, P)
    return ir.Program("chain", n, w, (
        ir.Phase(ir.colour(n, 0, 0), (ir.Mix(x, "xor", ir.Rotl(ir.Lane(y), 1)),)),
        ir.Phase(ir.colour(n, 0, 1), (ir.Mix(y, "add", ir.Lane(z)),))))


BUILD = {"rules": rules, "chain": chain}


def below(lane, top):
    return {(lane, j) for j in range(top + 1)}


def identity(n, w):
    return {(lane, i): {(lane, i)} for lane in range(2 * n * n) for i in range(w)}


def rules_forward(n, w):
    a, b = ir.lane(n, 0, 0, P), ir.lane(n, 0, 0, V)
    c, d = ir.lane(n, 0, 1, P), ir.lane(n, 0, 1, V)
    e = ir.lane(n, 1, 0, P)
    a1 = {i: {(a, i), (d, (i - 3) % w)} for i in range(w)}
    b1 = {i: below(b, i) | {(e, j) for j in range(2, min(i + 2, w - 1) + 1)} for i in range(w)}
    out = identity(n, w)
    for i in range(w):
        out[(a, i)] = a1[i]
        out[(b, i)] = b1[i]
        out[(c, i)] = {(c, i)} | a1[i] | (b1[i - 1] if i >= 1 else set())
        out[(d, i)] = {(d, (i - 1) % w)}
        out[(e, i)] = below(e, i).union(*(a1[k] | b1[(k - 3) % w] for k in range(i + 1)))
    return out


def rules_inverse(n, w):
    a, b = ir.lane(n, 0, 0, P), ir.lane(n, 0, 0, V)
    c, d = ir.lane(n, 0, 1, P), ir.lane(n, 0, 1, V)
    e = ir.lane(n, 1, 0, P)
    e_ = {i: below(e, i).union(*({(a, k), (b, (k - 3) % w)} for k in range(i + 1))) for i in range(w)}
    out = identity(n, w)
    for i in range(w):
        out[(c, i)] = {(c, i), (a, i)} | ({(b, i - 1)} if i >= 1 else set())
        out[(d, i)] = {(d, (i + 1) % w)}
        out[(e, i)] = e_[i]
        out[(a, i)] = {(a, i), (d, (i - 2) % w)}
        out[(b, i)] = below(b, i).union(*(e_[j + 2] for j in range(i + 1) if j + 2 < w))
    return out


def chain_matrix(n, w, settled):
    x, y, z = ir.lane(n, 0, 0, P), ir.lane(n, 0, 1, V), ir.lane(n, 1, 1, P)
    out = identity(n, w)
    for i in range(w):
        t = (i - 1) % w
        out[(y, i)] = below(y, i) | below(z, i)
        out[(x, i)] = {(x, i)} | (below(y, t) | below(z, t) if settled else {(y, t)})
    return out


def expected(name, n, w, direction, rounds):
    """Output bit -> the input bits it depends on, after `rounds` rounds."""
    if name == "rules":
        return rules_forward(n, w) if direction == FORWARD else rules_inverse(n, w)
    return chain_matrix(n, w, settled=direction == INVERSE or rounds >= 2)
