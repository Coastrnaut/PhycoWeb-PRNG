"""Run one pre-registered held-out acceptance attempt (contracts/cli.md; research R8).

Refuses (exit 2, nothing evaluated) unless the freeze for attempt N exists, is approved by the
owner, and matches the model, design and harness on disk; N is the next attempt (at most 3);
and attempt N has not been started before. Then it runs the positive control (OS CSPRNG), the
negative control (lut-v1) and the candidate (phyco-v2) on heldout-N, in that order. If the
positive control fails, the candidate is not generated or scored and the attempt is
INCONCLUSIVE (spec Edge Cases, FR-017). Exit 0 only for PASS, 1 otherwise.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import sys
import time
from pathlib import Path

import evalcore
from evalcore import N_BITS, ROOT
from protocol import freeze, seedsets
from protocol.disclaimer import DISCLAIMER

SEQUENCES = 100
NOT_RUN = "not run (positive control failed; spec Edge Cases)"
SOURCES = {"positive": "os-csprng", "negative": "lut-v1", "candidate": "phyco-v2"}


def controls_dir() -> Path:
    return ROOT / "data" / "controls"


def evaluate(role: str, n: int, seeds, workers: int, command: str) -> dict:
    """Generate and score one source of the attempt; returns its evaluation record."""
    started = time.time()
    extra, seed_set, seed_list = {"role": role, "attempt": n}, None, None
    if role == "positive":
        raw = os.urandom(SEQUENCES * N_BITS // 8)
        path = controls_dir() / f"attempt-{n}.bin"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        extra["bytes_file"] = path.relative_to(ROOT).as_posix()
        extra["bytes_sha256"] = evalcore.sha256_file(path)
        step = N_BITS // 8
        jobs = [(i, "bytes", raw[i * step:(i + 1) * step], N_BITS, 0) for i in range(SEQUENCES)]
    else:
        seed_set, seed_list = f"heldout-{n}", [list(s) for s in seeds]
        jobs = [(i, "model", (SOURCES[role], list(s)), N_BITS, 0) for i, s in enumerate(seeds)]
    per_sequence = evalcore.run_jobs(jobs, workers)
    return evalcore.build_record(SOURCES[role], per_sequence, seed_set=seed_set, seeds=seed_list,
                                 n_bits=N_BITS, command=command, workers=workers,
                                 started=started, extra=extra)


def refuse(message: str) -> int:
    print(f"refused: {message}", file=sys.stderr)
    return 2


def _summary(n, attempt, records) -> str:
    lines = [f"# Acceptance Attempt {n}: {attempt['overall']}", "",
             f"Date: {attempt['finished'][:10]}. Seed set `heldout-{n}`; freeze "
             f"`attempt-{n}/freeze.json` (SHA-256 `{attempt['freeze_sha256']}`).", "",
             "| Role | Source | Verdict | Families failed |", "|------|--------|---------|-----------------|"]
    for role in ("positive", "negative", "candidate"):
        rec = records.get(role)
        if rec is None:
            lines.append(f"| {role} | {SOURCES[role]} | {NOT_RUN} | — |")
        else:
            failed = ", ".join(rec["families_failed"]) or "none"
            lines.append(f"| {role} | {SOURCES[role]} | {rec['verdict']} | {failed} |")
    lines += ["", f"**Overall verdict (spec rule): {attempt['overall']}**", "", "## Limitations", ""]
    lines += [f"- {text}" for text in evalcore.LIMITATIONS]
    lines += ["", "## Disclaimer", "", DISCLAIMER, ""]
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=int, required=True)
    parser.add_argument("--workers", type=int, default=evalcore.default_workers())
    args = parser.parse_args(argv)
    n = args.attempt
    command = "python " + " ".join([Path(sys.argv[0]).as_posix()] + (argv or sys.argv[1:]))

    if not 1 <= n <= freeze.MAX_ATTEMPTS:
        return refuse(f"attempt must be 1..{freeze.MAX_ATTEMPTS}; further attempts need a spec "
                      f"amendment")
    out = freeze.attempt_dir(n)
    if (out / "attempt.json").exists():
        return refuse(f"attempt {n} already has an attempt record; a held-out set is never reused")
    if (out / "started.json").exists():
        return refuse(f"attempt {n} was started before ({out / 'started.json'}); it counts as "
                      f"used and needs an owner decision")
    if n != freeze.next_attempt():
        return refuse(f"attempt {n} is not the next attempt ({freeze.next_attempt()})")
    try:
        record = freeze.load(n)
    except freeze.FreezeError as exc:
        return refuse(str(exc))
    problems = freeze.validate(record, n)
    if problems:
        return refuse("; ".join(problems))
    seeds = seedsets.load(f"heldout-{n}", allow={f"heldout-{n}"})
    freeze_sha256 = hashlib.sha256(freeze.freeze_path(n).read_bytes()).hexdigest()

    started = time.strftime("%Y-%m-%dT%H:%M:%S")
    (out / "started.json").write_text(json.dumps({"attempt": n, "freeze_sha256": freeze_sha256,
                                                  "started": started}) + "\n", encoding="utf-8")
    records, order = {}, []
    for role in ("positive", "negative", "candidate"):
        if role == "candidate" and records["positive"]["verdict"] != "pass":
            order.append({"role": role, "status": NOT_RUN})
            continue
        t0 = time.strftime("%Y-%m-%dT%H:%M:%S")
        records[role] = evaluate(role, n, seeds, args.workers, command)
        evalcore.write_record(out / f"eval-{role}.json", records[role])
        order.append({"role": role, "start": t0, "end": time.strftime("%Y-%m-%dT%H:%M:%S")})
        print(f"{role} ({SOURCES[role]}): {records[role]['verdict']}; failed "
              f"{records[role]['families_failed'] or 'none'}")

    passed = {role: (rec["verdict"] == "pass") for role, rec in records.items()}
    overall = importlib.import_module("sp80022.assess").overall(
        passed["positive"], passed["negative"], passed.get("candidate"))
    attempt = {
        "attempt": n,
        "seed_set": f"heldout-{n}",
        "freeze_sha256": freeze_sha256,
        "order": order,
        "started": started,
        "finished": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    for role in ("positive", "negative", "candidate"):
        attempt[role] = ({"record": f"eval-{role}.json", "verdict": records[role]["verdict"]}
                         if role in records else NOT_RUN)
    attempt["overall"] = overall
    attempt["disclaimer"] = DISCLAIMER
    (out / "attempt.json").write_text(json.dumps(attempt, indent=1) + "\n", encoding="utf-8")
    (out / "summary.md").write_text(_summary(n, attempt, records), encoding="utf-8")
    print(f"attempt {n}: {overall}. Wrote {out.as_posix()}/attempt.json and summary.md")
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
