# Phase 0 Research: Core Dynamics Redesign

**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Date**: 2026-10-28

The defect IDs continue the series from feature 001 (N1–N3, in
[001 research R6](../001-integer-lut-perturbation/research.md)).

## R1. The NIST harness cannot keep using nistrng 1.2.3

**Finding.** While sizing the harness, each nistrng test was run on sequences of 2²¹ bits taken
directly from `os.urandom`. An ideal source should give p-values spread evenly over [0, 1].
Five of the 15 tests do not:

| ID | Test | Observed on urandom input | Effect |
|----|------|---------------------------|--------|
| N4 | Non-Overlapping Template Matching | p = 1.000000 every time. The code computes the variance and then divides by `sigma**2`, i.e. by the variance squared. The template set only goes up to length 8; there is no length-9 set of 148 templates. | Can never fail. Cannot meet FR-011. |
| N5 | Overlapping Template Matching | p = 0.0 on 5/5 sequences | Always fails |
| N6 | Random Excursion | p = 0.0 on 39 of 40 sub-tests across 5 sequences (one was 0.0006) | Always fails |
| N7 | Maurer's Universal | p between 0.9979 and 0.9989 on 5/5 sequences | Fails uniformity |
| N8 | Linear Complexity | p = 0.0 on 5/5 sequences | Always fails |

Method: nistrng 1.2.3 on Windows / Python 3.10.11 / numpy 2.2.6. Each test was run on its own
copy, with `random.seed(0)`, and all `_score_list` p-values were read. The check is
reproducible with quickstart step H0, and the result is the first entry of the harness change
log. N4 has been traced to source code. The causes of N5–N8 have not been diagnosed,
but the symptom is conclusive: an established CSPRNG fails these tests, so they are not
measuring the input.

**Consequence for feature 001.** Every feature-001 run failed Linear Complexity and Random
Excursion. N6 and N8 show that those failures say nothing about either model. The other failures
(lut-v1, seed 1024: 4 more tests) were in tests that behaved normally on urandom here, so they
still stand, but they are unconfirmed until rerun with the new harness. The feature-001 reports
are approved records and stay unchanged. The plan adds an **erratum** to
`reports/001-integer-lut-perturbation/summary.md` once the owner approves (Principle VIII). The
new harness then re-scores the four feature-001 inputs (task in /speckit-tasks).

**Decision.** Implement all 15 SP 800-22 Rev. 1a tests in our own package, `sp80022/`, following
the formulas in SP 800-22 sections 2 and 3 and the default parameters of NIST STS 2.1.2 (R2).
nistrng stays installed only as an optional, informative cross-check (R3c). It never determines
a verdict.

**Rationale.** With nistrng, the positive control fails in every attempt, so every attempt would
be INCONCLUSIVE (spec, Overall verdict), and FR-011 cannot be met at all. Replacing the
implementation counts as a defect fix and a move closer to SP 800-22 (FR-014). It removes no test
or sub-test, and it adds 147 template sub-tests.

**Alternatives considered.**
- *Patch nistrng locally*: a vendored fork with five unexplained defects is harder to trust
  than a fresh implementation written against the specification and validated against
  published values.
- *NIST STS 2.1.2 (C)*: the reference tool. It would need to be downloaded and built, it reports
  rounded proportions, and its output is text that would need parsing. It remains the best
  **independent oracle** and is proposed as an optional cross-check (R3d), subject to the
  owner's approval to download it.
- *Another Python package*: no candidate with a known-good record on all 15 tests was available
  offline. Any choice would need the same validation as our own code.

## R2. Test parameters (fixed and recorded)

Taken from SP 800-22 recommendations, with the values NIST STS 2.1.2 selects for n = 2,097,152.
Each value is written into every evaluation record (FR-010).

| Test | Parameters |
|------|-----------|
| Frequency (Monobit) | none |
| Frequency within a Block | M = 128 |
| Runs | none (frequency prerequisite τ = 2/√n; if it fails, p = 0.0, as SP 800-22 §2.3.4 says) |
| Longest Run of Ones | M = 10,000, K = 6, ν classes ≤10 … ≥16 (n ≥ 750,000 table) |
| Binary Matrix Rank | 32 × 32 matrices, N = 2,048, remaining bits discarded |
| DFT (Spectral) | threshold T = √(ln(1/0.05)·n), N₀ = 0.95·n/2 (Rev. 1a correction) |
| Non-Overlapping Template | m = 9, N = 8 blocks, M = 262,144; all 148 aperiodic templates (R6) |
| Overlapping Template | m = 9, M = 1,032, K = 5, N = 2,032 blocks; Rev. 1a π values 0.364091, 0.185659, 0.139381, 0.100571, 0.070432, 0.139865 |
| Maurer's Universal | L = 8, Q = 2,560 (n ≥ 2,068,480 row of the table), K = 259,584 |
| Linear Complexity | M = 500, K = 6, N = 4,194 blocks |
| Serial | m = 16, 2 p-values |
| Approximate Entropy | m = 10 |
| Cumulative Sums | forward and reverse, 2 p-values |
| Random Excursion | states ±1…±4, 8 p-values; not eligible if J < 500 |
| Random Excursion Variant | states ±1…±9, 18 p-values; not eligible if J < 500 |

