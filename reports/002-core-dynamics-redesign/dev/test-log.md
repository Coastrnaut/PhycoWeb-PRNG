# Test Log: phyco-v2 reference model (T043; SC-001, SC-004, Principle V)

Date: 2026-10-28. Model `phycoweb/model_v2.py` (`MODEL_ID = "phyco-v2"`, design.md 1.0).
Harness `sp80022` 1.0.0.

| Environment | Command | Result |
|-------------|---------|--------|
| Windows 11, Python 3.10.11, numpy 2.2.6, scipy 1.15.3 | `python -W ignore -m unittest discover -s tests -t .` | **97 tests OK, 3 skipped**, exit 0 (61 s) |
| Ubuntu (WSL2), Python 3.14.4, numpy 2.5.4, scipy 1.18.1 | `~/.venvs/phycoweb/bin/python -W ignore -m unittest discover -s tests -t .` | **97 tests OK, 3 skipped**, exit 0 (43 s) |

The 3 skips are the sp80022 worked examples that can't be reproduced: §2.6.8, which is
inconsistent with its own input, and §2.7.8 and §2.9.8, which need G-SHA-1 data (research R11).

The suite includes:
- all feature-001 tests (lut-v1 and float-v0 vectors, period, purity, baseline, equivalence);
- the harness and protocol tests;
- the new phyco-v2 tests:
  - `test_purity_v2`: AST check. No `*`, `/`, `//`, `%` or `**`, no floats, literal shift
    amounts only, allowed imports only.
  - `test_widths_v2`: 5,002 fuzz and edge states stay within their widths after one step.
  - `test_design_trace`: equals an independent transcription of design.md §4 on 2 dev seeds ×
    10,000 words and on the 5,002 states (word, state and disruption flag). Also equals
    exploration variant v005 on 4 seeds × 2,000 words.
  - `test_vectors_v2`: the golden files for dev seeds 0 and 1, determinism, seed domain, and the
    all-equal seeds (not constant; no period ≤ 2¹⁵ in 2¹⁶ words).
  - `test_disruption_v2`: rate in [1%, 50%] on 3 dev seeds × 10⁶ steps.

Vector checks (T042): `scripts/gen_vectors.py --verify` reports "OK: 10000 words match" for both
`vectors/float-v0_seed-1024-2048-4096-8192_10000.hex` and
`vectors/lut-v1_seed-1024-2048-4096-8192_10000.hex`. New golden files:

| File | SHA-256 |
|------|---------|
| `vectors/phyco-v2_seed-56053-7029-30841-11050_10000.hex` | `57e77429353f2bb622ea5dc4ec8e947a633a32626bdcb2ac72ede2669acca773` |
| `vectors/phyco-v2_seed-41278-32039-25293-40850_10000.hex` | `2647415c585555cd094f480289e05bc2f99b9445c555b16135e336a98018e5bc` |

## Dev evidence (T044, T045). Not an acceptance result.

- `python scripts/disruption_rate.py --out reports/002-core-dynamics-redesign/dev/disruption.json`
  (exit 0): the disruption rate is **13.49–13.83%** on all 100 dev seeds and 13.56–13.58% on the
  2 feature-001 seeds, measured over 10⁶ steps after warm-up. All are inside [1%, 50%]. The
  values equal those logged for variant v005 in `research/002/runs.jsonl`.
- `python -W ignore scripts/sts_eval.py --source phyco-v2 --set dev --out reports/002-core-dynamics-redesign/dev/dev-final.json`:
  **15/15 families pass**, verdict pass.
- `python -W ignore scripts/sts_eval.py --source lut-v1 --set dev --out reports/002-core-dynamics-redesign/dev/dev-lut-v1.json`:
  **fails 11 of 15 families**: frequency, block_frequency, runs, longest_run, dft,
  non_overlapping_template, overlapping_template, universal, serial, approximate_entropy and
  cumulative_sums. The harness discriminates (Principle IV).

> Statistical tests that find no defect are not evidence of cryptographic security. The dev
> results are optimistic, because the design was selected on these seeds (design.md §9). Only
> the held-out attempt counts for acceptance.

## Quickstart end to end (T059), 2026-10-28

Run on Windows (Python 3.10.11) and WSL (Python 3.14.4), at git `78a1be7` plus report files.
Steps whose commands write recorded evidence (H2 writes `cal-1.*`; A4 writes `rescore.json`)
were sent to a scratch directory instead and compared with the recorded evidence. Tolerance:
Windows exact; WSL p-values within 1e-9 with verdicts exact (research R7).

| Step | Windows | WSL |
|------|---------|-----|
| H1 `python -m unittest tests.test_sp80022` (worked examples, Appendix B, templates, contract; includes H4 known-bad) | OK, 3 skipped | OK, 3 skipped |
| H2 one fresh positive control, 100 × 2²¹ urandom bits | 14/15. Random Excursions Variant failed (3 of 18 sub-tests at 70/74 vs 71 needed; k_max 1). Allowed by H2 (at most one family by chance). Not a repeat of an earlier failing sub-test, so T024's defect rule is not triggered. See phase-report open issue O3 | 15/15 pass |
| H3 re-score `cal-1.bin` vs `cal-1.json` | identical (max \|Δp\| 0) | verdicts equal, max \|Δp\| 3.1e-13 |
| H5 re-score the 4 feature-001 inputs vs `feature001-rescore/*.json` | identical | input bytes identical (SHA-256), max \|Δp\| 2.2e-16 |
| D1 `python scripts/seedsets.py --check` | 4/4 OK | 4/4 OK |
| D2 `explore.py --set heldout-1` | exit 2 (refused) | exit 2 (refused) |
| D3 `scripts/disruption_rate.py` (102 seeds × 10⁶ steps) vs `dev/disruption.json` | identical per-seed rates, 13.49–13.83% | identical |
| M1 `python -W ignore -m unittest discover -s tests -t .` | 116 OK, 3 skipped | 116 OK, 3 skipped |
| M2 `gen_vectors.py --verify` for the 2 phyco-v2 files | OK, OK | OK, OK |
| M3 `sts_eval.py --source phyco-v2 --set dev` vs `dev/dev-final.json` | identical, pass | pass, max \|Δp\| 5.6e-16 |
| A4 attempt 1 re-score (positive, negative, candidate) | identical (also `rescore_attempt.py`, exit 0) | verdicts equal, max \|Δp\| ≤ 1.0e-15 |

H0 (nistrng defects) is recorded in `harness/nistrng-defects.json` and was not repeated.
