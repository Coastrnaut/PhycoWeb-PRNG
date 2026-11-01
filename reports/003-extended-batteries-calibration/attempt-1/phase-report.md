# Phase Report: Battery Attempt 1 on `heldout-1` (feature 003, T035–T037)

Date: 2026-10-31. Format: constitution, Phase Completion Reporting. Gate: **⛔ T038, owner
result review (Principle VIII)**.

> Passing statistical batteries does not show cryptographic security. This generator must not be
> used to generate secrets; use an established cryptographic random-number generator for keys,
> nonces, tokens and salts.

The attempt used the held-out seed set `heldout-1` under the freeze approved by the owner on
2026-10-30 (`freeze.json`, S = 101,210). Nothing in the protocol was changed after the freeze.

## 1. Outcome

- **Verdict: PASS. The candidate, `phyco-v2`, failed no rule in any of its 70 runs** across
  PractRand to 1 TiB, SmallCrush, Crush and BigCrush in both orientations, on 10 held-out seeds.
- **Both controls behaved as designed.** The positive control (`os`) failed nothing; the
  negative control (`lut-v1`) failed all 70 of its runs. So the batteries could tell a broken
  generator from a good one at this threshold.
- **The re-score is identical** (T036, SC-006): `rescore.json` reproduces the verdict and every
  run outcome from the saved logs, with no difference.
- **What PASS means:** no statistical defect was found at this depth. It is not evidence of
  cryptographic security, and it does not change any finding of security.md §9.2 (S1–S15).
  `phyco-v2` stays at claim level L0, with no claim.
- **It took 37.8 h, not the projected 24.1 h,** almost entirely because of a few slow lut-v1
  BigCrush runs while most cores sat idle (section 5).
- **One parser defect was found** (section 6, issue 1). It cannot have affected this verdict,
  but it must be fixed before any later attempt.

## 2. Commands

```text
# T035 (WSL, background, 2026-10-30 08:54:16 to 2026-10-31 22:40:41)
~/.venvs/phycoweb/bin/python -W ignore scripts/battery_attempt.py --attempt 1 --slots 32
# -> attempt 1: PASS (candidate did not fail); exit 0

# T036 (WSL)
~/.venvs/phycoweb/bin/python -W ignore scripts/battery_rescore.py --attempt 1
# -> attempt 1 re-score: identical (PASS); exit 0
```

Records: `started.json` (git `5b9fcfd`, freeze SHA-256 `b440721a…`), `equivalence.json`,
`progress.txt`, `attempt.json`, `summary.md`, `rescore.json`, and one directory per run under
`positive/`, `negative/` and `candidate/` (`run.json`, `log.txt`, `stderr.txt`,
`stream.sha256`, and `pvalues.jsonl` for TestU01). No run was interrupted or restarted.

## 3. Results

Before the runs, the fast C streams matched the Python models on 10⁶ words for each of the 10
seeds, for both `phyco-v2` and `lut-v1` (20,000,000 words, no mismatch).

| Role | Generator | Runs | Failing runs | Incomplete | p-values | Effective S | Threshold |
|------|-----------|------|--------------|------------|----------|-------------|-----------|
| positive | os | 70 | 0 | 0 | 101,210 | 101,210 | 4.94 × 10⁻⁸ |
| negative | lut-v1 | 70 | 70 | 0 | 10,242 | 101,210 | 4.94 × 10⁻⁸ |
| candidate | phyco-v2 | 70 | 0 | 0 | 101,210 | 101,210 | 4.94 × 10⁻⁸ |

**The effective S rule.** The threshold is 0.005 / S with S = max(frozen S, p-values actually
reported) for each role (`protocol/batteries.py`, `effective_threshold`; research R8). A larger
actual count lowers the threshold, so the rule can only become stricter. In this attempt the
positive control and the candidate each reported exactly the frozen 101,210 (9,483 per PractRand
run, 160 per BigCrush, 144 per Crush and 15 per SmallCrush, per seed), so S stayed at 101,210.
The negative control reported fewer, and max() kept the frozen value.

### 3.1 The candidate and the positive control

Every run completed: PractRand reached 2⁴⁰ bytes in all 20 runs, and every TestU01 run printed
its summary. No rule fired. An independent scan of the logs agrees: no `FAIL`, no
`suspicious` grade, no saturated `R>` line, and no `eps` p-value (the only `eps` text is the
legend line TestU01 prints).

The smallest two-sided values, min(p, 1 − p), over all PractRand p-values:

