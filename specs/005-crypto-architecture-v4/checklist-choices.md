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

The round's two commits are 2808b55 (its choices) and aedcabd (its changes applied).

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

The round's two commits are 63f4003 (its choices) and 904185a (its changes applied).

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

## Round 3 (second re-run, 2026-11-09)

**Answered in advance**, as rounds 1 and 2 were: the owner's instruction of 2026-11-09 takes option A of every row.

| Item | Question | A (recommended) | Alternatives | Where |
|------|----------|-----------------|--------------|-------|
| SEC-021 | Cross-references in the chapters copied from Version 0.4 | FR-010: the copied chapters cite feature 004's requirements, decisions and research items as "feature 004's FR-<n>" (D-, R- alike) and name the later features by security.md §22's numbers (T2's and T11's deferrals to feature 006, T4's and its risk's to feature 009), each edit listed among the changes | B: keep the numbers as written, read under FR-001. C: no change | spec FR-010 |
| SEC-022 | The functionality class among the candidate-dependent items | FR-012 keeps it there and gives the reason: feature 004 was to close it at a security-target review held after its selection, with the selected design's records, and here it moves with those items to the owner design review; Version 0.4's "here at the security-target review" becomes one of FR-010's listed changes | B: close it at this feature's security-target review (a change of FR-012's list, which the changed rules do not allow). C: no change | spec FR-012 |
| SEC-023 | The papers and the AIS 20/31 proposal feature 004 fetched | FR-001: feature 004's downloads manifest and its files under `data/local/004/downloads/` are read as feature 004's, not under the path rule; each file is checked against that manifest's SHA-256 before it is read, `limits.json` cites feature 004's `fetched` entry by path and SHA-256, and a file missing on disk is fetched again only under a row "Download <n>" with the owner's permission | B: fetch every file again under this feature's manifest. C: no change | spec FR-001, FR-012 |
| SEC-024 | The guard on instantiation code | FR-030: the inherited guard reads feature 004's row "FUT-SEC-8 result review" (ffb1425) and its latest demonstration record at HEAD, from feature 004's spec and paths, as the claim test reads them (FR-013); this table adds no such row | B: copy the row into this table. C: no change | spec FR-030 |
| SEC-025 | The demonstration record's path and the register's evidence | FR-030 names it `reports/004-crypto-architecture-v3/fut-sec-8/demonstration-20261104T165604Z-4406adb9.json`, SHA-256 `5c93e850284120dc9935d3e4317b8dc94df3a7b79fc038dbc8a6c49508613651` (raw); FR-013: `phyco-v4`'s `evidence` lists it, with the files the two review rows name, while "L1 recorded" reads Approved | B: cite it by record ID only. C: no change | spec FR-030, FR-013 |
| SEC-026 | The register's `bound` and `evidence` while R is a placeholder | FR-011: from the commit that first commits the files, `bound` holds the profile's `bound_bits` by the variant IDs as the profile writes them, placeholders included, and `evidence` names both files; both are written again in the commit that writes R into the files (inherited FR-069 applied as written) | B: `bound` reads `none` while a placeholder remains. C: no change | spec FR-011 |
| SEC-027 | The numbers of "Security-target review 2" and "L1 recorded 2" | FR-012, FR-013 and research R8: the review of the chapters with every R filled in is the next row of its family, "Security-target review <k>", and its "L1 recorded <k>" follows, whatever number earlier reviews took | B: reserve the number 2 for it. C: no change | spec FR-012, FR-013; research R8 |
| SEC-028 | The later review and the owner design review | FR-012: the later review comes after the selection and before the owner design review, which waits for it; it reviews the round counts, the figures computed from them and the open items as the chapters then state them, and the owner design review checks the open items against the selected candidate's records: both | B: the owner design review alone checks the open items. C: no change | spec FR-012 |
| SEC-029 | `rationale.md`'s chapters "Security target" and "Mode" | FR-010: they start from feature 004's `rationale.md`, Version 0.4 (SHA-256 `01a6de45ae18e5dfb5fad070322dcfa908cb55e842ac2cbe1d5ebe5730ebbc32`), read and changed as the design document's chapters are, the two files sharing Version 0.5 (inherited FR-034); FR-011: the review's row names both documents' chapters with the files | B: the rationale's chapters after the selection. C: no change | spec FR-010, FR-011; research R8 |
| SEC-030 | The commits that record `phyco-v4`'s level | FR-013: each change of level is made in the commit that changes the rows or files it rests on, with the register's `claim_level` and `history`, security.md §1.1 and §15 and a security.md version with its history entry: when "L1 recorded <k>" reads Approved, and back to L0 in the commit that writes R into the reviewed chapters; FR-027 names these versions as a family | B: security.md follows at the next gate. C: no change | spec FR-013, FR-027 |
| SEC-031 | A parameter change at the security-target review | The edge case and FR-010: a change found needed there is made only in the stricter direction (a larger key, nonce or capacity, none below FR-010's), as a change to FR-010 listed under FR-031 before the review's approval, the output limits then recomputed; the changed rules gain "The security target's parameters: FR-010. Stricter means: the key, nonce and capacity only grow" | B: delete the edge case. C: no change | spec Edge Cases, FR-010, changed rules |
| SEC-032 | Roadmap row 5a.1b's status | FR-027: the row's status follows this feature's gates, each in a security.md version of its own, as 2.10 recorded feature 004's plan approval; security.md 2.20 records the plan approval and the checklist rounds | B: only at the end (inherited FR-051). C: no change | spec FR-027; security.md §22 (2.20) |
| SEC-033 | Feature numbers in the register | FR-030: `phyco-v4`'s `fut_sec` names the later stages by security.md §22's numbers since 2.18 (the analysis feature 006, the statistical re-validation feature 008); `phyco-v3`'s entry, feature 004's, stays as written and reads under FR-001's rule, as security.md §5's note on T11 reads feature 004's documents | B: rewrite `phyco-v3`'s entry. C: no change | spec FR-030 |
| SEC-034 | A trail on an operation the format cannot hold | FR-020: no trail search runs on an operation list holding a nonlinear operation outside FR-020's list until data-model §3 defines its weight; the candidate is `blocked` for that cause meanwhile, so no trail is left out of R_dist | B: record such a trail without a re-check. C: no change | spec FR-020 |
| SEC-035 | The projection table under the claim test | FR-024: the projection table holds numbers, record IDs and fixed field names and no prose; the wording rule binds the Markdown that renders it, the final report among them, which the claim test scans | B: extend the claim test to JSON records. C: no change | spec FR-024 |
| SEC-036 | A flagged generated line that names a property of a design | FR-026: it gets an allow-list entry like any flagged generated line, its reason stating that the line is a checklist question quoting the passage it asks about and stating nothing of its own; the owner reviews such entries at the next ⛔ gate, as inherited FR-069 has every entry added since the last gate reviewed | B: answer it by a new item replacing it. C: no change | spec FR-026 |
| SEC-037 | Allow-list entries against the reviewer's tick | FR-026: such an entry is written once the item's state is final, after its round's verification, naming the line as it then reads; a later change of state gets a new entry and the old one is removed in the same commit | B: phrase entries for the flagged words. C: no change | spec FR-026 |
| RAT-016 | Inherited and own requirement numbers | FR-001: a bare FR-<n> in this feature's documents is this spec's; an inherited requirement is cited as "inherited FR-<n>" or "feature 004's FR-<n>", and an inherited text's own FR-<n> reads as feature 004's; "changes it, by number" means that this spec names the inherited requirement it changes | B: renumber the inherited requirements. C: no change | spec FR-001 |
| RAT-017 | `derived_from` for a starting point | Data-model §5: `derived_from` gains `relation`, `derived` (unchanged, or changed only as a variant or a fix) or `starting point` (a structural change), and `changes`, the structural changes listed (`none` for `derived`); §6's table shows the relation | B: a field for derived designs only. C: no change | data-model §5, §6 |
| RAT-018 | The refused list and the constant rule | FR-023: this feature's candidates read the constant rule as research R15 fixed it at 99e6994 and a list `research/005/refused-constants.json` created in plan phase 1 as a byte copy of feature 004's (66 entries, SHA-256 `cdbcb8031d1de839dacd71abcabdec38869fa6b102c6e86f10cfea2eb52a8a95` at 99e6994), growing only by this feature's stricter changes; FR-031: the change log's first entry names feature 004's list by that SHA-256 | B: read feature 004's file in place. C: no change | spec FR-023, FR-031 |
| RAT-019 | The rotation amounts of a re-entered design | FR-023: an unchanged re-entered design keeps the amounts feature 004's ranking chose, part of its committed operation list; its rotation search is not run again, the ranking record cited as a prior result; a design whose amounts are searched again is a variant if they change (values its logged rules derive), entered with its own `derived_from` | B: run the search again for every re-entered design. C: no change | spec FR-023 |
| RAT-020 | Where a re-entered design's rationale says so | FR-023: its `proposed` entry states that its permutation and constants equal feature 004's, with `derived_from`; `rationale.md` says so for the selected candidate, and the selection-bias statement for each | B: `rationale.md` only. C: no change | spec FR-023 |
| RAT-021 | 3×3 among the exploration sizes | FR-001: every other n from 2 to 16 (5×5 to 7×7, 9×9 to 15×15, and 3×3 where the design document gives it no three-colour schedule) is for exploration only | B: list no sizes. C: no change | spec FR-001 |
| RAT-022 | D14's reason | D14's note: each candidate that cannot be bounded at 16×16 ends at its first searches there, its cause its own, so the family's replacements follow up to its limit of three evaluated candidates, each at that cost, before the fallback reaches the other family | B: drop the reason. C: no change | spec D14 |
| RAT-023 | The chapter that holds R_bound's routes | FR-025: the design document's chapter "Permutation", in a section "Round counts", and `rationale.md`'s chapter "Margin", each route citing its searched and `split` records by ID and SHA-256 | B: the review package only. C: no change | spec FR-025 |
| RAT-024 | The label of a `split` bound | FR-025: in `rationale.md` a searched bound and a `split` bound each carry the label "fact", citing the record, with the condition FR-016 asks of a sum stated beside the `split` bound as an "argument" | B: label a `split` bound "argument". C: no change | spec FR-025 |
| RAT-025 | The place of FR-010's list of changes | FR-010: the list stands in `rationale.md`'s chapters "Security target" and "Mode", each in a section "Changes from Version 0.4", so that the design document's header and chapters keep their fixed form | B: a chapter of its own in the design document. C: no change | spec FR-010 |
| RAT-026 | The count in the selection-bias statement | FR-024: every result of the frozen candidate is on development inputs chosen among up to eight evaluated candidates, feature 004's two and up to six of this feature's, beside the two declined proposals, so that feature 008's held-out evaluation is the unbiased test | B: count this feature's candidates only. C: no change | spec FR-024 |
| ANA-023 | An addition of a constant | FR-019, FR-020 and data-model §3: an addition or subtraction of a committed constant c is a nonlinear operation of its own, its exact weight the probability over the 2^w inputs that (x ⊕ α) ⊞ c = (x ⊞ c) ⊕ β, and the squared correlation of u·x ⊕ v·(x ⊞ c), each computed exactly by the carry's two-state automaton over the bits of c | B: no trail record for it. C: no change | spec FR-019, FR-020; data-model §3 |
| ANA-024 | The extent of a per-bit S-box | FR-019: the S-box is the function the validated tool counts: where updates in turn form one invertible map per bit position, that map (feature 004's four-update NOR network: one 4-bit S-box per position, table 9 c 3 0 2 5 4 7 6 1 a b 8 d e f), recorded before its first update and after its last; inside one update, its function F per bit position, its table F's truth table over the bits it reads, an addition or subtraction that follows F being its own operation | B: one S-box per update. C: no change | spec FR-019 |
| ANA-025 | Layers in turn and cycles | FR-016: a cycle is the shortest run of rounds after which the round structure repeats, constants aside: one round for feature 004's designs, whose layers in turn `active_sbox.py` takes as one round's `Cycle`; sums join spans of whole cycles starting at a cycle's first round; R_bound is the smallest whole number of cycles, counted in rounds, at which both kinds' bounds lie below 2⁻¹²⁸; R and Δ count rounds | B: rounds only, no cycles. C: no change | spec FR-016 |
| ANA-026 | A capped size-independent search | FR-015: it ends that kind's searches at every size; the candidate is then decided at 16×16 under FR-018, with no hour at 8×8 or 4×4 | B: it ends the 4×4 searches only. C: no change | spec FR-015 |
| ANA-027 | R12 and V6 against the box bound | Research R12 and the edge case read "a kind with no established bound at 16×16, its first search there capped or refused and no size-independent bound read there"; quickstart V6 uses a test list with no size-independent search | B: no change to R12, V6 naming its list. C: no change | research R12; spec Edge Cases; quickstart V6 |
| ANA-028 | The ceiling in `plan-projections.json` | `plan_projections.py` takes the ceiling per option (2,200 h for E, as the owner raised it; 720 h for the others), names `approved_option` E at the top level and moves `provisional_needs_h` and `feature_wide_needs_h` into each option; the file is written again, every other value unchanged, and named by its new SHA-256 in the change log's first entry (FR-031), the plan approval's hash standing as the record of what was approved | B: a note in the plan only. C: no change | `research/005/plan_projections.py`, `plan-projections.json`; data-model §4; spec FR-031 |
| ANA-029 | R2's table under option E | Research R2 gives option E's needs and projected R_bound, from `plan-projections.json`, option A's kept beside them | B: option A's only. C: no change | research R2 |
| ANA-030 | A non-search probe that does not finish | Research R5: it keeps the plan's provisional need for its kind (12 h structural, 24 h bias per candidate); only a probe that finishes lowers a need | B: the need becomes the probe limit times a factor. C: no change | research R5 |
| ANA-031 | "One structural check" | Research R5: one run of every structural kind that inherited FR-037 asks at that size (inverse tests, dependency matrices, symmetry and invariant checks), each kind's hours in the probe's record; a probe lowers the provisional need only by the kinds it covers | B: one kind per probe, named. C: no change | research R5 |
| ANA-032 | A search where sums already decide | FR-015: a kind's climb at a size ends at the first r at which its established bound, searched or summed, has weight above 128; where the sums already exceed it, no search of that kind runs at that r or beyond, as the listed climb has it | B: search at every r anyway. C: no change | spec FR-015 |
| ANA-033 | A `split` record's status | Data-model §2: `status` `pass` once both parts are established and the sum is computed, `validation` `none`; a `split` record is no counted trail-bound record of the register's `in_progress`, which counts searched `pass` records citing a validation, and is a bound record for the inherited eligibility items | B: a status of its own, `sum`. C: no change | data-model §2 |
| ANA-034 | Per-bit S-boxes in data-model §3 | Data-model §3 names the bitwise Boolean function's S-boxes as FR-019 does (ANA-024), and each operation entry gains `position`, the bit position or the S-box's index in its layer or update (`none` for an addition or subtraction), `op_index` naming the update or, for updates in turn, the first of them | B: one entry per update with the bits in a list. C: no change | data-model §3 |
| PRO-020 | Which changes FR-031 lists | FR-031: each row of a round is a listed change; the list "Rows that change the protocol" names those that touch a rule, with their direction, and every other row is a clarification, listed by its round's table alone; the change log takes each round's changes, citing the round's row | B: list every row with a direction. C: no change | spec FR-031 |
| PRO-021 | When "Place check" reads Not needed | The notes: the place check is made at the tasks approval, comparing every edit since the plan approval with the rows that made it, its file named by SHA-256 and each place that no row made listed for the owner; the row reads Not needed only where no edit was made since the plan approval | B: Not needed whenever every change was listed. C: no change | spec Review & Approval notes |
| PRO-022 | FR-009's answer to a probe above its row | FR-009: the owner may lower the candidate limit of the family whose row cannot hold the run, to zero where every candidate of it would need the run; D4 then scores the families that hold candidates, D14's fallback reaching no family at zero, and SC-001 reads over the rows that hold candidates; without such a change the run is refused when it comes, its cause shared | B: the report informs only. C: no change | spec FR-009, SC-001 |
| PRO-023 | The approved texts in the change log | FR-031: the first entry also names the spec as approved (a656bcf, `bb62fef653ad25665e6670333e9447d5bc26f7bd5b421fbcf26f28af35c31a11`) and the plan's documents at 74dd867 by SHA-256: plan.md `5f3300b82e9ad6fa1e3e7e64a58bbf3ecdd32a60abe3860f1c13dc54d081a873`, research.md `799896741ce4ecd1f06f51a191998ed493a65b437b89c3dfd5302cb7dc2fa33c`, data-model.md `77c23010cefab81959f75f78c37a414a9b64d2a035768d0367027d52b9c3327c`, contracts/cli.md `f295367ada174a3274adfcdc10e7f71997553547e4fbe3af9ea55b0234f29cba`, quickstart.md `6f6c4cac173ce20dccc2c049046d76eed1610e024368fa4ea00601092d87d01d` | B: the Review & Approval rows only. C: no change | spec FR-031 |
| PRO-024 | The candidate log's guard in three documents | FR-011 and data-model §5 agree with the contract: `propose` exits 2 while the security-target review's row does not read Approved at HEAD with the chapters' SHA-256 it names or while the projection table does not exist, for every `proposed` entry | B: the first entry only. C: no change | spec FR-011; data-model §5 |
| PRO-025 | Trail records' direction | The changed rules keep "Trail records: stricter means: no change"; round 1's ANA-005 and ANA-006 read `settled` (they settle what the old text left open, as ANA-021 does), and the plan's "fields only added" for FR-019's format covers only a settled case | B: change the rule to "fields only added". C: no change | spec changed rules; plan "Values this plan fixes"; this file's round 1 list |
| PRO-026 | Readings set aside after the tasks approval | FR-031: a change made after the tasks approval and before any result is made only in a form that sets no reading aside (for a claim-test finding, an allow-list entry), or waits for the owner's decision in a row "Readings set aside <k>" before any result it affects | B: no such change after the tasks approval. C: no change | spec FR-031 |
| PRO-027 | The probes and the security target in the plan | Plan Summary and phases: the probes (step 2) and the security target (step 3) run in either order, each after step 1 and both before step 4, as FR-005 has it | B: fix the plan's order in FR-005. C: no change | plan Summary, Plan Phases |
| HW-014 | What R_max bounds | D5, FR-017 and FR-022: R_max = 64 bounds R_bound + Δ at 66; the round rule's R, the largest of 2·R_dist, R_bound + Δ and 2·max(R_f, R_b), may exceed it, and the tools hold every R the rule gives, a table for a larger R generated and checked as inherited FR-023 asks of every rise; the figures and the ROM size are reported at R | B: a new eligibility item, R at most 66. C: no change | spec D5, FR-017, FR-022 |
| HW-015 | Row 5a.3's order of sizes | security.md 2.20: row 5a.3 reads "in the order of sizes that features 004 and 005 keep for vectors and statistical evaluation (FUT-GRID-5)" | B: drop the reference. C: no change | security.md §22 (2.20) |
| HW-016 | Figures for a candidate without R | FR-022: the figures and the ROM size are reported for each candidate at every size where it has R; a candidate decided `ineligible` at 16×16 has no `cost` record, its decision entry saying so | B: figures at R_max + Δ for it. C: no change | spec FR-022 |
| REP-016 | Runs under feature 004's paths | FR-003: no run of this feature writes under feature 004's paths: once the setting exists, the whole suite and every script run for this feature with `PHYCOWEB_FEATURE=005`; FR-003's test and quickstart V2 run `recheck_004.py --no-record`, which prints the result and writes nothing | B: an exception for those records. C: no change | spec FR-003; contracts/cli.md; quickstart V2 |
| REP-017 | Provenance of shared code | FR-031: feature 005's provenance log covers every file outside its own paths that this feature changes, the shared code and its tests among them (research R9), each from its first change, entered whole, as inherited FR-067 enters scripts and tests; the four files named are examples | B: the four files only. C: no change | spec FR-031 |
| REP-018 | The approved option for the projection table | `plan-projections.json` names `approved_option` (ANA-028), which `projection_table.py` reads (data-model §4) | B: the option named in the contract. C: no change | data-model §4; contracts/cli.md |
| REP-019 | Citations of feature 004's records | Data-model §4: each pair in `plan-projections.json` and each source in the projection table cites a feature-004 record by path and SHA-256 (raw) beside its record ID; `plan_projections.py` writes them | B: record IDs only. C: no change | data-model §4; `research/005/plan_projections.py` |
| REP-020 | Kinds of the new hashes | Data-model §2 and §4: each part's `sha256` and `plan_projections_sha256` are of the committed bytes, kind `raw`, with `sha256_kind` and `plan_projections_sha256_kind` beside them, as feature 004's records hold | B: no kind field. C: no change | data-model §2, §4 |

### Rows that change the protocol (round 3)

The round's two commits are 2cf3687 (its choices) and 936f586 (its changes applied).

Written with the rows, before they are applied; none sets a reading aside. Every other row clarifies text and changes no
rule. The round also reads round 1's ANA-005 and ANA-006 as `settled` (PRO-025).

| Row | Rule | Direction | Why |
|-----|------|-----------|-----|
| SEC-023 | Feature 004's downloads (FR-001, FR-012) | settled | the files the inherited rule reads, named; none loosened |
| SEC-024 | The guard on instantiation code (FR-030) | settled | the guard reads the row that exists; no instantiation code runs unguarded |
| SEC-025 | The register's evidence (FR-013, FR-030) | stricter | an evidence entry required |
| SEC-026, SEC-030 | The register's bound and level (FR-011, FR-013, FR-027) | settled | inherited FR-069 applied as written |
| SEC-027, SEC-028 | The later review (FR-012, FR-013) | settled | names fixed; both reviews check the open items, the most conservative reading |
| SEC-029 | The rationale's chapters (FR-010, FR-011) | settled | inherited FR-034 applied |
| SEC-031 | The security target's parameters (FR-010, Edge Cases) | stricter | a loosening option removed |
| SEC-034 | Trails on unlisted operations (FR-020) | stricter | no trail search where a weight is undefined |
| SEC-036, SEC-037 | Allow-list entries of generated lines (FR-026) | settled | the inherited allow-list rule applied |
| RAT-016, RAT-021 | Requirement numbers and the exploration sizes (FR-001) | settled | the reading rule stated; inherited FR-018 as written |
| RAT-017, ANA-033, ANA-034, REP-020 | Record formats (FR-016, FR-019, FR-023) | settled | fields only added |
| RAT-018, RAT-019 | The refused list and a re-entered design's amounts (FR-023, FR-031) | settled | feature 004's list read and only grown; the design unchanged, as the old text has it |
| RAT-026 | Selection bias (FR-024) | stricter | designs counted only added |
| ANA-023, ANA-024 | Additions of a constant and per-bit S-boxes (FR-019, FR-020) | settled | an exact weight where the old text gave none; the S-boxes the validated tool counts |
| ANA-025 | Cycles (FR-016) | settled | sums only over whole cycles |
| ANA-026, ANA-032 | The end of a kind's searches (FR-015) | settled | the most conservative reading: a capped size-independent search ends every size's; the listed climb's end applied to the climb |
| ANA-028, REP-018, REP-019 | The plan's data (FR-004, FR-005, FR-008) | settled | the file follows the approved values, every number unchanged |
| ANA-030, ANA-031 | Non-search probes (FR-005) | settled | a need lowered only by a finished run |
| PRO-020, PRO-025 | Listing changes and trail records' direction (FR-031, changed rules) | settled | the old text read as its lists had it; the strictest reading kept |
| PRO-021 | The place check (Review & Approval notes) | stricter | the comparison always made |
| PRO-022 | Answers to a probe above its row (FR-009) | settled | the stricter answer described |
| PRO-023, PRO-024 | The change log's first entry and the candidate log's guard (FR-031, FR-011) | stricter | more texts named; every proposal guarded |
| PRO-026 | Readings set aside after the tasks approval (FR-031) | stricter | no reading set aside without the owner |
| HW-014, HW-016 | R and the figures (D5, FR-017, FR-022) | settled | the round rule as written; figures only where R exists |
| REP-016, REP-017 | Runs under feature 004's paths and provenance (FR-003, FR-031) | stricter | no writes there; records added |

## Round 4 (third re-run, 2026-11-09)

**Answered in advance**, as rounds 1 to 3 were: the owner's instruction of 2026-11-09 takes option A of every row.

| Item | Question | A (recommended) | Alternatives | Where |
|------|----------|-----------------|--------------|-------|
| SEC-038 | The key and the nonce under a stricter change | FR-010, the edge case and the changed rules: the inherited rule gives a claimable size's key k = min(c, 256) bits and its nonce k/2, so the key and the nonce stay at 256 and 128 bits; the one parameter a stricter change may raise is the capacity, the rate falling and the output limits recomputed; the changed rules read "Stricter means: the capacity only grows; the key and the nonce do not change" | B: change the inherited rule to allow a larger key. C: no change | spec FR-010, Edge Cases, changed rules |
| SEC-039 | Row 5a.1b's status over later rounds | FR-027: the row names the gates passed and the next gate, never the checklist rounds; security.md 2.21 rewrites it so ("...; plan approved on 2026-11-09, with the run limits extended; tasks not started"), its history entry naming the change | B: update the row at every round. C: no change | spec FR-027; security.md §22 (2.21) |
| SEC-040 | The demonstration record as evidence | FR-013: the register's `evidence` for `phyco-v4` lists feature 004's demonstration record while the register gives `phyco-v4` the level those rows rest on, as inherited FR-069 has it, and drops it in the commit that returns the level to L0 | B: keep it while "L1 recorded" reads Approved. C: no change | spec FR-013 |
| RAT-027 | Re-entered designs and the rotation search | FR-023: the rotation ranking chose a design's amounts and is part of the design, not evidence about it: an unchanged re-entered design keeps feature 004's amounts, found at width 16, its ranking record cited as a prior result; where research R6's rule fixes this feature's D4 width at 8, inherited FR-024 searches its amounts again at 8, as for every entered candidate; amounts that come out otherwise make it a variant (`relation` `derived`), its permutation and constants no longer feature 004's; "every kind of evidence" reads "every kind of evidence about the design" | B: exclude re-entered designs from the search at 8. C: no change | spec FR-023 |
| RAT-028 | Values in the list of changes | FR-010: the sections "Changes from Version 0.4" name each change with its reason and cite each value by the design document's chapter and section, as inherited FR-034 has `rationale.md` cite every value | B: exempt the sections from the value rule. C: no change | spec FR-010 |
| RAT-029 | `relation` and `changes` on the command line | The contract: `candidate_log.py propose ID --derived-from PATH:SHA256 --relation derived\|starting-point [--changes TEXT]`, writing data-model §5's fields, `changes` reading `none` for `derived` | B: infer the relation from the operation lists. C: no change | contracts/cli.md |
| RAT-030 | A bare FR-053 | FR-004 reads "feature 004's FR-053 projections" | B: leave it, the context naming feature 004. C: no change | spec FR-004 |
| ANA-035 | Weights that read the constants | FR-019: a trail's weight follows from the characteristic, the committed operation list and, where it holds an addition of a committed constant, the committed constant table, named in the record by SHA-256; FR-016: a design holding such an addition takes no sum, its parts' bounds depending on the constants of the rounds they cover; inherited FR-023's "the trail bounds ... read no constant value" holds for designs without such additions, and a design with them covers each call type's permutation in its bounds, as in its other constant-dependent evidence | B: sums over spans with the same constants only. C: no change | spec FR-016, FR-019 |
| ANA-036 | Per-size probes against per-candidate needs | Research R5 and data-model §4: the provisional needs are split equally over the three claimable sizes (4 h structural and 8 h bias per size); a probe that finishes at a size gives that size its hours, a size whose probe did not finish keeps its share, and a candidate's need is the smaller of the provisional need and that sum | B: one probe result replaces the whole need. C: no change | research R5; data-model §4 |
| PRO-028 | The paragraph after FR-001's table | FR-001: a blank line separates the table from the paragraph that follows, so that the reading of the later features' numbers and of feature 004's Review & Approval rows stands as text | B: move the paragraph above the table. C: no change | spec FR-001 |
| PRO-029 | The place check's tool and commits | The notes: the comparison is made by `research/005/place_check.py`, feature 004's tool read for this feature's paths, written before the tasks approval as feature 004's was before its own (2392150), its file `research/005/place-check.json`; each list "Rows that change the protocol" names its round's two commits, the choices commit and the apply commit, rounds 1 to 3 gaining them now (2808b55 and aedcabd; 63f4003 and 904185a; 2cf3687 and 936f586) | B: a comparison by hand. C: no change | spec Review & Approval notes; this file's lists |
| PRO-030 | Approving a change after the tasks approval | The notes: a change made after the tasks approval and before any result is set in a row "Protocol change <k>" that the owner approves in writing, the agent recording the owner's words, before the change takes effect; a claim-test finding answered by an allow-list entry alone needs no row, the entry being reviewed at the next ⛔ gate as inherited FR-069 has it | B: the owner's advance approval of 2026-11-09 covers it. C: no change | spec Review & Approval notes, FR-031 |
| REP-021 | Feature 004's tests under the setting 005 | FR-003: each test that reads feature 004's committed records pins feature 004 for those reads, and every test that writes a record writes under the active feature's paths (FR-053's test among them), so that a whole-suite run with `PHYCOWEB_FEATURE=005` checks feature 004's records as before and writes nothing under its paths; plan phase 1's change makes the tests so | B: run the suite once per feature. C: no change | spec FR-003; plan "Testing" |
| REP-022 | The re-check test's before side | FR-003: the test compares feature 004's re-check at HEAD after the change, run with `--no-record`, with T132's committed record (`reports/004-crypto-architecture-v3/rechecks/recheck-20261110T010625Z-454c1890.json`, SHA-256 `d53424fb529ab2254825c107a2f066dab702f46e66c0ef176787b5d5f6526f21`: 160 records, 0 disagreements), the result before the change | B: run the old code in a worktree. C: no change | spec FR-003 |

### Rows that change the protocol (round 4)

The round's two commits are a8a7023 (its choices) and ea2e924 (its changes applied).

Written with the rows, before they are applied; none sets a reading aside. Every other row clarifies text and changes no
rule.

| Row | Rule | Direction | Why |
|-----|------|-----------|-----|
| SEC-038 | The security target's parameters (FR-010, changed rules) | stricter | the key and the nonce fixed; only the capacity may grow |
| SEC-040 | The register's evidence (FR-013) | settled | inherited FR-069 applied as written |
| RAT-027, RAT-029 | Re-entered designs and the candidate log's fields (FR-023) | settled | inherited FR-024 applied to every entered candidate; the command carries the fields data-model §5 added |
| ANA-035 | Constant-dependent weights (FR-016, FR-019) | stricter | no sum where a part's bound depends on its rounds' constants |
| ANA-036 | Non-search needs (FR-005) | settled | a need lowered only by finished runs, size by size |
| PRO-029, PRO-030 | The place check and changes after the tasks approval (notes, FR-031) | stricter | a tool and its commits fixed; an approval required |
| REP-021, REP-022 | Runs under the setting (FR-003) | stricter | no writes under feature 004's paths; the comparison fixed |

## Round 5 (fourth re-run, 2026-11-09)

**Answered in advance**, as rounds 1 to 4 were: the owner's instruction of 2026-11-09 takes option A of every row.

| Item | Question | A (recommended) | Alternatives | Where |
|------|----------|-----------------|--------------|-------|
| RAT-031 | One spelling of `starting-point` | Data-model §5 writes the value as `starting-point`, the contract's spelling, so that the record and the command read one value and the selection-bias statement shows it as written | B: the contract maps `starting-point` to `starting point`. C: no change | data-model §5 |
| ANA-037 | Repetition inside a search for designs that add constants | FR-016: a design holding an addition of a committed constant takes no bound that rests on the repetition: no sum, no floor taken from shorter spans inside a search (the floors of Matsui's lemma in `active_sbox.py` and `long_trail.py`) and no active-box count multiplied by one box's bound over one call; its bounds come only from searches that model each round's constants, by a tool validated for such additions (inherited FR-039) | B: floors and counts where the spans' constants coincide. C: no change | spec FR-016 |

### Rows that change the protocol (round 5)

The round's two commits are 51536bf (its choices) and 50aaef1 (its changes applied).

Written with the rows, before they are applied; none sets a reading aside. Every other row clarifies text and changes no
rule.

| Row | Rule | Direction | Why |
|-----|------|-----------|-----|
| RAT-031 | The candidate log's fields (FR-023) | settled | one value fixed |
| ANA-037 | Constant-dependent bounds (FR-016) | stricter | no bound resting on repetition for such designs |

## Analysis remediation 1 (first /speckit-analyze run after /speckit-tasks, 2026-11-10)

**Answered in advance**: the owner's instruction of 2026-11-09 for the analysis loop, "suggest edits for all issues,
make the changes, commit, then rerun speckit-analyze skill. run this process in a loop until speckit analyze finds no new
issues", takes the recommended edit of every finding of the report on d5acd08. Item IDs are the batch's number and the
report's finding ID.

| Item | Question | A (recommended) | Alternatives | Where |
|------|----------|-----------------|--------------|-------|
| AR1-I1 | The trail characteristic at every addition, and the tool that writes it | Research R7 and the plan name a companion of feature 004's ARX search under `research/005/tools/`, a copy whose trail output adds the state after every step of every round, since feature 004's `arx_search.c` prints only the states at round boundaries and its check modes read a round of one addition; the companion is validated on the ARX search's known results before its first counted use (inherited FR-039), feature 004's tool staying unchanged (FR-003); plan phase 4 validates it, and tasks T038, T039 and T043 follow | B: change feature 004's `arx_search.c` in place. C: no change | research R7; plan Technical Context, Project Structure, Plan Phases; tasks T038, T039, T043 |
| AR1-I2 | Feature 004's validation records under `PHYCOWEB_FEATURE=005` | Tasks T006 and T007: under `005` the validation lookup reads feature 004's validation records beside this feature's (research R14), a tool matched by its exact hash, `tool_sha256` and a C tool's binary, as `protocol/evidence.py` matches it; the sentence of T007 and T043 on hashes restated so, since the records' `code_sha256` names `protocol/evidence.py` | B: validate every tool again under this feature. C: no change | tasks T006, T007, T043 |
| AR1-I3 | The re-check's reading of an operation list | Tasks T019 and T020: a standard-library reader of the forms of `research/004/ir.py` under `protocol/`, so that the re-check keeps the inherited rule that it imports only the standard library and `protocol/` and runs in any environment, `ir` importing numpy; T019 compares its evaluation with `ir`'s on the reference designs | B: the re-check imports `ir` and numpy. C: no change | tasks T019, T020 |
| AR1-I4 | An exact D4 tie under the 16×16-first order | FR-022: while an exact D4 tie waits, the two representatives' production-width climbs run in FR-014's order, 16×16 first, and only as far as R at 4×4 needs; `--tie` decides once both have R at 4×4 or one is `ineligible`, a decision at 16×16 under FR-018 included; the contract and T049 follow | B: the inherited order for the tie, 4×4 first. C: no change | spec FR-022; contract; tasks T049 |
| AR1-I5 | Research R13's rotation search against FR-023 | Research R13 restates FR-023: an unchanged re-entered design keeps the amounts feature 004's ranking chose at width 16, its ranking record cited as a prior result; where inherited research R6's rule fixes this feature's D4 width at 8, its amounts are searched again at 8, and amounts that come out otherwise make it a variant (`relation` `derived`) | B: FR-023 follows R13. C: no change | research R13 |
| AR1-I6 | The spelling of `candidate_log.py propose` | The contract writes `propose FILE` with `--derived-from PATH:SHA256`, `--relation` `derived` or `starting-point` and `--changes TEXT`, FILE holding the entry's fields as inherited, as the script and tasks T028 and T046 have it | B: `propose ID`, the script changed. C: no change | contract |
| AR1-U1 | The round count of the structural and bias probes | Research R5: each structural check and each frequency and avalanche measurement of the probes runs at R = 66 rounds, R_max + Δ, the largest R_bound + Δ the climb allows, so that a probe that finishes bounds the run at every R up to it; the contract's `--probe` and task T025 follow | B: at each design's feature-004 R where one exists. C: no change | research R5; contract; tasks T025 |
| AR1-U2 | The security target's files before the variant table exists | Research R8: until the chapter "Permutation" holds its variant table, `mode_limits_v3.py` read for this feature takes the variant rows from the chapter "Security target"'s parameter table, R as the placeholders, so that the files rest on the reviewed chapters alone; tasks T030 to T032 follow, the chapters after "Mode" reading "Not drafted yet" at Version 0.5 | B: a section "Variant table" in "Permutation" at Version 0.5. C: no change | research R8; tasks T030, T031, T032 |
| AR1-U3 | The register's `in_progress` and the code the claim test scans | Tasks T016 and T017: each model's `in_progress` counts its own feature's searched `pass` bound records citing a validation record, a `split` record never counted (data-model §2); the code paths gain `research/005/`, read from this feature's first commit; task T048 sets `phyco-v4`'s `in_progress` with this feature's first counted trail-bound record | B: count every `pass` bound record. C: no change | tasks T016, T017, T048 |
| AR1-U4 | The selection-bias statement's generator | The contract gains `research/005/selection_bias.py [--check]`, and the plan's structure names it | B: a mode of `round_rule.py`. C: no change | contract; plan Project Structure |
| AR1-U5 | A probe's row before the projection table exists | Task T023: before `$REP/projection-table.json` exists, the runner reads the feature-wide row and the probes' 40 h share of it from `plan-projections.json`'s approved option | B: no guard before the table. C: no change | tasks T023 |
| AR1-U6 | The thread count in every record | Tasks T042 and T053: every record states its thread or worker count (FR-007), each structural and bias run at the count its record states | B: searches only. C: no change | tasks T042, T053 |
| AR1-G1 | Constant-adding designs' bounds, and a sum whose part falls | Tasks T040 and T019: a design holding an addition of a committed constant covers each call type's permutation in its bounds (FR-016); a `split` record stands only while both its parts stand (spec, Edge Cases) | B: left to the implementation. C: no change | tasks T019, T040 |
| AR1-G2 | The sections that hold each R_bound's route | Tasks T057 and T072: the chapters test also requires the section "Round counts" in "Permutation" and the routes in `rationale.md`'s chapter "Margin" (FR-025) | B: no test. C: no change | tasks T057, T072 |
| AR1-I7 | The [P] marks | No [P] on T028, T030, T040, T042 and T044, which write one test file; [P] on T023 and T024; the parallel section restated | B: separate test modules. C: no change | tasks |
| AR1-I8 | The Requirement Coverage lists | Regenerated from the tasks' citations | B: no change | tasks |
| AR1-I9 | The success criterion each task serves | Each task that serves a success criterion cites it: T006, T007, T023, T031 to T033, T039, T043, T048 to T050, T055, T065, T070 and T078 | B: FR only. C: no change | tasks |
| AR1-I10 | A probe that reaches its limit | The contract: a search probe reads as reaching its cap, a structural or bias probe as keeping its kind's provisional need (research R5) | B: no change | contract |
| AR1-I11 | Where the three logs stand | Data-model §1 and the plan's structure: the protocol change log and the candidate log under `research/005/`, the provenance log under `reports/005-crypto-architecture-v4/` (research R9) | B: no change | data-model §1; plan Project Structure |

### Rows that change the protocol (analysis remediation 1)

The batch's two commits are 8382f1b (its choices) and d8e5d1f (its changes applied).

Written with the rows, before they are applied; none sets a reading aside. Every other row clarifies text and changes no
rule.

| Row | Rule | Direction | Why |
|-----|------|-----------|-----|
| AR1-I1 | Trail records (FR-019; research R7) | settled | the format the rule asks for, written by a validated tool; feature 004's tool unchanged |
| AR1-I4 | The D4 choice (FR-022; the contract's `d4_choice.py`) | settled | FR-018's MUST and FR-022's order for the production width kept for the tied representatives |
| AR1-I5 | Re-entered designs (FR-023; research R13) | settled | research R13 read as FR-023 states it, the amounts searched again where the width is 8 |
| AR1-U1 | The probes (FR-005; research R5; the contract's `evidence_v3.py … --probe`) | settled | the largest R the climb allows, so that a finished probe bounds every run up to it |
| AR1-U2 | The security target's files (FR-011; research R8) | settled | the files computed from the reviewed chapters alone; the review's scope unchanged |

## Analysis remediation 2 (second /speckit-analyze run, 2026-11-10)

**Answered in advance**, as Analysis remediation 1 was: the owner's instruction of 2026-11-09 for the analysis loop
takes the recommended edit of every finding of the report on 13a02be.

| Item | Question | A (recommended) | Alternatives | Where |
|------|----------|-----------------|--------------|-------|
| AR2-I12 | Which tool runs this feature's ARX searches | Research R7: this feature's ARX searches run on the companion alone, its search feature 004's unchanged but for its output, so that no search runs twice, projected with the factor research R1 gives a tool with no pair at a size; tasks T043 and T051 follow | B: feature 004's tool for the bounds and the companion again for each trail. C: no change | research R7; tasks T043, T051 |
| AR2-I13 | One thread for every heavy run, against research R4 | The tasks' header and Phase 5's rules: a search at one thread (FR-007), the uniform controls, the bias tests and the rotation search at their workers (research R4), each record's `parallelism` stating it; T042 names the field; T022 notes that a bias probe at one thread, as FR-005 has every probe, gives an upper figure for the bias tests' workers | B: one thread for every run. C: no change | tasks header, Phase 5 rules, T022, T042 |
| AR2-U7 | The whole-suite run's row before the projection table exists | Task T021: the feature-wide row read from `plan-projections.json`'s approved option, as T023 reads it for the probes | B: no change | tasks T021 |
| AR2-A1 | The code the claim test scans for this feature | Task T016: the code paths gain `research/005/`, the phrase "read from this feature's first commit" removed, the test's base already covering this feature's files | B: name a656bcf's parent as a second base. C: no change | tasks T016 |
| AR2-I14 | Phase 3's heavy runs | The dependencies: Phase 3 has no heavy run | B: no change | tasks, Dependencies |
| AR2-I15 | Where the companion's tests stand | The tasks' paragraphs "Prerequisites" and "Tests" and the plan's "Testing" line name `tests/test_tools_005.py` and, for the tasks, the analysis loop's batches | B: no change | tasks header; plan Technical Context |
| AR2-I16 | Implementation Strategy item 3's second line | Indented as the other items | B: no change | tasks, Implementation Strategy |

### Rows that change the protocol (analysis remediation 2)

The batch's two commits are 7c230d1 (its choices) and 8947e05 (its changes applied).

Written with the rows, before they are applied; none sets a reading aside. Every other row clarifies text and changes no
rule.

| Row | Rule | Direction | Why |
|-----|------|-----------|-----|
| AR2-I12 | Trail records and the ARX searches (FR-019; research R7) | settled | the searches and their trails from one validated tool, so that no search runs twice; research R1's rule for a tool with no pair applied as written |

## Analysis remediation 3 (third /speckit-analyze run, 2026-11-10)

**Answered in advance**, as Analysis remediations 1 and 2 were: the owner's instruction of 2026-11-09 for the
analysis loop takes the recommended edit of the one finding of the report on 2b52ddc.

| Item | Question | A (recommended) | Alternatives | Where |
|------|----------|-----------------|--------------|-------|
| AR3-G3 | The claim test's register checks for each model | Task T016: each model's `history`, `bound` and `evidence` checked against its own feature's files, `phyco-v4`'s `bound` from this feature's size profile by variant ID, placeholders included (FR-011), its `evidence` the two security-target files and, at L1, feature 004's demonstration record and the files the two review rows name (FR-013), its `history` from this spec's rows "L1 recorded"; each feature's design document held to the mapping chapter's rule | B: the checks for `phyco-v3` alone, as now. C: no change | tasks T016 |

### Rows that change the protocol (analysis remediation 3)

The batch's two commits are 8d91f6b (its choices) and 3cb08f8 (its changes applied).

None: the batch's one row clarifies a task and changes no rule.

## Analysis remediation 4 (fourth /speckit-analyze run, 2026-11-10)

**Answered in advance**, as Analysis remediations 1 to 3 were: the owner's instruction of 2026-11-09 for the
analysis loop takes the recommended edit of both findings of the report on 5f0d566.

| Item | Question | A (recommended) | Alternatives | Where |
|------|----------|-----------------|--------------|-------|
| AR4-H1 | The hours a trail row holds back for the sizes not yet climbed | Research R12: in the 16×16-first order a candidate's trail row holds back, for the sizes not yet climbed, the projection table's needs of those sizes' listed runs for its family's reference design, the recorded need FR-018 and FR-022 name, never a probe at those sizes before the decision at 16×16, since feature 004's runner wants a `--project` probe of every later search at every size and charges each probe's time to the row; each search is still projected first at its own size; the contract's `round_rule.py` and tasks T042 and T043 follow | B: no hours held back at 16×16. C: no change | research R12; contract; tasks T042, T043 |
| AR4-M1 | The rows' hours under `PHYCOWEB_FEATURE=005` | Tasks T006, T007 and T043: every reader of a row's hours (`guard_candidate_row`, the feature-wide row's guard, `left_in_row` and `spent_is_shared` in `protocol/candidates.py`, `scripts/evidence_v3.py`) takes the row by the candidate's family from `$REP/projection-table.json`, or from `plan-projections.json`'s approved option before the table exists, feature 004's constants `ROW_HOURS` and `FEATURE_ROW_HOURS` staying its own | B: the constants changed to this feature's values. C: no change | tasks T006, T007, T043 |

### Rows that change the protocol (analysis remediation 4)

The batch's two commits are 3cc4d8b (its choices) and 6bf28fe (its changes applied).

Written with the rows, before they are applied; none sets a reading aside. Every other row clarifies text and changes no
rule.

| Row | Rule | Direction | Why |
|-----|------|-----------|-----|
| AR4-H1 | The budget in the 16×16-first order (FR-018, FR-022; research R12; the contract's `round_rule.py`) | settled | FR-018's MUST read over feature 004's probes of every later search; the recorded needs held back, as FR-018 and FR-022 name them |

## Analysis remediation 5 (fifth /speckit-analyze run, 2026-11-10)

**Answered in advance**, as Analysis remediations 1 to 4 were: the owner's instruction of 2026-11-09 for the
analysis loop takes the recommended edit of the one finding of the report on 7c92090.

| Item | Question | A (recommended) | Alternatives | Where |
|------|----------|-----------------|--------------|-------|
| AR5-M2 | Feature 004's model ID, variant prefix, candidate IDs and directories in the shared code | Tasks T006, T007 and T039: every record and log entry written under `005` holds `phyco-v4`, variant IDs `phyco-v4/…` and candidate IDs `v4-A<k>` and `v4-B<k>`, the candidate log refusing a `cand-` ID; no shared code keeps a literal feature-004 model ID, variant prefix, candidate-ID pattern or candidate directory for this feature, those of `protocol/candidates.py` (`CANDIDATE_ID`), `scripts/gen_constants_v3.py`, `scripts/round_rule.py` and `research/004/ir.py` among them; `scripts/validate_tool.py` reads a tool under `research/005/tools/` | B: paths only, as now. C: no change | tasks T006, T007, T039 |

### Rows that change the protocol (analysis remediation 5)

The batch's two commits are 73be9bb (its choices) and 8cbfeab (its changes applied).

None: the batch's one row clarifies tasks and changes no rule.

## Analysis remediation 6 (sixth /speckit-analyze run, 2026-11-10)

**Answered in advance**, as Analysis remediations 1 to 5 were: the owner's instruction of 2026-11-09 for the
analysis loop takes the recommended edit of the one finding of the report on b5a23af.

| Item | Question | A (recommended) | Alternatives | Where |
|------|----------|-----------------|--------------|-------|
| AR6-C1 | The contract's modes that this feature's tasks change | The contract gains a section under "Changed" for each mode the tasks change and the contract left to "applies as written": `scripts/protocol_change.py create` (FR-031's first entry, this feature's lists in their table form and its batches; T013), `scripts/mode_limits_v3.py --out` (R as placeholders, the parameter table until the variant table exists; research R8; T031), `scripts/evidence_v3.py`'s bound and trail runs (the order of sizes per kind, the ARX searches on research R7's companion, data-model §3's trail record, the rows by family and the hours held back; research R7, R12; T042, T043) and `scripts/validate_tool.py` (a tool under `research/005/tools/`; T039), each restating the rule it follows | B: leave them to the tasks. C: no change | contract |

### Rows that change the protocol (analysis remediation 6)

The batch's two commits are ec6edf7 (its choices) and 01b4c43 (its changes applied).

None: the batch's one row restates in the contract rules that the spec, research and data model already fix, and
changes no rule.

## Analysis remediation 7 (seventh /speckit-analyze run, 2026-11-10)

**Answered in advance**, as Analysis remediations 1 to 6 were: the owner's instruction of 2026-11-09 for the
analysis loop takes the recommended edit of the three findings of the report on 3f876e4.

| Item | Question | A (recommended) | Alternatives | Where |
|------|----------|-----------------|--------------|-------|
| AR7-L1 | How the place check keys the contract's sections | Task T001: each contract section keyed by its heading's code span, as feature 004's tool keys it, a renamed heading reading as one place removed and one added, since the contract holds two sections of `scripts/evidence_v3.py` | B: merge the two sections. C: no change | tasks T001 |
| AR7-L2 | Which rows come from `plan-projections.json` | The contract's `evidence_v3.py` bound and trail runs and tasks T006 and T007: a candidate's rows come by its family from `$REP/projection-table.json`, and the feature-wide row from that table or, before it exists, from `plan-projections.json`'s approved option | B: no change | contract; tasks T006, T007 |
| AR7-L3 | The claim test's per-model register checks in the contract | The contract's `check_claims.py` adds that each model's `history`, `bound` and `evidence` are checked against its own feature's files (task T016) | B: no change | contract |

### Rows that change the protocol (analysis remediation 7)

None: the batch's rows clarify wording and change no rule.
