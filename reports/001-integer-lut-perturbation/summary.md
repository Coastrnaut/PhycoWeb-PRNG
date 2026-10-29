# NIST SP 800-22 Screening Summary: float-v0 vs lut-v1

**Feature**: 001-integer-lut-perturbation | **Date**: 2026-10-28 | **Tool**: nistrng 1.2.3 via `scripts/nist_eval.py` | **Sample**: 1,000,000 bits per run, MSB-first per 32-bit word

> **Erratum (2026-10-28, approved by the owner; feature 002 research R1).** The harness used
> here, nistrng 1.2.3, was found to be defective after this summary was approved. On sequences
> of 2²¹ bits taken directly from `os.urandom`, it gave:
>
> - **Linear Complexity**: p = 0.0 on 5 of 5 sequences (N8).
> - **Random Excursion**: p = 0.0 on 39 of 40 sub-tests (N6).
> - **Overlapping Template**: p = 0.0 on 5 of 5 sequences (N5).
> - **Maurer's Universal**: p ≈ 0.998 every time (N7).
> - **Non-Overlapping Template**: divides by the variance squared, so p = 1.0 always (N4).
> - **Random Excursion Variant**: returns p-values above 1, which is impossible (N9; found
>   during feature-002 T008, same day).
>
> Therefore:
>
> - The Linear Complexity and Random Excursion failures below, in every run, say **nothing**
>   about either model.
> - The Maurer's Universal, Non-Overlapping Template and Random Excursion Variant passes are
>   also **uninformative**.
> - The other lut-v1 failures with seed 1024… (Monobit, Frequency Within Block, Approximate
>   Entropy, Cumulative Sums) were in tests that behaved normally on urandom input. They still
>   stand, but they are unconfirmed.
>
> The defects were observed at 2²¹ bits, not at the 10⁶ bits used here. The four inputs will
> be re-scored with the feature-002 harness, and the results added here as a re-score table.
> The original text below is left unchanged as the approved record.

### Re-score with the feature-002 harness (2026-10-28, T057)

The same four inputs were regenerated (10⁶ bits each, MSB-first, from `gen_vectors.generate`) and scored with `sp80022` 1.0.0, the harness validated in feature 002 (research R3, NIST STS oracle). Each input is **a single sequence**, so these are per-test p-values only: no proportion or uniformity assessment is possible, and roughly 1 sub-test in 100 is expected below 0.01 by chance (about 2 of the 188 per input). Bold marks p < 0.01. Records: `reports/002-core-dynamics-redesign/feature001-rescore/*.json`, made with `python -W ignore scripts/sts_eval.py --source file --bytes <input> --bits 1000000 --out ...` (exit 1 by design: one sequence cannot pass a family, m′ < 55).

| Test | float-v0, seed 1024… | float-v0, seed 4660… | lut-v1, seed 1024… | lut-v1, seed 4660… |
|------|------|------|------|------|
| Frequency (Monobit) | 0.1499 | 0.1270 | **0.0020** | 0.6017 |
| Block Frequency (M=128) | 0.7013 | 0.2412 | 0.1416 | 0.7351 |
| Runs | 0.3607 | 0.6860 | 0.1086 | 0.2334 |
| Longest Run (M=10000) | 0.9606 | 0.1684 | 0.6116 | 0.3175 |
| Rank | 0.3348 | 0.6699 | 0.7294 | 0.3787 |
| DFT | 0.0587 | 0.3128 | 0.2629 | 0.3446 |
| Non-Overlapping Template (148) | **2/148 below 0.01 (min 0.0011)** | 0/148 below 0.01 (min 0.0156) | **3/148 below 0.01 (min 0.0051)** | **1/148 below 0.01 (min 0.0014)** |
| Overlapping Template | 0.3874 | 0.4582 | 0.9217 | 0.0320 |
| Universal (L=7) | 0.2716 | 0.0567 | 0.1434 | 0.6061 |
| Linear Complexity | 0.3416 | 0.3862 | 0.8137 | 0.3145 |
| Serial (2) | 0/2 below 0.01 (min 0.9634) | 0/2 below 0.01 (min 0.8221) | 0/2 below 0.01 (min 0.2144) | 0/2 below 0.01 (min 0.2833) |
| Approximate Entropy (m=10) | 0.2566 | 0.0939 | 0.4874 | 0.4234 |
| Cumulative Sums (2) | 0/2 below 0.01 (min 0.1705) | 0/2 below 0.01 (min 0.0381) | **2/2 below 0.01 (min 0.0025)** | 0/2 below 0.01 (min 0.7958) |
| Random Excursions (8) | not eligible (J < 500) | not eligible (J < 500) | not eligible (J < 500) | not eligible (J < 500) |
| Random Excursions Variant (18) | not eligible (J < 500) | not eligible (J < 500) | not eligible (J < 500) | not eligible (J < 500) |

