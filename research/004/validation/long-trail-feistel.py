"""Known result `long-trail-feistel` of the long-trail counter, at w = 8 and 16 (research R12; data-model section 7).

The further known result that R12 asks for, since `sparkle-box` covers the counter's use at w = 32 and not at the D4 width, 16 or else 8. None of
research R19's approved papers gives a long-trail bound at those widths, so this one is self-written.

The layer is two branches of 2w bits, a left L and a right R, with a bijective linear F on a branch. For differences, new L = R xor F(L) and
new R = L. For masks, by the transpose of the inverse, new L = R and new R = L xor F'(R), with F' the transpose of F. It is `sparkle-box`'s layer
at h = 1, the box between layers and the chains as they are there, and r steps hold r - 1 layers.

For differences, L always goes on into R. R goes on into L only where L was inactive, since otherwise F(L) reaches it from outside: that chain
then ends, and the new L, if active, starts another. For masks the two branches trade places.

BOXES are bounds of a box at each width, as the counter takes them, one for each number of steps. At w = 16, SPECK32 at 4 and 8 rounds as
`speck32-diff` and `speck32-lin` state it: weights 5 and 24, and exponents of the correlation 3 and 12. At w = 8, the floors of `box-tables-second`
at 2 and 4 rounds of its round: 1 and 6, and for the squared correlation 0 and 6, so that one step of a mask costs nothing.

A chain of more steps than a box's bounds is cut, and costs the largest sum over the ways of cutting it: `chain_costs`. `enumerated` goes through
every truncated trail, 3 of them at r = 1 and 19 at r = 6, and adds the cost of each one's chains. That is the route of these values: plain
enumeration, with no solver and no search. By hand, the differences' minimum follows the pattern (L, R) of 01, 10, 11 repeated. R goes on into L,
L into R, and there F(L) reaches the next L, so that a chain of three ends, cancelled, as the L just started takes its place:

    r = 1: one chain of 1       r = 2: one chain of 2       r = 3: chains of 1 and 3
    r = 4: chains of 2 and 3    r = 5: chains of 3 and 3    r = 6: chains of 1, 3 and 4

which at w = 16 gives 5, 24, 5 + 29 = 34, 24 + 29 = 53, 29 + 29 = 58 and 5 + 29 + 48 = 82, as MINIMA says. Masks follow 10, 01, 11, with the same
chains.

What must match is the minimum at each r from 1 to ROUNDS, at each width, of each kind.
"""

TOOL = "long-trail active-box counting"
KNOWN_ID = "long-trail-feistel"
SECOND_OF = "none"
SOURCE = "self-written: every truncated trail enumerated in this file, and the winners by hand in its docstring"
WIDTHS = (8, 16)
ROUNDS = 6
BOXES = {8: {"differential": (1, 6), "linear": (0, 6)},
         16: {"differential": (5, 24), "linear": (3, 12)}}
MINIMA = {8: {"differential": {1: 1, 2: 6, 3: 8, 4: 13, 5: 14, 6: 20},
              "linear": {1: 0, 2: 6, 3: 6, 4: 12, 5: 12, 6: 18}},
          16: {"differential": {1: 5, 2: 24, 3: 34, 4: 53, 5: 58, 6: 82},
               "linear": {1: 3, 2: 12, 3: 18, 4: 27, 5: 30, 6: 42}}}


def chain_costs(box, longest):
    """The cost of a chain of each length up to `longest`, index 0 unused: the largest sum of bounds over the ways of cutting it."""
    costs = [0] * (longest + 1)
    for t in range(1, longest + 1):
        costs[t] = max(box[k - 1] + costs[t - k] for k in range(1, min(t, len(box)) + 1))
    return tuple(costs)


def following(kind, pattern):
    """The patterns (L, R) that may come after `pattern`."""
    left, right = pattern
    if kind == "differential":
        if not left:
            return [(right, 0)]
        return [(1, 1)] if not right else [(0, 1), (1, 1)]
    if not right:
        return [(0, left)]
    return [(1, 1)] if not left else [(1, 0), (1, 1)]


def going_on(kind, before, after):
    """What each chain of `before` goes on into, as {branch: branch}, 0 for L and 1 for R."""
    left, right = before
    if kind == "differential":
        links = {0: 1} if left else {}
        if right and not left and after[0]:
            links[1] = 0
        return links
    links = {1: 0} if right else {}
    if left and not right and after[1]:
        links[0] = 1
    return links


def chain_lengths(kind, trail):
    """The length of each chain of a truncated trail, sorted."""
    alive = {branch: 1 for branch in (0, 1) if trail[0][branch]}
    ended = []
    for before, after in zip(trail, trail[1:]):
        links = going_on(kind, before, after)
        following_alive = {}
        for branch, length in alive.items():
            if branch in links:
                following_alive[links[branch]] = length + 1
            else:
                ended.append(length)
        for branch in (0, 1):
            if after[branch] and branch not in following_alive:
                following_alive[branch] = 1
        alive = following_alive
    return sorted(ended + list(alive.values()))


def trails(kind, rounds):
    """Every truncated trail of `rounds` steps, active at each step."""
    out = [[start] for start in ((0, 1), (1, 0), (1, 1))]
    for _ in range(rounds - 1):
        out = [trail + [after] for trail in out for after in following(kind, trail[-1]) if any(after)]
    return out


def enumerated(kind, box, rounds):
    """The least sum of chain costs over every truncated trail of `rounds` steps."""
    costs = chain_costs(box, rounds)
    return min(sum(costs[length] for length in chain_lengths(kind, trail)) for trail in trails(kind, rounds))
