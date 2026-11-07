#!/usr/bin/env python3
"""Feature 004: the choice between the families (spec "Nonlinearity choice rule"; research R5, R6; data-model section 8).

    d4_choice.py --log research/004/candidates.jsonl --out $REP/d4/choice.json
    d4_choice.py --tie --log research/004/candidates.jsonl --out $REP/d4/tie.json
    d4_choice.py --choose ID --seen SHA256 --by NAME --out $REP/d4/tie-choice.json [--written-approval WORDS]
    d4_choice.py --reproduce RECORD [--owner-request "WORDS (DATE)"]

The score is (min(W_D, W_L) / r*) / L, compared exactly, over the entered set, at 4×4 and at the widest reduced width, 16 or else 8,
with a common r* of at least 2. Only bound records of a tool that has passed its cross-check on that candidate count. A choice is
written once, and a tie's owner's choice is the owner's own act, which the agent performs only on the owner's written approval.

This script makes no security claim.
"""
import argparse
import json
import subprocess
import sys
import tempfile
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[1]
for place in (str(ROOT), str(ROOT / "research/004"), str(ROOT / "research/004/tools")):
    if place not in sys.path:
        sys.path.insert(0, place)

from protocol import candidates, evidence  # noqa: E402
from protocol.evidence import NONE, Refused, ToolFailure  # noqa: E402
from protocol.rules import (FAMILIES, KINDS, LEAST_ROUNDS, METHODS, SIZE, WIDTHS, bounds_of, climb_end, climbs_owed,  # noqa: E402,F401
                            cross_checked, decide, family_rounds, higher, locate, outcome_of, representatives_of, rounds_with_both,
                            scored_rows, weight_at, weight_pair)

import costmodel  # noqa: E402
import ir  # noqa: E402

SCRIPT = "scripts/d4_choice.py"
CODE = [SCRIPT, "protocol/evidence.py", "protocol/disclaimer.py", "protocol/devinputs_v3.py", "protocol/candidates.py", "protocol/rules.py",
        "research/004/ir.py", "research/004/tools/costmodel.py"]
DIRECTORY = "d4"
CHOICE, TIE, TIE_CHOICE = "choice.json", "tie.json", "tie-choice.json"
R_STAR_STATEMENT = "r* compares the candidates over the same rounds and is not a rate per round"
ROW = "D4 tie"
RUN_HERE = """
import importlib.util, sys
spec = importlib.util.spec_from_file_location("d4_choice", "scripts/d4_choice.py")
module = importlib.util.module_from_spec(spec)
sys.modules["d4_choice"] = module
spec.loader.exec_module(module)
getattr(module, sys.argv[1])(*sys.argv[2:])
"""


# ----------------------------------------------------------------------------------- the choice

def entered_set() -> Tuple[Dict[str, int], Dict[str, str], List[Dict]]:
    log = candidates.entries()
    entered = {entry["candidate_id"]: entry["seq"] for entry in candidates.of_event(log, "entered-d4")}
    if not entered:
        raise Refused("no entered set is recorded")
    families = {entry["candidate_id"]: entry["family"] for entry in candidates.of_event(log, "proposed")}
    return entered, families, log


def lists_at(entered: Sequence[str]) -> Dict[int, Dict[str, Fraction]]:
    builds = ir.candidate_modules(evidence.REPO.path(candidates.CANDIDATES_REL))
    return {width: {candidate: costmodel.count(ir.load(builds[candidate](SIZE, width)), 1, 1)["luts"] for candidate in entered}
            for width in WIDTHS}


def measured(entered: Sequence[str], log: Sequence[Dict]) -> Tuple[Dict, Dict]:
    by_width = {width: {candidate: bounds_of(candidate, width) for candidate in entered} for width in WIDTHS}
    outcomes = {candidate: {str(width): {kind: outcome_of(candidate, width, kind, candidates.decisions(log, candidate))
                                         for kind in KINDS} for width in WIDTHS} for candidate in entered}
    return by_width, outcomes


def guard_outcomes(outcomes: Dict, needed: Sequence[int]) -> None:
    missing = [f"{candidate} at {width}, {kind}" for candidate, widths in outcomes.items() for width in needed
               for kind, outcome in widths[str(width)].items() if outcome is None]
    if missing:
        raise Refused("no final reduced-width outcome yet: " + ", ".join(missing))


def guard_climbs(entered: Sequence[str], families: Dict[str, str], log: Sequence[Dict], width: Any) -> None:
    """An outcome is final only once the candidate's climb has ended or has reached the last r it could share (research R6)."""
    closed = [candidate for candidate in entered if {"ineligible", "rejected"} & set(candidates.decisions(log, candidate))]
    owed = []
    for at in ((16,) if width == 16 else WIDTHS):
        tables = {candidate: bounds_of(candidate, at) for candidate in entered}
        ends = {candidate: climb_end(candidate, at) for candidate in entered}
        owed += [f"at w = {at}, {item}" for item in climbs_owed(tables, ends, families, closed)]
    if owed:
        raise Refused("no final reduced-width outcome yet: " + "; ".join(owed))


