"""Known result `speck32-diff` of the ARX search (research R12; data-model section 7).

The weights of SPECK32's optimal differential trails over the first rounds: Biryukov, Velichkov and Le Corre, "Automatic Search for
the Best Trails in ARX: Application to Block Cipher Speck", FSE 2016, `409.pdf`, Table 1, column BS of Speck32, and Table 4, which agree
at every round from 1 to 10. A weight is -log2 of a trail's probability, under the Markov assumption that a trail's weight is built on.

What must match is the weight at each r from 1 to ROUNDS, and not a trail, since several trails share a weight, as Table 1 counts them.

SPECK's round on two words, as `internal-trails` writes a box: word 0 is x and word 1 is y, x becomes rotr(x, 7) + y and y becomes
rotl(y, 2) xor x. A rotation right by 7 is a rotation left by 9.
"""

TOOL = "ARX search"
KNOWN_ID = "speck32-diff"
SECOND_OF = "none"
DOWNLOAD = "409.pdf"
PAPER = "Biryukov, Velichkov and Le Corre, Automatic Search for the Best Trails in ARX: Application to Block Cipher Speck, FSE 2016"
TABLE = "Tables 1 and 4, Speck32"
VALUE = "the weights 0, 1, 3, 5, 9, 13, 18, 24, 30, 34 of 1 to 10 rounds"
KIND = "differential"
W = 16
ROUND = (("rot", 0, 9), ("add", 0, 1, 0), ("rot", 1, 2), ("xor", 1, 0, 0))
WEIGHTS = {1: 0, 2: 1, 3: 3, 4: 5, 5: 9, 6: 13, 7: 18, 8: 24, 9: 30, 10: 34}
ROUNDS = 7
