"""Golden vectors and determinism for lut-v1 (FR-008b, FR-010, SC-002)."""
import re
import unittest
from pathlib import Path

from phycoweb.model import PhycoWebEngine

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "vectors" / "lut-v1_seed-1024-2048-4096-8192_10000.hex"
SEED = [1024, 2048, 4096, 8192]
COUNT = 10000


def words(seed, count):
    engine = PhycoWebEngine(seed)
    return [engine.compute_block() for _ in range(count)]


class TestGoldenVectors(unittest.TestCase):
    def test_file_format_and_contents(self):
        lines = GOLDEN.read_text(encoding="ascii").split("\n")
        self.assertEqual(lines[-1], "")
        self.assertEqual(lines[0], "# model=lut-v1 seed=1024,2048,4096,8192 count=10000 format=u32-hex")
        data = lines[1:-1]
        self.assertEqual(len(data), COUNT)
        for line in data:
            self.assertRegex(line, re.compile(r"^[0-9A-F]{8}$"))
        self.assertEqual([int(line, 16) for line in data], words(SEED, COUNT))

    def test_deterministic(self):
        first = words(SEED, COUNT)
        self.assertEqual(first, words(SEED, COUNT))
        self.assertTrue(all(0 <= w <= 0xFFFFFFFF for w in first))


class TestSeedDomain(unittest.TestCase):
    def test_rejects_invalid_seeds(self):
        for seed in ([1, 2, 3], [0, 0, 0, 65536], [-1, 0, 0, 0], [0, 0, 0, 1.0], [True, 0, 0, 0]):
            with self.subTest(seed=seed):
                with self.assertRaises(ValueError):
                    PhycoWebEngine(seed)

    def test_accepts_boundaries(self):
        PhycoWebEngine([65535, 0, 65535, 0])
        PhycoWebEngine([0, 0, 0, 0])

    def test_extra_seed_values_ignored(self):
        self.assertEqual(words(SEED + [99999], 100), words(SEED, 100))


if __name__ == "__main__":
    unittest.main()
