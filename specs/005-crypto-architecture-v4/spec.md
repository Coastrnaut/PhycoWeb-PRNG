# Feature Specification: Cryptographic Architecture, Second Design Round (phyco-v4)

> This feature makes no security claim. No PhycoWeb-PRNG model, `phyco-v4` included, may be used
> to generate secrets; use an established cryptographic random-number generator for keys,
> nonces, tokens and salts. Passing statistical tests does not show cryptographic security.

**Feature Branch**: `005-crypto-architecture-v4` (directory only; no git branch, as for feature 004)

**Created**: 2026-11-09

**Status**: Spec approved by the owner (2026-11-09), with decisions D1–D14 as their defaults; plan
approved (2026-11-09), with the run limits extended (option E); checklist choices of rounds 1 to 5
answered in advance and applied (2026-11-09); analysis remediations 1 to 10 applied (2026-11-10);
tasks approved (2026-11-12)

**Input**: User description (verbatim), given on 2026-11-09 after the agent explained why feature
004 stopped and offered a new spec that budgets for the 16×16 bounds from the start:

> draft the new spec

**Scope as the agent drafted it**, from that conversation and feature 004's final report (§11,
§14, §16). Nothing in it is the owner's wording; the owner reviews it with this spec:

> A second, pre-registered design round for the keyed successor to `phyco-v2`, under a new model
> ID, `phyco-v4`, after feature 004 stopped at its selection with no eligible candidate. Carry
> feature 004's protocol, machinery and validated tools where they do not change, and count its
> candidates, results and stop in this feature's selection bias. Change what made feature 004
> stop: a bound climb continues past a capped search with the bound from shorter spans; caps,
> thread counts and budgets per claimable size are fixed in the plan from projections calibrated
> on feature 004's committed timings; the production-width trail bounds run at 16×16 first; trail
> characteristics are recorded at every nonlinear operation; and the security target is reviewed
> before any candidate is proposed. No security claim; development keys only.

## Context

**In short.** Feature 004 tried to design a successor to `phyco-v2` that could one day be analysed
for cryptographic use. It stopped because neither of its two designs obtained, within the time its
rules allowed, the bound its rules required on the best shortcuts through the design (differential
and linear trails) at every grid size it covered. Part of that was the time limit, and part was a
rule that gave up as soon as one search ran out of time, even where shorter results already added
up to the bound it needed. This feature tries again under a new name, `phyco-v4`, with the same
goal and safeguards. It plans the machine time for the largest grid before any design is entered,
lets a bound be built from shorter pieces, tests the largest grid first so that a design that
cannot meet it fails early and cheaply, and has the owner review the security target before any
design exists. It makes no security claim, and stopping again remains a valid outcome.

**Why a second round.** Feature 004 set out to specify a keyed, bio-inspired permutation for
`phyco-v3` and freeze it. It stopped at its selection on 2026-11-09, by its own pre-registered
rules, and the owner's Final result review approved the stop (feature-004 spec, row "Final result
review", a06f75f). Its selection record (`reports/004-crypto-architecture-v3/freeze/selection.json`,
record `selection-20261109T122326Z-254be6df`, SHA-256
`9f38b7489e4577f3615c2c7c207b516926edb0f72f5e4c053349bdce74407a02`) reads "none of the evaluated
candidates is eligible":

- **B1**, the Boolean candidate that the nonlinearity choice rule (D4) chose by its score, had
  trail bounds of weight 16, 24 and 32 at r = 2, 3 and 4, at 4×4 and w = 32, growing about 8 per
  round. Its search at r = 5 was refused: the projection, with the hours held for the larger sizes,
  needed 23.256 h and its trail row had 22.738 h left (candidate-log entry 47). Its r = 4 searches
  had each been projected at 8 h, and they took 7 and 40 minutes (final report §14).
- **A1**, the ARX candidate analysed after B1 under the fallback, established R_bound = 17 at 4×4
  and 9 at 8×8. At 16×16 its bounds stood at W_L = 16, 44 and 80 and W_D = 24, 66 and 120 at r =
  2, 3 and 4, and its linear search at r = 5 reached its 8 h cap, on one thread, before it finished
  (entry 107; record `bound-20261109T051632Z-d69901f4`).
- The agent proposed one replacement per family, B2 and A2, assessed each as likely to end as the
  candidate it replaced, and recommended declining; the owner declined both (entries 49 and 109).

The final report names the cause, "the cost of bounding trails at 16×16 within the per-search
cap", and recommends that any later attempt start with a new specification "whose protocol is
fixed before any result and plans the 16×16 bounds from the start" (§16). Feature 004's stop rule
allows exactly this: after a stop, a later feature may evaluate further candidates only under its
own pre-registered protocol and new model IDs, and it counts feature 004's candidates, results and
stop in its selection bias.

**What feature 004's records show about its climb.** Its round rule ended a size's climb at the
first search that reached its cap or that its trail row refused, and that left the candidate
without R_bound at that size. Yet its FR-038 also lets an active-box count stand as the sum of the
counts of two shorter spans of rounds, a bound that needs no further search, since every trail
over r₁ + r₂ rounds is a trail over r₁ rounds followed by one over r₂. Read with that sum, A1's
committed 16×16 bounds already lie below 2⁻¹²⁸ at r = 8 for the linear kind (weight 80 + 80 =
160) and at r = 6 for the differential kind (weight 24 + 120 = 144). So the rule that ended the
climb, not the lack of a bound, left A1 without R_bound at 16×16. These figures stay feature 004's:
this feature does not re-decide any feature-004 candidate, and every design entered here is
analysed afresh.

**What this feature is.** Stage 5a.1 of security.md §22 run again for a new model ID, as row 5a
foresees ("sends the work back to 004 with a new model ID"). It has feature 004's goal and
deliverables: a security target, a mode, a keyless permutation Π on the parameterised grid with
its inverse, reduced variants, the design rationale, a reference model, vectors, first trail
bounds from validated tools, the owner design review, an external design review if one can be
arranged, and the design freeze of `phyco-v4`, or a recorded stop. It aims at claim level L1 for
`phyco-v4` and starts L2, as feature 004 did.

**This feature makes no security claim.** Under the constitution's Security Policy, no
cryptographic claim may be made, and no evaluation meant to support one pursued, until FUT-SEC-1
to FUT-SEC-9 are met. Everything this spec asks of the design is a requirement the design must
meet, not a statement that it does.

**What it inherits.** Feature 004 built the machinery this feature needs and validated its tools:
the record writers and their guards, the three hash-chained logs, the claim register and its test,
the archive of `phyco-v2` in `baseline/`, the FUT-SEC-8 demonstration and its review, 47
tool-validation records, the operation-list form of a candidate with its evaluators, the cost model
and the re-check. This feature takes feature 004's documents as its baseline protocol, named by
commit and SHA-256 (FR-001), and states only what changes. Where this spec and an inherited
document differ, this spec applies.

**What it changes, and why:**

| Change | Feature 004's record that motivates it | Requirements |
|--------|----------------------------------------|--------------|
| A climb continues past a capped search with sums of shorter spans; searches of a kind at a size end at the first cap | A1's 16×16 climb ended at r = 5 while the sums of its committed bounds lay below 2⁻¹²⁸ by r = 8 | FR-014 to FR-018 |
| Caps, a thread count and budget rows per claimable size, fixed in the plan from projections calibrated on feature 004's records | B1's searches projected at 8 h took 7 and 40 minutes; A1's 16×16 search ran on one of the machine's 32 logical processors | FR-004 to FR-009 |
| Production-width trail bounds at 16×16 first | A1 reached 16×16, the size that stopped it, only after its 4×4 and 8×8 climbs; B1's search at 4×4 was refused for the hours its row held back for the larger sizes | FR-014, FR-018 |
| Trail characteristics at every nonlinear operation | A characteristic held per round cannot fix the differences inside a round with more than one nonlinear layer (feature-004 T131) | FR-019, FR-020 |
| The security target reviewed before any candidate | Feature 004's chapters "Security target" and "Mode" were drafted and never reviewed, the review waiting for a selection that never came | FR-010 to FR-013 |

**Out of scope**, as in feature 004: the RTL, the statistical programme on held-out key sets
(FUT-SEC-7), the full cryptanalysis campaign, the independent review of claim level L5,
publication, and any security claim. The features of security.md §22 rows 5a.3 and 5a.5, now features
007 and 009, take the RTL and the board from this feature's design document.

**This feature changes no existing generator.** `phyco-v2`, `lut-v1`, harness `sp80022` 1.0.0,
the protocols of features 002 to 004, their seed sets, records, logs and documents, and every
frozen file stay as they are.

## Review & Approval *(Constitution Principle VIII)*

