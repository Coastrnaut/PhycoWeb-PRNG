# PhycoWeb-PRNG Security Policy and Cryptographic Validation Strategy

- **Document:** `security.md`, version 2.5 (2026-10-31). The change history is in section 25.
- **Project:** PhycoWeb-PRNG.
- **Purpose:** This document does three things:
  - states the security policy for the generator;
  - defines the evidence-driven programme for deciding whether it could ever support a
    cryptographic claim;
  - records the evidence gathered so far in features 001–003.
- **Governed by:** the [constitution](.specify/memory/constitution.md) v1.2.0, specifically the
  Security Policy and Principles IV, V, VIII and IX. Where this document and the constitution
  differ, the constitution applies.
- **Status:** a research and validation plan. It is not a security certification. **No security
  property is claimed for any PhycoWeb-PRNG model.**

> **Do not use PhycoWeb-PRNG to generate keys, nonces, tokens, salts or any other secret.**
> Use an established cryptographic random-number generator instead: the operating system CSPRNG
> (for example `os.urandom` or `getrandom()`), or a NIST SP 800-90A DRBG seeded from a validated
> entropy source. Passing statistical tests does not show cryptographic security. That includes
> NIST SP 800-22, PractRand and TestU01.

------------------------------------------------------------------------

## 1. Security status at a glance

### 1.1 Models

| Model | Source | State | Seed | Statistical evidence | Cryptographic evidence | Role |
|-------|--------|-------|------|----------------------|------------------------|------|
| `float-v0` | `baseline/float-v0/` (archived; SHA-256 in `MANIFEST.json`) | floating-point food generator (`np.sin`, `np.cos`) | 4 × 16 bits | Feature-001 screening only, done with the defective `nistrng` 1.2.3 (see the erratum in `reports/001-integer-lut-perturbation/summary.md`) | none | archive only |
| `lut-v1` | `phycoweb/model.py` (feature 001) | 144 bits: P and D 4 × 16 bits each, two 8-bit phases | 4 × 16 bits | Fails SP 800-22 (11 of 15 families, feature-002 attempt 1). Fails PractRand and TestU01 (feature 003, section 11.5) | none. The output exposes the low 8 bits of every vein value | negative control |
| `phyco-v2` | `phycoweb/model_v2.py`, [`design.md`](specs/002-core-dynamics-redesign/design.md) 1.0 (feature 002) | 272 bits, of which the 16 phase bits are public | 4 × 16 bits = **64 bits** | Passed the pre-registered SP 800-22 attempt 1 (15 of 15 families, `heldout-1`). PractRand/TestU01 attempt 1 is in progress (feature 003) | none | research candidate |

### 1.2 What is and is not established for `phyco-v2`

- **Established**:
  - The algorithm is fully specified: every width, signedness, shift, wrap, comparison and
    update order is defined.
  - It is integer-only and multiplierless.
  - It is deterministic and identical on two platforms.
  - Three implementations written in this project agree bit for bit.
  - The pre-registered SP 800-22 protocol detected no statistical defect in 100 held-out
    sequences.
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

### 1.3 Validation phases for `phyco-v2` (status 2026-10-31)

