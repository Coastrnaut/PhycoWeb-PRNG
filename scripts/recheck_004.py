#!/usr/bin/env python3
"""Feature 004: every verdict recomputed from committed files (FR-065; SC-017; contracts/cli.md; research R16).

    recheck_004.py [--kind KIND]
    recheck_004.py --reproduce RECORD

Recomputes each record's verdict from what it commits, a `trail` record's weight and class among them, and compares it with the
recorded one, with the verdict functions of the record's own `git_head`, taken from a separate worktree, and lists the rules in force
where a later stricter change applies. Where a local-only output is present it also re-derives the committed summary from it. It writes
a `recheck` record naming the interpreter, the platform and its `pip freeze`, and exits 1 on any disagreement, each listed. It imports
only the standard library and protocol/, runs in any environment, and makes no run of any tool.

A record that clear_lock.py wrote holds no saved output: its status, class and hours are checked against the `lock-cleared` record that
names it. Every decision and `replacement` state of the candidate log is recomputed too, with the cause its cited record shows. The
operation-list items of eligibility need the interpreter, so they are read as recorded and `--reproduce` of the record recomputes them.

This script makes no security claim.
"""
import argparse
import gzip
import importlib.util
import json
import platform
import subprocess
import sys
import tempfile
from fractions import Fraction
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from protocol import candidates, evidence, rules  # noqa: E402
from protocol.evidence import NONE, Refused, ToolFailure  # noqa: E402

SCRIPT = "scripts/recheck_004.py"
CODE = [SCRIPT, "protocol/evidence.py", "protocol/disclaimer.py", "protocol/devinputs_v3.py", "protocol/candidates.py", "protocol/rules.py"]
DIRECTORIES = {"demonstration": "fut-sec-8", "validation": "validation", "control": "controls", "selection": "freeze", "d4-choice": "d4",
               "generator-check": "generator-checks", "generator-run": "generator-runs"}
RUN_HERE = """
import importlib.util, sys
spec = importlib.util.spec_from_file_location("recheck_004", "scripts/recheck_004.py")
module = importlib.util.module_from_spec(spec)
sys.modules["recheck_004"] = module
spec.loader.exec_module(module)
getattr(module, sys.argv[1])(*sys.argv[2:])
"""


# ----------------------------------------------------------------------- the functions of a commit

class Verdicts:
    """The verdict functions at each record's `git_head`, each commit in a worktree of its own for as long as this run lasts. A commit
    from before a function existed made no record that needs it, and one that does is read with HEAD's, which the output names."""

    def __init__(self) -> None:
        self.trees: List[Path] = []
        self.modules: Dict[str, ModuleType] = {}

    def at(self, commit: str) -> ModuleType:
        if commit not in self.modules:
            tree = evidence.add_worktree(commit)
            self.trees.append(tree)
            spec = importlib.util.spec_from_file_location(f"evidence_at_{commit[:12]}", tree / "protocol/evidence.py")
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            self.modules[commit] = module
        return self.modules[commit]

    def close(self) -> None:
        for tree in self.trees:
            evidence.remove_worktree(tree)


def function(module: ModuleType, name: str) -> Callable:
    return getattr(module, name, getattr(evidence, name))


# --------------------------------------------------------------------------------- saved outputs

def output_values(entry: Dict) -> Optional[Any]:
    """An output's values, a local-only one where it is present here."""
    path = evidence.REPO.path(entry["path"])
    if not path.exists():
        return None
    data = path.read_bytes()
    return json.loads((gzip.decompress(data) if path.name.endswith(".gz") else data).decode("utf-8"))


def frequency_rederived(record: Dict) -> Optional[bool]:
    held = output_values(record["raw_counts"])
    if held is None:
        return None
    return all([[min(row), max(row)] for row in rows] == record["summaries"][name][direction]
               for name, directions in held.items() for direction, rows in directions.items())


# ----------------------------------------------------------------------------- each kind's verdict

def check_demonstration(record: Dict, v: ModuleType) -> Dict:
    recovered = all(record["recovered"])
    if not recovered:
        return {"status": "fail", "classification": NONE}
    outcome = "recovered" if record["matches"]["agrees"] else "disagreement"
    return {"status": "pass", "classification": function(v, "classify")("demonstration", outcome)}


