"""Reproduce the nistrng 1.2.3 defects N4-N9 on OS-CSPRNG input (feature 002, research R1).

Runs every nistrng SP 800-22 test on SEQUENCES sequences of 2**21 bits from os.urandom. Each
test gets its own copy of the bits and random.seed(0) before it runs; all `_score_list`
p-values are recorded. An ideal source gives p-values spread evenly over [0, 1], so a test
that returns p ~ 0 (or p ~ 1) on every sequence is not measuring its input.
"""
import json
import os
import platform
import random
import sys
import warnings
from multiprocessing import Pool
from pathlib import Path

import numpy

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "002-core-dynamics-redesign" / "harness" / "nistrng-defects.json"
N_BITS = 2 ** 21
SEQUENCES = 4

# Defect id -> (test name, how the symptom is recognised in the p-values of all sequences).
DEFECTS = {
    "N4": ("non_overlapping_template_matching", lambda ps: all(p >= 0.999999 for p in ps)),
    "N5": ("overlapping_template_matching", lambda ps: all(p < 1e-3 for p in ps)),
    "N6": ("random_excursion", lambda ps: sum(p < 1e-3 for p in ps) >= 0.9 * len(ps)),
    "N7": ("maurers_universal", lambda ps: all(p > 0.99 for p in ps)),
    "N8": ("linear_complexity", lambda ps: all(p < 1e-3 for p in ps)),
    # Found while running this script: p-values above 1 are impossible.
    "N9": ("random_excursion_variant", lambda ps: any(p > 1.0 for p in ps)),
}


def run_sequence(raw: bytes):
    import nistrng
    warnings.simplefilter("ignore")
    bits = numpy.unpackbits(numpy.frombuffer(raw, dtype=numpy.uint8)).astype(numpy.int64)
    out = {}
    for name, test in nistrng.SP800_22R1A_BATTERY.items():
        if not test.is_eligible(bits.copy()):
            out[name] = None
            continue
        random.seed(0)
        result, _ = test.run(bits.copy())
        out[name] = [float(p) for p in numpy.atleast_1d(result._score_list)]
    return out


def main() -> int:
    import nistrng
    import scipy
    raws = [os.urandom(N_BITS // 8) for _ in range(SEQUENCES)]
    with Pool(SEQUENCES) as pool:
        per_seq = pool.map(run_sequence, raws)
    tests = {}
    for name in per_seq[0]:
        tests[name] = [seq[name] for seq in per_seq]
        print(f"{name:36s}", [None if ps is None else [round(p, 4) for p in ps] for ps in tests[name]])
    findings = {}
    for defect, (name, symptom) in DEFECTS.items():
        pooled = [p for ps in tests[name] if ps for p in ps]
        findings[defect] = {"test": name, "reproduced": bool(pooled) and symptom(pooled)}
        print(defect, name, "REPRODUCED" if findings[defect]["reproduced"] else "NOT reproduced")
    record = {
        "purpose": "reproduce nistrng 1.2.3 defects N4-N9 on os.urandom input (research R1)",
        "n_bits": N_BITS,
        "sequences": SEQUENCES,
        "source": "os.urandom (not stored)",
        "per_test_p_values": tests,
        "findings": findings,
        "versions": {"python": platform.python_version(), "platform": platform.platform(),
                     "numpy": numpy.__version__, "scipy": scipy.__version__,
                     "nistrng": getattr(nistrng, "__version__", "1.2.3")},
        "command": "python " + " ".join([Path(sys.argv[0]).as_posix()] + sys.argv[1:]),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print("wrote", OUT.relative_to(ROOT).as_posix())
    return 0 if all(f["reproduced"] for f in findings.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
