# Data Model: Cryptographic Architecture and phyco-v3 Design

> This feature makes no security claim. No PhycoWeb-PRNG model, `phyco-v3` included, may be used
> to generate secrets; use an established cryptographic random-number generator for keys,
> nonces, tokens and salts. Passing statistical tests does not show cryptographic security.

All records are JSON (UTF-8, LF line endings, sorted keys), written by one module,
`protocol/evidence.py`. Paths are under `reports/004-crypto-architecture-v3/` unless stated. A
record is never overwritten: a repeat run writes a new record with a new identifier, and the old
one stays.

## 1. Common fields (every evidence record; FR-061, security.md §17.2)

| Field | Type | Rule |
|-------|------|------|
| `record_id` | str | `<kind>-<UTC yyyymmddThhmmssZ>-<8 hex>`; unique; part of the file name |
| `kind` | str | one of the kinds of sections 4–11 |
| `created_utc` | str | ISO 8601, seconds |
| `model_id`, `variant_id` | str | `phyco-v2` for US1 and for tool validation on it; otherwise a candidate or `phyco-v3` variant ID (research R14) |
| `design_version`, `design_sha256` | str | the design document's version and hash; `none` before it exists |
| `spec_sha256` | hex | SHA-256 of `spec.md` at run time |
| `git_head`, `git_dirty` | str, bool | as in the feature-002 and feature-003 records |
| `versions` | object | Python, numpy, scipy, gcc, and every tool used, with its version and licence |
| `platform` | object | operating system, CPU, logical CPUs, RAM |
| `command`, `config` | str, object | the exact command line and every parameter |
| `inputs` | object | namespace (`dev` or `control`; for US1 the feature-002 `dev` set), kind, index range, fingerprint (R3) |
| `outputs` | list | `{path, sha256, bytes, committed}`; `committed` false for local-only files (R16) |
| `exit_status`, `assertions` | int, list | every assertion with its outcome |
| `status` | str | `pass`, `fail`, `inconclusive`, `not evaluated` or `blocked` (security.md §16.3), computed by code (FR-065) |
| `classification` | str | one of the four classes of security.md §9.1 (FR-060) |
| `analyst`, `reviewer`, `review_status` | str | the AI agent and model, or a person; `reviewer` stays `pending` until a review is recorded |
| `limitations` | list[str] | known limitations, and the scope of any negative result |
| `heavy_run` | bool | true if the run held the heavy-run lock (FR-045) |
| `disclaimer` | str | `protocol.disclaimer.DESIGN_DISCLAIMER`, verbatim (FR-068) |

Statistical records (section 5, `frequency`, `avalanche` and `control`) also hold the items of
security.md §11.6: `sample_size`, `test_parameters`, `raw_counts` (path and SHA-256),
`p_values` (path and SHA-256), `failure_locations` (every fired bit with its round count and
direction) and `exclusions_and_reruns` (each with its justification; empty unless a tool defect
is recorded).

## 2. Development inputs (`protocol/devinputs_v3.py`; FR-040, R3)

| Constant or function | Rule |
|----------------------|------|
| `PREFIX` | `phycoweb-004/` |
| `NAMESPACES` | `dev`, `control`; nothing else is accepted |
| `key(i)`, `nonce(i)`, `pers(i, m)`, `reseed(i)` | 32, 16, min(m, 32) and 32 bytes from SHA-256 of `phycoweb-004/<ns>/<kind>/<i>` |
| `state(n, w, i)` | b = 2w·n² bits from the digests of `phycoweb-004/<ns>/state/n<n>w<w>/<i>/<j>`, j = 0, 1, …, read into lanes as R3 states |
| `FINGERPRINTS` | per namespace and kind, and per (n, w) for `state`: SHA-256 of the hex values for i = 0…99, one per line, LF |
| `load(ns, kind, allow, ...)` | checks the fingerprint, refuses a namespace not in `allow` (`PermissionError`; scripts exit 2) |

The empty personalization string is a named input of its own. Indices are decimal without
leading zeros. The module imports only `hashlib`.

## 3. Candidate log (`research/004/candidates.jsonl`; FR-041, SC-011)

One JSON object per line, append-only, each entry chained to the one before it.

| Field | Rule |
|-------|------|
| `seq` | 0, 1, 2, … with no gaps |
| `prev_sha256` | SHA-256 of the previous line's bytes; 64 zeros for `seq` 0 |
| `candidate_id` | `cand-A1` to `cand-A3`, `cand-B1` to `cand-B3`; a fourth of a family is refused |
| `family` | `ARX` or `Boolean` (D4) |
| `event` | `proposed`, `entered-d4`, `scored`, `evidence`, `decision`, `correction` |
| `oplist_sha256` | hash of the candidate's operation-list module (R11) |
| `parameters` | round structure, nonlinear component, rotation and constant rules, generics |
| `evidence` | record IDs |
| `budget_used_h` | `{trails, structural, statistics}` with the caps of R7 |
| `decision`, `reason` | `eligible`, `ineligible`, `rejected`, `selected` or `not selected`, with the reason |
| `date_utc` | ISO 8601 |

