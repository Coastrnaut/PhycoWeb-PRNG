"""Second known result of `dependency-small` (research R12, R13): a list that reaches full dependency.

`sweep` takes every lane in turn along a closed path through the grid. The path visits the nodes
node_0 ... node_(m-1), m = n², going east along each row and south to the next, row i starting at
column -i, so that each node is a direct neighbour of the next and the last of the first, at every n.
Its L = 2m lanes are l_0 ... l_(L-1), with l_(2k) = P(node_k) and l_(2k+1) = V(node_k). A round is L
phases of one update each, for k = 0 ... L - 1 in that order:

    l_k <- l_k xor S(l_(k-1))       k - 1 taken mod L

S(x) being the XOR of rotl(x, t) for t = 0 ... w - 1, so that by R13's rules every bit of S(x) depends
on every bit of x, and dependency is a matter of whole lanes. Call D_r(k) the set of lanes every bit
of l_k depends on after r rounds; each bit i of l_k also depends on its own input bit.

Forward. The updates run in order, so each reads its predecessor's new value, and only the first reads
an old one: D_r(0) = D_(r-1)(0) + D_(r-1)(L-1) + {L-1}, and D_r(k) = D_(r-1)(k) + D_r(k-1) + {k-1}.
From D_0 empty:

    D_1(k) = {L-1, 0, ..., k-1}, for k <= L - 2; D_1(L-1) = every lane; D_r(k) = every lane, r >= 2

so that R_f = 2, since D_1(0) is one lane.

Inverse. The undone updates run from L - 1 down to 0, each reading a value not yet changed but for the
last, which reads the new l_(L-1): D_r(k) = D_(r-1)(k) + D_(r-1)(k-1) + {k-1} for k >= 1, and
D_r(0) = D_(r-1)(0) + D_r(L-1) + {L-1}. By induction on r:

    k >= r :  D_r(k) = {k-r, ..., k-1}
    k < r  :  D_r(k) = {0, ..., k-1} + {L-1-(r-k), ..., L-1}, cut at 0

so that a lane k < r holds r + 1 lanes, until they overlap at r = L - 1, and a lane k >= r holds r.
The last to fill is l_(L-1), which lacks its own other bits until r = L: R_b = L = 2n².
Structural dependency over-approximates: for even w the XOR of all rotations has even weight in each
bit, so two S in a row cancel in fact, which is why R13 calls the matrices an upper estimate.
"""
import ir

TOOL = "dependency"
KNOWN_ID = "dependency-small-second"
SECOND_OF = "dependency-small"
SOURCE = "self-written: derived by hand in this file's docstring"
PAIRS = ((2, 4), (2, 8), (2, 16), (2, 32), (3, 8), (3, 16), (3, 32), (4, 8), (4, 16), (4, 32))
P, V = ir.PRESSURE, ir.VEIN
FORWARD, INVERSE = "forward", "inverse"


def path(n):
    """The closed path of the docstring, as nodes in order."""
    return [(i, (t - i) % n) for i in range(n) for t in range(n)]


def chain_lanes(n):
    lanes = []
    for i, j in path(n):
        lanes += [ir.lane(n, i, j, P), ir.lane(n, i, j, V)]
    return lanes


def spread(index, w):
    expr = ir.Lane(index)
    for t in range(1, w):
        expr = ir.Xor(expr, ir.Rotl(ir.Lane(index), t))
    return expr


def sweep(n, w):
    lanes = chain_lanes(n)
    phases = []
    for k, dst in enumerate(lanes):
        node = ir.node_of(n, dst)
        phases.append(ir.Phase(ir.colour(n, *node),
                               (ir.Mix(dst, "xor", spread(lanes[k - 1], w)),)))
    return ir.Program("sweep", n, w, tuple(phases))


def first_full(n):
    return {FORWARD: 2, INVERSE: 2 * n * n}


def lanes_held(length, k, direction, rounds):
    """D_rounds(k) of the docstring, as positions along the path."""
    every = set(range(length))
    if direction == FORWARD:
        if rounds >= 2 or k == length - 1:
            return every
        return set(range(k)) | {length - 1}
    if k >= rounds:
        return set(range(k - rounds, k))
    return set(range(k)) | set(range(max(0, length - 1 - (rounds - k)), length))


def expected(n, w, direction, rounds):
    """Output bit -> the input bits it depends on, after `rounds` rounds."""
    lanes = chain_lanes(n)
    out = {}
    for k, lane in enumerate(lanes):
        held = lanes_held(len(lanes), k, direction, rounds)
        whole = {(lanes[position], t) for position in held for t in range(w)}
        for i in range(w):
            out[(lane, i)] = whole | {(lane, i)}
    return out
