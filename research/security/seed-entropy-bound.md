# Research Note: Seed-Entropy Bound on PhycoWeb-PRNG Security

Date: 2026-10-31.

**Status:** a finding of the security review ([security.md](../../security.md) 2.0, §9.2,
S1–S5). It was derived from the specification. No attack has been executed. Since
[constitution](../../.specify/memory/constitution.md) 1.2.0 (approved 2026-10-31), the
requirements in §5 are binding policy (Security Policy).

**Applies to:**
- `phyco-v2`: [design.md](../../specs/002-core-dynamics-redesign/design.md) 1.0, model
  `1260142d…`;
- `lut-v1`: same seed domain.

> Passing statistical batteries does not show cryptographic security. This generator must not be
> used to generate secrets; use an established cryptographic random-number generator for keys,
> nonces, tokens and salts.

## 1. Finding

**phyco-v2's seed is four 16-bit words, 64 bits in total. That caps any security level at 64 bits,
however large the internal state, which is below the 112-bit minimum for approved cryptographic
use.**

- **Why state size doesn't help.** The bound holds whatever the quality of the step function.
  The 272-bit state and the 256-step warm-up are both deterministic functions of the 64-bit seed.
- **Where the minimum comes from.** 112 bits is the minimum security strength for approved use
  (NIST SP 800-57 Part 1 Rev. 5, SP 800-131A Rev. 2). SP 800-57 accepts it for applying
  protection only through 2030; from 2031 the minimum is 128 bits. The constitution therefore
  sets 128 bits as the floor for any claim (FUT-SEC-1).
- **Classification** (security.md §9.1): a confirmed upper bound, derived from the
  specification. The generic attack below has not been run.

## 2. Derivation

1. **Seed domain.** Each seed value s₀…s₃ must be in 0…65535. Anything else is rejected:
   `ValueError` in the model, exit 2 from the C stream (`design.md` §3). That gives 2⁶⁴ seeds.
   Extra values add nothing: the Python models read only the first four values of a longer
   sequence (`seed[:4]`), and the C stream rejects a fifth seed argument.
2. **The initial state is a public function of the seed:**
   - P[k] = (s[k] << 16) | s[(k+1) mod 4];
   - D[k] = 0x00010000 << k, a constant;
   - phase_a = phase_b = 0, a constant;
   - then 256 warm-up steps, which are deterministic.

   The state at any step index t is therefore F_t(seed), and at most 2⁶⁴ distinct states exist
   at that index, out of 2²⁷² nominal ones.
3. **Part of the state is public.** The phase counters advance by fixed amounts (4 and 6, mod
   256), have period 128 and do not depend on the seed. Given t, 16 state bits and the whole food
   sequence are known.
4. **Three output words identify the seed.** Each step outputs one 32-bit word, computed from
   the four P words (`design.md` §5). If the map from seed to output behaves like a random
   function, k observed words leave about 2^(64 − 32k) wrong seeds that still fit: about one for
   k = 2, and 2⁻³² for k = 3. Three consecutive words are therefore expected to identify the seed
   uniquely.
5. **Exhaustive search.** For each candidate seed, run 256 warm-up steps plus 3 output steps (259
   steps) and compare. The total is at most 2⁶⁴ × 259 ≈ 2⁷² steps. Recovering the seed gives
   every earlier and every later output of that stream. Unpredictability and backtracking
   resistance both fail.
6. **Measured cost.**
   - The C stream runs 8.5 × 10⁷ steps/s on one core (feature 003,
     `reports/003-extended-batteries-calibration/dev/timing.json`, measured idle on 2026-10-29).
   - So 2⁶⁴ × 259 / 8.5 × 10⁷ ≈ 5.6 × 10¹³ core-seconds, about **1.8 million core-years**.
   - The search parallelizes perfectly and can be vectorized. The design also targets cheap,
     multiplierless hardware with one register-transfer step per update (`design.md` §7), so
     dedicated hardware would cut the cost by orders of magnitude.
   - Work of this size has been done in public. The 2017 SHA-1 collision took about 2⁶³ SHA-1
     computations.
7. **Precomputation (time–memory trade-off).** The state after warm-up depends only on the seed:
   there is no key, nonce or secret position. A Hellman trade-off therefore applies:
   - one precomputation of about 2⁶⁴ seed evaluations;
   - then about 2⁴³ work and 2⁴³ stored entries per target;
   - every later target of the same design is then cheap.
8. **Known and unknown position.** The bound is for the threat-model attacker T1, who knows the
   position, for example the first words after seeding. An unknown offset adds a search over the
   offset range R, about 2⁶⁴ · R steps in the simplest form, and data from many positions makes
   trade-off attacks cheaper.
9. **lut-v1** has the same seed domain, so the same bound applies. It also fails every
   statistical battery.

## 3. What a cryptographic claim would need

| Requirement | Source | phyco-v2 design 1.0 |
|-------------|--------|---------------------|
| Security strength of at least 112 bits through 2030 and 128 bits from 2031; at least 128 bits for any claim here | SP 800-57 Part 1 Rev. 5 (§5.6.3, Table 4, "Security strength time frames"); SP 800-131A Rev. 2; constitution 1.2.0 (FUT-SEC-1) | **at most 64 bits** (this note) |
| Entropy input with at least as many bits of entropy as the security strength, at instantiation | SP 800-90A Rev. 1 (DRBG instantiation) | 64-bit seed |
| Reachable secret state of at least twice the security strength | Babbage–Golić time–memory–data trade-off | 2⁶⁴ reachable states per step index |
| Nonce or IV to separate streams | SP 800-90A (nonce); stream-cipher practice | none |
| Reseed input, for prediction resistance | SP 800-90A | none |
| An approved mechanism, for FIPS 140-3 | FIPS 140-3; SP 800-90A | not possible for any custom design |

