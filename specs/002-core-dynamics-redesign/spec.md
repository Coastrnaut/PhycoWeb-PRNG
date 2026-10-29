# Feature Specification: Core Dynamics Redesign

**Feature Branch**: `002-core-dynamics-redesign`

**Created**: 2026-10-28

**Status**: Approved for planning (2026-10-28); design-freeze and result reviews pending

**Input**: User description: "Redesign the PhycoWeb-PRNG core dynamics so the integer reference
model passes the NIST SP 800-22 battery under acceptance rules that are fixed before any tuning.
Integer-only and multiplierless; fix the always-on disruption; improve output mixing using only
grid-internal integer operations; no cryptographic or external PRNG whitening; keep the lut-v1
perturbation table. The test suite may only become stricter. Development seeds for tuning,
held-out seeds for acceptance, multi-sequence pass-rate criterion. A pass must not be presented
as cryptographic security."

## Context

Feature 001 produced `lut-v1`, an integer-only reference model. Its NIST SP 800-22 screening
(single sequence of 10⁶ bits per seed) failed Linear Complexity and Random Excursion in every run,
and failed up to six tests with one seed.

> **Note (2026-10-28, added during planning; it changes no requirement).** The Linear Complexity
> and Random Excursion failures above come from defects in nistrng 1.2.3. That tool fails these
> tests even on OS cryptographic random data (research R1, N6 and N8), so the failures say
> nothing about lut-v1. The other lut-v1 failures are unconfirmed until re-scored with the
> feature-002 harness. See the erratum in `reports/001-integer-lut-perturbation/summary.md`.

Feature 001 also recorded structural defects that this feature addresses:

- the flux stage multiplies two state variables, conflicting with the multiplierless rule
  (Open Issue 1);
- the disruption fires on about 99.5% of steps, so the "frustration" mechanism is effectively
  always on (Open Issue 4);
- each output word exposes only the low 8 bits of each vein, with no mixing between nodes.

