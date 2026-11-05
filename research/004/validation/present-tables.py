"""Known result `present-tables` of the exhaustive tables (research R12; data-model section 7).

Research R12's row: every entry of the PRESENT S-box's published difference and linear tables. The PRESENT
paper prints the S-box and four conditions on it, and neither table, so the tables come from two other papers
that print them, each with this S-box in its Table 1:

    Wang, "Differential Cryptanalysis of PRESENT", Cryptology ePrint Archive 2007/408, Table 3, the "Differential
    Distribution Table of S-box": DIFFERENCE below, the row the input difference, the column the output
    difference, each entry the number of the 16 inputs that give that output difference.

    Ohkuma, "Weak Keys of Reduced-Round PRESENT for Linear Cryptanalysis", SAC 2009, Table 2, the "Linear deviation
    of S-box (with sign)": EIGHTHS below, in eighths, each entry eight times the deviation printed. Its columns
    are headed input masks 1 to F; its rows carry output masks 1 to F; the masks 0 are not printed. An entry is
    the deviation from one half of the chance that a.x = b.S(x), for input mask a and output mask b, in the
    usual dot product of bit vectors.

What must match is every entry: 256 and 225. Both tables are as the papers print them, parsed from the text of
each downloaded file and written here by a script that never computes from the S-box. A sum of signs
over the 16 inputs is 32 times a deviation, so 4 times an entry of EIGHTHS.
"""

TOOL = "exhaustive tables"
KNOWN_ID = "present-tables"
SECOND_OF = "none"
DOWNLOAD = ("408.pdf", "978-3-642-05445-7_16.pdf")
PAPER = ("Wang, Differential Cryptanalysis of PRESENT, ePrint 2007/408; Ohkuma, Weak Keys of Reduced-Round PRESENT "
         "for Linear Cryptanalysis, SAC 2009")
TABLE = "Wang, Table 3; Ohkuma, Table 2"
VALUE = "every entry: the 256 of the difference table and the 225 of the linear table"
SBOX = (0xC, 0x5, 0x6, 0xB, 0x9, 0x0, 0xA, 0xD, 0x3, 0xE, 0xF, 0x8, 0x4, 0x7, 0x1, 0x2)
DIFFERENCE = (
    (16,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0),
    ( 0,  0,  0,  4,  0,  0,  0,  4,  0,  4,  0,  0,  0,  4,  0,  0),
    ( 0,  0,  0,  2,  0,  4,  2,  0,  0,  0,  2,  0,  2,  2,  2,  0),
    ( 0,  2,  0,  2,  2,  0,  4,  2,  0,  0,  2,  2,  0,  0,  0,  0),
    ( 0,  0,  0,  0,  0,  4,  2,  2,  0,  2,  2,  0,  2,  0,  2,  0),
    ( 0,  2,  0,  0,  2,  0,  0,  0,  0,  2,  2,  2,  4,  2,  0,  0),
    ( 0,  0,  2,  0,  0,  0,  2,  0,  2,  0,  0,  4,  2,  0,  0,  4),
    ( 0,  4,  2,  0,  0,  0,  2,  0,  2,  0,  0,  0,  2,  0,  0,  4),
    ( 0,  0,  0,  2,  0,  0,  0,  2,  0,  2,  0,  4,  0,  2,  0,  4),
    ( 0,  0,  2,  0,  4,  0,  2,  0,  2,  0,  0,  0,  2,  0,  4,  0),
    ( 0,  0,  2,  2,  0,  4,  0,  0,  2,  0,  2,  0,  0,  2,  2,  0),
    ( 0,  2,  0,  0,  2,  0,  0,  0,  4,  2,  2,  2,  0,  2,  0,  0),
    ( 0,  0,  2,  0,  0,  4,  0,  2,  2,  2,  2,  0,  0,  0,  2,  0),
    ( 0,  2,  4,  2,  2,  0,  0,  2,  0,  0,  2,  2,  0,  0,  0,  0),
    ( 0,  0,  2,  2,  0,  0,  2,  2,  2,  2,  0,  0,  2,  2,  0,  0),
    ( 0,  4,  0,  0,  4,  0,  0,  0,  0,  0,  0,  0,  0,  0,  4,  4),
)
EIGHTHS = (
    ( 0,  0,  0,  0,  0,  0,  0,  0,  2,  0, -2,  0,  2,  0,  2),
    ( 0,  1,  1, -1, -1,  0,  0,  1, -1,  2,  0,  0,  2,  1, -1),
    ( 0,  1,  1,  1,  1, -2,  2, -1, -1,  0,  0,  0,  0,  1,  1),
    ( 0, -1,  1, -1, -1,  0,  2,  0,  0,  1, -1, -1, -1, -2,  0),
    (-2, -1, -1, -1,  1,  0,  0,  0,  0,  1, -1, -1, -1,  2,  0),
    ( 0,  0, -2,  0,  0, -2,  0, -1,  1,  1,  1, -1,  1, -1, -1),
    (-2,  0,  0,  2,  0,  0,  0,  1, -1, -1, -1, -1,  1, -1, -1),
    ( 0,  1, -1, -1,  1,  0,  0, -1, -1,  0, -2,  2,  0, -1, -1),
    ( 0, -1,  1, -1,  1, -2, -2,  1, -1,  0,  0,  0,  0, -1,  1),
    ( 0,  0, -2,  0, -2,  0,  0,  0, -2,  0,  0,  0,  0,  0,  2),
    ( 0,  2,  0, -2,  0,  0,  0,  0,  0, -2,  0, -2,  0,  0,  0),
    ( 0,  0,  0,  0,  2,  2,  0, -1, -1,  1,  1, -1,  1, -1,  1),
    (-2,  2,  0,  0,  0,  0,  0,  1,  1,  1,  1,  1, -1, -1,  1),
    ( 0, -1, -1, -1,  1,  0,  2,  2,  0, -1,  1,  1,  1,  0,  0),
    ( 2,  1, -1,  1,  1,  0,  0,  2,  0,  1, -1, -1, -1,  0,  0),
)
