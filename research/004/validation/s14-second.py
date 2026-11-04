"""Second known result of `s14` (research R4, R12, R13): exact bit frequencies, on a stated map.

S14 measures the ones in each bit of the vein lanes and finds bit 31 never set and the top bits far from
one half. This stated map on 32-bit words gives such a pattern by construction:

    m(D) = D and (D >> 1)

Bit 31 of D >> 1 is 0, so bit 31 of m(D) is never set. For i below 31, bit i of m(D) is bit i and bit i + 1
of D, two independent uniform bits on uniform inputs, so it is set with probability exactly 1/4. What must
match: bit 31 set on no word, exactly; and for each other bit, as a measured fraction, a count in the
binomial interval around 1/4 at the tool's sample size, at most 0.005 in each tail (data-model section 7).
Every bit below 31 fires by the bias rule at any sample size the test uses, and bit 31 fires as well, as a
bit that is never set.
"""
TOOL = "bias"
KNOWN_ID = "s14-second"
SECOND_OF = "s14"
SOURCE = "self-written: derived by hand in this file's docstring"
W = 32
WORDS = 4
FREQUENCY = {31: 0.0, **{bit: 0.25 for bit in range(31)}}


def m(value):
    return value & (value >> 1)


def step(state):
    """The stated map: four words, each through m."""
    return [m(word) for word in state]