**Acceptance is defined in this spec before any redesign work starts** (Section "Pre-registered
Acceptance Protocol"). After approval, those rules may only be made stricter, never weaker
(Constitution Principle IV). A design that does not meet them is reported as failing.

## Review & Approval *(Constitution Principle VIII)*

| Gate | Reviewer | Date | Decision | Notes |
|------|----------|------|----------|-------|
| Spec approval (algorithm change + acceptance protocol) | Coastrnaut (repository owner) | 2026-10-28 | Approved | Approved in session; protocol frozen as written, may only become stricter |
| Spec amendment 1 (protocol clarification, stricter only) | Coastrnaut (repository owner) | 2026-10-28 | Approved | Approved in session (analysis findings I1, I2). Changes: a failed positive control halts the attempt before the candidate is evaluated, and the set counts as used (Edge Cases, FR-017); proportion **or** uniformity failures count toward k_max. Made before any result was produced |
| Design freeze (before each held-out attempt) | _pending_ | _pending_ | _pending_ | One row per attempt |
| Result review | _pending_ | _pending_ | _pending_ | Required before the feature is declared complete |

## User Scenarios & Testing *(mandatory)*

Users: (a) the repository owner deciding whether the bio-inspired design is statistically
credible; (b) hardware engineers who will implement the design in RTL; (c) researchers who must
be able to reproduce and audit the verdict.

### User Story 1 - Redesigned, fully specified generator (Priority: P1)

A hardware engineer receives a new generator design in which every operation is integer-only,
uses no multiplication or division, keeps every value within a stated width of at most 32 bits,
and whose disruption mechanism fires only some of the time, as the design intends.

**Why this priority**: Without it there is nothing to evaluate, and the current design has a
multiplier and an always-on disruption.

**Independent Test**: Review the specification and run the static checks on the reference model.
Run the model for 10⁶ steps on the development seeds and measure the disruption rate.

**Acceptance Scenarios**:

1. **Given** the new reference model, **When** the static purity checks run, **Then** they find
   no floating point, multiplication, division, modulo or power operations anywhere in the
   per-step path.
2. **Given** any development seed, **When** the model runs for 10⁶ steps, **Then** the
   disruption fires on between 1% and 50% of steps.
3. **Given** the design document, **When** each state element and operation is checked, **Then**
   its width, signedness, wrap rule, comparison semantics and update order are all stated.

---

### User Story 2 - Pre-registered statistical verdict (Priority: P2)

The owner obtains a pass/fail verdict on the redesigned generator from a held-out evaluation
whose rules, seeds and thresholds were fixed before the design was tuned, so the verdict cannot
be the result of tuning against the tests.

**Why this priority**: This is the outcome the feature exists to produce, and its value depends
entirely on the protocol being honest.

**Independent Test**: Run the acceptance evaluation on the frozen design with held-out set 1 and
read the verdict, which comes with the positive- and negative-control results.

**Acceptance Scenarios**:

1. **Given** a frozen design, **When** the acceptance evaluation runs, **Then** it reports, for
   each of the 15 tests and each of their sub-tests, the pass proportion, the uniformity p-value
   and a pass/fail verdict, plus an overall verdict.
2. **Given** the positive control (an established operating-system cryptographic RNG),
   **When** it is evaluated under the same protocol, **Then** it meets the acceptance criterion.
   If it does not, the evaluation is declared **inconclusive**, not passed.
3. **Given** the negative control (the `lut-v1` model from feature 001), **When** it is
   evaluated under the same protocol, **Then** it fails the criterion. If it passes, the harness
   is declared unable to discriminate, and the verdict is **inconclusive**.
4. **Given** a held-out set has been used once, **When** the design is changed afterwards,
   **Then** that set may not be used again. Only the next unused held-out set may be used, after
   a new design-freeze approval.

---

### User Story 3 - Strictly improved, reproducible test harness (Priority: P3)

A researcher re-runs the evaluation and gets identical results. They can also confirm that every
change to the harness made it stricter or more faithful to SP 800-22, never more lenient.

**Why this priority**: The harness changes are prerequisites for the verdict, but they are
supporting work.

**Independent Test**: Run the harness twice on the same inputs and compare. Check the change log
of harness rules against the list of permitted changes.

**Acceptance Scenarios**:

1. **Given** the same sequences, **When** the evaluation is run twice, **Then** every p-value and
   verdict is identical.
2. **Given** 2,097,152-bit sequences, **When** Overlapping Template Matching is evaluated,
   **Then** it is eligible and reported (it was not eligible at 10⁶ bits).
3. **Given** Non-Overlapping Template Matching, **When** it is evaluated, **Then** all 148
   aperiodic templates of length 9 are tested, each as a separate sub-test.

### Edge Cases

- **Ineligible sequences**: Random Excursion tests apply only to sequences with enough cycles.
  Ineligible sequences are excluded from that test's denominator. If fewer than 55 of 100
  sequences are eligible, the test **fails**; it is not skipped.
- **Design reaches no pass**: If the third held-out attempt fails, work stops and the feature is
  reported as not meeting its goal. No further attempts are made without a spec amendment.
- **Warm-up**: A design may discard a fixed number of initial outputs (warm-up). If it does, the
  number is part of the frozen design, applies to every sequence, and is the same in RTL.
- **Seed with all-equal values** (e.g., `[0,0,0,0]`) must not produce a constant or short-cycle
  output. Development checks include such seeds.
- **Positive control fails by chance**: About 1 in 5 attempts with a perfect generator fail at
  least one test under this protocol (see Assumptions). If the positive control fails, the
  attempt is **INCONCLUSIVE** and **halts before the candidate is generated or scored**. The
  negative control is still evaluated and reported. The held-out set counts as used. Any
  protocol amendment is made, and approved, before the next attempt. *(Amendment 1, 2026-10-28.)*

## Requirements *(mandatory)*

### Functional Requirements

**Generator design**

- **FR-001**: The redesigned generator MUST use only integer operations: add, subtract, XOR, AND,
  OR, NOT, constant shifts, constant rotations, comparisons, table lookups and conditional
  selection. Multiplication (including by constants), division, modulo and power MUST NOT appear
  in the per-step path.
- **FR-002**: Every state element and intermediate value MUST have a specified width of at most
  32 bits, with its signedness, wrap rule and comparison semantics stated. Values MUST NOT depend
  on wider or unbounded arithmetic.
- **FR-003**: The generator MUST keep the `lut-v1` perturbation table, phase increments and
  quarter-period offset from feature 001 unchanged.
- **FR-004**: The design MUST keep the bio-inspired structure: node pressures, vein thicknesses,
  flux driven by pressure differences, growth and decay of veins, and a threshold-triggered
  disruption.
- **FR-005**: The disruption MUST fire on between 1% and 50% of steps, measured over 10⁶ steps on
  every development seed.
- **FR-006**: Output words MUST be 32-bit unsigned values produced only from the generator's own
  state, using operations allowed by FR-001.
- **FR-007**: The generator MUST NOT include any cryptographic primitive (hash, block or stream
  cipher, MAC), any external or standard PRNG (e.g., LCG, xorshift, Mersenne Twister, PCG), or any
  value derived from one, in its state update or output path.
- **FR-008**: The reference model MUST be bit-exact and deterministic. It MUST come with golden
  vectors for at least two development seeds (10,000 words each) and an RTL-consumable
  description of the design. RTL itself is out of scope (RTL-pending).
- **FR-009**: The seed domain MUST be four integers in 0…65535 (as in feature 001), and any
  derivation of the initial state from the seed MUST be specified.

**Test harness (may only become stricter)**

- **FR-010**: The NIST evaluation MUST run each of the 15 SP 800-22 tests on sequences of
  **2,097,152 bits** (2²¹), MSB-first per output word, with each test given its own copy of the
  input and fixed, recorded test parameters.
- **FR-011**: Non-Overlapping Template Matching MUST evaluate **all 148** aperiodic templates of
  length 9 defined in SP 800-22, each as a separate sub-test.
- **FR-012**: Every sub-test p-value MUST be recorded individually (Cumulative Sums: 2; Serial: 2;
  Random Excursion: 8; Random Excursion Variant: 18; Non-Overlapping Template: 148).
- **FR-013**: The harness MUST be deterministic. Repeated runs on the same input MUST produce
  identical p-values.
- **FR-014**: Changes to the harness MUST be logged. Each change MUST be one of: fixing a defect,
  moving closer to SP 800-22, or adding tests/sub-tests. No change may remove a test or sub-test,
  shorten sequences, reduce the sequence count, or loosen a threshold.

**Protocol**

- **FR-015**: Design tuning MUST use only the **development seed set** (see Pre-registered
  Acceptance Protocol) and the two feature-001 seeds. Held-out seeds MUST NOT be used before a
  design-freeze approval.
- **FR-016**: Before each held-out attempt, the design MUST be frozen: the reference model's
  source hash, the design document version and the harness version are recorded, and the owner
  approves the freeze.
- **FR-017**: Each held-out attempt MUST use the next unused held-out set, exactly once. The
  positive control MUST be evaluated first, then the negative control, then the candidate. Every
  result that was produced MUST be reported whatever the outcome. If the positive control fails,
  the candidate is not evaluated (see Edge Cases). *(Amendment 1.)*
- **FR-018**: At most three held-out attempts are allowed (sets 1–3). Results of every attempt,
  including failed ones, MUST be kept and reported.
- **FR-019**: All reports MUST state that passing SP 800-22 does not show cryptographic security,
  and that the generator must not be used to generate secrets (Security Policy).

### Pre-registered Acceptance Protocol

These values are fixed by this spec. After approval they may only be changed to be stricter.

**Seed sets.** Seed *i* of set *S* is the first 8 bytes of SHA-256 of the ASCII string
`phycoweb-002/<S>/<i>`, read as four big-endian unsigned 16-bit integers, for i = 0…99. Set
identity is fixed by the SHA-256 of the set's canonical text (one line per seed:
`a b c d\n`, in order):

