"""Known result `present-linear` of the active-S-box counter (research R12; data-model section 7).

The further known result for the counter's model of masks, since a D4 score needs both a differential and a linear
bound (research R6) and `present-5r` covers differences alone. Ohkuma, "Weak Keys of Reduced-Round PRESENT for Linear
Cryptanalysis", SAC 2009, section 3, `978-3-642-05445-7_16.pdf`: PRESENT has single-bit linear paths, one active bit in every mask
and so one active S-box in every round, and they connect to any number of rounds. Each round of a non-trivial
linear trail holds at least one active S-box, since an S-box is a bijection. So the minimum over r rounds is r exactly.

What must match is the minimum at each r from 1 to ROUNDS. The state and the round are those of `present-5r`, and a mask
moves through the permutation as a difference does.
"""

TOOL = "active-S-box counting"
KNOWN_ID = "present-linear"
SECOND_OF = "none"
DOWNLOAD = "978-3-642-05445-7_16.pdf"
PAPER = "Ohkuma, Weak Keys of Reduced-Round PRESENT for Linear Cryptanalysis, SAC 2009"
TABLE = "section 3, the single-bit paths"
VALUE = "one active S-box per round over any number of rounds, so a minimum of r over r rounds"
SBOX = (0xC, 0x5, 0x6, 0xB, 0x9, 0x0, 0xA, 0xD, 0x3, 0xE, 0xF, 0x8, 0x4, 0x7, 0x1, 0x2)
PERMUTATION = tuple((16 * i) % 63 for i in range(63)) + (63,)
ROUNDS = 5
MINIMA = {r: r for r in range(1, ROUNDS + 1)}
