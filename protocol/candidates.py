"""Feature 004: the one writer of the candidate log, research/004/candidates.jsonl (spec FR-041;
data-model section 3).

An entry is never edited or deleted, and a candidate counts towards the stop rule from its first
entry. `scripts/candidate_log.py` writes the entries that no other script writes; `append` is what
`scripts/evidence_v3.py`, `scripts/d4_choice.py` and `scripts/round_rule.py` call for theirs. Every
append takes data/log-append.lock and checks the chain first, and every refusal exits 2 and appends
nothing.

This module makes no security claim.
"""
from __future__ import annotations

import json
import re
from typing import Dict, List, Optional, Sequence, Tuple

from protocol import evidence
from protocol.evidence import NONE, Refused

LOG = evidence.CANDIDATE_LOG_REL
CANDIDATES_REL = "research/004/candidates"
SUPERSEDED_REL = evidence.SUPERSEDED_REL
FAMILIES = {"A": "ARX", "B": "Boolean"}
CANDIDATE_ID = re.compile(r"cand-([AB])([123])")


def _follow_feature() -> None:
    """This log, its candidates' directory and their IDs are the active feature's."""
    global LOG, CANDIDATES_REL, SUPERSEDED_REL, CANDIDATE_ID
    LOG = evidence.CANDIDATE_LOG_REL
    CANDIDATES_REL = evidence.FEATURES[evidence.FEATURE]["research"] + "/candidates"
    SUPERSEDED_REL = evidence.SUPERSEDED_REL
    CANDIDATE_ID = re.compile(re.escape(evidence.CANDIDATE_PREFIX) + r"([AB])([123])")


evidence.on_feature(_follow_feature)
MOST_PER_FAMILY = 3
ADDED_BY_THE_WRITER = ("seq", "prev_sha256", "date_utc")
# What a `proposed` entry's `parameters` holds, all of it before the candidate's first tool run.
PARAMETERS = ("round_structure", "nonlinear_component", "rotation_rule", "constant_rule", "generics",
              "constant_instance", "rotation_search", "folding_rule", "longest_link", "food_nodes",
              "trees", "reduced_variants", "phases")
# FR-030's five components, the colour schedule, the local linear layer, the round constants and the
# key path, each with its place in the metaphor and what it serves (data-model section 3).
MAPPING = ("pressure and vein lanes", "flux coupling", "vein accumulation", "food nodes",
           "peristaltic rotations", "colour schedule", "local linear layer", "round constants",
           "key path")
MAPPING_FIELDS = ("place", "serves")
DECIDED_HERE = ("eligible", "ineligible", "rejected", "withdrawn")
FINAL = evidence.CLOSING_DECISIONS
SHOWN_BY_THE_REASON = ("rejected", "ineligible")
# The rules' reasons, each with what shows it and whether a replacement may follow.
FAILED_CHECK, ITEM, INCONCLUSIVE, SPENT = "failed check", "eligibility item", "inconclusive", "spent budget"
D4_NOT_ANALYSED = "not analysed at the production width: D4 chose the other family"
D4_TIE = "D4 chose the other family by its tie-breaks"
UNIFORM_CONTROL, NO_TRAIL_ROUTE, SHARED_MATCH = ("uniform control fired", "no validated trail route",
                                                 "match in the shared polynomial")
CAUSES = {"rejected": (FAILED_CHECK,),
          "ineligible": (ITEM, INCONCLUSIVE, SPENT, D4_NOT_ANALYSED, D4_TIE, UNIFORM_CONTROL,
                         NO_TRAIL_ROUTE, SHARED_MATCH)}
ALWAYS_SHARED = (D4_NOT_ANALYSED, D4_TIE, UNIFORM_CONTROL, NO_TRAIL_ROUTE, SHARED_MATCH)
SHARED_REASON = "cause shared"
FULL, BUDGET_SPENT, OWNER_DECLINED = ("the family full", "the budget spent",
                                      "the owner declined the proposed design")
