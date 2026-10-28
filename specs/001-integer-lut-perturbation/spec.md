# Feature Specification: Integer LUT Perturbation Source

**Feature Branch**: `001-integer-lut-perturbation`

**Created**: 2026-10-28

**Status**: Approved for planning (2026-10-28); result review pending

**Input**: User description: "replace sin/cos perturbation with integer LUT source"

## Context

The PhycoWeb-PRNG reference model drives its two environmental "food" signals
(`food_a`, `food_b`) from floating-point sine and cosine evaluations each step. This violates
Constitution Principle I (integer-domain, multiplierless arithmetic) and blocks Principle II
(bit-accurate parity with hardware): a floating-point trigonometric source cannot be reproduced
bit-for-bit in synthesizable logic, and its sequence never repeats exactly, so it cannot be
captured in a finite hardware table. This feature replaces that source with a fixed, finite
table of pre-computed integer values indexed by an integer phase counter.

## Clarifications

### Session 2026-10-28

- Q: What fidelity target should the table aim for? → A: Sampled sine with the 2:3 frequency
  ratio kept exactly; periods rounded to values the table can produce (Option A).
- Q: What table size and phase increments? → A: 256 entries; increments 4 (`food_a`) and 6
  (`food_b`); periods 64 and ≈42.67 steps; combined period 128 steps (Option A).
- Q: How are table values reduced to integers? → A: Truncation toward zero, matching the
  current model's `int()` conversion.
- Q: Should SC-001's multiplication ban cover the whole per-step path or only the perturbation
  stage? → A: Only the perturbation stage, which matches FR-002 and FR-008. Float,
  trigonometry and division stay banned throughout the per-step path.

## Review & Approval *(Constitution Principle VIII)*

This feature changes generator algorithm behavior and MUST NOT proceed to `/speckit-plan`
until a human reviewer approves it below.

| Gate | Reviewer | Date | Decision | Notes |
|------|----------|------|----------|-------|
| Spec approval (algorithm change) | Coastrnaut (repository owner) | 2026-10-28 | Approved | Approved in session after the v1.1.0 revision |
| Result review (golden vectors + NIST results) | _pending_ | _pending_ | _pending_ | Required before the feature is declared complete |

## User Scenarios & Testing *(mandatory)*

Primary users are (a) hardware engineers implementing the generator in RTL and (b) researchers
evaluating the generator's statistical quality.

### User Story 1 - Integer-only reference model (Priority: P1)

A hardware engineer reads the reference model and can map every operation in the perturbation
stage directly to registers, a counter, and a read-only table, with no floating-point or
multiplier logic.

**Why this priority**: This is the constitutional violation being fixed; without it the
reference model cannot serve as the golden model for any RTL work.

**Independent Test**: Inspect and execute the reference model; confirm the perturbation stage
uses only integer table lookups, integer counters, additions, and masks, and that it produces
output words for a given seed.

**Acceptance Scenarios**:

1. **Given** the updated reference model, **When** the perturbation stage is reviewed, **Then**
   it contains no floating-point values, trigonometric calls, multiplications, or divisions.
2. **Given** a seed, **When** the generator is stepped, **Then** `food_a` and `food_b` are each
   obtained by reading one entry from the perturbation table at an integer phase index.
3. **Given** the perturbation table, **When** its contents are inspected, **Then** every entry is
   a 16-bit value in the same encoding the model applies to node pressures (two's-complement,
   masked to 16 bits).

---

### User Story 2 - Deterministic, reproducible sequences (Priority: P2)

A researcher runs the generator with the same seed on different machines and Python versions and
obtains identical output word sequences, and can regenerate committed golden vectors.

**Why this priority**: Required by Constitution Principle V and is the basis for future
model/RTL equivalence vectors (Principle II).

**Independent Test**: Generate 10,000 output words for a fixed seed on two environments and
compare; compare against a committed golden vector file.

**Acceptance Scenarios**:

1. **Given** a fixed seed, **When** 10,000 words are generated twice, **Then** the sequences are
   identical.
2. **Given** a committed golden vector file for the reference seed `[1024, 2048, 4096, 8192]`,
   **When** the model is run, **Then** its output matches the file word-for-word.
3. **Given** the perturbation table, **When** the generator runs for more steps than the table
   period, **Then** the perturbation values repeat with exactly the documented period.

---

### User Story 3 - Statistical quality is re-measured and reported (Priority: P3)

A researcher can see how replacing the perturbation source affected randomness test results,
recorded per Constitution Principle IV.

**Why this priority**: Changing the driving signal changes generator output; the impact must be
measured and reported honestly, but it does not block the model fix itself.

**Independent Test**: Run the NIST SP 800-22 evaluation on the new model and confirm a results
record exists with seed, sample size, commit, and per-test p-values.

**Acceptance Scenarios**:

1. **Given** the updated model, **When** the statistical evaluation is run, **Then** a results
   record is produced containing seed, sample size, model version, and per-test p-values.
2. **Given** results exist, **When** they are reviewed, **Then** all tests run are reported,
   including failures, alongside the prior floating-point baseline where available.

### Edge Cases