def check_validation(record: Dict, v: ModuleType) -> Dict:
    held = all(item["holds"] for item in record["assertions"])
    return {"status": "pass" if held else "fail", "outcome": "re-found" if held else "not re-found", "classification": NONE}


def check_cross_check(record: Dict, v: ModuleType) -> Dict:
    return {"status": v.verdict_cross_check(record["rows"]), "classification": NONE}


def check_inverse(record: Dict, v: ModuleType) -> Dict:
    status, outcome = v.verdict_inverse(record["mismatches"])
    return {"status": status, "classification": v.classify("inverse", outcome)}


def check_bijectivity(record: Dict, v: ModuleType) -> Dict:
    status, outcome = v.verdict_bijectivity(record["inputs"] if isinstance(record["inputs"], int) else 2 ** 32, record["ones"])
    return {"status": status, "classification": v.classify("bijectivity", outcome)}


def first_full(row: Dict) -> Optional[int]:
    """The first round count with no pair left, from the committed per-round counts."""
    for r, pairs in enumerate(row["pairs_without_dependency"]):
        if pairs == 0:
            return r + 1
    return None


def check_dependency(record: Dict, v: ModuleType) -> Dict:
    report = record["per_round"]
    status, outcome, incomplete = v.verdict_dependency(report)
    names = sorted(report)
    return {"status": status, "classification": v.classify("dependency", outcome), "incomplete_rounds": incomplete,
            "r_f": first_full(report[names[0]] if names[0].startswith("f") else report[names[1]]),
            "r_b": first_full(report[names[1]] if names[0].startswith("f") else report[names[0]])}


def check_frequency(record: Dict, v: ModuleType) -> Dict:
    low, high = record["test_parameters"]["critical"]
    fired = v.frequency_rounds_fired(record["summaries"], low, high)
    status, outcome, raises = v.verdict_bias(fired, record["config"]["rounds"])
    return {"status": status, "classification": v.classify("frequency", outcome), "rounds_fired": fired, "raises": raises}


def check_avalanche(record: Dict, v: ModuleType) -> Dict:
    parameters = record["test_parameters"]
    fired = v.avalanche_rounds_fired(record["paths"], tuple(parameters["critical_first"]), tuple(parameters["critical_whole"]))
    status, outcome, raises = v.verdict_bias(fired, record["config"]["rounds"])
    return {"status": status, "classification": v.classify("avalanche", outcome), "rounds_fired": fired, "raises": raises}


def check_control(record: Dict, v: ModuleType) -> Dict:
    parameters = record["test_parameters"]
    summaries = record["summaries"]
    if "critical" in parameters:
        fires = v.control_fired([summaries[name] for name in sorted(summaries)], [tuple(parameters["critical"])])
    else:
        fires = v.control_fired([summaries["first"], summaries["whole"]],
                                [tuple(parameters["critical_first"]), tuple(parameters["critical_whole"])])
    return {"status": "inconclusive" if fires else "pass", "classification": NONE, "fires": fires}


def check_symmetry(record: Dict, v: ModuleType) -> Dict:
    status, outcome = v.verdict_symmetry(record["fixed"], record["word_rotations"], record["composed"], record["relations"])
    return {"status": status, "classification": v.classify("symmetry", outcome)}


def check_invariant(record: Dict, v: ModuleType) -> Dict:
    status, outcome, fired = v.verdict_invariant(record["round_counts"], record["differences"])
    return {"status": status, "classification": v.classify("invariant", outcome), "rounds_fired": fired}


def check_degree(record: Dict, v: ModuleType) -> Dict:
    status, outcome, fired = v.verdict_degree(record)
    return {"status": status, "classification": v.classify("degree", outcome), "rounds_fired": fired}


def bound_value(record: Dict) -> str:
    """The bound from the record's own rows: a count in whole numbers, or a box's least weight as a rational."""
    rounds = record["rounds"]
    if record["method"] == "branch-and-bound":
        least = min(row["weights"][str(rounds)] for row in record["boxes"].values())
        weight = Fraction(2 * least if record["bound_kind"] == "linear" else least)
        return f"{int(weight * 65536)}/65536"
    count = record["counts"][str(rounds)]["count"]
    return str(count * record["weight_per_sbox"]) if record["method"] == "active-S-box count" else str(count)


