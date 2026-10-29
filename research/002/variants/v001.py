"""Variant v001: faithful dissipative ring (exploration only; research R10).

4 nodes in a ring, channel k joins node k to node k+1. 32-bit pressures P and veins D.
Flux uses conductance classes (a constant shift selected by the top bits of D, FR-001), mass
is conserved by transport, veins grow with |flux| and decay by D >> 4, and a threshold rule on
flux triggers the disruption. No extra mixing inside the state update.
"""
from typing import Sequence

from phycoweb.lut import COS_OFFSET, INC_A, INC_B, PERTURBATION_LUT

MODEL_ID = "v001"
WARMUP = 256
M32 = 0xFFFFFFFF
_SHIFT = (1, 2, 3, 4)          # conductance class -> flux shift (thick vein = small shift)
THRESH = 0x00400000            # disruption threshold on |Q0|


def _sext16(v: int) -> int:
    return v | 0xFFFF0000 if v & 0x8000 else v


def _asr(v: int, s: int) -> int:
    """Arithmetic right shift of a 32-bit two's-complement value, result masked to 32 bits."""
    return ((v >> s) | (M32 ^ (M32 >> s))) & M32 if v & 0x80000000 else v >> s


def _rotl(v: int, r: int) -> int:
    return ((v << r) | (v >> (32 - r))) & M32


class PhycoWebEngineV2:
    def __init__(self, seed: Sequence[int]) -> None:
        if len(seed) < 4:
            raise ValueError("seed must contain at least 4 values")
        for value in seed[:4]:
            if type(value) is not int or not 0 <= value <= 0xFFFF:
                raise ValueError(f"seed values must be ints in 0..65535, got {value!r}")
        s = list(seed[:4])
        self.P = [(s[i] << 16) | s[(i + 1) & 3] for i in range(4)]
        self.D = [0x00010000 << i for i in range(4)]
        self.phase_a = 0
        self.phase_b = 0
        self.disruptions = 0
        self.step_count = 0
        for _ in range(WARMUP):
            self._step()

    def _step(self) -> None:
        self.step_count += 1
        self.phase_a = (self.phase_a + INC_A) & 0xFF
        self.phase_b = (self.phase_b + INC_B) & 0xFF
        P, D = self.P, self.D
        P[0] = (P[0] + _sext16(PERTURBATION_LUT[self.phase_a])) & M32
        P[2] = (P[2] + _sext16(PERTURBATION_LUT[(self.phase_b + COS_OFFSET) & 0xFF])) & M32
        Q = [_asr((P[k] - P[(k + 1) & 3]) & M32, _SHIFT[D[k] >> 30]) for k in range(4)]
        self.P = [(P[k] - Q[k] + Q[(k - 1) & 3]) & M32 for k in range(4)]
        mag = [(M32 ^ q) + 1 & M32 if q & 0x80000000 else q for q in Q]
        self.D = [(D[k] + (mag[k] >> 2) - (D[k] >> 4)) & M32 for k in range(4)]
        if mag[0] > THRESH:
            self.disruptions += 1
            self.P[1] ^= 0x5A5A5A5A
            self.P[3] ^= 0xA5A5A5A5

    def compute_block(self) -> int:
        self._step()
        P, D = self.P, self.D
        return (P[0] ^ _rotl(P[2], 16) ^ _rotl(D[1], 8) ^ _rotl(D[3], 24)) & M32