- Negative waveform samples: entries representing negative values must use the same 16-bit
  two's-complement masked encoding as the current behavior (e.g., -1024 → `0xFC00`), so the
  addition into node pressure wraps identically.
- Phase counter wrap: the phase index must wrap cleanly at the table length with no skipped or
  duplicated entry at the boundary.
- Step counter overflow: running for very long sequences (beyond 2³² steps) must not change the
  perturbation period or cause errors.
- Zero-step behavior: the first generated block must use a well-defined table entry (the
  current model increments the step counter before computing, so step 1 is the first sample).
- Two signals sharing one table: `food_a` and `food_b` must remain distinct sequences (different
  phase rates and/or offsets) so they do not collapse into identical perturbations.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The reference model MUST derive `food_a` and `food_b` exclusively from a fixed,
  pre-computed table of integer values indexed by integer phase counters.
- **FR-002**: The perturbation stage MUST NOT perform floating-point arithmetic, trigonometric
  evaluation, multiplication, or division at run time.
- **FR-003**: Table contents MUST be fixed constants committed to the repository (or produced by
  a committed, deterministic generation script whose output is committed), not computed during
  generator operation.
- **FR-004**: Each table entry MUST be a 16-bit value in the encoding applied to node pressures,
  with peak amplitude ±1024 to preserve the current perturbation magnitude.
- **FR-005**: The table MUST hold one full period of a sampled sine wave. `food_a` MUST follow
  the sampled sine and `food_b` the sampled cosine (the same table read a quarter period ahead),
  with the 2:3 frequency ratio between them preserved exactly. The periods are rounded to
  values the table can produce; exact reproduction of the prior floating-point output is not a
  goal.
- **FR-006**: Phase advancement for each signal MUST use integer increments with modular
  wrap-around at the table length, expressible as a counter plus mask (table length is a power
  of two).
- **FR-007**: The table MUST have 256 entries. `food_a` MUST advance its phase by 4 entries per
  step (period 64 steps, against ≈62.8 originally) and `food_b` by 6 entries per step (period
  256/6 ≈ 42.67 steps, against ≈41.9 originally; it returns to the same phase every 128 steps).
  The combined perturbation pattern MUST repeat every 128 steps, and this period MUST be
  documented.
- **FR-007a**: Table entry `T[i]` for `i` = 0…255 MUST equal `trunc0(sin(2π·i/256) × 1024)`
  masked to 16 bits (`& 0xFFFF`), where `trunc0` is truncation toward zero. The table is
  computed offline once; the committed integer values are authoritative. Reference values:
  `T[0] = 0x0000`, `T[64] = 0x0400` (+1024), `T[128] = 0x0000`, `T[192] = 0xFC00` (−1024).
- **FR-007b**: Arithmetic semantics of the perturbation stage (Constitution Principle I):

  | Element | Width / encoding | Rule |
  |---------|------------------|------|
  | `phase_a`, `phase_b` | 8-bit unsigned, initial value 0 | `phase = (phase + inc) & 0xFF`; wraps modulo 256 |
  | `inc_a`, `inc_b` | constants | 4 and 6 |
  | table index for `food_b` | 8-bit unsigned | `(phase_b + 64) & 0xFF` (quarter-period offset = cosine) |
  | `food_a`, `food_b` | 16-bit, two's-complement bit pattern held as 0…65535 | read directly from `T` |
  | `P[0]`, `P[2]` update | 16-bit, held as 0…65535 | `P = (P + food) & 0xFFFF` (modulo 2¹⁶) |
  | step counter | unbounded | not used to index the table; it must not affect the perturbation period |

- **FR-007c**: The per-step update order MUST be:
  1. Increment the step counter.
  2. Advance `phase_a` and `phase_b` (so step 1 reads index 4 for `food_a` and index
     `(6 + 64) & 0xFF = 70` for `food_b`, i.e., step *n* uses index `4n mod 256` and
     `(6n + 64) mod 256`).
  3. Read `food_a = T[phase_a]` and `food_b = T[(phase_b + 64) & 0xFF]`.
  4. Apply `P[0] += food_a` and `P[2] += food_b`, each masked to 16 bits.
  5. Compute flux for all four channels from the updated `P` and the current `D`.
  6. Apply growth and decay to all four channels, mask each `D` to 16 bits, then set any `D`
     equal to 0 to 1.
  7. Evaluate the Frustrated Foraging comparison (`D[0] > 4096 or D[2] > 4096`) on the values
     from step 6. `D` is always in 0…65535 after masking, and the comparison treats it as an
     unsigned 16-bit value. If true, apply `P[1] ^= 0x5A5A` and `P[3] ^= 0xA5A5`.
  8. Harvest the output word from the low 8 bits of `D[0]…D[3]` (MSB to LSB).
- **FR-008**: All other generator stages (flux, growth/decay, Frustrated Foraging disruption,
  output harvesting) MUST remain behaviorally unchanged.
- **FR-009**: The reference model MUST exist as a runnable source file in the repository, and
  the model listing in the project documentation MUST be updated to match it.
- **FR-010**: A golden output vector file of at least 10,000 words for the reference seed MUST
  be generated and committed, along with a check that verifies the model against it.
