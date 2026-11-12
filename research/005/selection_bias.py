"""Feature 005: the selection-bias statement (spec FR-024; research R11; data-model section 6).

    python -X utf8 research/005/selection_bias.py [--check FILE]

It prints a Markdown table of every design considered in features 004 and 005, generated from
research/004/candidates.jsonl and research/005/candidates.jsonl, which it reads and never writes:
per design its feature, ID, family, outcome, the log entry of its decision and the feature-004
design it derives from, if any; then feature 004's D4 record and selection record by path and
SHA-256, and the bias rule's family-wise rate over this feature's tests. With --check FILE it
compares the statement that FILE holds with the one it generates and exits 1 on a difference. It
writes no record and no file. Run from the repository root. This script makes no security claim.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FEATURES = (("004", "research/004/candidates.jsonl", "reports/004-crypto-architecture-v3", "cand-"),
            ("005", "research/005/candidates.jsonl", "reports/005-crypto-architecture-v4", "v4-"))
FAMILIES = {"A": "ARX", "B": "Boolean"}
CLOSING = ("ineligible", "rejected", "withdrawn")
DECLINED = "the owner declined the proposed design"
D4_RECORD = "reports/004-crypto-architecture-v3/d4/choice.json"
SELECTION_RECORD = "reports/004-crypto-architecture-v3/freeze/selection.json"
BIAS_KINDS = ("frequency", "avalanche")
AVALANCHE_ROUNDS = 128
HEADER = ("| Feature | Design | Family | Outcome | Decision entry | Derived from |",
          "|---------|--------|--------|---------|----------------|--------------|")
FIRST_LINE = "Every design considered in features 004 and 005, from their candidate logs:"


def entries(rel, root=ROOT):
    path = root / rel
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_bytes().decode("utf-8").splitlines() if line.strip()]


def selected_of(rep, root=ROOT):
    """The candidate the feature's latest selection record names, or None."""
    directory = root / rep / "freeze"
    found = sorted(directory.glob("selection*.json")) if directory.exists() else []
    records = [json.loads(path.read_bytes().decode("utf-8")) for path in found if "tie-choice" not in path.name]
    if not records:
        return None
    value = max(records, key=lambda record: record.get("created_utc", "")).get("selected")
    return value if isinstance(value, str) and value != "none" else None


def derived(entry):
    given = entry.get("derived_from", "none")
    if not isinstance(given, dict):
        return "none"
    return f"feature {given['feature']}, {given['candidate']}, {given['relation']}"


def rows_of(feature, log, selected, prefix):
    """One row per design with a `proposed` entry, and one per design that was proposed to the owner
    in place of another and declined, which the log holds as a closed replacement entry."""
    out = []
    decisions = {}
    for entry in log:
        if entry.get("event") == "decision":
            decisions.setdefault(entry["candidate_id"], []).append(entry)
    for entry in log:
        if entry.get("event") != "proposed":
            continue
        name = entry["candidate_id"]
        made = decisions.get(name, [])
        closing = [d for d in made if d.get("decision") in CLOSING]
        if closing:
            outcome, seq = closing[-1]["decision"], closing[-1]["seq"]
        elif any(d.get("decision") == "eligible" for d in made):
            last = [d for d in made if d.get("decision") == "eligible"][-1]
            outcome, seq = ("selected" if name == selected else "not selected"), last["seq"]
        else:
            outcome, seq = "undecided", entry["seq"]
        out.append((feature, name, entry["family"], outcome, seq, derived(entry)))
    proposed = {row[1] for row in out}
    for entry in log:
        if entry.get("event") == "replacement" and entry.get("reason") == DECLINED:
            letter = next(key for key, value in FAMILIES.items() if value == entry["family"])
            taken = sorted(name for name in proposed if name.startswith(prefix + letter))
            name = f"{prefix}{letter}{len(taken) + 1}"
            proposed.add(name)
            out.append((feature, name, entry["family"], "proposed and declined", entry["seq"], "none"))
    return out


def named(rel, root=ROOT):
    path = root / rel
    if not path.exists():
        return f"`{rel}`: not written"
    record = json.loads(path.read_bytes().decode("utf-8"))
    return f"`{rel}`, record `{record.get('record_id', 'none')}`, SHA-256 `{hashlib.sha256(path.read_bytes()).hexdigest()}` (raw)"


def bias_tests(rep, root=ROOT):
    """The pairs of a size and a round count that this feature's finished bias records tested with
    2r above the R in force, and each avalanche size's factor, as feature 004's research R4 counts
    them for the chance of a false firing."""
    pairs, factors = 0, []
    base = root / rep / "candidates"
    for directory in sorted(base.iterdir()) if base.exists() else ():
        tested, measured = set(), {}
        for kind in BIAS_KINDS:
            for path in sorted(directory.glob(f"{kind}-*.json")):
                record = json.loads(path.read_bytes().decode("utf-8"))
                if record.get("status") not in ("pass", "fail") or record.get("ended_outside", "none") != "none":
                    continue
                size, rounds = record["config"]["size"], record["config"]["rounds"]
                tested.update((size, r) for r in range(1, rounds + 1) if 2 * r > rounds)
                if kind == "avalanche":
                    measured[size] = max(measured.get(size, 0), rounds)
        pairs += len(tested)
        factors += [2.0 if m <= AVALANCHE_ROUNDS else m / 64.0 for _, m in sorted(measured.items())]
    return pairs, factors


def rate(pairs, factors):
    rest = 0.995 ** pairs
    for a in factors:
        rest *= 1.0 - 0.005 * a
    return 1.0 - rest


def statement(root=ROOT):
    lines = [FIRST_LINE, "", *HEADER]
    for feature, rel, rep, prefix in FEATURES:
        for row in rows_of(feature, entries(rel, root), selected_of(rep, root), prefix):
            lines.append(f"| {row[0]} | `{row[1]}` | {row[2]} | {row[3]} | feature {row[0]}, seq {row[4]} | {row[5]} |")
    lines += ["", f"Feature 004's D4 record: {named(D4_RECORD, root)}.",
              f"Feature 004's selection record: {named(SELECTION_RECORD, root)}."]
    pairs, factors = bias_tests(FEATURES[1][2], root)
    if pairs or factors:
        lines.append(f"The bias rule's family-wise rate over this feature's tests, {pairs} pairs of a size and a round count "
                     f"and {len(factors)} avalanche sizes: {rate(pairs, factors):.4f}. Feature 004 ran no bias test at w = 32.")
    else:
        lines.append("The bias rule's family-wise rate over this feature's tests: no frequency or avalanche test of this "
                     "feature has finished. Feature 004 ran no bias test at w = 32.")
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--check")
    args = parser.parse_args(argv)
    text = statement()
    if args.check:
        held = Path(args.check).read_bytes().decode("utf-8").replace("\r\n", "\n")
        same = text.strip("\n") in held
        print("the statement matches" if same else "the statement differs")
        return 0 if same else 1
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
