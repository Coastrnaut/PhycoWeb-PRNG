# Feature 004 final report: a keyed successor to `phyco-v2`, stopped at the selection

> This feature makes no security claim. No PhycoWeb-PRNG model, `phyco-v3` included, may be
> used to generate secrets; use an established cryptographic random-number generator for keys,
> nonces, tokens and salts. Passing statistical tests does not show cryptographic security.

**Feature**: 004-crypto-architecture-v3 · **Report date**: 2026-11-09 · **Written by**: Claude Code,
model claude-opus-5-5, for the owner's Final result review (T127) · **HEAD when written**: see the
commit that adds this file

## 1. Outcome

The feature stopped at Phase 5, by its own pre-registered rules. Two candidate designs for
`phyco-v3` were analysed, one per family, and neither ended eligible:

- **B1**, the Boolean candidate that the nonlinearity choice rule (D4) chose by its score, did not
  establish R_bound at 4×4. At the production word width, w = 32, its trail bounds stood at
  W_L = W_D = 16, 24 and 32 at r = 2, 3 and 4, and its trails row refused the search at r = 5
  (projection-20261108T155222Z-360a33d6). Candidate-log entry 47 records it `ineligible`.
- **A1**, the ARX candidate analysed after B1 under the selection rule's fallback, established
  R_bound = 17 at 4×4 and 9 at 8×8, but not at 16×16, where the linear active-box count at r = 5
  reached its 8 h cap (bound-20261109T051632Z-d69901f4). Entry 107 records it `ineligible`.
- The agent proposed one replacement per family, B2 and A2, assessed each as likely to end as the
  candidate it replaced, and recommended declining; the owner declined both (entries 49 and 109).
- The set closed (entry 110), and the selection record
  (`freeze/selection.json`, selection-20261109T122326Z-254be6df) stops with "none of the evaluated
  candidates is eligible". No `phyco-v3` model, constants, vectors or freeze exist.

**Recommendation: stop** (section 16). This is security.md §21's Option C for this design round:
PhycoWeb-PRNG stays a documented non-cryptographic research generator, and the work done here
stays available to any later attempt.

## 2. What was reached, phase by phase

| Phase | Reached | Main evidence |
|-------|---------|---------------|
| 0, 1: approvals, writers, logs, register, archive | Spec, plan and tasks approved; the record writers, the three hash-chained logs, the claim register and test, and the archive of `phyco-v2` | spec.md Review & Approval rows; `protocol/`; `baseline/phyco-v2/` |
| 2: FUT-SEC-8 | `phyco-v2`'s 64-bit seed bound reproduced on a reduced domain, 3 of 3 development targets recovered | demonstration-20261104T165604Z-4406adb9; the row "FUT-SEC-8 result review", 2026-11-04 |
| 3: tool validation | Every analysis tool re-found a known result before its results counted | 47 validation records under `validation/` |
| 4: security target | The chapters "Security target" and "Mode" of `design.md` drafted (Version 0.4) | `specs/004-crypto-architecture-v3/design.md` |
| 5: candidates and evidence | Two candidates, the D4 choice, the production-width climbs of seq 524, both candidates `ineligible`, both replacements declined, the set closed, the selection a stop | `research/004/candidates.jsonl` (seq 0–110), 90 bound records, `d4/choice.json`, `freeze/selection.json` |
| 6, 7, 8: model, transcription, reviews and freeze | Not reached: they need a selected candidate (T093) | none |
| 9: polish and this report | README, the feature-002 addendum, the claims checks, the fresh-clone re-check, the whole suite, this report | T121 to T126 |

## 3. Files created or modified

From the feature's first commit (801c6d7, 2026-11-01) to this report: 547 files in 487 commits
before this report's own, all local, none pushed by the agent.

- **Code**: `protocol/` (evidence writers, candidates, rules, changelog, provenance, claims
  register), `scripts/` (17 files: the evidence tool `evidence_v3.py`, `candidate_log.py`,
  `d4_choice.py`, `round_rule.py`, `recheck_004.py`, `gen_constants_v3.py`, `check_claims.py`,
  `clear_lock.py`, `validate_tool.py`, `fut_sec8.py` and the others), `research/004/` (the
  operation-list IR, the candidate modules `cand-A1.py` and `cand-B1.py`, the tools, among them
  the C ARX search, and the refused-constants list), `fast/` (the FUT-SEC-8 seed search).
- **Documents**: `specs/004-crypto-architecture-v3/` (19 files: spec, plan, tasks, research, data
  model, contracts, quickstart, checklists, design document), `README.md`, `security.md`,
  `reports/002-core-dynamics-redesign/phase-report.md` (an addendum).
