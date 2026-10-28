"""Run the NIST SP 800-22 battery (nistrng) on a model's output (spec FR-011, FR-014, SC-005).

Exit 0 means the evaluation ran; pass/fail is recorded in the report, never in the exit code.
"""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import platform
import random
import subprocess
import sys
from pathlib import Path
from typing import List

import numpy
import nistrng

from gen_vectors import MODELS, ROOT, generate

TEMPLATE_SEED = 0

LIMITATIONS = [
    "Single sequence per seed; not the multi-sequence proportion/uniformity analysis of SP 800-22.",
    "Passing statistical tests is not evidence of cryptographic security.",
    "Tests are run individually on copies of the bits, not via nistrng.run_all_battery, because "
    "nistrng 1.2.3's Binary Matrix Rank test modifies its input in place.",
    "nistrng's Non-Overlapping Template Matching evaluates ONE randomly chosen template (Python "
    "random seeded with TEMPLATE_SEED before each test), not all 148 templates as in SP 800-22.",
    "p_value is the minimum of a test's p-values; nistrng's own pass/fail (all p-values >= 0.01) "
    "is used for status.",
]


def git_output(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=False)
    return result.stdout.strip()


def bits_msb_first(model: str, seed: List[int], n_bits: int) -> numpy.ndarray:
    words = numpy.fromiter(generate(model, seed, n_bits // 32), dtype=">u4", count=n_bits // 32)
    # Big-endian bytes unpacked MSB-first give each word's bits MSB-first. int64, not int8:
    # nistrng's Cumulative Sums overflows on int8 input (research R6, finding N1).
    return numpy.unpackbits(words.view(numpy.uint8)).astype(numpy.int64)


def evaluate(bits: numpy.ndarray) -> list:
    """Run every battery test on its own copy of the bits.

    nistrng's Binary Matrix Rank test modifies its input in place, so run_all_battery (which
    shares one array) corrupts every later test (research R6, finding N2).
    """
    battery = nistrng.SP800_22R1A_BATTERY
    names = list(battery)
    tests = []
    for name in names:
        test = battery[name]
        if not test.is_eligible(bits.copy()):
            tests.append({"name": name, "status": "not_eligible", "p_value": None,
                          "p_values": None, "elapsed_ms": None})
            continue
        # Non-Overlapping Template Matching picks its template with random.choice; seed it so
        # the run is reproducible (Constitution Principle V).
        random.seed(TEMPLATE_SEED)
        result, elapsed_ms = test.run(bits.copy())
        # Result.score is the mean of a test's p-values; record them all and report the
        # smallest. nistrng exposes the list only as the private _score_list.
        p_values = [float(p) for p in numpy.atleast_1d(result._score_list)]
        tests.append({
            "name": name,
            "status": "pass" if result.passed else "fail",
            "p_value": min(p_values),
            "p_values": p_values,
            "elapsed_ms": elapsed_ms,
        })
    if sorted(t["name"] for t in tests) != sorted(names):
        raise RuntimeError("report does not list every battery test exactly once")
    return tests


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, choices=MODELS)
    parser.add_argument("--seed", required=True, type=int, nargs=4, metavar="S")
    parser.add_argument("--bits", required=True, type=int)
    parser.add_argument("--out", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    if args.bits < 32 or args.bits % 32:
        print("ERROR: --bits must be a positive multiple of 32", file=sys.stderr)
        return 2
    try:
        tests = evaluate(bits_msb_first(args.model, args.seed, args.bits))
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    report = {
        "model": args.model,
        "seed": args.seed,
        "n_bits": args.bits,
        "bit_order": "msb-first",
        "template_seed": TEMPLATE_SEED,
        "git_head": git_output("rev-parse", "HEAD"),
        "git_dirty": bool(git_output("status", "--porcelain")),
        "versions": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "numpy": importlib.metadata.version("numpy"),
            "nistrng": importlib.metadata.version("nistrng"),
        },
        "command": " ".join(["python", "scripts/nist_eval.py", *argv]),
        "tests": tests,
        "limitations": LIMITATIONS,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")

    counts = {s: sum(t["status"] == s for t in tests) for s in ("pass", "fail", "not_eligible")}
    print(f"{args.model} seed={args.seed} bits={args.bits}: {counts} -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
