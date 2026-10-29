"""Compare sp80022 with NIST STS 2.1.2 p-value by p-value (T028, research R3d).

Runs in WSL, where STS was built (T027). Inputs:
  * the four exact expansions (pi, e, sqrt2, sqrt3; 10**6 bits each), also checked against the
    data.* files shipped with STS;
  * NIST's own data.sha1 (Appendix B example 3);
  * the first SEQUENCES sequences of data/controls/cal-1.bin (2**21 bits each).
STS gets each input as a binary file with the default parameters, which equal research R2.
Every p-value must agree to +-1e-6 (STS prints 6 decimals). For Overlapping Template and Linear
Complexity, STS uses different reference constants (research R11), so those are compared after
recomputing our p-value from our counts with STS's constants; our counts must be identical.
"""
from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path

import numpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import sp80022  # noqa: E402
from sp80022.tests_template import _otm_pi  # noqa: E402
from tests import expansions  # noqa: E402

OUT = ROOT / "reports" / "002-core-dynamics-redesign" / "harness"
TOL = 1e-6
SEQUENCES = 10
STS_LC_PI = [0.01047, 0.03125, 0.125, 0.5, 0.25, 0.0625, 0.020833]
# STS result directory for each sp80022 test, in battery order.
STS_DIRS = {"frequency": "Frequency", "block_frequency": "BlockFrequency", "runs": "Runs",
            "longest_run": "LongestRun", "rank": "Rank", "dft": "FFT",
            "non_overlapping_template": "NonOverlappingTemplate",
            "overlapping_template": "OverlappingTemplate", "universal": "Universal",
            "linear_complexity": "LinearComplexity", "serial": "Serial",
            "approximate_entropy": "ApproximateEntropy", "cumulative_sums": "CumulativeSums",
            "random_excursions": "RandomExcursions",
            "random_excursions_variant": "RandomExcursionsVariant"}


def chi2_p(nu, N, pi, dof):
    from scipy.special import gammaincc
    nu, pi = numpy.array(nu), numpy.array(pi)
    chi2 = float(((nu - N * pi) ** 2 / (N * pi)).sum())
    return float(gammaincc(dof / 2.0, chi2 / 2.0))


def run_sts(sts: Path, data: Path, n_bits: int, streams: int):
    """Run STS non-interactively on a binary file; return {sts_dir: [floats]}."""
    answers = f"0\n{data}\n1\n0\n{streams}\n1\n"
    proc = subprocess.run(["./assess", str(n_bits)], cwd=sts, input=answers, text=True,
                          capture_output=True, timeout=7200)
    if "Statistical Testing Complete" not in proc.stdout:
        raise RuntimeError(f"STS did not complete:\n{proc.stdout[-2000:]}\n{proc.stderr}")
    out = {}
    for d in STS_DIRS.values():
        path = sts / "experiments" / "AlgorithmTesting" / d / "results.txt"
        out[d] = [float(x) for x in path.read_text().split()]
    return out


def ours_for_sts(r: sp80022.TestResult):
    """Our p-values, with OTM and LC recomputed from our counts using STS's constants."""
    if r.name == "overlapping_template":
        return [chi2_p(r.stats["nu"], r.stats["N"], _otm_pi(9, 1032, 5), 5)]
    if r.name == "linear_complexity":
        return [chi2_p(r.stats["nu"], r.stats["N"], STS_LC_PI, 6)]
    return r.p_values


