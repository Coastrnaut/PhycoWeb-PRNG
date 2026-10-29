"""Design exploration on development seeds only (T031; FR-015, FR-005, SC-006; research R9).

Loads a variant from research/002/variants/<id>.py (same API as contracts/model-v2-api.md),
measures its disruption rate, runs the sp80022 battery on N dev sequences, and appends one line
to research/002/runs.jsonl (data-model section 7). This script is the only writer of
runs.jsonl. A variant whose file hash differs from the hash already logged for its id is
refused: a changed design needs a new id (Principle V).

Seeds: `--set dev` (the pre-registered dev set) or `--set feature001` (the two feature-001
seeds). Anything else exits 2 before any generator runs. Held-out sets cannot be loaded here.

Exploration results are not acceptance results.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import time
from multiprocessing import get_context
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
VARIANTS = HERE / "variants"
RUNS = HERE / "runs.jsonl"
for p in (str(ROOT), str(ROOT / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

N_BITS = 2 ** 21
N_WORDS = N_BITS // 32
SEED_SETS = ("dev", "feature001")
# All-equal seeds checked for degenerate output on every run (T033; spec Edge Cases).
EDGE_SEEDS = [(0, 0, 0, 0), (65535, 65535, 65535, 65535)]


def load_variant(variant_id: str):
    path = VARIANTS / f"{variant_id}.py"
    spec = importlib.util.spec_from_file_location(f"variant_{variant_id}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _words(module, seed, skip: int, count: int):
    engine = module.PhycoWebEngineV2(seed)
    step = engine.compute_block
    for _ in range(skip):
        step()
    return [step() for _ in range(count)], engine


def _battery_job(job):
    import numpy
    import sp80022
    index, variant_id, seed, window = job
    words, _ = _words(load_variant(variant_id), seed, window * N_WORDS, N_WORDS)
    bits = numpy.unpackbits(numpy.array(words, dtype=">u4").view(numpy.uint8))
    return index, [(r.name, r.eligible, [float(p) for p in r.p_values]) for r in
                   sp80022.battery(bits)]


def _disruption_job(job):
    index, variant_id, seed, steps = job
    engine = load_variant(variant_id).PhycoWebEngineV2(seed)
    start_d, start_s = engine.disruptions, engine.step_count
    step = engine.compute_block
    for _ in range(steps):
        step()
    return index, (engine.disruptions - start_d) / (engine.step_count - start_s)


def edge_check(module, n: int = 2 ** 16, max_lag: int = 2 ** 15):
    """For each all-equal seed: are the first n words all equal, or periodic with lag <= max_lag?"""
    out = []
    for seed in EDGE_SEEDS:
        words, _ = _words(module, seed, 0, n)
        constant = len(set(words)) == 1
        period = None
        for lag in range(1, max_lag + 1):
            # Only lags where the first word repeats can be periods; check those in full.
            if words[lag] == words[0] and words[lag:] == words[:-lag]:
                period = lag
                break
        out.append({"seed": list(seed), "constant": constant, "short_period": period,
                    "ok": not constant and period is None})
    return out


def logged_hash(variant_id: str):
    if not RUNS.exists():
        return None
    for line in RUNS.read_text(encoding="utf-8").splitlines():
        rec = json.loads(line)
        if rec["variant"] == variant_id:
            return rec["source_sha256"]
    return None


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant", required=True)
    parser.add_argument("--set", dest="seed_set", default="dev")
    parser.add_argument("--sequences", type=int, default=100)
    parser.add_argument("--window", type=int, default=0,
                        help="use bits [window*2**21, (window+1)*2**21) after warm-up")
    parser.add_argument("--disruption-steps", type=int, default=10 ** 6)
    parser.add_argument("--workers", type=int, default=32)
    parser.add_argument("--note", default="")
    args = parser.parse_args(argv)

    if args.seed_set not in SEED_SETS:
        print(f"explore.py: seed set {args.seed_set!r} is not allowed (dev seeds only: "
              f"{', '.join(SEED_SETS)}); FR-015", file=sys.stderr)
        return 2
    from protocol import seedsets
    if args.seed_set == "dev":
        seeds = seedsets.load("dev", allow={"dev"})
    else:
        seeds = list(seedsets.FEATURE001_SEEDS)
    seeds = seeds[:args.sequences]

    path = VARIANTS / f"{args.variant}.py"
    if not path.exists():
        print(f"explore.py: no variant file {path}", file=sys.stderr)
        return 2
    source_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    previous = logged_hash(args.variant)
    if previous is not None and previous != source_sha256:
        print(f"explore.py: {path.name} changed since it was logged ({previous[:12]} -> "
              f"{source_sha256[:12]}); create a new variant id instead", file=sys.stderr)
        return 2

    import sp80022
    started = time.time()
    module = load_variant(args.variant)
    ctx = get_context("spawn")
    with ctx.Pool(args.workers) as pool:
        rates = []
        if args.disruption_steps:
            jobs = [(i, args.variant, s, args.disruption_steps) for i, s in enumerate(seeds)]
            rates = [r for _, r in sorted(pool.map(_disruption_job, jobs, chunksize=1))]
        jobs = [(i, args.variant, s, args.window) for i, s in enumerate(seeds)]
        out = sorted(pool.map(_battery_job, jobs, chunksize=1))
    per_sequence = [[sp80022.TestResult(n, e, p, {}) for n, e, p in res] for _, res in out]
    summary = sp80022.assess(per_sequence)
    failed = {n: f["failed_sub"] for n, f in summary["families"].items() if not f["pass"]}
    # Screening statistic: share of p-values below 0.01 per test (about 0.01 for good output).
    low_p = {}
    for t, name in enumerate(r.name for r in per_sequence[0]):
        ps = [p for seq in per_sequence if seq[t].eligible for p in seq[t].p_values]
        low_p[name] = round(sum(p < 0.01 for p in ps) / len(ps), 4) if ps else None
    edges = edge_check(module)

    record = {
        "variant": args.variant,
        "source_sha256": source_sha256,
        "seeds": args.seed_set,
        "n_sequences": len(seeds),
        "window": args.window,
        "warmup": getattr(module, "WARMUP", None),
        "families_failed": sorted(failed),
        "failed_subtests": failed,
        "low_p_rate": low_p,
        "disruption_rate": [min(rates), max(rates)] if rates else None,
        "disruption_steps": args.disruption_steps,
        "edge_seeds_ok": all(e["ok"] for e in edges),
        "edge_seeds": edges,
        "harness_version": sp80022.__version__,
        "harness_sha256": sp80022.source_sha256(),
        "command": "python research/002/explore.py " + " ".join(argv or sys.argv[1:]),
        "note": args.note,
        "date": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "elapsed_s": round(time.time() - started, 1),
    }
    with RUNS.open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(record) + "\n")
    rate = record["disruption_rate"]
    print(f"{args.variant} window {args.window} n={len(seeds)}: failed families "
          f"{failed or 'none'}; disruption {rate}; edge seeds ok {record['edge_seeds_ok']}; "
          f"{record['elapsed_s']} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
