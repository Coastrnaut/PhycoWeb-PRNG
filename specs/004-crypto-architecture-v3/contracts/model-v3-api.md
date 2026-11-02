# Contract: the `phyco-v3` reference model (`phycoweb/model_v3.py`)

> This feature makes no security claim. No PhycoWeb-PRNG model, `phyco-v3` included, may be used
> to generate secrets; use an established cryptographic random-number generator for keys,
> nonces, tokens and salts. Passing statistical tests does not show cryptographic security.

The model is the oracle for every later implementation (FR-056). It is written from the design
document after selection, and the design document is the authority: where this contract and
the design document differ, the design document wins and this contract is corrected. Values
shown as `<…>` are fixed by the design document.

## Module rules (FR-020, FR-035, FR-055; research R17)

- Imports: the standard library, `phycoweb.constants_v3` and `phycoweb.selftest_v3` only, the two
  data modules the generators write (data model §11). `phycoweb.selftest_v3` is imported inside
  `Generator`'s constructor only, so `pi`, `pi_inv`, `pi_trace` and `ResearchDuplex` import without
  it, as `gen_vectors_v3.py` needs on its first run, before the module exists; a test imports the
  model with the module absent. A test bans every other import
  (numpy, scipy and the analysis code included), as `tests/test_purity_v2.py` does for
  `phyco-v2`, and also bans `time`, `random`, `os`, `sys`, `platform` and `secrets` in the
  model. The generators read the clock and the platform only for the sidecar record of the
  vectors (data model §11), never for content.
- Arithmetic: integers only. In the functions that compute Π, Π⁻¹ and the mode, a test bans
  multiplication, division, modulo and power operators, floating-point constants and
  data-dependent shift or rotation amounts (every amount is a literal or a constant from
  `constants_v3`). Index arithmetic outside those functions is not restricted.
- No branch, table index or selection on secret data; comparisons only on public counters, and
  those are unsigned (FR-020, FR-055). In the model this is a discipline only, and the model is
  never called constant time, since Python integers are not; the claim test flags "constant time" in
  every line it scans, beside the model and elsewhere (FR-069). Constant time by construction is a
  property of the design's sequence of operations and of a hardware implementation of it: in
  hardware, a cycle count fixed by public values; in feature 006's C, no branch or memory index that
  depends on secret data.
- Key and zeroization: the object stores its own copy of the key as a `bytearray`; `zeroize`, and
  every path that zeroizes, overwrites that copy with zeros in place and then drops it, and drops
  the state's integers, which Python cannot overwrite. Like constant time, this is a discipline: it
  governs what the object keeps, not what Python's memory may still hold, and the caller's own copy
  of the key is outside the rule. A test keeps a reference to the buffer, calls `zeroize`, and
  checks that the buffer reads all zeros and that the object no longer refers to it (FR-025,
  FR-058).
- Python 3.8 grammar (best-effort `ast.parse(source, feature_version=(3, 8))` check).
- Deterministic: the same inputs give the same outputs on every platform and Python version
  (FR-035).
- `MODEL_ID = "phyco-v3"`; the module docstring marks it model-only, RTL-pending (Principle II).

## Variant IDs (FR-032, FR-033; R14)

`<design>/n<n>-w<w>-R<R>-c<c>`, for example `phyco-v3/n4-w32-R<R4>-c256`.

| Constant or function | Contract |
|----------------------|----------|
| `PRODUCTION_VARIANTS` | exactly the three IDs at n = 4, 8 and 16, w = 32, c = 256 and the frozen R of each size |
| `parse_variant(variant_id)` | returns `(n, w, R, c)`; raises `VariantRefused` for a malformed ID or a value neither supported nor open to exploration |
| `is_production(variant_id)` | true only for the three production IDs |

Supported values: n ∈ {2, 4, 8, 16}, and 3 where the design document specifies a three-colour
schedule, the sizes spec FR-018 lists; w ∈ {4, 8, 16, 32}, with w = 4 at 2×2 only; R from 1 to the
frozen R at those sizes; c a multiple of w and of 16 with 0 < c < b, a multiple of 64 for a keyed
variant, and c = 256 at every claimable size (research R14). Every other n from 2 to 16 is for
exploration only, where the design document's update schedule covers n (even n, and odd n only with
a three-colour schedule): the research interface accepts its ID, which carries its R, with the table
that `gen_constants_v3.py --exploration N W` writes for that (n, w) under
`research/004/exploration/`, never frozen and never evidence (spec FR-018).

## Permutation (research interface)

```text
pi(lanes, variant_id, table=None) -> list[int]
pi_inv(lanes, variant_id, table=None) -> list[int]
pi_trace(lanes, variant_id, table=None) -> list[list[int]]
```

- `lanes`: 2n² integers in the design document's node and lane order, each 0 ≤ x < 2^w; any
  other length or value raises `ValueError`.
- `pi_inv(pi(x, v), v) == x` and `pi(pi_inv(x, v), v) == x` for every input (FR-019).
- `pi_trace` returns the state after every phase of every round, the first entry being the
  input; it is the step-by-step record the second transcription is compared against (FR-057).
