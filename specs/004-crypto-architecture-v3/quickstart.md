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

- Spec approved (done 2026-11-01); plan approved (done 2026-11-01); tasks approved (pending).
- For P and U: nothing else; WSL with gcc 15 and make is present.
- For V (published values), T (theorem papers) and AIS 20/31 3.0: the files of research R19,
  whose downloads the owner approved on 2026-11-01 (`169.pdf` and `47270450.pdf` through the
  owner's browser), or values the owner provides with their source.
- For E with key loading, M and F: the FUT-SEC-8 result review approved.
- For X: the owner's recorded go-ahead for the separate session.

## Setup (P)

| Step | Command | Expected |
|------|---------|----------|
| P0 | `python -W ignore -m unittest discover -s tests -t .`, **heavy** once FR-053's two-worker test exists | all tests pass, or skip with a listed open item, and none fails, existing or new, while no other heavy run holds `data/heavy-run.lock`; FR-053's two-worker test is marked heavy and takes the lock, and fails naming the lock if another run holds it |
| P1 | `python scripts/archive_phyco_v2.py --check` | 0 mismatches between copies, manifest and live files (SC-012) |
| P2 | `python -c "from protocol import devinputs_v3 as d; print(d.load('dev', 'key', allow=('dev',), count=1)[0].hex())"` | 64 hex digits; fingerprint checked at load |
| P3 | any evidence script with an input namespace other than `dev` or `control` | exit 2, nothing written (FR-040) |
| P4 | append to the candidate log while another process holds `data/log-append.lock` | exit 2 after 10 s, nothing appended (R16) |

## FUT-SEC-8 (US1)

| Step | Command | Expected |
|------|---------|----------|
| U1 | `make -C fast -f seed_search.mk` (WSL) | builds `fast/build/seed_search` with `-Werror`, committed before U3 (research R18), its `--source-sha256` printing the SHA-256 of `fast/seed_search.c` (research R16); `fast/build/phyco_stream` untouched and ignored |
| U2 | `fast/build/seed_search --check-vectors vectors/phyco-v2_*.hex` | exit 0: 2 × 10,000 words match |
| U3 | **heavy**: `wpy scripts/fut_sec8.py --binary fast/build/seed_search --out-dir $REP/fut-sec-8` | all 3 targets recovered; matches after one, two and three words beside about 1, 2⁻³² and 2⁻⁶⁴; under an hour (SC-001); progress lines from the main thread only (R2) |
| U4 | run U3 again | exit 2 (one pass per target) |
| U5 | owner review recorded in the spec | key-loading guard passes from then on (FR-003) |

## Tool validation (V)

| Step | Command | Expected |
|------|---------|----------|
| V1 | `python scripts/validate_tool.py --tool <tool> --known s13-transport --out-dir $REP/validation` with the invariant checks as the tool, and the same for `s13-decay` (the invariant checks), for `s12`, `s14` and `s15` (the bias test) and for each structural tool's known result of research R13 (symmetry, dependency propagation, exhaustive bijectivity, invariant checks, avalanche, cost model, degree derivation) | `re-found` records, which with V2's for the four trail tools' published values make one for every counted tool (SC-007); the bias test's record also shows its planted bit firing in 82 to 97 of each family's 100 synthetic sets, with at most 3 sets holding an unplanted firing (R4) |
| V2 | `validate_tool.py --tool <trail tool> --known speck32-diff` (and `speck32-lin`, `present-5r`, `sparkle-box`) | `re-found`; exit 2 without a recorded source for the value |

## Security target (T, US2)

| Step | Command | Expected |
|------|---------|----------|
| T1 | `python scripts/mode_limits_v3.py --out $REP/security-target/limits.json` | bound at most ε = 2⁻⁶⁴ at the limits, doubling check passes; `theorem` `unverified` until its paper is read; the size profile `parameters.json` written beside `limits.json` |
| T2 | reviewer checks `security-target/parameters.json`, written by T1's `mode_limits_v3.py`, and its record against security.md §12.2 | 0 violations at every claimable size, each check computed by code (SC-003; FR-010, FR-065); keyed reduced variants with a c-bit key and a c/2-bit nonce, checked at s = c/2 (R14) |

## Candidates and evidence (E, US4)

| Step | Command | Expected |
|------|---------|----------|
| E1 | `python scripts/evidence_v3.py --candidate cand-A1 --kind inverse --out-dir $REP/candidates/cand-A1` | `pass` at every supported size and variant (SC-004) |
| E2 | **heavy**: `wpy scripts/evidence_v3.py --candidate cand-A1 --kind bijectivity --size 2 --width 4 --out-dir …` | 2³² distinct outputs (SC-004) |
| E3 | **heavy** `evidence_v3.py --kind control --test frequency --size 4 --out-dir $REP/controls` and the same with `--test avalanche`, each projected first with `--project`; `evidence_v3.py … --kind frequency --size 4 --project`; then **heavy** `--kind frequency --size 4` and `--kind avalanche --size 4` | each control, run once per test and size before that test's first use there by any candidate, does not fire, and its one record serves every candidate (a control that fires makes that size's bias evidence inconclusive for every candidate, and the feature recommends stopping); the projection fits the budget row (R7), and the probes at 8×8 and 16×16 that it needs write only projection records; frequency and avalanche records with every input and difference set of R4, counts, p-values, projected and used hours, and 0 disagreements between the avalanche counts and the dependency matrices; every heavy run takes the lock and records `heavy_run` true |
| E4 | `python scripts/d4_choice.py --log research/004/candidates.jsonl --out $REP/d4/choice.json`; run it again | the choice with its inputs and `outcome`; the second run exits 2; after an exact tie, `--tie` writes `d4/tie.json` once both values of R at 4×4 exist |
| E5 | `python scripts/round_rule.py --candidate cand-A1`, then `--select` | R per claimable size with every input cited (SC-005, SC-008); a selection, or exit 1 for a stop |
| E6 | log a fourth candidate of one family | exit 2 (SC-011) |
| E7 | `evidence_v3.py … --kind frequency --size 8` before that candidate's 4×4 frequency run has finished | exit 2: sizes run in order (R7); a `--project` probe at size 8 is not refused and writes only its projection record |

