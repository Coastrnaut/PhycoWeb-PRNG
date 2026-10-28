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
    def __init__(self, seed_array: list):
        self.P = np.array(seed_array[:4], dtype=np.int32)
        self.D = np.array([256, 256, 256, 256], dtype=np.int32)
        self.step_count = 0

    def compute_block(self) -> int:
        self.step_count += 1
        
        # Drive fluid-dynamic environmental perturbations
        food_a = int(np.sin(self.step_count * 0.1) * 1024) & 0xFFFF
        food_b = int(np.cos(self.step_count * 0.15) * 1024) & 0xFFFF
        
        self.P[0] = (self.P[0] + food_a) & 0xFFFF
        self.P[2] = (self.P[2] + food_b) & 0xFFFF

        # Compute directional localized transport flux vectors
        Q = np.zeros(4, dtype=np.int32)
        Q[0] = (self.D[0] * (self.P[0] - self.P[1])) >> 8
        Q[1] = (self.D[1] * (self.P[1] - self.P[2])) >> 8
        Q[2] = (self.D[2] * (self.P[2] - self.P[3])) >> 8
        Q[3] = (self.D[3] * (self.P[3] - self.P[0])) >> 8

        # Apply growth rules and network structural decay
        for i in range(4):
            growth = abs(Q[i]) >> 2
            decay = self.D[i] >> 4
            self.D[i] = (self.D[i] + growth - decay) & 0xFFFF
            if self.D[i] == 0:
                self.D[i] = 1

        # Frustrated Foraging: Trigger localized register disruptions upon saturation
        if self.D[0] > 4096 or self.D[2] > 4096:
            self.P[1] ^= 0x5A5A
            self.P[3] ^= 0xA5A5
            
        # Harvest least significant bits from the channel matrix
        out_bits = ((self.D[0] & 0xFF) << 24) | \
                   ((self.D[1] & 0xFF) << 16) | \
                   ((self.D[2] & 0xFF) << 8)  | \
                   ((self.D[3] & 0xFF))
        return int(out_bits)

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
    results = nistrng.run_all_battery(sequence)
    for name, p_value in results.items():
        pass_flag = "SUCCESS [ PASS ]" if p_value >= 0.01 else "CRITICAL [ FAIL ]"
        print(f"{name:<30} | {p_value:<12.6f} | {pass_flag:<25}")
            
    print("="*85 + "\n")

if __name__ == "__main__":
    execute_nist_bench()
