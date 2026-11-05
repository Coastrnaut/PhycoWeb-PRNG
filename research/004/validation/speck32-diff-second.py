"""Second known result of `speck32-diff` (research R12; data-model section 7): the 9-round trail of the 2014 paper.

Biryukov and Velichkov, "Automatic Search for Differential Trails in ARX Ciphers", CT-RSA 2014, `automatic-search-arx-trails.pdf`, Table 5,
Speck32: the differences before each round, and the weight the paper prints for each round. Its total, 31, is no optimum: the paper
found the trail by a search that states none, and the optimum over 9 rounds is 30 (`speck32-diff`). What must match is the weight of
each round, each difference being checked against the round function.

SPECK's round on two words, as `internal-trails` writes a box: word 0 is x and word 1 is y, x becomes rotr(x, 7) + y and y becomes
rotl(y, 2) xor x. A rotation right by 7 is a rotation left by 9. The exact model of addition and the printed linear layer gave these weights, before this file was fixed.
"""

TOOL = "ARX search"
KNOWN_ID = "speck32-diff-second"
SECOND_OF = "speck32-diff"
SOURCE = "published: Biryukov and Velichkov, CT-RSA 2014, Table 5, Speck32, automatic-search-arx-trails.pdf"
KIND = "differential"
W = 16
ROUND = (("rot", 0, 9), ("add", 0, 1, 0), ("rot", 1, 2), ("xor", 1, 0, 0))
TRAIL = ((0x0A60, 0x4205), (0x0211, 0x0A04), (0x2800, 0x0010), (0x0040, 0x0000), (0x8000, 0x8000),
         (0x8100, 0x8102), (0x8000, 0x840A), (0x850A, 0x9520), (0x802A, 0xD4A8), (0x00A8, 0x520B))
WEIGHTS = (5, 4, 2, 0, 1, 2, 4, 6, 7)
