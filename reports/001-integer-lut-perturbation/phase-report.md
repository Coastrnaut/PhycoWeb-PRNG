# Phase Report: 001-integer-lut-perturbation (implementation)

**Date**: 2026-10-28 | **Constitution**: v1.1.0 (Phase Completion Reporting) | **Status**: implementation
complete on one environment; **SC-002 open (T019)**; **result review pending (T027)**

Exact commands and outputs are in [test-log.md](./test-log.md). Statistical results are in
[summary.md](./summary.md).

## Files created or modified

| Area | Files |
|------|-------|
| Model | `phycoweb/__init__.py`, `phycoweb/model.py`, `phycoweb/lut.py` (generated) |
| Tools | `scripts/archive_baseline.py`, `scripts/gen_lut.py`, `scripts/gen_vectors.py`, `scripts/nist_eval.py` (`scripts/phase0_audit.py` unchanged) |
| Tests | `tests/__init__.py`, `test_baseline.py`, `test_lut.py`, `test_purity.py`, `test_period.py`, `test_equivalence.py`, `test_vectors.py`, `test_nist_eval.py` |
| Archive | `baseline/float-v0/` (5 archived files + `MANIFEST.json`) |
| Data | `data/lut/perturbation_lut.hex`, `vectors/float-v0_seed-1024-2048-4096-8192_10000.hex`, `vectors/lut-v1_seed-1024-2048-4096-8192_10000.hex` |
| Reports | `reports/001-integer-lut-perturbation/` (4 NIST JSON records, `summary.md`, `test-log.md`, this file) |
| Docs/config | `readmee.md` (section 2 only), `.gitattributes`, `.gitkeep` placeholders |
| Spec docs | `spec.md` (implementation status line), `tasks.md` (task marks; T020 amended for N2), `research.md` (R6: N2, N3) |

## Requirements and evidence

| ID | Status | Evidence |
|----|--------|----------|
| FR-001, FR-002 | ✅ | `test_purity` (AST: no float, trig, division or power; no multiplication in `_perturb`) |
| FR-003, FR-004, FR-005, FR-007a | ✅ | `test_lut`; `gen_lut.py --check` exit 0 |
| FR-006, FR-007, FR-007b, FR-007c | ✅ | `test_period` (step 1 → indices 4/70; step-*n* formula; period 128) |
| FR-008, FR-008a | ✅ | `test_equivalence`: 2 seeds × 10,000 words, plus 5,000 random states and 5 edge states; mutation check caught 6/6 mutants |
| FR-008b | ✅ | `test_vectors.TestSeedDomain` |
| FR-009 | ✅ | `readmee.md` §2 listing equals `phycoweb/model.py` (checked); other sections unchanged |
| FR-010 | ✅ | `vectors/lut-v1_…hex`; `test_vectors`; `--verify` exit 0; tampered copy detected |
| FR-011 | ✅ | 4 NIST records + `summary.md`; reproduced exactly in a second run |
| FR-012 | ✅ | `data/lut/perturbation_lut.hex`; spec status "RTL-pending" |
| FR-013 | ✅ | `baseline/float-v0/MANIFEST.json`; `test_baseline` |
| FR-014 | ✅ | `vectors/float-v0_…hex` (first word D6EDF3D6); float-v0 NIST records |
| SC-001 | ✅ | `test_purity` |
| SC-002 | ⏳ **OPEN** | Passed on Windows 11 / Python 3.10.11 only. Needs a second environment (T019, owner) |
| SC-003 | ✅ | `test_period` (1,280 steps; no shorter period) |
| SC-004 | ✅ | `test_lut` truncation/magnitude test |
| SC-005 | ✅ | `summary.md` reports all 15 tests per run, including failures and one not-eligible test |
| SC-006 | ✅ | `test_baseline` (5/5 hashes match) |

## Tests actually run (final state)

- `python -W ignore -m unittest discover -s tests -v`: **31 tests, OK**. Windows 11
  (`platform.platform()` = Windows-10-10.0.26200-SP0), Python 3.10.11, numpy 2.2.6, nistrng 1.2.3.
