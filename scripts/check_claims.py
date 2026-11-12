"""Features 004 and 005: the claim test, FR-069 as written (contracts/cli.md; data-model section
15), and feature 005's FR-026: one run reads both features, each with its own documents, reports,
rows, disclaimer and model, `phyco-v3` and `phyco-v4`.

    check_claims.py

It checks README, security.md's sections 1.1 and 15 and the three disclaimer blocks against
protocol/claims.json, the register against the Review & Approval rows and the files at HEAD, that
every hand-written document of this feature carries the design-form disclaimer, and the wording of
every scanned line. A line its rules flag passes only through an allow-list entry, and no entry
passes a finding inside a block or a finding of the register's checks. Each run prints the entries
added since the last gate's approval commit. Exit 0 with no finding, 1 on a finding. It writes no
record and runs as a test, so it has no --reproduce mode.

In its rules "near" and "beside" mean the same sentence or table row, and a word is a run of letters
and digits. This script makes no security claim.
"""
from __future__ import annotations

import ast
import bisect
import io
import json
import re
import subprocess
import sys
import tokenize
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Sequence, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from protocol import evidence  # noqa: E402
from protocol.disclaimer import DESIGN_DISCLAIMER  # noqa: E402,F401

REGISTER_REL = "protocol/claims.json"
# Each feature's own model: the one model its rows can raise above L0.
FEATURE_MODELS = {name: f["model_id"] for name, f in evidence.FEATURES.items()}
FUT_SEC_FEATURE = "004"
FIXED_SENTENCE = "PhycoWeb-PRNG, every model included, must not be used to generate secrets."
FEATURE_BASE = "801c6d7^"
CODE_PATHS = ("phycoweb/", "protocol/", "scripts/", "research/004/", "research/005/", "tests/",
              "fast/seed_search.c")
MODEL_IDS = ("float-v0", "lut-v1", "phyco-v2", "phyco-v3", "phyco-v4")
FUT_SEC_KEYS = tuple(f"FUT-SEC-{k}" for k in range(1, 10))
LEVELS = ("L0", "L1", "L2", "L3", "L4", "L5", "L6")
GATE_ROWS = ("Spec approval", "Plan approval", "Tasks approval", "FUT-SEC-8 result review",
             "Security-target review", "Owner design review", "Design freeze",
             "Final result review")
QUOTING_FILES = ("checklists/", "checklist-choices.md")
MAPPING_HEADING = "Slime-mould mapping"
MAPPING_SENTENCE = "The slime-mould mapping contributes no security property."
# Copies that a record cites read as the document they copy, so one entry passes the line in both.
VERSION_DIRS = {"spec-versions": "spec.md", "research-versions": "research.md",
                "design-versions": "design.md"}


@contextmanager
def feature(name: str) -> Iterator[None]:
    """The checks inside read the named feature's paths, rows, model and disclaimer."""
    previous = evidence.set_feature(name)
    try:
        yield
    finally:
        evidence.set_feature(previous)


def features_present() -> List[str]:
    """The features whose spec exists in the working tree, in their order."""
    return [name for name, f in sorted(evidence.FEATURES.items())
            if evidence.REPO.path(f["spec"] + "/spec.md").exists()]


def words(*forms: str) -> "re.Pattern[str]":
    """Whole words, ignoring case, a word being a run of letters and digits."""
    return re.compile(r"(?<![^\W_])(?:" + "|".join(forms) + r")(?![^\W_])", re.I)


RANDOM = words("random", "randomly", "randomness", "randomi[sz]e", "randomi[sz]es", "randomi[sz]ed",
               "randomi[sz]ing", "randomi[sz]ation")
HIGH_ENTROPY = words("high-entropy")
SECURE = words("secure", "securely")
UNBREAKABLE = words("unbreakable")
CONSTANT_TIME = words("constant[ -]time")
KEY_ANALYSIS = words("related-key analysis", "weak-key analysis")
PREDICTION = words("prediction[ -]resist(?:ance|ant)")
LEVEL_NAME = re.compile(r"(?<![^\W_])L([1-6])(?![^\W_])")
LINE_RULES = (("random", RANDOM), ("high-entropy", HIGH_ENTROPY), ("secure", SECURE),
              ("unbreakable", UNBREAKABLE), ("constant time", CONSTANT_TIME),
              ("related-key or weak-key analysis", KEY_ANALYSIS),
              ("prediction resistance", PREDICTION))
