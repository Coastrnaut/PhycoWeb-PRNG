"""Second known result of `s13-decay` (research R12, R13): the merge of S13(a), on a stated map.

S13(a): the vein decay D - (D >> 4) sends 16m + 15 and 16m + 16 to one value, so that two states that
differ only there have one successor, and about 41% of states have such a partner. An operation list is
bijective by construction, so this result is a stated map, four 32-bit words each through

    d(D) = D - (D >> 5)

With D = 32m + 31: D >> 5 = m, so d(D) = 31m + 31. With D + 1 = 32(m + 1): (D + 1) >> 5 = m + 1, so
d(D + 1) = 32m + 32 - m - 1 = 31m + 31. So 32m + 31 and 32m + 32 go to one value, for every m with
32m + 32 < 2^32, exactly. A word has such a partner if its low five bits are 31 or 0, 2 values in 32, so
that on uniform states a state of four words has one with probability 1 - (30/32)^4 = 0.227... The first
is a deterministic fact and must match exactly. The second is a measured fraction, which matches when
the tool's count lies in the binomial interval around SHARE at its sample size, at most 0.005 in each
tail (data-model section 7). On every merged pair, the difference mode reports the successors as
coinciding.
"""
TOOL = "invariants"
KNOWN_ID = "s13-decay-second"
SECOND_OF = "s13-decay"
SOURCE = "self-written: derived by hand in this file's docstring"
W = 32
WORDS = 4
SHIFT = 5
MODULUS = 1 << SHIFT
LOW = (0, MODULUS - 1)
SHARE = 1 - ((MODULUS - len(LOW)) / MODULUS) ** WORDS


def decay(value):
    return (value - (value >> SHIFT)) % (1 << W)


def step(state):
    """The stated map: four words, each through the decay."""
    return [decay(word) for word in state]


def pair(m):
    """The two words the decay sends to one value."""
    return MODULUS * m + MODULUS - 1, MODULUS * m + MODULUS


def has_partner(state):
    return any(word % MODULUS in LOW for word in state)