- **Records**: `reports/004-crypto-architecture-v3/` (392 files: 141 projections, 90 bounds, 47
  validations, 8 generator runs, 6 controls, 2 cross-checks, 2 rotation rankings, 2 round-rule
  records, 2 re-checks, the D4 choice, the selection, the demonstration, the environment records,
  the downloads manifest, a lock-cleared record, the provenance log, and the spec and research
  versions the records cite).
- **Tests**: `tests/` (11 files).
- **Configuration**: `.gitignore`, `.gitattributes`, `requirements.txt` (pinned), `.specify/`.

## 4. Requirements and success criteria

"Met" means the requirement's tasks are done and the evidence cited holds it. "Partly met" names
what is open. "Not reached" means that every task of the requirement lies in Phases 6 to 8, which
need a selected candidate, so the stop leaves it open.

| ID | Requirement | Status | Evidence, or what is open |
|----|-------------|--------|---------------------------|
| FR-001 | Reproduce `phyco-v2`'s seed bound first | Met | demonstration-20261104T165604Z-4406adb9: 3 of 3 targets recovered (T038 to T043) |
| FR-002 | The demonstration record's fields | Met | the same record: matches after one to three words, cost per candidate, the expected numbers |
| FR-003 | The owner reviews the result before key-loading code | Met | the row "FUT-SEC-8 result review" reads Approved, 2026-11-04 (T045) |
| FR-004 | Properties stated as bounds on an adversary's advantage | Met | `design.md`, chapter "Security target" (T069); its review not reached |
| FR-005 | Target strength s = 128 bits at every claimable size | Met | the target stated in `design.md` (T069); a target, never a claim |
| FR-006 | A 256-bit key at the production sets | Met | `design.md` (T069) |
| FR-007 | The output limits | Partly met | stated (T067, T069); `scripts/mode_limits_v3.py`'s first run (T107) not reached |
| FR-008 | Threat model T1 to T11 and the assets | Met | `design.md` (T069) |
| FR-009 | Key entropy and reachable state per size | Met | `design.md` and the parameter table (T067, T069) |
| FR-010 | Every generic bound of security.md §12.2 per claimable size | Partly met | the parameter checks (T066, T067); T107 not reached |
| FR-011 | The certification route named | Partly met | `design.md`, section "Certification route" (T069), with the AIS 20/31 version 3.0 proposal fetched (T065); the security-target review (T108) not reached |
| FR-012 | The claim template filled as a target | Partly met | drafted (T017, T069); T108 to T110 not reached, so "L1 recorded" was never reached |
| FR-013 | The keyed duplex and its calls | Partly met | chapter "Mode" (T070), its theorem papers fetched (T065); the model (T098) not reached |
| FR-014 | Padding and domain separation | Met | chapter "Mode" (T070) |
| FR-015 | Capacity c ≥ 384 bits per claimable size | Partly met | stated (T067, T070); the model (T098) not reached |
| FR-016 | The reseed input chosen by the attacker | Met | chapter "Mode" (T070) |
| FR-017 | The claimable sizes decided | Partly met | 4×4, 8×8 and 16×16, recorded in security.md 2.11 (T069); the design document's chapter (T095) not reached |
| FR-018 | Π a keyless permutation of the torus grid | Partly met | the operation-list IR and its checks (T046, T047); T095 not reached |
| FR-019 | Π bijective by construction | Partly met | the IR's checks and the validated inverse and bijectivity tools (T046, T047, T057, T078); the candidates' runs at w = 32 (T092) and T095 not reached |
| FR-020 | Fixed operations only | Partly met | the operation-list checks and the cost model (T047, T078); T095, T098 not reached |
| FR-021 | Full-range state words | Partly met | the validated frequency tool and the round-rule items (T051, T078); T092, T095 not reached |
| FR-022 | The nonlinear component designed, named and bounded | Partly met | the D4 choice (`d4/choice.json`, Boolean by score, 1/16 against 1/20 at r* = 6, w = 16) and 90 bound records; T095 not reached |
| FR-023 | Round constants by a committed script | Partly met | `scripts/gen_constants_v3.py`, the refused list with its sources (T010, T012, T027, T054, T077, T080); T095, T097 not reached |
| FR-024 | Rotation amounts chosen by trail bounds | Partly met | the rotation search of research R15, two rotation-ranking records, re-checked (T088); T095, T097 not reached |
| FR-025 | The hardware structure rules | Not reached | T095 |
| FR-026 | Output bits per call and throughput | Partly met | the cost model `research/004/tools/costmodel.py` (T073, T074); T095 not reached |
| FR-027 | Semantics of every operation | Not reached | T095; each candidate module declares its semantics, an item the round-rule records find met |
| FR-028 | R from the pre-registered round rule | Partly met | `scripts/round_rule.py` and both round-rule records, R none at every size (T083, T085, T093); T095 not reached |
| FR-029 | R_f and R_b computed exactly | Partly met | the validated dependency tool (T055, T058); the runs at w = 32 (T092) not reached |
| FR-030 | The slime-mould mapping in the design document | Not reached | T095, T111; each candidate's mapping entry stands in the candidate log |
| FR-031 | The threshold-triggered disruption removed | Not reached | T095; neither candidate's operation list holds one |
| FR-032 | Reduced variants from the same generics | Partly met | the IR's generics (T047); T095 not reached |
| FR-033 | The production interface refuses research variants | Not reached | T096, T098 |
| FR-034 | The versioned design document and rationale | Partly met | `design.md` at Version 0.4 with its chapters "Security target" and "Mode", `rationale.md`'s first chapters, and the chapters' test (T066, T068 to T072); the chapters "Permutation", "Hardware structure", "Replaced mechanisms" and "Slime-mould mapping" (T095) and the rest of the rationale (T111) not reached |
| FR-035 | The `phyco-v3` reference model | Not reached | T096, T098, T102 (T024, done, pinned `requirements.txt` as research R18 states) |
| FR-036 | Golden vectors and known-answer tests | Not reached | T099, T100, T102 |
| FR-037 | The structural evidence | Partly met | the validated tools and the uniform controls, 6 records, none fired (T051 to T058, T081, T082, T091); the candidates' runs at w = 32 (T092) not reached |
| FR-038 | First differential and linear trail bounds | Partly met | 90 bound records from validated tools with their cross-checks; R_bound established for A1 at 4×4 and 8×8 only; T092 open |
| FR-039 | Every tool re-finds a known result first | Met | 47 validation records; T124's re-check found each counted result younger than its validation |
| FR-040 | Development inputs only | Met | T008, T023, T033, T034, T039 |
| FR-041 | The append-only candidate log | Met | `research/004/candidates.jsonl`, seq 0 to 110, hash-chained, every candidate with its decisions and reasons, the selection record (T075 to T094) |
| FR-042 | `phyco-v2` archived | Met | `baseline/phyco-v2/` with its manifest (T035, T036) |
| FR-043 | The freeze after the owner design review | Partly met | `round_rule.py` (T085); the review and the freeze not reached; the owner's commit of the Final result review ends FR-043's window (T127) |
| FR-044 | The protocol only stricter, every change logged | Partly met | `research/004/protocol-changes.jsonl` to seq 524, each change before any result it affects (T001 to T077); T109 not reached |
| FR-045 | Heavy runs never overlap | Met | every heavy run projected first and run alone, the whole suite included (T125, projection-20261109T130332Z-95d26c03) |
| FR-046 | Every download with the owner's permission and its licence | Met | the downloads manifest and the rows "Download 1" to "Download 16" (T016 to T031) |
| FR-047 | Feature-002 FR-001 to FR-009 re-decided | Met | the spec's table, restated in section 7 |
| FR-048 | The redesign checklist's dispositions and evidence | Met | section 6 |
| FR-049 | FUT-SEC-1 to FUT-SEC-9 traced | Met | section 5, FUT-SEC-7 and FUT-SEC-5's analysis kept open |
| FR-050 | The design-form disclaimer on every document | Met | `scripts/check_claims.py`: 0 findings over the final documents (T020, T123) |
| FR-051 | security.md's `phyco-v3` section and README | Partly met | README states `phyco-v3`'s status (T121), the feature-002 addendum (T122); security.md's new version (T112) not reached, there being no design to describe |
| FR-052 | This report | Met | this report; the owner's review is T127 |
| FR-053 | Every record reproducible, hashes and line endings pinned | Met | T003 to T042; the records' `code_sha256` and the line-ending tests in the whole suite (T125) |
| FR-054 | Edge states and constructed-state vectors | Not reached | T095, T101 |
| FR-055 | Sign-free operations | Not reached | T095, T098 |
| FR-056 | The frozen oracle the only source of expected values | Not reached | T101, T102, T106 |
| FR-057 | The second transcription | Not reached | T103 to T106 |
| FR-058 | The tests of the model | Partly met | the suite's tests (T015, T031, T032, T037, T125); the model's own tests (T096, T102) not reached |
| FR-059 | The start-up known-answer self-test | Not reached | the chapters' test (T068) waits for it; the chapter "Hardware structure", where the self-test is defined, and its implementation (T095 to T100) not reached |
| FR-060 | Every finding classified | Met | section 10, computed by code from each record's kind and outcome |
| FR-061 | The fields of security.md §17.2 in every record | Met | T008, T009, T041, T082; T124's re-check |
| FR-062 | Facts kept apart; the nine reports of §17.3 | Partly met | section 10; the rationale's labels (T111) not reached |
| FR-063 | The review package | Not reached | T115, T118 |
| FR-064 | No AI session recorded as a reviewer; who took each role | Partly met | section 9; the review steps (T105, T116, T118) not reached |
| FR-065 | Every verdict recomputed from committed files | Partly met | `scripts/recheck_004.py`: 160 records and 4 log entries, 0 disagreements (T124); the `trail` branch of T086 open, no `trail` record existing |
| FR-066 | What feature 005's instructions need | Not reached | no model ID version or design version exists to hand on (section 14) |
| FR-067 | Provenance of every AI-drafted file | Partly met | 410 provenance entries (T010, T011, T013, T026, T072); review entries none; T104, T105, T117 not reached |
| FR-068 | `DESIGN_DISCLAIMER` defined once in code | Met | `protocol/disclaimer.py` (T007, T009, T020) |
| FR-069 | The claim register and its test | Partly met | `protocol/claims.json` and `scripts/check_claims.py`, 0 findings, README's sentence (T017 to T022, T121, T123); T107, T110 not reached |
| SC-001 | 3 of 3 FUT-SEC-8 targets recovered | Met | the demonstration record |
| SC-002 | 9 of 9 FUT-SEC requirements traced with their statuses | Met | section 5 |
| SC-003 | Every generic bound per claimable size, 0 violations | Partly met | T066, T067; T107 not reached |
| SC-004 | Π⁻¹(Π(x)) = x on 100% of the test inputs | Not reached | the inverse tool validated (T057); the candidates' runs at w = 32 (T092) not made |
| SC-005 | R_f, R_b per size; R as the round rule gives | Partly met | both round-rule records give R none at every size; T092 open |
| SC-006 | Constants reproduced on both platforms | Partly met | the generator checks at the reduced sizes (T054, T077); T097 not reached |
| SC-007 | Every counted tool result younger than its validation | Met | T124's re-check, 0 disagreements |
| SC-008 | R_bound established at every claimable size | Not met | the reason for the stop: B1 at no size, A1 at 4×4 and 8×8 only |
| SC-009 | Generated files reproduced on Windows and in WSL | Not reached | T097, T099 to T102 |
| SC-010 | Research variants and requests beyond a limit refused | Not reached | T096, T098, T102 |
| SC-011 | 0 candidates missing from the log, 0 entries deleted, 0 held-out keys | Met | the candidate log's hash chain; T124 |
| SC-012 | The archive and the frozen files of features 002 and 003 hold | Met | T035, T036; T122 found no freeze record of either feature that hashes the report it amended |
| SC-013 | The rationale covers security.md §8 | Not reached | T111, T116, T118, T119 |
| SC-014 | 9 of 9 feature-002 requirements and every §5.3 item disposed | Met | sections 6 and 7 |
| SC-015 | No document describes any model in FR-069's forbidden terms | Met | `scripts/check_claims.py`, 0 findings (T123) |
| SC-016 | Constructed-state vectors and the second transcription | Not reached | T101, T104, T106 |
| SC-017 | Every record holds §17.2's fields; every finding classified | Partly met | T082, T124; the `trail` branch of T086 open |
| SC-018 | The claim-register test reports 0 disagreements | Met | T020 to T022, T121, T123 |
| SC-019 | Input coverage, and 12 of 12 rules of the hardware note mapped | Met | section 8 |
| SC-020 | Provenance for every AI-drafted file; 0 AI sessions as reviewers | Partly met | 410 entries, 0 AI sessions recorded as reviewers; the review package (T115) not reached |

