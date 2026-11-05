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
DOWNLOADS = "reports/004-crypto-architecture-v3/downloads.json"
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


def words_of(name: str):
    entries = changelog.parse_refused_list(LIST.read_bytes())
    return [int(word, 16) for entry in entries if entry["name"] == name for word in entry["words"]]


def c_of(name: str) -> int:
    entries = changelog.parse_refused_list(LIST.read_bytes())
    return next(int(entry["c"], 16) for entry in entries if entry["name"] == name)


ASCON_ROTATIONS = ((19, 28), (61, 39), (1, 6), (10, 17), (7, 41))


def ascon_by_table(state, constants, sbox) -> None:
    """Ascon's permutation with the S-box's table in place of its bitsliced form."""
    for constant in constants:
        state[2] ^= constant
        out = [0] * 5
        for j in range(64):
            x = 0
            for word in state:
                x = (x << 1) | (word >> j & 1)
            for i in range(5):
                out[i] |= (sbox[x] >> (4 - i) & 1) << j
        state[:] = [word ^ rotr(word, a, 64) ^ rotr(word, b, 64)
                    for word, (a, b) in zip(out, ASCON_ROTATIONS)]


def grain_v1(key: str, iv: str, taps, length: int) -> str:
    b = [int(bit) for bit in f"{int(key, 16):080b}"]
    s = [int(bit) for bit in f"{int(iv, 16):064b}"] + [1] * 16

    def clock():
        x0, x1, x2, x3, x4 = s[3], s[25], s[46], s[64], b[63]
        h = (x1 ^ x4 ^ x0 & x3 ^ x2 & x3 ^ x3 & x4 ^ x0 & x1 & x2 ^ x0 & x2 & x3 ^ x0 & x2 & x4
             ^ x1 & x2 & x4 ^ x2 & x3 & x4)
        z = b[1] ^ b[2] ^ b[4] ^ b[10] ^ b[31] ^ b[43] ^ b[56] ^ h
        feedback = 0
        for tap in taps:
            feedback ^= s[tap]
        nonlinear = (s[0] ^ b[62] ^ b[60] ^ b[52] ^ b[45] ^ b[37] ^ b[33] ^ b[28] ^ b[21] ^ b[14]
                     ^ b[9] ^ b[0] ^ b[63] & b[60] ^ b[37] & b[33] ^ b[15] & b[9]
                     ^ b[60] & b[52] & b[45] ^ b[33] & b[28] & b[21]
                     ^ b[63] & b[45] & b[28] & b[9] ^ b[60] & b[52] & b[37] & b[33]
                     ^ b[63] & b[60] & b[21] & b[15] ^ b[63] & b[60] & b[52] & b[45] & b[37]
                     ^ b[33] & b[28] & b[21] & b[15] & b[9]
                     ^ b[52] & b[45] & b[37] & b[33] & b[28] & b[21])
        return z, feedback, nonlinear

    for _ in range(160):
        z, feedback, nonlinear = clock()
        s, b = s[1:] + [feedback ^ z], b[1:] + [nonlinear ^ z]
    out = 0
    for _ in range(length):
        z, feedback, nonlinear = clock()
        out = (out << 1) | z
        s, b = s[1:] + [feedback], b[1:] + [nonlinear]
    return f"{out:0{length // 4}x}"


