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


if __name__ == "__main__":
    unittest.main()
