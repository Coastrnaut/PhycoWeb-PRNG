"""Every phyco-v2 state element stays within its design.md width after a step (T037; FR-002)."""
import unittest

from phycoweb.model_v2 import PhycoWebEngineV2
from tests.test_design_trace import fuzz_states, set_state


class TestWidthsV2(unittest.TestCase):
    def test_fuzz_and_edge_states(self):
        engine = PhycoWebEngineV2([0, 0, 0, 0])
        for i, state in enumerate(fuzz_states()):
            set_state(engine, state)
            word = engine.compute_block()
            self.assertTrue(0 <= word <= 0xFFFFFFFF, i)
            for name in ("P", "D"):
                values = getattr(engine, name)
                self.assertEqual(len(values), 4, (i, name))
                for v in values:
                    self.assertIs(type(v), int, (i, name))
                    self.assertTrue(0 <= v <= 0xFFFFFFFF, (i, name, v))
            for name in ("phase_a", "phase_b"):
                v = getattr(engine, name)
                self.assertIs(type(v), int, (i, name))
                self.assertTrue(0 <= v <= 0xFF, (i, name, v))


if __name__ == "__main__":
    unittest.main()
