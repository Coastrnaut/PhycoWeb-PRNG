"""Summarize the positive-control calibration (feature 003 US1; FR-003, FR-004, FR-005; R3).

Refuses unless runs 0..999 are all present and each record is consistent. Rates use exact
Clopper-Pearson 95% intervals. Expected rates follow the feature-002 rules: a sub-test fails
with probability q_fail(m') + 1e-4 (proportion, plus the uniformity threshold treated as
independent), and a family fails if more than k_max(n_sub, m') sub-tests fail, using each
run's own m'. scipy is used here only, as analysis tooling.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
from itertools import combinations
from pathlib import Path
from typing import Dict, List

from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
for p in (str(ROOT), str(ROOT / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import calibrate  # noqa: E402
from protocol.disclaimer import DISCLAIMER  # noqa: E402
from sp80022.assess import UNIFORMITY_ALPHA, k_max, q_fail  # noqa: E402

ASSUMED_OVERALL = 0.19   # feature-002 spec Assumptions
RECOMMENDATION_NOTE = ("recommendation only; needs a separate, owner-approved, stricter-only "
                       "spec amendment (feature 002 FR-014)")


def clopper_pearson(k: int, n: int, level: float = 0.95):
    a = (1 - level) / 2
    lo = 0.0 if k == 0 else float(stats.beta.ppf(a, k, n - k + 1))
    hi = 1.0 if k == n else float(stats.beta.ppf(1 - a, k + 1, n - k))
    return lo, hi


def rate(k: int, n: int) -> Dict:
    lo, hi = clopper_pearson(k, n)
    return {"failures": k, "n": n, "rate": k / n, "ci95": [lo, hi]}


def subtest_fail_probability(m: int) -> float:
    return float(q_fail(m)) + UNIFORMITY_ALPHA


def family_fail_probability(n_sub: int, m: int) -> float:
    if m < 55:
        return 1.0
    p = subtest_fail_probability(m)
    if n_sub == 1:
        return p
    return float(stats.binom.sf(k_max(n_sub, m), n_sub, p))


def load_runs(runs_dir: Path, n_runs: int) -> List[Dict]:
    records = []
    missing = [r for r in range(n_runs) if not calibrate.run_path(runs_dir, r).exists()]
    if missing:
        raise ValueError(f"{len(missing)} run files missing (first: {missing[0]})")
    for r in range(n_runs):
        with gzip.open(calibrate.run_path(runs_dir, r), "rt", encoding="utf-8") as fh:
            rec = json.load(fh)
        if (rec["run"] != r or rec["harness_sha256"] != calibrate.HARNESS_SHA256
                or rec["n_sequences"] != calibrate.N_SEQUENCES or rec["n_bits"] != calibrate.N_BITS):
            raise ValueError(f"run file {r} is inconsistent with its index or the protocol")
        records.append(rec)
    return records


def summarize(records: List[Dict]) -> Dict:
    n = len(records)
    names = list(records[0]["families"])
    fam_fail = {f: [not rec["families"][f]["pass"] for rec in records] for f in names}
    run_fail = [rec["verdict"] == "fail" for rec in records]

    overall = rate(sum(run_fail), n)
    overall["assumed"] = ASSUMED_OVERALL
    overall["consistent"] = overall["ci95"][0] <= ASSUMED_OVERALL <= overall["ci95"][1]

    per_family = {}
    for f in names:
        expected = sum(family_fail_probability(rec["families"][f]["n_sub"],
                                               rec["subtests"][f][0]["m_prime"])
                       for rec in records) / n
        entry = rate(sum(fam_fail[f]), n)
        entry["expected"] = expected
        entry["consistent"] = entry["ci95"][0] <= expected <= entry["ci95"][1]
        per_family[f] = entry

    per_subtest = {}
    for f in names:
        for j in range(len(records[0]["subtests"][f])):
            subs = [rec["subtests"][f][j] for rec in records]
            per_subtest[f"{f}[{j}]"] = {
                "combined": rate(sum(not s["ok"] for s in subs), n),
                "proportion": rate(sum(not s["proportion_ok"] for s in subs), n),
                "uniformity": rate(sum(not s["uniformity_ok"] for s in subs), n),
                "expected": sum(subtest_fail_probability(s["m_prime"]) for s in subs) / n,
            }

    counts = [sum(fam_fail[f][i] for f in names) for i in range(n)]
    histogram = [counts.count(c) for c in range(len(names) + 1)]

    co_failure = []
    for a, b in combinations(names, 2):
        both = sum(x and y for x, y in zip(fam_fail[a], fam_fail[b]))
        only_a = sum(fam_fail[a]) - both
        only_b = sum(fam_fail[b]) - both
        neither = n - both - only_a - only_b
        expected = n * (sum(fam_fail[a]) / n) * (sum(fam_fail[b]) / n)
        p = float(stats.fisher_exact([[both, only_a], [only_b, neither]])[1])
        co_failure.append({"a": a, "b": b, "both": both, "expected_independent": expected,
                           "fisher_p": p})

    lo, hi = overall["ci95"]
    implied = {"value": (1 - overall["rate"]) ** 2, "ci95": [(1 - hi) ** 2, (1 - lo) ** 2],
               "assumption": "perfect candidate and perfect positive control; negative control "
                             "fails with probability 1"}
    return {"runs": n, "overall": overall, "per_family": per_family,
            "per_subtest": per_subtest, "failing_family_count": histogram,
            "co_failure": co_failure, "implied_pass_probability": implied}


def recommendations(summary: Dict) -> List[str]:
    out = []
    if not summary["overall"]["consistent"]:
        out.append(f"The overall false-failure rate {summary['overall']['rate']:.3f} is outside "
                   f"the assumed {ASSUMED_OVERALL}; restate the feature-002 assumption before any "
                   f"further attempt ({RECOMMENDATION_NOTE}).")
    for f, e in summary["per_family"].items():
        if not e["consistent"]:
            out.append(f"Family {f}: measured {e['rate']:.4f} vs expected {e['expected']:.4f} "
                       f"({RECOMMENDATION_NOTE}).")
    return out


def render_md(summary: Dict, run_hashes_sha: str) -> str:
    o, ip = summary["overall"], summary["implied_pass_probability"]
    lines = [
        "# Calibration Summary: SP 800-22 Positive Control (feature 003, US1)",
        "",
        f"{summary['runs']} runs × 100 sequences × 2²¹ bits of os.urandom data, harness "
        f"`sp80022` 1.0.0, feature-002 rules. SHA-256 of `runs/SHA256SUMS`: `{run_hashes_sha}`.",
        "",
        f"- **Overall false-failure rate**: {o['failures']}/{o['n']} = {o['rate']:.4f} "
        f"(95% CI {o['ci95'][0]:.4f}–{o['ci95'][1]:.4f}); assumed {o['assumed']}; "
        f"{'consistent' if o['consistent'] else '**not consistent**'}.",
        f"- **Implied PASS probability** (perfect candidate and control): {ip['value']:.4f} "
        f"(95% CI {ip['ci95'][0]:.4f}–{ip['ci95'][1]:.4f}).",
        "",
        "| Family | Failures | Rate | 95% CI | Expected | Consistent |",
        "|--------|----------|------|--------|----------|------------|",
    ]
    for f, e in summary["per_family"].items():
        lines.append(f"| {f} | {e['failures']} | {e['rate']:.4f} | {e['ci95'][0]:.4f}–"
                     f"{e['ci95'][1]:.4f} | {e['expected']:.4f} | {'yes' if e['consistent'] else '**no**'} |")
    lines += ["", "Failing families per run: " +
              ", ".join(f"{c}: {k}" for c, k in enumerate(summary["failing_family_count"]) if k), ""]
    strong = sorted(summary["co_failure"], key=lambda c: c["fisher_p"])[:10]
    lines += ["Ten pairs with the smallest Fisher p (co-failure; reported only):", "",
              "| Pair | Both fail | Expected if independent | Fisher p |",
              "|------|-----------|-------------------------|----------|"]
    for c in strong:
        lines.append(f"| {c['a']} + {c['b']} | {c['both']} | {c['expected_independent']:.2f} | "
                     f"{c['fisher_p']:.2e} |")
    lines += ["", "## Recommendations", ""]
    lines += [f"- {r}" for r in summary["recommendations"]] or ["- None."]
    lines += ["", "## Disclaimer", "", DISCLAIMER, ""]
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        records = load_runs(args.runs_dir, calibrate.RUNS)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 2
    sums = "".join(f"{hashlib.sha256(calibrate.run_path(args.runs_dir, r).read_bytes()).hexdigest()}"
                   f"  {calibrate.run_path(args.runs_dir, r).name}\n" for r in range(calibrate.RUNS))
    (args.runs_dir / "SHA256SUMS").write_text(sums, encoding="ascii", newline="\n")
    summary = summarize(records)
    summary["recommendations"] = recommendations(summary)
    summary["input_sha256"] = [rec["input_sha256"] for rec in records]
    summary["run_files_sha256sums"] = hashlib.sha256(sums.encode("ascii")).hexdigest()
    summary["disclaimer"] = DISCLAIMER
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8", newline="\n")
    args.out.with_suffix(".md").write_text(render_md(summary, summary["run_files_sha256sums"]),
                                           encoding="utf-8", newline="\n")
    print(f"overall {summary['overall']['rate']:.4f} {summary['overall']['ci95']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