PROVE = words("prove", "proves", "proved", "proving", "proven", "provably")
PROVE_OBJECT = words("bound", "bounds", "theorem", "theorems", "trail", "trails")
PROVE_RECORD = words("record", "records", "cited", "cites", "cite")
STANDARD_WORD = words("comply", "complies", "complied", "complying", "compliant", "compliance",
                      "conform", "conforms", "conformed", "conforming", "conformance",
                      "conformant", "approve", "approves", "approved", "approving", "approval")
STANDARD_NAME = re.compile(r"\bSP\s*800\b|\bFIPS\b|\bAIS\b|\bISO\b|\bNIST\b|\bBSI\b|\bRFC\s*\d")
DRBG = words("DRBG", "DRBGs")
MODEL_WORD = re.compile(r"(?<![^\W_])(?:phyco-v\d|float-v0|lut-v1|cand-[AB]\d|v4-[AB]\d)"
                        r"(?![^\W_])|"
                        r"\bthe (?:model|generator|design)\b", re.I)
FIPS_140 = re.compile(r"\bFIPS\s*140\b")
SELF_TEST = words("self-test", "self-tests")
REVIEW_WORD = words("evaluation", "evaluated", "certified")
REVIEW_NAME = words("external review", "design review")
STRENGTH_WORD = words("security", "strength", "secure")
COST_WORD = words("security")
BITS = re.compile(r"(?<![\d.,])\d[\d,]*(?:\s+|-)bits?\b")
POWER_OF_2 = re.compile(r"(?<![\d.])2(?:[⁰¹²³⁴⁵⁶⁷⁸⁹]+|\^\{?\d+)")
TARGET = words("target", "targets")
RULE_CITED = re.compile(r"\bFR-\d{3}\b|\bSC-\d{3}\b|\bFUT-SEC-\d\b|\bPrinciple [IVX]+\b|"
                        r"\bR\d{1,2}\b")
RESULT_WORD = words("frequency", "avalanche", "battery", "batteries")
MIX_WORD = words("mix", "mixes", "mixed", "mixing")
EVIDENCE_OF = re.compile(r"\bevidence (?:of|for) (?:\w+ )?security\b", re.I)
MAPPING_WORDS = words(
    "security", "secure", "securely", "insecure", "strength", "strengths", "strong", "resist",
    "resists", "resisted", "resisting", "resistance", "resistant", "unpredictable",
    "unpredictability", "chaos", "chaotic", "Lyapunov", "ergodic", "ergodicity", "emergent",
    "emergence", "complexity", "biological", "mix", "mixes", "mixed", "mixing", "diffusion",
    "diffuse", "diffuses", "avalanche", "battery", "batteries")
CLAIM_WORD = words("secure", "securely", "security levels?", "cryptographic security", "strengths?",
                   "resist", "resists", "resisted", "resisting", "resistance", "resistant", "claim",
                   "claims", "claimed", "claiming")
NEGATED = ("no claim", "do not show cryptographic security", "does not show cryptographic security")
README_READ = re.compile(r"security levels?|strength|claim|(?<![^\W_])L[0-6](?![^\W_])", re.I)
MODEL_ID = re.compile(r"(?<![^\W_])(float-v0|lut-v1|phyco-v2|phyco-v3|phyco-v4)(/[\w-]+)?"
                      r"(?![^\W_])")