## 5. Security Policy traceability as it stands

The spec's table gives each requirement's expected status at the end of a feature that freezes a
design. With the stop, the statuses that rest on a frozen design document or model are not
reached; the requirements themselves stand specified for any later attempt.

| Requirement | Expected (spec) | At the end of this feature |
|-------------|-----------------|----------------------------|
| FUT-SEC-1 Key entropy | Met by specification | Specified (FR-005, FR-006, FR-010); not reached in a frozen document |
| FUT-SEC-2 Reachable secret state | Met by specification at every claimable size | Specified (FR-009, FR-015, FR-017); not reached in a frozen document |
| FUT-SEC-3 Stream separation | Met by specification | Specified (FR-006, FR-014); not reached in a frozen document |
| FUT-SEC-4 Reseeding | Met by statement (D7) | Met by statement: D7 seeks no property that needs reseeding |
| FUT-SEC-5 Initialization analysis | Partly by specification and evidence; the analysis open for feature 005 | Key loading specified (FR-013, FR-014); the diffusion and first-order measurements (FR-029) not run; the analysis open for feature 005 |
| FUT-SEC-6 Output limit | Met by specification | Specified (FR-007); its tool's first run (T107) not reached |
| FUT-SEC-7 Re-validation | Partly met; the statistical programme open for feature 007 | Open: no model ID, vectors or freeze exist; the statistical programme open for feature 007 |
| FUT-SEC-8 Demonstration first | Done | Done: the demonstration record and its review (FR-001 to FR-003; SC-001) |
| FUT-SEC-9 Certification route | Met by specification; the class an open item | Named in `design.md` (FR-011); the security-target review not reached, the functionality class open |
| FUT-GRID-1 Parameterised size | Partly met | The candidates' operation lists take n and w as generics (FR-018); no model |
| FUT-GRID-2 Key fills the state at every size | Met at every claimable size | Specified (FR-009, FR-017); not reached in a model |
| FUT-GRID-3 Spread across the grid | Met by evidence | Not reached: R_f and R_b were not measured at w = 32 (FR-029) |
| FUT-GRID-4 Per-node constants by rule | Met by evidence | The constant generator and the refused list stand (FR-023); no frozen constants |
| FUT-GRID-5 Validation per size | Vectors met; statistics open for 007 | Not reached: no vectors |
| FUT-HW-1 Generic VHDL | Specified; RTL open for 006 | Not reached in a design document; RTL open for feature 006 |
| FUT-HW-2 Efficient on the Arty A7-100T | Designed for; results open for 008 | The cost model only (FR-026); open for features 006 and 008 |
| FUT-HW-3 Performance on the board | Open for 006 and 008 | Open for features 006 and 008 |
| FUT-HW-4 Equivalence and statistics from hardware output | Open for 008 | Open for feature 008 |
| FUT-HW-5 Hardware security tests | Specified | Not reached: the chapter "Hardware structure" is not written (FR-020, FR-025, FR-059) |

