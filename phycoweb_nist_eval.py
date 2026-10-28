# File: phycoweb_nist_eval.py
# Architecture: PhycoWeb-PRNG Emulation Loop with Integrated NIST SP 800-22 Metric Monitors

import numpy as np
import math

class PhycoWebEngineWithNIST:
    def __init__(self, seed_array: list):
        # Establish a 4-node localized cellular layout matrix
        self.P = np.array(seed_array[:4], dtype=np.int32)
        # Initialize 4 inter-node structural foraging channels
        self.D = np.array([512, 512, 512, 512], dtype=np.int32)
        # Step counter to maintain tracking frequencies
        self.step_count = 0
        
        # NIST Metric Accumulators
        self.bit_count = 0
        self.ones_count = 0
        self.runs_count = 0
        self.last_bit = -1
        
        # Serial Test Tracking Arrays (Pre-allocating 2-bit frequency bins)
        # Bins: [00, 01, 10, 11]
        self.v_pair_counts = np.zeros(4, dtype=np.int64)

    def compute_block(self) -> int:
        self.step_count += 1
        
        # 1. Drive environmental perturbations using basic periodic shifts
        food_a = int(np.sin(self.step_count * 0.1) * 1024) & 0xFFFF
        food_b = int(np.cos(self.step_count * 0.15) * 1024) & 0xFFFF
        
        self.P[0] = (self.P[0] + food_a) & 0xFFFF
        self.P[1] = (self.P[1] + food_b) & 0xFFFF

        # 2. Compute directional localized transport flux vectors
        Q = np.zeros(4, dtype=np.int32)
        Q[0] = (self.D[0] * (self.P[0] - self.P[1])) >> 8
        Q[1] = (self.D[1] * (self.P[1] - self.P[2])) >> 8
        Q[2] = (self.D[2] * (self.P[2] - self.P[3])) >> 8
        Q[3] = (self.D[3] * (self.P[3] - self.P[0])) >> 8

        # 3. Apply growth parameters and structural decay limits
        for i in range(4):
            growth = abs(Q[i]) >> 2
            decay = self.D[i] >> 4
            self.D[i] = (self.D[i] + growth - decay) & 0xFFFF
            if self.D[i] == 0:
                self.D[i] = 1

        # 4. Frustrated Foraging: Trigger localized disruptions upon saturation
        if self.D[0] > 4096 or self.D[1] > 4096:
            self.P[0] ^= 0x5A5A
            self.P[2] ^= 0xA5A5
            
        # 5. Harvest least significant bits from the channel matrix
        out_bits = ((self.D[0] & 0xFF) << 24) | \
                   ((self.D[1] & 0xFF) << 16) | \
                   ((self.D[2] & 0xFF) << 8)  | \
                   ((self.D[3] & 0xFF))
                   
        # 6. Stream bits individually to the automated NIST tracking loop
        self._ingest_word_into_nist(out_bits)
        
        return int(out_bits)

    def _ingest_word_into_nist(self, word: int):
        """Processes 32-bit output blocks one bit at a time to update entropy logs."""
        for shift in range(32):
            bit = (word >> shift) & 1
            self.bit_count += 1
            
            # Update Frequency Monobit Test metrics
            if bit == 1:
                self.ones_count += 1
                
            # Update Runs Test metrics
            if self.last_bit != -1:
                if bit != self.last_bit:
                    self.runs_count += 1
                    
                # Update Serial Block Frequency pairs
                pair_idx = (self.last_bit << 1) | bit
                self.v_pair_counts[pair_idx] += 1
                
            self.last_bit = bit

    def execute_nist_report(self):
        """Calculates p-values from accumulated results to check NIST compliance flags."""
        print("\n" + "="*85)
        print("          REAL-TIME NIST SP 800-22 STATISTICAL CRITIQUE (PHYCOWEB CORE)")
        print("="*85)
        print(f"Total Evaluated Sample Stream Size : {self.bit_count} bits")
        print(f"Total Observed One-Bit Occurrences : {self.ones_count}")
        print(f"Total Observed Zero-Bit Occurrences: {self.bit_count - self.ones_count}")
        print("-"*85)

        if self.bit_count < 100:
            print("[Warning] Sample payload too low for valid statistical assessment.")
            return

        # 1. NIST Test 01: Frequency (Monobit) Assessment
        # Formula: S_obs = |ones - zeros| / sqrt(n)
        zeros_count = self.bit_count - self.ones_count
        s_obs = abs(self.ones_count - zeros_count) / math.sqrt(self.bit_count)
        p_val_monobit = math.erfc(s_obs / math.sqrt(2.0))
        status_mono = "[ SUCCESS ]" if p_val_monobit >= 0.01 else "[ FAILED  ]"
        print(f"TEST 01: Frequency (Monobit)       | p-Value: {p_val_monobit:.6f} | Pass Gate: {status_mono}")

        # 2. NIST Test 03: Runs Test Verification Layer
        # Formula: p-value = erfc(|V_n(obs) - 2npi(1-pi)| / (2 * sqrt(2n) * pi * (1-pi)))
        pi_ratio = self.ones_count / self.bit_count
        # Guard calculation safety bounds
        if abs(pi_ratio - 0.5) >= (2 / math.sqrt(self.bit_count)):
            print("TEST 03: Runs Verification         | p-Value: 0.000000 | Pass Gate: [ FAILED  ] (Frequency Bias Too Large)")
        else:
            v_n_obs = self.runs_count + 1
            num_runs = abs(v_n_obs - (2.0 * self.bit_count * pi_ratio * (1.0 - pi_ratio)))
            den_runs = 2.0 * math.sqrt(2.0 * self.bit_count) * pi_ratio * (1.0 - pi_ratio)
            p_val_runs = math.erfc(num_runs / den_runs) if den_runs != 0 else 0.0
            status_runs = "[ SUCCESS ]" if p_val_runs >= 0.01 else "[ FAILED  ]"
            print(f"TEST 03: Runs Matrix Compliance    | p-Value: {p_val_runs:.6f} | Pass Gate: {status_runs}")

        # 3. Approximate Entropy Estimation Model
        # Calculates balance across 2-bit structural tuples
        n_pairs = sum(self.v_pair_counts)
        entropy = 0.0
        if n_pairs > 0:
            for count in self.v_pair_counts:
                if count > 0:
                    prob = count / n_pairs
                    entropy -= prob * math.log2(prob)
            normalized_entropy = entropy / 2.0  # Scaled max output scale limit
            status_ent = "[ HIGH ENTROPY ]" if normalized_entropy > 0.95 else "[ LOW ENTROPY  ]"
            print(f"METRIC : Approximate Bit Entropy   | Density: {normalized_entropy:.6f} | Pass Gate: {status_ent}")
        print("="*85 + "\n")

# Execution Script Integration Testbed
if __name__ == "__main__":
    # Initialize using arbitrary mock seed matrix input parameters
    bio_generator = PhycoWebEngineWithNIST([0x1234, 0xABCD, 0x5555, 0xAAAA])
    
    print("[Testing] Generating data blocks to populate validation buffers...")
    # Cycle the engine through enough iterations to accumulate data points
    for cycle in range(50000):
        _ = bio_generator.compute_block()
        
    # Compile metrics
    bio_generator.execute_nist_report()
