"""Golden vectors, determinism, seed domain and edge seeds for phyco-v2 (T039; FR-008, FR-009)."""
import re
import unittest
from pathlib import Path

from phycoweb.model_v2 import MODEL_ID, WARMUP, PhycoWebEngineV2
from protocol import seedsets

ROOT = Path(__file__).resolve().parents[1]
COUNT = 10000
DEV = seedsets.load("dev", allow={"dev"})


def words(seed, count):
    engine = PhycoWebEngineV2(seed)
    return [engine.compute_block() for _ in range(count)]


def golden_path(seed):
    return ROOT / "vectors" / f"phyco-v2_seed-{'-'.join(str(s) for s in seed)}_{COUNT}.hex"


class TestGoldenVectorsV2(unittest.TestCase):
    def test_contract_constants(self):
        self.assertEqual(MODEL_ID, "phyco-v2")
        self.assertEqual(WARMUP, 256)
        engine = PhycoWebEngineV2(DEV[0])
        self.assertEqual(engine.step_count, WARMUP)
        engine.compute_block()
        self.assertEqual(engine.step_count, WARMUP + 1)

    def test_golden_files_dev_seeds_0_and_1(self):
        for seed in DEV[:2]:
            with self.subTest(seed=seed):
                lines = golden_path(seed).read_text(encoding="ascii").split("\n")
                self.assertEqual(lines[-1], "")
                self.assertEqual(lines[0], f"# model=phyco-v2 seed={','.join(str(s) for s in seed)} "
                                           f"count={COUNT} format=u32-hex")
                data = lines[1:-1]
                self.assertEqual(len(data), COUNT)
                for line in data:
                    self.assertRegex(line, re.compile(r"^[0-9A-F]{8}$"))
                self.assertEqual([int(line, 16) for line in data], words(seed, COUNT))

    def test_deterministic(self):
        first = words(DEV[0], COUNT)
        self.assertEqual(first, words(DEV[0], COUNT))
        self.assertTrue(all(0 <= w <= 0xFFFFFFFF for w in first))


class TestSeedDomainV2(unittest.TestCase):
    def test_rejects_invalid_seeds(self):
        for seed in ([1, 2, 3], [], [0, 0, 0, 65536], [-1, 0, 0, 0], [0, 0, 0, 1.0],
                     [True, 0, 0, 0], [0, "1", 0, 0]):
            with self.subTest(seed=seed):
                with self.assertRaises(ValueError):
                    PhycoWebEngineV2(seed)

    def test_accepts_boundaries_and_ignores_extra_values(self):
        PhycoWebEngineV2([65535, 0, 65535, 0])
        self.assertEqual(words(list(DEV[0]) + [99999], 100), words(DEV[0], 100))


class TestEdgeSeedsV2(unittest.TestCase):
    """All-equal seeds give non-constant output with no short cycle (spec Edge Cases)."""

    def test_all_equal_seeds(self):
        for seed in ((0, 0, 0, 0), (65535, 65535, 65535, 65535)):
            with self.subTest(seed=seed):
                w = words(seed, 2 ** 16)
                self.assertGreater(len(set(w)), 1)
                for lag in range(1, 2 ** 15 + 1):
                    if w[lag] == w[0]:
                        self.assertNotEqual(w[lag:], w[:-lag], f"period {lag}")


if __name__ == "__main__":
    unittest.main()
