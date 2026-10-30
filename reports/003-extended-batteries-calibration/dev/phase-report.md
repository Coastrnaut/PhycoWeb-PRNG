# Phase Report: US2/US3 Tools, Fast Streams and Dev Rehearsal (feature 003)

Date: 2026-10-30. Format: constitution, Phase Completion Reporting. Gate: **T034, owner battery
freeze approval (Principle VIII)**. That gate also requires T011, the calibration review.

> Passing statistical batteries does not show cryptographic security. This generator must not be
> used to generate secrets; use an established cryptographic random-number generator for keys,
> nonces, tokens and salts.

Every result in this report comes from the feature-002 `dev` seed `(56053, 7029, 30841, 11050)`
or from `os.urandom`. No held-out seed has been used.

## 1. Outcome

- **The tools are installed and recorded, and the fast streams match the reference models.**
  On the dev data, the fast streams agree with the Python models on 200,030,000 words, with no
  mismatch (SC-003).
- **The rehearsal ran in full**: 11 of 11 runs completed, exit 0, from 22:42 on 2026-10-29 to
  01:30 on 2026-10-30.
  - phyco-v2 failed no rule in any of its 7 runs. These were PractRand to 1 TiB, and SmallCrush,
    Crush and BigCrush in both orientations.
  - lut-v1, the negative control, failed under rule 2 (PractRand) and rule 3 (SmallCrush).
  - os, the positive control, passed.
- **S = 101,210**, so the rule-1 threshold is **4.94 × 10⁻⁸**. The projected attempt time is
  about **24 h**, below the 5-day limit.
- The draft freeze `attempt-1/freeze.json` (`heldout-1`) is written. Its approval fields are
  empty.

## 2. Files created or modified

| Area | Files |
|------|-------|
| Fast streams | `fast/phyco_stream.c`, `fast/lut_table.h`, `scripts/gen_c_lut.py`, `fast/Makefile`, `scripts/stream_equiv.py`, `tests/test_fast_stream.py` |
| Tools | `fast/build_tools.sh`, `fast/testu01_driver.c`, `tools/practrand.json`, `tools/testu01.json` |
| Protocol | `protocol/battery_seedsets.py`, `protocol/battery_freeze.py`, `protocol/batteries.py`, `scripts/battery_run.py`, `scripts/battery_freeze.py`, `scripts/battery_attempt.py`, `scripts/battery_rescore.py` |
| Tests | `tests/test_batteries.py`, `tests/test_battery_protocol.py`, `tests/data/batteries/*` |
| Results | `streams/equivalence.json`, `dev/timing.json`, `dev/S.json`, `dev/practrand-listing.md`, `dev/rehearsal/*`, `dev/test-log.md`, `attempt-1/freeze.json` (draft) |

All paths are under `reports/003-extended-batteries-calibration/` unless they start with
`fast/`, `scripts/`, `protocol/` or `tests/`.

## 3. Tools (FR-009)

| Tool | Version | Archive SHA-256 | Binary SHA-256 | Licence |
|------|---------|-----------------|----------------|---------|
| PractRand | 0.96 | `e4caf7fd…a672e1` | RNG_test `7ae4a26b…de874f` | public domain / free use |
| TestU01 | 1.2.3 | `bc1d1dd2…ed1cac` | libtestu01 `b2b28cb6…0bd48`, libprobdist `c83c1901…bc96b2`, libmylib `890c3b35…0120ce` | non-commercial research only; not redistributed |

Both downloads were approved in session on 2026-10-29. Build commands and upstream warnings are
recorded in `tools/*.json` and repeated in the freeze.

## 4. Commands and test results

| Task | Command | Result |
|------|---------|--------|
| T016 | `python -W ignore scripts/stream_equiv.py --binary fast/build/phyco_stream --set dev --out …/streams/equivalence.json` (WSL) | 200,030,000 words, all match, 25 s |
| T016 | `phyco_stream <gen> --words 10^9 > /dev/null`, one at a time | phyco-v2 8.5 × 10⁷, lut-v1 7.1 × 10⁷, os 2.1 × 10⁸ words/s |
| T025 | 11 × `battery_run.py --set dev …` in parallel (script in session scratchpad; commands recorded in each `run.json`) | 11/11 complete, exit 0 |
| T029 | count from `run.json` / runner output; slot-scheduler simulation | S = 101,210; ~8 h per role |
| T033 | `battery_freeze.py create --attempt 1 --S 101210` (WSL) | draft written; `validate` exit 2: approval fields empty, which is correct |
| tests | `python -W ignore -m unittest tests.test_batteries tests.test_battery_protocol` (Windows) | 40 OK |
| tests | `python -W ignore -m unittest tests.test_fast_stream tests.test_batteries tests.test_battery_protocol` (WSL) | 48 OK |

