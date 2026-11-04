"""Feature 004: the sets of research R15's refused list that have a published derivation.

    python research/004/refused_sources.py --write    writes research/004/refused-constants.json
    python research/004/refused_sources.py --check    exit 1 while that file differs from this output
    python research/004/refused_sources.py --status   every design the documents name, and its state

Each function computes one set from the derivation that its entry cites. A polynomial or a set that
is only a table in a document is not stated here: it waits for a file (tasks T027), and DESIGNS says
which. tests/test_refused_sources.py uses each computed set in its own primitive and compares that
primitive with an independent implementation or a published vector.

This module makes no security claim.
"""
import argparse
import itertools
import json
import math
import sys
from pathlib import Path
from typing import Dict, Iterator, List, NamedTuple, Tuple

ROOT = Path(__file__).resolve().parents[2]
LIST = ROOT / "research/004/refused-constants.json"
SCRIPT = "research/004/refused_sources.py"

CRC64_ECMA_182 = 0x42F0E1EBA9EA3693  # as the standard states it; the test compares it with liblzma's
AES_C = 0x1B
KECCAK_C = 0x71


# ---------------------------------------------------------------------- polynomials over GF(2)

def reduced(value: int, poly: int) -> int:
    width = poly.bit_length()
    while value.bit_length() >= width:
        value ^= poly << (value.bit_length() - width)
    return value


def times(a: int, b: int, poly: int) -> int:
    out = 0
    while b:
        if b & 1:
            out ^= a
        a <<= 1
        b >>= 1
    return reduced(out, poly)


def common_factor(a: int, b: int) -> int:
    while b:
        a, b = b, reduced(a, b)
    return a


def prime_factors(number: int) -> List[int]:
    return [p for p in range(2, number + 1)
            if number % p == 0 and all(p % d for d in range(2, p))]


