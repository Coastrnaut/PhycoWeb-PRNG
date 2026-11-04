"""Feature 004: the one writer of the protocol change log, research/004/protocol-changes.jsonl
(spec FR-044; data-model section 18).

`check` makes FR-044's comparison and writes nothing; `create` writes the first entries, from the
lists "Rows that change the protocol", and `propose` one later entry, each ending in the approval
step, an owner's own act that the agent never performs. Every refusal exits 2 and appends nothing.

This module makes no security claim.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
from types import ModuleType
from typing import Any, Dict, List, Optional, Sequence, Tuple

from protocol import evidence
from protocol.evidence import NONE, Refused

LOG = evidence.PROTOCOL_LOG_REL
REFUSED_REL = evidence.REFUSED_LIST_REL
CHOICES_REL = evidence.FEATURE_REL + "/checklist-choices.md"
PLACE_CHECK_REL = "research/004/place-check.json"
PLACE_CHECK_SCRIPT = "research/004/place_check.py"
DIRECTIONS = ("stricter", "settled")
CONSTANT_RULE = "Constant rule"
# Spec FR-044's list: the headings whose direction is "no change", where a row is `settled`.
NO_CHANGE_RULES = (CONSTANT_RULE, "FUT-SEC-8 demonstration", "Development inputs",
                   "Nonlinearity choice rule (D4)")
# The first word of a recommendation says what kind of change it is: these two fix a meaning.
SETTLING_KINDS = ("Settle", "Clarify")
ROW_LINE = re.compile(r"^\| ((?:SEC|RAT|ANA|PRO|HW|REP)-\d{3}) \| ")
COMMIT = re.compile(r"\b[0-9a-f]{7}\b")
OWN_ENTRY = re.compile(r'\("([^"]+)", `(stricter|settled)`')


# --------------------------------------------------------------------------- the refused list

def parse_refused_list(data: bytes) -> List[Dict]:
    """Research R15's entry format, or a ValueError: each entry holds `name`, `kind` and `source`; a
    polynomial `degree` and `c`, a hexadecimal integer; a constant set `word_bits` and `words`, each
    a hexadecimal integer of at most `word_bits` bits."""
    document = json.loads(data.decode("utf-8"))
    entries = document.get("entries") if isinstance(document, dict) else None
    if not isinstance(entries, list):
        raise ValueError("the list holds no entries")
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("an entry is not an object")
        for name in ("name", "kind", "source"):
            if not isinstance(entry.get(name), str) or not entry[name]:
                raise ValueError(f"an entry holds no {name}")
        if entry["kind"] == "polynomial":
            if not isinstance(entry.get("degree"), int) or not is_hex(entry.get("c")):
                raise ValueError(f"{entry['name']}: a polynomial holds degree and c in hexadecimal")
        elif entry["kind"] == "constant-set":
            bits, words = entry.get("word_bits"), entry.get("words")
            if not isinstance(bits, int) or not isinstance(words, list) or not words:
                raise ValueError(f"{entry['name']}: a constant set holds word_bits and words")
            for word in words:
                if not is_hex(word) or int(word, 16) >> bits:
                    raise ValueError(f"{entry['name']}: {word} is no word of {bits} bits")
        else:
            raise ValueError(f"{entry['name']}: kind {entry['kind']!r}")
    return entries


def is_hex(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"0x[0-9a-fA-F]+", value) is not None


def refused_at_head() -> Tuple[bytes, List[Dict]]:
    blob = evidence.show(REFUSED_REL)
    if blob is None:
        raise Refused(f"{REFUSED_REL} is missing at HEAD")
    try:
        return blob, parse_refused_list(blob)
    except ValueError as exc:
        raise Refused(f"{REFUSED_REL} does not parse in research R15's format: {exc}") from None


def check_refused_list_at_head() -> Dict:
    """`create`'s step: the file exists, equals HEAD and parses; the entry's `refused_list`."""
    path = evidence.REPO.path(REFUSED_REL)
    if not path.exists():
        raise Refused(f"{REFUSED_REL} is missing")
    blob, _ = refused_at_head()
    if path.read_bytes() != blob:
        raise Refused(f"{REFUSED_REL} differs from HEAD")
    return {"path": REFUSED_REL, "sha256": evidence.sha256(blob), "sha256_kind": "raw"}


def latest_named() -> Optional[str]:
    """The SHA-256 that the latest `refused_list` of the log names."""
    named = [e["refused_list"]["sha256"] for e, _ in evidence.log_entries(LOG)
             if isinstance(e.get("refused_list"), dict)]
    return named[-1] if named else None


def version_with(digest: str) -> Optional[bytes]:
    """The refused list's version with that SHA-256, found in the file's git history."""
    commits = evidence.git("log", "--format=%H", "--", REFUSED_REL).decode("ascii").split()
    for commit in commits:
        blob = evidence.show(REFUSED_REL, commit)
        if blob is not None and evidence.sha256(blob) == digest:
            return blob
    return None


def guard_refused_addition(entry: Dict) -> List[Dict]:
    """`propose`'s refusals; returns the entries added, which the approval step prints. A version
    that no entry names is a draft, which the next named version may correct (research R15)."""
    blob, current = refused_at_head()
    if entry["refused_list"].get("sha256") != evidence.sha256(blob):
        raise Refused(f"refused_list differs from {REFUSED_REL} at HEAD")
    digest = latest_named()
    if digest is None:
        return current
    version = version_with(digest)
    if version is None:
        raise Refused(f"no version of {REFUSED_REL} in its history has {digest}")
    earlier = parse_refused_list(version)
    missing = [e["name"] for e in earlier if e not in current]
    if missing:
        raise Refused(f"the list at HEAD drops or changes {missing} of the latest named version")
    return [e for e in current if e not in earlier]


# ----------------------------------------------------------------------------- the comparison

def place_check() -> ModuleType:
    """research/004/place_check.py, the comparison committed for FR-044, on this repository."""
    rel = evidence.REPO.path(PLACE_CHECK_SCRIPT)
    if not rel.exists():
        rel = evidence.ROOT_OF_CODE / PLACE_CHECK_SCRIPT
    spec = importlib.util.spec_from_file_location("place_check", rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.ROOT = evidence.REPO.root
    return module


def check(to: str = "HEAD") -> Dict:
    """FR-044's comparison up to `to`; writes nothing."""
    module = place_check()
    try:
        return module.compare(to)
    except module.Refused as exc:
        raise Refused(str(exc)) from None


