"""Feature 004: the exhaustive bijectivity check (research R13; data-model section 5).

All 2^32 inputs of the 2×2 variant at w = 4 pass through the batch interpreter into a bitmap of 2^32 bits,
512 MiB; the variant is bijective if the bitmap holds 2^32 ones. A state is packed with lane i in bits 4i
to 4i + 3. Each input is one word of the sweep, so that the sweep needs nothing but the map.

Run on its known results by scripts/validate_tool.py (`bijectivity-maps` and its second; R13), each a heavy
run, projected first against the feature-wide row. Analysis code: the model never imports it. This tool
makes no security claim.
"""
import hashlib
import sys
import time
from pathlib import Path
from typing import Callable, Dict, Optional, Tuple

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
for place in (str(ROOT / "research/004"), str(ROOT)):
    if place not in sys.path:
        sys.path.insert(0, place)

import ir  # noqa: E402

CODE = ("research/004/ir.py",)
HEAVY = ("bijectivity-maps", "bijectivity-maps-second")
LANES, W = 8, 4
BATCH = 2 ** 22
PROBE_BATCHES = 8
KIND = {"widths": [4], "operations": "any map on the 32-bit state of 2×2 at w = 4",
        "model": "an exhaustive bitmap of outputs",
        "uses": [{"use": "the `bijectivity` record of each candidate at 2×2, w = 4",
                  "covered_by": ["bijectivity-maps"]}]}


def unpack(words: np.ndarray, lanes: int = LANES, w: int = W) -> np.ndarray:
    """A batch of packed states as one row per lane, uint64."""
    mask = np.uint64((1 << w) - 1)
    return np.stack([(words >> np.uint64(lane * w)) & mask for lane in range(lanes)])


def pack(states: np.ndarray, w: int = W) -> np.ndarray:
    out = np.zeros(states.shape[1], dtype=np.uint64)
    for lane in range(states.shape[0]):
        out |= states[lane] << np.uint64(lane * w)
    return out


def sweep(step: Callable[[np.ndarray], np.ndarray], lanes: int = LANES, w: int = W,
          batch: int = BATCH) -> Dict:
    """Every input through `step`, the outputs marked in a bitmap: its ones, and its SHA-256."""
    bits = lanes * w
    bitmap = np.zeros(max(1, (1 << bits) // 8), dtype=np.uint8)
    for start in range(0, 1 << bits, batch):
        words = np.arange(start, min(start + batch, 1 << bits), dtype=np.uint64)
        outputs = pack(step(unpack(words, lanes, w)), w)
        np.bitwise_or.at(bitmap, (outputs >> np.uint64(3)).astype(np.int64),
                         (np.uint8(1) << (outputs & np.uint64(7)).astype(np.uint8)))
    return {"inputs": 1 << bits, "ones": int(np.bitwise_count(bitmap).sum(dtype=np.int64)),
            "bitmap_sha256": hashlib.sha256(bitmap.tobytes()).hexdigest()}


def passes(found: Dict) -> bool:
    """The `bijectivity` verdict: as many distinct outputs as inputs."""
    return found["ones"] == found["inputs"]


def steps_of(known) -> Dict[str, Callable[[np.ndarray], np.ndarray]]:
    loaded = ir.load(known.permutation())
    return {"permutation": lambda states: ir.permute_batch(loaded, states, rounds=known.ROUNDS),
            "collisions": known.collisions}


def re_find(known, keep) -> Dict:
    steps = steps_of(known)
    permutation = sweep(steps["permutation"])
    collisions = sweep(steps["collisions"])
    held = permutation["ones"] == known.PERMUTATION_ONES and collisions["ones"] == known.COLLISION_ONES
    return {"found": {"permutation": permutation, "collisions": collisions}, "re_found": held,
            "validated_kind": KIND}


RUNS = {"bijectivity-maps": re_find, "bijectivity-maps-second": re_find}


def validation(known_id: str, known, keep: Optional[Callable[[str, bytes], None]]) -> Dict:
    return RUNS[known_id](known, keep)


def time_batches(step: Callable[[np.ndarray], np.ndarray], batches: int = PROBE_BATCHES) -> float:
    """Seconds per batch of a sample of the sweep, with the marking of its outputs."""
    bitmap = np.zeros(2 ** 29, dtype=np.uint8)
    started = time.monotonic()
    for number in range(batches):
        words = np.arange(number * BATCH, (number + 1) * BATCH, dtype=np.uint64)
        outputs = pack(step(unpack(words)))
        np.bitwise_or.at(bitmap, (outputs >> np.uint64(3)).astype(np.int64),
                         (np.uint8(1) << (outputs & np.uint64(7)).astype(np.uint8)))
    return (time.monotonic() - started) / batches


def projection(known_id: str) -> Tuple[float, Dict]:
    """A timing probe of both maps, at most 60 s, and the hours of both sweeps."""
    import importlib.util
    path = ROOT / "research/004/validation" / f"{known_id}.py"
    spec = importlib.util.spec_from_file_location("bijectivity_" + known_id.replace("-", "_"), path)
    known = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = known
    spec.loader.exec_module(known)
    per_batch = {name: time_batches(step) for name, step in steps_of(known).items()}
    sweeps = 2 ** 32 / BATCH
    hours = sum(per_batch.values()) * sweeps / 3600.0
    return hours, {"seconds_per_batch": per_batch, "batch": BATCH}