BOUND_VALUE = re.compile(r"(?<![\d.,])(\d[\d,]*)(?:\s+|-)bits?\b")
SUPERSCRIPT = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")
AT_MOST = re.compile(r"^at most (\d+) bits$")
SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z(`\"*\[⛔])")
UNIT_START = ("- ", "* ", "#", "|", ">", "1. ", "2. ", "3. ", "4. ", "5. ", "6. ", "7. ", "8. ",
              "9. ", "• ")
QUOTED = re.compile(r"\"[^\"]*\"|“[^”]*”|`[^`]*`")


@dataclass
class Finding:
    path: str
    line: int
    rule: str
    text: str


@dataclass
class Sentence:
    """A sentence or a table row, with the place in `lines` of each of its stretches."""
    text: str
    starts: List[int]
    numbers: List[int]

    def line_of(self, position: int) -> int:
        return self.numbers[bisect.bisect_right(self.starts, position) - 1]


def read_text(rel: str) -> str:
    return evidence.REPO.path(rel).read_bytes().decode("utf-8")


def read_lines(rel: str) -> List[str]:
    return read_text(rel).replace("\r\n", "\n").split("\n")


# --------------------------------------------------------------------------- sentences and rows

def sentences_of(lines: Sequence[str]) -> List[Sentence]:
    """Each table row whole, and each paragraph or list item split into its sentences."""
    out: List[Sentence] = []
    current: List[Tuple[int, str]] = []

    def flush() -> None:
        if not current:
            return
        starts: List[int] = []
        numbers: List[int] = []
        text = ""
        for number, line in current:
            starts.append(len(text))
            numbers.append(number)
            text += line + " "
        begin = 0
        for match in list(SENTENCE_END.finditer(text)) + [None]:
            end = match.start() if match else len(text)
            piece_starts = [max(s - begin, 0) for s in starts if s < end]
            piece_numbers = numbers[:len(piece_starts)]
            keep = [i for i, s in enumerate(starts[:len(piece_starts)]) if s >= begin]
            first = max(0, keep[0] - 1) if keep and starts[keep[0]] > begin else (
                keep[0] if keep else len(piece_starts) - 1)
            out.append(Sentence(text[begin:end], piece_starts[first:], piece_numbers[first:]))
            begin = match.end() if match else end
        current.clear()

    for number, raw in enumerate(lines):
        line = raw.strip()
        if not line:
            flush()
        elif line.startswith("|"):
            flush()
            out.append(Sentence(line, [0], [number]))
        else:
            if line.startswith(UNIT_START):
                flush()
            current.append((number, line))
    flush()
    return out


def sentence_rules(sentence: Sentence) -> Iterable[Tuple[int, str]]:
    """Each rule of FR-069 that reads a sentence or a row, with the line of its match."""
    text = sentence.text
    exempt = TARGET.search(text) or RULE_CITED.search(text)
    if not exempt:
        if STRENGTH_WORD.search(text):
            for match in BITS.finditer(text):
                yield sentence.line_of(match.start()), "a strength not labelled as a target"
        if COST_WORD.search(text):
            for match in POWER_OF_2.finditer(text):
                yield sentence.line_of(match.start()), "a strength not labelled as a target"
    for match in PROVE.finditer(text):
        if not (PROVE_OBJECT.search(text) and PROVE_RECORD.search(text)):
            yield sentence.line_of(match.start()), "a form of prove without its object and record"
    if RESULT_WORD.search(text):
        for pattern in (MIX_WORD, EVIDENCE_OF):
            for match in pattern.finditer(text):
                yield sentence.line_of(match.start()), "results offered as evidence"
    if STANDARD_NAME.search(text):
        for match in STANDARD_WORD.finditer(text):
            yield sentence.line_of(match.start()), "a conformity word near a standard's name"
    if MODEL_WORD.search(text):
        for match in DRBG.finditer(text):
            yield sentence.line_of(match.start()), "DRBG beside a model"
    if SELF_TEST.search(text):
        for match in FIPS_140.finditer(text):
            yield sentence.line_of(match.start()), "FIPS 140 beside self-test"
    if REVIEW_NAME.search(text):
        for match in REVIEW_WORD.finditer(text):
            yield sentence.line_of(match.start()), "evaluation beside a review"


def line_level(line: str, register: Dict) -> int:
    """The lowest level the register gives the models a line names by ID, L0 where it names none."""
    named = {match.group(1) for match in MODEL_ID.finditer(line)}
    levels = [LEVELS.index(register["models"][m]["claim_level"]) for m in named
              if m in register["models"] and register["models"][m]["claim_level"] in LEVELS]
    return min(levels) if levels else 0


def line_rules(masked: str, original: str, register: Dict) -> Iterable[str]:
    for name, pattern in LINE_RULES:
        if pattern.search(masked):
            yield name
    allowed = line_level(original, register)
    for match in LEVEL_NAME.finditer(masked):
        if int(match.group(1)) > allowed:
            yield f"a level above claim_level: L{match.group(1)}"


def blank(text: str) -> str:
    return " " * len(text)


def mask_phrases(line: str, phrases: Sequence[str]) -> str:
    """A standing phrase passes only where it stands: the line's other words are still read."""
    for phrase in phrases:
        if phrase in line:
            line = line.replace(phrase, blank(phrase))
    return line


def mask_quotes(line: str) -> str:
    return QUOTED.sub(lambda match: blank(match.group(0)), line)


def allow_path(rel: str) -> str:
    parts = rel.split("/")
    owner = next((f for f in evidence.FEATURES.values() if rel.startswith(f["rep"] + "/")),
                 evidence.FEATURES[evidence.FEATURE])
    for directory, document in VERSION_DIRS.items():
        if directory in parts:
            return owner["spec"] + "/" + document
    return rel


def scan_lines(rel: str, numbers: Sequence[int], lines: Sequence[str],
               register: Dict) -> List[Finding]:
    """The wording rules over the given lines, each with its number in the file."""
    phrases = [entry["phrase"] for entry in register["allow_list"]["phrases"]]
    path = allow_path(rel)
    entries = {entry["text"] for entry in register["allow_list"]["lines"]
               if entry["path"] == path}
    quoting = any(part in rel for part in QUOTING_FILES)
    masked = []
    for line in lines:
        text = mask_phrases(line, phrases)
        masked.append(mask_quotes(text) if quoting else text)
    found: Set[Tuple[int, str]] = set()
    for index, (line, text) in enumerate(zip(lines, masked)):
        found.update((index, rule) for rule in line_rules(text, line, register))
    for sentence in sentences_of(masked):
        found.update(sentence_rules(sentence))
    return [Finding(rel, numbers[index] + 1, rule, lines[index])
            for index, rule in sorted(found) if lines[index] not in entries]


# ------------------------------------------------------------------------------- the disclaimers

def block_quotes(lines: Sequence[str]) -> List[List[int]]:
    """Each run of lines that start with ">", by their indices."""
    blocks: List[List[int]] = []
    current: List[int] = []
    for number, line in enumerate(lines):
        if line.startswith(">"):
            current.append(number)
        elif current:
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)
    return blocks


def disclaimer_blocks(rel: str, lines: Sequence[str]) -> List[List[int]]:
    """README's status block and security.md's opening block are the first block quote of each file,
    and security.md's closing block its last."""
    blocks = block_quotes(lines)
    if rel == "README.md":
        return blocks[:1]
    return [blocks[0], blocks[-1]] if len(blocks) > 1 else blocks


def strip_quote(line: str) -> str:
    return line[1:].strip()


def bounds_stated(line: str) -> List[int]:
    """Every number of bits a line states: "<d> bits", "<d>-bit" or a power of 2."""
    values = [int(match.group(1).replace(",", "")) for match in BOUND_VALUE.finditer(line)]
    for match in POWER_OF_2.finditer(line):
        digits = re.sub(r"\D", "", match.group(0)[1:].translate(SUPERSCRIPT))
        values.append(int(digits))
    return values


def register_bound(entry: Dict, variant: Optional[str]) -> Optional[int]:
    """The entry's bound in bits; None where it holds `none`. `phyco-v3`'s is the least of its
    sizes' bounds unless the line names a size by its variant ID."""
    bound = entry["bound"]
    if isinstance(bound, dict):
        sizes = bound.get("sizes", bound)
        if variant is not None and variant in sizes:
            bound = sizes[variant]
        else:
            values = [register_bound({"bound": value}, None) for value in sizes.values()]
            values = [value for value in values if value is not None]
            return min(values) if values else None
    match = AT_MOST.match(str(bound))
    return int(match.group(1)) if match else None


def bound_and_claim_findings(rel: str, number: int, line: str, register: Dict) -> List[Finding]:
    """A bound or a claim stated in a line, against the entries of the models it names by ID."""
    out: List[Finding] = []
    named = [(match.group(1), (match.group(1) + (match.group(2) or "")))
             for match in MODEL_ID.finditer(line)]
    text = line
    for phrase in NEGATED:
        text = words(re.escape(phrase)).sub(blank(phrase), text)

    def add(rule: str) -> None:
        out.append(Finding(rel, number + 1, rule, line))

    values = bounds_stated(text)
    if values and not named:
        add("a bound that names no model")
    for model, full in named:
        entry = register["models"].get(model)
        if entry is None:
            continue
        limit = register_bound(entry, full if "/" in full else None)
        for value in values:
            if limit is None or limit < value:
                add(f"a bound beyond the register's for {model}")
    if CLAIM_WORD.search(text):
        if not named:
            add("a claim that names no model")
        for model, _ in named:
            entry = register["models"].get(model)
            if entry is not None and entry["claim"] == "no claim":
                add(f"a claim beside no claim for {model}")
    return out


def check_blocks(register: Dict) -> Tuple[List[Finding], Dict[str, Set[int]]]:
    """Each disclaimer: found by its place, it holds the fixed sentence word for word, and no entry
    passes a finding inside it."""
    findings: List[Finding] = []
    block_lines: Dict[str, Set[int]] = {}
    bare = dict(register, allow_list={"phrases": [], "lines": []})
    for rel, wanted in (("README.md", 1), ("security.md", 2)):
        lines = read_lines(rel)
        blocks = disclaimer_blocks(rel, lines)
        block_lines[rel] = {number for block in blocks for number in block}
        if len(blocks) < wanted:
            findings.append(Finding(rel, 1, "a disclaimer block is missing", ""))
        for block in blocks:
            text = " ".join(strip_quote(lines[number]) for number in block)
            if FIXED_SENTENCE not in text:
                findings.append(Finding(rel, block[0] + 1, "the block lacks the fixed sentence",
                                        lines[block[0]]))
            for number in block:
                line = strip_quote(lines[number])
                findings.extend(bound_and_claim_findings(rel, number, line, register))
            findings.extend(scan_lines(rel, block, [strip_quote(lines[n]) for n in block], bare))
    return findings, block_lines


# --------------------------------------------------------------------------- the register's checks

def named_hashes(notes: str) -> List[Tuple[str, Optional[str], str]]:
    """Each (path, chapter, SHA-256) a review row names: a path in backticks, with a chapter in
    quotation marks where it names one, followed by its 64 hex digits."""
    return [(m.group(1), m.group(2), m.group(3)) for m in re.finditer(
        r"`([\w./-]+)`(?:, chapter \"([^\"]+)\")?[^`]*?\b([0-9a-f]{64})\b", notes)]


def hash_holds(path: str, chapter: Optional[str], digest: str) -> bool:
    return evidence.citation_holds(path, digest, chapter or evidence.NONE)


def fut_sec_rows(rows: Sequence[evidence.Row]) -> List[evidence.Row]:
    """The table that holds the row "FUT-SEC-8 result review": feature 004's spec at HEAD, for
    feature 004 its own rows and for a later feature read from there (feature 005, FR-013)."""
    if evidence.FEATURE == FUT_SEC_FEATURE:
        return list(rows)
    return evidence.head_table(evidence.FEATURES[FUT_SEC_FEATURE]["spec"] + "/spec.md")


def review_rows(rows: Sequence[evidence.Row]) -> List[Optional[evidence.Row]]:
    """The highest-k row of each review family that the first level rests on."""
    return [evidence.family_row("FUT-SEC-8 result review", fut_sec_rows(rows)),
            evidence.family_row("Security-target review", list(rows))]


def expected_level(rows: Sequence[evidence.Row]) -> str:
    """The first level while the "L1 recorded" row with the highest k reads Approved and names the
    highest-k row of each review family, both Approved, and every hash those rows name matches the
    file at HEAD, and the lowest otherwise."""
    recorded = evidence.family_row("L1 recorded", list(rows))
    reviews = review_rows(rows)
    if recorded is None or recorded.decision != "Approved" or None in reviews:
        return "L0"
    for review in reviews:
        if review.decision != "Approved" or review.name not in recorded.notes:
            return "L0"
        if not all(hash_holds(*item) for item in named_hashes(review.notes)):
            return "L0"
    return "L1"


def counted_bounds() -> List[Dict]:
    """The counted trail-bound records of the feature in force at HEAD: searched, `pass`, each
    citing its validation; a `split` record is never counted (feature 005, data-model section 2)."""
    return [record for path, record in evidence.iter_records("bound")
            if record.get("status") == "pass" and record.get("validation")
            and record.get("method") != "split"
            and evidence.show(evidence.rel_to_repo(path)) is not None]


def check_in_progress(entry: Dict) -> Iterable[str]:
    records = counted_bounds()
    state = entry["in_progress"]
    if not records:
        if state != evidence.NONE:
            yield "in_progress names a level while no counted trail-bound record exists"
        return
    first = min(record["created_utc"] for record in records)[:10]
    if not isinstance(state, dict) or state.get("level") != "L2" \
            or state.get("status") != "not reached" or state.get("start") != first:
        yield f"in_progress does not name L2, not reached, from {first}"


def check_history(entry: Dict, rows: Sequence[evidence.Row], level: str) -> Iterable[str]:
    """`history` holds every level that a later row or a change to the reviewed set ended."""
    recorded = [r for r in rows if re.fullmatch(r"L1 recorded( \d+)?", r.name)
                and r.decision == "Approved"]
    current = evidence.family_row("L1 recorded", list(rows))
    held = {name for item in entry["history"] for name in item.get("rows", ())}
    for row in recorded:
        ended = level != "L1" or (current is not None and row.name != current.name)
        if ended and row.name not in held:
            yield f"history lacks the L1 of {row.name}"


def profile_paths() -> Tuple[str, str]:
    base = f"{evidence.REP_REL}/security-target"
    return f"{base}/parameters.json", f"{base}/limits.json"


def check_bound(entry: Dict) -> Iterable[str]:
    parameters, _ = profile_paths()
    blob = evidence.show(parameters)
    if blob is None:
        if entry["bound"] != evidence.NONE:
            yield "bound must read none until the size profile exists"
        return
    bound = entry["bound"]
    sizes = bound.get("sizes") if isinstance(bound, dict) else None
    if sizes is None:
        yield "bound holds no size of the profile"
        return
    if bound.get("sha256") != evidence.sha256(blob):
        yield "bound names another SHA-256 of the size profile"
    profile = json.loads(blob.decode("utf-8"))
    for row in profile.get("rows", ()):
        wanted = f"at most {row.get('bound_bits')} bits"
        if row.get("claimable") and sizes.get(row["variant_id"]) != wanted:
            yield f"bound differs from the profile's bound_bits at {row['variant_id']}"


def check_evidence(entry: Dict, level: str, rows: Sequence[evidence.Row]) -> Iterable[str]:
    wanted: Set[str] = set()
    for rel in profile_paths():
        if evidence.show(rel) is not None:
            wanted.add(rel)
    if level == "L1":
        latest = evidence.latest_demonstration()
        if latest is not None:
            wanted.add(evidence.rel_to_repo(latest[0]))
        for row in review_rows(rows):
            wanted.update(path for path, _, _ in named_hashes(row.notes if row else ""))
    held = {item["path"]: item for item in entry["evidence"]}
    for rel in sorted(wanted - set(held)):
        yield f"evidence lacks {rel}"
    for rel, item in held.items():
        if not evidence.citation_holds(rel, item["sha256"]):
            yield f"evidence names another SHA-256 of {rel}"


def check_fut_sec(entry: Dict) -> Iterable[str]:
    """`phyco-v4`'s expected statuses of FUT-SEC-1 to FUT-SEC-9 (feature 005, FR-030): FUT-SEC-8 met
    by feature 004's demonstration, FUT-SEC-7 open for feature 008, the analysis feature 006."""
    held = entry.get("fut_sec")
    if not isinstance(held, dict) or tuple(sorted(held)) != FUT_SEC_KEYS:
        yield "fut_sec does not hold FUT-SEC-1 to FUT-SEC-9"
        return
    for key in FUT_SEC_KEYS:
        if not str(held[key]).startswith("expected: "):
            yield f"fut_sec: {key} is not an expected status"
    if "feature 004's demonstration" not in held["FUT-SEC-8"]:
        yield "fut_sec: FUT-SEC-8 does not name feature 004's demonstration"
    if "open for feature 008" not in held["FUT-SEC-7"]:
        yield "fut_sec: FUT-SEC-7 is not open for feature 008"
    if "feature 006" not in held["FUT-SEC-5"]:
        yield "fut_sec: FUT-SEC-5 does not name the analysis feature 006"
    for key in FUT_SEC_KEYS:
        if key != "FUT-SEC-8" and re.search("feature 00[579]", str(held[key])):
            yield f"fut_sec: {key} names a stage by another number than security.md section 22's"


def check_register(register: Dict) -> List[Finding]:
    out: List[Finding] = []

    def add(text: str) -> None:
        out.append(Finding(REGISTER_REL, 1, "the register's checks", text))

    models = register["models"]
    for model in MODEL_IDS:
        if model not in models:
            add(f"no entry for {model}")
    for model, entry in models.items():
        if entry["claim_level"] not in LEVELS:
            add(f"{model}: claim_level {entry['claim_level']} is outside L0 to L6")
        elif model not in FEATURE_MODELS.values() and entry["claim_level"] != "L0":
            add(f"{model}: every other model stays at L0 in this feature")
    present = features_present()
    for name, model in sorted(FEATURE_MODELS.items()):
        entry = models.get(model)
        if entry is None:
            continue
        # Feature 004's findings read as they always did; a later feature's name its model.
        lead = "" if name == FUT_SEC_FEATURE else f"{model}: "
        if name not in present:
            if entry["claim_level"] != "L0":
                add(f"{model} reads {entry['claim_level']}, and its feature has no spec")
            continue
        with feature(name):
            rows = evidence.head_table()
            level = expected_level(rows)
            if entry["claim_level"] != level:
                add(f"{model} reads {entry['claim_level']}, and the rows give {level}")
            checks = [check_in_progress(entry), check_history(entry, rows, level),
                      check_bound(entry), check_evidence(entry, level, rows)]
            if name != FUT_SEC_FEATURE:
                checks.append(check_fut_sec(entry))
            for check in checks:
                for text in list(check):
                    add(lead + text)
    return out


# --------------------------------------------------------------------- README and security.md

def check_section_1_1(register: Dict, lines: Sequence[str]) -> List[Finding]:
    """Row by row, the model ID and the leading level and claim of the cell (SEC-095)."""
    out: List[Finding] = []
    rel = "security.md"
    start = next((i for i, line in enumerate(lines) if line.startswith("### 1.1")), None)
    if start is None:
        return [Finding(rel, 1, "section 1.1 is missing", "")]
    first = next(i for i in range(start, len(lines)) if lines[i].startswith("|"))
    header = [c.strip() for c in lines[first].strip().strip("|").split("|")]
    column = header.index("Claim level (section 15)")
    seen = set()
    for i in range(first + 2, len(lines)):
        if not lines[i].startswith("|"):
            break
        cells = [c.strip() for c in lines[i].strip().strip("|").split(" | ")]
        model = cells[0].strip("`")
        seen.add(model)
        if model not in register["models"]:
            out.append(Finding(rel, i + 1, "a section 1.1 row with no register entry", lines[i]))
            continue
        entry = register["models"][model]
        wanted = f"{entry['claim_level']}; {entry['claim']}"
        if not cells[column].startswith(wanted):
            out.append(Finding(rel, i + 1, f"the row's cell differs from {wanted}", lines[i]))
    for model in register["models"]:
        if model not in seen:
            out.append(Finding(rel, start + 1, f"no section 1.1 row for {model}", ""))
    return out


def check_section_15(register: Dict, lines: Sequence[str]) -> List[Finding]:
    out: List[Finding] = []
    text = "\n".join(lines)
    for model, entry in register["models"].items():
        wanted = f"- `{model}`: {entry['claim_level']}; {entry['claim']}."
        if wanted not in text:
            out.append(Finding("security.md", 1, f"section 15 does not state {wanted}", ""))
    return out


def check_readme(register: Dict, lines: Sequence[str], block: Set[int]) -> List[Finding]:
    out: List[Finding] = []
    for number, line in enumerate(lines):
        if number not in block and README_READ.search(line):
            out.extend(bound_and_claim_findings("README.md", number, line, register))
    return out


# ------------------------------------------------------------------------------------ the documents

def markdown_files() -> List[str]:
    out = []
    for base in (evidence.FEATURE_REL, evidence.REP_REL):
        root = evidence.REPO.path(base)
        if root.exists():
            out.extend(evidence.rel_to_repo(p) for p in sorted(root.rglob("*.md")))
    return out


def check_design_disclaimer(rel: str, lines: Sequence[str]) -> List[Finding]:
    """Every hand-written document carries its feature's design-form disclaimer under its title."""
    blocks = block_quotes(lines)
    if blocks:
        text = " ".join(strip_quote(lines[number]) for number in blocks[0])
        if text == evidence.FEATURE_DISCLAIMER:
            return []
    return [Finding(rel, 1, "the document does not carry the design-form disclaimer", "")]


def code_files() -> List[str]:
    """The files this feature adds or changes under the paths FR-069 names, with their comments."""
    done = evidence.git("diff", "--name-only", FEATURE_BASE, "--", *CODE_PATHS).decode("utf-8")
    fresh = evidence.git("ls-files", "--others", "--exclude-standard", "--",
                         *CODE_PATHS).decode("utf-8")
    names = sorted(set(done.split("\n")) | set(fresh.split("\n")))
    return [n for n in names if n.endswith((".py", ".c", ".h")) and evidence.REPO.path(n).exists()]


def python_comments(source: str) -> Dict[int, str]:
    """Each comment and docstring line of a Python source, by its line number."""
    out: Dict[int, str] = {}
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type == tokenize.COMMENT:
            out[token.start[0] - 1] = token.string.lstrip("#").strip()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            doc = ast.get_docstring(node, clean=False)
            if doc:
                first = node.body[0].lineno - 1
                for offset, line in enumerate(doc.split("\n")):
                    out[first + offset] = line.strip()
    return out


def c_comments(source: str) -> Dict[int, str]:
    out: Dict[int, str] = {}
    for match in re.finditer(r"/\*.*?\*/|//[^\n]*", source, re.S):
        first = source.count("\n", 0, match.start())
        for offset, line in enumerate(match.group(0).split("\n")):
            out[first + offset] = line.strip(" /*")
    return out


def scan_code(rel: str, register: Dict) -> List[Finding]:
    source = read_text(rel).replace("\r\n", "\n")
    comments = python_comments(source) if rel.endswith(".py") else c_comments(source)
    numbers = sorted(comments)
    return scan_lines(rel, numbers, [comments[n] for n in numbers], register)


def mapping_findings(register: Dict) -> List[Finding]:
    """The chapter's own rule, the design document's section headed "Slime-mould mapping"."""
    rel = evidence.DESIGN_REL
    if not evidence.REPO.path(rel).exists():
        return []
    lines = read_lines(rel)
    heads = [h for h in evidence.headings_of(lines) if h.text == MAPPING_HEADING]
    if len(heads) != 1:
        return [Finding(rel, 1, f"the heading {MAPPING_HEADING!r} stands {len(heads)} times", "")]
    head = heads[0]
    later = [h.line for h in evidence.headings_of(lines)
             if h.line > head.line and h.level <= head.level]
    out = []
    for number in range(head.line, later[0] if later else len(lines)):
        line = lines[number].replace(MAPPING_SENTENCE, "")
        if MAPPING_WORDS.search(line):
            out.append(Finding(rel, number + 1, "a word of FR-030's list in the mapping chapter",
                               lines[number]))
    return out


def check_entries(register: Dict, block_lines: Dict[str, Set[int]]) -> List[Finding]:
    """An entry that names a line of a block is a finding itself (SEC-094)."""
    out = []
    for rel, numbers in block_lines.items():
        lines = read_lines(rel)
        texts = {lines[n] for n in numbers} | {strip_quote(lines[n]) for n in numbers}
        for entry in register["allow_list"]["lines"]:
            if entry["path"] == rel and entry["text"] in texts:
                out.append(Finding(REGISTER_REL, 1, "an entry names a line of a block",
                                   entry["text"]))
    for entry in register["allow_list"]["lines"]:
        if entry["path"] == REGISTER_REL or entry.get("rule") == "the register's checks":
            out.append(Finding(REGISTER_REL, 1, "an entry names a finding of the register's checks",
                               entry["text"]))
    return out


def run_checks(register: Dict) -> List[Finding]:
    findings = check_register(register)
    block_findings, block_lines = check_blocks(register)
    findings.extend(block_findings)
    security = read_lines("security.md")
    readme = read_lines("README.md")
    findings.extend(check_section_1_1(register, security))
    findings.extend(check_section_15(register, security))
    findings.extend(check_readme(register, readme, block_lines["README.md"]))
    findings.extend(check_entries(register, block_lines))
    present = features_present()
    for name in present:
        with feature(name):
            for rel in markdown_files():
                lines = read_lines(rel)
                findings.extend(check_design_disclaimer(rel, lines))
                findings.extend(scan_lines(rel, list(range(len(lines))), lines, register))
    for rel in ("README.md", "security.md"):
        lines = read_lines(rel)
        quoted = " ".join(strip_quote(line) for line in lines if line.startswith(">"))
        if any(f["disclaimer"] in quoted for f in evidence.FEATURES.values()):
            findings.append(Finding(rel, 1, "it keeps its own blocks and carries no copy", ""))
        skip = block_lines[rel]
        kept = [n for n in range(len(lines)) if n not in skip]
        findings.extend(scan_lines(rel, kept, [lines[n] for n in kept], register))
    for rel in code_files():
        findings.extend(scan_code(rel, register))
    for name in present:
        with feature(name):
            findings.extend(mapping_findings(register))
    return findings


def last_gate_commit() -> Optional[str]:
    """The newest commit that records a gate's approval in the spec's table."""
    best: List[Tuple[int, str]] = []
    specs = [evidence.FEATURES[name]["spec"] + "/spec.md" for name in features_present()]
    for name in GATE_ROWS:
        pattern = f"-G^\\| {re.escape(name)}.*\\| Approved"
        found = evidence.git("log", "-1", "--format=%ct %H", pattern, "--",
                             *specs).decode("ascii").split()
        if found:
            best.append((int(found[0]), found[1]))
    return max(best)[1] if best else None


def entries_since_gate(register: Dict) -> List[Dict]:
    commit = last_gate_commit()
    blob = evidence.show(REGISTER_REL, commit) if commit else None
    earlier = {"phrases": [], "lines": []}
    if blob:
        earlier = json.loads(blob.decode("utf-8"))["allow_list"]
    out = []
    for kind in ("phrases", "lines"):
        out.extend(entry for entry in register["allow_list"][kind] if entry not in earlier[kind])
    return out


def main(argv: Optional[List[str]] = None) -> int:
    register = json.loads(read_text(REGISTER_REL))
    for entry in entries_since_gate(register):
        print(f"entry since the last gate: {entry.get('phrase') or entry.get('text')!r}: "
              f"{entry['reason']}")
    findings = run_checks(register)
    for finding in findings:
        print(f"{finding.path}:{finding.line}: {finding.rule}: {finding.text[:120]}")
    print(f"{len(findings)} findings")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
