# Implementation Plan: Cryptographic Architecture, Second Design Round (phyco-v4)

**Branch**: `005-crypto-architecture-v4` (directory only; no git branch, as for feature 004) | **Date**: 2026-11-09 |
**Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/005-crypto-architecture-v4/spec.md`, approved by the owner on 2026-11-09 with
decisions D1–D14 as their defaults (b1b79d8); security.md 2.18 and the register in a84daa1 (FR-027).

> This feature makes no security claim. No PhycoWeb-PRNG model, `phyco-v4` included, may be used
> to generate secrets; use an established cryptographic random-number generator for keys,
> nonces, tokens and salts. Passing statistical tests does not show cryptographic security.

## Summary

Feature 005 runs feature 004's plan, which the spec's FR-001 makes its baseline (`plan.md` at 99e6994, SHA-256
`665c793450918805ed7e5b86873b1b5195cbc9d86f99ad94f7bbbdfd665f2c95`), and this plan states only what changes. Where the two
differ, this plan applies. The work runs in this order, each step needing the one before it, except that steps 2 and 3, the
probes and the security target, run in either order, each after step 1 and both before step 4 (spec FR-005):

1. **Machinery for feature 005** (research R9): the record writers, guards and logs take the feature as a parameter, so that
   feature 005 writes under its own paths and feature 004's verdicts, records and re-check stay as they are (FR-003). Feature
   005 gets its own environment records, three hash-chained logs, the disclaimer naming `phyco-v4`, the claim test's coverage
   (FR-026) and the re-check of `split` bounds and trail characteristics (FR-016, FR-020).
2. **Probes before any candidate** (R5): the runs feature 004 never made on the reference designs, cand-A1 and cand-B1, are
   probed, each up to 4 h, as `projection` records charged to the feature-wide row, and complete the projection table; its
   values only fall from this plan's (FR-005, FR-009).
3. **The security target first** (User Story 2): the design document's chapters "Security target" and "Mode" start from
   feature 004's Version 0.4; the ⛔ security-target review comes before any candidate is proposed, and "L1 recorded" follows
   (FR-010 to FR-013; R8).
4. **Candidates and evidence** (User Stories 3 and 4): candidates `v4-A<k>` and `v4-B<k>`; the D4 choice as inherited; the
   production-width bound climbs at 16×16 first, continued past a capped search by sums of shorter spans, a candidate without
   R_bound at 16×16 decided at once; the structural checks and bias tests at 4×4 first; the round rule; a selection or a stop;
   the selection-bias statement over features 004 and 005 (FR-014 to FR-024; R6, R7, R11 to R13).
5. **Model, vectors, transcription, reviews and freeze** (User Story 5), as inherited (FR-025).
6. **The final report** (FR-029), with the projection table beside the hours measured.

### Values this plan fixes before first use

From plan approval these values belong to the pre-registered protocol and may only become stricter (FR-009; inherited
FR-044). Every number below is computed by `research/005/plan_projections.py` from feature 004's committed records, which it
reads and never writes, into `research/005/plan-projections.json`, committed with this plan; `--check` recomputes it and exits
1 on a difference (FR-004).

| Item | Value fixed here | Research | Stricter means |
|------|------------------|----------|----------------|
| Calibration (FR-004) | From feature 004's 90 bound searches paired with their projections: measured over projected runs from 0.00021 to 2274 (median 0.10); 27 projections were feature 004's 8 h cap, no estimate, and 26 read below 0.001 h, the clock's tick. Factor F = max(1, the largest ratio over the 37 pairs projected at 0.001 h or more and below the cap): active-box count 1.000 at 4×4, 7.447 at 8×8, 2274 at 16×16 (its capped run's ratio, a lower bound); active-S-box count 1.000 at 4×4; branch-and-bound 1.006 at 4×4. Other kinds, from records holding their own projected and used hours: control 3.867, validation 1.186, cross-check 1.000, demonstration 1.000, rotation ranking 1.000 | R1 | the factors do not change |
| Projected needs (FR-005) | A search feature 004 made: its measured hours, or this plan's cap where it ended at its cap; one feature 004 projected but did not make: its projection times F, or the cap where that projection was feature 004's cap or the product is not below this cap; one it neither made nor projected: the cap. Other kinds never run at w = 32: provisional needs per candidate of 12 h (structural checks) and 24 h (frequency and avalanche tests), twice feature 004's rows, until the probes replace them | R2, R5 | needs only fall after the probes |
| Listed climbs (FR-005) | Per reference design, size and kind, r = 1, 2, … in order, ending after the first search projected to reach its cap (FR-015), at the first r whose bound, searched or summed, has weight above 128, or at R_max = 64 | R2 | no change |
| Caps (FR-006) | 8 h at 4×4, 24 h at 8×8, 48 h at 16×16, for each kind (option E, the owner's extension at the plan approval); each at least twice the longest listed search projected to finish under it (floors 2.17 h, 18.61 h and 0.34 h) | R3 | caps only fall |
| Thread count (FR-007) | 1 for every search, recorded in every record | R4 | does not change |
| Rows (FR-005, FR-008) | Per candidate, from its family's reference design, each at least twice the projected needs it holds: an ARX candidate 267.5 h (trail searches 195.5 h, structural checks 24 h, bias tests 48 h), a Boolean candidate 425.3 h (trail searches 353.3 h, structural 24 h, bias 48 h); the feature-wide row 102 h (probes 40 h, two whole-suite runs per platform 2 h, reproductions and re-checks 9 h, doubled) | R3 | rows only fall |
| Candidate limit and ceiling (FR-008) | Three evaluated candidates per family, as inherited; the rows of six candidates and the feature-wide row sum to 2,180.4 h, and the ceiling is 2,200 h, raised from D7's 720 h by the owner at the plan approval, as FR-008 provides | R3 | both only fall |
| Margin and R_max (D5, D7) | Margin 2; R_max = 64 | R2, R3 | the margin only rises; R_max only falls |
| Order at a size (FR-015) | r ascending, the linear search then the differential search at each r, each kind's climb independent; a capped or refused search ends that kind's searches at that size | R12 | no change |
| Formats (FR-016, FR-019) | The `split` bound record and the trail characteristic at every nonlinear operation, as data-model §2 and §3 state | R6, R7 | fields only added, each settling a case the format left open (spec, the changed rules) |
| Development inputs (FR-028) | Feature 004's derivation under the namespace `phycoweb-005/`, every other namespace refused | inherited R3 | the derivation does not change |

### Choices for owner review

The planner took the first option of each, the recommended one. At the plan approval of 2026-11-09 the owner took the
recommended option of the last four and, for the first, asked to "extend run limits even more to ensure we find a good
candidate also": option E (research R3) replaces option A, with the probe limit raised from 1 h to 4 h and the provisional
structural and bias needs doubled.

| Choice | Options | Research |
|--------|---------|----------|
| FR-008's case: with feature 004's caps, 8 h at every size, the rows of six candidates come to 736.6 h, above the ceiling, and the 8 h cap at 8×8 fails FR-006 (B1's calibrated projection at r = 1 there, 5.95 h, needs a cap of at least 11.9 h) | **A (recommended): caps 4, 4 and 12 h; three per family; 700.9 h, within 720 h.** B: caps 8, 20 and 20 h; two per family; 843.6 h, the ceiling raised. C: caps 4, 4 and 24 h; three per family; 988.9 h, the ceiling raised. **E (decided by the owner): caps 8, 24 and 48 h; three per family; 2,180.4 h, the ceiling raised to 2,200 h** | R3 |
| Thread count | **1 (recommended): the calibration holds only one-thread runs, and scipy's HiGHS interface sets no thread count.** Alternatives, each a tool change validated again before use: the MILP split by first-round activity over worker processes; a solver that runs threads, named only as candidates (OR-Tools CP-SAT, HiGHS through `highspy`), each a download needing the owner's permission for that file | R4 |
| Probes for runs feature 004 made | **Cite feature 004's record (recommended): the same tool on the same operation list, size, width, kind and r, on the same machine, at one thread, needs no second run.** Alternative: probe every listed run again | R5 |
| Rows per family | **A candidate's rows from its family's reference design (recommended).** Alternative: every candidate's rows at the larger of the two | R3 |
| Machinery | **The feature as a parameter of the protocol modules, feature 004's values its default (recommended).** Alternative: copies of the modules for feature 005 | R9 |

## Technical Context

**Language/Version**: Python 3.10.11 (Windows) and 3.14.4 (WSL venv `~/.venvs/phycoweb`), as feature 004's research R1 pins
them; C99 for any tool too slow in Python (gcc 15.2.0 in WSL); the model `phycoweb/model_v4.py`, standard library only,
Python 3.8 grammar, after a selection.

**Primary Dependencies**: numpy 2.2.6 and scipy 1.15.3 (HiGHS through `scipy.optimize.milp`) for analysis only, never imported
by the model; feature 004's validated tools under `research/004/tools/`, unchanged; no new download is planned.

**Storage**: committed JSON records and hash-chained JSON-lines logs under `reports/005-crypto-architecture-v4/` and
`research/005/`, as feature 004's data model states them for its paths; local-only outputs under `data/local/005/`.

**Testing**: `python -W ignore -m unittest discover -s tests -t .` on both platforms (feature 004's quickstart P0), with
feature 005's tests in `tests/test_protocol_005.py` and beside the modules they test.

**Target Platform**: the machine of feature 004's research R1: Windows 11 and WSL, 32 logical processors, 68 GB of memory.

**Project Type**: a research protocol of command-line scripts, records and logs, with a reference model after a selection.

**Performance Goals**: every search within its cap (FR-006); every heavy run within its row and all of them within the
ceiling of 2,200 h (FR-008); the throughput goal of feature 004's research R5 reported, deciding nothing.

**Constraints**: one heavy run at a time, projected first (inherited FR-045); one thread per search (FR-007); feature 004's
records, logs and documents read-only (FR-003); every download needs the owner's permission for that file, with its name,
source, size and licence.

**Scale/Scope**: three claimable sizes, 4×4, 8×8 and 16×16 at w = 32, with the research sizes 2×2 and 3×3; at most three
evaluated candidates per family; heavy runs within 2,200 h.

## Constitution Check

*GATE: must pass before Phase 0 research; re-checked after Phase 1 design.*

| Principle | How this plan meets it | Status |
|-----------|------------------------|--------|
| I. Integer-domain arithmetic | The model, written after a selection, keeps feature 004's fully specified integer semantics (its FR-027); no floating point in any datapath; floating point only in analysis tools | Pass |
| II. Reference model and differential testing | Vectors at every size, constructed states and a second transcription, as inherited (FR-025); RTL is out of scope | Pass |
| III. RTL | Out of scope; the grid stays parameterised from 2×2 to 16×16 with neighbour-only data flow (inherited FR-018) | Pass |
| IV. Evidence-based claims | No claim; the protocol is fixed before any candidate's result; the claim test covers this feature (FR-026); every failure is recorded | Pass |
| V. Reproducibility | Every number of this plan is recomputed by `plan_projections.py --check`; records, hashes and the re-check as inherited; `phyco-v2` stays archived | Pass |
| VI. Specification before implementation | The spec is approved; no generator code is written before the plan approval and the tasks approval. `plan_projections.py` is planning analysis over committed records, and no model | Pass |
| VII. Traceability | Every task will cite the FR and SC it serves; FR-030 carries FUT-SEC-1 to FUT-SEC-9 | Pass |
| VIII. Human review gates | ⛔ plan approval, security-target review, owner design review, design freeze and final result review; the agent stops at each | Pass |
| IX. Outward actions | Local commits only, under the owner's standing authorization, with no co-author line naming an AI tool; no push, tag or release | Pass |
| Security Policy | `phyco-v4` at L0 with no claim; FUT-SEC-1 to FUT-SEC-9 traced; FUT-SEC-8 met by feature 004's demonstration and review (FR-030) | Pass |

Post-design re-check (after research.md, data-model.md, the contract and quickstart.md): no principle is affected by the
design; every row still passes, and Complexity Tracking stays empty.

## Project Structure

### Documentation (this feature)

```text
specs/005-crypto-architecture-v4/
├── spec.md              # approved 2026-11-09
├── plan.md              # this file
├── research.md          # Phase 0: R1 to R14
├── data-model.md        # Phase 1: the changes to feature 004's data model
├── quickstart.md        # Phase 1: validation scenarios
├── contracts/cli.md     # Phase 1: the changes to feature 004's command-line contract
├── checklists/          # requirements.md, and the /speckit-checklist runs after the plan approval
├── design.md            # plan phase 3: the design document of phyco-v4
└── tasks.md             # /speckit-tasks, after the plan approval
```

### Source Code (repository root)

```text
protocol/             # the feature as a parameter of evidence.py and its writers (R9); claims.json holds phyco-v4
scripts/              # feature 004's scripts taking the feature; round_rule.py with sums and the 16×16-first order
research/005/         # plan_projections.py, plan-projections.json, the three logs, candidates/<id>/ operation lists
reports/005-crypto-architecture-v4/   # environment records, projections/, candidates/, rechecks/, freeze/, the final report
tests/                # test_protocol_005.py and the tests beside each changed module
phycoweb/model_v4.py  # after a selection only
vectors/phyco-v4/     # after a selection only
```

**Structure Decision**: the repository's existing layout, with feature 005's records, logs and research under their own
paths beside feature 004's, which no step writes.

## Plan Phases

| Phase | Work | Ends with |
|-------|------|-----------|
| 0 | Plan approval (⛔); the `/speckit-checklist` runs; tasks and their approval (⛔) | the tasks approved |
| 1 | Machinery (R9), environment records with their rows, the three logs, the claim test's coverage with `phyco-v4`'s `fut_sec` in the register, the re-check of sums and trails, and `plan_projections.py` reading feature 004's records at 99e6994 | the protocol change log's first entry, naming the baseline documents and `plan-projections.json` by SHA-256 (FR-001, FR-031) |
| 2 | Probes and the final projection table (R5), in either order with phase 3 (spec FR-005) | the table committed before any candidate |
| 3 | The security target first (R8): chapters, ⛔ review, "L1 recorded"; in either order with phase 2 | the review Approved |
| 4 | Tool validation where a tool changed (inherited R12), none planned | each changed tool validated |
| 5 | Candidates and evidence (R6, R7, R11 to R13): entry, D4, climbs 16×16 first, structural and bias tests, round rule, selection or a stop | a selection record |
| 6–8 | Model, vectors, transcription, reviews and freeze (inherited) | `phyco-v4` frozen, or not reached after a stop |
| 9 | Final report (FR-029), ⛔ final result review | the owner's decision |

## Complexity Tracking

No principle is violated; nothing to justify.