def count_stands(row: Dict) -> bool:
    """A count stands where the status is infeasible with a limit of k - 1, or k is the sum of two shorter spans (research R12)."""
    return row.get("status") == 0 and ("sum_of" in row or row.get("below", {}).get("status") == 2)


def check_bound(record: Dict, v: ModuleType) -> Dict:
    if record.get("capped") is True:
        return {"status": "inconclusive", "classification": NONE, "bound": NONE}
    held = all(count_stands(row) for row in (record.get("counts") or {}).values())
    return {"status": "pass" if held else "fail", "bound": bound_value(record),
            "classification": v.classify("bound", "established") if held else NONE}


def check_trail(record: Dict, v: ModuleType) -> Dict:
    """The weight again from its rational, and the class from the tool: a trail that a validated tool found is a finding of the
    rounds it covers, and one from a tool not yet validated an unverified hypothesis, `blocked` until a validated tool or the
    validated exact models settle it (data-model sections 1, 5 and 6)."""
    found: Dict[str, Any] = {"weight_log2": function(v, "trail_weight_log2")(record["weight"])}
    validation = record.get("validation")
    if isinstance(validation, dict) and validation.get("record_id"):
        found["classification"] = v.classify("trail", "found")
    else:
        found.update(status="blocked", classification=v.classify("trail", "unvalidated"))
    return found


def check_rotation_ranking(record: Dict, v: ModuleType) -> Dict:
    """The ranking again from the record's own entries: each measure the smaller of its two weights, the higher measure first, a tie in
    the stated order of the assignments, and the amounts chosen its first entry (research R15)."""
    entries = record["entries"]
    measured = all(Fraction(str(entry["measure"])) == min(Fraction(str(entry["W_D"])), Fraction(str(entry["W_L"]))) for entry in entries)
    ranked = sorted(entries, key=lambda entry: (-Fraction(str(entry["measure"])), entry["assignment"]))
    return {"status": "pass" if measured and ranked == entries else "fail", "classification": NONE,
            "chosen": ranked[0]["assignment"] if ranked else NONE}


def check_generator_run(record: Dict, v: ModuleType) -> Dict:
    checks = record.get("checks") or {}
    held = all(checks.get(name, True) for name in ("relations_hold", "symmetry_holds")) and not checks.get("refused_matches")
    return {"status": "pass" if held else "fail", "classification": NONE}


def check_round_rule(record: Dict, v: ModuleType) -> Dict:
    """Each size's terms and R again, from the records that stood when this one was written."""
    candidate = record["candidate"]
    rules.until[0] = record["created_utc"]
    try:
        rows = {}
        for size, row in record["sizes"].items():
            r_f, r_b, _ = rules.r_f_and_b(candidate, int(size))
            r_bound, _ = rules.r_bound_of(candidate, int(size))
            r_dist, _ = rules.r_dist_of(candidate, int(size))
            rows[size] = {"R_f": r_f, "R_b": r_b, "R_bound": r_bound, "R_dist": r_dist, "R": rules.round_count(r_dist, r_bound, r_f, r_b)}
    finally:
        rules.until[0] = None
    stated = {size: {name: row[name] for name in ("R_f", "R_b", "R_bound", "R_dist", "R")} for size, row in record["sizes"].items()}
    return {"sizes": rows, "stated": stated}


def check_selection(record: Dict, v: ModuleType) -> Dict:
    """The rule over the record's own values: the smallest R at 4×4 among those it lists."""
    values = record["R_at_4x4"]
    if not values:
        return {"outcome": "stop"}
    least = min(values.values())
    tied = sorted(candidate for candidate, value in values.items() if value == least)
    return {"outcome": "tie", "tie": tied} if len(tied) > 1 else {"selected": tied[0]}


