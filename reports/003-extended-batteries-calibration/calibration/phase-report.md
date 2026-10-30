# Phase Report: US1, Positive-Control Calibration (feature 003, O3)

Date: 2026-10-29. Format: constitution, Phase Completion Reporting. Gate: **T011, owner
calibration result review (Principle VIII)**.

> Passing NIST SP 800-22 does not show cryptographic security. This generator must not be used
> to generate secrets; use an established cryptographic random-number generator for keys,
> nonces, tokens and salts.

## 1. Outcome

- **O3 is answered.** Under the feature-002 rules, the OS CSPRNG fails SP 800-22 by chance
  in **207 of 1,000 runs: 20.7% (95% CI 18.2%–23.3%)**. Feature 002 assumed about 19%; the
  assumption lies inside the interval (FR-004).
- **Implied probability that a perfect candidate PASSes a feature-002 attempt**: (1 − r)² =
  **0.629 (95% CI 0.588–0.669)**. The positive control and the candidate must both pass.
- 12 of 15 families match their expected rates. The 3 that do not are explained in section 4.
  None of them suggests a harness defect.
- Nothing in feature 002 was changed (FR-005): not the harness, rules, verdicts or seed sets.

## 2. Files created or modified (US1)

| File | Role |
|------|------|
| `scripts/calibrate.py` | Runner: 100 × 2²¹ bits per run from `os.urandom`, scored through the feature-002 code path (`evalcore`, `sp80022.assess`); harness hash guard; `--resume`; gaps refused |
| `scripts/calibration_report.py` | Summary: Clopper–Pearson intervals, expected rates, co-failure (Fisher), implied PASS probability, `SHA256SUMS` |
| `tests/test_calibration.py` | 12 unit tests |
| `reports/003-extended-batteries-calibration/calibration/runs/run-0000…0999.json.gz` | 1,000 run records (167 MB), every per-sequence p-value (FR-002); input bytes not stored, only their SHA-256 (FR-006) |
| `…/calibration/runs/SHA256SUMS` | Hash of every record |
| `…/calibration/summary.json`, `summary.md` | Calibration result |
| `…/calibration/calibrate-output.txt`, `test-log.md`, `phase-report.md` | Logs and this report |
| `specs/003-extended-batteries-calibration/tasks.md` | T001–T010 marked done |

## 3. Commands run and results

| Task | Command | Result |
|------|---------|--------|
| T004–T006, re-run T010 | `python -W ignore -m unittest tests.test_calibration` | 12 OK (10.4 s) |
| T007 | `calibrate.py --runs 0-1` into the scratchpad | 1 pass, 1 fail (rank); not counted |
| T008 | `python -W ignore scripts/calibrate.py --runs 0-999 --workers 32 --out-dir reports/003-extended-batteries-calibration/calibration/runs` | 1,000/1,000 runs, exit 0, no interruption; 08:52–22:36 (13 h 44 min; 49.4 s per run) |
| T009 | `python scripts/calibration_report.py --runs-dir …/calibration/runs --out …/calibration/summary.json`, twice | Byte-identical outputs (`cmp`); `summary.json` `a41e512d…1ec8`, `SHA256SUMS` `8708246e…4f62` |

SC-001: 1,000 of 1,000 runs completed, and the overall rate has an interval. SC-002: each
family has a measured rate, an interval and an expected rate (table in `summary.md`).

## 4. Results by family

| Family | Failures | Rate (95% CI) | Expected | Consistent |
|--------|----------|---------------|----------|------------|
| frequency | 16 | 0.016 (0.009–0.026) | 0.0185 | yes |
| block_frequency | 15 | 0.015 (0.008–0.025) | 0.0185 | yes |
| runs | 21 | 0.021 (0.013–0.032) | 0.0185 | yes |
| longest_run | 13 | 0.013 (0.007–0.022) | 0.0185 | yes |
| rank | 16 | 0.016 (0.009–0.026) | 0.0185 | yes |
| **dft** | 32 | 0.032 (0.022–0.045) | 0.0185 | **no** |
| non_overlapping_template | 12 | 0.012 (0.006–0.021) | 0.0065 | yes |
| overlapping_template | 20 | 0.020 (0.012–0.031) | 0.0185 | yes |
| universal | 23 | 0.023 (0.015–0.034) | 0.0185 | yes |
| linear_complexity | 19 | 0.019 (0.012–0.030) | 0.0185 | yes |
| serial | 1 | 0.001 (0.000–0.006) | 0.0003 | yes |
| approximate_entropy | 17 | 0.017 (0.010–0.027) | 0.0185 | yes |
| **cumulative_sums** | 5 | 0.005 (0.002–0.012) | 0.0003 | **no** |
| random_excursions | 0 | 0.000 (0.000–0.004) | 0.0012 | yes |
| **random_excursions_variant** | 16 | 0.016 (0.009–0.026) | 0.0055 | **no** |

