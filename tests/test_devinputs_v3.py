"""Feature 004: the development inputs (spec FR-040; research R3; data-model section 2; T033).

The strings and the fingerprint text are written out here a second time, apart from the module, so
that another implementation computes the same values. This file makes no security claim.
"""
import ast
import hashlib
import re
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

from protocol import devinputs_v3 as d
from protocol import evidence

from tests.support_004 import pin_feature_004  # noqa: E402

setUpModule, tearDownModule = pin_feature_004()

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "protocol/devinputs_v3.py"
SPEC_PAIRS = {(2, 4)} | {(n, w) for n in (2, 3, 4, 8, 16) for w in (8, 16, 32)}
CLAIMABLE = (4, 8, 16)
ALLOW = ("dev",)


def digest(text: str) -> bytes:
    return hashlib.sha256(text.encode("ascii")).digest()


def fingerprint(lines) -> str:
    return hashlib.sha256("".join(line + "\n" for line in lines).encode("ascii")).hexdigest()


def state_bytes(ns: str, n: int, w: int, i: int) -> bytes:
    size = 2 * w * n * n // 8
    out = b""
    j = 0
    while len(out) < size:
        out += digest(f"phycoweb-004/{ns}/state/n{n}w{w}/{i}/{j}")
        j += 1
    return out[:size]


class Strings(unittest.TestCase):
    """Each input is the digest of its public string, cut as research R3's table states."""

    def test_keys_nonces_and_reseed_inputs(self):
        keys = d.load("dev", "key", ALLOW, 3)
        nonces = d.load("dev", "nonce", ALLOW, 3)
        reseeds = d.load("dev", "reseed", ALLOW, 3)
        for i in range(3):
            self.assertEqual(keys[i], digest(f"phycoweb-004/dev/key/{i}"))
            self.assertEqual(nonces[i], digest(f"phycoweb-004/dev/nonce/{i}")[:16])
            self.assertEqual(reseeds[i], digest(f"phycoweb-004/dev/reseed/{i}"))

    def test_indices_are_decimal_without_leading_zeros(self):
        self.assertEqual(d.load("dev", "key", ALLOW, 11)[10], digest("phycoweb-004/dev/key/10"))

    def test_personalization_is_cut_to_min_m_and_32(self):
        for m in (0, 5, 32, 64):
            value = d.load("dev", "pers", ALLOW, 2, m=m)[1]
            self.assertEqual(value, digest("phycoweb-004/dev/pers/1")[:min(m, 32)])

    def test_the_empty_personalization_string_is_a_named_input(self):
        self.assertEqual(d.EMPTY_PERS, b"")

    def test_a_personalization_string_needs_the_design_maximum(self):
        with self.assertRaisesRegex(ValueError, "pers needs m"):
            d.load("dev", "pers", ALLOW, 1)

    def test_a_state_reads_the_digests_most_significant_bit_first(self):
        for n, w in sorted(SPEC_PAIRS):
            value = d.load("dev", "state", ALLOW, 2, n=n, w=w)[1]
            self.assertEqual(len(value), 2 * n * n, (n, w))
            whole = int.from_bytes(state_bytes("dev", n, w, 1), "big")
            total = 2 * w * n * n
            wanted = [(whole >> (total - w * (k + 1))) & ((1 << w) - 1) for k in range(2 * n * n)]
            self.assertEqual(value, wanted, (n, w))

    def test_a_state_of_several_digests_uses_consecutive_j(self):
        words = d.load("dev", "state", ALLOW, 1, n=16, w=32)[0]
        self.assertEqual(len(words), 512)
        self.assertEqual(words[8], int.from_bytes(digest(
            "phycoweb-004/dev/state/n16w32/0/1")[:4], "big"))

    def test_a_short_state_stops_inside_its_digest(self):
        words = d.load("dev", "state", ALLOW, 1, n=2, w=4)[0]
        head = digest("phycoweb-004/dev/state/n2w4/0/0")[:4].hex()
        self.assertEqual(words, [int(c, 16) for c in head])

    def test_the_uniform_controls_come_from_their_own_strings(self):
        value = d.load("control", "state", ("control",), 1, n=4, w=32)[0]
        wanted = state_bytes("control", 4, 32, 0)
        self.assertEqual(b"".join(word.to_bytes(4, "big") for word in value), wanted)
        self.assertNotEqual(value, d.load("dev", "state", ALLOW, 1, n=4, w=32)[0])

    def test_a_synthetic_seed_is_sixteen_bytes_read_big_endian(self):
        for n in CLAIMABLE:
            seeds = d.load("dev", "synthetic", ALLOW, 200, n=n)
            for j in (0, 99, 100, 199):
                wanted = digest(f"phycoweb-004/dev/synthetic/n{n}/{j}")[:16]
                self.assertEqual(seeds[j], int.from_bytes(wanted, "big"))


