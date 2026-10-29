# Contract: command-line tools

All tools run from the repository root. Exit codes are 0 for success, 1 for a completed run
whose verdict is not a pass, and 2 for a usage error or a refused run. A non-pass verdict is
never turned into exit 0.

## `scripts/seedsets.py`

```text
python scripts/seedsets.py --set {dev,heldout-1,heldout-2,heldout-3} [--print] [--check]
```
`--check` recomputes all four sets and compares them with the spec fingerprints. `--print`
outputs the canonical text. It is allowed for held-out sets, because the seeds are already
public in the spec and printing them is not "use".

## `scripts/sts_eval.py` (dev and re-scoring)

```text
python scripts/sts_eval.py --source {phyco-v2,lut-v1,os-csprng,file}
       (--set dev | --seed A B C D ... | --bytes PATH) [--sequences 100] [--workers 32]
       --out PATH.json
```
- It refuses `--set heldout-*` (exit 2). Held-out sets only run through `acceptance.py`.
- `--source os-csprng --save-bytes PATH` stores the drawn control bytes so they can be
  re-scored later.
- `--source file --bytes PATH` re-scores stored bytes, for example to reproduce a positive
  control or re-score the feature-001 inputs.
- It writes an evaluation record ([data-model §4](../data-model.md)). It never writes
  `research/002/runs.jsonl`; only `research/002/explore.py` does (data-model §7).

## `scripts/freeze.py`

```text
python scripts/freeze.py --attempt N --dev-evidence PATH.json
```
Writes a draft `attempt-N/freeze.json` with empty approval fields. It refuses if N is not the
next attempt, if the working tree has uncommitted changes to the model, design or harness, or if
`attempt-N/` already exists.

## `scripts/acceptance.py`

```text
python scripts/acceptance.py --attempt N [--workers 32]
```
Checks are listed in research R8. It then runs the positive control, the negative control and
the candidate, in that order. It writes three eval records, `attempt.json` and `summary.md`, and
exits 0 only for PASS.

## Existing tools (extended, backward compatible)

- `scripts/gen_vectors.py`: `MODELS` gains `"phyco-v2"`. Existing outputs for `float-v0` and
  `lut-v1` stay byte-identical, and a test checks this.
- `scripts/nist_eval.py` (feature 001): kept unchanged as the feature-001 record. Its use for
  feature 002 is replaced by `sts_eval.py`.