| Gate | Reviewer | Date | Decision | Notes |
|------|----------|------|----------|-------|
| Spec approval (scope, the changes from feature 004's protocol, decisions D1–D14, the security.md and register changes of FR-027) | Coastrnaut (repository owner) | 2026-11-09 | Approved | Approves this spec as the protocol's text. From approval the protocol may only become stricter, every change entered in the protocol change log before any result it affects (inherited FR-044). Records the owner's decision on each of D1–D14. Approved by the owner in writing, in the words "spec approved with all recommended defaults, set the row and commit", 2026-11-09: D1–D14 confirmed as their defaults, with the security.md and register changes of FR-027, which security.md 2.18 and `protocol/claims.json` make in the commit after this one. The spec approved is this file as of a656bcf, SHA-256 `bb62fef653ad25665e6670333e9447d5bc26f7bd5b421fbcf26f28af35c31a11`; this commit changes only this row, the Status line, and the decisions' introduction and Status column. Written and committed by the agent on the owner's word |
| Plan approval | Coastrnaut (repository owner) | 2026-11-09 | Approved | The plan fixes, before any candidate is proposed, the calibration, the projection table, the caps, the thread count, the rows and the margin (FR-004 to FR-009); from approval they belong to the protocol. Approved by the owner in writing, in the words "plan approved with all recommended options, set the row and commit" and "extend run limits even more to ensure we find a good candidate also", 2026-11-09: choices 2 to 5 of the plan's "Choices for owner review" as recommended (one thread for every search; feature 004's records cited where they measured a run; rows per family from its reference design; the feature as a parameter of the protocol modules), and choice 1 as option E, the owner's extension: caps of 8 h at 4×4, 24 h at 8×8 and 48 h at 16×16, probes of up to 4 h, rows of 267.5 h per ARX candidate, 425.3 h per Boolean candidate and 102 h feature-wide, three evaluated candidates per family, and the ceiling raised from D7's 720 h to 2,200 h, as FR-008 lets the owner raise it at the plan approval. The plan approved is the plan's documents as of 74dd867: `plan.md`, SHA-256 `5f3300b82e9ad6fa1e3e7e64a58bbf3ecdd32a60abe3860f1c13dc54d081a873`; `research.md`, SHA-256 `799896741ce4ecd1f06f51a191998ed493a65b437b89c3dfd5302cb7dc2fa33c`; `data-model.md`, `contracts/cli.md` and `quickstart.md`; with `research/005/plan-projections.json`, SHA-256 `80b5182c2fd3e0d390b82858e58477d119f737d8b666551dac13128a48a5f489`, from `research/005/plan_projections.py`, SHA-256 `22d562040f03a50fafc6fb8cfb7a8da5818014f285954f70bb547a40bf09ea0a`. Written and committed by the agent on the owner's word |
| Tasks approval | Coastrnaut (repository owner) | 2026-11-12 | Approved | Approves `tasks.md` as of 1ac3fee, 87 tasks in plan phases 0 to 9, after eleven `/speckit-analyze` runs, the last with no finding, and Analysis remediations 1 to 10; the ticks of the six checklists, 176 of 176 items, stand as set; each list "Rows that change the protocol" of `checklist-choices.md` is confirmed, no row taken out. Approved by the owner in writing, in the words "tasks approved, R13 as proposed, set the rows and commit", 2026-11-12. Written and committed by the agent on the owner's word |
| Checklist choices, round 1 ([checklist-choices.md](./checklist-choices.md): the 86 items of the six first-run checklists) | Coastrnaut (repository owner) | 2026-11-09 | Approved | Answered in advance on 2026-11-09, with the instruction to loop the checklists until a re-run finds no new item: "you have my approval of all suggestions to continue without human interaction", which takes option A of every row and approves the round's list "Rows that change the protocol", written with its rows before they were applied (FR-031). Applied the same day to this spec, the plan's documents, security.md (2.19) with its allow-list entry in `protocol/claims.json`, and `.gitattributes`; no row sets a reading aside. Written and committed by the agent on that word |
| Checklist choices, round 2 ([checklist-choices.md](./checklist-choices.md): the 18 items of the first re-run of the six checklists) | Coastrnaut (repository owner) | 2026-11-09 | Approved | Answered in advance on 2026-11-09 by the same instruction as round 1, which takes option A of every row and approves the round's list "Rows that change the protocol", written with its rows before they were applied (FR-031). Applied the same day to this spec and plan.md; two rows correct round 1's text (FR-009's D13 alternative, FR-001's other sizes); no row sets a reading aside. Written and committed by the agent on that word |
| Checklist choices, round 3 ([checklist-choices.md](./checklist-choices.md): the 56 items of the second re-run of the six checklists) | Coastrnaut (repository owner) | 2026-11-09 | Approved | Answered in advance on 2026-11-09 by the same instruction as round 1, which takes option A of every row and approves the round's list "Rows that change the protocol", written with its rows before they were applied (FR-031). Applied the same day to this spec, the plan's documents, security.md (2.20) with its allow-list entries in `protocol/claims.json`, and `research/005/plan_projections.py` with `plan-projections.json`; research R8 and R13, data-model §4 and §5 and the contract also restate rows they follow beyond the rows' "Where" (PRO-024, RAT-018 to RAT-020, SEC-035), places the place check names; no row sets a reading aside. Written and committed by the agent on that word |
| Checklist choices, round 4 ([checklist-choices.md](./checklist-choices.md): the 14 items of the third re-run of the six checklists) | Coastrnaut (repository owner) | 2026-11-09 | Approved | Answered in advance on 2026-11-09 by the same instruction as round 1, which takes option A of every row and approves the round's list "Rows that change the protocol", written with its rows before they were applied (FR-031). Applied the same day to this spec, research R5, data-model §4, the contract, `checklist-choices.md`'s lists (each naming its round's two commits) and security.md (2.21) with its allow-list entry in `protocol/claims.json`; PRO-029's tool is feature 004's adapted to this feature's paths and to its lists' table form, which feature 004's tool does not read; no row sets a reading aside. Written and committed by the agent on that word |
| Checklist choices, round 5 ([checklist-choices.md](./checklist-choices.md): the 2 items of the fourth re-run of the six checklists) | Coastrnaut (repository owner) | 2026-11-09 | Approved | Answered in advance on 2026-11-09 by the same instruction as round 1, which takes option A of every row and approves the round's list "Rows that change the protocol", written with its rows before they were applied (FR-031). Applied the same day to this spec and data-model §5; no row sets a reading aside. Written and committed by the agent on that word |
| Analysis remediation 1 ([checklist-choices.md](./checklist-choices.md): the 19 findings of the first `/speckit-analyze` run after `/speckit-tasks`, on d5acd08) | Coastrnaut (repository owner) | 2026-11-10 | Approved | Answered in advance on 2026-11-09 by the owner's instruction for the analysis loop, "suggest edits for all issues, make the changes, commit, then rerun speckit-analyze skill. run this process in a loop until speckit analyze finds no new issues", which takes option A of every row and approves the batch's list "Rows that change the protocol", written with its rows before they were applied (FR-031). Applied the same day to this spec (FR-022), plan.md, research R5, R7, R8 and R13, data-model §1, the contract and tasks.md; no row sets a reading aside. Written and committed by the agent on that word |
| Analysis remediation 2 ([checklist-choices.md](./checklist-choices.md): the 7 findings of the second `/speckit-analyze` run, on 13a02be) | Coastrnaut (repository owner) | 2026-11-10 | Approved | Answered in advance on 2026-11-09 by the same instruction as Analysis remediation 1, which takes option A of every row and approves the batch's list "Rows that change the protocol", written with its rows before they were applied (FR-031). Applied the same day to research R7, plan.md and tasks.md; no row sets a reading aside. Written and committed by the agent on that word |
| Analysis remediation 3 ([checklist-choices.md](./checklist-choices.md): the one finding of the third `/speckit-analyze` run, on 2b52ddc) | Coastrnaut (repository owner) | 2026-11-10 | Approved | Answered in advance on 2026-11-09 by the same instruction as Analysis remediation 1, which takes option A of the row (FR-031). Applied the same day to tasks.md; the row changes no rule and sets no reading aside. Written and committed by the agent on that word |
| Analysis remediation 4 ([checklist-choices.md](./checklist-choices.md): the 2 findings of the fourth `/speckit-analyze` run, on 5f0d566) | Coastrnaut (repository owner) | 2026-11-10 | Approved | Answered in advance on 2026-11-09 by the same instruction as Analysis remediation 1, which takes option A of every row and approves the batch's list "Rows that change the protocol", written with its rows before they were applied (FR-031). Applied the same day to research R12, the contract and tasks.md; no row sets a reading aside. Written and committed by the agent on that word |
| Analysis remediation 5 ([checklist-choices.md](./checklist-choices.md): the one finding of the fifth `/speckit-analyze` run, on 7c92090) | Coastrnaut (repository owner) | 2026-11-10 | Approved | Answered in advance on 2026-11-09 by the same instruction as Analysis remediation 1, which takes option A of the row (FR-031). Applied the same day to tasks.md; the row changes no rule and sets no reading aside. Written and committed by the agent on that word |
| Analysis remediation 6 ([checklist-choices.md](./checklist-choices.md): the one finding of the sixth `/speckit-analyze` run, on b5a23af) | Coastrnaut (repository owner) | 2026-11-10 | Approved | Answered in advance on 2026-11-09 by the same instruction as Analysis remediation 1, which takes option A of the row (FR-031). Applied the same day to the contract; the row changes no rule and sets no reading aside. Written and committed by the agent on that word |
| Analysis remediation 7 ([checklist-choices.md](./checklist-choices.md): the 3 findings of the seventh `/speckit-analyze` run, on 3f876e4) | Coastrnaut (repository owner) | 2026-11-10 | Approved | Answered in advance on 2026-11-09 by the same instruction as Analysis remediation 1, which takes option A of every row (FR-031). Applied the same day to the contract and tasks.md; no row changes a rule or sets a reading aside. Written and committed by the agent on that word |
| Analysis remediation 8 ([checklist-choices.md](./checklist-choices.md): the 2 findings of the eighth `/speckit-analyze` run, on 49efc40) | Coastrnaut (repository owner) | 2026-11-10 | Approved | Answered in advance on 2026-11-09 by the same instruction as Analysis remediation 1, which takes option A of every row (FR-031). Applied the same day to this spec (FR-001) and tasks.md; no row changes a rule or sets a reading aside. Written and committed by the agent on that word |
| Analysis remediation 9 ([checklist-choices.md](./checklist-choices.md): the one finding of the ninth `/speckit-analyze` run, on 25772a7) | Coastrnaut (repository owner) | 2026-11-10 | Approved | Answered in advance on 2026-11-09 by the same instruction as Analysis remediation 1, which takes option A of the row (FR-031). Applied the same day to this spec (FR-001); the row changes no rule and sets no reading aside. Written and committed by the agent on that word |
| Analysis remediation 10 ([checklist-choices.md](./checklist-choices.md): the one finding of the tenth `/speckit-analyze` run, on 74b37bc) | Coastrnaut (repository owner) | 2026-11-10 | Approved | Answered in advance on 2026-11-09 by the same instruction as Analysis remediation 1, which takes option A of the row (FR-031). Applied the same day to quickstart.md and tasks.md; the row changes no rule and sets no reading aside. Written and committed by the agent on that word |
| Readings set aside (FR-031: each change whose direction sets a reading of the old text aside, decided at the tasks approval) | Coastrnaut (repository owner) | 2026-11-12 | Not needed | No listed change of rounds 1 to 5 or of Analysis remediations 1 to 10 sets a reading aside: each of the 71 listed entries is `stricter` or `settled`. Approved by the owner in writing, in the words "tasks approved, R13 as proposed, set the rows and commit", 2026-11-12. Written and committed by the agent on the owner's word |
| Place check (a comparison of the edits with the rows that made them, where one is made) | Coastrnaut (repository owner) | 2026-11-12 | Approved | Names `research/005/place-check.json`, SHA-256 `db8b2701848d82d2116b4a0947c72d94fa8d1463056f7a1c6979a53517f88712`, `compared_to` 671f34df20661f13bdefeb4f6056b447e99ea55c, from `research/005/place_check.py`: 131 places, no place changed outside the rounds' pairs of commits, and one place changed inside them by an edit that no row of its round names, research R13 in round 3 (936f586), confirmed as no change of rule of its own: its added sentence restates what rows RAT-018 and RAT-019 fix in FR-023, listed as settled, and row AR1-I5 of Analysis remediation 1 later corrected it, naming R13. Approved by the owner in writing, in the words "tasks approved, R13 as proposed, set the rows and commit", 2026-11-12. Written and committed by the agent on the owner's word |
| Environment record 1 (windows) | Coastrnaut (repository owner) | 2026-11-12 | Approved | windows, approval hash `f587a4c6242bcf4c8c54dca507d355c39a0f576c66540e97ac38917273ffc015`, kind `canonical`, 2026-11-12. Names `reports/005-crypto-architecture-v4/environment-windows.json`, record `environment-20261112T201804Z-03dadd34`. Set on the owner's standing word of 2026-11-12, "work autonomously through this whole process. do not stop to ask questions, use your best judgement", which the record keeps as its written approval; the record written and the row set and committed by the agent on that word (T010) |
| Environment record 2 (wsl) | Coastrnaut (repository owner) | 2026-11-12 | Approved | wsl, approval hash `33343f28557eecbad74ec8827bda6169f69acd60c811d75545cdb3bbf19bb429`, kind `canonical`, 2026-11-12. Names `reports/005-crypto-architecture-v4/environment-wsl.json`, record `environment-20261112T201847Z-741efe8b`. Set on the owner's standing word of 2026-11-12, "work autonomously through this whole process. do not stop to ask questions, use your best judgement", which the record keeps as its written approval; the record written and the row set and committed by the agent on that word (T010) |
| Tool acquisition (each download: name, source, size, licence) | _pending_ | _pending_ | _pending_ | No download is planned; a file needs a row of its own, "Download <n>", before it is fetched |
| Security-target review (`phyco-v4`: the design document's chapters "Security target" and "Mode", with `rationale.md`'s chapters of those names, before any candidate is proposed) | _pending_ | _pending_ | _pending_ | Names the version and SHA-256 of both documents' chapters, with the security target's files (FR-011). The candidate log refuses every `proposed` entry while this row does not read Approved at HEAD |
| L1 recorded (`phyco-v4`) | _pending_ | _pending_ | _pending_ | Names this feature's security-target review row and feature 004's FUT-SEC-8 result review row (ffb1425), each with what it reviewed by path and SHA-256 (FR-013) |
| D4 tie | _pending_ | _pending_ | _pending_ | As feature 004's row of that name, for this feature's records |
| Selection tie | _pending_ | _pending_ | _pending_ | As feature 004's row of that name, for this feature's records |
| Second transcription go-ahead | _pending_ | _pending_ | _pending_ | As feature 004's row of that name (inherited FR-057) |
| Owner design review | _pending_ | _pending_ | _pending_ | As feature 004's row of that name; also checks the candidate-dependent items the security-target review left open (FR-012) |
| External design review | _pending_ | _pending_ | _pending_ | Recorded as done or "not arranged", as feature 004's row of that name |
| Design freeze (`phyco-v4`) | _pending_ | _pending_ | _pending_ | As feature 004's row of that name |
| Final result review | _pending_ | _pending_ | _pending_ | The final report and its recommendation to proceed, revise or stop (FR-029) |

The notes under feature 004's Review & Approval table apply to this table, with `phyco-v4` and this
feature's paths: which rows a guard reads at HEAD, which record an owner's own act, the numbered
rows ("Download <n>", "Environment record <n>", "Owner-provided value <n>", "Log repair <n>", and a
row with a number for each later selection record or review), and how each is set. The owner sets
each row and commits it, or gives the decision in writing, which the agent then writes and commits,
quoting the owner's words with their date, as in feature 004 from 2026-11-05. The agent stops at
every gate of this table (Principle VIII); no standing authorization covers a gate unless the owner
gives one in writing for it. Inside inherited FR-043's window, from the owner design review's
approval to the final result review, the owner's written word, recorded and committed by the agent
quoting it, stands in place of the owner's commit, as in feature 004 from 2026-11-05. Each later
checklist round has a row "Checklist choices, round <k>", and each batch of the analysis loop's
changes a row "Analysis remediation <k>", set by the agent on the owner's advance approval of
2026-11-09, quoting it. A change made after the tasks approval and before any result is set in a row
"Protocol change <k>" that the owner approves in writing, the agent recording the owner's words,
before the change takes effect; a claim-test finding answered by an allow-list entry alone needs no
row, the entry being reviewed at the next ⛔ gate as inherited FR-069 has it. "Readings set aside"
reads Not needed at the tasks approval when no listed change sets a reading aside, and "Place check"
is made at the tasks approval: a comparison of every edit since the plan approval with the rows that
made it, its file named by SHA-256 and each place that no row made listed for the owner's decision;
it reads Not needed only where no edit was made since the plan approval. The comparison is made by
`research/005/place_check.py`, feature 004's tool adapted to this feature's paths and to its lists'
table form, written before the tasks approval as feature 004's was before its own (2392150), its
file `research/005/place-check.json`; each list "Rows that change the protocol" names its round's
two commits, the choices commit and the apply commit.

## Decisions Taken as Defaults

The agent took a default for each decision below, so that every requirement is definite. Each was
the owner's to confirm or change at spec approval, and on 2026-11-09 the owner confirmed all
fourteen as written ("spec approved with all recommended defaults"). A later change is made in this
spec before any result it affects.

| ID | Decision | Choice (default) | Alternative | Used in | Status |
|----|----------|------------------|-------------|---------|--------|
| D1 | Model and candidate IDs | `phyco-v4`; candidates `v4-A<k>` (ARX) and `v4-B<k>` (Boolean). A feature-004 design may be entered again as a new candidate, with a new ID, counted as evaluated and in the selection bias | New designs only, feature-004 designs excluded | FR-002, FR-023 | Confirmed 2026-11-09 |
| D2 | Baseline protocol | Feature 004's documents at commit 99e6994, named by SHA-256, with this spec's changes | A self-contained spec that restates every rule | FR-001 | Confirmed 2026-11-09 |
| D3 | Security target and mode | Feature 004's chapters of Version 0.4, unchanged: a 128-bit target strength, a 256-bit key, a 128-bit nonce, c = 384 at every claimable size, the keyed duplex, a target advantage of 2⁻⁶⁴ | Revised before the review, for example a smaller capacity for a higher rate | FR-010 | Confirmed 2026-11-09 |
| D4 | When the security target is reviewed | Before the first candidate is proposed; the candidate-dependent items at the owner design review | After the selection, as in feature 004 | FR-011, FR-012 | Confirmed 2026-11-09 |
| D5 | The climb past a capped search | Sums of shorter spans continue it; searches of a kind at a size end at the first cap or refusal; the climb starts at r = 1; R_max = 64, which bounds R_bound + Δ at 66; the round rule's R may exceed it through its other terms, and the tools hold every R the rule gives (FR-017) | Feature 004's rule: the climb ends at the first cap | FR-015 to FR-017 | Confirmed 2026-11-09 |
| D6 | Order of sizes for the bounds | 16×16, then 8×8, then 4×4; every other kind keeps 4×4 first | 4×4 first for every kind, as in feature 004 | FR-014, FR-018 | Confirmed 2026-11-09 |
| D7 | Budgets | Fixed in the plan from calibrated projections, every row holding at least twice its projected need, within a ceiling of 720 h of heavy runs for the whole feature, which the owner raised to 2,200 h at the plan approval, as FR-008 allows | Feature 004's values: per candidate 48 h of trail searches at 8 h each, 6 h of structural checks and 12 h of bias tests, with a feature-wide row of 66 h | FR-004 to FR-009 | Confirmed 2026-11-09 |
| D8 | Thread count | Fixed once in the plan from the calibration, the same for every search, recorded in every record | One thread, as in feature 004 | FR-007 | Confirmed 2026-11-09 |
| D9 | Trail records | The characteristic at every nonlinear operation; a trail at or below 2⁻¹²⁸ classed `none` | Feature 004's characteristic, the difference or mask after every round | FR-019, FR-020 | Confirmed 2026-11-09 |
| D10 | Selection bias | Counts feature 004's B1 and A1, the declined proposals B2 and A2, its D4 record and its stop, with every design of this feature | The evaluated candidates of both features only | FR-024 | Confirmed 2026-11-09 |
| D11 | A proof that carries a bound to a larger size | A check beside the computed bounds, for the selected candidate only, as in feature 004 | A source of R_bound above 8×8, with acceptance rules fixed at spec approval | FR-021 | Confirmed 2026-11-09 |
| D12 | Roadmap numbering | This feature takes stage 5a.1's place for `phyco-v4`; the features of stages 5a.2 to 5a.6 become 006 to 010 | Those features keep their numbers, and row 5a.1 names this feature beside feature 004 | FR-027 | Confirmed 2026-11-09 |
| D13 | Claimable sizes | 4×4, 8×8 and 16×16, each needing R_bound and every eligibility item, as in feature 004; a claimable size that does not fit the XC7A100T stays claimable, covered by the implementation feature's simulation alone (security.md §22 row 5a.5) | 16×16 claimable only where its R_bound and every item are established, otherwise a research size outside every claim | FR-022 | Confirmed 2026-11-09 |
| D14 | Families | Both; D4 chooses the family as in feature 004, the other analysed at the production width only if the chosen one ends with no eligible candidate. Reason: under FR-018 each candidate that cannot be bounded at 16×16 ends at its first searches there, its cause its own, so the family's replacements follow up to its limit of three evaluated candidates, each at that cost, before the fallback reaches the other family; the plan's projections are planning data and change no rule | Both analysed at the production width, in the order of their D4 scores | FR-022 | Confirmed 2026-11-09 |

## User Scenarios & Testing *(mandatory)*

The users are the repository owner, who decides at every gate, and the reviewers and later features
that read this feature's records.

### User Story 1 - Every run planned at every claimable size before any candidate (Priority: P1)

The owner wants to know, before any machine time goes to a candidate, that the rules can be carried
out at 16×16: that each search, check and test the rules require of a candidate at each claimable
size fits its row. The plan measures costs on feature 004's validated tools and committed
operation lists, calibrates its projections against feature 004's projections and the hours its
runs actually took, and fixes caps, a thread count and rows from them, with a margin.

**Why this priority**: feature 004 stopped on the cost of its 16×16 searches. Planning them first
is what makes the rest of this feature worth running.

**Independent Test**: from feature 004's committed records and the plan alone, before any
candidate exists, every row's value is checked to be at least the margin times the projected need
of the runs charged to it, at every claimable size.

**Acceptance Scenarios**:

1. **Given** feature 004's committed projection and bound records, **When** the plan is written,
   **Then** it lists for each kind of evidence and each claimable size the projected need of each
   run the rules require of one candidate, the calibration factor from feature 004's projections
   against their measured hours, and the row that holds the run.
2. **Given** a row that cannot hold a run's projected need at 16×16 with the margin, **When** the
   plan is reviewed, **Then** the row is raised, or the plan states that the run cannot be made,
   before any candidate is proposed, never after a candidate's result.
3. **Given** a projection table whose rows exceed the feature's ceiling, **When** the plan is
   reviewed, **Then** the owner decides at plan approval, by raising the ceiling, lowering the
   candidate limit or taking D13's alternative, before any candidate is proposed.

---

### User Story 2 - The security target reviewed before any candidate (Priority: P2)

The owner reviews `phyco-v4`'s security target and mode before any candidate is proposed, so that
no candidate's result can shape the target: the properties sought, the 128-bit target strength,
the key, nonce and capacity, the threat model, the output limits, and the mode's theorem with its
preconditions. The chapters start from feature 004's design document, Version 0.4, which was
drafted but never reviewed. Items that depend on a selected design stay open in the chapter and
are checked at the owner design review.

**Why this priority**: the target bounds every later rule, and an early review gives a recorded
milestone, L1 for `phyco-v4`, whatever the selection brings.

**Independent Test**: the review row, the chapters' SHA-256 and the order of the commits: the
review's approval commit comes before the candidate log's first `proposed` entry.

**Acceptance Scenarios**:

1. **Given** the drafted chapters, **When** the owner reviews them, **Then** the row names their
   version and SHA-256, and the candidate log refuses a first `proposed` entry until the row reads
   Approved.
2. **Given** a declined review, **When** the owner states the reasons, **Then** the chapters are
   revised and reviewed again, and no candidate is proposed meanwhile.
3. **Given** the review Approved beside feature 004's FUT-SEC-8 result review, **When** the
   register is updated, **Then** `phyco-v4` stands at L1 with no claim, and every
   candidate-dependent item stays listed as open until the owner design review.

---

### User Story 3 - Bounds at every claimable size, 16×16 first, with no stalled climb (Priority: P3)

For each entered candidate, the production-width trail-bound climbs run at 16×16 first, then 8×8,
then 4×4. A search that reaches its cap ends that kind's searches at that size, but not the climb:
the bound at each later round count is the largest sum of established bounds over shorter spans,
until both kinds' bounds lie below 2⁻¹²⁸ (R_bound) or the round count passes R_max. Every trail a
search returns is recorded at every nonlinear operation, so that the re-check recomputes its exact
weight.

**Why this priority**: this is the change that removes feature 004's stop condition while keeping
every bound a bound.

**Independent Test**: from a candidate's committed records alone, the re-check recomputes every
sum from the records it cites, every trail's weight from its characteristic and the candidate's
committed operation list, and R_bound at each size.

**Acceptance Scenarios**:

1. **Given** searched bounds at r = 1 to k at a size and a capped search at r = k + 1, **When** the
   climb continues, **Then** the bound at every r > k is the largest sum W(r₁) + W(r₂), r₁ + r₂ = r,
   of established bounds of that kind and size, written as a `split` bound record citing its two
   parts, and no further search of that kind runs at that size.
2. **Given** a candidate with no established bound of a kind at 16×16, its first search there
   capped or refused, **When** the climb ends, **Then** the candidate is `ineligible` before any of
   its production-width hours at 8×8 or 4×4 are charged, and the decision states that cause.
3. **Given** a trail record, **When** the re-check runs, **Then** it recomputes the weight as an
   exact rational from the characteristic at every nonlinear operation and the committed operation
   list, checks every transition, and classes the trail by the 2⁻¹²⁸ threshold.

---

### User Story 4 - Evidence, selection or a stop, with feature 004 counted (Priority: P4)

The structural checks, the frequency and avalanche tests, the round rule, eligibility and selection
run as in feature 004, on the candidates whose bounds stand at every claimable size. The final
report and the design rationale state the selection bias over every design considered in features
004 and 005.

**Why this priority**: this is inherited machinery, changed only where the earlier stories change
it.

**Independent Test**: the selection record, and the selection-bias statement checked against the
candidate logs of both features.

**Acceptance Scenarios**:

1. **Given** eligible candidates, **When** the selection runs, **Then** feature 004's rule selects,
   and the selection-bias statement lists feature 004's B1 and A1 with their decisions, B2 and A2
   as declined proposals, its D4 record and its stop, beside this feature's designs.
2. **Given** no eligible candidate, **When** the set closes, **Then** the selection stops, the
   final report states what was reached, and the tasks for the model, vectors, reviews and freeze
   are marked with that reason.

---

### User Story 5 - The model, its vectors, the reviews and the freeze of phyco-v4 (Priority: P5)

After a selection, as in feature 004: the reference model and its constants, vectors at every
size, constructed states, the second transcription from a separate session, the design rationale,
the review package, the owner design review, the external design review recorded as done or not
arranged, and the design freeze.

**Why this priority**: it needs a selected candidate.

**Independent Test**: as in feature 004: the vectors reproduced on both platforms, the second
transcription agreeing at every step of every committed vector, and the freeze record's hashes.

**Acceptance Scenarios**:

1. **Given** a selected candidate, **When** the model and vectors are written, **Then** they
   reproduce on both platforms, and the second transcription agrees at every step of every
   committed vector.
2. **Given** the owner design review Approved, **When** the freeze is made, **Then** `phyco-v4` is
   frozen with its hashes, and the final report recommends proceed, revise or stop.

---

### Edge Cases

- **A search beside a sum**: a searched bound below a sum at the same r and size is no
  contradiction, both being lower bounds, and the larger stands (FR-016). A trail or a solution
  that a search exhibits at r rounds with a weight below a bound established at that r and size
  contradicts that bound: it is a tool defect (inherited definition), recorded before any re-run,
  and a sum stands only while both its parts stand.
- **No bound below 2⁻¹²⁸ by R_max**: where even the largest sums do not lie below 2⁻¹²⁸ at any r up
  to R_max, for instance because every established bound of a kind is 0, the candidate has no
  R_bound at that size and is `ineligible`.
- **The first search at 16×16 capped**: with no established bound of that kind at 16×16, its first
  search there capped or refused and no size-independent bound read there (FR-015), no sum exists;
  the candidate is `ineligible` at once (User Story 3, scenario 2).
- **A trail above 2⁻¹²⁸**: a trail found with probability or squared correlation above 2⁻¹²⁸ at r
  rounds is a source of R_dist (inherited round rule), recorded at every nonlinear operation, beside
  any sum at a larger r.
- **A characteristic that does not hold**: a transition the re-check finds impossible, or a weight
  it recomputes differently, is a disagreement, a tool defect that blocks the candidate (inherited).
- **Projections that miss**: a run whose measured hours differ from its calibrated projection is
  reported with both figures; no decision already made changes, and the calibration is not refitted
  during the feature.
- **A feature-004 tool changed**: a tool whose exact hash differs from its validation record's is
  validated again before its first use here (inherited triggers).
- **A feature-004 design entered again**: it is a new candidate with a new ID, counted as evaluated;
  its feature-004 records are cited as prior results, never as its evidence, and every kind of
  evidence runs again here.
- **The security-target review changes a parameter**: a change found needed there is made only in
  the stricter direction, a larger capacity, the key and the nonce staying as FR-010 states them, as
  a change to FR-010 listed under FR-031 before the review's approval and before any candidate is
  proposed; the output limits are then recomputed.
- **Rows that turn out short**: a row only falls; a run that does not fit is refused, and the
  candidate is `ineligible` for that cause, classed shared or its own as feature 004 classes it
  (inherited ANA-078). The margin is there to prevent it, not to excuse it.
- **No external reviewer**: recorded as "not arranged" (inherited).
- **A run ended from outside, an environment change, a broken log**: as in feature 004.

## Requirements *(mandatory)*

### Functional Requirements

**Baseline and identity**

- **FR-001**: Feature 004's documents at commit 99e6994, in the table below, MUST be this feature's
  baseline protocol. They are read with `phyco-v3` as `phyco-v4`, feature 004's paths as this
  feature's (`specs/005-crypto-architecture-v4/`, `reports/005-crypto-architecture-v4/`,
  `research/005/`), the development-input namespace `phycoweb-004/` as `phycoweb-005/`, and feature
  004's Review & Approval rows as this spec's. Every inherited requirement applies unchanged except
  where this spec changes it, by number. A bare FR-<n> in this feature's documents is this spec's;
  an inherited requirement is cited as "inherited FR-<n>" or "feature 004's FR-<n>", an inherited
  text's own FR-<n> reads as feature 004's, and "by number" means that this spec names the inherited
  requirement it changes. Wherever D4 names a choice, a score, a record, a width or a tie of the
  families' choice, it is feature 004's D4, the nonlinearity choice rule, as are the names "the D4
  choice", "D4 tie", `d4_choice.py` and the `d4` records; elsewhere, as in research R8, D4 is this
  spec's decision so numbered in its table. The protocol change log's first entry names these
  documents by their SHA-256, each of the committed blob's bytes, LF, kind `raw`, before any result
  exists.

  | Document under `specs/004-crypto-architecture-v3/` | SHA-256 at 99e6994 |
  |----------------------------------------------------|--------------------|
  | `spec.md` | `3e8d96ea8e7bb1eef542cd4a5b2b7fd61f3f9e65e014a5c1c5b2a961be431d48` |
  | `plan.md` | `665c793450918805ed7e5b86873b1b5195cbc9d86f99ad94f7bbbdfd665f2c95` |
  | `research.md` | `614afc499c5941ccb5284ca1baafbe0055f011b6dde1bf816127884e2c66da0a` |
  | `data-model.md` | `a4409c024adbc0e0fc2fe5c70bdf25fd977311a7cb077254ab9e1b9f0d8e01dc` |
  | `quickstart.md` | `ed2ca406e19bc96f0b22e6200b20c054a34c0be9b0e57b8627ada5f25047b2d4` |
  | `contracts/cli.md` | `2d0f3aff4081185b6c6160edb8d67f3ecdb1f8b8d48c87a9df296648eabec9a5` |
  | `contracts/model-v3-api.md` | `5a988a0f5fe325909dabc952fc9bd9083cae40b64ded2cfb7ea211bd4a6dc17f` |

  The later features of the inherited text are read as security.md §22 numbers them since its
  version 2.18: feature 005 as the cryptanalysis stage, row 5a.2, now feature 006; feature 006 as
  row 5a.3, now feature 007; feature 007 as row 5a.4, now feature 008; feature 008 as row 5a.5, now
  feature 009; and feature 009 as row 5a.6, now feature 010. Feature 004's Review & Approval rows
  are read as this spec's gate families with their reading rules; a row that records feature 004's
  own past act (its downloads, environment records, tool acquisition, owner-provided values and
  checklist rounds) is not this spec's and is not repeated.

  Every inherited design rule applies unchanged to `phyco-v4`: a permutation of the whole state of
  an n×n torus, two w-bit lanes per node, neighbour-only data flow with at most four channels per
  node and phase, an operation list of invertible updates, fixed operations with no data-dependent
  control or shift amounts, at most one or two carry chains per pipeline stage, constants in a ROM
  at each food node, the replaced mechanisms and the slime-mould mapping's one sentence. Every other
  n from 2 to 16 (5×5 to 7×7, 9×9 to 15×15, and 3×3 where the design document gives it no
  three-colour schedule) is for exploration only, as feature 004's FR-018 has it: a table written
  for that (n, w), never frozen and never evidence; the size profile lists keyed variants only at
  the claimable sizes, 2×2 and a supported 3×3.

  The spec, research and design versions that this feature's records cite are copied under its paths
  (`spec-versions/`, `research-versions/`, `design-versions/`), and the claim test reads each copy
  as the document it copies. A reproduction re-runs and re-checks what inherited research R16 lists;
  the probes and the projection table are re-checked, never re-run. Feature 004's downloads manifest
  and the files it lists under `data/local/004/downloads/` are read as feature 004's, not under the
  path rule: each file is checked against that manifest's SHA-256 before it is read, `limits.json`
  cites feature 004's `fetched` entry by path and SHA-256, and a file missing on disk is fetched
  again only under a row "Download <n>" with the owner's permission.
