# Data Model: Cryptographic Architecture, Second Design Round (phyco-v4)

> This feature makes no security claim. No PhycoWeb-PRNG model, `phyco-v4` included, may be used
> to generate secrets; use an established cryptographic random-number generator for keys,
> nonces, tokens and salts. Passing statistical tests does not show cryptographic security.

Feature 004's data model (`specs/004-crypto-architecture-v3/data-model.md` at 99e6994, SHA-256
`a4409c024adbc0e0fc2fe5c70bdf25fd977311a7cb077254ab9e1b9f0d8e01dc`) is this feature's baseline (spec FR-001): every record
kind, field, guard and log it defines applies, read with `phyco-v3` as `phyco-v4` and its paths as this feature's. This
document states only the changes. Fields are only added: a record valid under feature 004's model stays valid.

## 1. Paths and the feature field

| Feature 004 | Feature 005 |
|-------------|-------------|
| `reports/004-crypto-architecture-v3/` (`$REP`) | `reports/005-crypto-architecture-v4/` |
| `research/004/` (the three logs, `candidates/<id>/`) | `research/005/` |
| `specs/004-crypto-architecture-v3/` (spec, research, design) | `specs/005-crypto-architecture-v4/` |
| `data/local/004/` | `data/local/005/` |
| development inputs `phycoweb-004/…` | `phycoweb-005/…` |
| candidate IDs `cand-A<k>`, `cand-B<k>` | `v4-A<k>`, `v4-B<k>` |

Every record of this feature holds `feature`: `"005"`. A record without the field is feature 004's. The writers take the
feature from the setting `PHYCOWEB_FEATURE` (research R9) and refuse to write a record whose path and `feature` disagree.

## 2. The `split` bound record (FR-016, FR-017)

A record of kind `bound` with `method`: `"split"`, at `candidates/<id>/<record_id>.json`:

| Field | Type | Rule |
|-------|------|------|
| `bound_kind` | str | `linear` or `differential` |
| `rounds` | int | r ≥ 2 |
| `size`, `width` | int | the claimable size and 32 |
| `bound` | str | the weight as an exact rational, `"p/q"` or a whole number: the sum of the two parts' weights |
| `parts` | list of 2 objects | each `{record_id, sha256, rounds, bound}`, the two established bounds summed, r₁ + r₂ = r, each `pass` and never `inconclusive`, each itself a searched or a `split` bound of the same candidate, kind, size and width |
| `alternatives` | int | the number of splits r₁ + r₂ = r compared; the record holds the largest |
| `searched` | str or `none` | the searched bound at r where one exists, so that the record shows which is larger |
| `tool`, `validation` | `none` | a sum needs no tool: it adds two committed weights |
| `scope` | str | the scope every bound states: single trails under the usual independence assumptions; clustering into differentials and linear hulls and key-dependent effects open for the cryptanalysis feature |
| `budget` | object | `{cap_hours: none, hours_used: 0}`: a sum charges no row |

Classification `no weakness identified within the analysis performed`, with its scope (feature 004's table). A `split` record
is written only where it is the established bound at r, that is where no searched bound exists at r or the sum exceeds it.
`round-rule.json` names, per size and kind, the record that sets R_bound, searched or `split`.

## 3. The trail record's characteristic (FR-019, FR-020)

A `trail` record's `characteristic` is a list with one entry per round, each:

| Field | Type | Rule |
|-------|------|------|
| `round` | int | 1, 2, … in order |
| `state_in` | str | the state's difference or mask at the round's start, as hexadecimal words in the operation list's word order |
| `operations` | list | one entry per nonlinear operation of the round, in the operation list's order: `{op_index, inputs, output, weight}`, the operation's index in the committed operation list, its input differences or masks, its output difference or mask, and the transition's exact weight as a rational |
| `state_out` | str | the state's difference or mask at the round's end |

`weight` at the top of the record stays the product over every operation, as a rational `"p/q"` (feature 004's model), with
its −log₂. The re-check recomputes each operation's weight from its inputs and output (for a modular addition the exact
differential probability or squared correlation; for an S-box its table entry), evaluates every linear step between recorded
points, and recomputes the product; any difference is a disagreement. The classification follows the weight: probability or
squared correlation above 2⁻¹²⁸, `confirmed vulnerability` of the rounds it covers; at or below 2⁻¹²⁸, `none`.

## 4. The calibration and the projection table (FR-004 to FR-009)

- **`research/005/plan-projections.json`**, written by `research/005/plan_projections.py`, committed with the plan:
  `calibration` (`summary`, `factors` per tool and size, `pairs` with each projection's and run's record ID, `other_kinds`),
  `options` (per option: `caps_h`, `candidates_per_family`, `climbs` per reference design, size and kind with each listed
  search's `need_h` and its source, `rows`, `feature_wide_row_h`, `sum_of_rows_h`, `fits_ceiling`, `fr006`), `margin`,
  `ceiling_h`, `r_max`. It is planning data, not a record: it holds no result about any candidate.
- **`reports/005-crypto-architecture-v4/projection-table.json`**, kind `projection-table`, written by
  `scripts/projection_table.py` after the probes (research R5) and before the candidate log's first `proposed` entry: per
  family, size and kind, each listed run with `need_h`, its source (`record_id` of a feature-004 run or of a probe, or
  `cap`), and the value fixed; per candidate row, the value the plan fixed and the value that holds, the smaller of the
  plan's and the probes'; the caps; the sum against the ceiling; `plan_projections_sha256`. Classification `none`.

## 5. The candidate log (FR-011, FR-018, FR-023)

- `candidate_log.py propose` exits 2, appending nothing, while the row "Security-target review" does not read Approved at
  HEAD with the chapters' SHA-256 that it names.
- A `proposed` entry gains `derived_from`: `none`, or `{feature: "004", candidate, oplist_path, oplist_sha256}` for a
  feature-004 design entered again (research R13).
- A `decision` entry `ineligible` may hold the cause `"no R_bound at 16×16"`, with the record that ends the climb there (a
  capped or refused search's record, or the last `split` record below weight 128 at R_max), and the size order's statement
  that no hour was charged at 8×8 or 4×4.
- The candidate limit and the replacement rule read the limit the plan approval fixes (three per family under option A).

## 6. The selection-bias statement (FR-024)

A table in the final report and in `rationale.md`, generated by code from the candidate logs of both features: per design,
`feature`, `id`, `family`, `outcome` (`ineligible`, `proposed and declined`, `selected`, `not selected`, `withdrawn`,
`rejected`), the decision's log entry (feature and `seq`), and `derived_from`; then feature 004's D4 record and selection record
by path and SHA-256, and the bias rule's family-wise rate over this feature's tests.

## 7. Unchanged

Every other record kind and log of feature 004's model applies as written: environment, downloads, projection, lock-cleared,
validation, cross-check, the structural kinds, frequency, avalanche, control, degree, `bound` searched, rotation ranking, D4
choice and ties, round rule, cost, selection and its tie choice, size profile, limits, generator runs and checks,
reproduction, recheck, freeze and review package, with the three hash-chained logs and their repair.