def is_irreducible(poly: int) -> bool:
    """Rabin's test: x^(2^n) = x modulo poly, and no x^(2^(n/q)) - x shares a factor with it."""
    degree = poly.bit_length() - 1
    if degree < 1 or not poly & 1 or bin(poly).count("1") % 2 == 0:
        return False
    powers = [2]
    for _ in range(degree):
        powers.append(times(powers[-1], powers[-1], poly))
    if powers[degree] != reduced(2, poly):
        return False
    return all(common_factor(poly, powers[degree // q] ^ 2) == 1 for q in prime_factors(degree))


def ascending(count: int, limit: int) -> Iterator[int]:
    """Every integer with `count` bits set, each between bit 1 and bit limit - 1, in ascending order."""
    if count == 0:
        yield 0
        return
    for top in range(count, limit):
        for rest in ascending(count - 1, top):
            yield (1 << top) | rest


def first_of_least_weight(degree: int) -> int:
    """c of the lexicographically first irreducible polynomial of that degree with the fewest
    nonzero terms, the rule of SP 800-38B section 5.3 for R_b."""
    for count in range(1, degree):
        for rest in ascending(count, degree):
            if is_irreducible((1 << degree) | rest | 1):
                return rest | 1
    raise ValueError(degree)


def gcm_c() -> int:
    """SP 800-38D section 6.3: R = 11100001 || 0^120, its bits the coefficients from x^0 up."""
    return sum(1 << i for i, bit in enumerate("11100001" + "0" * 120) if bit == "1")


# ------------------------------------------------------------------------------- constant sets

def first_primes(count: int) -> List[int]:
    return list(itertools.islice((n for n in itertools.count(2)
                                  if all(n % d for d in range(2, math.isqrt(n) + 1))), count))


def integer_root(value: int, degree: int) -> int:
    low, high = 0, 1 << (value.bit_length() // degree + 1)
    while low + 1 < high:
        middle = (low + high) // 2
        if middle ** degree <= value:
            low = middle
        else:
            high = middle
    return low


def root_fraction(prime: int, degree: int, bits: int) -> int:
    """The first `bits` bits of the fractional part of the degree-th root of a prime."""
    return integer_root(prime << (degree * bits), degree) & ((1 << bits) - 1)


def sha256_k() -> List[int]:
    return [root_fraction(prime, 3, 32) for prime in first_primes(64)]


def sha256_h0() -> List[int]:
    return [root_fraction(prime, 2, 32) for prime in first_primes(8)]


def keccak_bit(t: int) -> int:
    """rc(t) of algorithm 5 of FIPS 202: the LFSR of x^8 + x^6 + x^5 + x^4 + 1."""
    register = 1
    for _ in range(t % 255):
        register <<= 1
        if register & 0x100:
            register ^= 0x100 | KECCAK_C
    return register & 1


def keccak_round_constants() -> List[int]:
    return [sum(keccak_bit(j + 7 * index) << ((1 << j) - 1) for j in range(7))
            for index in range(24)]


def aes_times(a: int, b: int) -> int:
    return times(a, b, 0x100 | AES_C)


def aes_sbox() -> List[int]:
    """The inverse in GF(2^8), then the affine map with the constant 0x63."""
    box = []
    for value in range(256):
        inverse = 1
        for _ in range(254):
            inverse = aes_times(inverse, value)
        turned = [((inverse << k) | (inverse >> (8 - k))) & 0xFF for k in range(5)]
        box.append(turned[0] ^ turned[1] ^ turned[2] ^ turned[3] ^ turned[4] ^ 0x63)
    return box


def aes_rcon() -> List[int]:
    out = [1]
    for _ in range(9):
        out.append(aes_times(out[-1], 2))
    return out


def aes_rcon_words() -> List[int]:
    return [byte << 24 for byte in aes_rcon()]


def ascon_round_constants() -> List[int]:
    """p^12's constants: the high nibble falls from 0xf as the low nibble rises from 0."""
    return [((0xF - r) << 4) | r for r in range(12)]


def chacha_words() -> List[int]:
    text = b"expand 32-byte k"
    return [int.from_bytes(text[i:i + 4], "little") for i in range(0, 16, 4)]


def salsa_bytes(key_bytes: int) -> List[int]:
    return list(b"expand %d-byte k" % key_bytes)


def rc5_words(width: int) -> Tuple[int, int]:
    """P = Odd((e - 2) 2^w) and Q = Odd((phi - 1) 2^w), Odd(x) being the odd integer nearest x."""
    guard = width + 64
    unit = 1 << guard
    term, fraction = unit, 0
    for k in range(1, 300):
        term //= k
        fraction += term if k >= 2 else 0
    golden = (math.isqrt(5 << (2 * guard)) - unit) // 2
    return (fraction >> (guard - width)) | 1, (golden >> (guard - width)) | 1


def speck_counters(rounds: int) -> List[int]:
    """The key schedule XORs the round index i into each of its rounds 0 to T - 2."""
    return list(range(rounds - 1))


def pcg64_multiplier() -> int:
    """The multiplier of numpy's PCG64, solved from three successive states of its 128-bit
    congruential step: s[t + 1] = m s[t] + inc, whose differences hold no increment."""
    import numpy
    generator = numpy.random.PCG64(0)
    states = []
    for _ in range(3):
        states.append(generator.state["state"]["state"])
        generator.advance(1)
    modulus = 1 << 128
    return (states[2] - states[1]) * pow((states[1] - states[0]) % modulus, -1, modulus) % modulus


# ------------------------------------------------------------------------------------ the list

def polynomial(name: str, degree: int, c: int, citation: str) -> Dict:
    return {"name": name, "kind": "polynomial", "degree": degree, "c": hex(c),
            "source": f"{SCRIPT}, {citation}"}


def constant_set(name: str, bits: int, words: List[int], citation: str) -> Dict:
    digits = (bits + 3) // 4
    return {"name": name, "kind": "constant-set", "word_bits": bits,
            "words": [f"0x{word:0{digits}x}" for word in words], "source": f"{SCRIPT}, {citation}"}


def entries() -> List[Dict]:
    r64, r128 = first_of_least_weight(64), first_of_least_weight(128)
    speck = "Beaulieu et al., The SIMON and SPECK Families of Lightweight Block Ciphers, " \
            "IACR ePrint 2013/404: the key schedule's round index"
    rc5 = "Rivest, The RC5 Encryption Algorithm, FSE 1994: P = Odd((e - 2) 2^w), " \
          "Q = Odd((phi - 1) 2^w)"
    return [
        polynomial("CMAC R64", 64, r64, "SP 800-38B section 5.3: the lexicographically first "
                   "irreducible polynomial of degree 64 with the fewest nonzero terms"),
        polynomial("CMAC R128", 128, r128, "SP 800-38B section 5.3: the same rule at degree 128"),
        polynomial("GCM field polynomial", 128, gcm_c(),
                   "SP 800-38D section 6.3: R = 11100001 || 0^120"),
        polynomial("CRC-64 of ISO 3309", 64, r64, "ISO 3309's x^64 + x^4 + x^3 + x + 1, the "
                   "polynomial of CMAC R64 (research R15); checked by its CRC check value"),
        polynomial("CRC-64 of ECMA-182", 64, CRC64_ECMA_182, "ECMA-182, the polynomial as the "
                   "standard states it; checked against liblzma's CRC-64 and its check value"),
        polynomial("AES field polynomial", 8, AES_C, "FIPS 197 section 4.2: x^8 + x^4 + x^3 + x + 1"),
        polynomial("Keccak-f round-constant LFSR polynomial", 8, KECCAK_C,
                   "FIPS 202 algorithm 5: x^8 + x^6 + x^5 + x^4 + 1"),
        constant_set("SHA-256 round constants K", 32, sha256_k(), "FIPS 180-4 section 4.2.2: the "
                     "first 32 bits of the fractional parts of the cube roots of the first 64 "
                     "primes"),
        constant_set("SHA-256 initial hash value H0", 32, sha256_h0(), "FIPS 180-4 section 5.3.3: "
                     "the first 32 bits of the fractional parts of the square roots of the first "
                     "8 primes"),
        constant_set("Keccak-f[1600] round constants", 64, keccak_round_constants(),
                     "FIPS 202 algorithms 5 and 6: rc(t) and RC[2^j - 1] = rc(j + 7 i_r)"),
        constant_set("AES S-box", 8, aes_sbox(), "FIPS 197 section 5.1.1: the inverse in GF(2^8), "
                     "then the affine map with the constant 0x63"),
        constant_set("AES Rcon, bytes", 8, aes_rcon(),
                     "FIPS 197 section 5.2: x^(i - 1) in GF(2^8)"),
        constant_set("AES Rcon, 32-bit words", 32, aes_rcon_words(),
                     "FIPS 197 section 5.2: [x^(i - 1), 00, 00, 00]"),
        constant_set("Ascon round constants", 8, ascon_round_constants(), "Dobraunig et al., "
                     "Ascon v1.2, and NIST SP 800-232, the constant-addition layer of p^12"),
        constant_set("ChaCha20 constants", 32, chacha_words(), "RFC 8439 section 2.3: "
                     "expand 32-byte k, as four little-endian words"),
        constant_set("Salsa20 sigma", 8, salsa_bytes(32),
                     "Bernstein, Salsa20 specification, the expansion function: expand 32-byte k"),
        constant_set("Salsa20 tau", 8, salsa_bytes(16),
                     "Bernstein, Salsa20 specification, the expansion function: expand 16-byte k"),
        constant_set("RC5 P and Q, 16-bit", 16, list(rc5_words(16)), rc5),
        constant_set("RC5 P and Q, 32-bit", 32, list(rc5_words(32)), rc5),
        constant_set("RC5 P and Q, 64-bit", 64, list(rc5_words(64)), rc5),
        constant_set("SPECK32/64 key-schedule counter", 16, speck_counters(22), speck),
        constant_set("SPECK64/96 key-schedule counter", 32, speck_counters(26), speck),
        constant_set("SPECK64/128 key-schedule counter", 32, speck_counters(27), speck),
        constant_set("PCG64 multiplier", 128, [pcg64_multiplier()], "O'Neill, HMC-CS-2014-0905, "
                     "as numpy's PCG64 holds it, solved from three successive states"),
    ]


def render() -> bytes:
    text = json.dumps({"entries": entries()}, sort_keys=True, ensure_ascii=False, indent=1)
    return (text + "\n").encode("utf-8")


# ------------------------------------------------------- what the documents name, and its state

class Design(NamedTuple):
    name: str
    documents: Tuple[str, ...]
    state: str
    detail: str


STATES = ("listed", "nothing", "paper", "file")
SP_800_232 = "NIST SP 800-232: its initial values and S-box have no derivation to compute"
ESTREAM = "the eSTREAM portfolio's specification"
SPARX = "Dinu et al., ASIACRYPT 2016: IACR ePrint 2016/984"
# listed: its sets stand on the list, under names that begin with `detail`.
# nothing: no polynomial or word constant of its own, for the reason in `detail`.
# paper: a paper of research R19's table, fetched by T059, enters as a stricter entry.
# file: a file of its own, a row "Download <n>" first, enters as a stricter entry (T027; R15).
DESIGNS = (
    Design("AES", ("strategy",), "listed", "AES"),
    Design("Rijndael", ("strategy",), "listed", "AES"),
    Design("Keccak-f", ("strategy",), "listed", "Keccak-f"),
    Design("SHAKE", ("security",), "listed", "Keccak-f"),
    Design("SHA-256", ("spec", "plan", "research", "security"), "listed", "SHA-256"),
    Design("Ascon", ("spec", "security", "strategy"), "listed", "Ascon round constants"),
    Design("ChaCha20", ("strategy",), "listed", "ChaCha20"),
    Design("Salsa20/12", ("security",), "listed", "Salsa20"),
    Design("RC5", ("strategy",), "listed", "RC5"),
    Design("SPECK32", ("spec", "research"), "listed", "SPECK32/64"),
    Design("SPECK64", ("research",), "listed", "SPECK64/"),
    Design("PCG64", ("research",), "listed", "PCG64"),
    Design("CMAC", ("research",), "listed", "CMAC"),
    Design("GCM", ("research",), "listed", "GCM"),
    Design("CRC-64", ("research",), "listed", "CRC-64"),
    Design("Trivium", ("spec", "security", "strategy"), "nothing",
           "its state starts from key, IV, zeros and three ones"),
    Design("HC-128", ("security",), "nothing", "its tables come from the key and IV"),
    Design("Chaskey", ("research",), "nothing",
           "no round constant; its subkeys use the polynomial of CMAC R128"),
    Design("Hash_DRBG", ("security",), "nothing", "a mechanism over a hash function"),
    Design("HMAC_DRBG", ("security",), "nothing", "a mechanism over HMAC"),
    Design("CTR_DRBG", ("security",), "nothing", "a mechanism over a block cipher"),
    Design("SPARKLE", ("research", "strategy"), "paper", "main.pdf"),
    Design("Alzette", ("strategy",), "paper", "main.pdf"),
    Design("PRESENT", ("research",), "paper", "47270450.pdf"),
    Design("Ascon-AEAD128", ("security",), "file", SP_800_232),
    Design("Ascon-Hash256", ("security",), "file", SP_800_232),
    Design("Ascon-XOF128", ("security",), "file", SP_800_232),
    Design("Ascon-CXOF128", ("security",), "file", SP_800_232),
    Design("Grain v1", ("security",), "file", ESTREAM),
    Design("Grain-128AEAD", ("spec", "strategy"), "file", "its NIST lightweight-cryptography "
           "specification"),
    Design("MICKEY", ("security",), "file", ESTREAM),
    Design("Rabbit", ("security",), "file", "RFC 4503"),
    Design("SOSEMANUK", ("security",), "file", ESTREAM),
    Design("Enocoro", ("security",), "file", "its specification, or ISO/IEC 29192-3"),
    Design("PRINTcipher", ("strategy",), "file", "Knudsen et al., CHES 2010"),
    Design("Luffa", ("strategy",), "file", "its specification"),
    Design("Sparx", ("strategy",), "file", SPARX),
    Design("LAX", ("strategy",), "file", SPARX),
    Design("MT19937", ("security",), "file", "Matsumoto and Nishimura, ACM TOMACS 1998"),
    Design("Dual_EC_DRBG", ("security",), "file", "NIST SP 800-90A of 2012, withdrawn since"),
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--status", action="store_true")
    args = parser.parse_args()
    if args.status:
        for state in STATES:
            for design in DESIGNS:
                if design.state == state:
                    print(f"{state:8} {design.name:16} {design.detail}")
        return 0
    data = render()
    if args.write:
        LIST.write_bytes(data)
        print(f"{LIST.relative_to(ROOT).as_posix()}: {len(json.loads(data)['entries'])} entries")
        return 0
    if LIST.read_bytes() != data:
        print("research/004/refused-constants.json differs from what this script computes")
        return 1
    print("research/004/refused-constants.json is what this script computes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
