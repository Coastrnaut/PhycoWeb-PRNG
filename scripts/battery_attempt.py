"""Run one pre-registered battery attempt (feature 003 US2; contracts/cli.md; data-model section 8;
FR-012 to FR-014, FR-016).

  battery_attempt.py --attempt N [--slots 32]

Refuses (exit 2) unless the freeze for attempt N exists, is approved and validates, N is the
next allowed attempt (FR-013) and the attempt has not been started. Then: writes started.json;
checks the fast stream against the reference models on the first 10^6 words of every held-out
seed (a mismatch makes the attempt INVALID); runs the positive control, the negative control
(always, even if the positive control failed) and, only if the positive control neither failed
nor was incomplete, the candidate; writes attempt.json and summary.md. Runs are never repeated.
Exit 0 on PASS, 1 otherwise. Run in WSL.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import get_context
from pathlib import Path
from threading import Condition
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
for p in (str(ROOT), str(ROOT / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from protocol import battery_freeze, battery_seedsets, batteries  # noqa: E402
from protocol.disclaimer import DISCLAIMER  # noqa: E402

EQUIV_WORDS = 1_000_000
SLOT_COST = {"practrand": 6, "smallcrush": 2, "crush": 2, "bigcrush": 2}


def run_specs(role: str, seeds) -> List[Dict]:
    """Every run of one role: PractRand fwd, and each TestU01 battery fwd and rev, per seed."""
    specs = []
    for i, seed in enumerate(seeds):
        for battery in batteries.BATTERIES:
            for orientation in batteries.ORIENTATIONS[battery]:
                specs.append({"role": role, "battery": battery, "orientation": orientation,
                              "seed_index": i, "seed": None if role == "positive" else list(seed),
                              "name": f"{battery}-{orientation}-seed{i}"})
    return specs


def launch(spec: Dict, attempt: int, out: Path) -> int:
    """Run one battery_run.py subprocess (replaced by a fake in tests)."""
    cmd = [sys.executable, str(ROOT / "scripts" / "battery_run.py"), "--attempt", str(attempt),
           "--role", spec["role"], "--battery", spec["battery"], "--orientation",
           spec["orientation"], "--out", str(out)]
    cmd += ["--os"] if spec["seed"] is None else ["--seed", *map(str, spec["seed"])]
    if spec["role"] == "negative" and spec["battery"] == "practrand":
        cmd.append("--stop-on-fail")
    with open(out.parent / f"{out.name}.runner.txt", "wb") as fh:
        return subprocess.run(cmd, stdout=fh, stderr=subprocess.STDOUT).returncode


def run_role(role: str, seeds, attempt: int, slots: int, log) -> List[Path]:
    """Run all runs of one role with at most `slots` cost units in progress."""
    role_dir = battery_freeze.attempt_dir(attempt) / role
    role_dir.mkdir(parents=True, exist_ok=True)
    specs = run_specs(role, seeds)
    free, cond = [slots], Condition()

    def work(spec):
        cost = min(SLOT_COST[spec["battery"]], slots)
        with cond:
            cond.wait_for(lambda: free[0] >= cost)
            free[0] -= cost
        try:
            log(f"{role} {spec['name']} start")
            status = launch(spec, attempt, role_dir / spec["name"])
            log(f"{role} {spec['name']} exit {status}")
        finally:
            with cond:
                free[0] += cost
                cond.notify_all()

    # Long runs first so the short ones fill the gaps.
    order = sorted(specs, key=lambda s: ("bigcrush", "practrand", "crush", "smallcrush").index(s["battery"]))
    with ThreadPoolExecutor(max_workers=len(specs)) as pool:
        list(pool.map(work, order))
    return [role_dir / s["name"] for s in specs]


def _equiv_job(args):
    import stream_equiv
    model, seed = args
    return model, list(seed), stream_equiv.compare(
        stream_equiv.stream_words(ROOT / "fast" / "build" / "phyco_stream", model, seed, EQUIV_WORDS),
        stream_equiv.model_words(model, seed, EQUIV_WORDS))


def equivalence(seeds, workers: int) -> Dict:
    """First 10^6 words of every held-out seed, both models (US3 scenario 3)."""
    jobs = [(m, s) for m in ("phyco-v2", "lut-v1") for s in seeds]
    with get_context("spawn").Pool(min(workers, len(jobs))) as pool:
        rows = [dict(model=m, seed=s, **r) for m, s, r in pool.map(_equiv_job, jobs)]
    return {"words_per_seed": EQUIV_WORDS, "rows": rows,
            "all_match": all(r["mismatches"] == 0 for r in rows)}


def summarize_runs(outcome: Dict) -> List[Dict]:
    return [{"run": r["run"], "fails": r["fails"], "complete": r["complete"],
             "stopped_early": r["stopped_early"], "rule1": len(r["rule1"]),
             "rule2": len(r["rule2"]), "rule3": len(r["rule3"]),
             "rule1_first": r["rule1"][:5], "rule2_first": r["rule2"][:5],
             "rule3_first": r["rule3"][:5]} for r in outcome["runs"]]


def evaluate_role(run_dirs: List[Path], S: int) -> Dict:
    loaded = []
    for d in run_dirs:
        try:
            loaded.append(batteries.load_run(d))
        except (OSError, ValueError, KeyError):
            loaded.append({"run": d.name, "n_pvalues": 0, "results": [], "rule2": [], "rule3": [],
                           "complete": False, "stopped_early": False})
    out = batteries.role_outcome(loaded, S)
    out["n_pvalues"] = sum(r["n_pvalues"] for r in loaded)
    out["runs"] = summarize_runs(out)
    return out


def render_summary(record: Dict) -> str:
    lines = [f"# Battery Attempt {record['attempt']} ({record['seed_set']})", "",
             f"**Verdict: {record['verdict']}** ({record['reason']}).", "",
             f"S (frozen) = {record['S']}; equivalence: "
             f"{'all match' if record['equivalence']['all_match'] else '**mismatch**'}.", "",
             "| Role | Generator | Status | Runs failing | Incomplete | p-values | Threshold |",
             "|------|-----------|--------|--------------|------------|----------|-----------|"]
    for role in batteries.ROLES:
        r = record["roles"][role]
        if r["status"] != "run":
            lines.append(f"| {role} | {batteries.GENERATOR[role]} | {r['status']} | | | | |")
            continue
        o = r["outcome"]
        lines.append(f"| {role} | {batteries.GENERATOR[role]} | run | {len(o['failing_runs'])} | "
                     f"{len(o['incomplete_runs'])} | {o['n_pvalues']} | {o['threshold']:.3e} |")
    lines += ["", "## Disclaimer", "", DISCLAIMER, ""]
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=int, required=True)
    parser.add_argument("--slots", type=int, default=32)
    args = parser.parse_args(argv)
    n = args.attempt
    try:
        record = battery_freeze.load(n)
        problems = battery_freeze.validate(record, n)
        if problems:
            raise battery_freeze.FreezeError("freeze not usable: " + "; ".join(problems))
        if battery_freeze.next_attempt() != n:
            raise battery_freeze.FreezeError(f"attempt {n} is not the next allowed attempt")
    except battery_freeze.FreezeError as exc:
        print(exc, file=sys.stderr)
        return 2
    adir = battery_freeze.attempt_dir(n)
    if (adir / "started.json").exists():
        print(f"attempt {n} was already started", file=sys.stderr)
        return 2
    seeds = battery_seedsets.load(record["seed_set"], allow={record["seed_set"]})
    started = time.time()
    progress = open(adir / "progress.txt", "a", encoding="utf-8")

    def log(msg):
        progress.write(time.strftime("%Y-%m-%dT%H:%M:%S ") + msg + "\n")
        progress.flush()

    (adir / "started.json").write_text(json.dumps({
        "attempt": n, "seed_set": record["seed_set"],
        "started": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(started)),
        "freeze_sha256": hashlib.sha256(battery_freeze.freeze_path(n).read_bytes()).hexdigest(),
        "git_head": battery_freeze.git_head()}, indent=1) + "\n", encoding="utf-8")
    log("equivalence start")
    equiv = equivalence(seeds, args.slots)
    (adir / "equivalence.json").write_text(json.dumps(equiv, indent=1) + "\n", encoding="utf-8")
    log(f"equivalence all_match={equiv['all_match']}")
    roles = {r: {"status": "not_run"} for r in batteries.ROLES}
    outcomes = {r: None for r in batteries.ROLES}
    if equiv["all_match"]:
        for role in batteries.ROLES:
            if role == "candidate" and (outcomes["positive"]["fails"]
                                        or outcomes["positive"]["incomplete_runs"]):
                log("candidate not run: positive control failed or incomplete")
                break
            dirs = run_role(role, seeds, n, args.slots, log)
            outcomes[role] = evaluate_role(dirs, record["S"])
            roles[role] = {"status": "run", "outcome": outcomes[role]}
            log(f"{role} done: fails={outcomes[role]['fails']} "
                f"incomplete={len(outcomes[role]['incomplete_runs'])}")
    verdict, reason = batteries.verdict(equiv["all_match"], outcomes["positive"],
                                        outcomes["negative"], outcomes["candidate"])
    result = {"attempt": n, "seed_set": record["seed_set"], "S": record["S"],
              "equivalence": {"all_match": equiv["all_match"], "words_per_seed": EQUIV_WORDS,
                              "mismatching": [r for r in equiv["rows"] if r["mismatches"] != 0]},
              "roles": roles, "verdict": verdict, "reason": reason,
              "started": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(started)),
              "elapsed_s": round(time.time() - started, 1), "disclaimer": DISCLAIMER}
    (adir / "attempt.json").write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    (adir / "summary.md").write_text(render_summary(result), encoding="utf-8")
    log(f"verdict {verdict}: {reason}")
    progress.close()
    print(f"attempt {n}: {verdict} ({reason})")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