## 6. Redesign checklist (`seed-entropy-bound.md` §5.3), with the evidence of each item covered

| Group | Covered in this feature, with its evidence | Left open by the stop | Later feature |
|-------|--------------------------------------------|-----------------------|---------------|
| A. Fix in the design | key, nonce, capacity and output limits stated in `design.md` (FR-006, FR-007, FR-015, FR-016); the 2×2 decision in security.md 2.11 (FR-017); constants by rule, `scripts/gen_constants_v3.py` and the refused list (FR-023, FR-024); invertibility decided by the IR's checks (FR-019) | parameterised grid in a model, warm-up from measured diffusion, carry chains, food and trees in a frozen document (FR-018, FR-025, FR-029) | VHDL (006); fit and timing (008) |
| B. Analyse | FUT-SEC-8, the demonstration record (FR-001); first linear and differential bounds, 90 bound records (FR-038) | the functional graph of a frozen Π (FR-037) | the attack campaign (005) |
| C. Answer in the spec | the source of the nonlinearity, the D4 choice (FR-022); the certification route (FR-011); the throughput goal, the cost model (FR-026) | the throughput of a frozen design | measured throughput (006, 008) |
| D. Protocol and tooling | every variant logged, the candidate log (FR-041); approval status outside frozen files, the Review & Approval table (FR-034) | the freeze (FR-043); vectors per size (FR-036) | statistics per size (007); on-board counters (008) |
| E. First repository review | re-decided requirements (FR-047, section 7); reduced widths from one generic, the IR (FR-032) | rationale chapters, conserved sum, serialization, branch-free model, key-loading interface (FR-015, FR-020, FR-023, FR-025, FR-034, FR-037) | 006, 007, 008 |
| F. Second repository review | line endings and pinned dependencies (FR-053); the archive of `phyco-v2` (FR-042); storage of this feature's records; documentation drift, README and the feature-002 addendum (FR-051) | backtracking, transport, top bits, rotations, slide, warm-up, invariants and output bits in a frozen design (FR-013, FR-014, FR-019, FR-021, FR-024, FR-026, FR-028, FR-029, FR-037, FR-058) | held-out sets, controls, SP 800-22 rule, PractRand length (007); hardware equivalence (008) |
| G. Pending input | battery attempt 1 of feature 003, a reference only (FUT-SEC-7) | none | none |