- These functions accept every supported variant, reduced ones included, and an exploration ID with
  its table: they are the research interface, not the production interface.
- `table`: for an exploration ID only (Variant IDs), the table that the caller reads from
  `research/004/exploration/`, since the model imports no other data module (Module rules); a
  supported variant takes its table from `constants_v3` and refuses a `table`, and an exploration ID
  without a table, or with one whose (n, w) or number of rounds differs from the ID's, raises
  `VariantRefused`.

## Generator (production interface; FR-007, FR-013 to FR-016, FR-033)

```text
g = Generator(variant_id, key)          # key 32 bytes; runs the start-up self-test (FR-059)
g.instantiate(nonce, pers=b"")          # nonce 16 bytes, pers ≤ <max> bytes; uses the stored key
out = g.generate(nbits)                 # canonical serialization (FR-015); forget runs inside
g.reseed(data)                          # data ≤ <max> bytes; treated as attacker-chosen (T9)
g.zeroize()                             # clears the whole state and the key; the object is then unusable
```

| Rule | Contract |
|------|----------|
| Variant | `Generator` accepts only `PRODUCTION_VARIANTS`; any other ID raises `VariantRefused` (SC-010) |
| Construction | the constructor checks in this order, each refusal raising one exception: the variant (`VariantRefused`), then the key length (`ValueError`), then the self-test (`SelfTestError`); only then does it store the key. A failed construction leaves no object, and each refusal is tested with an input that would also fail every later check, so the order shows; the tests check the exact type, since `VariantRefused` is a `ValueError` (FR-058) |
| Start-up self-test | the constructor imports `phycoweb.selftest_v3` (Module rules) and runs the known-answer self-test of FR-059, whose inputs and expected output come from it, copied from the committed vectors (frozen at the freeze; data model §11), then zeroizes the whole state, and only then stores its own copy of the key as a `bytearray`, which the object holds until `zeroize` clears it (Module rules); on failure it zeroizes any state the self-test used and raises `SelfTestError`, and no object exists; a `Generator` built before that module exists fails its self-test in the same way |
| Key | taken once, at construction. The key enters the state at every `instantiate`, from the stored copy, so FR-013's instantiate keeps its inputs. No key is ever compared. In hardware the key register is loaded once and zeroized with the state, and key loading is a call of its own, with its latency and cycle count (FR-020, FR-025) |
| Call sequence | `generate` or `reseed` before `instantiate`, and any call after `zeroize`, raise `CallSequenceError`; `zeroize` is final, so a new key needs a new `Generator`; `instantiate` may be called again with a new nonce |
| Forget | runs inside every `generate`, after its last output block, so it can never be skipped; instantiate also ends with a forget call, in the form the theorem covers (FR-013; research R10) |
| Output | `generate(nbits)` returns `nbits / 8` bytes in the design document's serialization; nbits a positive multiple of 32, otherwise `ValueError`; `words32(out)` splits it into 32-bit words as the vector files list them. The last output block of a request whose length is not a multiple of r keeps its first bits in FR-015's serialization order and discards the rest, and the padding rule fixes partial input blocks (FR-014); nothing rounds, since nothing divides (FR-027) |
| No read-back | `Generator` exposes no state, key or counter through any public method or attribute, and refuses reduced variants. `pi`, `pi_inv`, `pi_trace` and `ResearchDuplex`, named research-only in the docstring, are the only places that show state or run reduced variants. Python cannot make memory unreadable, so the rule concerns the interface (FR-025, FR-033) |
| Per-request limit | nbits above min(per-instantiation limit, 2¹⁹) raises `LimitExceeded`, with no output and no state change |
| Per-instantiation limit | output that would pass the limit raises `LimitExceeded`, with no output and no state change; a new nonce is needed; `reseed` never resets a counter |
| Other limits | every other online quantity the theorem's bound counts (for example calls of Π per key, instantiations per key, held at research R9's random-nonce limit whatever the nonces, and reseeds per instantiation) has the design document's limit and a counter; a call that would pass one raises `LimitExceeded`, with no output and no state change, except at a per-key limit, which also ends the object (below; research R9) |
| Per-key limit | a `Generator` holds one key, from construction; output under all its nonces counts against the per-key limit, and its instantiations against the random-nonce limit of research R9, at most 2³², whatever nonces the caller uses, since the object cannot tell a random nonce from a counter value; and a call refused at a per-key limit raises `LimitExceeded`, zeroizes and ends the object, since nothing more may be done with that key; the counters are never reset, since `zeroize` ends the object; the refusals at this limit and at the per-instantiation limit are tested through `ResearchDuplex.from_state`, which applies the same limit function (Research duplex; REP-078) |
| Keys u, and limits across objects | u is a parameter of the bound, stated in the security target. Across objects, processes and devices, the per-key limits and u are usage rules that the design document states for the caller; the model enforces them only within one object |
| Nonce reuse | the same key, nonce and personalization string give the same output; more generally, under one key and nonce, two instantiations agree until the first call or input word that differs takes effect (the personalization string, a request's length, a reseed's input or the order of calls), and the output blocks given while they agree repeat, the design document's chapter "Mode" naming which blocks repeat in each case; stated behaviour (T7), not detected, and outside the mode's bound, which covers a repeated nonce only through the collision term of research R9 (spec FR-006; SEC-083); the tests show each case the model can run (spec FR-058) |
| Lengths | a key other than 32 bytes at construction, a nonce other than 16 bytes, or a personalization string or reseed input over its maximum raises `ValueError` |

