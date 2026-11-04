"""Development inputs for feature 004 (spec FR-040; research R3; data-model section 2).

Every key, nonce, personalization string, reseed input and test state of this feature is derived
from a public ASCII string by SHA-256, and a script takes them only through `load`, which checks the
namespace and the kind's fingerprint and hands back the values i = 0..count - 1. SHA-256 here is
protocol bookkeeping only: it never appears in the permutation, the mode or key loading (FR-007).
Standard library only.
"""
import hashlib

PREFIX = "phycoweb-004/"
NAMESPACES = ("dev", "control")
# Spec FR-018's sizes with research R14's widths: 4 at 2x2 only, then 8, 16 and 32.
PAIRS = ((2, 4), (2, 8), (2, 16), (2, 32), (3, 8), (3, 16), (3, 32), (4, 8), (4, 16), (4, 32),
         (8, 8), (8, 16), (8, 32), (16, 8), (16, 16), (16, 32))
KINDS = ("key", "nonce", "pers", "reseed", "state", "synthetic")
# `control` serves only uniform controls, which are states (research R4).
CONTROL_KINDS = ("state",)
FINGERPRINT_COUNT = 100
EMPTY_PERS = b""
# The closed class beside the derivation (data-model section 2); none of them is a kind of `load`.
CONSTRUCTED = ("fixed patterns", "edge states", "derived from development inputs",
               "feature 002's `dev` seeds", "synthetic counts")

FINGERPRINTS = {
    "dev": {
        "key": "39e78a2920c2db6367405167d34c937c135bceac4b264babf84b2761b366befb",
        "nonce": "838ef3417809aaf47b1e0e2dedf0d4cc606eb515959fe7ad21a12c6fee26056d",
        "pers": "abd3d846bccc1ee56ffdb2b5ba27f37b758e65465291f4e0db721a1f29a74b92",
        "reseed": "d91fd90463acaa576efd90e5d1bac28308e4533bccf785eb7ef65ab954c9f3cf",
        "state": {
            (2, 4): "ccd1cf308c8c23eb82c9b454ec3204d56897e72bfb167b87ed81e5a52ea89c49",
            (2, 8): "3732bb91a653f93df0d513da17bb14bf3147ee1c6002138bce02a3c36d4ec17d",
            (2, 16): "f679239fbd7b8bdfe1c4bae898fbadc1c9259517d3404d21eaef7c46dc0c0763",
            (2, 32): "3e651bf224afd940774d73db7371af7bab04685fd76e4024366739fb248e2226",
            (3, 8): "6cea5cd9c1c19196cd2194497c32d0faf5d253d7d0e350c54928eedd70c52236",
            (3, 16): "2bfbf4ef3a88ae86f44b042afc0ea898f3165ba65c259825059fc326037b5dde",
            (3, 32): "4f25c18961f0b1f8b3e991cd94b9e8575541e891efcf4a0976a9cfa043d8d660",
            (4, 8): "e35222319405d66dc29a88fdec28ac6176d4f3c6415216f649613ba506bd6a69",
            (4, 16): "2b5734d2c1b96d25db18f4bf2cad9c581028160d149fe577f52934c5fdda87a5",
            (4, 32): "3d97babb0356c360d2b9e49f5b497eb1bf2fce19fd9eb005b27006968524ad7e",
            (8, 8): "5ef5f4c91c8be6af58ff9bac4151b0a231da406da206c7a6000355ddfe585357",
            (8, 16): "a5dd17421818c3a4fd2ebcd78f1e0fd648503385252f8cd2d698d6ee750869b2",
            (8, 32): "ec7dc4898d808eff5bd1bc95c885e7cdf306ba3da83ef05fe3489a73d7a47455",
            (16, 8): "2f911bd2f352adab705d75d0aa4518ce43f4534e233cf28bcf34d7dc4dd5a806",
            (16, 16): "b7d4e4a3ef40daff309581d140375e2da963793005ed3eb18c7f7719242e9ee8",
            (16, 32): "946512fee4bc82b4d2e60504fedf78cc03f993dca473e37f8087cbca6ccf5f2d",
        },
        "synthetic": {
            4: "8e5bbe0208682b388a73a9692964b8c141be9862b983ccf44989c9e33fd9771e",
            8: "d62d2cfd1023623b2fd2d6580d7fe0136f72a130b4621516dee9129e436c629c",
            16: "f43140c90f769a04a8f7edfc4a29ee252a7896d752fcc87571df78fa5b3d197c",
        },
    },
    "control": {
        "state": {
            (2, 4): "0418200377d33e08f21eb72d07e28bfdc921a62b4798c170da54dd4b90656155",
            (2, 8): "e7430564b725eadf235bcac5fbc9ae24d9d8cbb856499643e9099e86d585aaac",
            (2, 16): "5052ea41d8e3d766969b1cb94e4f39515a59050c6d5f7a0f6d3595e974647f39",
            (2, 32): "a51b70e6077ebb8c09d74132bdcccada82c5d56fc16db01dc64da286c3092547",
            (3, 8): "1a1447ffe47d4e40379864b60b6e3001d980fc73e1a926280c3b52288e2f84d2",
            (3, 16): "27aafc61f5032b2f6863fea1699867e97ed443dbea4aa8a0821caf7e7dcae7eb",
            (3, 32): "c794384d9f5128cbe6014970230be5010e2cac8d13d142957d3d800901e014fb",
            (4, 8): "53a86f1fcd96b5a0530cf37d1d2c6e1b338bd7ef23ae01a5367f343b5468c829",
            (4, 16): "84b03851cf9e1c81b52499def80e5c932c4f3e82f7d01c364b5000f89a19339d",
            (4, 32): "4b5cc781838c95fbcaebfd1e156e1b41389915e795c8812a93678cd30264f8cc",
            (8, 8): "04c26b437cdaaec348f67848b4fae40e5624a57b50b5f51a43253548bb9d242e",
            (8, 16): "b7381651d9a3b886a557647b2913cbf18e0957a0e18734ef8c796f2c66a2b62a",
            (8, 32): "35e8225a10348ac5a121983e4624db157891fc50e0e47b82197f8bc92ae33a0a",
            (16, 8): "271c1ca7b6f221be93e5cdc3d780f63577bf81ff158a69d1fa459b87df9ec4b0",
            (16, 16): "84d56913ca9f4e7f5cdbd976bd8c0a25bc6ebb742cfa05bec4204fa6c5fe3799",
            (16, 32): "d9c182495b649a046601c84bfd5734a6592e89bd3595e940f21f90d0cb003a26",
        },
    },
}


