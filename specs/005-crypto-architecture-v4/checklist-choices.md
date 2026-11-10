# Checklist Choices: Cryptographic Architecture, Second Design Round (phyco-v4)

> This feature makes no security claim. No PhycoWeb-PRNG model, `phyco-v4` included, may be used
> to generate secrets; use an established cryptographic random-number generator for keys,
> nonces, tokens and salts. Passing statistical tests does not show cryptographic security.

Each open item of the six `/speckit-checklist` checklists gets a row: the question in short, option A (recommended), the
alternatives and where the change goes. Item IDs are the checklist's prefix and number: SEC (security), RAT (design
rationale), ANA (analysis), PRO (protocol), HW (hardware) and REP (reproducibility).

**How to answer.** After the spec approval (b1b79d8) and the plan approval (afc6769) the protocol may only become
stricter (inherited FR-044; FR-009): a change that touches a protocol rule must, under every reading of the old text, lie in
its rule's stricter direction or settle an open case by its most conservative reading; one that sets aside a reading of
the old text is marked `set_aside` and decided in the row "Readings set aside" at the tasks approval. Each round's list
"Rows that change the protocol" names those rows with their direction; every other row clarifies text and changes no rule.

## Round 1 (first run, 2026-11-09)

**Answered in advance**: on 2026-11-09 the owner gave the instruction to loop the checklists until a re-run finds no new
item, "you have my approval of all suggestions to continue without human interaction", which takes option A of every row.

### Security (SEC)

| Item | Question | A (recommended) | Alternatives | Where |
|------|----------|-----------------|--------------|-------|
| SEC-001 | `phyco-v4`'s key entropy, reachable state and bound in the spec's own words | Add to FR-010: a 256-bit key, the reachable secret state the 384-bit capacity at every claimable size, and the size profile's bound of 128 bits as a target, a ceiling and not a claim | B: leave it to FR-001's reading. C: restate feature 004's whole parameter table | spec FR-010 |
| SEC-002 | R among FR-012's candidate-dependent items | Add the round counts `<R4>`, `<R8>`, `<R16>` and every figure computed from R to FR-012's list | B: review the chapters only after R is known. C: no change | spec FR-012 |
| SEC-003 | The security target's files before R exists | The files are written before the review with R as `<R4>`, `<R8>` and `<R16>`, named by the row; written again once every R is known and reviewed in "Security-target review 2" | B: the row names the chapters only. C: postpone the files' naming to the owner design review | spec FR-011, FR-012; research R8 |
| SEC-004 | The register's `fut_sec` for `phyco-v4` | `phyco-v4`'s entry gains `fut_sec`, the expected statuses of the traceability table, written with the claim test's extension in plan phase 1 | B: added at the freeze. C: no field | spec FR-030; plan phase 1 |
| SEC-005 | The disclaimer's exact text | Fix it word for word in FR-026: feature 004's text with `phyco-v4` for `phyco-v3`, held in `protocol/disclaimer.py` as feature 005's constant | B: refer to feature 004's constant. C: no change | spec FR-026 |
| SEC-006 | T6 to T11 for `phyco-v4` in security.md §5 | FR-027 also asks §5's note on T11 to name `phyco-v4` beside `phyco-v3`; security.md 2.19 makes it | B: leave §5 to feature 004. C: restate T1 to T11 in this spec | spec FR-027; security.md §5 |
| SEC-007 | L1 while R is a placeholder, and after | State in FR-013: L1 rests on the chapters as reviewed; once R fills them, the named hashes no longer match and the level reads L0 until "Security-target review 2" and "L1 recorded 2" | B: record L1 only after R is known. C: no change | spec FR-013 |
| SEC-008 | Reading feature 004's FUT-SEC-8 row | FR-013 names the row as feature 004's table's, read by the claim test from that spec at HEAD | B: copy the row into this table. C: no change | spec FR-013; research R10 |
| SEC-009 | Feature numbers in the inherited text | FR-001 reads feature 005 to 009 of the inherited text as the stages of security.md §22 rows 5a.2 to 5a.6, now features 006 to 010 | B: replace the numbers in a copy of the text. C: no change | spec FR-001 |
| SEC-010 | FR-020's `none` against feature 004's row | FR-020 states that it replaces feature 004's data-model row for trails, and that a trail at or below 2⁻¹²⁸ is no finding under security.md §9.1 | B: class it `no weakness identified`. C: keep feature 004's row | spec FR-020; data-model §3 |
| SEC-011 | security.md §1.1's cells for `phyco-v4` | FR-027 gives the cells: a 256-bit key and a 128-bit nonce as targets, the state "not specified until the selection"; security.md 2.19 writes them | B: keep "not specified yet". C: fill them at the freeze only | spec FR-027; security.md §1.1 |
| SEC-012 | The claim test before "L1 recorded" | FR-013: "L1 recorded" is set only after the claim test covers `phyco-v4` (plan phase 1 before phase 3) | B: let the agent hold the register at L0 by hand. C: no change | spec FR-013, FR-026 |
| SEC-013 | An open item that fails at the owner design review | FR-012: the candidate fails its eligibility item as inherited; L1 stays while the reviewed chapters do not change; a change to the target is reviewed again, with "L1 recorded <k>" | B: L1 withdrawn at once. C: no change | spec FR-012 |
| SEC-014 | Documents written before the claim test covers them | FR-026: once the extension lands, it scans every document of this feature written before it, checklists and choices included, each finding fixed or allow-listed before the next step | B: rely on the agent's own scans. C: no change | spec FR-026 |
| SEC-015 | The scope statements of sums | FR-016 requires feature 004's scope statement word for word in every `split` record | B: a shorter scope. C: no change | spec FR-016 |
| SEC-016 | Bound wording in reports | FR-024 and FR-029: the statement, the table and the report keep to bound wording and state no property of any design, under the claim test's rules | B: no rule. C: a review of the wording by the owner | spec FR-024, FR-029 |

