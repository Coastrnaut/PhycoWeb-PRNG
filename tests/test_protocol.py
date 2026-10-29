"""Protocol tests for feature 002: seed sets (FR-015, SC-006, data-model section 2)."""
import hashlib
import unittest
from unittest import mock

from protocol import seedsets

SPEC_TABLE = {
    "dev": ((56053, 7029, 30841, 11050),
            "7e7e33c75e9e58048a26c1926e6addd4dc3514502574ea6687ded889aa47950e"),
    "heldout-1": ((44401, 31074, 35395, 61291),
                  "84a30b2e037550d0c6b1cfba1444eb0447fbc15b5b7c631ad8fc8a577dfca23d"),
    "heldout-2": ((61805, 51202, 28895, 20558),
                  "13120fcb1c1a49f6e6109f059982909470da33784bd0490f1e0f10252e214ad4"),
    "heldout-3": ((5899, 31471, 52105, 42678),
                  "af3b9b8e62829ef732a5c2bb2963c7655c9b461635da0c40d960b4c7eaace88f"),
}


class TestSeedSets(unittest.TestCase):
    def test_sets_match_spec_table(self):
        for name, (first, digest) in SPEC_TABLE.items():
            seeds = seedsets.derive(name)
            self.assertEqual(len(seeds), 100, name)
            self.assertEqual(len(set(seeds)), 100, name)
            self.assertEqual(seeds[0], first, name)
            text = seedsets.canonical_text(seeds).encode("ascii")
            self.assertEqual(hashlib.sha256(text).hexdigest(), digest, name)
            self.assertEqual(seedsets.FINGERPRINTS[name], digest, name)

    def test_sets_are_disjoint(self):
        sets = [set(seedsets.derive(name)) for name in SPEC_TABLE]
        for i in range(len(sets)):
            for j in range(i + 1, len(sets)):
                self.assertFalse(sets[i] & sets[j])

    def test_seed_values_in_domain(self):
        for name in SPEC_TABLE:
            for seed in seedsets.derive(name):
                self.assertEqual(len(seed), 4)
                self.assertTrue(all(type(v) is int and 0 <= v <= 0xFFFF for v in seed))

    def test_tampered_fingerprint_rejected(self):
        bad = dict(seedsets.FINGERPRINTS, dev="0" * 64)
        with mock.patch.object(seedsets, "FINGERPRINTS", bad):
            with self.assertRaises(ValueError):
                seedsets.load("dev", allow={"dev"})

    def test_allow_list_blocks_heldout(self):
        for name in ("heldout-1", "heldout-2", "heldout-3"):
            with self.assertRaises(PermissionError):
                seedsets.load(name, allow={"dev"})
        self.assertEqual(len(seedsets.load("dev", allow={"dev"})), 100)

    def test_unknown_set_rejected(self):
        with self.assertRaises(ValueError):
            seedsets.load("heldout-4", allow={"heldout-4"})


if __name__ == "__main__":
    unittest.main()