## 7. Re-decided feature-002 requirements

9 of 9 stand as the spec's table "Re-decided feature-002 requirements" records them (FR-047): FR-001
kept and made stricter (fixed operations only); FR-002 kept for every datapath word; FR-003
dropped (round constants by rule); FR-004 revised (the mapping kept as documentation, the
disruption removed); FR-005 withdrawn with the disruption; FR-006 revised (the rate part after a
full call of Π); FR-007 re-decided under D6 (a standard mode with a published proof allowed, any
published primitive and its constants refused); FR-008 kept and extended to every size; FR-009
replaced by a 256-bit key and a 128-bit nonce. With the stop none of them is yet carried by a
frozen design; `phyco-v2` keeps its own rules.

## 8. Input coverage and the hardware note's rules

Every section and item of the four input documents keeps the disposition of the spec's section
"Input coverage" (SC-019). The hardware note's rules, 12 of 12:

| Rule | Disposition in the spec | At the end |
|------|-------------------------|------------|
| R1 expected values only from the oracle | FR-056 | not reached: no frozen oracle |
| R2 the tool ladder | 006 | open for feature 006 |
| R3 corner vectors from constructed states | FR-054 | not reached |
| R4 explicit widths, never INTEGER | FR-027, FR-055 | not reached in a design document; each candidate module declares its widths |
| R5 mutation-checked testbenches | 006 | open for feature 006 |
| R6 separate sessions; the oracle before the RTL | FR-043, FR-056; 006 | not reached; the testbench open for feature 006 |
| R7 provenance | FR-067 | partly met: 410 provenance entries, none reviewed yet |
| R8 behavioural VHDL only | 006 | open for feature 006 |
| R9 licence of reused code | FR-046 | met: every download's licence recorded in the manifest |
| R10 downloads | FR-046 | met: rows "Download 1" to "Download 16" |
| R11 heavy runs | FR-045 | met: every heavy run projected first, none overlapping |
| R12 the RTL gate | 006 | open for feature 006 |