- **FR-002**: The model ID MUST be `phyco-v4` and candidate IDs `v4-A<k>` and `v4-B<k>` (D1);
  feature 004's IDs keep their records.
- **FR-003**: Feature 004's records, logs and documents MUST be read-only inputs: this feature
  edits none of them.
  The feature setting that this feature adds to the code both features share (research R9) leaves
  feature 004's verdicts unchanged: feature 004's re-check at HEAD gives the same result before and
  after the change, a test showing it. Feature 004's FR-053 test writes its records under the active
  feature's paths once that setting exists; until then no whole-suite run is made for this feature.
  No run of this feature writes under feature 004's paths: once the setting exists, the whole suite
  and every script run for this feature with `PHYCOWEB_FEATURE=005`, and the test of feature 004's
  re-check above and quickstart V2 run `scripts/recheck_004.py --no-record`, which prints its result
  and writes nothing; that test compares the result after the change with T132's committed record,
  the result before it
  (`reports/004-crypto-architecture-v3/rechecks/recheck-20261110T010625Z-454c1890.json`, SHA-256
  `d53424fb529ab2254825c107a2f066dab702f46e66c0ef176787b5d5f6526f21`: 160 records, 0 disagreements).
  Each test that reads feature 004's committed records pins feature 004 for those reads, and every
  test that writes a record writes under the active feature's paths, feature 004's FR-053 test among
  them, so that a whole-suite run with `PHYCOWEB_FEATURE=005` checks feature 004's records as before
  and writes nothing under its paths; plan phase 1's change makes the tests so.

