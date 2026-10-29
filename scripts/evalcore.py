"""Shared evaluation code for sts_eval.py and acceptance.py (data-model section 4; R5, R7).

Each worker evaluates one whole sequence. Results are keyed by sequence index and sorted, so
the record does not depend on the worker count or on completion order (FR-013).
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from multiprocessing import get_context
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import numpy

ROOT = Path(__file__).resolve().parents[1]
for p in (str(ROOT), str(ROOT / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import sp80022  # noqa: E402
from protocol.disclaimer import DISCLAIMER  # noqa: E402

N_BITS = 2 ** 21
MODEL_SOURCES = ("phyco-v2", "lut-v1")
LIMITATIONS = [
    "Passing SP 800-22 shows only that these tests detected no statistical defect; it is not "
    "evidence of cryptographic security.",
    "Positive-control bytes are stored only locally (data/controls/, owner decision Q1); only "
    "this machine can re-score them.",
    "Only the NIST SP 800-22 battery is run; broader batteries (PractRand, TestU01, "
    "Dieharder) are not.",
]


def model_bits(model: str, seed: Sequence[int], n_bits: int, skip_words: int = 0) -> numpy.ndarray:
    from gen_vectors import word_source
    next_word = word_source(model, seed)
    for _ in range(skip_words):
        next_word()
    n_words = n_bits // 32
    words = numpy.fromiter((next_word() for _ in range(n_words)), dtype=">u4", count=n_words)
    return numpy.unpackbits(words.view(numpy.uint8))


def bytes_bits(raw: bytes) -> numpy.ndarray:
    return numpy.unpackbits(numpy.frombuffer(raw, dtype=numpy.uint8))


def _evaluate(job):
    index, kind, payload, n_bits, skip_words = job
    if kind == "model":
        model, seed = payload
        bits = model_bits(model, seed, n_bits, skip_words)
    else:
        bits = bytes_bits(payload)
    results = sp80022.battery(bits)
    return index, [(r.name, r.eligible, [float(p) for p in r.p_values], r.params, r.stats)
                   for r in results]


def run_jobs(jobs: List[tuple], workers: int) -> List[List[sp80022.TestResult]]:
    if workers <= 1 or len(jobs) == 1:
        out = [_evaluate(j) for j in jobs]
    else:
        with get_context("spawn").Pool(workers) as pool:
            out = pool.map(_evaluate, jobs, chunksize=1)
    out.sort(key=lambda t: t[0])
    return [[sp80022.TestResult(n, e, p, prm, st) for n, e, p, prm, st in res] for _, res in out]


def _git(*args: str) -> str:
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True,
                              check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def versions() -> Dict[str, str]:
    import scipy
    return {"python": platform.python_version(), "platform": platform.platform(),
            "numpy": numpy.__version__, "scipy": scipy.__version__,
            "sp80022": sp80022.__version__}


def _json_safe(value):
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, numpy.generic):
        return value.item()
    return value


def build_record(source: str, per_sequence, *, seed_set: Optional[str], seeds, n_bits: int,
                 command: str, workers: int, started: float, extra: Optional[Dict] = None):
    summary = sp80022.assess(per_sequence)
    record = {
        "source": source,
        "seed_set": seed_set,
        "seeds": seeds,
        "n_bits": n_bits,
        "bit_order": "msb-first",
        "harness_version": sp80022.__version__,
        "harness_sha256": sp80022.source_sha256(),
        "parameters": {r.name: r.params for r in per_sequence[0]},
        "sequences": [{r.name: {"eligible": r.eligible, "p_values": r.p_values} for r in seq}
                      for seq in per_sequence],
        "subtests": summary["subtests"],
        "families": summary["families"],
        "families_failed": [n for n, f in summary["families"].items() if not f["pass"]],
        "verdict": "pass" if summary["pass"] else "fail",
        "git_head": _git("rev-parse", "--short", "HEAD"),
        "git_dirty": bool(_git("status", "--porcelain")),
        "versions": versions(),
        "command": command,
        "workers": workers,
        "started": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(started)),
        "elapsed_s": round(time.time() - started, 1),
        "limitations": LIMITATIONS,
        "disclaimer": DISCLAIMER,
    }
    if extra:
        record.update(extra)
    return _json_safe(record)


def write_record(path: Path, record: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def default_workers() -> int:
    return max(1, min(32, os.cpu_count() or 1))
