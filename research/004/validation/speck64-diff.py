"""Known result `speck64-diff` of the ARX search, at w = 32 (research R12; data-model section 7).

The further known result that R12 names for the ARX search at 32-bit words: the weights of SPECK64's optimal differential trails. Beierle et
al., "Lightweight AEAD and Hashing using the Sparkle Permutation Family", ToSC 2020, `main.pdf` of research R19, Table 4, cites them from
Biryukov, Velichkov and Le Corre, 2016: 0, 1, 3, 6, 10, 15, 21, 29 and at least 32 for 1 to 9 rounds. That paper itself, `409.pdf`, gives
the same in its Table 1, and in its Table 4 prints 27 at 8 rounds, a slip: its own Table 1 and `main.pdf` read 29. ROUNDS stays where every
source agrees.

What must match is the weight at each r from 1 to ROUNDS.

SPECK's round on two words, as `internal-trails` writes a box: word 0 is x and word 1 is y, x becomes rotr(x, 8) + y and y becomes
rotl(y, 3) xor x. A rotation right by 8 is a rotation left by 24.
"""

TOOL = "ARX search"
KNOWN_ID = "speck64-diff"
SECOND_OF = "none"
DOWNLOAD = "main.pdf"
PAPER = "Beierle et al., Lightweight AEAD and Hashing using the Sparkle Permutation Family, ToSC 2020, citing Biryukov, Velichkov and Le Corre, 2016"
TABLE = "Table 4, Speck64"
VALUE = "the weights 0, 1, 3, 6, 10, 15, 21 of 1 to 7 rounds"
KIND = "differential"
W = 32
ROUND = (("rot", 0, 24), ("add", 0, 1, 0), ("rot", 1, 3), ("xor", 1, 0, 0))
WEIGHTS = {1: 0, 2: 1, 3: 3, 4: 6, 5: 10, 6: 15, 7: 21}
ROUNDS = 5
