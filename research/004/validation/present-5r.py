"""Known result `present-5r` of the active-S-box counter (research R12; data-model section 7).

Bogdanov et al., "PRESENT: An Ultra-Lightweight Block Cipher", CHES 2007, `47270450.pdf` of research R19, Theorem 1:
any five-round differential characteristic of PRESENT has a minimum of 10 active S-boxes. What must match is the
stated minimum, exactly, as a count of R12, which is never read from a float.

SBOX is the paper's S-box, and PERMUTATION its pLayer table as printed: bit i of the state moves to position
PERMUTATION[i]. The state's 64 bits go through sixteen S-boxes, the S-box j taking bits 4j to 4j + 3, the lowest
first, and a round is the S-boxes and then the permutation. An S-box is active where its input difference is not 0.
"""

TOOL = "active-S-box counting"
KNOWN_ID = "present-5r"
SECOND_OF = "none"
DOWNLOAD = "47270450.pdf"
PAPER = "Bogdanov et al., PRESENT: An Ultra-Lightweight Block Cipher, CHES 2007"
TABLE = "Theorem 1"
VALUE = "any five-round differential characteristic has a minimum of 10 active S-boxes"
SBOX = (0xC, 0x5, 0x6, 0xB, 0x9, 0x0, 0xA, 0xD, 0x3, 0xE, 0xF, 0x8, 0x4, 0x7, 0x1, 0x2)
PERMUTATION = (
    0, 16, 32, 48, 1, 17, 33, 49, 2, 18, 34, 50, 3, 19, 35, 51,
    4, 20, 36, 52, 5, 21, 37, 53, 6, 22, 38, 54, 7, 23, 39, 55,
    8, 24, 40, 56, 9, 25, 41, 57, 10, 26, 42, 58, 11, 27, 43, 59,
    12, 28, 44, 60, 13, 29, 45, 61, 14, 30, 46, 62, 15, 31, 47, 63,
)
ROUNDS = 5
MINIMUM = 10