| Set | Purpose | First seed | SHA-256 of canonical text |
|-----|---------|-----------|---------------------------|
| `dev` | tuning (unrestricted use) | 56053 7029 30841 11050 | `7e7e33c75e9e58048a26c1926e6addd4dc3514502574ea6687ded889aa47950e` |
| `heldout-1` | acceptance attempt 1 | 44401 31074 35395 61291 | `84a30b2e037550d0c6b1cfba1444eb0447fbc15b5b7c631ad8fc8a577dfca23d` |
| `heldout-2` | acceptance attempt 2 | 61805 51202 28895 20558 | `13120fcb1c1a49f6e6109f059982909470da33784bd0490f1e0f10252e214ad4` |
| `heldout-3` | acceptance attempt 3 | 5899 31471 52105 42678 | `af3b9b8e62829ef732a5c2bb2963c7655c9b461635da0c40d960b4c7eaace88f` |

The four sets have no seeds in common.

**Sample.** For each attempt, 100 sequences (one per seed of the held-out set), each of
2,097,152 bits, taken from the generator's output after the frozen warm-up (if any). The
positive control produces 100 sequences of the same length from the operating system's
cryptographic RNG. The negative control is `lut-v1` run on the same 100 seeds.

**Per sub-test criteria** (SP 800-22 Section 4.2), with significance level α = 0.01 and m′ = the
number of eligible sequences:

1. **Proportion**: the share of eligible sequences with p ≥ 0.01 is at least
   0.99 − 3·√(0.99·0.01 / m′). For m′ = 100 this is 0.96015, so at least **97 of 100** must pass.
   This is stricter than the NIST tool's rounded value of 96.
