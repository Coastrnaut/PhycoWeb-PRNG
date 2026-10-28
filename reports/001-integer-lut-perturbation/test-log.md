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
