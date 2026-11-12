"""Feature 004: the arithmetic of the D4 choice and of the round rule, read from committed records (spec "Pre-registered Design
Protocol"; research R6; data-model sections 8 and 9).

scripts/d4_choice.py and scripts/round_rule.py call these, and scripts/recheck_004.py calls them again, so this module takes only the
standard library and protocol/. Every comparison of a score is exact. A run ended from outside decides nothing, and `until` holds a
re-check to the records that existed when the record under check was written.

This module makes no security claim.
"""
from fractions import Fraction
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from protocol import evidence
from protocol.evidence import NONE

WIDTHS = (16, 8)
SIZE = 4
KINDS = ("differential", "linear")
METHODS = ("active-box count", "active-S-box count")
FAMILIES = ("ARX", "Boolean")
LEAST_ROUNDS = 2
WIDTH = 32
DELTA = 2
TARGET_WEIGHT = 128
CONTROLLED = ("frequency", "avalanche")
CALLS_BEFORE_OUTPUT = 7
until: List[Optional[str]] = [None]


def held(kind: str, directory: str = "") -> List[Dict]:
    """Records of a kind, those written by `until` when it is set."""
    limit = until[0]
    return [record for _, record in evidence.iter_records(kind, directory)
            if limit is None or record.get("created_utc", "") < limit]


# -------------------------------------------------------------------------------- the records read

def weight_at(record: Dict, r: int) -> Optional[Fraction]:
    """A Π-level bound record's weight over r rounds, whole by the count's own rule, or None."""
    row = (record.get("counts") or {}).get(str(r))
    if row is None:
        return None
    count = row["count"]
    return Fraction(count * record["weight_per_sbox"]) if record["method"] == "active-S-box count" else Fraction(count)


def record_named(candidate: str, record_id: str) -> Optional[Dict]:
    found = evidence.find_record(record_id)
    if found is None or found[1].get("candidate") != candidate:
        return None
    return found[1]


def cross_checked(candidate: str, record: Dict) -> bool:
    """A count of active S-boxes cites its counter's cross-check, and a count of active boxes rests on a box record that cites the
    search's (data-model sections 6 and 8)."""
    source = record
    if record["method"] == "active-box count":
        source = record_named(candidate, record.get("box_record", NONE))
        if source is None:
            return False
    cited = record_named(candidate, source.get("cross_check", NONE))
    return cited is not None and cited.get("kind") == "cross-check" and cited.get("status") == "pass"


def bounds_of(candidate: str, width: int) -> Dict[str, Dict[int, Tuple[Fraction, str]]]:
    """Per kind and r, the weight and the record that holds it, the latest record of a counted tool."""
    out: Dict[str, Dict[int, Tuple[Fraction, str]]] = {kind: {} for kind in KINDS}
    chosen = [record for record in held("bound", f"candidates/{candidate}")
              if record.get("status") == "pass" and record.get("width") == width and record.get("size") == SIZE
              and record.get("method") in METHODS and cross_checked(candidate, record)]
    for record in sorted(chosen, key=lambda item: item["created_utc"]):
        for r in range(1, record["rounds"] + 1):
            weight = weight_at(record, r)
            if weight is not None:
                out[record["bound_kind"]][r] = (weight, record["record_id"])
    return out


def outcome_of(candidate: str, width: int, kind: str, decisions: Sequence[str]) -> Any:
    """A candidate's final reduced-width outcome for one bound kind: a bound record, a capped search's record or a decision."""
    records = [record for record in held("bound", f"candidates/{candidate}")
               if record.get("width") == width and record.get("size") == SIZE and record.get("bound_kind") == kind
               and record.get("method") in METHODS]
    if any(record.get("status") == "pass" for record in records):
        return {"bound": sorted(record["record_id"] for record in records if record.get("status") == "pass")}
    capped = [record["record_id"] for record in records if evidence.reached_cap(record)]
    if capped:
        return {"inconclusive": sorted(capped)}
    closing = [decision for decision in decisions if decision in ("ineligible", "rejected")]
    return {"decision": closing[0]} if closing else None


