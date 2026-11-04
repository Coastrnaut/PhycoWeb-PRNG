"""Feature 004: the FUT-SEC-8 search tool (FR-001, FR-002, FR-053; research R2, R16; T038).

WSL only, like the tool. A full sweep is a heavy run, so these tests build the same source with a
small S2_COUNT in a temporary directory, which leaves the sweep's own code in the test. This file
makes no security claim.
"""
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from phycoweb.model_v2 import PhycoWebEngineV2

ROOT = Path(__file__).resolve().parents[1]
FAST = ROOT / "fast"
SOURCE = FAST / "seed_search.c"
BINARY = FAST / "build/seed_search"
FROZEN = (FAST / "build/phyco_stream", FAST / "Makefile", FAST / "phyco_stream.c")
ONLY = "the search tool is built and run in WSL only"
SEED = (41278, 32039, 2, 12345)


def sha256_of(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def words_of(seed, count: int):
    engine = PhycoWebEngineV2(seed)
    return [engine.compute_block() for _ in range(count)]


def vector_text(seed, count: int = 10000) -> str:
    head = f"# model=phyco-v2 seed={','.join(map(str, seed))} count={count} format=u32-hex\n"
    return head + "".join(f"{word:08X}\n" for word in words_of(seed, count))


def run(binary: Path, *args: str):
    return subprocess.run([str(binary), *args], capture_output=True, text=True)


def small_build(directory: Path, s2_count: int) -> Path:
    """The committed source and make file in a directory of their own, with a small S2_COUNT."""
    for name in ("seed_search.c", "seed_search.mk", "lut_table.h"):
        shutil.copy(FAST / name, directory / name)
    subprocess.run(["make", "-C", str(directory), "-f", "seed_search.mk",
                    f"EXTRA=-DS2_COUNT={s2_count}u"], capture_output=True, check=True)
    return directory / "build/seed_search"


@unittest.skipUnless(sys.platform == "linux", ONLY)
class Build(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.before = {path: sha256_of(path) for path in FROZEN}
        cls.built = subprocess.run(["make", "-C", str(FAST), "-f", "seed_search.mk"],
                                   capture_output=True, text=True)

    def test_quickstart_u1_it_builds(self):
        self.assertEqual(self.built.returncode, 0, self.built.stderr)
        self.assertTrue(BINARY.is_file())

    def test_it_compiles_with_werror_relative_paths_and_no_debug_information(self):
        plan = subprocess.run(["make", "-n", "-B", "-C", str(FAST), "-f", "seed_search.mk"],
                              capture_output=True, text=True, check=True).stdout
        line = next(ln for ln in plan.splitlines() if "seed_search.c" in ln and "gcc" in ln)
        self.assertIn("-Werror", line)
        self.assertNotRegex(line, r"(^|\s)-g\d?(\s|$)")
        self.assertNotIn(str(ROOT), line)

    def test_it_prints_the_sha256_of_its_source(self):
        done = run(BINARY, "--source-sha256")
        self.assertEqual(done.returncode, 0)
        self.assertEqual(done.stdout.strip(), sha256_of(SOURCE))

    def test_the_same_source_builds_the_same_binary_in_a_second_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "elsewhere"
            directory.mkdir()
            for name in ("seed_search.c", "seed_search.mk", "lut_table.h"):
                shutil.copy(FAST / name, directory / name)
            subprocess.run(["make", "-C", str(directory), "-f", "seed_search.mk"],
                           capture_output=True, check=True)
            self.assertEqual(sha256_of(directory / "build/seed_search"), sha256_of(BINARY))

    def test_the_frozen_files_are_untouched(self):
        self.assertEqual({path: sha256_of(path) for path in FROZEN}, self.before)

    def test_the_make_file_names_no_target_of_the_frozen_binary(self):
        text = (FAST / "seed_search.mk").read_text(encoding="utf-8")
        self.assertNotIn("phyco_stream", text)
        self.assertNotIn("clean", text)


@unittest.skipUnless(sys.platform == "linux", ONLY)
class Vectors(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)

    def check(self, *paths):
        done = run(BINARY, "--check-vectors", *map(str, paths))
        return done.returncode, json.loads(done.stdout) if done.stdout.strip() else None

    def test_quickstart_u2_both_golden_files(self):
        paths = sorted(ROOT.glob("vectors/phyco-v2_*.hex"))
        self.assertEqual(len(paths), 2)
        code, out = self.check(*paths)
        self.assertEqual(code, 0)
        self.assertEqual([(f["words"], f["mismatches"]) for f in out["files"]],
                         [(10000, 0), (10000, 0)])

    def test_the_step_agrees_with_the_python_model_on_other_seeds(self):
        seeds = ((0, 0, 0, 0), (65535, 65535, 65535, 65535), (1, 2, 3, 4), (0, 65535, 0, 65535),
                 (41278, 32039, 25293, 40850))
        paths = []
        for number, seed in enumerate(seeds):
            path = self.dir / f"{number}.hex"
            path.write_text(vector_text(seed), encoding="ascii")
            paths.append(path)
        code, out = self.check(*paths)
        self.assertEqual(code, 0, out)

    def test_one_word_wrong_exits_1_and_counts_it(self):
        lines = vector_text(SEED).split("\n")
        lines[5000] = f"{int(lines[5000], 16) ^ 1:08X}"
        path = self.dir / "wrong.hex"
        path.write_text("\n".join(lines), encoding="ascii")
        code, out = self.check(path)
        self.assertEqual(code, 1)
        self.assertEqual(out["files"][0]["mismatches"], 1)
        self.assertEqual(out["files"][0]["words"], 10000)

    def test_a_short_file_exits_1(self):
        lines = vector_text(SEED).split("\n")
        path = self.dir / "short.hex"
        path.write_text("\n".join(lines[:9000]) + "\n", encoding="ascii")
        self.assertEqual(self.check(path)[0], 1)

    def test_another_count_exits_1(self):
        path = self.dir / "fewer.hex"
        path.write_text(vector_text(SEED, 100), encoding="ascii")
        self.assertEqual(self.check(path)[0], 1)

    def test_a_header_that_misstates_the_count_exits_1(self):
        path = self.dir / "misstated.hex"
        path.write_text(vector_text(SEED).replace("count=10000", "count=100"), encoding="ascii")
        self.assertEqual(self.check(path)[0], 1)

    def test_a_good_file_does_not_hide_a_bad_one_in_either_order(self):
        good = self.dir / "good.hex"
        good.write_text(vector_text(SEED), encoding="ascii")
        bad = self.dir / "bad.hex"
        bad.write_text(vector_text(SEED).replace("seed=41278", "seed=41279"), encoding="ascii")
        self.assertEqual(self.check(good, bad)[0], 1)
        self.assertEqual(self.check(bad, good)[0], 1)

    def test_a_missing_file_exits_1(self):
        done = run(BINARY, "--check-vectors", str(self.dir / "absent.hex"))
        self.assertEqual(done.returncode, 1)

    def test_a_header_that_names_another_model_exits_1(self):
        path = self.dir / "other.hex"
        path.write_text(vector_text(SEED).replace("model=phyco-v2", "model=lut-v1"), "ascii")
        self.assertEqual(self.check(path)[0], 1)


@unittest.skipUnless(sys.platform == "linux", ONLY)
class Arguments(unittest.TestCase):

    GOOD = ("--s0", "1", "--s1", "2", "--words", "00000001", "00000002", "00000003")

    def refused(self, *args):
        done = run(BINARY, *args)
        self.assertEqual(done.returncode, 2, args)
        self.assertEqual(done.stdout, "", args)

    def test_anything_else_exits_2(self):
        self.refused()
        self.refused("--help")
        self.refused("--check-vectors")
        self.refused("--source-sha256", "extra")
        self.refused(*self.GOOD, "--unknown")
        self.refused(*self.GOOD, "positional")
        self.refused(*self.GOOD, "--threads")
        self.refused(*self.GOOD, "--threads", "0")
        self.refused(*self.GOOD, "--threads", "x")
        self.refused(*self.GOOD, "--threads", "4097")
        self.refused(*self.GOOD, "--progress", "0")
        self.refused(*self.GOOD, "--progress", "1.5")

    def test_s0_and_s1_are_integers_up_to_65535(self):
        for value in ("-1", "65536", "x", "1x", "", "0x10"):
            self.refused("--s0", value, "--s1", "2", "--words", "1", "2", "3")
            self.refused("--s0", "1", "--s1", value, "--words", "1", "2", "3")

    def test_each_word_is_a_32_bit_hex_word(self):
        for value in ("123456789", "xyz", "", "0x1", "-1"):
            self.refused("--s0", "1", "--s1", "2", "--words", value, "2", "3")

    def test_every_required_argument_is_required(self):
        self.refused("--s0", "1", "--s1", "2")
        self.refused("--s1", "2", "--words", "1", "2", "3")
        self.refused("--s0", "1", "--words", "1", "2", "3")
        self.refused("--s0", "1", "--s1", "2", "--words", "1", "2")


@unittest.skipUnless(sys.platform == "linux", ONLY)
class Sweep(unittest.TestCase):
    """The sweep's code, over the first s2 values only, against the Python model."""

    S2 = 4
    CANDIDATES = 4 * 65536

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.binary = small_build(Path(cls.tmp.name), cls.S2)

    def sweep(self, words, *extra, s0=SEED[0], s1=SEED[1]):
        done = run(self.binary, "--s0", str(s0), "--s1", str(s1), "--words",
                   *(f"{word:08X}" for word in words), *extra)
        self.assertEqual(done.returncode, 0, done.stderr)
        return json.loads(done.stdout), done.stderr

    def test_the_target_is_recovered_from_three_words(self):
        out, _ = self.sweep(words_of(SEED, 3))
        self.assertIn([SEED[2], SEED[3]], out["three_word_matches"])
        self.assertGreaterEqual(out["after_one"], out["after_two"])
        self.assertGreaterEqual(out["after_two"], out["after_three"])
        self.assertGreaterEqual(out["after_three"], 1)

    def test_it_echoes_what_it_searched(self):
        out, _ = self.sweep(words_of(SEED, 3), "--threads", "3")
        self.assertEqual(out["s0"], SEED[0])
        self.assertEqual(out["s1"], SEED[1])
        self.assertEqual(out["words"], [f"{w:08X}" for w in words_of(SEED, 3)])
        self.assertEqual(out["threads"], 3)
        self.assertEqual(out["candidates"], self.CANDIDATES)

    def test_a_candidate_is_dropped_at_its_first_mismatch(self):
        w1, w2, w3 = words_of(SEED, 3)
        out, _ = self.sweep((w1, w2 ^ 1, w3))
        self.assertGreaterEqual(out["after_one"], 1)
        self.assertEqual(out["after_two"], 0)
        self.assertEqual(out["after_three"], 0)
        out, _ = self.sweep((w1, w2, w3 ^ 1))
        self.assertGreaterEqual(out["after_two"], 1)
        self.assertEqual(out["after_three"], 0)
        self.assertEqual(out["three_word_matches"], [])

    def test_a_seed_outside_the_range_is_not_found(self):
        out, _ = self.sweep(words_of((SEED[0], SEED[1], self.S2, 5), 3))
        self.assertEqual(out["three_word_matches"], [])

    def test_the_last_candidate_of_the_range_is_reached(self):
        seed = (SEED[0], SEED[1], self.S2 - 1, 65535)
        out, _ = self.sweep(words_of(seed, 3))
        self.assertEqual(out["three_word_matches"], [[seed[2], seed[3]]])

    def test_the_first_candidate_is_reached(self):
        seed = (SEED[0], SEED[1], 0, 0)
        out, _ = self.sweep(words_of(seed, 3))
        self.assertIn([0, 0], out["three_word_matches"])

    def test_total_steps_count_every_step(self):
        out, _ = self.sweep(words_of(SEED, 3))
        wanted = 257 * self.CANDIDATES + out["after_one"] + out["after_two"]
        self.assertEqual(out["total_steps"], wanted)

    def test_the_rate_is_steps_over_seconds(self):
        out, _ = self.sweep(words_of(SEED, 3))
        self.assertGreater(out["seconds"], 0)
        self.assertAlmostEqual(out["steps_per_second"] * out["seconds"], out["total_steps"],
                               delta=out["total_steps"] * 1e-3)

    def test_the_count_after_one_word_agrees_with_the_python_model(self):
        probe = (SEED[0], SEED[1], 1, 777)
        word = words_of(probe, 1)[0]
        out, _ = self.sweep((word, word ^ 1, 0))
        self.assertGreaterEqual(out["after_one"], 1)
        self.assertLess(out["after_one"], 5)

    def test_the_result_does_not_depend_on_the_threads(self):
        words = words_of(SEED, 3)
        results = [self.sweep(words, "--threads", str(n))[0] for n in (1, 2, 7)]
        for field in ("after_one", "after_two", "after_three", "three_word_matches", "total_steps",
                      "candidates"):
            self.assertEqual({json.dumps(r[field]) for r in results}.__len__(), 1, field)

    def test_more_threads_than_rows_of_work(self):
        out, _ = self.sweep(words_of(SEED, 3), "--threads", "32")
        self.assertIn([SEED[2], SEED[3]], out["three_word_matches"])

    def test_nothing_goes_to_stderr_without_progress(self):
        _, err = self.sweep(words_of(SEED, 3))
        self.assertEqual(err, "")

    def test_progress_goes_to_stderr_and_stdout_stays_one_json_object(self):
        words = words_of(SEED, 3)
        out, err = self.sweep(words, "--progress", "1")
        self.assertIn("after_one", out)
        lines = err.strip().splitlines()
        self.assertGreaterEqual(len(lines), 1)
        for line in lines:
            self.assertRegex(line, r"^progress: \d+ of \d+ s2 values")


class ProgressWriter(unittest.TestCase):
    """Only the main thread writes: the workers' code calls nothing that writes (research R2)."""

    def body_of(self, name: str) -> str:
        text = SOURCE.read_text(encoding="utf-8")
        begin, end = f"/* BEGIN {name} */", f"/* END {name} */"
        self.assertEqual(text.count(begin), 1, begin)
        self.assertEqual(text.count(end), 1, end)
        return text[text.index(begin):text.index(end)]

    def test_the_workers_write_nothing(self):
        body = self.body_of("worker")
        self.assertNotRegex(body, r"\b(printf|fprintf|vfprintf|fputs|puts|putc|fputc|perror|write|"
                                  r"fwrite|dprintf|exit|abort)\s*\(")

    def test_the_workers_update_the_counter_the_main_thread_reads(self):
        self.assertIn("rows_done", self.body_of("worker"))

    def test_the_binary_is_committed_executable(self):
        """A commit from Windows records no execute bit, and a clone on Linux could not run it."""
        line = subprocess.run(["git", "-C", str(ROOT), "ls-files", "-s", "fast/build/seed_search"],
                              capture_output=True, text=True, check=True).stdout
        self.assertTrue(line.startswith("100755 "), line)

    def test_the_tool_keeps_its_own_copy_of_the_step(self):
        text = SOURCE.read_text(encoding="utf-8")
        self.assertNotIn('#include "phyco_stream', text)
        self.assertIn('#include "lut_table.h"', text)
        self.assertEqual(len(re.findall(r"^#define WARMUP 256$", text, re.M)), 1)

    def test_the_branches_no_seed_reaches_are_the_frozen_stream_tools(self):
        """S12: classes 2 and 3 are in effect unused, so no vector shows a slip in them, and the
        text is what can be held to the source feature 003 froze."""
        stream = (FAST / "phyco_stream.c").read_text(encoding="utf-8")
        text = SOURCE.read_text(encoding="utf-8")
        lines = re.findall(r"^\s+(?:case \d|default): return neg \?.*$", stream, re.M)
        self.assertEqual(len(lines), 4)
        for line in lines:
            self.assertIn(line.strip(), text)

    def test_the_step_holds_no_multiplication_division_or_modulo(self):
        code = re.sub(r"/\*.*?\*/", "", self.body_of("phyco-v2"), flags=re.S)
        self.assertNotRegex(code, r"[/%]|\w\s\*\s\w")


if __name__ == "__main__":
    unittest.main()
