"""Feature 004: the mode's limits and the size profile (contracts/cli.md; research R9, R10).

    mode_limits_v3.py --out $REP/security-target/limits.json
    mode_limits_v3.py --reproduce RECORD

Reads three tables of the design document, each a Markdown table with fixed columns in a section of
its own (data-model section 10): "Variant table" in the chapter "Permutation", "Layout" and "Limits"
in the chapter "Mode". Exit 2 if one is missing, appears twice or holds a row it cannot read, or if
a theorem marked verified has no `fetched` entry in downloads.json, or its file on disk has another
SHA-256. Exit 1 if a bound exceeds the target advantage at the limits, if doubling a limit that a
term of a bound reads leaves both within that advantage, or on a violation at a claimable size.

Two bounds are evaluated: Theorem 1 of Daemen, Mennink and Van Assche, for keystream and multi-user
security, and the forget result of Gazi and Tessaro, Lemmas 10 and 12 summed by their Theorem 4, for
backtracking resistance. Every bound is computed in whole numbers and fractions, and a float only
ever prints one, so that no limit rests on a rounding. Writes `parameters.json` beside `limits.json`,
each under its fixed name.
"""
import argparse
import json
import math
import re
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Optional, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from protocol import evidence  # noqa: E402
from protocol.evidence import NONE, Refused  # noqa: E402

CODE = ["scripts/mode_limits_v3.py", "protocol/evidence.py", "protocol/disclaimer.py"]
DIRECTORY = "security-target"
TARGET_ADVANTAGE = Fraction(1, 2 ** 64)
OFFLINE_CALLS = 2 ** 128
REQUEST_CAP_BITS = 2 ** 19
MOST_INSTANTIATIONS = 2 ** 32
TARGET_LEVEL = 128
MOST_KEY_BITS = 256
LANES_PER_NODE = 2
WORD_BITS = 32
THROUGHPUT_GOAL = 10 ** 8

VARIANT_COLUMNS = ("ID", "n", "w", "b", "c", "r", "R", "status")
LAYOUT_COLUMNS = ("Size", "w", "c", "Rate lanes", "Capacity lanes", "Key lanes", "Nonce lanes")
LIMIT_COLUMNS = ("Limit", "Size", "Value", "Bits")
ALL_SIZES = "all"
KEYS = "keys u"
INSTANTIATIONS = "instantiations per key"
PER_INSTANTIATION = "calls of Π per instantiation"
PER_KEY = "calls of Π per key"
PER_REQUEST = "calls of Π per request"
PER_INSTANTIATE = "calls of Π per instantiate"
RESEEDS = "reseeds per instantiation"
PERSONALIZATION = "personalization string, bytes"
RESEED_INPUT = "reseed input, bytes"
FIRST_WAY = "nonces, first way"
SECOND_WAY = "nonces, second way"
FOR_ALL_SIZES = (KEYS, INSTANTIATIONS, RESEEDS, PERSONALIZATION, RESEED_INPUT, FIRST_WAY, SECOND_WAY)
PER_SIZE = (PER_INSTANTIATION, PER_KEY, PER_REQUEST, PER_INSTANTIATE)
PERSONALIZATION_BLOCK, RESEED_BLOCK = 1, 2
VARIANT_ID = re.compile(r"^[\w-]+/n(\d+)-w(\d+)-R(\d+)-c(\d+)$")
# Feature 005 (research R8; spec FR-011): the chapter "Security target"'s parameter table, whose R may be a placeholder.
PARAMETER_COLUMNS = ("Variant", "n", "w", "b", "c", "r", "R", "Key entropy", "Reachable secret state", "Bound", "Status")
OPEN_VARIANT_ID = re.compile(r"^[\w-]+/n(\d+)-w(\d+)-R(\d+|<R\d+>)-c(\d+)$")
PLACEHOLDER = re.compile(r"<R(\d+)>")
LIMITS_FIELDS = ("epsilon", "N", "theorems", "u", "per_instantiation", "per_key", "per_request", "per_instantiate",
                 "other_limits", "nonces", "bound", "doubling", "outside_the_doubling_check")
PROFILE_FIELDS = ("rows", "u", "throughput_goal")

# Every theorem the mode chapter uses (data-model section 10). The agent's marks are made here, once
# a paper is read, and count only as the security-target review row says (research R10).
THEOREMS: Tuple[Dict[str, Any], ...] = (
    {"id": "full-state keyed duplex", "paper": "Daemen.pdf", "theorem": "Theorem 1", "page": "619-620",
     "citation": "Daemen, Mennink and Van Assche, ASIACRYPT 2017", "status": "unverified",
     "covers": ["keystream", "multi-user"],
     "preconditions": (
         ("one ideal permutation f of b bits, in both directions", "Calls"),
         ("r < b and k <= b", "Layout"),
         ("the first call applies f to K||iv, the key in the state's first k bits", "Layout"),
         ("every later call is f, then the outer part returned, then sigma added", "Calls"),
         ("N + M <= 0.1 2^c at the limits", "Limits"),
         ("keys drawn independently and uniformly, so H_min and H_coll are k", "Key loading"),
         ("no path repeats, L = 0: a nonce is used once per key", "Nonce reuse"),
         ("each forget is one query with flag true, and no other call is", "Forget"),
         ("inputs absorbed over the rate are sigma with its inner part zero", "Padding and domain separation"),
         ("a reseed input is sigma chosen by the adversary before that call's Z", "Calls"),
         ("output is the outer part of the state after a full call of f", "Serialization"),
     )},
    {"id": "forget", "paper": "169.pdf", "theorem": "Lemma 12, with Lemma 10 and Theorem 4", "page": "25, 22, 14",
     "citation": "Gazi and Tessaro, EUROCRYPT 2016, ePrint 2016/169", "status": "unverified", "covers": ["backtracking"],
     "preconditions": (
         ("one ideal permutation of b bits, in both directions", "Calls"),
         ("next: f, the outer part read, then t times f and the outer part set to zero", "Forget"),
         ("refresh: an input added to the outer part, then f", "Calls"),
         ("before each next, a state of zeros in the outer part and a secret inner part", "Forget"),
         ("the key's state has min-entropy k, and is independent of f, for Lemma 10", "Key loading"),
         ("no seed: every input is taken as chosen by the adversary, and Lemma 12's proof reads "
          "only the inner part's secrecy", "Padding and domain separation"),
         ("several blocks from one next: the paper's remark on page 15, which it does not work out", "Forget"),
         ("the sum over the calls of next stays within the target advantage at the limits", "Limits"),
         ("the sum across instantiations and keys, with a nonce the adversary chooses: the mode "
          "chapter's own hybrid, which the paper does not state", "Limits"),
     )},
)


