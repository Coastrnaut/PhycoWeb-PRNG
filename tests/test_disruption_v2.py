"""Quick FR-005 check: phyco-v2 disruption rate in [1%, 50%] on 3 dev seeds (T040).

The full measurement over all 100 dev seeds is T044 (reports/002-core-dynamics-redesign/dev/).
"""
import unittest

from phycoweb.model_v2 import PhycoWebEngineV2
from protocol import seedsets

STEPS = 10 ** 6


class TestDisruptionRateV2(unittest.TestCase):
    def test_three_dev_seeds(self):
        for seed in seedsets.load("dev", allow={"dev"})[:3]:
            with self.subTest(seed=seed):
                engine = PhycoWebEngineV2(seed)
                d0, s0 = engine.disruptions, engine.step_count
                step = engine.compute_block
                for _ in range(STEPS):
                    step()
                rate = (engine.disruptions - d0) / (engine.step_count - s0)
                self.assertGreaterEqual(rate, 0.01)
                self.assertLessEqual(rate, 0.50)


if __name__ == "__main__":
    unittest.main()