class Fingerprints(unittest.TestCase):
    """The text of data-model section 2, computed apart from the module."""

    def test_keys_and_the_rest(self):
        self.assertEqual(d.FINGERPRINTS["dev"]["key"], fingerprint(
            digest(f"phycoweb-004/dev/key/{i}").hex() for i in range(100)))
        self.assertEqual(d.FINGERPRINTS["dev"]["nonce"], fingerprint(
            digest(f"phycoweb-004/dev/nonce/{i}")[:16].hex() for i in range(100)))
        self.assertEqual(d.FINGERPRINTS["dev"]["reseed"], fingerprint(
            digest(f"phycoweb-004/dev/reseed/{i}").hex() for i in range(100)))

    def test_personalization_covers_the_full_32_bytes(self):
        self.assertEqual(d.FINGERPRINTS["dev"]["pers"], fingerprint(
            digest(f"phycoweb-004/dev/pers/{i}").hex() for i in range(100)))

    def test_states_in_both_namespaces(self):
        for ns in ("dev", "control"):
            for pair in SPEC_PAIRS:
                self.assertEqual(d.FINGERPRINTS[ns]["state"][pair], fingerprint(
                    state_bytes(ns, *pair, i).hex().upper() for i in range(100)), (ns, pair))

    def test_synthetic_seeds_as_decimal_integers(self):
        for n in CLAIMABLE:
            self.assertEqual(d.FINGERPRINTS["dev"]["synthetic"][n], fingerprint(
                str(int.from_bytes(digest(f"phycoweb-004/dev/synthetic/n{n}/{j}")[:16], "big"))
                for j in range(100)), n)

    def test_every_allowed_pair_has_a_fingerprint_and_no_other_does(self):
        self.assertEqual(set(d.PAIRS), SPEC_PAIRS)
        self.assertEqual(len(d.PAIRS), 16)
        for ns in d.NAMESPACES:
            self.assertEqual(set(d.FINGERPRINTS[ns]["state"]), SPEC_PAIRS)

    def test_the_synthetic_seeds_stand_at_the_claimable_sizes_only(self):
        self.assertEqual(sorted(d.FINGERPRINTS["dev"]["synthetic"]), list(CLAIMABLE))
        self.assertNotIn("synthetic", d.FINGERPRINTS["control"])

    def test_a_changed_fingerprint_is_refused_at_load(self):
        wrong = dict(d.FINGERPRINTS["dev"], key="0" * 64)
        with mock.patch.dict(d.FINGERPRINTS, {"dev": wrong}):
            with self.assertRaisesRegex(ValueError, "fingerprint"):
                d.load("dev", "key", ALLOW, 1)

    def test_a_changed_derivation_is_refused_at_load(self):
        with mock.patch.object(d, "PREFIX", "phycoweb-005/"):
            for call in (lambda: d.load("dev", "nonce", ALLOW, 1),
                         lambda: d.load("dev", "state", ALLOW, 1, n=2, w=8),
                         lambda: d.load("dev", "synthetic", ALLOW, 1, n=4)):
                with self.assertRaisesRegex(ValueError, "fingerprint"):
                    call()

    def test_load_checks_every_pair(self):
        for ns in d.NAMESPACES:
            for n, w in sorted(SPEC_PAIRS):
                self.assertEqual(len(d.load(ns, "state", (ns,), 1, n=n, w=w)), 1)


