import numpy as np

class MycoPRNG:
    def __init__(self, initial_pressures: list):
        # 4-node grid pressure states
        self.P = np.array(initial_pressures, dtype=np.int32)
        # 4 interconnecting vein thicknesses (0->1, 1->2, 2->3, 3->0)
        self.D = np.array([256, 256, 256, 256], dtype=np.int32)
        
    def step(self, food_a: int, food_b: int) -> int:
        # Inject dynamic environmental food signals into border nodes
        self.P[0] = (self.P[0] + food_a) & 0xFFFF
        self.P[2] = (self.P[2] + food_b) & 0xFFFF
        
        # Calculate localized fluxes between adjacent nodes
        Q = np.zeros(4, dtype=np.int32)
        Q[0] = (self.D[0] * (self.P[0] - self.P[1])) >> 8
        Q[1] = (self.D[1] * (self.P[1] - self.P[2])) >> 8
        Q[2] = (self.D[2] * (self.P[2] - self.P[3])) >> 8
        Q[3] = (self.D[3] * (self.P[3] - self.P[0])) >> 8
        
        # Update vein thicknesses: Growth based on flux, constant decay
        for i in range(4):
            growth = abs(Q[i]) >> 2
            decay = self.D[i] >> 4
            self.D[i] = max(1, (self.D[i] + growth - decay) & 0xFFFF)
            
        # Frustrated Foraging: If a vein gets too thick, trigger a network disruption
        if self.D[0] > 2000:
            self.P[1] ^= 0x5A5A # Scramble intermediate nodes
            self.P[3] ^= 0xA5A5
            
        # Extract and bundle the least significant bits from the vein states
        out_bits = ((self.D[0] & 0xFF) << 24) | \
                   ((self.D[1] & 0xFF) << 16) | \
                   ((self.D[2] & 0xFF) << 8)  | \
                   ((self.D[3] & 0xFF))
        return out_bits
