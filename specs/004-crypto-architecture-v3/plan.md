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
2. **Security target (US2)**: chapter 1 of the design document states the properties sought,
   s = 128, the 256-bit key and 128-bit nonce, threats T1–T11, every generic bound per size, and
   the keyed-duplex theorem with its preconditions. The output limits follow from the theorem at
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
| Analysis budget per candidate (stop rule) | 48 h of trail searches (at most 8 h per search instance), 6 h of structural checks, 12 h of frequency and avalanche tests; one re-run per evidence kind per candidate, only after a recorded tool defect, inside the budget; each kind of evidence at 4×4, then 8×8, then 16×16; a run starts only if its projection, with the probes of the larger sizes, fits its row | R7 | every budget and the candidate limit only fall; a budget lowered below the hours used leaves zero hours |
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
download the owner approved on 2026-11-01 (R19; FR-058).

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
owner's standing authorization, and never pushes.

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
| III. Synchronous, localized RTL | No RTL. The design rules serve it: all state registered, neighbour links only on a folded torus, no multiplication (0 DSP), generics n and w, at most two carry chains per stage (FR-018, FR-025) | N/A (designed for; see Complexity Tracking for the absorption and output trees, and for the clock, reset and counters) |
| IV. Evidence-based claims | No claim. The bias rule, its control and its counts are fixed before any measurement (R4); every result is reported; no re-run except after a recorded tool defect; findings classified (FR-060); disclaimer everywhere. SP 800-22 and the held-out programme belong to feature 007, so FUT-SEC-7 stays open | Pass |
| V. Reproducibility, archival, provenance | Inputs from public strings (R3); every record holds the §17.2 fields (R16); `phyco-v2` archived with SHA-256 in `baseline/phyco-v2/` (FR-042); pinned requirements and line endings (R18); a re-check script recomputes every verdict | Pass |
| VI. Specification before implementation | Spec and plan approved 2026-11-01; tasks await approval. Candidates are research objects under the approved rules; the reference model is written from the design document after selection, and the design is frozen only after the owner design review | Pass |
| VII. Requirements traceability | Tasks will cite FR and SC identifiers; the spec's traceability tables map FUT-SEC, FUT-GRID and FUT-HW; the final report lists every requirement without evidence as open | Pass (enforced in tasks) |
| VIII. Human review gates | Plan approval; downloads (every file of R19 approved on 2026-11-01, any other file separately); FUT-SEC-8 review; go-ahead for the second transcription; owner design review; design freeze; final result review | Pass |
| IX. Outward actions | The agent makes local commits only under the owner's standing authorization and never pushes, tags, releases or publishes; downloads only with per-file permission; sending the review package is the owner's action | Pass |
| Security Policy | FUT-SEC-1 to FUT-SEC-9 carried and traced (FR-049); key 256 bits and reachable secret state ≥ 256 bits at every claimable size (FR-009, FR-010); no claim, only a target at L1; restriction stated wherever use is described (FR-050) | Pass |
| Technical constraints | Python 3.8+ for the model (standard library only); numpy with explicit dtypes; scipy for analysis only; a test checks that the model imports no analysis dependency. Adds C tooling for the sweep | Justified (Complexity Tracking) |
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
central LFSR would need, so the absorption and output trees, the key chain, and the clock, reset,
start signal and replicated counters, are Principle III's only exceptions, each justified in
Complexity Tracking. The checklist answers of 2026-11-01, of the first run, the re-run and the
second re-run, add no violation beyond the key chain, which the second re-run's answers make
explicit and Complexity Tracking justifies: each is stricter, adds a check, or settles an open case
by its most conservative reading before any result it affects, and each protocol change among them
becomes an entry of the protocol change log (FR-044). The start signal reaches the nodes and the
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
├── design_freeze.py          # new: freeze create, approve and validate (FR-043)
├── claims.json               # new: claim and evidence register (FR-069)
└── disclaimer.py             # gains DESIGN_DISCLAIMER; DISCLAIMER unchanged (FR-068)

