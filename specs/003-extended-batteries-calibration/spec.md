# Feature Specification: Extended Batteries and Positive-Control Calibration

**Feature Branch**: `003-extended-batteries-calibration`

**Created**: 2026-10-29

**Status**: Approved for planning (2026-10-29)

**Input**: User description: "Run broader test suites (PractRand, TestU01) on phyco-v2. Measure
how often the positive control fails by chance (O3) before any further acceptance attempt"

## Context

Feature 002 produced `phyco-v2` (design.md 1.0, `phycoweb/model_v2.py`, SHA-256 `1260142d…`).
Its pre-registered NIST SP 800-22 acceptance attempt 1 gave **PASS**
(`reports/002-core-dynamics-redesign/attempt-1/`). The final report
(`reports/002-core-dynamics-redesign/phase-report.md`) left two follow-ups that this feature
covers:

- **O3, positive-control false-failure rate.** The k_max rule assumes independent sub-tests, but
  Random Excursions and Random Excursions Variant sub-tests share one random walk and fail
  together. Two of five 100-sequence positive-control runs failed one family. The real
  false-failure rate of a perfect generator under the protocol is therefore unknown and probably
  above the ~19% assumed in the feature-002 spec. A positive-control failure makes an attempt
  INCONCLUSIVE and still uses up a held-out set, so the rate must be known before any further
  attempt.
- **Broader batteries (§7).** Only SP 800-22 has been run. Constitution Principle IV says broader
  batteries SHOULD also be used; PractRand and TestU01 are much more sensitive than SP 800-22 and
  test far longer output.

**This feature changes no generator.** `phyco-v2` (design.md 1.0) and `lut-v1` are evaluated as
they are. The feature-002 protocol, harness `sp80022` 1.0.0 and its unused seed sets
(`heldout-2`, `heldout-3`) are not changed or used here.

**Acceptance for the new batteries is defined in this spec before any battery result exists**
(Section "Pre-registered Battery Protocol"). After approval those rules may only become stricter
(Principle IV).

## Review & Approval *(Constitution Principle VIII)*

| Gate | Reviewer | Date | Decision | Notes |
|------|----------|------|----------|-------|
| Spec approval (calibration method + battery protocol) | Coastrnaut (repository owner) | 2026-10-29 | Approved | Approved in session, including option A scale and per-sequence p-values in FR-002; protocol frozen as written, may only become stricter |
| Plan approval (plan.md, research R1–R11, data-model, contracts) | Coastrnaut (repository owner) | 2026-10-29 | Approved | Approved in session; proceed to tasks |
| Tool acquisition (PractRand, TestU01 downloads) | Coastrnaut (repository owner) | 2026-10-29 | Approved | Approved in session ("approved, download both"): `PractRand_0.96.zip` (904,832 bytes, sourceforge.net/projects/pracrand, 2025-12-26) and `TestU01.zip` 1.2.3 (3,123,035 bytes, simul.iro.umontreal.ca/testu01, 2015-02-11) |
| Calibration result review (US1) | _pending_ | _pending_ | _pending_ | Required before any battery attempt |
| Battery freeze (before each held-out battery attempt) | _pending_ | _pending_ | _pending_ | One row per attempt |
| Final result review | _pending_ | _pending_ | _pending_ | Required before the feature is declared complete |

## Clarifications

### Session 2026-10-29

- Q: How large is each battery attempt (seeds, PractRand length, TestU01 levels)? → A: Option A:
  10 seeds; PractRand to 1 TiB per seed; TestU01 SmallCrush, Crush and BigCrush per seed, on the
  words and on the bit-reversed words.
- Q: How much disk does option A need? → A: Under 1 GB; all inputs are streamed, none stored
  (Assumptions, "Volume and disk").

## User Scenarios & Testing *(mandatory)*

Users: (a) the repository owner deciding whether `phyco-v2` deserves further work and whether the
feature-002 protocol needs amending; (b) researchers who must be able to reproduce and audit
every figure.

