"""Known result `rotation-layer` of the active-S-box counter, at w = 8, 16 and 32 (research R12; data-model section 7).

The further known result that R12 gives as its example, since `present-5r` has no word width: a layer of WORDS words of w bits,
one S-box per bit position of the group of words, whose linear part rotates every word by one amount.

The S-box i takes bit i of each word, word 0 lowest, so that a column of the state goes through one S-box. A round is the S-boxes
and then the rotation of every word by AMOUNT. The minimum of active S-boxes over r rounds is r at every w, for differences and
for masks alike, by hand: the rotation moves the one active column of a round to one column of the next, so a trail of one active
column per round exists, and a bijective S-box leaves no round without an active column, so none has fewer.

What must match is the minimum at each r from 1 to ROUNDS, at each width, of each kind. The exhaustive search at w = 4, by the same
S-box and layer, gave r at each r to 6 before this file was fixed.
"""

TOOL = "active-S-box counting"
KNOWN_ID = "rotation-layer"
SECOND_OF = "none"
SOURCE = "self-written: research R12's example, by hand in this file's docstring"
SBOX = (0xC, 0x5, 0x6, 0xB, 0x9, 0x0, 0xA, 0xD, 0x3, 0xE, 0xF, 0x8, 0x4, 0x7, 0x1, 0x2)
WIDTHS = (8, 16, 32)
WORDS = 4
AMOUNTS = (3, 3, 3, 3)
ROUNDS = 3
DIFFERENTIAL = {1: 1, 2: 2, 3: 3}
LINEAR = {1: 1, 2: 2, 3: 3}
