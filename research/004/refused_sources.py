"""Feature 004: the sets of research R15's refused list that have a published derivation.

    python research/004/refused_sources.py --write    writes research/004/refused-constants.json
    python research/004/refused_sources.py --check    exit 1 while that file differs from this output
    python research/004/refused_sources.py --status   every design the documents name, and its state

Each function computes one set from the derivation that its entry cites. A polynomial or a set that
is only a table in a document stands here once that file is recorded `fetched`, its entry's source
naming the file and the table; until then it waits (tasks T027), and DESIGNS says which.
tests/test_refused_sources.py uses each set in its own primitive where a primitive or a published
relation can show a wrong word, and compares that primitive with an independent implementation or a
published vector.

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


# ------------------------------------------------------------- sets read from fetched files

# Each table stands in the file that its entry's source names, recorded `fetched` in downloads.json.
# A pattern read it from that file's text, so that no word of it was typed by hand.

ASCON_CONST = (
    0x000000000000003c, 0x000000000000002d, 0x000000000000001e, 0x000000000000000f,
    0x00000000000000f0, 0x00000000000000e1, 0x00000000000000d2, 0x00000000000000c3,
    0x00000000000000b4, 0x00000000000000a5, 0x0000000000000096, 0x0000000000000087,
    0x0000000000000078, 0x0000000000000069, 0x000000000000005a, 0x000000000000004b,
)

ASCON_SBOX = (
    0x04, 0x0b, 0x1f, 0x14, 0x1a, 0x15, 0x09, 0x02, 0x1b, 0x05, 0x08, 0x12, 0x1d, 0x03, 0x06,
    0x1c, 0x1e, 0x13, 0x07, 0x0e, 0x00, 0x0d, 0x11, 0x18, 0x10, 0x0c, 0x01, 0x19, 0x16, 0x0a,
    0x0f, 0x17,
)

ASCON_IV = (
    0x00001000808c0001, 0x0000080100cc0002, 0x0000080000cc0003, 0x0000080000cc0004,
)

ASCON_STATES = (
    0x9b1e5494e934d681, 0x4bc3a01e333751d2, 0xae65396c6b34b81a, 0x3c7fd4a4d56a4db3,
    0x1a5c464906c5976d, 0xda82ce768d9447eb, 0xcc7ce6c75f1ef969, 0xe7508fd780085631,
    0x0ee0ea53416b58cc, 0xe0547524db6f0bde, 0x675527c2a0e8de03, 0x43d12d7dc0377bbc,
    0xe9901dec426e81b5, 0x2ab14907720780b6, 0x8f3f1d02d432bc46,
)

MICKEY_RTAPS = (
    0x00, 0x01, 0x03, 0x04, 0x05, 0x06, 0x09, 0x0c, 0x0d, 0x10, 0x13, 0x14, 0x15, 0x16, 0x19,
    0x1c, 0x25, 0x26, 0x29, 0x2a, 0x2d, 0x2e, 0x32, 0x34, 0x36, 0x38, 0x3a, 0x3c, 0x3d, 0x3f,
    0x40, 0x41, 0x42, 0x43, 0x47, 0x48, 0x4f, 0x50, 0x51, 0x52, 0x57, 0x58, 0x59, 0x5a, 0x5b,
    0x5c, 0x5e, 0x5f, 0x60, 0x61,
)

MICKEY_COMP0 = (
    "000110001011110100101010101011010010000000101010100001010011"
    "11001010111111111010111111010100000011"
)

MICKEY_COMP1 = (
    "101100101111001010001101011101111000110101110000100010111000"
    "11111101011101111000100001110001001100"
)

MICKEY_FB0 = (
    "111101011111111001011111111110011000000111001001010100101111"
    "0101010000000001101000110111001110011000"
)

MICKEY_FB1 = (
    "111011100001110100110001001100101100011000001101100010001001"
    "0010110101001010001111011111000000100001"
)

RABBIT_A = (
    0x4d34d34d, 0xd34d34d3, 0x34d34d34, 0x4d34d34d, 0xd34d34d3, 0x34d34d34, 0x4d34d34d,
    0xd34d34d3,
)

SERPENT_SBOXES = (
    0x3, 0x8, 0xf, 0x1, 0xa, 0x6, 0x5, 0xb, 0xe, 0xd, 0x4, 0x2, 0x7, 0x0, 0x9, 0xc, 0xf, 0xc, 0x2,
    0x7, 0x9, 0x0, 0x5, 0xa, 0x1, 0xb, 0xe, 0x8, 0x6, 0xd, 0x3, 0x4, 0x8, 0x6, 0x7, 0x9, 0x3, 0xc,
    0xa, 0xf, 0xd, 0x1, 0xe, 0x4, 0x0, 0xb, 0x5, 0x2, 0x0, 0xf, 0xb, 0x8, 0xc, 0x9, 0x6, 0x3, 0xd,
    0x1, 0x2, 0x4, 0xa, 0x7, 0x5, 0xe, 0x1, 0xf, 0x8, 0x3, 0xc, 0x0, 0xb, 0x6, 0x2, 0x5, 0x4, 0xa,
    0x9, 0xe, 0x7, 0xd, 0xf, 0x5, 0x2, 0xb, 0x4, 0xa, 0x9, 0xc, 0x0, 0x3, 0xe, 0x8, 0xd, 0x6, 0x7,
    0x1, 0x7, 0x2, 0xc, 0x5, 0x8, 0x4, 0x6, 0xb, 0xe, 0x9, 0x1, 0xf, 0xd, 0x3, 0xa, 0x0, 0x1, 0xd,
    0xf, 0x0, 0xe, 0x8, 0x2, 0xb, 0x7, 0x4, 0xc, 0xa, 0x9, 0x3, 0x5, 0x6,
)

SOSEMANUK_M = (
    0x54655307,
)

ENOCORO_S4 = (
    0x1, 0x3, 0x9, 0xa, 0x5, 0xe, 0x7, 0x2, 0xd, 0x0, 0xc, 0xf, 0x4, 0x8, 0x6, 0xb,
)

ENOCORO_S8 = (
    0x63, 0x52, 0x1a, 0xdf, 0x8a, 0xf6, 0xae, 0x55, 0x89, 0xe7, 0xd0, 0x2d, 0xbd, 0x01, 0x24,
    0x78, 0x1b, 0xd9, 0xe3, 0x54, 0xc8, 0xa4, 0xec, 0x7e, 0xab, 0x00, 0x9c, 0x2e, 0x91, 0x67,
    0x37, 0x53, 0x4e, 0x6b, 0x6c, 0x11, 0xb2, 0xc0, 0x82, 0xfd, 0x39, 0x45, 0xfe, 0x9b, 0x34,
    0xd7, 0xa7, 0x08, 0xb8, 0x9a, 0x33, 0xc6, 0x4c, 0x1d, 0x69, 0xa1, 0x6e, 0x3e, 0xc5, 0x0a,
    0x57, 0xf4, 0xf1, 0x83, 0xf5, 0x47, 0x1f, 0x7a, 0xa5, 0x29, 0x3c, 0x42, 0xd6, 0x73, 0x8d,
    0xf0, 0x8e, 0x18, 0xaa, 0xc1, 0x20, 0xbf, 0xe6, 0x93, 0x51, 0x0e, 0xf7, 0x98, 0xdd, 0xba,
    0x6a, 0x05, 0x48, 0x23, 0x6d, 0xd4, 0x1e, 0x60, 0x75, 0x43, 0x97, 0x2a, 0x31, 0xdb, 0x84,
    0x19, 0xaf, 0xbc, 0xcc, 0xf3, 0xe8, 0x46, 0x88, 0xac, 0x8b, 0xe4, 0x7b, 0xd5, 0x58, 0x36,
    0x02, 0xb1, 0x07, 0x72, 0xe1, 0xdc, 0x5f, 0x2f, 0x5d, 0xe5, 0xd1, 0x0c, 0x26, 0x99, 0xb5,
    0x6f, 0xe0, 0x4a, 0x3b, 0xde, 0xa2, 0x68, 0x92, 0x17, 0xca, 0xee, 0xa9, 0xb6, 0x03, 0x5e,
    0xd3, 0x25, 0xfb, 0x9d, 0x61, 0x59, 0x06, 0x90, 0x74, 0x2c, 0x27, 0x95, 0xa0, 0xb9, 0x7c,
    0xed, 0x04, 0xd2, 0x50, 0xe2, 0x49, 0x77, 0xcb, 0x3a, 0x0f, 0x9e, 0x70, 0x16, 0x5c, 0xef,
    0x21, 0xb3, 0x9f, 0x0d, 0xa6, 0xc9, 0x22, 0x94, 0xfa, 0x4b, 0xd8, 0x65, 0x85, 0x3d, 0x96,
    0x28, 0x14, 0x5b, 0x66, 0xea, 0x7f, 0xce, 0xf9, 0x40, 0x13, 0xad, 0xc3, 0xb0, 0xf2, 0xc2,
    0x38, 0x80, 0xcf, 0x71, 0x0b, 0x87, 0x4d, 0x35, 0x56, 0xe9, 0x64, 0xbe, 0x1c, 0xbb, 0xb7,
    0x30, 0xc4, 0x2b, 0xff, 0x62, 0x41, 0xa8, 0x15, 0x8c, 0x12, 0xc7, 0x79, 0x8f, 0x5a, 0xfc,
    0xcd, 0x09, 0x4f, 0x7d, 0xf8, 0x86, 0xda, 0x10, 0x32, 0x76, 0xb4, 0xa3, 0x3f, 0x44, 0x81,
    0xeb,
)

ENOCORO_C = (
    0x66, 0xe9, 0x4b, 0xd4, 0xef, 0x8a, 0x2c, 0x3b, 0x88, 0x4c,
)

LUFFA_V = (
    0x6d251e69, 0x44b051e0, 0x4eaa6fb4, 0xdbf78465, 0x6e292011, 0x90152df4, 0xee058139,
    0xdef610bb, 0xc3b44b95, 0xd9d2f256, 0x70eee9a0, 0xde099fa3, 0x5d9b0557, 0x8fc944b3,
    0xcf1ccf0e, 0x746cd581, 0xf7efc89d, 0x5dba5781, 0x04016ce5, 0xad659c05, 0x0306194f,
    0x666d1836, 0x24aa230a, 0x8b264ae7, 0x858075d5, 0x36d79cce, 0xe571f7d7, 0x204b1f67,
    0x35870c6a, 0x57e9e923, 0x14bcb808, 0x7cde72ce, 0x6c68e9be, 0x5ec41e22, 0xc825b7c7,
    0xaffb4363, 0xf5df3999, 0x0fc688f1, 0xb07224cc, 0x03e86cea,
)

LUFFA_START = (
    0x181cca53, 0x380cde06, 0x5b6f0876, 0xf16f8594, 0x7e106ce9, 0x38979cb0, 0xbb62f364,
    0x92e93c29, 0x9a025047, 0xcff2a940,
)

LUFFA_STEP = (
    0x303994a6, 0xe0337818, 0xc0e65299, 0x441ba90d, 0x6cc33a12, 0x7f34d442, 0xdc56983e,
    0x9389217f, 0x1e00108f, 0xe5a8bce6, 0x7800423d, 0x5274baf4, 0x8f5b7882, 0x26889ba7,
    0x96e1db12, 0x9a226e9d, 0xb6de10ed, 0x01685f3d, 0x70f47aae, 0x05a17cf4, 0x0707a3d4,
    0xbd09caca, 0x1c1e8f51, 0xf4272b28, 0x707a3d45, 0x144ae5cc, 0xaeb28562, 0xfaa7ae2b,
    0xbaca1589, 0x2e48f1c1, 0x40a46f3e, 0xb923c704, 0xfc20d9d2, 0xe25e72c1, 0x34552e25,
    0xe623bb72, 0x7ad8818f, 0x5c58a4a4, 0x8438764a, 0x1e38e2e7, 0xbb6de032, 0x78e38b9d,
    0xedb780c8, 0x27586719, 0xd9847356, 0x36eda57f, 0xa2c78434, 0x703aace7, 0xb213afa5,
    0xe028c9bf, 0xc84ebe95, 0x44756f91, 0x4e608a22, 0x7e8fce32, 0x56d858fe, 0x956548be,
    0x343b138f, 0xfe191be2, 0xd0ec4e3d, 0x3cb226e5, 0x2ceb4882, 0x5944a28e, 0xb3ad2208,
    0xa1c4c355, 0xf0d2e9e3, 0x5090d577, 0xac11d7fa, 0x2d1925ab, 0x1bcb66f2, 0xb46496ac,
    0x6f2d9bc9, 0xd1925ab0, 0x78602649, 0x29131ab6, 0x8edae952, 0x0fc053c3, 0x3b6ba548,
    0x3f014f0c, 0xedae9520, 0xfc053c31,
)

LUFFA_SBOX = (
    0xd, 0xe, 0x0, 0x1, 0x5, 0xa, 0x7, 0x6, 0xb, 0x3, 0x9, 0xc, 0xf, 0x8, 0x2, 0x4,
)

LUFFA_G_EXPONENTS = (
    64, 63, 62, 58, 55, 54, 52, 50, 49, 46, 43, 40, 38, 37, 35, 34, 30, 28, 26, 24, 23, 22, 18,
    17, 12, 11, 10, 7, 3, 2, 0,
)

MT19937_WORDS = (
    0x9908b0df, 0x9d2c5680, 0xefc60000,
)

MT19937_MULTIPLIER = (
    0x00010dcd,
)

DUAL_EC_P256 = (
    0xffffffff00000001000000000000000000000000ffffffffffffffffffffffff,
    0xffffffff00000000ffffffffffffffffbce6faada7179e84f3b9cac2fc632551,
    0x5ac635d8aa3a93e7b3ebbd55769886bc651d06b0cc53b0f63bce3c3e27d2604b,
    0x6b17d1f2e12c4247f8bce6e563a440f277037d812deb33a0f4a13945d898c296,
    0x4fe342e2fe1a7f9b8ee7eb4a7c0f9e162bce33576b315ececbb6406837bf51f5,
    0xc97445f45cdef9f0d3e05e1e585fc297235b82b5be8ff3efca67c59852018192,
    0xb28ef557ba31dfcbdd21ac46e2a91e3c304f44cb87058ada2cb815151e610046,
)

DUAL_EC_P384 = (
   
    0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffeffffffff0000000000000000ffffffff,
    0xffffffffffffffffffffffffffffffffffffffffffffffffc7634d81f4372ddf581a0db248b0a77aecec196accc52973,
    0xb3312fa7e23ee7e4988e056be3f82d19181d9c6efe8141120314088f5013875ac656398d8a2ed19d2a85c8edd3ec2aef,
    0xaa87ca22be8b05378eb1c71ef320ad746e1d3b628ba79b9859f741e082542a385502f25dbf55296c3a545e3872760ab7,
    0x3617de4a96262c6f5d9e98bf9292dc29f8f41dbd289a147ce9da3113b5f0b8c00a60b1ce1d7e819d7a431d7c90ea0e5f,
    0x8e722de3125bddb05580164bfe20b8b432216a62926c57502ceede31c47816edd1e89769124179d0b695106428815065,
    0x023b1660dd701d0839fd45eec36f9ee7b32e13b315dc02610aa1b636e346df671f790f84c5e09b05674dbb7e45c803dd,
)

DUAL_EC_P521 = (
   
    0x1ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff,
    0x1fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffa51868783bf2f966b7fcc0148f709a5d03bb5c9b8899c47aebb6fb71e91386409,
    0x051953eb9618e1c9a1f929a21a0b68540eea2da725b99b315f3b8b489918ef109e156193951ec7e937b1652c0bd3bb1bf073573df883d2c34f1ef451fd46b503f00,
    0x0c6858e06b70404e9cd9e3ecb662395b4429c648139053fb521f828af606b4d3dbaa14b5e77efe75928fe1dc127a2ffa8de3348b3c1856a429bf97e7e31c2e5bd66,
    0x11839296a789a3bc0045c8a5fb42c7d1bd998f54449579b446817afbd17273e662c97ee72995ef42640c550b9013fad0761353c7086a272c24088be94769fd16650,
    0x1b9fa3e518d683c6b65763694ac8efbaec6fab44f2276171a42726507dd08add4c3b3f4c1ebc5b1222ddba077f722943b24c3edfa0f85fe24d0c8c01591f0be6f63,
    0x1f3bdba585295d9a1110d1df1f9430ef8442c5018976ff3437ef91b81dc0b8132c8d5c39c32d0e004a3092b7d327c0e7a4d26d2c7b69b58f9066652911e457779de,
)

PRESENT_SBOX = (
    0xc, 0x5, 0x6, 0xb, 0x9, 0x0, 0xa, 0xd, 0x3, 0xe, 0xf, 0x8, 0x4, 0x7, 0x1, 0x2,
)

PRINTCIPHER_SBOX = (
    0x0, 0x1, 0x3, 0x6, 0x7, 0x4, 0x5, 0x2,
)

PRINTCIPHER_VIRTUAL = (
    0x0, 0x1, 0x3, 0x6, 0x7, 0x4, 0x5, 0x2, 0x0, 0x1, 0x7, 0x4, 0x3, 0x6, 0x5, 0x2, 0x0, 0x3, 0x1,
    0x6, 0x7, 0x5, 0x4, 0x2, 0x0, 0x7, 0x3, 0x5, 0x1, 0x4, 0x6, 0x2,
)

PRINTCIPHER_RC96 = (
    0x01, 0x03, 0x07, 0x0f, 0x1f, 0x3f, 0x7e, 0x7d, 0x7b, 0x77, 0x6f, 0x5f, 0x3e, 0x7c, 0x79,
    0x73, 0x67, 0x4f, 0x1e, 0x3d, 0x7a, 0x75, 0x6b, 0x57, 0x2e, 0x5c, 0x38, 0x70, 0x61, 0x43,
    0x06, 0x0d, 0x1b, 0x37, 0x6e, 0x5d, 0x3a, 0x74, 0x69, 0x53, 0x26, 0x4c, 0x18, 0x31, 0x62,
    0x45, 0x0a, 0x15, 0x2b, 0x56, 0x2c, 0x58, 0x30, 0x60, 0x41, 0x02, 0x05, 0x0b, 0x17, 0x2f,
    0x5e, 0x3c, 0x78, 0x71, 0x63, 0x47, 0x0e, 0x1d, 0x3b, 0x76, 0x6d, 0x5b, 0x36, 0x6c, 0x59,
    0x32, 0x64, 0x49, 0x12, 0x25, 0x4a, 0x14, 0x29, 0x52, 0x24, 0x48, 0x10, 0x21, 0x42, 0x04,
    0x09, 0x13, 0x27, 0x4e, 0x1c, 0x39,
)

GRAIN_V1_F = (80, 67, 57, 42, 29, 18, 0)
GRAIN_128AEAD_F = (128, 121, 90, 58, 47, 32, 0)
SOSEMANUK_Q = (8, 7, 5, 3, 0)
SOSEMANUK_P_POWERS = (23, 245, 48, 239)
ENOCORO_PHI8 = (8, 4, 3, 2, 0)
ENOCORO_PHI4 = (4, 1, 0)
LUFFA_PHI = (8, 4, 3, 1, 0)
SPARKLE_BLOCKS = (1, 3, 6, 9, 14, 15, 26, 29)
PRESENT_ROUNDS = 31
LUFFA = "Luffa_v2_Specification_20091002.pdf"
ENOCORO = "enocoro_spec_20100222.zip, spec/09spec_e.pdf"
MICKEY = "mickey_p3.pdf, section 4.3"
SP_800_90A = "nistspecialpublication800-90a.pdf, appendix A.1"


def bits_of(text: str) -> List[int]:
    return [int(bit) for bit in text]


def sosemanuk_p() -> List[int]:
    """The coefficients of P(X), each a power of the root of Q(X) in the basis that section 2.2
    gives."""
    poly = sum(1 << exponent for exponent in SOSEMANUK_Q)
    out = []
    for exponent in SOSEMANUK_P_POWERS:
        value = 1
        for _ in range(exponent):
            value = times(value, 2, poly)
        out.append(value)
    return out


def e_blocks(count: int) -> List[int]:
    """The first `count` 32-bit blocks of the fractional part of e, in base 16."""
    guard = 32 * count + 64
    term, fraction = 1 << guard, 0
    for k in range(1, 400):
        term //= k
        fraction += term if k >= 2 else 0
    return [(fraction >> (guard - 32 * (i + 1))) & 0xFFFFFFFF for i in range(count)]


def sparkle_constants() -> List[int]:
    blocks = e_blocks(max(SPARKLE_BLOCKS))
    return [blocks[block - 1] for block in SPARKLE_BLOCKS]


def counter_from_one(count: int) -> List[int]:
    return list(range(1, count + 1))


def printcipher_counter(bits: int, count: int) -> List[int]:
    """Section 3's shift register: from zeros, t = 1 + x_(n-1) + x_(n-2) enters at x_0, each value
    taken after its round's update."""
    register, out = 0, []
    for _ in range(count):
        fresh = 1 ^ (register >> (bits - 1) & 1) ^ (register >> (bits - 2) & 1)
        register = (register << 1 | fresh) & ((1 << bits) - 1)
        out.append(register)
    return out


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


