"""Second known result of `rotation-layer`, at w = 8, 16 and 32 (research R12; data-model section 7): four distinct amounts.

The layer of `rotation-layer` with word j rotated by AMOUNTS[j], four distinct amounts, so that the bits of one column land in
different columns of the next round. By hand, with the PRESENT S-box:

    Differences. One round holds at least one active column, so the minimum is 1 at r = 1, and 2 at r = 2 by an input of weight 2
    that gives an output of weight 1, then any output. At r = 3 the count 3 would need one column in each round. One column in the
    second round needs an output of weight 1 from the first, since the amounts are distinct. Its one bit enters the second round,
    and condition 2 of the PRESENT paper (`present-tables-second`) gives an output of weight at least 2, so the third round holds
    at least two columns. So the minimum is at least 4, and that trail, of 1, 1 and 2 columns, reaches it: 1, 2 and 4.

    Masks. A mask of one bit in word 1 goes to a mask of one bit in word 1 through the S-box, a pair that Ohkuma's list holds
    (`present-tables-second`, SINGLE_BIT_PAIRS), and a rotation keeps one bit one bit. So one column per round exists at any r, and
    no round has none: 1, 2 and 3.

The exhaustive search at w = 4, by the same S-box and amounts, gave these before this file was fixed.
"""

TOOL = "active-S-box counting"
KNOWN_ID = "rotation-layer-second"
SECOND_OF = "rotation-layer"
SOURCE = "self-written: by hand in this file's docstring"
SBOX = (0xC, 0x5, 0x6, 0xB, 0x9, 0x0, 0xA, 0xD, 0x3, 0xE, 0xF, 0x8, 0x4, 0x7, 0x1, 0x2)
WIDTHS = (8, 16, 32)
WORDS = 4
AMOUNTS = (0, 1, 2, 3)
ROUNDS = 3
DIFFERENTIAL = {1: 1, 2: 2, 3: 4}
LINEAR = {1: 1, 2: 2, 3: 3}
