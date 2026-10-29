"""phyco-v2 equals a literal transcription of design.md 1.0 (T038; FR-004, Principle II)."""
import importlib.util
import random
import unittest
from pathlib import Path

from phycoweb.model_v2 import PhycoWebEngineV2
from protocol import seedsets
from tests import v2_reference as ref

ROOT = Path(__file__).resolve().parents[1]
V005 = ROOT / "research" / "002" / "variants" / "v005.py"
COUNT = 10000


def model_words(seed, count):
    engine = PhycoWebEngineV2(seed)
    return [engine.compute_block() for _ in range(count)]


def set_state(engine, state):
    P, D, pa, pb = state
    engine.P, engine.D, engine.phase_a, engine.phase_b = list(P), list(D), pa, pb


def fuzz_states(n=5000):
    rng = random.Random(20261029)
    states = [[[rng.getrandbits(32) for _ in range(4)], [rng.getrandbits(32) for _ in range(4)],
               rng.getrandbits(8), rng.getrandbits(8)] for _ in range(n)]
    states.append([[0] * 4, [0] * 4, 0, 0])
    states.append([[ref.M] * 4, [ref.M] * 4, 255, 255])
    return states


class TestDesignTrace(unittest.TestCase):
    def test_dev_seeds_10000_words(self):
        for seed in seedsets.load("dev", allow={"dev"})[:2]:
            with self.subTest(seed=seed):
                self.assertEqual(model_words(seed, COUNT), ref.words(seed, COUNT))

    def test_fuzz_states_single_step(self):
        engine = PhycoWebEngineV2([0, 0, 0, 0])
        for i, state in enumerate(fuzz_states()):
            set_state(engine, state)
            before = engine.disruptions
            word = engine.compute_block()
            expected, w, disrupted = ref.step(state)
            self.assertEqual(word, w, i)
            self.assertEqual([engine.P, engine.D, engine.phase_a, engine.phase_b], expected, i)
            self.assertEqual(engine.disruptions - before, int(disrupted), i)

    def test_equals_explored_variant_v005(self):
        # design.md 11: the reference model reproduces the variant that produced the dev evidence.
        spec = importlib.util.spec_from_file_location("variant_v005", V005)
        v005 = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(v005)
        self.assertEqual(v005.WARMUP, 256)
        for seed in seedsets.load("dev", allow={"dev"})[:2] + [(0, 0, 0, 0), (65535,) * 4]:
            with self.subTest(seed=seed):
                engine = v005.PhycoWebEngineV2(seed)
                self.assertEqual(model_words(seed, 2000),
                                 [engine.compute_block() for _ in range(2000)])


if __name__ == "__main__":
    unittest.main()
