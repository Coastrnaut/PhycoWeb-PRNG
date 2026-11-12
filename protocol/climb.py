"""Feature 005: the bound climb at the production width (spec FR-014 to FR-018; research R6, R12; data-model section 2).

What scripts/round_rule.py does for a candidate under PHYCOWEB_FEATURE=005, read from the candidate's records alone:

- the sizes in the order 16×16, 8×8, 4×4; at a size r ascends from 1, the linear search before the differential at
  each r, each kind independent;
- a size-independent search first where the family has one, an ARX box's bound over one call: capped or refused, it
  ends that kind's searches at every size;
- the first capped or refused search of a kind ends that kind's searches at that size, and the climb goes on by sums:
  after each r a `split` record where the largest sum of two established bounds, r1 + r2 = r, exceeds the searched
  bound or stands where none ran;
- a kind's climb at a size ends at the first r whose established bound has weight above 128, or at R_max = 64;
- R_bound at a size is the smallest r at which both kinds' bounds have weight above 128;
- a candidate whose established bounds at 16×16 cannot pass weight 128 by R_max is decided `ineligible` at once, with
  the cause `no R_bound at 16×16`, and no search runs at 8×8 or 4×4.

`next_step` gives the one step that comes next; the caller makes it, and asks again. Standard library and protocol/
only, so that the re-check can read a climb as it stands. This module makes no security claim.
"""
from __future__ import annotations

from fractions import Fraction
from typing import Any, Dict, List, Optional, Sequence, Tuple

from protocol import evidence
from protocol.evidence import NONE

SIZES = (16, 8, 4)
KINDS = ("linear", "differential")
WIDTH = 32
R_MAX = 64
TARGET_WEIGHT = 128
BOX_METHOD = "branch-and-bound"
BOX_SIZE = 4
COUNT_METHODS = {"ARX": "active-box count", "Boolean": "active-S-box count"}
SPLIT = "split"
NO_R_BOUND = "no R_bound at 16×16"
ESTABLISHED = "no weakness identified within the analysis performed"
NO_HOUR = "no hour was charged at 8×8 or 4×4: the sizes are climbed in the order 16×16, 8×8, 4×4 (spec FR-014, FR-018)"


def bounds(candidate: str) -> List[Dict]:
    """The candidate's bound records at the production width, a run ended from outside left out, oldest first."""
    found = [record for _, record in evidence.iter_records("bound", f"candidates/{candidate}")
             if record.get("width") == WIDTH and record.get("ended_outside", NONE) == NONE]
    return sorted(found, key=lambda record: (record["created_utc"], record["record_id"]))


def refusals(candidate: str) -> List[Dict]:
    """The projection records that hold a search's refusal by its row (research R6)."""
    return [record for _, record in evidence.iter_records("projection", "projections")
            if record.get("row") == f"{candidate}/trails" and record.get("refused")
            and (record.get("probe") or {}).get("width") == WIDTH]


def capped(record: Dict) -> bool:
    return record.get("capped") is True or record.get("status") == "inconclusive"


def weight_at(record: Dict, r: int) -> Optional[Fraction]:
    """A count record's weight over r rounds, whole by the count's own rule, or a `split` record's own at its r."""
    if record.get("method") == SPLIT:
        return Fraction(record["bound"]) if record.get("rounds") == r else None
    row = (record.get("counts") or {}).get(str(r))
    if row is None:
        return None
    count = row["count"]
    return Fraction(count * record["weight_per_sbox"]) if record["method"] == "active-S-box count" else Fraction(count)


