"""Second known result of `long-trail-feistel`, at w = 8 and 16 (research R12; data-model section 7): a layer of copies, and the paper's example.

Two things that the first does not hold.

A layer that only moves branches: BRANCHES branches, each going to the next, with nothing added to any. So no branch ever receives a difference
from outside, every active branch stays active, and each is one chain of r steps. k active branches cost k chains of r steps, so the minimum at
r steps is one active branch, a single chain: the chain cost of `long-trail-feistel` at r, by hand, for each kind alike. With the BOXES of that
file, whose chain of 3 is one step more than a bound holds, these are MINIMA.

Example 1 of Beierle et al., "Lightweight AEAD and Hashing using the Sparkle Permutation Family", ToSC 2020, section 3.2.2, `main.pdf` of
research R19, which reproduces the example of the Sparx specification: a block of two branches on a 32-bit box, so w = 16, one Feistel round as its
layer, as `long-trail-feistel` has it, and four steps. The paper's trail is (dL0, dR0), (dL1, dR1), (0, dR2), (dL3, 0), and it decomposes it into
long trails of lengths 1, 2 and 3: dR0 alone, dL0 for two steps, and dL1 for three. It writes this t_1 = 1, t_2 = 1, t_3 = 1. EXAMPLE is that
trail as patterns (L, R), and EXAMPLE_LENGTHS those lengths. The paper states the decomposition and no number, so that is what must match.

What must match is the minimum at each r from 1 to ROUNDS at each width, of each kind, and the example's lengths.
"""

TOOL = "long-trail active-box counting"
KNOWN_ID = "long-trail-feistel-second"
SECOND_OF = "long-trail-feistel"
SOURCE = "self-written: by hand in this file's docstring; and published: Beierle et al., ToSC 2020, Example 1, main.pdf"
WIDTHS = (8, 16)
BRANCHES = 4
ROUNDS = 6
BOXES = {8: {"differential": (1, 6), "linear": (0, 6)},
         16: {"differential": (5, 24), "linear": (3, 12)}}
MINIMA = {8: {"differential": {1: 1, 2: 6, 3: 7, 4: 12, 5: 13, 6: 18},
              "linear": {1: 0, 2: 6, 3: 6, 4: 12, 5: 12, 6: 18}},
          16: {"differential": {1: 5, 2: 24, 3: 29, 4: 48, 5: 53, 6: 72},
               "linear": {1: 3, 2: 12, 3: 15, 4: 24, 5: 27, 6: 36}}}
EXAMPLE_W = 16
EXAMPLE_KIND = "differential"
EXAMPLE = ((1, 1), (1, 1), (0, 1), (1, 0))
EXAMPLE_LENGTHS = (1, 2, 3)