## 4. Consequences

- **No feature-002 or feature-003 result changes.** The statistical evidence is unaffected. The
  bound concerns only cryptographic claims, and none has been made.
- **Removing the bound is an algorithm change.** It needs a new seed (key) interface and
  seed-to-state mapping, and probably changes to the state and the step function. Under the
  constitution, that needs:
  - an approved spec (Principle VI);
  - an owner review (Principle VIII);
  - a new model ID and new golden vectors;
  - a new statistical evaluation on unused held-out sets;
  - requirements FUT-SEC-1 to FUT-SEC-9 (§5) carried in that spec (Security Policy).
- **Why it probably means another core redesign, not just a wider seed:**
  - In design 1.0, the seed fills only the four P words (128 bits); D and the phases start from
    constants.
    - A 128-bit key loaded into P alone would give 2¹²⁸ reachable states per step index. That
      meets the exhaustive-search bound for 128 bits.
    - D would still be public at reset, so the warm-up would have to do all the mixing.
    - Loading key material into D changes the vein dynamics that feature 002 tuned: the
      conductance classes, and the disruption rate required by feature-002 FR-005. That
      behaviour would have to be re-established.
  - The phase counters cannot carry key material without changing the food sequence, which is
    public by design.
  - Using several streams per key needs a nonce or IV. A prediction-resistance claim needs a
    reseed input fed from an entropy source. Neither exists.
  - Key and IV loading is a classic weak point of new stream ciphers. It needs its own analysis,
    including related-key and related-IV attacks.
- **The rest of the programme still applies.** Even with all of these changes:
  - the full validation programme (security.md §8–§15) still has to be carried out;
  - FIPS 140-3 approval stays impossible for a custom generator. A deployment that needs
    approval can only use Option B, an approved DRBG (security.md §21).

## 5. Future feature requirements (conditional; binding since constitution 1.2.0)

These apply **only if the owner decides to pursue a cryptographic claim, evaluation or
certification**. They are not scheduled, and they are not requirements of any current feature.
Since constitution 1.2.0 they are binding: no cryptographic claim, evaluation or certification
may be made or pursued for any model until they are met. The constitution's Security Policy
holds the governing wording and prevails if the two differ.

| ID | Requirement |
|----|-------------|
| FUT-SEC-1 | **Key entropy.** The generator MUST accept a key with at least 128 bits of entropy, and no claimed strength may be below 128 bits. No seed or key search, and no trade-off attack, may cost less than the claimed strength. |
| FUT-SEC-2 | **Reachable secret state.** At least twice the claimed strength, in bits, reachable through key and IV loading (time–memory–data trade-off). |
| FUT-SEC-3 | **Stream separation.** If more than one stream per key is allowed, a nonce or IV with defined uniqueness rules. |
| FUT-SEC-4 | **Reseeding.** If prediction resistance is claimed, a reseed input fed from a validated entropy source (SP 800-90B). |
| FUT-SEC-5 | **Initialization analysis.** Key and IV loading and the warm-up MUST be analysed for related-key, related-IV and weak-key behaviour before any claim. |
| FUT-SEC-6 | **Output limit.** The maximum output per key, and per key and IV, MUST be specified and covered by the analysis. |
| FUT-SEC-7 | **Re-validation.** A new model ID, golden vectors, a design freeze, and the complete statistical programme on unused held-out sets. Results from features 002 and 003 do not carry over. |
| FUT-SEC-8 | **Demonstration first.** Before a redesigned key interface is implemented, reproduce this bound on a reduced seed domain, for example with two seed words fixed (2³² candidates): recover the seed from three words and measure the cost per candidate (security.md §12.3, item 1). |
| FUT-SEC-9 | **Certification route.** State which scheme is targeted, for example independent academic cryptanalysis plus an AIS 20/31-style evaluation. FIPS 140-3 approval is not available to a custom generator; FIPS deployments need an approved DRBG (Option B). No model may be described as FIPS 140-3 approved or as an SP 800-90A DRBG. |

## 6. Suggested feature description, for `/speckit-specify` when the owner decides

```text
Cryptographic key interface for PhycoWeb-PRNG: replace the 64-bit seed with a key of at least
128 bits, plus a nonce for stream separation and, if claimed, a reseed input, so that seed
search no longer caps security at 64 bits. First demonstrate the current 64-bit bound on a
reduced seed domain. Treat the change as a core redesign (new model id), re-run the statistical
programme on unused held-out sets, and make no security claim before independent review.
Requirements FUT-SEC-1 to FUT-SEC-9: constitution Security Policy (1.2.0) and
research/security/seed-entropy-bound.md.
```

## 7. Where this finding is recorded

- `.specify/memory/constitution.md` 1.2.0: Security Policy (the binding wording of §5).
- `security.md` 2.2: §1.2, §4, §5, §6, §9.2 (S1–S5), §12.2, §20 and §20.1, §21, §22, §24.
- `README.md`: §1.1 status and §5.
- `reports/002-core-dynamics-redesign/phase-report.md`: addendum dated 2026-10-31.
- `specs/003-extended-batteries-calibration/tasks.md`: T041, T042 and T043 (the feature-003
  claims check, README update and final report).

## 8. Reproducing the numbers

- **The bound** follows from `design.md` §3–§5.
- **The throughput** comes from `reports/003-extended-batteries-calibration/dev/timing.json`.
  It was measured in WSL on an idle machine on 2026-10-29 with:
  `phyco_stream phyco-v2 56053 7029 30841 11050 --words 1000000000 > /dev/null`.
- **The arithmetic:** 2⁶⁴ × 259 / 85,375,305 s⁻¹ = 5.60 × 10¹³ s ≈ 1.77 × 10⁶ years.