The model never wraps, truncates or carries on past a limit (Edge Cases). Counters wider than
32 bits are held as 32-bit words with the design document's carry rule (re-decided feature-002
FR-002).

**Failure paths**, each tested (FR-058):

| Path | Effect |
|------|--------|
| A failed construction: a refused variant, a wrong key length or a failed self-test | no object exists; any state the self-test used is zeroized; no copy of the key was stored |
| A refused request: a limit other than a per-key one, a length, a call out of sequence | nothing changes, and the object stays usable |
| A failed self-test | a failed construction (above): it zeroizes, and no object exists |
| An exception after the state has changed | zeroizes the whole state and ends the object, so no half-updated state survives |
| A call refused at a per-key limit | zeroizes and ends the object |

**Error paths in hardware**: the design document lists every condition the RTL detects after the
state has changed, each of which zeroizes, raises the error signal with a zeroizing code and needs a
new key, such as a last partial word of a personalization string or a reseed input with a nonzero
unused byte, which can arrive after earlier blocks of that input have been absorbed; a bad request
that valid and ready refuse before anything changes is a refusal that changes nothing (FR-025). The
model takes whole byte strings and has no such case.

**Across resets in hardware**: a device cannot end itself as an object can, so a reset or
zeroization returns it to a state that accepts a new key. The per-key limits and counters then
restart, so across resets they are usage rules for the caller, as across objects in the model,
and the design document lists them with the other usage rules (FR-007, FR-025).

## Research duplex

```text
d = ResearchDuplex(variant_id, key)     # any supported keyed variant, reduced ones included
d = ResearchDuplex.from_state(variant_id, key, lanes, counters)   # research only: chosen state
```

The same calls and rules as `Generator`, on any supported variant, for evidence on reduced
variants, except two: it runs no self-test, since `gen_vectors_v3.py` writes the vectors, and the
self-test data copied from them, through it (data model §11), so its constructor checks the variant
and then the key length only; and the lengths: a key of c/8 bytes and a nonce of c/16 bytes for the
variant's capacity c, so 32 and 16 bytes at every claimable size (research R14). Other lengths raise
`ValueError`. A keyless variant, whose c is not a multiple of 64 or whose key and nonce
leave no room in the state for the padding and domain bits (research R14),
raises `VariantRefused`; only the permutation interface applies to it. It is
not the production interface: it is named in the model's docstring as research only, and
`Generator` never delegates to it.

`ResearchDuplex.from_state(variant_id, key, lanes, counters)`, a call `Generator` lacks and
research-only, starts the mode from a chosen state and chosen counter values, each within its range,
and refuses any other with `ValueError`. `Generator` has no such path: a test checks that it has
none and that `Generator` and `ResearchDuplex` enforce every limit through one shared function, so
that a refusal reached through `from_state` tests the rule `Generator` applies. The refusals at a
per-key or per-instantiation limit (spec FR-058) and quickstart M5's refusals beyond every limit are
tested through it, every other path through the normal calls, and `gen_constructed_v3.py` writes
through it the constructed-state vectors that the design document's list of edge states marks as
covered only from a chosen state (data model §11; REP-078).

## Exceptions

| Exception | Base | Raised when |
|-----------|------|-------------|
| `VariantRefused` | `ValueError` | an unsupported or reduced variant at `Generator`; a keyless variant at `ResearchDuplex`; an unsupported value anywhere; an exploration ID without its table, or with a table that does not match it |
| `CallSequenceError` | `RuntimeError` | a call out of the order above |
| `LimitExceeded` | `ValueError` | a request or total beyond a limit; at a per-key limit the object is also zeroized and ended |
| `SelfTestError` | `RuntimeError` | the start-up self-test fails; any state it used is zeroized, and no object exists |

There is no `KeyMismatch`: the key is taken at construction and never compared.
The constructor's checks run in the order of the Generator table's "Construction" row, so a call
wrong in two ways raises the first check's exception.

## Tests that hold the model to this contract (FR-058)

`tests/test_model_v3.py`: minimum, maximum and boundary values; all-zero and all-one keys and
nonces; single-bit keys; overflow and truncation; shift and rotation boundaries; reset,
zeroization and repeated instantiation; long runs (the 2²⁰-word digest); every exception above
and every failure path; every supported configuration; every data-flow direction the design
document states. `tests/test_vectors_v3.py` and `tests/test_v3_transcription.py` cover the
vectors and the second transcription; the model's tests also check that `phyco-v3` reproduces
the selected candidate's outputs through the variant map of the `selected` log entry (data
model §3).
