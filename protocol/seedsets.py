"""Pre-registered seed sets for feature 002 (spec: Pre-registered Acceptance Protocol).

Seed i of set S is the first 8 bytes of SHA-256(b"phycoweb-002/<S>/<i>"), read as four
big-endian unsigned 16-bit integers, for i = 0..99. SHA-256 here is protocol bookkeeping only;
it is never part of the generator (FR-007). Standard library only.
"""
import hashlib
from typing import Iterable, List, Tuple

Seed = Tuple[int, int, int, int]

SET_SIZE = 100

# SHA-256 of each set's canonical text, copied from spec.md.
FINGERPRINTS = {
    "dev": "7e7e33c75e9e58048a26c1926e6addd4dc3514502574ea6687ded889aa47950e",
    "heldout-1": "84a30b2e037550d0c6b1cfba1444eb0447fbc15b5b7c631ad8fc8a577dfca23d",
    "heldout-2": "13120fcb1c1a49f6e6109f059982909470da33784bd0490f1e0f10252e214ad4",
    "heldout-3": "af3b9b8e62829ef732a5c2bb2963c7655c9b461635da0c40d960b4c7eaace88f",
}

# The feature-001 seeds count as development seeds (spec Assumptions).
FEATURE001_SEEDS: List[Seed] = [(1024, 2048, 4096, 8192), (4660, 43981, 21845, 43690)]


def derive(name: str) -> List[Seed]:
    seeds = []
    for i in range(SET_SIZE):
        d = hashlib.sha256(f"phycoweb-002/{name}/{i}".encode("ascii")).digest()
        seeds.append(tuple(int.from_bytes(d[k:k + 2], "big") for k in range(0, 8, 2)))
    return seeds


def canonical_text(seeds: Iterable[Seed]) -> str:
    return "".join(" ".join(str(v) for v in seed) + "\n" for seed in seeds)


def fingerprint(seeds: Iterable[Seed]) -> str:
    return hashlib.sha256(canonical_text(seeds).encode("ascii")).hexdigest()


def load(name: str, allow: Iterable[str]) -> List[Seed]:
    """Return set `name` after checking it is allowed here and matches its fingerprint."""
    if name not in FINGERPRINTS:
        raise ValueError(f"unknown seed set {name!r}")
    if name not in set(allow):
        raise PermissionError(f"seed set {name!r} is not allowed here (allowed: {sorted(allow)})")
    seeds = derive(name)
    actual = fingerprint(seeds)
    if actual != FINGERPRINTS[name]:
        raise ValueError(f"seed set {name!r} fingerprint {actual} != spec {FINGERPRINTS[name]}")
    return seeds
