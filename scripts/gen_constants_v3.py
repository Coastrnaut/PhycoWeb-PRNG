"""Feature 004: the constant generator (contracts/cli.md; research R15; data-model sections 11 and 13).

    gen_constants_v3.py [--check]                   writes phycoweb/constants_v3.py and the JSON tables
    gen_constants_v3.py --candidate ID --variant V  a candidate's table, before the freeze
    gen_constants_v3.py --exploration N W           an (n, w) outside the supported sizes
    gen_constants_v3.py --reproduce RECORD          a generator-run or generator-check record

The rule, fixed by research R15: the polynomials x^64 + c(x) with c(0) = 1, in ascending order of the
integer whose bits are c's coefficients, the first primitive one not on the refused list; Fibonacci
form s(t + 64) = sum of c_i s(t + i), seeded with the bits of ASCII `PhycoWeb`, most significant
first, and read from s(64) on, w bits per word, most significant first, in the order round, food
node, skipping any word that is periodic or related to a constant already taken in the same call.
The four call types share one stream. Where a call needs more constants than there are aperiodic
classes, the record of taken classes starts afresh each time every class has been used once, and
every repeat is recorded.

The LFSR is a stated rule that yields a fixed table: no key, nonce or state enters it. A match with
the refused list makes a candidate fail FR-023 and is never a reason to change the rule. Every record
holds the list's path and SHA-256 in `refused_list`, and every mode but --reproduce exits 2 while
that SHA-256 is not the one the protocol change log last names.

This script makes no security claim.
"""
import argparse
import json
import platform as platform_module
import re
import shlex
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]
for place in (str(ROOT), str(ROOT / "research/004"), str(ROOT / "research/004/tools")):
    if place not in sys.path:
        sys.path.insert(0, place)

from protocol import candidates, changelog, devinputs_v3, evidence  # noqa: E402
from protocol.evidence import NONE, Refused, ToolFailure  # noqa: E402

import ir  # noqa: E402
import numpy as np  # noqa: E402
import symmetry  # noqa: E402

CODE = ["scripts/gen_constants_v3.py", "protocol/evidence.py", "protocol/disclaimer.py",
        "protocol/candidates.py", "protocol/changelog.py", "protocol/devinputs_v3.py",
        "research/004/ir.py", "research/004/tools/symmetry.py"]
SCRIPT = CODE[0]
DEGREE = 64
SEED = int.from_bytes(b"PhycoWeb", "big")
# 2^64 - 1 = 3 · 5 · 17 · 257 · 641 · 65537 · 6700417.
ORDER_PRIMES = (3, 5, 17, 257, 641, 65537, 6700417)
RUN_BITS = 64
ENUMERATED_WIDTH = 8
VARIANT = re.compile(r"n(\d+)-w(\d+)-R(\d+)-c(\d+)")
MODULE_REL = "phycoweb/constants_v3.py"
VECTORS_REL = "vectors/phyco-v3"
SIDECAR_REL = VECTORS_REL + "/MANIFEST.json"
EXPLORATION_REL = "research/004/exploration"


def _follow_feature() -> None:
    """The module, the vectors and the exploration tables are the active feature's model's
    (feature 005, research R9): phycoweb/constants_v4.py and vectors/phyco-v4 under 005."""
    global MODULE_REL, VECTORS_REL, SIDECAR_REL, EXPLORATION_REL
    version = evidence.MODEL_ID.rsplit("-", 1)[-1]
    MODULE_REL = f"phycoweb/constants_{version}.py"
    VECTORS_REL = "vectors/" + evidence.MODEL_ID
    SIDECAR_REL = VECTORS_REL + "/MANIFEST.json"
    EXPLORATION_REL = evidence.FEATURES[evidence.FEATURE]["research"] + "/exploration"


evidence.on_feature(_follow_feature)
REFERENCE_STATES = 12
RUN_FIELDS = ("files", "refused_list", "checks")
CHECK_FIELDS = ("files", "refused_list", "verdict")


# ---------------------------------------------------------------------- the polynomial

