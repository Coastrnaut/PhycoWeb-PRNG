"""Cross-check the DFT excess found by the calibration (feature 003 US1, T011 follow-up).

  dft_crosscheck.py [--fresh 1000] [--workers 32]      (run in WSL; needs NIST STS 2.1.2)

Part A uses the stored calibration p-values (100,000 per test) and needs no new data:
per-sequence rejection rate at alpha = 0.01 for dft and, as a control, frequency; and
E[d^2] for dft, recovered from p = erfc(|d| / sqrt 2). If the statistic is standardized
correctly, E[d^2] = 1.
Part B draws fresh os.urandom sequences (2^21 bits each, as in the calibration), runs the
sp80022 dft and NIST STS 2.1.2 DFT (menu test 7 only) on the same bytes, compares the p-values
(+-1e-6, as in feature 002 T028) and measures the variance of N1 directly. The bytes are
deleted afterwards. Nothing in the harness, the rules or the calibration is changed.
Writes reports/003-extended-batteries-calibration/calibration/dft-crosscheck.json.
"""
from __future__ import annotations

import argparse
import gzip
import json
import math
import os
import platform
import shutil
import subprocess
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy
from scipy import special, stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import sp80022  # noqa: E402
from protocol.disclaimer import DISCLAIMER  # noqa: E402

REP = ROOT / "reports" / "003-extended-batteries-calibration" / "calibration"
N_BITS = 2 ** 21
ALPHA = 0.01
TOL = 1e-6


def ci(k, n):
    lo = 0.0 if k == 0 else float(stats.beta.ppf(0.025, k, n - k + 1))
    hi = 1.0 if k == n else float(stats.beta.ppf(0.975, k + 1, n - k))
    return [lo, hi]


def mean_ci(x):
    m, se = float(numpy.mean(x)), float(numpy.std(x, ddof=1) / math.sqrt(len(x)))
    return {"mean": m, "ci95": [m - 1.96 * se, m + 1.96 * se], "n": len(x)}


def stored():
    p = {"dft": [], "frequency": []}
    for f in sorted((REP / "runs").glob("run-*.json.gz")):
        for seq in json.load(gzip.open(f))["sequences"]:
            for name in p:
                p[name] += seq[name]["p_values"]
    out = {}
    for name, values in p.items():
        v = numpy.array(values)
        k = int((v < ALPHA).sum())
        out[name] = {"sequences": len(v), "rejected": k, "rate": k / len(v), "ci95": ci(k, len(v))}
    d2 = 2.0 * special.erfcinv(numpy.clip(numpy.array(p["dft"]), 1e-300, 1.0)) ** 2
    out["dft"]["E_d2"] = mean_ci(d2)
    return out


def _ours(chunk: bytes):
    r = sp80022.tests.dft(numpy.unpackbits(numpy.frombuffer(chunk, dtype=numpy.uint8)))
    return r.p_values[0], r.stats["N1"]


def fresh(n: int, workers: int, sts: Path, work: Path):
    work.mkdir(parents=True, exist_ok=True)
    data = work / "dft-fresh.bin"
    step = N_BITS // 8
    raw = os.urandom(n * step)
    data.write_bytes(raw)
    with Pool(workers) as pool:
        ours = pool.map(_ours, [raw[i * step:(i + 1) * step] for i in range(n)])
    # STS menu order: 07 is the Discrete Fourier Transform.
    answers = f"0\n{data}\n0\n000000100000000\n{n}\n1\n"
    results = sts / "experiments" / "AlgorithmTesting" / "FFT" / "results.txt"
    results.unlink(missing_ok=True)
    proc = subprocess.run(["./assess", str(N_BITS)], cwd=sts, input=answers, text=True,
                          capture_output=True, timeout=7200)
    if "Statistical Testing Complete" not in proc.stdout:
        raise RuntimeError(f"STS did not complete:\n{proc.stdout[-2000:]}\n{proc.stderr}")
    theirs = [float(x) for x in results.read_text().split()]
    shutil.rmtree(work, ignore_errors=True)
    if len(theirs) != n:
        raise RuntimeError(f"STS gave {len(theirs)} p-values for {n} sequences")
    p = numpy.array([o[0] for o in ours])
    n1 = numpy.array([o[1] for o in ours], dtype=float)
    diffs = numpy.abs(p - numpy.array(theirs))
    k = int((p < ALPHA).sum())
    var_n1 = float(numpy.var(n1, ddof=1))
    return {"sequences": n, "max_abs_diff_vs_sts": float(diffs.max()),
            "mismatches_vs_sts": int((diffs > TOL).sum()),
            "rejected": k, "rate": k / n, "ci95": ci(k, n),
            "N1_mean": float(n1.mean()), "N0": 0.95 * N_BITS / 2,
            "N1_variance": var_n1,
            "N1_variance_ci95": [var_n1 * (n - 1) / float(stats.chi2.ppf(0.975, n - 1)),
                                 var_n1 * (n - 1) / float(stats.chi2.ppf(0.025, n - 1))],
            "variance_used_by_test": N_BITS * 0.95 * 0.05 / 4,
            "denominator_implied": N_BITS * 0.95 * 0.05 / var_n1}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fresh", type=int, default=1000)
    parser.add_argument("--workers", type=int, default=32)
    parser.add_argument("--sts-dir", type=Path,
                        default=Path.home() / "nist-sts" / "sts-2.1.2" / "sts-2.1.2")
    parser.add_argument("--work", type=Path, default=Path.home() / "nist-sts" / "work-dft")
    args = parser.parse_args()
    report = {"stored": stored()}
    print(json.dumps(report["stored"], indent=1))
    report["fresh"] = fresh(args.fresh, args.workers, args.sts_dir, args.work)
    print(json.dumps(report["fresh"], indent=1))
    report["versions"] = {"python": platform.python_version(), "numpy": numpy.__version__,
                          "sp80022": sp80022.__version__,
                          "sp80022_sha256": sp80022.source_sha256(), "sts": str(args.sts_dir)}
    report["command"] = f"python scripts/dft_crosscheck.py --fresh {args.fresh} (in WSL)"
    report["disclaimer"] = DISCLAIMER
    (REP / "dft-crosscheck.json").write_text(json.dumps(report, indent=1) + "\n")
    return 0 if report["fresh"]["mismatches_vs_sts"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