**Every run planned before any candidate (User Story 1)**

- **FR-004**: The plan MUST derive, from feature 004's committed `projection` records and the
  measured hours of the runs they projected, a calibration per kind of evidence, and for the bound
  searches per tool and size with research R1's transfer rule, the ratio of measured to projected
  time, and apply it to every projection of this feature. The calibration and the records it reads
  MUST be committed with the plan. It reads feature 004's records as committed at 99e6994, so that a
  later record never changes it, and `research/005/plan_projections.py --check` MUST pass on both
  platforms. Plan phase 1 changes `plan_projections.py` to read those records at 99e6994, its output
  unchanged, which `--check` shows; the records added since are feature 004's FR-053 projections,
  which the calibration does not read.
- **FR-005**: Before any candidate is proposed, the plan MUST give a projection table: for every
  kind of evidence the rules require of one candidate, at every claimable size and the production
  width, the projected need of each run, from probes on feature 004's committed operation lists of
  cand-A1 and cand-B1, the reference designs, at the thread count of FR-007, each probe a
  `projection` record charged to the feature-wide row. For the bound searches the table lists each
  reference design's searches at each size from r = 1 up to the first r at which its bounds,
  searched or summed as FR-016 sums them, are projected to lie below 2⁻¹²⁸, or up to R_max. Each
  row's value MUST be at least the margin, at least 2 (D7), times the sum of the projected needs it
  must hold.
  The probes run after plan phase 1's environment records and protocol change log and before the
  candidate log's first `proposed` entry, before or after the security-target review. A probe's
  outputs other than its timing are discarded unread. A probe that would take the probes past their
  40 h share of the feature-wide row is refused, and its run keeps the plan's projection. The
  projection table is reproduced from its committed probe records and `plan-projections.json`, never
  by running the probes again.