class Refusals(unittest.TestCase):

    def test_no_other_namespace_is_accepted(self):
        for ns in ("heldout", "heldout-1", "DEV", "", "dev/"):
            with self.assertRaisesRegex(ValueError, "namespace"):
                d.load(ns, "key", (ns,), 1)

    def test_a_namespace_must_be_allowed_here(self):
        with self.assertRaisesRegex(PermissionError, "not allowed here"):
            d.load("dev", "key", ("control",), 1)
        with self.assertRaisesRegex(PermissionError, "not allowed here"):
            d.load("control", "state", ALLOW, 1, n=4, w=32)

    def test_control_serves_only_uniform_controls(self):
        for kind in ("key", "nonce", "reseed"):
            with self.assertRaisesRegex(PermissionError, "control"):
                d.load("control", kind, ("control",), 1)
        with self.assertRaisesRegex(PermissionError, "control"):
            d.load("control", "pers", ("control",), 1, m=8)
        with self.assertRaisesRegex(PermissionError, "control"):
            d.load("control", "synthetic", ("control",), 1, n=4)

    def test_a_synthetic_seed_is_dev_only(self):
        with self.assertRaisesRegex(ValueError, "dev"):
            d.synthetic_seed("control", 4, 0)

    def test_an_unknown_kind_is_refused_naming_it(self):
        with self.assertRaisesRegex(ValueError, "'held'"):
            d.load("dev", "held", ALLOW, 1)

    def test_a_pair_without_a_fingerprint_is_refused_naming_it(self):
        for n, w in ((5, 32), (4, 4), (3, 4), (16, 64)):
            with self.assertRaisesRegex(ValueError, rf"\({n}, {w}\)"):
                d.load("dev", "state", ALLOW, 1, n=n, w=w)

    def test_a_size_without_a_synthetic_fingerprint_is_refused_naming_it(self):
        for n in (2, 3):
            with self.assertRaisesRegex(ValueError, rf"n={n}"):
                d.load("dev", "synthetic", ALLOW, 1, n=n)

    def test_a_state_needs_its_size(self):
        with self.assertRaisesRegex(ValueError, "state needs n and w"):
            d.load("dev", "state", ALLOW, 1, n=4)
        with self.assertRaisesRegex(ValueError, "synthetic needs n"):
            d.load("dev", "synthetic", ALLOW, 1)

    def test_a_kind_takes_only_its_own_arguments(self):
        with self.assertRaisesRegex(ValueError, "takes no"):
            d.load("dev", "key", ALLOW, 1, n=4)
        with self.assertRaisesRegex(ValueError, "takes no"):
            d.load("dev", "state", ALLOW, 1, n=4, w=32, m=8)

    def test_a_count_is_a_positive_whole_number(self):
        for count in (0, -1, 1.5, "3", True):
            with self.assertRaisesRegex(ValueError, "count"):
                d.load("dev", "key", ALLOW, count)

    def test_no_index_outside_the_declared_range_can_be_read(self):
        values = d.load("dev", "key", ALLOW, 3)
        self.assertEqual(len(values), 3)
        self.assertEqual(len(list(values)), 3)
        for index in (3, 4, 1000, -4):
            with self.assertRaises(IndexError):
                values[index]
        self.assertEqual(values[-1], values[2])
        self.assertEqual(values[1:9], [values[1], values[2]])

    def test_an_index_is_a_whole_number(self):
        values = d.load("dev", "key", ALLOW, 3)
        for index in ("0", 1.0, True, None):
            with self.assertRaises(TypeError):
                values[index]

    def test_a_large_range_costs_nothing_until_it_is_read(self):
        values = d.load("control", "state", ("control",), 1 << 21, n=16, w=32)
        self.assertEqual(len(values), 1 << 21)
        self.assertEqual(len(values[(1 << 21) - 1]), 512)


class ScriptExits(unittest.TestCase):
    """Quickstart P2 and P3: a script exits 2 on the loader's refusal, as on any other."""

    def guarded(self, call) -> int:
        def run() -> int:
            call()
            return evidence.EXIT_OK
        with mock.patch("sys.stderr"):
            return evidence.main_guard(run)

    def test_quickstart_p2(self):
        command = ("from protocol import devinputs_v3 as d; "
                   "print(d.load('dev', 'key', allow=('dev',), count=1)[0].hex())")
        out = subprocess.run([sys.executable, "-c", command], cwd=ROOT, capture_output=True,
                             text=True, check=True).stdout.strip()
        self.assertRegex(out, r"^[0-9a-f]{64}$")

    def test_quickstart_p3_another_namespace_exits_2(self):
        for ns in ("heldout-1", "other"):
            self.assertEqual(self.guarded(lambda: d.load(ns, "key", (ns,), 1)),
                             evidence.EXIT_REFUSED)

    def test_every_refusal_of_the_loader_exits_2(self):
        for call in (lambda: d.load("dev", "key", ("control",), 1),
                     lambda: d.load("control", "key", ("control",), 1),
                     lambda: d.load("dev", "held", ALLOW, 1),
                     lambda: d.load("dev", "state", ALLOW, 1, n=5, w=32),
                     lambda: d.load("dev", "synthetic", ALLOW, 1, n=2),
                     lambda: d.load("dev", "key", ALLOW, 0)):
            self.assertEqual(self.guarded(call), evidence.EXIT_REFUSED)

    def test_a_refused_fingerprint_exits_2(self):
        wrong = dict(d.FINGERPRINTS["dev"], key="0" * 64)
        with mock.patch.dict(d.FINGERPRINTS, {"dev": wrong}):
            self.assertEqual(self.guarded(lambda: d.load("dev", "key", ALLOW, 1)),
                             evidence.EXIT_REFUSED)

    def test_a_permission_error_of_the_system_stays_a_tool_failure(self):
        def denied() -> None:
            raise PermissionError("the disk said no")
        self.assertEqual(self.guarded(denied), evidence.EXIT_TOOL)


