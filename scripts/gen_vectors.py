"""Generate or verify golden output-vector files (spec FR-010, FR-014).

Format: contracts/file-formats.md. Words are unsigned 32-bit, 8 uppercase hex digits per line.
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
import warnings
from pathlib import Path
from typing import Callable, Iterator, List, Sequence

ROOT = Path(__file__).resolve().parents[1]
FLOAT_V0_PATH = ROOT / "baseline" / "float-v0" / "readmee_model.py"

MODELS = ("float-v0", "lut-v1")


def load_float_v0():
    """Load the archived readmee.md model from its file without modifying it."""
    spec = importlib.util.spec_from_file_location("phycoweb_float_v0", FLOAT_V0_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def word_source(model: str, seed: Sequence[int]) -> Callable[[], int]:
    """Return a zero-argument callable producing successive unsigned 32-bit words."""
    if model == "float-v0":
        engine = load_float_v0().PhycoWebEngine(list(seed))

        def next_word() -> int:
            # numpy int32 overflow is the archived behavior (research R1); the archived
            # model returns signed int32, so take the unsigned bit pattern (research R2).
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                return engine.compute_block() & 0xFFFFFFFF

        return next_word
    if model == "lut-v1":
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        from phycoweb.model import MODEL_ID, PhycoWebEngine

        assert MODEL_ID == model
        return PhycoWebEngine(list(seed)).compute_block
    raise ValueError(f"unknown model {model!r}")


def generate(model: str, seed: Sequence[int], count: int) -> Iterator[int]:
    next_word = word_source(model, seed)
    for _ in range(count):
        yield next_word()


def header(model: str, seed: Sequence[int], count: int) -> str:
    return f"# model={model} seed={','.join(str(s) for s in seed)} count={count} format=u32-hex"


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, choices=MODELS)
    parser.add_argument("--seed", required=True, type=int, nargs=4, metavar="S")
    parser.add_argument("--count", required=True, type=int)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--out", type=Path)
    target.add_argument("--verify", type=Path)
    args = parser.parse_args(argv)
    if args.count < 1:
        parser.error("--count must be >= 1")
    return args


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    words = generate(args.model, args.seed, args.count)
    expected_header = header(args.model, args.seed, args.count)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("w", encoding="ascii", newline="\n") as stream:
            stream.write(expected_header + "\n")
            for word in words:
                stream.write(f"{word:08X}\n")
        print(f"wrote {args.count} words to {args.out}")
        return 0

    lines = args.verify.read_text(encoding="ascii").split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    if not lines or lines[0] != expected_header:
        print(f"MISMATCH: header {lines[0] if lines else '(empty)'!r} != {expected_header!r}")
        return 1
    if len(lines) - 1 != args.count:
        print(f"MISMATCH: file has {len(lines) - 1} words, expected {args.count}")
        return 1
    for index, (line, word) in enumerate(zip(lines[1:], words)):
        if line != f"{word:08X}":
            print(f"MISMATCH at word {index}: file {line}, model {word:08X}")
            return 1
    print(f"OK: {args.count} words match {args.verify}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
