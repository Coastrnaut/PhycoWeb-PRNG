# Implementation Plan: Cryptographic Architecture and phyco-v3 Design

**Branch**: `004-crypto-architecture-v3` (directory only; no git branch, as in the spec's
Assumptions) | **Date**: 2026-11-01 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/004-crypto-architecture-v3/spec.md` (approved
2026-11-01, with D1–D10 as clarified).

> This feature makes no security claim. No PhycoWeb-PRNG model, `phyco-v3` included, may be used
> to generate secrets; use an established cryptographic random-number generator for keys,
> nonces, tokens and salts. Passing statistical tests does not show cryptographic security.

## Summary

The feature runs in the spec's order, and each step needs the one before it:

1. **FUT-SEC-8 first (US1)**: a new C tool, `fast/seed_search.c`, checked word for word against
   both `phyco-v2` golden vector files, sweeps all 2³² candidates for the last two seed words of
   three development targets, under an hour on 32 threads (research R2). The owner reviews the
   result (⛔) before any `phyco-v3` key-loading code exists.
2. **Security target (US2)**: chapter 1 of the design document, "Security target", states the
   properties sought, s = 128, the 256-bit key and 128-bit nonce, threats T1–T11 and every generic
   bound per size, and the mode chapter beside it, "Mode", the keyed-duplex theorem with its
   preconditions; the security-target review covers both, with the security
   target's files (SEC-075). The output limits follow from the theorem at
   a target advantage of 2⁻⁶⁴ (R9, R10). Reading each theorem paper is a download; the owner
   approved every file of R19, as listed with its source, size and licence, on 2026-11-01.
3. **Design (US3)**: every candidate Π is written once as an operation list made only of
   invertible updates, so it is bijective by construction (R11). From that list come the
   evaluators, the inverse, dependency matrices, the cost model and the trail models. After
   selection come a hand-written standard-library model, `phycoweb/model_v3.py`, constants from
   a committed script, vectors at every size (R8), constructed-state vectors and a second
   transcription from a separate session (R17).
4. **Evidence (US4)**: tools first re-find known results (S12–S15 and the FUT-SEC-8 recovery on
   `phyco-v2`; published SPECK32, PRESENT and SPARKLE values, R12). Then structural checks
   (R13), the frequency and avalanche tests, related-key, related-nonce and rotational
   differences included (R4), and trail bounds, within a fixed budget per candidate and size by
   size from 4×4 (R7). The D4 score (R5, R6), the round rule and the stop rule decide.
5. **Review and freeze (US5)**: design rationale, review package, ⛔ owner design review,
   external review recorded as done or not arranged, ⛔ design freeze, then the final report
   with FUT-SEC-7 open for feature 007.

### Values this plan fixes before first use

The spec leaves these values to the plan. From plan approval they belong to the pre-registered
design protocol and may only become stricter (FR-044). The first six rows are the values the
owner asked the plan to fix. The next four list the other values that research.md marks
protocol, so that one list names them all: the plan approval covered research.md, so these rows
record those values and change nothing, except that the constant rule's early fixing is one of
the stricter checklist answers of 2026-11-01, and its values were settled by the answers to the
re-run the same day. The last row lists the spec's security parameters with their directions. Every
change from now on is an entry of the protocol change log `research/004/protocol-changes.jsonl`
(data-model §18). Its first entries, written when the log is created, record the answered rows of
every checklist round answered before the log is created, by the lists "Rows that change the
protocol" of checklist-choices.md, in round order, one entry per row, citing its ID; the constant
rule's values and its refused list's SHA-256 are among them, `settled`
before the first candidate is scored.

| Item left to the plan | Value fixed here | Research | Stricter means |
|-----------------------|------------------|----------|----------------|
| Development inputs (FR-040) | Key, nonce, personalization string, reseed input and test state i = SHA-256 of the ASCII string `phycoweb-004/dev/<kind>/<i>` (test states: `phycoweb-004/dev/state/n<n>w<w>/<i>/<j>`); uniform controls under `phycoweb-004/control/`; the loader refuses every other namespace and any index outside a use's declared range; fingerprints checked at load; no held-out set. Beside the derivation, a closed class of constructed inputs fixed by public rules before first use (R3; data-model §2) | R3 | the derivation does not change |
| Inputs per bias measurement (bias rule) | Two sets of N = 2²⁰ instantiation states per claimable size, key i with nonce i and key 0 with nonce i, through Π and Π⁻¹, S = 4b bits per round count; the avalanche measurement of FR-037 also feeds R_dist: N_a = 2¹³ states per flipped bit, per key or nonce bit flipped in instantiation states and per rotation amount, threshold 0.005/(128·S_A) with S_A = (2·\|F\| + 384 + 2(w − 1))·b, so it adds at most 0.005 per size to the chance of a false firing; each avalanche run cross-checked against the exact dependency matrices; controls with the same counts; verdicts from integer critical counts | R4 | only a change that can add firings and never remove one: N, N_a, F and the sets only grow, every recorded firing stands, and a larger N, N_a or F, or a new set, is tested in addition, so R can only rise |
| Operation-count cost model (D4) | 6-input LUTs per node and round: 0 for rotations, constant shifts and wiring; w per bitwise word operation with fan-in k ≤ 6; w·⌈(k − 1)/5⌉ above; w and one carry chain per addition or subtraction; no fusion | R5 | no stricter direction, so in effect no change from plan approval, and none after the first score. FR-026's reported figures decide nothing; a correction to them, such as counting P cycles per round, is a change-log entry |
| Analysis budget per candidate (stop rule) | 48 h of trail searches (at most 8 h per search instance), 6 h of structural checks, 12 h of frequency and avalanche tests; one re-run per evidence kind per candidate, only after a recorded tool defect, inside the budget; each kind of evidence at 4×4, then 8×8, then 16×16; a run starts only if its projection, with the probes of the larger sizes, fits its row; beside the six candidates' rows, one feature-wide 66 h row for the heavy runs that charge no candidate | R7 | every budget and the candidate limit only fall; a budget lowered below the hours used leaves zero hours |
| Vector lengths at large sizes (FR-036) | The same at every size: 16 Π and Π⁻¹ inputs with 4 traced phase by phase; 2 development keys × 10,000 words for the mode; a SHA-256 digest of 2²⁰ words over their 4·2²⁰ raw bytes; no shortening at 8×8 or 16×16 | R8 | lengths only grow |
| Target advantage for the output limits (FR-007) | ε = 2⁻⁶⁴ at N = 2¹²⁸ offline evaluations of Π or Π⁻¹, with every online quantity at its limit; per-request cap 2¹⁹ bits; instantiations per key held at the random-nonce limit, at most 2³², whatever the nonces | R9 | ε only falls and N only rises; u, every output limit and the cap only fall |
| The D4 choice (FR-022) | Once, by code, over the entered set recorded before the first score; at 4×4 and the widest reduced width, 16 or else 8, with a common r* ≥ 2; score (min(W_D, W_L)/r*)/L, compared exactly; an exact tie waits for R at 4×4; one family scored, chosen by default; none, the smallest R at 4×4 | R6 | no stricter direction, so in effect no change from plan approval, and none after the first score |
| The trail tools (FR-038, FR-039) | The tools with a `re-found` validation record when the first trail search starts, none added later; a known result per tool, cross-checks between kinds and re-validation triggers | R12 | known results, cross-checks and triggers only added; the set stays fixed |
| Structural checks (FR-019, FR-029, FR-037) | Inverse on the 16 vector inputs and 2¹⁰ test states; exhaustive bijectivity at 2×2, w = 4; exact dependency; symmetries with reflections, compositions and word rotations; invariants on 2¹⁰ states | R13 | counts only rise; symmetries, constant relations, forms and sources of R_dist only added |
| The constant rule (FR-023) | Degree 64: the first primitive x⁶⁴ + c(x) with c(0) = 1, in ascending order of the integer whose bits are c's coefficients, not on the frozen refused list (CMAC's, GCM's and the CRC-64 polynomials among its entries); Fibonacci form, seeded with ASCII `PhycoWeb` (0x506879636F576562), output from s(64) on; each table read w bits per word, most significant bit first, in the order call type (if the streams are distinct), round, food node, skipping a periodic word or one related to a constant already taken in the call; these values, and whether the call types draw on distinct streams, fixed before the first candidate is scored, each candidate's instance before its first tool run | R15 | no change once fixed; the refused list and the relations checked only grow, and a later addition that matches fails the check and blocks the freeze |
| Security parameters (FR-005, FR-006, FR-015) | s = 128; a 256-bit key and a 128-bit nonce; c = 256 at every claimable size (D2, D3) | R9, R14 | s, the key and nonce lengths and c only rise |

### Other choices, answered on review

On 2026-11-01 the owner asked the planner to settle the five choices the first draft flagged for
checking. All five are kept, and three gain rules:

| Choice | Answer | Research |
|--------|--------|----------|
| Per-request cap | Kept: the smaller of the per-instantiation limit and 2¹⁹ bits, SP 800-90A's largest request. A state compromised in mid-request exposes the request's earlier blocks through Π⁻¹, back to the last forget call, and the cap bounds that window | R9 |
| One moment for the D4 choice | Kept: once, by code, over the entered set recorded before the first score. Added: an exact tie waits for R at 4×4 of both representatives, because the spec's first tie-break needs it; if neither family has a scored candidate, selection takes the eligible candidate with the smallest R at 4×4 from either family | R6 |
| One key per `Generator` | Kept and tightened: zeroize is final, and every online quantity the bound counts has a limit and a counter. Across objects, processes and devices, the per-key limits and u are usage rules the design document states for the caller. Since the checklist answers of 2026-11-01, the key is taken at construction, `Generator(variant_id, key)`, and `instantiate(nonce, pers=b"")` uses the stored copy: no key is ever compared, and `KeyMismatch` is gone | R9; model contract |
| Checks beyond the spec | Kept. The avalanche measurement is FR-037's own; feeding R_dist is the stricter part. Its threshold now covers up to 128 round counts per size, with N_a = 2¹³, so it fires by chance less often (a false raise of R at R = 32 falls from about 38% to 23%) and still detects smaller biases (0.037 instead of 0.047 at 4×4). The symmetry check keeps reflections and compositions and adds word rotations | R4, R13 |
| A separate build file | Kept: `fast/seed_search.mk`. The feature-003 freeze hashes the stream's source and binary, not `fast/Makefile`, but a new target there could rebuild the frozen binary | R2 |

The same review fixed the set of trail tools when the first trail search starts (R12), added a
projection before every heavy run (R7), listed every download with its name, source, size and
licence (R19), and brought the status of the strategy note and of security.md §22 up to date
(security.md 2.10).

A choice for every research item now opens [research.md](./research.md) ("Choices for owner
review"), with the recommended option first. On 2026-11-01 the owner chose every recommended
option and approved every download of R19. The eleven changes, each traced to an item of the
seed-entropy note's redesign checklist or to a requirement behind it
([checklists/redesign-inputs.md](./checklists/redesign-inputs.md)), are applied:

| Change | Research | Checklist |
|--------|----------|-----------|
| Only the sweep's main thread writes progress | R2 | D4 |
| A second frequency input set, key 0 with nonce i, so S = 4b | R4 | FUT-SEC-3 |
| Related-key, related-nonce and rotational differences in the avalanche test, before the freeze | R4 | B4, B7, E7 |
| Every avalanche run cross-checked against the exact dependency matrices | R4, R13 | F9 |
| A throughput goal of 10⁸ words/s at 200 MHz, reported, not an eligibility rule | R5 | C3 |
| Each kind of evidence at 4×4, then 8×8, then 16×16 | R7 | FUT-GRID-5, D8 |
| A c-bit key and a c/2-bit nonce for keyed reduced variants | R14, R3 | A7, FUT-GRID-2 |
| The LFSR classed as a published design method (wording) | R15 | C2 |
| Constants held in a ROM at each food node | R15, R5 | A11 |
| A lock and a chain check for every append to the hash-chained logs, the provenance log now chained as well | R16, R18 | D4 |
| `*.mk` and `Makefile` pinned to LF | R18 | F12 |

The plan also settles the spec's edge case on large records: up to 10 MB compressed is
committed, larger outputs stay local with their SHA-256 and the regenerating command (R16).

## Technical Context

**Language/Version**: Python 3.10.11 (Windows) and 3.14.4 (WSL venv `~/.venvs/phycoweb`). The
model `phycoweb/model_v3.py` and `protocol/devinputs_v3.py` use the standard library only and
keep to Python 3.8 grammar. C99 for `fast/seed_search.c` and any exhaustive check too slow in
Python (gcc 15.2.0 in WSL).

**Primary Dependencies**: no new ones. numpy 2.2.6 / 2.5.4 for batch evaluation and dependency
matrices (explicit `uint64` dtypes); scipy 1.15.3 / 1.18.1 for the p-values reported and
`scipy.optimize.milp` (HiGHS) for active-box counting, analysis only. The bias verdicts compare
counts with integer critical counts derived by exact integer arithmetic and committed, so
scipy's tails decide nothing (R4). A reproduction compares counts, critical counts and verdicts byte
for byte and p-values within a relative tolerance of 10⁻⁶, since they decide nothing (R4;
data-model §1). The owner approved every download of R19 on 2026-11-01, the papers and the
Hypothesis wheels; any other file needs its own permission.

**Storage**: JSON and gzip JSON records under `reports/004-crypto-architecture-v3/`; the
hash-chained candidate log `research/004/candidates.jsonl`, provenance log and protocol change
log, each appended under a lock; vectors under `vectors/phyco-v3/`, with the sidecar
`MANIFEST.json`; local-only large outputs listed by hash (R16).

**Testing**: `python -W ignore -m unittest discover -s tests -t .` on both platforms; WSL-only
tests (the C tool) skip cleanly on Windows; property-based tests with Hypothesis 6.168.5, whose
download the owner approved on 2026-11-01, skipping with the open item named until its wheels are
installed and checked (R17, R18, R19; FR-058).

**Target Platform**: Windows 11 and Ubuntu on WSL2, i9-14900K, 32 logical CPUs, 31 GiB RAM.
The design targets the Arty A7-100T at 200 MHz, which this feature does not build for.

**Project Type**: design and research tooling inside the existing single Python project; no
RTL.

**Performance Goals**: FUT-SEC-8 under 1 h of wall time for three targets; each candidate
within the 66 h of R7; each vector file in at most an hour; model speed measured and recorded
(FR-036); the implied throughput reported beside a goal of 10⁸ 32-bit words per second at
200 MHz (R5).

**Constraints**: no change to `phyco-v2`, `lut-v1`, `sp80022`, the feature-002 and feature-003
protocols, their seed sets, or any frozen file, `fast/phyco_stream.c` and `fast/Makefile`
included (its LF pin leaves its bytes unchanged, R18); development inputs only; the protocol
only becomes stricter; no key-loading code before the FUT-SEC-8 review; heavy runs never
overlap; no download beyond the approved files of R19; the agent commits only locally, under the
owner's standing authorization, no file of this feature from the owner design review's approval on
(FR-043), and never pushes.

**Scale/Scope**: three claimable sizes (b = 1,024, 4,096 and 16,384 bits at w = 32), research
size 2×2 (3×3 only with a three-colour schedule); at most six candidates; 3 × 2³² sweep
candidates; 69 functional requirements and 20 success criteria.

No item is left as NEEDS CLARIFICATION: research R1–R19 settle every open choice.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design (below).*

| Principle | Check | Status |
|-----------|-------|--------|
| I. Integer, fully specified arithmetic | Π and the mode use only addition and subtraction modulo 2^w, XOR, AND, OR, NOT, constant rotations and logical shifts (re-decided feature-002 FR-001), all sign-free (FR-055). The 32-bit unsigned lanes are ratified by the spec (D3, FR-018), as Principle I allows. No floating point in the model; numpy and scipy only in analysis. The design document states width, signedness, wrap rule, shift kind and order of every operation (FR-027) | Pass |
| II. Bit-accurate reference model | `phycoweb/model_v3.py` is the golden model, marked model-only, RTL-pending (FR-035); golden vectors and known-answer tests per size, 2 keys × 10,000 words for the mode (R8); a second transcription agrees step by step (FR-057) | Pass |
| III. Synchronous, localized RTL | No RTL. The design rules serve it: all state registered, neighbour links only on a folded torus, no multiplication (0 DSP), generics n and w, at most one carry chain from the round's updates per stage on any path and one more from a public counter (FR-018, FR-025) | N/A (designed for; see Complexity Tracking for the absorption and output trees, for the clock, reset and counters, and for the key and nonce chains) |
| IV. Evidence-based claims | No claim. The bias rule, its control and its counts are fixed before any measurement (R4); every result is reported; no re-run except after a recorded tool defect; findings classified (FR-060); disclaimer everywhere. SP 800-22 and the held-out programme belong to feature 007, so FUT-SEC-7 stays open | Pass |
| V. Reproducibility, archival, provenance | Inputs from public strings (R3); every record holds the §17.2 fields (R16); `phyco-v2` archived with SHA-256 in `baseline/phyco-v2/` (FR-042); pinned requirements and line endings (R18); a re-check script recomputes every verdict | Pass |
| VI. Specification before implementation | Spec and plan approved 2026-11-01; tasks await approval. Candidates are research objects under the approved rules; the reference model is written from the design document after selection, and the design is frozen only after the owner design review | Pass |
| VII. Requirements traceability | Tasks will cite FR and SC identifiers; the spec's traceability tables map FUT-SEC, FUT-GRID and FUT-HW; the final report lists every requirement without evidence as open | Pass (enforced in tasks) |
| VIII. Human review gates | Every gate of the spec's Review & Approval table, which is the source: spec approval; plan approval; the checklist choices of each round; tasks approval; tool acquisition (every file of R19 approved on 2026-11-01, any other file separately); FUT-SEC-8 result review; the D4 and selection ties, where a tie reaches the owner; go-ahead for the second transcription; security-target review; owner design review; L1 recorded; external design review, recorded as done or not arranged; design freeze; final result review; and the rows added when needed: each environment record, owner-provided value and log repair, and each review held again | Pass |
| IX. Outward actions | The agent makes local commits only under the owner's standing authorization and never pushes, tags, releases or publishes; downloads only with per-file permission; sending the review package is the owner's action | Pass |
| Security Policy | FUT-SEC-1 to FUT-SEC-9 carried and traced (FR-049); key 256 bits and reachable secret state ≥ 256 bits at every claimable size (FR-009, FR-010); no claim, only a target at L1; restriction stated wherever use is described (FR-050) | Pass |
| Technical constraints | Python 3.8+ for the model (standard library only); numpy with explicit dtypes; scipy for analysis only; a test checks that the model imports no analysis dependency. Adds C tooling for the sweep and for research R12's ARX trail search | Justified (Complexity Tracking) |
| Workflow and phase reporting | This plan has its Constitution Check; the change-completion items still open at the end (statistical evaluation, RTL) are reported (FR-052); every phase ends with the constitution's report | Pass |

**Post-design re-check**: research R1–R19, the data model and the contracts add no new
violation. What they add is stricter than the spec or settles what it leaves open: the avalanche
measurement as a source of R_dist, with related-key, related-nonce and rotational differences
and a cross-check against the dependency matrices, and a second, fixed-key frequency input set
(R4); reflections, compositions and word rotations in the symmetry check (R13); a fixed moment
for the D4 choice, with rules for a tie and for no scored family (R6); a per-request cap, a final
zeroize and a counter for every online quantity (R9); a fixed set of trail tools (R12); a
projection before every heavy run, and sizes in order (R7); keys of reduced variants (R14);
constants held at each food node (R15); and a lock for every append to a hash-chained log
(R16). The numpy interpreter of the operation lists is analysis code that the model never
imports (R11, R17). The constant ROMs at the food nodes remove the grid-wide data path that one
central LFSR would need, so the absorption and output trees, the key chain and the nonce
chain beside it, and the clock, reset, start signal and replicated counters,
are Principle III's only exceptions, each justified in Complexity Tracking.
The checklist answers of 2026-11-01, of the first run, the re-run and the
second re-run, add no violation beyond the key chain, which the second re-run's answers make
explicit, those of 2026-11-02, of the third re-run, none beyond the nonce chain beside it, both
justified in Complexity Tracking, and those of the fourth re-run, the same day,
none, the rate lanes' nonce registers being registers at their own nodes,
filled through the absorption tree, and those of the fifth to tenth re-runs, the same day, none.
Each of these answers that changes a protocol value is, under every reading of the old text,
stricter, or settles an open case by its most conservative reading before any result it affects, but
for fifteen, each of which sets aside one reading of the old text, under which it fails every
candidate or every correct tool or refuses a write the protocol needs: RAT-036, RAT-052, ANA-062,
ANA-068, PRO-065, PRO-068, PRO-071, REP-063 and REP-085, from earlier rounds, the last two
added by the owner on 2026-11-03, and SEC-093, RAT-086, ANA-087, PRO-076,
REP-100 and REP-101, from the tenth re-run, whose change log entries mark that reading `set_aside`
for the owner's decision in the spec's Review & Approval row "Readings set aside"
(checklist-choices.md, "How to answer"; PRO-079); each protocol change among them becomes an entry
of the protocol change log (FR-044). Three edits that no row made, ccfd9d1, 5f34d5c and 7a6d0e8,
among the `/speckit-analyze` remediations of 2026-11-03, set aside one reading each as well, and
the first entries made from their places mark it the same way, on the owner's answer of the same
day, so that the row "Readings set aside" decides eighteen (checklist-choices.md, beside the tenth
re-run's list; PRO-079). The start signal reaches the nodes and the
replicated counters through a registered fan-out tree, as reset does, and output leaves through a
buffer of one block, so the core never stalls in mid-call (FR-025).

## Project Structure

### Documentation (this feature)

```text
specs/004-crypto-architecture-v3/
├── spec.md                  # approved 2026-11-01
├── plan.md                  # this file
├── research.md              # R1–R19, opening with the choices, answered 2026-11-01
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── model-v3-api.md      # the model's interface, call sequence and refusals
│   └── cli.md               # every new script and tool, with exit codes
├── checklists/
│   ├── requirements.md
│   ├── redesign-inputs.md   # the seed-entropy note's §5.3, item by item (FR-048)
│   └── security.md, design-rationale.md, analysis.md, protocol.md, hardware.md,
│       reproducibility.md   # the six /speckit-checklist passes, reviewer-owned
├── checklist-choices.md     # the choices for every open checklist item, answered 2026-11-01
├── design.md                # written in tasks; the phyco-v3 design document, frozen
├── rationale.md             # written in tasks; the design rationale (security.md §8), its own
│                            # file, versioned with design.md and frozen with it; its approval
│                            # status stays outside it (FR-034)
└── tasks.md                 # /speckit-tasks
```

### Source Code (repository root)

```text
fast/
├── seed_search.c             # new: FUT-SEC-8 sweep with its own design-1.0 step (R2)
└── seed_search.mk            # new: builds fast/build/seed_search; fast/Makefile unchanged

