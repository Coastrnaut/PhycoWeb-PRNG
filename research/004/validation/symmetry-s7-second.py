"""Second known result of `s7` (research R12, R13): the three relations of S7 on stated words.

security.md's S7 names three rotation relations of `phyco-v2`'s constants: a word its own rotation
leaves unchanged, a pair of words one rotation apart, and a family of words each one bit from the next.
These stated 32-bit words carry one of each, by construction:

    0x33333333 is unchanged by rotations of 4, 8, ..., 28 bits, its period being 4;
    0xCCCCCCCC = rotl(0x33333333, 2);
    0x00000003 << k, k = 0, 1, 2, 3, are 1-bit rotations of each other.

What must match is each relation, exactly, and nothing else among the words. Their other relations,
which the tool reports as well, follow from the same three: 0xCCCCCCCC, of the same period, is also
rotl(0x33333333, 6), 10, ... 30, and is the complement of 0x33333333; and each two of the family are k
bits apart. The last word, 0x1D2B4F71, is aperiodic and related to none of them.
"""
TOOL = "symmetry"
KNOWN_ID = "symmetry-s7-second"
SECOND_OF = "s7"
SOURCE = "self-written: derived by hand in this file's docstring"
W = 32
PERIODIC = 0x33333333
ROTATED = 0xCCCCCCCC
FAMILY = tuple(0x00000003 << k for k in range(4))
UNRELATED = 0x1D2B4F71
WORDS = (PERIODIC, ROTATED) + FAMILY + (UNRELATED,)
FIXED_BY = {PERIODIC: tuple(range(4, 32, 4)), ROTATED: tuple(range(4, 32, 4))}
ROTATIONS = (
    (PERIODIC, ROTATED, tuple(range(2, 32, 4))),
    (FAMILY[0], FAMILY[1], (1,)), (FAMILY[0], FAMILY[2], (2,)), (FAMILY[0], FAMILY[3], (3,)),
    (FAMILY[1], FAMILY[2], (1,)), (FAMILY[1], FAMILY[3], (2,)), (FAMILY[2], FAMILY[3], (1,)),
)
COMPLEMENTS = ((PERIODIC, ROTATED),)
