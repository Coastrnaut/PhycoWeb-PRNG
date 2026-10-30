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
| start | 2026-10-29T08:52:30 | runs 0000–0999, 32 workers |
| end | 2026-10-29T22:36:22 | exit 0; no interruption, no `--resume` needed |

Runs: 1,000 records present (`run-0000` … `run-0999`), 167 MB total. Time per run: mean 49.4 s
(min 48.8, max 59.6); wall time 13 h 44 min. Verdicts: 793 pass, 207 fail.

## T009 summary (2026-10-29)

`python scripts/calibration_report.py --runs-dir reports/003-extended-batteries-calibration/calibration/runs --out reports/003-extended-batteries-calibration/calibration/summary.json`
(Windows, Python 3.10.11, 25.8 s), run twice. Both runs printed
`overall 0.2070 [0.18228090285734658, 0.23345695036925954]`; `cmp` of `summary.json` and
`summary.md` against a copy of the first run: **identical** (quickstart C3).

| File | SHA-256 |
|------|---------|
| `summary.json` | `a41e512d4d108d12d699dd2fa7163c37eabd6ca3f697ac4668aaa294044d1ec8` |
| `summary.md` | `8184eed374ef4a1918dd9eba3a761518dcccc3af6fa64fe4cc8b106a9f9a920a` |
| `runs/SHA256SUMS` | `8708246efc94e99a81e2db2284cb1eac68c71b476838a9569bfa9fbd42cd4f62` |

## T010 re-run of unit tests (2026-10-29)

`python -W ignore -m unittest tests.test_calibration` (Windows): **12 tests OK** (10.4 s).
