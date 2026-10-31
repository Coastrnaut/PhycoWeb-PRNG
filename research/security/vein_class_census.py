"""Conductance-class census for phyco-v2 (security.md section 9.2, finding S12).

Evaluates the bounds that show classes 2 and 3 are in effect unused: the largest |Q| in each
class c = D >> 30 and the largest next vein value D' that any D in the class can produce. Then
runs the bit-exact reference model on fixed seeds and counts, after the 256-step warm-up, how
often each vein value falls in each class, how often the class changes, the largest D seen,
how often bit 31 of D is set and how often the disruption fires.

Seeds: the first development seed (feature-002 `dev` set) and the two all-equal edge seeds.
No held-out seed is used. Writes research/security/vein-class-census.json.

Structural analysis only: not an acceptance result and not evidence of security.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phycoweb import model_v2  # noqa: E402
from phycoweb.model_v2 import M32, SIGN32, PhycoWebEngineV2, _flux  # noqa: E402

OUT = HERE / "vein-class-census.json"
SEEDS = [(56053, 7029, 30841, 11050), (0, 0, 0, 0), (65535, 65535, 65535, 65535)]
STEPS = 200_000


def next_d(d: int, a: int) -> int:
    """design.md section 4 step 4, as in model_v2: D' = (D + (A >> 2) - (D >> 4)) mod 2^32."""
    return (d + (a >> 2) - (d >> 4)) & M32


def bounds() -> dict:
    # The most negative difference, 0x80000000, gives the largest |Q| in every class. Since
    # D - (D >> 4) never decreases as D grows, the top of a class bounds the next D for the class.
    classes = []
    for c in range(4):
        q = _flux(SIGN32, c)
        a = ((q ^ M32) + 1) & M32
        top = ((c + 1) << 30) - 1
        classes.append({"class": c, "max_abs_q": a, "max_growth": a >> 2,
                        "class_top": hex(top), "max_next_d": hex(next_d(top, a))})
    edge = 1 << 31
    return {"classes": classes,
            "from_2_31": {"d": hex(edge), "max_next_d": hex(next_d(edge, classes[2]["max_abs_q"]))},
            "reset_values": [hex(d) for d in (0x00010000 << k for k in range(4))]}


def census(seed: tuple, steps: int) -> dict:
    e = PhycoWebEngineV2(list(seed))
    counts = [0, 0, 0, 0]
    prev = [d >> 30 for d in e.D]
    changes = bit31 = max_d = 0
    start = e.disruptions
    for _ in range(steps):
        e.compute_block()
        for k, d in enumerate(e.D):
            c = d >> 30
            counts[c] += 1
            changes += c != prev[k]
            prev[k] = c
            bit31 += d >> 31
            if d > max_d:
                max_d = d
    return {"seed": list(seed), "class_counts": counts, "class_changes": changes,
            "max_d": hex(max_d), "max_d_over_2_30": round(max_d / 2 ** 30, 4),
            "bit31_set": bit31, "disruption_steps": e.disruptions - start}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--steps", type=int, default=STEPS)
    args = ap.parse_args()
    rows = [census(s, args.steps) for s in SEEDS]
    total = [sum(r["class_counts"][c] for r in rows) for c in range(4)]
    n = sum(total)
    record = {
        "finding": "security.md section 9.2, S12",
        "model_id": model_v2.MODEL_ID,
        "model_sha256": hashlib.sha256((ROOT / "phycoweb" / "model_v2.py").read_bytes()).hexdigest(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "command": "python -I research/security/vein_class_census.py --steps " + str(args.steps),
        "warmup": model_v2.WARMUP,
        "steps_per_seed": args.steps,
        "seeds": "first dev seed (feature-002 dev set) and the two all-equal edge seeds",
        "bounds": bounds(),
        "census": rows,
        "totals": {"vein_values": n, "class_counts": total,
                   "class_share": [round(t / n, 4) for t in total],
                   "bit31_set": sum(r["bit31_set"] for r in rows)},
        "note": "Structural analysis only: not an acceptance result and not evidence of security.",
    }
    OUT.write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(record["totals"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