def place_row() -> evidence.Row:
    """The row "Place check" with the highest k, Approved at HEAD and naming the file's SHA-256."""
    row = evidence.family_row("Place check")
    if row is None or row.decision != "Approved":
        raise Refused("the row \"Place check\" does not read Approved at HEAD")
    blob = evidence.show(PLACE_CHECK_REL)
    if blob is None or evidence.sha256(blob) not in row.notes:
        raise Refused(f"the row \"Place check\" does not name {PLACE_CHECK_REL} at HEAD")
    return row


def guard_comparison(row: evidence.Row) -> Dict:
    """Its result up to `compared_to` equals the file the row names, and no place changed after."""
    stored = json.loads(evidence.show(PLACE_CHECK_REL).decode("utf-8"))
    if check(stored["compared_to"]) != stored:
        raise Refused(f"the comparison up to compared_to differs from {PLACE_CHECK_REL}")
    module = place_check()
    head = module.full("HEAD")
    if head != stored["compared_to"]:
        after = module.per_commit(stored["rules"], stored["compared_to"], head, {})
        if after:
            raise Refused(f"a place changed after compared_to, in {after[0]['commit'][:7]}: make "
                          "the comparison again and confirm it in \"Place check <k>\"")
    for item in stored["unmade"]:
        if item["commit"][:7] not in row.notes:
            raise Refused(f"{item['commit'][:7]} changed a place with no row and no confirmation")
    return stored


def own_entries(notes: str) -> Dict[str, Dict[str, str]]:
    """From the row "Place check", per commit confirmed as an entry of its own, each rule's
    direction (data-model section 18; PRO-064)."""
    part = notes.split("An entry of its own:", 1)
    if len(part) < 2:
        return {}
    text = part[1].split("The other commits", 1)[0]
    out: Dict[str, Dict[str, str]] = {}
    for piece in re.split(r";\s+(?:and\s+)?(?=[0-9a-f]{7}\b)", text):
        head = piece.split(",", 1)[0]
        commits = COMMIT.findall(head)
        for commit in commits:
            for rule, direction in OWN_ENTRY.findall(piece):
                out.setdefault(commit, {})[rule] = direction
    return out


# -------------------------------------------------------------------------- the first entries