class InputRefused(PermissionError):
    """The namespace is not allowed here, or serves no such kind: scripts exit 2."""


class UnknownInput(ValueError):
    """No such namespace, kind, size or count, or a fingerprint that differs: scripts exit 2."""


def digest(ns: str, rest: str) -> bytes:
    return hashlib.sha256(f"{PREFIX}{ns}/{rest}".encode("ascii")).digest()


def key(ns: str, i: int) -> bytes:
    return digest(ns, f"key/{i}")


def nonce(ns: str, i: int) -> bytes:
    return digest(ns, f"nonce/{i}")[:16]


def pers(ns: str, i: int, m: int) -> bytes:
    return digest(ns, f"pers/{i}")[:min(m, 32)]


def reseed(ns: str, i: int) -> bytes:
    return digest(ns, f"reseed/{i}")


def state_bytes(ns: str, n: int, w: int, i: int) -> bytes:
    """The first b = 2w n^2 bits of the digests j = 0, 1, ... concatenated."""
    size = 2 * w * n * n // 8
    out = b""
    j = 0
    while len(out) < size:
        out += digest(ns, f"state/n{n}w{w}/{i}/{j}")
        j += 1
    return out[:size]


def state(ns: str, n: int, w: int, i: int) -> list:
    """Those bits read most significant first into 2 n^2 w-bit lanes, in the design's lane order."""
    data = state_bytes(ns, n, w, i)
    if w == 4:
        return [int(digit, 16) for digit in data.hex()]
    return [int.from_bytes(data[k:k + w // 8], "big") for k in range(0, len(data), w // 8)]


def synthetic_seed(ns: str, n: int, j: int) -> int:
    if ns != "dev":
        raise UnknownInput(f"a synthetic seed is dev only, not {ns!r}")
    return int.from_bytes(digest(ns, f"synthetic/n{n}/{j}")[:16], "big")


def fingerprint_text(ns: str, kind: str, n: int = 0, w: int = 0) -> str:
    """Data-model section 2: the first 100 values, one per line, each line ending in LF."""
    indices = range(FINGERPRINT_COUNT)
    if kind == "state":
        lines = [state_bytes(ns, n, w, i).hex().upper() for i in indices]
    elif kind == "synthetic":
        lines = [str(synthetic_seed(ns, n, j)) for j in indices]
    elif kind == "pers":
        lines = [pers(ns, i, 32).hex() for i in indices]
    else:
        derive = {"key": key, "nonce": nonce, "reseed": reseed}[kind]
        lines = [derive(ns, i).hex() for i in indices]
    return "".join(line + "\n" for line in lines)


def fingerprint(ns: str, kind: str, n: int = 0, w: int = 0) -> str:
    return hashlib.sha256(fingerprint_text(ns, kind, n, w).encode("ascii")).hexdigest()


class Values:
    """The values i = 0..count - 1 of one use, each derived as it is read, so that the 2^21 control
    states of the largest size take no memory; no other index can be read."""

    def __init__(self, read, count: int) -> None:
        self._read = read
        self._count = count

    def __len__(self) -> int:
        return self._count

    def __getitem__(self, index):
        if isinstance(index, slice):
            return [self._read(i) for i in range(*index.indices(self._count))]
        if isinstance(index, bool) or not isinstance(index, int):
            raise TypeError(f"an index is a whole number, not {index!r}")
        if not -self._count <= index < self._count:
            raise IndexError(f"index {index} is outside the declared range 0..{self._count - 1}")
        return self._read(index % self._count)

    def __iter__(self):
        return (self._read(i) for i in range(self._count))


def guard_arguments(kind: str, n, w, m) -> None:
    """A kind takes the arguments that fix its size, and no others."""
    given = {"n": n, "w": w, "m": m}
    wanted = {"state": ("n", "w"), "synthetic": ("n",), "pers": ("m",)}.get(kind, ())
    missing = [name for name in wanted if given[name] is None]
    if missing:
        raise UnknownInput(f"{kind} needs {' and '.join(wanted)}")
    extra = [name for name in given if name not in wanted and given[name] is not None]
    if extra:
        raise UnknownInput(f"{kind} takes no {', '.join(extra)}")


def wanted_fingerprint(ns: str, kind: str, n, w) -> str:
    entry = FINGERPRINTS[ns].get(kind)
    if kind == "state":
        if (n, w) not in entry:
            raise UnknownInput(f"no fingerprint for state at (n, w) = ({n}, {w})")
        return entry[(n, w)]
    if kind == "synthetic":
        if n not in entry:
            raise UnknownInput(f"no fingerprint for synthetic at n={n}")
        return entry[n]
    return entry


def reader(ns: str, kind: str, n, w, m):
    if kind == "state":
        return lambda i: state(ns, n, w, i)
    if kind == "synthetic":
        return lambda j: synthetic_seed(ns, n, j)
    if kind == "pers":
        return lambda i: pers(ns, i, m)
    derive = {"key": key, "nonce": nonce, "reseed": reseed}[kind]
    return lambda i: derive(ns, i)


def load(ns: str, kind: str, allow, count: int, n=None, w=None, m=None) -> Values:
    """Return values 0..count - 1 of a kind, after checking that the namespace is allowed here and
    that the kind matches its fingerprint; `state` takes n and w, `synthetic` n and `pers` m."""
    if ns not in NAMESPACES:
        raise UnknownInput(f"unknown namespace {ns!r}")
    if ns not in set(allow):
        raise InputRefused(f"namespace {ns!r} is not allowed here (allowed: {sorted(allow)})")
    if kind not in KINDS:
        raise UnknownInput(f"unknown kind {kind!r}")
    if ns == "control" and kind not in CONTROL_KINDS:
        raise InputRefused(f"control serves only uniform controls, not {kind!r}")
    if isinstance(count, bool) or not isinstance(count, int) or count < 1:
        raise UnknownInput(f"count {count!r} is not a positive whole number")
    guard_arguments(kind, n, w, m)
    wanted = wanted_fingerprint(ns, kind, n, w)
    actual = fingerprint(ns, kind, n, w) if kind in ("state", "synthetic") else fingerprint(ns, kind)
    if actual != wanted:
        raise UnknownInput(f"{ns} {kind}: fingerprint {actual} != {wanted}")
    return Values(reader(ns, kind, n, w, m), count)
