# Final Phase Report: Feature 003, Extended Batteries and Positive-Control Calibration

Date: 2026-11-01. Format: constitution, Phase Completion Reporting. Gate: **⛔ T044, owner final
result review (Principle VIII)**.

> Passing statistical batteries does not show cryptographic security. This generator must not be
> used to generate secrets; use an established cryptographic random-number generator for keys,
> nonces, tokens and salts.

## 1. Outcome

- **O3 is answered.** Under the feature-002 SP 800-22 rules, the OS CSPRNG fails by chance in
  **207 of 1,000 runs: 20.7% (95% CI 18.2–23.3%)**, consistent with the ~19% feature 002
  assumed. A perfect candidate therefore passes a feature-002 attempt with probability **0.629
  (95% CI 0.588–0.669)** (`calibration/`, owner-reviewed at T011).
- **Battery attempt 1 is PASS**, accepted by the owner on 2026-11-01 (T038). On 10 held-out
  seeds, `phyco-v2` failed no rule in any of its 70 runs (PractRand to 1 TiB; TestU01
  SmallCrush, Crush and BigCrush in both bit orders). The positive control (`os`) failed none of
  70; the negative control (`lut-v1`) failed all 70. The re-score was identical.
- **A parser defect found after the attempt is fixed** (T039a): PractRand lines with a saturated
  statistic (`R>`, `R<`) were skipped. All 553 such lines were the negative control's. A
  supplementary re-score with the fixed parser gives the same verdict; the frozen verdict
  stands.
- **What this means:** neither SP 800-22 nor PractRand nor TestU01 found a statistical defect
  in `phyco-v2` at the depths run. That is all it means. `phyco-v2` stays at claim level L0,
  with no claim; its 64-bit seed caps any security level at 64 bits (section 7).

## 2. Files created or modified (whole feature)

| Area | Files |
|------|-------|
| Calibration (US1) | `scripts/calibrate.py`, `scripts/calibration_report.py`, `scripts/dft_crosscheck.py`, `tests/test_calibration.py` |
| Fast streams (US3) | `fast/phyco_stream.c`, `fast/lut_table.h` (from `scripts/gen_c_lut.py`), `fast/testu01_driver.c`, `fast/Makefile`, `fast/build_tools.sh`, `scripts/stream_equiv.py`, `tests/test_fast_stream.py` |
| Battery protocol (US2) | `protocol/batteries.py`, `protocol/battery_freeze.py`, `protocol/battery_seedsets.py`, `scripts/battery_run.py`, `scripts/battery_freeze.py`, `scripts/battery_attempt.py`, `scripts/battery_rescore.py`, `tests/test_batteries.py`, `tests/test_battery_protocol.py`, `tests/data/batteries/` (5 fixtures, `pr-saturated` added in T039a) |
| Records | `calibration/` (1,000 run records, `SHA256SUMS`, summary, DFT cross-check), `tools/`, `streams/`, `dev/` (rehearsal, S, timing, test log), `attempt-1/` (freeze, start, equivalence, runs, attempt, summary, re-scores, phase report) |
| Documents | `specs/003-extended-batteries-calibration/` (spec, plan, research, data model, contracts, quickstart, tasks, checklist); `README.md` §5; `security.md` 2.9 (§1, §11, roadmap); `.gitattributes` |

All record paths are under `reports/003-extended-batteries-calibration/`.

## 3. Requirements → evidence