def checklist_rows() -> Dict[str, Tuple[str, str, str]]:
    """Each row of checklist-choices.md: its question, its chosen option and its kind."""
    text = evidence.show(CHOICES_REL).decode("utf-8").replace("\r\n", "\n")
    out: Dict[str, Tuple[str, str, str]] = {}
    for line in text.split("\n"):
        match = ROW_LINE.match(line)
        if match:
            cells = [c.strip() for c in line.strip().strip("|").split(" | ")]
            kind = re.match(r"[A-Za-z]+", cells[2]).group(0)
            out[match.group(1)] = (cells[1], cells[2], kind)
    return out


def direction_of(rule: str, kind: str) -> str:
    return "settled" if rule in NO_CHANGE_RULES or kind in SETTLING_KINDS else "stricter"


def texts(places: Sequence[str], texts_at: Dict[str, str]) -> Dict[str, Optional[str]]:
    return {place: texts_at.get(place) for place in places}


def rule_object(module: ModuleType, cache: Dict, rule: str, places: Sequence[str], before: str,
                after: str, direction: str, readings: List[Dict]) -> Dict:
    return {"rule": rule, "commits": [before, after], "direction": direction, "readings": readings,
            "old_text": texts(places, module.place_texts(before, cache)),
            "new_text": texts(places, module.place_texts(after, cache))}


def row_entry(module: ModuleType, cache: Dict, row_id: str, row: Tuple[str, str, str],
              rules: Dict[str, List[str]], names: List[str], place: Dict,
              refused: Optional[Dict]) -> Dict:
    before, after = place["commits"]
    question, option, kind = row
    objects = []
    for name in names:
        direction = direction_of(name, kind)
        readings = [{"reading": question, "new_reading": option,
                     "no_looser": "as the row's option states, answered with its round"}] \
            if direction == "settled" else []
        objects.append(rule_object(module, cache, name, rules[name], before, after, direction,
                                   readings))
    return {"rules": objects, "row": {"id": row_id, "question": question, "option": option},
            "granularity": "round", "place_check": place, "reason": row_id,
            "refused_list": refused if CONSTANT_RULE in names else NONE,
            "last_record_id": NONE, "results_known": []}


def commit_entry(module: ModuleType, cache: Dict, commit: str, items: List[Dict],
                 directions: Dict[str, str], rules: Dict[str, List[str]], span: Dict,
                 notes: str, refused: Optional[Dict]) -> Dict:
    parent = module.full(commit + "^")
    objects = []
    for item in items:
        direction = directions.get(item["rule"])
        if direction is None:
            raise Refused(f"{commit[:7]}, {item['rule']}: no direction in the row \"Place check\"")
        readings = [{"reading": confirmation(notes, commit), "new_reading": "the edit's new text",
                     "no_looser": "as the owner's confirmation states"}] \
            if direction == "settled" else []
        objects.append(rule_object(module, cache, item["rule"], rules[item["rule"]], parent, commit,
                                   direction, readings))
    return {"rules": objects, "row": NONE, "granularity": "commit", "commit": commit,
            "place_check": span, "reason": confirmation(notes, commit),
            "refused_list": refused if CONSTANT_RULE in [o["rule"] for o in objects] else NONE,
            "last_record_id": NONE, "results_known": []}


def confirmation(notes: str, commit: str) -> str:
    """The owner's words on a commit, in the part of the row "Place check" that confirms it."""
    part = notes[notes.index("An entry of its own:"):]
    start = part.index(commit[:7])
    end = part.find(";", start)
    return part[start:end if end > 0 else len(part)]


SET_ASIDE_ITEM = re.compile(r"(?:^|;\s+(?:and\s+)?)((?:the entry for [0-9a-f]{7}|"
                            r"(?:SEC|RAT|ANA|PRO|HW|REP)-\d{3})[^;]*?): (kept|restored)([^;]*)")


def set_aside_readings(notes: str) -> Dict[str, Dict]:
    """The row "Readings set aside", entry by entry: per row ID or commit, the reading with the case
    under which the old text fails, and the owner's decision with its reason."""
    body = notes.split("entry by entry", 1)[-1]
    body = body[body.index(":") + 1:]
    body = body.split("`protocol_change.py create` reads", 1)[0].strip()
    out: Dict[str, Dict] = {}
    for match in SET_ASIDE_ITEM.finditer(body):
        head, decision, reason = match.groups()
        key = re.search(r"[0-9a-f]{7}\b|(?:SEC|RAT|ANA|PRO|HW|REP)-\d{3}", head).group(0)
        reading, _, case = head.partition(", under which ")
        if not case:
            reading, _, case = head.partition(", where ")
        out[key] = {"reading": reading, "set_aside": True, "case": case,
                    "decision": f"{decision}{reason}".strip().rstrip(".")}
    return out