An ineligible sequence is excluded from that test's m′ for that attempt; the spec's rules then
apply (m′ < 55 fails uniformity; k_max and the proportion bound are recomputed for m′).

## R3. How the harness is validated

The harness must be shown to work before it is allowed to judge anything (Principle IV).

a. **Worked examples.** Each SP 800-22 test section ends with a worked example that gives an
   input and its p-value. All of them become unit tests.
b. **Appendix B reference values.** SP 800-22 Appendix B lists p-values for the first 10⁶ bits of
   the binary expansions of π, e, √2 and √3. These expansions are computed with exact integer
   arithmetic in the test code, so no external data file is needed. Every listed p-value must be
   matched to the 6 printed decimals. The values are transcribed from the published document
   during implementation, with the page cited. They are **not** typed from memory.
c. **Calibration on the positive control.** On dev runs, the OS CSPRNG must pass every test and
   sub-test family over 100 sequences. Its pooled p-values over several such runs must pass
   uniformity. This is the check that caught N4–N8.
d. **Independent oracle.** The owner approved NIST STS 2.1.2, built from the nist.gov source in
   WSL (plan, Owner Decisions Q2). It is fed the same bytes through its binary-file input mode,
   with the parameters from R2. The Appendix B inputs and 10 positive-control sequences are
   compared p-value by p-value, for every test. STS prints 6 decimals, so the comparison is to
   ±1e-6.
   Known STS quirks (e.g. its rounded proportion threshold) affect only the summary report, not
   the per-sequence p-values compared here. A disagreement beyond 1e-6 is investigated before the
   harness is accepted. nistrng, on the 10 tests where it behaved normally, is a second,
   informative comparison only.
e. **Known-bad inputs.** All-zero, alternating 0101…, the lut-v1 period-128 artefacts and a
   biased source must fail the expected tests. This checks that a test can fail.

A harness version string (`sp80022` package version plus the SHA-256 of its source files) is
recorded in each freeze record and evaluation record.

## R4. Proportion, uniformity and family verdicts

- **Proportion** bound: 0.99 − 3·√(0.0099/m′). A sub-test passes proportion if
  count(p ≥ 0.01) ≥ ⌈bound·m′⌉ (97 for m′ = 100).
- **Uniformity**: p-values are placed in 10 bins [0, 0.1), …, [0.9, 1.0] (1.0 goes in the last
  bin, as in STS). χ² = Σ (Fᵢ − m′/10)² / (m′/10), and P-valueᴛ = igamc(9/2, χ²/2). It passes if
  P-valueᴛ ≥ 0.0001 and m′ ≥ 55.
- **q(m′)** is the exact binomial probability that an ideal sub-test fails proportion:
  P(Binomial(m′, 0.01) > m′ − ⌈bound·m′⌉). For m′ = 100 this gives 0.01837, which matches the
  spec. **k_max(n_sub, m′)** is the smallest k with P(Binomial(n_sub, q) > k) ≤ 0.01. Both are
  computed exactly with integer binomial coefficients and checked against the spec table in a
  unit test.
- A sub-test fails if it fails proportion **or** uniformity. A family's k_max counts both kinds
  of failure. The spec states this explicitly since Amendment 1 (2026-10-28).
- igamc and erfc come from `scipy.special.gammaincc` and `math.erfc`.

## R5. Run time and parallelism

Measured on this machine (32 logical CPUs) with nistrng on one 2²¹-bit sequence: 128 s in total,
of which Linear Complexity takes 87.5 s, Serial 19.5 s and Approximate Entropy 11.8 s.

- **Decision**: each worker process evaluates one whole sequence (all 15 tests), using
  `multiprocessing.Pool` with the `spawn` start method. Results are keyed by sequence index and
  sorted, so the record does not depend on worker count or completion order (FR-013). The
  worker count is recorded but has no effect on results.
- **Implementation targets**: Linear Complexity runs Berlekamp–Massey on all 4,194 blocks at once
  as numpy bit arrays (500 iterations of vector operations). Serial and Approximate Entropy use
  `numpy.bincount` over m-bit sliding windows. The template tests use window codes. Target: under
  60 s per sequence, so an attempt (300 sequences) takes about 10–20 min on 32 workers. That is
  well inside the spec's "several hours".
- **Generation**: the generator itself is pure Python and produces 65,536 words per sequence.
  A dev iteration of 100 sequences costs about the same as the evaluation, so it is parallelized
  the same way.

## R6. Non-Overlapping Template set

