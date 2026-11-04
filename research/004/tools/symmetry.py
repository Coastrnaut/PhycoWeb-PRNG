"""Feature 004: the symmetry check (research R13; data-model section 5).

No symmetry of the torus that moves a node may map a constant pattern to itself, and no word rotation by
k = 1 ... w - 1 may map a round's constants to themselves. The torus's symmetries are every composition of
translations, rotations by 90°, 180° and 270° and reflections, in the stated order below, and each is also
composed with each word rotation. The patterns are each round's constants, the placement of the food
nodes and every per-node constant, each on its own. At 2×2 and 3×3, where every placement has such a
symmetry, the placements are checked with the round constants as one pattern, and the record says so.

Beside them, the relations between the constants of one call: equal, equal up to a word rotation,
complements, and rotations of complements.

Run on its known results by scripts/validate_tool.py (`s7`, the stated lists and their seconds; R13).
Analysis code: the model never imports it. This tool makes no security claim.
"""
import sys
from itertools import combinations
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[3]
for place in (str(ROOT / "research/004"), str(ROOT)):
    if place not in sys.path:
        sys.path.insert(0, place)

import ir  # noqa: E402
from phycoweb import model_v2  # noqa: E402

CODE = ("research/004/ir.py", "phycoweb/model_v2.py", "phycoweb/lut.py")
LINEAR = (("id", (1, 0, 0, 1)), ("r90", (0, 1, -1, 0)), ("r180", (-1, 0, 0, -1)),
          ("r270", (0, -1, 1, 0)), ("swap", (0, 1, 1, 0)), ("flip-j", (1, 0, 0, -1)),
          ("flip-i", (-1, 0, 0, 1)), ("anti", (0, -1, -1, 0)))
JOINED_SIZES = (2, 3)
RESET_VEINS = tuple(0x00010000 << k for k in range(4))
KIND = {"widths": [8, 16, 32],
        "operations": "torus symmetries and word rotations, on constants, placements and amounts",
        "model": "enumeration of every symmetry that moves a node",
        "uses": [{"use": "the symmetry check at every supported size",
                  "covered_by": ["s7", "symmetry-planted"]}]}


# ------------------------------------------------------------------------------------ the group

def nodes(n: int) -> List[Tuple[int, int]]:
    return [(i, j) for i in range(n) for j in range(n)]


def group(n: int) -> List[Tuple[Tuple[str, int, int], Tuple[Tuple[int, int], ...]]]:
    """Every symmetry that moves a node, once, as (name, a, b) and its images in node order: a
    linear part from LINEAR, then a translation. Two names of one map, as at 2×2, keep the first."""
    order = nodes(n)
    seen = {tuple(order)}
    out = []
    for name, (p, q, r, s) in LINEAR:
        for a in range(n):
            for b in range(n):
                image = tuple(((p * i + q * j + a) % n, (r * i + s * j + b) % n) for i, j in order)
                if image not in seen:
                    seen.add(image)
                    out.append(((name, a, b), image))
    return out


def rotl(word: int, k: int, w: int) -> int:
    return ((word << k) | (word >> (w - k))) & ((1 << w) - 1)


def fixing(pattern: Dict[Tuple[int, int], Any], n: int) -> List[Tuple[Tuple[int, int], ...]]:
    """The symmetries that map a pattern to itself, a node outside it holding nothing."""
    order = nodes(n)
    found = []
    for _, image in group(n):
        if all(pattern.get(x) == pattern.get(y) for x, y in zip(order, image)):
            found.append(image)
    return found


def turned(value: Any, k: int, w: int) -> Any:
    """A constants' value with every word rotated by k: a tuple of (lane kind, word)."""
    return None if value is None else tuple((kind, rotl(word, k, w)) for kind, word in value)


def word_rotations(pattern: Dict[Tuple[int, int], Any], w: int) -> List[int]:
    """The k that map a round's constants to themselves, each in its place."""
    return [k for k in range(1, w)
            if all(value == turned(value, k, w) for value in pattern.values())]


def composed(pattern: Dict[Tuple[int, int], Any], n: int, w: int) -> List[List[Any]]:
    """Each symmetry that moves a node, composed with each word rotation, that keeps the constants."""
    order = nodes(n)
    found = []
    for symmetry, image in group(n):
        for k in range(1, w):
            if all(pattern.get(x) == turned(pattern.get(y), k, w) for x, y in zip(order, image)):
                found.append([list(symmetry), k])
    return found


# -------------------------------------------------------------------------------- the list's patterns

