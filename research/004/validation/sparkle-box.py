"""Known result `sparkle-box` of the long-trail counter, at w = 32 (research R12; data-model section 7).

SPARKLE's published long-trail bounds, from its published box bounds: Beierle et al., "Lightweight AEAD and Hashing using the Sparkle
Permutation Family", ToSC 2020, `main.pdf` of research R19, Table 6.

A state is 2h branches of 64 bits, h on the left and h on the right, and a step is the box Alzette, four rounds of it, on every branch,
followed by the layer of the paper's section 2.1.2: M_h of the left branches is added to the right branches, the right branches rotate by
one branch to the left, and the two sides swap. So, with indices mod h:

    new left j = right (j + 1) xor M_h(left) (j + 1), and new right j = left j

r steps hold r - 1 layers, since the argument ends at the last box. M_h has h branches in and h branches out, and `relation` below
writes out what the paper's Theorem 1 says of which may be active.

The argument, the paper's sections 3.2.2 and 4.2.1. A truncated trail says which branches are active at each step. A long trail, called a
chain in this tool, is a run of active branches, one per step, each going on unmixed from the one before and receiving no difference from
outside: a left branch goes on into its copy on the right, and a right branch goes on where M_h adds nothing active to it. A chain of t
steps costs the bound of t steps of the box, and the bound of a truncated trail is the sum over its chains, in -log2 of a probability.
Table 4 gives 6, 32 and at least 52 for the 4, 8 and 12 rounds of one, two and three steps, BOX here. A chain of more steps than that table
holds is cut, and costs the largest sum over the ways of cutting it, so that a chain of 4 costs 32 + 32 = 64 and of 6 costs 52 + 52 = 104.
The bound of r steps is the least of these over every truncated trail allowed.

What must match is BOUNDS: Table 6's value at each stated step count of each size, and the two the paper's caption gives, 6 and 32 at 1 and 2
steps. Entries printed as "at least" a size are left out, being no value. An exhaustive search over truncated trails by these rules, outside
this file, gave every entry of BOUNDS before this file was fixed; a test of tests/test_tools_004.py repeats it.

Three entries of Table 6, all at Sparkle512, are left out in the open. LEFT_OUT holds them as printed. The same search gives 304, 396 and 460 at
those steps. 295 and 433 are odd, and every cost here is even, so no sum of the box bounds is either of them, and 276 is not reached by any
truncated trail either, Theorem 1's relation and the stricter relation of M_h itself alike. They are below the rule's value, so they stand as
weaker bounds of the same trails, and which of the paper's runs gave them is not said. R12 asks for a published bound, not for each, so the
known result is the rest of the table, fixed here before the tool exists.
"""
import itertools

TOOL = "long-trail active-box counting"
KNOWN_ID = "sparkle-box"
SECOND_OF = "none"
DOWNLOAD = "main.pdf"
PAPER = "Beierle et al., Lightweight AEAD and Hashing using the Sparkle Permutation Family, ToSC 2020"
TABLE = "Table 6, from the bounds of Alzette in Table 4"
VALUE = "the bounds of Sparkle256 at 1 to 8 steps, Sparkle384 at 1 to 10, and Sparkle512 at 1 to 7, 10 and 12"
KIND = "differential"
BOX = (6, 32, 52)
HALVES = {256: 2, 384: 3, 512: 4}
BOUNDS = {256: {1: 6, 2: 32, 3: 64, 4: 88, 5: 140, 6: 168, 7: 192, 8: 216},
          384: {1: 6, 2: 32, 3: 70, 4: 100, 5: 178, 6: 200, 7: 230, 8: 260, 9: 326, 10: 356},
          512: {1: 6, 2: 32, 3: 76, 4: 112, 5: 210, 6: 232, 7: 268, 10: 424, 12: 496}}
LEFT_OUT = {512: {8: 276, 9: 295, 11: 433}}


def relation(h):
    """The pairs (input pattern, output pattern) of M_h that Theorem 1 does not exclude, a pattern being a tuple of h bits, 1 for active. No
    input gives no output. One active input activates every output. One active output needs every input active. For h > 2, two active
    inputs j and k give only j and k, or all but j, or all but k, or all. Any other pair of non-zero patterns stands."""
    every = list(itertools.product((0, 1), repeat=h))
    pairs = {((0,) * h, (0,) * h)}
    for a in every:
        active = [i for i in range(h) if a[i]]
        if not active:
            continue
        if len(active) == 1:
            pairs.add((a, (1,) * h))
            continue
        for b in every:
            if not any(b) or (sum(b) == 1 and len(active) != h):
                continue
            if len(active) == 2 and h > 2:
                j, k = active
                if b not in (a, tuple(0 if i == j else 1 for i in range(h)), tuple(0 if i == k else 1 for i in range(h)), (1,) * h):
                    continue
            pairs.add((a, b))
    return pairs
