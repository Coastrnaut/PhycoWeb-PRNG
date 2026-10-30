"""Re-score a battery attempt from its saved logs (feature 003; data-model section 9; SC-006).

  battery_rescore.py --attempt N

Re-parses every saved run with protocol/batteries.py, recomputes every role outcome and the
verdict with the frozen S, and compares them with attempt.json. Writes rescore.json.
Exit 0 if everything is identical, 1 if anything differs, 2 if the attempt has no record.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in (str(ROOT), str(ROOT / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import battery_attempt  # noqa: E402
from protocol import battery_freeze, batteries  # noqa: E402
from protocol.disclaimer import DISCLAIMER  # noqa: E402


def rescore(n: int) -> dict:
    adir = battery_freeze.attempt_dir(n)
    old = json.loads((adir / "attempt.json").read_text(encoding="utf-8"))
    outcomes, diffs = {r: None for r in batteries.ROLES}, []
    for role in batteries.ROLES:
        if old["roles"][role]["status"] != "run":
            continue
        dirs = sorted(d for d in (adir / role).iterdir() if d.is_dir())
        new = battery_attempt.evaluate_role(dirs, old["S"])
        outcomes[role] = new
        key = lambda runs: sorted(runs, key=lambda r: r["run"])  # noqa: E731
        for a, b in zip(key(old["roles"][role]["outcome"]["runs"]), key(new["runs"])):
            if a != b:
                diffs.append({"role": role, "run": a["run"], "recorded": a, "rescored": b})
        for field in ("fails", "failing_runs", "incomplete_runs", "threshold", "n_pvalues"):
            o, nv = old["roles"][role]["outcome"][field], new[field]
            if (sorted(o) if isinstance(o, list) else o) != (sorted(nv) if isinstance(nv, list) else nv):
                diffs.append({"role": role, "field": field, "recorded": o, "rescored": nv})
    verdict, reason = batteries.verdict(old["equivalence"]["all_match"], outcomes["positive"],
                                        outcomes["negative"], outcomes["candidate"])
    return {"attempt": n, "recorded_verdict": old["verdict"], "rescored_verdict": verdict,
            "reason": reason, "differences": diffs,
            "identical": not diffs and verdict == old["verdict"], "disclaimer": DISCLAIMER}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=int, required=True)
    args = parser.parse_args(argv)
    if not (battery_freeze.attempt_dir(args.attempt) / "attempt.json").exists():
        print(f"attempt {args.attempt} has no attempt record", file=sys.stderr)
        return 2
    result = rescore(args.attempt)
    (battery_freeze.attempt_dir(args.attempt) / "rescore.json").write_text(
        json.dumps(result, indent=1) + "\n", encoding="utf-8")
    print(f"attempt {args.attempt} re-score: "
          f"{'identical' if result['identical'] else 'DIFFERENT'} ({result['rescored_verdict']})")
    return 0 if result["identical"] else 1


if __name__ == "__main__":
    sys.exit(main())
