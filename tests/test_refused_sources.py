"""Feature 004: the refused list and the sets computed for it (research R15; T027).

Each computed set is used here in the primitive it belongs to, and that primitive is compared with an
independent implementation or a published vector, so a wrong word in a set fails. The list's format
is the writer's own reading (protocol/changelog.py); this file makes no security claim.
"""
import hashlib
import importlib.util
import json
import lzma
import unittest
from pathlib import Path

from protocol import changelog

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "research/004/refused_sources.py"
LIST = ROOT / "research/004/refused-constants.json"
DOCUMENTS = {"spec": "specs/004-crypto-architecture-v3/spec.md",
             "plan": "specs/004-crypto-architecture-v3/plan.md",
             "research": "specs/004-crypto-architecture-v3/research.md",
             "security": "security.md",
             "strategy": "research/security/crypto-redesign-strategy.md"}
M32, M64 = (1 << 32) - 1, (1 << 64) - 1


def load():
    spec = importlib.util.spec_from_file_location("refused_sources", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


refused = load()


def rotr(value: int, amount: int, bits: int) -> int:
    amount %= bits
    mask = (1 << bits) - 1
    return ((value >> amount) | (value << (bits - amount))) & mask


def rotl(value: int, amount: int, bits: int) -> int:
    return rotr(value, bits - amount % bits, bits)


def sha256_with(k, h0, message: bytes) -> bytes:
    h = list(h0)
    tail = (len(message) * 8).to_bytes(8, "big")
    padded = message + b"\x80" + b"\0" * ((55 - len(message)) % 64) + tail
    for start in range(0, len(padded), 64):
        w = [int.from_bytes(padded[start + 4 * i:start + 4 * i + 4], "big") for i in range(16)]
        for t in range(16, 64):
            s0 = rotr(w[t - 15], 7, 32) ^ rotr(w[t - 15], 18, 32) ^ (w[t - 15] >> 3)
            s1 = rotr(w[t - 2], 17, 32) ^ rotr(w[t - 2], 19, 32) ^ (w[t - 2] >> 10)
            w.append((w[t - 16] + s0 + w[t - 7] + s1) & M32)
        a, b, c, d, e, f, g, last = h
        for t in range(64):
            big1 = rotr(e, 6, 32) ^ rotr(e, 11, 32) ^ rotr(e, 25, 32)
            t1 = (last + big1 + ((e & f) ^ (~e & g & M32)) + k[t] + w[t]) & M32
            big0 = rotr(a, 2, 32) ^ rotr(a, 13, 32) ^ rotr(a, 22, 32)
            t2 = (big0 + ((a & b) ^ (a & c) ^ (b & c))) & M32
            last, g, f, e, d, c, b, a = g, f, e, (d + t1) & M32, c, b, a, (t1 + t2) & M32
        h = [(x + y) & M32 for x, y in zip(h, (a, b, c, d, e, f, g, last))]
    return b"".join(x.to_bytes(4, "big") for x in h)


def keccak_f(lanes, constants) -> None:
    for constant in constants:
        columns = [lanes[x][0] ^ lanes[x][1] ^ lanes[x][2] ^ lanes[x][3] ^ lanes[x][4]
                   for x in range(5)]
        for x in range(5):
            mix = columns[(x + 4) % 5] ^ rotl(columns[(x + 1) % 5], 1, 64)
            for y in range(5):
                lanes[x][y] ^= mix
        x, y = 1, 0
        current = lanes[x][y]
        for t in range(24):
            x, y = y, (2 * x + 3 * y) % 5
            current, lanes[x][y] = lanes[x][y], rotl(current, (t + 1) * (t + 2) // 2, 64)
        for y in range(5):
            row = [lanes[x][y] for x in range(5)]
            for x in range(5):
                lanes[x][y] = row[x] ^ (~row[(x + 1) % 5] & row[(x + 2) % 5] & M64)
        lanes[0][0] ^= constant


def sponge(constants, message: bytes, rate: int, suffix: int, length: int) -> bytes:
    lanes = [[0] * 5 for _ in range(5)]
    padded = bytearray(message + bytes([suffix]))
    padded += b"\0" * (rate - len(padded) % rate)
    padded[-1] ^= 0x80

    def absorb(block: bytes) -> None:
        for i in range(rate // 8):
            lanes[i % 5][i // 5] ^= int.from_bytes(block[8 * i:8 * i + 8], "little")
        keccak_f(lanes, constants)

    for start in range(0, len(padded), rate):
        absorb(bytes(padded[start:start + rate]))
    out = b""
    while len(out) < length:
        out += b"".join(lanes[i % 5][i // 5].to_bytes(8, "little") for i in range(rate // 8))
        keccak_f(lanes, constants)
    return out[:length]


def aes128(key: bytes, block: bytes, sbox, rcon) -> bytes:
    words = [list(key[i:i + 4]) for i in range(0, 16, 4)]
    for i in range(4, 44):
        temp = list(words[i - 1])
        if i % 4 == 0:
            temp = [sbox[b] for b in temp[1:] + temp[:1]]
            temp[0] ^= rcon[i // 4 - 1]
        words.append([a ^ b for a, b in zip(words[i - 4], temp)])
    state = list(block)

    def add_round_key(number: int) -> None:
        for i in range(16):
            state[i] ^= words[4 * number + i // 4][i % 4]

    def times2(value: int) -> int:
        return ((value << 1) ^ (0x1B if value & 0x80 else 0)) & 0xFF

    add_round_key(0)
    for number in range(1, 11):
        state[:] = [sbox[b] for b in state]
        state[:] = [state[(i + 4 * (i % 4)) % 16] for i in range(16)]
        if number != 10:
            for column in range(0, 16, 4):
                a = state[column:column + 4]
                every = a[0] ^ a[1] ^ a[2] ^ a[3]
                state[column:column + 4] = [a[i] ^ every ^ times2(a[i] ^ a[(i + 1) % 4])
                                            for i in range(4)]
        add_round_key(number)
    return bytes(state)


def chacha20_block(constants, key: bytes, counter: int, nonce: bytes) -> bytes:
    initial = list(constants)
    initial += [int.from_bytes(key[i:i + 4], "little") for i in range(0, 32, 4)]
    initial += [counter] + [int.from_bytes(nonce[i:i + 4], "little") for i in range(0, 12, 4)]
    x = list(initial)

    def quarter(a: int, b: int, c: int, d: int) -> None:
        x[a] = (x[a] + x[b]) & M32
        x[d] = rotl(x[d] ^ x[a], 16, 32)
        x[c] = (x[c] + x[d]) & M32
        x[b] = rotl(x[b] ^ x[c], 12, 32)
        x[a] = (x[a] + x[b]) & M32
        x[d] = rotl(x[d] ^ x[a], 8, 32)
        x[c] = (x[c] + x[d]) & M32
        x[b] = rotl(x[b] ^ x[c], 7, 32)

    for _ in range(10):
        for indices in ((0, 4, 8, 12), (1, 5, 9, 13), (2, 6, 10, 14), (3, 7, 11, 15),
                        (0, 5, 10, 15), (1, 6, 11, 12), (2, 7, 8, 13), (3, 4, 9, 14)):
            quarter(*indices)
    return b"".join(((a + b) & M32).to_bytes(4, "little") for a, b in zip(x, initial))


def rc5_32_12(p: int, q: int, key: bytes, a: int, b: int):
    words = [int.from_bytes(key[i:i + 4], "little") for i in range(0, len(key), 4)]
    s = [p]
    while len(s) < 26:
        s.append((s[-1] + q) & M32)
    x = y = i = j = 0
    for _ in range(3 * max(len(s), len(words))):
        x = s[i] = rotl((s[i] + x + y) & M32, 3, 32)
        y = words[j] = rotl((words[j] + x + y) & M32, (x + y) & 31, 32)
        i, j = (i + 1) % len(s), (j + 1) % len(words)
    a, b = (a + s[0]) & M32, (b + s[1]) & M32
    for r in range(1, 13):
        a = (rotl(a ^ b, b & 31, 32) + s[2 * r]) & M32
        b = (rotl(b ^ a, a & 31, 32) + s[2 * r + 1]) & M32
    return a, b


def speck(counters, bits: int, alpha: int, beta: int, key, x: int, y: int):
    """`key` as the papers print it, l[m-2] ... l[0], k[0]; each round's XOR takes `counters`."""
    mask = (1 << bits) - 1
    k = key[-1]
    l = list(reversed(key[:-1]))
    for i, counter in enumerate(list(counters) + [None]):
        x = ((rotr(x, alpha, bits) + y) & mask) ^ k
        y = rotl(y, beta, bits) ^ x
        if counter is None:
            break
        fresh = ((k + rotr(l[i], alpha, bits)) & mask) ^ counter
        l.append(fresh)
        k = rotl(k, beta, bits) ^ fresh
    return x, y


def ascon_permutation(state, constants) -> None:
    for constant in constants:
        state[2] ^= constant
        state[0] ^= state[4]
        state[4] ^= state[3]
        state[2] ^= state[1]
        original = list(state)
        for i in range(5):
            state[i] ^= ~original[(i + 1) % 5] & original[(i + 2) % 5] & M64
        state[1] ^= state[0]
        state[0] ^= state[4]
        state[3] ^= state[2]
        state[2] ^= M64
        for i, (a, b) in enumerate(((19, 28), (61, 39), (1, 6), (10, 17), (7, 41))):
            state[i] ^= rotr(state[i], a, 64) ^ rotr(state[i], b, 64)


def crc64(data: bytes, poly: int, start: int, final: int) -> int:
    crc = start
    for byte in data:
        crc ^= byte << 56
        for _ in range(8):
            crc = ((crc << 1) ^ poly if crc >> 63 else crc << 1) & M64
    return crc ^ final


def crc64_reflected(data: bytes, poly: int, start: int, final: int) -> int:
    reflected = int(f"{poly:064b}"[::-1], 2)
    crc = start
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ reflected if crc & 1 else crc >> 1
    return crc ^ final


class Polynomials(unittest.TestCase):

    def test_irreducibility_on_known_cases(self):
        self.assertTrue(refused.is_irreducible(0x11B))  # AES's
        self.assertTrue(refused.is_irreducible((1 << 64) | 0x1B))
        self.assertFalse(refused.is_irreducible(0x11A))  # no constant term
        self.assertFalse(refused.is_irreducible(0b101))  # (x + 1) squared
        self.assertFalse(refused.is_irreducible((1 << 64) | 0b1111))

    def test_cmac_polynomials_follow_their_rule(self):
        self.assertEqual(refused.first_of_least_weight(64), 0x1B)
        self.assertEqual(refused.first_of_least_weight(128), 0x87)

    def test_no_trinomial_at_either_degree(self):
        for degree in (64, 128):
            for k in range(1, degree):
                self.assertFalse(refused.is_irreducible((1 << degree) | (1 << k) | 1), (degree, k))

    def test_gcm_polynomial_reads_the_published_string(self):
        self.assertEqual(refused.gcm_c(), 0x87)

    def test_crc64_ecma_is_the_polynomial_liblzma_uses(self):
        c = refused.CRC64_ECMA_182
        self.assertEqual(crc64(b"123456789", c, 0, 0), 0x6C40DF5F0B497347)
        data = b"PhycoWeb refused list"
        value = crc64_reflected(data, c, M64, M64)
        stream = lzma.compress(data, format=lzma.FORMAT_XZ, check=lzma.CHECK_CRC64)
        self.assertIn(value.to_bytes(8, "little"), stream)

    def test_crc64_iso_check_value(self):
        c = refused.first_of_least_weight(64)
        self.assertEqual(crc64_reflected(b"123456789", c, M64, M64), 0xB90956C775A41001)


class ConstantSets(unittest.TestCase):

    def test_sha256_words_build_sha256(self):
        for message in (b"", b"abc", b"x" * 55, b"x" * 56, bytes(range(256)) * 4):
            self.assertEqual(sha256_with(refused.sha256_k(), refused.sha256_h0(), message),
                             hashlib.sha256(message).digest())

    def test_keccak_words_build_sha3_and_shake(self):
        constants = refused.keccak_round_constants()
        self.assertEqual(len(constants), 24)
        for message in (b"", b"abc", bytes(range(256)) * 2):
            self.assertEqual(sponge(constants, message, 136, 0x06, 32),
                             hashlib.sha3_256(message).digest())
            self.assertEqual(sponge(constants, message, 168, 0x1F, 200),
                             hashlib.shake_128(message).digest(200))

    def test_aes_words_build_aes(self):
        out = aes128(bytes(range(16)), bytes.fromhex("00112233445566778899aabbccddeeff"),
                     refused.aes_sbox(), refused.aes_rcon())
        self.assertEqual(out.hex(), "69c4e0d86a7b0430d8cdb78070b4c55a")

    def test_the_two_rcon_forms_agree(self):
        self.assertEqual([word >> 24 for word in refused.aes_rcon_words()], refused.aes_rcon())

    def test_ascon_constants_build_ascon_hash(self):
        state = [0x00400C0000000100, 0, 0, 0, 0]
        constants = refused.ascon_round_constants()
        ascon_permutation(state, constants)
        state[0] ^= 1 << 63
        ascon_permutation(state, constants)
        out = b""
        for block in range(4):
            out += state[0].to_bytes(8, "big")
            if block != 3:
                ascon_permutation(state, constants)
        self.assertEqual(out.hex(),
                         "7346bc14f036e87ae03d0997913088f5f68411434b3cf8b54fa796a80d251f91")

    def test_chacha_words_build_chacha20(self):
        key = bytes(range(32))
        nonce = bytes.fromhex("000000090000004a00000000")
        self.assertEqual(chacha20_block(refused.chacha_words(), key, 1, nonce)[:16].hex(),
                         "10f1e7e4d13b5915500fdd1fa32071c4")

    def test_salsa_bytes_are_the_same_text(self):
        joined = b"".join(word.to_bytes(4, "little") for word in refused.chacha_words())
        self.assertEqual(bytes(refused.salsa_bytes(32)), joined)
        self.assertEqual(bytes(refused.salsa_bytes(16)), b"expand 16-byte k")

    def test_rc5_words_build_rc5(self):
        p, q = refused.rc5_words(32)
        self.assertEqual(rc5_32_12(p, q, bytes(16), 0, 0), (0xEEDBA521, 0x6D8F4B15))

    def test_rc5_words_at_the_other_widths_are_odd(self):
        for width in (16, 32, 64):
            for word in refused.rc5_words(width):
                self.assertEqual(word & 1, 1)
                self.assertEqual(word >> width, 0)

    def test_speck_counters_build_speck(self):
        counters = refused.speck_counters(22)
        self.assertEqual(speck(counters, 16, 7, 2, [0x1918, 0x1110, 0x0908, 0x0100],
                               0x6574, 0x694C), (0xA868, 0x42F2))
        counters = refused.speck_counters(27)
        self.assertEqual(speck(counters, 32, 8, 3, [0x1B1A1918, 0x13121110, 0x0B0A0908,
                                                    0x03020100], 0x3B726574, 0x7475432D),
                         (0x8C6FA548, 0x454E028B))

    def test_pcg64_multiplier_steps_numpys_generator(self):
        try:
            import numpy
        except ImportError:
            self.skipTest("numpy is required")
        multiplier = refused.pcg64_multiplier()
        generator = numpy.random.PCG64(987654321)
        before = generator.state["state"]
        generator.advance(1)
        after = generator.state["state"]["state"]
        self.assertEqual((before["state"] * multiplier + before["inc"]) % (1 << 128), after)
        self.assertEqual(multiplier & 1, 1)


class TheList(unittest.TestCase):

    def entries(self):
        return changelog.parse_refused_list(LIST.read_bytes())

    def test_the_committed_list_is_what_the_script_computes(self):
        self.assertEqual(LIST.read_bytes(), refused.render())

    def test_names_are_unique_and_each_source_cites(self):
        entries = self.entries()
        names = [entry["name"] for entry in entries]
        self.assertEqual(len(names), len(set(names)))
        for entry in entries:
            self.assertTrue(entry["source"].startswith("research/004/refused_sources.py, "),
                            entry["name"])
            self.assertGreater(len(entry["source"]), len("research/004/refused_sources.py, "))

    def test_r15s_standard_polynomials_stand_on_the_list(self):
        polynomials = {(e["degree"], int(e["c"], 16)) for e in self.entries()
                       if e["kind"] == "polynomial"}
        for wanted in ((64, 0x1B), (128, 0x87), (64, 0x42F0E1EBA9EA3693)):
            self.assertIn(wanted, polynomials)
        names = " ".join(e["name"] for e in self.entries())
        for word in ("CMAC R64", "CMAC R128", "GCM", "CRC-64 of ISO 3309", "CRC-64 of ECMA-182"):
            self.assertIn(word, names)

    def test_every_design_is_named_where_the_inventory_says(self):
        texts = {key: (ROOT / rel).read_bytes().decode("utf-8") for key, rel in DOCUMENTS.items()}
        self.assertGreater(len(refused.DESIGNS), 20)
        for design in refused.DESIGNS:
            self.assertTrue(design.documents, design.name)
            for key in design.documents:
                self.assertIn(design.name, texts[key], (design.name, key))

    def test_every_design_has_one_known_state(self):
        for design in refused.DESIGNS:
            self.assertIn(design.state, refused.STATES, design.name)
            self.assertTrue(design.detail, design.name)

    def test_a_listed_design_has_entries(self):
        names = [entry["name"] for entry in self.entries()]
        for design in refused.DESIGNS:
            if design.state == "listed":
                self.assertTrue(any(name.startswith(design.detail) for name in names),
                                (design.name, design.detail))

    def test_a_design_waiting_for_a_file_is_not_on_the_list(self):
        names = [entry["name"] for entry in self.entries()]
        for design in refused.DESIGNS:
            if design.state in ("paper", "file"):
                self.assertFalse(any(name.startswith(design.name) for name in names), design.name)

    def test_the_written_file_is_lf_and_ends_in_one(self):
        data = LIST.read_bytes()
        self.assertEqual(data.count(b"\r"), 0)
        self.assertTrue(data.endswith(b"}\n"))
        self.assertIn("entries", json.loads(data.decode("utf-8")))


if __name__ == "__main__":
    unittest.main()