### User Story 1 - Measured false-failure rate of the SP 800-22 positive control (Priority: P1)

The owner learns, from a large number of independent runs of a known-good generator, how often a
perfect generator fails the feature-002 SP 800-22 protocol by chance: overall, per test family,
and how often families fail together. They can then decide, with evidence, whether the
feature-002 protocol needs a (stricter-only) amendment before any further SP 800-22 attempt.

**Why this priority**: It is the stated precondition for any further acceptance attempt, it needs
no new tools or downloads, and its method (a positive control judged by a fixed rule) is also
how the new batteries are checked.

**Independent Test**: Run the calibration with the frozen `sp80022` 1.0.0 harness and the
feature-002 verdict rules on OS cryptographic RNG data only, and read the measured rates with
their confidence intervals.

**Acceptance Scenarios**:

1. **Given** the feature-002 protocol and harness `sp80022` 1.0.0 unchanged, **When** the
   calibration runs, **Then** it evaluates 1,000 independent simulated positive-control runs,
   each of 100 sequences of 2²¹ bits, with exactly the feature-002 per-sub-test and per-family
   rules.
2. **Given** the calibration results, **When** the report is read, **Then** it states the
   overall false-failure rate, the rate per family (15) and per sub-test, the distribution of the
   number of failing families per run, and how often pairs of families fail together, each with a
   95% confidence interval.
3. **Given** the measured overall rate, **When** it is compared with the ~19% assumed in the
   feature-002 spec, **Then** the report says whether the assumption is consistent with the
   measurement and what this means for the chance of a PASS with a perfect candidate and a
   perfect control (feature-002 Assumptions).
4. **Given** any conclusion of the calibration, **When** it is reported, **Then** no change is
   made to the feature-002 protocol or harness by this feature; any proposed amendment is listed
   as a recommendation only, and must be stricter-only (feature 002 FR-014).

---

### User Story 2 - Pre-registered PractRand and TestU01 verdict on phyco-v2 (Priority: P2)

The owner obtains a PASS, FAIL or INCONCLUSIVE verdict for `phyco-v2` from PractRand and TestU01,
run on held-out seeds under rules fixed before any battery result was seen, with a positive
control (OS cryptographic RNG) and a negative control (`lut-v1`) run under the same rules.

**Why this priority**: It is the main new evidence about `phyco-v2`, but it depends on new tools,
the owner's download permission and long runs, and its verdict rule relies on the lesson of US1.

**Independent Test**: With the frozen tools and generators, run one held-out attempt and read
the verdict together with both control results.

**Acceptance Scenarios**:

1. **Given** a battery freeze, **When** the held-out attempt runs, **Then** for each battery,
   generator and seed it reports every test result with its p-value and the battery's own grade,
   the length reached, and whether the run met the failure rule.
2. **Given** the positive control, **When** it is evaluated under the same rules, **Then** it
   meets them; if not, the attempt is **INCONCLUSIVE** and halts before the candidate is run.
3. **Given** the negative control `lut-v1`, **When** it is evaluated under the same rules,
   **Then** it fails; if it passes, the batteries are declared unable to discriminate and the
   attempt is **INCONCLUSIVE**.
4. **Given** a candidate failure, **When** it is reported, **Then** the failing tests, seed and
   length are stated, and the failure is not re-run, re-seeded or omitted.

---

### User Story 3 - Fast, bit-exact generator streams (Priority: P3)

A researcher can feed the batteries terabytes of `phyco-v2` and `lut-v1` output and is certain
the stream is exactly what the reference models produce.

**Why this priority**: Supporting work: the Python reference models are far too slow for these
volumes, but any faster implementation is worthless unless it is proven identical to them.

**Independent Test**: Compare the fast stream with the reference model on the committed golden
vectors and on long prefixes for many seeds.

**Acceptance Scenarios**:

1. **Given** the committed golden vectors of `phyco-v2` and `lut-v1`, **When** the fast stream
   is generated for the same seeds, **Then** every word matches.