## Model and vectors (M, US3)

| Step | Command | Expected |
|------|---------|----------|
| M1 | `python scripts/gen_constants_v3.py --check` on Windows; `wpy scripts/gen_constants_v3.py --check` in WSL | exit 0 on both, each writing a `generator-check` record with verdict `match` under `$REP/generator-checks/`; the pair is SC-009's evidence (SC-006, SC-009) |
| M2 | `python scripts/gen_vectors_v3.py --check` on Windows; `wpy scripts/gen_vectors_v3.py --check` in WSL | exit 0 on both, each writing a `generator-check` record, as in M1 (SC-009) |
| M3 | `python scripts/gen_constructed_v3.py --check` on Windows; `wpy scripts/gen_constructed_v3.py --check` in WSL | exit 0 on both, each writing a `generator-check` record, as in M1 (SC-016, SC-009) |
| M4 | `python -c "from phycoweb.model_v3 import Generator; Generator('phyco-v3/n2-w16-R8-c64', bytes(32))"` | `VariantRefused` (SC-010) |
| M5 | `python -W ignore -m unittest tests.test_model_v3` | refusals beyond every limit, reached through `ResearchDuplex.from_state` from chosen counter values (REP-078), call-sequence errors including any call after `zeroize`, boundaries (FR-058) |
| M6 | `python -c "from phycoweb.model_v3 import ResearchDuplex as D; D('phyco-v3/n2-w16-R8-c64', bytes(32))"` | `ValueError` at construction: that variant takes an 8-byte key, and a 4-byte nonce at `instantiate` (R14) |

## Second transcription (X)

| Step | Command | Expected |
|------|---------|----------|
| X1 | `python -W ignore -m unittest tests.test_v3_transcription` | agreement at 100% of the steps of the committed vectors, with the common-mode caveat (SC-016) |
| X2 | `python -c "import json; …"` over `$REP/provenance.jsonl` | the model and the transcription come from different sessions (FR-057) |

## Review and freeze (F, US5)

| Step | Command | Expected |
|------|---------|----------|
| F1 | `python scripts/design_freeze.py create` before the owner design review | exit 2 |
| F2 | after the reviews, the five steps of [contracts/cli.md](./contracts/cli.md): the owner commits the feature files, the owner's next commit after the one that records the owner design review's approval in its row with the highest k, of every feature file changed since or an empty commit of the owner's where none changed, and, where the owner commits "Environment record <n>" or "Log repair <n>" on its own between that approval and step (1), the owner's next commit after the one that records the approval of the review held again in "Owner design review <k>", the agent committing no file of this feature from the first commit that records an owner design review's approval to the feature's end, plan phase 9 included, and writing the owner design review's review entries right after that approval's commit, before the owner sets any row for step (1), the external review's row among them, so that step (1)'s commit holds the entries and the rows (PRO-075); `create` on a clean tree, with that commit as HEAD, recorded as `owner_commit` (`freeze_status` `draft`); the owner's approval; the owner commits the record; `validate` | exit 0 (FR-043); `create` exits 2 unless HEAD is that commit of step (1), the one it records as `owner_commit`, and while `check_claims.py` reports a finding at HEAD (PRO-070; SEC-084; PRO-073); `validate` exits 2 while its `freeze_status` is `draft` (REP-093) |
| F3 | `python scripts/recheck_004.py` in a fresh clone, on any machine | 0 disagreements (SC-017); its `recheck` record names the interpreter, platform and `pip freeze` it ran with, and says when that environment is not one of research R1's |
| F4 | `python scripts/check_claims.py` | 0 findings (SC-015, SC-018) |