CLOSE_REASONS = (FULL, BUDGET_SPENT, OWNER_DECLINED)
OUTCOMES = ("declined", "revised", "fixed", "stopped")
REVIEW_FAMILY = "Owner design review"


# -------------------------------------------------------------------------------- reading the log

def entries() -> List[Dict]:
    return [entry for entry, _ in evidence.check_chain(LOG)]


def of_event(log: Sequence[Dict], event: str, candidate: Optional[str] = None) -> List[Dict]:
    return [e for e in log if e.get("event") == event
            and (candidate is None or e.get("candidate_id") == candidate)]


def proposed_ids(log: Sequence[Dict], family: str) -> List[str]:
    return sorted({e["candidate_id"] for e in of_event(log, "proposed") if e["family"] == family})


def decisions(log: Sequence[Dict], candidate: str) -> List[str]:
    return [e["decision"] for e in of_event(log, "decision", candidate)]


def is_scored(log: Sequence[Dict], candidate: Optional[str] = None) -> bool:
    return bool(of_event(log, "scored", candidate))


def pending_replacements(log: Sequence[Dict]) -> List[Dict]:
    """The `replacement` entries logged `pending` that no later entry closes."""
    closed = {e.get("closes") for e in log if e.get("closes") is not None}
    return [e for e in of_event(log, "replacement")
            if e.get("state") == "pending" and e["seq"] not in closed]


def require(fields: Dict, names: Sequence[str]) -> None:
    for name in names:
        if name not in fields or fields[name] in ("", None, [], {}):
            raise Refused(f"the entry holds no {name}")
    for name in ADDED_BY_THE_WRITER:
        if name in fields:
            raise Refused(f"{name}: the writer adds it")


def guard_candidate(fields: Dict) -> Tuple[str, str]:
    """A candidate's ID and family: `cand-A1` to `cand-A3` and `cand-B1` to `cand-B3`, no more."""
    candidate = fields.get("candidate_id")
    match = CANDIDATE_ID.fullmatch(candidate or "")
    if match is None:
        raise Refused(f"candidate {candidate!r}: the stop rule allows A1 to A3 and B1 to B3")
    family = FAMILIES[match.group(1)]
    if fields.get("family", family) != family:
        raise Refused(f"{candidate} is of the family {family}")
    return candidate, family


def guard_known(log: Sequence[Dict], candidate: str) -> None:
    if not of_event(log, "proposed", candidate):
        raise Refused(f"{candidate} has no proposed entry")


def guard_owner_word(fields: Dict, why: str) -> None:
    """The owner's explicit word, quoted with its date, as a provenance review's `owner_word` is."""
    word = fields.get("owner_word")
    if not isinstance(word, dict) or not str(word.get("words", "")).strip() \
            or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(word.get("date"))):
        raise Refused(f"{why} is written only on the owner's explicit word, quoted with its date")


def append(fields: Dict) -> Dict:
    """One entry; `seq`, `prev_sha256` and `date_utc` are the writer's."""
    return evidence.append_entry(LOG, fields)


# ------------------------------------------------------------------------------ a proposed entry

def module_rel(candidate: str) -> str:
    return f"{CANDIDATES_REL}/{candidate}.py"


def guard_committed_module(candidate: str, digest: str) -> None:
    """The module the entry names is committed, and its hash is the entry's: a tool's first run
    reads what the log holds (data-model sections 1 and 3)."""
    rel = module_rel(candidate)
    path = evidence.REPO.path(rel)
    if not path.exists():
        raise Refused(f"{rel} does not exist")
    data = path.read_bytes()
    if evidence.sha256(data) != digest:
        raise Refused(f"{rel}: its SHA-256 is not the entry's oplist_sha256")
    if evidence.show(rel) != data:
        raise Refused(f"{rel} is not committed as it stands")