2. **Given** each of the 100 feature-002 `dev` seeds, **When** the first 10⁶ words of the fast
   stream are compared with the reference model, **Then** every word matches.
3. **Given** a held-out battery attempt, **When** it starts, **Then** the first 10⁶ words of every
   candidate and negative-control seed are checked against the reference model before testing;
   any mismatch makes the attempt **INVALID** (not a verdict) and stops it.

### Edge Cases

- **Positive control fails by chance in a battery attempt**: the attempt is INCONCLUSIVE, halts
  before the candidate is run, the negative control is still evaluated and reported, and the
  held-out set counts as used.
- **Candidate fails**: a FAIL is final for this feature. No further attempt is allowed, because
  the generator cannot change and a re-run on new seeds would be re-seeding until passing
  (Principle IV).
- **Negative control fails very early**: a run may stop at the first result meeting the failure
  rule; the length reached is recorded.
- **Tool crash, timeout or out-of-disk during a run**: the run is reported as incomplete with its
  log. An attempt with any incomplete candidate or control run is INCONCLUSIVE, and the set
  counts as used; failures already seen are still reported.
- **Calibration data source**: calibration uses only the OS cryptographic RNG, never `phyco-v2`,
  and uses no seed set at all, so it cannot consume held-out seeds.
- **Low-bit weakness**: TestU01 mostly examines the high bits of each word, so it is also run on
  the bit-reversed words; a failure in either orientation counts.

## Requirements *(mandatory)*

### Functional Requirements

**Calibration (O3)**

- **FR-001**: The calibration MUST evaluate **1,000** independent simulated positive-control runs,
  each of 100 sequences of 2²¹ bits drawn fresh from the operating system's cryptographic RNG,
  with harness `sp80022` 1.0.0 and the feature-002 rules (proportion, uniformity, k_max,
  m′ ≥ 55, a sub-test fails on proportion **or** uniformity) exactly as approved.
- **FR-002**: For every run the calibration MUST record every per-sequence p-value, every
  sub-test's proportion, uniformity p-value and pass/fail, every family verdict, and the run
  verdict, so all proportions, uniformity values and rates can be recomputed from the record.
- **FR-003**: The calibration report MUST give, each with a 95% confidence interval: the overall
  false-failure rate; the rate per family and per sub-test; the distribution of the number of
  failing families per run; the co-failure rate of every pair of families; and the implied
  chance of PASS on one attempt with a perfect candidate and a perfect control.
- **FR-004**: The report MUST compare the measurements with the feature-002 assumptions (~19%
  overall; per-family figures implied by its k_max table) and state, per family, whether the
  measurement is consistent with them.
- **FR-005**: The calibration MUST NOT change the feature-002 protocol, harness, verdicts or seed
  sets. Any recommended amendment MUST be stated as a recommendation for a separate, owner-approved
  spec amendment, and MUST be stricter-only under feature 002 FR-014.
- **FR-006**: The calibration bytes are not stored; a SHA-256 of each run's input stream MUST be
  recorded so the run's identity is fixed.

**Fast streams**

- **FR-007**: A high-throughput stream for `phyco-v2` and for `lut-v1` MUST be provided that is
  word-for-word identical to the reference models, shown on all committed golden vectors and on
  the first 10⁶ words of each of the 100 feature-002 `dev` seeds.
- **FR-008**: The fast streams MUST NOT change either generator; the reference models remain the
  golden models (Principle II). The stream byte order and word width given to each battery MUST
  be fixed and recorded.

**Battery protocol**

- **FR-009**: The batteries MUST be PractRand and TestU01 at the versions recorded in the battery
  freeze, built outside the repository from sources whose SHA-256 is recorded. Each download
  needs explicit owner permission (name, source, size) before it is made.
- **FR-010**: Battery setup, timing and pipeline checks MUST use only the feature-002 `dev` seeds
  and the two feature-001 seeds. Held-out battery seeds MUST NOT be used before the battery
  freeze approval.
