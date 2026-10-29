"""Variant v002: v001 plus peristaltic rotation and vein tone (exploration only; research R10).

Changes from v001:
- each node's pressure is rotated by a node-specific constant after transport (shuttle
  streaming: the protoplasm's rhythmic contraction), which stops the pressure field from
  collapsing to the periodic attractor seen in v001;
- the updated vein value is XORed into its upstream node (vein tone feeds back on pressure);
- disruption fires when vein 0 or vein 2 exceeds a fixed thickness (as in feature 001, rescaled
  to 32 bits).
"""
from typing import Sequence

from phycoweb.lut import COS_OFFSET, INC_A, INC_B, PERTURBATION_LUT

MODEL_ID = "v002"
WARMUP = 256
M32 = 0xFFFFFFFF
_SHIFT = (1, 2, 3, 4)          # conductance class (top 2 bits of D) -> flux shift
_ROT = (5, 11, 19, 27)         # peristaltic rotation per node
THRESH = 0xF0000000            # vein thickness that triggers frustrated foraging


def _sext16(v: int) -> int:
    return v | 0xFFFF0000 if v & 0x8000 else v


def _asr(v: int, s: int) -> int:
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
        mag = [((M32 ^ q) + 1) & M32 if q & 0x80000000 else q for q in Q]
        D = [(D[k] + (mag[k] >> 2) - (D[k] >> 4)) & M32 for k in range(4)]
        self.D = D
        self.P = [_rotl(((P[k] - Q[k] + Q[(k - 1) & 3]) & M32) ^ D[k], _ROT[k]) for k in range(4)]
        if D[0] > THRESH or D[2] > THRESH:
            self.disruptions += 1
            self.P[1] ^= 0x5A5A5A5A
            self.P[3] ^= 0xA5A5A5A5

    def compute_block(self) -> int:
        self._step()
        P, D = self.P, self.D
        return (P[0] ^ _rotl(P[2], 16) ^ _rotl(D[1], 8) ^ _rotl(D[3], 24)) & M32