def rounds_with_both(table: Dict[str, Dict[int, Tuple[Fraction, str]]]) -> Set[int]:
    return {r for r in set(table["differential"]) & set(table["linear"]) if r >= LEAST_ROUNDS}


def climb_end(candidate: str, width: int) -> Optional[int]:
    """The r at which a candidate's climb ended at a width: the first at which a search of either kind reached its cap or its trail row
    refused it (research R6, "How far the searches go")."""
    ended = [record["rounds"] for record in held("bound", f"candidates/{candidate}")
             if record.get("width") == width and record.get("size") == SIZE and record.get("method") in METHODS and evidence.reached_cap(record)]
    for record in held("projection", "projections"):
        probe = record.get("probe") or {}
        if record.get("refused") and record.get("row") == f"{candidate}/trails" and probe.get("width") == width \
                and probe.get("size") == SIZE and probe.get("method") in METHODS:
            ended.append(record["rounds"])
    return min(ended) if ended else None


def climbs_owed(tables: Dict[str, Dict], ends: Dict[str, Optional[int]], families: Dict[str, str], closed: Sequence[str] = ()) -> List[str]:
    """What the climbs of research R6 still owe at one width. A family's top, the most it can still share, is known once each of its
    candidates has ended; nobody owes an r above the lowest top, every candidate owes r = 2, and until a family has a top everyone climbs
    on. A candidate with a closing decision owes nothing."""
    reach = {candidate: max(rounds_with_both(table), default=LEAST_ROUNDS - 1) for candidate, table in tables.items()}
    tops = []
    for family in FAMILIES:
        own = [candidate for candidate in tables if families[candidate] == family]
        if own and all(ends[candidate] is not None or candidate in closed for candidate in own):
            tops.append(max(reach[candidate] if candidate in closed else ends[candidate] - 1 for candidate in own))
    active = [candidate for candidate in sorted(tables) if candidate not in closed]
    if not tops:
        return [f"{candidate} has both bounds up to r = {reach[candidate]}, and no family's climb has ended" for candidate in active
                if ends[candidate] is None]
    last = max(min(tops), LEAST_ROUNDS)
    owed = []
    for candidate in active:
        wanted = last if ends[candidate] is None else min(last, ends[candidate] - 1)
        if reach[candidate] < wanted:
            owed.append(f"{candidate} has both bounds up to r = {reach[candidate]}, and r = {wanted} is wanted")
    return owed


def family_rounds(tables: Dict[str, Dict], families: Dict[str, str], family: str) -> Set[int]:
    out: Set[int] = set()
    for candidate, table in tables.items():
        if families[candidate] == family:
            out |= rounds_with_both(table)
    return out


def locate(by_width: Dict[int, Dict[str, Dict]], families: Dict[str, str]) -> Tuple[Optional[int], Optional[int], str, Optional[str]]:
    """The width, r*, the outcome and a family chosen by default, research R6's "Where", "One family scored" and "Neither family
    scored"."""
    for width in WIDTHS:
        common = family_rounds(by_width[width], families, "ARX") & family_rounds(by_width[width], families, "Boolean")
        if common:
            return width, max(common), "chosen", None
    for width in WIDTHS:
        first, second = (family_rounds(by_width[width], families, family) for family in FAMILIES)
        if first or second:
            family = FAMILIES[0] if max(first, default=0) > max(second, default=0) else FAMILIES[1]
            return width, max(first if family == FAMILIES[0] else second), "chosen by default", family
    return None, None, "not computable", None


def higher(left: Tuple[Fraction, Fraction], right: Tuple[Fraction, Fraction]) -> int:
    """Which score is higher, each a pair (W, L), by W_A·L_B against W_B·L_A: 1, -1 or 0."""
    a, b = left[0] * right[1], right[0] * left[1]
    return (a > b) - (a < b)