class Variant(NamedTuple):
    variant_id: str
    n: int
    w: int
    b: int
    c: int
    r: int
    rounds: int
    reason: str
    status: str


class Layout(NamedTuple):
    n: int
    w: int
    c: int
    rate: Tuple[int, ...]
    capacity: Tuple[int, ...]
    key: Tuple[int, ...]
    nonce: Tuple[int, ...]


class Limits(NamedTuple):
    keys: int
    instantiations: int
    calls: int
    per_key: int
    reseeds: int
    personalization: int
    reseed_input: int
    first_way: str
    second_way: str
    per_size: Dict[Tuple[str, int], Tuple[int, int]]


# ------------------------------------------------------------------------------ the three tables

def headings(lines: Sequence[str]) -> List[Tuple[int, int, str]]:
    """Each ATX heading outside fenced code: its line, its level and its text."""
    found, fence = [], None
    for number, line in enumerate(lines):
        mark = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if mark and fence is None:
            fence = mark.group(1)[0]
        elif mark and mark.group(1)[0] == fence:
            fence = None
        elif fence is None:
            match = re.match(r"^(#{1,6})\s+(.*?)\s*$", line)
            if match:
                found.append((number, len(match.group(1)), match.group(2)))
    return found


def span(heads: Sequence[Tuple[int, int, str]], level: int, title: str, first: int, last: int) -> Tuple[int, int]:
    """The lines of the one heading of that level and text between first and last."""
    named = [i for i, (line, depth, text) in enumerate(heads)
             if depth == level and text == title and first <= line < last]
    if len(named) != 1:
        raise Refused(f"the design document holds {len(named)} headings {title!r} of level {level}")
    start = heads[named[0]][0]
    ends = [line for line, depth, _ in heads[named[0] + 1:] if depth <= level]
    return start, min(ends + [last])


def section_lines(text: str, chapter: str, section: str) -> List[str]:
    lines = text.split("\n")
    heads = headings(lines)
    first, last = span(heads, 2, chapter, 0, len(lines))
    first, last = span(heads, 3, section, first, last)
    return lines[first:last]


def mode_sections(text: str) -> List[str]:
    lines = text.split("\n")
    heads = headings(lines)
    first, last = span(heads, 2, "Mode", 0, len(lines))
    return [title for line, depth, title in heads if depth == 3 and first < line < last]


