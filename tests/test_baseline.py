"""Archived floating-point variants are present and unmodified (FR-013, SC-006)."""
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "baseline" / "float-v0" / "MANIFEST.json"


class TestBaselineArchive(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_manifest_lists_five_files(self):
        self.assertEqual(len(self.manifest["files"]), 5)

    def test_hashes_match(self):
        for entry in self.manifest["files"]:
            with self.subTest(path=entry["archive_path"]):
                path = ROOT / entry["archive_path"]
                self.assertTrue(path.is_file())
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), entry["sha256"])

    def test_readmee_listing_is_float_variant(self):
        text = (ROOT / "baseline" / "float-v0" / "readmee_model.py").read_text(encoding="utf-8")
        self.assertIn("class PhycoWebEngine", text)
        self.assertIn("np.sin(self.step_count * 0.1)", text)


if __name__ == "__main__":
    unittest.main()