- **FR-006**: The plan MUST fix a cap per search instance for each claimable size and each kind of
  bound search, at least the margin times the calibrated projection of the longest search the
  projection table lists for that size and kind; feature 004's "one 8 h limit" for the runs of one
  count becomes one cap of the count's size.
- **FR-007**: The plan MUST fix one thread count for every search, from the calibration (D8), and
  every record MUST state it. One heavy run runs at a time (inherited FR-045), and a reproduction
  uses its original's thread count.
- **FR-008**: The rows of every candidate and the feature-wide row together MUST fit the ceiling of
  heavy runs for the whole feature: D7's 720 h by default, raised by the owner to 2,200 h at the
  plan approval of 2026-11-09. Where the projection table needs more, the owner
  decides at plan approval, before any candidate is proposed, by raising the ceiling, lowering the
  candidate limit or taking D13's alternative.
- **FR-009**: From plan approval, the calibration and the thread count MUST NOT change, and the
  caps, the rows, the ceiling and the candidate limit MUST only fall (inherited FR-044). The plan
  approval fixed the values of option E, which the owner chose before the approval was recorded
  (research R3). A clarification of the calibration's rule that leaves every factor as computed is
  no change. A probe that shows a need above its row is reported before the first `proposed` entry;
  the owner may then lower the candidate limit of the family whose row cannot hold the run, a
  stricter change, to zero where every candidate of that family would need the run, D4 then scoring
  the families that hold candidates, D14's fallback reaching no family at zero, and SC-001 reading
  over the rows of those families; without such a change the run is refused when it comes, its cause
  shared (FR-018). D13's alternative removes an eligibility requirement, is not stricter, and is out
  of reach after the plan approval; no row is raised.

