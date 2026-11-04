"""Second known result of `symmetry-planted` (research R12, R13): per-node amounts and a placement alone.

The first known result plants its symmetries in the constants. These lists plant them in the two
patterns it leaves out. A symmetry is written as there: (name, a, b), the node (i, j) going to
(p + a, q + b) mod n, with (p, q) as in LINEAR below.

`amounts` lists: every node's vein is rotated by the amount `amount[node]`, and no constants enter, so
that the one pattern is the amounts.

n = 4, `amounts-parity`: the amount is 1 + (i mod 2) + 2·(j mod 2). A symmetry must keep i mod 2 and
j mod 2 of every node, and signs do, so the elements are the sign pairs (id, r180, flip-j, flip-i)
with a and b even, 16 of them, 15 that move a node. `swap` and the turns exchange the two parities,
sending the amount 2 of (1,0) to the amount 3 of (0,1).

n = 4, `amounts-turn`: each of the four orbits of the quarter-turn about the centre of (0,0), (0,1),
(1,1), (1,0) has one amount of its own. A symmetry keeps each orbit, so it keeps Q = that block, as in
`symmetry-planted`, and the reflections about its centre exchange the orbit of (0,2) with that of
(2,0). The three turns are left.

n = 3, `amounts-swap`: the amounts 1 to 6 on (0,0), (0,1), (0,2), (1,1), (1,2), (2,2), and on (j, i) as
on (i, j). The three diagonal nodes have amounts of their own, so each stays, and only `swap` keeps
them all and moves a node.

n = 4, `amounts-none`: the amount 1 at the three nodes (0,0), (0,1), (1,2), and 2 at the others, so
that a symmetry would fix that placement, which nothing does (spec FR-018).

`placement-only` at n = 4: the placement of `symmetry-planted`'s rotation, with eight different words,
so that its three turns fix the placement and nothing fixes either round's constants.
"""
import ir

TOOL = "symmetry"
KNOWN_ID = "symmetry-planted-second"
SECOND_OF = "symmetry-planted"
SOURCE = "self-written: derived by hand in this file's docstring"
WIDTHS = (8, 16, 32)
ROUNDS = 2
P, V = ir.PRESSURE, ir.VEIN
LINEAR = {"id": (1, 0, 0, 1), "r90": (0, 1, -1, 0), "r180": (-1, 0, 0, -1), "r270": (0, -1, 1, 0),
          "swap": (0, 1, 1, 0), "flip-j": (1, 0, 0, -1), "flip-i": (-1, 0, 0, 1), "anti": (0, -1, -1, 0)}
TURNS = (("r90", 0, 1), ("r180", 1, 1), ("r270", 1, 0))
PARITY = tuple((name, a, b) for name in ("id", "r180", "flip-j", "flip-i")
               for a in (0, 2) for b in (0, 2) if (name, a, b) != ("id", 0, 0))
ORBITS = (((0, 0), (0, 1), (1, 1), (1, 0)), ((0, 2), (2, 1), (1, 3), (3, 0)),
          ((2, 0), (1, 2), (3, 1), (0, 3)), ((2, 2), (2, 3), (3, 3), (3, 2)))
SWAP_LEVELS = {(0, 0): 1, (0, 1): 2, (0, 2): 3, (1, 1): 4, (1, 2): 5, (2, 2): 6}
WORDS = {8: (0x1D, 0x2B, 0x4F, 0x07, 0x13, 0x25, 0x01, 0x1B),
         16: (0x1D2B, 0x4F71, 0x96C3, 0x0B5D, 0x2E87, 0x3A1F, 0x6D59, 0x1C37),
         32: (0x1D2B4F71, 0x96C3A85E, 0x3B7E15A9, 0x0F4D62B7, 0x2C9A71E5, 0x51D8E3C6, 0x6E1B39D4,
              0x17F2C58B)}


def parity(i, j):
    return 1 + (i % 2) + 2 * (j % 2)


def turn(i, j):
    return 1 + [k for k, orbit in enumerate(ORBITS) if (i, j) in orbit][0]


def swap(i, j):
    return SWAP_LEVELS[(min(i, j), max(i, j))]


def none(i, j):
    return 1 if (i, j) in ((0, 0), (0, 1), (1, 2)) else 2


AMOUNTS = (("amounts-parity", 4, parity, PARITY), ("amounts-turn", 4, turn, TURNS),
           ("amounts-swap", 3, swap, (("swap", 0, 0),)), ("amounts-none", 4, none, ()))
PLACEMENT = ((0, 0), (0, 1), (1, 1), (1, 0), (0, 2), (2, 1), (1, 3), (3, 0))


def node_map(n, symmetry):
    """The symmetry as {node: image}, for comparison with what the tool reports."""
    name, a, b = symmetry
    p, q, r, s = LINEAR[name]
    return {(i, j): ((p * i + q * j + a) % n, (r * i + s * j + b) % n)
            for i in range(n) for j in range(n)}


def build_amounts(name, n, amount, w):
    return ir.Program(name, n, w, tuple(
        ir.Phase(colour, tuple(ir.Rot(ir.lane(n, i, j, V), amount(i, j))
                               for i, j in ir.nodes_of(n, colour)))
        for colour in range(ir.colours(n))))


def build_placement(w):
    n = 4
    phases = []
    for colour in range(ir.colours(n)):
        updates = tuple(ir.Mix(ir.lane(n, i, j, P), "xor", ir.Constant(column))
                        for column, (i, j) in enumerate(PLACEMENT) if ir.colour(n, i, j) == colour)
        phases.append(ir.Phase(colour, updates))
    return ir.Program("placement-only", n, w, tuple(phases))


def table(w):
    """Two rows of eight words, the second the first read from the other end."""
    return [WORDS[w], tuple(reversed(WORDS[w]))]
