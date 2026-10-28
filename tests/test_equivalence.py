"""All non-perturbation stages match the archived float-v0 model (FR-008, FR-008a).

The archived model is fed the LUT food values through a substitute `np` namespace, so the
perturbation source is the only possible difference. The archived file is never modified.
"""
import importlib.util
import unittest
import warnings
from pathlib import Path

from phycoweb.lut import PERTURBATION_LUT as T
from phycoweb.model import PhycoWebEngine

try:
    import numpy
except ImportError:  # pragma: no cover
    numpy = None

ROOT = Path(__file__).resolve().parents[1]
ARCHIVED = ROOT / "baseline" / "float-v0" / "readmee_model.py"
SEEDS = ([1024, 2048, 4096, 8192], [0x1234, 0xABCD, 0x5555, 0xAAAA])
WORDS = 10000


def s16(value):
    return value - 0x10000 if value & 0x8000 else value


class LutNumpy:
    """numpy stand-in whose sin/cos return LUT samples; everything else is real numpy."""

    def sin(self, x):
        return s16(T[(4 * round(x / 0.1)) & 0xFF]) / 1024

    def cos(self, x):
        return s16(T[(6 * round(x / 0.15) + 64) & 0xFF]) / 1024

    def __getattr__(self, name):
        return getattr(numpy, name)


def load_archived_with_lut_food():
    spec = importlib.util.spec_from_file_location("float_v0_lut_food", ARCHIVED)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.np = LutNumpy()
    return module


@unittest.skipIf(numpy is None, "numpy is required to run the archived float-v0 model")
class TestEquivalenceWithArchivedModel(unittest.TestCase):
    def test_words_match(self):
        archived_module = load_archived_with_lut_food()
        for seed in SEEDS:
            with self.subTest(seed=seed):
                archived = archived_module.PhycoWebEngine(list(seed))
                current = PhycoWebEngine(seed)
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", RuntimeWarning)
                    for index in range(WORDS):
                        expected = archived.compute_block() & 0xFFFFFFFF
                        self.assertEqual(current.compute_block(), expected, f"word {index}")

    def test_single_steps_from_random_and_edge_states(self):
        """Trajectories rarely reach some paths (e.g. the D == 0 floor), so also compare
        single steps from forced states, including one that drives D[0] to exactly 0."""
        import random

        rng = random.Random(20261028)
        states = [([rng.randrange(0x10000) for _ in range(4)],
                   [rng.randrange(1, 0x10000) for _ in range(4)],
                   rng.randrange(1 << 20)) for _ in range(5000)]
        # Step 0 food is T[4] for P[0] and T[70] for P[2]. With D[0] = 4096 the flux is
        # Q = 16 * (P[0] - P[1]); growth 4 * 15424 + 4096 - 256 = 65536 wraps D[0] to 0.
        states.append(([15424 - s16(T[4]), 0, 0, 0], [4096, 256, 256, 256], 0))
        # Disruption threshold boundaries: pressures equal after food injection give Q = 0,
        # so D' = D - (D >> 4); 4369 -> 4096 (no trigger) and 4370 -> 4097 (trigger).
        flat = [(0x8000 - T[4]) & 0xFFFF, 0x8000, (0x8000 - T[70]) & 0xFFFF, 0x8000]
        for d in (4369, 4370):
            states.append((flat, [d, 256, 256, 256], 0))
            states.append((flat, [256, 256, d, 256], 0))

        archived_module = load_archived_with_lut_food()
        floor_hit = False
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            for index, (P, D, step) in enumerate(states):
                archived = archived_module.PhycoWebEngine([0, 0, 0, 0])
                archived.P = numpy.array(P, dtype=numpy.int32)
                archived.D = numpy.array(D, dtype=numpy.int32)
                archived.step_count = step
                current = PhycoWebEngine([0, 0, 0, 0])
                current.P, current.D = list(P), list(D)
                current.step_count = step
                current.phase_a = (4 * step) & 0xFF
                current.phase_b = (6 * step) & 0xFF
                expected = archived.compute_block() & 0xFFFFFFFF
                self.assertEqual(current.compute_block(), expected, f"state {index}")
                self.assertEqual(current.P, [int(v) for v in archived.P], f"state {index}")
                self.assertEqual(current.D, [int(v) for v in archived.D], f"state {index}")
                floor_hit = floor_hit or index == 5000 and current.D[0] == 1
        self.assertTrue(floor_hit, "edge state did not exercise the D == 0 floor")


if __name__ == "__main__":
    unittest.main()
