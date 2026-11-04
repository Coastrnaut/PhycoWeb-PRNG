"""Second known result of `avalanche-planted` (research R4, R12, R13): the three paths on another stem.

The same three planted results, at w = 32 at any even n, with other amounts and other planted lanes, and
the pressures and veins exchanged in the stem, for each class c:

    P(x) add rotl(V(x), 5);   V(x) xor rotl(P(x), 9);   V(x) add (rotl(P(east x), 2) xor rotl(P(south x), 15))

As in the first, a plain look with the batch interpreter before this file was fixed found every difference
bit that depends on the flip well spread by R = 4n rounds. The expected sets are stated as there.

`unmixed`: no update writes P(1,2). Its 32 bits are the planted bits for every flipped bit, both directions.
V(1,2), which only that lane's update read, is read by one stated update of P(1,3), so that a flip in it
spreads as any other.

`closed`: P(3,3) and V(3,3) take only P add rotl(V, 5) and V xor rotl(P, 9), and read no other lane. The
loader below puts key words 0 to 6 in the veins of KEY_NODES, key word 7 in V(3,3), nonce words 0 to 2 in
the pressures of NONCE_NODES and nonce word 3 in P(3,3), every other lane 0. KEY_BIT and NONCE_BIT, and every
key or nonce bit outside the pair, never reach STATED_LANE: the 64 bits of the pair are the planted bits for
those flips, and for a flip inside the pair none is planted.

`commuting`: P(1,2) takes only the rotation update Rot(P(1,2), 11), so its 32 rotational difference bits are
0 on every state, for every k, both directions.
"""
import ir

TOOL = "avalanche"
KNOWN_ID = "avalanche-planted-second"
SECOND_OF = "avalanche-planted"
SOURCE = "self-written: derived by hand in this file's docstring, its round count measured as stated there"
W = 32
SIZES = (4, 8, 16)
P, V = ir.PRESSURE, ir.VEIN
AMOUNTS = (5, 9, 2, 15)
KEY_NODES = ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 3))
NONCE_NODES = ((0, 0), (0, 1), (0, 2))
KEY_BIT = (3, 7)
NONCE_BIT = (2, 31)


def rounds(n):
    return 4 * n


def planted_lane(n):
    """The lane of `unmixed` and `commuting`."""
    return ir.lane(n, 1, 2, P)


def stated_lane(n):
    return ir.lane(n, 3, 3, P)


def closed_lanes(n):
    return ir.lane(n, 3, 3, P), ir.lane(n, 3, 3, V)


def stem(name, n, w, skip=(), extra=None):
    """The stem's three updates at each node; an update is left out if `skip` names (kind, node)."""
    a, b, c, d = AMOUNTS
    phases = []

    def lanes(i, j, kind):
        return ir.lane(n, i, j, kind)

    for colour in range(ir.colours(n)):
        nodes = ir.nodes_of(n, colour)
        phases.append(ir.Phase(colour, tuple(
            ir.Mix(lanes(i, j, P), "add", ir.Rotl(ir.Lane(lanes(i, j, V)), a))
            for i, j in nodes if ("first", (i, j)) not in skip)))
        phases.append(ir.Phase(colour, tuple(
            ir.Mix(lanes(i, j, V), "xor", ir.Rotl(ir.Lane(lanes(i, j, P)), b))
            for i, j in nodes if ("second", (i, j)) not in skip)))
        phases.append(ir.Phase(colour, tuple(
            ir.Mix(lanes(i, j, V), "add", ir.Xor(ir.Rotl(ir.Lane(lanes(i, j + 1, P)), c),
                                                 ir.Rotl(ir.Lane(lanes(i + 1, j, P)), d)))
            for i, j in nodes if ("third", (i, j)) not in skip)))
    if extra is not None:
        phases.append(extra)
    return ir.Program(name, n, w, tuple(phases))


def unmixed(n, w=W):
    reader = ir.Mix(ir.lane(n, 1, 3, P), "xor", ir.Rotl(ir.Lane(ir.lane(n, 1, 2, V)), AMOUNTS[0]))
    return stem("unmixed", n, w, skip={("first", (1, 2))},
                extra=ir.Phase(ir.colour(n, 1, 3), (reader,)))


def closed(n, w=W):
    return stem("closed", n, w, skip={("third", (3, 3))})


def commuting(n, w=W):
    colour = ir.colour(n, 1, 2)
    return stem("commuting", n, w, skip={("first", (1, 2))},
                extra=ir.Phase(colour, (ir.Rot(planted_lane(n), 11),)))


def instantiation_state(n, key_words, nonce_words):
    """The state instantiate gives to the first call of Π in `closed`: the lanes, in lane order."""
    state = [0] * (2 * n * n)
    for word, (i, j) in zip(key_words[:7], KEY_NODES):
        state[ir.lane(n, i, j, V)] = word
    state[ir.lane(n, 3, 3, V)] = key_words[7]
    for word, (i, j) in zip(nonce_words[:3], NONCE_NODES):
        state[ir.lane(n, i, j, P)] = word
    state[ir.lane(n, 3, 3, P)] = nonce_words[3]
    return state


def planted_bits(path, n, flipped_lane=None):
    """The planted lanes of a path; for `closed`, of a flip in `flipped_lane`."""
    if path == "closed":
        return () if flipped_lane in closed_lanes(n) else closed_lanes(n)
    return (planted_lane(n),)
