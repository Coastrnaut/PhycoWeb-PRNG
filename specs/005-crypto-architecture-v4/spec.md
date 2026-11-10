# Feature Specification: Cryptographic Architecture, Second Design Round (phyco-v4)

> This feature makes no security claim. No PhycoWeb-PRNG model, `phyco-v4` included, may be used
> to generate secrets; use an established cryptographic random-number generator for keys,
> nonces, tokens and salts. Passing statistical tests does not show cryptographic security.

**Feature Branch**: `005-crypto-architecture-v4` (directory only; no git branch, as for feature 004)

**Created**: 2026-11-09

**Status**: Spec approved by the owner (2026-11-09), with decisions D1–D14 as their defaults; plan
approved (2026-11-09), with the run limits extended (option E); checklist choices of round 1 answered
in advance and applied (2026-11-09)

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
| Tasks approval | _pending_ | _pending_ | _pending_ | |
| Checklist choices, round 1 ([checklist-choices.md](./checklist-choices.md): the 86 items of the six first-run checklists) | Coastrnaut (repository owner) | 2026-11-09 | Approved | Answered in advance on 2026-11-09, with the instruction to loop the checklists until a re-run finds no new item: "you have my approval of all suggestions to continue without human interaction", which takes option A of every row and approves the round's list "Rows that change the protocol", written with its rows before they were applied (FR-031). Applied the same day to this spec, the plan's documents, security.md (2.19) and `.gitattributes`; no row sets a reading aside. Written and committed by the agent on that word |
| Readings set aside (FR-031: each change whose direction sets a reading of the old text aside, decided at the tasks approval) | _pending_ | _pending_ | _pending_ | Lists each such change with the case under which the old text fails and the owner's decision, entry by entry; none so far |
| Place check (a comparison of the edits with the rows that made them, where one is made) | _pending_ | _pending_ | _pending_ | Names the comparison's file by SHA-256 and confirms each place an edit changed that no row made |
| Tool acquisition (each download: name, source, size, licence) | _pending_ | _pending_ | _pending_ | No download is planned; a file needs a row of its own, "Download <n>", before it is fetched |
| Security-target review (`phyco-v4`: the design document's chapters "Security target" and "Mode", before any candidate is proposed) | _pending_ | _pending_ | _pending_ | Names the chapters' version and SHA-256 (FR-011). The candidate log refuses a first `proposed` entry until this row reads Approved at HEAD |
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
gives one in writing for it. Inside inherited FR-043's window, from the owner design review's approval
to the final result review, the owner's written word, recorded and committed by the agent quoting it,
stands in place of the owner's commit, as in feature 004 from 2026-11-05.

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
| D5 | The climb past a capped search | Sums of shorter spans continue it; searches of a kind at a size end at the first cap or refusal; the climb starts at r = 1; R_max = 64, which bounds R at R_max + Δ = 66 and so the largest constant table, vector and cost figure the tools hold | Feature 004's rule: the climb ends at the first cap | FR-015 to FR-017 | Confirmed 2026-11-09 |
| D6 | Order of sizes for the bounds | 16×16, then 8×8, then 4×4; every other kind keeps 4×4 first | 4×4 first for every kind, as in feature 004 | FR-014, FR-018 | Confirmed 2026-11-09 |
| D7 | Budgets | Fixed in the plan from calibrated projections, every row holding at least twice its projected need, within a ceiling of 720 h of heavy runs for the whole feature, which the owner raised to 2,200 h at the plan approval, as FR-008 allows | Feature 004's values: per candidate 48 h of trail searches at 8 h each, 6 h of structural checks and 12 h of bias tests, with a feature-wide row of 66 h | FR-004 to FR-009 | Confirmed 2026-11-09 |
| D8 | Thread count | Fixed once in the plan from the calibration, the same for every search, recorded in every record | One thread, as in feature 004 | FR-007 | Confirmed 2026-11-09 |
| D9 | Trail records | The characteristic at every nonlinear operation; a trail at or below 2⁻¹²⁸ classed `none` | Feature 004's characteristic, the difference or mask after every round | FR-019, FR-020 | Confirmed 2026-11-09 |
| D10 | Selection bias | Counts feature 004's B1 and A1, the declined proposals B2 and A2, its D4 record and its stop, with every design of this feature | The evaluated candidates of both features only | FR-024 | Confirmed 2026-11-09 |
| D11 | A proof that carries a bound to a larger size | A check beside the computed bounds, for the selected candidate only, as in feature 004 | A source of R_bound above 8×8, with acceptance rules fixed at spec approval | FR-021 | Confirmed 2026-11-09 |
| D12 | Roadmap numbering | This feature takes stage 5a.1's place for `phyco-v4`; the features of stages 5a.2 to 5a.6 become 006 to 010 | Those features keep their numbers, and row 5a.1 names this feature beside feature 004 | FR-027 | Confirmed 2026-11-09 |
| D13 | Claimable sizes | 4×4, 8×8 and 16×16, each needing R_bound and every eligibility item, as in feature 004; a claimable size that does not fit the XC7A100T stays claimable, covered by the implementation feature's simulation alone (security.md §22 row 5a.5) | 16×16 claimable only where its R_bound and every item are established, otherwise a research size outside every claim | FR-022 | Confirmed 2026-11-09 |
| D14 | Families | Both; D4 chooses the family as in feature 004, the other analysed at the production width only if the chosen one ends with no eligible candidate. Reason: under FR-018 a family that cannot be bounded at 16×16 ends at its first searches there, so the fallback reaches the other family at that cost; the plan's projections are planning data and change no rule | Both analysed at the production width, in the order of their D4 scores | FR-022 | Confirmed 2026-11-09 |

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
- **The first search at 16×16 capped**: with no established bound of that kind at 16×16, no sum
  exists; the candidate is `ineligible` at once (User Story 3, scenario 2).
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
- **The security-target review changes a parameter**: the key, nonce or capacity is changed before
  any candidate is proposed, and the output limits are recomputed.
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
  where this spec changes it, by number. The protocol change log's first entry names these
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
  at each food node, the replaced mechanisms and the slime-mould mapping's one sentence. The sizes
  5×5 to 7×7 and 9×9 to 15×15 are supported variants, permutation-only and outside every claim, as
  feature 004's variant table lists them.

  The spec, research and design versions that this feature's records cite are copied under its paths
  (`spec-versions/`, `research-versions/`, `design-versions/`), and the claim test reads each copy
  as the document it copies. A reproduction re-runs and re-checks what inherited research R16 lists;
  the probes and the projection table are re-checked, never re-run.
- **FR-002**: The model ID MUST be `phyco-v4` and candidate IDs `v4-A<k>` and `v4-B<k>` (D1);
  feature 004's IDs keep their records.
- **FR-003**: Feature 004's records, logs and documents MUST be read-only inputs: this feature
  edits none of them.
  The feature setting that this feature adds to the code both features share (research R9) leaves
  feature 004's verdicts unchanged: feature 004's re-check at HEAD gives the same result before and
  after the change, a test showing it. Feature 004's FR-053 test writes its records under the active
  feature's paths once that setting exists; until then no whole-suite run is made for this feature.

**Every run planned before any candidate (User Story 1)**

- **FR-004**: The plan MUST derive, from feature 004's committed `projection` records and the
  measured hours of the runs they projected, a calibration per kind of evidence, and for the bound searches per tool and size with research R1's
  transfer rule, the ratio of measured to projected time, and apply it to every projection of this
  feature. The calibration
  and the records it reads MUST be committed with the plan.
  It reads feature 004's records as committed at 99e6994, so that a later record never changes it,
  and `research/005/plan_projections.py --check` MUST pass on both platforms.
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
  caps, the rows, the ceiling and the candidate limit MUST only fall (inherited FR-044).
  The plan approval fixed the values of option E, which the owner chose before the approval was
  recorded (research R3). A clarification of the calibration's rule that leaves every factor as
  computed is no change. A probe that shows a need above its row is reported before the first
  `proposed` entry; the owner may then lower the candidate limit or take D13's alternative, each a
  stricter change, and no row is raised.

**The security target first (User Story 2)**

- **FR-010**: The chapters "Security target" and "Mode" of this feature's design document MUST
  start from feature 004's `design.md`, Version 0.4 (SHA-256
  `60a9c9496792c7f3ca98ddb4df3e2c481c8c4b8059780ab2f29044e53cbd9e9b`), read with `phyco-v4` for
  `phyco-v3` (D3), and list every change with its reason.
  The document is Version 0.5, continuing feature 004's numbering, and each later change makes a new
  version. `phyco-v4`'s key holds 256 bits of entropy, its secret state reachable from the key is
  the capacity, 384 bits at every claimable size, and the bound these place on any level is the size
  profile's 128 bits at every claimable size, a target and a ceiling, not a claim (constitution,
  Security Policy).