## 9. Roles (security.md §16.2)

Computed from the provenance log's review entries, as FR-064 asks: the log holds 410 entries before this report's own, every
one with `review_status` `pending` and no `reviewer`, so no role was staffed by a reviewer in this
feature. Who did the work:

| Role | Taken in this feature by |
|------|--------------------------|
| Lead and evidence tracking | AI agent (Claude Code, model claude-opus-5-5); the owner's gate decisions in the Review & Approval table |
| Specification | AI agent; the owner's approval of the spec, plan and tasks |
| Implementation | AI agent |
| Statistics | AI agent: the uniform controls only; no bias test on a candidate at w = 32 |
| Mathematics | not staffed: the agent's structural tools ran, but no person analysed the state space |
| Cryptanalysis | not staffed: the trail-bound searches are tool runs, not cryptanalysis by a cryptanalyst |
| Hardware | not staffed: no RTL in this feature |
| Independent reviewer | not staffed (security.md §14); no AI session is recorded as one |
| Evidence auditor | partly: `scripts/recheck_004.py` and `scripts/check_claims.py`, written by the same agent |

From 2026-11-09 the owner gave the agent standing approval for the remaining steps; the agent then
set the row "Selection tie" to Not needed and committed the Phase 9 files, each commit saying so.
The Final result review stays the owner's (T127).

## 10. Findings by class, and the kinds of statement kept apart

**Findings by class** (FR-060; computed by code from each record's kind and outcome, over the 307
records of `reports/004-crypto-architecture-v3/`):

- **Confirmed vulnerability**: 1, of `phyco-v2`: its seed caps it at 64 bits, and the exhaustive
  seed search of FUT-SEC-1's threat ran to completion on a reduced domain, 2³² candidates for each
  of three development targets (demonstration-20261104T165604Z-4406adb9).
- **No weakness identified within the analysis performed**: 87 bound records, 70 of A1 and 17 of
  B1, each limited to its scope: single trails under the usual independence assumptions, over the
  rounds and at the size and width it states.
- **No finding** (`none`): the other 219 records, the 6 uniform controls among them, none of which
  fired, and 3 capped searches, `inconclusive`.
- No strong theoretical concern and no unverified hypothesis was recorded.

**Kinds of statement kept apart** (FR-062):

- *Demonstrated facts*: the seed-bound demonstration; the tool validations; the bound records and
  their weights; the candidate log's decisions; the stop.
- *Mathematical arguments*: the long-trail argument that a chain of t box calls costs at least t
  times one call (seq 524), on which every active-box count rests.
- *Experimental observations*: the run times that shaped the budgets; A1's 16×16 count at r = 5,
  where the solver's first run found 124 before the run that confirms it reached the cap.
- *Unverified hypotheses*: none recorded. The agent's assessments of B2 and A2 ("likely to end as
  the candidate it replaces") are predictions, not findings, and no design was tested on them.
- *Unsuccessful attacks*: none; no attack was run on a candidate.
- *Untested areas*: every structural and bias test of a candidate at w = 32; clustering into
  differentials and linear hulls; key-dependent effects; every hardware question.
- *Residual risks*: the gap between single-trail bounds and bounds on differentials and linear
  hulls, for feature 005 (FR-034); the risks of section 11.