### Design rationale (RAT)

| Item | Question | A (recommended) | Alternatives | Where |
|------|----------|-----------------|--------------|-------|
| RAT-001 | Constants of a re-entered design | FR-023: the inherited rule gives an unchanged design at an unchanged variant feature 004's constants exactly, the rule holding no ID; research R13 corrected | B: seed the rule with the model ID (a new rule). C: no change | spec FR-023; research R13 |
| RAT-002 | How each R_bound was reached | FR-025: the design document and `rationale.md` state each R_bound's route per size and kind: the searched records up to the first cap, then the `split` records and their parts | B: the final report only. C: no change | spec FR-025, FR-029 |
| RAT-003 | The design document's version | FR-010: Version 0.5, continuing feature 004's numbering, each later change a new version | B: start at 0.1. C: no change | spec FR-010 |
| RAT-004 | The reason for R_max | D5 and FR-017: R_max = 64 bounds R at R_max + Δ = 66, which fixes the largest constant table, vector length and cost figure the tools hold | B: R_max = 32. C: no reason | spec D5, FR-017 |
| RAT-005 | Which of feature 004's rows FR-001 reads | FR-001: the gate families and their reading rules; rows that record feature 004's own past acts are not this spec's | B: every row. C: no change | spec FR-001 |
| RAT-006 | What "derived from" covers | FR-023: an unchanged operation list or one changed as a variant or a fix in the inherited sense; a structural change makes a new design that still names its starting point in `derived_from`, with the change listed | B: unchanged lists only. C: no change | spec FR-023; data-model §5 |
| RAT-007 | The selection-bias statement's effect | FR-024: it reports and changes no threshold, rule or decision | B: it scales the bias rule's threshold. C: no change | spec FR-024 |
| RAT-008 | FUT-GRID-5 against 16×16 first | FR-014: FUT-GRID-5's order governs vectors and statistical evaluation per size, which keep 4×4 first; trail bounds analyse the permutation and run where the cost is highest first | B: run bounds at 4×4 first. C: no change | spec FR-014 |
| RAT-009 | D14 against the projections | Keep D14 and record the reason in D14's note: under FR-018 a family that cannot be bounded at 16×16 ends at its first searches there, so the fallback reaches the other family at that cost; the projections are planning data and change no rule | B: analyse both families in score order (D14's alternative, a change of rule). C: no change | spec D14 |
| RAT-010 | `v4-` IDs in the claim test | FR-026: the extension adds `v4-A<k>` and `v4-B<k>` to the model words | B: rename the candidates `cand-`. C: no change | spec FR-026 |
| RAT-011 | Sums beside searched bounds in documents | FR-025: the design document and the review package mark each bound searched or `split`, with its parts | B: the records only. C: no change | spec FR-025 |
| RAT-012 | D4 with a re-entered design | FR-023: D4 scores a re-entered design here like any other; feature 004's D4 record is cited as a prior result only | B: reuse feature 004's scores. C: no change | spec FR-023 |
| RAT-013 | The inherited design rules for `phyco-v4` | FR-001 lists them: the torus, two lanes, neighbour-only data flow, the operation list, the replaced mechanisms and the mapping chapter's one sentence | B: leave them implied. C: no change | spec FR-001 |

