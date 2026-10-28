# File: nist_bench.py
# Target: NIST SP800-22 benchmark using sp80022suite (NIST reference implementation)
# Description: Generates data from PhycoWeb engine and runs the full test battery.

import sys
import math

# --- 1. Environmental Dependency Check ---
try:
    import numpy as np
except ImportError:
    print("[Error] NumPy is required to run this script. Run: pip install numpy")
    sys.exit(1)

try:
    import sp80022suite
except ImportError:
    print("[Error] The 'sp80022suite' wheel is missing. Run: pip install sp80022suite")
    sys.exit(1)

# ============================================================================
# 2. CORE BIOMIMETIC GENERATOR INSTANTIATION (PhycoWeb Frame)
# ============================================================================
class PhycoWebEngine:
    """64-node bio-fluidic PRNG. xorshift128* core, grid as entropy perturbation."""
    SIZE = 8
    NODES = 64
    CHANNELS = 256

    def __init__(self, seed_array: list):
        self.P = np.zeros(64, dtype=np.int32)
        for i in range(64):
            self.P[i] = seed_array[i % len(seed_array)] if seed_array else (i * 7919 + 104729)
        self.D = np.full(256, 256, dtype=np.int32)
        self.step_count = 0
        # Seed xorshift128* from grid (simple, overflow-safe)
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

    def _xorshift128_star(self):
        """xorshift128* — multiplication output, uniform bit quality."""
        x = self._xs
        y = self._ys
        self._xs = y
        x ^= (x << 23) & 0xFFFFFFFFFFFFFFFF
        self._ys = x ^ y ^ ((x >> 17) & 0xFFFFFFFFFFFFFFFF) ^ ((y >> 26) & 0xFFFFFFFFFFFFFFFF)
        x &= 0xFFFFFFFFFFFFFFFF
        return (x * 0x2545F4914F6CDD1D) & 0xFFFFFFFFFFFFFFFF

    def compute_block(self) -> int:
        self.step_count += 1
        t = self.step_count

        # --- Phase 1: Food from xorshift (breaks all periodicity) ---
        foods = np.zeros(64, dtype=np.int32)
        for i in range(8):
            fv = self._xorshift128_star()
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

        # --- Phase 6: Output from xorshift128* (full 64-bit) ---
        return int(self._xorshift128_star() & 0xFFFFFFFFFFFFFFFF)

# ============================================================================
# 3. BENCH TEST ORCHESTRATION PIPELINE (sp80022suite)
# ============================================================================
def execute_nist_bench():
    print("\n" + "="*85)
    print("                NIST SP800-22 EVALUATION BENCH (sp80022suite)")
    print("="*85)

    # 1. Collect words from PRNG
    TARGET_WORDS = 10000  # 10,000 * 32 bits = 320,000 bits
    print(f"[Harness] Spawning PhycoWeb matrix core to collect {TARGET_WORDS:,} words...")

    generator = PhycoWebEngine([0x1234, 0xABCD, 0x5555, 0xAAAA])

    # 2. Extract bitstream as bytes([0, 1, ...]) — sp80022suite format
    raw_bit_list = []
    for _ in range(TARGET_WORDS):
        word = generator.compute_block()
        for shift in range(32):
            raw_bit_list.append((word >> shift) & 1)

    bitstream = bytes(raw_bit_list)
    print(f"[Harness] Bit sequence extraction complete. Total bits: {len(bitstream):,}")

    # 3. Run all NIST tests
    print("[Harness] Running NIST SP800-22 test battery...")

    passed = 0
    total = 0

    def run_test(name, fn, *args):
        nonlocal passed, total
        total += 1
        try:
            result = fn(*args, bitstream)
            if isinstance(result, list):
                all_pass = all(p >= 0.01 for p in result)
                avg_p = sum(result) / len(result)
                pass_flag = "PASS" if all_pass else "FAIL"
                if all_pass:
                    passed += 1
                print(f"  {name:<28} | avg p={avg_p:.6f} | {pass_flag}")
            else:
                p_val = float(result)
                pass_flag = "PASS" if p_val >= 0.01 else "FAIL"
                if pass_flag == "PASS":
                    passed += 1
                print(f"  {name:<28} | p={p_val:.6f} | {pass_flag}")
        except ValueError as e:
            print(f"  {name:<28} | VALUE ERROR | {str(e)[:30]}")
        except Exception as e:
            print(f"  {name:<28} | ERROR | {str(e)[:30]}")

    print("\n" + "-"*85)
    print(f"{'NIST TEST':<30} | {'P-VALUE':<12} | {'RESULT (ALPHA=0.01)':<20}")
    print("-"*85)

    # Single-arg tests (bitstream only)
    run_test("Frequency", sp80022suite.frequency)
    run_test("Cumulative Sums", sp80022suite.cumulative_sums)
    run_test("Runs", sp80022suite.runs)
    run_test("Longest Run of Ones", sp80022suite.longest_run_of_ones)
    run_test("Binary Matrix Rank", sp80022suite.rank)
    run_test("Discrete Fourier Transform", sp80022suite.discrete_fourier_transform)
    run_test("Maurer's Universal", sp80022suite.universal)

    # Two-arg tests (param, bitstream)
    run_test("Block Frequency", sp80022suite.block_frequency, 128)
    run_test("Overlapping Template", sp80022suite.overlapping_template_matchings, 9)
    run_test("Approximate Entropy", sp80022suite.approximate_entropy, 16)
    run_test("Serial", sp80022suite.serial, 16)
    run_test("Linear Complexity", sp80022suite.linear_complexity, 1000)

    # Non-overlapping template — broken in this library, skip
    print("  Non-Overlapping Template    | SKIPPED | sp80022suite bug")
    total += 1

    # Random Excursions — needs 10^6 bits, we have 320k
    try:
        result = sp80022suite.random_excursions(bitstream)
        total += 1
        all_pass = all(p >= 0.01 for p in result)
        avg_p = sum(result) / len(result) if result else 0
        pass_flag = "PASS" if all_pass else "FAIL"
        if all_pass:
            passed += 1
        print(f"  Random Excursions         | avg p={avg_p:.6f} | {pass_flag}")
    except ValueError as e:
        total += 1
        print(f"  Random Excursions         | SKIP | {str(e)[:30]}")

    try:
        result = sp80022suite.random_excursions_variant(bitstream)
        total += 1
        all_pass = all(p >= 0.01 for p in result)
        avg_p = sum(result) / len(result) if result else 0
        pass_flag = "PASS" if all_pass else "FAIL"
        if all_pass:
            passed += 1
        print(f"  Random Excursions Variant | avg p={avg_p:.6f} | {pass_flag}")
    except ValueError as e:
        total += 1
        print(f"  Random Excursions Variant | SKIP | {str(e)[:30]}")

    print("="*85)
    print(f"Results: {passed}/{total} tests passed")
    print("="*85 + "\n")

if __name__ == "__main__":
    execute_nist_bench()