def guard_reopened(log: Sequence[Dict], fields: Dict) -> None:
    """After a `set-closed` entry the set reopens once, on a decline, for that decline's further
    candidate or one of its replacements (data-model section 3; ANA-083)."""
    closed = of_event(log, "set-closed")
    if not closed:
        return
    outcomes = of_event(log, "review-outcome")
    latest = outcomes[-1] if outcomes else None
    if latest is None or latest["outcome"] != "declined" or latest["seq"] < closed[-1]["seq"]:
        raise Refused("the set is closed: no decline of the owner design review reopens it")
    if len(closed) != 1:
        raise Refused("the set reopens once")
    guard_owner_word(fields, "a further candidate after a decline")
    further = latest.get("further_candidate")
    replacement = fields.get("replaces") in {e["seq"] for e in pending_replacements(log)}
    if fields["candidate_id"] != further and not replacement:
        raise Refused(f"{fields['candidate_id']} is not the decline's further candidate")


def guard_entered_late(log: Sequence[Dict], fields: Dict) -> None:
    """Once a candidate is scored, a further one comes only in place of one `rejected` or
    `ineligible`, never because another's R is high (research R6; data-model section 3)."""
    if fields.get("replaces") is not None:
        wanted = {e["seq"]: e for e in pending_replacements(log)}
        target = wanted.get(fields["replaces"])
        if target is None:
            raise Refused(f"seq {fields['replaces']} is no pending replacement entry")
        if target["family"] != fields["family"]:
            raise Refused("a replacement comes from the family of the candidate it replaces")
        guard_owner_word(fields, "a replacement's proposed entry")
    elif is_scored(log) and not of_event(log, "set-closed"):
        raise Refused("after the first score a candidate enters only in place of another")


def propose(fields: Dict) -> Dict:
    candidate, family = guard_candidate(fields)
    fields = dict(fields, family=family)
    require(fields, ("candidate_id", "oplist_sha256", "parameters"))
    missing = [name for name in PARAMETERS if not fields["parameters"].get(name)]
    if missing:
        raise Refused(f"the entry's parameters hold no {', '.join(missing)}")
    log = entries()
    if of_event(log, "proposed", candidate):
        raise Refused(f"{candidate} has its proposed entry: a change is a correction")
    if len(proposed_ids(log, family)) >= MOST_PER_FAMILY:
        raise Refused(f"a fourth proposed entry of {family}: the stop rule allows three per family")
    guard_committed_module(candidate, fields["oplist_sha256"])
    guard_reopened(log, fields)
    guard_entered_late(log, fields)
    return append(dict(fields, event="proposed", evidence=[], budget_used_h={}))


# -------------------------------------------------------------------- mapping and the entered set

def mapping(fields: Dict) -> Dict:
    candidate, family = guard_candidate(fields)
    require(fields, ("candidate_id", "mapping"))
    log = entries()
    guard_known(log, candidate)
    if is_scored(log, candidate):
        raise Refused(f"{candidate} is scored: its mapping entry comes before its first score")
    table = fields["mapping"]
    for name in MAPPING:
        item = table.get(name) if isinstance(table, dict) else None
        if not isinstance(item, dict) or any(not item.get(part) for part in MAPPING_FIELDS):
            raise Refused(f"the mapping holds no place and purpose for {name}")
    return append(dict(fields, family=family, event="mapping"))


def enter() -> List[Dict]:
    """One `entered-d4` entry per candidate of the entered set, before any score (research R6)."""
    log = entries()
    if is_scored(log):
        raise Refused("a scored entry exists: the entered set is recorded before the first score")
    held = {e["candidate_id"] for e in of_event(log, "entered-d4")}
    closed = {e["candidate_id"] for e in of_event(log, "decision")
              if e["decision"] in FINAL}
    entered = sorted({e["candidate_id"] for e in of_event(log, "proposed")} - held - closed)
    set_now = held | set(entered)
    families = {FAMILIES[CANDIDATE_ID.fullmatch(c).group(1)] for c in set_now}
    if families != set(FAMILIES.values()):
        raise Refused("the entered set holds at least one candidate of each family")
    if not entered:
        raise Refused("every candidate of the set has its entered-d4 entry")
    return [append({"candidate_id": candidate, "family": guard_candidate({"candidate_id": candidate})[1],
                    "event": "entered-d4"}) for candidate in entered]