def fields_of(entered: Dict[str, int], families: Dict[str, str], log: Sequence[Dict]) -> Dict:
    by_width, outcomes = measured(sorted(entered), log)
    guard_outcomes(outcomes, (16,))
    fields = decide(by_width, families, lists_at(sorted(entered)))
    if fields["width"] != 16:
        guard_outcomes(outcomes, WIDTHS)
    records = sorted({record for row in fields["scored"].values() for record in row["bound_records"].values()})
    fields.update(entered=entered, outcomes=outcomes, bound_records=records, r_star_statement=R_STAR_STATEMENT, tie_breaks_applied=[])
    return fields


def choice_path() -> Path:
    return evidence.REPO.rep / DIRECTORY / CHOICE


def write_choice(command: List[str]) -> int:
    if choice_path().exists():
        raise Refused(f"{DIRECTORY}/{CHOICE} exists, and it is written once")
    entered, families, log = entered_set()
    fields = fields_of(entered, families, log)
    guard_climbs(sorted(entered), families, log, fields["width"])
    run = evidence.Run("d4-choice", directory=DIRECTORY, file_name=CHOICE, code_files=CODE, argv=command)
    with run:
        path = run.finish("pass", fields=fields)
    cited = {"path": evidence.rel_to_repo(path), "sha256": evidence.sha256(path.read_bytes()), "sha256_kind": "raw"}
    for candidate in sorted(fields["scored"]):
        candidates.append({"candidate_id": candidate, "family": families[candidate], "event": "scored", "record": cited})
    print(f"{evidence.rel_to_repo(path)}: {fields['outcome']}, {fields['chosen_family']}")
    return evidence.EXIT_OK


# -------------------------------------------------------------------------------------- the tie

def read_choice() -> Dict:
    if not choice_path().exists():
        raise Refused("no choice record exists")
    return json.loads(choice_path().read_bytes().decode("utf-8"))


def size_r(candidate: str) -> Optional[int]:
    path = evidence.REPO.rep / "candidates" / candidate / "round-rule.json"
    if not path.exists():
        return None
    row = json.loads(path.read_bytes().decode("utf-8")).get("sizes", {}).get(str(SIZE))
    return None if row is None else row.get("R")


def carry_chains(candidate: str, width: int) -> int:
    builds = ir.candidate_modules(evidence.REPO.path(candidates.CANDIDATES_REL))
    return costmodel.chains_per_round(builds[candidate](SIZE, width))


def tie_breaks(choice: Dict, log: Sequence[Dict]) -> Dict:
    """The spec's tie-breaks in order: a representative found ineligible loses, then the smaller R at 4×4, then fewer serial carry
    chains per round, and then the owner's recorded choice."""
    first, second = choice["representatives"]["ARX"], choice["representatives"]["Boolean"]
    pair = (first, second)
    families = {first: "ARX", second: "Boolean"}
    out = {candidate: candidates.decisions(log, candidate) for candidate in pair}
    closed = [candidate for candidate in pair if set(out[candidate]) & set(evidence.CLOSING_DECISIONS)]
    if len(closed) == 1:
        winner = second if closed[0] == first else first
        return {"decided_by": "ineligible", "chosen_family": families[winner], "ineligible": closed[0], "R_at_4x4": NONE}
    values = {candidate: size_r(candidate) for candidate in pair}
    if any(value is None for value in values.values()):
        raise Refused("the tie waits for R at 4×4 of both representatives")
    fields = {"R_at_4x4": values}
    if values[first] != values[second]:
        winner = min(pair, key=lambda candidate: values[candidate])
        return dict(fields, decided_by="R at 4×4", chosen_family=families[winner])
    chains = {candidate: carry_chains(candidate, choice["width"]) for candidate in pair}
    fields["carry_chains"] = chains
    if chains[first] != chains[second]:
        winner = min(pair, key=lambda candidate: chains[candidate])
        return dict(fields, decided_by="carry chains", chosen_family=families[winner])
    return dict(fields, decided_by="owner", chosen_family=NONE)


def write_tie(command: List[str]) -> int:
    choice = read_choice()
    if choice["outcome"] != "tie":
        raise Refused("the choice record holds no tie")
    if (evidence.REPO.rep / DIRECTORY / TIE).exists():
        raise Refused(f"{DIRECTORY}/{TIE} exists, and it is written once")
    fields = tie_breaks(choice, candidates.entries())
    fields["choice"] = {"path": evidence.rel_to_repo(choice_path()), "sha256": evidence.sha256(choice_path().read_bytes()),
                        "sha256_kind": "raw"}
    run = evidence.Run("d4-tie", directory=DIRECTORY, file_name=TIE, code_files=CODE, argv=command)
    with run:
        path = run.finish("pass", fields=fields)
    print(f"{evidence.rel_to_repo(path)}: decided by {fields['decided_by']}")
    return evidence.EXIT_OK


