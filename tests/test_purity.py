"""Static checks that the generator is integer-only (FR-001, FR-002, SC-001 as amended)."""
import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "phycoweb" / "model.py"
LUT = ROOT / "phycoweb" / "lut.py"

ALLOWED_IMPORTS = {"typing", "phycoweb.lut", "lut"}
BANNED_OPERATORS = (ast.Div, ast.FloorDiv, ast.Mod, ast.Pow)
BANNED_NAMES = {"sin", "cos", "float", "math"}


def parse(path):
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


class TestModelPurity(unittest.TestCase):
    def setUp(self):
        self.tree = parse(MODEL)

    def test_imports(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertIn(alias.name, ALLOWED_IMPORTS)
            elif isinstance(node, ast.ImportFrom):
                self.assertIn(node.module, ALLOWED_IMPORTS)

    def test_no_float_constants(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Constant):
                self.assertNotIsInstance(node.value, (float, complex), f"line {node.lineno}")

    def test_no_division_modulo_or_power(self):
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.BinOp, ast.AugAssign)):
                self.assertNotIsInstance(node.op, BANNED_OPERATORS, f"line {node.lineno}")

    def test_no_trig_or_float_names(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Name):
                self.assertNotIn(node.id, BANNED_NAMES, f"line {node.lineno}")
            elif isinstance(node, ast.Attribute):
                self.assertNotIn(node.attr, BANNED_NAMES, f"line {node.lineno}")

    def test_perturbation_stage_has_no_multiplication(self):
        functions = [n for n in ast.walk(self.tree)
                     if isinstance(n, ast.FunctionDef) and n.name == "_perturb"]
        self.assertEqual(len(functions), 1, "_perturb must exist exactly once")
        for node in ast.walk(functions[0]):
            if isinstance(node, (ast.BinOp, ast.AugAssign)):
                self.assertNotIsInstance(node.op, ast.Mult, f"line {node.lineno}")


class TestLutPurity(unittest.TestCase):
    def test_only_int_literals(self):
        tree = parse(LUT)
        for node in ast.walk(tree):
            self.assertNotIsInstance(node, (ast.Import, ast.ImportFrom, ast.Call, ast.BinOp))
            if isinstance(node, ast.Constant):
                self.assertIs(type(node.value), int, f"line {node.lineno}")


if __name__ == "__main__":
    unittest.main()
