# NIST SP 800-22 Screening Summary: float-v0 vs lut-v1

**Feature**: 001-integer-lut-perturbation | **Date**: 2026-10-28 | **Tool**: nistrng 1.2.3 via `scripts/nist_eval.py` | **Sample**: 1,000,000 bits per run, MSB-first per 32-bit word

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
