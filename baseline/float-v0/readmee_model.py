import numpy as np

class PhycoWebEngine:
    def __init__(self, seed_array: list):
        # Establish a 4-node localized cellular layout matrix
        self.P = np.array(seed_array[:4], dtype=np.int32)
        # Initialize 4 inter-node structural foraging channels
        self.D = np.array([256, 256, 256, 256], dtype=np.int32)
        # Step counter to maintain tracking frequencies
        self.step_count = 0

    def compute_block(self) -> int:
        self.step_count += 1
        
        # 1. Drive environmental perturbations using basic periodic shifts
        food_a = int(np.sin(self.step_count * 0.1) * 1024) & 0xFFFF
        food_b = int(np.cos(self.step_count * 0.15) * 1024) & 0xFFFF
        
        self.P[0] = (self.P[0] + food_a) & 0xFFFF
        self.P[2] = (self.P[2] + food_b) & 0xFFFF

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
        if self.D[0] > 4096 or self.D[2] > 4096:
            self.P[1] ^= 0x5A5A
            self.P[3] ^= 0xA5A5
            
        # 5. Harvest least significant bits from the channel matrix
        out_bits = ((self.D[0] & 0xFF) << 24) | \
                   ((self.D[1] & 0xFF) << 16) | \
                   ((self.D[2] & 0xFF) << 8)  | \
                   ((self.D[3] & 0xFF))
        return int(out_bits)

if __name__ == "__main__":
    # Test initialization vector
    generator = PhycoWebEngine([1024, 2048, 4096, 8192])
    print("--- Initializing PhycoWeb-PRNG Output Capture Loop ---")
    for step in range(5):
        print(f"Iteration {step}: Block Word = 0x{generator.compute_block():08X}")