| Phase | Gate | Status | Evidence |
|-------|------|--------|----------|
| 0 Specification | frozen and unambiguous | **Met** for design 1.0, at the owner design review on 2026-10-28 (design SHA-256 `a1109bf1…`) | `design.md` §2–§6; tests `test_design_trace`, `test_widths_v2`, `test_purity_v2` |
| 1 Mathematical and structural analysis | review completed; critical defects resolved | **Not started.** The known structural facts are in section 9.2 | — |
| 2 Reference implementation | independent implementations agree | **Partly met.** Three in-project implementations agree; none comes from outside the project; there is no VHDL | `vectors/`, `tests/v2_reference.py`, `reports/003-extended-batteries-calibration/streams/equivalence.json` |
| 3 Statistical validation | campaign completed; anomalies assessed | **In progress.** SP 800-22 PASS; positive control calibrated; PractRand/TestU01 attempt 1 running; structural (level 3) tests not started | `reports/002-core-dynamics-redesign/`, `reports/003-extended-batteries-calibration/` |
| 4 Cryptanalysis | threat model and attack campaign completed | **Not started.** A draft threat model is in section 5 | — |
| 5 Hardware validation | RTL matches the model | **Not started.** RTL is pending, with the exceptions recorded as O1 in feature 002 | `design.md` §7 |
| 6 Independent evaluation | external review and reproduction | **Not started** | — |
| 7 Security qualification | claims supported by evidence | **Research candidate**; no claim | this document |

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
- **Forward and backward secrecy** (AIS 20/31 classes DRG.1 and DRG.2): future (respectively,
  earlier) outputs cannot be computed from observed outputs, without state compromise. The AIS
  "forward secrecy" is unrelated to forward secrecy in key exchange.
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

------------------------------------------------------------------------

## 4. Security policy and permitted use

The constitution's Security Policy (version 1.2.0) applies. Its three general rules, verbatim:

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
- the seed;
- the internal state;
- the integrity of the output, meaning it cannot be forced or biased.

| ID | Attacker capability | Typical goals |
|----|---------------------|---------------|
| T1 Known output | Sees a contiguous or sparse output stream, and knows the step index modulo 128 (the phase period) | predict, recover the seed or state, distinguish |
| T2 Related seeds | Sees outputs for seeds with known relations: counters, rotations of the four seed words, single-bit differences | distinguish, recover the seed |
| T3 State compromise | Learns the full state once | recover earlier outputs, predict later ones |
| T4 Implementation access | Timing, power, EM or fault injection on a software or FPGA implementation | leak or force the state |
| T5 Seed influence | Can choose or bias the seed, for example through weak seeding | force degenerate or low-entropy states |

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
- **Backtracking resistance is unknown**. If the step function is invertible, a single state
  compromise reveals every earlier output (S9).

------------------------------------------------------------------------

## 6. Standards and technical references

The programme follows established standards, not criteria invented for this algorithm. Status was
checked against the NIST CSRC pages on 2026-10-31.

| Reference | Status | Role | What it means here |
|-----------|--------|------|--------------------|
| NIST SP 800-90A Rev. 1 | Final, June 2015. Rev. 2 initial preliminary draft (call for comments) released 4 September 2025, comments closed 4 November 2025. It proposes an XOF (SHAKE) based DRBG and alignment with SP 800-90C | Approved DRBG mechanisms: Hash_DRBG, HMAC_DRBG, CTR_DRBG. Dual_EC_DRBG was withdrawn in Rev. 1 | A custom generator cannot be an approved DRBG. For secrets, use one of these mechanisms |
| NIST SP 800-90B | Final, January 2018. NIST noted two errata on 29 May 2025, for a future update | Entropy sources: min-entropy estimation (IID and non-IID tracks), restart tests, health tests (repetition count, adaptive proportion) | PhycoWeb-PRNG is deterministic. It is not an entropy source and cannot be validated as one |
| NIST SP 800-90C | Final, September 2025 | Complete RBG constructions: RBG1, RBG2, RBG3, RBGC | Defines how an approved RBG combines an entropy source and a DRBG. A bio-inspired component would add no assurance to such a construction (section 21) |
| NIST SP 800-22 Rev. 1a | Final, April 2010. On 19 April 2022 NIST decided to revise it. The revision is to clarify its purpose, "in particular rejecting its use for assessing cryptographic random number generators"; drafting had not started when the decision was announced | Statistical tests | Used here only to detect defects. This project's calibration and DFT cross-check show its limits (section 11.4) |
| NIST FIPS 140-3 | Approved March 2019 | Cryptographic module validation (CMVP) | An RBG in a validated module must use an approved DRBG, and its entropy source must be validated (ESV programme). A custom generator cannot be approved |
| NIST SP 800-57 Part 1 Rev. 5; SP 800-131A Rev. 2 | Final (2020; 2019) | Security strengths; algorithm transitions | 112 bits is the minimum security strength for approved use, accepted for applying protection only through 2030; from 2031 the minimum is 128 bits. The constitution's floor for any claim is 128 bits (FUT-SEC-1). `phyco-v2` is bounded at 64 |
| BSI AIS 20 / AIS 31 | German Common Criteria methodology for RNGs | Functionality classes DRG.1–DRG.4 for deterministic RNGs, PTG.1–PTG.3 for physical true RNGs and NTG.1 for non-physical true RNGs (class names as in the functionality-class proposal; check the current BSI version) | DRG.3 (enhanced backward secrecy) or DRG.4 (adds enhanced forward secrecy through reseeding) would be the bar for any future claim |
| ISO/IEC 18031 | International standard | Random bit generation | International counterpart to the SP 800-90 series |
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
| 0 | Specification and algorithm definition | Specification frozen and unambiguous |
| 1 | Mathematical and structural analysis | Review completed; critical defects resolved |
| 2 | Reference implementation verification | Independent implementations agree with the specification |
| 3 | Statistical validation | Pre-registered campaign completed; anomalies assessed |
| 4 | Cryptanalysis | Threat model and attack campaign completed; findings assessed |
| 5 | Hardware validation | Hardware shown to implement the specified algorithm |
| 6 | Independent security evaluation | External review and reproduction completed |
| 7 | Security qualification | Claims supported by evidence; limitations stated |