phycoweb/
├── model_v3.py               # new: phyco-v3 model, standard library only (R17)
├── constants_v3.py           # GENERATED by scripts/gen_constants_v3.py (R15)
└── selftest_v3.py            # GENERATED by scripts/gen_vectors_v3.py from the vectors (FR-059)

protocol/
├── devinputs_v3.py           # new: development inputs and uniform controls (R3)
├── evidence.py               # new: the one writer of evidence records (R16)
├── candidates.py             # new: hash-chained candidate log, appended under a lock (FR-041, R16)
├── changelog.py              # new: the one writer of the protocol change log (FR-044)
├── provenance.py             # new: the one writer of the provenance log (FR-067)
├── design_freeze.py          # new: the freeze's code, create, approve and validate (FR-043)
│                             # and hashes every module a frozen script imports (REP-091)
├── review_package.py         # new: the review package and its manifest (FR-063; REP-085)
├── claims.json               # new: claim and evidence register (FR-069)
└── disclaimer.py             # gains DESIGN_DISCLAIMER; DISCLAIMER unchanged (FR-068)

research/004/
├── ir.py                     # operation lists, interpreters, inverse (R11)
├── candidates/               # A1–A3 and B1–B3 at most, one module each, cand-A1.py to
│                             # cand-B3.py, with reference outputs
│   ├── <id>/superseded/      # every replaced operation list, as <sha256>.py, unchanged
│   ├── <id>/constants/       # GENERATED: each variant's constant table, before the freeze (R15)
│   └── superseded.json       # committed inventory of every superseded hash and path
├── tools/                    # bijectivity.py, dependency.py, bias.py, symmetry.py,
│                             # invariants.py, avalanche.py, degree.py and costmodel.py
│   ├── critical_counts.json  # integer critical counts per (N, S) and (N_a, S_A) (R4)
│   └── trails/               # tables.py (box tables), active_sbox.py and long_trail.py (MILP
│                             # active-box counting), arx_search.c with arx_search.mk (ARX
│                             # branch-and-bound, C99 in WSL)
├── validation/               # re-finding S12–S15, FUT-SEC-8, published trail values
├── exploration/              # constant tables for exploration: never frozen or evidence (R14)
├── refused-constants.json    # research R15's refused list, read by gen_constants_v3.py (FR-023)
├── refused_sources.py        # computes the refused sets that have a published derivation (R15)
├── place_check.py            # the lists' comparison before the tasks approval (FR-044)
├── place-check.json          # its result, which the row "Place check" names by SHA-256
├── candidates.jsonl          # the candidate log
└── protocol-changes.jsonl    # the protocol change log (FR-044; data-model §18)