def check_d4_choice(record: Dict, v: ModuleType) -> Dict:
    """Each score and the family again, exactly, from the record's weights and LUTs."""
    rows = record["scored"]
    families = {entry["candidate_id"]: entry["family"] for entry in candidates.of_event(candidates.entries(), "proposed")}
    representatives = rules.representatives_of(rows, families)
    out: Dict[str, Any] = {"representatives": representatives}
    if record["outcome"] in ("chosen", "tie"):
        order = rules.higher(rules.weight_pair(rows[representatives["ARX"]]), rules.weight_pair(rows[representatives["Boolean"]]))
        out["outcome"] = "tie" if order == 0 else "chosen"
        out["chosen_family"] = NONE if order == 0 else "ARX" if order > 0 else "Boolean"
    for name, row in rows.items():
        out[f"score of {name}"] = str(min(Fraction(row["W_D"]), Fraction(row["W_L"])) / record["r_star"] / Fraction(row["luts"]))
    return out


CHECKS: Dict[str, Callable[[Dict, ModuleType], Dict]] = {
    "demonstration": check_demonstration, "validation": check_validation, "cross-check": check_cross_check, "inverse": check_inverse,
    "bijectivity": check_bijectivity, "dependency": check_dependency, "frequency": check_frequency, "avalanche": check_avalanche,
    "control": check_control, "symmetry": check_symmetry, "invariant": check_invariant, "degree": check_degree, "bound": check_bound,
    "trail": check_trail,
    "generator-run": check_generator_run, "round-rule": check_round_rule, "selection": check_selection, "d4-choice": check_d4_choice,
    "rotation-ranking": check_rotation_ranking}
NOT_READ_HERE = ("the operation-list items of eligibility, which `round_rule.py --reproduce` recomputes",)


def stated_value(record: Dict, found: Dict, name: str) -> Any:
    if name.startswith("score of "):
        return record["scored"][name[len("score of "):]]["score"]
    return found["stated"] if name == "sizes" else record.get(name)


def differences(record: Dict, found: Dict) -> List[Dict]:
    return [{"record_id": record["record_id"], "field": name, "recorded": stated_value(record, found, name), "recomputed": value}
            for name, value in found.items() if name != "stated" and stated_value(record, found, name) != value]


def cleared_by_the_lock_script(record: Dict) -> bool:
    return "scripts/clear_lock.py" in (record.get("code_sha256") or {})


def check_cleared(record: Dict) -> List[Dict]:
    """No saved output: its status, class and hours against the `lock-cleared` record that names it (data-model section 1)."""
    out = []
    if record.get("status") != "inconclusive" or record.get("classification") != NONE:
        out.append({"record_id": record["record_id"], "field": "status", "recorded": record.get("status"), "recomputed": "inconclusive"})
    named = [item for _, item in evidence.iter_records("lock-cleared", "locks")
             if isinstance(item.get("run_record"), dict) and item["run_record"].get("record_id") == record["record_id"]]
    if not named:
        return out + [{"record_id": record["record_id"], "field": "lock-cleared", "recorded": NONE, "recomputed": "a record that names it"}]
    used = evidence.run_hours_used(record) if record.get("kind") != "projection" else float(record.get("time_hours", 0.0))
    ended = record.get("ended_outside", NONE)
    stated = evidence.hours_between(named[0]["lock"]["time"], record["created_utc"] if ended == NONE else ended)
    if abs(used - stated) > 1e-9:
        out.append({"record_id": record["record_id"], "field": "hours", "recorded": used, "recomputed": stated})
    return out


def records_of(kind: str) -> List[Dict]:
    return [record for _, record in evidence.iter_records(kind, DIRECTORIES.get(kind, ""))]


def check_kind(kind: str, verdicts: Verdicts) -> Tuple[Dict, List[Dict]]:
    checked, rederived, found = 0, 0, []
    for record in records_of(kind):
        checked += 1
        if cleared_by_the_lock_script(record):
            found += check_cleared(record)
            continue
        if record.get("ended_outside", NONE) != NONE or record.get("status") == "not evaluated" or any(
                "aborted:" in text for text in record.get("limitations") or ()):
            continue
        commit = record.get("git_head")
        module = verdicts.at(commit) if commit else evidence
        found += differences(record, CHECKS[kind](record, module))
        if kind == "frequency":
            again = frequency_rederived(record)
            if again is not None:
                rederived += 1
                if not again:
                    found.append({"record_id": record["record_id"], "field": "summaries", "recorded": "committed", "recomputed": "differs"})
    return {"checked": checked, "rederived_from_outputs": rederived, "disagreements": len(found)}, found


