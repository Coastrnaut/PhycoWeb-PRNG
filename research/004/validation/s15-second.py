"""Second known result of `s15` (research R4, R12, R13): a bound reached in stated steps, on a stated map.

S15: from every starting state every vein is at most 2^31 within 16 steps, which leaves at most
2^128 · (2^31 + 1)^4 states after them. This stated map shows the same shape. Each of four 32-bit words goes
through h(D) = (D >> 1) + (D and 1), D / 2 rounded up, and t steps of h give D / 2^t rounded up, so that from
every starting word

    after STEPS = 4 steps a word is at most 2^28, reached at D = 2^32 - 1, since (2^32 - 1) / 16 rounds up to 2^28
    after 3 steps it can be 2^29, which is more than that

So 4 is the first step count with the bound, and a state of four such words beside four free 32-bit words has
at most 2^128 · (2^28 + 1)^4 values after them. What must match, exactly: bit 28 is set after 4 steps only on
a word equal to 2^28, no higher bit is set, on every test state and on EDGE; the bound above; and the word
EDGE[0] exceeds 2^28 after 3 steps.
"""
TOOL = "bias"
KNOWN_ID = "s15-second"
SECOND_OF = "s15"
SOURCE = "self-written: derived by hand in this file's docstring"
W = 32
WORDS = 4
STEPS = 4
LIMIT = 1 << 28
BOUND = 2 ** 128 * (LIMIT + 1) ** 4
EDGE = (2 ** 32 - 1, 2 ** 32 - 16, 2 ** 28, 1, 0)


def h(value):
    return (value >> 1) + (value & 1)


def after(value, steps):
    for _ in range(steps):
        value = h(value)
    return value