- **FR-011**: The NIST SP 800-22 evaluation MUST be re-run on the updated model and the results
  recorded per Constitution Principle IV.
- **FR-012**: Because no RTL exists yet, this change MUST be flagged as "RTL-pending" per
  Constitution Principle II, and the table definition MUST be in a form an RTL implementation can
  consume directly (e.g., a plain list of hex constants).
- **FR-013**: Before the reference model is changed, the floating-point variant MUST be
  archived (Constitution Principle V) as read-only reference material, not as active code:
  1. the model listing exactly as it appears in `readmee.md` at the current commit,
  2. `MycoPRNG.py` as of commit `290e563^`,
  3. `nist_bench.py`, `nistrng_bench.py` and `phycoweb_nist_eval.py` as of commit `d6980eb^`.
  Each archived file MUST have its SHA-256 hash and source commit recorded in a committed
  inventory.
- **FR-014**: Before the change, the archived floating-point model MUST be run for the reference
  seed to produce baseline output vectors and, where feasible, baseline NIST results, so that
  FR-011 has a prior result to compare against.

### Key Entities

- **Perturbation Table**: Ordered, fixed list of 16-bit integer samples of one waveform period;
  attributes: length (power of two), amplitude, encoding, source/generation method.
- **Phase Counter**: Per-signal integer index into the table; attributes: increment per step,
  initial offset, wrap modulus (table length).
- **Golden Vector File**: Committed sequence of output words for a stated seed, model version,
  and word count; used to detect behavioral regressions.
- **Statistical Results Record**: Seed, sample size, model version/commit, per-test p-values,
  pass/fail outcome.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Zero floating-point, trigonometric, multiplication, or division operations remain
  in the perturbation stage, and zero floating-point, trigonometric, or division operations
  remain anywhere in the generator's per-step path (verified by review and automated source
  check). *Amended 2026-10-28, before any results existed, with owner approval: the earlier
  wording banned multiplication across the whole per-step path, which contradicted FR-002 and
  FR-008. The flux-stage product is tracked as Open Issue 1.*
- **SC-002**: 100% of 10,000 output words match the committed golden vectors on every run, on at
  least two different environments.
- **SC-003**: The (`food_a`, `food_b`) pair repeats with a period of exactly 128 steps, and no
  shorter period, verified over at least 10 full periods (1,280 steps).
- **SC-004**: The perturbation magnitude stays within ±1024. At every table sample point, each
  entry is less than 1 unit from the ideal value `sin(2π·i/256) × 1024` and never larger in
  magnitude (truncation toward zero). This was checked while writing the spec: the largest
  deviation is 0.997.
- **SC-005**: A statistical results record for the new model exists, covering all NIST
  SP 800-22 tests run, with results compared against the prior baseline where one is available.
  No statistical result is presented as evidence of cryptographic security.
- **SC-006**: 100% of the archived files in FR-013 are present, and each one's recorded SHA-256
  hash matches when it is recomputed.

## Assumptions

- The reference model listed in `readmee.md` is the current source of truth for behavior. The
  deleted scripts are archived (FR-013) for provenance but are not restored as active code; a
  new runnable model file is created instead.
- The existing `scripts/phase0_audit.py` (inventories `baseline/` into
  `reports/phase-0/baseline_inventory.json` with SHA-256 hashes) may be used to satisfy FR-013.
- No RTL exists in the repository; RTL implementation of the table is out of scope and follows
  in a later feature.
- Output sequences will differ from the floating-point version; exact backward compatibility
  with prior outputs is not required (the floating-point sequence is aperiodic and cannot be
  reproduced by any finite table).
- A single shared table may serve both signals (cosine obtained as a quarter-period phase
  offset), provided FR-005 and the distinct-sequence edge case hold.
- Rewording the "cryptographically secure" claim and renaming `readmee.md` are out of scope
  for this feature.
- The NIST evaluation uses `nistrng` as listed in `requirements.txt`.

## Open Issues *(outside this feature's scope)*

Found while writing down the arithmetic semantics; each needs its own feature:

- **Flux stage multiplies two variables**: `Q = (D × (P_i − P_j)) >> 8` multiplies two state
  variables, which conflicts with Constitution Principle I (multiplierless) and the 0-DSP target.
- **Flux overflow is unspecified**: `D` (up to 65535) × `ΔP` (up to ±65535) can exceed the
  32-bit signed range of the container, so the result depends on the platform's overflow
  behavior. The overflow rule must be specified.
- **State width mismatch**: `P` and `D` are held as unsigned 0…65535 values, while the
  constitution and `readmee.md` describe "16-bit signed" state. The intended signedness of
  `P`, `D` and `Q` must be defined.
- **Disruption almost always fires** (found during planning, research R8): the disruption
  fires on about 99.5% of steps and `D` stays at its 65,535 ceiling, so the threshold
  supervisor is effectively always on. This needs design review.
- **Signed output words** (found during planning, research R2): the `readmee.md` model returns
  signed output words when bit 31 is set. This feature defines the output as unsigned 32-bit;
  the bit pattern is unchanged.
