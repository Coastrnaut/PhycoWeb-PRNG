"""Candidate A1, the long-trail ARX design (spec FR-022; research R6, R11; D10).

Each node's pressure and vein lanes form one box of 2w bits, on w-bit operations only. Four steps of
the box, each an addition and then an XOR over two phases, since an update may not read what another
of its phase writes:

    V <- V + rotl(P, a[t])
    P <- P ^ rotl(V, b[t])      t = 0 to 3

The classes run their boxes in turn, so that every node's box runs once per round. Then the layer
between boxes, one phase per class: a node gains from its two neighbours along one axis, a class of
even number along the row and one of odd number along the column, each word crossing lanes:

    P <- P ^ G(V[+], a[0], b[1]) ^ G(V[-], b[0], a[1])
    V <- V ^ G(P[+], a[0], b[1]) ^ G(P[-], b[0], a[1])      G(x, r, s) = rotl(x ^ (x << s), r)

Each G is a bijection of its word, whatever r and s are, so a branch that alone reaches a node always
reaches it, and the shift keeps the layer from commuting with a rotation of the words. A node receives
four words in a phase, two from each of two neighbours (spec FR-018).

Food nodes are (0,0), (0,1) and (1,2), wrapping at 2×2, an arrangement that no symmetry of the torus
that moves a node keeps at a claimable size. Each takes one column of the constant table in its box's
first XOR.

The amounts come from K = 2 sets, the first at the food nodes and the second elsewhere (spec FR-024).
A set is a pair (g, h) of odd numbers below 16, which give at w = 16

    a[t] = (t + 1) · g mod 16        b[t] = (t + 1) · h mod 16

and `scaled` carries each to the other widths. AMOUNTS holds the assignment in force: until the search
of research R15 has chosen one, the first of its space in tie order.

The mapping to the slime mould is the mapping entry's, and no argument here rests on it. Only the
long-trail method is reused, never a published box or its constants (D6). This module makes no
security claim.
"""
import ir

FAMILY = "ARX"
P, V = ir.PRESSURE, ir.VEIN
SEARCH_WIDTH = 16
STEPS = 4
GENERATORS = (1, 3, 5, 7, 9, 11, 13, 15)
AMOUNTS = ((1, 1), (1, 3))
FOOD = ((0, 0), (0, 1), (1, 2))


def scaled(amount, w):
    """The stated rule from the search width: at 32 twice the amount, plus one where it is odd, so
    that odd amounts stay odd; at 16 itself; below it the amount times w / 16, rounded to nearest with
    halves up, and where that gives 0 or w, 1 or w - 1."""
    if w == 32:
        return 2 * amount + (amount & 1)
    if w == SEARCH_WIDTH:
        return amount
    return max(1, min(w - 1, (amount * w + 8) // 16))


def food_nodes(n):
    return tuple((i % n, j % n) for i, j in FOOD)


def set_of(n, i, j):
    return 0 if (i, j) in food_nodes(n) else 1


def amounts(index, w, assignment=AMOUNTS):
    """The pairs (a[t], b[t]) of one set at width w."""
    g, h = assignment[index]
    return tuple((scaled((t + 1) * g % 16, w), scaled((t + 1) * h % 16, w)) for t in range(STEPS))


def box_steps(index, w, assignment=AMOUNTS):
    """One set's box as the ARX search and the exhaustive tables take it: word 0 is P and word 1 is V."""
    steps = []
    for a, b in amounts(index, w, assignment):
        steps += [("add", 1, 0, a), ("xor", 0, 1, b)]
    return tuple(steps)


def word(n, i, j, kind):
    return ir.Lane(ir.lane(n, i, j, kind))


def spread(value, r, s):
    """G: a bijection of the word, since x ^ (x << s) is one for every s above 0."""
    return ir.Rotl(ir.Xor(value, ir.Shl(value, s)), r)


def box_phases(n, w, colour):
    nodes = ir.nodes_of(n, colour)
    food = food_nodes(n)
    phases = []
    for t in range(STEPS):
        phases.append(ir.Phase(colour, tuple(
            ir.Mix(ir.lane(n, i, j, V), "add", ir.Rotl(word(n, i, j, P), amounts(set_of(n, i, j), w)[t][0]))
            for i, j in nodes)))
        updates = []
        for i, j in nodes:
            expr = ir.Rotl(word(n, i, j, V), amounts(set_of(n, i, j), w)[t][1])
            if t == 0 and (i, j) in food:
                expr = ir.Xor(expr, ir.Constant(food.index((i, j))))
            updates.append(ir.Mix(ir.lane(n, i, j, P), "xor", expr))
        phases.append(ir.Phase(colour, tuple(updates)))
    return phases


def layer_phase(n, w, colour):
    """One class gains from its two neighbours along its axis, the row for an even class number."""
    step_i, step_j = (0, 1) if colour % 2 == 0 else (1, 0)
    updates = []
    for i, j in ir.nodes_of(n, colour):
        (a0, b0), (a1, b1) = amounts(set_of(n, i, j), w)[:2]
        ahead, behind = (i + step_i, j + step_j), (i - step_i, j - step_j)
        for target, source in ((P, V), (V, P)):
            updates.append(ir.Mix(ir.lane(n, i, j, target), "xor", ir.Xor(
                spread(word(n, *ahead, source), a0, b1), spread(word(n, *behind, source), b0, a1))))
    return ir.Phase(colour, tuple(updates))


def build(n, w):
    classes = range(ir.colours(n))
    phases = [phase for colour in classes for phase in box_phases(n, w, colour)]
    phases += [layer_phase(n, w, colour) for colour in classes]
    return ir.Program("cand-A1", n, w, tuple(phases))