An entry is never edited or deleted; a correction is a new entry that cites the `seq` it
corrects. `cand-A1` is the long-trail ARX-box design (FR-022). A reduced variant, a round count or
a fix to the model that leaves the design unchanged is logged under its candidate, never as a new
one (stop rule).

```text
proposed ─► entered-d4 ─► scored ─┐       (only candidates entered before the D4 choice)
   │                              ▼
   └────────────────────────► analysed ─► eligible ─► selected ─► frozen
                                  │           └─────► not selected
                                  └─► ineligible or rejected (reason recorded; stays in the log)
```

## 4. Demonstration record (`fut-sec-8/demonstration.json`; FR-001 to FR-003)

| Field | Rule |
|-------|------|
| `targets` | the first three seeds of the feature-002 `dev` set, from `protocol.seedsets.load("dev", allow=("dev",))` |
| `revealed` | per target, (s₀, s₁) |
| `observed` | per target, the first three output words after the 256-step warm-up, with their positions (T1 knows them) |
| `tool` | SHA-256 of `fast/seed_search.c` and of the binary; compiler, flags, threads |
| `vector_check` | per golden file: 10,000 words compared, mismatches; must be 0 before the sweep |
| `matches` | per target, after one, two and three words, beside the expected numbers (about 1, 2⁻³² and 2⁻⁶⁴) |
| `listed` | every (s₂, s₃) that matches three words; any extra one separated by the fourth word |
| `recovered` | per target: whether the target is among the three-word matches |
| `cost` | steps per candidate, total steps and seconds, steps per second; extrapolation to 2⁶⁴ seeds |
| `model_sha256` | `1260142d…` for `phycoweb/model_v2.py`, checked |
| `report` | the nine items of security.md §12.4, with T1 as the attacker |

The record is the search tool's validation record (security.md §12.5), and security.md's
best-attack register row for exhaustive seed search cites it (FR-003).

## 5. Structural and statistical evidence (`candidates/<id>/<kind>-<record_id>.json`)

| Kind | Fields beyond section 1 | Verdict computed by code |
|------|-------------------------|--------------------------|
| `inverse` | sizes and variants; the 16 vector inputs and 2¹⁰ test states; both directions | `pass` if 0 mismatches |
| `bijectivity` | variant 2×2, w = 4; 2³² inputs; ones in the output bitmap; bitmap SHA-256 | `pass` if 2³² distinct outputs |
| `dependency` | per round and direction, the bit pairs without dependency; R_f, R_b; per-round summaries committed, full matrices local (R16) | R_f and R_b reported |
| `frequency` | N = 2²⁰, S = 2b, threshold 0.005/S; per round count and direction the smallest p-value and the fired bits | fires or not; raises R_dist |
| `avalanche` | N_a = 2¹², the flip set F, S_A = 2·\|F\|·b; as for `frequency` | fires or not; raises R_dist |
| `control` | the test it controls, its counts, whether it fired | if it fired, that size's bias evidence is `inconclusive` |
| `symmetry` | patterns and symmetries checked; symmetries that fix a pattern | `pass` if none |
| `invariant` | forms and differences checked; any kept on every test state | `pass` if none |

## 6. Trail-bound record (`candidates/<id>/bound-<record_id>.json`; FR-038)

| Field | Rule |
|-------|------|
| `bound_kind` | `differential` (trail probability) or `linear` (squared trail correlation) |
| `rounds`, `width`, `size` | the variant it bounds |
| `bound` | a rational `{num, den}` and its −log₂ |
| `method` | for example `active-box count`, `exhaustive table`, `milp`, `branch-and-bound` |
| `tool`, `validation_record` | the tool and its validation record, which must be older (FR-039) |
| `scope` | "single trails under the usual independence assumptions; clustering into differentials and linear hulls, and key-dependent effects, open for feature 005" |
| `budget` | hours used and the cap; a capped search has `status` `inconclusive` and no `bound` |

## 7. Tool validation record (`validation/<tool>-<record_id>.json`; FR-039)

`tool`, `version`, `licence`, `source` (in the repository, or the download-approval row),
`known_result` (paper, table and value, or the security.md finding S12–S15 or FUT-SEC-8),
`found`, `outcome` (`re-found` or `not re-found`). A tool's results count only after a
`re-found` record of the same kind exists.

## 8. D4 choice record (`d4/choice.json`; R5, R6)

`entered` (candidate IDs with their log `seq`), `width` (16 or 8), `r_star`; per scored
candidate `W_D` and `W_L` as rationals, `luts` (R5) and the score; `representatives`;
`chosen_family`; `tie_breaks_applied`; `bound_records`. Written once by `scripts/d4_choice.py`
from saved bound records; a second run that would change it is refused.

## 9. Round rule, eligibility and selection