scripts/
├── archive_phyco_v2.py       # baseline/phyco-v2/ and its MANIFEST.json (R18)
├── fut_sec8.py               # US1 driver (R2)
├── validate_tool.py          # one tool validation record (FR-039)
├── candidate_log.py          # the candidate log's entries no other script writes (FR-041; ANA-080)
├── evidence_v3.py            # one evidence kind for one candidate (R4, R12, R13)
├── d4_choice.py              # the D4 score and choice (R5, R6)
├── round_rule.py             # R, eligibility, selection, stop rule
├── mode_limits_v3.py         # the theorem's bound at the limits and the size profile (R9; FR-010)
├── gen_constants_v3.py       # constants and their checks; candidates' tables (R15)
├── gen_vectors_v3.py         # vectors and known-answer tests (R8)
├── gen_constructed_v3.py     # constructed-state vectors (FR-054)
├── design_freeze.py          # the freeze command, calling protocol/design_freeze.py
├── review_package.py         # the review package's assembly and --check (FR-063; REP-085)
├── recheck_004.py            # recomputes every verdict (FR-065)
├── repair_log.py             # a chain repair, only with the owner's go-ahead (R16)
├── owner_record.py           # the owner's environment records and owner-provided values (R1, R19)
├── downloads.py              # the downloads manifest's other entries, run by the agent (R19)
├── protocol_change.py        # the protocol change log's create and propose (FR-044)
├── provenance.py             # the provenance log's add and review (FR-067)
├── clear_lock.py             # removes a stale lock, only once its holder is shown gone (R16)
└── check_claims.py           # register against README, security.md, disclaimers

