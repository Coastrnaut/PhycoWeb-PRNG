# Data Model: Extended Batteries and Positive-Control Calibration

All records are JSON (UTF-8). Every record carries `disclaimer` (the `protocol.disclaimer`
text, FR-016), `git_head`, `git_dirty`, `versions` and `command`. Paths are under
`reports/003-extended-batteries-calibration/`.

## 1. Calibration run (`calibration/runs/run-<NNNN>.json.gz`)

| Field | Type | Rule |
|-------|------|------|
| `run` | int | 0…999; file name matches; never overwritten |
| `input_sha256` | hex | SHA-256 of the run's 100 × 262,144 bytes, in sequence order (FR-006) |
| `n_sequences`, `n_bits` | int | 100, 2,097,152 |
| `harness_version`, `harness_sha256` | str | `1.0.0`, `1563526e…0602c41700` (checked) |
| `sequences` | list[100] of {test: {eligible, p_values}} | every per-sequence p-value (FR-002) |
| `subtests` | {test: [{proportion, passed, m, uniformity_p, pass}]} | from `sp80022.assess` |
| `families` | {test: {pass, failed_subtests, k_max, m}} | from `sp80022.assess` |
| `families_failed` | list[str] | |
| `verdict` | `pass` / `fail` | fail if any family fails |
| `started`, `elapsed_s` | | |

## 2. Calibration summary (`calibration/summary.json`, `calibration/summary.md`)

- `runs`: 1000, plus the SHA-256 of every run file (list, in order).
- `overall`: failures, rate, 95% Clopper–Pearson interval; assumed 0.19; consistent (bool).
- `per_family[15]`: failures, rate, interval, expected rate (research R3), consistent.
- `per_subtest[188]`: failures, rate, interval (proportion and uniformity failures separately
  and combined).
- `failing_family_count`: histogram 0…15.
- `co_failure[15×15]`: observed both-fail count, expected under independence, Fisher p.
- `implied_pass_probability`: value and interval (research R3).
- `recommendations`: free text, each marked "recommendation only; needs a separate,
  stricter-only spec amendment" (FR-005).

## 3. Fast-stream equivalence (`streams/equivalence.json`)

- `stream_source_sha256`, `binary_sha256`, `compiler`, `flags`, `lut_table_sha256`.
- `golden`: per vector file: words compared, mismatches (must be 0).
- `dev`: per generator × 100 seeds: words compared (10⁶), mismatches, first mismatch index.
- `byte_order`: `little-endian u32`; `reverse`: `bit 0 <-> bit 31`.

## 4. Battery seed set

`name` (`heldout-1`, `heldout-2`), `prefix` `phycoweb-003/`, `size` 10, `fingerprint`
(spec table), `status` (`unused` / `used by attempt n`). Status is derived from the attempt
directories, never edited by hand.

## 5. Tool record (`tools/<tool>.json`)

`name`, `version`, `source_url`, `archive_name`, `archive_sha256`, `archive_bytes`,
`licence` (as read), `downloaded_on`, `owner_permission` (date and wording), `build_commands`,
`build_flags`, `binary_sha256` (PractRand `RNG_test`; TestU01 `libtestu01`, `libprobdist`,
`libmylib`; the driver binary).

## 6. Battery freeze (`attempt-<n>/freeze.json`)

| Field | Rule |
|-------|------|
| `attempt` | 1 or 2; 2 only if attempt 1's verdict is INCONCLUSIVE or INVALID (FR-013) |
| `seed_set`, `seed_set_fingerprint` | next unused set |
| `phyco_v2_model_sha256`, `lut_v1_model_sha256`, `lut_sha256` | Python reference sources |
| `stream_source_sha256`, `stream_binary_sha256`, `driver_source_sha256`, `driver_binary_sha256` | |
| `tools` | copies of the tool records (§5) |
| `commands` | exact command template per battery and orientation |
| `S` | integer, from the dev rehearsal (research R8) |
| `threshold` | 0.005 / S |
| `approved_by`, `approved_on` | owner; empty until approved; the attempt refuses without them |

## 7. Battery run (`attempt-<n>/<role>/<battery>-<orientation>-seed<i>/`)

`role` ∈ {positive, negative, candidate}; `battery` ∈ {practrand, smallcrush, crush, bigcrush};
`orientation` ∈ {fwd, rev} (PractRand: fwd only, it tests all bits).

Files: `log.txt` (tool output), `pvalues.jsonl` (TestU01) or parsed results (PractRand),
`stream.sha256`, `run.json`:

| Field | Rule |
|-------|------|
| `seed` | four ints, or `null` for `os` |
| `complete` | tool exited 0 and reached its full length/battery |
| `stopped_early` | negative control only (spec Edge Cases) |
| `length_bytes` | PractRand: last checkpoint reached |
| `n_pvalues` | count contributing to S |
| `results` | list of {test, checkpoint, p, grade} |
| `rule1`, `rule2`, `rule3` | lists of results that meet each rule |
| `fails` | any rule met |
| `exit_status`, `elapsed_s` | |

## 8. Battery attempt (`attempt-<n>/attempt.json`, `summary.md`)

- `equivalence`: per held-out seed and model, 10⁶ words checked, mismatches (non-zero → INVALID).
- `roles`: for each of positive, negative, candidate: `status` (`run` / `not_run`), runs
  complete / total, `fails`, failing runs.
- `verdict`: PASS / FAIL / INCONCLUSIVE / INVALID (spec rules), with the reason.
- `rescore` (§9) after the re-score.

## 9. Re-score (`attempt-<n>/rescore.json`)

Re-applies `protocol/batteries.py` to every saved log; records per run whether `fails` and the
rule lists are identical, and whether the verdict is identical (SC-006).

## State transitions

```text
seed set:  unused --(freeze approved + attempt started)--> used
attempt:   draft freeze --approve--> frozen --start--> equivalence --(mismatch)--> INVALID
           equivalence ok --> positive --(fails)--> INCONCLUSIVE (candidate not_run)
                          --> negative --> candidate --> PASS | FAIL | INCONCLUSIVE
```
