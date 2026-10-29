"""PractRand and TestU01 output parsing, the pre-registered failure rule and the verdict
(feature 003 spec: Pre-registered Battery Protocol; research R6-R8; data-model sections 7-8).

Pure functions on saved tool output, so an attempt and its re-score use the same code (SC-006).

Failure rule for one generator, with S p-values and threshold t = 0.005 / S:
  rule 1: any p-value with min(p, 1 - p) <= t (two-sided Bonferroni bound);
  rule 2: PractRand grades any result "FAIL" (any number of "!"), or a pass/fail result "fail";
  rule 3: TestU01 reports any p-value as "eps" or "1 - eps".
"""
import json
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional

BATTERIES = ("practrand", "smallcrush", "crush", "bigcrush")
TESTU01 = ("smallcrush", "crush", "bigcrush")
ORIENTATIONS = {"practrand": ("fwd",), "smallcrush": ("fwd", "rev"), "crush": ("fwd", "rev"),
                "bigcrush": ("fwd", "rev")}
GENERATOR = {"positive": "os", "negative": "lut-v1", "candidate": "phyco-v2"}
ROLES = ("positive", "negative", "candidate")
PRACTRAND_TLMAX_LOG2 = 40          # 2^40 bytes = 1 TiB (spec option A)
PRACTRAND_TLMIN_LOG2 = 27          # data-based start, so checkpoints do not depend on speed


def practrand_args(stop_on_fail: bool = False, tlmax_log2: int = PRACTRAND_TLMAX_LOG2) -> List[str]:
    """RNG_test options (research R6). Only the negative control may stop at a failure."""
    return ["stdin32", "-tf", "2", "-te", "0", "-a", "-tlmin", str(PRACTRAND_TLMIN_LOG2),
            "-tlmax", str(tlmax_log2), "-tlfail" if stop_on_fail else "-tlmaxonly",
            "-multithreaded"]


def commands() -> Dict[str, str]:
    """Command templates recorded in the battery freeze (FR-011)."""
    stream = "fast/build/phyco_stream <generator> [S0 S1 S2 S3] [--reverse]"
    return {
        "pipeline": f"{stream} | (SHA-256 of every byte) | <consumer>",
        "practrand": "~/practrand/RNG_test " + " ".join(practrand_args()),
        "practrand_negative": "~/practrand/RNG_test " + " ".join(practrand_args(True)),
        "testu01": "fast/build/testu01_driver <smallcrush|crush|bigcrush> --name <run> "
                   "--pvalues pvalues.jsonl",
        "orientations": "practrand: fwd; TestU01: fwd and rev (--reverse)",
        "failure_rule": "rule 1: min(p, 1-p) <= 0.005/S; rule 2: PractRand FAIL grade or "
                        "\"fail\"; rule 3: TestU01 eps / 1 - eps",
    }


# ---------------------------------------------------------------- PractRand

_LENGTH = re.compile(r"^length=\s.*\(2\^(\d+) bytes\)")
_RESULT = re.compile(
    r"^\s+(?P<name>\S+)\s+(?:R=\s*(?P<raw>\S+)\s+)?"
    r"(?:(?P<pf>\"pass\"|\"fail\")|p\s*~?=\s*(?P<one>1-)?\s*(?P<val>[0-9.]+(?:e-[0-9]+)?))"
    r"\s+(?P<grade>\S.*?)\s*$")


def _practrand_q(one: Optional[str], val: str) -> (float, float):
    """Return (p, q) where q = min(p, 1 - p), exact from the printed text."""
    x = float(val)
    if one:
        return 1.0 - x, x
    return x, min(x, 1.0 - x)


def parse_practrand(text: str) -> Dict:
    results, checkpoint, last = [], None, None
    for line in text.splitlines():
        m = _LENGTH.match(line)
        if m:
            checkpoint = int(m.group(1))
            last = checkpoint
            continue
        if checkpoint is None:
            continue
        m = _RESULT.match(line)
        if not m or m.group("name") == "Test":
            continue
        grade = m.group("grade")
        if m.group("pf"):
            results.append({"test": m.group("name"), "checkpoint": checkpoint, "p": None,
                            "q": None, "passfail": m.group("pf").strip('"'), "grade": grade})
        else:
            p, q = _practrand_q(m.group("one"), m.group("val"))
            results.append({"test": m.group("name"), "checkpoint": checkpoint, "p": p, "q": q,
                            "grade": grade})
    return {"results": results, "length_log2": last,
            "n_pvalues": sum(r["q"] is not None for r in results)}


# ---------------------------------------------------------------- TestU01

