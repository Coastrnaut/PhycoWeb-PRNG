"""Second known result of `speck64-lin`, at w = 32 (research R12; data-model section 7): the 12-round trail of Liu, Wang and Rijmen.

The same paper's Table 3 prints a linear trail of SPECK64, masks (x, y) before each round, thirteen rows for 12 rounds. Each holds as
printed, and their exponents sum to 27, the value of Table 2 at 12 rounds. What must match is the exponent of each round, and the total.

SPECK's round on two words, as `internal-trails` writes a box: word 0 is x and word 1 is y, x becomes rotr(x, 8) + y and y becomes
rotl(y, 3) xor x. A rotation right by 8 is a rotation left by 24. The masks read as in `speck32-lin-second`.
"""

TOOL = "ARX search"
KNOWN_ID = "speck64-lin-second"
SECOND_OF = "speck64-lin"
SOURCE = "published: Liu, Wang and Rijmen, ACNS 2016, Table 3, SPECK64, 2657"
KIND = "linear"
W = 32
ROUND = (("rot", 0, 24), ("add", 0, 1, 0), ("rot", 1, 3), ("xor", 1, 0, 0))
TRAIL = ((0x00101800, 0x00001812), (0x00001000, 0x00000010), (0x00000018, 0x00000000), (0xD8000000, 0xC0000000),
         (0x04100006, 0x04800006), (0x0026D030, 0x0420C030), (0x01070101, 0x21073781), (0x01B00100, 0x00318601),
         (0x01800001, 0x0181B000), (0x01000000, 0x00018000), (0x00010000, 0x00000000), (0x00000D00, 0x00000C00),
         (0x00006065, 0x00006068))
EXPONENTS = (2, 1, 1, 2, 3, 6, 5, 2, 2, 1, 1, 1)
TOTAL = 27