| Requirement | Evidence | Status |
|-------------|----------|--------|
| FR-001 1,000 positive-control runs, feature-002 rules | `calibration/runs/` (1,000 records), `calibration/phase-report.md` §3 | Met |
| FR-002 every p-value and verdict recorded | run records hold every per-sequence p-value, proportion, uniformity and verdict; `test_calibration` | Met |
| FR-003 rates with 95% CIs, failing-family distribution, co-failure, implied PASS | `calibration/summary.json`, `summary.md` | Met |
| FR-004 comparison with the feature-002 assumptions | `calibration/phase-report.md` §1, §4: 12 of 15 families consistent; dft, cumulative_sums and random_excursions_variant above expectation, explained | Met |
| FR-005 feature 002 unchanged | T040 hashes unchanged (`dev/test-log.md`); 3 recommendations stated as recommendations only | Met |
| FR-006 input SHA-256 per run, bytes not stored | `input_sha256` in every run record | Met |
| FR-007 fast streams word-for-word identical | `streams/equivalence.json`: golden vectors plus 10⁶ words × 100 dev seeds × 2 generators, 200,030,000 words, all match | Met |
| FR-008 generators unchanged; byte order and width fixed | reference models unchanged (T040); 32-bit little-endian words, `--reverse` for TestU01's second orientation (`contracts/cli.md`) | Met |
| FR-009 PractRand and TestU01 at recorded versions, downloads approved | `tools/practrand.json` (0.96), `tools/testu01.json` (1.2.3): owner permission, archive SHA-256, build commands, binary hashes | Met |
| FR-010 setup on dev seeds only | `dev/phase-report.md`; dev tools refuse held-out seeds (`test_dev_mode_refuses_heldout_seed`) | Met |
| FR-011 freeze before the attempt | `attempt-1/freeze.json` (S = 101,210, hashes, tools, commands, owner approval 2026-10-30); `started.json` pins its SHA-256 | Met |
| FR-012 order positive → negative → candidate, once | `attempt-1/attempt.json`, `progress.txt`; role windows in `attempt-1/phase-report.md` §5 | Met |
| FR-013 at most two attempts | one attempt, PASS; T039 not applicable; `test_no_third_attempt`, `test_attempt_2_only_after_inconclusive_or_invalid` | Met |
| FR-014 every result reported | 210 runs reported, none dropped or restarted; the parser defect and its re-score reported (`attempt-1/phase-report.md` §6 and addendum) | Met, with the defect disclosed |
| FR-015 stricter-only | no rule changed after the freeze; the T039a fix only adds failures and applies from the next freeze | Met |
| FR-016 disclaimer in every report | all reports; see T041 findings in section 6 (5 provenance records lack the field; generated text names SP 800-22) | Met for reports, with 2 findings on records |
| SC-001 1,000/1,000 runs, CI ±3 points or narrower | 1,000 of 1,000; CI 18.2–23.3%, half-width 2.6 points | Met |
| SC-002 per-family rates and implied PASS probability | `calibration/summary.md` | Met |
| SC-003 100% word match, including 10⁶ words per held-out seed | `streams/equivalence.json`; `attempt-1/equivalence.json`: 20,000,000 words, no mismatch | Met |
| SC-004 a verdict with both controls within two attempts | PASS in attempt 1 | Met |
| SC-005 no held-out seed before the freeze; no feature-002 held-out seed | `dev/` uses dev seeds only; battery sets disjoint from earlier sets (`test_disjoint_from_all_earlier_sets`) | Met |
| SC-006 re-score reproduces 100% | `attempt-1/rescore.json`: identical | Met |
| SC-007 no claim of security | T041 claims check (`dev/test-log.md`): no claim found | Met |

## 4. Tests run (T040, recorded in `dev/test-log.md`)

| Environment | Result |
|-------------|--------|
| Windows 11, Python 3.10.11 | 179 tests OK, 9 skipped (the 6 extra skips need the Linux fast-stream binary) |
| Ubuntu (WSL2), Python 3.14.4 | 179 tests OK, 3 skipped |

The feature-002 frozen sources (`model_v2.py`, `model.py`, `lut.py`, `seedsets.py`,
`evalcore.py`, `sp80022` 1.0.0) hash exactly as at T003.

## 5. Attempts

| Attempt | Seed set | Verdict | Re-score | Review |
|---------|----------|---------|----------|--------|
| 1 | `heldout-1` (battery) | **PASS** | identical; supplementary re-score with the fixed parser also PASS | owner, 2026-11-01 |

