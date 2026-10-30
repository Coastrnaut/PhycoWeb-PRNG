# CLI Contracts

Exit codes for every repository script: **0** success; **1** completed with a failing or
non-PASS verdict (by design); **2** refused by a guard (wrong seed set, missing approval, hash
mismatch, existing record) — nothing is written; **3** tool or I/O error.

## `fast/phyco_stream` (C, WSL)

```text
phyco_stream phyco-v2|lut-v1 S0 S1 S2 S3 [--words N] [--reverse] [--hex]
phyco_stream os [--words N] [--reverse] [--hex]
```

- Seeds: four integers 0…65535; anything else exits 2.
- Default output: little-endian u32 words to stdout until `--words` or a closed pipe (SIGPIPE
  exits 0). `--hex`: one `%08X` word per line. `--reverse`: bit-reversed words.
- `phyco-v2` applies the 256-step warm-up before the first word; `lut-v1` has none.
- Writes nothing else to stdout; errors go to stderr.

## `fast/testu01_driver` (C, WSL, links TestU01 1.2.3)

```text
testu01_driver smallcrush|crush|bigcrush --name NAME --pvalues OUT.jsonl < words
```

- Reads little-endian u32 words from stdin. Exits 3 if stdin ends before the battery finishes.
- Full TestU01 text output on stdout (`swrite_Basic = TRUE`).
- `OUT.jsonl`: one line `{"battery", "n_tests", "tests": [{"index", "name", "p"}]}` from
  `bbattery_NTests`, `bbattery_TestNames`, `bbattery_pVal`.

## `scripts/gen_c_lut.py`

Writes `fast/lut_table.h` from `phycoweb/lut.py` (GENERATED header). `--check` exits 1 if the
file on disk differs.

## `scripts/stream_equiv.py`

```text
stream_equiv.py --binary PATH [--set dev] [--words 1000000] --out streams/equivalence.json
```

Compares golden vectors and the `dev` set (both generators) with the Python models. Accepts
only the feature-002 `dev` set and feature-001 seeds; any held-out set exits 2. Exit 1 on any
mismatch.

## `scripts/calibrate.py` (Windows)

```text
calibrate.py --runs 0-999 [--workers 32] --out-dir reports/003-…/calibration/runs
```

- Checks the `sp80022` source hash (exit 2 on mismatch). Skips nothing: an existing run file
  for a requested index exits 2 unless `--resume`, which starts at the first missing index.
- Writes one record per run (data-model §1); never writes bytes to disk.

## `scripts/calibration_report.py`

```text
calibration_report.py --runs-dir … --out reports/003-…/calibration/summary.json
```

Exits 2 unless runs 0…999 are all present and each file passes its own consistency check.
Writes `summary.json` and `summary.md` (data-model §2).

## `scripts/battery_run.py` (WSL)

```text
battery_run.py --role positive|negative|candidate --battery practrand|smallcrush|crush|bigcrush
               --orientation fwd|rev --seed S0 S1 S2 S3 | --os --out DIR
               [--set dev | --attempt N]
```

- Runs one pipeline (research R5); writes `log.txt`, `stream.sha256`, parsed results and
  `run.json` (data-model §7).
- With `--set dev` only dev/feature-001 seeds are accepted. With `--attempt N` it is called by
  `battery_attempt.py` only (it checks the freeze and refuses otherwise, exit 2).
- `--stop-on-fail` is accepted only with `--role negative`.

## `scripts/battery_freeze.py`

```text
battery_freeze.py create --attempt N --S S
battery_freeze.py validate --attempt N
```

`create` writes a draft freeze (data-model §6) with empty approval fields. `validate` re-hashes
every frozen file and exits 2 on any difference or missing approval.

## `scripts/battery_attempt.py` (WSL)

```text
battery_attempt.py --attempt N [--slots 32]
```

Refuses (exit 2) if: the freeze is missing, unapproved or does not validate; the attempt is not
the next allowed one (FR-013); the attempt directory already has `started.json`. Then: writes
`started.json`; checks held-out stream equivalence (INVALID on mismatch); runs positive, then
negative, then candidate (candidate `not_run` if the positive control fails); writes
`attempt.json` and `summary.md`. Exit 0 on PASS, 1 otherwise.

## `scripts/battery_rescore.py`

```text
battery_rescore.py --attempt N
```

Re-parses every saved log with `protocol/batteries.py`; writes `rescore.json`; exit 1 if any
outcome differs.