**The security target first (User Story 2)**

- **FR-010**: The chapters "Security target" and "Mode" of this feature's design document MUST start
  from feature 004's `design.md`, Version 0.4 (SHA-256
  `60a9c9496792c7f3ca98ddb4df3e2c481c8c4b8059780ab2f29044e53cbd9e9b`), read with `phyco-v4` for
  `phyco-v3` (D3), and list every change with its reason. The copied chapters cite feature 004's
  requirements, decisions and research items as "feature 004's FR-<n>" (D<n> and R<n> alike) and
  name the later features by security.md §22's numbers, T2's and T11's deferrals going to feature
  006 and T4's and its risk's to feature 009, each edit listed among the changes. `rationale.md`'s
  chapters of those names start from feature 004's `rationale.md`, Version 0.4 (SHA-256
  `01a6de45ae18e5dfb5fad070322dcfa908cb55e842ac2cbe1d5ebe5730ebbc32`), read and changed the same
  way, the two files sharing their version (inherited FR-034); the list of changes, each with its
  reason, stands in `rationale.md`'s chapters "Security target" and "Mode", each in a section
  "Changes from Version 0.4", so that the design document's header and chapters keep their fixed
  form, each value there cited by the design document's chapter and section, as inherited FR-034 has
  `rationale.md` cite every value. The document is Version 0.5, continuing feature 004's numbering,
  and each later change makes a new version. `phyco-v4`'s key holds 256 bits of entropy, its secret
  state reachable from the key is the capacity, 384 bits at every claimable size, and the bound
  these place on any level is the least of feature 004's generic bounds, k/2 = 128 bits from
  single-target quantum search on the key, the capacity's c/2 being 192 bits: the size profile's 128
  bits at every claimable size, a target and a ceiling, not a claim (constitution, Security Policy).
  A parameter change that the security-target review finds needed is made only in the stricter
  direction: the inherited rule gives a claimable size's key k = min(c, 256) bits and its nonce k/2,
  so the key and the nonce stay at 256 and 128 bits, and the one parameter such a change may raise
  is the capacity, the rate falling and the output limits recomputed (Edge Cases).
- **FR-011**: The security-target review (⛔) MUST be held before the first candidate is proposed.
  Its row names the version and SHA-256 of the design document's chapters and of `rationale.md`'s
  chapters of those names, with the security target's files, written before the review with R as
  `<R4>`, `<R8>` and `<R16>` (the strings stand where a number will, and the size profile's check
  reads a placeholder as not yet known, checking every other figure), and the candidate log MUST
  refuse every `proposed` entry while the row does not read Approved at HEAD with the chapters'
  SHA-256 it names or while the projection table does not exist (FR-005).
  From the commit that first commits the security target's files, the register's `bound` for
  `phyco-v4` holds the size profile's `bound_bits` by the variant IDs as the profile writes them,
  placeholders included, and its `evidence` names both files (inherited FR-069); both are written
  again in the commit that writes R into the files.
- **FR-012**: Every item of the security target that depends on a selected design MUST be listed in
  the chapter as open and checked at the owner design review: the round counts that the parameter
  table holds as `<R4>`, `<R8>` and `<R16>`, with every figure computed from them; the margin of
  instantiation's diffusion over R_f (inherited FR-029), read from the same dependency measurement
  as FUT-GRID-3's warm-up; the first-order related-key and related-nonce differences (inherited
  research R4); and the functionality class (inherited FR-011), which feature 004 was to close at a
  security-target review held after its selection, with the selected design's records, and which
  moves here with those items, Version 0.4's "here at the security-target review" being one of
  FR-010's listed changes.
  Once every R is known, the chapters and the security target's files are written again and reviewed
  in the family's next row, "Security-target review <k>", the later review: it comes after the
  selection and before the owner design review, which waits for it, and reviews the round counts,
  the figures computed from them and the open items as the chapters then state them, while the owner
  design review checks the open items against the selected candidate's records. An open item that
  fails at the owner design review fails the candidate's eligibility item, as inherited; L1 stays
  while the reviewed chapters do not change, and a change to the target is reviewed again, with "L1
  recorded <k>".
- **FR-013**: The row "L1 recorded" MUST name this feature's security-target review row and feature
  004's FUT-SEC-8 result review row (ffb1425), each with what it reviewed by path and SHA-256. The
  claim register gives `phyco-v4` L1 while both read Approved and those hashes hold at HEAD, and L0
  otherwise, as feature 004's rules give it for `phyco-v3`.
  Feature 004's FUT-SEC-8 result review row is read by the claim test from feature 004's spec at
  HEAD. "L1 recorded" is set only once the claim test covers `phyco-v4` (FR-026; plan phase 1 before
  phase 3). L1 rests on the chapters as the review read them: when R fills them in, the named hashes
  no longer match, and the level reads L0 until the later review (FR-012) and its "L1 recorded <k>",
  k the family's next number, read Approved.
  Each change of level is made in the commit that changes the rows or files it rests on, with the
  register's `claim_level` and `history`, security.md §1.1 and §15, and a security.md version with
  its history entry: when an "L1 recorded <k>" reads Approved, and back to L0 in the commit that
  writes R into the reviewed chapters. While the register gives `phyco-v4` the level those rows rest
  on, its `evidence` lists feature 004's demonstration record (FR-030) by path and SHA-256, with the
  files the two review rows name, as inherited FR-069 has it, and the commit that returns the level
  to L0 drops them.

**The climb (User Story 3)**

- **FR-014**: At the production width, each candidate's trail-bound climbs MUST run at 16×16 first,
  then 8×8, then 4×4 (D6). Every other kind of evidence keeps feature 004's order, 4×4, then 8×8,
  then 16×16 (FUT-GRID-5). FUT-GRID-5's order governs vectors and statistical evaluation per size,
  which keep 4×4 first, as the hardware features' RTL and board do; trail bounds analyse the
  permutation, not a size's validation, and run where their cost is highest first. A search that
  does not depend on the size (FR-015) runs before every size's climb.
- **FR-015**: At each claimable size, the climb MUST start at r = 1, with one search per kind and r,
  each within its size's cap. The first search of a kind that reaches its cap, or that its row
  refuses, MUST end that kind's searches at that size; the refusal is written in the search's
  `projection` record (D5).
  For an ARX design, r = 1 is the box's bound over one call (inherited FR-038). A search that does
  not depend on the size, such as that box search, runs first, under the 4×4 cap, charged to the
  candidate's trail row, and its bound is read at every size.
  A size-independent search that reaches its cap or is refused ends that kind's searches at every
  size, the candidate then being decided at 16×16 under FR-018 with no hour at 8×8 or 4×4. A kind's
  climb at a size ends at the first r at which its established bound, searched or summed, has weight
  above 128: where the sums already exceed it, no search of that kind runs at that r or beyond.
