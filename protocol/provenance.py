"""Feature 004: the one writer of the provenance log, $REP/provenance.jsonl (data-model section 14).

One line per file drafted or repaired with an AI tool, and per section where a file is drafted in
parts; a review is a new entry that follows the one it reviews, and no entry changes. Every append
takes data/log-append.lock and checks the chain first; a refusal exits 2 and appends nothing.

This module makes no security claim.
"""
from __future__ import annotations

import re
from typing import Dict, List, Sequence

from protocol import evidence
from protocol.evidence import NONE, Refused

LOG = evidence.PROVENANCE_LOG_REL
STATUSES = ("pending", "accepted", "changes-requested")
RATIONALE_REL = evidence.FEATURE_REL + "/rationale.md"
ADDED_BY_THE_WRITER = ("seq", "prev_sha256", "date_utc")
ENTRY_FIELDS = ("path", "section", "sha256", "sha256_kind", "tool", "model", "session", "task_id",
                "review_status")
KNOWN_RESULT_FIELDS = ("known_result", "source", "tool", "model", "session", "task_id",
                       "review_status")
REVIEW_FIELDS = ("path", "section", "follows", "sha256", "sha256_kind", "reviewer", "row",
                 "reviewed_sha256", "owner_word", "review_status")
RECORD_REVIEW_FIELDS = ("record_id", "sha256", "sha256_kind", "reviewer", "row", "reviewed_sha256",
                        "owner_word", "review_status")
# A reviewer is a person: never an AI tool or session (spec FR-064).
NOT_A_REVIEWER = re.compile(r"\b(claude|gpt|chatgpt|copilot|gemini|codex|llm|model|agent|agent's|"
                            r"session|ai|tool|bot|assistant|anthropic|openai)\b", re.I)


def require(fields: Dict, names: Sequence[str]) -> None:
    """An entry with a field of its kind missing or empty is refused, naming it."""
    for name in names:
        if name not in fields or fields[name] in ("", None):
            raise Refused(f"the entry holds no {name}")
    for name in ADDED_BY_THE_WRITER:
        if name in fields:
            raise Refused(f"{name}: the writer adds it")
    if fields.get("review_status") not in STATUSES:
        raise Refused(f"review_status {fields.get('review_status')!r} is not one of {STATUSES}")


def check_hash(fields: Dict) -> None:
    """The entry's `sha256` and kind are those of the named file or section, computed here."""
    path = evidence.REPO.path(fields["path"])
    if not path.exists():
        raise Refused(f"{fields['path']} does not exist")
    digest, kind = evidence.named_hash(fields["path"], fields["section"])
    if (fields["sha256"], fields["sha256_kind"]) != (digest, kind):
        raise Refused(f"{fields['path']}: its sha256 or kind differs from {digest}, {kind}")


def append(fields: Dict) -> Dict:
    environment = evidence.guard_environment("provenance")
    return evidence.append_entry(LOG, dict(fields, environment=environment))


def add(fields: Dict) -> Dict:
    """An entry for a file or a section of one, or for a known result this feature writes itself or
    a tool's second known result, which may be a published value that no file holds."""
    if "known_result" in fields and "path" not in fields:
        require(fields, KNOWN_RESULT_FIELDS)
    else:
        require(fields, ENTRY_FIELDS)
        check_hash(fields)
    return append(fields)


def latest_for(path: str, section: str) -> Dict:
    entries = [e for e, _ in evidence.check_chain(LOG)
               if e.get("path") == path and e.get("section") == section]
    if not entries:
        raise Refused(f"no entry for {path}, {section}")
    return entries[-1]


def guard_row(fields: Dict) -> None:
    """The row reads at HEAD, with `reviewed_sha256`, the decision the entry records."""
    wanted = {"accepted": "Approved", "changes-requested": "Declined"}.get(fields["review_status"])
    if wanted is None:
        raise Refused("a review entry reads accepted or changes-requested")
    rows: List[evidence.Row] = [r for r in evidence.head_table() if r.name == fields["row"]]
    if not rows or rows[-1].decision != wanted or fields["reviewed_sha256"] not in rows[-1].notes:
        raise Refused(f"the row {fields['row']!r} does not read {wanted} at HEAD with "
                      f"{fields['reviewed_sha256']}")


def guard_reviewer(fields: Dict) -> None:
    if NOT_A_REVIEWER.search(fields["reviewer"]):
        raise Refused(f"reviewer {fields['reviewer']!r} names an AI tool or session")


def guard_record_review(fields: Dict) -> None:
    found = evidence.find_record(fields["record_id"])
    if found is None:
        raise Refused(f"no record {fields['record_id']}")
    digest = evidence.sha256(found[0].read_bytes())
    if (fields["sha256"], fields["sha256_kind"]) != (digest, "raw"):
        raise Refused(f"{fields['record_id']}: its sha256 or kind differs from {digest}, raw")


def guard_section_review(fields: Dict) -> None:
    """So that the status the latest entry gives is that of the text the reviewer read."""
    check_hash(fields)
    path, section = fields["path"], fields["section"]
    latest = latest_for(path, section)
    if fields["follows"] != latest["seq"]:
        raise Refused(f"follows {fields['follows']}: the latest entry for {path}, {section} is "
                      f"{latest['seq']}")
    if fields["sha256"] != latest["sha256"]:
        raise Refused(f"{path}, {section}: the text differs from the text of entry {latest['seq']}")
    now = (evidence.named_hash(path)[0], evidence.named_hash(path, section)[0])
    if fields["reviewed_sha256"] not in now:
        raise Refused(f"{path} does not have the reviewed_sha256 the row names")
    if path == RATIONALE_REL and not re.fullmatch(r"Owner design review( \d+)?", fields["row"]):
        raise Refused(f"{fields['row']!r}: a section of rationale.md takes the owner design "
                      "review's entries, not a row of another family")


def review(fields: Dict) -> Dict:
    """A review entry, or the review of an evidence record, on the owner's explicit word alone."""
    of_record = "record_id" in fields
    require(fields, RECORD_REVIEW_FIELDS if of_record else REVIEW_FIELDS)
    guard_reviewer(fields)
    guard_row(fields)
    if of_record:
        guard_record_review(fields)
    else:
        guard_section_review(fields)
    return append(fields)


def repair(row_name: str) -> Dict:
    """The one append to a broken chain, while its row "Log repair <n>" reads Approved at HEAD."""
    environment = evidence.guard_environment("provenance")
    fields = evidence.repair_fields(LOG, row_name)
    return evidence.restore_chain(LOG, fields, {"environment": environment,
                                                "section": NONE, "review_status": "pending"})