| Role | p-values | Below 10⁻⁴ | Expected by chance | Below 10⁻⁶ | Smallest |
|------|----------|------------|--------------------|------------|----------|
| positive | 94,830 | 12 | 19.0 | 0 | 2.1 × 10⁻⁶ (seed 7, `[Low4/64]FPF/16:(4,14-0)`, 2³⁷) |
| candidate | 94,830 | 14 | 19.0 | 0 | 1.0 × 10⁻⁶ (seed 2, `[Low4/16]BCFN(2+23,13-9U)`, 2³⁹) |

Both are in line with chance; the smallest candidate value is about 20 times the threshold.
PractRand graded 15 candidate results and 7 positive-control results "unusual", its mildest
flag, and none worse. TestU01's smallest values were not tabulated separately; none reached
rule 1 or rule 3.

### 3.2 The negative control, and how many p-values it reported

`lut-v1` failed every run. Rule 1 fired in all 70; rule 2 in all 10 PractRand runs; rule 3 in
all 60 TestU01 runs. PractRand stopped at its first checkpoint, 2²⁷ bytes, in every run, as
`stop_on_fail` intends, about 2 s each.

The PractRand p-value count varied from seed to seed: 424, 325, 428, 418, 426, 300, 387, 403, 345
and 406 for seeds 0–9 (3,862 in all), against about 444–448 result lines printed per run. The
cause is the parser defect of section 6, issue 1: lines whose statistic saturates, printed as
`R>+99999  p = 0  FAIL`, are not matched, and how many saturate depends on the seed. The TestU01
counts did not vary (160, 144 and 15). The role total is 10,242.

This does not weaken the result: the negative control failed by a wide margin on the lines that
were parsed, and its effective S stayed at the frozen value.

## 4. Suspicious results

None for the candidate or the positive control (section 3.1).

## 5. Timings, the projection and the idle cores

| Role | Window | Span | Slot use | Longest run |
|------|--------|------|----------|-------------|
| positive | 10-30 08:54 → 10-30 16:14 | 7.3 h | 93% | BigCrush rev, 3.2 h |
| negative | 10-30 16:14 → 10-31 12:21 | 20.1 h | 41% | BigCrush fwd seed 5, 20.1 h |
| candidate | 10-31 12:21 → 10-31 22:40 | 10.3 h | 90% | BigCrush rev, 4.25 h |
| all | 10-30 08:54 → 10-31 22:40 | 37.8 h | — | — |

**The projection missed by 13.7 h (+57%).** `dev/S.json` projected 8 h per role and 24.1 h in
all, from the rehearsal times of `phyco-v2`, noting that the negative control would be faster
because its PractRand runs stop early. That held for PractRand (2 s) but not for BigCrush. Four
lut-v1 BigCrush runs took 11.8 to 20.1 h, against a median of 3.9 h. TestU01's own timers put
the time in one test, `snpair_ClosePairs`: up to 9.9 h of CPU in a single instance for seed 5,
against 0.1 h for seed 0. The run was not slowed by contention: TestU01 reports 18.8 h of CPU
time for seed 5, close to its 20.1 h wall time. The likely reason is that `lut-v1`'s
structured output makes the close-pairs search degenerate. That was not investigated further.
The candidate also ran 2.3 h over its share: its median run times were about 50% longer than in
the rehearsal for BigCrush, 37% for Crush and 31% for PractRand, plausibly because all 32 slots
were busy here, against 11 runs in the rehearsal.

**The idle cores.** The scheduler runs the roles one after another, so the candidate could not
start until the last negative run ended. From 22:49 on 10-30, the negative role never again used
16 of the 32 slots: for 12.7 h it used at most 8, with 4 runs left (8 slots) and then down to 1
(2 slots), while about 75% of the machine did nothing. Within the candidate role, PractRand runs
are weighted 6 slots each, so at most 5, and usually 4, ran together. Its tail, after the last
time 16 slots were in use, lasted 1.2 h. A scheduler that starts the next role's runs as slots
free up would have saved most of the 13.5 h negative tail. It was not changed during the attempt,
because `scripts/battery_attempt.py` is frozen (section 6, issue 2).

## 6. Open issues

1. **The PractRand parser skips saturated results.** `_RESULT` in `protocol/batteries.py`
   requires `R=`, so a line printed with `R>` (the statistic exceeded PractRand's display range,
   always with `p = 0` and a FAIL grade) is dropped. In this attempt that dropped 553 of 4,415
   lut-v1 PractRand result lines, and none of the candidate's or positive control's 94,830 each,
   checked by an independent scan. A candidate that failed only with saturated lines would be
   missed by rules 1 and 2. **Fix before any later attempt**: match `R>` and `R<`, count those
   lines as failures, and add a test fixture. The change is stricter-only, and needs a new freeze
   because the file's hash is frozen. *Fixed on 2026-11-01 (T039a); see the addendum.*
