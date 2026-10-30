# Test Log: Feature 003

## T003 Baseline (2026-10-29, git `f507c6b` plus uncommitted feature-002/003 documents)

| Environment | Command | Result |
|-------------|---------|--------|
| Windows 11, Python 3.10.11 | `python -W ignore -m unittest discover -s tests -t .` | **116 tests OK, 3 skipped** (53.5 s) |
| Ubuntu (WSL2), Python 3.14.4 | `~/.venvs/phycoweb/bin/python -W ignore -m unittest discover -s tests -t .` | **116 tests OK, 3 skipped** (46.5 s) |

Frozen sources (must be unchanged at T040):

| File | SHA-256 |
|------|---------|
| `phycoweb/model_v2.py` | `1260142d1205f5d7340cf3f82ed557bbe9dc7bb5de370e668688964d01f1c2ec` |
| `phycoweb/model.py` | `80ffd147af92006204bd426bc99259fcbd6e55dc655295a9ad1aedc2685ec346` |
| `phycoweb/lut.py` | `387a99edefac0e9d38e97f7e84b24d19d6d96dfdcbd14f3866bf01940a49b5c3` |
| `protocol/seedsets.py` | `0471cb7bd009500a885f3a2228dae9b637469ab5b44bc51ae0dee4e1a228c057` |
| `scripts/evalcore.py` | `ab4ad2d1b29893c02582f73b24abbcffa35973cf0c9d9aa6a9b5188328525298` |
| `sp80022` 1.0.0 (`source_sha256`) | `1563526ed25f695dba223c3d62c8ce900ba4f485dd62f09a694ece0602c41700` |

## T012–T015 fast streams (2026-10-29)

| Environment | Command | Result |
|-------------|---------|--------|
| WSL, gcc 15.2.0 | `make -C fast` | builds with `-O2 -std=c99 -Wall -Wextra -Werror`, no warnings |
| Windows | `python -W ignore -m unittest tests.test_fast_stream` | 8 tests: 2 OK (LUT header, no `*` `/` `%` in the phyco-v2 block), 6 skipped (need the Linux binary) |
| WSL | `~/.venvs/phycoweb/bin/python -W ignore -m unittest tests.test_fast_stream` | **8 tests OK**: all 3 golden vector files match word for word (3 × 10,000), bad seeds exit 2, `--reverse`, little-endian order, `os`, closed pipe exits 0 |

Throughput, measured **while the calibration used all 32 cores** (`--words 10^8 > /dev/null`):
phyco-v2 3.52 s, lut-v1 3.93 s, os 1.14 s per 10⁸ words (≈ 2.8 × 10⁷, 2.5 × 10⁷, 8.8 × 10⁷
words/s). Below the plan's 10⁸ words/s goal; to be re-measured on an idle machine at T016.

## T019–T031 tools and protocol code (2026-10-29)

| Environment | Command | Result |
|-------------|---------|--------|
| WSL | `bash fast/build_tools.sh practrand …`; `RNG_test --self_test` | built (12 upstream warnings, recorded in `tools/practrand.json`); **self-test passed** |
| WSL | `bash fast/build_tools.sh testu01 …` | built with `CFLAGS="-O2 -std=gnu89"` (50 upstream warnings) |
| WSL | `make -C fast build/testu01_driver` | builds with `-Werror` |
| WSL | `phyco_stream os \| testu01_driver smallcrush …` | 15 statistics, all passed, 10.3 s |
| WSL | `battery_run.py --set dev` smoke runs (PractRand 2²⁸ os; PractRand 2³⁰ lut-v1 with stop-on-fail; SmallCrush rev lut-v1; SmallCrush fwd phyco-v2 dev seed 0) | os: 937 p-values, no FAIL grade, min tail 4e-5; lut-v1 PractRand: stopped at 2²⁷ with 370 FAIL grades; lut-v1 SmallCrush rev: 14 of 15 statistics eps / 1 − eps1; phyco-v2 SmallCrush fwd: 15 p-values, min 0.038, no eps |
| WSL | guards: held-out seed with `--set dev`; `--stop-on-fail` on the candidate | both exit 2 |
| Windows | `python -W ignore -m unittest tests.test_batteries` | **12 tests OK** |
| Windows | `python -W ignore -m unittest tests.test_battery_protocol` | **28 tests OK** (41.6 s) |

These smoke outputs are the parser fixtures in `tests/data/batteries/` (T027; taken from these
dev smoke runs, before the full rehearsal). A defect was found and fixed through them: the first
rule-3 pattern also matched TestU01's legend lines "(eps means a value < 1.0e-300)", which appear
whenever any p-value is outside [0.001, 0.999] — a chance event for a good generator — and would
have failed a good positive control. The pattern now matches only summary-table rows; a test
covers the legend-only case. No held-out data was involved.

## T016 stream equivalence and idle throughput (2026-10-29, after T008)

`python -W ignore scripts/stream_equiv.py --binary fast/build/phyco_stream --set dev --out reports/003-extended-batteries-calibration/streams/equivalence.json`
(WSL venv, Python 3.14.4, 25.4 s): golden vectors plus the first 10⁶ words of all 100 `dev`
seeds for phyco-v2 and lut-v1; **200,030,000 words compared, all match** (SC-003). Binary
`17f7c963…dc97ea`, source `1b46c952…e7c451`, LUT header `fb1e468b…c2dac0`.

Idle throughput (`dev/timing.json`; one process at a time, 10⁹ words to `/dev/null`):

| Generator | Words/s | Time for 1 TiB |
|-----------|---------|----------------|
| phyco-v2 | 8.5 × 10⁷ | 54 min |
| lut-v1 | 7.1 × 10⁷ | 65 min |
| os | 2.1 × 10⁸ | 22 min |

phyco-v2 and lut-v1 are below the plan's 10⁸ words/s goal. The goal was set so the stream would
not limit PractRand; whether it does is measured at T029 from the rehearsal timing.

## T025 dev rehearsal (2026-10-29 22:42 to 2026-10-30 01:30)

The first launch failed before any run started: Git Bash rewrote the `/mnt/c` script path, and
the launcher exited 127. It was relaunched with `MSYS_NO_PATHCONV=1`. All 11 runs completed with
exit 0. Results, S and timing are in `dev/phase-report.md`, `dev/S.json` and `dev/timing.json`.

## T032 tests (2026-10-30)

- Windows: `python -W ignore -m unittest tests.test_batteries tests.test_battery_protocol`:
  40 OK.
- WSL: the same, plus `tests.test_fast_stream`: 48 OK.
