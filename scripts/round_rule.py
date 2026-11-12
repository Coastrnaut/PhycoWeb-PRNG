#!/usr/bin/env python3
"""Feature 004: the round rule, eligibility and selection (spec "Pre-registered Design Protocol"; data-model section 9).

    round_rule.py --candidate ID           writes candidates/<ID>/round-rule.json
    round_rule.py --close                  writes the candidate log's set-closed entry
    round_rule.py --select                 writes freeze/selection.json, later selection-<k>.json
    round_rule.py --decide                 appends the latest selection record's decision entries
    round_rule.py --choose ID --seen SHA256 --by NAME [--written-approval WORDS]
    round_rule.py --reproduce RECORD

R = max(2·R_dist, R_bound + 2, 2·max(R_f, R_b)) per claimable size, every input cited by record ID. A record that holds `ended_outside`
decides nothing. --select applies eligibility, the fallback to the other family and the stop rule, and exits 1 for a stop. A choice
in a tie is the owner's own act, which the agent performs only on the owner's written approval.

This script makes no security claim.
"""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[1]
for place in (str(ROOT), str(ROOT / "scripts"), str(ROOT / "research/004"), str(ROOT / "research/004/tools")):
    if place not in sys.path:
        sys.path.insert(0, place)

from protocol import candidates, evidence  # noqa: E402
from protocol.evidence import NONE, Refused, ToolFailure  # noqa: E402
from protocol.rules import (CALLS_BEFORE_OUTPUT, CONTROLLED, DELTA, TARGET_WEIGHT, WIDTH, bias_item, bound_weights, control_of,  # noqa: E402,F401
                            diffusion_item, item, latest, pairs_and_avalanche, passed, r_bound_of, r_dist_of, r_f_and_b, records_at,
                            round_count, row_met, structural_items, unresolved)

import d4_choice  # noqa: E402
import ir  # noqa: E402

SCRIPT = "scripts/round_rule.py"
CODE = [SCRIPT, "scripts/d4_choice.py", "protocol/evidence.py", "protocol/disclaimer.py", "protocol/devinputs_v3.py", "protocol/candidates.py",
        "protocol/rules.py", "research/004/ir.py", "research/004/tools/costmodel.py"]
SIZES = evidence.CLAIMABLE_SIZES
FREEZE = "freeze"
FIRST_SELECTION = "selection.json"
RUN_HERE = """
import importlib.util, sys
spec = importlib.util.spec_from_file_location("round_rule", "scripts/round_rule.py")
module = importlib.util.module_from_spec(spec)
sys.modules["round_rule"] = module
spec.loader.exec_module(module)
getattr(module, sys.argv[1])(*sys.argv[2:])
"""


def parameters_of(candidate: str) -> Dict:
    return candidates.of_event(candidates.entries(), "proposed", candidate)[0]["parameters"]


def declarations_of(candidate: str, n: int) -> Optional[Dict]:
    """The operation list's own declarations, which FR-025 and FR-027 read: stages, chains per phase, key path and semantics."""
    ir.candidate_modules(evidence.REPO.path(candidates.CANDIDATES_REL))
    module = sys.modules[candidate.replace("-", "_")]
    declared = getattr(module, "declarations", None)
    return None if declared is None else declared(n, WIDTH)


# ----------------------------------------------------------------------------------- eligibility

def stages_item(declared: Optional[Dict], candidate: str, size: int) -> Dict:
    """Each stage holds at most one serial carry chain, by the phase rule, read from the list and set against its declaration."""
    if declared is None or "stages" not in declared:
        return item(False, why="no declaration of its stages")
    import costmodel
    builds = ir.candidate_modules(evidence.REPO.path(candidates.CANDIDATES_REL))
    counted = costmodel.count(ir.load(builds[candidate](size, WIDTH)), 1, 1)
    stated = declared["stages"]
    held = stated.get("phases") == counted["phases"] and stated.get("chains_per_phase") == counted["chains_per_phase"] \
        and all(chains <= 1 for chains in counted["chains_per_phase"])
    return item(held, {"phases": counted["phases"], "chains_per_phase": counted["chains_per_phase"]})