## 5. Rehearsal results in full (FR-014)

The threshold is 0.005 / 101,210 = 4.94 × 10⁻⁸. "min q" is the smallest min(p, 1 − p) in the
run.

| Run | Generator | Length | p-values | min q | Rule 1 | Rule 2 | Rule 3 | Fails | Time |
|-----|-----------|--------|----------|-------|--------|--------|--------|-------|------|
| practrand fwd | phyco-v2 | 1 TiB | 9,483 | 1.0e-4 | 0 | 0 | 0 | no | 1 h 30 min |
| smallcrush fwd | phyco-v2 | | 15 | 0.038 | 0 | 0 | 0 | no | 8 s |
| smallcrush rev | phyco-v2 | | 15 | 0.082 | 0 | 0 | 0 | no | 8 s |
| crush fwd | phyco-v2 | | 144 | 0.0010 | 0 | 0 | 0 | no | 21 min |
| crush rev | phyco-v2 | | 144 | 0.0098 | 0 | 0 | 0 | no | 21 min |
| bigcrush fwd | phyco-v2 | | 160 | 0.0061 | 0 | 0 | 0 | no | 2 h 43 min |
| bigcrush rev | phyco-v2 | | 160 | 0.0045 | 0 | 0 | 0 | no | 2 h 48 min |
| practrand fwd (`-tlfail`) | lut-v1 | stopped at 2²⁷ B | 421 | 0 | | 373 | 0 | **yes** | 2 s |
| smallcrush fwd | lut-v1 | | 15 | 0 | | 0 | 14 | **yes** | 8 s |
| practrand fwd | os | 2³⁵ B | 5,366 | 5e-5 | 0 | 0 | 0 | no | 2 min 19 s |
| smallcrush fwd | os | | 15 | 0.029 | 0 | 0 | 0 | no | 6 s |

Raw logs are in `dev/rehearsal/<run>/log.txt` and stream hashes in `stream.sha256`.

**This is a dev rehearsal, not evidence.** It is one seed and the controls ran at reduced
length. It shows that the pipeline, the parsers and the rules work end to end. The verdict
depends only on the held-out attempt.

## 6. S and timing (FR-011; R8, R9)

- Per seed, phyco-v2 gives 9,483 + 2 × 15 + 2 × 144 + 2 × 160 = **10,121** p-values. For 10
  seeds, **S = 101,210**.
- With `-a`, PractRand prints a fixed set of results per checkpoint. The positive control's 1 TiB
  count is therefore taken to equal the candidate's.
- At the attempt, the effective S is max(frozen S, p-values actually reported) for each role.
  Any larger actual count raises S, which can only make the protocol stricter.
- **Projection**: the slot-scheduler simulation (32 slots; PractRand cost 6, TestU01 cost 2),
  using the rehearsal times, gives **about 8 h per role and at most about 24 h** for all three
  roles. This is an upper estimate: the negative control stops PractRand early, and the os stream
  is faster. It is well below the 5-day limit, so no owner decision on scale is needed.
- BigCrush dominates the run time: 20 runs per role, about 2.8 h each. At this point the stream
  is not the bottleneck.

## 7. PractRand listing (T026)

Every run uses `-a`, so every p-value is printed and S is an exact count. `-tlmaxonly` and
`-tlmin 27` replace the defaults; these choices are deterministic or stricter. Printed tail
p-values are rounded down, which is also stricter. Details are in `dev/practrand-listing.md`.

## 8. Open issues

1. **`stream_bytes` counts bytes written, not bytes consumed.** For TestU01 runs, the relay
   hashes what the stream wrote before the consumer closed the pipe. Because of pipe
   buffering, fwd and rev BigCrush therefore differ by 12.6 MB. The hash is valid for what was
   produced. It is not an exact consumption count, and the re-score does not use it.
2. **Interleaved progress line.** `dev/rehearsal/progress.txt` has one stray line, `t`, from
   concurrent appends by the dev launcher script. It does not affect any run record.
   `battery_attempt.py` logs through a single writer.
3. **Uncommitted working tree.** The freeze records `git_head` 5b9fcfd, but feature-003 files are
   not committed yet. The freeze also hashes every source and binary directly, so it pins the
   exact code either way. Committing before approval would make `git_head` meaningful.
4. **Throughput.** phyco-v2 produces 8.5 × 10⁷ words/s, below the 10⁸ goal. This does not limit
   the attempt; see section 6.

## 9. Security concerns

None new. The battery results are statistical; they say nothing about cryptographic security.
Held-out seeds are refused by `battery_run.py --set dev` and `stream_equiv.py`, as tested.

## 10. Recommendation

**Proceed to T034.** That requires approval of T011 first. After both approvals, attempt 1
runs on `heldout-1`, for about 24 h.