Input SHA-256: float-v0 1024… `075854dde62a92a5…`; float-v0 4660… `0c8f4471ae1135d0…`; lut-v1 1024… `25a7b878fab1d2b6…`; lut-v1 4660… `68b607a4e56ab1c2…`.

Reading (no new claim is made from single sequences):

- lut-v1 with seed 1024… has Frequency p = 0.0020 and both Cumulative Sums p < 0.01, so the original Monobit and Cumulative Sums failures are **reproduced** by the validated harness. Its original Frequency Within Block and Approximate Entropy failures are **not** reproduced (p = 0.14 and 0.49). The parameters differ from nistrng's (block M = 128, ApEn m = 10, research R2), so that difference is not a contradiction.
- The Linear Complexity and Random Excursion failures in the original text were nistrng artefacts. With the validated harness, Linear Complexity has p between 0.31 and 0.81 on all four inputs, and the excursion tests are not eligible (fewer than 500 cycles) on all four.
- Single-sequence results cannot show that a generator is good. The multi-sequence verdict for lut-v1 is in feature 002: it fails 11 of 15 families on 100 dev seeds and on 100 held-out seeds (`reports/002-core-dynamics-redesign/attempt-1/`).

Source records: the four `nist_*.json` files in this directory. Values below are copied from them, rounded to 6 decimals. `p_value` is the smallest of a test's p-values; status is nistrng's verdict (every p-value ≥ 0.01).

## Seed 1024, 2048, 4096, 8192

| Test | float-v0 | lut-v1 |
|------|----------|--------|
| monobit | pass 0.149867 | **FAIL** 0.002015 |
| frequency_within_block | pass 0.345415 | **FAIL** 0.003064 |
| runs | pass 0.360677 | pass 0.108608 |
| longest_run_ones_in_a_block | pass 0.981278 | pass 0.587500 |
| binary_matrix_rank | pass 0.334839 | pass 0.729411 |
| dft | pass 0.058706 | pass 0.262906 |
| non_overlapping_template_matching | pass 1.000000 | pass 1.000000 |
| overlapping_template_matching | not eligible | not eligible |
| maurers_universal | pass 0.998626 | pass 0.998172 |
| linear_complexity | **FAIL** 0.000000 | **FAIL** 0.000000 |
| serial | pass 0.141826 (min of 2) | pass 0.058898 (min of 2) |
| approximate_entropy | pass 0.100985 | **FAIL** 0.009870 |
| cumulative sums | pass 0.170501 (min of 2) | **FAIL** 0.002528 (min of 2) |
| random_excursion | **FAIL** 0.000000 (min of 8) | **FAIL** 0.000000 (min of 8) |
| random_excursion_variant | pass 0.128300 (min of 18) | pass 0.057378 (min of 18) |

## Seed 4660, 43981, 21845, 43690

| Test | float-v0 | lut-v1 |
|------|----------|--------|
| monobit | pass 0.127010 | pass 0.601670 |
| frequency_within_block | pass 0.069704 | pass 0.373326 |
| runs | pass 0.685970 | pass 0.233368 |
| longest_run_ones_in_a_block | pass 0.451931 | pass 0.497313 |
| binary_matrix_rank | pass 0.669935 | pass 0.378655 |
| dft | pass 0.312769 | pass 0.344560 |
| non_overlapping_template_matching | pass 1.000000 | pass 1.000000 |
| overlapping_template_matching | not eligible | not eligible |
| maurers_universal | pass 0.997619 | pass 0.999356 |
| linear_complexity | **FAIL** 0.000000 | **FAIL** 0.000000 |
| serial | pass 0.376302 (min of 2) | pass 0.283613 (min of 2) |
| approximate_entropy | pass 0.240591 | pass 0.524758 |
| cumulative sums | pass 0.038054 (min of 2) | pass 0.795817 (min of 2) |
| random_excursion | **FAIL** 0.000000 (min of 8) | **FAIL** 0.000000 (min of 8) |
| random_excursion_variant | pass 0.085249 (min of 18) | pass 0.047565 (min of 18) |