class Kind:
    """One kind's climb at one size, as the records give it."""

    def __init__(self) -> None:
        self.established: Dict[int, Tuple[Fraction, Dict]] = {}
        self.searched: Dict[int, Tuple[Fraction, Dict]] = {}
        self.ended: Optional[int] = None
        self.ending: Optional[Dict] = None
        self.last_search: Optional[Dict] = None

    def passed(self) -> Optional[int]:
        over = [r for r, (weight, _) in self.established.items() if weight > TARGET_WEIGHT]
        return min(over) if over else None

    def best_sum(self, r: int) -> Tuple[Optional[Fraction], Optional[Tuple[int, int]], int]:
        """The largest W(r1) + W(r2), r1 + r2 = r, of the established bounds, the pair that gives it, the first in
        ascending r1, and the number of pairs compared."""
        best, pair, compared = None, None, 0
        for first in range(1, r // 2 + 1):
            if first in self.established and r - first in self.established:
                compared += 1
                total = self.established[first][0] + self.established[r - first][0]
                if best is None or total > best:
                    best, pair = total, (first, r - first)
        return best, pair, compared

    def reachable(self) -> bool:
        """Whether the established bounds, carried on by sums alone, pass weight 128 by R_max."""
        held = {r: weight for r, (weight, _) in self.established.items()}
        for r in range(1, R_MAX + 1):
            sums = [held[first] + held[r - first] for first in range(1, r // 2 + 1) if first in held and r - first in held]
            if sums and max(sums) > held.get(r, Fraction(-1)):
                held[r] = max(sums)
            if held.get(r, Fraction(0)) > TARGET_WEIGHT:
                return True
        return False


def read_kind(candidate: str, size: int, kind: str, counted=None) -> Kind:
    """`counted(record)` says whether a searched record's bound counts, its cross-check among what that asks."""
    out = Kind()
    method = COUNT_METHODS[evidence.family_of(candidate)]
    for record in bounds(candidate):
        if record.get("size") != size or record.get("bound_kind") != kind:
            continue
        if record.get("method") == method:
            out.last_search = record
            if capped(record):
                if out.ended is None or record["rounds"] < out.ended:
                    out.ended, out.ending = record["rounds"], record
            elif record.get("status") == "pass" and (counted is None or counted(record)):
                for r in range(1, record["rounds"] + 1):
                    weight = weight_at(record, r)
                    if weight is not None and (r not in out.searched or weight > out.searched[r][0]):
                        out.searched[r] = (weight, record)
        elif record.get("method") == SPLIT and record.get("status") == "pass":
            weight = weight_at(record, record["rounds"])
            if record["rounds"] not in out.established or weight > out.established[record["rounds"]][0]:
                out.established[record["rounds"]] = (weight, record)
    for r, item in out.searched.items():
        if r not in out.established or item[0] >= out.established[r][0]:
            out.established[r] = item
    for record in refusals(candidate):
        probe = record["probe"]
        if probe.get("size") == size and probe.get("bound_kind") == kind and probe.get("method") == method:
            r = record.get("rounds")
            if r not in out.searched and (out.ended is None or r < out.ended):
                out.ended, out.ending = r, record
    return out


def box_state(candidate: str, kind: str) -> Tuple[Optional[Dict], Optional[Dict]]:
    """The size-independent search of an ARX candidate: its `pass` record, and the record that ended it, capped or
    refused, either of them or neither."""
    done, ended = None, None
    for record in bounds(candidate):
        if record.get("method") == BOX_METHOD and record.get("bound_kind") == kind and record.get("size") == BOX_SIZE:
            if record.get("status") == "pass" and not capped(record):
                done = record
            elif capped(record):
                ended = record
    for record in refusals(candidate):
        probe = record["probe"]
        if probe.get("method") == BOX_METHOD and probe.get("bound_kind") == kind and done is None:
            ended = record
    return done, ended


def r_bound(candidate: str, size: int, counted=None) -> Tuple[Optional[int], Dict[str, Dict]]:
    """R_bound at a size, the smallest r at which both kinds' bounds have weight above 128, with, per kind, the record
    that sets it, searched or `split`, the last searched record and the r of the first capped or refused search."""
    detail: Dict[str, Dict] = {}
    passes = []
    for kind in KINDS:
        state = read_kind(candidate, size, kind, counted)
        r = state.passed()
        passes.append(r)
        detail[kind] = {"r": r if r is not None else NONE,
                        "record": state.established[r][1]["record_id"] if r is not None else NONE,
                        "method": state.established[r][1]["method"] if r is not None else NONE,
                        "last_searched_record": state.last_search["record_id"] if state.last_search else NONE,
                        "first_capped_or_refused_r": state.ended if state.ended is not None else NONE}
    return (max(passes) if None not in passes else None), detail


def part_of(record: Dict, weight: Fraction, r: int, digest: str) -> Dict:
    return {"record_id": record["record_id"], "sha256": digest, "sha256_kind": "raw", "rounds": r, "bound": str(weight)}


def next_step(candidate: str, counted=None) -> Dict[str, Any]:
    """The step that comes next in the candidate's climb: `box`, `search`, `split`, `ineligible` or `done`."""
    family = evidence.family_of(candidate)
    blocked: Dict[str, Dict] = {}
    if family == "ARX":
        for kind in KINDS:
            done, ended = box_state(candidate, kind)
            if done is None and ended is None:
                return {"step": "box", "bound_kind": kind, "method": BOX_METHOD, "size": BOX_SIZE, "rounds": 1}
            if done is None:
                blocked[kind] = ended
    for size in SIZES:
        states = {kind: read_kind(candidate, size, kind, counted) for kind in KINDS}
        for kind in blocked:
            if states[kind].ended is None:
                states[kind].ended, states[kind].ending = 1, blocked[kind]
        for r in range(1, R_MAX + 1):
            for kind in KINDS:
                state = states[kind]
                passed = state.passed()
                if passed is not None and passed <= r:
                    continue
                if state.ended is None and r not in state.searched:
                    return {"step": "search", "size": size, "bound_kind": kind, "rounds": r, "method": COUNT_METHODS[family]}
                total, pair, compared = state.best_sum(r)
                held = state.established.get(r)
                if total is not None and (held is None or total > held[0]):
                    searched = state.searched.get(r)
                    return {"step": "split", "size": size, "bound_kind": kind, "rounds": r, "bound": str(total),
                            "parts": [(state.established[p][1], state.established[p][0], p) for p in pair],
                            "alternatives": compared, "searched": str(searched[0]) if searched else NONE}
                if size == SIZES[0] and state.ended is not None and not state.reachable():
                    return {"step": "ineligible", "size": size, "bound_kind": kind, "cause": NO_R_BOUND,
                            "record": state.ending["record_id"], "statement": NO_HOUR}
            if all(states[kind].passed() is not None and states[kind].passed() <= r for kind in KINDS):
                break
        else:
            if size == SIZES[0]:
                last = [state.established[max(state.established)][1] for state in states.values()
                        if state.established and state.passed() is None]
                return {"step": "ineligible", "size": size, "bound_kind": NONE, "cause": NO_R_BOUND,
                        "record": last[0]["record_id"] if last else NONE, "statement": NO_HOUR}
            return {"step": "done", "reached": f"no R_bound at {size}×{size} by r = {R_MAX}"}
    return {"step": "done", "reached": "R_bound at every claimable size"}


def split_fields(step: Dict, digests: Sequence[str], scope: str) -> Dict:
    """A `split` bound record's fields (data-model section 2): a sum needs no tool and charges no row."""
    parts = [part_of(record, weight, r, digest) for (record, weight, r), digest in zip(step["parts"], digests)]
    return {"bound_kind": step["bound_kind"], "rounds": step["rounds"], "size": step["size"], "width": WIDTH,
            "bound": step["bound"], "method": SPLIT, "parts": parts, "alternatives": step["alternatives"],
            "searched": step["searched"], "tool": NONE, "validation": NONE, "cross_check": NONE, "scope": scope,
            "budget": {"cap_hours": NONE, "hours_used": 0}}
