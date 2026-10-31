"""Structural probes of phyco-v2 (security.md section 9.2, findings S13 and S14).

S13, the step function is not one-to-one:
  - vein decay: D - (D >> 4) is the same for D = 16m + 15 and D = 16m + 16, so two states that
    differ only there (same class) have the same successor;
  - transport: with all four veins in class 1, adding 2v = (2, -2, 2, -2) to the pressures
    leaves the transport sums T unchanged, and the successors coincide when every |Q| >> 2 is
    unchanged too.
S14, the vein values sit near 2^30: ones-frequency of every bit of D and P, and the share of
bits in which two unrelated states differ, predicted from those frequencies.
Also measured, for the redesign checklist: how fast a one-bit seed change spreads from the
initial state (output and state avalanche per step).

Seeds: the first three development seeds (feature-002 `dev` set) and the two all-equal edge
seeds. No held-out seed is used. Writes research/security/step-probes.json.

Structural analysis only: not an acceptance result and not evidence of security.
"""
from __future__ import annotations

import hashlib
import json
import platform
import sys
from array import array
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phycoweb import model_v2  # noqa: E402
from phycoweb.lut import COS_OFFSET, INC_A, INC_B, PERTURBATION_LUT  # noqa: E402
from phycoweb.model_v2 import M32, SIGN32, PhycoWebEngineV2, _flux, _sext16  # noqa: E402
from protocol import seedsets  # noqa: E402

OUT = HERE / "step-probes.json"
DEV = seedsets.load("dev", allow=("dev",))[:3]
EDGE = [(0, 0, 0, 0), (65535, 65535, 65535, 65535)]
DECAY_STEPS = 5_000
ALT_STEPS = 100_000
BIAS_STEPS = 200_000
V2 = (2, M32 - 1, 2, M32 - 1)          # 2v = (2, -2, 2, -2) mod 2^32


def clone(e: PhycoWebEngineV2) -> PhycoWebEngineV2:
    c = PhycoWebEngineV2.__new__(PhycoWebEngineV2)
    c.P, c.D = list(e.P), list(e.D)
    c.phase_a, c.phase_b, c.disruptions, c.step_count = e.phase_a, e.phase_b, 0, e.step_count
    return c


def raw_engine(seed) -> PhycoWebEngineV2:
    """Engine at step 0, before the warm-up: design.md section 3, as in model_v2."""
    s = list(seed)
    e = PhycoWebEngineV2.__new__(PhycoWebEngineV2)
    e.P = [(s[0] << 16) | s[1], (s[1] << 16) | s[2], (s[2] << 16) | s[3], (s[3] << 16) | s[0]]
    e.D = [0x00010000 << k for k in range(4)]
    e.phase_a = e.phase_b = e.disruptions = e.step_count = 0
    return e


def state(e: PhycoWebEngineV2) -> tuple:
    return tuple(e.P), tuple(e.D), e.phase_a, e.phase_b


def flux_and_transport(e: PhycoWebEngineV2) -> tuple:
    """Q and T of the next step without changing e: design.md section 4 steps 1-3 and 5."""
    pa, pb = (e.phase_a + INC_A) & 0xFF, (e.phase_b + INC_B) & 0xFF
    p = [(e.P[0] + _sext16(PERTURBATION_LUT[pa])) & M32, e.P[1],
         (e.P[2] + _sext16(PERTURBATION_LUT[(pb + COS_OFFSET) & 0xFF])) & M32, e.P[3]]
    q = [_flux((p[k] - p[(k + 1) & 3]) & M32, e.D[k] >> 30) for k in range(4)]
    t = tuple((p[k] - q[k] + q[(k - 1) & 3]) & M32 for k in range(4))
    return q, t


def growth(q: int) -> int:
    a = ((q ^ M32) + 1) & M32 if q & SIGN32 else q
    return a >> 2


def decay_collisions() -> dict:
    e = PhycoWebEngineV2(list(DEV[0]))
    tested = same = with_partner = 0
    for _ in range(DECAY_STEPS):
        e.compute_block()
        partner = False
        for k in range(4):
            lo = e.D[k] | 0xF
            if (lo >> 30) != ((lo + 1) >> 30):
                continue
            partner |= (e.D[k] & 0xF) in (0x0, 0xF)
            a, b = clone(e), clone(e)
            a.D[k], b.D[k] = lo, lo + 1
            a.compute_block()
            b.compute_block()
            tested += 1
            same += state(a) == state(b)
        with_partner += partner
    return {"seed": list(DEV[0]), "steps": DECAY_STEPS, "pairs_tested": tested,
            "identical_successors": same, "states_with_a_partner": with_partner,
            "share_with_a_partner": round(with_partner / DECAY_STEPS, 4),
            "expected_share": round(1 - (14 / 16) ** 4, 4)}


