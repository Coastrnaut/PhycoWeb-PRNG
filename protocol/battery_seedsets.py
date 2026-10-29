"""Held-out seed sets for the feature-003 battery attempts (spec: Pre-registered Battery Protocol).

Seed i of set S is the first 8 bytes of SHA-256(b"phycoweb-003/<S>/<i>"), read as four
big-endian unsigned 16-bit integers, for i = 0..9. SHA-256 here is protocol bookkeeping only;
it is never part of a generator. Standard library only. The feature-002 module
protocol/seedsets.py is deliberately not changed (research R10).
"""
import hashlib
from typing import Iterable, List

from protocol.seedsets import Seed, canonical_text, fingerprint

PREFIX = "phycoweb-003"
SET_SIZE = 10

# SHA-256 of each set's canonical text, copied from spec.md.
FINGERPRINTS = {
    "heldout-1": "bb1e1a2df50d121996863680e0668550690cf1e448af0cf797661a9713d7de80",
    "heldout-2": "c7c7960803b25368b1ab3f745ec855a356f8189d7cfc8ce98348828bd1c6dbf8",
}
ORDER = ("heldout-1", "heldout-2")

__all__ = ["FINGERPRINTS", "ORDER", "derive", "load", "canonical_text", "fingerprint"]


def derive(name: str) -> List[Seed]:
    seeds = []
    for i in range(SET_SIZE):
        d = hashlib.sha256(f"{PREFIX}/{name}/{i}".encode("ascii")).digest()
        seeds.append(tuple(int.from_bytes(d[k:k + 2], "big") for k in range(0, 8, 2)))
    return seeds


def load(name: str, allow: Iterable[str]) -> List[Seed]:
    """Return set `name` after checking it is allowed here and matches its fingerprint."""
    if name not in FINGERPRINTS:
        raise ValueError(f"unknown battery seed set {name!r}")
    if name not in set(allow):
        raise PermissionError(f"battery seed set {name!r} is not allowed here "
                              f"(allowed: {sorted(allow)})")
    seeds = derive(name)
    actual = fingerprint(seeds)
    if actual != FINGERPRINTS[name]:
        raise ValueError(f"battery seed set {name!r} fingerprint {actual} != spec "
                         f"{FINGERPRINTS[name]}")
    return seeds
