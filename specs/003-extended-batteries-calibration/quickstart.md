# Quickstart: Extended Batteries and Positive-Control Calibration

Validation guide. `REP=reports/003-extended-batteries-calibration`. Windows commands use the
feature-002 Python; WSL commands use `~/.venvs/phycoweb/bin/python` (written `wpy`) from
`/mnt/c/GIT/PhycoWeb-PRNG`. Contracts: [contracts/cli.md](./contracts/cli.md); records:
[data-model.md](./data-model.md).

## Prerequisites

- Spec approved (done 2026-10-29).
- For C1–C3: nothing else.
- For S1–S3: WSL with gcc 15 and make (present).
- For B1–B5: owner permission for, and completion of, the PractRand and TestU01 downloads and
  builds (`$REP/tools/*.json`); calibration result review approved.

## Calibration (US1)

| Step | Command | Expected |
|------|---------|----------|
| C0 | `python -W ignore -m unittest discover -s tests -t .` | all tests pass, including the new calibration tests (mocked evaluator) |
| C1 | `python -W ignore scripts/calibrate.py --runs 0-999 --workers 32 --out-dir $REP/calibration/runs` | 1,000 run files; about 17 h; a crash is resumed with `--resume` |
| C2 | `python scripts/calibration_report.py --runs-dir $REP/calibration/runs --out $REP/calibration/summary.json` | summary with overall rate and 95% interval no wider than ±3 points (SC-001), 15 per-family rows with "consistent" flags (SC-002), co-failure matrix, implied PASS probability |
| C3 | re-run C2 | byte-identical `summary.json` |

## Fast streams (US3)

| Step | Command | Expected |
|------|---------|----------|
| S1 | `python scripts/gen_c_lut.py --check`; `make -C fast` (WSL) | header up to date; build with `-Werror` succeeds |
| S2 | `wpy scripts/stream_equiv.py --binary fast/build/phyco_stream --set dev --out $REP/streams/equivalence.json` | 0 mismatches: golden vectors and 2 × 100 × 10⁶ words |
| S3 | `fast/build/phyco_stream os --words 4 --hex`; `phyco_stream phyco-v2 1 2 3 70000` | 4 hex words; second exits 2 |

## Batteries (US2)

| Step | Command | Expected |
|------|---------|----------|
| B1 | `wpy scripts/battery_run.py --set dev --role candidate --battery smallcrush --orientation fwd --seed 56053 7029 30841 11050 --out $REP/dev/…` | complete run, `run.json` with all p-values; the same for each battery (dev rehearsal, research R9) |
| B2 | `wpy scripts/battery_run.py --set dev … --seed <heldout seed>` | exit 2 (held-out seed refused) |
| B3 | `wpy scripts/battery_freeze.py create --attempt 1 --S <S from B1>`; owner approves; `validate` | validate exit 0 only after approval |
| B4 | `wpy scripts/battery_attempt.py --attempt 1` | `attempt.json` with equivalence 0 mismatches, positive/negative/candidate results and a verdict; 1–3 days |
| B5 | `wpy scripts/battery_rescore.py --attempt 1` | identical outcomes and verdict (SC-006) |
| B6 | `battery_attempt.py --attempt 1` again; `--attempt 2` after a FAIL | both exit 2 |
