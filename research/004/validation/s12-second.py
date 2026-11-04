"""Second known result of `s12` (research R4, R12, R13): a word range and its one edge value, on a stated map.

S12: every vein value stays in 0 ... 2^31, and bit 31 is set only on a value equal to 2^31. The bias test
re-finds that from its count on the vein lanes. An operation list is bijective by construction, so this
result is a stated map, four 32-bit words each through

    h(D) = (D >> 1) + (D and 1)

which is D / 2 rounded up. For D at most 2^32 - 1 its value is at most 2^31, reached at D = 2^32 - 1 and at
no other input, since h(2^32 - 2) = 2^31 - 1. So bit 31 of an output is set only on an output equal to
2^31, exactly, and on uniform inputs it is in effect never set. What must match, exactly: on every test
state and on EDGE, bit 31 is set only on a word equal to 2^31, and each word of EDGE gives its stated value.
"""
TOOL = "bias"
KNOWN_ID = "s12-second"
SECOND_OF = "s12"
SOURCE = "self-written: derived by hand in this file's docstring"
W = 32
WORDS = 4
TOP = 1 << 31
EDGE = ((2 ** 32 - 1, 2 ** 31), (2 ** 32 - 2, 2 ** 31 - 1), (2 ** 31, 2 ** 30), (1, 1), (0, 0))


def h(value):
    return (value >> 1) + (value & 1)


def step(state):
    """The stated map: four words, each through h."""
    return [h(word) for word in state]
