# PhycoWeb-PRNG Security Policy and Cryptographic Validation Strategy

- **Document:** `security.md`, version 2.21 (2026-11-09). The change history is in section 25.
- **Project:** PhycoWeb-PRNG.
- **Purpose:** This document does three things:
  - states the security policy for the generator;
  - defines the evidence-driven programme for deciding whether it could ever support a
    cryptographic claim;
  - records the evidence gathered so far in features 001–003.
- **Governed by:** the [constitution](.specify/memory/constitution.md) v1.3.0, specifically the
  Security Policy and Principles IV, V, VIII and IX. Where this document and the constitution
  differ, the constitution applies.
- **Status:** a research and validation plan. It is not a security certification. **No security
  property is claimed for any PhycoWeb-PRNG model.**

> **Do not use PhycoWeb-PRNG to generate keys, nonces, tokens, salts or any other secret.**
> PhycoWeb-PRNG, every model included, must not be used to generate secrets. Use an established
> cryptographic RNG instead: the operating system CSPRNG (for example `os.urandom` or
> `getrandom()`), or a NIST SP 800-90A DRBG seeded from a validated entropy source. Passing
> statistical tests does not show cryptographic security. That includes NIST SP 800-22, PractRand
> and TestU01.

------------------------------------------------------------------------

## 1. Security status at a glance

### 1.1 Models

| Model | Source | State | Seed | Statistical evidence | Cryptographic evidence | Claim level (section 15) | Role |
|-------|--------|-------|------|----------------------|------------------------|--------------------------|------|
| `float-v0` | `baseline/float-v0/` (archived; SHA-256 in `MANIFEST.json`) | floating-point food generator (`np.sin`, `np.cos`) | 4 × 16 bits | Feature-001 screening only, done with the defective `nistrng` 1.2.3 (see the erratum in `reports/001-integer-lut-perturbation/summary.md`) | none | L0; no claim | archive only |
| `lut-v1` | `phycoweb/model.py` (feature 001) | 144 bits: P and D 4 × 16 bits each, two 8-bit phases | 4 × 16 bits | Fails SP 800-22 (11 of 15 families, feature-002 attempt 1). Fails PractRand and TestU01 (feature 003, section 11.5) | none. The output exposes the low 8 bits of every vein value | L0; no claim | negative control |
| `phyco-v2` | `phycoweb/model_v2.py`, [`design.md`](specs/002-core-dynamics-redesign/design.md) 1.0 (feature 002) | 272 bits, of which the 16 phase bits are public | 4 × 16 bits = **64 bits** | Passed the pre-registered SP 800-22 attempt 1 (15 of 15 families, `heldout-1`). Passed the pre-registered PractRand/TestU01 attempt 1 (0 of 70 runs failing, `heldout-1` battery set; feature 003, section 11.4) | none | L0; no claim. It cannot reach L1 as specified: the 64-bit seed is below FUT-SEC-1 (S1–S3) | research candidate |
| `phyco-v3` | none yet: the design of feature 004, [`spec.md`](specs/004-crypto-architecture-v3/spec.md) | not specified yet | a key, not a seed; not specified yet | none | none | L0; no claim | feature 004 stopped at the selection, no candidate eligible; no model exists |
| `phyco-v4` | none yet: the design of feature 005, [`spec.md`](specs/005-crypto-architecture-v4/spec.md) | not specified until the selection | a 256-bit key and a 128-bit nonce, as targets (feature 005, D3) | none | none | L0; no claim | feature 005's spec approved on 2026-11-09, a second design round after feature 004's stop; no model exists |

### 1.2 What is and is not established for `phyco-v2`

- **Established**:
  - The algorithm is fully specified: every width, signedness, shift, wrap, comparison and
    update order is defined.
  - It is integer-only and multiplierless.
  - It is deterministic and identical on two platforms.
  - Three implementations written in this project agree bit for bit.
  - The pre-registered SP 800-22 protocol detected no statistical defect in 100 held-out
    sequences.
  - The pre-registered battery protocol (PractRand to 1 TiB; TestU01 SmallCrush, Crush and
    BigCrush in both bit orders) detected no statistical defect on 10 held-out seeds.
- **Bounded by the specification**: phyco-v2's seed is four 16-bit words, 64 bits in total.
  That caps any security strength at **64 bits**, however large the internal state (section 9.2,
  S1–S3). 64 bits is below the 112-bit minimum for approved cryptographic use (SP 800-57 Part 1,
  SP 800-131A) and below the constitution's 128-bit floor for any claim. Any cryptographic claim
  or certification would therefore need a new key interface, and probably another core redesign.
  The constitution's Security Policy (1.2.0) makes requirements FUT-SEC-1 to FUT-SEC-9
  (section 20.1) binding before any such claim. The derivation is in the research note
  [`research/security/seed-entropy-bound.md`](research/security/seed-entropy-bound.md).
- **Not established**: unpredictability, state-recovery resistance, backtracking resistance,
  prediction resistance (impossible as specified: there is no reseed input), side-channel
  behaviour, and hardware equivalence. No RTL exists.

### 1.3 Validation phases for `phyco-v2` (status 2026-11-01)

| Phase | Gate | Status | Evidence |
|-------|------|--------|----------|
| 0 Specification | frozen and unambiguous | **Met** for design 1.0, at the owner design review on 2026-10-28 (design SHA-256 `a1109bf1…`) | `design.md` §2–§6; tests `test_design_trace`, `test_widths_v2`, `test_purity_v2` |
| 1 Mathematical and structural analysis | review completed; critical defects resolved | **Started.** S12–S15 are recorded with proofs and committed scripts, not yet reviewed; the other facts in section 9.2 come from the specification and feature 002 | `research/security/` |
| 2 Reference implementation | independent implementations agree | **Partly met.** Three in-project implementations agree; none comes from outside the project; there is no VHDL | `vectors/`, `tests/v2_reference.py`, `reports/003-extended-batteries-calibration/streams/equivalence.json` |
| 3 Statistical validation | campaign completed; anomalies assessed | **In progress.** SP 800-22 PASS; positive control calibrated; PractRand/TestU01 attempt 1 PASS (owner review 2026-11-01); structural (level 3) tests not started | `reports/002-core-dynamics-redesign/`, `reports/003-extended-batteries-calibration/` |
| 4 Cryptanalysis | threat model and attack campaign completed | **Not started.** A draft threat model is in section 5 | — |
| 5 Hardware validation | RTL matches the model | **Not started.** RTL is pending, with the exceptions recorded as O1 in feature 002 | `design.md` §7 |
| 6 Independent evaluation | external review and reproduction | **Not started** | — |
| 7 Security qualification | claims supported by evidence | **L0, research candidate**; no claim (section 15) | this document |

To report a weakness, see section 23.

------------------------------------------------------------------------

## 2. Executive summary

This document defines a validation programme for a newly proposed pseudorandom number generator
(PRNG). It is applied here to PhycoWeb-PRNG.

The programme must answer five questions:

1. **Mathematical correctness:** Is the algorithm precisely defined and deterministic, with no
   implementation ambiguity?
2. **Statistical quality:** Does the output show detectable statistical biases or patterns?
3. **Cryptographic strength:** Can an adversary predict future output, reconstruct the internal
   state, or distinguish the output from uniformly random data?
4. **Implementation correctness:** Do the software and hardware implementations behave exactly
   as specified?
5. **Security assurance:** Is there enough independent evidence to justify a clearly scoped
   security claim?

**Statistical testing finds defects. It cannot establish unpredictability.**

- The Mersenne Twister (MT19937) passes most statistical batteries. Yet its entire internal state
  can be reconstructed from 624 consecutive 32-bit outputs, after which every later output is
  known.
- In 2022 NIST decided to revise SP 800-22. The revision is to clarify the suite's purpose, "in
  particular rejecting its use for assessing cryptographic random number generators" (section 6).

### 2.1 Governing principles

> 1. A generator that passes statistical tests is not thereby cryptographically secure.
> 2. An AI assistant can help discover weaknesses. Passing a test suite that an AI assistant
>    wrote or ran is not evidence of cryptographic security.
> 3. A claim is only as strong as its weakest stage. The seed, initialization, transition,
>    output and implementation all count.

All security conclusions must rest on:

- reproducible experiments;
- mathematical arguments;
- independently checked implementations;
- recorded review by qualified humans (constitution Principle VIII).

------------------------------------------------------------------------

## 3. Scope and security terminology

This plan covers a deterministic pseudorandom generator. Where relevant, it also covers a complete
random-bit-generator (RBG) construction, which adds an entropy source, initialization, reseeding
and output generation.

Do not conflate these concepts:

- **Statistical quality**: whether the output passes the stated tests at the stated sample size.
  It describes the tests, not what an adversary can do.
- **Indistinguishability (pseudorandomness)**: no efficient algorithm can tell the output from
  uniform random bits with a non-negligible advantage, provided the seed or key is secret and
  uniformly chosen.
- **Next-bit unpredictability**: given any prefix of the output, no efficient algorithm predicts
  the next bit with probability non-negligibly above 1/2. Yao (1982) showed that, for
  polynomial-time adversaries, this is equivalent to indistinguishability.
- **Security strength**, in bits: log₂ of the work of the best attack (SP 800-57 terminology).
  It can never exceed the entropy of the seed or key. Against time–memory–data trade-offs it can
  also not exceed about half the size of the secret state (section 12.2).
- **State compromise**: the attacker learns the full internal state at some time t.
- **Backtracking resistance** (SP 800-90A): a compromise at time t does not let the attacker
  recover or distinguish outputs produced *before* t. The AIS 20/31 term is *enhanced backward
  secrecy*.
- **Prediction resistance** (SP 800-90A): a compromise at time t does not let the attacker
  predict outputs produced *after the next reseed with sufficient fresh entropy*. It requires an
  entropy source and a reseed operation. A purely deterministic generator that is never reseeded
  cannot have it. The AIS 20/31 term is *enhanced forward secrecy*.
- **Forward and backward secrecy** (AIS 20/31 classes DRG.1 and DRG.2, as named in version 2.0
  of the functionality classes; section 6): future (respectively, earlier) outputs cannot be
  computed from observed outputs, without state compromise. The AIS "forward secrecy" is
  unrelated to forward secrecy in key exchange.
- **Entropy**: uncertainty in an input under a stated model. SP 800-90B measures **min-entropy**,
  H∞ = −log₂ max p. A deterministic algorithm creates no entropy. Its output never contains more
  entropy than its seed, which is at most 64 bits for every PhycoWeb-PRNG model.
- **Seed, key, nonce, personalization string**:
  - a seed initializes the state;
  - a key is a secret with full entropy for the claimed strength;
  - nonces and personalization strings separate instances.
  - The PhycoWeb-PRNG models have only a 64-bit seed. They have no separate key, nonce,
    personalization string or reseed interface.
- **Cryptographic qualification**: a conclusion supported by a defined security model, adequate
  analysis, implementation evidence and any applicable external validation.

Every claim must state:

- the exact property claimed;
- the configuration and model version;
- the attacker's capabilities;
- the data, time and memory limits;
- the security strength in bits;
- the assumptions, above all about the seed's entropy.

**Definitions for a keyed design.** No PhycoWeb-PRNG model has a key yet. A model meant to
support a claim states each property it seeks as a bound on an adversary's advantage. An
adversary A queries an oracle and outputs one bit. Its advantage is
Adv(A) = |Pr[A outputs 1, real generator] − Pr[A outputs 1, ideal oracle]|, a function of its
resources: time t (evaluations of the primitive), data σ (output bits, or calls of the
primitive), the number of keys u, and the nonces per key.

- **Keystream (PRG) security**: the real oracle generates output under a uniform secret key, for
  nonces that A chooses and never repeats; the ideal oracle returns uniform bits.
- **Multi-user security**: the same with u independent keys, A choosing the key of each query.
- **Backtracking resistance**: A also receives the full state after a forget or reseed call of
  its choice. The output produced before that call must stay indistinguishable from uniform.
- **Prediction resistance**, only with a reseed input (FUT-SEC-4): A receives the full state, a
  reseed with enough fresh min-entropy follows, and the output after it must stay
  indistinguishable from uniform.
- **Nonce misuse**: the behaviour on a repeated nonce is stated, never assumed safe. A keystream
  generator gives the same output for the same key and nonce.
- **The permutation assumption**: a mode proof bounds the advantage when its permutation is
  ideal. A claim built on it states only that no attack on the real permutation below the
  claimed strength is known, never that the permutation is ideal (section 12.6).

A claim of s-bit strength means that every attack within the stated limits needs work of about
2^s or more to reach a constant advantage. The claim states the bound ε(t, σ, u) that shows it.

**Claim template.** A claim, if one is ever approved (level L6, section 15), fills in every
field:

```text
Model:        model ID, design version, grid size, rounds; SHA-256 of the design
Property:     keystream security, multi-user security, backtracking resistance or
              prediction resistance
Attacker:     capabilities from section 5 (T1 to T11); the nonce rule
Limits:       output bits per key and nonce, and per key; number of keys u
Strength:     s bits, from the named theorem and its bound ε(t, σ, u), assuming no attack
              on the permutation below 2^s (best-attack register, section 12.6)
Assumptions:  the key is uniform and secret, with its stated entropy; the entropy source
              for reseeds, if any
Not claimed:  everything else, including FIPS 140-3 approval and any side-channel
              resistance that was not measured
Evidence:     the records of levels L1 to L5
```

------------------------------------------------------------------------

## 4. Security policy and permitted use

The constitution's Security Policy (version 1.3.0) applies. Its three general rules, verbatim:

- Real secret generation (keys, nonces, tokens, salts) MUST use an established cryptographic
  random-number generator (e.g., the operating system CSPRNG or a NIST SP 800-90A DRBG).
- PhycoWeb-PRNG MUST NOT be recommended or used for secret generation unless it has all of
  (a) a documented, defensible design rationale, (b) independent expert cryptographic review,
  and (c) evidence that it meets the security-strength requirements below, with all three
  recorded in the repository.
- Documentation MUST state this restriction wherever usage of the generator is described.