Passing a gate means only that its stated criteria were met. It does not establish any other
property.

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
  frozen hash (feature-002 open issue O5).

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
| S9 | It is unknown whether the step function is a bijection. If it is not, states can merge and cycles can be shorter. If it is, one state compromise reveals every earlier output, so there is no backtracking resistance either way unless shown otherwise. | not analysed | Not evaluated |
| S10 | The only cycle evidence is for the all-equal edge seeds: no period ≤ 2¹⁵ in the first 2¹⁶ words. | `design.md` §9 | Limited evidence |
| S11 | Without the peristaltic rotation and vein-tone feedback (variant v001), the network locks onto the periodic food forcing and fails all 15 SP 800-22 families. The statistical quality comes from two added ARX terms, not from the slime-mold dynamics alone. | `design.md` §8–§9, `research/002/runs.jsonl` | Confirmed (experiment) |
| S12 | Conductance classes 2 and 3 are in effect unused. Every vein value stays in 0…2³¹, so class 3 is unreachable and class 2 can occur only at exactly D = 2³¹, for one step. SHIFT = 4 never applies and the class is in effect bit 30 of D. Bit 31 of D is set only in that edge case, so the vein-tone XOR in effect never reaches bit 31 of T[k], which the rotation moves to bit 4, 10, 18 or 26 of P′[k]. For S6 this leaves one effective control bit per vein, not two. Details below the table. | `design.md` §4 steps 3–5, [`research/security/vein-class-census.json`](research/security/vein-class-census.json) | Confirmed (proof and experiment) |

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
| 2 Established batteries | NIST SP 800-22; TestU01 SmallCrush, Crush, BigCrush; PractRand (Dieharder optional) | SP 800-22 done; PractRand/TestU01 attempt 1 in progress |
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
  TestU01 `eps` row also counts as a failure.

### 11.4 Results to date

