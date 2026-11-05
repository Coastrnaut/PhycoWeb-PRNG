"""Second known result of `present-5r` (research R12; data-model section 7): the two characteristics that show Theorem 1 tight.

The PRESENT paper (`47270450.pdf`), straight after Theorem 1, prints two five-round characteristics of 10 active
S-boxes, each the difference before the S-boxes of each round and after the last:

    ITERATIVE, a two-round characteristic of two S-boxes per round, taken over five rounds: 10 active S-boxes.
    OTHER, which it gives probability 2^-21: 2, 1, 1, 2 and 4 active S-boxes, of total weight 21, the weight of a trail being
    the sum over its S-boxes of 4 - log2 of the entry of the difference table.

The paper gives the iterative one 2^-25 over five rounds. That is the mean of a pair: from one start the five rounds weigh 24
and from the other 26, each by the S-box's table, so its weight is not stated here and its count of S-boxes is.

What must match: the counter's model admits each characteristic, as it must any real one, at those counts round by round, and
the second at its weight. A model drawn too tight would refuse them, which Theorem 1's minimum alone would not show: a
model that counted a false 10 with no trail behind it would pass the first known result.
"""

TOOL = "active-S-box counting"
KNOWN_ID = "present-5r-second"
SECOND_OF = "present-5r"
SOURCE = "published: Bogdanov et al., PRESENT, CHES 2007, the two characteristics printed after Theorem 1, 47270450.pdf"
SBOX = (0xC, 0x5, 0x6, 0xB, 0x9, 0x0, 0xA, 0xD, 0x3, 0xE, 0xF, 0x8, 0x4, 0x7, 0x1, 0x2)
PERMUTATION = tuple((16 * i) % 63 for i in range(63)) + (63,)
A, B = 0x0000000000000011, 0x0000000000030003
ITERATIVE = (A, B, A, B, A, B)
ITERATIVE_ACTIVE = (2, 2, 2, 2, 2)
OTHER = (0x0000000000007070, 0x000000000000000A, 0x0001000000000000, 0x0000000010001000, 0x0000000000880088, 0x0033000000330033)
OTHER_ACTIVE = (2, 1, 1, 2, 4)
OTHER_WEIGHT = 21