# ------------------------------------------------------------------------------------- decisions

def cited_record(fields: Dict) -> Dict:
    """The record a decision cites, by ID and SHA-256; a file with another hash is not that record."""
    cited = fields.get("record")
    if not isinstance(cited, dict) or not cited.get("record_id") or not cited.get("sha256"):
        raise Refused("the decision cites no record by ID and SHA-256")
    found = evidence.find_record(cited["record_id"])
    if found is None:
        raise Refused(f"no record {cited['record_id']}")
    path, record = found
    if evidence.sha256(path.read_bytes()) != cited["sha256"]:
        raise Refused(f"{cited['record_id']}: its SHA-256 is not the one the decision cites")
    return record


def failed_items(record: Dict) -> bool:
    """Whether a round-rule record holds a size at which an item of eligibility fails."""
    for row in record.get("sizes", {}).values():
        items = row.get("eligible", {})
        if isinstance(items, dict) and any(item.get("met") is False for item in items.values()):
            return True
    return False


def left_in_row(candidate: str, row: str) -> float:
    return evidence.row_hours(candidate, row) - evidence.candidate_row_used(candidate, row)


def shows_reason(candidate: str, cause: str, record: Dict, fields: Dict) -> bool:
    """Whether the record shows the decision's reason (data-model section 3; ANA-088)."""
    if cause == FAILED_CHECK:
        return record.get("kind") in ("inverse", "bijectivity") and record.get("status") == "fail" \
            and record.get("candidate") == candidate
    if cause == ITEM:
        return record.get("kind") == "round-rule" and record.get("candidate") == candidate \
            and failed_items(record)
    if cause == INCONCLUSIVE:
        return record.get("status") == "inconclusive" and record.get("candidate") == candidate
    if cause == SPENT:
        row = fields.get("row")
        return record.get("kind") == "projection" and row in evidence.ROW_HOURS \
            and float(record.get("projected_hours", 0.0)) > left_in_row(candidate, row)
    if cause in (D4_NOT_ANALYSED, D4_TIE):
        family = guard_candidate({"candidate_id": candidate})[1]
        return record.get("kind") in ("d4-choice", "d4-tie") \
            and record.get("chosen_family") not in (None, NONE, family)
    if cause == UNIFORM_CONTROL:
        return record.get("kind") == "control" and record.get("status") == "inconclusive" and record.get("fires") is True
    if cause == SHARED_MATCH:
        return record.get("kind") == "generator-run" and record.get("status") == "fail"
    return cause == NO_TRAIL_ROUTE and record.get("kind") == "cross-check" \
        and record.get("status") == "fail"


def guard_d4_reason(log: Sequence[Dict], candidate: str) -> None:
    """A D4 reason comes after every candidate of the chosen family has its final decision, with one
    of them eligible (research R6; data-model section 3)."""
    family = guard_candidate({"candidate_id": candidate})[1]
    others = [c for name in FAMILIES.values() if name != family
              for c in proposed_ids(log, name)]
    finals = [set(decisions(log, other)) for other in others]
    if not others or not all(final & set(FINAL + ("eligible",)) for final in finals) \
            or not any("eligible" in final for final in finals):
        raise Refused("a D4 reason waits for the chosen family's final decisions, one of them "
                      "eligible")