| Item | Result | Evidence |
|------|--------|----------|
| SP 800-22 acceptance attempt 1 (`heldout-1`, 100 × 2²¹ bits) | **PASS**: phyco-v2 passed 15/15 families, the positive control passed, lut-v1 failed 11/15. The re-score was identical | `reports/002-core-dynamics-redesign/attempt-1/` |
| Positive-control calibration (1,000 runs of OS data) | Chance failure rate under the feature-002 rules: **20.7% (95% CI 18.2–23.3%)**. A perfect candidate passes an attempt only **63%** of the time (CI 59–67%) | `reports/003-extended-batteries-calibration/calibration/` |
| DFT cross-check | Our DFT agrees with STS 2.1.2 on 1,000 fresh sequences. The test's own variance constant is about 6% too small: E[d²] = 1.062 (CI 1.053–1.071), and it rejects 1.23% of random sequences at α = 0.01 | `calibration/dft-crosscheck.md` |
| Battery dev rehearsal (1 dev seed; not evidence) | phyco-v2 had no failures in PractRand to 1 TiB or in SmallCrush, Crush and BigCrush in both bit orders | `reports/003-extended-batteries-calibration/dev/` |
| Battery attempt 1 (`heldout-1` battery set) | Started 2026-10-30. The positive control passed (70 of 70 runs). The negative control failed as required (section 11.5). The candidate runs are in progress. **The verdict needs the owner result review (T038) and is not stated here** | `reports/003-extended-batteries-calibration/attempt-1/` |

### 11.5 Negative control (lut-v1) in battery attempt 1, not yet reviewed

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
| Side-channel and fault | Timing, power, EM or fault leakage (section 13) |

### 12.2 Generic bounds every claim must respect

- **Seed or key size**: security strength ≤ the entropy of the seed. For phyco-v2 that is
  64 bits; any claim needs FUT-SEC-1, a key of at least 128 bits (section 20.1).
- **State size**: the Babbage–Golić time–memory–data trade-off breaks a generator whose secret
  state is smaller than about twice the claimed strength. For a 128-bit claim, the secret state
  must have at least 256 bits that are actually reachable. phyco-v2 has 256 secret bits
  nominally, but only 2⁶⁴ reachable states per step index (S1).
- **Output volume**: a claim must state how much output per seed it covers.

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
   solve (S6, S12).
4. **Related-seed and rotational experiments**: rotated seed words, single-bit seed differences
   and rotational pairs (S7, S8).
5. **Invertibility and cycle structure**: decide whether the step function is a bijection (S9),
   and map the functional graph on reduced variants that are small enough to enumerate.
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

| Classification | Meaning |
|----------------|---------|
| Research candidate | Defined and under evaluation |
| Statistically evaluated | Pre-registered statistical campaign completed; significant anomalies assessed |
| Cryptographically evaluated | Threat model and substantial cryptanalysis completed |
| Cryptographically qualified | Claim supported by independent evidence and the applicable validation |

**Current classification:**

- `float-v0`: archived, not evaluated further.
- `lut-v1`: rejected statistically; used as the negative control.
- `phyco-v2`: research candidate, with statistical evaluation in progress. It could at most
  become "statistically evaluated" when feature 003 closes.

**Rules for any qualification:**

- A custom algorithm is not called cryptographically secure merely because it reaches the third
  classification.
- A qualification states the exact version, configuration, intended use, properties,
  assumptions, limitations and external reviews.
- Under FIPS 140-3, a custom generator cannot be an approved RBG at all (section 6). For
  deployments that need approval, "qualified" is only reachable along Option B (section 21).

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
- A phase is never marked passed because its documents exist.
- Tool output, logs, artifacts and revisions must support every claim of execution. Where
  evidence is missing, the status is "not evaluated", "inconclusive" or "blocked".

### 16.4 Instructions for a cryptanalysis session

```text
# Cryptanalysis — Instructions

## Role
You are an independent cryptanalyst evaluating PhycoWeb-PRNG (phyco-v2,
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

## Mandatory rules
- Never assume the generator is secure, and never treat statistical
  success as evidence of security.
- Never claim an attack succeeds without executable or mathematical
  evidence. Never invent results.
- Separate confirmed findings from hypotheses (security.md section 9.1).
- State the attacker capabilities (T1-T5), complexities and limits.
- Record the exact revisions and every parameter needed to reproduce.
- Follow the repository constitution: work from an approved spec, use
  dev seeds only for exploration, never use held-out seed sets, ask
  the owner before any download, and never commit, push or publish.

## Output per investigation
Attack description; target property; attacker capabilities; required
observations; analysis; code; results; data, time and memory complexity;
reproduction steps; implications and limitations.

## Final objective
Attempt to disprove any security claim. If no attack is found, report
"no attack identified within the scope of this investigation", never
"secure".
```

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
|-- .specify/memory/constitution.md   governing principles (v1.2.0)
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
- GHDL and cocotb, for VHDL simulation and testbenches;
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