**The nine reports of security.md §17.3**: this feature contributes to report 1 (algorithm
specification and change history: the spec, `design.md` at Version 0.4 and the candidate log), 2
(threat model and security requirements: the chapter "Security target"), 3 (mathematical and
state-space analysis: the bound records) and 6 (cryptanalysis and attacks: FUT-SEC-8's
demonstration). Reports 4 (reference implementation verification), 5 (statistical testing), 7
(hardware verification), 8 (independent review) and 9 (security assessment and qualification
decision) are not started.

## 11. Risks as they stand

- **The strategy note's §11**: most new symmetric designs are broken or never reviewed, and public
  review takes years; a FIPS 140-3 validation stays out of reach and the outcome of an AIS
  20/31-style assessment of a custom generator is uncertain (FUT-SEC-9); the programme needs
  cryptographers, which an AI assistant cannot replace (security.md §2.1, §16). The note names
  Option C, stopping with a documented research generator, as an honest result, and this feature
  reached it.
- **Selection among up to six candidates on development inputs**: two candidates were analysed
  and none was selected, so no selection bias enters any result.
- **The chance of a false raise of R**: the bias rule ran on no candidate at w = 32, so it raised
  no R; the plan's figures (about 21% at R = 32 with one stream, research R4) stand for any later
  attempt.
- **The common-mode caveat**: no model and no second transcription exist, so no agreement between
  them is reported. One agent wrote the tools, the candidates and the checks; the checks' agreement
  with the tools is that agent's agreement with itself (security.md §10.2).
- **The stop itself**: the trail models at 16×16 were the hardest part, as the plan's risk
  "Stop" foresaw. Both families met the limit of the tools within the 8 h per search instance:
  B1 through its row's reserve for the searches still to come, A1 through the solver's time at
  16×16. A later attempt would need either a design whose bounds rise faster per round at 16×16 or
  a protocol, fixed before any result, that reaches 16×16 another way.

## 12. Change-completion items still open

Of the constitution's list, items 1, 3, 4, 5 and 6 apply to a change of generator behaviour, and
the stop made none: no `phyco-v3` model exists, and `phyco-v2` was archived unchanged (item 2,
FR-042). Item 7 holds for this feature's own requirements (section 4). For any later successor the
statistical evaluation stays open for feature 007, and the RTL for feature 006.

## 13. Tests run in Phase 9, with exact commands

T125, the whole suite, `python -X utf8 -W ignore -m unittest discover -s tests -t .`, projected
first at 1.5 h in research R7's feature-wide row, charging no candidate
(projection-20261109T130332Z-95d26c03), with no other heavy run going:

- Windows, Python 3.10.11, first run at aad0dc3: 1925 tests, 71 skipped, 2 failed, 1449.2 s. Both
  failures were tests that only a run with other test modules exposes (section 14); 85ba667 fixed
  them, no expected value changed.
- Windows, at bd47734 after the fixes: 1925 tests OK, 71 skipped, 1432.4 s.
- WSL with wpy, Python 3.14.4, at bd47734, verbose: 1925 tests OK, 8 skipped, 631.7 s.
- Every skip names its reason. In both runs, 4 wait for T107, 1 waits for plan phase 6, and 3
  are feature 002's SP 800-22 harness notes; on Windows the other 63 need a tool, binary or build
  that runs in WSL only, and run there. None fails.
- FR-053's two-worker test ran in each run under the heavy-run lock and wrote its two projection
  records each time, committed with these results.

Phase 9's other runs:

- T124, `python -X utf8 scripts/recheck_004.py` in a fresh clone of 23c5520 on Windows:
  recheck-20261109T130121Z-cc622313, 160 records and the candidate log's 4 decision and closing
  entries recomputed, 0 disagreements. A first attempt, in a clone under a longer path, stopped with
  exit 3 before any check, its worktrees past Windows' 260-character path limit; the second clone
  set `core.longpaths` for itself alone.
- T123, over the final documents, this report among them: `python -X utf8 scripts/check_claims.py`,
  0 findings on Windows and in WSL, listing the two allow-list entries added since the last gate
  (section 14); `python -X utf8 -W ignore -m unittest tests.test_claims`, 83 tests OK on Windows (49.8 s) and in WSL (26.6 s).

At the end of Phase 5 (2026-11-09):

- `python -X utf8 -W ignore -m unittest tests.test_protocol_004`: 745 tests OK on Windows, 2
  skipped (the two ARX-search tests that need the WSL binary), 590.6 s; 745 OK in WSL, 130.4 s.
- `python -X utf8 -W ignore -m unittest tests.test_costmodel` and `tests.test_refused_sources`: 35
  and 49 OK on both platforms.