- **FR-011**: Before each held-out attempt the battery freeze MUST record: the `phyco-v2` and
  `lut-v1` model hashes, the fast-stream source hashes, the battery tool versions and source
  hashes, the exact commands and options, the total p-value count S used by the failure rule,
  and the owner's approval.
- **FR-012**: Each attempt MUST run, in order, the positive control, the negative control, then
  the candidate, each on the same seeds of the next unused battery held-out set, exactly once.
  If the positive control fails, the candidate is not run.
- **FR-013**: At most **two** held-out battery attempts are allowed. A second attempt is allowed
  only if the first was INCONCLUSIVE or INVALID; a FAIL is final.
- **FR-014**: Every result produced MUST be reported, including incomplete runs, whatever the
  outcome. No test, seed, orientation or length may be dropped after results are seen.
- **FR-015**: Battery rules MAY only become stricter after approval: no test, battery level,
  orientation, seed or length may be removed, and no threshold loosened.
- **FR-016**: All reports MUST state that passing statistical batteries does not show
  cryptographic security, and that the generator must not be used to generate secrets.

### Pre-registered Battery Protocol

These values are fixed by this spec. After approval they may only be changed to be stricter.

**Seed sets.** Seed *i* of set *S* is the first 8 bytes of SHA-256 of the ASCII string
`phycoweb-003/<S>/<i>`, read as four big-endian unsigned 16-bit integers, for i = 0…9. Identity
is fixed by the SHA-256 of the canonical text (one line per seed, `a b c d\n`, in order). Neither
set shares a seed with any feature-001 or feature-002 set.

| Set | Purpose | First seed | SHA-256 of canonical text |
|-----|---------|-----------|---------------------------|
| `heldout-1` | battery attempt 1 | 12132 10603 3424 61301 | `bb1e1a2df50d121996863680e0668550690cf1e448af0cf797661a9713d7de80` |
| `heldout-2` | battery attempt 2 (only if attempt 1 is INCONCLUSIVE or INVALID) | 5338 17654 46179 7977 | `c7c7960803b25368b1ab3f745ec855a356f8189d7cfc8ce98348828bd1c6dbf8` |

**Scale per attempt** (each generator: candidate `phyco-v2`, positive control, negative control
`lut-v1` on the same seeds), owner decision 2026-10-29 (option A):

- **Seeds**: all 10 seeds of the held-out set.
- **PractRand**: one run per seed, up to 2⁴⁰ bytes (1 TiB).
- **TestU01**: SmallCrush, Crush and BigCrush, one run each per seed, on the output words and
  again on the bit-reversed words (6 TestU01 runs per seed).

Each generator stream starts after the `phyco-v2` frozen warm-up (256 steps) as specified in
design.md 1.0; `lut-v1` uses its feature-001 definition. The positive control draws fresh bytes
from the operating system's cryptographic RNG for each seed slot.

**Failure rule (per generator).** Let S be the total number of p-values the attempt's battery
runs report for one generator (all batteries, levels, seeds, orientations and lengths), counted
on development runs and fixed in the battery freeze. A generator **fails** if any of:

1. any reported p-value p satisfies p ≤ 0.005/S or p ≥ 1 − 0.005/S (two-sided Bonferroni bound,
   so a perfect generator fails with probability at most 1% whatever the dependence between
   tests); or
2. PractRand grades any result "FAIL" at any length; or
3. TestU01 reports any test as failing with p-value written as "eps" or "1 − eps".

Rules 2 and 3 can only add failures to rule 1 (stricter). Suspicious but non-failing results are
reported in full and do not affect the verdict.

**Overall verdict.**
- **PASS**: the positive control does not fail, the negative control fails, and the candidate
  does not fail.
- **FAIL**: the positive control does not fail, the negative control fails, and the candidate
  fails.
- **INCONCLUSIVE**: the positive control fails, the negative control does not fail, or any
  required run is incomplete.