- **FR-016**: At every r, a kind's established bound at a size MUST be the larger of its searched
  bound, where one exists, and the largest sum W(r₁) + W(r₂) over r₁ + r₂ = r, r₁ and r₂ at least 1,
  of that kind's established bounds at that size, sums included, so that every split of r into
  shorter spans counts; W(r) is a bound's weight, the −log₂ of the probability or squared
  correlation it bounds, so that a bound lies below 2⁻¹²⁸ where its weight exceeds 128. A sum is
  written as a `bound` record with method `split`, citing its two parts by record ID and SHA-256,
  computed by code in exact arithmetic, with the scope every bound states: single trails under the
  usual independence assumptions, clustering into differentials and linear hulls and key-dependent
  effects open for the cryptanalysis feature. A sum never cites an `inconclusive` record. A sum
  rests on each part bounding every trail over any span of its length: the parts count whole cycles,
  a cycle being the shortest run of rounds after which the round structure repeats, constants aside
  (one round for feature 004's designs, whose layers in turn `active_sbox.py` takes as one round's
  `Cycle`), each span starting at a cycle's first round; a design whose rounds repeat in no such
  cycle, or that holds an addition of a committed constant, whose parts' bounds depend on the
  constants of the rounds they cover, takes no sum. A design holding such an addition takes no other
  bound that rests on the repetition either: no floor taken from shorter spans inside a search (the
  floors of Matsui's lemma in `active_sbox.py` and `long_trail.py`) and no active-box count
  multiplied by one box's bound over one call; its bounds come only from searches that model each
  round's constants, by a tool validated for such additions (inherited FR-039). Inherited FR-023's
  "the trail bounds and the dependency matrices read no constant value" holds for designs without
  such additions, and a design with them covers each call type's permutation in its bounds, as in
  its other constant-dependent evidence. An established bound is a searched bound of status `pass`
  from a validated tool that passed its cross-check on the candidate, or a `split` record whose
  parts are established, never a capped, refused or blocked record. A sum may join parts from
  different methods (an ARX box's bound over one call with active-box counts), each part established
  and of the same candidate, kind, size and width. Every `split` record states feature 004's scope
  statement word for word, and it is a bound record for every inherited eligibility item. Where a
  cycle spans more than one round, the climb counts whole cycles: searches and sums at each whole
  number of cycles, and R_bound is the smallest whole number of cycles, counted in rounds, at which
  both kinds' bounds lie below 2⁻¹²⁸; R and Δ count rounds.
- **FR-017**: R_bound at a size MUST be the smallest r at which both kinds' established bounds lie
  below 2⁻¹²⁸. The climb continues by sums after the searches end, up to R_max = 64 (D5); where no
  r up to R_max qualifies, the candidate has no R_bound at that size.
  R_max = 64 bounds R_bound + Δ at 66; the round rule's R, the largest of 2·R_dist, R_bound + Δ and
  2·max(R_f, R_b), may exceed it, and the tools hold every R the rule gives, a table for a larger R
  being generated and checked as inherited FR-023 asks of every rise. R_bound, once the climb sets
  it, is not lowered by any later search; R follows the round rule.
- **FR-018**: A candidate without R_bound at 16×16 MUST be decided `ineligible` before any of its
  production-width hours at 8×8 or 4×4 are charged. A replacement may then be entered under the
  inherited stop rule. The decision comes as soon as either kind's established bounds at 16×16
  cannot pass weight 128 by R_max; a search of the other kind then running stops, its record
  `inconclusive` and its hours charged. The cause is the candidate's own, a replacement being
  possible, unless it is a row that cannot hold the run at its recorded need, which is shared, as
  inherited (ANA-078). A size-independent search's hours count at no size: they are charged to the
  trail row before the 16×16 climb.
- **FR-019**: A trail record MUST hold the difference or mask at the input and output of every
  nonlinear operation of every round, and the state at every round boundary, so that its weight
  follows by exact integer arithmetic from the characteristic and the candidate's committed
  operation list alone, with, where the list holds an addition of a committed constant, the
  committed constant table, which the record names by SHA-256 (D9). The data model fixes the format
  before the first trail search. A nonlinear operation is one modular addition or subtraction on
  w-bit words, one addition or subtraction of a committed constant, or one S-box applied to its
  input bits; an S-box layer is recorded S-box by S-box. A bitwise Boolean function is recorded as
  the S-boxes the validated tool counts: where updates in turn form one invertible map per bit
  position, that map, recorded before its first update and after its last (feature 004's four-update
  NOR network: one 4-bit S-box per bit position, table 9 c 3 0 2 5 4 7 6 1 a b 8 d e f); inside one
  update, its function F per bit position, the table F's truth table over the bits it reads, an
  addition or subtraction that follows F being its own operation.
- **FR-020**: The re-check MUST recompute every `split` bound from its parts, and every trail's
  weight as an exact rational, with every transition checked. A trail with probability or squared
  correlation above 2⁻¹²⁸ is classed a confirmed vulnerability of the rounds it covers and enters
  R_dist; one at or below 2⁻¹²⁸ is classed `none`. A disagreement is a tool defect that blocks the
  candidate (inherited FR-065).
  The exact weights are the differential probability and squared correlation of a two-input addition
  or subtraction modulo 2^w; for an addition of a committed constant c, a subtraction being the
  addition of −c, the probability over the 2^w inputs that (x ⊕ α) ⊞ c = (x ⊞ c) ⊕ β and the squared
  correlation of u·x ⊕ v·(x ⊞ c), each computed exactly by the carry's two-state automaton over the
  bits of c; and an S-box's table entry; masks pass the linear steps between recorded points through
  the transpose. No trail search runs on an operation list holding any other nonlinear operation
  until data-model §3 defines its weight; the candidate is `blocked` for that cause meanwhile, so
  that no trail is left out of R_dist. This class replaces feature 004's data-model row for trails,
  and a trail at or below 2⁻¹²⁸ is no finding under security.md §9.1.
- **FR-021**: A proof that carries a bound to a larger size MUST stay what feature 004's FR-038
  makes it, a check beside the computed bounds, written for the selected candidate only (D11).

**Evidence, selection and the stop (User Story 4)**

- **FR-022**: The structural checks, the bias rule, the round rule (Δ = 2), the nonlinearity choice
  rule, eligibility, selection and the stop rule MUST apply as inherited, with R_bound from FR-016
  and FR-017, the budgets of FR-005 to FR-009, the claimable sizes of D13 and the families of D14.
  Every reduced-width score of the D4 choice comes before the first production-width search, the
  16×16-first order being the production width's. While an exact D4 tie waits, the two
  representatives' production-width climbs run in that order, 16×16 first, and only as far as R at
  4×4 needs; the tie-break reads R at 4×4 once both have it, or `ineligible` once either is decided
  so, a decision at 16×16 under FR-018 included. D4's cost model scores this feature's candidates
  unchanged, its direction kept. A replacement takes its family's row, the budget allowing it while
  that row holds the recorded need of each run the rules require at every size. Feature 004's FR-026
  figures, with the goal of 10⁸ words per second, and the constants' ROM size per food node are
  reported for each candidate at every size where it has R, at that R, whatever the round rule
  gives; a candidate decided `ineligible` at 16×16 has no R and no `cost` record, its decision entry
  saying so; a candidate whose R puts the goal out of reach stays eligible. The selection rule reads
  R as established, whatever its route, with no adjustment for a sum's weaker bound.
- **FR-023**: A feature-004 design entered again (D1) MUST be a new candidate with a new ID, counted
  as evaluated from its first entry; its feature-004 records are cited as prior results, never as
  its evidence, and every kind of evidence about the design runs again under this protocol. The
  inherited constant rule holds no ID, so an unchanged design at an unchanged variant receives
  feature 004's constants exactly. A design is derived from a feature-004 design when its operation
  list is that design's, unchanged or changed only as a variant or a fix in the inherited sense; a
  structural change makes a new design, whose `derived_from` still names its starting point, with
  the change listed. D4 scores a re-entered design here like any other, feature 004's D4 record
  cited as a prior result only, and the design meets every inherited hardware rule. An unchanged
  re-entered design is a candidate of this feature, its permutation and constants equal to feature
  004's, and its `proposed` entry says so, `rationale.md` too where it is selected, and the
  selection-bias statement for each; the inherited rule on what makes a new candidate governs
  changes within this feature.
  This feature's candidates read the constant rule as research R15 fixed it at 99e6994 and the
  refused list `research/005/refused-constants.json`, created in plan phase 1 as a byte copy of
  feature 004's `research/004/refused-constants.json` at 99e6994 (66 entries, SHA-256
  `cdbcb8031d1de839dacd71abcabdec38869fa6b102c6e86f10cfea2eb52a8a95`), growing only by this
  feature's stricter changes. The rotation ranking chose a design's amounts and is part of the
  design, not evidence about it: an unchanged re-entered design keeps the amounts feature 004's
  ranking chose at width 16, part of its committed operation list, its ranking record cited as a
  prior result; where inherited research R6's rule fixes this feature's D4 width at 8, inherited
  FR-024 searches its amounts again at 8, as for every entered candidate, and amounts that come out
  otherwise make it a variant (`relation` `derived`), its permutation and constants no longer
  feature 004's.
- **FR-024**: The final report and the design rationale MUST state the selection bias over every
  design considered in features 004 and 005, by family and with each design's outcome: B1 and A1
  `ineligible`, B2 and A2 proposed and declined, never evaluated, feature 004's D4 record and its
  stop; every design of this feature; which feature-004 design, if any, a candidate derives from;
  and the family-wise rate of chance firings of the bias rule over this feature's tests, feature
  004 having run none at w = 32 (D10).
  The statement reports and changes no threshold, rule or decision; it, the projection table and the
  final report keep to bound wording and state no property of any design, under the claim test's
  rules.
  The projection table holds numbers, record IDs and fixed field names and no prose, so that the
  wording rule binds the Markdown that renders it, the final report among them, which the claim test
  scans. The final report states that every result of the frozen candidate is on development inputs
  chosen among up to eight evaluated candidates, feature 004's two and up to six of this feature's,
  beside the two declined proposals, so that feature 008's held-out evaluation is the unbiased test.

**The model, reviews and freeze (User Story 5)**

- **FR-025**: After a selection, the model, constants, vectors, constructed states, second
  transcription, design rationale, review package, reviews and freeze MUST follow feature 004's
  requirements for them, for `phyco-v4`, under this feature's paths.
  The design document, `rationale.md` and the review package state each R_bound's route per size and
  kind (the searched records up to the first cap, then the `split` records with their parts) and
  mark each bound searched or `split`.
  The routes stand in the design document's chapter "Permutation", in a section "Round counts", and
  in `rationale.md`'s chapter "Margin", each citing its searched and `split` records by ID and
  SHA-256; in `rationale.md` a searched bound and a `split` bound each carry the label "fact",
  citing the record, with the condition FR-016 asks of a sum stated beside the `split` bound as an
  "argument" (inherited FR-062).

**Documents, register and reports**

- **FR-026**: Every hand-written document of this feature MUST carry the disclaimer naming
  `phyco-v4` that opens this spec, word for word, held in `protocol/disclaimer.py` as feature 005's
  constant. The claim test MUST cover this feature's documents, its reports and `phyco-v4` with
  feature 004's rules, `v4-A<k>` and `v4-B<k>` among its model words, from plan phase 1, before "L1
  recorded" can be set; once it does, it scans every document of this feature written before it, the
  checklists and `checklist-choices.md` included, each finding fixed or allow-listed before plan
  phase 2's probes start. A generated checklist line that the claim test flags is never rewritten:
  it gets an allow-list entry with its reason, stating that the line is a checklist question naming
  a parameter, a file or a rule, or quoting the passage it asks about, and stating nothing of its
  own; the owner reviews such entries at the next ⛔ gate, as inherited FR-069 has every entry added
  since the last gate reviewed. Such an entry is written once the item's state is final, after its
  round's verification, naming the line as it then reads; a later change of state gets a new entry,
  and the old one is removed in the same commit.
- **FR-027**: The spec approval MUST bring a new version of security.md, with its history entry: a
  row for `phyco-v4` in §1.1 and its line in §15's register, L0 with no claim and not for secrets;
  §15's L1 gate naming this spec's FR-013 beside feature 004's FR-012; and §22 with this feature in
  stage 5a.1's place for `phyco-v4` and the later stages renumbered (D12). `protocol/claims.json`
  gains `phyco-v4` at L0 in the same change. README gains its line on `phyco-v4` at the end of the
  feature (inherited FR-051).
  A later version, 2.19, gives §5's note on T11 `phyco-v4` beside `phyco-v3`, §1.1's cells for
  `phyco-v4` a 256-bit key and a 128-bit nonce as targets and its state "not specified until the
  selection", and row 5a.3 "features 004 and 005's order of sizes".
  Row 5a.1b's status names the gates this feature has passed and the next one, never the checklist
  rounds, each gate in a security.md version of its own, as 2.10 recorded feature 004's plan
  approval; version 2.20 recorded the plan approval, with row 5a.3 naming the order of sizes that
  features 004 and 005 keep for vectors and statistical evaluation, and version 2.21 drops the
  rounds from the row. The versions that record a change of `phyco-v4`'s level (FR-013) form a
  family of their own.
- **FR-028**: Development inputs only, derived as in feature 004 under the namespace
  `phycoweb-005/`; no held-out set exists in this feature (inherited FR-040).
- **FR-029**: The final report MUST follow feature 004's FR-052 and add: the projection table beside
  the measured hours of every heavy run, the sums each R_bound rests on, and the selection-bias
  statement of FR-024.
  It states each R_bound's route, one resting on r·W(1) alone named as such.
- **FR-030**: FUT-SEC-1 to FUT-SEC-9 MUST be carried as requirements traced to tasks and evidence,
  as in feature 004's table "Security Policy traceability", for `phyco-v4`; FUT-SEC-8 is met by
  feature 004's demonstration
  (`reports/004-crypto-architecture-v3/fut-sec-8/demonstration-20261104T165604Z-4406adb9.json`,
  SHA-256 `5c93e850284120dc9935d3e4317b8dc94df3a7b79fc038dbc8a6c49508613651`, raw) and its review
  (ffb1425) and is not repeated, since no new design changes `phyco-v2`'s seed bound; the inherited
  guard on instantiation code reads feature 004's row "FUT-SEC-8 result review" and that record at
  HEAD, from feature 004's spec and paths, as the claim test reads them (FR-013), this table adding
  no such row; FUT-SEC-7 stays open for the statistical feature.
  FUT-GRID-1 to FUT-GRID-5 and FUT-HW-1 to FUT-HW-5 are carried and traced as in feature 004's
  table. The register's entry for `phyco-v4` gains `fut_sec`, the expected statuses of that table,
  written with the claim test's extension in plan phase 1.
  `phyco-v4`'s `fut_sec` names the later stages by security.md §22's numbers since 2.18 (the
  analysis feature 006, the statistical re-validation feature 008); `phyco-v3`'s entry, feature
  004's, stays as written and reads under FR-001's rule.
- **FR-031**: Every change to this spec, the plan or their documents after the plan approval and
  before any result MUST be listed in `checklist-choices.md`: each row of a checklist round, or of a
  section of its own for a batch outside a round, is a listed change; the list "Rows that change the
  protocol" names those that touch a rule, with their direction (stricter, settled, or a reading set
  aside), every other row being a clarification listed by its table alone; each is entered in
  feature 005's protocol change log after its first entry, before any result, citing its row. A
  reading set aside is decided in the row "Readings set aside" at the tasks approval; a change made
  after the tasks approval and before any result is made only in a form that sets no reading aside
  (for a claim-test finding, an allow-list entry), or waits for the owner's decision in a row
  "Readings set aside <k>" before any result it affects. The protocol change log is created in plan
  phase 1, after the tasks approval and before any evidence run, its first entry naming by SHA-256
  FR-001's baseline documents, `research/005/plan-projections.json` as committed then, feature 004's
  refused list (FR-023), the spec as the spec approval names it and the plan's documents at 74dd867,
  plan.md and research.md as the plan approval names them, data-model.md
  `77c23010cefab81959f75f78c37a414a9b64d2a035768d0367027d52b9c3327c`, contracts/cli.md
  `f295367ada174a3274adfcdc10e7f71997553547e4fbe3af9ea55b0234f29cba` and quickstart.md
  `6f6c4cac173ce20dccc2c049046d76eed1610e024368fa4ea00601092d87d01d`; the provenance log of this
  feature's hand-written documents starts in the same phase, its first entries covering the
  documents written before it.
  Feature 005's provenance log also covers every file outside its own paths that this feature
  changes, the files both features share (security.md, `protocol/claims.json`, `.gitattributes`,
  README) and the shared code with its tests (research R9) among them, each from its first change by
  this feature, entered whole, as inherited FR-067 enters scripts and tests, feature 004's log
  keeping its last entries for them.