2. **Role-sequential scheduling** (open item for feature 007) wasted most of the 13.5 h
   negative tail (section 5). Before a later attempt, start runs from any role as slots free
   up, and project times per role and per generator, including the negative control's BigCrush.
3. **`freeze.json` still reads `"status": "draft"`** (open item for feature 007), although its
   `approved_by` and `approved_on` fields are filled and the attempt accepted it. The status
   field is cosmetic but misleading. Set it on approval in future freezes.
4. **The `lut-v1` close-pairs times** (open item for feature 007; section 5) are unexplained.
   They do not affect any verdict.
5. **Carried over from the dev report:** `stream_bytes` counts bytes written, not consumed, and
   feature-003 files were uncommitted when the freeze recorded `git_head`.

## 7. Security concerns

None new. This is a statistical result about `phyco-v2` on 10 held-out seeds. The structural
findings S1–S15 stand, among them the 64-bit seed bound (about 2⁷² steps to try every seed) and
the merging step (S13). No cryptographic claim follows (constitution, Security Policy;
security.md §15).

## 8. Recommendation

**Owner result review, ⛔ T038.** If the owner accepts the PASS, T039 (attempt 2) is not
applicable, and the polish tasks T040–T044 follow. Fix issue 1 before any further battery
attempt, in feature 003 if the owner wants it there, otherwise in feature 007's protocol.

## Addendum (2026-11-01, after the owner's review): the parser fix

This addendum follows the owner's approval of the report above and does not change it. **The
frozen verdict, PASS, stands.** The freeze pins the hash of the parser that scored the attempt
(`batteries_sha256` `46c4dd15…`), so the result below is a supplementary check, kept beside
`attempt.json` and `rescore.json` and never in place of them.

**The fix (T039a).** `_RESULT` in `protocol/batteries.py` now matches `R=`, `R>` and `R<`, marks
a line printed with `R>` or `R<` as saturated, and counts every saturated line as a rule-2
failure whatever its printed grade. That is stricter-only: no line that failed before passes
now. A synthetic fixture whose only failures are saturated lines
(`tests/data/batteries/pr-saturated/`) and three new tests in `tests/test_batteries.py` cover it;
the three failed before the fix and pass after it, and all 15 battery tests pass. The fixed
file's SHA-256 is `fc141a2b…`; any later attempt needs a new freeze that pins it.

**The supplementary re-score** (`rescore-parser-fix.json`), the same saved logs read by the
fixed parser:

| Role | p-values, frozen parser | p-values, fixed parser | Saturated lines | Failing runs, frozen / fixed | Outcome |
|------|-------------------------|------------------------|-----------------|------------------------------|---------|
| positive (`os`) | 101,210 | 101,210 | 0 | 0 / 0 | unchanged |
| negative (`lut-v1`) | 10,242 | 10,795 | 553 | 70 / 70 | unchanged |
| candidate (`phyco-v2`) | 101,210 | 101,210 | 0 | 0 / 0 | unchanged |

Verdict with the fixed parser: **PASS** (candidate did not fail), identical to the frozen
verdict. The 553 recovered lines all belong to the negative control, which already failed every
run; its PractRand count per run is now 438 to 448, and its rule-2 lines number 3,978. The
threshold stays at 4.94 × 10⁻⁸, because the negative role's count stays below the frozen S. In
short, the bug hid failures only from a generator that was failing loudly anyway, which is the
least embarrassing place a bug like this can hide, and it is now gone.

**Open items for feature 007's protocol.** Issues 2 to 4 of section 6 are carried to the
protocol of feature 007 (statistical re-validation), recorded in the 007 prompt of the strategy
note (§9.3):

- schedule runs from any role as slots free up, not role by role, and project times per role
  and per generator, including the negative control's BigCrush;
- set the freeze's `status` field to `approved` when the owner approves it;
- explain or bound the `lut-v1` `snpair_ClosePairs` times before projecting a negative control's
  run time.

Issue 5 stays as recorded in the dev report.

## Review & Approval

| Role | Name | Date | Decision |
|------|------|------|----------|
| Owner (T038) | Coastrnaut (repository owner) | 2026-11-01 | Approved: PASS accepted, with the report as written; attempt 2 not applicable |