Attempt 2 was not run and is not allowed (FR-013).

## 6. Open issues

1. **Parser defect (fixed).** Saturated PractRand lines were skipped (attempt-1 phase report,
   issue 1). Fixed in T039a; `protocol/batteries.py` now hashes `fc141a2b…`, not the frozen
   `46c4dd15…`, so any later attempt needs a new freeze.
2. **For feature 007's protocol** (carried in strategy note §9.3): schedule runs from any role as
   slots free up; set the freeze's `status` to `approved` on approval; explain or bound the
   `lut-v1` `snpair_ClosePairs` times (up to 20.1 h per BigCrush run) before projecting
   run times.
3. **Provenance records without `disclaimer`** (T041): `tools/*.json`, `attempt-1/freeze.json`,
   `started.json`, `equivalence.json`. Not edited, because the freeze is approved and hashed.
   Fix the writers before the next freeze.
4. **The generated disclaimer names SP 800-22** in the battery `summary.md` and records, because
   they use feature 002's constant. A battery form needs a change to the frozen
   `scripts/battery_attempt.py`; make it before the next freeze.
5. **Calibration recommendations** (dft, cumulative_sums, random_excursions_variant) remain
   recommendations; any change to feature 002 needs a separate, stricter-only amendment.
6. **Convergence (2026-11-01).** `/speckit-converge` found three partial gaps against
   data-model.md. T045 (records lack `git_head`, `git_dirty`, `versions`, `command`) is deferred
   by the owner to before the next freeze, with issues 3 and 4. T046 and T047 were resolved by an
   owner-approved data-model correction (§7–§9) describing what the code writes.
7. **Carried from the dev report:** `stream_bytes` counts bytes written, not consumed; feature-003
   files were uncommitted when the freeze recorded `git_head`.
8. **Selection bias** (feature-002 O6) still applies to `phyco-v2`, which was chosen on dev
   seeds; only held-out results are unbiased, and both reported verdicts are held-out.

## 7. Security concerns and known limitations

- **The seed-entropy bound.** `phyco-v2`'s seed is four 16-bit words, 64 bits in total. That
  caps any security level at 64 bits, however large the state, below the 112-bit minimum for
  approved cryptographic use and the constitution's 128-bit floor. Trying every seed costs about
  2⁷² generator steps. Any cryptographic claim, evaluation or certification must first meet
  FUT-SEC-1 to FUT-SEC-9 (`research/security/seed-entropy-bound.md`; security.md §20.1).
- **The structural findings stand:** S1–S15 of security.md §9.2, among them the step function not
  being one-to-one (S13) and the biased top bits of D (S14). No battery result changes them.
- **Statistical success is not security.** These batteries look for statistical defects; they
  do not model an attacker who knows the algorithm. Structural (level 3) tests have not
  started, and Dieharder was not run.
- No new security concern arose in this feature.

## 8. Constitution

Constitution 1.2.0, approved on 2026-10-31 after this feature's Constitution Check against 1.1.0
(plan.md), applies. The feature meets its Security Policy: it makes no cryptographic claim, every
report carries the disclaimer, the seed-entropy bound is stated where security levels are
mentioned, and nothing here starts any evaluation or certification that FUT-SEC-1 to FUT-SEC-9
would gate. The protocol only became stricter.

## 9. Recommendation

**Owner final result review, ⛔ T044.** If the owner accepts, feature 003 is complete. Before
feature 004, `/speckit-converge` runs on feature 003 and its result is shown to the owner. Open
issues 2–4 belong to the next freeze, in feature 007 at the latest.

## Review & Approval

| Role | Name | Date | Decision |
|------|------|------|----------|
| Owner (T044) | Coastrnaut (repository owner) | 2026-11-01 | Approved; the T041 findings (open issues 3 and 4) are to be fixed before the next freeze |