## Counts

| Run | pass | fail | not eligible |
|-----|------|------|--------------|
| float-v0, seed 1024, 2048, 4096, 8192 | 12 | 2 | 1 |
| lut-v1, seed 1024, 2048, 4096, 8192 | 8 | 6 | 1 |
| float-v0, seed 4660, 43981, 21845, 43690 | 12 | 2 | 1 |
| lut-v1, seed 4660, 43981, 21845, 43690 | 12 | 2 | 1 |

## Failures (reported as-is)

- **float-v0, seed 1024, 2048, 4096, 8192**: linear_complexity (p = 0.000000); random_excursion (p = 0.000000)
- **lut-v1, seed 1024, 2048, 4096, 8192**: monobit (p = 0.002015); frequency_within_block (p = 0.003064); linear_complexity (p = 0.000000); approximate_entropy (p = 0.009870); cumulative sums (p = 0.002528); random_excursion (p = 0.000000)
- **float-v0, seed 4660, 43981, 21845, 43690**: linear_complexity (p = 0.000000); random_excursion (p = 0.000000)
- **lut-v1, seed 4660, 43981, 21845, 43690**: linear_complexity (p = 0.000000); random_excursion (p = 0.000000)

Every run fails **Linear Complexity** (p = 0.000000) and **Random Excursion** (smallest of 8 p-values = 0.000000), for both models and both seeds.

With the reference seed, lut-v1 fails 4 more tests than float-v0 (Monobit, Frequency Within Block, Approximate Entropy, Cumulative Sums). With the second seed it fails the same 2 as float-v0. Two seeds of one sequence each cannot show whether this difference comes from the perturbation source or from sampling variation.

## Limitations (verbatim from the reports)

- Single sequence per seed; not the multi-sequence proportion/uniformity analysis of SP 800-22.
- Passing statistical tests is not evidence of cryptographic security.
- Tests are run individually on copies of the bits, not via nistrng.run_all_battery, because nistrng 1.2.3's Binary Matrix Rank test modifies its input in place.
- nistrng's Non-Overlapping Template Matching evaluates ONE randomly chosen template (Python random seeded with TEMPLATE_SEED before each test), not all 148 templates as in SP 800-22.
- p_value is the minimum of a test's p-values; nistrng's own pass/fail (all p-values >= 0.01) is used for status.

Additional notes:

- Non-Overlapping Template Matching gives p = 1.000000 in all four runs. With a single template this result is treated as **uninformative**. It has not been investigated.
- Overlapping Template Matching was not eligible for this sequence length in nistrng; it is reported and not omitted.
- Results from an earlier harness version were **invalid** (research R6, findings N2 and N3: in-place input mutation, averaged p-values, random template) and were discarded. Only these regenerated records are valid.
- Provenance: the owner committed files while these runs were in progress, so `git_head` differs between records (`b9fb0f7` for float-v0 with seed 1024…, `22bd079` for the others). All four runs used identical `phycoweb/` and `scripts/` contents (`git diff 22bd079 -- phycoweb scripts` is empty; the code in `b9fb0f7`'s dirty tree was the same). After the runs,
  `scripts/gen_vectors.py` changed in one way only: its archive loader now sets
  `sys.dont_write_bytecode`, so no `__pycache__` is written into `baseline/`. That does not
  affect generated words; `--verify` against both vector files still passes.
- Linear Complexity was not cross-checked independently. Cumulative Sums was: float-v0 with seed 1024… has a forward p of 0.170501, matching an independent scipy recomputation (0.1705).

**These results do not show that either model is random or secure. Passing statistical tests is not evidence of cryptographic security** (Constitution Principle IV, Security Policy).