def amounts_in(expr: Any) -> List[Tuple[str, int]]:
    kind = type(expr)
    if kind in (ir.Rotl, ir.Shl, ir.Shr):
        return [(kind.__name__, expr.amount)] + amounts_in(expr.value)
    if kind is ir.Not:
        return amounts_in(expr.value)
    if kind in (ir.Xor, ir.And, ir.Or):
        return amounts_in(expr.left) + amounts_in(expr.right)
    return []


def constants_at(program: "ir.Program") -> Dict[Tuple[int, int], List[Tuple[int, int]]]:
    """Each food node's constants as (lane kind, column), in list order."""
    out: Dict[Tuple[int, int], List[Tuple[int, int]]] = {}
    for phase in program.phases:
        for update in phase.updates:
            if type(update) is ir.Mix:
                for column in sorted(ir.constants_used(update.expr)):
                    node = ir.node_of(program.n, update.dst)
                    out.setdefault(node, []).append((update.dst % 2, column))
    return out


def amounts_at(program: "ir.Program") -> Dict[Tuple[int, int], Tuple[Tuple[str, int], ...]]:
    """Each node's rotation and shift amounts, in list order."""
    out: Dict[Tuple[int, int], List[Tuple[str, int]]] = {}
    for phase in program.phases:
        for update in phase.updates:
            node = ir.node_of(program.n, update.dst)
            held = amounts_in(update.expr) if type(update) is ir.Mix \
                else [("Rot", update.amount)]
            out.setdefault(node, []).extend(held)
    return {node: tuple(held) for node, held in out.items() if held}


def patterns(program: "ir.Program", table: Sequence[Sequence[int]]) -> Dict[str, Dict]:
    """Each pattern on its own, by name: the placement, each round's constants, the amounts."""
    food = constants_at(program)
    out: Dict[str, Dict] = {}
    if food:
        out["placement"] = {node: 1 for node in food}
        for r, row in enumerate(table):
            out[f"round {r}"] = {node: tuple((kind, row[column]) for kind, column in held)
                                 for node, held in food.items()}
    amounts = amounts_at(program)
    if amounts:
        out["amounts"] = amounts
    return out


def joined(program: "ir.Program", table: Sequence[Sequence[int]]) -> Dict[str, Dict]:
    """At 2×2 and 3×3: the placements with each round's constants, as one pattern (R13)."""
    food = constants_at(program)
    amounts = amounts_at(program)
    out = {}
    for r, row in enumerate(table):
        out[f"round {r} with the placements"] = {
            node: (tuple((kind, row[column]) for kind, column in food.get(node, ())),
                   amounts.get(node, ())) for node in nodes(program.n)}
    return out


def check(program: "ir.Program", table: Sequence[Sequence[int]]) -> Dict:
    """Every symmetry that fixes each pattern. `pass` is computed by the caller from `found`."""
    n, w = program.n, program.w
    chosen = joined(program, table) if n in JOINED_SIZES else patterns(program, table)
    fixed = {}
    for name, pattern in chosen.items():
        fixed[name] = fixing(pattern, n)
    rounds = {name: pattern for name, pattern in patterns(program, table).items()
              if name.startswith("round")}
    return {"size": n, "width": w, "joined": n in JOINED_SIZES, "fixed": fixed,
            "word_rotations": {name: word_rotations(p, w) for name, p in rounds.items()},
            "composed": {name: composed(p, n, w) for name, p in rounds.items()}}


# ------------------------------------------------------------------- relations between constants

def relations(words: Sequence[int], w: int) -> Dict[str, List[Any]]:
    """Between the words of one call: a word its own rotation keeps, two words equal, a rotation
    apart, complements, or a rotation of complements. The sets of amounts are listed in full."""
    mask = (1 << w) - 1
    out: Dict[str, List[Any]] = {"periodic": [], "equal": [], "rotations": [], "complements": [],
                                 "rotated_complements": []}
    for word in sorted(set(words)):
        held = [k for k in range(1, w) if rotl(word, k, w) == word]
        if held:
            out["periodic"].append([word, held])
    for a, b in combinations(words, 2):
        if a == b:
            out["equal"].append([a, b])
        held = [k for k in range(1, w) if rotl(a, k, w) == b]
        if held and a != b:
            out["rotations"].append([a, b, held])
        if a ^ b == mask:
            out["complements"].append([a, b])
        held = [k for k in range(1, w) if rotl(a, k, w) == b ^ mask]
        if held:
            out["rotated_complements"].append([a, b, held])
    return out


# ----------------------------------------------------------------------------------- known results