def required_readings(section_18: str, place_notes: str) -> List[str]:
    """Each entry that must hold a decided reading: those that data-model section 18 names, and each
    commit that the row "Place check" says holds "one reading marked `set_aside`" (PRO-079)."""
    named = section_18.split("The first entries that hold one are those of", 1)
    rows = re.findall(r"(?:SEC|RAT|ANA|PRO|HW|REP)-\d{3}",
                      named[1].split("with every other entry", 1)[0]) if len(named) > 1 else []
    commits = [piece.split(",", 1)[0].strip()[:7]
               for piece in re.split(r";\s+(?:and\s+)?(?=[0-9a-f]{7}\b)",
                                     place_notes.split("An entry of its own:", 1)[-1])
               if "reading marked `set_aside`" in piece]
    return rows + commits


def rule_for_reading(entry: Dict, reading: Dict) -> Dict:
    """The rule whose places the reading names, or else the entry's first `settled` rule, or else
    its first."""
    words = reading["reading"] + " " + reading["case"]
    tokens = re.findall(r"FR-\d{3}|\bR\d+\b", words)
    for rule in entry["rules"]:
        if any(token in rule["old_text"] for token in tokens):
            return rule
    settled = [rule for rule in entry["rules"] if rule["direction"] == "settled"]
    return settled[0] if settled else entry["rules"][0]


def attach_readings(entries: List[Dict], readings: Dict[str, Dict]) -> None:
    """Each decided reading goes into the rule it concerns, which it makes `settled`. A row or a
    commit that the row decides and no first entry holds is an error of the row."""
    remaining = dict(readings)
    for entry in entries:
        key = entry["row"]["id"] if isinstance(entry["row"], dict) else entry["commit"][:7]
        if key in remaining:
            reading = remaining.pop(key)
            rule = rule_for_reading(entry, reading)
            rule["direction"] = "settled"
            rule["readings"] = rule["readings"] + [reading]
    if remaining:
        raise Refused(f"the row \"Readings set aside\" decides entries that do not exist: "
                      f"{sorted(remaining)}")


def build_first_entries() -> List[Dict]:
    """One entry per listed row in round order, and one per place confirmed as an entry of its own,
    each after its round's rows, as the log keeps the order of the commits (PRO-064)."""
    row = place_row()
    stored = guard_comparison(row)
    module = place_check()
    cache: Dict = {}
    to = stored["compared_to"]
    protocol = {k[len("protocol: "):] for k in module.place_texts(to, cache)
                if k.startswith("protocol: ")}
    rules, rounds = module.read_lists(to, protocol)
    table = checklist_rows()
    refused = check_refused_list_at_head()
    own = own_entries(row.notes)
    spans = {s["after"]: s for s in stored["spans"]}
    entries: List[Dict] = []

    def add_commits(heading: Optional[str]) -> None:
        by_commit: Dict[str, List[Dict]] = {}
        for item in stored["unmade"]:
            if item["beside"] == heading and item["commit"][:7] in own:
                by_commit.setdefault(item["commit"], []).append(item)
        for commit, items in by_commit.items():
            span = spans.get(heading)
            entries.append(commit_entry(module, cache, commit, items, own[commit[:7]], rules, span,
                                        row.notes, refused))

    add_commits(None)
    for listed, result in zip(rounds, stored["rounds"]):
        rows: Dict[str, List[str]] = {}
        for name, ids in listed["listed"].items():
            for row_id in ids:
                rows.setdefault(row_id, []).append(name)
        for row_id, names in rows.items():
            if row_id not in table:
                raise Refused(f"{row_id} is listed and has no row in {CHOICES_REL}")
            entries.append(row_entry(module, cache, row_id, table[row_id], rules, names, result,
                                     refused))
        add_commits(result["heading"])
    decided = evidence.family_row("Readings set aside")
    if decided is None or decided.decision != "Approved":
        raise Refused("the row \"Readings set aside\" does not read Approved at HEAD")
    readings = set_aside_readings(decided.notes)
    model = evidence.show(evidence.FEATURE_REL + "/data-model.md").decode("utf-8")
    undecided = [key for key in required_readings(model, row.notes) if key not in readings]
    if undecided:
        raise Refused(f"a reading marked set_aside is not decided: {undecided}")
    attach_readings(entries, readings)
    return entries


