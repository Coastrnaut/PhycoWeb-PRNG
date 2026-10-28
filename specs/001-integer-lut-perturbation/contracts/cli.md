# Contract: Command-Line Tools

All tools run from the repository root, write only to the paths given, and exit non-zero on any
failure. None of them commits or publishes anything (Principle IX).

## `python scripts/gen_lut.py [--check]`

- Without flags: writes `phycoweb/lut.py` and `data/lut/perturbation_lut.hex`.
- `--check`: writes nothing; exits 1 if either file differs from the formula's output.

## `python scripts/archive_baseline.py`

- Extracts the `readmee.md` model listing and the four deleted files from git history (spec
  FR-013) into `baseline/float-v0/`, then writes `baseline/float-v0/MANIFEST.json`.
- Refuses to overwrite an existing archived file whose hash differs (exit 2): archived files are
  immutable.

## `python scripts/gen_vectors.py --model {lut-v1|float-v0} --seed S0 S1 S2 S3 --count N --out PATH`

- Writes a golden vector file ([file-formats](./file-formats.md)).
- `--verify PATH` instead of `--out`: regenerates the sequence and compares; on mismatch exits 1
  and reports the index of the first differing word.

## `python scripts/nist_eval.py --model {lut-v1|float-v0} --seed S0 S1 S2 S3 --bits N --out PATH`

- Runs the full `nistrng.SP800_22R1A_BATTERY` on N bits (MSB-first per word) and writes a JSON
  results record ([data-model](../data-model.md#statistical-results-record)).
- Exit code 0 means the evaluation **ran**, not that the tests passed. Pass/fail is in the
  report. Failures are never turned into a non-zero exit, so a failing test cannot be hidden by
  treating it as a crash.
