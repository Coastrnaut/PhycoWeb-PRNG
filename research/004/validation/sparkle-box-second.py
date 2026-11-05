"""Second known result of `sparkle-box`, at w = 32 (research R12; data-model section 7): the linear bounds.

Beierle et al., "Lightweight AEAD and Hashing using the Sparkle Permutation Family", ToSC 2020, `main.pdf` of research R19, Table 7: the bound of
each step count on the absolute correlation of a linear trail, as -log2 of it, from the same argument as `sparkle-box`.

The paper's section 4.2.2 replaces the layer by the transpose of its inverse, which it writes as a Feistel function going the other way, with
M_w its own transpose by its Lemma 3. So for masks, with indices mod h:

    new left j = right (j + 1), and new right j = left j xor M_h(right) j

A right branch goes on into its copy on the left, and a left branch goes on where M_h adds nothing active to it. Which outputs of M_h may be
active is `sparkle-box`'s `relation`. Table 4 gives 2 and 17 for the 4 and 8 rounds of one and two steps, and no linear bound of 12 rounds, so a
chain of three steps is cut into 17 + 2 = 19.

What must match is BOUNDS up to ROUNDS at each size: Table 7's value at each step count, and the two its caption gives. Entries printed as "at
least" a size are left out, being no value. The search that `sparkle-box` describes, on these rules, gave every entry before this file was
fixed, and every number Table 7 prints is here: none is left out. ROUNDS only says how far a validation goes, as it does there: Sparkle512
stops at 8 steps, where a look with a solver, before this file was fixed, took about a minute an instance.
"""

TOOL = "long-trail active-box counting"
KNOWN_ID = "sparkle-box-second"
SECOND_OF = "sparkle-box"
SOURCE = "published: Beierle et al., ToSC 2020, Table 7, from the bounds of Alzette in Table 4, main.pdf"
KIND = "linear"
BOX = (2, 17)
HALVES = {256: 2, 384: 3, 512: 4}
ROUNDS = {256: 9, 384: 10, 512: 8}
BOUNDS = {256: {1: 2, 2: 17, 3: 23, 4: 42, 5: 57, 6: 72, 7: 91, 8: 106, 9: 125},
          384: {1: 2, 2: 17, 3: 25, 4: 46, 5: 76, 6: 89, 7: 110, 8: 131, 9: 161, 10: 174},
          512: {1: 2, 2: 17, 3: 27, 4: 50, 5: 93, 6: 106, 7: 129, 8: 152, 9: 195, 10: 208, 11: 231, 12: 254}}