def key_path_item(declared: Optional[Dict], size: int) -> Dict:
    """A registered shift chain through the nodes that hold key bits, each step between direct neighbours (FR-025)."""
    if declared is None or "key_path" not in declared:
        return item(False, why="no declaration of its key path")
    chain = [tuple(node) for node in declared["key_path"]]
    holding = {ir.node_of(size, lane) for lane in range(256 // WIDTH)}
    joined = all(second in ir.neighbours(size, *first) for first, second in zip(chain, chain[1:]))
    return item(holding <= set(chain) and joined, {"nodes": [list(node) for node in chain]})


def semantics_item(declared: Optional[Dict]) -> Dict:
    """FR-027's width, signedness, wrap rule, shift kind and rotation direction, for every operation the list uses."""
    wanted = ("width", "signedness", "wrap", "shift", "rotation")
    held = declared is not None and all(name in declared.get("semantics", {}) for name in wanted)
    return item(held, why=NONE if held else "the list's semantics are not declared")


def ranking_item(candidate: str) -> Dict:
    log = candidates.entries()
    held = [entry for entry in candidates.of_event(log, "correction", candidate) if entry.get("ranking_after_scaling")]
    return item(bool(held), *[entry["seq"] for entry in held], why=NONE if held else "no report on the ranking after scaling")


def eligible_items(candidate: str, size: int, row: Dict) -> Dict[str, Dict]:
    rounds, parameters = row["R"], parameters_of(candidate)
    declared = declarations_of(candidate, size)
    trees = parameters.get("trees", {})
    cost = records_at(candidate, "cost", size)
    cost_at_r = [record for record in cost if record["config"]["rounds"] == rounds]
    log = candidates.entries()
    mapped = candidates.of_event(log, "mapping", candidate)
    instance = parameters.get("constant_instance", {})
    out = structural_items(candidate, size, rounds)
    out.update({
        "R_dist, R_f, R_b and R_bound established": item(rounds is not None and row["R_dist"] is not None, row["R_bound_records"]),
        "FR-018 folding rule": item(bool(parameters.get("folding_rule"))),
        "FR-018 longest link": item(str(size) in parameters.get("longest_link", {})),
        "FR-018 food nodes": item(bool(parameters.get("food_nodes", {}).get("reason"))),
        "FR-018 trees": item(str(size) in trees),
        "FR-020 cycles per call": item(bool(cost_at_r), *[record["record_id"] for record in cost_at_r]),
        "FR-022 bounds": item(row["R_bound"] is not None, *row["R_bound_records"]),
        "FR-023 streams": item(bool(instance.get("reason") or instance.get("distinct_streams_reason"))),
        "FR-024 ranking after scaling": ranking_item(candidate),
        "FR-025 stages": stages_item(declared, candidate, size),
        "FR-025 key path": key_path_item(declared, size),
        "FR-026 figures": item(bool(cost_at_r), *[record["record_id"] for record in cost_at_r]),
        "FR-027 semantics": semantics_item(declared),
        "FR-029 through instantiate": diffusion_item(candidate, size, rounds),
        "FR-030 mapping": item(bool(mapped), *[entry["seq"] for entry in mapped]),
        "frequency": bias_item(candidate, "frequency", size, rounds),
        "avalanche": bias_item(candidate, "avalanche", size, rounds)})
    blocked = unresolved(candidate)
    out["no unresolved finding"] = item(not blocked, *blocked)
    return out


def size_row(candidate: str, size: int, previous: Optional[Dict]) -> Dict:
    r_f, r_b, dependency_records = r_f_and_b(candidate, size)
    r_bound, bound_records = r_bound_of(candidate, size)
    r_dist, sources = r_dist_of(candidate, size)
    rounds = round_count(r_dist, r_bound, r_f, r_b)
    rises = list((previous or {}).get("rises", []))
    before = (previous or {}).get("R")
    if rounds is not None and before is not None and rounds > before:
        rises.append({"from": before, "to": rounds, "cause": [item_ for item_ in sources if 2 * item_["rounds"] == rounds] or "the bound or the matrices"})
    row = {"R_f": r_f, "R_b": r_b, "R_f_records": dependency_records, "R_bound": r_bound, "R_bound_records": bound_records, "R_dist": r_dist,
           "R_dist_sources": sources, "delta": DELTA, "R": rounds, "rises": rises}
    row["eligible"] = eligible_items(candidate, size, row)
    return row


def round_rule_path(candidate: str) -> Path:
    return evidence.REPO.rep / "candidates" / candidate / "round-rule.json"


def read_round_rule(candidate: str) -> Optional[Dict]:
    path = round_rule_path(candidate)
    return json.loads(path.read_bytes().decode("utf-8")) if path.exists() else None


def fields_of(candidate: str, previous: Optional[Dict]) -> Dict:
    sizes = {str(size): size_row(candidate, size, (previous or {}).get("sizes", {}).get(str(size))) for size in SIZES}
    pairs, sizes_run = pairs_and_avalanche(candidate)
    return {"candidate": candidate, "sizes": sizes, "pairs_tested": pairs, "false_firing_rate": evidence.false_firing_chance(pairs, sizes_run)}


def write_round_rule(args: argparse.Namespace, command: List[str]) -> int:
    candidate = args.candidate
    if not candidates.of_event(candidates.entries(), "proposed", candidate):
        raise Refused(f"{candidate} is not in the candidate log")
    fields = fields_of(candidate, read_round_rule(candidate))
    run = evidence.Run("round-rule", candidate=candidate, model_id=candidate, directory=f"candidates/{candidate}", file_name="round-rule.json",
                       fixed=True, code_files=CODE + [candidates.module_rel(candidate)], argv=command)
    with run:
        path = run.finish("pass", fields=fields)
    print(f"{evidence.rel_to_repo(path)}: R = {[row['R'] for row in fields['sizes'].values()]}")
    return evidence.EXIT_OK


# -------------------------------------------------------------------------- closing and selecting

def set_candidates(log: Sequence[Dict]) -> List[str]:
    return sorted({entry["candidate_id"] for entry in candidates.of_event(log, "proposed")})


def has_final_decision(log: Sequence[Dict], candidate: str) -> bool:
    if set(candidates.decisions(log, candidate)) & set(evidence.CLOSING_DECISIONS):
        return True
    record = read_round_rule(candidate)
    return record is not None and all(row["R"] is not None for row in record["sizes"].values())


def close(command: List[str]) -> int:
    log = candidates.entries()
    waiting = [candidate for candidate in set_candidates(log) if not has_final_decision(log, candidate)]
    if waiting:
        raise Refused(f"no final decision yet: {waiting}")
    if candidates.pending_replacements(log):
        raise Refused("a replacement entry is pending")
    candidates.append({"event": "set-closed", "candidates": set_candidates(log)})
    print(f"{candidates.LOG}: set-closed")
    return evidence.EXIT_OK


def selection_files() -> List[Path]:
    base = evidence.REPO.rep / FREEZE
    found = [path for path in base.glob("selection*.json") if "tie-choice" not in path.name] if base.exists() else []

    def number(path: Path) -> int:
        return 1 if path.name == FIRST_SELECTION else int(path.stem.split("-")[1])

    return sorted(found, key=number)


def chosen_family() -> Tuple[Optional[str], str]:
    """The family the D4 records give: chosen, by default, by a tie's records, or none where D4 was not computable."""
    choice = d4_choice.read_choice()
    if choice["outcome"] == "not computable":
        return None, "not computable"
    if choice["outcome"] != "tie":
        return choice["chosen_family"], choice["outcome"]
    tie_path = evidence.REPO.rep / d4_choice.DIRECTORY / d4_choice.TIE
    if not tie_path.exists():
        raise Refused("the D4 tie has no record")
    tie = json.loads(tie_path.read_bytes().decode("utf-8"))
    row = evidence.family_row(d4_choice.ROW)
    if row is None:
        raise Refused("the row \"D4 tie\" does not exist at HEAD")
    if tie["decided_by"] != "owner":
        if row.decision != "Not needed":
            raise Refused("the row \"D4 tie\" does not read Not needed at HEAD")
        return tie["chosen_family"], tie["decided_by"]
    made = evidence.REPO.rep / d4_choice.DIRECTORY / d4_choice.TIE_CHOICE
    if row.decision != "Approved" or not made.exists() or evidence.sha256(made.read_bytes()) not in row.notes:
        raise Refused("the row \"D4 tie\" does not read Approved at HEAD with the choice's SHA-256")
    held = json.loads(made.read_bytes().decode("utf-8"))["choice"]
    return candidates.of_event(candidates.entries(), "proposed", held)[0]["family"], "owner"


def selection_fields(log: Sequence[Dict]) -> Dict:
    family, by = chosen_family()
    families = {entry["candidate_id"]: entry["family"] for entry in candidates.of_event(log, "proposed")}
    rows = {candidate: read_round_rule(candidate) for candidate in sorted(families)}
    closed = {candidate for candidate in families if set(candidates.decisions(log, candidate)) & set(evidence.CLOSING_DECISIONS)}
    eligible = sorted(candidate for candidate, record in rows.items() if candidate not in closed and row_met(record))
    chosen = [candidate for candidate in eligible if family is None or families[candidate] == family]
    fallback = False
    if not chosen and family is not None:
        chosen, fallback = [candidate for candidate in eligible if families[candidate] != family], True
    r_values = {candidate: rows[candidate]["sizes"]["4"]["R"] for candidate in chosen}
    declined = [entry.get("declined") for entry in candidates.of_event(log, "review-outcome") if entry.get("outcome") == "declined"]
    fields: Dict[str, Any] = {"family": family or NONE, "family_by": by, "fallback": fallback, "eligible": chosen,
                              "R_at_4x4": r_values, "tie": [], "selected": NONE}
    if not chosen:
        return dict(fields, outcome="stop", reason="none of the evaluated candidates is eligible")
    least = min(r_values.values())
    tied = sorted(candidate for candidate, value in r_values.items() if value == least)
    if len(tied) > 1:
        return dict(fields, outcome="tie", tie=tied)
    if tied[0] in declined:
        return dict(fields, outcome="stop", reason="the rules select the declined candidate again")
    return dict(fields, outcome="selected", selected=tied[0])


def select(command: List[str]) -> int:
    log = candidates.entries()
    if not candidates.of_event(log, "set-closed"):
        raise Refused("selection runs after the set-closed entry")
    open_findings = [item_ for candidate in set_candidates(log) for item_ in unresolved(candidate)]
    if open_findings:
        raise Refused(f"unresolved disagreements: {open_findings}")
    fields = selection_fields(log)
    files = selection_files()
    name = FIRST_SELECTION if not files else f"selection-{len(files) + 1}.json"
    if files:
        fields["previous"] = {"path": evidence.rel_to_repo(files[-1]), "sha256": evidence.sha256(files[-1].read_bytes()), "sha256_kind": "raw"}
    run = evidence.Run("selection", directory=FREEZE, file_name=name, code_files=CODE, argv=command)
    with run:
        path = run.finish("pass" if fields["outcome"] != "stop" else "fail", fields=fields,
                          exit_status=evidence.EXIT_VERDICT if fields["outcome"] == "stop" else evidence.EXIT_OK)
    print(f"{evidence.rel_to_repo(path)}: {fields['outcome']}")
    return evidence.EXIT_VERDICT if fields["outcome"] == "stop" else evidence.EXIT_OK


def latest_selection() -> Tuple[Path, Dict]:
    files = selection_files()
    if not files:
        raise Refused("no selection record exists")
    return files[-1], json.loads(files[-1].read_bytes().decode("utf-8"))


def choice_name(selection: Path) -> str:
    return selection.stem + "-tie-choice.json"


def tie_row_name(selection: Path) -> str:
    return "Selection tie" if selection.name == FIRST_SELECTION else f"Selection tie {selection.stem.split('-')[1]}"


def variant_map(candidate: str) -> Dict[str, str]:
    record = read_round_rule(candidate)
    return {f"{candidate}/n{size}-w{WIDTH}-R{record['sizes'][str(size)]['R']}-c384":
            f"{evidence.MODEL_ID}/n{size}-w{WIDTH}-R{record['sizes'][str(size)]['R']}-c384"
            for size in SIZES}


def decide(command: List[str]) -> int:
    path, record = latest_selection()
    if record["outcome"] == "stop":
        raise Refused("the record's outcome is a stop")
    log = candidates.entries()
    cited = {"path": evidence.rel_to_repo(path), "sha256": evidence.sha256(path.read_bytes()), "sha256_kind": "raw"}
    if any((entry.get("selection") or {}).get("sha256") == cited["sha256"] for entry in candidates.of_event(log, "decision")):
        raise Refused("the record has its entries")
    selected = record["selected"]
    tie_choice: Any = NONE
    if record["outcome"] == "tie":
        made = path.parent / choice_name(path)
        row = evidence.family_row(tie_row_name(path))
        if not made.exists() or row is None or row.decision != "Approved" or evidence.sha256(made.read_bytes()) not in row.notes:
            raise Refused(f"the tie has no choice whose row {tie_row_name(path)} reads Approved at HEAD")
        selected = json.loads(made.read_bytes().decode("utf-8"))["choice"]
        tie_choice = {"path": evidence.rel_to_repo(made), "sha256": evidence.sha256(made.read_bytes()), "sha256_kind": "raw"}
    families = {entry["candidate_id"]: entry for entry in candidates.of_event(log, "proposed")}
    digest = evidence.sha256(evidence.REPO.path(candidates.module_rel(selected)).read_bytes())
    candidates.append({"candidate_id": selected, "family": families[selected]["family"], "event": "decision", "decision": "selected",
                       "reason": "the rule selects it", "selection": cited, "tie_choice": tie_choice, "variant_map": variant_map(selected),
                       "oplist_sha256": digest})
    for candidate in record["eligible"]:
        if candidate != selected:
            candidates.append({"candidate_id": candidate, "family": families[candidate]["family"], "event": "decision",
                               "decision": "not selected", "reason": "the rule selects another", "selection": cited, "tie_choice": tie_choice})
    print(f"{candidates.LOG}: {selected} selected")
    return evidence.EXIT_OK


def write_owner_choice(args: argparse.Namespace, command: List[str]) -> int:
    """The owner's act: nothing is written unless the owner's digits, or the owner's written approval, confirm the record seen."""
    path, record = latest_selection()
    if record["outcome"] != "tie":
        raise Refused("the record has no tie")
    name = choice_name(path)
    if (path.parent / name).exists():
        raise Refused("a choice for it exists, and it never changes")
    if args.choose not in record["tie"]:
        raise Refused(f"{args.choose} is not in the tie")
    digest = evidence.sha256(path.read_bytes())
    if args.seen != digest:
        raise Refused(f"the hash seen differs from the record's, {digest}")
    written = evidence.written_approval(args.written_approval) if args.written_approval else None
    run = evidence.Run("selection-tie-choice", directory=FREEZE, file_name=name, code_files=CODE, argv=command, analyst=args.by)
    with run:
        digits = evidence.approval_step(digest, written)
        fields = {"choice": args.choose, "who": args.by, "when": evidence.utc_now(), "seen_sha256": digest, "choice_confirmed": digits}
        if written is not None:
            fields["written_approval"] = written
        made = run.finish("pass", fields=fields)
    print(f"{evidence.rel_to_repo(made)}: {args.choose}")
    return evidence.EXIT_OK


# --------------------------------------------------------------------------------------- --reproduce

def recompute(text: str, out: str) -> None:
    """The run of a reproduction, in its worktree: everything is read from that commit."""
    original = json.loads(text)
    if original["kind"] == "round-rule":
        previous = None
        if original.get("previous_sha256", NONE) != NONE:
            kept = round_rule_path(original["candidate"]).parent / "versions" / f"{original['previous_sha256']}.json"
            previous = json.loads(kept.read_bytes().decode("utf-8"))
        fields = fields_of(original["candidate"], previous)
    else:
        fields = selection_fields(candidates.entries())
    status = original["status"]
    Path(out).write_bytes(evidence.pretty(dict(fields, kind=original["kind"], inputs=original.get("inputs", NONE), model_id=original.get("model_id"),
                                               variant_id=None, exit_status=original["exit_status"], assertions=[], status=status,
                                               classification=NONE, outputs=[])))


def reproduce(args: argparse.Namespace, command: List[str]) -> int:
    path = Path(args.reproduce)
    path = path if path.is_absolute() else evidence.REPO.path(args.reproduce)
    if not path.exists():
        raise Refused(f"{args.reproduce} does not exist")
    original = json.loads(path.read_bytes().decode("utf-8"))
    if original.get("kind") not in ("round-rule", "selection"):
        raise Refused(f"{args.reproduce} is no record that this script computes")

    def run(place: evidence.Place) -> Dict:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "fields.json"
            done = subprocess.run([sys.executable, "-X", "utf8", "-c", RUN_HERE, "recompute", json.dumps(original), str(out)],
                                  cwd=place.worktree, capture_output=True, text=True, encoding="utf-8", errors="replace")
            if done.returncode != 0:
                raise ToolFailure(f"the run exited {done.returncode}: {done.stderr.strip()[-400:]}")
            return dict(json.loads(out.read_bytes().decode("utf-8")), code_sha256=original["code_sha256"])

    names = ("candidate", "sizes", "pairs_tested", "false_firing_rate", "family", "family_by", "fallback", "eligible", "R_at_4x4", "tie", "selected",
             "outcome", "reason")
    return evidence.reproduce(evidence.Reproduction(record_path=path, run=run, code_files=CODE, argv=command,
                                                    extra=tuple(name for name in names if name in original)))


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--candidate")
    parser.add_argument("--close", action="store_true")
    parser.add_argument("--select", action="store_true")
    parser.add_argument("--decide", action="store_true")
    parser.add_argument("--choose")
    parser.add_argument("--seen")
    parser.add_argument("--by")
    parser.add_argument("--written-approval")
    parser.add_argument("--reproduce")
    args = parser.parse_args(argv)
    command = [SCRIPT] + list(sys.argv[1:] if argv is None else argv)

    def body() -> int:
        if args.reproduce:
            return reproduce(args, command)
        if args.choose:
            if not args.seen or not args.by:
                raise Refused("--choose takes --seen SHA256 --by NAME")
            return write_owner_choice(args, command)
        if args.close:
            return close(command)
        if args.select:
            return select(command)
        if args.decide:
            return decide(command)
        if not args.candidate:
            raise Refused("a run names --candidate, --close, --select, --decide, --choose or --reproduce")
        return write_round_rule(args, command)

    return evidence.main_guard(body)


if __name__ == "__main__":
    raise SystemExit(main())
