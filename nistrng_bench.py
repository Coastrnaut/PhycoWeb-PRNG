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
    """16-node bio-fluidic PRNG with crypto whitening layer."""
    # 4x4 toroidal grid: each node connects to right and down neighbors
    # 16 nodes, 32 directed channels (right + down per node, wrap-around)
    NODES = 16
    CHANNELS = 32

    def __init__(self, seed_array: list):
        # 16 nutrient pressure nodes
        self.P = np.zeros(16, dtype=np.int32)
        for i in range(16):
            self.P[i] = seed_array[i % len(seed_array)] if seed_array else (i * 7919 + 104729)

        # 32 directed channels (each node has 2 outgoing: right and down on 4x4 grid)
        self.D = np.full(32, 256, dtype=np.int32)
        self.step_count = 0
        # Internal mixing accumulator (whitening state)
        self._mix_a = 0x12345678
        self._mix_b = 0x9ABCDEF0

    def _channel_for(self, node, direction):
        """Map (node, direction) -> channel index. direction=0=right, 1=down on 4x4 grid."""
        return node * 2 + direction

    def _neighbor(self, node, direction):
        """Toroidal 4x4 grid neighbor."""
        row, col = divmod(node, 4)
        if direction == 0:  # right
            col = (col + 1) % 4
        else:  # down
            row = (row + 1) % 4
        return row * 4 + col

    def _xorshift32(self, x):
        """Standard xorshift32 mixing."""
        x ^= (x << 13) & 0xFFFFFFFF
        x ^= (x >> 17) & 0xFFFFFFFF
        x ^= (x << 5) & 0xFFFFFFFF
        return x & 0xFFFFFFFF

    def compute_block(self) -> int:
        self.step_count += 1

        # --- Phase 1: Environmental perturbations (6 food sources) ---
        foods = np.zeros(16, dtype=np.int32)
        for i in range(6):
            freq = 0.07 * (i + 1)
            phase = i * 1.3
            foods[i * 2] = int(np.sin(self.step_count * freq + phase) * 8192) & 0xFFFF
            foods[i * 2 + 1] = int(np.cos(self.step_count * freq + phase) * 8192) & 0xFFFF
        self.P = (self.P + foods) & 0xFFFF

        # --- Phase 2: Compute flux on all 32 channels ---
        Q = np.zeros(32, dtype=np.int32)
        for node in range(16):
            for d in range(2):
                ch = self._channel_for(node, d)
                nb = self._neighbor(node, d)
                Q[ch] = (self.D[ch] * (self.P[node] - self.P[nb])) >> 8

        # --- Phase 3: Growth + decay on channels ---
        for ch in range(32):
            growth = abs(Q[ch]) >> 2
            decay = self.D[ch] >> 4
            self.D[ch] = (self.D[ch] + growth - decay) & 0xFFFF
            if self.D[ch] == 0:
                self.D[ch] = 1

        # --- Phase 4: Feedback — inject flux back into pressures ---
        for node in range(16):
            inflow = 0
            for d in range(2):
                ch = self._channel_for(node, d)
                nb = self._neighbor(node, d)
                # Incoming from neighbor's channel pointing to this node
                nb_ch = self._channel_for(nb, d)
                inflow += Q[nb_ch]
            self.P[node] = (self.P[node] + (inflow >> 6)) & 0xFFFF

        # --- Phase 5: Frustrated Foraging disruptions ---
        # Check all channels; disrupt when multiple saturated
        saturated = np.sum(self.D > 4096)
        if saturated >= 4:
            # XOR scramble on half the nodes
            for i in range(0, 16, 2):
                self.P[i] ^= 0x5A5A
                self.P[i + 1] ^= 0xA5A5
        elif saturated >= 2:
            # Lighter disruption
            for i in range(0, 16, 4):
                self.P[i] ^= 0x3333

        # --- Phase 6: Harvest + crypto whitening ---
        # Pack 8 channel values into a raw 32-bit word
        raw = 0
        for i in range(8):
            raw |= int(self.D[i * 4] & 0xFF) << (i * 4)
        raw &= 0xFFFFFFFF

        # Whitening: xorshift mix + feedback
        self._mix_a = self._xorshift32(self._mix_a ^ raw)
        self._mix_b = self._xorshift32(self._mix_b ^ (self.step_count & 0xFFFFFFFF))
        output = (self._mix_a + self._mix_b) & 0xFFFFFFFF

        # Additional non-linear mixing: rotate and XOR
        rot = (output << 7 | output >> 25) & 0xFFFFFFFF
        output ^= rot
        output ^= (output >> 11) & 0xFFFFFFFF

        return int(output)

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
