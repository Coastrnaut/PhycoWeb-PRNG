"""Feature 003 US3: fast stream checks (T012; FR-007, FR-008, SC-003).

The static checks run everywhere. The binary checks need the WSL build
(`make -C fast`) and run only on Linux; elsewhere they are skipped.
"""
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in (str(ROOT), str(ROOT / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import gen_c_lut  # noqa: E402
import stream_equiv  # noqa: E402

SOURCE = ROOT / "fast" / "phyco_stream.c"
BINARY = ROOT / "fast" / "build" / "phyco_stream"
HAVE_BINARY = sys.platform.startswith("linux") and BINARY.exists()


def phyco_v2_block() -> str:
    text = SOURCE.read_text(encoding="ascii")
    block = text.split("/* BEGIN phyco-v2", 1)[1].split("/* END phyco-v2 */", 1)[0]
    block = block.split("*/", 1)[1]                       # rest of the BEGIN comment
    block = re.sub(r"/\*.*?\*/", "", block, flags=re.S)   # block comments
    return re.sub(r"//[^\n]*", "", block)                 # line comments


class TestStatic(unittest.TestCase):
    def test_lut_header_up_to_date(self):
        self.assertEqual((ROOT / "fast" / "lut_table.h").read_text(encoding="ascii"),
                         gen_c_lut.render())

    def test_phyco_v2_has_no_multiply_divide_modulo(self):
        block = phyco_v2_block()
        self.assertIn("v2_step", block)
        for op in ("*", "/", "%"):
            self.assertNotIn(op, block, f"operator {op!r} in the phyco-v2 block (FR-001 of 002)")


def run(*args, **kw):
    return subprocess.run([str(BINARY), *args], capture_output=True, **kw)


@unittest.skipUnless(HAVE_BINARY, "needs the WSL build of fast/build/phyco_stream")
class TestBinary(unittest.TestCase):
    def test_golden_vectors(self):
        for name, res in stream_equiv.golden(BINARY).items():
            self.assertEqual(res["mismatches"], 0, name)
            self.assertEqual(res["words"], 10000, name)

    def test_bad_seed_and_usage_exit_2(self):
        for args in (("phyco-v2", "1", "2", "3", "70000"), ("lut-v1", "1", "2", "3", "-1"),
                     ("phyco-v2", "1", "2", "3", "x"), ("bogus",), ("os", "--words", "0")):
            self.assertEqual(run(*args).returncode, 2, args)

    def test_reverse_reverses_bits(self):
        fwd = run("phyco-v2", "1", "2", "3", "4", "--words", "64", "--hex", text=True).stdout.split()
        rev = run("phyco-v2", "1", "2", "3", "4", "--words", "64", "--hex", "--reverse",
                  text=True).stdout.split()
        self.assertEqual([int(f"{int(w, 16):032b}"[::-1], 2) for w in fwd],
                         [int(w, 16) for w in rev])

    def test_binary_matches_hex_little_endian(self):
        hexw = run("lut-v1", "5", "6", "7", "8", "--words", "16", "--hex", text=True).stdout.split()
        raw = run("lut-v1", "5", "6", "7", "8", "--words", "16").stdout
        self.assertEqual([int.from_bytes(raw[i:i + 4], "little") for i in range(0, 64, 4)],
                         [int(w, 16) for w in hexw])

    def test_os_words(self):
        out = run("os", "--words", "4", "--hex", text=True)
        self.assertEqual(out.returncode, 0)
        self.assertEqual(len(out.stdout.split()), 4)

    def test_closed_pipe_exits_0(self):
        proc = subprocess.Popen([str(BINARY), "phyco-v2", "1", "2", "3", "4"],
                                stdout=subprocess.PIPE)
        proc.stdout.read(1 << 20)
        proc.stdout.close()
        self.assertEqual(proc.wait(timeout=10), 0)


if __name__ == "__main__":
    unittest.main()