# A summary-table row whose p-value is printed as "eps" or "1 - eps1"; the legend lines
# "(eps  means a value < 1.0e-300)" printed above the table must not match.
_EPS = re.compile(r"^\s*\d+\s+\S.*?\s+(eps|1 - eps1)\s*$")


def parse_testu01(text: str, jsonl: str) -> Dict:
    lines = [ln for ln in jsonl.splitlines() if ln.strip()]
    data = json.loads(lines[-1]) if lines else {"tests": []}
    results = [{"test": t["name"], "index": t["index"], "p": t["p"],
                "q": min(t["p"], 1.0 - t["p"])} for t in data["tests"]]
    summary = text.split("========= Summary results of", 1)
    eps_lines = [ln.strip() for ln in (summary[1].splitlines() if len(summary) > 1 else [])
                 if _EPS.match(ln)]
    return {"results": results, "n_pvalues": len(results), "eps_lines": eps_lines,
            "summary_found": len(summary) > 1, "n_tests": data.get("n_tests")}


# ---------------------------------------------------------------- rules and verdict

def threshold_rules(parsed: Dict, battery: str) -> Dict:
    """Rules 2 and 3, which do not depend on S."""
    if battery == "practrand":
        rule2 = [r for r in parsed["results"]
                 if r["grade"].startswith("FAIL") or r.get("passfail") == "fail"]
        return {"rule2": rule2, "rule3": []}
    return {"rule2": [], "rule3": parsed["eps_lines"]}


def rule1(parsed: Dict, threshold: float) -> List[Dict]:
    return [r for r in parsed["results"] if r["q"] is not None and r["q"] <= threshold]


def effective_threshold(S_frozen: int, runs: Iterable[Dict]) -> float:
    """0.005 / max(S frozen, p-values actually reported): a larger count is stricter (R8)."""
    actual = sum(r["n_pvalues"] for r in runs)
    return 0.005 / max(S_frozen, actual)


def run_fails(run: Dict, threshold: float) -> Dict:
    r1 = rule1(run, threshold)
    return {"rule1": r1, "rule2": run["rule2"], "rule3": run["rule3"],
            "fails": bool(r1 or run["rule2"] or run["rule3"])}


def role_outcome(runs: List[Dict], S_frozen: int) -> Dict:
    """Outcome of one generator over all its runs (spec failure rule)."""
    t = effective_threshold(S_frozen, runs)
    per_run = [dict(run_fails(r, t), run=r["run"], complete=r["complete"],
                    stopped_early=r.get("stopped_early", False)) for r in runs]
    failing = [r["run"] for r in per_run if r["fails"]]
    # A run that stopped early because it failed is not incomplete (spec Edge Cases).
    incomplete = [r["run"] for r in per_run if not r["complete"]
                  and not (r["stopped_early"] and r["fails"])]
    return {"threshold": t, "fails": bool(failing), "failing_runs": failing,
            "incomplete_runs": incomplete, "runs": per_run}


def verdict(equivalence_ok: bool, positive: Optional[Dict], negative: Optional[Dict],
            candidate: Optional[Dict]) -> (str, str):
    """Overall verdict (spec Pre-registered Battery Protocol)."""
    if not equivalence_ok:
        return "INVALID", "fast stream differs from the reference model"
    if positive is None or positive["incomplete_runs"]:
        return "INCONCLUSIVE", "positive control incomplete"
    if positive["fails"]:
        return "INCONCLUSIVE", "positive control failed; candidate not run"
    if negative is None or negative["incomplete_runs"]:
        return "INCONCLUSIVE", "negative control incomplete"
    if not negative["fails"]:
        return "INCONCLUSIVE", "negative control did not fail: batteries cannot discriminate"
    if candidate is None or candidate["incomplete_runs"]:
        return "INCONCLUSIVE", "candidate incomplete"
    return ("FAIL", "candidate failed") if candidate["fails"] else ("PASS", "candidate did not fail")


def load_run(run_dir: Path) -> Dict:
    """Re-parse one saved run from its raw files (used by the attempt and the re-score)."""
    meta = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    text = (run_dir / "log.txt").read_text(encoding="utf-8", errors="replace")
    if meta["battery"] == "practrand":
        parsed = parse_practrand(text)
        reached = parsed["length_log2"] == meta["length_target_log2"]
    else:
        pv = run_dir / "pvalues.jsonl"
        parsed = parse_testu01(text, pv.read_text(encoding="utf-8") if pv.exists() else "")
        reached = parsed["summary_found"] and parsed["n_pvalues"] > 0
    parsed.update(threshold_rules(parsed, meta["battery"]))
    parsed.update(run=run_dir.name, battery=meta["battery"], role=meta["role"],
                  complete=meta["exit_status"] == 0 and reached,
                  stopped_early=meta.get("stop_on_fail", False) and not reached)
    return parsed