### Analysis (ANA)

| Item | Question | A (recommended) | Alternatives | Where |
|------|----------|-----------------|--------------|-------|
| ANA-001 | The condition a sum rests on | FR-016: each part bounds every trail over any span of its length, the round structure repeating from round to round or, for layers in turn, whole cycles; a design whose rounds differ beyond their constants takes no sum | B: sums only of spans from round 1. C: no change | spec FR-016 |
| ANA-002 | "Established bound" | FR-016 defines it: a searched bound of status `pass` from a validated tool that passed its cross-check on the candidate, or a `split` record whose parts are established; never a capped, refused or blocked record | B: any `pass` record. C: no change | spec FR-016 |
| ANA-003 | The cap of a size-independent search | FR-015: a search that does not depend on the size, such as an ARX box over one call, runs first, under the 4×4 cap, charged to the trail row, its bound read at every size | B: under the 16×16 cap. C: no change | spec FR-015 |
| ANA-004 | The class of "no R_bound at 16×16" | FR-018: the candidate's own cause, a replacement possible, unless the cause is a row that cannot hold the run at its recorded need, shared as inherited | B: always shared. C: no change | spec FR-018 |
| ANA-005 | "Nonlinear operation" | FR-019: one modular addition or subtraction on w-bit words, or one S-box applied to its input bits; an S-box layer is recorded S-box by S-box | B: per layer. C: no change | spec FR-019; data-model §3 |
| ANA-006 | Exact weights | FR-020: the exact differential probability and squared correlation of a two-input addition or subtraction modulo 2^w and an S-box's table entry; masks pass linear steps through the transpose; an operation list holding any other nonlinear operation gets no trail record until data-model §3 defines its weight | B: name formulas only. C: no change | spec FR-020; data-model §3 |
| ANA-007 | The moment of the 16×16 decision | FR-018: as soon as either kind's established bounds at 16×16 cannot pass weight 128 by R_max; a search of the other kind then running stops, its record `inconclusive`, its hours charged | B: after both kinds end. C: no change | spec FR-018 |
| ANA-008 | Sums across methods | FR-016: allowed, each part established, of the same candidate, kind, size and width | B: one method per sum. C: no change | spec FR-016 |
| ANA-009 | r = 1 for ARX designs | FR-015 reads r = 1 as the box's bound over one call for an ARX design, run first by ANA-003's rule | B: an active-box count at r = 1 at each size. C: no change | spec FR-015 |
| ANA-010 | Calibration per kind and per tool | FR-004: per kind of evidence, and for bound searches per tool and size, with research R1's transfer rule | B: per kind only. C: no change | spec FR-004 |
| ANA-011 | `split` records in the eligibility items | FR-016: a `split` record is a bound record for every inherited eligibility item | B: list the items one by one. C: no change | spec FR-016 |
| ANA-012 | A probe's outputs | FR-005: a probe's outputs other than its timing are discarded unread | B: kept as prior results. C: no change | spec FR-005 |
| ANA-013 | R from sums | FR-017: R_bound, once the climb sets it, is not lowered by any later search; R follows the round rule | B: a later search may lower it before the freeze. C: no change | spec FR-017 |
| ANA-014 | The weakest route | FR-029: the report states each R_bound's route, one resting on r·W(1) alone named as such | B: no special mention. C: no change | spec FR-029 |
| ANA-015 | D4 before the climbs | FR-022: every reduced-width score of D4 comes before the first production-width search; the 16×16-first order is the production width's | B: D4 after the 16×16 climbs. C: no change | spec FR-022 |
| ANA-016 | SC-003 from records | data-model §2: the round-rule record names, per size and kind, the last searched record and the r of the first cap or refusal | B: the candidate log only. C: no change | data-model §2 |
| ANA-017 | The table's rows measurable | Already holds: data-model §4 and the contract write each row's plan value, the value that holds and its source; no change | — | — |

