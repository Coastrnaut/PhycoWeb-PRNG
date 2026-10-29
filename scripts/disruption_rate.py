"""Measure the phyco-v2 disruption rate on the dev seeds (T044; FR-005, SC-002).

The rate for a seed is (disruption firings) / (steps) over STEPS steps after the warm-up. Dev
seeds only; held-out sets cannot be loaded here.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from multiprocessing import get_context
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

LOW, HIGH = 0.01, 0.50


def _rate(job):
    index, seed, steps = job
    from phycoweb.model_v2 import PhycoWebEngineV2
    engine = PhycoWebEngineV2(seed)
    d0, s0 = engine.disruptions, engine.step_count
    step = engine.compute_block
    for _ in range(steps):
        step()
    return index, (engine.disruptions - d0) / (engine.step_count - s0)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=10 ** 6)
    parser.add_argument("--workers", type=int, default=32)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    from phycoweb.model_v2 import MODEL_ID, WARMUP
    from protocol import seedsets
    seeds = seedsets.load("dev", allow={"dev"}) + list(seedsets.FEATURE001_SEEDS)
    started = time.time()
    with get_context("spawn").Pool(args.workers) as pool:
        rates = [r for _, r in sorted(pool.map(_rate, [(i, s, args.steps)
                                                        for i, s in enumerate(seeds)]))]
    dev = rates[:100]
    record = {
        "model": MODEL_ID,
        "warmup": WARMUP,
        "steps_per_seed": args.steps,
        "bounds": [LOW, HIGH],
        "dev": {"min": min(dev), "max": max(dev),
                "per_seed": [{"seed": list(s), "rate": r} for s, r in zip(seeds[:100], dev)]},
        "feature001": [{"seed": list(s), "rate": r} for s, r in zip(seeds[100:], rates[100:])],
        "all_within_bounds": all(LOW <= r <= HIGH for r in rates),
        "command": "python " + " ".join([Path(sys.argv[0]).as_posix()] + sys.argv[1:]),
        "date": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "elapsed_s": round(time.time() - started, 1),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")
    print(f"dev min {record['dev']['min']:.6f} max {record['dev']['max']:.6f}; "
          f"feature-001 {[round(r, 6) for r in rates[100:]]}; "
          f"all within [{LOW}, {HIGH}]: {record['all_within_bounds']}")
    return 0 if record["all_within_bounds"] else 1


if __name__ == "__main__":
    sys.exit(main())
