"""Known result `symmetry-planted` of the symmetry check (research R13; data-model section 7).

Stated lists with planted torus symmetries, a translation, a rotation by 90° and a reflection, at n = 3
and 4, and one with none. Each list is one update per food node, P(node) xor a constant, so that the
patterns are the placement of the food nodes and each round's constants, and no per-node amounts
exist. What must match is the set of symmetries that fix each pattern, entry by entry, and, for the
constants of each round, the word rotations that fix them.

A symmetry is written (name, a, b): the node (i, j) goes to (p + a, q + b) mod n, with (p, q) one of

    id (i, j)    r90 (j, -i)    r180 (-i, -j)    r270 (-j, i)
    swap (j, i)  flip-j (i, -j) flip-i (-i, j)   anti (-j, -i)

and the group of all of them that moves a node has 8n² - 1 elements at n = 3 and 4.

n = 4, `translation`: U = (0,0), (0,1), (1,2), with constants A, B, C, and its translate by (2, 2) with
the same three. Placement: the six nodes form two L-shapes, corners (0,0) and (2,2), arms north and
east. A symmetry keeps the corners as a set, so it is the translation, or it swaps each L's arms,
which only `anti` does, about either corner. Round: a symmetry must also keep the level sets of the
constants, and `anti` sends (0,1), holding B, to (3,0), holding C, so only the translation is left.

n = 4, `rotation`: Q = (0,0), (0,1), (1,1), (1,0), the only full 2×2 block of the placement, holding one
constant, and O = (0,2), (2,1), (1,3), (3,0), its image under a quarter-turn about Q's centre, holding
another. A symmetry keeps Q, so it keeps Q's centre, and it is one of the eight about that centre. The
four reflections about it each send (0,2) out of O: to (2,0), (3,1), (1,2) and (0,3). The three turns
are left, for placement and round alike.

n = 4 and n = 3, `reflection`: (0,0) holding one constant, (0,1) and (1,0) another. (0,0) is the only
node with two neighbours in the set, so it stays, and only `swap` exchanges or keeps the other two.

n = 4, `none`: (0,0), (0,1), (1,2), three constants, the placement of spec FR-018, fixed by nothing.

n = 3, `translation`: the diagonal, one constant. A symmetry keeps the line of direction (1, 1): its
linear part is id, r180, swap or anti, and its translation lies along the line, 3 choices, so 12
elements, 11 that move a node.

n = 3, `rotation`: the four neighbours of (0,0), one constant. (0,0) alone has all four in the set, so
it stays, and all eight of its turns and reflections keep them: 7 that move a node.

`word-rotation` at n = 4 puts the same word, of period 4, on the placement of `none`: the torus fixes
nothing, and the word rotations by the multiples of 4 below w fix each round's constants. The other
lists' words are unrelated and aperiodic, so that no word rotation fixes them.
"""
import ir

TOOL = "symmetry"
KNOWN_ID = "symmetry-planted"
SECOND_OF = "none"
SOURCE = "self-written: derived by hand in this file's docstring"
WIDTHS = (8, 16, 32)
ROUNDS = 2
P = ir.PRESSURE
LINEAR = {"id": (1, 0, 0, 1), "r90": (0, 1, -1, 0), "r180": (-1, 0, 0, -1), "r270": (0, -1, 1, 0),
          "swap": (0, 1, 1, 0), "flip-j": (1, 0, 0, -1), "flip-i": (-1, 0, 0, 1), "anti": (0, -1, -1, 0)}
WORDS = {8: (0x1D, 0x2B, 0x4F, 0x07, 0x13, 0x25),
         16: (0x1D2B, 0x4F71, 0x96C3, 0x0B5D, 0x2E87, 0x3A1F),
         32: (0x1D2B4F71, 0x96C3A85E, 0x3B7E15A9, 0x0F4D62B7, 0x2C9A71E5, 0x51D8E3C6)}
PERIODIC = {8: 0x33, 16: 0x3333, 32: 0x33333333}


def case(name, n, food, placement, round_pattern):
    return {"name": name, "n": n, "food": food, "placement": placement, "round": round_pattern}


TURNS = (("r90", 0, 1), ("r180", 1, 1), ("r270", 1, 0))
PLUS = tuple((name, 0, 0) for name in LINEAR if name != "id")
LINE = (("id", 1, 1), ("id", 2, 2),
        ("r180", 0, 0), ("r180", 1, 1), ("r180", 2, 2),
        ("swap", 0, 0), ("swap", 1, 1), ("swap", 2, 2),
        ("anti", 0, 0), ("anti", 1, 1), ("anti", 2, 2))
CASES = (
    case("translation", 4, {(0, 0): 0, (0, 1): 1, (1, 2): 2, (2, 2): 0, (2, 3): 1, (3, 0): 2},
         (("id", 2, 2), ("anti", 0, 0), ("anti", 2, 2)), (("id", 2, 2),)),
    case("rotation", 4, {(0, 0): 0, (0, 1): 0, (1, 1): 0, (1, 0): 0,
                         (0, 2): 1, (2, 1): 1, (1, 3): 1, (3, 0): 1}, TURNS, TURNS),
    case("reflection", 4, {(0, 0): 0, (0, 1): 1, (1, 0): 1},
         (("swap", 0, 0),), (("swap", 0, 0),)),
    case("none", 4, {(0, 0): 0, (0, 1): 1, (1, 2): 2}, (), ()),
    case("translation", 3, {(0, 0): 0, (1, 1): 0, (2, 2): 0}, LINE, LINE),
    case("rotation", 3, {(0, 1): 0, (1, 0): 0, (0, 2): 0, (2, 0): 0}, PLUS, PLUS),
    case("reflection", 3, {(0, 0): 0, (0, 1): 1, (1, 0): 1},
         (("swap", 0, 0),), (("swap", 0, 0),)),
)
WORD_ROTATION = case("word-rotation", 4, {(0, 0): 0, (0, 1): 0, (1, 2): 0}, (), ())


def node_map(n, symmetry):
    """The symmetry as {node: image}, for comparison with what the tool reports."""
    name, a, b = symmetry
    p, q, r, s = LINEAR[name]
    return {(i, j): ((p * i + q * j + a) % n, (r * i + s * j + b) % n)
            for i in range(n) for j in range(n)}


def build(entry, w):
    """One phase per colour that holds a food node."""
    n = entry["n"]
    phases = []
    for colour in range(ir.colours(n)):
        updates = tuple(ir.Mix(ir.lane(n, i, j, P), "xor", ir.Constant(column))
                        for (i, j), column in sorted(entry["food"].items())
                        if ir.colour(n, i, j) == colour)
        if updates:
            phases.append(ir.Phase(colour, updates))
    return ir.Program(f"{entry['name']}-{n}", n, w, tuple(phases))


def table(entry, w):
    """The constant table: one row per round, one word per column."""
    if entry is WORD_ROTATION:
        return [(PERIODIC[w],), (PERIODIC[w],)]
    return [WORDS[w][:3], WORDS[w][3:]]


def word_rotations(entry, w):
    """The word rotations that fix each round's constants."""
    return tuple(range(4, w, 4)) if entry is WORD_ROTATION else ()
