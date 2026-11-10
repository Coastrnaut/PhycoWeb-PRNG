# Command-Line Contract: Cryptographic Architecture, Second Design Round (phyco-v4)

> This feature makes no security claim. No PhycoWeb-PRNG model, `phyco-v4` included, may be used
> to generate secrets; use an established cryptographic random-number generator for keys,
> nonces, tokens and salts. Passing statistical tests does not show cryptographic security.

Feature 004's contracts (`specs/004-crypto-architecture-v3/contracts/cli.md` at 99e6994, SHA-256
`2d0f3aff4081185b6c6160edb8d67f3ecdb1f8b8d48c87a9df296648eabec9a5`, and `model-v3-api.md`, SHA-256
`5a988a0f5fe325909dabc952fc9bd9083cae40b64ded2cfb7ea211bd4a6dc17f`) are this feature's baseline (spec FR-001): every script,
mode, guard and exit status they define applies, read with `phyco-v3` as `phyco-v4`, `model_v3` as `model_v4` and their paths
as this feature's. This contract states only what is new or changes. Exit statuses keep feature 004's meaning: 0 done, 1 a
finding or a failed check, 2 refused by a guard, 3 a tool failure.

## The feature setting

Every script of feature 004 runs for this feature with `PHYCOWEB_FEATURE=005` in its environment, and for feature 004 without it
(research R9). A script exits 2 when the setting names no known feature, when a record's path and its `feature` field disagree,
or when it would write under another feature's paths. Feature 004's records, logs and documents are never written, and no run of
this feature writes under feature 004's paths (spec FR-003).

## New

### `research/005/plan_projections.py [--check]`

Computes the calibration and the provisional projection table from feature 004's committed records into
`research/005/plan-projections.json` (data-model §4). `--check` recomputes and exits 1 if the committed file differs. It reads
no record of this feature and writes no record.

### `scripts/projection_table.py [--check]`

After the probes and before the candidate log's first `proposed` entry, writes `$REP/projection-table.json` (data-model §4): the
values of the option `plan-projections.json` names as `approved_option`, each lowered to the probes' value where a probe shows
less, never raised; each row and cap with its source.
Exits 2 once any `proposed` entry exists, when `plan-projections.json` fails its `--check`, or when a listed probe record is
missing. `--check` recomputes the table and exits 1 on a difference. A probe that shows a need above its row is printed, and
the table records it; the run is refused when it comes (inherited ANA-078).

## Changed

### `scripts/evidence_v3.py … --probe`

A probe for the projection table (research R5): the run itself, up to 4 h, written as a `projection` record charged to the
feature-wide row, its outputs other than timing discarded unread. It records `finished` with the hours taken, or
`reached the probe limit`, which the table reads as reaching the run's cap. Exits 2 once any `proposed` entry exists.

### `scripts/round_rule.py --candidate ID`

At the production width the climbs run at 16×16, then 8×8, then 4×4 (spec FR-014); at a size r ascends from 1, the linear
search before the differential at each r, each kind independent; the first capped or refused search of a kind ends that kind's
searches at that size (FR-015). After each r it writes the `split` record where a sum is the established bound (data-model §2;
FR-016) and continues by sums until both kinds' weights exceed 128 or r reaches 64 (FR-017). A candidate with no R_bound at
16×16 is decided `ineligible` at once, with the cause `no R_bound at 16×16` (FR-018), and no search runs at 8×8 or 4×4. Every
search runs at one thread, under its size's cap from the projection table, and is refused when its projection does not fit
its row.

### `scripts/candidate_log.py propose ID --derived-from PATH:SHA256 --relation derived|starting-point [--changes TEXT]`

Exits 2 while the row "Security-target review" does not read Approved at HEAD with the chapters' SHA-256 it names (FR-011), and
while `$REP/projection-table.json` does not exist (research R5), for every `proposed` entry. `--derived-from` names a
feature-004 operation list by path and SHA-256 (FR-023), and `--relation` and `--changes` write data-model §5's `relation` and
`changes`, `changes` reading `none` for `derived`; without `--derived-from`, `derived_from` reads `none`.

### `scripts/recheck_004.py` for feature 005

With `PHYCOWEB_FEATURE=005`, it also recomputes every `split` bound from its two parts, and every trail's weight, transitions
and classification from its characteristic and the candidate's committed operation list (FR-020); a disagreement is a tool
defect that blocks the candidate. Its `recheck` record names the feature. `--no-record` prints the result and writes nothing,
for spec FR-003's test of feature 004's re-check and quickstart V2.

### `scripts/check_claims.py`

Covers `phyco-v4` and feature 005's documents and reports beside feature 004's, reading each feature's gate rows from its own
spec (FR-026; research R10).

## Unchanged

Every other script and mode of feature 004's contract applies as written for this feature: the environment and owner records,
the downloads manifest, the heavy-run lock and `clear_lock.py`, the protocol change log, provenance, the D4 choice, the
structural, bias and degree evidence, the generators and their `--check`, the size profile and limits, the self-test, the
freeze and the review package.
