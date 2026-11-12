"""Feature 005: the tests of its tools (tasks T039).

The ARX search's companion, research/005/tools/trails/arx_search_ops.c: on the ARX search's known results it finds the
optimum weights and the round-boundary states that feature 004's tool finds, and each step it prints gives that step's
exact weight, the weights summing to the trail's. Its binary is built and run in WSL, as feature 004's is.

This file makes no security claim.
"""
import importlib.util
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for place in (str(ROOT), str(ROOT / "research/004/tools/trails")):
    if place not in sys.path:
        sys.path.insert(0, place)

from protocol import trailcheck  # noqa: E402
from protocol.evidence import ToolFailure  # noqa: E402

SOURCE = ROOT / "research/005/tools/trails/arx_search_ops.c"
SOURCE_004 = ROOT / "research/004/tools/trails/arx_search.c"
BINARY = ROOT / "research/005/tools/trails/build/arx_search_ops"
BINARY_004 = ROOT / "research/004/tools/trails/build/arx_search"
KNOWN = ("speck32-diff", "speck32-lin")
ROUNDS = 6
# A box of the reference ARX design's form, two of its four steps, at a width a test can search.
SMALL_BOX = (("add", 1, 0, 1), ("xor", 0, 1, 1), ("add", 1, 0, 2), ("xor", 0, 1, 3))


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def driver():
    return load(ROOT / "research/005/tools/trails/arx_search_ops_known.py", "arx_search_ops_known")


def known(name: str):
    return load(ROOT / f"research/004/validation/{name}.py", "known_" + name.replace("-", "_"))


class TheSource(unittest.TestCase):
    """The companion is feature 004's search with its output added: no line of the search differs."""

    def test_feature_004s_lines_all_stand_in_it_but_the_names_and_the_two_calls(self):
        theirs = SOURCE_004.read_text(encoding="utf-8").split("\n")
        ours = set(SOURCE.read_text(encoding="utf-8").split("\n"))
        missing = [line for line in theirs if line not in ours]
        self.assertTrue(all("arx_search" in line or "search(" in line or line.startswith("/* Feature 004") for line in missing),
                        missing)
        self.assertLessEqual(len(missing), 12)

    def test_the_committed_binary_is_the_sources(self):
        if os.name == "nt" or not BINARY.exists():
            self.skipTest("the companion's binary is built and run in WSL")
        printed = subprocess.run([str(BINARY), "--source-sha256"], capture_output=True, text=True, check=True).stdout.strip()
        import hashlib
        self.assertEqual(printed, hashlib.sha256(SOURCE.read_bytes()).hexdigest())


class TheCompanion(unittest.TestCase):
    def setUp(self):
        if os.name == "nt" or not BINARY.exists() or not BINARY_004.exists():
            self.skipTest("the companion's binary is built and run in WSL")
        self.tool = driver()
        import arx_search_known
        self.theirs = arx_search_known

    def test_it_finds_feature_004s_weights_and_round_boundary_states(self):
        for name in KNOWN:
            result = known(name)
            ours = self.tool.search(result.KIND, result.W, ROUNDS, result.ROUND)
            theirs = self.theirs.search(result.KIND, result.W, ROUNDS, result.ROUND)
            table = self.tool.weights_of(result)
            for r in range(1, ROUNDS + 1):
                self.assertEqual(ours[r]["weight"], table[r], (name, r))
                self.assertEqual((ours[r]["weight"], ours[r]["walks"], ours[r]["trail"]),
                                 (theirs[r]["weight"], theirs[r]["walks"], theirs[r]["trail"]), (name, r))

    def test_each_step_printed_gives_its_exact_weight_and_the_weights_sum_to_the_trails(self):
        for name in KNOWN:
            result = known(name)
            found = self.tool.search(result.KIND, result.W, ROUNDS, result.ROUND)
            for r, row in found.items():
                rounds = self.tool.operations(result.KIND, result.W, result.ROUND, row)
                self.assertEqual(len(rounds), r)
                self.assertEqual(sum(item["weight"] for per_round in rounds for item in per_round), row["weight"], (name, r))
                for per_round in rounds:
                    for item in per_round:
                        if result.KIND == "differential":
                            count = trailcheck.add_count(result.W, item["inputs"][0], item["inputs"][1], item["output"])
                            self.assertEqual(count << item["weight"], 1 << (2 * result.W))
                        else:
                            total = trailcheck.add_sum(result.W, item["inputs"][0], item["inputs"][1], item["output"])
                            self.assertEqual(abs(total) << item["weight"], 1 << (2 * result.W))

    def test_a_box_of_several_additions_and_a_subtraction(self):
        for kind in ("differential", "linear"):
            found = self.tool.search(kind, 8, 3, SMALL_BOX)
            theirs = self.theirs.search(kind, 8, 3, SMALL_BOX)
            for r in (1, 2, 3):
                self.assertEqual((found[r]["weight"], found[r]["trail"]), (theirs[r]["weight"], theirs[r]["trail"]))
                rounds = self.tool.operations(kind, 8, SMALL_BOX, found[r])
                self.assertEqual([len(per_round) for per_round in rounds], [2] * r)
        mixed = (("sub", 0, 1, 3), ("xor", 1, 0, 5), ("add", 1, 0, 7), ("rot", 0, 2))
        for kind in ("differential", "linear"):
            found = self.tool.search(kind, 8, 3, mixed)
            for r, row in found.items():
                self.tool.operations(kind, 8, mixed, row)

    def test_a_changed_state_or_weight_is_a_tool_failure(self):
        result = known("speck32-diff")
        row = self.tool.search(result.KIND, result.W, 4, result.ROUND)[4]
        changed = dict(row, steps=[[list(pair) for pair in per_round] for per_round in row["steps"]])
        changed["steps"][0][1][0] ^= 1
        with self.assertRaises(ToolFailure):
            self.tool.operations(result.KIND, result.W, result.ROUND, changed)
        changed = dict(row, weights=[row["weights"][0] + 1] + row["weights"][1:])
        with self.assertRaises(ToolFailure):
            self.tool.operations(result.KIND, result.W, result.ROUND, changed)


if __name__ == "__main__":
    unittest.main()