`candidates/<id>/round-rule.json`, per claimable size: `R_f`, `R_b`, `R_bound` (with its bound
records), `R_dist` (with its evidence records), `delta` = 2, `R`, and `eligible` with each item
of FR-018 to FR-031 and FR-037 and its evidence. `selection.json`: the eligible candidates of the
chosen family, or of the other family if it has none; R at 4×4; any tie and the owner's recorded
choice; or the stop-rule outcome with its reason.

## 10. Size profile and security target (`security-target/`)

`parameters.json`, one row per supported size: `n`, `w`, `lanes_per_node` (2), `b`, `c`, `r`,
`R`, `key_entropy_bits` (256), `reachable_secret_state_bits`, `bound_bits`, `status` (`claimable`
or `research`), `variant_id`, and the generic-bound checks of FR-010 with 0 violations required
at every claimable size. `limits.json`: `epsilon` (2⁻⁶⁴), `N` (2¹²⁸), the theorem (paper,
theorem number, `verified` or `unverified`), the limits per instantiation, per request and per
key, `u`, the bound at the limits and the doubling check of R9.

## 11. Vectors (`vectors/phyco-v3/`; FR-036, FR-054)

| File | Content |
|------|---------|
| `pi_<variant>.json` | 16 inputs and their Π and Π⁻¹ outputs, as lanes in hex in the design document's order; round-by-round states for the first 4 |
| `mode_<variant>_dev<i>.hex` | header line, then 10,000 lines of `%08X`, as the `phyco-v2` vector files |
| `digest_<variant>.json` | SHA-256 of the first 2²⁰ words for key and nonce 0, in requests of 4,096 words |
| `constructed_<variant>.json` | per edge state: name, construction, whether a key reaches it, inputs, outputs |

The header of a mode vector file reads, for example:

```text
# model=phyco-v3 variant=phyco-v3/n4-w32-R<R>-c256 key=dev/0 nonce=dev/0 pers=empty requests=1,7,64,1000 count=10000 format=u32-hex
```

Every file records its generating command, the model's SHA-256, the measured speed and the
generation time; a variant directory name is the variant ID with `/` replaced by `_`.

## 12. Baseline archive (`baseline/phyco-v2/MANIFEST.json`; FR-042)

As `baseline/float-v0/MANIFEST.json`: `created_utc`, `git_head`, and `files`, each with
`archive_path`, `source` (path and commit), `sha256` and `note`. The archive holds
`phycoweb/model_v2.py`, `phycoweb/lut.py`, `fast/phyco_stream.c`, `fast/lut_table.h`,
`specs/002-core-dynamics-redesign/design.md` and both `vectors/phyco-v2_*.hex`. A test checks each
copy against its manifest hash and its live source (SC-012).

## 13. Design freeze record (`freeze/freeze.json`; FR-043)

SHA-256 of the design document (with its version), `phycoweb/model_v3.py`,
`phycoweb/constants_v3.py`, every vector file including the constructed-state vectors, and the
scripts that generate the constants and the vectors; per claimable size R with every input of
the round rule (record IDs); tool versions; `git_head`; `git_dirty`, which must be false;
`status` `draft` until the owner approves, then `approved` with who, when and the wording.
`validate` recomputes every hash; after approval the frozen files must not change.

## 14. Provenance record (`provenance.jsonl`; FR-067)

One line per file drafted or repaired with an AI tool: `path`, `sha256`, `tool` and `model`,
`session`, `date_utc`, `task_id`, `review_status`. The entries for `phycoweb/model_v3.py` and
`tests/v3_reference.py` must name different sessions (FR-057).

## 15. Claim and evidence register (`protocol/claims.json`; FR-069)

One entry per model ID (`float-v0`, `lut-v1`, `phyco-v2`, `phyco-v3`): `claim_level` (L0…L5),
`claim` (`no claim`), `bound` (for example "at most 64 bits" for `phyco-v2`), `evidence`
(record paths), `updated`. `phyco-v3` starts at L0 and moves to L1 only after its gate (FR-012).

## 16. Review package (`review-package/MANIFEST.json`; FR-063)

Every item of security.md §14, each with its path, `git_head` and SHA-256, plus the known
limitations and the unresolved findings. Assembling it is in scope; sending it is the owner's
action.

## 17. State transitions

- **Candidate**: the diagram in section 3.
- **Claim level of `phyco-v3`**: L0 now; L1 once its gate has passed after the review of
  FUT-SEC-8 and of the security-target chapter (FR-012); L2 started, not reached. Every level
  carries "no claim".
- **Design document**: draft versions 0.x; the version the owner design review approves; frozen
  as 1.0. After the freeze any change is a new model ID (FR-028).
- **Gates** (spec Review & Approval table): `_pending_` to Approved or Declined, with date and
  notes; one row per approved download.
- **Evidence status**: `not evaluated` until a record exists; `inconclusive` for a capped search
  or a fired control; `blocked` while a gate it needs is pending; otherwise the computed verdict.