- **FR-011**: The security-target review (⛔) MUST be held before the first candidate is proposed.
  Its row names the chapters' version and their SHA-256, with the security target's files, written
  before the review with R as `<R4>`, `<R8>` and `<R16>`, and the candidate log MUST refuse a first
  `proposed` entry until the row reads Approved at HEAD and the projection table exists (FR-005).
- **FR-012**: Every item of the security target that depends on a selected design MUST be listed in
  the chapter as open and checked at the owner design review: the round counts that the parameter
  table holds as `<R4>`, `<R8>` and `<R16>`, with every figure computed from them; the margin of
  instantiation's diffusion over R_f (inherited FR-029), read from the same dependency measurement as
  FUT-GRID-3's warm-up; the first-order related-key and related-nonce differences (inherited research
  R4); and the functionality class (inherited FR-011).
  Once every R is known, the chapters and the security target's files are written again and reviewed
  in "Security-target review 2", which reviews the round counts and the open items only. An open
  item that fails at the owner design review fails the candidate's eligibility item, as inherited;
  L1 stays while the reviewed chapters do not change, and a change to the target is reviewed again,
  with "L1 recorded <k>".
- **FR-013**: The row "L1 recorded" MUST name this feature's security-target review row and feature
  004's FUT-SEC-8 result review row (ffb1425), each with what it reviewed by path and SHA-256. The
  claim register gives `phyco-v4` L1 while both read Approved and those hashes hold at HEAD, and L0
  otherwise, as feature 004's rules give it for `phyco-v3`.
  Feature 004's FUT-SEC-8 result review row is read by the claim test from feature 004's spec at
  HEAD. "L1 recorded" is set only once the claim test covers `phyco-v4` (FR-026; plan phase 1 before
  phase 3). L1 rests on the chapters as the review read them: when R fills them in, the named hashes
  no longer match, and the level reads L0 until "Security-target review 2" and "L1 recorded 2" read
  Approved.

