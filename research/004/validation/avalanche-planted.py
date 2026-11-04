"""Known result `avalanche-planted` of the avalanche test (research R4, R13; data-model section 7).

One planted result per path, each a stated variant at w = 32 at any even n, R = 4n rounds, fixed here
before the tool is drafted. All three share one stem, a stated ARX round on the torus, for each class c:

    V(x) add rotl(P(x), 7);   P(x) xor rotl(V(x), 13);   P(x) add (rotl(V(east x), 3) xor rotl(V(south x), 11))

A difference crosses the torus at about one node per round, so that R = 4n leaves every bit that depends
on the flipped bit well spread. That is a measured fact about the stem, not about any candidate: a plain
look at 2^13 states with the batch interpreter, before this file was fixed, found the largest bias of any
difference bit at or below 0.03 from 12, 23 and 46 rounds at n = 4, 8 and 16.

At every round count from 1 to R, a path's expected set is its planted bits with every bit that the exact
dependency matrices show independent of the flipped bit at that round count. Every bit of it must fire at
every round count, any other firing is reported and decides nothing below R, and at R exactly that set
must fire. Each list below keeps the three stem updates at every node except where stated.

`unmixed`, the flip set: no update writes V(1,1), which others read. A flip anywhere else never reaches
it, and a flip inside it stays at its own bit, so its 32 difference bits are the planted bits, for every
flipped bit, forward and inverse. In the stem a pressure is read only by its own vein's update, which
leaves P(1,1) with no reader here, so that one stated update lets V(1,2) read it, and a flip in P(1,1)
spreads as any other. Every other output bit depends on every flipped bit at R.

`closed`, the related-key and related-nonce set: the two lanes C = P(2,2), V(2,2) form a closed pair: they
take only V add rotl(P, 7) and P xor rotl(V, 13), and read no other lane, while other lanes read them. The
loader below puts key words 0 to 6 in the pressures of KEY_NODES, key word 7 in P(2,2), nonce words 0 to
2 in the veins of NONCE_NODES and nonce word 3 in V(2,2), with every other lane 0. So a key bit or nonce
bit outside C, KEY_BIT and NONCE_BIT among them, never reaches STATED_LANE or its partner: the 64 bits of
C are the planted bits for those flips, and for a flip inside C none is planted.

`commuting`, the rotational pairs: V(1,1) takes only the rotation update Rot(V(1,1), 7), and reads nothing
else, so that it commutes with word rotation: rot_k of it after any round is what comes of rot_k of it
before. The 32 bits of its rotational difference are 0 on every state, for every k, forward and inverse,
which makes them the planted bits, while every other lane passes through additions, which keep a word
rotation only with a fixed probability.
"""
import ir

TOOL = "avalanche"
KNOWN_ID = "avalanche-planted"
SECOND_OF = "none"
SOURCE = "self-written: derived by hand in this file's docstring, its round count measured as stated there"
W = 32
SIZES = (4, 8, 16)
P, V = ir.PRESSURE, ir.VEIN
AMOUNTS = (7, 13, 3, 11)
KEY_NODES = ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2))
NONCE_NODES = ((0, 0), (0, 1), (0, 2))
KEY_BIT = (0, 0)
NONCE_BIT = (0, 0)


def rounds(n):
    return 4 * n


def planted_lane(n):
    """The lane of `unmixed` and `commuting`."""
    return ir.lane(n, 1, 1, V)


def stated_lane(n):
    """STATED_LANE of `closed`: the lane the stated key bit and nonce bit never reach."""
    return ir.lane(n, 2, 2, V)


def closed_lanes(n):
    return ir.lane(n, 2, 2, P), ir.lane(n, 2, 2, V)


def stem(name, n, w, skip=(), extra=None):
    """The stem's three updates at each node; an update is left out if `skip` names (kind, node)."""
    a, b, c, d = AMOUNTS
    phases = []

    def lanes(i, j, kind):
        return ir.lane(n, i, j, kind)

    for colour in range(ir.colours(n)):
        nodes = ir.nodes_of(n, colour)
        phases.append(ir.Phase(colour, tuple(
            ir.Mix(lanes(i, j, V), "add", ir.Rotl(ir.Lane(lanes(i, j, P)), a))
            for i, j in nodes if ("first", (i, j)) not in skip)))
        phases.append(ir.Phase(colour, tuple(
            ir.Mix(lanes(i, j, P), "xor", ir.Rotl(ir.Lane(lanes(i, j, V)), b))
            for i, j in nodes if ("second", (i, j)) not in skip)))
        phases.append(ir.Phase(colour, tuple(
            ir.Mix(lanes(i, j, P), "add", ir.Xor(ir.Rotl(ir.Lane(lanes(i, j + 1, V)), c),
                                                 ir.Rotl(ir.Lane(lanes(i + 1, j, V)), d)))
            for i, j in nodes if ("third", (i, j)) not in skip)))
    if extra is not None:
        phases.append(extra)
    return ir.Program(name, n, w, tuple(phases))


def unmixed(n, w=W):
    reader = ir.Mix(ir.lane(n, 1, 2, V), "xor", ir.Rotl(ir.Lane(ir.lane(n, 1, 1, P)), AMOUNTS[0]))
    return stem("unmixed", n, w, skip={("first", (1, 1))},
                extra=ir.Phase(ir.colour(n, 1, 2), (reader,)))


def closed(n, w=W):
    return stem("closed", n, w, skip={("third", (2, 2))})


def commuting(n, w=W):
    colour = ir.colour(n, 1, 1)
    return stem("commuting", n, w, skip={("first", (1, 1))},
                extra=ir.Phase(colour, (ir.Rot(planted_lane(n), 7),)))


def instantiation_state(n, key_words, nonce_words):
    """The state instantiate gives to the first call of Π in `closed`: the lanes, in lane order."""
    state = [0] * (2 * n * n)
    for word, (i, j) in zip(key_words[:7], KEY_NODES):
        state[ir.lane(n, i, j, P)] = word
    state[ir.lane(n, 2, 2, P)] = key_words[7]
    for word, (i, j) in zip(nonce_words[:3], NONCE_NODES):
        state[ir.lane(n, i, j, V)] = word
    state[ir.lane(n, 2, 2, V)] = nonce_words[3]
    return state


def planted_bits(path, n, flipped_lane=None):
    """The planted lanes of a path; for `closed`, of a flip in `flipped_lane`."""
    if path == "closed":
        return () if flipped_lane in closed_lanes(n) else closed_lanes(n)
    return (planted_lane(n),)
