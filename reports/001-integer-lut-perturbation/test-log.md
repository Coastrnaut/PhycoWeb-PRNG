# Test Log: 001-integer-lut-perturbation

Environment: Windows-10-10.0.26200-SP0 | Python 3.10.11 |
numpy 2.2.6 | nistrng 1.2.3 |
git HEAD cec8377 (working tree has uncommitted feature changes)

## Phase 2 (2026-10-28)

| Command | Result |
|---------|--------|
| `python scripts/archive_baseline.py` | exit 0; 5 files archived, MANIFEST.json written |
| `python scripts/archive_baseline.py` (re-run) | exit 0; all unchanged |
| `python scripts/gen_vectors.py --model float-v0 --seed 1024 2048 4096 8192 --count 10000 --out vectors/float-v0_seed-1024-2048-4096-8192_10000.hex` | exit 0; first word D6EDF3D6 |
| same with `--verify` | exit 0; OK 10000 words |
| `python -m unittest tests.test_baseline -v` | 3 tests, OK |

## Phase 3 / US1 (2026-10-28)

| Command | Result |
|---------|--------|
| `python -m unittest tests.test_lut tests.test_purity tests.test_period tests.test_equivalence` (before T012–T014) | 9 errors (modules missing), as expected for test-first |
| `python scripts/gen_lut.py` | exit 0; wrote phycoweb/lut.py, data/lut/perturbation_lut.hex |
| `python scripts/gen_lut.py --check` | exit 0; line 65 = 0400, line 193 = FC00 |
| `python -m unittest tests.test_lut tests.test_purity tests.test_period tests.test_equivalence -v` | Ran 19 tests in 0.278s — OK |

Mutation check of the equivalence test (one-off script in the session scratchpad, not committed):
run the equivalence tests against single-edit copies of `phycoweb/model.py`.

- Trajectory comparison alone (2 seeds × 10,000 words) missed two mutants: removing the
  `D == 0 → 1` floor and changing the threshold 4096 → 4097. The trajectories never reach those
  paths. Added a single-step comparison from 5,000 random states plus 5 hand-built edge states
  (zero floor; threshold boundaries 4096/4097 for D[0] and D[2]).
- After that, all 6 mutants are detected: zero floor removed, D[0] threshold 4097, D[2] threshold
  4095, growth `>> 3`, flux without wrap32, XOR constant changed.
- `wrap32(abs(Q))` can never take effect: after `>> 8`, Q is in [−2²³, 2²³), so the wrap is
  provably a no-op. It is kept because FR-008a specifies it.

## Phase 4 / US2 (2026-10-28)

| Command | Result |
|---------|--------|
| `python -m unittest tests.test_vectors` (before the vector file existed) | 1 error, as expected for test-first |
| `python scripts/gen_vectors.py --model lut-v1 --seed 1024 2048 4096 8192 --count 10000 --out vectors/lut-v1_seed-1024-2048-4096-8192_10000.hex` | exit 0; first word D7EDF3D7 |
| same with `--verify` | exit 0; OK 10000 words |
| `--verify` with seed `1024 2048 4096 8193` | exit 1; header mismatch reported |
| `--verify` against a scratch copy with word 4999 altered | exit 1; `MISMATCH at word 4999` |
| `python -m unittest tests.test_vectors -v` | Ran 5 tests — OK |

**SC-002 status: OPEN.** Verified on one environment only (this machine). T019 (second
environment, owner action) is pending.

## Phase 5 / US3 (2026-10-28)

| Command | Result |
|---------|--------|
| `python scripts/nist_eval.py --model lut-v1 ... --bits 33 ...` | exit 2 (not a multiple of 32), as specified |
| 4 × `python scripts/nist_eval.py --model {float-v0,lut-v1} --seed {1024 2048 4096 8192, 4660 43981 21845 43690} --bits 1000000 --out reports/001-integer-lut-perturbation/nist_<model>_seed-<seed>_1000000.json` (first harness, `run_all_battery`) | exit 0; 44–70 s each. **Results invalid** (N2) and discarded |
| Independent forward Cumulative Sums (scipy) vs nistrng | float-v0: independent p = 0.1705 against 0.000000 inside the battery and 0.201 run alone, which led to the discovery of N2 (Binary Matrix Rank modifies its input in place) |
| Per-test isolation check, forward vs reverse order | 14/15 order-independent; Non-Overlapping Template order-dependent, which led to N3 (random template; `score` = mean of p-values) |
| `python -W ignore -m unittest tests.test_nist_eval -v` (after N2/N3 fixes) | Ran 4 tests — OK |
| 4 × `nist_eval.py` as above (fixed harness) | exit 0; 90 s, 110 s, 60 s, 61 s (all under the 10-minute limit). Pass/fail/not-eligible: float-v0 12/2/1 and 12/2/1; lut-v1 8/6/1 (seed 1024…) and 12/2/1 (seed 4660…) |

Summary: `reports/001-integer-lut-perturbation/summary.md`.
