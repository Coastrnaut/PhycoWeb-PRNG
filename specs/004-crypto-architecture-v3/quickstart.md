# Quickstart: Cryptographic Architecture and phyco-v3 Design

> This feature makes no security claim. No PhycoWeb-PRNG model, `phyco-v3` included, may be used
> to generate secrets; use an established cryptographic random-number generator for keys,
> nonces, tokens and salts. Passing statistical tests does not show cryptographic security.

Validation guide. `REP=reports/004-crypto-architecture-v3`. Windows commands use the
feature-002 Python; WSL commands use `~/.venvs/phycoweb/bin/python` (written `wpy`) from
`/mnt/c/GIT/PhycoWeb-PRNG`. Interfaces: [contracts/model-v3-api.md](./contracts/model-v3-api.md)
and [contracts/cli.md](./contracts/cli.md); records: [data-model.md](./data-model.md). Steps
marked **heavy** take the heavy-run lock and never overlap another heavy run.

## Prerequisites

- Spec approved (done 2026-11-01); plan approved (pending).
- For P and U: nothing else; WSL with gcc 15 and make is present.
- For V (published values), T (theorem papers) and AIS 20/31 3.0: the owner's permission for
  each file, or values the owner provides with their source.
- For E with key loading, M and F: the FUT-SEC-8 result review approved.
- For X: the owner's recorded go-ahead for the separate session.

## Setup (P)

| Step | Command | Expected |
|------|---------|----------|
| P0 | `python -W ignore -m unittest discover -s tests -t .` | all tests pass, existing and new |
| P1 | `python scripts/archive_phyco_v2.py --check` | 0 mismatches between copies, manifest and live files (SC-012) |
| P2 | `python -c "from protocol import devinputs_v3 as d; print(d.key(0).hex())"` | 64 hex digits; fingerprints checked at import |
| P3 | any evidence script with an input namespace other than `dev` or `control` | exit 2, nothing written (FR-040) |

## FUT-SEC-8 (US1)

| Step | Command | Expected |
|------|---------|----------|
| U1 | `make -C fast -f seed_search.mk` (WSL) | builds `fast/build/seed_search` with `-Werror`; `fast/build/phyco_stream` untouched |
| U2 | `fast/build/seed_search --check-vectors vectors/phyco-v2_*.hex` | exit 0: 2 × 10,000 words match |
| U3 | **heavy**: `wpy scripts/fut_sec8.py --binary fast/build/seed_search --out-dir $REP/fut-sec-8` | all 3 targets recovered; matches after one, two and three words beside about 1, 2⁻³² and 2⁻⁶⁴; under an hour (SC-001) |
| U4 | run U3 again | exit 2 (one pass per target) |
| U5 | owner review recorded in the spec | key-loading guard passes from then on (FR-003) |

## Tool validation (V)

| Step | Command | Expected |
|------|---------|----------|
| V1 | `python scripts/validate_tool.py --tool <tool> --known s13-transport --out-dir $REP/validation`, and the same for `s12`, `s13-decay`, `s14`, `s15` | `re-found` records (SC-007) |
| V2 | `validate_tool.py --tool <trail tool> --known speck32-diff` (and `speck32-lin`, `present-5r`, `sparkle-box`) | `re-found`; exit 2 without a recorded source for the value |

## Security target (T, US2)

| Step | Command | Expected |
|------|---------|----------|
| T1 | `python scripts/mode_limits_v3.py --out $REP/security-target/limits.json` | bound at most ε = 2⁻⁶⁴ at the limits, doubling check passes; `theorem` `unverified` until its paper is read |
| T2 | reviewer reads `security-target/parameters.json` against security.md §12.2 | 0 violations at every claimable size (SC-003) |

## Candidates and evidence (E, US4)

| Step | Command | Expected |
|------|---------|----------|
| E1 | `python scripts/evidence_v3.py --candidate cand-A1 --kind inverse --out-dir $REP/candidates/cand-A1` | `pass` at every supported size and variant (SC-004) |
| E2 | **heavy**: `wpy scripts/evidence_v3.py --candidate cand-A1 --kind bijectivity --size 2 --width 4 --out-dir …` | 2³² distinct outputs (SC-004) |
| E3 | `evidence_v3.py … --kind control --size 4`, then **heavy** `--kind frequency --size 4` | the control does not fire; a frequency record with its counts and p-values |
| E4 | `python scripts/d4_choice.py --log research/004/candidates.jsonl --out $REP/d4/choice.json`; run it again | the choice with its inputs; the second run exits 2 |
| E5 | `python scripts/round_rule.py --candidate cand-A1`, then `--select` | R per claimable size with every input cited (SC-005, SC-008); a selection, or exit 1 for a stop |
| E6 | log a fourth candidate of one family | exit 2 (SC-011) |

## Model and vectors (M, US3)

| Step | Command | Expected |
|------|---------|----------|
| M1 | `python scripts/gen_constants_v3.py --check` | exit 0 (SC-006) |
| M2 | `python scripts/gen_vectors_v3.py --check` on Windows; `wpy scripts/gen_vectors_v3.py --check` in WSL | exit 0 on both (SC-009) |
| M3 | `python scripts/gen_constructed_v3.py --check` | exit 0 (SC-016) |
| M4 | `python -c "from phycoweb.model_v3 import Generator; Generator('phyco-v3/n2-w16-R8-c64')"` | `VariantRefused` (SC-010) |
| M5 | `python -W ignore -m unittest tests.test_model_v3` | refusals beyond every limit, call-sequence errors, boundaries (FR-058) |

## Second transcription (X)

| Step | Command | Expected |
|------|---------|----------|
| X1 | `python -W ignore -m unittest tests.test_v3_transcription` | agreement at 100% of the steps of the committed vectors, with the common-mode caveat (SC-016) |
| X2 | `python -c "import json; …"` over `$REP/provenance.jsonl` | the model and the transcription come from different sessions (FR-057) |

## Review and freeze (F, US5)

| Step | Command | Expected |
|------|---------|----------|
| F1 | `python scripts/design_freeze.py create` before the owner design review | exit 2 |
| F2 | after the reviews: `create`; owner approval; `validate` | exit 0 (FR-043) |
| F3 | `python scripts/recheck_004.py` | 0 disagreements (SC-017) |
| F4 | `python scripts/check_claims.py` | 0 findings (SC-015, SC-018) |