def times_x_power(exponent: int, poly: int) -> int:
    """x^exponent modulo poly over GF(2), by squaring."""
    def reduce(value: int) -> int:
        while value.bit_length() > DEGREE:
            value ^= poly << (value.bit_length() - DEGREE - 1)
        return value

    def square(value: int) -> int:
        out, place = 0, 0
        while value >> place:
            if value >> place & 1:
                out ^= 1 << (2 * place)
            place += 1
        return reduce(out)

    result = 1
    for bit in bin(exponent)[2:]:
        result = square(result)
        if bit == "1":
            result = reduce(result << 1)
    return result


def is_primitive(c: int) -> bool:
    """x has order 2^64 - 1 modulo x^64 + c(x), so that the quotient ring is the field."""
    poly = 1 << DEGREE | c
    order = (1 << DEGREE) - 1
    return times_x_power(order, poly) == 1 \
        and all(times_x_power(order // prime, poly) != 1 for prime in ORDER_PRIMES)


def listed_polynomials(entries: Sequence[Dict]) -> Set[int]:
    return {int(e["c"], 16) for e in entries if e["kind"] == "polynomial" and e["degree"] == DEGREE}


def chosen_polynomial(entries: Sequence[Dict]) -> int:
    """c of the first primitive polynomial in the stated order that the list does not hold."""
    listed = listed_polynomials(entries)
    c = 1
    while True:
        if c not in listed and is_primitive(c):
            return c
        c += 2


# -------------------------------------------------------------------------- the stream

class Stream:
    """s(0) to s(63) are SEED's bits, most significant first, and the output starts at s(64)."""

    def __init__(self, c: int):
        self.c = c
        self.register = sum((SEED >> (DEGREE - 1 - i) & 1) << i for i in range(DEGREE))

    def bit(self) -> int:
        fresh = bin(self.register & self.c).count("1") & 1
        self.register = self.register >> 1 | fresh << (DEGREE - 1)
        return fresh

    def word(self, w: int) -> int:
        value = 0
        for _ in range(w):
            value = value << 1 | self.bit()
        return value


def rotl(word: int, k: int, w: int) -> int:
    return symmetry.rotl(word, k, w) if k else word


def is_periodic(word: int, w: int) -> bool:
    return any(rotl(word, k, w) == word for k in range(1, w))


def class_of(word: int, w: int) -> int:
    """One number for a word, its rotations, its complement and their rotations (research R13)."""
    mask = (1 << w) - 1
    return min(min(rotl(word, k, w), rotl(word ^ mask, k, w)) for k in range(w))


def aperiodic_classes(w: int) -> Optional[int]:
    """The classes of aperiodic words at a width small enough to run out of them; beyond it no table
    comes near their number."""
    if w > ENUMERATED_WIDTH:
        return None
    return len({class_of(word, w) for word in range(1 << w) if not is_periodic(word, w)})


def read_table(c: int, rounds: int, columns: int, w: int) -> Dict:
    stream, taken, ever = Stream(c), set(), set()
    total = aperiodic_classes(w)
    table: List[List[int]] = []
    skipped = 0
    repeats: List[Dict] = []
    for r in range(rounds):
        row = []
        for column in range(columns):
            word = stream.word(w)
            while is_periodic(word, w) or class_of(word, w) in taken:
                skipped += 1
                word = stream.word(w)
            kind = class_of(word, w)
            if kind in ever:
                repeats.append({"round": r, "column": column, "class": kind})
            row.append(word)
            taken.add(kind)
            ever.add(kind)
            if len(taken) == total:
                taken = set()
        table.append(row)
    return {"table": table, "skipped": skipped, "repeats": repeats}


# --------------------------------------------------------------------- the refused list

def run_length(w: int) -> int:
    """The fewest table words of at least 64 bits: 16 at w = 4, 8 at 8, 4 at 16 and 2 at 32."""
    return -(-RUN_BITS // w)


def bit_string(entry: Dict) -> str:
    return "".join(format(int(word, 16), f"0{entry['word_bits']}b") for word in entry["words"])


def words_of(bits: str, w: int) -> List[int]:
    return [int(bits[at:at + w], 2) for at in range(0, len(bits) - w + 1, w)]


def refused_matches(words: Sequence[int], w: int, entries: Sequence[Dict]) -> List[Dict]:
    """Each run of consecutive table words of at least 64 bits equal to as many consecutive w-bit
    words of a listed string, read from any multiple of w, under one of the 2w transforms."""
    length = run_length(w)
    mask = (1 << w) - 1
    turned: Dict[Tuple[int, ...], Tuple[int, int, bool]] = {}
    for start in range(len(words) - length + 1):
        run = words[start:start + length]
        for k in range(w):
            rotated = tuple(rotl(word, k, w) for word in run)
            turned.setdefault(rotated, (start, k, False))
            turned.setdefault(tuple(word ^ mask for word in rotated), (start, k, True))
    found = []
    for entry in entries:
        if entry["kind"] != "constant-set":
            continue
        listed = words_of(bit_string(entry), w)
        for at in range(len(listed) - length + 1):
            hit = turned.get(tuple(listed[at:at + length]))
            if hit is not None:
                found.append({"name": entry["name"], "listed_word": at, "table_word": hit[0],
                              "rotation": hit[1], "complement": hit[2]})
    return found


def chance_of_a_match(words: int, entries: Sequence[Dict], w: int) -> str:
    """T·L·2w·2⁻⁶⁴, the bound on an accidental match that every record states."""
    listed = sum(len(bit_string(e)) // w for e in entries if e["kind"] == "constant-set")
    return f"{words * listed * 2 * w} / 2^64"


def guard_refused_list(root: Path) -> Tuple[List[Dict], Dict]:
    """The list's entries and the record's `refused_list`. Exit 2 while its SHA-256 is not the one
    the protocol change log last names, or no entry names one."""
    data = (root / evidence.REFUSED_LIST_REL).read_bytes()
    digest = evidence.sha256(data)
    named = changelog.latest_named()
    if named is None:
        raise Refused("no entry of the protocol change log names the refused list")
    if named != digest:
        raise Refused(f"the refused list's SHA-256 {digest} is not the one the log names, {named}")
    return listed_entries(data), refused_field(digest)


def refused_field(digest: str) -> Dict:
    return {"path": evidence.REFUSED_LIST_REL, "sha256": digest, "sha256_kind": "raw"}


def listed_entries(data: bytes) -> List[Dict]:
    try:
        return changelog.parse_refused_list(data)
    except ValueError as exc:
        raise Refused(f"{evidence.REFUSED_LIST_REL}: {exc}") from None


# ------------------------------------------------------------------------------ one table

def relations_with_repeats(table: Sequence[Sequence[int]], w: int, repeats: Sequence[Dict]) -> Dict:
    """Research R13's relations within one call, a recorded repeat left out: repeats are the rule's
    own case at the widths that run out of classes, listed in the table's file."""
    held = {(item["round"], item["column"]) for item in repeats}
    words = [word for r, row in enumerate(table) for column, word in enumerate(row)
             if (r, column) not in held]
    return symmetry.relations(words, w)


def symmetry_holds(found: Dict) -> bool:
    return not any(found["fixed"].values()) and not any(found["word_rotations"].values()) \
        and not any(found["composed"].values())


def checked(program: "ir.Program", rounds: int, c: int, entries: Sequence[Dict]) -> Tuple[Dict, Dict]:
    """A table with each check of research R15, and its verdicts."""
    columns = ir.last_constant(program) + 1
    if columns < 1:
        raise Refused(f"{program.name} reads no constant")
    w = program.w
    read = read_table(c, rounds, columns, w)
    words = [word for row in read["table"] for word in row]
    related = relations_with_repeats(read["table"], w, read["repeats"])
    fixed = symmetry.check(program, read["table"])
    matches = refused_matches(words, w, entries)
    joined = fixed["joined"]
    checks = {"relations": {name: len(items) for name, items in related.items()},
              "relations_hold": not any(related.values()),
              "symmetry_holds": symmetry_holds(fixed), "symmetry_joined": joined,
              "refused_matches": matches, "chance_of_a_match": chance_of_a_match(len(words), entries, w)}
    return read, checks


def all_held(checks: Dict) -> bool:
    return checks["relations_hold"] and checks["symmetry_holds"] and not checks["refused_matches"]


def table_file(variant: str, program: "ir.Program", rounds: int, c: int, read: Dict) -> bytes:
    w = program.w
    digits = (w + 3) // 4
    return evidence.pretty({
        "variant": variant, "n": program.n, "w": w, "rounds": rounds, "polynomial": f"0x{c:016x}",
        "seed": f"0x{SEED:016x}", "columns": len(read["table"][0]),
        "table": [[f"0x{word:0{digits}x}" for word in row] for row in read["table"]],
        "skipped": read["skipped"], "repeats": read["repeats"]})


def file_row(rel: str, data: bytes) -> Dict:
    return {"path": rel, "sha256": evidence.sha256(data), "sha256_kind": "raw"}


def reference_inputs(n: int, w: int) -> List[Tuple[str, List[int]]]:
    """Research R8's 16 inputs: all-zero, all-one, alternating, a counting pattern and test states
    0 to 11, the fixed patterns being constructed inputs of research R3's classes (1) and (2)."""
    lanes = 2 * n * n
    mask = (1 << w) - 1
    values = devinputs_v3.load("dev", "state", ("dev",), REFERENCE_STATES, n=n, w=w)
    fixed = [("all-zero", [0] * lanes), ("all-one", [mask] * lanes),
             ("alternating", [int("01" * w, 2) & mask] * lanes),
             ("counting", [index & mask for index in range(lanes)])]
    return fixed + [(f"test state {i}", list(values[i])) for i in range(REFERENCE_STATES)]


def reference_file(variant: str, program: "ir.Program", read: Dict) -> bytes:
    """The scalar interpreter's outputs; the batch interpreter must agree on each, or it is a tool
    defect (research R11)."""
    loaded = ir.Loaded(program)
    table = read["table"]
    inputs = reference_inputs(program.n, program.w)
    outputs = [ir.permute(loaded, state, table) for _, state in inputs]
    batch = np.array([state for _, state in inputs], dtype=np.uint64).T
    other = ir.permute_batch(loaded, batch, table).T.tolist()
    if [[int(word) for word in row] for row in other] != outputs:
        raise ToolFailure(f"{variant}: the scalar and batch interpreters disagree")
    digits = (program.w + 3) // 4
    return evidence.pretty({"variant": variant, "rows": [
        {"name": name, "input": [f"{word:0{digits}x}" for word in state],
         "output": [f"{word:0{digits}x}" for word in out]}
        for (name, state), out in zip(inputs, outputs)]})


# ------------------------------------------------------------------------------ candidates

def variant_parts(variant: str) -> Tuple[int, int, int, int]:
    match = VARIANT.fullmatch(variant)
    if match is None:
        raise Refused(f"variant {variant!r}: the part of a variant ID after the design")
    return tuple(int(part) for part in match.groups())  # type: ignore[return-value]


def build_list(root: Path, candidate: str, n: int, w: int, exploration: bool = False) -> "ir.Program":
    builds = ir.candidate_modules(root / candidates.CANDIDATES_REL)
    if candidate not in builds:
        raise Refused(f"{candidates.module_rel(candidate)} does not exist")
    return ir.load(builds[candidate](n, w), exploration=exploration).program


def guard_instance(log: Sequence[Dict], candidate: str, c: int) -> None:
    """The candidate's `parameters` hold the instance of the rule that this run computes."""
    entries_of = candidates.of_event(log, "proposed", candidate)
    if not entries_of:
        raise Refused(f"{candidate} has no proposed entry")
    instance = entries_of[-1]["parameters"].get("constant_instance")
    wanted = {"polynomial": f"0x{c:016x}", "seed": f"0x{SEED:016x}"}
    if not isinstance(instance, dict) or any(instance.get(k) != v for k, v in wanted.items()):
        raise Refused(f"{candidate}'s constant_instance is not the rule's: {wanted}")


def guard_before_freeze() -> None:
    if evidence.pinned_entries():
        raise Refused("the design is frozen: a candidate's table is written before the freeze")


def candidate_table(root: Path, candidate: str, variant: str, entries: Sequence[Dict],
                    log: Sequence[Dict]) -> Dict:
    n, w, rounds, _ = variant_parts(variant)
    c = chosen_polynomial(entries)
    guard_instance(log, candidate, c)
    program = build_list(root, candidate, n, w)
    read, checks = checked(program, rounds, c, entries)
    base = f"{candidates.CANDIDATES_REL}/{candidate}"
    named = f"{candidate}/{variant}"
    return {"files": {f"{base}/constants/{variant}.json": table_file(named, program, rounds, c, read),
                      f"{base}/reference/{variant}.json": reference_file(named, program, read)},
            "checks": checks}


def write_one(result: Dict, argv: Sequence[str], candidate: Optional[str], refused: Dict,
              variant_id: Optional[str], exploration: bool, started: float) -> int:
    """A table and its record; a failed check leaves no table, the record stating why."""
    held = all_held(result["checks"])
    directory = EXPLORATION_REL if exploration else None
    with evidence.Run("generator-run", candidate=candidate, argv=argv, code_files=CODE,
                      variant_id=variant_id, directory=directory) as run:
        if held:
            for rel, data in result["files"].items():
                target = evidence.REPO.path(rel)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
        fields = {"files": files_held(result), "refused_list": refused, "checks": result["checks"],
                  "inputs": inputs_field(result),
                  "exploration": exploration, "generation_seconds": time.monotonic() - started}
        status, code = ("pass", evidence.EXIT_OK) if held else ("fail", evidence.EXIT_VERDICT)
        path = run.finish(status, fields=fields, exit_status=code,
                          classification=NONE if held else "reproducible defect")
    print(f"{evidence.rel_to_repo(path)}: {status}")
    return code


def exploration_table(root: Path, n: int, w: int, entries: Sequence[Dict], log: Sequence[Dict]) -> Dict:
    """An (n, w) outside the supported sizes, for the selected candidate, at the largest R of its
    variant map, since a table's rows are read from the first: a shorter ID reads fewer of them."""
    if (n, w) in ir.PAIRS:
        raise Refused(f"({n}, {w}) is a supported size")
    if n not in ir.EXPLORATION_N or w not in ir.EXPLORATION_W:
        raise Refused(f"({n}, {w}) is outside the research interface")
    selected, table = selected_variants(log)
    rounds = max(R for R, _ in table.values())
    c = chosen_polynomial(entries)
    program = build_list(root, selected, n, w, exploration=True)
    read, checks = checked(program, rounds, c, entries)
    data = table_file(f"{evidence.MODEL_ID}/n{n}-w{w}-R{rounds}", program, rounds, c, read)
    return {"files": {f"{EXPLORATION_REL}/constants_n{n}_w{w}.json": data}, "checks": checks}


# --------------------------------------------------------------------------- the frozen files

def selected_variants(log: Sequence[Dict]) -> Tuple[str, Dict[Tuple[int, int], Tuple[int, str]]]:
    """The candidate of the `selected` entry in force, and per supported (n, w) its largest R with
    the variant's `phyco-v3` ID, from that entry's `variant_map`."""
    chosen = [e for e in candidates.of_event(log, "decision") if e.get("decision") == "selected"]
    if not chosen:
        raise Refused("no selected entry: the frozen tables follow the selection")
    entry = chosen[-1]
    table: Dict[Tuple[int, int], Tuple[int, str]] = {}
    for source, target in entry["variant_map"].items():
        n, w, rounds, _ = variant_parts(source.split("/", 1)[1])
        if (n, w) not in table or table[(n, w)][0] < rounds:
            table[(n, w)] = (rounds, target)
    return entry["candidate_id"], table


def guard_restatement(root: Path, c: int) -> None:
    """The design document restates the rule's values, and the two agree (research R15)."""
    path = root / evidence.DESIGN_REL
    text = path.read_bytes().decode("utf-8").lower() if path.exists() else ""
    for name, value in (("polynomial", c), ("seed", SEED)):
        if f"0x{value:016x}" not in text:
            raise Refused(f"the design document does not restate the rule's {name}, 0x{value:016x}")


def module_text(c: int, tables: Dict[Tuple[int, int], Tuple[int, List[List[int]]]],
                amounts: Dict[Tuple[int, int], Dict]) -> bytes:
    lines = ['"""Generated by scripts/gen_constants_v3.py from the constant rule of research R15. Do '
             'not edit."""', f"POLYNOMIAL = 0x{c:016x}", f"SEED = 0x{SEED:016x}", "TABLES = {"]
    for (n, w), (rounds, table) in sorted(tables.items()):
        lines.append(f"    ({n}, {w}): ({rounds}, (")
        digits = (w + 3) // 4
        for row in table:
            lines.append("        (" + ", ".join(f"0x{word:0{digits}x}" for word in row) + ",),")
        lines.append("    )),")
    lines += ["}", "AMOUNTS = {"]
    for pair, at in sorted(amounts.items()):
        lines.append(f"    {pair}: {{")
        lines += [f"        {node}: {tuple(items)!r}," for node, items in sorted(at.items())]
        lines.append("    },")
    lines.append("}")
    return ("\n".join(lines) + "\n").encode("utf-8")


def frozen_files(root: Path, entries: Sequence[Dict], log: Sequence[Dict]) -> Dict[str, bytes]:
    """Every generated file, in memory: the module, and one JSON table per supported (n, w)."""
    selected, wanted = selected_variants(log)
    missing = [pair for pair in ir.PAIRS if pair not in wanted]
    if missing:
        raise Refused(f"the variant map holds no variant at {missing}")
    c = chosen_polynomial(entries)
    guard_restatement(root, c)
    files: Dict[str, bytes] = {}
    tables, amounts = {}, {}
    for (n, w), (rounds, target) in sorted(wanted.items()):
        program = build_list(root, selected, n, w)
        read, checks = checked(program, rounds, c, entries)
        if not all_held(checks):
            raise Refused(f"({n}, {w}): a check of research R15 fails: {checks}")
        tables[(n, w)] = (rounds, read["table"])
        amounts[(n, w)] = symmetry.amounts_at(program)
        files[f"{VECTORS_REL}/constants_n{n}_w{w}.json"] = table_file(target, program, rounds, c, read)
    files[MODULE_REL] = module_text(c, tables, amounts)
    return files


def append_sidecar(record_id: str, argv: Sequence[str], seconds: float) -> None:
    path = evidence.REPO.path(SIDECAR_REL)
    held = json.loads(path.read_bytes().decode("utf-8")) if path.exists() else {"entries": []}
    held["entries"].append({"record_id": record_id, "command": list(argv), "interpreter": sys.version.split()[0],
                            "platform": platform_module.platform(), "generation_seconds": seconds})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(evidence.pretty(held))


def write_frozen(root: Path, entries: Sequence[Dict], log: Sequence[Dict], refused: Dict,
                 argv: Sequence[str], started: float) -> int:
    files = frozen_files(root, entries, log)
    with evidence.Run("generator-run", argv=argv, code_files=CODE, model_id=evidence.MODEL_ID) as run:
        for rel, data in files.items():
            target = evidence.REPO.path(rel)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        path = run.finish("pass", fields={"files": [file_row(rel, data) for rel, data in sorted(files.items())],
                                          "refused_list": refused, "inputs": NONE, "exploration": False})
    record = json.loads(path.read_bytes().decode("utf-8"))
    append_sidecar(record["record_id"], argv, time.monotonic() - started)
    print(f"{evidence.rel_to_repo(path)}: pass")
    return evidence.EXIT_OK


def check_frozen(root: Path, entries: Sequence[Dict], log: Sequence[Dict], refused: Dict,
                 argv: Sequence[str]) -> int:
    files = frozen_files(root, entries, log)
    differs = [rel for rel, data in files.items()
               if not (root / rel).exists() or (root / rel).read_bytes() != data]
    verdict = "differs" if differs else "match"
    code = evidence.EXIT_VERDICT if differs else evidence.EXIT_OK
    with evidence.Run("generator-check", argv=argv, code_files=CODE, model_id=evidence.MODEL_ID) as run:
        path = run.finish("fail" if differs else "pass", exit_status=code, fields={
            "files": [file_row(rel, data) for rel, data in sorted(files.items())],
            "refused_list": refused, "verdict": verdict, "differs": sorted(differs), "inputs": NONE})
    print(f"{evidence.rel_to_repo(path)}: {verdict}")
    return code


# ----------------------------------------------------------------------------- --reproduce

def reproduce(args: argparse.Namespace, command: List[str]) -> int:
    """The run again at the record's commit, in memory: the list is the one at that commit, compared
    with the record's `refused_list`, and every file is compared with the hash the record holds."""
    path = Path(args.reproduce)
    path = path if path.is_absolute() else evidence.REPO.path(args.reproduce)
    if not path.exists():
        raise Refused(f"{args.reproduce} does not exist")
    original = json.loads(path.read_bytes().decode("utf-8"))
    if original.get("kind") not in ("generator-run", "generator-check"):
        raise Refused(f"{args.reproduce} is no generator-run or generator-check record")
    argv = shlex.split(original["command"])[1:]

    def run(place: evidence.Place) -> Dict:
        root = place.worktree
        data = (root / evidence.REFUSED_LIST_REL).read_bytes()
        digest = evidence.sha256(data)
        if digest != original["refused_list"]["sha256"]:
            raise Refused(f"the list at the record's commit is not the one it names: {digest}")
        entries, log = listed_entries(data), log_at(root)
        fields: Dict[str, Any] = {"refused_list": refused_field(digest)}
        if "--candidate" in argv:
            result = candidate_table(root, value_of(argv, "--candidate"), value_of(argv, "--variant"),
                                     entries, log)
            fields.update(checks=result["checks"], files=files_held(result), inputs=inputs_field(result))
        elif "--exploration" in argv:
            at = argv.index("--exploration")
            result = exploration_table(root, int(argv[at + 1]), int(argv[at + 2]), entries, log)
            fields.update(checks=result["checks"], files=files_held(result), inputs=NONE)
        else:
            files = frozen_files(root, entries, log)
            fields.update(files=[file_row(rel, blob) for rel, blob in sorted(files.items())], inputs=NONE)
            if original["kind"] == "generator-check":
                fields["verdict"] = original.get("verdict")
        return dict(fields, kind=original["kind"], model_id=original.get("model_id"),
                    variant_id=original.get("variant_id"), exit_status=original["exit_status"],
                    assertions=[], status=original["status"], classification=original["classification"],
                    code_sha256=original["code_sha256"], outputs=[])

    extra = RUN_FIELDS if original["kind"] == "generator-run" else CHECK_FIELDS
    if "checks" not in original:
        extra = tuple(name for name in extra if name != "checks")
    return evidence.reproduce(evidence.Reproduction(record_path=path, run=run, extra=extra, code_files=CODE,
                                                    argv=command))


def files_held(result: Dict) -> List[Dict]:
    if not all_held(result["checks"]):
        return []
    return [file_row(rel, data) for rel, data in result["files"].items()]


def inputs_field(result: Dict) -> Any:
    """The test states a reference file read, by namespace, kind and range (spec FR-061)."""
    if not any("/reference/" in rel for rel in result["files"]):
        return NONE
    return {"namespace": "dev", "kind": "state", "indices": [0, REFERENCE_STATES - 1],
            "constructed": ["all-zero", "all-one", "alternating", "counting"]}


def value_of(argv: Sequence[str], name: str) -> str:
    return argv[list(argv).index(name) + 1]


def log_at(root: Path) -> List[Dict]:
    path = root / candidates.LOG
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_bytes().decode("utf-8").splitlines()]


# -------------------------------------------------------------------------------------- main

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--candidate")
    parser.add_argument("--variant")
    parser.add_argument("--exploration", nargs=2, type=int, metavar=("N", "W"))
    parser.add_argument("--reproduce")
    args = parser.parse_args(argv)
    command = [SCRIPT] + list(sys.argv[1:] if argv is None else argv)

    def body() -> int:
        started = time.monotonic()
        if args.reproduce:
            return reproduce(args, command)
        root = evidence.REPO.root
        entries, refused = guard_refused_list(root)
        log = candidates.entries()
        if args.candidate or args.variant:
            if not args.candidate or not args.variant:
                raise Refused("--candidate and --variant go together")
            guard_before_freeze()
            result = candidate_table(root, args.candidate, args.variant, entries, log)
            return write_one(result, command, args.candidate, refused,
                             f"{args.candidate}/{args.variant}", False, started)
        if args.exploration:
            result = exploration_table(root, *args.exploration, entries, log)
            return write_one(result, command, None, refused, None, True, started)
        if args.check:
            return check_frozen(root, entries, log, refused, command)
        return write_frozen(root, entries, log, refused, command, started)

    return evidence.main_guard(body)


if __name__ == "__main__":
    raise SystemExit(main())