def spent_is_shared(fields: Dict, record: Dict) -> bool:
    """A run every candidate needs is shared where its need exceeds the row's value, and the
    candidate's own where its earlier charges left too little (ANA-078)."""
    return float(record.get("projected_hours", 0.0)) \
        > evidence.row_hours(fields.get("candidate_id") or record.get("candidate"), fields["row"])


def replacement_state(cause: str, fields: Dict, record: Dict) -> Dict:
    """What the rules' classification gives: pending where the cause lies in the candidate itself,
    closed at once where its family or the whole set shares it (ANA-073; ANA-088)."""
    shared = cause in ALWAYS_SHARED or (cause == SPENT and spent_is_shared(fields, record))
    return {"state": "closed", "reason": SHARED_REASON} if shared else {"state": "pending"}


def decide(fields: Dict) -> List[Dict]:
    """A decision other than `selected` and `not selected`, with the `replacement` entry that a
    `rejected` or `ineligible` one brings."""
    candidate, family = guard_candidate(fields)
    decision = fields.get("decision")
    if decision not in DECIDED_HERE:
        raise Refused(f"decision {decision!r}: the log writer takes {DECIDED_HERE}")
    require(fields, ("candidate_id", "decision", "reason"))
    log = entries()
    guard_known(log, candidate)
    earlier = set(decisions(log, candidate)) & set(FINAL)
    if earlier:
        raise Refused(f"{candidate} has its final decision: {sorted(earlier)}")
    if decision == "withdrawn" and of_event(log, "evidence", candidate):
        raise Refused(f"{candidate} has had a tool run: it is withdrawn only before its first")
    entry = dict(fields, family=family, event="decision")
    if decision == "eligible":
        record = cited_record(fields)
        if record.get("kind") != "round-rule" or record.get("candidate") != candidate \
                or failed_items(record):
            raise Refused("an eligible decision cites the candidate's round-rule record")
    if decision not in SHOWN_BY_THE_REASON:
        return [append(entry)]
    cause = fields.get("cause")
    if cause not in CAUSES[decision]:
        raise Refused(f"cause {cause!r}: the rules' reasons for {decision} are {CAUSES[decision]}")
    record = cited_record(fields)
    if not shows_reason(candidate, cause, record, fields):
        raise Refused(f"the record {record.get('record_id')} does not show the reason: {cause}")
    if cause in (D4_NOT_ANALYSED, D4_TIE):
        guard_d4_reason(log, candidate)
    state = replacement_state(cause, fields, record)
    given = fields.get("replacement")
    if given is not None and given != state:
        raise Refused(f"replacement {given!r}: the rules give {state!r}")
    entry.pop("replacement", None)
    first = append(entry)
    return [first, append(dict(state, candidate_id=candidate, family=family, event="replacement",
                               decision_seq=first["seq"]))]


# ----------------------------------------------------------- corrections, replacements, outcomes

def superseded_inventory() -> Dict[str, str]:
    path = evidence.REPO.path(SUPERSEDED_REL)
    return json.loads(path.read_bytes().decode("utf-8")) if path.exists() else {}


def guard_superseded(candidate: str, digest: str) -> None:
    """A replaced list stays unchanged under `<id>/superseded/`, and the inventory lists it."""
    rel = f"{CANDIDATES_REL}/{candidate}/superseded/{digest}.py"
    path = evidence.REPO.path(rel)
    if not path.exists() or evidence.sha256(path.read_bytes()) != digest:
        raise Refused(f"{rel}: the replaced list is not kept unchanged")
    if superseded_inventory().get(digest) != rel:
        raise Refused(f"{SUPERSEDED_REL} does not list {digest}")


def latest_oplist(log: Sequence[Dict], candidate: str) -> str:
    named = [e["oplist_sha256"] for e in log if e.get("candidate_id") == candidate
             and e.get("event") in ("proposed", "correction") and e.get("oplist_sha256")]
    return named[-1]


