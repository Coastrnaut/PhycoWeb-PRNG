"""Positive-control calibration runner (feature 003 US1; FR-001, FR-002, FR-005, FR-006).

Each run draws 100 sequences of 2^21 bits from os.urandom, scores them with the frozen
sp80022 1.0.0 harness and the feature-002 rules (sp80022.assess) through the same worker as
scripts/evalcore.py, and writes one gzip JSON record. No byte is written to disk: only the
SHA-256 of the run's input, in sequence order. Records are append-only (research R2).
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import sys
import time
from multiprocessing import get_context
from pathlib import Path
from typing import Callable, List, Sequence

ROOT = Path(__file__).resolve().parents[1]
for p in (str(ROOT), str(ROOT / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import evalcore  # noqa: E402
import sp80022  # noqa: E402
from protocol.disclaimer import DISCLAIMER  # noqa: E402

HARNESS_SHA256 = "1563526ed25f695dba223c3d62c8ce900ba4f485dd62f09a694ece0602c41700"
N_SEQUENCES = 100
N_BITS = evalcore.N_BITS
RUNS = 1000


def run_path(out_dir: Path, run: int) -> Path:
    return out_dir / f"run-{run:04d}.json.gz"


def parse_range(text: str) -> List[int]:
    lo, _, hi = text.partition("-")
    lo, hi = int(lo), int(hi or lo)
    if not 0 <= lo <= hi < RUNS:
        raise ValueError(f"run range must lie within 0-{RUNS - 1}, got {text!r}")
    return list(range(lo, hi + 1))


def draw_sequences(n: int, n_bits: int, rand: Callable[[int], bytes] = os.urandom):
    """Return (sequences, sha256 of their concatenation in order)."""
    digest = hashlib.sha256()
    out = []
    for _ in range(n):
        raw = rand(n_bits // 8)
        digest.update(raw)
        out.append(raw)
    return out, digest.hexdigest()


def score(pool, sequences: Sequence[bytes], n_bits: int):
    """Score byte sequences exactly as evalcore.run_jobs does (same worker, same ordering)."""
    jobs = [(i, "bytes", raw, n_bits, 0) for i, raw in enumerate(sequences)]
    out = pool.map(evalcore._evaluate, jobs, chunksize=1) if pool else [evalcore._evaluate(j) for j in jobs]
    out.sort(key=lambda t: t[0])
    return [[sp80022.TestResult(n, e, p, prm, st) for n, e, p, prm, st in res] for _, res in out]


def build_record(run: int, per_sequence, input_sha256: str, started: float, command: str):
    summary = sp80022.assess(per_sequence)
    record = {
        "run": run,
        "input_sha256": input_sha256,
        "source": "os-csprng (os.urandom)",
        "n_sequences": len(per_sequence),
        "n_bits": N_BITS,
        "bit_order": "msb-first",
        "harness_version": sp80022.__version__,
        "harness_sha256": sp80022.source_sha256(),
        "sequences": [{r.name: {"eligible": r.eligible, "p_values": r.p_values} for r in seq}
                      for seq in per_sequence],
        "subtests": summary["subtests"],
        "families": summary["families"],
        "families_failed": [n for n, f in summary["families"].items() if not f["pass"]],
        "verdict": "pass" if summary["pass"] else "fail",
        "versions": evalcore.versions(),
        "git_head": evalcore._git("rev-parse", "--short", "HEAD"),
        "command": command,
        "started": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(started)),
        "elapsed_s": round(time.time() - started, 1),
        "disclaimer": DISCLAIMER,
    }
    return evalcore._json_safe(record)


def write_run(path: Path, record) -> None:
    tmp = path.with_suffix(".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8") as fh:
        json.dump(record, fh)
    os.replace(tmp, path)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", required=True, help="inclusive range, e.g. 0-999")
    parser.add_argument("--workers", type=int, default=evalcore.default_workers())
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--resume", action="store_true",
                        help="skip existing run files at the start of the range")
    args = parser.parse_args(argv)
    try:
        runs = parse_range(args.runs)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 2
    if sp80022.source_sha256() != HARNESS_SHA256:
        print(f"sp80022 source hash {sp80022.source_sha256()} != frozen {HARNESS_SHA256}",
              file=sys.stderr)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    existing = [r for r in runs if run_path(args.out_dir, r).exists()]
    if existing and not args.resume:
        print(f"run files already exist (first: {existing[0]}); use --resume", file=sys.stderr)
        return 2
    if args.resume:
        while runs and run_path(args.out_dir, runs[0]).exists():
            runs.pop(0)
        later = [r for r in runs if run_path(args.out_dir, r).exists()]
        if later:
            print(f"gap in existing run files before run {later[0]}; refusing", file=sys.stderr)
            return 2
    command = "python " + " ".join([Path(sys.argv[0]).as_posix()] + sys.argv[1:])
    pool = get_context("spawn").Pool(args.workers) if args.workers > 1 else None
    try:
        for run in runs:
            started = time.time()
            sequences, digest = draw_sequences(N_SEQUENCES, N_BITS)
            per_sequence = score(pool, sequences, N_BITS)
            record = build_record(run, per_sequence, digest, started, command)
            write_run(run_path(args.out_dir, run), record)
            print(f"run {run:04d} {record['verdict']} {record['families_failed']} "
                  f"{record['elapsed_s']} s", flush=True)
    finally:
        if pool:
            pool.close()
            pool.join()
    return 0


if __name__ == "__main__":
    sys.exit(main())
