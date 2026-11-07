"""Candidate B1, the Boolean design (spec FR-022; research R6, R11).

Every bit position of two neighbouring nodes passes through one 4-bit S-box, made of four single
updates in turn, each a phase of its class, since a lane gains only from lanes that its phase does
not write. With x0 and x2 the lanes P and V of one node and x3 and x1 the lanes P and V of its partner:

    x0 ^= nor(x3, x2)    x3 ^= nor(x2, x1)    x2 ^= nor(x1, x0)    x1 ^= nor(x0, x3)

Its table is 9 c 3 0 2 5 4 7 6 1 a b 8 d e f, x3 the highest bit. It is the rule's: among the 65,536
networks of this form, each update a function of two bits, the least largest entry of the difference
table, 4, then the least largest Walsh value, 8, and the first of the 4,096 such networks in ascending
order of the four functions' truth tables, all four being nor. Three half-steps of a Feistel network on
two pairs of bits reach no better than a largest entry of 8, so a box takes four updates.

A round takes four partners in turn, east, south, west and north of a node of an even class, its
partner taking the opposite direction, so that the S-boxes of two neighbouring nodes change every
time and the partners join every node of the torus. No bit moves: the partner's lanes are read rotated
by the pair's amount, so that a word's bit i meets the partner's bit i - u, and each set of S-boxes
lies across those of the set before.

Food nodes are (0,0), (0,1) and (1,2), wrapping at 2×2. Each takes one column of the constant table
in its first update of the round.

The amounts come from K = 2 sets, the first for a pair that holds a food node and the second elsewhere
(spec FR-024). A set is an odd number g below 16, which gives at w = 16 the amounts (t + 1) · g mod 16
for the four partners, t = 0 to 3, and `scaled` carries them to the other widths. AMOUNTS holds the
assignment in force: until the search of research R15 has chosen one, the first of its space in tie
order. At an odd n no perfect pairing of the nodes exists, so the updates keep their form with a third
class and no S-box partition holds; such a size claims nothing (D3).

No argument here rests on the mapping to the slime mould. This module makes no security claim.
"""
import ir

FAMILY = "Boolean"
P, V = ir.PRESSURE, ir.VEIN
SEARCH_WIDTH = 16
SBOX = (0x9, 0xC, 0x3, 0x0, 0x2, 0x5, 0x4, 0x7, 0x6, 0x1, 0xA, 0xB, 0x8, 0xD, 0xE, 0xF)
PARTNERS = ((0, 1), (1, 0), (0, -1), (-1, 0))
GENERATORS = (1, 3, 5, 7, 9, 11, 13, 15)
AMOUNTS = (1, 3)
FOOD = ((0, 0), (0, 1), (1, 2))


def scaled(amount, w):
    """The stated rule from the search width, as candidate A1's: at 32 twice the amount, plus one
    where it is odd; at 16 itself; below it the amount times w / 16, rounded to nearest with halves
    up, and where that gives 0 or w, 1 or w - 1."""
    if w == 32:
        return 2 * amount + (amount & 1)
    if w == SEARCH_WIDTH:
        return amount
    return max(1, min(w - 1, (amount * w + 8) // 16))


def food_nodes(n):
    return tuple((i % n, j % n) for i, j in FOOD)


def amount_of(index, t, w, assignment=AMOUNTS):
    return scaled((t + 1) * assignment[index] % 16, w)


def rotated(value, amount, w):
    return ir.Rotl(value, amount % w)


def nor(left, right):
    return ir.And(ir.Not(left), ir.Not(right))


def word(n, i, j, kind):
    return ir.Lane(ir.lane(n, i, j, kind))


def pair_set(n, first, second):
    food = food_nodes(n)
    return 0 if first in food or second in food else 1


def partner_of(n, i, j, t, colour):
    """The partner in direction t: an even class looks along it, an odd class against it."""
    di, dj = PARTNERS[t]
    sign = 1 if colour % 2 == 0 else -1
    return (i + sign * di) % n, (j + sign * dj) % n


def update(n, w, i, j, t, colour, step):
    """Lane P at step 0 and V at step 1, gaining nor of the partner's lane and its own other lane."""
    partner = partner_of(n, i, j, t, colour)
    amount = amount_of(pair_set(n, (i, j), partner), t, w)
    even = colour % 2 == 0
    own, other = (P, V) if step == 0 else (V, P)
    # An even class reads the partner's lane of the same name, and an odd class the other, as the
    # four updates of the S-box name them.
    read = own if even else other
    expr = nor(rotated(word(n, *partner, read), amount if even else w - amount, w), word(n, i, j, other))
    if t == 0 and step == 0 and (i, j) in food_nodes(n):
        expr = ir.Xor(expr, ir.Constant(food_nodes(n).index((i, j))))
    return ir.Mix(ir.lane(n, i, j, own), "xor", expr)


def key_path(n, w):
    """The nodes whose lanes hold key bits, along one row and back along the next, each step between
    direct neighbours (spec FR-025)."""
    nodes = (256 // w + 1) // 2
    return [(i, n - 1 - j if i % 2 else j) for i, j in (divmod(node, n) for node in range(nodes))]


def declarations(n, w):
    """What spec FR-025 and FR-027 read from the list. Its operations are bitwise, so that no stage
    holds a carry chain, no word wraps and no word shifts."""
    phases = 2 * len(PARTNERS) * ir.colours(n)
    return {"stages": {"phases": phases, "chains_per_phase": [0] * phases},
            "key_path": [list(node) for node in key_path(n, w)],
            "semantics": {"width": w, "signedness": "unsigned", "wrap": "none: no addition",
                          "shift": "none", "rotation": "left, bit i to bit (i + k) mod w"}}


def build(n, w):
    phases = []
    for t in range(len(PARTNERS)):
        for step in (0, 1):
            for colour in range(ir.colours(n)):
                phases.append(ir.Phase(colour, tuple(update(n, w, i, j, t, colour, step)
                                                     for i, j in ir.nodes_of(n, colour))))
    return ir.Program("cand-B1", n, w, tuple(phases))