research/004/
├── ir.py                     # operation lists, interpreters, inverse (R11)
├── candidates/               # A1–A3 and B1–B3 at most, one module each, with reference outputs
│   ├── <id>/superseded/      # every replaced operation list, as <sha256>.py, unchanged
│   └── superseded.json       # committed inventory of every superseded hash and path
├── tools/                    # bijectivity, dependency, bias, symmetry, invariants, costmodel
│   ├── critical_counts.json  # integer critical counts per (N, S) and (N_a, S_A) (R4)
│   └── trails/               # box tables, MILP active-box counting, ARX branch-and-bound
├── validation/               # re-finding S12–S15, FUT-SEC-8, published trail values
├── candidates.jsonl          # the candidate log
└── protocol-changes.jsonl    # the protocol change log (FR-044; data-model §18)

scripts/
├── archive_phyco_v2.py       # baseline/phyco-v2/ and its MANIFEST.json (R18)
├── fut_sec8.py               # US1 driver (R2)
├── validate_tool.py          # one tool validation record (FR-039)
├── evidence_v3.py            # one evidence kind for one candidate (R4, R12, R13)
├── d4_choice.py              # the D4 score and choice (R5, R6)
├── round_rule.py             # R, eligibility, selection, stop rule
├── mode_limits_v3.py         # the theorem's bound at the limits (R9)
├── gen_constants_v3.py       # constants and their checks (R15)
├── gen_vectors_v3.py         # vectors and known-answer tests (R8)
├── gen_constructed_v3.py     # constructed-state vectors (FR-054)
├── design_freeze.py          # create, approve and validate the freeze
├── recheck_004.py            # recomputes every verdict (FR-065)
├── repair_log.py             # a chain repair, only with the owner's go-ahead (R16)
├── clear_lock.py             # removes a stale lock, only once its holder is shown gone (R16)
└── check_claims.py           # register against README, security.md, disclaimers

tests/
├── test_devinputs_v3.py
├── test_ir.py
├── test_costmodel.py
├── test_tools_004.py         # tool validations on known results
├── test_seed_search.py       # WSL; skips on Windows
├── test_model_v3.py          # FR-058's list, refusals, call sequences
├── test_vectors_v3.py
├── test_v3_transcription.py  # model against tests/v3_reference.py, step by step
├── v3_reference.py           # second transcription, separate session (FR-057)
├── test_protocol_004.py      # candidate log and its lock, budgets, size order, stop rule, freeze;
│                             # no key loaded into any state before the FUT-SEC-8 review (FR-001);
│                             # every seed-set load is dev-only (FR-040)
├── test_records_004.py       # --reproduce of one light command per light kind (R7); the two-worker
│                             # test, marked heavy; the attribute pin and byte-order mark of every
│                             # hashed path (FR-053)
├── test_baseline_v2.py       # archive against manifest and live files
└── test_claims.py            # FR-069

vectors/phyco-v3/             # Π and Π⁻¹ KATs, mode vectors, digests, constructed states, the
                              # constant tables, and the sidecar MANIFEST.json (R8)
baseline/phyco-v2/            # byte-exact copies and MANIFEST.json (FR-042)