- Quickstart steps 1–6: all pass. Details in test-log.md.
- NIST (1,000,000 bits each; pass / fail / not eligible):

  | Model | Seed 1024… | Seed 4660… |
  |-------|-----------|-----------|
  | float-v0 | 12 / 2 / 1 | 12 / 2 / 1 |
  | lut-v1 | 8 / 6 / 1 | 12 / 2 / 1 |

  Both models fail Linear Complexity and Random Excursion in every run.

## Deviations from the plan

1. **NIST harness (T020)**: tests run individually on copies instead of through
   `run_all_battery`. nistrng 1.2.3's Binary Matrix Rank test modifies its input in place (N2), which
   made the first set of reports invalid. Those reports were discarded and regenerated.
   Also: `Result.score` is a mean, so all p-values are now recorded, and the template test's
   random choice is seeded (N3). Recorded in research R6 and T020.
2. **Equivalence test (T011)**: added single-step comparisons from forced states. Trajectory
   comparison alone missed the zero-floor and threshold-boundary paths.
3. **Quickstart steps 2 and 4** were checked with `--verify` against the committed files instead of
   being rewritten with `--out`. Step 6 wrote to a scratch directory and was compared with the
   committed reports.

## Open issues

- **SC-002 / T019**: needs a second environment (owner action).
- **T027**: owner result review (Principle VIII).
- Spec Open Issues 1–5 are unchanged, and two are reinforced:
  - **1. Flux multiplier**: still present. It conflicts with Principle I and the 0-DSP target.
  - **2. Flux overflow**: now specified (FR-008a); the redesign question is open.
  - **3. P/D/Q signedness** versus the "16-bit signed" wording in the constitution and README.
  - **4. Disruption fires about 99.5% of steps**, which may be degenerate dynamics.
  - **5. Signed output** in the archived model (handled by the unsigned output definition).
- **`wrap32(abs(Q))` can never take effect** (|Q| < 2²³ after `>> 8`). It is kept because
  FR-008a specifies it, and it is a candidate for a spec PATCH.
- **nistrng limitations**:
  - Non-Overlapping Template Matching uses one template and gives p = 1.000000 in every run
    (uninformative).
  - Overlapping Template Matching is not eligible at 10⁶ bits.
  - Only a single sequence per seed was tested.
  - Linear Complexity failures were not cross-checked with an independent implementation.
- **lut-v1 vs float-v0**: with the reference seed, lut-v1 fails 4 more tests. With the second seed
  they fail the same tests. The evidence is not enough to attribute the difference to the
  perturbation source.
- **Provenance**: the owner committed files while the NIST runs were in progress, so `git_head`
  differs between records. The code was identical across all four runs (see summary.md).

## Security concerns

- Every run fails Linear Complexity, and every run fails Random Excursion. lut-v1 with the
  reference seed also fails 4 more tests. **The generator must not be used for secrets**
  (Security Policy). These results are evidence against cryptographic suitability, and nothing
  here supports it.
- The pasted feasibility research (analysis finding I1) identified structural concerns: the
  output exposes the low 8 bits of each `D`, there is no keying, and the effective state is small.
  `lut-v1` adds only 8 bits of phase state with a 128-step cycle. These are untested and unresolved.
- `readmee.md` still describes the output as "cryptographically secure bitstreams" in section 1.1
  (line 38).
  This conflicts with Principle IV and the Security Policy. It is out of scope here but should be
  corrected soon.

## Recommendation

**Proceed to owner review, but do not build further on this generator design yet.**

The feature's goal is met on this environment: an integer-only, fully specified reference model,
bit-exact with the archived model apart from the perturbation source, with RTL-ready table data.
Before closing:
1. run T019 on a second environment;
2. complete the T027 result review.

Then, before any RTL work, address Open Issues 1 and 4 and the README security claim in new
specs. The statistical failures (Linear Complexity in all runs) suggest the core dynamics, not
just the perturbation source, need redesign.
