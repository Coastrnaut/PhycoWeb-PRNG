"""PhycoWeb-PRNG bit-accurate integer reference model, `phyco-v2`.

Spec: specs/002-core-dynamics-redesign (FR-001 to FR-009). Design: design.md 1.0; the step
comments below refer to its numbered update (section 4). Every shift and rotation amount is a
literal constant (FR-001). Experimental deterministic generator; not suitable for generating
secrets.
"""
from typing import List, Sequence

from phycoweb.lut import COS_OFFSET, INC_A, INC_B, PERTURBATION_LUT

MODEL_ID = "phyco-v2"
WARMUP = 256

M32 = 0xFFFFFFFF
SIGN32 = 0x80000000
THRESH = 0x4D000000            # vein thickness that triggers Frustrated Foraging
X1 = 0x5A5A5A5A                # disruption pattern for node 1
X3 = 0xA5A5A5A5                # disruption pattern for node 3


def _sext16(v: int) -> int:
    """Sign-extend a 16-bit two's-complement table entry to 32 bits."""
    return v | 0xFFFF0000 if v & 0x8000 else v


def _flux(d: int, cls: int) -> int:
    """Step 3: arithmetic right shift of d by SHIFT[cls], SHIFT = (1, 2, 3, 4)."""
    negative = d & SIGN32
    if cls == 0:
        return (d >> 1) | 0x80000000 if negative else d >> 1
    if cls == 1:
        return (d >> 2) | 0xC0000000 if negative else d >> 2
    if cls == 2:
        return (d >> 3) | 0xE0000000 if negative else d >> 3
    return (d >> 4) | 0xF0000000 if negative else d >> 4


def _peristalsis(k: int, t: int) -> int:
    """Step 5: rotate node k left by ROT[k], ROT = (5, 11, 19, 27)."""
    if k == 0:
        return ((t << 5) | (t >> 27)) & M32
    if k == 1:
        return ((t << 11) | (t >> 21)) & M32
    if k == 2:
        return ((t << 19) | (t >> 13)) & M32
    return ((t << 27) | (t >> 5)) & M32


def _rotl8(v: int) -> int:
    return ((v << 8) | (v >> 24)) & M32


def _rotl16(v: int) -> int:
    return ((v << 16) | (v >> 16)) & M32


class PhycoWebEngineV2:
    def __init__(self, seed: Sequence[int]) -> None:
        if len(seed) < 4:
            raise ValueError("seed must contain at least 4 values")
        for value in seed[:4]:
            if type(value) is not int or not 0 <= value <= 0xFFFF:
                raise ValueError(f"seed values must be ints in 0..65535, got {value!r}")
        s = list(seed[:4])
        # design.md 3: seed -> state.
        self.P: List[int] = [(s[0] << 16) | s[1], (s[1] << 16) | s[2],
                             (s[2] << 16) | s[3], (s[3] << 16) | s[0]]
        self.D: List[int] = [0x00010000, 0x00020000, 0x00040000, 0x00080000]
        self.phase_a = 0
        self.phase_b = 0
        self.disruptions = 0
        self.step_count = 0
        for _ in range(WARMUP):
            self._step()

    def _step(self) -> None:
        P, D = self.P, self.D
        self.step_count += 1
        # 1. Phase advance.
        self.phase_a = (self.phase_a + INC_A) & 0xFF
        self.phase_b = (self.phase_b + INC_B) & 0xFF
        # 2. Food injection into nodes 0 and 2.
        p = [(P[0] + _sext16(PERTURBATION_LUT[self.phase_a])) & M32,
             P[1],
             (P[2] + _sext16(PERTURBATION_LUT[(self.phase_b + COS_OFFSET) & 0xFF])) & M32,
             P[3]]
        # 3. Flux on channel k (node k -> node k+1), conductance class from the top 2 bits of D.
        Q = [_flux((p[k] - p[(k + 1) & 3]) & M32, D[k] >> 30) for k in range(4)]
        # 4. Vein growth and decay.
        new_d = []
        for k in range(4):
            a = ((Q[k] ^ M32) + 1) & M32 if Q[k] & SIGN32 else Q[k]
            new_d.append((D[k] + (a >> 2) - (D[k] >> 4)) & M32)
        # 5. Transport, vein tone and peristalsis.
        new_p = [_peristalsis(k, ((p[k] - Q[k] + Q[(k - 1) & 3]) & M32) ^ new_d[k])
                 for k in range(4)]
        # 6. Frustrated Foraging: registered, neighbour-local supervisors.
        fire1 = D[0] > THRESH
        fire3 = D[2] > THRESH
        if fire1:
            new_p[1] ^= X1
        if fire3:
            new_p[3] ^= X3
        if fire1 or fire3:
            self.disruptions += 1
        # 7. Commit.
        self.P, self.D = new_p, new_d

    def compute_block(self) -> int:
        self._step()
        P = self.P
        # design.md 5: output from the four pressure nodes.
        return ((P[0] + _rotl16(P[2])) & M32) ^ _rotl8((P[1] + _rotl16(P[3])) & M32)