### Protocol (PRO)

| Item | Question | A (recommended) | Alternatives | Where |
|------|----------|-----------------|--------------|-------|
| PRO-001 | Recording changes after the approvals | New FR-031: each change listed with its direction in this file's lists and entered in feature 005's protocol change log after its first entry, before any result; a reading set aside decided in "Readings set aside" | B: the commit messages only. C: no change | spec FR-031 |
| PRO-002 | Rows the table needs | Add the rows "Checklist choices, round 1", "Readings set aside", "Place check" and "Tool acquisition", each with its rule | B: add each when first needed. C: no change | spec Review & Approval |
| PRO-003 | When the change log is created | FR-031: in plan phase 1, after the tasks approval and before any evidence run, its first entry naming the baseline documents and `plan-projections.json` | B: at the spec approval. C: no change | spec FR-031 |
| PRO-004 | Feature 004's re-check under the setting | FR-003: the feature setting leaves feature 004's verdicts unchanged, its re-check at HEAD giving the same result before and after, a test showing it | B: a note only. C: no change | spec FR-003 |
| PRO-005 | The stricter-only standard | The section "Pre-registered Design Protocol: the changed rules" states it as this file's "How to answer" does | B: refer to feature 004's text. C: no change | spec changed rules |
| PRO-006 | A clarification of the calibration | FR-009: a clarification of the calibration's rule that leaves every factor as computed is no change | B: any wording change is a change. C: no change | spec FR-009 |
| PRO-007 | The probes' conditions | FR-005: after plan phase 1's environment records and protocol change log, before the first `proposed` entry; the probes and the security-target review in either order | B: probes after the review. C: no change | spec FR-005 |
| PRO-008 | "The budget allows" with rows per family | FR-022: a replacement takes its family's row, allowed while that row holds the recorded need of each run the rules require at every size | B: the larger row. C: no change | spec FR-022 |
| PRO-009 | The ceiling in the spec's text | D7's row, FR-008 and the Context's table name 720 h as D7's default and 2,200 h as the ceiling the owner set at the plan approval | B: replace 720 h everywhere. C: no change | spec D7, FR-008, Context |
| PRO-010 | FR-011 and the contract's guards | FR-011 adds the projection table's existence to the candidate log's guard, as the contract has it | B: drop it from the contract. C: no change | spec FR-011 |
| PRO-011 | The margin's direction | The changed rules: "the margin only rises", as the plan says | B: the margin fixed. C: no change | spec changed rules |
| PRO-012 | Option E before the approval | FR-009: the plan approval fixed the values of option E, which the owner chose before the approval was recorded | B: no mention. C: no change | spec FR-009 |
| PRO-013 | Probes beyond their share | FR-005: a probe that would take the probes past their 40 h is refused, and its run keeps the plan's projection | B: charge the rest of the feature-wide row. C: no change | spec FR-005; research R5 |
| PRO-014 | The owner's commits in FR-043's window | The notes under the table: inside FR-043's window, the owner's written word, recorded and committed by the agent quoting it, stands in place of the owner's commit, as in feature 004 from 2026-11-05 | B: the owner commits by hand. C: no change | spec Review & Approval notes |
| PRO-015 | A probe above its row | FR-009: reported before the first `proposed` entry; the owner may then lower the candidate limit or take D13's alternative, each stricter, and no row is raised | B: the run refused when it comes, unreported. C: no change | spec FR-009 |

### Hardware (HW)

