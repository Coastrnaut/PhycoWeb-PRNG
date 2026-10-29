"""Static checks that phyco-v2 is integer-only and multiplierless (T036; FR-001, SC-001)."""
import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "phycoweb" / "model_v2.py"

ALLOWED_IMPORTS = {"typing", "phycoweb.lut"}
BANNED_OPERATORS = (ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow, ast.MatMult)
BANNED_NAMES = {"sin", "cos", "float", "math"}


class TestModelV2Purity(unittest.TestCase):
    def setUp(self):
        self.tree = ast.parse(MODEL.read_text(encoding="utf-8"), filename=str(MODEL))

    def test_imports(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertIn(alias.name, ALLOWED_IMPORTS, f"line {node.lineno}")
            elif isinstance(node, ast.ImportFrom):
                self.assertIn(node.module, ALLOWED_IMPORTS, f"line {node.lineno}")

    def test_no_multiplication_division_modulo_or_power(self):
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.BinOp, ast.AugAssign)):
                self.assertNotIsInstance(node.op, BANNED_OPERATORS, f"line {node.lineno}")

    def test_no_float_constants(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Constant):
                self.assertNotIsInstance(node.value, (float, complex), f"line {node.lineno}")

    def test_no_trig_or_float_names(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Name):
                self.assertNotIn(node.id, BANNED_NAMES, f"line {node.lineno}")
            elif isinstance(node, ast.Attribute):
                self.assertNotIn(node.attr, BANNED_NAMES, f"line {node.lineno}")

    def test_shift_amounts_are_int_literals(self):
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.BinOp, ast.AugAssign)) and \
                    isinstance(node.op, (ast.LShift, ast.RShift)):
                amount = node.right if isinstance(node, ast.BinOp) else node.value
                self.assertIsInstance(amount, ast.Constant, f"line {node.lineno}")
                self.assertIs(type(amount.value), int, f"line {node.lineno}")


if __name__ == "__main__":
    unittest.main()
