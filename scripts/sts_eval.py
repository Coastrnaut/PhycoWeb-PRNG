"""Evaluate sequences with the own SP 800-22 harness (contracts/cli.md; FR-010, FR-013).

Dev and re-scoring only: held-out seed sets are refused here and run only through
acceptance.py. Exit 0 if every test family passes, 1 if not, 2 on a usage error or refusal.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import evalcore
from evalcore import ROOT, N_BITS
from protocol import seedsets

SOURCES = ("phyco-v2", "lut-v1", "os-csprng", "file")


def parse_args(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, choices=SOURCES)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--set", dest="seed_set")
    group.add_argument("--seed", type=int, nargs=4, action="append", metavar="S")
    group.add_argument("--bytes", type=Path)
    parser.add_argument("--sequences", type=int)
    parser.add_argument("--bits", type=int, default=N_BITS,
                        help="bits per sequence (default 2**21; other values only for re-scoring)")
    parser.add_argument("--skip-words", type=int, default=0,
                        help="model words discarded before each sequence (dev reruns, T033)")
    parser.add_argument("--workers", type=int, default=evalcore.default_workers())
    parser.add_argument("--save-bytes", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    started = time.time()
    command = "python " + " ".join([Path(sys.argv[0]).as_posix()] + sys.argv[1:])
    if args.bits < 1 or args.bits % 8:
        print("--bits must be a positive multiple of 8", file=sys.stderr)
        return 2
    extra = {}
    seed_set, seeds = None, None
    if args.source in evalcore.MODEL_SOURCES:
        if args.bits % 32:
            print("--bits must be a multiple of 32 for model sources", file=sys.stderr)
            return 2
        if args.source == "phyco-v2":
            try:
                import phycoweb.model_v2  # noqa: F401
            except ImportError:
                print("phyco-v2 does not exist yet (phycoweb/model_v2.py, T041)", file=sys.stderr)
                return 2
        if args.seed_set:
            try:
                seeds = seedsets.load(args.seed_set, allow={"dev"})
            except (PermissionError, ValueError) as exc:
                print(f"refused: {exc}", file=sys.stderr)
                return 2
            seed_set = args.seed_set
        elif args.seed:
            seeds = [tuple(s) for s in args.seed]
            held = {s for name in seedsets.FINGERPRINTS if name != "dev"
                    for s in seedsets.derive(name)}
            if any(s in held for s in seeds):
                print("refused: a held-out seed was given explicitly", file=sys.stderr)
                return 2
        else:
            print("model sources need --set dev or --seed", file=sys.stderr)
            return 2
        if args.sequences:
            seeds = seeds[:args.sequences]
        jobs = [(i, "model", (args.source, list(s)), args.bits, args.skip_words)
                for i, s in enumerate(seeds)]
        extra["skip_words"] = args.skip_words
    elif args.source == "os-csprng":
        count = args.sequences or 100
        raw = os.urandom(count * args.bits // 8)
        if args.save_bytes:
            args.save_bytes.parent.mkdir(parents=True, exist_ok=True)
            args.save_bytes.write_bytes(raw)
            extra["bytes_file"] = args.save_bytes.as_posix()
            extra["bytes_sha256"] = evalcore.sha256_file(args.save_bytes)
        step = args.bits // 8
        jobs = [(i, "bytes", raw[i * step:(i + 1) * step], args.bits, 0) for i in range(count)]
    else:
        if not args.bytes:
            print("--source file needs --bytes", file=sys.stderr)
            return 2
        raw = args.bytes.read_bytes()
        step = args.bits // 8
        count = len(raw) // step
        if args.sequences:
            count = min(count, args.sequences)
        if count < 1:
            print("file holds less than one sequence", file=sys.stderr)
            return 2
        jobs = [(i, "bytes", raw[i * step:(i + 1) * step], args.bits, 0) for i in range(count)]
        extra["bytes_file"] = args.bytes.as_posix()
        extra["bytes_sha256"] = evalcore.sha256_file(args.bytes)
    per_sequence = evalcore.run_jobs(jobs, args.workers)
    record = evalcore.build_record(
        args.source, per_sequence, seed_set=seed_set,
        seeds=[list(s) for s in seeds] if seeds else None, n_bits=args.bits, command=command,
        workers=args.workers, started=started, extra=extra)
    evalcore.write_record(args.out, record)
    fams = record["families"]
    print(f"{args.source}: {len(per_sequence)} sequences, "
          f"{sum(f['pass'] for f in fams.values())}/15 families pass, verdict {record['verdict']}")
    for name in record["families_failed"]:
        f = fams[name]
        print(f"  FAIL {name}: {f['failed_sub']}/{f['n_sub']} sub-tests failed (k_max {f['k_max']})")
    print("wrote", args.out.as_posix())
    return 0 if record["verdict"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
