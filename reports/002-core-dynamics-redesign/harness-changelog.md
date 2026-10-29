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

## Entry 2: 2026-10-28, harness `sp80022` 1.0.0 (validated; frozen pending review T030)

- **Changes since 0.1.0** (made during T010, T011 and T021–T028; research R11):
  - `sp800-22-fidelity`: Longest Run with M = 8 uses the exact π = 55/256, 94/256, 59/256 and
    48/256 instead of the 4-decimal printed values, which reproduce the §2.4.8 example.
    No effect at n = 2²¹, which uses M = 10000.
  - `sp800-22-fidelity`: Universal always applies the c(L, K) correction, as in the §2.9.8
    example. The unused `variance_correction` option was removed. Its default was already the
    correction, so evaluator output does not change.
  - Version bumped from 0.1.0 to 1.0.0. Source SHA-256
    `1563526ed25f695dba223c3d62c8ce900ba4f485dd62f09a694ece0602c41700`.
- **Decisions recorded, with no code change** (R11):
  - Overlapping Template keeps the Rev. 1a π (§2.8.4, §3.8). STS 2.1.2 and the published
    example values use the older Poisson π. At n = 2²¹, the old π would make random data fail
    p < 0.01 on 1.23% of sequences instead of 1.00%. That is a calibration error, not extra
    strictness.
  - Linear Complexity keeps π₀ = 0.010417 (§2.10.4, §3.10). STS uses 0.01047. Effect: λ ≈ 0.001.
  - Two document inconsistencies: §2.6.8 N₁, and the §2.14.8 state +1 entry. Our values agree
    with Appendix B.
- **Evidence**:
  - `python -W ignore -m unittest discover -s tests -t .`: 80 tests OK, 3 skipped (G-SHA-1
    examples; see R11).
  - Worked examples (T010) and Appendix B (T011): 56 of 64 Appendix B values match directly. The
    other 8 (OTM and LC) match when recomputed from our counts with the published constants.
  - [harness/oracle-compare.md](./harness/oracle-compare.md): sp80022 vs NIST STS 2.1.2 on
    π, e, √2, √3, SHA-1 and 10 cal-1 sequences. 0 mismatches at ±1e-6; largest difference
    5.0e-7. Oracle build: [harness/sts-2.1.2.md](./harness/sts-2.1.2.md).
  - `cal-1` re-scored with 1.0.0
    ([harness/cal-1-rescore-1.0.0.json](./harness/cal-1-rescore-1.0.0.json)): sequences,
    sub-tests, families, verdict, parameters and bytes are identical to `cal-1.json` (0.1.0).
    So the T024 and T025 evidence carries over to 1.0.0.
- **Statement (FR-014)**: this change removes no test or sub-test, does not shorten sequences,
  does not reduce the sequence count, and does not loosen thresholds.
- **Status**: validated. The harness becomes authoritative after owner review (T030).
