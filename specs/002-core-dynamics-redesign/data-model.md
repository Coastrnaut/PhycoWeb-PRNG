# Data Model: Core Dynamics Redesign

**Feature**: [spec.md](./spec.md) | **Research**: [research.md](./research.md)

## 1. Generator design `phyco-v2`

The exact state and update are **not fixed by this plan**. They are fixed in `design.md` at the
design freeze (research R9). The plan fixes the shape that every candidate must fill in, and
the checks that apply to it.

| Field | Rule |
|-------|------|
| `MODEL_ID` | `"phyco-v2"`. A later frozen revision gets `"phyco-v2.<k>"`. |
| State elements | Each element has a name, a width ≤ 32 bits, a signedness, a wrap rule (mask or two's-complement wrap) and a reset value (FR-002) |
| Seed → state | Four ints in 0…65535, otherwise `ValueError` (FR-009). The derivation is written out step by step |
| Perturbation | lut-v1 table, `INC_A = 4`, `INC_B = 6`, `COS_OFFSET = 64`, imported from `phycoweb.lut` unchanged (FR-003) |
| Step order | Numbered list: perturbation → flux → growth/decay → disruption → output (FR-004). Each line uses only FR-001 operations |
| Disruption | A threshold rule, with a counter `disruptions` exposed for FR-005 measurement |
| Output | `compute_block()` → int in 0…2³²−1 from state only (FR-006) |
| Warm-up | `WARMUP` steps run before the first output word. This is a constant of the design |

**Validation (automatic)**:
- AST purity check on `phycoweb/model_v2.py`. No `Mult`, `Div`, `FloorDiv`, `Mod` or `Pow`
  anywhere in the module. No float literals, and none of `float`, `math`, `sin`, `cos`. No
  shifts by a non-constant amount. Allowed imports: `typing`, `phycoweb.lut` (SC-001).
- Width check: every assignment to state goes through a mask or wrap helper. A state-fuzz test
  asserts the bounds after every step.
- FR-007: imports are on an allow-list, and the code is reviewed at freeze. This cannot be
  proven automatically.

## 2. Seed set

| Field | Type / rule |
|-------|-------------|
| `name` | `dev`, `heldout-1`, `heldout-2`, `heldout-3` |
| `seeds` | 100 tuples (a, b, c, d). Seed *i* = first 8 bytes of SHA-256(`phycoweb-002/<name>/<i>`) as 4 big-endian u16 |
| `canonical_sha256` | SHA-256 of the lines `"a b c d\n"`. Must equal the spec value, or loading fails |
| `status` | `unused` → `frozen` (a freeze record names it) → `used` (an attempt record exists). Never goes back. `dev` is always unrestricted |

## 3. Design freeze record

File: `reports/002-core-dynamics-redesign/attempt-<N>/freeze.json`

| Field | Rule |
|-------|------|
| `attempt` | 1, 2 or 3. Must be the next one after the existing attempts |
| `seed_set` | `heldout-<N>` |
| `model_id`, `model_sha256` | SHA-256 of `phycoweb/model_v2.py` (and of `phycoweb/lut.py`) |
| `design_version`, `design_sha256` | `design.md` version line and file hash |
| `harness_version`, `harness_sha256` | `sp80022.__version__` and a combined hash of its sources |
| `warmup` | Copied from the design |
| `dev_evidence` | Path to the dev evaluation record the owner reviewed |
| `approved_by`, `approved_on` | **Left empty by the tool.** The owner fills them in. Acceptance refuses to run while they are empty |

State transitions: `draft` (written by `freeze.py`) → `approved` (owner edit) → `consumed` (the
attempt record exists). A consumed freeze is never edited.

## 4. Evaluation record

File: `.../eval.json` (one per source: positive control, negative control, candidate; or one per
dev run).

| Field | Content |
|-------|---------|
| `source` | `os-csprng`, `lut-v1`, `phyco-v2`, … |
| `seed_set`, `seeds` | Name and list (control: the stored byte file and its SHA-256 instead) |
| `n_bits`, `bit_order` | 2,097,152, `msb-first` |
| `parameters` | The table from research R2, as data |
| `sequences[i]` | For each test: `eligible`, list of sub-test p-values |
| `subtests[test][j]` | `m_prime`, `pass_count`, `proportion_bound`, `proportion_ok`, `histogram[10]`, `p_value_t`, `uniformity_ok`, `ok` |
| `families[test]` | `n_sub`, `failed_sub`, `k_max`, `pass` |
| `verdict` | `pass` if all 15 families pass |
| provenance | `git_head`, `git_dirty`, `versions` (python, numpy, scipy, sp80022), `command`, `workers`, `started`, `elapsed_s` |
| `limitations`, `disclaimer` | The FR-019 text, verbatim |

## 5. Attempt record

File: `reports/002-core-dynamics-redesign/attempt-<N>/attempt.json` plus `summary.md`.

| Field | Content |
|-------|---------|
| `attempt`, `freeze_sha256` | Links to the approved freeze |
| `order` | `["positive", "negative", "candidate"]`, with the start and end time of each |
| `positive`, `negative`, `candidate` | Paths to the eval records and their verdicts |
| `overall` | `PASS`, `FAIL` or `INCONCLUSIVE`, using the spec's overall-verdict rule |

## 6. Harness change log

File: `reports/002-core-dynamics-redesign/harness-changelog.md`. One entry per change:
date, harness version, change, category (`defect-fix`, `sp800-22-fidelity`, `added-coverage`),
evidence, and the statement "removes no test or sub-test, does not shorten sequences or loosen
thresholds" (FR-014).

## 7. Dev run log

File: `research/002/runs.jsonl`. One JSON line per exploration run: `variant`, `source_sha256`,
`seeds` (set name or explicit list), `n_sequences`, `families_failed`, `disruption_rate`
(min, max), `command`, `date`.