class ControlStates(unittest.TestCase):
    """The evidence tool's uniform-control states are research R3's control states, as this module derives them. The check lives with
    the module's own tests, the only code beside the module that may call a derivation (TheModule's guard)."""

    def test_the_control_inputs_are_research_r3s_control_states(self):
        import importlib.util
        if "evidence_v3" not in sys.modules:
            spec = importlib.util.spec_from_file_location("evidence_v3", ROOT / "scripts/evidence_v3.py")
            module = importlib.util.module_from_spec(spec)
            sys.modules["evidence_v3"] = module
            spec.loader.exec_module(module)
        states = sys.modules["evidence_v3"].control_states(4, 2, 3)
        self.assertEqual([int(value) for value in states[:, 0]], list(d.state("control", 4, 32, 2)))
        self.assertEqual([int(value) for value in states[:, 2]], list(d.state("control", 4, 32, 4)))


class TheModule(unittest.TestCase):

    def tree(self) -> ast.Module:
        return ast.parse(MODULE.read_bytes().decode("utf-8"))

    def test_it_imports_only_hashlib(self):
        imported = set()
        for node in ast.walk(self.tree()):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.add(node.module)
        self.assertEqual(imported, {"hashlib"})

    def test_the_constants_of_data_model_section_2(self):
        self.assertEqual(d.PREFIX, "phycoweb-004/")
        self.assertEqual(tuple(d.NAMESPACES), ("dev", "control"))

    def test_the_closed_class_holds_only_its_listed_members(self):
        text = (ROOT / "specs/004-crypto-architecture-v3/data-model.md").read_bytes().decode("utf-8")
        section = text[text.index("**Constructed inputs**"):]
        rows = re.findall(r"^\| ([1-9]) \| ([^|]+?) \|", section, re.M)
        self.assertEqual([number for number, _ in rows], ["1", "2", "3", "4", "5"])
        self.assertEqual([name for _, name in rows], list(d.CONSTRUCTED))

    def test_a_constructed_class_is_no_kind_of_the_loader(self):
        for name in d.CONSTRUCTED:
            with self.assertRaises(ValueError):
                d.load("dev", name, ALLOW, 1)

    def test_no_code_outside_the_module_and_its_tests_calls_a_derivation(self):
        names = {"digest", "key", "nonce", "pers", "reseed", "state", "state_bytes",
                 "synthetic_seed"}
        allowed = {MODULE, Path(__file__).resolve()}
        offenders = []
        for top in ("phycoweb", "protocol", "scripts", "research/004", "tests"):
            for path in (ROOT / top).rglob("*.py"):
                if path.resolve() in allowed:
                    continue
                source = path.read_bytes().decode("utf-8", "replace")
                if "devinputs_v3" not in source:
                    continue
                aliases = set()
                tree = ast.parse(source)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        for alias in node.names:
                            if node.module == "protocol.devinputs_v3" and alias.name in names:
                                offenders.append(f"{path}: imports {alias.name}")
                            if alias.name == "devinputs_v3":
                                aliases.add(alias.asname or alias.name)
                    elif isinstance(node, ast.Import):
                        for alias in node.names:
                            if alias.name == "protocol.devinputs_v3":
                                aliases.add(alias.asname or "protocol")
                for node in ast.walk(tree):
                    if isinstance(node, ast.Attribute) and node.attr in names:
                        base = node.value
                        if isinstance(base, ast.Attribute):
                            base = base.value
                        if isinstance(base, ast.Name) and base.id in aliases:
                            offenders.append(f"{path}:{node.lineno}: {node.attr}")
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