def cells_of(line: str) -> List[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def read_table(lines: Sequence[str], columns: Sequence[str], where: str) -> List[Dict[str, str]]:
    """The one table with these columns: a table missing or twice, or a row that does not fit, is refused."""
    blocks: List[List[str]] = []
    block: List[str] = []
    for line in list(lines) + [""]:
        if line.lstrip().startswith("|"):
            block.append(line)
        elif block:
            blocks.append(block)
            block = []
    tables = [b for b in blocks if tuple(cells_of(b[0])) == tuple(columns)]
    if len(tables) != 1:
        raise Refused(f"{where}: {len(tables)} tables with the columns {list(columns)}")
    rows = tables[0][1:]
    if not rows or not all(re.fullmatch(r":?-+:?", cell) for cell in cells_of(rows[0])):
        raise Refused(f"{where}: a table with no separator line")
    out = []
    for row in rows[1:]:
        cells = cells_of(row)
        if len(cells) != len(columns):
            raise Refused(f"{where}: a row of {len(cells)} cells: {row.strip()}")
        out.append(dict(zip(columns, cells)))
    if not out:
        raise Refused(f"{where}: a table with no rows")
    return out


def whole(cell: str, where: str) -> int:
    """A whole number as the tables write it: 2^24, or digits with or without commas."""
    power = re.fullmatch(r"2\^(\d+)", cell)
    if power:
        return 2 ** int(power.group(1))
    if re.fullmatch(r"\d[\d,]*", cell):
        return int(cell.replace(",", ""))
    raise Refused(f"{where}: {cell!r} is no number")


def read_variants(text: str) -> List[Variant]:
    where = "the variant table"
    out = []
    for row in read_table(section_lines(text, "Permutation", "Variant table"), VARIANT_COLUMNS, where):
        match = VARIANT_ID.match(row["ID"])
        rounds = re.fullmatch(r"(\d+)(?:\s*\((.+)\))?", row["R"])
        if match is None or rounds is None:
            raise Refused(f"{where}: a row it cannot read: {row['ID']} {row['R']}")
        n, w, b, c, r = (whole(row[name], where) for name in ("n", "w", "b", "c", "r"))
        if (int(match.group(1)), int(match.group(2)), int(match.group(3)), int(match.group(4))) \
                != (n, w, int(rounds.group(1)), c):
            raise Refused(f"{where}: {row['ID']} differs from its row")
        if b != 2 * w * n * n or r != b - c or not 0 < c < b:
            raise Refused(f"{where}: {row['ID']}: b, c and r do not fit n and w")
        if row["status"] not in ("claimable", "research"):
            raise Refused(f"{where}: {row['ID']}: no status {row['status']!r}")
        out.append(Variant(row["ID"], n, w, b, c, r, int(rounds.group(1)), rounds.group(2) or NONE, row["status"]))
    if len({v.variant_id for v in out}) != len(out):
        raise Refused(f"{where}: a variant listed twice")
    return out


def variant_table_drafted(text: str) -> bool:
    """Whether the chapter "Permutation" holds its section "Variant table"."""
    lines = text.split("\n")
    heads = headings(lines)
    first, last = span(heads, 2, "Permutation", 0, len(lines))
    return any(depth == 3 and title == "Variant table" and first < line < last for line, depth, title in heads)


def read_parameter_variants(text: str) -> List[Variant]:
    """Feature 005: the variant rows from the chapter "Security target"'s parameter table, read while the chapter
    "Permutation" holds no variant table. A placeholder R, `<R4>`, `<R8>` or `<R16>`, stands where a number will: it is
    read as not yet known, kept as it is written, and every other figure of the row is checked (research R8)."""
    where = "the parameter table"
    out = []
    for row in read_table(section_lines(text, "Security target", "Parameter table"), PARAMETER_COLUMNS, where):
        match = OPEN_VARIANT_ID.match(row["Variant"])
        if match is None or match.group(3) != row["R"]:
            raise Refused(f"{where}: a row it cannot read: {row['Variant']} {row['R']}")
        n, w, b, c, r = (whole(row[name], where) for name in ("n", "w", "b", "c", "r"))
        if (int(match.group(1)), int(match.group(2)), int(match.group(4))) != (n, w, c):
            raise Refused(f"{where}: {row['Variant']} differs from its row")
        open_r = PLACEHOLDER.fullmatch(row["R"])
        if open_r is not None and int(open_r.group(1)) != n:
            raise Refused(f"{where}: {row['Variant']}: the placeholder of size {n} is <R{n}>")
        if b != 2 * w * n * n or r != b - c or not 0 < c < b:
            raise Refused(f"{where}: {row['Variant']}: b, c and r do not fit n and w")
        if row["Status"] not in ("claimable", "research"):
            raise Refused(f"{where}: {row['Variant']}: no status {row['Status']!r}")
        out.append(Variant(row["Variant"], n, w, b, c, r, row["R"] if open_r is not None else int(row["R"]), NONE, row["Status"]))
    if len({v.variant_id for v in out}) != len(out):
        raise Refused(f"{where}: a variant listed twice")
    return out


def variants_of(text: str) -> List[Variant]:
    """The variant table; under feature 005, the parameter table until the variant table is drafted (research R8)."""
    if evidence.FEATURE != "004" and not variant_table_drafted(text):
        return read_parameter_variants(text)
    return read_variants(text)


def stated_faults(text: str, rows: Sequence[Dict[str, Any]]) -> List[str]:
    """Feature 005: what the parameter table states beside each variant, against the row computed for it."""
    out = []
    computed = {row["variant_id"]: row for row in rows}
    for row in read_table(section_lines(text, "Security target", "Parameter table"), PARAMETER_COLUMNS, "the parameter table"):
        have = computed.get(row["Variant"])
        if have is None:
            out.append(f"{row['Variant']}: the parameter table names a variant the variant table does not hold")
            continue
        secret = have["reachable_secret_state_bits"]
        secret = secret if secret == NONE else secret["after_generate"]
        stated = (row["Key entropy"], row["Reachable secret state"], row["Bound"])
        wanted = (str(have["key_entropy_bits"]), str(secret), str(have["bound_bits"]))
        if stated != wanted:
            out.append(f"{row['Variant']}: the parameter table states {stated}, and the row gives {wanted}")
    return out


def lane_set(cell: str, total: int, where: str) -> Tuple[int, ...]:
    """Lanes as the layout writes them: `3`, `0-7`, `1-15/2`, joined by commas, or `none`."""
    if cell == "none":
        return ()
    out: List[int] = []
    for item in cell.split(","):
        match = re.fullmatch(r"(\d+)(?:-(\d+)(?:/(\d+))?)?", item.strip())
        if match is None:
            raise Refused(f"{where}: {cell!r} is no set of lanes")
        first, last, step = match.groups()
        if last is None:
            out.append(int(first))
            continue
        if int(last) <= int(first) or (step is not None and int(step) < 1):
            raise Refused(f"{where}: {cell!r} is no set of lanes")
        out.extend(range(int(first), int(last) + 1, int(step or 1)))
    if len(set(out)) != len(out) or any(lane >= total for lane in out):
        raise Refused(f"{where}: {cell!r} repeats a lane or passes the {total} lanes")
    return tuple(sorted(out))


def read_layouts(text: str) -> Dict[Tuple[int, int, int], Layout]:
    where = "the layout"
    out: Dict[Tuple[int, int, int], Layout] = {}
    for row in read_table(section_lines(text, "Mode", "Layout"), LAYOUT_COLUMNS, where):
        size = re.fullmatch(r"(\d+)×(\d+)", row["Size"])
        if size is None or size.group(1) != size.group(2):
            raise Refused(f"{where}: no size {row['Size']!r}")
        n = int(size.group(1))
        w, c = whole(row["w"], where), whole(row["c"], where)
        total = LANES_PER_NODE * n * n
        layout = Layout(n, w, c, *(lane_set(row[name], total, where) for name in LAYOUT_COLUMNS[3:]))
        if (n, w, c) in out:
            raise Refused(f"{where}: {row['Size']} at w = {w}, c = {c} listed twice")
        out[(n, w, c)] = layout
    return out


def read_limits(text: str, claimable: Sequence[Variant]) -> Limits:
    where = "the limits"
    rows = read_table(section_lines(text, "Mode", "Limits"), LIMIT_COLUMNS, where)
    single: Dict[str, str] = {}
    sized: Dict[Tuple[str, int], Tuple[int, int]] = {}
    sizes = {f"{v.n}×{v.n}": v.n for v in claimable}
    for row in rows:
        name, size = row["Limit"], row["Size"]
        if name in FOR_ALL_SIZES and size == ALL_SIZES and name not in single:
            single[name] = row["Value"]
        elif name in PER_SIZE and size in sizes and (name, sizes[size]) not in sized:
            sized[(name, sizes[size])] = (whole(row["Value"], where), whole(row["Bits"], where))
        else:
            raise Refused(f"{where}: a row it cannot read: {name} at {size}")
    missing = [name for name in FOR_ALL_SIZES if name not in single] + \
        [f"{name} at {n}×{n}" for name in PER_SIZE for n in sizes.values() if (name, n) not in sized]
    if missing:
        raise Refused(f"{where}: no row for {missing}")
    numbers = [whole(single[name], where) for name in (KEYS, INSTANTIATIONS, RESEEDS, PERSONALIZATION, RESEED_INPUT)]
    calls = {value for (name, _), (value, _) in sized.items() if name == PER_INSTANTIATION}
    per_key = {value for (name, _), (value, _) in sized.items() if name == PER_KEY}
    if len(calls) != 1 or len(per_key) != 1:
        raise Refused(f"{where}: a limit in calls of Π differs between sizes")
    return Limits(numbers[0], numbers[1], calls.pop(), per_key.pop(), numbers[2], numbers[3], numbers[4],
                  single[FIRST_WAY], single[SECOND_WAY], sized)


# ------------------------------------------------------------------------------ the mode's arithmetic

def key_bits(v: Variant) -> int:
    """Research R14: k = min(c, 256), so 256 at a claimable size and c at a keyed reduced variant."""
    return min(v.c, MOST_KEY_BITS)


def keyed(v: Variant) -> bool:
    """Research R14: c a multiple of 64, r of 32 and of two words at least, one of data and one of
    domain bits, and room in the state for the key, the nonce and the initial word."""
    k = key_bits(v)
    return v.c % 64 == 0 and v.r % 32 == 0 and v.r >= 2 * WORD_BITS and k + k // 2 + WORD_BITS <= v.b


def forget_calls(v: Variant) -> int:
    """Bertoni et al., section 4.3: ceil(c / r) overwrites leave c bits to guess going backwards."""
    return -(-v.c // v.r)


def input_blocks(length: int, r: int) -> int:
    """Blocks of an input of `length` bytes: its length word and its words, on r/32 - 1 words each."""
    words = 1 + -(-length // 4)
    return -(-words // (r // WORD_BITS - 1))


def absorbed_blocks(code: int, data: bytes, r: int) -> List[bytes]:
    """FR-014's encoding: a length word, the input and zero bytes to a whole word, cut into blocks of
    r/32 - 1 words, zero words filling the last, each block closed by its domain word."""
    size = r // 8 - 4
    encoded = len(data).to_bytes(4, "little") + data + bytes(-len(data) % 4)
    domain = code.to_bytes(4, "little")
    return [encoded[at:at + size].ljust(size, b"\0") + domain for at in range(0, len(encoded), size)]


def decoded_input(blocks: Sequence[bytes]) -> Tuple[int, bytes, int]:
    """The call type, the input and the blocks read, from the first block on: the other way of the
    proof, which needs nothing but the domain word and the length word."""
    code = int.from_bytes(blocks[0][-4:], "little")
    size = len(blocks[0]) - 4
    length = int.from_bytes(blocks[0][:4], "little")
    count = -(-(4 + length + -length % 4) // size)
    joined = b"".join(block[:-4] for block in blocks[:count])
    return code, joined[4:4 + length], count


def request_calls(bits: int, v: Variant) -> int:
    return -(-bits // v.r) + forget_calls(v)


def reseed_calls(length: int, r: int) -> int:
    """One call per block, and one more: `refresh` runs f after its last input, and `next` again."""
    return input_blocks(length, r) + 1


def instantiate_calls(length: int, v: Variant) -> int:
    """`next` from the key's state, the string as a refresh, then `next` again, its block withheld."""
    return (1 + forget_calls(v)) + reseed_calls(length, v.r) + (1 + forget_calls(v))


def call_blocks(call: str, value: Any, r: int) -> List[Tuple[Optional[bytes], bool]]:
    """What one call of the interface adds to the state, call of f by call of f: a block or None,
    and whether the outer part is overwritten. FR-014's encoding of every call type."""
    plain, flagged = (None, False), (None, True)
    if call == "generate":
        return [plain] * value + [flagged]
    if call == "reseed":
        return [(block, False) for block in absorbed_blocks(RESEED_BLOCK, value, r)] + [plain]
    if call == "instantiate":
        blocks = [(block, False) for block in absorbed_blocks(PERSONALIZATION_BLOCK, value, r)]
        return [plain, flagged] + blocks + [plain, plain, flagged]
    raise ValueError(call)


def decoded_calls(sequence: Sequence[Tuple[Optional[bytes], bool]]) -> List[Tuple[str, Any]]:
    """The calls back from what `call_blocks` gives, an instantiate first: the other way of the proof.
    A block's length word says where its input ends, and a run of plain calls ends at the flag."""
    def read_input(at: int) -> Tuple[bytes, int]:
        end = at
        while end < len(sequence) and sequence[end][0] is not None:
            end += 1
        _, data, count = decoded_input([block for block, _ in sequence[at:end]])
        return data, count

    data, count = read_input(2)
    out: List[Tuple[str, Any]] = [("instantiate", data)]
    at = 2 + count + 3
    while at < len(sequence):
        if sequence[at][0] is not None:
            data, count = read_input(at)
            out.append(("reseed", data))
            at += count + 1
        else:
            count = 0
            while not sequence[at + count][1]:
                count += 1
            out.append(("generate", count))
            at += count + 1
    return out


def multicollision_limit(balls: int, r: int, c: int) -> int:
    """An upper bound on Definition 2's function: the union bound Pr(mu > x) <= C(balls, x + 1) 2^(-rx)."""
    x = 1
    while math.comb(balls, x + 1) * 2 ** c > x * 2 ** (r * x):
        x += 1
    return x


def forget_terms(queries: int, blocks: int, v: Variant) -> Dict[str, Fraction]:
    """Lemma 12 of Gazi and Tessaro, one call of `next`, and Lemma 10, from the key's state, at t = forget calls."""
    t, b, c, r = forget_calls(v), v.b, v.c, v.r
    rate_term = Fraction(queries, 2 ** ((r - 1) * t))
    return {"preserving": Fraction((2 * blocks + 2) * (queries + blocks), 2 ** b) + rate_term
            + Fraction(4 * (queries + t) ** 2 + queries, 2 ** c),
            "from the key": Fraction(queries, 2 ** key_bits(v)) + rate_term + Fraction(4 * (queries + t) ** 2, 2 ** c)
            + Fraction(1, 2 ** b)}


def forget_bound(keys: int, instantiations: int, calls: int, v: Variant) -> Dict[str, Any]:
    """Theorem 4's sum: Lemma 12 over every call of `next`, at most one for each 1 + t calls of f, and
    Lemma 10 once per instantiation. Every call of f the construction makes counts among the queries,
    and a step's blocks are at most the calls of an instantiation."""
    total = keys * instantiations * calls
    steps = total // (1 + forget_calls(v))
    terms = forget_terms(OFFLINE_CALLS + total, calls, v)
    summed = {"preserving": steps * terms["preserving"], "from the key": keys * instantiations * terms["from the key"]}
    return {"steps": steps, "queries": OFFLINE_CALLS + total, "terms": summed, "total": sum(summed.values(), Fraction(0))}


def resources(keys: int, instantiations: int, calls: int, v: Variant) -> Dict[str, int]:
    """Theorem 1's quantities at the limits, each at its worst. A forget follows at least one call of
    its own request, or of its instantiate, so at most a share forget/(forget + 1) of the calls is flagged."""
    forget = forget_calls(v)
    total = keys * instantiations * calls
    return {"M": total, "Omega": total * forget // (forget + 1), "q": keys * instantiations, "q_iv": keys,
            "L": 0, "u": keys, "N": OFFLINE_CALLS}


def theorem_terms(have: Dict[str, int], v: Variant, instantiations: int) -> Dict[str, Fraction]:
    """Theorem 1 of Daemen et al., term by term, with H_min = H_coll = k, and the nonces' collision term."""
    big_m, omega, q, q_iv, big_l, u, big_n = (have[name] for name in ("M", "Omega", "q", "q_iv", "L", "u", "N"))
    k, b, c, r = key_bits(v), v.b, v.c, v.r
    nu = multicollision_limit(2 * (big_m - big_l), r, c)
    left = (big_m - q - big_l) * q
    return {"overwrites": Fraction((big_l + omega) * big_n, 2 ** c),
            "multicollisions": Fraction(2 * nu * (big_n + 1), 2 ** c),
            "repeated paths": Fraction(math.comb(big_l + omega + 1, 2), 2 ** c),
            "initial states": Fraction(left, 2 ** b - q),
            "state pairs": Fraction(big_m * (big_m - big_l - 1), 2 ** b),
            "initial keys": Fraction(left, 2 ** (k + min(c, b - k))),
            "key search": Fraction(q_iv * big_n, 2 ** k),
            "key pairs": Fraction(math.comb(u, 2), 2 ** k),
            "nonce collisions": Fraction(u * instantiations ** 2, 2 ** 129)}


def log2_of(value: Fraction) -> str:
    if value == 0:
        return "-inf"
    return f"{math.log2(value.numerator) - math.log2(value.denominator):.6f}"


def bound_at(keys: int, instantiations: int, calls: int, v: Variant) -> Fraction:
    """The larger of the two bounds, each of which must stay within the target advantage."""
    keystream = sum(theorem_terms(resources(keys, instantiations, calls, v), v, instantiations).values(), Fraction(0))
    return max(keystream, forget_bound(keys, instantiations, calls, v)["total"])


def doubled(limits: Limits, v: Variant) -> Dict[str, Dict]:
    """R9's doubling check, limit by limit, against the larger bound. The per-key limit is the
    product of two others, so that doubling it is doubling the calls of an instantiation."""
    out = {}
    for name, keys, instantiations, calls in (
            (KEYS, 2 * limits.keys, limits.instantiations, limits.calls),
            (INSTANTIATIONS, limits.keys, 2 * limits.instantiations, limits.calls),
            (PER_INSTANTIATION, limits.keys, limits.instantiations, 2 * limits.calls),
            (PER_KEY, limits.keys, limits.instantiations, 2 * limits.calls)):
        value = bound_at(keys, instantiations, calls, v)
        out[name] = {"log2_bound": log2_of(value), "above_target_advantage": value > TARGET_ADVANTAGE}
    return out


def table_faults(limits: Limits, claimable: Sequence[Variant]) -> List[str]:
    """Where the limits table disagrees with itself, with R9 or with a size's rate."""
    faults = []
    for name, value in ((KEYS, limits.keys), (INSTANTIATIONS, limits.instantiations),
                        (PER_INSTANTIATION, limits.calls), (PER_KEY, limits.per_key)):
        if value & (value - 1):
            faults.append(f"{name} is no power of two")
    if limits.instantiations > MOST_INSTANTIATIONS:
        faults.append(f"{INSTANTIATIONS} passes the most R9 allows")
    if limits.per_key != limits.instantiations * limits.calls:
        faults.append(f"{PER_KEY} is not the product of the two limits it joins")
    if limits.reseeds > limits.calls:
        faults.append(f"{RESEEDS} passes {PER_INSTANTIATION}")
    for v in claimable:
        for name, calls in ((PER_INSTANTIATION, limits.calls), (PER_KEY, limits.per_key)):
            if limits.per_size[(name, v.n)] != (calls, calls * v.r):
                faults.append(f"{name} at {v.n}×{v.n} is not {calls} calls of {v.r} bits")
        cap = min(REQUEST_CAP_BITS, limits.calls * v.r)
        if limits.per_size[(PER_REQUEST, v.n)] != (request_calls(cap, v), cap):
            faults.append(f"{PER_REQUEST} at {v.n}×{v.n} is not the cap's calls")
        first = instantiate_calls(limits.personalization, v)
        if limits.per_size[(PER_INSTANTIATE, v.n)] != (first, first * v.r):
            faults.append(f"{PER_INSTANTIATE} at {v.n}×{v.n} is not the {first} calls of the longest string")
    return faults


def layout_faults(layout: Layout, v: Variant) -> List[str]:
    """The form Theorem 1 takes: the state is the lanes in order, the outer part its first r bits,
    and the initial state K||iv, so the key fills the first k bits (Algorithm 1; its proof, section 6)."""
    lanes, width = LANES_PER_NODE * v.n * v.n, v.w
    rate = tuple(range(v.r // width))
    capacity = tuple(range(v.r // width, lanes))
    key = tuple(range(key_bits(v) // width))
    nonce = tuple(range(len(key), len(key) + key_bits(v) // 2 // width))
    faults = []
    for name, lanes_read, lanes_wanted in (("rate", layout.rate, rate), ("capacity", layout.capacity, capacity),
                                           ("key", layout.key, key), ("nonce", layout.nonce, nonce)):
        if lanes_read != lanes_wanted:
            faults.append(f"{v.variant_id}: its {name} lanes are not the theorem's form")
    return faults


# ------------------------------------------------------------------------------ the size profile

def profile_row(v: Variant, layouts: Dict[Tuple[int, int, int], Layout], limits: Limits,
                peers: Sequence[Variant], nonce_section: bool, output_volume: Optional[bool]) -> Dict[str, Any]:
    """One row of data-model section 10. A keyless variant has no key, no bound and no check."""
    size_keyed = sorted(p.variant_id for p in peers if p.n == v.n and keyed(p))
    row: Dict[str, Any] = {"n": v.n, "w": v.w, "lanes_per_node": LANES_PER_NODE, "b": v.b, "c": v.c, "r": v.r,
                           "variant_id": v.variant_id, "R": v.rounds, "R_reason": v.reason, "status": v.status,
                           "keyed_variants": size_keyed, "throughput_goal": THROUGHPUT_GOAL}
    if not keyed(v):
        row.update(key_entropy_bits=0, nonce_bits=0, reachable_secret_state_bits=NONE, bound_bits=NONE,
                   bound_terms=NONE, bound_label="keyless: permutation only", checks=NONE, violations=[])
        return row
    layout = layouts.get((v.n, v.w, v.c))
    if layout is None:
        raise Refused(f"the layout holds no row for {v.variant_id}")
    secret = len(layout.capacity) * v.w
    key, nonce = key_bits(v), key_bits(v) // 2
    terms = {"key entropy": key, "half the reachable secret state": secret // 2,
             "multi-target": max(key - int(math.log2(limits.keys)), 0),
             "half of key and nonce": (key + nonce) // 2, "half the capacity": v.c // 2,
             "single-target quantum search": key // 2}
    least = min(terms.values())
    level = TARGET_LEVEL if v.status == "claimable" else v.c // 2
    checks = {"key entropy": key >= level, "reachable secret state": secret >= 2 * level,
              "multi-target": terms["multi-target"] >= level, "key and nonce": key + nonce >= 2 * level,
              "capacity": v.c >= 2 * level, "quantum search": key // 2 >= level,
              "nonce reuse stated": nonce_section, "output volume": output_volume if output_volume is not None else NONE}
    faults = layout_faults(layout, v)
    violations = sorted(name for name, holds in checks.items() if holds is False) + faults
    row.update(key_entropy_bits=key, nonce_bits=nonce, bound_bits=least, level_checked=level,
               reachable_secret_state_bits={"after_instantiate": secret, "after_generate": secret,
                                            "after_reseed": secret, "basis": "by specification"},
               bound_terms=dict(terms, sets=sorted(name for name, value in terms.items() if value == least)),
               bound_label="research variant, no claim" if v.status == "research" else "target, not a claim",
               checks=checks, quantum_met_with_equality=key // 2 == level, violations=violations,
               forget_calls=forget_calls(v), rate_lanes=len(layout.rate), capacity_lanes=len(layout.capacity))
    return row


def theorem_entries(manifest: Sequence[Dict], root: Path, sections: Sequence[str]) -> List[Dict]:
    """Each theorem with its paper's `fetched` entry; `verified` needs that entry and its file on disk."""
    named = {entry["name"]: entry for entry in manifest}
    out = []
    for theorem in THEOREMS:
        entry = named.get(theorem["paper"], {})
        fetched = entry.get("status") == "fetched"
        if theorem["status"] not in ("verified", "unverified"):
            raise Refused(f"{theorem['id']}: no status {theorem['status']!r}")
        if theorem["status"] == "verified":
            if not fetched:
                raise Refused(f"{theorem['id']} is verified, and {theorem['paper']} has no `fetched` entry")
            path = Path(entry["local_path"].replace("\\", "/"))
            path = path if path.is_absolute() else root / path
            if not path.exists() or evidence.sha256(path.read_bytes()) != entry["sha256"]:
                raise Refused(f"{theorem['id']} is verified, and {theorem['paper']} on disk has another SHA-256")
        rows = []
        for text, section in theorem["preconditions"]:
            if section not in sections:
                raise Refused(f"{theorem['id']}: {section!r} is no section of the mode chapter")
            rows.append({"precondition": text, "section": section, "met": theorem["status"] == "verified"})
        out.append({"id": theorem["id"], "paper": theorem["paper"], "citation": theorem["citation"],
                    "fetched_sha256": entry["sha256"] if fetched else NONE, "theorem": theorem["theorem"],
                    "page": theorem["page"], "status": theorem["status"], "covers": theorem["covers"],
                    "preconditions": rows})
    return out


def power(value: int) -> str:
    return f"2^{value.bit_length() - 1}" if value and not value & (value - 1) else str(value)


def compute(text: str, manifest: Sequence[Dict], root: Path) -> Dict[str, Any]:
    """Both files' fields from the design document's text, with the run's verdict."""
    variants = variants_of(text)
    claimable = [v for v in variants if v.status == "claimable"]
    if not claimable:
        raise Refused("the variant table holds no claimable size")
    layouts = read_layouts(text)
    limits = read_limits(text, claimable)
    sections = mode_sections(text)
    theorems = theorem_entries(manifest, root, sections)
    faults = table_faults(limits, claimable)
    if faults:
        raise Refused("the limits: " + "; ".join(faults))
    nonce_section = "Nonce reuse" in sections

    bounds: Dict[str, Dict] = {}
    doubling: Dict[str, Dict] = {}
    within: Dict[str, bool] = {}
    for v in claimable:
        have = resources(limits.keys, limits.instantiations, limits.calls, v)
        terms = theorem_terms(have, v, limits.instantiations)
        total = sum(terms.values(), Fraction(0))
        condition = 10 * (have["N"] + have["M"]) <= 2 ** v.c
        forget = forget_bound(limits.keys, limits.instantiations, limits.calls, v)
        bounds[v.variant_id] = {"keystream": {"resources": {k: power(n) for k, n in have.items()},
                                              "terms_log2": {k: log2_of(t) for k, t in terms.items()},
                                              "log2_bound": log2_of(total), "at_most_target_advantage": total <= TARGET_ADVANTAGE,
                                              "theorem_condition": condition},
                                "backtracking": {"calls_of_next": power(forget["steps"]), "queries": "N + M",
                                                 "terms_log2": {k: log2_of(t) for k, t in forget["terms"].items()},
                                                 "log2_bound": log2_of(forget["total"]),
                                                 "at_most_target_advantage": forget["total"] <= TARGET_ADVANTAGE}}
        doubling[v.variant_id] = doubled(limits, v)
        within[v.variant_id] = total <= TARGET_ADVANTAGE and forget["total"] <= TARGET_ADVANTAGE and condition \
            and all(entry["above_target_advantage"] for entry in doubling[v.variant_id].values())

    rows = [profile_row(v, layouts, limits, variants, nonce_section, within.get(v.variant_id)) for v in variants]
    if evidence.FEATURE != "004":
        for v, row in zip(variants, rows):
            if v.status == "claimable":
                # Both figures are computed from R and the hardware structure's latencies (inherited data-model section 10):
                # where R is a placeholder they keep it, and they wait for the chapter "Hardware structure" otherwise.
                open_figure = v.rounds if isinstance(v.rounds, str) else NONE
                row.update(throughput_implied=open_figure, rate_before_forget=open_figure)
        stated = stated_faults(text, rows)
        if stated:
            raise Refused("the parameter table: " + "; ".join(stated))
    broken = sorted(row["variant_id"] for row in rows if row["status"] == "claimable" and row["violations"])
    held = not broken
    limits_fields = {
        "epsilon": "2^-64", "N": "2^128", "theorems": theorems, "u": power(limits.keys),
        "per_instantiation": {"calls": power(limits.calls), "bits": {v.variant_id: limits.calls * v.r for v in claimable}},
        "per_key": {"calls": power(limits.per_key), "bits": {v.variant_id: limits.per_key * v.r for v in claimable}},
        "per_request": {v.variant_id: {"calls": limits.per_size[(PER_REQUEST, v.n)][0],
                                       "bits": limits.per_size[(PER_REQUEST, v.n)][1]} for v in claimable},
        "per_instantiate": {v.variant_id: limits.per_size[(PER_INSTANTIATE, v.n)][0] for v in claimable},
        "other_limits": {"instantiations_per_key": power(limits.instantiations), "reseeds_per_instantiation": power(limits.reseeds),
                         "personalization_bytes": limits.personalization, "reseed_input_bytes": limits.reseed_input},
        "nonces": {"first_way": limits.first_way, "second_way": limits.second_way, "collision_term": "q^2/2^129"},
        "bound": bounds, "doubling": doubling,
        "outside_the_doubling_check": {
            "per-request cap": "research R9 fixes it at 2^19 bits, and no term of the theorem reads it",
            RESEEDS: "a reseed takes at least one call, so that the limit on calls holds it"}}
    profile_fields = {"rows": rows, "u": power(limits.keys), "throughput_goal": THROUGHPUT_GOAL}
    assertions = [{"assertion": "each bound is within the target advantage at the limits, and doubling a limit that a "
                                "term reads passes that advantage, at every claimable size", "holds": all(within.values())},
                  {"assertion": "no violation of a generic bound at a claimable size", "holds": not broken}]
    return {"limits": limits_fields, "parameters": profile_fields, "held": held, "assertions": assertions}


# ------------------------------------------------------------------------------ the two files

def fixed_run(name: str, command: Sequence[str]) -> evidence.Run:
    return evidence.Run("security-target", directory=DIRECTORY, file_name=name, fixed=True, argv=command,
                        code_files=CODE)


def write(result: Dict[str, Any], command: Sequence[str]) -> int:
    status, code = ("pass", evidence.EXIT_OK) if result["held"] else ("fail", evidence.EXIT_VERDICT)
    for name, fields in (("parameters.json", result["parameters"]), ("limits.json", result["limits"])):
        with fixed_run(name, command) as run:
            path = run.finish(status, fields=dict(fields, inputs=NONE), assertions=result["assertions"], exit_status=code)
        print(f"{evidence.rel_to_repo(path)}: {status}")
    return code


def reproduce(args: argparse.Namespace, command: List[str]) -> int:
    path = Path(args.reproduce)
    path = path if path.is_absolute() else evidence.REPO.path(args.reproduce)
    if not path.exists():
        raise Refused(f"{args.reproduce} does not exist")
    original = json.loads(path.read_bytes().decode("utf-8"))
    if original.get("kind") != "security-target":
        raise Refused(f"{args.reproduce} is no size profile or limits file")
    part = "limits" if "epsilon" in original else "parameters"

    def run(place: evidence.Place) -> Dict:
        text = (place.worktree / evidence.DESIGN_REL).read_bytes().decode("utf-8")
        data = (place.worktree / evidence.DOWNLOADS_REL).read_bytes().decode("utf-8")
        result = compute(text, json.loads(data)["entries"], ROOT)
        return dict(result[part], kind="security-target", inputs=NONE, model_id=original.get("model_id"), variant_id=None,
                    exit_status=evidence.EXIT_OK if result["held"] else evidence.EXIT_VERDICT,
                    assertions=result["assertions"], status="pass" if result["held"] else "fail",
                    classification=NONE, code_sha256=original["code_sha256"], outputs=[])

    extra = LIMITS_FIELDS if part == "limits" else PROFILE_FIELDS
    return evidence.reproduce(evidence.Reproduction(record_path=path, run=run, extra=extra, code_files=CODE, argv=command))


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--out")
    modes.add_argument("--reproduce")
    args = parser.parse_args(argv)
    command = ["scripts/mode_limits_v3.py"] + list(sys.argv[1:] if argv is None else argv)

    def body() -> int:
        if args.reproduce:
            return reproduce(args, command)
        if evidence.REPO.path(args.out).resolve() != (evidence.REPO.rep / DIRECTORY / "limits.json").resolve():
            raise Refused(f"--out must be {evidence.REP_REL}/{DIRECTORY}/limits.json")
        design = evidence.REPO.path(evidence.DESIGN_REL)
        if not design.exists():
            raise Refused(f"{evidence.DESIGN_REL} does not exist")
        # Feature 005 plans no download: a theorem's paper is feature 004's `fetched` entry, read as FR-001 states.
        manifest = evidence.read_manifest() if evidence.FEATURE == "004" else evidence.read_manifest("004")
        return write(compute(design.read_bytes().decode("utf-8"), manifest, evidence.REPO.root), command)

    return evidence.main_guard(body)


if __name__ == "__main__":
    raise SystemExit(main())
