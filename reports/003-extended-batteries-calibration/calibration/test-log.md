# Calibration Test Log (feature 003, US1)

## T004–T006 unit tests (2026-10-29)

`python -W ignore -m unittest tests.test_calibration` (Windows, Python 3.10.11): **12 tests OK**
(10.4 s). Covers runner guards (harness hash, range, no overwrite, resume, gap), record shape,
no byte files, input hash, Clopper–Pearson values, expected rates, summary counts, co-failure,
implied PASS probability, report refusal with missing runs, reproducible report.

## T007 smoke run (2026-10-29)

`python -W ignore scripts/calibrate.py --runs 0-1 --workers 32 --out-dir <scratchpad>/cal-smoke`

| Run | Verdict | Failed families | Time |
|-----|---------|-----------------|------|
| smoke 0 | fail | rank (96/100 passed; bound 97) | 59.3 s |
| smoke 1 | pass | none | 49.1 s |

Records: 15 families, 188 sub-tests, ~173 KB gzip each. Projected full run: 1,000 × ~55 s ≈
15 h; ~173 MB of records. The two smoke runs were written to the scratchpad by design (T007)
and are **not** part of the 1,000 calibration runs; they are reported here only.

## T008 full calibration

Command (started in the background):
`python -W ignore scripts/calibrate.py --runs 0-999 --workers 32 --out-dir reports/003-extended-batteries-calibration/calibration/runs`

Console output: `calibration/calibrate-output.txt`. Interruptions and resumes are listed below.

| Event | Time | Note |
|-------|------|------|
