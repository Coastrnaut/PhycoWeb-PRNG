"""Vein descent from any state for phyco-v2 (security.md section 9.2, finding S15).

S12 shows that every vein value stays in 0...2^31 once it is there, as the reset values are.
S15 extends this to every starting state: while D > 2^31 (class 2 or 3) the decay D >> 4 is at
least 2^27 and the growth A >> 2 at most 2^26, so D falls by at least 2^26 per step and never
wraps. Every vein is therefore at most 2^31 within 32 steps, and S12 keeps it there.

Evaluates the per-class bounds, iterates the worst-case envelope from D = 2^32 - 1 to find the
most steps any vein can need, and runs the bit-exact reference model from arbitrary states with
every vein above 2^31, checking the bound at every step. Then gives the resulting bound on the
secret states of a 2x2 ring that keeps the design-1.0 vein update.

The starting states are arbitrary 272-bit states from a fixed random.Random seed, not from the
seed interface, which never produces them. No development or held-out seed is used. Writes
research/security/vein-descent.json.

Structural analysis only: not an acceptance result and not evidence of security.
"""
from __future__ import annotations

import hashlib
import json
import math
import platform
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phycoweb import model_v2  # noqa: E402
from phycoweb.model_v2 import M32, SIGN32, PhycoWebEngineV2, _flux  # noqa: E402

OUT = HERE / "vein-descent.json"
PROBES = HERE / "step-probes.json"
EDGE = 1 << 31
RNG_SEED = 15
STARTS = 2_000
STEPS = 64
TAIL_STARTS = 100
TAIL_STEPS = 1_000


def max_growth(c: int) -> int:
    """Largest growth term A >> 2 in class c: the most negative difference gives the largest |Q|."""
    q = _flux(SIGN32, c)
    return (((q ^ M32) + 1) & M32) >> 2


def envelope_step(x: int) -> int:
    """Largest next value of any vein value D with 2^31 < D <= x (design.md section 4 step 4).

    Within a class D + max_growth - (D >> 4) never decreases as D grows, so the largest D of each
    class up to x bounds that class.
    """
    best = 0
    for c in (2, 3):
        lo, hi = max(EDGE + 1, c << 30), min(x, ((c + 1) << 30) - 1)
        if lo <= hi:
            best = max(best, hi + max_growth(c) - (hi >> 4))
    return best


def bounds() -> dict:
    rows = []
    for c in (2, 3):
        lowest = max(EDGE + 1, c << 30)
        g = max_growth(c)
        rows.append({"class": c, "max_growth": g, "min_decay": lowest >> 4,
                     "min_drop_per_step": (lowest >> 4) - g})
    drop = min(r["min_drop_per_step"] for r in rows)
    trajectory = [M32]
    while trajectory[-1] > EDGE:
        trajectory.append(envelope_step(trajectory[-1]))
    return {"above_2_31": rows, "min_drop_per_step": drop,
            "steps_bound_simple": -(-(M32 - EDGE) // drop),
            "envelope_from_2_32_minus_1": [hex(x) for x in trajectory],
            "steps_bound_envelope": len(trajectory) - 1}


def engine(p: tuple, d: tuple, phase_a: int, phase_b: int) -> PhycoWebEngineV2:
    e = PhycoWebEngineV2.__new__(PhycoWebEngineV2)
    e.P, e.D = list(p), list(d)
    e.phase_a, e.phase_b, e.disruptions, e.step_count = phase_a, phase_b, 0, 0
    return e


def starts() -> list:
    """Four fixed edge cases, one with the largest first-step flux, then random states."""
    rng = random.Random(RNG_SEED)
    fixed = [(M32,) * 4, (EDGE + 1,) * 4, ((3 << 30) - 1,) * 4, (3 << 30,) * 4]
    out = [engine((SIGN32, 0, SIGN32, 0), (M32,) * 4, 0, 0)]
    for i in range(STARTS - 1):
        if i < len(fixed):
            d = fixed[i]
        else:
            d = tuple(rng.randrange(EDGE + 1, 1 << 32) for _ in range(4))
        p = tuple(rng.getrandbits(32) for _ in range(4))
        out.append(engine(p, d, rng.getrandbits(8), rng.getrandbits(8)))
    return out


def model_check() -> dict:
    worst = checked = drop_fail = wrap_fail = above = after = 0
    for i, e in enumerate(starts()):
        entered = None
        for t in range(1, STEPS + 1):
            before = list(e.D)
            e._step()
            for d0, d1 in zip(before, e.D):
                if d0 > EDGE:
                    checked += 1
                    drop_fail += d1 > d0 - (1 << 26)
                    wrap_fail += d1 < d0 - (d0 >> 4)
            if entered is None:
                if all(d <= EDGE for d in e.D):
                    entered = t
            else:
                after += 1
                above += any(d > EDGE for d in e.D)
        assert entered is not None, "a vein stayed above 2^31 for every step"
        worst = max(worst, entered)
        for _ in range(TAIL_STEPS if i < TAIL_STARTS else 0):
            e._step()
            after += 1
            above += any(d > EDGE for d in e.D)
    return {"starts": STARTS, "rng": f"random.Random({RNG_SEED})", "steps_per_start": STEPS,
            "tail_starts": TAIL_STARTS, "tail_steps": TAIL_STEPS,
            "vein_steps_above_2_31_checked": checked,
            "steps_not_dropping_by_2_26": drop_fail, "steps_below_d_minus_decay": wrap_fail,
            "max_steps_until_all_veins_at_most_2_31": worst,
            "steps_after_entry": after, "steps_after_entry_with_a_vein_above_2_31": above}


def state_bound() -> dict:
    d_range = json.loads(PROBES.read_text(encoding="utf-8"))["s14_bit_bias"]["d_range"]
    lo, hi = (int(x, 16) for x in d_range)
    return {"secret_bits_nominal_2x2": 256,
            "log2_states_after_entry_at_most": round(128 + 4 * math.log2(EDGE + 1), 4),
            "s14_d_range": d_range,
            "s14_values_per_vein_over_2_30": round((hi - lo + 1) / 2 ** 30, 4),
            "log2_estimate_from_s14_range": round(128 + 4 * math.log2(hi - lo + 1), 2),
            "log2_needed_by_fut_sec_2_for_128_bits": 256}


def main() -> int:
    record = {
        "finding": "security.md section 9.2, S15",
        "model_id": model_v2.MODEL_ID,
        "model_sha256": hashlib.sha256((ROOT / "phycoweb" / "model_v2.py").read_bytes()).hexdigest(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "command": "python -I research/security/vein_descent.py",
        "bounds": bounds(),
        "model_check": model_check(),
        "state_bound": state_bound(),
        "note": "Structural analysis only: not an acceptance result and not evidence of security.",
    }
    OUT.write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8", newline="\n")
    for key in ("bounds", "model_check", "state_bound"):
        print(key, json.dumps(record[key]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