def scored_rows(tables: Dict[str, Dict], r_star: int, luts: Dict[str, Fraction], only: Optional[str],
                families: Dict[str, str]) -> Dict[str, Dict]:
    rows = {}
    for candidate, table in sorted(tables.items()):
        if r_star not in rounds_with_both(table) or (only is not None and families[candidate] != only):
            continue
        w_d, w_l = table["differential"][r_star][0], table["linear"][r_star][0]
        rows[candidate] = {"W_D": str(w_d), "W_L": str(w_l), "luts": str(luts[candidate]),
                           "score": str(min(w_d, w_l) / r_star / luts[candidate]),
                           "bound_records": {"differential": table["differential"][r_star][1], "linear": table["linear"][r_star][1]}}
    return rows


def weight_pair(row: Dict) -> Tuple[Fraction, Fraction]:
    return min(Fraction(row["W_D"]), Fraction(row["W_L"])), Fraction(row["luts"])


def representatives_of(rows: Dict[str, Dict], families: Dict[str, str]) -> Dict[str, str]:
    """Each family's scored candidate with the highest score, the first by name among equals."""
    out: Dict[str, str] = {}
    for candidate in sorted(rows):
        family = families[candidate]
        if family not in out or higher(weight_pair(rows[candidate]), weight_pair(rows[out[family]])) > 0:
            out[family] = candidate
    return out


def decide(by_width: Dict[int, Dict[str, Dict]], families: Dict[str, str], luts: Dict[int, Dict[str, Fraction]]) -> Dict:
    """The choice, research R6's rule, from the bounds: every comparison exact."""
    width, r_star, outcome, default = locate(by_width, families)
    if width is None:
        return {"width": NONE, "r_star": NONE, "outcome": outcome, "scored": {}, "representatives": {}, "chosen_family": NONE}
    rows = scored_rows(by_width[width], r_star, luts[width], default, families)
    representatives = representatives_of(rows, families)
    chosen = default
    if default is None:
        order = higher(weight_pair(rows[representatives["ARX"]]), weight_pair(rows[representatives["Boolean"]]))
        chosen = "ARX" if order > 0 else "Boolean" if order < 0 else None
        if chosen is None:
            outcome = "tie"
    return {"width": width, "r_star": r_star, "outcome": outcome, "scored": rows, "representatives": representatives,
            "chosen_family": chosen or NONE}


# ---------------------------------------------------------------------------------- what is read

def records_at(candidate: str, kind: str, size: int) -> List[Dict]:
    """The records of a kind at a claimable size, a run ended from outside left out, oldest first."""
    found = [record for record in held(kind, f"candidates/{candidate}")
             if record.get("config", {}).get("size") == size and record.get("ended_outside", NONE) == NONE]
    return sorted(found, key=lambda record: record["created_utc"])


def latest(records: Sequence[Dict], status: str = "pass") -> Optional[Dict]:
    found = [record for record in records if record.get("status") == status]
    return found[-1] if found else None


def r_f_and_b(candidate: str, size: int) -> Tuple[Optional[int], Optional[int], List[str]]:
    record = latest(records_at(candidate, "dependency", size))
    return (None, None, []) if record is None else (record["r_f"], record["r_b"], [record["record_id"]])


def bound_weights(candidate: str, size: int) -> Dict[str, Dict[int, Tuple[Any, str]]]:
    out: Dict[str, Dict] = {kind: {} for kind in KINDS}
    chosen = [record for record in records_at(candidate, "bound", size)
              if record.get("status") == "pass" and record.get("width") == WIDTH and record.get("method") in METHODS
              and cross_checked(candidate, record)]
    for record in chosen:
        for r in range(1, record["rounds"] + 1):
            weight = weight_at(record, r)
            if weight is not None:
                out[record["bound_kind"]][r] = (weight, record["record_id"])
    return out


