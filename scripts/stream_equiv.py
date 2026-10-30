"""Fast-stream equivalence with the Python reference models (feature 003 US3; FR-007, SC-003).

Compares fast/build/phyco_stream with phycoweb/model_v2.py and phycoweb/model.py on every word
of the committed golden vectors and on the first --words words of every seed of the
feature-002 `dev` set (both generators). Held-out sets are refused (FR-010). Run in WSL.
Exit 0 if every word matches, 1 on any mismatch, 2 if refused.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from multiprocessing import get_context
from pathlib import Path

import numpy

ROOT = Path(__file__).resolve().parents[1]
for p in (str(ROOT), str(ROOT / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import evalcore  # noqa: E402
from gen_vectors import word_source  # noqa: E402
from protocol import seedsets  # noqa: E402
from protocol.disclaimer import DISCLAIMER  # noqa: E402

GOLDEN = ("phyco-v2_seed-56053-7029-30841-11050_10000.hex",
          "phyco-v2_seed-41278-32039-25293-40850_10000.hex",
          "lut-v1_seed-1024-2048-4096-8192_10000.hex")
MODELS = ("phyco-v2", "lut-v1")


def stream_words(binary: Path, model: str, seed, n: int) -> numpy.ndarray:
    out = subprocess.run([str(binary), model, *map(str, seed), "--words", str(n)],
                         capture_output=True, check=True).stdout
    return numpy.frombuffer(out, dtype="<u4")


def model_words(model: str, seed, n: int) -> numpy.ndarray:
    nxt = word_source(model, seed)
    return numpy.fromiter((nxt() for _ in range(n)), dtype=numpy.uint32, count=n)


def compare(a: numpy.ndarray, b: numpy.ndarray):
    if len(a) != len(b):
        return {"words": int(min(len(a), len(b))), "mismatches": None,
                "first_mismatch": None, "length_mismatch": [int(len(a)), int(len(b))]}
    diff = numpy.nonzero(a != b)[0]
    return {"words": int(len(a)), "mismatches": int(len(diff)),
            "first_mismatch": int(diff[0]) if len(diff) else None}


def _job(args):
    binary, model, seed, n = args
    return model, list(seed), compare(stream_words(Path(binary), model, seed, n),
                                      model_words(model, seed, n))


def golden(binary: Path):
    out = {}
    for name in GOLDEN:
        lines = (ROOT / "vectors" / name).read_text(encoding="ascii").split()
        header = (ROOT / "vectors" / name).read_text(encoding="ascii").splitlines()[0]
        fields = dict(f.split("=", 1) for f in header.lstrip("# ").split())
        model, seed = fields["model"], [int(v) for v in fields["seed"].split(",")]
        words = numpy.array([int(w, 16) for w in lines if not w.startswith("#") and "=" not in w],
                            dtype=numpy.uint32)
        out[name] = compare(stream_words(binary, model, seed, len(words)), words)
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, default=ROOT / "fast" / "build" / "phyco_stream")
    parser.add_argument("--set", dest="seed_set", default="dev")
    parser.add_argument("--words", type=int, default=1_000_000)
    parser.add_argument("--workers", type=int, default=evalcore.default_workers())
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        seeds = seedsets.load(args.seed_set, allow={"dev"})
    except (PermissionError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 2
    started = time.time()
    record = {"binary": str(args.binary), "binary_sha256": evalcore.sha256_file(args.binary),
              "stream_source_sha256": evalcore.sha256_file(ROOT / "fast" / "phyco_stream.c"),
              "lut_table_sha256": evalcore.sha256_file(ROOT / "fast" / "lut_table.h"),
              "compiler": subprocess.run(["gcc", "--version"], capture_output=True,
                                         text=True).stdout.splitlines()[0],
              "flags": "-O2 -std=c99 -Wall -Wextra -Werror",
              "byte_order": "little-endian u32", "reverse": "bit 0 <-> bit 31",
              "golden": golden(args.binary), "dev": {m: [] for m in MODELS}}
    jobs = [(str(args.binary), m, s, args.words) for m in MODELS for s in seeds]
    with get_context("spawn").Pool(args.workers) as pool:
        for model, seed, res in pool.imap(_job, jobs):
            record["dev"][model].append(dict(seed=seed, **res))
    bad = [r for r in record["golden"].values() if r["mismatches"] != 0]
    bad += [r for m in MODELS for r in record["dev"][m] if r["mismatches"] != 0]
    record.update({"seed_set": args.seed_set, "words_per_seed": args.words,
                   "total_words_compared": sum(r["words"] for r in record["golden"].values()) +
                   sum(r["words"] for m in MODELS for r in record["dev"][m]),
                   "all_match": not bad, "versions": evalcore.versions(),
                   "git_head": evalcore._git("rev-parse", "--short", "HEAD"),
                   "command": "python " + " ".join([Path(sys.argv[0]).as_posix()] + sys.argv[1:]),
                   "elapsed_s": round(time.time() - started, 1), "disclaimer": DISCLAIMER})
    evalcore.write_record(args.out, record)
    print(f"compared {record['total_words_compared']} words; all match: {record['all_match']}")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