def rabbit(key: bytes, constants, blocks: int):
    value = int.from_bytes(key, "big")
    k = [(value >> (16 * j)) & 0xFFFF for j in range(8)]
    x, c = [0] * 8, [0] * 8
    for j in range(8):
        if j % 2 == 0:
            x[j] = k[(j + 1) % 8] << 16 | k[j]
            c[j] = k[(j + 4) % 8] << 16 | k[(j + 5) % 8]
        else:
            x[j] = k[(j + 5) % 8] << 16 | k[(j + 4) % 8]
            c[j] = k[j] << 16 | k[(j + 1) % 8]
    carry = [0]

    def step() -> None:
        for j in range(8):
            total = c[j] + constants[j] + carry[0]
            carry[0], c[j] = total >> 32, total & M32
        g = []
        for j in range(8):
            square = ((x[j] + c[j]) & M32) ** 2
            g.append((square & M32) ^ (square >> 32))
        for j in range(8):
            if j % 2 == 0:
                x[j] = (g[j] + rotl(g[(j + 7) % 8], 16, 32) + rotl(g[(j + 6) % 8], 16, 32)) & M32
            else:
                x[j] = (g[j] + rotl(g[(j + 7) % 8], 8, 32) + g[(j + 6) % 8]) & M32

    for _ in range(4):
        step()
    for j in range(8):
        c[j] ^= x[(j + 4) % 8]
    out = []
    for _ in range(blocks):
        step()
        half = 0
        for j, (low, other_high, high, other_low) in enumerate(
                ((0, 5, 0, 3), (2, 7, 2, 5), (4, 1, 4, 7), (6, 3, 6, 1))):
            half |= ((x[low] & 0xFFFF) ^ (x[other_high] >> 16)) << (32 * j)
            half |= ((x[high] >> 16) ^ (x[other_low] & 0xFFFF)) << (32 * j + 16)
        out.append(half.to_bytes(16, "big"))
    return out


def enocoro_s8(s4):
    out = []
    for value in range(256):
        a, b = s4[value >> 4], s4[value & 15]
        y0 = s4[a ^ refused.times(4, b, 0x13) ^ 0xA]
        y1 = s4[refused.times(4, a, 0x13) ^ b ^ 0x5]
        byte = y0 << 4 | y1
        out.append((byte << 1 | byte >> 7) & 0xFF)
    return out


def enocoro(key: bytes, iv: bytes, constants, s8, poly: int, length: int) -> bytes:
    buffer = list(key) + list(iv) + list(constants[:8])
    state = list(constants[8:])

    def advance() -> None:
        nonlocal buffer, state
        u0, u1 = state[0] ^ s8[buffer[2]], state[1] ^ s8[buffer[7]]
        v0, v1 = u0 ^ u1, u0 ^ refused.times(2, u1, poly)
        fresh = [buffer[31] ^ state[0]] + buffer[:31]
        for q, p in ((2, 6), (7, 15), (16, 28)):
            fresh[q + 1] = buffer[q] ^ buffer[p]
        state, buffer = [v0 ^ s8[buffer[16]], v1 ^ s8[buffer[29]]], fresh

    counter = 1
    for _ in range(96):
        buffer[31] ^= counter
        counter = refused.times(counter, 2, poly)
        advance()
    out = bytearray()
    for _ in range(length):
        out.append(state[1])
        advance()
    return bytes(out)


