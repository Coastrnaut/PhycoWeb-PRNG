"""Known result `speck64-lin` of the ARX search, at w = 32 (research R12; data-model section 7).

The correlations of SPECK64's optimal linear trails: Liu, Wang and Rijmen, ACNS 2016, the COSIC article `2657`, Table 2, as `speck32-lin`,
EXPONENTS holding k of a magnitude 2^-k. `main.pdf`'s Table 4 gives the same to 12 rounds. What must match is k at each r from 1 to ROUNDS.

SPECK's round on two words, as `internal-trails` writes a box: word 0 is x and word 1 is y, x becomes rotr(x, 8) + y and y becomes
rotl(y, 3) xor x. A rotation right by 8 is a rotation left by 24.
"""

TOOL = "ARX search"
KNOWN_ID = "speck64-lin"
SECOND_OF = "none"
DOWNLOAD = "2657"
PAPER = "Liu, Wang and Rijmen, Automatic Search of Linear Trails in ARX with Applications to SPECK and Chaskey, ACNS 2016"
TABLE = "Table 2, SPECK64"
VALUE = "the exponents 0, 0, 1, 3, 6, 9, 13, 17, 19, 21, 24, 27, 30 of 1 to 13 rounds"
KIND = "linear"
W = 32
ROUND = (("rot", 0, 24), ("add", 0, 1, 0), ("rot", 1, 3), ("xor", 1, 0, 0))
EXPONENTS = {1: 0, 2: 0, 3: 1, 4: 3, 5: 6, 6: 9, 7: 13, 8: 17, 9: 19, 10: 21, 11: 24, 12: 27, 13: 30}
ROUNDS = 5