Failing families per run: 0 in 793 runs, 1 in 190, 2 in 15, 3 in 2. So nearly all false
failures come from a single family.

**Why three families differ.** These are descriptive checks on the stored records, made after
the result. They change nothing.

- **dft** (1 sub-test, k_max 0): all 32 failures are proportion failures, none are uniformity
  failures. The DFT sub-test itself rejects too often under these rules: 3.2% against 1.85%.
  The cross-check ([dft-crosscheck.md](./dft-crosscheck.md)) confirms that this comes from the
  test, not the port:
  - our dft agrees with NIST STS 2.1.2 on 1,000 fresh sequences, with 0 mismatches;
  - across the 100,000 stored sequences, dft rejects 1.23% at α = 0.01, against 0.96% for
    frequency, and E[d²] = 1.062 where 1 is expected. The test's variance constant is about 6%
    too small;
  - this predicts a family rate of 3.5% (CI 3.0–4.2%), which matches the measured 3.2%.
- **cumulative_sums** (2 sub-tests, k_max 1): each sub-test fails at the expected rate, 43 of
  2,000 = 2.15% (expected 1.85%). The family fails only when both sub-tests fail. The forward
  and backward sums are strongly correlated, so they fail together far more often (5 runs) than
  the independence model behind "expected" assumes. Cumulative sums also co-fails with
  frequency: 4 joint failures, Fisher p = 2.2 × 10⁻⁷.
- **random_excursions_variant** (18 sub-tests, k_max 1): 105 sub-test failures in total. At that
  rate, independent sub-tests would give about 0.5% family failures, which is the expected value.
  The measured rate is 1.6% because failures cluster: runs with 3, 4, 5 and 7 failing states
  occur, and neighbouring states are correlated.

So the expected-rate model is accurate for single sub-test families with uniform p-values. It
underestimates families whose sub-tests are correlated, and the DFT test has a small excess of
its own. The overall rate, which is what decides a verdict, matches the feature-002 assumption.

## 5. What this means for feature-002 `heldout-2` and `heldout-3`

Under feature-002 Amendment 1, an attempt is INCONCLUSIVE and the set is used if the positive
control fails. Using r = 0.207, a perfect candidate in a further feature-002 attempt has
these chances:

| Outcome | Probability |
|---------|-------------|
| PASS | 0.629 |
| INCONCLUSIVE (positive control fails; set used) | 0.207 |
| FAIL (control passes, perfect candidate fails by chance) | 0.164 |

Over the two remaining sets, the chance of at least one PASS for a perfect candidate is
1 − 0.371² ≈ 0.86. Attempt 1's PASS is consistent with this. No feature-002 attempt is made or
proposed here.

## 6. Recommendations (recommendation only)

None of these is applied. Each would need a separate, owner-approved spec amendment, and an
amendment may only make the protocol stricter (feature 002 FR-014).

1. Record **r = 0.207 (0.182–0.233)** as the measured false-failure baseline for this harness and
   these rules, in place of the ~19% assumption.
2. Any future expected-rate model should allow for correlation inside cumulative_sums and
   random_excursions_variant, and for the DFT excess. That matters only for reporting: no rule
   is loosened.
3. Report a single-family positive-control failure as an expected event, about 1 in 5 attempts,
   and not as evidence about the harness.

## 7. Open issues and assumptions

- **Run records, 167 MB**: the owner decided at T011, on 2026-10-30, that they are committed
  (research R10). No `.gitignore` rule is added.
- The "expected" column assumes independent sub-tests and treats uniformity as independent of
  proportion. Section 4 shows where that does not hold.
- DFT: resolved by the cross-check, which the owner asked for at T011
  (`scripts/dft_crosscheck.py`, `dft-crosscheck.json`, `dft-crosscheck.md`). The excess is the
  test's own; harness 1.0.0 (`1563526e…0602c41700`) is unchanged.

## 8. Security concerns

None new. This phase measures the statistical test, not the generator. A statistical pass rate
says nothing about cryptographic security.

## 9. Recommendation

**Proceed.** US1 is complete and ready for the owner review at T011. The battery work (US2/US3)
continues on dev data only. Held-out battery sets are not used before the freeze approval at
T034, which requires T011.