Its security-strength rules, in summary (the constitution's wording governs):

- No security level can exceed the seed's entropy. `phyco-v2` and `lut-v1` are bounded at
  64 bits.
- The specification of every new or changed model must state its seed or key entropy, its
  reachable secret state and the resulting bound.
- No artifact may state or imply a strength above a model's bound. Stating a bound, such as "at
  most 64 bits", reports a limitation and is not a claim.
- No cryptographic claim, and no evaluation or certification meant to support one, may be made
  or pursued until the model meets FUT-SEC-1 to FUT-SEC-9 (section 20.1) with recorded evidence.
  The claim then still needs the owner's approval.
- Cryptanalysis that looks for weaknesses is not restricted, and its results must be reported.
- Later amendments may make these rules stricter, never weaker.

In practice:

| Use | Allowed? |
|-----|----------|
| Research into the design, statistical behaviour and hardware mapping | yes |
| Reproducible test patterns and simulations where predictability is harmless | yes. For simulation work, an established non-cryptographic PRNG is usually the better choice |
| Keys, nonces, IVs, tokens, salts, passwords, session identifiers | **no** |
| Gambling, lotteries, sampling for audits or anything an adversary benefits from predicting | **no** |
| Seeding or reseeding another generator used for any of the above | **no** |

Lifting the restriction requires all of the following:

- the evidence in sections 8–15;
- requirements FUT-SEC-1 to FUT-SEC-9 met, with the evidence recorded (section 20.1);
- an owner-approved security claim (Principle VIII, gate 3);
- an independent expert review recorded in the repository.

No such claim exists or is planned for the current design, which is bounded at 64 bits
(section 9.2).

------------------------------------------------------------------------

## 5. Threat model (draft for Phase 4)

**Kerckhoffs' principle applies.** The algorithm, the constants and the lookup table are public
(this repository). Only the seed and the state can be secret.

**Assets:**

- outputs the attacker has not yet seen;
- earlier outputs;
- the seed, or the key of a keyed design;
- the internal state;
- the integrity of the output, meaning it cannot be forced or biased.

| ID | Attacker capability | Typical goals |
|----|---------------------|---------------|
| T1 Known output | Sees a contiguous or sparse output stream, and knows the step index modulo 128 (the phase period) | predict, recover the seed or state, distinguish |
| T2 Related seeds | Sees outputs for seeds with known relations: counters, rotations of the four seed words, single-bit differences | distinguish, recover the seed |
| T3 State compromise | Learns the full state once | recover earlier outputs, predict later ones |
| T4 Implementation access | Timing, power, EM or fault injection on a software or FPGA implementation | leak or force the state |
| T5 Seed influence | Can choose or bias the seed, for example through weak seeding | force degenerate or low-entropy states |
| T6 Chosen nonces (keyed design) | Chooses the nonce and personalization string of each instantiation; nonces are unique per key | distinguish, recover the key |
| T7 Nonce misuse (keyed design) | Repeats a nonce under one key, by error or by force | distinguish, recover the key or the state |
| T8 Many users (keyed design) | Attacks u keys at once and wins if any one falls | recover any one key, with less work per key |
| T9 Chosen absorbed input (keyed design) | Chooses or influences input absorbed into the state: personalization, additional input, reseed input | force state collisions or weak states |
| T10 Compromise around forget and reseed (keyed design) | Learns the full state just before or just after a forget or reseed call | recover earlier output, predict later output |
| T11 Quantum (optional) | Has a quantum computer: Grover search of a k-bit key in about 2^(k/2) evaluations, and quantum queries where the oracle allows them | recover the key, distinguish |

T6–T11 were added in version 2.7 for a keyed design, which does not exist yet: `phyco-v2` has no
key, nonce or reseed input. A spec that introduces a key interface adopts them, or states why
one does not apply. Feature 004 adopts T11 for `phyco-v3`, and feature 005 for `phyco-v4`, only as
single-target key search, k/2 ≥ s, which a 256-bit key meets with equality and no margin at
s = 128, since its 128-bit target is a
classical one; multi-target quantum key search, quantum attacks on the capacity through queries to
the public permutation and every other quantum generic attack are excluded for that reason and left
open for the cryptanalysis stage, roadmap row 5a.2, which feature 004's documents call feature 005
and which is feature 006 since version 2.18 (feature-004 FR-008).

**Generic results** that hold for `phyco-v2` as specified (no experiment needed):

- **Exhaustive seed search** succeeds against T1 in at most 2⁶⁴ trials.
  - Each trial is 256 warm-up steps plus a few output steps, about 2⁷² steps in all.
  - At the measured 8.5 × 10⁷ steps/s of the C stream (`reports/003-extended-batteries-calibration/dev/timing.json`),
    that is about 1.8 million core-years.
  - That cost is within reach of a well-resourced attacker with dedicated hardware, and the
    design is meant to be cheap in hardware.
- **Time–memory trade-off** (Hellman, 1980): the initial state is a fixed function of the
  64-bit seed. After a one-time precomputation of about 2⁶⁴ seed evaluations, each target costs
  about 2⁴³ evaluations with about 2⁴³ stored entries.
- **No prediction resistance**: there is no reseed input.
- **Backtracking resistance is unknown**. The step function is not one-to-one (S13), but the
  states that merge differ only locally, so a state compromise may still reveal earlier output.
  This has not been analysed (S9).

------------------------------------------------------------------------

## 6. Standards and technical references

The programme follows established standards, not criteria invented for this algorithm. Status was
checked on 2026-10-31 against the NIST CSRC pages and, for the BSI and ISO rows, the publishers'
pages. The ECRYPT site was unreachable that day, so the eSTREAM row rests on secondary sources.

| Reference | Status | Role | What it means here |
|-----------|--------|------|--------------------|
| NIST SP 800-90A Rev. 1 | Final, June 2015. Rev. 2 initial preliminary draft (call for comments) released 4 September 2025, comments closed 4 November 2025. It proposes an XOF (SHAKE) based DRBG and alignment with SP 800-90C | Approved DRBG mechanisms: Hash_DRBG, HMAC_DRBG, CTR_DRBG. Dual_EC_DRBG was withdrawn in Rev. 1 | A custom generator cannot be an approved DRBG. For secrets, use one of these mechanisms |
| NIST SP 800-90B | Final, January 2018. NIST noted two errata on 29 May 2025, for a future update | Entropy sources: min-entropy estimation (IID and non-IID tracks), restart tests, health tests (repetition count, adaptive proportion) | PhycoWeb-PRNG is deterministic. It is not an entropy source and cannot be validated as one |
| NIST SP 800-90C | Final, September 2025 | Complete RBG constructions: RBG1, RBG2, RBG3, RBGC | Defines how an approved RBG combines an entropy source and a DRBG. A bio-inspired component would add no assurance to such a construction (section 21) |
| NIST SP 800-22 Rev. 1a | Final, April 2010. On 19 April 2022 NIST decided to revise it. The revision is to clarify its purpose, "in particular rejecting its use for assessing cryptographic random number generators"; drafting had not started when the decision was announced | Statistical tests | Used here only to detect defects. This project's calibration and DFT cross-check show its limits (section 11.4) |
| NIST FIPS 140-3 | Approved March 2019 | Cryptographic module validation (CMVP) | An RBG in a validated module must use an approved DRBG, and its entropy source must be validated (ESV programme). A custom generator cannot be approved |
| NIST SP 800-57 Part 1 Rev. 5; SP 800-131A Rev. 2 | Final (2020; 2019) | Security strengths; algorithm transitions | 112 bits is the minimum security strength for approved use, accepted for applying protection only through 2030; from 2031 the minimum is 128 bits. The constitution's floor for any claim is 128 bits (FUT-SEC-1). `phyco-v2` is bounded at 64 |
| BSI AIS 20 / AIS 31 | German Common Criteria methodology for RNGs. The current mathematical-technical reference is version 3.0 of the functionality-class proposal, dated 17 September 2024 | Functionality classes DRG.1–DRG.4 for deterministic RNGs, PTG.1–PTG.3 for physical true RNGs and NTG.1 for non-physical true RNGs, as named in version 2.0 (2011). Version 3.0 was not read here, and a conference comparison of the current classes names only DRG.2–DRG.4, PTG.2, PTG.3 and NTG.1; read it before FUT-SEC-9 is answered | DRG.3 (enhanced backward secrecy) or DRG.4 (adds enhanced forward secrecy through reseeding) would be the bar for any future claim |
| ISO/IEC 18031 | International standard | Random bit generation | International counterpart to the SP 800-90 series |
| NIST SP 800-232 | Final, 13 August 2025 | Ascon-based lightweight cryptography: Ascon-AEAD128, Ascon-Hash256, Ascon-XOF128 and Ascon-CXOF128, all built on one 320-bit permutation | Comparison reference: a standardized permutation-based design for constrained hardware, the kind of architecture recommended for a redesign (section 21). It is not an RBG standard |
| eSTREAM portfolio (ECRYPT) | Final portfolio 2008, revised in September 2008. Not a standard | Stream ciphers selected after four years of public analysis. Profile 1 (software, 128-bit keys): HC-128, Rabbit, Salsa20/12, SOSEMANUK. Profile 2 (hardware, 80-bit keys): Grain v1, MICKEY 2.0, Trivium | Comparison reference for hardware keystream generators, and for how long public review takes |
| ISO/IEC 29192 | Part 3 (stream ciphers): edition 1, 2012, last confirmed in 2024 | Lightweight cryptography. Part 3 specifies the keystream generators Enocoro and Trivium | Comparison reference for lightweight keystream generators |
| BSI TR-02102-1 | Version 2026-01 | Recommended cryptographic mechanisms and key lengths, updated yearly | Comparison reference for key lengths and mechanism choices |
| TestU01 1.2.3 (L'Ecuyer and Simard, ACM TOMS 33(4), 2007) | Used in feature 003 | SmallCrush, Crush, BigCrush | Licence allows non-commercial research use only. Not redistributed here |
| PractRand 0.96 (C. Doty-Humphrey) | Used in feature 003 | Long-stream testing to 2⁴⁰ bytes | Public domain / free use |
| NIST STS 2.1.2 | Used as the oracle in features 002–003 | Reference SP 800-22 implementation | Our harness `sp80022` matches it (section 11.2) |

Official references:

- NIST SP 800-90A Rev. 1: https://csrc.nist.gov/pubs/sp/800/90/a/r1/final
- NIST SP 800-90A Rev. 2 (initial preliminary draft): https://csrc.nist.gov/pubs/sp/800/90/a/r2/iprd
- NIST SP 800-90B: https://csrc.nist.gov/pubs/sp/800/90/b/final
- NIST SP 800-90C: https://csrc.nist.gov/pubs/sp/800/90/c/final
- NIST SP 800-22 Rev. 1a: https://csrc.nist.gov/pubs/sp/800/22/r1/upd1/final
- Decision to revise SP 800-22 Rev. 1a (2022): https://csrc.nist.gov/news/2022/decision-to-revise-nist-sp-800-22-rev-1a
- NIST FIPS 140-3: https://csrc.nist.gov/pubs/fips/140-3/final
- NIST SP 800-232: https://csrc.nist.gov/pubs/sp/800/232/final
- BSI TR-02102, all parts: https://bsi.bund.de/dok/TR-02102-en
- BSI functionality classes for random number generators, version 3.0 (2024):
  https://bsi.bund.de/SharedDocs/Downloads/EN/BSI/Certification/Interpretations/AIS_31_Functionality_classes_for_random_number_generators_e_2024.html
- ISO/IEC 29192-3:2012: https://www.iso.org/standard/56426.html

Two cautions:

- **The deployment determines the applicable standard.** Compliance must be checked against
  the current revision the deployment needs. Citing a standard does not establish compliance.
- **Being standardized is not a proof of security either.** Dual_EC_DRBG was standardized and
  later withdrawn.

------------------------------------------------------------------------

## 7. Validation lifecycle and gates

The phases run in sequence, each with an explicit acceptance gate. A failed or unresolved
earlier gate blocks every claim that depends on it.

| Phase | Focus | Primary gate |
|-------|-------|--------------|
| 0 | Specification, design and design rationale | Specification frozen and unambiguous. For a model meant to support a claim, also a complete design rationale (section 8) and an external design review before the freeze (recommended; see below) |
| 1 | Mathematical and structural analysis | Review completed; critical defects resolved |
| 2 | Reference implementation verification | Independent implementations agree with the specification |
| 3 | Statistical validation | Pre-registered campaign completed; anomalies assessed |
| 4 | Cryptanalysis | Threat model and attack campaign completed; findings assessed |
| 5 | Hardware validation | Hardware shown to implement the specified algorithm |
| 6 | Independent security evaluation | External review and reproduction completed |
| 7 | Security qualification | Claims supported by evidence; limitations stated |

Passing a gate means only that its stated criteria were met. It does not establish any other
property.

**External design review (recommended).** A flaw that a cryptographer would see at once can
otherwise surface only after implementation and battery runs. Before the design freeze of any
model meant to support a cryptographic claim, an independent cryptographer should review its
specification and design rationale, and the review should be recorded in the feature's *Review
& Approval* table. The constitution does not yet require this; an optional amendment would add
it to Principle VIII (research note
[`crypto-redesign-strategy.md`](research/security/crypto-redesign-strategy.md) §9.1, and
[`next.md`](next.md)). Until then, a freeze without it is recorded as such.

**How gates work in this repository.** Each phase of work is a Spec Kit feature: specify, plan,
tasks, implement. Each gate is a recorded owner approval in that feature's *Review & Approval*
table, as required by Principle VIII. So far these gates have been recorded:

- spec, plan and task approvals;
- tool downloads;
- design reviews;
- design freezes and battery freezes;
- result reviews;
- final reviews.

------------------------------------------------------------------------

## 8. Phase 0: Formal algorithm specification

The specification must define:

- the complete internal state, with dimensions and bit widths;
- initialization and seeding;
- the state-transition equations and their update order;
- output extraction and formatting;
- the nonlinear operations;
- integer overflow, truncation and signedness;
- shift (arithmetic or logical) and rotation semantics;
- comparison semantics (signed or unsigned);
- reset and reseed behaviour, and invalid-state handling;
- any dependence on external entropy;
- parameter constraints, supported configurations, output rate and limits.

For a bio-inspired network of interacting nodes, it must also define:

1. how each node computes its next state;
2. how neighbouring nodes exchange information;
3. whether updates are synchronous, and whether update order matters;
4. whether the network can enter absorbing or repeating states;
5. whether different initial states converge to common attractors;
6. whether the output reveals information about node states;
7. how food signals and other inputs are represented and bounded;
8. whether any floating-point operation exists.

**Acceptance criteria:**

- Two independently developed implementations interpret the specification identically.
- Every security-relevant operation has exact semantics.
- No remaining ambiguity affects the transition, output, initialization or analysis.

**Status in this repository**

| Item | `lut-v1` (feature 001) | `phyco-v2` (feature 002) |
|------|------------------------|--------------------------|
| Exact semantics | spec FR-007/FR-008 (explicit `wrap32`, floor arithmetic shift, unsigned output) | `design.md` §2 (width, signedness and wrap of every register), §4 (numbered update steps), §6 (allowed operations) |
| Synchronous update | yes | yes. All primed values are computed from registered values (`design.md` §4, step 7) |
| Floating point | removed: an integer lookup table replaces `np.sin`/`np.cos` | none; checked by the AST purity test |
| Food input bounds | 16-bit table values | 16-bit table values, sign-extended to 32 bits |
| Absorbing states, attractors | disruption fires on about 99.5% of steps (degenerate) | v001 without peristalsis collapses to the periodic attractor; v005 is not analysed beyond the edge seeds (S10) |
| Version identity | `MODEL_ID = "lut-v1"`, golden vectors | `MODEL_ID = "phyco-v2"`; design 1.0 and model SHA-256 values in every freeze |

**Specification gaps that matter for security:**

- there is no key, nonce, personalization or reseed interface;
- the seed domain is only 64 bits;
- no output limit per seed is defined;
- the `design.md` status line still reads "awaiting owner design review". The approval is
  recorded in `spec.md`, and the line is left unchanged because editing it would change the
  frozen hash (feature-002 open issue O5);
- there is no design rationale in the sense below.

**Design rationale (Security Policy (a)).** The specification of any model meant to support a
claim comes with a design rationale that states:

- the security target, the threat model and the claim template (sections 3 and 5);
- the mode, the theorem it relies on, and how each precondition of the theorem is met;
- the role of every component and why it is there, including what the slime-mold mapping does
  and does not contribute;
- the sources of nonlinearity and their proven bounds;
- diffusion in both directions;
- every constant, with the rule that generates it;
- the round-count rule and the resulting margin;
- the known limitations, and the attacks the design was built to resist.

`phyco-v2` has no such rationale: `design.md` §8 explains why it is slime-mold dynamics
(feature-002 FR-007), not why it would resist attack.

------------------------------------------------------------------------

## 9. Phase 1: Mathematical and structural analysis

The aim is to find structural properties that undermine unpredictability.

### 9.1 What to analyse

**State space:**

- nominal state bits;
- reachable states, where tractable;
- invalid and absorbing states;
- transition collisions and convergence;
- cycle lengths;
- whether the transition is a bijection;
- whether the output function reduces the effective security of the state.

A nominal state of 2ⁿ states implies neither a period of 2ⁿ nor n bits of security.

**Nonlinearity and algebra:**

- algebraic degree;
- linear approximations;
- differential behaviour;
- correlation between state and output;
- decomposition into weakly coupled parts.

**Reconstruction:** whether outputs reveal node states, initial conditions, later outputs or
equivalent states.

**Structural weaknesses:**

- repeated patterns and short cycles;
- symmetries and invariant subspaces;
- weak initialization;
- predictable attractors;
- slowly varying state;
- unintended relations between node updates.

Classify every finding as one of:

- **Confirmed vulnerability**: proved, or reproduced by experiment.
- **Strong theoretical concern**: a compelling issue that needs further analysis.
- **Unverified hypothesis**: plausible, but not demonstrated.
- **No weakness identified within the analysis performed**: a statement limited to that scope,
  never proof that no weakness exists.

### 9.2 Known structural facts and concerns (`phyco-v2`, design 1.0)

None of these has been through the Phase 1 review. The classification says how well each one is
supported.

| ID | Fact or concern | Basis | Classification |
|----|-----------------|-------|----------------|
| S1 | The seed is 4 × 16 bits = 64 bits. The initial state is a fixed function of it: P comes from the seed words, while D and the phases are constants. At any step index, at most 2⁶⁴ states are reachable out of 2²⁷². | `design.md` §3 | Confirmed (by specification) |
| S2 | The phase counters do not depend on the seed and have period 128. Given the step index, 16 of the 272 state bits and the whole food sequence are public. | `design.md` §2, §4 steps 1–2 | Confirmed (by specification) |
| S3 | Hence security strength against T1 is at most 64 bits: exhaustive seed search takes about 2⁷² steps, and a time–memory trade-off amortizes it (section 5). | S1, `dev/timing.json`, [`research/security/seed-entropy-bound.md`](research/security/seed-entropy-bound.md) | Confirmed upper bound (generic attack, not executed) |
| S4 | There is no key, nonce, personalization or reseed input, so prediction resistance is impossible as specified. | `design.md` §3 | Confirmed (by specification) |
| S5 | Each output word is a 32-bit function of the four P words; D is never output directly. Since 64 seed bits fix the state, about three consecutive words are expected to determine the seed. | `design.md` §5 | Confirmed (counting argument) |
| S6 | Veins change slowly (D′ = D + \|Q\|/4 − D/16), and their top two bits choose the flux shift. Slowly varying control bits are a classic target for guess-and-determine attacks. | `design.md` §4 steps 3–4 | Unverified hypothesis |
| S7 | Several constants are rotation-structured. 0x5A5A5A5A is unchanged by 8-bit rotations, and 0xA5A5A5A5 = rotl(0x5A5A5A5A, 4). The D reset values 0x00010000 << k are 1-bit rotations of each other. Rotational cryptanalysis of ARX designs (Khovratovich and Nikolić, 2010) exploits such constants. | `design.md` §2, §4 | Unverified hypothesis |
| S8 | Neighbouring seeded pressures share halves: P[k] = (s[k] << 16) \| s[k+1]. Rotating the seed words rotates P. The D reset values, per-node rotations and food positions break the symmetry, but related-seed behaviour is untested. | `design.md` §3 | Unverified hypothesis |
| S9 | It is unknown whether the step function is a bijection. If it is not, states can merge and cycles can be shorter. If it is, one state compromise reveals every earlier output, so there is no backtracking resistance either way unless shown otherwise. S13 settles it: the step is not a bijection. | S13 | Answered: not a bijection (S13) |
| S10 | The only cycle evidence is for the all-equal edge seeds: no period ≤ 2¹⁵ in the first 2¹⁶ words. | `design.md` §9 | Limited evidence |
| S11 | Without the peristaltic rotation and vein-tone feedback (variant v001), the network locks onto the periodic food forcing and fails all 15 SP 800-22 families. The statistical quality comes from two added ARX terms, not from the slime-mold dynamics alone. | `design.md` §8–§9, `research/002/runs.jsonl` | Confirmed (experiment) |
| S12 | Conductance classes 2 and 3 are in effect unused. Every vein value stays in 0…2³¹, so class 3 is unreachable and class 2 can occur only at exactly D = 2³¹, for one step. SHIFT = 4 never applies and the class is in effect bit 30 of D. Bit 31 of D is set only in that edge case, so the vein-tone XOR in effect never reaches bit 31 of T[k], which the rotation moves to bit 4, 10, 18 or 26 of P′[k]. For S6 this leaves one effective control bit per vein, not two. Details below the table. | `design.md` §4 steps 3–5, [`research/security/vein-class-census.json`](research/security/vein-class-census.json) | Confirmed (proof and experiment) |
| S13 | The step function is not one-to-one, so distinct states merge. (a) The vein decay D − (D >> 4) maps 16m + 15 and 16m + 16 to the same value, so two states that differ only there have the same successor; about 41% of states have such a partner. (b) When all four veins are in class 1, adding (2, −2, 2, −2) to the pressures leaves every transport sum T[k] unchanged, and the successors coincide in about 32% of those states. This settles S9. The merged states differ only locally, so the merging is not evidence of backtracking resistance. Details below the table. | `design.md` §4 steps 3–6, [`research/security/step-probes.json`](research/security/step-probes.json) | Confirmed (proof and experiment) |
| S14 | The vein values stay close to 2³⁰: after the warm-up every D measured lay between 0.69 × 2³⁰ and 1.49 × 2³⁰. Bit 31 of D was never set, bit 30 was set in 90.6% of values, and bits 29 to 27 in 9.4%, 11.5% and 39.5%; bit 29 was always the complement of bit 30. The vein-tone XOR of step 5 therefore changes the top five bits of T[k] (bits ROT[k] − 1 to ROT[k] − 5 of P′[k]) rarely or predictably, and two unrelated states differ in about 47.7% of their 256 state bits, not 50%. Details below the table. | `design.md` §4 steps 4–5, [`research/security/step-probes.json`](research/security/step-probes.json) | Confirmed (experiment) |
| S15 | The bound of S12 holds from every starting state, not only from the reset values. While D > 2³¹ (class 2 or 3), the decay D >> 4 is at least 2²⁷ and the growth A >> 2 at most 2²⁶, so D falls by at least 2²⁶ per step and never wraps. Every vein is at most 2³¹ within 16 steps, and S12 then keeps it there. Any 2×2 design that keeps the design-1.0 vein update, however its key is loaded, therefore has at most 2¹²⁸ · (2³¹ + 1)⁴ ≈ 2²⁵² secret states after 16 steps, below the 2²⁵⁶ that FUT-SEC-2 needs for a 128-bit claim; the range measured for S14 suggests about 2²⁴⁷. This conflicts with FUT-GRID-2 at 2×2 (section 20.1). The bound of S1 for `phyco-v2` itself is unchanged. Details below the table. | `design.md` §4 steps 3–4, S12, [`research/security/vein-descent.json`](research/security/vein-descent.json) | Confirmed (proof and experiment) |

**S12 in detail.** In class c = D >> 30 the flux is the pressure difference shifted right by
SHIFT[c] = c + 1, so |Q| ≤ 2^(30−c). The growth term A >> 2 is then at most 2^(28−c), against a
decay of D >> 4. Since D − (D >> 4) never decreases as D grows, the top of each class bounds the
next value:

- from class 0 (D < 2³⁰): D′ ≤ 0x4C000000, about 1.19 × 2³⁰, in class 1;
- from class 1 (2³⁰ ≤ D < 2³¹): D′ ≤ 2³¹, with equality only when D = 2³¹ − 1 and Q = −2²⁹;
- from D = 2³¹ (class 2): the decay, 2²⁷, exceeds any class-2 growth (at most 2²⁶), so
  D′ ≤ 0x7C000000, back in class 1.

All four reset values (0x00010000 << k) are in class 0, so by induction 0 ≤ D ≤ 2³¹ at every
step. D never wraps modulo 2³², and bit 31 of D is set only when D = 2³¹ exactly. Reaching that
edge needs |Q| at or near its maximum for a long run of consecutive steps; the largest D in the
census below was about 1.49 × 2³⁰. Hence SHIFT = 3 applies at most in that edge case and
SHIFT = 4 never, so the 4:1 shift select of step 3 is in effect 2:1. Outside the edge case the
vein-tone XOR of step 5 leaves bit 31 of T[k] unchanged, and the rotation by ROT[k] moves that
bit to bit ROT[k] − 1 of P′[k] (bits 4, 10, 18 and 26), before the disruption XOR.
THRESH = 0x4D000000, about 1.20 × 2³⁰, lies inside class 1.

The cause is the direction of the shift table. The shift grows with the class, so a larger D gets
a smaller flux and therefore less growth: a negative feedback that bounds D. `design.md` calls D
the vein thickness (conductance) and describes the flux as discretized Tero et al. flow, in which
flux grows with conductance, yet its step 3 calls the low class, which holds the smallest D, a
"thick vein". The redesign must state which direction is intended
([research note §5.3](research/security/seed-entropy-bound.md)).

The census ([`research/security/vein_class_census.py`](research/security/vein_class_census.py),
run on 2026-10-31 on Windows with Python 3.10.11, model SHA-256 `1260142d…`) used the first
development seed and the two all-equal edge seeds, 200,000 steps each after the 256-step warm-up,
with four veins per step: 2.4 million vein values.

| Seed | Class 0 | Class 1 | Classes 2 and 3 | Largest D | Class changes |
|------|---------|---------|-----------------|-----------|---------------|
| 56053 7029 30841 11050 | 75,445 | 724,555 | 0 | 0x5E4C6AD1 (1.47 × 2³⁰) | 96,215 |
| 0 0 0 0 | 75,003 | 724,997 | 0 | 0x5D7956A1 (1.46 × 2³⁰) | 95,182 |
| 65535 65535 65535 65535 | 75,014 | 724,986 | 0 | 0x5F82634F (1.49 × 2³⁰) | 95,792 |

In total, class 0 held 9.4% of the vein values and class 1 90.6%, and bit 31 was never set. A
vein's class changed about once every 8 steps: class-0 visits lasted about 1.6 steps on average
and class-1 runs about 15.

**S13 in detail.** Two separate mechanisms make the step many-to-one.

*(a) Vein decay.* Step 4 computes D′ = D + (A >> 2) − (D >> 4). The map f(D) = D − (D >> 4) is
not one-to-one: f(16m + 15) = 15m + 15 = f(16m + 16). Take two states that differ only in one
vein, with the values 16m + 15 and 16m + 16. Step 3 reads only the class D >> 30, which is the
same for both unless the pair straddles a class boundary. Step 6 compares D with
THRESH = 0x4D000000, a multiple of 16, so the comparison never separates the pair. Every other
input is equal, so the successors are equal. A vein has such a partner when its low four bits
are 0 or 15, so about 1 − (7/8)⁴ = 41.4% of states have at least one.

*(b) Transport zero mode.* In class 1 the flux is Q[k] = asr(P*[k] − P*[k+1], 2). Adding 2v, with
v = (1, −1, 1, −1), to the pressures changes every pressure difference by ±4, so every Q[k]
changes by exactly ±1. The transport sum T[k] = P*[k] − Q[k] + Q[k−1] then changes by
+2 − 1 − 1 = 0 for even k and by −2 + 1 + 1 = 0 for odd k, unless a difference wraps past ±2³¹.
The successors are equal when, in addition, every growth term A >> 2 = |Q| >> 2 is unchanged:
about (3/4)⁴ = 31.6% of all-class-1 states. Over the integers the class-1 transport is
T = (I − L/4)P*, where L is the Laplacian of the 4-node ring. Its eigenvalues are 1, ½, ½ and 0,
so it is a diffusion step with a zero mode. In class 0 the transport I − L/2 has the two zero
modes (1, 0, −1, 0) and (0, 1, 0, −1); these were not measured. Any larger grid whose transport
keeps this form keeps zero modes, for example a pattern alternating along one axis of an
even-sided torus.

The probes ([`research/security/step_probes.py`](research/security/step_probes.py), run on
2026-10-31 on Windows with Python 3.10.11, model SHA-256 `1260142d…`) used the first development
seed after the 256-step warm-up:

| Probe | States | Result |
|-------|--------|--------|
| (a) every vein of 5,000 states set to the pair 16m + 15, 16m + 16 | 20,000 pairs | 20,000 identical successors; 42.0% of the states had a partner (41.4% expected) |
| (b) P and P + 2v, all veins in class 1, in 100,000 steps | 67,150 states | T unchanged in all; 21,219 (31.6%) identical successors (31.6% expected); the rule above predicted every case |

Consequences: the step is not a bijection (S9), so the functional graph has trees that feed into
cycles, and S10 remains open. A merged predecessor differs only in one vein's low bits or by a
±2 pressure pattern, so it is close to the true predecessor; whether that makes backtracking any
harder has not been analysed. A design that relies on a one-to-one step must show it at every
grid size (FUT-SEC-2 and FUT-GRID-1). The feature-002 phase report (§7) calls the step
"invertible-looking ARX"; that description is wrong.

**S14 in detail.** By S12 every D stays in 0…2³¹. The decay pulls D towards a level set by the
growth term, and the growth term is bounded by the class-1 flux, so D settles in a band around
2³⁰. The same probe script took 200,000 steps from each of the three census seeds (2.4 million
values):

| Bit of D | 31 | 30 | 29 | 28 | 27 | 26 to 0 |
|----------|----|----|----|----|----|---------|
| Ones | 0.0% | 90.6% | 9.4% | 11.5% | 39.5% | 49.9–50.0% |

The P words showed 49.9–50.1% ones in every bit. Two independent states differ in a bit with
ones-frequency p with probability 2p(1 − p). Over the 128 bits of P and the 128 bits of D this
gives 47.7%. A one-bit seed change (64 flips on each of the first three development seeds)
reached the same 47.7% of state bits from step 4 onwards, and changed about 50% of the output
bits from step 2; the warm-up is 256 steps. So the shortfall from 50% is the vein bias, not slow
diffusion. Because the vein-tone XOR of step 5 rarely changes the top bits of T[k], those bits
of P′[k] depend on D far less than the other bits do.

**S15 in detail.** The induction of S12 starts from the reset values, which are all in class 0. A
keyed design that keeps the design-1.0 vein update could start anywhere, for example with key
material loaded into D, so the bound must hold from every state. It does. The growth of each vein
depends only on its own class (step 3 reads c[k] = D[k] >> 30), so each vein is bounded on its
own:

- class 2 above 2³¹ (2³¹ < D < 3 × 2³⁰, SHIFT = 3): growth at most 2²⁶, decay at least 2²⁷;
- class 3 (D ≥ 3 × 2³⁰, SHIFT = 4): growth at most 2²⁵, decay at least 3 × 2²⁶;
- so while D > 2³¹, D − (D >> 4) ≤ D′ ≤ D − 2²⁶: D falls by at least 2²⁶ per step and never
  wraps modulo 2³².

From D ≤ 2³² − 1 every vein is therefore at most 2³¹ within 32 steps. A sharper bound iterates
the largest value that any vein above 2³¹ and at most x can reach in one step; within a class the
next value never decreases as D grows, so the top of each class gives it. From x = 2³² − 1 this
envelope falls to 0x7EFA55B3, below 2³¹, in 16 steps, so every vein from every start is at most
2³¹ within 16 steps. From then on the induction of S12 keeps every D in 0…2³¹.

The check ([`research/security/vein_descent.py`](research/security/vein_descent.py), run on
2026-10-31 on Windows with Python 3.10.11, model SHA-256 `1260142d…`) ran the reference model
from 2,000 arbitrary states with every vein above 2³¹, five of them fixed edge cases, for 64
steps each, and 100 of them for 1,000 steps more:

| Check | Result |
|-------|--------|
| Every step of a vein above 2³¹ gave D − (D >> 4) ≤ D′ ≤ D − 2²⁶ | 62,982 of 62,982 |
| Steps until all four veins were at most 2³¹ | at most 14 (bound: 16) |
| Steps after that with a vein above 2³¹ | 0 of 205,270 |

Consequences. A 2×2 ring with one 32-bit pressure and one 32-bit vein per node has exactly 256
secret bits. After 16 steps each vein takes at most 2³¹ + 1 values, so the secret state takes at
most 2¹²⁸ · (2³¹ + 1)⁴ ≈ 2²⁵² values, whatever the key interface. The range measured for S14,
about 0.80 × 2³⁰ values per vein, suggests about 2²⁴⁷, and the merging of S13 can only shrink
the set further. FUT-SEC-2 needs at least 2²⁵⁶ reachable secret states for a 128-bit claim, so
the design-1.0 vein update rules out a 128-bit claim at 2×2. With two 32-bit words per node, 2×2
leaves no slack under any update: every state would have to be reachable, and a duplex mode with
a 256-bit capacity would have no rate left. FUT-GRID-2 requires FUT-SEC-1 and FUT-SEC-2 at every
supported size, including the smallest, so the two requirements conflict at 2×2. The owner
decided on 2026-11-01 that 2×2 is a research size outside every claim (section 20.1, option 1).
For `phyco-v2` itself, S1 still applies: at most 2⁶⁴ states.

For `lut-v1`: its output is the low 8 bits of every vein value D, so half of D is visible at each
step (L1). The disruption fires on about 99.5% of steps (L2). Every battery rejects it (L3).
lut-v1 is used only as the negative control.

------------------------------------------------------------------------

## 10. Phase 2: Reference and independent implementations

The integer-exact Python reference model is the executable form of the frozen specification. It
is the golden model for any RTL (Principle II). There should be at least three implementations:

| Implementation | Purpose |
|----------------|---------|
| Python reference model | Executable specification and test oracle |
| Independent implementation, sharing no transition code | Catch common-mode and interpretation errors |
| VHDL implementation | The target hardware behaviour |

### 10.1 Test coverage

Test vectors and properties must cover:

- minimum, maximum and boundary values;
- all-zero and all-one seeds;
- single-bit seeds;
- overflow and truncation;
- shift and rotation boundaries;
- signed and unsigned behaviour;
- reset and repeated initialization;
- long runs;
- invalid parameters and states;
- every supported configuration.

Use property-based testing (for example Hypothesis) to explore states and parameters widely.

### 10.2 Status in this repository

- **Python reference models**: `phycoweb/model.py` (lut-v1) and `phycoweb/model_v2.py`
  (phyco-v2). Their tests include:
  - AST purity tests (no floating point, multiplication, division or modulo);
  - width tests (5,002 states for phyco-v2);
  - golden vectors (`vectors/`, 2 × 10,000 words for phyco-v2);
  - seed-domain tests.
  - Results are identical on Windows 11 (Python 3.10.11, numpy 2.2.6) and Ubuntu on WSL2
    (Python 3.14.4, numpy 2.5.4). Both run on the same x86-64 CPU, so other architectures, such
    as ARM, are untested.
- **Second and third implementations of phyco-v2**:
  - `tests/v2_reference.py` is a literal transcription of `design.md` §3–§5, written separately
    from the model with generic helpers. `test_design_trace` compares the two step by step.
  - `fast/phyco_stream.c` is the C stream used for the batteries. It is bit-exact with the
    Python models for both generators: on 200,030,000 words (golden vectors plus the first 10⁶
    words of all 100 dev seeds), and on the first 10⁶ words of every held-out seed at the start of
    each battery attempt.
- **lut-v1 against float-v0**: bit-exact in every stage except the perturbation source, on 2
  seeds × 10,000 words plus 5,000 random states and edge states. A mutation check caught 6 of 6
  mutants.
- **Common-mode caveat**: all three phyco-v2 implementations were written in this project, by the
  same AI coding agent, from the same design document. They catch transcription errors, but not
  a misreading of the specification they all share. An implementation by someone outside the
  project is still needed.
- **Not yet done**: property-based testing with Hypothesis; any VHDL.

### 10.3 Semantics that must agree across languages

The prior feasibility assessment raised two concerns: floating-point contamination in the food
generator, and differences between Python and VHDL shift semantics.

- **Floating point**: resolved by feature 001.
- **Shift semantics**: resolved at the specification level, and shown in a second language (C).
  The VHDL column below is guidance; no VHDL exists yet.

| Operation | Python reference | C stream (`fast/phyco_stream.c`) | VHDL guidance (`numeric_std`) |
|-----------|------------------|----------------------------------|-------------------------------|
| Wrap mod 2³² | `& 0xFFFFFFFF` | `uint32_t` arithmetic | addition on `unsigned(31 downto 0)` |
| Arithmetic right shift | `>>` on a signed Python int (floor) | logical shift plus sign fill, constant amounts only | `shift_right` on `signed` |
| Logical right shift | `>>` on a non-negative int | `>>` on `uint32_t` | `shift_right` on `unsigned` |
| Rotate left | helper | `(x << r) \| (x >> (32 − r))` with constant r | `rotate_left` on `unsigned` |
| Unsigned compare (`D > THRESH`) | `>` on 0…2³²−1 | `>` on `uint32_t` | `>` on `unsigned` |
| Sign extension 16 → 32 | OR 0xFFFF0000 if bit 15 is set | the same | `resize` of a `signed(15 downto 0)` |

A difference in overflow, signedness, truncation, shift, update order or representation makes a
different algorithm. Principle II requires Python/VHDL differential tests of at least 10,000 words
per seed once RTL exists.

**Acceptance criteria:**

- the implementations agree on the vectors and properties;
- every difference is investigated and resolved;
- the source revision and configuration are recorded;
- consistency with the specification is demonstrated.

------------------------------------------------------------------------

## 11. Phase 3: Statistical validation

The aim is to find detectable statistical defects. It does not prove cryptographic security.

### 11.1 Testing hierarchy

| Level | Content | Status for `phyco-v2` |
|-------|---------|-----------------------|
| 1 Basic properties | frequency, runs, serial correlation, bit distribution, autocorrelation, block frequency, entropy estimates (read according to their assumptions) | covered inside SP 800-22 |
| 2 Established batteries | NIST SP 800-22; TestU01 SmallCrush, Crush, BigCrush; PractRand (Dieharder optional) | SP 800-22 done; PractRand/TestU01 attempt 1 PASS (Dieharder not run) |
| 3 Structural and adversarial | state-dependent output, cross-stream correlation, seed sensitivity, related seeds (T2), long-period and cycle studies, tests conditioned on chosen initial states, tests aimed at the design's own structure (S6–S8) | not started |

### 11.2 Test-tool validation (lesson from features 001–002)

The test tool must be validated too:

- **nistrng 1.2.3** had defects. Its Binary Matrix Rank test changed its input in place. Its
  `Result.score` is a mean. Its Non-Overlapping Template test used a single template and returned
  p = 1 in every run. These defects made the feature-001 screening unreliable: see the erratum,
  `scripts/repro_nistrng_defects.py` and `harness/nistrng-defects.json`.
- **The project's harness `sp80022` 1.0.0** (SHA-256 `1563526e…`) replaced it. It was validated
  against the SP 800-22 worked examples, Appendix B, and NIST STS 2.1.2: 0 mismatches at ±1e-6
  (`reports/002-core-dynamics-redesign/harness/`).

### 11.3 Pre-registered protocol (features 002–003)

Every acceptance result in this repository comes from a protocol that was fixed before the data
existed:

- **Seed separation.** Tuning, exploration and setup use `dev` seeds only. Held-out sets are
  identified by SHA-256 fingerprints. Development tools refuse held-out seeds (exit 2), and each
  held-out set is used exactly once.
- **Freeze.** Before each attempt, a freeze record pins:
  - the model, design, harness, source and binary SHA-256 values;
  - the tool versions;
  - the commands;
  - the thresholds.

  The owner approves it, and the runner refuses to start without that approval.
- **Controls.**
  - Positive control: the OS CSPRNG. If it fails, the attempt is INCONCLUSIVE and the candidate
    is not evaluated. The held-out set still counts as used.
  - Negative control: lut-v1. If it does not fail, the attempt is INCONCLUSIVE, because the tests
    have not shown they can discriminate.
- **Limited attempts.** Three for SP 800-22 (feature 002), two for the batteries (feature 003).
  A second battery attempt is allowed only after INCONCLUSIVE or INVALID.
- **Stricter only.** Rules may change only before results exist, with owner approval, and only
  to make the protocol stricter. No test may be removed or loosened (feature-002 FR-014,
  feature-003 FR-015).
- **Report everything.** Every run is reported, including failures and incomplete runs. A
  re-score from the saved logs must reproduce every verdict (`scripts/rescore_attempt.py`,
  `scripts/battery_rescore.py`).
- **Multiple testing.** The battery rule is a Bonferroni threshold over every reported p-value:
  min(p, 1 − p) ≤ 0.005 / S, with S = 101,210, giving 4.94 × 10⁻⁸. Any PractRand FAIL grade or
  TestU01 `eps` row also counts as a failure. From 2026-11-01 (T039a) a PractRand line whose
  statistic saturates (printed `R>` or `R<`) counts as a failure too; the parser used for
  attempt 1 skipped such lines (section 11.4).

### 11.4 Results to date

| Item | Result | Evidence |
|------|--------|----------|
| SP 800-22 acceptance attempt 1 (`heldout-1`, 100 × 2²¹ bits) | **PASS**: phyco-v2 passed 15/15 families, the positive control passed, lut-v1 failed 11/15. The re-score was identical | `reports/002-core-dynamics-redesign/attempt-1/` |
| Positive-control calibration (1,000 runs of OS data) | Chance failure rate under the feature-002 rules: **20.7% (95% CI 18.2–23.3%)**. A perfect candidate passes an attempt only **63%** of the time (CI 59–67%) | `reports/003-extended-batteries-calibration/calibration/` |
| DFT cross-check | Our DFT agrees with STS 2.1.2 on 1,000 fresh sequences. The test's own variance constant is about 6% too small: E[d²] = 1.062 (CI 1.053–1.071), and it rejects 1.23% of random sequences at α = 0.01 | `calibration/dft-crosscheck.md` |
| Battery dev rehearsal (1 dev seed; not evidence) | phyco-v2 had no failures in PractRand to 1 TiB or in SmallCrush, Crush and BigCrush in both bit orders | `reports/003-extended-batteries-calibration/dev/` |
| Battery attempt 1 (`heldout-1` battery set, 10 seeds; S = 101,210, threshold 4.94 × 10⁻⁸) | **PASS**, accepted at the owner result review on 2026-11-01 (T038). phyco-v2 failed no rule in any of its 70 runs (PractRand to 1 TiB; SmallCrush, Crush and BigCrush in both bit orders); smallest min(p, 1 − p) 1.0 × 10⁻⁶, about 20 times the threshold. The positive control failed none of 70; the negative control failed all 70 (section 11.5). The re-score was identical. A parser defect found afterwards (saturated `R>` lines skipped, all of them lut-v1's) was fixed, and a supplementary re-score with the fixed parser gives the same verdict. PASS means that no statistical defect was found at this depth, not cryptographic security | `reports/003-extended-batteries-calibration/attempt-1/` (phase report and addendum; `rescore.json`, `rescore-parser-fix.json`) |

### 11.5 Negative control (lut-v1) in battery attempt 1, reviewed 2026-11-01

- **PractRand**: all 10 seeds stopped at the first checkpoint (2²⁷ bytes) with FAIL grades.
- **SmallCrush**: 12–15 of 15 statistics at `eps` in every run.
- **Crush**: 123–132 of 144 in every run.
- **BigCrush**: 147–154 of 160 in every run.

### 11.6 Interpretation rules

- A set of passing p-values is not proof of randomness. Every test has false-positive and
  false-negative behaviour.
- Multiple testing needs a pre-declared rule, and that rule must itself be calibrated. Feature
  003 measured it: the feature-002 rules fail a perfect generator about one time in five.
- **Selection bias**: 5 variants and 12 runs were tried on dev seeds before phyco-v2 was chosen
  (feature-002 O6). Only held-out attempts are unbiased.
- Statistical success says nothing about S1–S9.

For every test, record:

- the algorithm revision and configuration;
- the seed or seed derivation;
- the sample size;
- the test parameters and tool version;
- the raw output and the p-values;
- the failure locations;
- the reproduction commands;
- any exclusion or re-run, with its justification.

------------------------------------------------------------------------

## 12. Phase 4: Cryptographic attack and resistance evaluation

This phase tests whether the generator withstands attackers trying to predict or distinguish its
output, under the threat model in section 5. Whoever does it, human or AI, acts as an adversary,
not as an advocate for the design.

### 12.1 Attack families

| Attack class | Objective |
|--------------|-----------|
| Seed exhaustion and time–memory trade-off | Recover the seed by search or precomputation (S1–S3) |
| State recovery, including guess-and-determine | Recover the state from output (S5, S6) |
| Prediction | Predict future output |
| Backtracking | Recover earlier output after a state compromise (S9) |
| Distinguishing | Tell the output from uniform data |
| Differential and related-seed | Exploit related seeds or inputs (S8) |
| Rotational | Exploit rotation-structured constants in an ARX design (S7) |
| Algebraic, SAT and SMT | Solve the transition and output equations |
| Linear and correlation | Find linear approximations, or dependencies between outputs or streams |
| Reduced-state | Find structure in smaller variants that may scale |
| Initialization and weak seeds | Exploit the seed mapping, warm-up, or degenerate seeds (T5) |
| Reseeding | Not applicable as specified (S4); required for any prediction-resistance claim |
| Slide | Exploit a step or round function that repeats, for example the 128-step food period (S2) |
| Invariant subspace and nonlinear invariant | Find sets or Boolean functions that the step or round maps onto themselves (compare the zero mode of S13) |
| Integral and division property | Find balanced or constant sums over structured sets of inputs |
| Cube and zero-sum | Exploit a low algebraic degree after few rounds or steps |
| Impossible differential | Rule out key or state candidates with differentials of probability zero |
| Boomerang and differential-linear | Combine two short trails into a longer distinguisher |
| Rotational-XOR | Rotational pairs with an XOR offset, which survive round constants (S7) |
| Inverse direction | Attack a permutation from its output side, through its inverse |
| Mode | Exploit the padding, domain separation, nonce handling, forget and reseed calls or output limits of a mode |
| Side-channel and fault | Timing, power, EM or fault leakage (section 13) |

The rows from Slide to Mode were added in version 2.7 for a permutation-based redesign
(section 21). Most of them also apply to `phyco-v2`.

### 12.2 Generic bounds every claim must respect

- **Seed or key size**: security strength ≤ the entropy of the seed. For phyco-v2 that is
  64 bits; any claim needs FUT-SEC-1, a key of at least 128 bits (section 20.1).
- **State size**: the Babbage–Golić time–memory–data trade-off breaks a generator whose secret
  state is smaller than about twice the claimed strength. For a 128-bit claim, the secret state
  must have at least 256 bits that are actually reachable. phyco-v2 has 256 secret bits
  nominally, but only 2⁶⁴ reachable states per step index (S1).
- **Output volume**: a claim must state how much output per seed it covers.
- **Multi-target key search**: against u keys, some key falls after about 2^k / u trials, so a
  k-bit key gives at most k − log₂ u bits against an attacker who needs any one of them (T8). A
  256-bit key keeps 128 bits for up to 2¹²⁸ keys.
- **Key and nonce trade-offs**: if key and nonce together have fewer than 2s bits, a
  time–memory–data trade-off over many streams costs less than 2^s (Hong and Sarkar, 2005). For
  s = 128, key plus nonce must have at least 256 bits.
- **Capacity (birthday) bound**: a sponge or duplex with capacity c can be distinguished
  generically after about 2^(c/2) calls of the permutation, so c ≥ 2s: at least 256 bits for
  s = 128.
- **Quantum search** (optional threat T11): Grover's algorithm finds a k-bit key with about
  2^(k/2) quantum evaluations. A 256-bit key meets k/2 = 128 with equality and no margin;
  multi-target quantum search falls below it for u > 1.
- **Nonce reuse**: a deterministic generator gives the same output for the same key and nonce.
  A claim states the nonce rule and the behaviour on reuse (T7).

### 12.3 Proposed first investigations for PhycoWeb-PRNG

Each would be its own Spec Kit feature, with a spec, an owner review and recorded results.

1. **Demonstrate the seed bound** on a reduced seed domain, for example two seed words fixed and
   2³² candidates. Recover the seed from three output words and measure the cost per candidate.
   This turns S3 from a generic argument into a reproduced result.
2. **Guess-and-determine and SAT/SMT state recovery** on reduced-width variants (8-bit and 16-bit
   words, with the same structure), then the full width. Report how the number of outputs and the
   solver time scale.
3. **Slow-variable leakage**: test whether the conductance classes (D >> 30, in effect bit 30 of D;
   S12) can be inferred from the output, and whether fixing them makes the step linear enough to
   solve (S6, S12). The top bits of D are strongly biased (S14).
4. **Related-seed and rotational experiments**: rotated seed words, single-bit seed differences
   and rotational pairs (S7, S8).
5. **Merging and cycle structure**: the step function is not a bijection (S13). Measure how
   far states merge, and map the functional graph on reduced variants that are small enough to
   enumerate (S9, S10).
6. **Distinguishers**: linear and differential trail search (MILP or SAT), plus machine-learning
   distinguishers (as in Gohr, 2019) on reduced-step variants. Any advantage found must be
   confirmed with fresh data and a pre-registered test.

For each one, define in advance:

- the attacker's observations;
- the computational budget;
- the success metric;
- the random baseline.

Report the advantage with confidence intervals. A finite experiment never proves
indistinguishability.

### 12.4 Attack report requirements

1. Attack description and target property.
2. Attacker capabilities and assumptions (T1–T5).
3. Required observations and inputs.
4. Mathematical analysis.
5. Executable implementation, where applicable.
6. Experimental results.
7. Data, time and memory complexity.
8. Reproduction instructions and exact revisions.
9. Security implications and limitations.

A proposed attack is not a confirmed vulnerability until it is proved mathematically or
reproduced. An unsuccessful attack is not proof of security.

### 12.5 Tool validation

A negative result from an analysis tool counts only after the tool has re-found known results:

- on `phyco-v2` and its reduced variants: the seed bound on a reduced domain (FUT-SEC-8), the
  merging of S13, the bounded veins of S12 and S15, and the bias of S14;
- for trail search: a published optimal trail of a reference cipher.

This is the lesson of `nistrng` and of the STS oracle comparison (section 11.2). Record each
tool's version, licence and validation result with its first use. Every download needs the
owner's permission, and solver runs, which are heavy, never overlap battery runs.

### 12.6 Best-attack register

For each model meant to support a claim, this register keeps one row per attack class: the
rounds reached out of R, the complexity (time, data, memory), the source (internal or external,
with a reference), the date and the margin. The margin is R divided by the rounds of the best
attack. A claim is never stronger than its weakest row, and an attack below the claimed strength
withdraws the claim at once (section 15).

| Model | Attack class | Reach | Complexity | Source | Date | Margin |
|-------|--------------|-------|------------|--------|------|--------|
| `phyco-v2` | Exhaustive seed search (T1) | full generator | about 2⁷² steps: 2⁶⁴ seeds × (256 warm-up steps plus a few output steps); not executed in full, and reproduced on a reduced domain, 2³² candidates for each of three development targets, all three recovered | generic, S3 (section 5); demonstration record `demonstration-20261104T165604Z-4406adb9`, SHA-256 `5c93e850284120dc9935d3e4317b8dc94df3a7b79fc038dbc8a6c49508613651`, under `reports/004-crypto-architecture-v3/fut-sec-8/` | 2026-11-04 | none: 64 bits is below the 128-bit floor |
| `phyco-v2` | Time–memory trade-off (T1) | full generator | one-time precomputation of about 2⁶⁴ seed evaluations, then about 2⁴³ per target with 2⁴³ stored entries; not executed | generic (Hellman, 1980; section 5) | 2026-10-31 | none |

`phyco-v2` has no rounds, so a margin is not defined for it; the rows record why it can carry no
claim.

------------------------------------------------------------------------

## 13. Phase 5: Hardware implementation validation

Software findings do not transfer to hardware automatically. The FPGA design must be shown to
implement exactly the evaluated algorithm.

The hardware programme includes:

- bit-exact Python/VHDL comparison (Principle II: at least 10,000 words per seed);
- simulation across boundary conditions;
- reset and initialization checks;
- synthesis with 0 DSP blocks and vendor-neutral code (Principle III);
- timing analysis against the ≥ 200 MHz target;
- resource and power analysis;
- glitch and switching behaviour;
- side-channel and fault assessment matched to the threat model.

**Status:** no RTL exists. The open RTL-pending items, recorded as O1 in feature 002 and in the
`design.md` §7 checklist, are:

- a fixed 4-node ring, where Principle III requires a parameterizable grid;
- about 7 serial 32-bit carry chains per step, which puts the 200 MHz target at risk;
- the food source and the output tap, which are not neighbour-to-neighbour signals.

**Side channels and faults (not evaluated).**

- **Values that depend on the state**: the sign tests, the absolute value, the class-selected
  flux shift and the threshold-triggered disruption XOR.
- **In hardware**, these are multiplexers and need not leak through timing, but power and EM have
  not been studied.
- **In software**, the C stream writes them as conditional expressions, which a compiler may turn
  into branches. That stream is a test tool, not for secrets.
- **Fault injection** on the threshold comparison could force or suppress disruptions. This is an
  unverified hypothesis.

**Acceptance criteria:**

- VHDL matches the reference model on the agreed vectors and properties;
- reset, initialization and boundaries are verified;
- synthesis results and tool versions are recorded;
- deviations are investigated;
- side-channel claims are limited to what was measured.

**AI-assisted RTL (from version 2.8).** An RTL or testbench file drafted or repaired with an AI
tool is untrusted until deterministic tools have judged it. For such files:

- expected values come only from the reference model, its golden vectors and the independent C
  implementation, never from the drafting tool, and are never edited to make a test pass;
- every draft passes analysis, a synthesis check and bit-exact simulation before review, and a
  second, independent simulator is recommended;
- a testbench counts only after it has failed on a recorded catalogue of seeded mutants of the
  design, with every surviving mutant explained;
- state words and arithmetic use `numeric_std` types of explicit width and signedness, never
  INTEGER, whose minimum range differs between VHDL-2008 and VHDL-2019;
- the vectors include the model's known edge states, such as a vein value of exactly 2³¹ in
  `phyco-v2` (S12), from constructed states where seeds do not reach them;
- the session that drafts a design does not write the only testbench that judges it;
- the tool, model, date and review status of each such file are recorded with the feature's
  evidence (section 17.2), and code that matches a known library has that library's licence
  checked.

The reasons and sources are in section 5 of
[`research/hardware/vhdl-genai.md`](research/hardware/vhdl-genai.md).

Simulation equivalence alone does not establish side-channel resistance.

------------------------------------------------------------------------

## 14. Phase 6: Independent cryptographic evaluation

The reviewer receives:

- the specification, with exact revisions;
- the source code and test vectors;
- the statistical, attack and hardware reports, with the attack code;
- the threat model;
- the claims and assumptions;
- the known limitations and unresolved findings.

The reviewer looks for:

- inconsistencies between claims and evidence;
- unsupported assumptions;
- missing attack classes;
- common-mode implementation errors;
- statistical method errors;
- overstated conclusions;
- unexamined parameters;
- differences between the evaluated design and the deployment.

A second AI review is not independent cryptanalysis. The Security Policy requires a review by
independent experts in PRNGs, cryptographic primitives and hardware security, recorded in the
repository. The reviewers should reproduce the important findings themselves.

**Status:** not started.

------------------------------------------------------------------------

## 15. Phase 7: Security qualification

Each model carries one claim level. A level is reached only when its evidence is recorded and its
gate is passed, and only in order. Version 2.7 replaced the four classifications used before
(research candidate, statistically evaluated, cryptographically evaluated, cryptographically
qualified), because "substantial cryptanalysis" could not be checked.

| Level | Name | Evidence required | Gate |
|-------|------|-------------------|------|
| L0 | Research candidate | specification; no claim | — |
| L1 | Security target specified | security target, threat model, mode, parameters and generic bounds; FUT-SEC-1 to FUT-SEC-6 met by specification; FUT-SEC-8 done; certification route named (FUT-SEC-9) | FUT-SEC-8 result review and security-target review (feature-004 FR-012; feature-005 FR-013) |
| L2 | Internally analysed | design rationale (section 8); structural proofs; proven trail bounds; an internal attack campaign with validated tools (section 12.5); a reduced-round statistical margin | design freeze; result review |
| L3 | Statistically re-validated | the complete statistical programme on unused held-out key sets, per supported size (FUT-SEC-7) | battery freeze; result review |
| L4 | Implementations verified | an implementation from outside the project; VHDL equivalent to the model (FUT-HW-1, FUT-HW-4) | RTL start (Principle VIII gate 2) |
| L5 | Independently reviewed | review by independent experts recorded in the repository (Security Policy (b)); a public analysis period with no attack below the claimed strength on the full rounds | external review |
| L6 | Scoped claim | an owner-approved claim that fills in the template of section 3 | Principle VIII gate 3 |

The order follows the Security Policy: no evaluation meant to support a claim may be pursued until
FUT-SEC-1 to FUT-SEC-9 are met. Work at L1 and L2 is design work and weakness search, which the
policy allows and requires to be reported. External review meant to support a claim (L5) starts
only after L1–L4 have recorded evidence.

**Claim register.** A model's claim is worded only here; other sections cite only its level:

- `float-v0`: L0; no claim. Archived, not evaluated further.
- `lut-v1`: L0; no claim. Rejected statistically; used as the negative control.
- `phyco-v2`: L0; no claim. It cannot reach L1, because its 64-bit seed is below FUT-SEC-1
  (S1–S3). Its statistical evaluation (Phase 3) may be completed when feature 003 closes; that
  changes no level.
- `phyco-v3`: L0; no claim. Feature 004 stopped at the selection on 2026-11-09, no candidate eligible, and no model
  exists. Its level
  follows the spec's Review & Approval rows and `protocol/claims.json`, which the claim test checks.
- `phyco-v4`: L0; no claim. Feature 005, a second design round after feature 004's stop, had its spec
  approved on 2026-11-09; no model exists, and like every model it must not be used to generate
  secrets. Its level follows feature 005's Review & Approval rows and `protocol/claims.json`.

**Rules for every level:**

- No level, L6 included, makes a custom algorithm "cryptographically secure". L6 carries exactly
  its scoped claim.
- A claim states the exact version, configuration, intended use, properties, assumptions,
  limitations and external reviews.
- An attack below the claimed strength withdraws the claim at once, with a history entry and a
  README update. Upgrades follow the ladder and its gates.
- A later version may narrow a claim, never widen it without new evidence (stricter only).
- Wording: "proven bound", "best known attack", "no attack found within budget", "not
  evaluated". Never "secure", "unbreakable" or "proven secure".
- Under FIPS 140-3, a custom generator cannot be an approved RBG at all (section 6). For
  deployments that need approval, a claim is only reachable along Option B (section 21).

------------------------------------------------------------------------

## 16. AI-assisted work in this repository

### 16.1 How AI assistance has been used (features 001–003)

- **Process.** Work follows the Spec Kit flow: specify, plan, tasks, implement. An AI coding
  agent drafts the documents, writes code and runs the tools. The repository owner approves at
  the recorded gates: spec, plan, tasks, downloads, design and battery freezes, and results.
- **Rules.** The agent is bound by the constitution exactly as a human contributor is:
  - it stops at gates (Principle VIII);
  - it never commits, pushes or publishes (Principle IX);
  - it reports every result, including failures (Principle IV).
- **Verdicts.** Verdicts are computed by code (`protocol/`, `scripts/`), not by the agent's
  narrative, and re-scoring reproduces them from saved logs.

### 16.2 Roles

Separate responsibilities reduce shared blind spots. Any role can be taken by a human or by an AI
session with its own instructions.

| Role | Responsibility | Taken in features 001–003 by |
|------|----------------|------------------------------|
| Lead and evidence tracking | Gate status, traceability, phase reports | AI agent; owner approval |
| Specification | Definitions, ambiguity detection | AI agent; owner review |
| Implementation | Reference model, second implementations, tests | AI agent |
| Statistics | Batteries, protocol, calibration | AI agent; owner freeze and result review |
| Mathematics | State space, invariants, structure | not yet staffed |
| Cryptanalysis | Attacks under the threat model | not yet staffed |
| Hardware | VHDL, simulation, synthesis | not yet staffed |
| Independent reviewer | Challenge every claim | not yet staffed (section 14) |
| Evidence auditor | Check that reports match executions and revisions | partly: re-score scripts and claims checks |

Different AI sessions or models reduce some shared biases, but they do not give true
independence. Agreement between implementations written by one agent from one document is
weaker evidence than agreement with an implementation written by someone else.

### 16.3 Controls against false conclusions

| Control | Requirement | Mechanism in this repository |
|---------|-------------|------------------------------|
| Reproducibility | Every finding has reproducible evidence | Scripts with fixed seeds; commands recorded in every report; re-score scripts |
| Source traceability | Claims cite an equation or specification section | FR/SC identifiers (Principle VII); `design.md` section references |
| Executable verification | Claims are checked by code | Purity, width, trace and vector tests; oracle comparison with STS |
| Independent implementation | No shared transition code | `tests/v2_reference.py`, `fast/phyco_stream.c` (common-mode caveat, section 10.2) |
| AI-drafted RTL and testbenches | Drafts are judged by tools against an independent oracle | The rules of section 13 (from version 2.8); no RTL exists yet |
| Adversarial review | Every security claim has a matching attack investigation | none yet, so no security claim is made |
| Evidence separation | Measured results kept apart from theory | Classification in section 9; dev rehearsals labelled "not evidence" |
| Version control | Every result tied to exact revisions | `git_head` and SHA-256 values in every freeze and run record |
| Human approval | Acceptance needs recorded human review | Review & Approval tables (Principle VIII) |
| Claims discipline | No security wording beyond the evidence | Verbatim disclaimer from `protocol/disclaimer.py` in every report; claims check before final reviews |

**Strict rules:**

- A generated report is not proof that tests ran.
- A generated attack explanation is not proof that an attack worked.
- A generated security argument is not proof of unpredictability.
- A passing simulation is not proof of side-channel resistance.
- A testbench that has never failed is not proof that a design is correct.
- A phase is never marked passed because its documents exist.
- Tool output, logs, artifacts and revisions must support every claim of execution. Where
  evidence is missing, the status is "not evaluated", "inconclusive" or "blocked".

### 16.4 Instructions for a cryptanalysis session

```text
# Cryptanalysis — Instructions

## Role
You are an independent cryptanalyst evaluating PhycoWeb-PRNG model
<MODEL_ID>, design <DESIGN_DOCUMENT> <VERSION> (for phyco-v2:
specs/002-core-dynamics-redesign/design.md 1.0). Your objective is to find
weaknesses, not to show that the generator works.

## Responsibilities
1. Analyse the state transition and output functions.
2. Identify state-space limits, invariant states and short cycles.
3. Investigate output correlations and slowly varying state.
4. Develop seed-recovery, state-recovery and prediction attacks.
5. Investigate backtracking behaviour and related-seed behaviour.
6. Build distinguishing experiments with pre-declared metrics.
7. Analyse reduced-state variants that keep the structure.
8. For a keyed design: attack key and nonce loading, the mode, and the
   permutation in both directions (security.md sections 5 and 12.1).

## Mandatory rules
- Never assume the generator is secure, and never treat statistical
  success as evidence of security.
- Never claim an attack succeeds without executable or mathematical
  evidence. Never invent results.
- Separate confirmed findings from hypotheses (security.md section 9.1).
- State the attacker capabilities (T1-T11), complexities and limits.
- Record the exact revisions and every parameter needed to reproduce.
- Follow the repository constitution: work from an approved spec, use
  development seeds or keys only for exploration, never use held-out
  sets, ask the owner before any download, and never commit, push or
  publish.

## Output per investigation
Attack description; target property; attacker capabilities; required
observations; analysis; code; results; data, time and memory complexity;
reproduction steps; implications and limitations.

## Final objective
Attempt to disprove any security claim. If no attack is found, report
"no attack identified within the scope of this investigation", never
"secure".
```

Each model ID gets its own copy of these instructions in the feature that analyses it, with the
placeholders filled in, and with that model's threat-model rows, structural facts and best-attack
register (section 12.6) as inputs.

The other roles get similar short instructions:

- **Mathematics**: decide whether the transition is a bijection, whether the output leaks state,
  and whether invariant or absorbing states exist. Give derivations and executable checks.
- **Statistics**: run a pre-registered, reproducible campaign. State test assumptions, sample
  sizes, the multiple-testing rule and its calibration, anomalies and limits.
- **Independent reviewer**: assume the development team's claims are wrong until independently
  supported.

------------------------------------------------------------------------

## 17. Evidence management and reporting

### 17.1 Mechanisms already in use

- **Freeze records**: for example `attempt-1/freeze.json` in features 002 and 003. They contain
  the model, design, harness, source, binary and tool SHA-256 values, the commands, the
  thresholds and the owner approval fields. The runners validate them and refuse otherwise.
- **Seed-set fingerprints**: development tools refuse held-out seeds, and each set is used once.
- **Archive inventory**: `baseline/float-v0/MANIFEST.json` (Principle V).
- **Run records**: per-run JSON with input hashes. These include the calibration
  `runs/SHA256SUMS` and the battery `stream.sha256` files.
- **Local-only data**: the positive-control byte files (`data/controls/*.bin`) are git-ignored,
  and only their SHA-256 values are committed. Others can re-run the controls but cannot re-score
  those exact bytes.
- **Re-score**: verdicts are recomputed from saved logs. The results were identical on Windows,
  and within floating-point rounding on WSL.
- **Phase completion reports** (constitution): these list:
  - files created or modified;
  - requirements addressed;
  - exact commands and results;
  - open issues;
  - security concerns;
  - a recommendation to proceed, revise or stop.

### 17.2 Every evidence record should include

- a unique identifier, and the date and time of execution;
- the algorithm version, specification version and git commit;
- tool and dependency versions, the operating system and the hardware;
- the exact command and configuration;
- the inputs, or the seed derivation;
- output paths with SHA-256 values;
- the exit status and assertions;
- the result classification;
- the analyst and the reviewer, with the review status;
- known limitations.

Preserve raw tool output, not only summaries.

### 17.3 Final reports required before any security decision

1. Algorithm specification and change history.
2. Threat model and security requirements.
3. Mathematical and state-space analysis.
4. Reference implementation verification.
5. Statistical testing.
6. Cryptanalysis and attacks.
7. Hardware verification.
8. Independent review.
9. Security assessment and qualification decision.

Each must keep these apart:

- demonstrated facts;
- mathematical arguments;
- experimental observations;
- unverified hypotheses;
- unsuccessful attacks;
- untested areas;
- residual risks.

------------------------------------------------------------------------

## 18. Repository organization

Security work follows the existing Spec Kit layout. It does not use a separate tree.

```text
PhycoWeb-PRNG/
|-- .specify/memory/constitution.md   governing principles (v1.3.0)
|-- specs/NNN-<feature>/              spec, plan, research, data model, tasks, design
|-- reports/NNN-<feature>/            evidence, phase reports, freezes, attempts
|-- phycoweb/                         reference models (lut-v1, phyco-v2) and the LUT
|-- baseline/                         archived variants with SHA-256 manifest
|-- sp80022/                          validated SP 800-22 harness
|-- protocol/                         seed sets, freezes, battery rules, disclaimer
|-- scripts/                          runners, re-score, generators, cross-checks
|-- fast/                             C streams and the TestU01 driver
|-- tests/                            unit tests, fixtures, independent transcription
|-- vectors/                          golden output vectors
|-- research/                         exploration logs and variants (dev seeds only)
|-- data/                             LUT data; local-only control bytes (git-ignored)
`-- security.md                       this document
```

Future security work fits the same pattern:

- a threat-model and security-claims feature (`specs/NNN-…`);
- cryptanalysis features, with attack code under `research/NNN/` or `scripts/` and results under
  `reports/NNN-…/`;
- an RTL feature, with VHDL and testbenches in a new `hardware/` directory, created by its spec.

------------------------------------------------------------------------

## 19. Tool environment

The tools actually used in features 001–003:

| Tool | Version | Use |
|------|---------|-----|
| Python | 3.10.11 (Windows 11); 3.14.4 (Ubuntu on WSL2) | reference models, harness, protocol, analysis |
| numpy / scipy | 2.2.6 / 1.15.3 (Windows); 2.5.4 / 1.18.1 (WSL) | integer arrays and FFT; scipy for analysis only |
| `sp80022` | 1.0.0 (SHA-256 `1563526e…`) | SP 800-22 harness |
| NIST STS | 2.1.2 (WSL) | reference oracle |
| PractRand | 0.96 | long-stream battery |
| TestU01 | 1.2.3 (non-commercial licence; not redistributed) | SmallCrush, Crush, BigCrush |
| gcc | 15.2.0 (WSL) | fast streams, TestU01 driver, tool builds |
| git | — | version control and provenance |

Planned for later phases, not yet installed or used:

- Hypothesis, for property-based tests;
- GHDL and NVC, for VHDL simulation; VUnit or cocotb, for testbenches; VHDL-LS, for analysis
  while editing; the GHDL plugin for Yosys with SymbiYosys, for synthesis checks and formal
  properties; GTKWave, for waveforms; Vivado for FUT-HW-2, with openXC7 as an optional open
  cross-check of fit (see [`research/hardware/vhdl-genai.md`](research/hardware/vhdl-genai.md)
  section 3);
- SAT and SMT solvers (for example CryptoMiniSat, Z3);
- SageMath, for algebraic analysis.

Each download needs the owner's explicit permission (file name, source and size), and the
versions are recorded in the feature that uses it.

The tools, not an assistant's narrative, decide whether a test completed and whether its
assertions passed. Record the tool versions, the environment, the configuration and the exact
command lines.

------------------------------------------------------------------------

## 20. Priorities for PhycoWeb-PRNG

The prior feasibility assessment named three concerns:

1. mathematical ambiguities in the four-node architecture;
2. a potentially insufficient state space;
3. floating point in the food generator, and differences between Python and VHDL shift
   semantics.

Their status, and that of the investigations that follow from them:

| Priority | Investigation | Status (2026-11-01) | Evidence or next step |
|----------|---------------|---------------------|-----------------------|
| Critical | Resolve mathematical ambiguities | **Resolved** for lut-v1 and phyco-v2 | feature 001 FR-007/FR-008; `design.md` §2–§6 |
| Critical | Remove floating point | **Resolved**: integer lookup table; AST purity tests | feature 001; `test_purity`, `test_purity_v2` |
| Critical | Python/VHDL semantic differences | **Resolved in the specification**, and bit-exact in C; VHDL pending | section 10.3; `streams/equivalence.json` |
| Critical | Effective reachable state space | **Open.** Upper bound: 2⁶⁴ states per step index. Any 2×2 design that keeps the design-1.0 vein update has at most about 2²⁵² secret states, below FUT-SEC-2 (S15) | section 9.2 S1–S3, S15 |
| Critical | Seed and key interface (new) | **Open.** 64 bits bounds every claim. A fix (a ≥ 128-bit key, plus a reseed input for prediction resistance) is an algorithm change and needs a new spec and owner review (Principles VI, VIII) | section 9.2 S1–S4 |
| High | Convergence and attractors | **Partly**: v001 collapse observed; disruption rate 13.5–13.8%; edge-seed period check only | `design.md` §9 |
| High | Output/state correlation | Not started | section 12.3 item 3 |
| High | State reconstruction | Not started | section 12.3 items 1–2 |
| High | Prediction resistance | Not applicable as specified (S4) | — |
| High | Distinguishing attacks | Statistical batteries only | section 12.3 item 6 |
| Medium | Statistical batteries | SP 800-22 done; PractRand/TestU01 attempt 1 PASS; structural tests not started | section 11.4 |
| Medium | FPGA implementation | Not started (O1) | section 13 |
| Final | Independent cryptographic review | Not started | section 14 |

### 20.1 Future feature requirements, if cryptographic certification is pursued

The main finding of this review: **phyco-v2's seed is four 16-bit words, 64 bits in total. That
caps any security level at 64 bits, however large the internal state, which is below the 112-bit
minimum for approved cryptographic use.** The derivation, the measured cost and the full
requirement text are in
[`research/security/seed-entropy-bound.md`](research/security/seed-entropy-bound.md).

These requirements apply **only if the owner decides to pursue a cryptographic claim, evaluation
or certification**. They are not scheduled. Since constitution 1.2.0 (approved 2026-10-31) they
are binding policy: the Security Policy forbids any cryptographic claim, evaluation or
certification, for any model, until they are met, and its wording prevails over this summary.
Meeting them is an algorithm change (Principles VI and VIII), and probably another core redesign
with a new model ID.

| ID | Requirement (summary) |
|----|-----------------------|
| FUT-SEC-1 | A key with at least 128 bits of entropy, and no claimed strength below 128 bits. No seed or key search, and no trade-off attack, cheaper than the claimed strength |
| FUT-SEC-2 | Reachable secret state of at least twice the claimed strength |
| FUT-SEC-3 | A nonce or IV with uniqueness rules, if a key can have more than one stream |
| FUT-SEC-4 | A reseed input from a validated entropy source, if prediction resistance is claimed |
| FUT-SEC-5 | Analysis of key and IV loading and of the warm-up (related-key, related-IV, weak keys) |
| FUT-SEC-6 | A specified maximum output per key, and per key and IV |
| FUT-SEC-7 | A new model ID, vectors, freeze, and the full statistical programme on unused held-out sets |
| FUT-SEC-8 | Before a redesigned key interface is implemented, reproduce the 64-bit bound on a reduced seed domain (section 12.3, item 1) |
| FUT-SEC-9 | A named certification route. FIPS 140-3 approval is not available to a custom generator (Option B only, section 21), and no model may be described as FIPS 140-3 approved or as an SP 800-90A DRBG |

The FUT-SEC-1 floor was raised from 112 to 128 bits when the constitution was amended. SP 800-57
Part 1 Rev. 5 accepts 112-bit strength for applying protection only through 2030, and a redesign
and its validation would probably finish after that.

**A wider seed alone is probably not enough**, for these reasons:

- the seed fills only the P words, while D and the phases start from constants;
- loading key material into D changes the vein dynamics that feature 002 tuned (feature-002
  FR-005);
- there is no nonce or reseed input;
- key and IV loading needs its own analysis.

Details are in §4 of the research note.

**Grid scaling in the same redesign.** Design 1.0 is a fixed 4-node ring (the 2×2 grid) and does
not meet Principle III's 2×2 to 16×16 scaling (feature-002 open issue O1). The key-interface
redesign should resolve that too. These design requirements come from Principle III, not the
Security Policy (full text in §5.1 of the research note):

| ID | Requirement (summary) |
|----|-----------------------|
| FUT-GRID-1 | Grid size a parameter, at least 2×2 to 16×16, with up to four channels per node, neighbour-only data flow and a registered output tree |
| FUT-GRID-2 | Key and IV loading defined for every supported size; FUT-SEC-1 and FUT-SEC-2 hold at every size, including the smallest |
| FUT-GRID-3 | Warm-up derived from the grid diameter and measured: every state bit depends on every key and IV bit |
| FUT-GRID-4 | Per-node constants generated by a stated rule that avoids translational and rotational symmetry (S7); disruption behaviour re-established per size |
| FUT-GRID-5 | Vectors and statistical evaluation per supported size; validate an intermediate size such as 4×4 before 16×16 |

**Decision: FUT-SEC-2 and FUT-GRID-2 at 2×2.** S15 shows that a 2×2 ring with two 32-bit
words per node cannot reach 2²⁵⁶ secret states with the design-1.0 vein update, and has no slack
with any update: a duplex mode with a 256-bit capacity would have no rate left. FUT-GRID-2
requires FUT-SEC-1 and FUT-SEC-2 at every supported size, including the smallest. The owner
was to decide, at the latest in the spec that introduces the key interface, between:

1. **Recommended:** sizes too small for the claim, 2×2 included, are reduced research variants
   outside every claim, and the claimable sizes start at 4×4. This narrows what can be claimed.
2. A wider node state, for example four 32-bit lanes per node, so that 2×2 holds 512 bits.

**Decided: option 1**, by the owner on 2026-11-01 in the approved feature-004 spec (default D3,
FR-017). The claimable sizes start at 4×4, and 2×2 and 3×3 are reduced research variants
outside every claim. The redesign must therefore meet FUT-GRID-2's clause on FUT-SEC-1 and
FUT-SEC-2 at every claimable size, and does not meet it at the research sizes, which carry no
claim. This weakens neither requirement: FUT-SEC-1 and FUT-SEC-2 bound a claimed strength, and
no claim covers a research size; each research row of feature 004's size profile states its
key entropy c, its s = c/2 and the status `research`; and the production interface refuses
every research variant (feature-004 FR-033). Key and IV loading stays defined at every
supported size, through the keyed variant each size has.

**Hardware target.** Security and performance must be testable on the owner's Digilent Arty
A7-100T (AMD Artix-7 XC7A100TCSG324-1), using LUTs, flip-flops and block RAM only, with 0 DSP
blocks as the constitution requires. DSP blocks were considered and rejected by the owner on
2026-10-31 (§5.2 of the research note):

| ID | Requirement (summary) |
|----|-----------------------|
| FUT-HW-1 | Behavioural, vendor-neutral VHDL with grid size and word width as generics; no instantiated primitives; 0 DSP blocks; GHDL bit-exact with the Python model |
| FUT-HW-2 | Vivado post-route resources and timing on the XC7A100T-1 at 4×4 and at the largest grid that fits; ≥ 200 MHz target |
| FUT-HW-3 | Throughput measured on the board with on-chip counters, per grid size; power from the board's core-supply sensor |
| FUT-HW-4 | Bit-exact equivalence on the board; stated split between battery levels run on captured hardware output (about 12 MB/s over Ethernet) and on the C stream |
| FUT-HW-5 | Hardware security tests the board and equipment allow (constant time, no key read-back, zeroization, fault behaviour); side channels recorded as untested without measurement equipment |

------------------------------------------------------------------------

## 21. Architectural decision: new primitive or established construction

**Option A: a new cryptographic primitive.** The bio-inspired architecture itself must provide
the security. This requires:

- a security model;
- a key or seed interface that matches the claimed strength (at least 128 bits, with a secret
  state of at least 256 reachable bits, section 12.2);
- a reseed design if prediction resistance is claimed;
- extensive independent cryptanalysis.

Novelty and complexity establish nothing.

Option A has three forms (research note
[`crypto-redesign-strategy.md`](research/security/crypto-redesign-strategy.md) §4):

- **A1**: a new state-evolving keystream generator, as `phyco-v2` is today. It is the hardest to
  analyse and has no reduction; `phyco-v2` shows the failure modes (S11–S15).
- **A2, the recommended route for any claim**: a new keyless permutation used in a mode with a
  published security proof, such as a keyed duplex (instantiate, generate, forget, optional
  reseed). The proof reduces every property to one assumption, that the permutation has no
  structural distinguisher below the claimed strength, and the cryptanalysis attacks that
  assumption. Bijectivity by construction removes S13, and FUT-SEC-2 becomes a capacity of at
  least 256 bits (section 12.2).
- **A3**: a new block cipher in counter mode. It adds a key schedule, a second source of
  weakness.

**Option B: a bio-inspired mechanism alongside an established construction.** An approved DRBG,
seeded from a validated entropy source, provides the security (SP 800-90A/B/C). The bio-inspired
generator could only be an additional, non-security input or a research component.

- It is deterministic, so it adds no entropy, and it cannot count as an entropy source.
- The composition must still be analysed so that it cannot weaken the approved construction.

**Option C: stop.** Keep PhycoWeb-PRNG as a documented non-cryptographic research generator.
This is a legitimate outcome; the research value remains.

For keys and other security-critical values, the preferred engineering choice is an established,
correctly instantiated DRBG with a validated entropy source, not an unreviewed custom generator.
No option is assumed secure.

------------------------------------------------------------------------

## 22. Roadmap

| Stage | Work | Status |
|-------|------|--------|
| 1 | Governance: constitution, gates, evidence rules, this document | Done (constitution 1.3.0; this document 2.13) |
| 2 | Remove floating point, fully specify integer semantics | Done (feature 001) |
| 3 | Redesign the core dynamics; reference model and vectors | Done (feature 002, phyco-v2) |
| 4 | Statistical validation: SP 800-22, calibration, PractRand, TestU01 | SP 800-22 done (002); calibration done (003); battery attempt 1 PASS (003, reviewed 2026-11-01) |
| 5 | Threat model and security-claims spec; structural analysis (seed bound, invertibility, cycles) | Next (sections 5, 9.2, 12.3) |
| 5a | Only if a cryptographic claim or certification is pursued: a key-interface redesign meeting FUT-SEC-1 to FUT-SEC-9 and the grid-scaling and hardware requirements FUT-GRID-1 to FUT-GRID-5 and FUT-HW-1 to FUT-HW-5, as a new design with a new model ID (Option A2, section 21), in features 004–010 below. An attack on the full design at any point sends the work back to 004 with a new model ID, or stops it (Option C) | Conditional; approved by the owner on 2026-11-01, with the strategy note and the 2.7 to 2.9 changes, when the feature-004 spec was approved. Its requirements are binding (constitution 1.2.0, section 20.1) |
| 5a.1 | Feature 004: the FUT-SEC-8 demonstration (stage 5's seed bound); security target and threat model; mode; the permutation and its inverse; reduced variants; design rationale; reference model and vectors; first proven bounds; owner design review and ⛔ design freeze (L1, start of L2) | Stopped at the selection on 2026-11-09, no candidate eligible; the final report (`reports/004-crypto-architecture-v3/phase-report.md`) recommends stopping, option C of section 21, and the owner's final result review approved it on 2026-11-09 |
| 5a.1b | Feature 005: stage 5a.1 again, for a new model ID, `phyco-v4`, under its own pre-registered protocol (row 5a; feature 004's stop rule): every run planned at 16×16 before any candidate, the security target reviewed first, and a bound climb continued past a capped search by sums of shorter spans; then the deliverables of stage 5a.1 (L1, start of L2) | Spec approved by the owner on 2026-11-09, with decisions D1–D14 as their defaults; plan approved on 2026-11-09, with the run limits extended; tasks not started |
| 5a.2 | Feature 006: internal cryptanalysis with validated tools (section 12.5); best-attack register (section 12.6); reduced-round battery sweep; margin (L2) | Not started |
| 5a.3 | Feature 007: an independent C implementation and generic VHDL, with equivalence evidence; the RTL validated at 4×4 before 8×8 and 16×16, in the order of sizes that features 004 and 005 keep for vectors and statistical evaluation (FUT-GRID-5); ⛔ RTL start (L4) | Not started |
| 5a.4 | Feature 008: statistical re-validation on unused held-out key sets per supported size (FUT-SEC-7; L3). The held-out keys are derived from data that does not exist until the later of `phyco-v4`'s design freeze and feature 008's protocol freeze, for example SHA-256 over feature 008's protocol freeze record with a public string; feature 008 states the derivation, and a test re-derives it (feature-004 FR-040, which feature 005 inherits) | Not started |
| 5a.5 | Feature 009: hardware validation on the Arty A7-100T (FUT-HW-2 to FUT-HW-5), at 4×4 first, then each larger claimable size that fits the XC7A100T, in order, the largest that fits last (FUT-GRID-5, FUT-HW-2); a size that does not fit is listed in feature 009's spec with its reason and stays covered by feature 007's simulation; may run alongside 008 | Not started |
| 5a.6 | Feature 010: review package, independent review, a public analysis period if the owner authorizes it, and the ⛔ claim decision (L5, L6) | Not started |
| 6 | Cryptanalysis: state recovery, related seeds, rotational, algebraic, distinguishers | Not started |
| 7 | RTL: VHDL, differential tests, synthesis, side channels | Not started (O1) |
| 8 | Independent review, reproduction, qualification decision | Not started |

The roadmap is sequential at the gate level. Research may run in parallel, but downstream
conclusions stay blocked while upstream definitions or implementations are unresolved.

------------------------------------------------------------------------

## 23. Reporting a weakness

Weaknesses, attacks and errors in this document are welcome. Report them through the
repository's issue tracker, and include:

- the model ID and version (for example `phyco-v2`, design 1.0), and the git commit;
- the property you believe is violated, and the attacker capabilities (section 5);
- the seeds, data volumes and exact commands;
- code or data that reproduces the result.

PhycoWeb-PRNG must not protect secrets (section 4), so public reports are appropriate. The owner
reviews each report. Confirmed findings are recorded with the classification in section 9.1 and
traced into a spec.

------------------------------------------------------------------------

## 24. Final recommendation

The project pursues three separate objectives:

- **Scientific**: show that the bio-inspired architecture produces well-defined, complex,
  reproducible state transitions.
- **Engineering**: show that it can be implemented consistently and efficiently in Python and
  synthesizable VHDL.
- **Cryptographic**: establish, through mathematical analysis and independent cryptanalysis,
  whether a construction based on it provides meaningful security under a stated threat model.

Success in the first two must not be read as success in the third. As specified, `phyco-v2`
cannot meet the cryptographic objective, because its 64-bit seed caps any security strength at
64 bits. Any cryptographic work therefore starts with a new, owner-approved specification of the
key and reseed interface, meeting requirements FUT-SEC-1 to FUT-SEC-9, which the constitution
makes binding (section 20.1). That is probably another core redesign. The work then follows
sections 9–15.

The next security-related artifact recommended for this repository is feature 004, whose prompt
is in [`next.md`](next.md). It would:

- adopt section 5, extended for keys and nonces, as its threat model, and specify the security
  target as requirements, not claims;
- state that no claim is made for design 1.0;
- start with the reduced-domain seed recovery (section 12.3 item 1, FUT-SEC-8);
- specify a permutation-based design (Option A2, section 21) up to a frozen design.

If the owner does not pursue a claim (Option C), a smaller feature for the threat model and the
investigations in section 12.3 on `phyco-v2` remains the recommendation.

**Final security rule:** classify PhycoWeb-PRNG as an experimental research candidate, not a
cryptographically secure PRNG, until both of the following hold:

- the algorithm has undergone adequate independent cryptanalysis;
- the complete construction satisfies its stated security requirements.

------------------------------------------------------------------------

## 25. Document history

| Version | Date | Change |
|---------|------|--------|
| 1.0 | before feature 001 (git `64e7e3d`) | Initial validation strategy |
| 2.0 | 2026-10-31 | Replaced the tool-environment section with the tools actually used. Corrected the definitions of prediction and backtracking resistance (SP 800-90A) and added the AIS 20/31 terms. Checked the standards' status (SP 800-90C final 2025; SP 800-90A Rev. 2 draft; the 2022 SP 800-22 revision decision). Added the security status, threat model, structural facts S1–S11 and generic bounds. Aligned every phase with the evidence from features 001–003 (specification, implementations, harness validation, pre-registered protocol, calibration, DFT cross-check, battery attempt status). Replaced the proposed directory tree with the actual layout. Added AI-assistance practice, weakness reporting and priority status |
| 2.1 | 2026-10-31 | Recorded the main finding, the 64-bit seed bound, as conditional future feature requirements FUT-SEC-1 to FUT-SEC-9 (section 20.1, roadmap stage 5a). Added the research note `research/security/seed-entropy-bound.md` |
| 2.2 | 2026-10-31 | Constitution 1.2.0, approved by the owner on 2026-10-31, makes FUT-SEC-1 to FUT-SEC-9 binding through its Security Policy and raises the FUT-SEC-1 floor from 112 to 128 bits. Section 4 now quotes the policy's general rules verbatim and summarizes its security-strength rules. Sections 1.2, 6, 12.2, 18, 20.1, 22 and 24 updated to match |
| 2.3 | 2026-10-31 | Added grid-scaling design requirements FUT-GRID-1 to FUT-GRID-5 for the key-interface redesign (section 20.1, roadmap stage 5a), from Principle III and feature-002 open issue O1 |
| 2.4 | 2026-10-31 | Added hardware-target requirements FUT-HW-1 to FUT-HW-5 for the owner's Arty A7-100T (0 DSP blocks; DSP use considered and rejected), with board figures checked against the Digilent reference manual (section 20.1) |
| 2.5 | 2026-10-31 | Recorded S12: conductance classes 2 and 3 are in effect unused, because a larger D gets a smaller flux. Section 9.2 gives the proof and a census by `research/security/vein_class_census.py`; section 12.3 item 3 links it |
| 2.6 | 2026-10-31 | Recorded S13: the step function is not one-to-one (vein-decay pairs and a transport zero mode), which settles S9; and S14: the vein values stay near 2³⁰, so the top bits of D are biased. Evidence from `research/security/step_probes.py`. Sections 5, 9.2 (S9) and 12.3 (items 3 and 5) and the roadmap updated |
| 2.7 | 2026-10-31 | Applied §7.3 of the research note `research/security/crypto-redesign-strategy.md`. Recorded S15: the bound of S12 holds from every state, so a 2×2 design with design-1.0 veins has at most about 2²⁵² secret states, below FUT-SEC-2; evidence from `research/security/vein_descent.py`. Added a claim level per model (sections 1.1 and 1.3); definitions for a keyed design, a claim template and the AIS class names by version (3); threat-model rows T6–T11 (5); SP 800-232, eSTREAM, ISO/IEC 29192 and BSI TR-02102-1 as comparison references, and the checked AIS 20/31 version (6); the design phase and a recommended external design review (7); design-rationale requirements (8); attack classes, generic bounds, tool validation and a best-attack register (12.1, 12.2, 12.5, 12.6); the claim ladder and claim register in place of the classifications (15); instructions per model ID (16.4); the open FUT-SEC-2 and FUT-GRID-2 decision (20, 20.1); Options A1–A3 and C (21); features 004–009 in stage 5a (22); and the next feature, with its prompt in `next.md` (24) |
| 2.8 | 2026-10-31 | Added rules for AI-assisted RTL and testbenches (section 13), from the research note `research/hardware/vhdl-genai.md`: expected values only from the model, its vectors and the C implementation; deterministic checks before review; testbenches checked against seeded mutants; explicit `numeric_std` types, and the model's edge states in the vectors; no shared author for a design and its only testbench; provenance and licence records. Added the matching control and strict rule (16.3) and the planned VHDL tools (19). Stricter only; no RTL exists yet |
| 2.9 | 2026-11-01 | Recorded the reviewed battery verdict (feature 003, attempt 1: PASS, accepted by the owner on 2026-11-01) in sections 1.1–1.3, 11.1, 11.4, 11.5 and the roadmap, and the stricter PractRand rule for saturated lines (section 11.3). No claim level changes |
| 2.10 | 2026-11-01 | Recorded the owner's approval, on 2026-11-01 with the feature-004 spec, of the strategy note `research/security/crypto-redesign-strategy.md` and of the 2.7 to 2.9 changes, and the owner's approval of the feature-004 plan the same day: roadmap rows 5a and 5a.1. No requirement or claim level changes |
| 2.11 | 2026-11-01 | Recorded the owner's decision on FUT-SEC-2 and FUT-GRID-2 at 2×2, option 1, taken on 2026-11-01 in the approved feature-004 spec (D3, FR-017), with the reason it weakens neither requirement (sections 9.2 and 20.1). Roadmap rows 5a.3 to 5a.5 now carry two feature-004 requirements: FUT-GRID-5's validation of 4×4 before 8×8 and 16×16 to features 006 and 008, and the checkable derivation of the held-out keys to feature 007 (feature-004 FR-040). From the owner's answers to the feature-004 checklist choices (SEC-010, PRO-010, HW-035). No claim level changes |
| 2.12 | 2026-11-01 | Roadmap row 5a.5 carries feature 004's corrected order of sizes for the board: 4×4 first, then each larger claimable size that fits the XC7A100T, in order, the largest that fits last (FUT-HW-2), and a size that does not fit stays covered by feature 006's simulation. This corrects the wording 2.11 carried, which could have required a size the device cannot hold. From the owner's answers to the feature-004 checklist re-run (HW-041). FUT-GRID-5, FUT-HW-2 and every claim level are unchanged |
| 2.13 | 2026-11-01 | Names constitution 1.3.0, which the owner approved on 2026-11-01, in the header, section 4, the tree of section 18 and roadmap stage 1. Version 1.3.0 amended only Principle IX, so the Security Policy that section 4 quotes is unchanged. The statements of what happened under 1.2.0 stay (sections 1 and 20, and roadmap row 5a), as do section 16.1, which describes features 001–003, and the review prompt's "never commit, push or publish", since review sessions hold no standing authorization. The L1 gate of section 15 reads "FUT-SEC-8 result review and security-target review" in place of "spec approval", and its evidence is unchanged: the feature-004 spec approval of 2026-11-01 started the design work and recorded no level, and `phyco-v3` stays at L0 until feature 004 records L1. Section 12.2 states that a 256-bit key meets k/2 = 128 with equality and no margin and that multi-target quantum search falls below it for u > 1, and section 5 records that feature 004 adopts T11 only as single-target key search. From the owner's answers to the second re-run of the feature-004 checklists (SEC-048, SEC-051, SEC-052). No requirement is weakened and no claim level changes |
| 2.14 | 2026-11-03 | Gave `phyco-v3` its line at L0 in section 15's register and its row in section 1.1, "L0; no claim", before the claim test's first run (feature 004, FR-051, FR-069). The opening and closing blocks gained the fixed sentence "PhycoWeb-PRNG, every model included, must not be used to generate secrets." and now state the restriction with "an established cryptographic RNG", as README's block does. No requirement, level or finding changed |
| 2.15 | 2026-11-04 | The best-attack register's row for exhaustive seed search cites the FUT-SEC-8 demonstration record by ID and SHA-256, the search tool's validation record (feature 004, FR-003; sections 12.5 and 12.6). The owner's FUT-SEC-8 result review follows. No requirement, level or finding changed |
| 2.16 | 2026-11-09 | Recorded that feature 004 stopped at the selection with no eligible candidate (`reports/004-crypto-architecture-v3/freeze/selection.json`): section 1.1's row and section 15's line for `phyco-v3`, and roadmap stage 5a.1, say so, and the final report recommends stopping (section 21, option C). No requirement, level or finding changes; `phyco-v3` stays at L0 with no claim and no model (feature 004, FR-051, FR-052) |
| 2.17 | 2026-11-09 | Recorded the owner's final result review of feature 004, which approved the final report and its recommendation to stop on 2026-11-09: roadmap stage 5a.1 says so. No requirement, level or finding changes; `phyco-v3` stays at L0 with no claim and no model (feature 004, T127) |
| 2.18 | 2026-11-09 | Recorded the owner's approval of the feature-005 spec on 2026-11-09, with its decisions D1–D14 as their defaults (feature 005, FR-027): `phyco-v4`, the model ID of feature 005's second design round, gains its row in section 1.1 and its line in section 15's register, L0 with no claim and not for secrets, and its entry in `protocol/claims.json`; section 15's L1 gate names feature 005's FR-013 beside feature 004's FR-012; roadmap row 5a.1b gives feature 005 stage 5a.1's place for `phyco-v4`, and the features of rows 5a.2 to 5a.6 become 006 to 010 (D12), section 5's note on T11 naming the cryptanalysis stage by its row. No requirement, level or finding changes; `phyco-v3` stays at L0 with no claim and no model |
| 2.19 | 2026-11-09 | Applied the first checklist round of feature 005, its FR-027 as changed: section 5's note on T11 names `phyco-v4` beside `phyco-v3`; section 1.1's row for `phyco-v4` gives a 256-bit key and a 128-bit nonce as targets and its state as not specified until the selection; roadmap row 5a.3 refers to features 004 and 005's order of sizes. No requirement, level or finding changes; `phyco-v4` stays at L0 with no claim |
| 2.20 | 2026-11-09 | Applied the third checklist round of feature 005, its FR-027 as changed: roadmap row 5a.1b records the plan approval of 2026-11-09, with the run limits extended, and checklist rounds 1 to 3; row 5a.3 names the order of sizes that features 004 and 005 keep for vectors and statistical evaluation (FUT-GRID-5). No requirement, level or finding changes; `phyco-v4` stays at L0 with no claim |
| 2.21 | 2026-11-09 | Applied the fourth checklist round of feature 005, its FR-027 as changed: roadmap row 5a.1b names the gates feature 005 has passed and the next one, and no longer its checklist rounds. No requirement, level or finding changes; `phyco-v4` stays at L0 with no claim |

> Passing statistical batteries does not show cryptographic security. PhycoWeb-PRNG, every model
> included, must not be used to generate secrets. Use an established cryptographic RNG for keys,
> nonces, tokens and salts.
