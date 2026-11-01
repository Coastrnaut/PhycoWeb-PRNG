# Contract: the `phyco-v3` reference model (`phycoweb/model_v3.py`)

> This feature makes no security claim. No PhycoWeb-PRNG model, `phyco-v3` included, may be used
> to generate secrets; use an established cryptographic random-number generator for keys,
> nonces, tokens and salts. Passing statistical tests does not show cryptographic security.

The model is the oracle for every later implementation (FR-056). It is written from the design
document after selection, and the design document is the authority: where this contract and
the design document differ, the design document wins and this contract is corrected. Values
shown as `<…>` are fixed by the design document.

## Module rules (FR-020, FR-035, FR-055; research R17)

- Imports: the standard library and `phycoweb.constants_v3` only. A test bans every other import
  (numpy, scipy and the analysis code included), as `tests/test_purity_v2.py` does for
  `phyco-v2`.
- Arithmetic: integers only. In the functions that compute Π, Π⁻¹ and the mode, a test bans
  multiplication, division, modulo and power operators, floating-point constants and
  data-dependent shift or rotation amounts (every amount is a literal or a constant from
  `constants_v3`). Index arithmetic outside those functions is not restricted.
- No branch, table index or selection on secret data; comparisons only on public counters, and
  those are unsigned (FR-020, FR-055).
- Python 3.8 grammar (best-effort `ast.parse(source, feature_version=(3, 8))` check).
- Deterministic: the same inputs give the same outputs on every platform and Python version
  (FR-035).
- `MODEL_ID = "phyco-v3"`; the module docstring marks it model-only, RTL-pending (Principle II).

## Variant IDs (FR-032, FR-033; R14)

`<design>/n<n>-w<w>-R<R>-c<c>`, for example `phyco-v3/n4-w32-R<R4>-c256`.

| Constant or function | Contract |
|----------------------|----------|
| `PRODUCTION_VARIANTS` | exactly the three IDs at n = 4, 8 and 16, w = 32, c = 256 and the frozen R of each size |
| `parse_variant(variant_id)` | returns `(n, w, R, c)`; raises `VariantRefused` for a malformed ID or an unsupported value |
| `is_production(variant_id)` | true only for the three production IDs |

Supported values: n = 2…16 where the design document's update schedule covers n (even n, and
odd n only with a three-colour schedule); w ∈ {4, 8, 16, 32}, with w = 4 at 2×2 only; R from 1
to the frozen R; c a multiple of w with 0 < c < b, and c = 256 at every claimable size.

## Permutation (research interface)

```text
pi(lanes, variant_id) -> list[int]
pi_inv(lanes, variant_id) -> list[int]
pi_trace(lanes, variant_id) -> list[list[int]]
```

- `lanes`: 2n² integers in the design document's node and lane order, each 0 ≤ x < 2^w; any
  other length or value raises `ValueError`.
- `pi_inv(pi(x, v), v) == x` and `pi(pi_inv(x, v), v) == x` for every input (FR-019).
- `pi_trace` returns the state after every phase of every round, the first entry being the
  input; it is the step-by-step record the second transcription is compared against (FR-057).
- These functions accept every supported variant, reduced ones included: they are the research
  interface, not the production interface.

## Generator (production interface; FR-007, FR-013 to FR-016, FR-033)

```text
g = Generator(variant_id)               # runs the start-up self-test (FR-059)
g.instantiate(key, nonce, pers=b"")     # key 32 bytes, nonce 16 bytes, pers ≤ <max> bytes
out = g.generate(nbits)                 # canonical serialization (FR-015); forget runs inside
g.reseed(data)                          # data ≤ <max> bytes; treated as attacker-chosen (T9)
g.zeroize()                             # whole state, counters and key binding cleared
```

| Rule | Contract |
|------|----------|
| Variant | `Generator` accepts only `PRODUCTION_VARIANTS`; any other ID raises `VariantRefused` (SC-010) |
| Start-up self-test | the constructor runs the known-answer self-test of FR-059, whose inputs and expected output come from the committed vectors (frozen at the freeze), then zeroizes the whole state; on failure it raises `SelfTestError` and the object stays unusable |
| Call sequence | `generate` or `reseed` before `instantiate`, or after `zeroize`, raises `CallSequenceError`; `instantiate` may be called again with a new nonce |
| Forget | runs inside every `generate`, after its last output block, so it can never be skipped (FR-013) |
| Output | `generate(nbits)` returns `nbits / 8` bytes in the design document's serialization; nbits a positive multiple of 32, otherwise `ValueError`; `words32(out)` splits it into 32-bit words as the vector files list them |
| Per-request limit | nbits above min(per-instantiation limit, 2¹⁹) raises `LimitExceeded`, with no output and no state change |
| Per-instantiation limit | output that would pass the limit raises `LimitExceeded`, with no output and no state change; a new nonce is needed; `reseed` never resets a counter |
| Per-key limit | a `Generator` is bound to the key of its first `instantiate`; a different key raises `KeyMismatch`; output under all its nonces counts against the per-key limit (`LimitExceeded` beyond it); `zeroize` ends the binding |
| Keys u | a parameter of the bound, stated in the security target; one object cannot observe it |
| Nonce reuse | the same key, nonce and personalization string give the same output; stated behaviour (T7), not detected |
| Lengths | a key other than 32 bytes, a nonce other than 16 bytes, or a personalization string or reseed input over its maximum raises `ValueError` |

The model never wraps, truncates or carries on past a limit (Edge Cases). Counters wider than
32 bits are held as 32-bit words with the design document's carry rule (re-decided feature-002
FR-002).

## Research duplex

```text
d = ResearchDuplex(variant_id)          # any supported variant with a capacity, reduced included
```

The same calls and rules as `Generator`, on any supported variant, for evidence on reduced
variants. It is not the production interface: it is named in the model's docstring as research
only, and `Generator` never delegates to it.

## Exceptions

| Exception | Base | Raised when |
|-----------|------|-------------|
| `VariantRefused` | `ValueError` | an unsupported or reduced variant at `Generator`; an unsupported value anywhere |
| `CallSequenceError` | `RuntimeError` | a call out of the order above |
| `LimitExceeded` | `ValueError` | a request or total beyond a limit |
| `KeyMismatch` | `ValueError` | `instantiate` with a key other than the bound one |
| `SelfTestError` | `RuntimeError` | the start-up self-test fails |

## Tests that hold the model to this contract (FR-058)

`tests/test_model_v3.py`: minimum, maximum and boundary values; all-zero and all-one keys and
nonces; single-bit keys; overflow and truncation; shift and rotation boundaries; reset,
zeroization and repeated instantiation; long runs (the 2²⁰-word digest); every exception above;
every supported configuration; every data-flow direction the design document states.
`tests/test_vectors_v3.py` and `tests/test_v3_transcription.py` cover the vectors and the second
transcription.