| Item | Question | A (recommended) | Alternatives | Where |
|------|----------|-----------------|--------------|-------|
| HW-001 | FUT-GRID and FUT-HW traced | FR-030 also carries FUT-GRID-1 to FUT-GRID-5 and FUT-HW-1 to FUT-HW-5, as feature 004's table did | B: FUT-GRID only. C: no change | spec FR-030 |
| HW-002 | Throughput figures at any R | FR-022: feature 004's FR-026 figures and the 10⁸ words/s goal reported for each candidate at its R, up to R_max + Δ | B: at the selected candidate only. C: no change | spec FR-022 |
| HW-003 | The constants' ROM as R grows | FR-022: the ROM's size per food node reported with those figures | B: a limit on the ROM. C: no change | spec FR-022 |
| HW-004 | The goal decides nothing | FR-022: a candidate whose R puts the goal out of reach stays eligible | B: an eligibility item. C: no change | spec FR-022 |
| HW-005 | The other supported sizes | FR-001: 5×5 to 7×7 and 9×9 to 15×15 are supported variants, permutation-only and outside every claim, as feature 004's variant table lists them | B: research variants. C: no change | spec FR-001 |
| HW-006 | FUT-GRID-3 against FR-012 | FR-012: the instantiation margin item reads the same dependency measurement as FUT-GRID-3's warm-up | B: separate measurements. C: no change | spec FR-012 |
| HW-007 | 16×16 first against the hardware order | FR-014 states the two orders govern different work (RAT-008) | B: one order. C: no change | spec FR-014 |
| HW-008 | Row 5a.3's cross-reference | security.md 2.19: row 5a.3 says "in features 004 and 005's order of sizes" | B: leave it. C: drop the reference | security.md §22 |
| HW-009 | A claimable size that does not fit | D13's note: such a size stays claimable, covered by the implementation feature's simulation alone (security.md §22 row 5a.5) | B: not claimable. C: no change | spec D13 |
| HW-010 | Hardware rules for every design | FR-023: a re-entered design meets every inherited hardware rule like any other | B: no statement. C: no change | spec FR-023 |
| HW-011 | The cost model unchanged | FR-022: D4's cost model scores this feature's candidates unchanged, its direction kept | B: re-fix it. C: no change | spec FR-022 |
| HW-012 | Hand-over to the RTL and board features | Context "Out of scope": the features of rows 5a.3 and 5a.5 (now 007 and 009) take the RTL and the board from this feature's design document | B: no statement. C: no change | spec Context |

### Reproducibility (REP)

| Item | Question | A (recommended) | Alternatives | Where |
|------|----------|-----------------|--------------|-------|
| REP-001 | FR-053's test writing under feature 004's paths | FR-003: once the feature setting exists, FR-053's test writes under the active feature's paths; before it exists, no whole-suite run is made for this feature | B: an exception for those records. C: no change | spec FR-003 |
| REP-002 | The setting in each record | data-model §1: every record holds the setting in its `config`, beside `feature` | B: `feature` only. C: no change | data-model §1 |
| REP-003 | Version copies | FR-001: the spec, research and design versions this feature's records cite are copied under its paths, read by the claim test as the documents they copy | B: cite by hash only. C: no change | spec FR-001 |
| REP-004 | The provenance log's start | FR-031: the provenance log starts in plan phase 1, its first entries covering the documents written before it | B: start at the tasks approval. C: no change | spec FR-031 |
| REP-005 | Line endings for later paths | `.gitattributes` gains `vectors/phyco-v4/** text eol=lf` now | B: before the first vector. C: no change | `.gitattributes` |
| REP-006 | Environment records | Assumptions: feature 005 writes environment records of its own, each with its row, even where the environment equals feature 004's records 3 and 4 | B: reuse feature 004's. C: no change | spec Assumptions |
| REP-007 | The kind of FR-001's hashes | FR-001: each SHA-256 is of the committed blob's bytes, LF, kind `raw` | B: canonical text. C: no change | spec FR-001 |
| REP-008 | Reproducing the projection table | FR-005: reproduced from its committed probe records and `plan-projections.json`, never by running the probes again | B: re-run the probes. C: no change | spec FR-005 |
| REP-009 | `--check` on both platforms | FR-004: `plan_projections.py --check` passes on both platforms | B: on Windows only. C: no change | spec FR-004 |
| REP-010 | `plan-projections.json` in the change log | FR-031: the first entry names it beside the baseline documents | B: the plan row only. C: no change | spec FR-031 |
| REP-011 | Sums and trails on a fresh clone | Already holds: SC-005 with data-model §2 and §3 (parts cited by ID and SHA-256, the characteristic in the record, the operation list committed); no change | — | — |
| REP-012 | `--check` when feature 004's records change | FR-004: the calibration reads feature 004's records as committed at 99e6994, so that a later record never changes it | B: read the working tree. C: no change | spec FR-004 |
| REP-013 | What a reproduction re-runs | FR-001: as inherited R16 lists them, with the probes and the projection table re-checked, not re-run | B: re-run everything. C: no change | spec FR-001 |

