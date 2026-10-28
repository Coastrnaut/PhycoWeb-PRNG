"""PhycoWeb-PRNG bit-accurate integer reference model, `lut-v1`.

Spec: specs/001-integer-lut-perturbation (FR-007b/c perturbation, FR-008a other stages).
Experimental deterministic generator; not suitable for generating secrets.
"""
from typing import List, Sequence, Tuple

from phycoweb.lut import COS_OFFSET, INC_A, INC_B, PERTURBATION_LUT

MODEL_ID = "lut-v1"

_CHANNELS = ((0, 1), (1, 2), (2, 3), (3, 0))


def wrap32(x: int) -> int:
    """Wrap to 32-bit two's complement, matching numpy int32 overflow (research R1)."""
    return ((x + 0x80000000) & 0xFFFFFFFF) - 0x80000000


class PhycoWebEngine:
    def __init__(self, seed: Sequence[int]) -> None:
        if len(seed) < 4:
            raise ValueError("seed must contain at least 4 values")
        for value in seed[:4]:
            if type(value) is not int or not 0 <= value <= 0xFFFF:
                raise ValueError(f"seed values must be ints in 0..65535, got {value!r}")
        self.P: List[int] = list(seed[:4])
        self.D: List[int] = [256, 256, 256, 256]
        self.phase_a = 0
        self.phase_b = 0
        self.step_count = 0

    def _perturb(self) -> Tuple[int, int]:
        """Stages 1-4 (FR-007c): advance phases, read the table, inject food."""
        self.step_count += 1
        self.phase_a = (self.phase_a + INC_A) & 0xFF
        self.phase_b = (self.phase_b + INC_B) & 0xFF
        food_a = PERTURBATION_LUT[self.phase_a]
        food_b = PERTURBATION_LUT[(self.phase_b + COS_OFFSET) & 0xFF]
        self.P[0] = (self.P[0] + food_a) & 0xFFFF
        self.P[2] = (self.P[2] + food_b) & 0xFFFF
        return food_a, food_b

    def compute_block(self) -> int:
        self._perturb()
        P, D = self.P, self.D

        # Stage 5, flux. The variable product and its 32-bit wrap are existing behavior kept
        # deliberately (FR-008a); see spec Open Issues 1 and 2.
        Q = [wrap32(D[i] * (P[i] - P[j])) >> 8 for i, j in _CHANNELS]

        # Stage 6, growth and decay.
        for k in range(4):
            growth = wrap32(abs(Q[k])) >> 2
            D[k] = (D[k] + growth - (D[k] >> 4)) & 0xFFFF
            if D[k] == 0:
                D[k] = 1

        # Stage 7, Frustrated Foraging disruption.
        if D[0] > 4096 or D[2] > 4096:
            P[1] ^= 0x5A5A
            P[3] ^= 0xA5A5

        # Stage 8, harvest (unsigned 32-bit word).
        return ((D[0] & 0xFF) << 24) | ((D[1] & 0xFF) << 16) | ((D[2] & 0xFF) << 8) | (D[3] & 0xFF)