def correct(fields: Dict) -> Dict:
    candidate, family = guard_candidate(fields)
    require(fields, ("candidate_id", "reason"))
    log = entries()
    guard_known(log, candidate)
    target = fields.get("corrects")
    if type(target) is not int or not 0 <= target < len(log):
        raise Refused(f"corrects {target!r}: a correction cites the seq it corrects")
    digest = fields.get("oplist_sha256")
    if digest:
        guard_committed_module(candidate, digest)
        guard_superseded(candidate, latest_oplist(log, candidate))
    return append(dict(fields, family=family, event="correction"))


def guard_budget_spent(fields: Dict, target: Dict) -> None:
    """R7's rows, the record of the need and, for a lowered row, the entry that lowered the budget
    show that the budget is spent (data-model section 3; ANA-078)."""
    row = fields.get("row")
    if row not in evidence.ROW_HOURS:
        raise Refused("a replacement closed for the budget names R7's row")
    record = cited_record(fields)
    need = float(record.get("projected_hours", 0.0))
    if record.get("kind") != "projection" or need <= 0.0:
        raise Refused("a replacement closed for the budget cites the record of the need")
    value = evidence.ROW_HOURS[row]
    lowered = fields.get("lowered_by")
    if lowered is not None:
        entry = next((e for e, _ in evidence.log_entries(evidence.PROTOCOL_LOG_REL)
                      if e.get("seq") == lowered and e.get("rule") == "Stop rule"), None)
        if entry is None or "row_hours" not in fields:
            raise Refused(f"seq {lowered} of the protocol change log lowers no budget")
        value = float(fields["row_hours"])
    if value > 0.0 and need <= value:
        raise Refused(f"{row}: {need} h of need fit the row's {value} h, so the budget allows")


def replace(fields: Dict) -> Dict:
    """Closes a pending `replacement` entry with its stated reason, after which the agent proposes
    no other design for that entry (ANA-087)."""
    log = entries()
    target = next((e for e in pending_replacements(log) if e["seq"] == fields.get("closes")), None)
    if target is None:
        raise Refused(f"seq {fields.get('closes')!r} is no pending replacement entry")
    reason = fields.get("reason")
    if reason not in CLOSE_REASONS:
        raise Refused(f"reason {reason!r}: the stated reasons are {CLOSE_REASONS}")
    if reason == FULL and len(proposed_ids(log, target["family"])) < MOST_PER_FAMILY:
        raise Refused(f"{target['family']} has fewer than {MOST_PER_FAMILY} candidates")
    if reason == BUDGET_SPENT:
        guard_budget_spent(fields, target)
    if reason == OWNER_DECLINED:
        guard_owner_word(fields, "a replacement closed for the owner's decline")
    return append(dict(fields, candidate_id=target["candidate_id"], family=target["family"],
                       event="replacement", state="closed"))


def outcome(fields: Dict) -> Dict:
    """A `review-outcome` entry, after the commit that records the decision of the owner design
    review's row with the highest k, which it reads at HEAD (ANA-083)."""
    candidate, family = guard_candidate(fields)
    require(fields, ("candidate_id", "outcome", "reasons"))
    log = entries()
    guard_known(log, candidate)
    result = fields["outcome"]
    if result not in OUTCOMES:
        raise Refused(f"outcome {result!r}: it is one of {OUTCOMES}")
    row = evidence.family_row(REVIEW_FAMILY)
    if row is None or row.decision.startswith("_") \
            or result not in f"{row.decision} {row.notes}".lower():
        raise Refused(f"the row with the highest k does not record the outcome {result}")
    if result == "declined":
        require(fields, ("needs", "further_candidate"))
    if result in ("revised", "fixed"):
        require(fields, ("old_version", "new_version"))
    return append(dict(fields, family=family, event="review-outcome", row=row.name))


def repair(row_name: str) -> Dict:
    """The one append to a broken chain, while its row "Log repair <n>" reads Approved at HEAD."""
    return evidence.restore_chain(LOG, evidence.repair_fields(LOG, row_name))