def logs_checked() -> List[Dict]:
    """The protocol change log's digits, a `repair` entry's list and the inventory of replaced lists."""
    out = []
    try:
        evidence.guard_protocol_log("recheck")
    except Refused as exc:
        out.append({"record_id": "protocol log", "field": "entries", "recorded": "approved", "recomputed": str(exc)})
    for entry in candidates.entries():
        if entry.get("event") == "repair":
            evidence.guard_repair_list(entry)
    for digest, rel in candidates.superseded_inventory().items():
        path = evidence.REPO.path(rel)
        if not path.exists() or evidence.sha256(path.read_bytes()) != digest:
            out.append({"record_id": rel, "field": "superseded", "recorded": digest, "recomputed": "differs"})
    return out


def decisions_checked() -> Tuple[int, List[Dict]]:
    """Every decision and `replacement` state again (data-model section 3; ANA-088): a `rejected` or `ineligible` decision's cited
    record, by ID and SHA-256, shows its cause, and the entry it brought holds the state the rules' classification gives; an `eligible`
    one cites the candidate's round-rule record with every item met; a closing entry closes a pending one once, for a stated reason that
    the log and the records show. Each is read against the whole log, which only grows, and the candidate's rows, which no run charges
    after its closing decision."""
    log = candidates.entries()
    found: List[Dict] = []

    def disagree(entry: Dict, field: str, recorded: Any, recomputed: Any) -> None:
        found.append({"record_id": f"candidate log seq {entry['seq']}", "field": field, "recorded": recorded, "recomputed": recomputed})

    replacements = candidates.of_event(log, "replacement")
    brought = {entry["decision_seq"]: entry for entry in replacements if "decision_seq" in entry}
    decided = [entry for entry in candidates.of_event(log, "decision") if entry["decision"] in candidates.SHOWN_BY_THE_REASON + ("eligible",)]
    for entry in decided:
        candidate = entry["candidate_id"]
        try:
            record = candidates.cited_record(entry)
        except Refused as exc:
            disagree(entry, "record", entry.get("record"), str(exc))
            continue
        if entry["decision"] == "eligible":
            if record.get("kind") != "round-rule" or record.get("candidate") != candidate or candidates.failed_items(record):
                disagree(entry, "decision", "eligible", f"{record['record_id']} is no round-rule record of {candidate} with every item met")
            continue
        cause = entry.get("cause")
        if not candidates.shows_reason(candidate, cause, record, entry):
            disagree(entry, "cause", cause, f"{record['record_id']} does not show it")
            continue
        state = candidates.replacement_state(cause, entry, record)
        logged = brought.get(entry["seq"])
        held = None if logged is None else {name: logged[name] for name in ("state", "reason") if name in logged}
        if held != state:
            disagree(entry, "replacement", held, state)
    pending = {entry["seq"]: entry for entry in replacements if entry.get("state") == "pending"}
    closings = [entry for entry in replacements if "closes" in entry]
    closed: set = set()
    for entry in closings:
        target = pending.get(entry["closes"])
        try:
            if target is None or entry["closes"] in closed or target["candidate_id"] != entry["candidate_id"]:
                raise Refused(f"seq {entry['closes']} is no pending replacement entry of {entry['candidate_id']} that this entry alone closes")
            closed.add(entry["closes"])
            reason = entry.get("reason")
            if reason not in candidates.CLOSE_REASONS:
                raise Refused(f"the stated reasons are {candidates.CLOSE_REASONS}")
            if reason == candidates.FULL and len(candidates.proposed_ids(log, target["family"])) < candidates.MOST_PER_FAMILY:
                raise Refused(f"{target['family']} has fewer than {candidates.MOST_PER_FAMILY} candidates")
            if reason == candidates.BUDGET_SPENT:
                candidates.guard_budget_spent(entry, target)
            if reason == candidates.OWNER_DECLINED:
                candidates.guard_owner_word(entry, "a replacement closed for the owner's decline")
        except Refused as exc:
            disagree(entry, "reason", entry.get("reason"), str(exc))
    return len(decided) + len(closings), found