### Pre-registered Design Protocol: the changed rules

The inherited protocol applies except for these rules, each fixed at spec approval and afterwards
only stricter (inherited FR-044): every later change, under every reading of the old text, lies in
its rule's stricter direction or settles an open case by its most conservative reading, as
`checklist-choices.md`'s "How to answer" states, and is recorded as FR-031 asks.

- **The climb (round rule's R_bound)**: FR-014 to FR-018. *Stricter means*: R_max only falls.
- **The budgets (stop rule)**: FR-004 to FR-009. *Stricter means*: caps, rows, the ceiling and the
  candidate limit only fall, the margin only rises, and the thread count does not change.
- **Trail records**: FR-019, FR-020. *Stricter means*: no change.
- **The security target's place**: FR-011, FR-012. *Stricter means*: no change.
- **The security target's parameters**: FR-010. *Stricter means*: the capacity only grows; the key
  and the nonce do not change.
- **Selection bias**: FR-024. *Stricter means*: designs counted are only added.

### Key Entities

- **Baseline protocol**: feature 004's documents named by commit and SHA-256, with the reading
  rules of FR-001.
- **Calibration**: per kind of evidence, feature 004's projected hours against measured hours, and
  the factor taken from them.
- **Projection table**: per kind of evidence and claimable size, the projected need of each run,
  its row and its cap, with the margin and the ceiling.
- **Split bound**: a `bound` record with method `split`, at a size, kind and r, citing the two
  established bounds it sums.
- **Trail characteristic**: the difference or mask at the input and output of every nonlinear
  operation of every round, with the state at every round boundary.
- **Candidate**: a design `v4-A<k>` or `v4-B<k>`, with the feature-004 design it derives from, if
  any.
- **Selection-bias statement**: every design of features 004 and 005, by family, with its outcome.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Before the first candidate is proposed, the projection table covers 100% of the runs
  the rules require of one candidate at each of the three claimable sizes, and every row holds at
  least twice the projected need of its runs, the rows of the families that hold candidates
  (FR-009).
- **SC-002**: The security-target review's approval commit precedes the candidate log's first
  `proposed` entry.
- **SC-003**: No climb ends at a capped search while a sum could continue it: every entered
  candidate ends its climbs with R_bound at each claimable size, or with one of FR-017's or
  FR-018's recorded causes.
- **SC-004**: Every candidate without R_bound at 16×16 is decided before any of its
  production-width hours at 8×8 or 4×4 are charged.
- **SC-005**: On a fresh clone, from committed files alone, the re-check recomputes 100% of the
  `split` bounds and 100% of the trail weights, transitions and classifications, with 0
  disagreements.
- **SC-006**: The selection-bias statement lists 100% of the designs considered in features 004 and
  005, each with its outcome.
- **SC-007**: The claim test reports 0 findings over this feature's documents, reports and the
  register; every hand-written document carries the disclaimer naming `phyco-v4`; and security.md
  §1.1, §15 and the register agree on `phyco-v4`'s level, the one its rows give.
- **SC-008**: No heavy run exceeds its row, and the heavy runs of the whole feature stay within the
  ceiling.
- **SC-009**: For every heavy run, the final report gives the ratio of measured to projected hours.
- **SC-010**: The feature ends with `phyco-v4` frozen, with R at every claimable size, its vectors
  reproduced on both platforms and the second transcription agreeing at 100% of the steps of the
  committed vectors, or with a stop recorded with what was reached; either way the final report
  recommends proceed, revise or stop.

## Assumptions

- Feature 005 writes environment records of its own, each with its row, even where the environment
  equals feature 004's records 3 and 4.
- The machine and environments are feature 004's (research R1): Windows with Python 3.10.11, WSL
  with Python 3.14.4, 32 logical processors and 68 GB of memory. A change brings a new environment
  record, as inherited.
- Feature 004's validated tools are used unchanged where they serve; no download is expected, and
  any file still needs the owner's permission for that file, with its name, source, size and
  licence.
- Feature 004's operation lists of cand-A1 and cand-B1 serve this feature's projections only. They
  enter as candidates only under D1, as new candidates.
- The owner decides each gate in writing or by a commit, and the agent records written decisions
  quoting them, as in feature 004.
- Whether a 16×16 grid fits the XC7A100T is a question for the hardware feature. The claim at
  16×16 needs its bounds here whatever the answer (D13).
- The claim test is extended to this feature in its plan; until then it covers feature 004 only.
- An external design review may not be arranged; the row then reads "not arranged".
