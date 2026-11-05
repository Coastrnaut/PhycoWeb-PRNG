"""Second known result of `present-tables` (research R12; data-model section 7).

The four conditions that the PRESENT paper places on its S-box, in its section 4.3 (Bogdanov et al., "PRESENT:
An Ultra-Lightweight Block Cipher", CHES 2007, `47270450.pdf` of research R19), each a statement on the two tables:

    1. For any non-zero input difference and any non-zero output difference, at most 4 of the 16 inputs give
       that output difference.
    2. For an input difference and an output difference each of Hamming weight 1, no input gives it.
    3. For all non-zero masks a and b, the sum of signs S^W_b(a) over the 16 inputs has magnitude at most 8,
       that sum being of (-1)^(b.S(x) + a.x), as `present-tables` states it.
    4. For all masks a and b each of Hamming weight 1, that sum is 4 or -4.

Beside them stands what the tables of any permutation owe the tables of its inverse, by hand. The pairs
(x, S(x)) and (S(x), x) are the same pairs, so an entry of the inverse's difference table at (b, a) is the entry
of S's at (a, b), and the sum for the inverse at output mask a and input mask b is the sum for S at output mask b
and input mask a. INVERSE is S's inverse, written out by hand from `present-tables`'s SBOX. So a tool that read a
table the wrong way round, in either direction, fails here.
"""

TOOL = "exhaustive tables"
KNOWN_ID = "present-tables-second"
SECOND_OF = "present-tables"
SOURCE = "published: Bogdanov et al., PRESENT, CHES 2007, section 4.3, 47270450.pdf; the inverse's tables by hand"
SBOX = (0xC, 0x5, 0x6, 0xB, 0x9, 0x0, 0xA, 0xD, 0x3, 0xE, 0xF, 0x8, 0x4, 0x7, 0x1, 0x2)
INVERSE = (0x5, 0xE, 0xF, 0x8, 0xC, 0x1, 0x2, 0xD, 0xB, 0x4, 0x6, 0x3, 0x0, 0x7, 0x9, 0xA)
MOST_INPUTS = 4
MOST_SUM = 8
SINGLE_BIT_SUM = 4