def read_polynomial(name: str, exponents: Tuple[int, ...], citation: str) -> Dict:
    degree = max(exponents)
    return {"name": name, "kind": "polynomial", "degree": degree,
            "c": hex(sum(1 << exponent for exponent in exponents if exponent != degree)),
            "source": citation}


def read_set(name: str, bits: int, words, citation: str) -> Dict:
    return dict(constant_set(name, bits, list(words), ""), source=citation)


def read_entries() -> List[Dict]:
    """The sets of research R15's designs that a fetched file gives. The list only grows, so these
    stand after the entries above, each source naming the file and the table."""
    sparkle = ("Beierle et al., ToSC 2020(S1), main.pdf, section 3: blocks 1, 3, 6, 9, 14, 15, 26 "
               "and 29 of the fractional part of e in base 16")
    return [
        read_set("Ascon const_i", 64, ASCON_CONST, "sp800-232.pdf, Table 5"),
        read_set("Ascon S-box", 5, ASCON_SBOX, "sp800-232.pdf, Table 6"),
        read_set("Ascon initial values", 64, ASCON_IV, "sp800-232.pdf, Table 14"),
        read_set("Ascon precomputed states", 64, ASCON_STATES,
                 "sp800-232.pdf, Table 12, column by column"),
        read_polynomial("Grain v1 LFSR polynomial", GRAIN_V1_F, "Grain_p3.pdf, section 2: f(x)"),
        read_polynomial("Grain-128AEAD LFSR polynomial", GRAIN_128AEAD_F,
                        "grain-128aead-spec-final.pdf, section 2.1: f(x)"),
        read_set("MICKEY 2.0 RTAPS", 8, MICKEY_RTAPS, "mickey_p3.pdf, section 4.2"),
        read_set("MICKEY 2.0 COMP0", 1, bits_of(MICKEY_COMP0), f"{MICKEY}: i = 1 to 98"),
        read_set("MICKEY 2.0 COMP1", 1, bits_of(MICKEY_COMP1), f"{MICKEY}: i = 1 to 98"),
        read_set("MICKEY 2.0 FB0", 1, bits_of(MICKEY_FB0), f"{MICKEY}: i = 0 to 99"),
        read_set("MICKEY 2.0 FB1", 1, bits_of(MICKEY_FB1), f"{MICKEY}: i = 0 to 99"),
        read_set("Rabbit counter constants", 32, RABBIT_A, "rfc4503.txt, section 2.5: A0 to A7"),
        read_polynomial("SOSEMANUK field polynomial Q", SOSEMANUK_Q,
                        "0810.1858.pdf, section 2.2: Q(X)"),
        read_set("SOSEMANUK polynomial P coefficients", 8, sosemanuk_p(),
                 "0810.1858.pdf, section 2.2: the powers of beta in P(X)"),
        read_set("SOSEMANUK multiplier M", 32, SOSEMANUK_M, "0810.1858.pdf, section 2.3"),
        read_set("SOSEMANUK Serpent S-boxes", 4, SERPENT_SBOXES,
                 "0810.1858.pdf, appendix A.1: S0 to S7"),
        read_polynomial("Enocoro field polynomial phi8", ENOCORO_PHI8, f"{ENOCORO}, section 2.2.3"),
        read_polynomial("Enocoro field polynomial phi4", ENOCORO_PHI4, f"{ENOCORO}, section 2.2.3"),
        read_set("Enocoro S-box s4", 4, ENOCORO_S4, f"{ENOCORO}, section 3.2.2"),
        read_set("Enocoro S-box s8", 8, ENOCORO_S8, f"{ENOCORO}, appendix A"),
        read_set("Enocoro initial constants", 8, ENOCORO_C, f"{ENOCORO}, section 4.2: C0 to C9"),
        read_polynomial("Luffa constant-generator polynomial g", LUFFA_G_EXPONENTS,
                        f"{LUFFA}, section 4.4: g(x)"),
        read_polynomial("Luffa field polynomial", LUFFA_PHI, f"{LUFFA}, section 3.2"),
        read_set("Luffa S-box", 4, LUFFA_SBOX, f"{LUFFA}, section 4.2"),
        read_set("Luffa starting variables", 32, LUFFA_V, f"{LUFFA}, appendix A: V0 to V4"),
        read_set("Luffa constant-generator initial values", 32, LUFFA_START,
                 f"{LUFFA}, appendix B-1: L and R for j = 0 to 4"),
        read_set("Luffa step constants", 32, LUFFA_STEP,
                 f"{LUFFA}, appendices B-2 to B-4: for each j, each r, k = 0 then 4"),
        read_set("Sparx-64/128 key-schedule counter", 16, counter_from_one(16),
                 "SPARX.pdf, section 4.2, Algorithms 1 and 2: r over 8 steps of 2 branches"),
        read_set("Sparx-128/128 key-schedule counter", 16, counter_from_one(32),
                 "SPARX.pdf, section 4.2, Algorithms 1 and 3: r over 8 steps of 4 branches"),
        read_set("Sparx-128/256 key-schedule counter", 16, counter_from_one(40),
                 "SPARX.pdf, section 4.2, Algorithms 1 and 4: r over 10 steps of 4 branches"),
        read_set("MT19937 parameters", 32, MT19937_WORDS,
                 "mt.pdf, the C program: MATRIX_A, TEMPERING_MASK_B, TEMPERING_MASK_C"),
        read_set("MT19937 seeding multiplier", 32, MT19937_MULTIPLIER,
                 "mt.pdf, the C program: sgenrand"),
        read_set("Dual_EC_DRBG P-256", 256, DUAL_EC_P256, f"{SP_800_90A}.1: p, n, b, P, Q"),
        read_set("Dual_EC_DRBG P-384", 384, DUAL_EC_P384, f"{SP_800_90A}.2: p, n, b, P, Q"),
        read_set("Dual_EC_DRBG P-521", 521, DUAL_EC_P521, f"{SP_800_90A}.3: p, n, b, P, Q"),
        constant_set("SPARKLE round constants", 32, sparkle_constants(), sparkle),
        read_set("PRESENT S-box", 4, PRESENT_SBOX, "47270450.pdf, section 3: S[x]"),
        read_set("PRESENT key-schedule counter", 5, counter_from_one(PRESENT_ROUNDS),
                 "47270450.pdf, section 3: round_counter"),
        read_set("PRINTcipher S-box", 3, PRINTCIPHER_SBOX, "62250016.pdf, section 3: S[x]"),
        read_set("PRINTcipher virtual S-boxes", 3, PRINTCIPHER_VIRTUAL,
                 "62250016.pdf, section 3.1: V0 to V3"),
        read_set("PRINTcipher-48 round counter", 6, printcipher_counter(6, 48),
                 "62250016.pdf, section 3: the shift register of 6 bits, RC1 to RC48"),
        read_set("PRINTcipher-96 round counter", 7, PRINTCIPHER_RC96, "62250016.pdf, Table 5"),
    ]