def run_checks(kinds: Tuple[str, ...]) -> Dict:
    verdicts = Verdicts()
    results, found = {}, logs_checked()
    decided, held = decisions_checked()
    found += held
    try:
        for kind in kinds:
            results[kind], held = check_kind(kind, verdicts)
            found += held
    finally:
        verdicts.close()
    for record in records_of("projection"):
        if cleared_by_the_lock_script(record):
            found += check_cleared(record)
    return {"results": results, "decisions_checked": decided, "disagreements": found, "not_read_here": list(NOT_READ_HERE)}


def own_environment() -> Dict:
    return {"interpreter": sys.version.split()[0], "platform": platform.platform(), "pip_freeze": evidence.pip_freeze()}


def recheck(args: argparse.Namespace, command: List[str]) -> int:
    kinds = (args.kind,) if args.kind else tuple(CHECKS)
    if args.kind and args.kind not in CHECKS:
        raise Refused(f"no kind {args.kind!r}: {tuple(CHECKS)}")
    environment = own_environment()
    fields = run_checks(kinds)
    if args.no_record:
        # Feature 005, FR-003: the result printed, nothing written.
        found = fields["disagreements"]
        print(json.dumps({"results": fields["results"], "decisions_checked": fields["decisions_checked"],
                          "disagreements": found}, sort_keys=True, ensure_ascii=False))
        print(f"no record written: {sum(row['checked'] for row in fields['results'].values())} records, "
              f"{len(found)} disagreements")
        return evidence.EXIT_VERDICT if found else evidence.EXIT_OK
    run = evidence.Run("recheck", code_files=CODE, argv=command, environment=environment)
    with run:
        found = fields["disagreements"]
        path = run.finish("blocked" if found else "pass", classification=evidence.classify("recheck", "disagreement") if found else NONE,
                          exit_status=evidence.EXIT_VERDICT if found else evidence.EXIT_OK, fields=dict(fields, environment_of_the_run=environment))
    print(f"{evidence.rel_to_repo(path)}: {sum(row['checked'] for row in fields['results'].values())} records, {len(found)} disagreements")
    return evidence.EXIT_VERDICT if found else evidence.EXIT_OK


def again_here(text: str, out: str) -> None:
    """The run of a reproduction, in its worktree."""
    original = json.loads(text)
    fields = run_checks(tuple(original["results"]))
    Path(out).write_bytes(evidence.pretty(dict(fields, kind="recheck", inputs=NONE, model_id=None, variant_id=None, exit_status=original["exit_status"],
                                               assertions=[], status=original["status"], classification=original["classification"], outputs=[])))


def reproduce(args: argparse.Namespace, command: List[str]) -> int:
    path = Path(args.reproduce)
    path = path if path.is_absolute() else evidence.REPO.path(args.reproduce)
    if not path.exists():
        raise Refused(f"{args.reproduce} does not exist")
    original = json.loads(path.read_bytes().decode("utf-8"))
    if original.get("kind") != "recheck":
        raise Refused(f"{args.reproduce} is no recheck record")

    def run(place: evidence.Place) -> Dict:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "fields.json"
            done = subprocess.run([sys.executable, "-X", "utf8", "-c", RUN_HERE, "again_here", json.dumps(original), str(out)],
                                  cwd=place.worktree, capture_output=True, text=True, encoding="utf-8", errors="replace")
            if done.returncode != 0:
                raise ToolFailure(f"the run exited {done.returncode}: {done.stderr.strip()[-400:]}")
            return dict(json.loads(out.read_bytes().decode("utf-8")), code_sha256=original["code_sha256"])

    return evidence.reproduce(evidence.Reproduction(record_path=path, run=run, recheck=own_environment(), code_files=CODE, argv=command,
                                                    extra=("results", "disagreements")))


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--kind")
    parser.add_argument("--reproduce")
    parser.add_argument("--no-record", action="store_true", help="print the result and write nothing")
    args = parser.parse_args(argv)
    command = [SCRIPT] + list(sys.argv[1:] if argv is None else argv)

    def body() -> int:
        return reproduce(args, command) if args.reproduce else recheck(args, command)

    return evidence.main_guard(body)


if __name__ == "__main__":
    raise SystemExit(main())