reports/004-crypto-architecture-v3/
├── environment-windows.json  # the environment records, written at setup (R1)
├── environment-wsl.json
├── downloads.json            # the downloads manifest (R19)
├── spec-versions/            # every spec version a record cites, by SHA-256 (R16)
├── research-versions/        # every research.md version a record cites, by SHA-256 (R16)
├── fut-sec-8/                # demonstration record, tool check, review, any reproduction
├── validation/               # tool validation records
├── controls/                 # uniform controls, one record per test and size,
│                             # shared by every candidate (R4)
├── candidates/<id>/          # evidence per candidate
├── d4/                       # the D4 choice and its inputs
├── security-target/          # bound at the limits, generic-bound table
├── freeze/                   # freeze record
├── review-package/
├── reproductions/            # one directory per reproduced record and reproduction (R16)
├── rechecks/                 # the re-check's records (FR-065)
├── provenance.jsonl          # FR-067
└── phase-report.md
```

**Structure Decision**: extend the single project. Feature-002 and feature-003 files are used
read-only: `phycoweb/model_v2.py`, `protocol/seedsets.py` for the FUT-SEC-8 targets, the golden
vectors and `fast/lut_table.h`. `fast/phyco_stream.c`, `fast/Makefile` and the built
`fast/build/phyco_stream` stay untouched, because the feature-003 freeze hashes the stream's
source and binary.

## Phases and gates (for /speckit-tasks)

1. **Setup**: directories; `.gitattributes` pins and the `.gitignore` entries for both locks and for
   `data/local/`, where local-only outputs go (R16, R18; the pins for
   `reports/004-crypto-architecture-v3/**` and `*.gz` were added on
   2026-11-01); the Hypothesis wheels of R19 downloaded, checked against PyPI's SHA-256 and
   installed; the downloads manifest `downloads.json`, one entry per file fetched (R19); the
   environment records of both platforms (R1); corrected `requirements.txt`;
   `DESIGN_DISCLAIMER`; `protocol/devinputs_v3.py` with fingerprints; `protocol/evidence.py`;
   the provenance log; the protocol change log, whose first entries are the answered rows of every
   checklist round answered before it is created, by the per-round lists of checklist-choices.md, in
   round order, approved by the owner at the log's approval step (FR-044; data-model §18); the
   `phyco-v2` archive (FR-042). (The status of the strategy note and of security.md §22 rows 5a and
   5a.1 was updated during planning, in security.md 2.10.)
2. **US1 FUT-SEC-8**: `fast/seed_search.c` and its vector check, with progress written by the
   main thread only (R2); the sweep, a heavy run → demonstration record → ⛔ **FUT-SEC-8 result
   review**. No key-loading code before it.
3. **Tool validation**: re-find S12–S15 and the FUT-SEC-8 recovery on `phyco-v2`; trail tools
   on published values, from the papers of R19, whose downloads the owner approved on
   2026-11-01 (`47270450.pdf` through the owner's browser), or from values the owner provides.
   The set of trail tools is fixed when the first trail search starts (R12).
4. **US2 security target**: design document chapter 1, drafted here and marked "draft, under review"
   until the security-target review of phase 8, which cites records that exist only after phase 5;
   the mode chapter with every precondition, `mode_limits_v3.py` at ε = 2⁻⁶⁴. The theorem papers and
   AIS 20/31 3.0 come from the approved downloads of R19, `169.pdf` through the owner's browser.
5. **US3 and US4 candidates**: operation-list framework and cost model; A1 (the ARX-box design)
   and at least one Boolean candidate; the entered set recorded; reduced-width bounds; the D4
   choice; production-width bounds, structural checks with the `degree` records, frequency and
   avalanche tests, in that order at each size, the bias tests starting at the R the earlier kinds
   give and extended to every later rise of R (R4); R by the round rule; eligibility; the stop rule.
   One heavy run at a time, each projected first, and each kind of evidence at 4×4, then 8×8, then
   16×16 (R7).
6. **US3 model and vectors**: the design document complete; constants; `model_v3.py`; vectors
   and known-answer tests on Windows and Linux; constructed states; refusals; tests.
7. **Second transcription**: ⛔ **owner go-ahead**; a separate session writes
   `tests/v3_reference.py`; step-by-step agreement with the common-mode caveat.
8. **US5**: first the security-target review, with its Review & Approval row, after the selection
   and before the owner design review: it cites the selected candidate's records of FR-029's
   diffusion through instantiation and of R4's first-order differences, and closes FR-011's
   functionality class; L1 recorded when its gate passes (security.md §15, 2.13: the FUT-SEC-8
   result review and the security-target review); then the rationale; the security.md version of
   FR-051 (2.11 already records the §20.1
   decision, from the checklist answers of 2026-11-01); review package; ⛔ **owner design
   review**; external review recorded as done or not arranged; the owner commits the feature
   files (Principle IX); ⛔ **design freeze**.
9. **Polish**: README stating the status of `phyco-v3`, with the documentation drift of
   checklist group F corrected, and an addendum to the feature-002 phase report, whose
   "invertible-looking ARX" S13 contradicts (FR-051); claim-register test; re-check of every
   verdict; final phase report, citing the evidence for every redesign-checklist item this
   feature covers (FR-048) → ⛔ **final result review**.

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
  sound Π a chance firing raises R with probability about 21% at R = 32, or 23% with the
  avalanche test (R4). It can only raise R, and the rule cannot be loosened (FR-044); the final
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
| C tooling beyond the Python and numpy stack (Technical Constraints) | The sweep costs about 2³² × 257 steps per target; a C evaluator generated from an operation list is added only if a heavy run's projection does not fit its budget (R7) | The Python model runs at about 2 × 10⁵ steps/s, about 64 days per target; lowering counts to fit a budget is not allowed |
| A second copy of the design-1.0 step, in `fast/seed_search.c` | `fast/phyco_stream.c` stays unchanged, because the feature-003 freeze hashes its source and binary | Editing or rebuilding it would touch frozen evidence; the copy is checked against both golden vector files before any sweep |
| Absorption and output trees over the rate lanes, which are not neighbour links (Principle III) | FR-018 requires registered trees for absorption and output | Neighbour-only paths would take about n steps per block. The trees are fully registered, and the design document specifies, per supported size, each tree's fan-in per stage, depth, registered stages and latency in cycles; the latency enters FR-025's instantiate latency and FR-026's throughput. The justification Principle III asks for is an argument in the design document: a register at every stage and a fan-in bounded by a stated number |
| Clock, reset (which every zeroization trigger also drives), the start signal with the call type, and the round and phase counters reaching every node (Principle III) | Every node needs the clock, a reset, every zeroization, the start of each call with its call type, and the round and phase position that index its constant ROM (R15) | The core takes its clock as an input on the device's clock network; its generation from the 100 MHz oscillator through an MMCM belongs to feature 008's board wrapper, outside the core and the only file with vendor primitives (FR-025). Reset is synchronous and reaches the nodes through a registered fan-out tree whose latency is part of the reset sequence (FR-025); the start signal reaches the nodes and the replicated counters through a registered fan-out tree with one stated latency to every node, as reset does, so lockstep holds. The counters are replicated, one copy at each food node or node, all started by that reset and running in lockstep, so no counter value crosses the grid. The core never stalls in mid-call: output leaves through a buffer of one block, and the next call starts only after the consumer has taken it; the buffer's size and the tree's latency enter FR-020's cycle formulas and FR-025. One global counter would be a grid-wide data path, an unregistered reset fan-out would be a long combinational path, and a global combinational enable to stall the core in mid-call, which the buffer makes unnecessary, would be another. Every zeroization trigger drives the reset's registered fan-out tree, so it reaches every register within the reset's latency, which each trigger's figure counts, and the call type travels with the start signal as a field of ⌈log₂ t⌉ bits for t call types, registered beside it at every node, to select the ROM's stream: each a public control signal with one stated latency |
| A key shift chain through the nodes that hold key bits (Principle III) | FR-013 and FR-025 place the key in the initial state at every instantiate, from key registers at the nodes whose lanes hold key bits | A central key register with a tree to the key lanes would be a grid-wide path carrying secret data. The chain is a local data path of public length, registered at every node it passes; its length enters the key-loading figure, the one-cycle copy into the lanes enters the instantiate figure, and zeroization clears every copy (FR-025) |
