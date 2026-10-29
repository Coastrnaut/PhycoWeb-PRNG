# Harness Change Log: 002-core-dynamics-redesign

Every change to the NIST SP 800-22 evaluation harness is listed here (FR-014, SC-005). Each
entry must be in one of the permitted categories: `defect-fix`, `sp800-22-fidelity`,
`added-coverage`. No entry may remove a test or sub-test, shorten sequences, reduce the
sequence count, or loosen a threshold.

## Entry 1: 2026-10-28, harness `sp80022` 0.1.0 (replaces nistrng 1.2.3)

- **Change**: replace nistrng 1.2.3 with our own SP 800-22 Rev. 1a implementation, `sp80022`
  (research R1, R2).
- **Categories**:
  - `defect-fix`: nistrng defects N4–N9.
  - `added-coverage`: Non-Overlapping Template Matching goes from 1 template to all 148
    length-9 templates (147 more sub-tests). Overlapping Template Matching becomes eligible at
    2²¹ bits.
  - `sp800-22-fidelity`: parameters follow SP 800-22 / NIST STS 2.1.2 defaults (R2).
- **Evidence**: [`harness/nistrng-defects.json`](./harness/nistrng-defects.json), produced by
  `python -W ignore scripts/repro_nistrng_defects.py` (exit 0, all six reproduced):
  4 sequences of 2²¹ bits from `os.urandom`, each test on its own copy, `random.seed(0)`.

  | Defect | Test | Symptom on urandom input |
  |--------|------|--------------------------|
  | N4 | Non-Overlapping Template | p = 1.0 on 4/4. The code divides by the variance squared; no length-9 template set |
  | N5 | Overlapping Template | p = 0.0 on 4/4 |
  | N6 | Random Excursion | p < 0.001 on at least 90% of the 32 sub-test p-values |
  | N7 | Maurer's Universal | p between 0.998 and 1.0 on 4/4 |
  | N8 | Linear Complexity | p = 0.0 on 4/4 |
  | N9 | Random Excursion Variant | p-values above 1 (impossible) on 4/4 |

- **Environment**: Windows 11, Python 3.10.11, numpy 2.2.6, scipy 1.15.3, nistrng 1.2.3. The WSL
  environment has scipy 1.18.1 and numpy 2.5.4 (T003).
- **Statement (FR-014)**: this change removes no test or sub-test, does not shorten sequences,
  does not reduce the sequence count, and does not loosen thresholds.
- **Status**: the harness is not yet authoritative. It becomes so at version 1.0.0, after
  validation (T024, T025, T028) and owner review (T030).

## Validation log (no harness change; recorded for T024, T025)

- **T024 calibration** on the positive control (100 × 2²¹ bits from `os.urandom` per run):
  - `cal-1`: 15/15 families pass.
  - `cal-2`: 15/15 families pass.
  - `cal-3`: 14/15. Linear Complexity failed proportion: 95 of 100 p ≥ 0.01, when 97 are
    needed; its uniformity was P-valueᴛ 0.456.
  - Only one sub-test failed, in one run, which is within the T024 rule.
  - Pooled over 300 sequences, 0 of 188 sub-tests fail uniformity (lowest P-valueᴛ 0.016).
  - Because Linear Complexity was a nistrng defect (N8), it got a separate diagnostic: 2,000
    urandom sequences, LC only.
    - 18 of 2,000 p < 0.01 (about 20 expected); P-valueᴛ 0.18.
    - Pooled class frequencies over 8.4 million blocks match the SP 800-22 π values
      (χ² = 5.29, p = 0.51).
    - Conclusion: the `cal-3` failure is chance, not bias.
  - About 25% of sequences are not eligible for the Random Excursion tests (m′ = 226 of 300).
    This matches P(J < 500) ≈ 0.27 for a random walk of 2²¹ steps.
- **T025 reproducibility**: see [harness/reproducibility.md](./harness/reproducibility.md).
  Same environment: identical. WSL vs Windows: verdicts identical, p-values within 3.1e-13.
- **T023 timing**: 1.44 s per sequence (nistrng: 128 s), and 60 s for 100 sequences on 32
  workers. See [harness/timing.json](./harness/timing.json).
