"""Second known result of `speck64-diff`, at w = 32 (research R12; data-model section 7): the 13-round trail of the 2014 paper.

Biryukov and Velichkov, CT-RSA 2014, `automatic-search-arx-trails.pdf`, Table 5, Speck64: the differences before each round and the weight
it prints for each, of total 58. The table runs each row's two words together. Each was split where the round function holds, and at
every row one split gives the printed weight, so that the split is no choice. What must match is the weight of each round.

SPECK's round on two words, as `internal-trails` writes a box: word 0 is x and word 1 is y, x becomes rotr(x, 8) + y and y becomes
rotl(y, 3) xor x. A rotation right by 8 is a rotation left by 24.
"""

TOOL = "ARX search"
KNOWN_ID = "speck64-diff-second"
SECOND_OF = "speck64-diff"
SOURCE = "published: Biryukov and Velichkov, CT-RSA 2014, Table 5, Speck64, automatic-search-arx-trails.pdf"
KIND = "differential"
W = 32
ROUND = (("rot", 0, 24), ("add", 0, 1, 0), ("rot", 1, 3), ("xor", 1, 0, 0))
TRAIL = ((0x00802490, 0x10800004), (0x80808020, 0x04808000), (0x24000080, 0x00040080), (0x80200080, 0x80000480),
         (0x00802480, 0x00800084), (0x808080A0, 0x84808480), (0x24000400, 0x00042004), (0x00202000, 0x00012020),
         (0x00010000, 0x00080100), (0x00080000, 0x00480800), (0x00480000, 0x02084000), (0x02080800, 0x124A0800),
         (0x12480008, 0x80184008), (0x880A0808, 0x88C8084C))
WEIGHTS = (5, 5, 3, 4, 5, 6, 4, 3, 2, 3, 4, 7, 7)