Throughout the feature, `python -X utf8 scripts/check_claims.py` ran before every commit, 0
findings each time it gated one; section 14 names the two commits, c8a30d9 and de66393, that went
through without it holding.

## 14. Open issues and disclosures

- **Open tasks**: T086 (the re-check's `trail` branch: no `trail` record exists, since no tool
  searched Π itself, every bound method used giving a bound); T092 (the structural and bias runs of
  a candidate at w = 32, never made); T095 to T120 (Phases 6 to 8, which need a selected
  candidate); T127, the owner's Final result review.
- **Two allow-list entries wait for the next gate**, T127: the claims check lists them at each run as
  entries added since the last gate's approval. One passes the design document's sentence that the
  property FUT-SEC-4's reseeding serves is not sought (D7); the other passes research R9's line on
  the mode's theorems, a line that a rewrap moved. Each holds its reason in `protocol/claims.json`,
  and the owner's decision at T127 covers them.
- **Feature 005's inputs** (FR-066): no model ID version, design version, threat-model rows of a
  frozen design or structural facts exist to hand on. Feature 005, if it runs, starts from the
  spec, the candidates' records and this report.
- **Two tests that failed only when run with others**, both since 2026-11-05: the evidence tool's
  code-list test read every module of the test process, so it failed naming modules other tests
  had loaded (the cost model within its own module, from 858799a; `phycoweb/model.py` in the whole
  suite), though the evidence tool imports neither; and a test of the uniform controls called the
  derivation `state` outside the module's own tests, which the derivation guard forbids (from
  90ec2b8). The first was found at the end of Phase 5 and narrowed in 48340cd, too narrowly, as
  T125's first whole-suite run showed; both were fixed in 85ba667, the code-list test reading a
  fresh interpreter's modules and the control test moving to `tests/test_devinputs_v3.py`. No
  expected value changed.
- **The claim register's miss**: c8a30d9 wrote the first counted bound without the register's
  in-progress entry, and de66393 went through with that one finding because the agent's guard read
  the check through `tail`; 2520d9d wrote the entry, and the guard now tests the last line exactly.
- **A slip in a commit message**: 0b995a1 said every w = 8 search stood at r = 23; only one did, and
  a8f2e46's message corrects it.
- **Runs the agent disturbed or mis-sized**: B1's first probes overran R7's minute; a correction of
  the reservation (32.9 h to 15.6 h) is what let B1 continue; the agent's edit stopped the climb
  driver once, and 3983d47 was committed by hand; the tiny controls' projections read 0.000 h, the
  Windows clock's tick; seq 524's `results_known` lists more than earlier entries did.
- **B1's refusal at r = 5** rested on conservative projections plus 15.256 h held for later probes;
  its r = 4 searches each projected 8 h and took 7 and 40 minutes. The conclusion stands, since
  B1's bounds grew 8 per round and needed about r = 17.
- **The cause cited for both decisions** is "eligibility item": the check behind "spent budget"
  reads the row without its reservations. Both round-rule records also fail the items whose runs
  were never made at w = 32.
- **The replacements**: the agent proposed B2 and A2 and recommended declining its own proposals;
  the log records the proposals, the assessments and the owner's words.
- **The time the work waited**: some hours passed while questions waited for the owner.
- **Housekeeping**: about 11,700 temporary `phyco004-*` folders from test runs remain in the
  system's temporary directory, not deleted.

## 15. Security concerns

None new. No candidate became eligible, no model exists, and nothing in this feature supports any
claim. `phyco-v2`'s seed bound, confirmed here, keeps every released model at L0 with no claim, and
`phyco-v3` stays at L0 with no claim. As FR-052 asks, this report states that, with FUT-SEC-7
(feature 007) and FUT-SEC-5's analysis (feature 005) open and the claim levels two to five of
security.md §15 not reached (features 005 to 009), no claim, evaluation or certification may follow
from this feature. The levels are written out in words here, where FR-052 gives their short names,
because the claim test reads a short name above a model's register level as a claim.

## 16. Recommendation

**Stop.** The rules stopped the selection, and the agent recommends recording the stop rather than
entering a third candidate per family: both families met the same limit, the cost of bounding
trails at 16×16 within the per-search cap, which a replacement design cannot change. Feature 005
should not start on this feature's results, since there is no design for it to attack. Any later
attempt should start with a new specification, whose protocol is fixed before any result and plans
the 16×16 bounds from the start.

The owner's commit that records the Final result review (T127) ends FR-043's window, the stop
ending it at that same commit.

This feature makes no security claim. No PhycoWeb-PRNG model, `phyco-v3` included, may be used to
generate secrets; use an established cryptographic random-number generator for keys, nonces,
tokens and salts. Passing statistical tests does not show cryptographic security.
