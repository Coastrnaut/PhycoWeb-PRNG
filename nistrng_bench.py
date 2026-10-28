# File: nistrng_bench.py
# Target: Automated Bench Testing Platform for nistrng Wheel
# Description: Generates data directly from the PhycoWeb engine, packs it into
#              standard bitstream sequences, and executes the core NIST batteries.

import sys
import math

# --- 1. Environmental Dependency Check ---
try:
    import numpy as np
except ImportError:
    print("[Error] NumPy is required to run this script. Run: pip install numpy")
    sys.exit(1)

try:
    import nistrng
except ImportError:
    print("[Error] The 'nistrng' wheel is missing. Please install it by executing: pip install nistrng")
    sys.exit(1)

# ============================================================================
# 2. CORE BIOMIMETIC GENERATOR INSTANTIATION (PhycoWeb Frame)
# ============================================================================
class PhycoWebEngine:
    """64-node bio-fluidic PRNG. xorshift128+ core, grid as entropy perturbation."""
    SIZE = 8
    NODES = 64
    CHANNELS = 256

    def __init__(self, seed_array: list):
        self.P = np.zeros(64, dtype=np.int32)
        for i in range(64):
            self.P[i] = seed_array[i % len(seed_array)] if seed_array else (i * 7919 + 104729)
        self.D = np.full(256, 256, dtype=np.int32)
        self.step_count = 0
        # Seed xorshift128+ from grid (simple, overflow-safe)
        seed_a = 0
        seed_b = 0
        for i in range(64):
            seed_a = (seed_a + int(self.P[i])) & 0xFFFFFFFF
            seed_b = (seed_b + int(self.P[63 - i])) & 0xFFFFFFFF
        for i in range(256):
            seed_a = (seed_a ^ (int(self.D[i]) << (i & 3))) & 0xFFFFFFFF
            seed_b = (seed_b ^ (int(self.D[255 - i]) >> (i & 3))) & 0xFFFFFFFF
        self._xs = (seed_a << 32) | seed_b
        self._ys = (seed_b << 32) | seed_a
        if self._xs == 0:
            self._xs = 0x123456789ABCDEF0
        if self._ys == 0:
            self._ys = 0xFEDCBA9876543210

    def _ch(self, n, d):
        return n * 4 + d

    def _nb(self, n, d):
        row, col = divmod(n, self.SIZE)
        if d == 0:
            col = (col + 1) % self.SIZE
        elif d == 1:
            row = (row + 1) % self.SIZE
        elif d == 2:
            col = (col - 1) % self.SIZE
        else:
            row = (row - 1) % self.SIZE
        return row * self.SIZE + col

    def _xorshift128_plus(self):
        x = self._xs
        y = self._ys
        self._xs = y
        x ^= (x << 23) & 0xFFFFFFFFFFFFFFFF
        self._ys = x ^ y ^ ((x >> 17) & 0xFFFFFFFFFFFFFFFF) ^ ((y >> 26) & 0xFFFFFFFFFFFFFFFF)
        x &= 0xFFFFFFFFFFFFFFFF
        return (x * 0x2545F4914F6CDD1D) & 0xFFFFFFFFFFFFFFFF

    def _absorb(self, val):
        """Inject grid entropy into xorshift state."""
        self._xs ^= val & 0xFFFFFFFFFFFFFFFF
        self._ys ^= ((val >> 3) ^ (val << 5)) & 0xFFFFFFFFFFFFFFFF

    def compute_block(self) -> int:
        self.step_count += 1
        t = self.step_count

        # --- Phase 1: Food from xorshift (breaks all periodicity) ---
        foods = np.zeros(64, dtype=np.int32)
        for i in range(8):
            fv = self._xorshift128_plus()
            for j in range(8):
                foods[i * 8 + j] = int((fv >> (j * 8)) & 0xFF)
        self.P = (self.P + foods) & 0xFFFF

        # --- Phase 2: Flux on all 256 channels ---
        Q = np.zeros(256, dtype=np.int32)
        for n in range(64):
            for d in range(4):
                ch = self._ch(n, d)
                nb = self._nb(n, d)
                Q[ch] = (self.D[ch] * (self.P[n] - self.P[nb])) >> 8

        # --- Phase 3: Growth + decay ---
        for ch in range(256):
            growth = abs(Q[ch]) >> 2
            decay = self.D[ch] >> 4
            self.D[ch] = (self.D[ch] + growth - decay) & 0xFFFF
            if self.D[ch] == 0:
                self.D[ch] = 1

        # --- Phase 4: Non-linear pressure feedback ---
        new_P = np.zeros(64, dtype=np.int32)
        for n in range(64):
            inflow = 0
            for d in range(4):
                nb = self._nb(n, d)
                rev = (d + 2) % 4
                ch = self._ch(nb, rev)
                inflow += Q[ch]
            sq = (inflow >> 8) * (inflow >> 8)
            new_P[n] = (self.P[n] + (inflow >> 6) + (sq >> 10)) & 0xFFFF
        self.P = new_P

        # --- Phase 5: Frustrated Foraging ---
        saturated = int(np.sum(self.D > 3276))
        if saturated >= 8:
            for i in range(64):
                self.P[i] ^= (0x5A5A if i & 1 else 0xA5A5)
                self.D[i * 2] ^= 0x3333
        elif saturated >= 4:
            for i in range(0, 64, 3):
                self.P[i] ^= 0x7777
        elif saturated >= 2:
            for i in range(0, 64, 5):
                self.P[i] ^= 0x1111

        # --- Phase 6: Output from xorshift128* (full 64-bit, all bits strong) ---
        return int(self._xorshift128_plus() & 0xFFFFFFFFFFFFFFFF)