def luffa_constants(start, low: int):
    def f(word: int) -> int:
        return ((word << 1) & M64) ^ (low if word >> 63 else 0)

    def swapped(word: int) -> int:
        return (word >> 32) | (word << 32) & M64

    out = []
    for j in range(len(start) // 2):
        word = start[2 * j] << 32 | start[2 * j + 1]
        for _ in range(8):
            word = f(word)
            out.append(word >> 32)
            word = f(swapped(word))
            out.append(word >> 32)
            word = swapped(word)
    return out


def luffa_double(a):
    t = a[7]
    return [t, a[0] ^ t, a[1], a[2] ^ t, a[3] ^ t, a[4], a[5], a[6]]


def luffa_times(factor: int, a):
    out, power = [0] * 8, list(a)
    while factor:
        if factor & 1:
            out = [x ^ y for x, y in zip(out, power)]
        power = luffa_double(power)
        factor >>= 1
    return out


def luffa_sum(items):
    out = [0] * 8
    for item in items:
        out = [x ^ y for x, y in zip(out, item)]
    return out


LUFFA_MATRICES = {3: ((3, 2, 2, 1), (2, 3, 2, 2), (2, 2, 3, 4)),
                  4: ((4, 6, 6, 7, 1), (7, 4, 6, 6, 2), (6, 7, 4, 6, 4), (6, 6, 7, 4, 8))}


def luffa_inject(h, message):
    if len(h) in LUFFA_MATRICES:
        return [luffa_sum(luffa_times(factor, item) for factor, item in zip(row, h + [message]))
            for row in LUFFA_MATRICES[len(h)]]
    total = luffa_double(luffa_sum(h))
    eta = [[x ^ y for x, y in zip(item, total)] for item in h]
    xi = [[x ^ y for x, y in zip(luffa_double(eta[j]), eta[(j + 1) % 5])] for j in range(5)]
    return [luffa_sum((luffa_double(xi[j]), xi[j - 1], luffa_times(1 << j, message)))
            for j in range(5)]


def luffa_crumbs(a, order, sbox) -> None:
    fresh = [0, 0, 0, 0]
    for bit in range(32):
        nibble = sum((a[index] >> bit & 1) << place for place, index in enumerate(order))
        for place in range(4):
            fresh[place] |= (sbox[nibble] >> place & 1) << bit
    for place, index in enumerate(order):
        a[index] = fresh[place]


def luffa_q(block, j: int, constants, sbox):
    a = list(block)
    for k in range(4, 8):
        a[k] = rotl(a[k], j, 32)
    for r in range(8):
        luffa_crumbs(a, (0, 1, 2, 3), sbox)
        luffa_crumbs(a, (5, 6, 7, 4), sbox)
        for k in range(4):
            high = a[k + 4] ^ a[k]
            low = rotl(a[k], 2, 32) ^ high
            high = rotl(high, 14, 32) ^ low
            low = rotl(low, 10, 32) ^ high
            a[k], a[k + 4] = low, rotl(high, 1, 32)
        a[0] ^= constants[16 * j + 2 * r]
        a[4] ^= constants[16 * j + 2 * r + 1]
    return a


def luffa(message: bytes, width: int, words: int, starting, constants, sbox) -> str:
    h = [list(starting[8 * j:8 * j + 8]) for j in range(width)]

    def absorb(block) -> None:
        nonlocal h
        h = [luffa_q(item, j, constants, sbox) for j, item in enumerate(luffa_inject(h, block))]

    padded = message + b"\x80"
    padded += b"\0" * (-len(padded) % 32)
    for start in range(0, len(padded), 32):
        absorb([int.from_bytes(padded[start + 4 * i:start + 4 * i + 4], "big") for i in range(8)])
    out = []
    while len(out) < words:
        absorb([0] * 8)
        out += luffa_sum(h)
    return " ".join(f"{word:08x}" for word in out[:words])


def sparx_a(word: int) -> int:
    left, right = word >> 16, word & 0xFFFF
    left = (rotr(left, 7, 16) + right) & 0xFFFF
    right = rotl(right, 2, 16) ^ left
    return left << 16 | right


def add_halves(a: int, b: int, extra: int = 0) -> int:
    high = ((a >> 16) + (b >> 16)) & 0xFFFF
    return high << 16 | ((a + b + extra) & 0xFFFF)


def sparx(words, key, steps: int, counters):
    """Sparx-64/128 for two words of state, Sparx-128/128 for four with four key words and
    Sparx-128/256 for four with eight, as the paper's Algorithms 1 to 4 give them."""
    y, k = list(words), list(key)
    rounds = 3 if len(y) == 2 else 4
    remaining = iter(counters)
    for _ in range(steps):
        for i in range(len(y)):
            for r in range(rounds):
                y[i] = sparx_a(y[i] ^ k[r])
            r_now = next(remaining)
            k[0] = sparx_a(k[0])
            k[1] = add_halves(k[1], k[0])
            if len(k) == 8:
                k[4] = sparx_a(k[4])
                k[5] = add_halves(k[5], k[4], r_now)
                k = k[5:] + k[:5]
            elif len(y) == 4:
                k[2] = sparx_a(k[2])
                k[3] = add_halves(k[3], k[2], r_now)
                k = k[3:] + k[:3]
            else:
                k[3] = add_halves(k[3], 0, r_now)
                k = k[3:] + k[:3]
        if len(y) == 2:
            x, z = y
            t = rotl((x >> 16) ^ (x & 0xFFFF), 8, 16)
            y = [z ^ x ^ (t << 16 | t), x]
        else:
            halves = [half for word in y[:2] for half in (word >> 16, word & 0xFFFF)]
            t = rotl(halves[0] ^ halves[1] ^ halves[2] ^ halves[3], 8, 16)
            mixed = [halves[2] ^ t, halves[1] ^ t, halves[0] ^ t, halves[3] ^ t]
            y = [y[2] ^ (mixed[0] << 16 | mixed[1]), y[3] ^ (mixed[2] << 16 | mixed[3]), y[0], y[1]]
    return [word ^ k[i] for i, word in enumerate(y)]


def mt19937(seed: int, multiplier: int, words, count: int):
    state = [seed & M32]
    for _ in range(623):
        state.append(multiplier * state[-1] & M32)
    start = list(state)
    a, b, c = words
    out = []
    for _ in range(count // 624 + 1):
        for k in range(624):
            y = (state[k] & 0x80000000) | (state[(k + 1) % 624] & 0x7FFFFFFF)
            state[k] = state[(k + 397) % 624] ^ (y >> 1) ^ (a if y & 1 else 0)
        for value in state:
            value ^= value >> 11
            value ^= (value << 7) & b
            value ^= (value << 15) & c
            out.append(value ^ (value >> 18))
    return start, out[:count]


def curve_add(p: int, first, second):
    if first is None or second is None:
        return first or second
    x1, y1, x2, y2 = *first, *second
    if x1 == x2:
        if (y1 + y2) % p == 0:
            return None
        slope = (3 * x1 * x1 - 3) * pow(2 * y1, -1, p) % p
    else:
        slope = (y2 - y1) * pow(x2 - x1, -1, p) % p
    x3 = (slope * slope - x1 - x2) % p
    return x3, (slope * (x1 - x3) - y1) % p


def curve_times(p: int, k: int, point):
    out = None
    while k:
        if k & 1:
            out = curve_add(p, out, point)
        point = curve_add(p, point, point)
        k >>= 1
    return out


def present80(plain: int, key: int, sbox, counters) -> int:
    state, register = plain, key
    for counter in counters:
        state ^= register >> 16
        state = sum(sbox[state >> (4 * i) & 15] << (4 * i) for i in range(16))
        state = sum((state >> i & 1) << (i * 16 % 63 if i != 63 else 63) for i in range(64))
        register = ((register & ((1 << 19) - 1)) << 61) | (register >> 19)
        register = (sbox[register >> 76] << 76) | (register & ((1 << 76) - 1))
        register ^= counter << 15
    return state ^ (register >> 16)


def printcipher48(plain: int, key: int, permutation_key: int, boxes, counters) -> int:
    state = plain
    for counter in counters:
        state ^= key
        state = sum((state >> i & 1) << (3 * i % 47 if i != 47 else 47) for i in range(48))
        state ^= counter
        out = 0
        for j in range(16):
            box = permutation_key >> (2 * j) & 3
            out |= boxes[8 * box + (state >> (3 * j) & 7)] << (3 * j)
        state = out
    return state


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


class SetsReadFromFiles(unittest.TestCase):
    """Each table is used in its own primitive and compared with a vector or relation that the same
    file prints, so that a word read wrongly fails. MICKEY's and SOSEMANUK's tables have no such
    vector here and are checked for shape and for the relations the files state."""

    def test_ascon_tables_rebuild_the_precomputed_states(self):
        constants, sbox = words_of("Ascon const_i"), words_of("Ascon S-box")
        values, states = words_of("Ascon initial values"), words_of("Ascon precomputed states")
        for column, value in enumerate(values[1:]):
            state = [value, 0, 0, 0, 0]
            ascon_by_table(state, constants[4:], sbox)
            self.assertEqual(state, states[5 * column:5 * column + 5])

    def test_ascon_initial_values_follow_formula_79(self):
        table = ((1, 12, 8, 128, 16), (2, 12, 12, 256, 8), (3, 12, 12, 0, 8), (4, 12, 12, 0, 8))
        for value, (v, a, b, t, rate) in zip(words_of("Ascon initial values"), table):
            self.assertEqual(value, v | a << 16 | b << 20 | t << 24 | rate << 40)

    def test_ascon_constants_hold_the_twelve_already_listed(self):
        self.assertEqual(words_of("Ascon const_i")[4:], refused.ascon_round_constants())

    def test_ascon_constants_keep_one_pattern_over_all_sixteen(self):
        self.assertEqual(words_of("Ascon const_i"),
                         [(3 - i & 15) << 4 | (12 + i & 15) for i in range(16)])

    def test_grain_v1_builds_the_files_vectors(self):
        c = c_of("Grain v1 LFSR polynomial")
        self.assertTrue(refused.is_irreducible(1 << 80 | c))
        taps = [80] + [80 - e for e in range(1, 80) if c >> e & 1]
        taps = [tap % 80 for tap in taps]
        self.assertEqual(sorted(taps), [0, 13, 23, 38, 51, 62], "the file's update function")
        self.assertEqual(grain_v1("0" * 20, "0" * 16, taps, 80), "7b978cf36846e5f4ee0b")
        self.assertEqual(grain_v1("0123456789abcdef1234", "0123456789abcdef", taps, 80),
                         "42b567ccc65317680225")

    def test_grain_128aead_polynomial_is_the_files_update_function(self):
        c = c_of("Grain-128AEAD LFSR polynomial")
        self.assertTrue(refused.is_irreducible(1 << 128 | c))
        update = (0, 7, 38, 70, 81, 96)
        self.assertEqual(c, 1 + sum(1 << (128 - tap) for tap in update if tap))

    def test_mickey_tables_have_the_files_shape(self):
        taps = words_of("MICKEY 2.0 RTAPS")
        self.assertEqual(taps, sorted(set(taps)))
        self.assertEqual((len(taps), taps[0], taps[-1]), (50, 0, 97))
        for name, length in (("COMP0", 98), ("COMP1", 98), ("FB0", 100), ("FB1", 100)):
            bits = words_of(f"MICKEY 2.0 {name}")
            self.assertEqual(len(bits), length)
            self.assertEqual(set(bits), {0, 1})

    def test_rabbit_builds_the_rfcs_vectors(self):
        constants = words_of("Rabbit counter constants")
        out = rabbit(bytes(16), constants, 3)
        self.assertEqual([block.hex() for block in out],
                         ["b15754f036a5d6ecf56b45261c4af702", "88e8d815c59c0c397b696c4789c68aa7",
                          "f416a1c3700cd451da68d1881673d696"])
        key = bytes.fromhex("912813292e3d36fe3bfc62f1dc51c3ac")
        self.assertEqual(rabbit(key, constants, 1)[0].hex(), "3d2df3c83ef627a1e97fc38487e2519c")

    def test_sosemanuk_sets_hold_the_files_relations(self):
        c = c_of("SOSEMANUK field polynomial Q")
        self.assertTrue(refused.is_irreducible(1 << 8 | c))
        self.assertEqual(words_of("SOSEMANUK polynomial P coefficients")[0], 0xE1, "beta^23")
        powers = [1]
        while len(powers) < 255:
            value = powers[-1] << 1
            powers.append(value ^ (1 << 8 | c) if value >> 8 else value)
        self.assertEqual(len(set(powers)), 255, "beta generates the field, as the file says")
        self.assertEqual(words_of("SOSEMANUK polynomial P coefficients"),
                         [powers[k] for k in (23, 245, 48, 239)])
        self.assertEqual(words_of("SOSEMANUK multiplier M"), [1415926535], "ten decimals of pi")
        boxes = words_of("SOSEMANUK Serpent S-boxes")
        for k in range(8):
            self.assertEqual(sorted(boxes[16 * k:16 * k + 16]), list(range(16)))

    def test_enocoro_s4_builds_the_files_s8(self):
        self.assertEqual(enocoro_s8(words_of("Enocoro S-box s4")), words_of("Enocoro S-box s8"))
        self.assertTrue(refused.is_irreducible(1 << 4 | c_of("Enocoro field polynomial phi4")))

    def test_enocoro_builds_the_files_vectors(self):
        poly = 1 << 8 | c_of("Enocoro field polynomial phi8")
        constants, s8 = words_of("Enocoro initial constants"), words_of("Enocoro S-box s8")
        self.assertEqual(enocoro(bytes(16), bytes(8), constants, s8, poly, 16).hex(),
                         "63d7da6b55737fcf5734b6773ae772e8")
        self.assertEqual(enocoro(bytes(range(16)), bytes(range(0, 128, 16)), constants, s8, poly,
                                 16).hex(), "c8c8ee433b0dc040e53bc506ea21ad82")

    def test_luffa_polynomial_is_the_files_pseudo_code(self):
        self.assertEqual(c_of("Luffa constant-generator polynomial g"), 0xC4D6496C55C61C8D)

    def test_luffa_field_polynomial_is_the_files_multiplication(self):
        doubled = luffa_double([0] * 7 + [1])
        self.assertEqual(c_of("Luffa field polynomial"),
                         sum(1 << i for i, word in enumerate(doubled) if word))

    def test_luffa_generator_rebuilds_every_step_constant(self):
        self.assertEqual(luffa_constants(words_of("Luffa constant-generator initial values"),
                                         c_of("Luffa constant-generator polynomial g")),
                         words_of("Luffa step constants"))

    def test_luffa_builds_the_files_vectors(self):
        starting, sbox = words_of("Luffa starting variables"), words_of("Luffa S-box")
        constants = words_of("Luffa step constants")
        self.assertEqual(luffa(b"abc", 3, 8, starting, constants, sbox),
                         "f29311b8 7e9e40de 7699be23 fbeb5a47 cb16ea4f 5556d47c a40c12ad 764a73bd")
        self.assertEqual(luffa(b"abc", 4, 12, starting, constants, sbox),
                         "9a7abb79 7a840e2d 423c34c9 1f559f68 09bdb291 6fb2e9ef fec2fa0a 7a69881b "
                         "e9872480 c635d20d 2fd6e95d 046601a7")
        self.assertEqual(luffa(b"abc", 5, 16, starting, constants, sbox),
                         "f4024597 3e80d79d 0f4b9b20 2ddd4505 b81b8830 501bea31 612b5817 aae38792 "
                         "1dcefd80 8ca2c780 20aff593 45d6f91f 0ee6b2ee e113f0cb cf22b643 81387e8a")

    def test_sparx_counters_build_the_files_vectors(self):
        key = [0x00112233, 0x44556677, 0x8899AABB, 0xCCDDEEFF]
        wide = key + [0xFFEEDDCC, 0xBBAA9988, 0x77665544, 0x33221100]
        plain = [0x01234567, 0x89ABCDEF]
        block = plain + [0xFEDCBA98, 0x76543210]
        self.assertEqual(sparx(plain, key, 8, words_of("Sparx-64/128 key-schedule counter")),
                         [0x2BBEF152, 0x01F55F98])
        self.assertEqual(sparx(block, key, 8, words_of("Sparx-128/128 key-schedule counter")),
                         [0x1CEE7540, 0x7DBF23D8, 0xE0EE1597, 0xF42852D8])
        self.assertEqual(sparx(block, wide, 10, words_of("Sparx-128/256 key-schedule counter")),
                         [0x3328E637, 0x14C76CE6, 0x32D15A54, 0xE4B0C820])

    def test_mt19937_words_step_numpys_generator(self):
        import numpy
        start, ours = mt19937(4357, words_of("MT19937 seeding multiplier")[0],
                              words_of("MT19937 parameters"), 1300)
        generator = numpy.random.MT19937()
        generator.state = {"bit_generator": "MT19937", "state": {
            "key": numpy.array(start, dtype=numpy.uint32), "pos": 624}}
        self.assertEqual(ours, [int(value) for value in generator.random_raw(1300)])

    def test_dual_ec_points_lie_on_their_curves_with_the_stated_order(self):
        for name, bits in (("P-256", 256), ("P-384", 384), ("P-521", 521)):
            p, n, b, px, py, qx, qy = words_of(f"Dual_EC_DRBG {name}")
            self.assertEqual((p.bit_length(), n.bit_length()), (bits, bits))
            for x, y in ((px, py), (qx, qy)):
                self.assertEqual((y * y - x ** 3 + 3 * x - b) % p, 0)
                self.assertIsNone(curve_times(p, n, (x, y)))

    def test_sparkle_constants_are_the_files_words(self):
        self.assertEqual(words_of("SPARKLE round constants"),
                         [0xB7E15162, 0xBF715880, 0x38B4DA56, 0x324E7738,
                          0xBB1185EB, 0x4F7C7B57, 0xCFBFA1C8, 0xC2B3293D])

    def test_printcipher_tables_build_the_files_vector(self):
        boxes = words_of("PRINTcipher virtual S-boxes")
        counters = words_of("PRINTcipher-48 round counter")
        self.assertEqual(printcipher48(0x4C847555C35B, 0xC28895BA327B, 0x69D2CDB6, boxes, counters),
                         0xEB4AF95E7D37)

    def test_printcipher_register_rebuilds_table_5(self):
        self.assertEqual(refused.printcipher_counter(7, 96), words_of("PRINTcipher-96 round counter"))

    def test_printcipher_s_box_is_the_first_virtual_box(self):
        boxes = words_of("PRINTcipher virtual S-boxes")
        self.assertEqual(words_of("PRINTcipher S-box"), boxes[:8])
        for k in range(4):
            self.assertEqual(sorted(boxes[8 * k:8 * k + 8]), list(range(8)))

    def test_present_builds_the_files_vectors(self):
        sbox, counters = words_of("PRESENT S-box"), words_of("PRESENT key-schedule counter")
        self.assertEqual(counters, list(range(1, 32)), "the last counter's low bit reaches no key")
        ones64, ones80 = (1 << 64) - 1, (1 << 80) - 1
        for plain, key, cipher in ((0, 0, 0x5579C1387B228445), (0, ones80, 0xE72C46C0F5945049),
                                   (ones64, 0, 0xA112FFC72F68417B),
                                   (ones64, ones80, 0x3333DCD3213210D2)):
            self.assertEqual(present80(plain, key, sbox, counters), cipher)


class TheList(unittest.TestCase):

    def entries(self):
        return changelog.parse_refused_list(LIST.read_bytes())

    def test_the_committed_list_is_what_the_script_computes(self):
        self.assertEqual(LIST.read_bytes(), refused.render())

    def test_names_are_unique_and_each_source_cites(self):
        entries = self.entries()
        names = [entry["name"] for entry in entries]
        self.assertEqual(len(names), len(set(names)))
        manifest = json.loads((ROOT / DOWNLOADS).read_bytes().decode("utf-8"))["entries"]
        fetched = {entry["name"] for entry in manifest if entry["status"] == "fetched"}
        for entry in entries:
            first, _, citation = entry["source"].partition(", ")
            self.assertIn(first, fetched | {"research/004/refused_sources.py"}, entry["name"])
            self.assertTrue(citation, entry["name"])

    def test_the_first_entries_stand_as_the_list_named_them(self):
        names = [entry["name"] for entry in self.entries()]
        self.assertEqual(names[:len(refused.entries())], [e["name"] for e in refused.entries()])

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