2. **Uniformity**: the chi-square test of the p-values over 10 equal bins gives
   P-valueᴛ ≥ 0.0001. It requires m′ ≥ 55.

**Per test (family) verdict.** For a single-p-value test, the test passes if its sub-test meets
both criteria. For multi-sub-test tests, the test passes if the number of failing sub-tests is at
most k_max, where k_max is the smallest k with P(Binomial(n_sub, q) > k) ≤ 0.01. Here
q = 0.01837 is the probability that one sub-test fails the proportion criterion for an ideal
generator with m′ = 100:

| Test | Sub-tests | k_max |
|------|-----------|-------|
| Cumulative Sums | 2 | 1 |
| Serial | 2 | 1 |
| Random Excursion | 8 | 1 |
| Random Excursion Variant | 18 | 2 |
| Non-Overlapping Template Matching | 148 | 7 |

If m′ < 100 for a test, k_max and the proportion bound are recomputed with the same formulas for
that m′.

A sub-test **fails** if it fails the proportion criterion **or** the uniformity criterion. Both
kinds of failure count toward k_max. *(Amendment 1: clarification, using the stricter reading.)*

**Overall verdict.**
- **PASS**: all 15 tests pass, the positive control passes, and the negative control fails.
- **FAIL**: the positive control passes, the negative control fails, and at least one of the 15
  tests fails for the candidate.
- **INCONCLUSIVE**: the positive control fails or the negative control passes.

### Key Entities

- **Generator design (`phyco-v2`)**: state elements with widths; the per-step update in order;
  output function; warm-up length; disruption rule.
- **Seed set**: name, derivation, canonical SHA-256, purpose, used/unused status.
- **Design freeze record**: attempt number, model source hash, design document version, harness
  version, approval.
- **Evaluation record**: per sequence and sub-test p-values; per sub-test proportion and
  uniformity; per test verdict; overall verdict; controls; commands; tool versions.
- **Harness change log**: change, category (defect fix / SP 800-22 fidelity / added coverage),
  date.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The redesigned generator contains zero multiplication, division, modulo, power or
  floating-point operations in its per-step path, and every value fits the stated width of at
  most 32 bits.
- **SC-002**: The disruption rate is between 1% and 50% on 100% of development seeds over
  10⁶ steps.
- **SC-003**: An acceptance attempt on a frozen design produces a PASS, FAIL or INCONCLUSIVE
  verdict under the pre-registered protocol, with positive- and negative-control results, within
  three held-out attempts. The feature's goal is met only by a **PASS**.
- **SC-004**: Re-running the evaluation of any attempt reproduces 100% of p-values and verdicts
  exactly.
- **SC-005**: 100% of harness changes are logged, and each is in a permitted category (FR-014).
- **SC-006**: 0 held-out seeds are used before the matching design-freeze approval. This is
  checked by the freeze records and the evaluation logs.
- **SC-007**: No report, document or comment describes the generator as cryptographically secure
  or fit for generating secrets.

## Assumptions

- **Effort is unbounded on the development set**; only held-out attempts are limited. Every
  development run is logged, so how much tuning happened is visible.
- **Expected false-fail rate**: a perfect generator fails at least one of the 15 tests about
  **19%** of the time under this protocol. Each single-p-value test fails about 1.85% of the time;
  the five multi-sub-test tests add about 2.0% between them. So a perfect candidate, with a
  perfect control, gets a PASS on one attempt only about 66% of the time (both must pass). That is
  why there is a positive control and why up to three attempts are allowed. The figure is an
  approximation, because sub-tests are not fully independent.
- **Run time**: one attempt is 3 × 100 sequences × 2²¹ bits, including 148 templates. Several
  hours of computation per attempt is acceptable. The plan decides how to parallelize, without
  changing any statistical rule.
- **Positive control**: the operating system's cryptographic RNG is used only as a control in the
  harness, never in the generator.
- The feature-001 seeds (`[1024, 2048, 4096, 8192]` and `[4660, 43981, 21845, 43690]`) count as
  development seeds, because their results are already known.
- **Feature 001 artifacts** (`lut-v1` model, vectors, archive) stay unchanged. The redesign is a
  new model id (`phyco-v2`), and `lut-v1` is kept as the negative control.
- Failing the protocol is a valid, reportable outcome of this feature.
- **Out of scope**: RTL implementation and cryptographic analysis. The README's unsupported
  claims ("cryptographically secure", "high-entropy", "Crypto Whitening Box", "validated … ready
  for deployment") were corrected on 2026-10-28 at the owner's request, separately from this
  feature's requirements. The file was renamed from `readmee.md` to `README.md` the same day.