| Priority | Investigation | Status (2026-10-31) | Evidence or next step |
|----------|---------------|---------------------|-----------------------|
| Critical | Resolve mathematical ambiguities | **Resolved** for lut-v1 and phyco-v2 | feature 001 FR-007/FR-008; `design.md` §2–§6 |
| Critical | Remove floating point | **Resolved**: integer lookup table; AST purity tests | feature 001; `test_purity`, `test_purity_v2` |
| Critical | Python/VHDL semantic differences | **Resolved in the specification**, and bit-exact in C; VHDL pending | section 10.3; `streams/equivalence.json` |
| Critical | Effective reachable state space | **Open.** Upper bound: 2⁶⁴ states per step index | section 9.2 S1–S3 |
| Critical | Seed and key interface (new) | **Open.** 64 bits bounds every claim. A fix (a ≥ 128-bit key, plus a reseed input for prediction resistance) is an algorithm change and needs a new spec and owner review (Principles VI, VIII) | section 9.2 S1–S4 |
| High | Convergence and attractors | **Partly**: v001 collapse observed; disruption rate 13.5–13.8%; edge-seed period check only | `design.md` §9 |
| High | Output/state correlation | Not started | section 12.3 item 3 |
| High | State reconstruction | Not started | section 12.3 items 1–2 |
| High | Prediction resistance | Not applicable as specified (S4) | — |
| High | Distinguishing attacks | Statistical batteries only | section 12.3 item 6 |
| Medium | Statistical batteries | SP 800-22 done; PractRand/TestU01 attempt 1 in progress | section 11.4 |
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

**Option B: a bio-inspired mechanism alongside an established construction.** An approved DRBG,
seeded from a validated entropy source, provides the security (SP 800-90A/B/C). The bio-inspired
generator could only be an additional, non-security input or a research component.

- It is deterministic, so it adds no entropy, and it cannot count as an entropy source.
- The composition must still be analysed so that it cannot weaken the approved construction.

For keys and other security-critical values, the preferred engineering choice is an established,
correctly instantiated DRBG with a validated entropy source, not an unreviewed custom generator.
Neither option is assumed secure.

------------------------------------------------------------------------

## 22. Roadmap

| Stage | Work | Status |
|-------|------|--------|
| 1 | Governance: constitution, gates, evidence rules, this document | Done (constitution 1.2.0; this document 2.5) |
| 2 | Remove floating point, fully specify integer semantics | Done (feature 001) |
| 3 | Redesign the core dynamics; reference model and vectors | Done (feature 002, phyco-v2) |
| 4 | Statistical validation: SP 800-22, calibration, PractRand, TestU01 | SP 800-22 done (002); calibration done (003); battery attempt 1 in progress (003) |
| 5 | Threat model and security-claims spec; structural analysis (seed bound, invertibility, cycles) | Next (sections 5, 9.2, 12.3) |
| 5a | Only if a cryptographic claim or certification is pursued: a key-interface redesign meeting FUT-SEC-1 to FUT-SEC-9 and the grid-scaling and hardware requirements FUT-GRID-1 to FUT-GRID-5 and FUT-HW-1 to FUT-HW-5, probably a new core design with a new model ID | Conditional; not scheduled. Its requirements are binding (constitution 1.2.0, section 20.1) |
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

The next security-related artifact recommended for this repository is a Spec Kit feature for the
threat model and security claims. It would:

- adopt section 5;
- state that no claim is made for design 1.0;
- schedule the investigations in section 12.3, starting with the reduced-domain seed recovery.

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

> Passing statistical batteries does not show cryptographic security. This generator must not be
> used to generate secrets; use an established cryptographic random-number generator for keys,
> nonces, tokens and salts.