### Rows that change the protocol (round 1)

Written with the rows, before they are applied. Each is, under every reading of the old text, in its rule's stricter
direction (`stricter`) or settles an open case by its most conservative reading (`settled`); none sets aside a reading.

| Row | Rule | Direction | Why |
|-----|------|-----------|-----|
| SEC-003 | The security-target review (FR-011, FR-012) | settled | the old text named files that do not exist before R; writing them with placeholders and reviewing them again adds a review and removes none |
| SEC-012 | "L1 recorded" (FR-013) | stricter | a condition added before the row may be set |
| ANA-001 | Sums (FR-016) | stricter | sums only where every span is bounded, which no reading of the old text exceeds |
| ANA-002 | Established bounds (FR-016) | settled | the most conservative reading of "established" |
| ANA-003, ANA-009 | r = 1 and size-independent searches (FR-015) | settled | a cap where the old text named none, the smallest of the three |
| ANA-004 | The class of the 16×16 decision (FR-018) | settled | inherited ANA-078's classification applied as written |
| ANA-005, ANA-006 | Trail records (FR-019, FR-020) | stricter | no trail record where its weight is undefined |
| ANA-007 | The 16×16 decision (FR-018) | stricter | the decision comes no later than under any reading |
| ANA-008, ANA-011 | Sums across methods, `split` as bound records (FR-016) | settled | each part established, as the old text asked of every bound |
| ANA-013 | R_bound not lowered (FR-017) | stricter | R can only rise |
| ANA-015 | D4 before the climbs (FR-022) | settled | the inherited order kept |
| PRO-001, PRO-003, REP-004, REP-010 | The change log and provenance log (FR-031) | stricter | records added before any result |
| PRO-004, REP-001 | Feature 004's re-check and FR-053's records (FR-003) | stricter | a test added; whole-suite runs forbidden until the setting exists |
| PRO-007 | The probes' conditions (FR-005) | settled | the plan's phase order made a rule |
| PRO-008 | The budget for replacements (FR-022) | settled | a replacement takes its own family's row |
| PRO-010 | The candidate log's guard (FR-011) | stricter | a second condition before a `proposed` entry |
| PRO-011 | The margin (changed rules) | stricter | the margin only rises |
| PRO-013 | Probes beyond their share (FR-005) | stricter | such a probe refused |
| PRO-015 | A probe above its row (FR-009) | stricter | reported, and only stricter answers allowed |
| REP-012 | The calibration's inputs (FR-004) | settled | the records the plan read, fixed |

## Round 2 (first re-run, 2026-11-09)

**Answered in advance**, as round 1 was: the owner's instruction of 2026-11-09 takes option A of every row.

