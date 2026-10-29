"""Literal transcription of design.md 1.0 sections 3-5, used only by tests (T038, T037).

Written independently of phycoweb/model_v2.py: signed values are handled as Python ints and
converted back, rotations and shifts use generic helpers. Step numbers refer to design.md 4.
"""
from phycoweb.lut import COS_OFFSET, INC_A, INC_B, PERTURBATION_LUT

M = 2 ** 32 - 1
WARMUP = 256
SHIFT = (1, 2, 3, 4)
ROT = (5, 11, 19, 27)
THRESH = 0x4D000000
X1, X3 = 0x5A5A5A5A, 0xA5A5A5A5


def signed(v, bits=32):
    return v - (1 << bits) if v >> (bits - 1) else v


def rotl(v, r):
    return ((v << r) | (v >> (32 - r))) & M


def init_state(seed):
    s = list(seed[:4])
    P = [(s[k] << 16) | s[(k + 1) % 4] for k in range(4)]
    D = [0x00010000 << k for k in range(4)]
    return [P, D, 0, 0]


def step(state):
    """One step; returns (new_state, output_word, disrupted)."""
    P, D, pa, pb = state
    # 1. Phase advance.
    pa, pb = (pa + INC_A) % 256, (pb + INC_B) % 256
    # 2. Food injection.
    fa = signed(PERTURBATION_LUT[pa], 16) % 2 ** 32
    fb = signed(PERTURBATION_LUT[(pb + COS_OFFSET) % 256], 16) % 2 ** 32
    Ps = [(P[0] + fa) % 2 ** 32, P[1], (P[2] + fb) % 2 ** 32, P[3]]
    # 3. Flux.
    Q = [(signed((Ps[k] - Ps[(k + 1) % 4]) % 2 ** 32) >> SHIFT[D[k] >> 30]) % 2 ** 32
         for k in range(4)]
    # 4. Vein growth and decay.
    A = [abs(signed(q)) for q in Q]
    Dn = [(D[k] + (A[k] >> 2) - (D[k] >> 4)) % 2 ** 32 for k in range(4)]
    # 5. Transport, vein tone, peristalsis.
    T = [(Ps[k] - Q[k] + Q[(k - 1) % 4]) % 2 ** 32 for k in range(4)]
    Pn = [rotl(T[k] ^ Dn[k], ROT[k]) for k in range(4)]
    # 6. Supervisors on the registered D.
    fire1, fire3 = D[0] > THRESH, D[2] > THRESH
    if fire1:
        Pn[1] ^= X1
    if fire3:
        Pn[3] ^= X3
    # Output (design.md 5).
    w = ((Pn[0] + rotl(Pn[2], 16)) % 2 ** 32) ^ rotl((Pn[1] + rotl(Pn[3], 16)) % 2 ** 32, 8)
    return [Pn, Dn, pa, pb], w, fire1 or fire3


def words(seed, count):
    state = init_state(seed)
    for _ in range(WARMUP):
        state = step(state)[0]
    out = []
    for _ in range(count):
        state, w, _ = step(state)
        out.append(w)
    return out