The template set is generated, not copied: every 9-bit string B with B[k:] ≠ B[:9−k] for all
k = 1…8, in increasing numeric order. That gives 148 templates, first `000000001`, last
`111111110`, which matches the count in SP 800-22 and the first entry of the STS template file.
A unit test checks the count, the order, and the counts for m = 2…10 (2, 4, 6, 12, 20, 40, 74,
148, 284). The statistic follows SP 800-22 §2.7: μ = (M − m + 1)/2ᵐ,
σ² = M(1/2ᵐ − (2m − 1)/2²ᵐ), χ² = Σⱼ (Wⱼ − μ)²/σ², p = igamc(N/2, χ²/2), with counting
restarting after a match (non-overlapping).

## R7. Determinism and floating point in the harness

The harness uses float64 (numpy and scipy). This is allowed, because Principle I governs the
generator, not the evaluator.
- **Same environment**: identical bits give identical p-values (FR-013), checked by a test that
  runs the battery twice.
- **Across environments**: p-values may differ in the last bits because of BLAS or libm.
  Verdicts are compared exactly and p-values within 1e-9 absolute. This is recorded as a
  limitation.
- **The positive control is not reproducible from a seed by design**, because it comes from the OS
  CSPRNG. So that SC-004 can still be met, the control bytes for each attempt are saved
  (100 × 256 KiB = 25 MiB), and their SHA-256 is recorded in the evaluation record. Re-scoring
  reads the saved bytes. Where they are stored is a decision for the owner (Open question Q1 in
  plan.md); the default is a git-ignored `data/controls/` with only the hashes committed.

## R8. Protocol enforcement in code

- `protocol/seedsets.py` derives the seed sets (SHA-256 of `phycoweb-002/<S>/<i>`). It refuses to
  return a set whose canonical-text SHA-256 differs from the spec table.
- `protocol/freeze.py` writes a draft freeze record: attempt, set, model source SHA-256, design
  document SHA-256 and version, harness version, warm-up. The **owner** fills in the approval
  fields (name, date). The tool never fills them in itself.
- `scripts/acceptance.py --attempt N` refuses to run in any of these cases: the freeze record is
  missing or unapproved; the model, design or harness hashes differ from the frozen ones; an
  attempt record for that set already exists; or N is not the next attempt. It then runs the
  positive control, the negative control and the candidate, in that order, and writes all three
  results whatever the outcome (FR-016, FR-017, FR-018).
- Dev tooling (`research/002/explore.py`) accepts only `dev` and the two feature-001 seeds.
  It calls the same seed-set guard with an allow-list, so held-out sets cannot be loaded by
  accident (SC-006).

## R9. Design exploration versus the reference model

- **Exploration** (candidate variants, parameter sweeps) happens in `research/002/`. Each run
  appends a line to `research/002/runs.jsonl` with the variant id, its source SHA-256, the seeds,
  a summary of results and the command. This makes the amount of tuning visible (spec,
  Assumptions).
- When one variant is chosen, it is written up in `specs/002-core-dynamics-redesign/design.md`:
  state widths, update order, output function, warm-up, disruption rule, and a statement of why it
  is not a cryptographic primitive or a standard PRNG (FR-007). The owner reviews that document at
  the design-freeze gate (Principles VI and VIII). Only then is it implemented as
  `phycoweb/model_v2.py` (`MODEL_ID = "phyco-v2"`). If the redesign needs changes after a failed
  attempt, the document gets a new version and a new freeze.

## R10. Design directions for phyco-v2 (not decisions)

These are inputs to exploration. The frozen design is decided in design.md, not here.

- **Flux without multiplication (FR-001)**: FR-001 allows only *constant* shifts, so D-dependent
  shifts are excluded. Options:
  - conductance classes by comparison: select among (ΔP >> c₁), (ΔP >> c₂), … depending on
    where D falls relative to fixed thresholds;
  - an add-based coupling, ΔP + (D >> c);
  - a table lookup on the top bits of D.
- **Disruption rate (FR-005)**: the feature-001 rule fires about 99.5% of the time because D
  usually exceeds 4,096. Options: compare against a running reference (e.g. the D of the other
  channel) instead of a fixed constant, or raise and retune the threshold. Measure over 10⁶ steps
  on all 100 dev seeds.
- **Output (FR-006)**: the current output exposes the low 8 bits of each D. Candidate: combine all
  four 16-bit D and P values with XOR, add and constant rotations across nodes. Each output bit
  should depend on several nodes.
- **State size and warm-up**: the seed gives 64 bits. A warm-up of a fixed number of steps before
  the first output word is allowed (spec, Sample) and becomes part of the design.
- **FR-007 boundary**: XOR/add/rotate mixing can drift towards a known ARX PRNG or a xorshift. The
  design document must show that the update is the slime-mold dynamics and not a renamed
  standard generator. The owner judges this at freeze.
- **Risk**: no direction is known to pass. FAIL is a valid outcome (spec, Assumptions).
