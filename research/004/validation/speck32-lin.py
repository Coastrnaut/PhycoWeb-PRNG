"""Known result `speck32-lin` of the ARX search (research R12; data-model section 7).

The correlations of SPECK32's optimal linear trails over the first rounds: Liu, Wang and Rijmen, "Automatic Search of Linear Trails in
ARX with Applications to SPECK and Chaskey", ACNS 2016, the COSIC article `2657`, Table 2. A trail's correlation there has magnitude
2^-k, and EXPONENTS holds k. What must match is k at each r from 1 to ROUNDS.

SPECK's round on two words, as `internal-trails` writes a box: word 0 is x and word 1 is y, x becomes rotr(x, 7) + y and y becomes
rotl(y, 2) xor x. A rotation right by 7 is a rotation left by 9.
"""

TOOL = "ARX search"
KNOWN_ID = "speck32-lin"
SECOND_OF = "none"
DOWNLOAD = "2657"
PAPER = "Liu, Wang and Rijmen, Automatic Search of Linear Trails in ARX with Applications to SPECK and Chaskey, ACNS 2016"
TABLE = "Table 2, SPECK32"
VALUE = "the exponents 0, 0, 1, 3, 5, 7, 9, 12, 14, 17, 19, 20, 22, 24, 26, 28, 30, 34, 36, 38, 40, 42 of 1 to 22 rounds"
KIND = "linear"
W = 16
ROUND = (("rot", 0, 9), ("add", 0, 1, 0), ("rot", 1, 2), ("xor", 1, 0, 0))
EXPONENTS = {1: 0, 2: 0, 3: 1, 4: 3, 5: 5, 6: 7, 7: 9, 8: 12, 9: 14, 10: 17, 11: 19, 12: 20, 13: 22, 14: 24, 15: 26, 16: 28, 17: 30,
             18: 34, 19: 36, 20: 38, 21: 40, 22: 42}
ROUNDS = 8