def write_owner_choice(args: argparse.Namespace, command: List[str]) -> int:
    """The owner's act: nothing is written unless the owner's digits, or the owner's written approval, confirm the record seen."""
    path = evidence.REPO.rep / DIRECTORY / TIE
    if not path.exists():
        raise Refused("no tie exists")
    if (evidence.REPO.rep / DIRECTORY / TIE_CHOICE).exists():
        raise Refused("a choice exists, and it never changes")
    tie = json.loads(path.read_bytes().decode("utf-8"))
    if tie["decided_by"] != "owner":
        raise Refused(f"a tie-break decided it: {tie['decided_by']}")
    choice = read_choice()
    if args.choose not in choice["representatives"].values():
        raise Refused(f"{args.choose} is not a representative of the tie")
    digest = evidence.sha256(path.read_bytes())
    if args.seen != digest:
        raise Refused(f"the hash seen differs from {TIE}'s, {digest}")
    written = evidence.written_approval(args.written_approval) if args.written_approval else None
    run = evidence.Run("d4-tie-choice", directory=DIRECTORY, file_name=TIE_CHOICE, code_files=CODE, argv=command, analyst=args.by)
    with run:
        digits = evidence.approval_step(digest, written)
        fields = {"choice": args.choose, "who": args.by, "when": evidence.utc_now(), "seen_sha256": digest, "choice_confirmed": digits}
        if written is not None:
            fields["written_approval"] = written
        written_to = run.finish("pass", fields=fields)
    print(f"{evidence.rel_to_repo(written_to)}: {args.choose}")
    return evidence.EXIT_OK


# --------------------------------------------------------------------------------------- --reproduce

def recompute(text: str, out: str) -> None:
    """The run of a reproduction, in its worktree: everything is read from that commit."""
    original = json.loads(text)
    kind = original["kind"]
    if kind == "d4-choice":
        fields = fields_of(*entered_set())
    else:
        fields = tie_breaks(json.loads(evidence.REPO.path(original["choice"]["path"]).read_bytes().decode("utf-8")), candidates.entries())
    Path(out).write_bytes(evidence.pretty(dict(fields, kind=kind, inputs=original.get("inputs", NONE), model_id=None, variant_id=None,
                                               exit_status=evidence.EXIT_OK, assertions=[], status="pass", classification=NONE,
                                               outputs=[])))


def reproduce(args: argparse.Namespace, command: List[str]) -> int:
    path = Path(args.reproduce)
    path = path if path.is_absolute() else evidence.REPO.path(args.reproduce)
    if not path.exists():
        raise Refused(f"{args.reproduce} does not exist")
    original = json.loads(path.read_bytes().decode("utf-8"))
    if original.get("kind") not in ("d4-choice", "d4-tie"):
        raise Refused(f"{args.reproduce} is no record that this script computes")

    def run(place: evidence.Place) -> Dict:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "fields.json"
            done = subprocess.run([sys.executable, "-X", "utf8", "-c", RUN_HERE, "recompute", json.dumps(original), str(out)],
                                  cwd=place.worktree, capture_output=True, text=True, encoding="utf-8", errors="replace")
            if done.returncode != 0:
                raise ToolFailure(f"the run exited {done.returncode}: {done.stderr.strip()[-400:]}")
            return dict(json.loads(out.read_bytes().decode("utf-8")), code_sha256=original["code_sha256"])

    names = ("entered", "outcomes", "width", "r_star", "r_star_statement", "scored", "representatives", "outcome", "chosen_family",
             "tie_breaks_applied", "bound_records", "decided_by", "R_at_4x4", "carry_chains", "ineligible")
    return evidence.reproduce(evidence.Reproduction(record_path=path, run=run, owner_request=args.owner_request, code_files=CODE,
                                                    extra=tuple(name for name in names if name in original), argv=command))


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--log")
    parser.add_argument("--out")
    parser.add_argument("--tie", action="store_true")
    parser.add_argument("--choose")
    parser.add_argument("--seen")
    parser.add_argument("--by")
    parser.add_argument("--written-approval")
    parser.add_argument("--reproduce")
    parser.add_argument("--owner-request")
    args = parser.parse_args(argv)
    command = [SCRIPT] + list(sys.argv[1:] if argv is None else argv)

    def body() -> int:
        if args.reproduce:
            return reproduce(args, command)
        if args.choose:
            if not args.seen or not args.by:
                raise Refused("--choose takes --seen SHA256 --by NAME")
            return write_owner_choice(args, command)
        if args.log and Path(args.log).as_posix().rstrip("/") not in (evidence.CANDIDATE_LOG_REL, evidence.REPO.path(evidence.CANDIDATE_LOG_REL).as_posix()):
            raise Refused(f"--log names {evidence.CANDIDATE_LOG_REL}")
        return write_tie(command) if args.tie else write_choice(command)

    return evidence.main_guard(body)


if __name__ == "__main__":
    raise SystemExit(main())