def compare(label, bits_list, sts_out):
    rows, worst = [], 0.0
    for name, sts_dir in STS_DIRS.items():
        values = sts_out[sts_dir]
        per = len(values) // len(bits_list)
        # A count that is not a whole multiple would misalign every sequence after the first.
        mismatches, max_diff = (0 if per * len(bits_list) == len(values) else 1), 0.0
        for k, bits in enumerate(bits_list):
            r = getattr(sp80022.tests, name)(bits)
            theirs = values[k * per:(k + 1) * per]
            if not r.eligible:
                # STS writes zeros for an ineligible excursion sequence.
                ok = all(v == 0.0 for v in theirs)
                mismatches += 0 if ok else 1
                continue
            mine = ours_for_sts(r)
            if len(mine) != len(theirs):
                mismatches += 1
                continue
            diffs = [abs(a - b) for a, b in zip(mine, theirs)]
            max_diff = max(max_diff, max(diffs))
            mismatches += sum(d > TOL for d in diffs)
        worst = max(worst, max_diff)
        rows.append({"input": label, "test": name, "values_per_sequence": per,
                     "max_abs_diff": max_diff, "mismatches": mismatches})
    return rows, worst


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sts-dir", type=Path,
                        default=Path.home() / "nist-sts" / "sts-2.1.2" / "sts-2.1.2")
    parser.add_argument("--work", type=Path, default=Path.home() / "nist-sts" / "work")
    args = parser.parse_args()
    args.work.mkdir(parents=True, exist_ok=True)
    sts = args.sts_dir
    report = {"sts_dir": str(sts), "tolerance": TOL, "rows": [], "expansion_files": {}}

    def sts_data_bits(name):
        """STS ships data.pi/e/sqrt2/sqrt3 as ASCII 0/1 text and data.sha1 as packed bytes."""
        raw = (sts / "data" / f"data.{name}").read_bytes()
        if name == "sha1":
            return numpy.unpackbits(numpy.frombuffer(raw, dtype=numpy.uint8))[:1_000_000]
        digits = numpy.frombuffer(raw, dtype=numpy.uint8)
        digits = digits[(digits == ord("0")) | (digits == ord("1"))] - ord("0")
        return digits[:1_000_000]

    inputs = []
    for name in ("pi", "e", "sqrt2", "sqrt3"):
        bits = expansions.load(name)
        same = bool((sts_data_bits(name) == bits).all())
        report["expansion_files"][name] = {"equal_to_sts_data_file": same}
        inputs.append((name, [bits], 1_000_000))
    inputs.append(("sha1", [sts_data_bits("sha1")], 1_000_000))
    raw = (ROOT / "data" / "controls" / "cal-1.bin").read_bytes()
    step = 2 ** 21 // 8
    cal = [numpy.unpackbits(numpy.frombuffer(raw[i * step:(i + 1) * step], dtype=numpy.uint8))
           for i in range(SEQUENCES)]
    inputs.append((f"cal-1 first {SEQUENCES}", cal, 2 ** 21))

    worst = 0.0
    for label, bits_list, n_bits in inputs:
        data = args.work / (label.split()[0] + ".bin")
        data.write_bytes(b"".join(numpy.packbits(b).tobytes() for b in bits_list))
        sts_out = run_sts(sts, data, n_bits, len(bits_list))
        rows, w = compare(label, bits_list, sts_out)
        report["rows"].extend(rows)
        worst = max(worst, w)
        bad = [r for r in rows if r["mismatches"]]
        print(f"{label:18s} max |dp| = {w:.2e}  mismatching tests: {[r['test'] for r in bad]}")
    report["max_abs_diff"] = worst
    report["total_mismatches"] = sum(r["mismatches"] for r in report["rows"])
    report["versions"] = {"python": platform.python_version(), "numpy": numpy.__version__,
                          "sp80022": sp80022.__version__,
                          "sp80022_sha256": sp80022.source_sha256(),
                          "gcc": subprocess.run(["gcc", "--version"], capture_output=True,
                                                text=True).stdout.splitlines()[0]}
    report["command"] = "python scripts/sts_oracle_compare.py (in WSL)"
    (OUT / "oracle-compare.json").write_text(json.dumps(report, indent=1) + "\n")
    print("expansion files equal to STS data files:", report["expansion_files"])
    print("total mismatches:", report["total_mismatches"], " max |dp|:", worst)
    shutil.rmtree(args.work, ignore_errors=True)
    return 0 if report["total_mismatches"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