tests/
├── test_devinputs_v3.py
├── test_ir.py                # proper colouring at every odd n from 3 to 15 (FR-018); the phase
│                             # rule on every list at every size (FR-019)
├── test_costmodel.py
├── test_tools_004.py         # tool validations on known results; their order and hashes (FR-039);
│                             # critical_counts.json only appended to (data-model §5)
├── test_seed_search.py       # WSL; skips on Windows
├── test_model_v3.py          # FR-058's list, refusals, call sequences
│                             # test_generator_selftest, Generator's self-test (REP-086)
├── test_vectors_v3.py
├── test_v3_transcription.py  # model against tests/v3_reference.py, step by step;
│                             # the second transcription's provenance (FR-057)
├── v3_reference.py           # second transcription, separate session (FR-057)
├── test_protocol_004.py      # candidate log and its lock, budgets, size order, stop rule, freeze;
│                             # no key loaded into any state before the FUT-SEC-8 review (FR-001);
│                             # every seed-set load is dev-only (FR-040);
│                             # the two log writers' refusals (FR-044, FR-067); the first list
│                             # of approvals and the guards agree both ways; the three status
│                             # lines agree; the heavy-run lock's coverage (FR-045); the constants
│                             # generator's refused-list guard and match check (FR-023); the
│                             # refused list's growth across its named versions (FR-044)
├── test_records_004.py       # --reproduce of a light run per kind, its latest and one older (R7);
│                             # the two-worker test, marked heavy; the attribute pin and byte-order
│                             # mark of every hashed path, each code_sha256 entry against its blob
│                             # and the header of every committed .gz (FR-053); the re-check's
│                             # imports (FR-065); mode_limits_v3.py on stated tables and the
│                             # security target's files (FR-010); the chapters' test (FR-034)
├── test_baseline_v2.py       # archive against manifest and live files
└── test_claims.py            # FR-069