def alternating_mode() -> dict:
    e = PhycoWebEngineV2(list(DEV[0]))
    n = t_same = same = predicted = disagree = 0
    for _ in range(ALT_STEPS):
        e.compute_block()
        if any(d >> 30 != 1 for d in e.D):
            continue
        a, b = clone(e), clone(e)
        b.P = [(x + y) & M32 for x, y in zip(b.P, V2)]
        qa, ta = flux_and_transport(a)
        qb, tb = flux_and_transport(b)
        pred = ta == tb and all(growth(x) == growth(y) for x, y in zip(qa, qb))
        a.compute_block()
        b.compute_block()
        eq = state(a) == state(b)
        n += 1
        t_same += ta == tb
        same += eq
        predicted += pred
        disagree += pred != eq
    return {"seed": list(DEV[0]), "steps": ALT_STEPS, "all_class_1_states": n,
            "transport_unchanged": t_same, "identical_successors": same,
            "predicted_identical": predicted, "prediction_disagreements": disagree,
            "share_identical": round(same / n, 4), "expected_share": round(0.75 ** 4, 4)}


def byte_histograms(values: array) -> list:
    """Histogram of each byte of the 32-bit values, least significant byte first."""
    raw = values.tobytes()
    order = range(4) if sys.byteorder == "little" else range(3, -1, -1)
    return [Counter(raw[j::4]) for j in order]


def ones_frequency(hists: list, n: int) -> list:
    return [sum(c for b, c in hists[i // 8].items() if b >> (i % 8) & 1) / n for i in range(32)]


def bit_bias() -> dict:
    d_vals, p_vals = array("I"), array("I")
    assert d_vals.itemsize == 4
    for seed in [DEV[0]] + EDGE:
        e = PhycoWebEngineV2(list(seed))
        for _ in range(BIAS_STEPS):
            e.compute_block()
            d_vals.extend(e.D)
            p_vals.extend(e.P)
    n = len(d_vals)
    d_hist = byte_histograms(d_vals)
    d_ones = ones_frequency(d_hist, n)
    p_ones = ones_frequency(byte_histograms(p_vals), n)
    ne = sum(c for b, c in d_hist[3].items() if (b >> 6 ^ b >> 5) & 1) / n
    differ = (sum(2 * f * (1 - f) for f in d_ones) + sum(2 * f * (1 - f) for f in p_ones)) / 64
    return {"seeds": [list(DEV[0])] + [list(s) for s in EDGE], "steps_per_seed": BIAS_STEPS,
            "values_per_variable": n,
            "d_range": [f"0x{min(d_vals):08X}", f"0x{max(d_vals):08X}"],
            "d_ones_frequency_bit31_to_bit0": [round(d_ones[i], 4) for i in range(31, -1, -1)],
            "p_ones_frequency_range": [round(min(p_ones), 4), round(max(p_ones), 4)],
            "d_bit30_ne_bit29": round(ne, 6),
            "predicted_differing_share_unrelated_states": round(differ, 4)}


def diffusion() -> dict:
    steps = model_v2.WARMUP
    for seed in DEV:
        e = raw_engine(seed)
        for _ in range(steps):
            e._step()
        assert state(e) == state(PhycoWebEngineV2(list(seed))), "raw_engine drifted from model"
    out = [0.0] * (steps + 1)
    st = [0.0] * (steps + 1)
    n = 0
    for seed in DEV:
        for bit in range(64):
            s2 = list(seed)
            s2[bit // 16] ^= 1 << (bit % 16)
            a, b = raw_engine(seed), raw_engine(s2)
            n += 1
            for t in range(1, steps + 1):
                out[t] += bin(a.compute_block() ^ b.compute_block()).count("1") / 32
                st[t] += sum(bin(x ^ y).count("1") for x, y in zip(a.P + a.D, b.P + b.D)) / 256
    marks = (1, 2, 3, 4, 6, 8, 16, 32, 64, 128, 256)
    return {"seeds": [list(s) for s in DEV], "flips_per_seed": 64, "steps": steps,
            "output_bits_differing": {str(t): round(out[t] / n, 4) for t in marks},
            "state_bits_differing": {str(t): round(st[t] / n, 4) for t in marks},
            "state_plateau_steps_16_to_256": round(sum(st[16:]) / n / (steps - 15), 4)}


def main() -> int:
    record = {
        "findings": "security.md section 9.2, S13 and S14",
        "model_id": model_v2.MODEL_ID,
        "model_sha256": hashlib.sha256((ROOT / "phycoweb" / "model_v2.py").read_bytes()).hexdigest(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "command": "python -I research/security/step_probes.py",
        "warmup": model_v2.WARMUP,
        "s13_vein_decay": decay_collisions(),
        "s13_alternating_mode": alternating_mode(),
        "s14_bit_bias": bit_bias(),
        "diffusion_from_initial_state": diffusion(),
        "note": "Structural analysis only: not an acceptance result and not evidence of security.",
    }
    OUT.write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8", newline="\n")
    for key in ("s13_vein_decay", "s13_alternating_mode"):
        print(key, json.dumps(record[key]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