def guard_entry_fields(entry: Dict) -> None:
    """The fields without which the writer refuses an entry (data-model section 18)."""
    for name in ("last_record_id", "results_known"):
        if name not in entry:
            raise Refused(f"the entry holds no {name}")
    if "repair" in entry:
        return
    for rule in entry.get("rules", [entry]):
        if "rules" not in entry and not rule.get("rule"):
            raise Refused("the entry holds no rule")
        if rule.get("direction") not in DIRECTIONS:
            raise Refused(f"a rule's direction is {rule.get('direction')!r}: not {DIRECTIONS}")
        if rule["direction"] == "settled" and not rule.get("readings"):
            raise Refused("a settled rule holds no readings")


def owner_name() -> str:
    return evidence.git("config", "user.name").decode("utf-8").strip()


def approver(digits: str) -> Dict:
    return {"owner": owner_name(), "date": evidence.utc_now()[:10], "approval_confirmed": digits}


def create() -> int:
    """The first entries, after the approval step, through a temporary file renamed to the log's
    path once all are written, so that a writer that dies leaves no partial log (PRO-065)."""
    path = evidence.REPO.path(LOG)
    if path.exists():
        raise Refused(f"{LOG} exists: `create` runs only before it does")
    environment = evidence.guard_environment("protocol-log")
    entries = build_first_entries()
    date = evidence.utc_now()
    for seq, entry in enumerate(entries):
        entry.update({"seq": seq, "date_utc": date, "environment": environment})
        guard_entry_fields(entry)
    print(f"{len(entries)} first entries, counted from the lists")
    digest = evidence.first_entries_hash(entries)
    digits = evidence.approval_step(digest)
    with evidence.AppendLock(LOG):
        previous = evidence.ZERO_HASH
        temporary = path.with_name(path.name + ".tmp")
        with open(temporary, "wb") as handle:
            for entry in entries:
                entry["approver"] = approver(digits)
                entry["prev_sha256"] = previous
                line = evidence.log_line(entry)
                handle.write(line)
                previous = evidence.sha256(line)
        os.replace(temporary, path)
    print(f"{LOG}: {len(entries)} entries")
    return evidence.EXIT_OK


def later_step(entry: Dict) -> Dict:
    """The approval step of one later entry: the hash covers it without `approver` and
    `prev_sha256`, both filled once the owner has typed the digits."""
    digest = evidence.later_entry_hash(entry)
    return dict(entry, approver=approver(evidence.approval_step(digest)))


def decide_readings(fields: Dict) -> Dict:
    """Each reading a later entry marks `set_aside` is shown, and the owner's decision and reason
    recorded in it, before the hash that the owner confirms (PRO-079)."""
    readings = []
    for reading in fields.get("readings") or []:
        if reading.get("set_aside") and not reading.get("decision"):
            print(f"reading set aside: {reading}")
            if not evidence.interactive_terminal():
                raise Refused("the approval step needs an interactive terminal")
            reading = dict(reading, decision=input("the owner's decision and reason: ").strip())
        readings.append(reading)
    return dict(fields, readings=readings) if "readings" in fields else fields


def propose(fields: Dict) -> Dict:
    """One later entry from a JSON object holding its fields, ending in the approval step."""
    guard_entry_fields(fields)
    environment = evidence.guard_environment("protocol-log")
    fields = dict(fields)
    fields.setdefault("refused_list", NONE)
    if isinstance(fields["refused_list"], dict):
        for entry in guard_refused_addition(fields):
            print(f"entry added to the refused list: {entry['name']}")
    return evidence.append_entry(LOG, dict(decide_readings(fields), environment=environment),
                                 later_step)


def repair(row_name: str) -> Dict:
    """The one append to a broken chain: it changes no rule and goes through the approval step."""
    environment = evidence.guard_environment("protocol-log")
    fields = evidence.repair_fields(LOG, row_name)
    return evidence.restore_chain(LOG, fields, {"environment": environment, "last_record_id": NONE,
                                                "results_known": []}, later_step)


def rule_texts_hold(entry: Dict) -> bool:
    """For a repair's list: each commit a first entry names gives the rule's text at it."""
    module = place_check()
    cache: Dict = {}
    for rule in entry.get("rules", []):
        commits = rule.get("commits") or []
        if len(commits) != 2:
            return False
        try:
            for commit, stored in zip(commits, (rule.get("old_text"), rule.get("new_text"))):
                texts_at = module.place_texts(commit, cache)
                if any(texts_at.get(place) != text for place, text in (stored or {}).items()):
                    return False
        except (OSError, subprocess.SubprocessError):
            return False
    return True
