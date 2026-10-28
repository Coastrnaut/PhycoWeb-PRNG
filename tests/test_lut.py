"""Perturbation table contents and artifacts (FR-003, FR-004, FR-005, FR-007, FR-007a, FR-012, SC-004)."""
import math
import subprocess
import sys
import unittest
from pathlib import Path

from phycoweb import lut

ROOT = Path(__file__).resolve().parents[1]
HEX_FILE = ROOT / "data" / "lut" / "perturbation_lut.hex"


def s16(value):
    return value - 0x10000 if value & 0x8000 else value


class TestPerturbationTable(unittest.TestCase):
    def test_matches_formula(self):
        expected = tuple(int(math.sin(2 * math.pi * i / 256) * 1024) & 0xFFFF for i in range(256))
        self.assertEqual(lut.PERTURBATION_LUT, expected)

    def test_reference_values(self):
        table = lut.PERTURBATION_LUT
        self.assertEqual(table[0], 0x0000)
        self.assertEqual(table[64], 0x0400)
        self.assertEqual(table[128], 0x0000)
        self.assertEqual(table[192], 0xFC00)

    def test_truncation_toward_zero_within_one_unit(self):
        for i, entry in enumerate(lut.PERTURBATION_LUT):
            with self.subTest(i=i):
                ideal = math.sin(2 * math.pi * i / 256) * 1024
                value = s16(entry)
                self.assertLessEqual(abs(value), 1024)
                self.assertLessEqual(abs(value), abs(ideal))
                self.assertLess(abs(ideal - value), 1)

    def test_constants(self):
        self.assertEqual(len(lut.PERTURBATION_LUT), 1 << lut.LUT_BITS)
        self.assertEqual(lut.LUT_BITS, 8)
        self.assertEqual(lut.INC_A, 4)
        self.assertEqual(lut.INC_B, 6)
        self.assertEqual(lut.COS_OFFSET, 64)

    def test_hex_file_matches_table(self):
        raw = HEX_FILE.read_bytes()
        self.assertNotIn(b"\r", raw)
        lines = raw.decode("ascii").split("\n")
        self.assertEqual(lines[-1], "")
        lines = lines[:-1]
        self.assertEqual(len(lines), 256)
        for i, line in enumerate(lines):
            with self.subTest(i=i):
                self.assertRegex(line, r"^[0-9A-F]{4}$")
                self.assertEqual(int(line, 16), lut.PERTURBATION_LUT[i])

    def test_generator_check_passes(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "gen_lut.py"), "--check"],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