**The climb (User Story 3)**

- **FR-014**: At the production width, each candidate's trail-bound climbs MUST run at 16×16 first,
  then 8×8, then 4×4 (D6). Every other kind of evidence keeps feature 004's order, 4×4, then 8×8,
  then 16×16 (FUT-GRID-5).
  FUT-GRID-5's order governs vectors and statistical evaluation per size, which keep 4×4 first, as
  the hardware features' RTL and board do; trail bounds analyse the permutation, not a size's
  validation, and run where their cost is highest first.
- **FR-015**: At each claimable size, the climb MUST start at r = 1, with one search per kind and r,
  each within its size's cap. The first search of a kind that reaches its cap, or that its row
  refuses, MUST end that kind's searches at that size; the refusal is written in the search's
  `projection` record (D5).
  For an ARX design, r = 1 is the box's bound over one call (inherited FR-038). A search that does
  not depend on the size, such as that box search, runs first, under the 4×4 cap, charged to the
  candidate's trail row, and its bound is read at every size.
- **FR-016**: At every r, a kind's established bound at a size MUST be the larger of its searched
  bound, where one exists, and the largest sum W(r₁) + W(r₂) over r₁ + r₂ = r, r₁ and r₂ at least
  1, of that kind's established bounds at that size, sums included, so that every split of r into
  shorter spans counts; W(r) is a bound's weight, the −log₂ of the probability or squared
  correlation it bounds, so that a bound lies below 2⁻¹²⁸ where its weight exceeds 128. A sum is
  written as a `bound` record with method `split`, citing its two parts by record ID and SHA-256,
  computed by code in exact arithmetic, with the scope every bound states: single trails under the
  usual independence assumptions, clustering into differentials and linear hulls and key-dependent
  effects open for the cryptanalysis feature. A sum never cites an `inconclusive` record.
  A sum rests on each part bounding every trail over any span of its length: the round structure
  repeats from round to round, constants aside, or, for layers in turn, the parts count whole
  cycles; a design whose rounds differ otherwise takes no sum. An established bound is a searched
  bound of status `pass` from a validated tool that passed its cross-check on the candidate, or a
  `split` record whose parts are established, never a capped, refused or blocked record. A sum may
  join parts from different methods (an ARX box's bound over one call with active-box counts), each
  part established and of the same candidate, kind, size and width. Every `split` record states
  feature 004's scope statement word for word, and it is a bound record for every inherited
  eligibility item.
- **FR-017**: R_bound at a size MUST be the smallest r at which both kinds' established bounds lie
  below 2⁻¹²⁸. The climb continues by sums after the searches end, up to R_max = 64 (D5); where no
  r up to R_max qualifies, the candidate has no R_bound at that size.
  R_max = 64 bounds the round rule's R at R_max + Δ = 66, which fixes the largest constant table,
  vector and cost figure the tools hold. R_bound, once the climb sets it, is not lowered by any
  later search; R follows the round rule.
- **FR-018**: A candidate without R_bound at 16×16 MUST be decided `ineligible` before any of its
  production-width hours at 8×8 or 4×4 are charged. A replacement may then be entered under the
  inherited stop rule.
  The decision comes as soon as either kind's established bounds at 16×16 cannot pass weight 128 by
  R_max; a search of the other kind then running stops, its record `inconclusive` and its hours
  charged. The cause is the candidate's own, a replacement being possible, unless it is a row that
  cannot hold the run at its recorded need, which is shared, as inherited (ANA-078).
- **FR-019**: A trail record MUST hold the difference or mask at the input and output of every
  nonlinear operation of every round, and the state at every round boundary, so that its weight
  follows by exact integer arithmetic from the characteristic and the candidate's committed
  operation list alone (D9). The data model fixes the format before the first trail search.
  A nonlinear operation is one modular addition or subtraction on w-bit words, or one S-box applied
  to its input bits; an S-box layer is recorded S-box by S-box.
- **FR-020**: The re-check MUST recompute every `split` bound from its parts, and every trail's
  weight as an exact rational, with every transition checked. A trail with probability or squared
  correlation above 2⁻¹²⁸ is classed a confirmed vulnerability of the rounds it covers and enters
  R_dist; one at or below 2⁻¹²⁸ is classed `none`. A disagreement is a tool defect that blocks the
  candidate (inherited FR-065).
  The exact weights are the differential probability and squared correlation of a two-input addition
  or subtraction modulo 2^w and an S-box's table entry; masks pass the linear steps between recorded
  points through the transpose. An operation list holding any other nonlinear operation gets no
  trail record until data-model §3 defines its weight. This class replaces feature 004's data-model
  row for trails, and a trail at or below 2⁻¹²⁸ is no finding under security.md §9.1.
- **FR-021**: A proof that carries a bound to a larger size MUST stay what feature 004's FR-038
  makes it, a check beside the computed bounds, written for the selected candidate only (D11).

**Evidence, selection and the stop (User Story 4)**

- **FR-022**: The structural checks, the bias rule, the round rule (Δ = 2), the nonlinearity choice
  rule, eligibility, selection and the stop rule MUST apply as inherited, with R_bound from FR-016
  and FR-017, the budgets of FR-005 to FR-009, the claimable sizes of D13 and the families of D14.
  Every reduced-width score of the D4 choice comes before the first production-width search, the
  16×16-first order being the production width's. D4's cost model scores this feature's candidates
  unchanged, its direction kept. A replacement takes its family's row, the budget allowing it while
  that row holds the recorded need of each run the rules require at every size. Feature 004's FR-026
  figures, with the goal of 10⁸ words per second, and the constants' ROM size per food node are
  reported for each candidate at its R, up to R_max + Δ; a candidate whose R puts the goal out of
  reach stays eligible.
- **FR-023**: A feature-004 design entered again (D1) MUST be a new candidate with a new ID,
  counted as evaluated from its first entry; its feature-004 records are cited as prior results,
  never as its evidence, and every kind of evidence runs again under this protocol.
  The inherited constant rule holds no ID, so an unchanged design at an unchanged variant receives
  feature 004's constants exactly. A design is derived from a feature-004 design when its operation
  list is that design's, unchanged or changed only as a variant or a fix in the inherited sense; a
  structural change makes a new design, whose `derived_from` still names its starting point, with
  the change listed. D4 scores a re-entered design here like any other, feature 004's D4 record
  cited as a prior result only, and the design meets every inherited hardware rule.
- **FR-024**: The final report and the design rationale MUST state the selection bias over every
  design considered in features 004 and 005, by family and with each design's outcome: B1 and A1
  `ineligible`, B2 and A2 proposed and declined, never evaluated, feature 004's D4 record and its
  stop; every design of this feature; which feature-004 design, if any, a candidate derives from;
  and the family-wise rate of chance firings of the bias rule over this feature's tests, feature
  004 having run none at w = 32 (D10).
  The statement reports and changes no threshold, rule or decision; it, the projection table and the
  final report keep to bound wording and state no property of any design, under the claim test's
  rules.

**The model, reviews and freeze (User Story 5)**

- **FR-025**: After a selection, the model, constants, vectors, constructed states, second
  transcription, design rationale, review package, reviews and freeze MUST follow feature 004's
  requirements for them, for `phyco-v4`, under this feature's paths.
  The design document, `rationale.md` and the review package state each R_bound's route per size and
  kind (the searched records up to the first cap, then the `split` records with their parts) and
  mark each bound searched or `split`.

**Documents, register and reports**

- **FR-026**: Every hand-written document of this feature MUST carry the disclaimer naming
  `phyco-v4` that opens this spec, word for word, held in `protocol/disclaimer.py` as feature 005's
  constant. The claim test MUST cover this feature's documents, its reports and `phyco-v4` with feature
  004's rules, `v4-A<k>` and `v4-B<k>` among its model words, from plan phase 1, before "L1 recorded"
  can be set; once it does, it scans every document of this feature written before it, the checklists
  and `checklist-choices.md` included, each finding fixed or allow-listed before the next step.
- **FR-027**: The spec approval MUST bring a new version of security.md, with its history entry: a
  row for `phyco-v4` in §1.1 and its line in §15's register, L0 with no claim and not for secrets;
  §15's L1 gate naming this spec's FR-013 beside feature 004's FR-012; and §22 with this feature in
  stage 5a.1's place for `phyco-v4` and the later stages renumbered (D12). `protocol/claims.json`
  gains `phyco-v4` at L0 in the same change. README gains its line on `phyco-v4` at the end of the
  feature (inherited FR-051).
  A later version, 2.19, gives §5's note on T11 `phyco-v4` beside `phyco-v3`, §1.1's cells for
  `phyco-v4` a 256-bit key and a 128-bit nonce as targets and its state "not specified until the
  selection", and row 5a.3 "features 004 and 005's order of sizes".
- **FR-028**: Development inputs only, derived as in feature 004 under the namespace
  `phycoweb-005/`; no held-out set exists in this feature (inherited FR-040).
- **FR-029**: The final report MUST follow feature 004's FR-052 and add: the projection table beside
  the measured hours of every heavy run, the sums each R_bound rests on, and the selection-bias
  statement of FR-024.
  It states each R_bound's route, one resting on r·W(1) alone named as such.
- **FR-030**: FUT-SEC-1 to FUT-SEC-9 MUST be carried as requirements traced to tasks and evidence,
  as in feature 004's table "Security Policy traceability", for `phyco-v4`; FUT-SEC-8 is met by
  feature 004's demonstration (`fut-sec-8/demonstration-20261104T165604Z-4406adb9.json`) and its
  review (ffb1425) and is not repeated, since no new design changes `phyco-v2`'s seed bound;
  FUT-SEC-7 stays open for the statistical feature.
  FUT-GRID-1 to FUT-GRID-5 and FUT-HW-1 to FUT-HW-5 are carried and traced as in feature 004's
  table. The register's entry for `phyco-v4` gains `fut_sec`, the expected statuses of that table,
  written with the claim test's extension in plan phase 1.
- **FR-031**: Every change to this spec, the plan or their documents after the plan approval and
  before any result MUST be listed with its direction (stricter, settled, or a reading set aside) in
  `checklist-choices.md`'s lists "Rows that change the protocol", or beside the change, and entered
  in feature 005's protocol change log after its first entry, before any result; a reading set aside
  is decided in the row "Readings set aside" at the tasks approval. The protocol change log is
  created in plan phase 1, after the tasks approval and before any evidence run, its first entry
  naming FR-001's baseline documents and `research/005/plan-projections.json` by SHA-256; the
  provenance log of this feature's hand-written documents starts in the same phase, its first
  entries covering the documents written before it.

### Pre-registered Design Protocol: the changed rules

The inherited protocol applies except for these rules, each fixed at spec approval and afterwards
only stricter (inherited FR-044): every later change, under every reading of the old text, lies in its
rule's stricter direction or settles an open case by its most conservative reading, as
`checklist-choices.md`'s "How to answer" states, and is recorded as FR-031 asks.

- **The climb (round rule's R_bound)**: FR-014 to FR-018. *Stricter means*: R_max only falls.
- **The budgets (stop rule)**: FR-004 to FR-009. *Stricter means*: caps, rows, the ceiling and the
  candidate limit only fall, the margin only rises, and the thread count does not change.
- **Trail records**: FR-019, FR-020. *Stricter means*: no change.
- **The security target's place**: FR-011, FR-012. *Stricter means*: no change.
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
  least twice the projected need of its runs.
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