| Item | Question | A (recommended) | Alternatives | Where |
|------|----------|-----------------|--------------|-------|
| SEC-017 | FR-010's bound and its derivation | FR-010 states the bound as the least of feature 004's generic bounds: k/2 = 128 bits from single-target quantum search on the key, the capacity's c/2 being 192 bits | B: name the size profile only. C: no change | spec FR-010 |
| SEC-018 | FR-026's "next step" | The step is plan phase 2's probes, which wait until every finding is fixed or allow-listed | B: the row "L1 recorded". C: no change | spec FR-026 |
| SEC-019 | Generated checklist lines the claim test flags | FR-026: such a line is never rewritten; it gets an allow-list entry with its reason (it names a parameter, a file or a rule, and no property of a design) | B: rewrite the line. C: no change | spec FR-026 |
| SEC-020 | The security target's files with placeholders | FR-011: where a number will stand the files hold the strings `<R4>`, `<R8>` and `<R16>`, and the size profile's check reads a placeholder as not yet known, checking every other figure | B: no files before R. C: no change | spec FR-011 |
| RAT-014 | An unchanged re-entered design | FR-023: it is a candidate of this feature, its permutation and constants equal to feature 004's, and its design rationale says so; the inherited rule on new candidates governs changes within this feature | B: refuse unchanged re-entry. C: no change | spec FR-023 |
| RAT-015 | Selection over R from sums or searches | FR-022: the selection rule reads R as established, whatever its route, with no adjustment for a sum's weaker bound | B: an adjustment. C: no change | spec FR-022 |
| ANA-018 | Size-independent searches against 16×16 first | FR-014: a search that does not depend on the size runs before every size's climb | B: after the 16×16 climb. C: no change | spec FR-014 |
| ANA-019 | Their hours against FR-018 | FR-018: a size-independent search's hours count at no size; they are charged to the trail row before the 16×16 climb | B: count them at 4×4. C: no change | spec FR-018 |
| ANA-020 | R_bound between whole cycles | FR-016: for layers in turn the climb counts whole cycles, searches and sums at each whole number of cycles, and R_bound is the smallest such number of rounds whose bounds lie below 2⁻¹²⁸ | B: searches at every r, sums at whole cycles. C: no change | spec FR-016 |
| ANA-021 | Bitwise Boolean functions | FR-019: a bitwise Boolean function inside an invertible update (feature 004's four-update NOR network among them) is recorded as one S-box per bit position, its table the update's truth table over its input bits | B: no trail record for them. C: no change | spec FR-019 |
| ANA-022 | FR-004's records at 99e6994 and the script | FR-004: plan phase 1 changes `plan_projections.py` to read feature 004's records at 99e6994, its output unchanged, which `--check` shows; the records added since are FR-053's projections, which the calibration does not read | B: leave the script as approved. C: no change | spec FR-004; plan phase 1 |
| PRO-016 | Changes outside a checklist round | FR-031: such a change is listed in `checklist-choices.md` in a section of its own for its batch, with its direction, in place of "or beside the change" | B: in the commit message. C: no change | spec FR-031 |
| PRO-017 | Row families for later rounds | The notes: each later round has a row "Checklist choices, round <k>", and each batch of analysis-loop changes a row "Analysis remediation <k>", set by the agent on the owner's advance approval of 2026-11-09, quoting it | B: one row for every round. C: no change | spec Review & Approval notes |
| PRO-018 | When two rows read Not needed | "Readings set aside" reads Not needed at the tasks approval when no listed change sets a reading aside; "Place check" when every change was listed with its row before it was applied | B: keep them pending. C: no change | spec Review & Approval |
| PRO-019 | D13's alternative after the plan approval | FR-009: the owner may lower the candidate limit, a stricter change; D13's alternative removes an eligibility requirement, is not stricter, and is out of reach after the plan approval | B: allow it as a set-aside reading. C: no change | spec FR-009 |
| HW-013 | The other sizes | FR-001: every other n from 2 to 16 is for exploration only, as feature 004's FR-018 has it: a table written for that (n, w), never frozen and never evidence; keyed variants only at the claimable sizes, 2×2 and a supported 3×3 | B: keep "supported variants". C: no change | spec FR-001 |
| REP-014 | Round 1's row and its files | The row names `protocol/claims.json` beside security.md 2.19 | B: no change | spec Review & Approval |
| REP-015 | Provenance of shared files | FR-031: feature 005's provenance log also covers the files both features share (security.md, `protocol/claims.json`, `.gitattributes`, README) from their first change by this feature, feature 004's log keeping its last entries for them | B: shared files without provenance. C: no change | spec FR-031 |

### Rows that change the protocol (round 2)

Written with the rows, before they are applied; none sets a reading aside.

| Row | Rule | Direction | Why |
|-----|------|-----------|-----|
| SEC-018 | The claim test's first scan (FR-026) | stricter | a step waits on it |
| SEC-020 | The security target's files (FR-011) | settled | the form the old text left open |
| ANA-018, ANA-019 | Size-independent searches (FR-014, FR-018) | settled | their place and hours, which the old text left open |
| ANA-020 | Whole cycles (FR-016) | settled | R_bound only at whole cycles, the most conservative reading |
| ANA-021 | Bitwise Boolean functions (FR-019) | settled | recorded as the S-boxes the validated tool already counts |
| ANA-022 | The calibration's inputs (FR-004) | settled | the script follows the requirement, its output unchanged |
| PRO-016, REP-015 | Listing and provenance (FR-031) | stricter | records added |
| PRO-019 | Answers to a probe above its row (FR-009) | stricter | a loosening option removed |
| HW-013 | The other sizes (FR-001) | settled | the inherited text as written |
| RAT-015 | Selection (FR-022) | settled | the inherited rule unchanged |
