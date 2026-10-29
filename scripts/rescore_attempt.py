"""Re-score an acceptance attempt and check it reproduces exactly (T050; SC-004, quickstart A4).

The positive control is re-scored from its saved bytes (whose SHA-256 must match the record).
Both models are regenerated from the recorded seeds. Every p-value, family and verdict must
be identical to the attempt's eval records. The attempt's own files are never modified; the
result goes to attempt-N/rescore.json. Exit 0 if identical, 1 if not, 2 if inputs are missing.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import evalcore
from evalcore import ROOT
from protocol import freeze

COMPARED = ("sequences", "subtests", "families", "families_failed", "verdict", "n_bits")


def rescore(record: dict, workers: int) -> dict:
    n_bits = record["n_bits"]
    if record["source"] == "os-csprng":
        path = ROOT / record["bytes_file"]
        if evalcore.sha256_file(path) != record["bytes_sha256"]:
            raise ValueError(f"{path} SHA-256 differs from the attempt record")
        raw = path.read_bytes()
        step = n_bits // 8
        jobs = [(i, "bytes", raw[i * step:(i + 1) * step], n_bits, 0)
                for i in range(len(raw) // step)]
    else:
        jobs = [(i, "model", (record["source"], list(s)), n_bits, 0)
                for i, s in enumerate(record["seeds"])]
    per_sequence = evalcore.run_jobs(jobs, workers)
    return evalcore.build_record(record["source"], per_sequence, seed_set=record["seed_set"],
                                 seeds=record["seeds"], n_bits=n_bits, command="rescore",
                                 workers=workers, started=time.time())


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=int, required=True)
    parser.add_argument("--workers", type=int, default=evalcore.default_workers())
    args = parser.parse_args(argv)
    out = freeze.attempt_dir(args.attempt)
    if not (out / "attempt.json").is_file():
        print(f"no attempt record in {out}", file=sys.stderr)
        return 2
    attempt = json.loads((out / "attempt.json").read_text(encoding="utf-8"))
    result = {"attempt": args.attempt, "roles": {}, "date": time.strftime("%Y-%m-%dT%H:%M:%S")}
    for role in ("positive", "negative", "candidate"):
        entry = attempt[role]
        if not isinstance(entry, dict):
            result["roles"][role] = {"status": entry}
            continue
        original = json.loads((out / entry["record"]).read_text(encoding="utf-8"))
        try:
            again = rescore(original, args.workers)
        except (OSError, ValueError) as exc:
            print(f"{role}: cannot re-score: {exc}", file=sys.stderr)
            return 2
        differing = [k for k in COMPARED if again.get(k) != original.get(k)]
        result["roles"][role] = {"identical": not differing, "differing_fields": differing,
                                 "verdict": again["verdict"]}
        print(f"{role}: {'identical' if not differing else 'DIFFERS in ' + ', '.join(differing)}")
    result["identical"] = all(r.get("identical", True) for r in result["roles"].values())
    (out / "rescore.json").write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    print(f"attempt {args.attempt} re-score: {'identical' if result['identical'] else 'DIFFERS'}")
    return 0 if result["identical"] else 1


if __name__ == "__main__":
    sys.exit(main())