def r_bound_of(candidate: str, size: int) -> Tuple[Optional[int], List[str]]:
    """The smallest r at which both bounds lie below 2⁻¹²⁸: both weights above 128, from bounds computed at that size (FR-038).
    Under feature 005 each kind's bound is the established one, searched or `split`, and a kind whose climb ended at its
    first weight above 128 keeps that bound at every larger r (feature 005, FR-016, FR-017; protocol/climb.py)."""
    if evidence.FEATURE != "004":
        from protocol import climb
        r, detail = climb.r_bound(candidate, size, lambda record: cross_checked(candidate, record))
        return r, sorted({row["record"] for row in detail.values() if row["record"] != NONE}) if r is not None else []
    weights = bound_weights(candidate, size)
    for r in sorted(set(weights["differential"]) & set(weights["linear"])):
        pair = (weights["differential"][r], weights["linear"][r])
        if all(item[0] > TARGET_WEIGHT for item in pair):
            return r, sorted({item[1] for item in pair})
    return None, []


def r_dist_of(candidate: str, size: int) -> Tuple[Optional[int], List[Dict]]:
    """The largest round count with a distinguisher, with each source: incomplete diffusion, a firing, a probabilistic invariant, a
    degree-based count, or a trail of Π lighter than 2⁻¹²⁸. Every firing recorded stands, so a later rise lowers nothing."""
    sources: List[Dict] = []
    for record in records_at(candidate, "dependency", size):
        if record.get("status") == "pass" and record.get("incomplete_rounds"):
            sources.append({"rounds": record["incomplete_rounds"], "source": "incomplete diffusion", "record": record["record_id"]})
    for kind in ("frequency", "avalanche", "invariant", "degree"):
        for record in records_at(candidate, kind, size):
            fired = record.get("rounds_fired") or []
            if fired:
                sources.append({"rounds": max(fired), "source": kind, "record": record["record_id"]})
    for record in records_at(candidate, "trail", size):
        if record.get("width") == WIDTH and evidence.trail_weight(record) < TARGET_WEIGHT:
            sources.append({"rounds": record["rounds"], "source": "trail", "record": record["record_id"]})
    return (max(item["rounds"] for item in sources), sources) if sources else (None, [])


def round_count(r_dist: Optional[int], r_bound: Optional[int], r_f: Optional[int], r_b: Optional[int]) -> Optional[int]:
    if r_bound is None or r_f is None or r_b is None:
        return None
    return max(2 * (r_dist or 0), r_bound + DELTA, 2 * max(r_f, r_b))


def control_of(test: str, size: int) -> Optional[Dict]:
    found = [record for record in held("control", "controls")
             if record.get("test") == test and record.get("size") == size and record.get("ended_outside", NONE) == NONE]
    return max(found, key=lambda record: record["created_utc"]) if found else None


def unresolved(candidate: str) -> List[str]:
    """A reproduction that differs on a field that enters a verdict, or a re-check that disagrees, blocks a record until a re-run after
    a recorded tool defect resolves it (data-model sections 1 and 9)."""
    resolved = {entry["record_id"] for kind in evidence.CANDIDATE_KINDS for record in held(kind, f"candidates/{candidate}")
                for entry in record.get("exclusions_and_reruns") or () if entry.get("why") == "tool defect"}
    own = {record["record_id"] for kind in evidence.CANDIDATE_KINDS for record in held(kind, f"candidates/{candidate}")}
    out = []
    for record in held("reproduction"):
        original = (record.get("original") or {}).get("record_id")
        if record.get("status") == "blocked" and original in own and original not in resolved:
            out.append(record["record_id"])
    for record in held("recheck"):
        for entry in record.get("disagreements") or ():
            if entry.get("record_id") in own and entry.get("record_id") not in resolved:
                out.append(record["record_id"])
    return sorted(set(out))