- **INVALID**: a fast-stream mismatch with the reference model (US3 scenario 3).

### Key Entities

- **Calibration run**: run index, input SHA-256, per-sub-test proportion and uniformity, per
  family verdict, run verdict, harness version.
- **Calibration summary**: overall, per-family and per-sub-test rates, failing-family count
  distribution, pairwise co-failure matrix, confidence intervals, comparison with feature-002
  assumptions.
- **Fast stream**: generator id, source hash, byte order and word width, equivalence evidence.
- **Battery seed set**: name, derivation, canonical SHA-256, used/unused status.
- **Battery freeze record**: attempt, model and stream hashes, tool versions and source hashes,
  commands, S, approval.
- **Battery evaluation record**: per generator, battery, level, seed and orientation: every test
  result with p-value and grade, length reached, completeness, failure-rule outcome; overall
  verdict; commands; tool versions.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The calibration completes 1,000 of 1,000 runs, and its overall false-failure rate is
  reported with a 95% confidence interval no wider than ±3 percentage points.
- **SC-002**: The calibration report states, for each of the 15 families, a measured rate and
  whether it is consistent with the feature-002 assumption, and states the implied PASS
  probability for a perfect candidate.
- **SC-003**: The fast streams match the reference models on 100% of compared words (golden
  vectors plus 10⁶ words × 100 dev seeds per generator, and 10⁶ words per held-out seed per
  attempt).
- **SC-004**: A battery attempt produces a PASS, FAIL, INCONCLUSIVE or INVALID verdict under the
  pre-registered protocol, with both control results, within at most two attempts.
- **SC-005**: 0 battery held-out seeds are used before the matching battery freeze approval, and
  0 feature-002 held-out seeds are used by this feature.
- **SC-006**: Re-scoring the recorded battery outputs of any attempt reproduces 100% of failure
  rule outcomes and verdicts.
- **SC-007**: No report, document or comment describes either generator as cryptographically
  secure or fit for generating secrets.

## Assumptions

- **Calibration cost**: one 100-sequence run takes about 60 s on the 32-worker machine
  (feature-002 `harness/timing.json`), so 1,000 runs take about 17 hours. With a true rate near
  20%, 1,000 runs give a 95% interval of about ±2.5 points.
- **Calibration uses no seeds** and is not an acceptance attempt, so it is unlimited in the sense
  of feature 002 (it consumes no held-out set). Its run count is still fixed here so the result
  cannot be stopped when convenient.
- **Why Bonferroni**: the O3 lesson is that rules assuming independent tests misstate the
  false-failure rate. A union bound holds under any dependence, so the battery positive control
  fails with probability at most 1% by construction; no separate battery calibration is needed.
  The price is a little sensitivity, accepted for a dependable control.
- **Volume and disk**: one option-A attempt feeds roughly 90 TiB to the batteries (PractRand
  3 × 10 × 1 TiB; BigCrush about 2³⁸ words per run). No battery or calibration input is stored:
  every stream goes straight into the tool, and `phyco-v2` and `lut-v1` runs can be regenerated
  exactly from their seeds. Expected disk use is under 1 GB (tool builds, logs, records,
  about 150 MB of calibration p-values). Machine time is a few days per attempt.
- **One fixed generator**: there is no tuning in this feature, so development seeds are used only
  to check the pipeline, timing and S.
- **Tools** are built and run outside the repository (as NIST STS 2.1.2 was in feature 002), in
  WSL where needed. They are not vendored, so their licences do not affect the repository's
  GPL-3.0 licence. Their versions and source hashes are recorded.
- **Positive-control bytes** for batteries and calibration are streamed and not kept; their
  hashes are recorded (as owner decision Q1 in feature 002, but here the volumes make keeping
  them impractical).
- **Out of scope**: any change to `phyco-v2`, `lut-v1`, harness `sp80022` or the feature-002
  protocol; Dieharder; RTL; cryptographic analysis. A FAIL is a valid, reportable outcome.