vectors/phyco-v3/             # Π and Π⁻¹ KATs, mode vectors, digests, constructed states, the
                              # constant tables, and the sidecar MANIFEST.json (R8)
baseline/phyco-v2/            # byte-exact copies and MANIFEST.json (FR-042)

reports/004-crypto-architecture-v3/
│                             # every fixed-name file keeps earlier contents in versions/ beside it
├── environment-windows.json  # the environment records, written by the owner (R1)
├── environment-wsl.json
├── downloads.json            # the downloads manifest (R19)
├── spec-versions/            # every spec version a record cites, by SHA-256 (R16)
├── research-versions/        # every research.md version a record cites, by SHA-256 (R16)
├── design-versions/          # every design-document version a record cites, by SHA-256 (REP-090)
├── fut-sec-8/                # demonstration records (<record_id>.json), tool check, review
├── validation/               # tool validation records
├── controls/                 # uniform controls, one record per test and size,
│                             # shared by every candidate (R4)
├── candidates/<id>/          # evidence per candidate
├── d4/                       # the D4 choice and its inputs
├── security-target/          # bound at the limits, generic-bound table
├── freeze/                   # freeze record
├── review-package/
├── reproductions/            # <record_id>/<n>/ per reproduction, FUT-SEC-8's included (R16)
├── rechecks/                 # the re-check's records (FR-065)
├── generator-runs/           # each generator run's record (data-model §11)
├── generator-checks/         # each generator's --check records, one per platform (SC-009)
├── projections/              # every projection record (data-model §1)
├── locks/                    # the lock-cleared records (R16)
├── provenance.jsonl          # FR-067
└── phase-report.md
```

**Structure Decision**: extend the single project. Feature-002 and feature-003 files are used
read-only: `phycoweb/model_v2.py`, `protocol/seedsets.py` for the FUT-SEC-8 targets, the golden
vectors and `fast/lut_table.h`. `fast/phyco_stream.c`, `fast/Makefile` and the built
`fast/build/phyco_stream` stay untouched, because the feature-003 freeze hashes the stream's source
and binary. Each test that a requirement names has its file in the tests tree above, and tasks.md
takes each from there.

## Phases and gates (for /speckit-tasks)

1. **Setup**, in this order, each step after the steps it needs (REP-081): (1) directories, the
   `.gitattributes` pins and the `.gitignore` entries for both locks and for `data/local/`, where
   local-only outputs go (R16, R18; the pins for `reports/004-crypto-architecture-v3/**`,
   `research/004/**`, `protocol/*.json` and `*.gz` were added on 2026-11-01), with R18's line-ending
   test, which runs from this phase on (FR-053); (2) the writers before what they write:
   `DESIGN_DISCLAIMER`, `protocol/evidence.py`, `protocol/provenance.py` with
   `scripts/provenance.py`, `protocol/changelog.py` with `scripts/protocol_change.py`,
   `scripts/clear_lock.py`, `scripts/owner_record.py` and `scripts/downloads.py` (REP-076), then the
   claim register `protocol/claims.json`, with an entry for each model ID and `phyco-v3` at L0 with
   "no claim", `in_progress` `none`, `bound` `none` and `evidence` empty (SEC-089), with
   `phyco-v3`'s line at L0 in security.md §15's register and its row in §1.1, "L0; no claim"
   (SEC-095), in a security.md version of its own, which also gives security.md's opening and
   closing blocks FR-069's fixed sentence, "PhycoWeb-PRNG, every model included, must not be used to
   generate secrets.", and words their restriction, as README's block does, with "an established
   cryptographic RNG", since no entry passes a finding inside a block (SEC-094), README's status
   block gaining it in the same phase, with its line on the 64-bit seed naming `float-v0`, `lut-v1`
   and `phyco-v2` and stating only their cap at 64 bits, in words that no rule flags, the seed's
   size and the 112-bit minimum standing in README's section 5, whose lines that FR-069's
   rules flag are reworded in the same phase (SEC-091, SEC-092, SEC-093,
   SEC-095), and `scripts/check_claims.py` and `tests/test_claims.py`, so
   that the claim-register test, with FR-069's wording rules and its disclaimer check, runs from
   this phase on, as R18's line-ending test does (FR-051, FR-069; SEC-081); (2a) each platform's
   first environment record (R1), before every other write through `protocol/evidence.py` or a log
   writer: once `requirements.txt` is corrected as R18 states, its Hypothesis pins commented out,
   the owner writes with `scripts/owner_record.py environment` the record of R1's interpreter and
   the packages that file pins, the one write the guard "Environment" admits while no record is in
   force (PRO-068) and one of the two kinds the guard "Protocol log" admits before the protocol
   change log exists, with `protocol_seq` and `protocol_line_sha256` `none` (PRO-071), and
   its row "Environment record <n>" reads Approved before the next step, so
   that (3) to (6) run under those records, every entry and record naming the record in
   force as its `environment` (REP-082); (3) the provenance log, its first entries those of the
   files drafted before it, the files outside the feature directory that this feature's
   sessions changed among them, as `git log` from 801c6d7 shows, whole or per
   section changed (FR-067; data-model §14; REP-080, REP-089); (4) the refused list
   `research/004/refused-constants.json` of research R15, committed first, since the constant
   rule's entries hold its SHA-256 in `refused_list` (data-model §18), then the protocol
   change log, after the owner's confirmation of every list at the tasks
   approval and before every file written through `protocol/evidence.py` but a
   `lock-cleared` record or an environment record (PRO-065, PRO-071), its first
   entries the answered rows of every checklist round answered before it is
   created, by the per-round lists of checklist-choices.md, in round order, approved by the owner at
   the log's approval step (FR-044; data-model §18); (5) the downloads manifest `downloads.json`,
   its `approved` entries, one per file of R19's tables, written by `scripts/downloads.py init`
   before any download, and one per later file that its row "Download <n>" permits, written by
   `downloads.py approve`, each later `fetched` or `not obtained`, and an `owner-provided` entry for
   each value the owner provides, written by the owner with `scripts/owner_record.py` (R19); (6) the
   Hypothesis wheels of R19, each downloaded into its own new directory, checked against PyPI's
   SHA-256 and recorded `fetched`, every one before any is installed, since an install changes the
   running environment and the guard then admits only a new record, then installed from outside the
   download directory under `-I`, as R19 states, and checked against R18's pins, which are written
   into the corrected `requirements.txt` only then; (7) each platform's new environment record (R1),
   matching those pins, written by the owner with `scripts/owner_record.py
   environment` once the wheels are installed, the new record FR-058 asks
   for, its Review & Approval row Approved before any later write (REP-082);
   (8) `protocol/devinputs_v3.py` with the fingerprints of every allowed (n, w), at most 16 pairs,
   and of the synthetic seeds (R3); (9) the `phyco-v2` archive (FR-042). (The status of the strategy
   note and of security.md §22 rows 5a and 5a.1 was updated during planning, in security.md 2.10.)
2. **US1 FUT-SEC-8**: `fast/seed_search.c` and its vector check, with progress written by the
   main thread only (R2); the sweep, a heavy run → demonstration record → ⛔ **FUT-SEC-8 result
   review**. No key-loading code before it.
3. **Tool validation**: first the operation-list framework `research/004/ir.py`, since the known
   results of research R13 for the structural tools are stated operation lists that those tools
   read through it (R11, R13); then re-find S12–S15 and the FUT-SEC-8 recovery on `phyco-v2`;
   trail tools on published values, from the papers of R19, whose downloads the owner approved on
   2026-11-01 (`47270450.pdf` through the owner's browser), or from values the owner provides.
   The set of trail tools is fixed when the first trail search starts (R12).
4. **US2 security target**: the design document's chapters "Security target", chapter 1, and "Mode",
   with every precondition, drafted here with `rationale.md`'s chapters of those names, which
   explain them, and recorded as under review, in the provenance log and in the security-target
   review's row, with no mark in the file, until the security-target review of phase 8, which also
   reads the two chapters of `rationale.md`, whose review entries the owner design
   review adds (RAT-086), and cites records that exist only after phase 5
   (RAT-068, RAT-069); `mode_limits_v3.py` at ε = 2⁻⁶⁴, written and tested here, its first run
   in phase 8, before the security-target review, once the design document's variant table
   holds the selected candidate's R (data-model §10). The theorem papers and
   AIS 20/31 3.0 come from the approved downloads of R19, `169.pdf` through the owner's browser.
5. **US3 and US4 candidates**: cost model (`ir.py` from phase 3); A1 (the ARX-box design)
   and at least one Boolean candidate; the entered set recorded; reduced-width bounds; the D4
   choice; production-width bounds, structural checks with the `degree` records, frequency and
   avalanche tests, in that order at each size, the bias tests starting at the R the earlier kinds
   give and extended to every later rise of R (R4); R by the round rule; eligibility; the stop
   rule. The production-width analysis covers the chosen family; the other
   family is analysed there only if the chosen one ends with no eligible
   candidate, and its candidates are otherwise `ineligible` (research R6, R7).
   One heavy run at a time, each projected first, and each kind of evidence at 4×4, then 8×8, then
   16×16 (R7).
6. **US3 model and vectors**: the design document complete; constants; `model_v3.py`; vectors
   and known-answer tests on Windows and Linux; constructed states; refusals; tests.
7. **Second transcription**: ⛔ **owner go-ahead**, the Review & Approval row "Second transcription
   go-ahead", which the owner sets and commits and the provenance test reads at HEAD; a separate
   session writes `tests/v3_reference.py`; step-by-step agreement with the common-mode caveat.
8. **US5**: first `mode_limits_v3.py`'s first run, with the claim register's `bound` (SEC-089),
   then the ⛔ **security-target review**, with its Review & Approval row, after the
   selection and before the owner design review: it cites the selected candidate's records of
   FR-029's diffusion through instantiation and of R4's first-order differences, and closes FR-011's
   functionality class; L1 recorded when its gate passes (security.md §15, 2.13: the FUT-SEC-8
   result review and the security-target review), the agent then changing `phyco-v3`'s entry,
   created at L0 in phase 1, its §15 line and its §1.1 row in a commit of its own right after the
   owner's commit (FR-012; SEC-081; SEC-095); then the rest of the rationale, its chapters
   "Security target" and "Mode" having been drafted in phase 4 and read by
   the security-target review (RAT-086); the security.md version of FR-051,
   which keeps the §1.1 row that phase 1 adds (SEC-095) (2.11 already records the §20.1 decision,
   from the checklist answers of 2026-11-01); review package, assembled by
   `scripts/review_package.py` (FR-063; REP-085); ⛔ **owner design review**, from whose first
   approval commit to the feature's end, phase 9 included, the agent commits no file of this
   feature, each later commit of such a file, the claim register's changes among them,
   being the owner's (FR-012, FR-043; SEC-084); external review recorded
   as done or not arranged, after that approval only in the owner's commit of the feature files; the
   owner commits the feature files (Principle IX), the commit `design_freeze.py create` records as
   `owner_commit` (FR-043; PRO-070); ⛔ **design freeze**.
9. **Polish**, inside FR-043's window, its files committed by the owner (SEC-084):
   README stating the status of `phyco-v3`, with the documentation drift of
   checklist group F corrected, and an addendum to the feature-002 phase report, whose
   "invertible-looking ARX" S13 contradicts (FR-051); the claim-register test, run since phase 1,
   again over the final documents (SEC-081); re-check of every verdict; final
   phase report, citing the evidence for every redesign-checklist item this
   feature covers (FR-048) → ⛔ **final result review**, whose decision the owner records in the
   commit that ends FR-043's window, a stop that the final report recommends ending it at the same
   commit; from the next commit the standing authorization covers this feature's files again, for
   the features that follow (FR-043; PRO-080).

## Risks

- **Stop**: no candidate may establish R_bound at the production width within its budget, most
  likely at 16×16 where the trail models are largest. A stop is a valid outcome and is reported
  with what was reached (stop rule).
- **Theorem mismatch**: forget or reseed may not match a published theorem exactly. The call
  then takes the theorem's form, or the feature stops; a mode without a theorem is never adopted
  (R10).
- **Downloads**: every file of R19 was approved on 2026-11-01, but two of the papers sit on
  hosts that refuse scripted requests, so they wait for the owner's browser. Without a paper the
  mode chapter stays "unverified" and L1 cannot be recorded, or a trail tool stays unvalidated
  (R19).
- **Run times**: from a timing probe (R4), the frequency and avalanche tests take about 3.8 h per
  candidate at R = 32 (7.7 h at R = 64), exhaustive bijectivity about 1 h and a long-run digest
  under a minute.
  Each heavy run is projected on the candidate itself first and starts only if it fits its
  budget row (R7); counts and lengths are never reduced to fit.
- **False raises of R**: the spec's bias rule bounds its error per size and round count, so on a
  sound Π a chance firing raises R with probability about 21% at R = 32, or 23% with the avalanche
  test, with one constant stream, and about 62% or 64% with four call types on distinct streams
  (R4). It can only raise R, and the rule cannot be loosened (FR-044); the final
  report states it.
- **Selection bias**: choosing among up to six candidates on development inputs is stated in the
  final report (FR-041).
- **Common mode**: the model and the second transcription both read one design document, and
  both may be written by AI sessions; agreement is reported with the caveat of security.md §10.2.
- **A coarse cost model**: no packing or fusion; it serves only the D4 choice and the FR-026
  estimate, and the board numbers belong to feature 008.
- **Run contention**: every heavy run takes the lock (R16) and runs alone.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| C tooling beyond the Python and numpy stack (Technical Constraints) | The sweep costs about 2³² × 257 steps per target; research R12's branch-and-bound ARX trail search, `research/004/tools/trails/arx_search.c` with `arx_search.mk` (C99, WSL), must finish each search within R7's 8 h per instance to give a bound, and an exhaustive table or check too slow in Python may be written in C (Technical Context); a C evaluator generated from an operation list is added only if a heavy run's projection does not fit its budget (R7) | The Python model runs at about 2 × 10⁵ steps/s, about 64 days per target; a slower trail search reaches its 8 h cap sooner, and a search that times out gives no bound (R12); lowering counts to fit a budget is not allowed |
| A second copy of the design-1.0 step, in `fast/seed_search.c` | `fast/phyco_stream.c` stays unchanged, because the feature-003 freeze hashes its source and binary | Editing or rebuilding it would touch frozen evidence; the copy is checked against both golden vector files before any sweep |
| Absorption and output trees over the rate lanes, which are not neighbour links (Principle III) | FR-018 requires registered trees for absorption and output | Neighbour-only paths would take about n steps per block. The trees are fully registered, and the design document specifies, per supported size, each tree's fan-in per stage, depth, registered stages and latency in cycles; the latency enters FR-025's instantiate latency and FR-026's throughput. The justification Principle III asks for is an argument in the design document: a register at every stage and a fan-in bounded by a stated number |
| Clock, reset (which every zeroization trigger also drives), the start signal with the call type, and the round and phase counters reaching every node (Principle III) | Every node needs the clock, a reset, every zeroization, the start of each call with its call type, and the round and phase position that index its constant ROM (R15) | The core takes its clock as an input on the device's clock network; its generation from the 100 MHz oscillator through an MMCM belongs to feature 008's board wrapper, outside the core and the only file with vendor primitives (FR-025). Reset is synchronous and reaches the nodes through a registered fan-out tree whose latency is part of the reset sequence (FR-025); the start signal reaches the nodes and the replicated counters through a registered fan-out tree with one stated latency to every node, as reset does, no greater than the reset tree's, so lockstep holds, and a zeroization clears its registers with the call-type field, so that no call of Π starts after a zeroization's clear (spec FR-025 "Zeroization"; HW-088). The counters are replicated, one copy at each food node or node, all started by that reset and running in lockstep, so no counter value crosses the grid. The core never stalls in mid-call: output leaves through a buffer of one block, and the next call starts only after the consumer has taken it; the buffer's size and the tree's latency enter FR-020's cycle formulas and FR-025. One global counter would be a grid-wide data path, an unregistered reset fan-out would be a long combinational path, and a global combinational enable to stall the core in mid-call, which the buffer makes unnecessary, would be another. Every zeroization trigger drives the reset's registered fan-out tree, so it reaches every register within the reset's latency, which each trigger's figure counts, and the call type travels with the start signal as a field of ⌈log₂ t⌉ bits for t call types, registered beside it at every node, to select the ROM's stream: each a public control signal with one stated latency |
| A key shift chain through the nodes that hold key bits, and a nonce chain beside it through the nodes that hold nonce bits in lanes outside the rate (Principle III) | FR-013 and FR-025 place the key and the nonce in the initial state at every instantiate, from key registers at the nodes whose lanes hold key bits, from the nonce chain and from the nonce registers of the rate lanes that hold nonce bits, filled through the absorption tree, through a selector at every lane with four sources: a key register, the nonce chain, a rate lane's nonce register or the lane's stated constant | A central key register with a tree to the key lanes would be a grid-wide path carrying secret data, and a nonce routed through the key chain would shift the key out of its registers. Each chain is a local data path of public length, registered at every node it passes, the nodes between those that hold its bits included, so no path of neighbours is required; the key chain's length enters the key-loading figure, the nonce chain's length, the nonce registers' transfer and the one-cycle copy into the lanes enter the instantiate figure, and zeroization clears both chains, the nonce registers and every copy (FR-025) |

The design rationale names each hardware structure of these rows, the trees, the clock, reset and
start signal, the counters with their ROMs, the key and nonce chains, the rate
lanes' nonce registers and the selector at every lane, with its functional
need, and for the key chain and the selectors, which carry secret data, the
attack class they meet (no read-back, zeroization), citing the row here for its justification (spec
FR-034, "Components"); fault attacks stay with feature 008.
