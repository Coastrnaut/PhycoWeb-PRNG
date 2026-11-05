"""Second known result of `speck32-lin` (research R12; data-model section 7): the 11-round trail of Liu, Wang and Rijmen, one row corrected.

The same paper's Table 3 prints a linear trail of SPECK32 over 11 rounds, masks (x, y) before each round. Row 4 is misprinted. As printed
it reads 0c1e 0818, and both rounds that touch it then have correlation 0, while the other nine hold. Over all 2^32 pairs three fit
between rows 3 and 5 at all, and one reaches the total of 2^-19 that the same paper's Table 2 gives for 11 rounds: 0c1e 0c18, one bit from the
print. TRAIL holds that row, and PRINTED_ROW_4 what the paper prints, so that the correction stands beside its source.

What must match is the exponent of each round, each mask being checked against the round function, and their total.

SPECK's round on two words, as `internal-trails` writes a box: word 0 is x and word 1 is y, x becomes rotr(x, 7) + y and y becomes
rotl(y, 2) xor x. A rotation right by 7 is a rotation left by 9. For masks (A, B) before a round and (C, D) after it, the addition sees the output mask C xor D, the input mask
rotr(A, 7) on x and B xor rotr(D, 2) on y, and the exact correlation of Wallen, 2003, gave these exponents before this file was fixed.
"""

TOOL = "ARX search"
KNOWN_ID = "speck32-lin-second"
SECOND_OF = "speck32-lin"
SOURCE = "published: Liu, Wang and Rijmen, ACNS 2016, Table 3, SPECK32, 2657, with row 4 corrected as this file's docstring states"
KIND = "linear"
W = 16
ROUND = (("rot", 0, 9), ("add", 0, 1, 0), ("rot", 1, 2), ("xor", 1, 0, 0))
PRINTED_ROW_4 = (0x0C1E, 0x0818)
TRAIL = ((0x4000, 0x00B0), (0x0000, 0x00C0), (0x0300, 0x0300), (0x0C1E, 0x0C18), (0xF000, 0xD010), (0x4683, 0x4743),
         (0x00A0, 0x0629), (0x78A0, 0x18A1), (0x0090, 0x6021), (0x6080, 0x4081), (0x0080, 0x0001), (0x0001, 0x0000))
EXPONENTS = (1, 0, 1, 5, 2, 3, 1, 4, 1, 1, 0)
TOTAL = 19