def pairs_and_avalanche(candidate: str) -> Tuple[int, List[float]]:
    """N and each size's a, from the records (research R4; ANA-075, ANA-079)."""
    pairs = set()
    measured: Dict[int, int] = {}
    for kind in CONTROLLED:
        for record in held(kind, f"candidates/{candidate}"):
            if not evidence.is_finished(record):
                continue
            size, rounds = record["config"]["size"], record["config"]["rounds"]
            pairs.update((size, r) for r in range(1, rounds + 1) if 2 * r > rounds)
            if kind == "avalanche":
                measured[size] = max(measured.get(size, 0), rounds)
    return len(pairs), [2.0 if m <= 128 else m / 64.0 for _, m in sorted(measured.items())]


def item(met: bool, *cited: Any, why: str = NONE) -> Dict:
    return {"met": bool(met), "evidence": list(cited), "why": why}


def passed(records: Sequence[Dict]) -> bool:
    return bool(records) and records[-1].get("status") == "pass"


def bias_item(candidate: str, kind: str, size: int, rounds: Optional[int]) -> Dict:
    """Measured at the size's R, its control quiet, and no record of it left inconclusive."""
    control = control_of(kind, size)
    if control is None or control.get("fires"):
        return item(False, why=f"the {kind} control at {size}×{size} has not run or fired")
    if candidate in control.get("not_charged", ()):
        return item(False, control["record_id"], why="the row could not hold the control")
    held = records_at(candidate, kind, size)
    if any(record.get("status") == "inconclusive" for record in held):
        return item(False, *[record["record_id"] for record in held], why="inconclusive")
    at_r = [record for record in held if rounds is not None and record["config"]["rounds"] == rounds and record["status"] in ("pass", "fail")]
    return item(bool(at_r), control["record_id"], *[record["record_id"] for record in at_r],
                why=NONE if at_r else f"no {kind} record at R = {rounds}")


def structural_items(candidate: str, size: int, rounds: Optional[int]) -> Dict[str, Dict]:
    at_r = [record for record in records_at(candidate, "inverse", size) if record["config"]["rounds"] == rounds]
    invariant = [record for record in records_at(candidate, "invariant", size) if record["config"]["rounds"] == rounds]
    symmetry = records_at(candidate, "symmetry", size)
    bijective = [record for record in held("bijectivity", f"candidates/{candidate}") if record.get("status") == "pass"]
    kept = any(record.get("status") == "fail" and any(row["kept"] for row in record["round_counts"].values()) for record in invariant)
    return {"FR-037 inverse": item(passed(at_r), *[record["record_id"] for record in at_r]),
            "FR-037 exhaustive bijectivity": item(bool(bijective), *[record["record_id"] for record in bijective]),
            "FR-037 symmetry": item(passed(symmetry), *[record["record_id"] for record in symmetry]),
            "FR-037 invariants": item(bool(invariant) and not kept, *[record["record_id"] for record in invariant]),
            "FR-037 degree": item(bool(records_at(candidate, "degree", size)), *[record["record_id"] for record in records_at(candidate, "degree", size)])}


def diffusion_item(candidate: str, size: int, rounds: Optional[int]) -> Dict:
    """The dependency through instantiate before the first output: at least seven calls of R rounds (FR-029)."""
    record = latest(records_at(candidate, "dependency", size))
    if record is None or rounds is None or not isinstance(record.get("through_instantiate"), dict):
        return item(False, why="no propagation through instantiate")
    reached = record["through_instantiate"]["every_bit_reached_after"]
    before = CALLS_BEFORE_OUTPUT * rounds
    return item(reached is not None and reached <= before, record["record_id"],
                {"every_bit_reached_after": reached, "rounds_before_first_output": before, "margin_over_r_f": before - record["r_f"]})


def row_met(record: Optional[Dict]) -> bool:
    return record is not None and all(row["R"] is not None and all(entry["met"] for entry in row["eligible"].values())
                                      for row in record["sizes"].values())