def re_find_s7(known, keep) -> Dict:
    """S7: 0x5A5A5A5A is unchanged by 8-bit rotations, 0xA5A5A5A5 is its rotation by 4, and the reset
    values of the veins are 1-bit rotations of each other."""
    words = [model_v2.X1, model_v2.X3] + list(RESET_VEINS)
    found = relations(words, 32)
    periodic = {word: held for word, held in found["periodic"]}
    pairs = {(a, b): held for a, b, held in found["rotations"]}
    held = periodic.get(model_v2.X1) == [8, 16, 24] \
        and pairs.get((model_v2.X1, model_v2.X3)) == [4, 12, 20, 28] \
        and all(pairs.get((a, b)) == [RESET_VEINS.index(b) - RESET_VEINS.index(a)]
                for a, b in combinations(RESET_VEINS, 2))
    return {"found": found, "re_found": held, "validated_kind": KIND}


def re_find_s7_second(known, keep) -> Dict:
    found = relations(known.WORDS, known.W)
    held = {word: tuple(ks) for word, ks in found["periodic"]} == known.FIXED_BY \
        and sorted((a, b, tuple(ks)) for a, b, ks in found["rotations"]) == sorted(known.ROTATIONS) \
        and [tuple(pair) for pair in found["complements"]] == list(known.COMPLEMENTS) \
        and not found["equal"]
    return {"found": found, "re_found": held, "validated_kind": KIND}


def images_of(known, n: int, symmetries: Iterable[Tuple[str, int, int]]) -> set:
    order = nodes(n)
    return {tuple(known.node_map(n, symmetry)[x] for x in order) for symmetry in symmetries}


def fixed_set(program: "ir.Program", table: Sequence[Sequence[int]]) -> Tuple[Dict[str, set], Dict]:
    """Each pattern's fixing set on its own, joined or not, as sets of images."""
    n = program.n
    each = patterns(program, table)
    return {name: set(fixing(pattern, n)) for name, pattern in each.items()}, each


def show(fixed: Dict[str, set]) -> Dict[str, int]:
    return {name: len(images) for name, images in fixed.items()}


def re_find_planted(known, keep) -> Dict:
    results = []
    held = True
    for entry in known.CASES + (known.WORD_ROTATION,):
        n = entry["n"]
        for w in known.WIDTHS:
            program, table = known.build(entry, w), known.table(entry, w)
            ir.load(program)
            fixed, each = fixed_set(program, table)
            rounds = [name for name in each if name.startswith("round")]
            turns = [word_rotations(each[name], w) for name in rounds]
            mixed = [composed(each[name], n, w) for name in rounds]
            good = fixed["placement"] == images_of(known, n, entry["placement"]) \
                and all(fixed[name] == images_of(known, n, entry["round"]) for name in rounds) \
                and all(tuple(ks) == known.word_rotations(entry, w) for ks in turns) \
                and "amounts" not in each and not any(mixed)
            held = held and good and len(rounds) == known.ROUNDS
            results.append({"list": entry["name"], "n": n, "w": w, "fixed": show(fixed),
                            "word_rotations": turns[0], "re_found": good})
    return {"found": {"lists": results}, "re_found": held, "validated_kind": KIND}


def re_find_planted_second(known, keep) -> Dict:
    results = []
    held = True
    for w in known.WIDTHS:
        for name, n, amount, wanted in known.AMOUNTS:
            program = known.build_amounts(name, n, amount, w)
            ir.load(program)
            fixed, _ = fixed_set(program, ())
            good = fixed == {"amounts": images_of(known, n, wanted)}
            held = held and good
            results.append({"list": name, "n": n, "w": w, "fixed": show(fixed), "re_found": good})
        program = known.build_placement(w)
        ir.load(program)
        fixed, _ = fixed_set(program, known.table(w))
        good = fixed["placement"] == images_of(known, 4, known.TURNS) \
            and fixed["round 0"] == set() and fixed["round 1"] == set()
        held = held and good
        results.append({"list": "placement-only", "n": 4, "w": w, "fixed": show(fixed), "re_found": good})
    return {"found": {"lists": results}, "re_found": held, "validated_kind": KIND}


RUNS = {"s7": re_find_s7, "symmetry-s7-second": re_find_s7_second,
        "symmetry-planted": re_find_planted, "symmetry-planted-second": re_find_planted_second}


def validation(known_id: str, known, keep: Optional[Callable[[str, bytes], None]]) -> Dict:
    return RUNS[known_id](known, keep)


def model_id(known_id: str) -> Optional[str]:
    return "phyco-v2" if known_id == "s7" else None