def render() -> bytes:
    text = json.dumps({"entries": entries() + read_entries()}, sort_keys=True, ensure_ascii=False,
                      indent=1)
    return (text + "\n").encode("utf-8")


# ------------------------------------------------------- what the documents name, and its state

class Design(NamedTuple):
    name: str
    documents: Tuple[str, ...]
    state: str
    detail: str


STATES = ("listed", "nothing", "paper", "file")
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
    Design("SPARKLE", ("research", "strategy"), "listed", "SPARKLE"),
    Design("Alzette", ("strategy",), "listed", "SPARKLE"),
    Design("PRESENT", ("research",), "listed", "PRESENT"),
    Design("Ascon-AEAD128", ("security",), "listed", "Ascon"),
    Design("Ascon-Hash256", ("security",), "listed", "Ascon"),
    Design("Ascon-XOF128", ("security",), "listed", "Ascon"),
    Design("Ascon-CXOF128", ("security",), "listed", "Ascon"),
    Design("Grain v1", ("security",), "listed", "Grain v1"),
    Design("Grain-128AEAD", ("spec", "strategy"), "listed", "Grain-128AEAD"),
    Design("MICKEY", ("security",), "listed", "MICKEY"),
    Design("Rabbit", ("security",), "listed", "Rabbit"),
    Design("SOSEMANUK", ("security",), "listed", "SOSEMANUK"),
    Design("Enocoro", ("security",), "listed", "Enocoro"),
    Design("PRINTcipher", ("strategy",), "listed", "PRINTcipher"),
    Design("Luffa", ("strategy",), "listed", "Luffa"),
    Design("Sparx", ("strategy",), "listed", "Sparx"),
    Design("LAX", ("strategy",), "nothing",
           "SPARX.pdf names its matrices by their codes and prints no word of them"),
    Design("MT19937", ("security",), "listed", "MT19937"),
    Design("Dual_EC_DRBG", ("security",), "listed", "Dual_EC_DRBG"),
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
