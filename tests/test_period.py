"""Perturbation phase schedule and period (FR-006, FR-007, FR-007b, FR-007c, SC-003)."""
import unittest

from phycoweb.lut import PERTURBATION_LUT as T
from phycoweb.model import PhycoWebEngine

SEED = [1024, 2048, 4096, 8192]
STEPS = 1280  # 10 periods of 128


def perturbation_sequence(engine, steps):
    return [engine._perturb() for _ in range(steps)]


class TestPerturbationSchedule(unittest.TestCase):
    def test_first_step_indices(self):
        engine = PhycoWebEngine(SEED)
        self.assertEqual(engine._perturb(), (T[4], T[70]))

    def test_step_n_indices(self):
        sequence = perturbation_sequence(PhycoWebEngine(SEED), STEPS)
        for n, pair in enumerate(sequence, start=1):
            with self.subTest(n=n):
                self.assertEqual(pair, (T[(4 * n) & 0xFF], T[(6 * n + 64) & 0xFF]))

    def test_period_is_exactly_128(self):
        sequence = perturbation_sequence(PhycoWebEngine(SEED), STEPS)
        repeats = lambda p: all(sequence[i] == sequence[i + p] for i in range(STEPS - p))
        self.assertTrue(repeats(128))
        for p in (d for d in range(1, 128) if STEPS % d == 0):
            with self.subTest(p=p):
                self.assertFalse(repeats(p))

    def test_signals_distinct_in_every_period(self):
        sequence = perturbation_sequence(PhycoWebEngine(SEED), STEPS)
        for start in range(0, STEPS, 128):
            with self.subTest(period=start // 128):
                self.assertTrue(any(a != b for a, b in sequence[start:start + 128]))

    def test_step_counter_overflow_does_not_affect_schedule(self):
        reference = perturbation_sequence(PhycoWebEngine(SEED), 256)
        engine = PhycoWebEngine(SEED)
        engine.step_count = 2**32 + 5
        self.assertEqual(perturbation_sequence(engine, 256), reference)
        self.assertEqual(engine.step_count, 2**32 + 5 + 256)


if __name__ == "__main__":
    unittest.main()