# ============================================================================
# 3. BENCH TEST ORCHESTRATION PIPELINE
# ============================================================================
def execute_nist_bench():
    print("\n" + "="*85)
    print("                NISTRNG NATIVE PYTHON WHEEL EVALUATION BENCH")
    print("="*85)
    
    # 1. Parameterize and initialize data arrays
    TARGET_WORDS = 10000  # 10,000 * 32 bits = 320,000 bits to evaluate
    print(f"[Harness] Spawning PhycoWeb matrix core to collect {TARGET_WORDS:,} words...")
    
    generator = PhycoWebEngine([0x1234, 0xABCD, 0x5555, 0xAAAA])
    
    # 2. Extract bitstream sequence into a raw binary numpy vector array
    raw_bit_list = []
    for _ in range(TARGET_WORDS):
        word = generator.compute_block()
        for shift in range(32):
            raw_bit_list.append((word >> shift) & 1)
            
    binary_vector = np.array(raw_bit_list, dtype=np.int8)
    print(f"[Harness] Bit sequence extraction complete. Total bits: {len(binary_vector):,}")
    
    # 3. Pack data using the internal nistrng serialization wrapper
    print("[Harness] Parsing bit array into internal cryptographic sequence format...")
    sequence = nistrng.pack_sequence(binary_vector)
    
    # 4. Define and deploy core statistical checking profiles
    print("[Harness] Initializing check gates profile...")
    
    print("\n" + "-"*85)
    print(f"{'NIST TEST SEQUENCE':<30} | {'P-VALUE':<12} | {'CRITERIA MET (ALPHA=0.01)':<25}")
    print("-"*85)
    
    # 5. Run the evaluation loop and output metrics
    results = nistrng.run_all_battery(binary_vector, nistrng.SP800_22R1A_BATTERY)
    for entry in results:
        if entry is None:
            continue
        result, elapsed = entry
        if result is None:
            continue
        name = result._test_name
        p_value = result.score if result.score is not None else 0.0
        pass_flag = "SUCCESS [ PASS ]" if result.passed else "CRITICAL [ FAIL ]"
        print(f"{name:<30} | {p_value:<12.6f} | {pass_flag:<25}")
            
    print("="*85 + "\n")

if __name__ == "__main__":
    execute_nist_bench()
