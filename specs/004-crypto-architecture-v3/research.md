# Research: Cryptographic Architecture and phyco-v3 Design

Feature `004-crypto-architecture-v3`. Date: 2026-11-01. Spec approved 2026-11-01, with D1–D10 as
clarified. Every decision below is fixed before any design result exists. From plan approval,
the values marked **protocol** belong to the pre-registered design protocol and may only become
stricter (FR-044). Each such value states what "stricter" means for it. Where a fact can only be
confirmed once a paper or tool is on disk, the decision says so and states what happens if it
turns out differently. No such fallback may loosen a rule. The plan's table "Values this plan
fixes" lists every value marked protocol here, so one list names them all.

The answers to the checklist choices ([checklist-choices.md](./checklist-choices.md), "all
recommended", 2026-11-01), those of the first run, the re-run and the second re-run the same day,
are applied in the sections below. Each that changes a protocol value is stricter, or settles an
open case by its most conservative reading before any result it affects, and becomes an entry of the
protocol change log `research/004/protocol-changes.jsonl` when that log is created, by the per-round
lists "Rows that change the protocol" of checklist-choices.md (FR-044; data-model §18).

> This feature makes no security claim. No PhycoWeb-PRNG model, `phyco-v3` included, may be used
> to generate secrets; use an established cryptographic random-number generator for keys,
> nonces, tokens and salts. Passing statistical tests does not show cryptographic security.

## Choices for owner review

Each row is a choice the owner could confirm or change before approving the plan, with the
recommended option first. "As decided" keeps the decision of the section the ID names.
"Answered" rows were settled on review on 2026-11-01 (plan.md, "Other choices, answered on
review"). "Change" rows alter a decision. They come from developing these choices and from an
item-by-item check of the seed-entropy note's redesign checklist
([checklists/redesign-inputs.md](./checklists/redesign-inputs.md)). Every change is stricter or
adds a check, as FR-044 allows.

**Answered 2026-11-01.** The owner chose every recommended option ("all recommended") and
approved every download in R19's two tables (R19.1). The eleven changes are applied in the
sections below, in plan.md, data-model.md, both contracts, quickstart.md and the checklist. The
rows stay as they were offered, and the sections they name hold the decisions. One row's wording
was corrected after the answer, not its choice: R5.2 now credits the 10⁸ words/s goal to feature
003, which set it for the C stream. Two decisions were refined later by checklist answers, in
their sections and not in their rows: R11.2's C evaluator is checked on the candidate's committed
reference outputs for R8's 16 Π inputs before its first run, not on the `phyco-v3` vectors, which
exist only after selection (R7, R11); and R15.2's round and phase counters are no longer global
but replicated and running in lockstep, while reset and the start signal reach the nodes through
registered fan-out trees (R15; FR-025).

| ID | Choice | Recommended | Other options |
|----|--------|-------------|---------------|
| R1.1 | Where things run | As decided: Python work on Windows 11 with Python 3.10.11; C tools and the Linux reproduction in WSL2; the i9-14900K, one heavy run at a time | Everything in WSL: loses the Windows half of SC-009. A Windows C compiler: a download for no gain. A cloud machine: an outward action, and the code and inputs leave the machine |
| R2.1 | The FUT-SEC-8 search tool | Answered: `fast/seed_search.c` with its own copy of the step, built by its own `fast/seed_search.mk` | Extending `fast/phyco_stream.c`: touches files the feature-003 freeze hashes. A Python sweep: about 64 days per target |
| R2.2 | Progress output of the 32-thread sweep | Change: only the main thread writes progress lines; the workers update counters that it reads (checklist D4) | As decided, unspecified: lines from 32 threads can interleave, as in feature-003 open issue 2 |
| R3.1 | How development inputs are derived | As decided: SHA-256 of one public string per input, `phycoweb-004/dev/<kind>/<i>` | One SHA-256 stream cut into fields: a change to one field's length shifts every later input. OS random values, recorded: no rule recomputes them, which FR-040 needs |
| R3.2 | Source of the uniform controls | As decided: the same strings under `control`, so every control run can be repeated | OS random controls: unrepeatable, the weakness of feature 003's `getrandom` control (checklist F8) |
| R4.1 | Inputs per frequency measurement | As decided: N = 2²⁰ per claimable size | 2¹⁶: needs biases 4 times larger. 2²⁴: 16 times the cost, about 5.6 h per candidate at R = 32 |
| R4.2 | Instantiation states for the frequency test | Change: two sets per size, key i with nonce i as now, and key 0 with nonce i, the many-nonces-under-one-key case an attacker sees (FUT-SEC-3); S = 4b; 0.35 h more at R = 32; the bias found at 50% power moves from 0.0023 to 0.0024 at 4×4 | As decided, key i with nonce i only. Uniform states: no information, since Π maps uniform inputs to uniform outputs |
| R4.3 | Avalanche counts and threshold | Answered: N_a = 2¹³ per flipped bit; threshold 0.005/(128·S_A) | The first draft, N_a = 2¹² at 0.005/S_A per round count: a false raise of R at R = 32 about 38% instead of 23%. N_a = 2¹² at the per-size threshold: catches 0.053 instead of 0.037 at 4×4 |
| R4.4 | Flip set F at 8×8 and 16×16 | As decided: the 2w = 64 bits of each node on the main diagonal (\|F\| = 512 and 1,024) | Every state bit: 2²⁷ pairs per direction at 16×16, 16 times the diagonal set, beyond the 12 h of R7 |
| R4.5 | Related-key, related-nonce and rotational differences before the freeze | Change: add to the avalanche measurement every key and nonce bit flipped in 2¹³ instantiation states, run forward as instantiate runs Π, and rotational pairs, every lane of 2¹³ test states rotated by each k = 1…w − 1, in both directions. Both count in S_A = (2·\|F\| + 384 + 2(w − 1))·b under the same threshold, so the chance of a false firing does not change; 0.6 h more at R = 32; sensitivity changes by under 1%. Their results can then still raise R before the freeze (checklist B4) | As decided, left to feature 005: after the freeze, a weakness found there can only lead to a new model ID |
| R4.6 | Detection power shown inside each avalanche run | Change: wherever the exact dependency matrices (R13) show an output bit independent of a flipped bit, that difference bit must never flip, and so must fire; any disagreement is recorded as a tool defect (checklist F9) | As decided: only the tools' validation on `phyco-v2` (FR-039) shows detection power |
| R5.1 | Cost model for D4 | As decided: 6-input LUTs per node and round, with carry chains counted, and no packing or fusion | A LUT6_2 packing model: closer to the fabric, but more rules to argue before any result. Gate equivalents: not the FPGA's resource |
| R5.2 | Throughput goal (checklist C3) | Change: state a goal of 10⁸ 32-bit words per second at the 200 MHz target for every claimable size, the goal feature 003 set for the C stream, which design 1.0 missed at 8.5 × 10⁷, and report FR-026's implied throughput beside it; not an eligibility rule | An eligibility rule: a slow candidate becomes ineligible, which could end the feature in a stop. As decided, no goal: C3 stays half answered |
| R6.1 | Width and rounds at which D4 is scored | As decided: the widest reduced width, 16 or else 8, at which both families have both bounds over a common r* ≥ 2 | w = 32 directly: bounds may not exist there for both families early. 2×2: a research size whose diffusion differs from the claimable sizes |
| R6.2 | When D4 is decided, ties, and no scored family | Answered: once, by code, over the entered set recorded before the first score; an exact tie waits for R at 4×4 of both representatives; with no scored family, selection takes the eligible candidate with the smallest R at 4×4 from either family | A second D4 run after more candidates: reopens the choice. A stop when no family is scored: discards the evidence of both. The owner's free choice: no rule behind it |
| R7.1 | Budget per candidate | As decided: 48 h of trail searches (8 h per instance), 6 h of structural checks, 12 h of statistics; at most about 16.5 days of runs for six candidates | Half: more searches end inconclusive, and stops come sooner. Double: up to about 33 days of runs |
| R7.2 | Re-runs | As decided: one per kind of evidence, only after a recorded tool defect, inside the budget | None: one tool bug decides a candidate. More: invites running again until a result pleases |
| R7.3 | Order of sizes | Change: each kind of evidence runs at 4×4, then 8×8, then 16×16; a larger size starts only when the smaller one's run of that kind has finished without making the candidate ineligible (FUT-GRID-5; checklist D8) | As decided, any order: a candidate that fails at 4×4 may already have spent its 16×16 hours |
| R7.4 | Projection before heavy runs | Answered: a timing run of at most 60 s on the candidate; the run starts only if the projection fits the hours left in its row; counts never change to fit | No projection: a run can use up a budget row before anyone notices |
| R8.1 | Mode vectors | As decided: 2 development keys × 10,000 words at every claimable size, in requests of 1, 7, 64 and 1,000 words | 10⁶ words: large files for little extra coverage. Shorter at 16×16: the spec allows it, but the model's speed does not need it |
| R8.2 | Long-run digest | As decided: SHA-256 of the first 2²⁰ words, under a minute per size | 2²⁴ words: about 30 min in all, still far short of feature 008's 2³²-word check, which needs a fast checked model anyway |
| R9.1 | Target advantage ε | As decided: 2⁻⁶⁴ at N = 2¹²⁸ evaluations of Π or Π⁻¹ | 2⁻³²: larger limits, a looser target. 2⁻⁸⁰: smaller limits; with a bound linear in the data, the per-key limit falls by 2¹⁶ |
| R9.2 | Per-request cap; one key per `Generator` | Answered: the smaller of the per-instantiation limit and 2¹⁹ bits; zeroize final, a counter for every online quantity, and per-key limits and u across objects stated as usage rules | No cap: a state compromised mid-request exposes everything since the last forget, up to the per-instantiation limit. A smaller cap: more forget calls per output bit |
| R10.1 | Mode theorem | As decided: the full-state keyed duplex of Daemen, Mennink and Van Assche (2017), with the forget result of Bertoni et al. (2010) or Gaži and Tessaro (2016), whichever matches forget exactly | The earlier single-user analysis of the full-state keyed duplex (Mennink, Reyhanitabar and Vizár, 2015): another paper to request, and u keys would need a hybrid argument. Counter mode with feed-forward: not D1, and no forget call |
| R11.1 | One operation list per candidate | As decided: only two invertible update forms, so a list is bijective by construction, and every tool derives from it | Hand-written code per tool: copies that can disagree. CASCADA's representation: a download, and it would not match the model |
| R11.2 | When to build a C evaluator | As decided: only when a heavy run's projection does not fit its row; generated from the operation list and checked on the committed vectors | From the start: faster runs, but more code to check before the first result |
| R12.1 | Trail tools | As decided: HiGHS in scipy and self-written searches; no solver download | PySAT with CaDiCaL (wheels of 1.9 and 4.1 MB, MIT, plus `six`): an independent cross-check that needs its own validation and approval before the first trail search. CryptoSMT or CASCADA: larger downloads, more to validate |
| R12.2 | Fixing the tool set | Answered: the tools with a `re-found` record when the first trail search starts; none added later | An open set: a search that reached its cap could be retried with a friendlier tool |
| R13.1 | Symmetries checked | Answered: translations, rotations by 90°, 180° and 270°, reflections and their compositions, and word rotations | The spec's translations and rotations only: misses mirror images and rotational cryptanalysis |
| R13.2 | Cycle structure of Π (checklist B5) | As decided, not measured: a permutation merges no states, and the generic bound covers its cycles | Count the cycles of the 2×2, w = 4 variant: about 2 h in C on one thread, against the about 23 cycles of a random permutation of 2³² points; weak evidence for the cost |
| R14.1 | Research sizes | As decided: 2×2 at every width with reduced capacity, and 3×3 only if the design document gives a three-colour schedule from the same generics | Even sizes only: 3×3 listed as unsupported, with its reason |
| R14.2 | Key and nonce of keyed reduced variants (FUT-GRID-2; checklist A7) | Change: a c-bit key and a c/2-bit nonce, so 256 and 128 bits at every claimable size, and FR-010's relations at s = c/2; c a multiple of 16; a variant whose key and nonce leave no room for padding and domain bits is keyless. The model contract and data-model §10 take these lengths. This removes a contradiction: the plan now gives every keyed variant a 256-bit key and a 128-bit nonce, which a 2×2 state, 256 bits at w = 32 and 32 bits at w = 4, cannot hold | A 256-bit key and 128-bit nonce everywhere, absorbed over several blocks where they do not fit: the construction changes at small sizes, so results transfer less. Keyless reduced variants only: key loading stays undefined at 2×2, against FUT-GRID-2 |
| R15.1 | The rule for round constants (checklist C2) | Change in wording only: the maximal-length LFSR, as decided, classed as a published design method that yields a fixed table, not as a standard PRNG in Π, under feature-002 FR-007 as the spec re-decides it (D6): no key, nonce or state enters it, and polynomials of published designs are refused | A plain counter formula, which that rule allows by name: simpler, but successive constants differ in few bits. Digits of a mathematical constant: several published primitives use them |
| R15.2 | How constants reach the food nodes (checklist A11) | Change: each food node holds its own constants in a small ROM indexed by the round counter, so no data signal crosses the grid; only the clock, reset and the round and phase counters are global. The cost model still does not count the ROMs | One central LFSR with a registered distribution tree: a grid-wide data path, to be justified like the output tree. A copy of the LFSR at each food node: local, but each copy must start at its own offset |
| R15.3 | Rotation amounts | As decided: a stated search over every amount, ranked by the trail bounds it gives, with ties to the smallest amounts in a stated order | Hand-picked amounts: FUT-GRID-4 forbids them. Amounts drawn from the LFSR: a rule, but not chosen by the bounds as FR-024 asks |
| R16.1 | What is committed | As decided: records up to 10 MB, compressed with gzip; larger outputs stay local with their SHA-256 and the command that regenerates them | Everything: hundreds of MB of matrices. Summaries only: verdicts could not be re-checked (FR-065) |
| R16.2 | Writers of the hash-chained logs (checklist D4) | Change: every append to `research/004/candidates.jsonl` and `provenance.jsonl` takes a short exclusive lock and checks the chain first, so two scripts never chain to the same last line | As decided: only heavy runs are serialized, so a light script appending during a heavy run could break the chain |
| R17.1 | How the model is written | As decided: by hand from the design document after selection, then checked against the operation-list interpreter on every vector | Generated from the operation list: one source, but harder to read as the oracle for the RTL (FR-056), and its check against the interpreter becomes circular |
| R17.2 | Test framework | As decided: `unittest`, as in features 001–003; Hypothesis 6.168.5 only if its download is approved | pytest: a download, with no gain in coverage |
| R18.1 | `requirements.txt` | As decided: one file pinning both tested environments with markers | Two files: two places to drift |
| R18.2 | Line endings of makefiles (checklist F12) | Change: pin `*.mk` and `Makefile` with `text eol=lf`, which covers the new `fast/seed_search.mk` and keeps feature 003's `fast/Makefile` LF on a fresh checkout without changing its bytes | Only `fast/seed_search.mk`. No pin: this machine's `core.autocrlf=true` writes CRLF on a fresh checkout, and the repository pins every script that runs in WSL |
| R19.1 | Downloads | The owner approves each file of R19's tables separately; `169.pdf` and `47270450.pdf` need the owner's browser | Values with their source from the owner instead. None: the mode chapter stays "unverified", L1 cannot be recorded, and the trail tools stay unvalidated |

Of the 42 rows, 23 keep a decision as made, 7 were answered on review, 11 changes were chosen
and applied, and R19.1's downloads were approved, all on 2026-11-01.

## R1. Where things run

- **Decision**: the model, the vectors, the evidence scripts and the statistics run on Windows 11
  with Python 3.10.11, numpy 2.2.6 and scipy 1.15.3. C tools (the FUT-SEC-8 search tool, and
  exhaustive checks if Python is too slow) are built and run in WSL2 Ubuntu with gcc 15.2.0, and
  the Linux reproduction of every vector (SC-009) uses the WSL venv `~/.venvs/phycoweb`
  (Python 3.14.4, numpy 2.5.4, scipy 1.18.1). The machine is the i9-14900K with 32 logical CPUs
  and 31 GiB RAM used in feature 003.
  - One environment record per platform, `environment-windows.json` and `environment-wsl.json`
    under `reports/004-crypto-architecture-v3/`, is written at setup and on any change by
    `scripts/owner_record.py environment`, which the owner runs, an owner's own act (spec FR-044):
    the Windows build, the WSL distribution, its version and the kernel, Python, gcc, make and the
    full `pip freeze`, with `approved_by`, `approved_utc` and `approval_confirmed`. The script
    prints the record's SHA-256, taken without those fields, and writes nothing unless standard
    input is an interactive terminal and the owner types its first 16 hex digits; the owner then
    sets the record's Review & Approval row, "Environment record <n>", to Approved with that SHA-256
    and commits it. A record is written only when its Python and pinned packages
    match this section and the pins of `requirements.txt` for that platform (R18). Each evidence
    record cites its environment record's SHA-256 (data-model §1). Both
    keep fixed names: before one changes, its current content is kept as `versions/<sha256>.json`
    beside it, and the new record holds `previous_sha256` (R16).
  - `protocol/evidence.py` checks at start the running environment against the platform's
    environment record in force, as a whole: Python, every package and version of `pip freeze` (one
    added, upgraded or removed), gcc and make in WSL, and the Windows build or the WSL distribution
    and kernel. Any difference exits 2, naming it, a Windows or WSL update included; the owner then
    writes and approves a new environment record, with this section updated first when a pinned
    version changes, and each later record cites the record in force. The check also exits 2 unless
    the record in force has its row "Environment record <n>" Approved at HEAD with its
    SHA-256 (cli contract, "Environment"). `scripts/recheck_004.py` alone is
    exempt, since it imports only the standard library and `protocol/` (R16).
  - A reproduction that re-runs evidence may run in either environment, whichever made the original,
    and in no other; the re-check of R16 may run anywhere. It compares the
    fields data-model §1 lists, and every other field, `command`, `config`, `parallelism`, the
    analyst and the reviewer included, is reported only, since each may differ between environments
    or analysts.
- **Rationale**: these are the environments of security.md §19, so no new tool is needed to
  start. There is no C compiler on Windows. Two Python versions on two platforms test FR-035's
  determinism across platforms and versions.
- **Alternatives**: everything in WSL (would lose the Windows half of SC-009); a Windows
  compiler (an extra download for no benefit).

## R2. The FUT-SEC-8 demonstration tool (FR-001 to FR-003)

- **Decision**:
  - A new C program, `fast/seed_search.c`, holds its own copy of the design-1.0 step and reads
    the existing generated `fast/lut_table.h`. `fast/phyco_stream.c` stays unchanged.
  - `--check-vectors` reproduces both committed `phyco-v2` golden vector files, all 10,000 words
    of each, and must pass before any sweep (FR-002). A mismatch stops the run.
  - The sweep splits s₂ = 0…65535 over 32 POSIX threads. For each (s₂, s₃) it initialises the
    state, runs the 256-step warm-up and compares output words 1, 2 and 3 with the target's,
    dropping a candidate at its first mismatch. It counts the matches after one, two and three
    words, lists every match after three, and reports steps, time and steps per second as JSON.
  - Only the main thread writes progress lines, to stderr; the workers update counters that it
    reads, so no two threads write to one stream (checklist D4).
  - `scripts/fut_sec8.py` takes the targets from `protocol.seedsets.load("dev", allow=["dev"])`
    (the first three seeds), computes the attacker's observations with `phycoweb/model_v2.py`,
    runs the tool once per target, separates any extra three-word match with the fourth word
    (Edge Cases), and writes the demonstration record (data-model §5).
  - Expected cost, from the spec: about 2³² × 257 steps per target, 3.6 core-hours at
    8.5 × 10⁷ steps/s, so under an hour of wall time for three targets on 32 threads. It is a
    heavy run (FR-045).
- **Rationale**: the Python model runs at about 2 × 10⁵ steps/s, so one target would take about
  64 days. Changing `fast/phyco_stream.c`, or rebuilding its binary, would touch files whose
  hashes the feature-003 freeze records. The freeze does not hash `fast/Makefile`, but a new
  target there could rebuild the frozen binary, so the tool has its own source and its own build
  file, `fast/seed_search.mk`, and `fast/Makefile` is left alone. The golden-vector check makes
  the copied step trustworthy.
- **Alternatives**: extend `phyco_stream.c` (rejected, as above); a Python sweep (too slow).

## R3. Development inputs (FR-040) — protocol

- **Decision**: every key, nonce, personalization string, reseed input and test state of this
  feature is derived from a public ASCII string by SHA-256, in `protocol/devinputs_v3.py`
  (standard library only):

  | Input | String hashed (i in decimal, no leading zeros) | Value |
  |-------|-----------------------------------------------|-------|
  | Key i | `phycoweb-004/dev/key/<i>` | the 32-byte digest; for a keyed reduced variant of capacity c < 256, its first c/8 bytes (R14) |
  | Nonce i | `phycoweb-004/dev/nonce/<i>` | the first 16 bytes; for a keyed reduced variant, the first c/16 bytes |
  | Personalization string i | `phycoweb-004/dev/pers/<i>` | the first min(m, 32) bytes, where m is the design's maximum length (FR-006); the empty string is a separate, named input |
  | Reseed input i | `phycoweb-004/dev/reseed/<i>` | the 32-byte digest |
  | Test state i at n, w | `phycoweb-004/dev/state/n<n>w<w>/<i>/<j>` for j = 0, 1, … | the digests concatenated; the first b bits, read most significant bit first into w-bit lanes in the design document's lane order |
  | Uniform control | the same strings with `control` in place of `dev` | as above |

  - A measurement with N inputs uses i = 0…N − 1. The fingerprint of each kind, of the state kind at
    every supported n and w and of the synthetic seeds at every size, is the SHA-256 of a text that
    data-model §2 fixes exactly, so that another implementation computes the same fingerprints: the
    values for i = 0…99, one per line, each line ending in LF, the last included, as
    `protocol/seedsets.py` writes; byte strings in lower-case hex, as digests are written, a state
    as one upper-case hex string of its w-bit words in the design document's lane order, and a
    synthetic seed as a decimal integer. A personalization string's fingerprint covers its full 32
    bytes, so it does not depend on m, which the design fixes later. The fingerprints are recorded
    in the module and checked at load, as `protocol/seedsets.py` does.
  - Every use takes its inputs from this rule: the vectors (keys and nonces 0 and 1, R8), the
    constructed states from development keys, the D4 scoring, the tool validation and every
    test. A use of N inputs takes i = 0…N − 1 of the kind it names, declared up front: scripts take
    inputs only through `load(ns, kind, allow, count, ...)`, as feature 002's scripts use
    `protocol/seedsets.py`'s `load`, which checks the namespace against `allow` and the kind's
    fingerprint and returns the values i = 0…count − 1, so no index outside the declared range can
    be read. The derivation functions take the namespace, as their strings do, and a test fails if
    code outside the module and its own tests calls one (data-model §2).
  - The loader accepts only the namespaces `dev` and `control`. `control` serves only uniform
    controls, and `dev` is never a control. Each evidence kind's namespace is fixed in code, not
    chosen on the command line, and the loader refuses `control` for any kind but a control. The
    `control` inputs are never redrawn or replaced: a size's control record stands for every
    candidate (R4). Every evidence script takes its inputs from the loader and records the
    namespace, kind and index range (FR-061).
  - Beside the derivation, which stays exactly as frozen, a closed class of constructed inputs
    is fixed by public rules before first use (data-model §2):
    1. the fixed patterns of FR-058 and R8: all-zero, all-one, alternating and counting, and the
       single-bit keys and nonces e_i for every i;
    2. the edge states of FR-054, from the design document's list;
    3. the avalanche flips x ⊕ e_j, the key and nonce bit flips and the word rotations of
       development inputs, for every j, bit and k the rule names (R4);
    4. feature 002's `dev` seeds for FUT-SEC-8 (R2), the one external development set.
    5. synthetic counts, for the bias test's validation only (R4): set j = 0…99 at each size draws
       from numpy's `Generator(PCG64(s))`, where s is the first 16 bytes of SHA-256 of
       `phycoweb-004/dev/synthetic/n<n>/<j>` read as a big-endian integer: one `binomial(N, 1/2)`
       count per tested bit, in the test's bit order, except the planted bit at position j mod S,
       drawn as `binomial(N, 1/2 + δ)` at that size's δ (0.0030, 0.0031 or 0.0033).
       `protocol/devinputs_v3.py` stays standard-library only and gives the seeds through `load`,
       `synthetic_seed(ns, n, j)` deriving them; `validate_tool.py` draws the counts. A set's
       SHA-256 covers its counts as decimal text, one per line in the test's bit order, each line
       ending in LF, as `protocol/seedsets.py` writes values. The sets are local-only (R16),
       regenerated by their deterministic command, and never replaced: the validation record commits
       each set's SHA-256, the numpy version and a per-set summary, and a later draw must reproduce
       every hash with that numpy version (R4). The bias test's validation adds a second family of
       such sets, j = 100…199, drawn by the same rule, each planting its bit at position
       ⌊(j − 100)·S/100⌋ (R4), a known result added under the tool-validation rule; class 5's own
       sets stay as settled. The test's bit order is R4's.

    A constructed input takes its index from its rule. No value or index is picked after any
    output is seen.
  - No held-out set exists. Feature 007 defines the held-out keys, and FR-040 carries a checkable
    form to it: the keys are derived from data that does not exist until the later of
    `phyco-v3`'s design freeze and feature 007's protocol freeze, and a test re-derives them.
  - SHA-256 here is protocol bookkeeping. It never appears in Π, the mode or key loading (D6).
- **Stricter means**: nothing may change; the rule is frozen at plan approval.
- **Rationale**: the same pattern as feature 002 (`phycoweb-002/<set>/<i>`), with a feature prefix
  that keeps the two families of inputs apart. Public strings make every input reproducible and
  show that no input was chosen after a result.
- **Alternatives**: OS random keys (not reproducible); one stream cut into fields (a change to one
  field length would shift every later input).

## R4. Inputs per bias measurement; the frequency and avalanche tests (bias rule; FR-037)

- **Decision** (**protocol**):
  - **Frequency test (the spec's bias rule).** At each claimable size (4×4, 8×8, 16×16; w = 32),
    two sets of N = 2²⁰ development inputs: for i = 0…2²⁰ − 1, the state that instantiate gives
    to its first call of Π for key i and nonce i, and for key 0 and nonce i, the many nonces under
    one key that an attacker sees (FUT-SEC-3), both with the empty personalization string. Each
    input runs through rounds 1…R_cur of Π, and separately of Π⁻¹. After every round the ones in
    each state bit are counted, per set. At a size and round count, the bits tested are the b bits
    after Π and the b bits after Π⁻¹ in each set, so S = 4b, in the test's bit order: set 1, then
    set 2; within each, the b bits after Π, then the b bits after Π⁻¹; lanes in the
    design document's index order and bits most significant first, as each
    synthetic set's SHA-256 covers them (R3). A bit fires if its two-sided
    binomial p-value (p = 1/2; twice the smaller tail, at most 1, computed exactly) is at most
    0.005/S.
  - **Exact verdicts.** For each (N, S) and (N_a, S_A), integer critical counts are derived once
    by exact integer arithmetic over the binomial distribution (sums of binomial coefficients,
    compared with the threshold as a rational) and recorded in a committed table,
    `research/004/tools/critical_counts.json` (data-model §5). The verdict compares each count
    with its critical values, so scipy's tails decide nothing; scipy still computes the
    p-values reported.
    A reproduction compares the counts, the critical counts and the verdicts byte for byte, and the
    p-values by value, decompressed first in either format: two p-values agree when their difference
    is at most 10⁻⁶ times the larger of their magnitudes, or when both are below 2⁻¹⁰²², the
    smallest normal double, so that a 0 beside a subnormal agrees. It lists any outside; a p-value
    never decides a verdict, and a `p_values` file's hash and `uncompressed_sha256` may differ
    between the two environments of R1 and are reported only (data-model §1).
  - **Avalanche test.** FR-037 asks for it; using it as a source of R_dist is stricter than the
    spec. For each flipped input bit j in a set F, N_a = 2¹³ test states x (kind `state`, R3);
    after every round r = 1…R_cur the difference Π^r(x) ⊕ Π^r(x ⊕ e_j) is counted bit by bit,
    and the same for Π⁻¹. F holds every state bit at 4×4 (|F| = 1,024) and the 2w = 64 bits of
    each node on the main diagonal at 8×8 and 16×16 (|F| = 512 and 1,024). Two further sets test
    related inputs before the freeze (checklist B4). Related keys and nonces: each of the 384 key
    and nonce bits is flipped in the first 2¹³ instantiation states of the frequency test (key i,
    nonce i), and the difference is counted after every round of Π only, as instantiate runs Π.
    Rotational pairs: for each k = 1…w − 1, the difference Π^r(rot_k(x)) ⊕ rot_k(Π^r(x)) over
    the N_a test states, rot_k rotating every lane by k, and the same for Π⁻¹. With
    S_A = (2·|F| + 384 + 2(w − 1))·b, a difference bit fires if its two-sided binomial p-value is
    at most 0.005/(128·S_A). The factor 128 spreads the test's 0.005 over up to 128 round counts
    at a size, so this extra test adds at most 0.005 per size, not per round count, to the chance
    of a false firing (below). The threshold stays 0.005/(128·S_A) whatever the number of round
    counts, so the rule never fires less. If more than 128 are measured, which needs R_cur above
    128, the stated chance of a false firing becomes 0.005·m/128 per size for m round counts,
    reported beside the result. A difference bit that never flips fires, so a dependency that is
    never observed raises R_dist.
  - **Null models.** Under a random permutation, p = 1/2 for each frequency bit, each avalanche
    difference bit and each rotational difference bit. For an invariant form (R13), the null
    model is its chance rate on uniform states, 2⁻ʷ for a w-bit sum or XOR. The uniform controls
    test these null models directly.
  - **Cross-check in every avalanche run.** Wherever the exact dependency matrices (R13) show an
    output bit independent of every input bit that a flip changes, that difference bit must never
    flip, and so must fire. Any disagreement is recorded as a tool defect (as R7 defines it), and
    the run's status is `inconclusive` (checklist F9).
  - **Rounds measured.** At each size the kinds run in plan phase 5's order: trail bounds (R_bound),
    then the structural checks (R_f, R_b, symmetries, invariants and the `degree` records), then the
    frequency test, then the avalanche test (R13). The bias tests start at the R the earlier kinds
    give, max(2·R_dist, R_bound + 2, 2·max(R_f, R_b)). R_cur is the candidate's current value of the
    round rule. If a test fires at a round count r with 2r > R_cur, R_cur becomes 2r and the
    measurement extends to it, until no firing round count raises R. Any later rise, from either
    bias test, a re-run after a reproduction's finding or a stricter change, first makes every
    record that depends on R again at the new variant, in R7's order ("After a rise of R"), the bias
    tests last: every bias test already run at that size is extended to the new R, as a new
    measurement of the same kind charged to the 12 h row (R7); if the row cannot hold it, that
    size's bias evidence is inconclusive and the candidate `ineligible`. A result at rounds 1 to the
    old R stands for the new variant only where its constants do not change, which with distinct
    streams holds only for the first call type in R15's reading order (Call types, below).
  - **Call types.** Where the call types draw on distinct constant streams (spec FR-023), both
    tests, with every set, run on each call type's permutation, each record naming its call type,
    and R_cur is the largest over the call types, so a firing in any of them raises it; the uniform
    controls read no constant and serve every call type. A rise of R changes the constants of every
    call type after the first in R15's reading order from round 1, so their results are measured
    again from round 1 on the new table, each record naming the table's SHA-256, as a new
    measurement charged to the 12 h row.
  - **Uniform control.** Before its first use at each size by any candidate, each test is applied
    once, with the same counts and the same threshold, to uniform control inputs: two sets of 2²⁰
    control states, and N_a·(|F| + 384 + w − 1) XOR differences of two independent control states,
    N_a for each flipped bit, key or nonce bit and rotation amount. The control inputs are R3's
    `control` states at that size: the two frequency sets are states 0…2²⁰ − 1 and
    2²⁰…2²¹ − 1, and XOR difference i is state 2i ⊕ state 2i + 1. The control's one record per test
    and size serves every candidate. Its hours are charged, at each size, to every candidate's 12 h
    row, whether the control ran for that candidate or before it, and each row's reservation counts
    them by projection until they exist; the control runs only if every entered candidate's row can
    hold it (R7). If a test fires on its control, the bias evidence of that size
    is inconclusive for every candidate, so none is eligible at that size, and the feature
    recommends stopping (stop rule), citing the control record; the control inputs are never redrawn
    or replaced, and the rule is not loosened (Edge Cases). The chance accepted is at most 0.0025
    per size for the frequency control, by the union bound over its 2b bits at 0.005/S, and below
    0.005/128 for the avalanche control. Inconclusive bias evidence leaves R_dist unestablished at
    that size, which makes the candidate ineligible unless a recorded tool defect is fixed and the
    one re-run that R7 allows is conclusive. That is one re-run per kind of evidence per candidate,
    across all sizes: a second recorded defect in that kind leaves the evidence inconclusive, which
    makes the candidate ineligible, and the tool is fixed and validated again before any other
    candidate uses it (R7). A control runs again, with the same counts, only after a recorded tool
    defect in its own code.
  - **Validation.** Before its first counted use, the bias test's validation record (R12;
    data-model §7) shows that it re-finds S14's bias on `phyco-v2`, and that on each of two families
    of 100 sets of synthetic binomial counts with one bit planted at the 90%-power biases above
    (0.0030, 0.0031 and 0.0033 at the three sizes) it fires in 82 to 97 of the family's 100 sets,
    the binomial interval around 90% with at most 0.005 in each tail: R3's class 5, j = 0…99, and a
    second family, a known result added, j = 100…199, drawn the same way
    from `phycoweb-004/dev/synthetic/n<n>/<j>`, each set planting its bit at
    position ⌊(j − 100)·S/100⌋, so that the planted bits spread over all S bits,
    both sets and both directions. Synthetic counts cost nothing to draw.
    They are R3's constructed class 5, drawn by a public rule from seeds fixed before first use,
    hashed and never redrawn, which means that no set is ever replaced: a later draw must reproduce
    every hash in an environment with that numpy version, and a draw that differs is reported and
    counts for nothing; after an approved numpy upgrade the old record stays the validation in the
    old environment, and a new validation, a new record, decides in the new one: outside 82 to 97 in
    either family the tool is unvalidated there, and its results `not evaluated`, until a defect is
    found and fixed. The sets are local-only (R16), regenerated by their deterministic command,
    and the validation record commits each set's SHA-256 (R3), the numpy version and a per-set
    summary, the planted bit's count and every fired bit, so a fresh clone recomputes both 82-to-97
    verdicts from committed files and a regeneration checks every count. The avalanche test's
    validation record also shows its verdict code and
    its power without new inputs: the verdict function, applied to every count 0 to N_a of one
    difference bit, must fire exactly on the counts at or beyond the two critical values of
    `critical_counts.json`, and the power at δ_A = 0.0443, 0.0451 and 0.0465, computed exactly from
    the binomial distribution, must be at least 0.9, as the table below states. R13's three planted
    results, one for each path (the flip set, the related-key and related-nonce set and the
    rotational pairs), and the cross-check keep validating the counting; each planted result is
    re-found only if the bits that fire match its stated set bit for bit at every round count
    tested. One record per size covers the three paths, which share N_a and the threshold.
    R3 does not change.
  - **Sensitivity**, computed for this plan with scipy 1.15.3, for the bias |f − 1/2| of one bit
    that fires with probability 1/2 (and 0.9):

    | Size | Frequency, N = 2²⁰ per set, threshold 0.005/S | Avalanche, N_a = 2¹³, threshold 0.005/(128·S_A) |
    |------|-----------------------------------------------|-------------------------------------------------|
    | 4×4 | 0.0024 (0.0030), S = 2¹² | 0.0373 (0.0443), S_A = 2,494·b |
    | 8×8 | 0.0025 (0.0031), S = 2¹⁴ | 0.0380 (0.0451), S_A = 1,470·b |
    | 16×16 | 0.0026 (0.0033), S = 2¹⁶ | 0.0395 (0.0465), S_A = 2,494·b |

    Against one input set (S = 2b) and F alone, the values were 0.0023, 0.0024 and 0.0026 for the
    frequency test and 0.0372, 0.0377 and 0.0394 for the avalanche test, so the added sets cost
    little sensitivity, under 1% for the avalanche test. The first draft's avalanche test,
    N_a = 2¹² at 0.005/S_A, caught 0.047 (0.057) at 4×4, so the test now detects smaller biases as
    well as firing by chance less often.

  - **Engine.** The counts come from the batch interpreter of R11 on numpy `uint64` arrays in
    batches of 2¹⁶. The verdict is computed by code from the saved counts (FR-065). Before any
    evidence run on a candidate, the scalar and batch interpreters agree on reference outputs
    for R8's 16 Π inputs at every variant the candidate uses, computed by the scalar interpreter
    and committed with the candidate (R11). A timing probe is a `projection` record (R7).
  - **False firing.** On uniform inputs the frequency test fires at a size and round count with
    probability at most 0.005 (the spec's rule), and the avalanche test at most 0.005 per size
    over all its round counts. A false firing can only raise R, but it does raise it: a firing
    is reported as a distinguisher at its round count that raises R, with the family-wise chance
    rate stated beside it, and it is never measured again to remove it. Only round
    counts r with 2r > R matter, ⌈R/2⌉ of them per size, so a Π whose outputs look uniform after
    a few rounds has R raised by chance with probability about 1 − 0.995^(3⌈R/2⌉): 11% at
    R = 16 and 21% at R = 32, or 23% with the avalanche test. With the avalanche threshold at
    0.005/S_A per round count, as first drafted, it would be 38% at R = 32. A raised R adds round
    counts, so a raise can repeat, and repeated raises can use up the budget of R7, which ends
    the measurement as inconclusive. The spec's rule cannot be loosened (FR-044), so this cost is
    accepted, and the final report repeats the rate beside every firing.
- **Stricter means**: a change is stricter only if it can add firings and never remove one, so R
  can only rise. Every firing recorded under the rule then in force stands. N and N_a may only
  rise, and F and the sets of inputs and differences may only grow; a larger N, N_a or F, or a
  new set, is tested under its new S or S_A in addition. S and S_A always count the bits tested;
  the thresholds stay 0.005/S and 0.005/(128·S_A); the cross-check stays.
- **Rationale**: Π maps uniform inputs to uniform outputs at every round count, so a frequency
  test needs structured inputs. Instantiation inputs are the structured inputs an attacker
  actually gets (FUT-SEC-5): about 384 varying key and nonce bits, the rest fixed. A timing probe
  on this machine (2026-11-01; Python 3.10.11, numpy 2.2.6) measured 0.21 ns per numpy word
  operation in batches of 2¹⁶ and 0.66 ns per counted bit. At R = 32 and 64 numpy operations per
  node and round, the frequency test then takes about 0.7 h per candidate over its two input
  sets, the three sizes and both directions, and the avalanche test about 3.1 h with its related
  and rotational sets, mostly counting bits: 3.8 h in all. A raise of R to 64 doubles that to 7.7 h,
  still inside the 12 h of R7. Where the call types draw on distinct streams, both tests run once
  per call type (Call types, above), so at four call types the 3.8 h become about 15 h at R = 32,
  more than the 12 h row holds; at the same cost per round, the row then
  holds such a candidate's bias evidence only up to about R = 25, and a rise
  of R measures every call type after the first again from round 1 (Rounds
  measured), at further cost. The avalanche test complements the exact dependency
  matrices (R13), which also check it, and its budget sets N_a and F. The second input set holds
  the key fixed, as the many nonces under one key do, and the related and rotational sets let
  their results raise R before the freeze instead of only in feature 005 (checklist B4).
- **Alternatives**: uniform inputs (no information for a permutation); N = 2¹⁶ (detects only
  biases 4 times larger); N = 2²⁴ (16 times the cost); every input bit at 16×16 (2²⁷ pairs per
  direction, 16 times the diagonal set, which would not fit the 12 h of R7); the avalanche test
  at 0.005/S_A per round count, as first drafted (38% instead of 23% at R = 32); N_a = 2¹² at
  the per-size threshold (half the cost, but 0.053 instead of 0.037 at 4×4); key i with nonce i
  only (no many-nonces case); related and rotational differences left to feature 005 (a weakness
  found after the freeze can only lead to a new model ID); detection power shown only by the
  tools' validation on `phyco-v2` (FR-039).

## R5. The operation-count cost model (D4; FR-026) — protocol

- **Decision**: LUTs per node and round are counted from the candidate's operation list (R11) on
  6-input LUTs, the Arty A7-100T's fabric, with no packing or fusion between listed operations:

  | Operation on w-bit words | LUTs | Carry chains |
  |--------------------------|------|--------------|
  | Rotation or shift by a constant; wiring between nodes; a register stage | 0 | 0 |
  | Bitwise function in which each output bit depends on k ≤ 6 input bits (constant bits count as inputs), such as XOR, AND-NOT or a χ-like row | w | 0 |
  | Bitwise function with k > 6 input bits per output bit | w · ⌈(k − 1)/5⌉ | 0 |
  | Addition or subtraction modulo 2^w of two words | w | 1, of w bits |

  - The round constants, held in a small ROM at each food node (R15), are not counted. Per
    supported size, the design document reports the number of food nodes, the ROM depth at each
    (R entries per call type, times the number of distinct constant streams), the word width and
    the total bits.
  - An operation shared by two nodes counts once, at the node that computes it.
  - **Stages.** One pipeline stage is one colour phase and takes one clock cycle, so a round of P
    phases takes P cycles, P being the number of phases in one round of the candidate's operation
    list at that size (a colour visited twice counts twice; P = 2 for a red-black schedule that
    visits each colour once), recorded in the candidate's log entry. Carry chains are counted per
    phase (R11).
  - Serial carry chains per round = the most additions on any dependency path within one round
    (the D4 tie-break). Per pipeline stage the count must be at most two serial w-bit carry
    chains (FR-025). A subtraction counts as one chain, as an addition does. A public counter
    held as 32-bit words counts where it sits on a stage's path, and not when it is registered
    on a path of its own.
  - **Depth.** Beside the chain count, the LUT levels on each stage's longest path are reported
    per candidate: ⌈(k − 1)/5⌉ levels for a bitwise function with k input bits per output bit,
    and one more for each dependent operation on the path. The design document states each
    stage's estimated delay against the 5 ns of 200 MHz on the XC7A100T −1, with its source, as
    an estimate that feature 008's post-route timing checks; reported, not an eligibility rule.
  - Flip-flops (2w per node, plus pipeline registers) are reported but not scored.
  - Cost per output bit (FR-026) = LUTs per node and round × n² × P·R / r, in LUT-cycles per
    output bit, for an implementation that computes one phase per clock cycle.
  - **Size estimate.** From the cost model, the design document estimates LUTs, flip-flops and block
    RAM per claimable size, each part with its own figure (the nodes and stages, LUTs per node and
    round × n² for the stages built; the trees; the ROMs; the output buffer of r bits with its
    read-out; the key registers and the key-loading buffer; the replicated counters; the limit
    counters; the self-test's stored key, nonce and expected output; 2w·n² state flip-flops plus
    pipeline registers; block RAM, expected to be 0 unless a ROM is mapped to it) against the
    device's 63,400 LUTs and 126,800 flip-flops, and names the largest size expected to fit, as an
    estimate that feature 008 checks part by part against Vivado's hierarchical utilization report
    (FR-026).
  - **Throughput goal** (checklist C3): 10⁸ 32-bit words per second at the 200 MHz target, at
    every claimable size. It is the goal feature 003 set for the C stream, which design 1.0
    missed at 8.5 × 10⁷. The design document reports FR-026's implied throughput beside it; the
    goal is reported, never an eligibility rule. The implied rate is r/(P·R + ⌈r/i⌉) bits per cycle
    for an output interface of i bits per cycle, a width the design document states per size (for
    example 32 bits per cycle, as the vector files list words, or a stated wider bus), since the
    next call starts only after the consumer has taken the block (FR-025); r/(P·R) and i are
    reported beside it. It is stated for stated request sizes, the 2¹⁹-bit
    cap and 4,096 words, counting each request's output calls plus its forget call, with
    instantiate's calls spread over a stated number of requests per instantiation; the rate
    before forget calls is reported beside it as an upper bound. At 4×4 with P = 2 and i = 32, the
    rate before forget calls is 768 bits per 88 cycles, about 0.55 × 10⁸ words per second, at R =
    32, and 768 bits per 152 cycles, about 0.32 × 10⁸, at R = 64, both below the goal.
  - `research/004/tools/costmodel.py` computes every number from the operation list, and a test
    checks the table above on hand-counted examples, written with their SHA-256 and entered in the
    provenance log before `costmodel.py` is drafted (R13; data-model §14).
- **Stricter means**: the parts that the D4 score and its tie-breaks use (the LUT table, L and
  the carry chains per round) have no stricter direction, so in effect they do not change from
  plan approval, and "no change once the first candidate is scored" is the later of two locks.
  FR-026's reported figures (cost per output bit, depth, size estimate, implied throughput)
  decide nothing, so a correction to them, such as the count of P cycles per round, is
  recorded in the protocol change log.
- **Rationale**: the model must be fixed before scoring and simple enough to compute by code. Both
  families are counted by the same table, so neither gains from a counting choice. Packing and
  fusion depend on synthesis; Vivado post-route numbers belong to feature 008 (FUT-HW-2).
- **Alternatives**: a LUT6_2 packing model (closer to the real fabric, but more rules to argue
  about before any result); gate-equivalent counts (not the FPGA's resource); the throughput
  goal as an eligibility rule (a slow candidate would become ineligible, which could end the
  feature in a stop).

## R6. The D4 score and the candidates (FR-022)

- **Decision** (**protocol**):
  - Families: A = ARX, B = Boolean. Candidates are A1…A3 and B1…B3, no more (stop rule).
    Candidate A1 is the long-trail design: each node's two lanes form one 2w-bit ARX-box (64 bits
    at w = 32), with a local linear layer between nodes and the bound for Π from counting active
    boxes (FR-022; Dinu et al., 2016). Only the method is reused (D6). The rationale states the
    layer's differential and linear branch numbers, or the rule by which a difference must
    activate boxes in later rounds, and derives the active-box count from it; the validated
    active-box counting of R12 checks it.
  - **When**: the choice is computed once, by code, after every candidate entered for it has
    been scored, and before the production-width analysis of the chosen family starts. At least
    one candidate per family is entered, and the entered set is recorded in the candidate log
    before the first score. `d4_choice.py` exits 2 until every candidate of the recorded entered set
    has, at 16 and, where this rule needs it, at 8, a final reduced-width outcome for each bound
    kind: a bound record, the `inconclusive` record of a capped search, or an `ineligible` or
    `rejected` log decision. A capped search counts as no bound at that width, so the choice
    proceeds once every entered candidate has an outcome, whatever it is, and the choice record
    lists each outcome; no search is retried to reach a score (R12). A candidate added later, only
    in place of one `rejected` or `ineligible`, or once after a decline at the owner design review,
    counts towards the stop rule but does not change the recorded choice; after a decline it comes
    from the chosen family, or from the other only where the declined one was selected by the
    fallback or D4 was not computable, so that the rules can select it (spec "Eligibility and
    selection").
  - **The other family.** Only the chosen family goes on to the production-width analysis. The other
    family is analysed at the production width only if the chosen family ends with no eligible
    candidate, once every candidate of the chosen family has its final decision (`withdrawn`,
    `rejected` or `ineligible`, or, for an eligible candidate, its round-rule record at every
    claimable size), in R7's order, its rows reserved meanwhile. If the chosen family has an
    eligible candidate, each candidate of the other family not analysed at the production width gets
    `ineligible`, with the reason "not analysed at the production width: D4 chose the other family",
    which the final report states. Where D4 is not computable both families are analysed, and an
    exact tie sends both representatives on (below).
  - **Where**: at 4×4, at the widest reduced width, 16 or else 8, at which at least one entered
    candidate of each family has both a differential and a linear trail bound for a common
    number of rounds of at least 2; r* is the largest such common number. Only candidates with
    both bounds at r* rounds are scored.
  - **Score**: with W_D and W_L the −log₂ of the bounds on the best differential trail
    probability and on the best linear trail's squared correlation over r* rounds, and L the
    LUTs per node and round of R5 at that width:

    ```text
    score = (min(W_D, W_L) / r*) / L
    ```

  - Each family's representative is its scored candidate with the highest score, and the family
    with the higher representative is chosen. Scores are compared exactly: each weight is kept as a
    rational, a multiple of 2⁻¹⁶ rounded down, never up (R12), and candidate A scores higher than B
    when p_A^(L_B) < p_B^(L_A), where p = 2^(−W) is the weaker (larger) of a candidate's two bounds,
    W = min(W_D, W_L), decided exactly as W_A·L_B > W_B·L_A, since 2^(−W) is irrational for a W that
    is not an integer.
  - **Exact tie.** The spec's first tie-break, the smaller R, needs R_bound at the production
    width, which does not exist yet at the moment of the choice. The choice then waits: both
    representatives go on to the production-width analysis within their own budgets, and
    `d4_choice.py --tie` applies the spec's tie-breaks in order (the smaller R at 4×4, then fewer
    serial carry chains per round, then the owner's recorded choice) once both values of R at 4×4
    exist. A representative found ineligible first loses the tie.
  - **One family scored.** That family is chosen by default, and the record says so.
  - **Neither family scored.** No family is chosen, and the record says that D4 was not
    computable. Selection then takes the eligible candidate with the smallest R at 4×4 from
    either family, with a tie going to the owner's recorded choice; the stop rule still applies.
  - **Rotation amounts** are chosen at this width (R15), ranked by this score's own measure,
    min(W_D, W_L) at the search width, at one number of rounds for every candidate
    (R15's one ranking rule). Each candidate's amounts are searched first
    at 16, the width this rule tries first, with the width recorded in its log entry before the
    search. If this rule then fixes the width at 8, every entered candidate's amounts are searched
    again at 8, with the same recorded space of amounts, K and placement rule, under the same
    ranking rule, as a new log entry, and the scores at 8 use the amounts
    found at 8; no choice is involved, since this rule fixes the width. The
    scaling rule to every other width is stated before the search. R_bound
    at w = 32 is computed with the scaled amounts, and
    the rationale reports whether the ranking held after scaling, without choosing again.
  - The D4 record states r* (data-model §8).
- **Stricter means**: the rule has no stricter direction, so in effect it does not change from
  plan approval; "nothing may change after the first score" is the later of two locks.
- **Rationale**: the D4 rule says "on reduced widths" but not when, at which width or over how
  many rounds, and without a common round count the weights per round are not comparable. The
  widest width both families reach is the closest to production, and fixing the moment of the
  choice keeps a later candidate from reopening it. r* compares the candidates over the same
  rounds; it is not a rate per round, since trail weight per round is often lower in the first
  rounds. A family better at r* may be worse at R, a risk the final report names. The score is
  unchanged.
- **Alternatives**: w = 32 directly (bounds may not exist there for both families early);
  scoring at 2×2 (a research size whose diffusion differs from the claimable sizes).

## R7. The analysis budget per candidate (stop rule) — protocol

- **Decision**: per candidate, in wall-clock hours on the machine of R1, one heavy run at a time
  (FR-045):

  | Work | Budget |
  |------|--------|
  | Trail-bound searches of every kind, width and size together (the solver cross-checks, the rotation-amount and reduced-width searches, box tables, box-trail searches, active-box or active-S-box counting) | 48 h; each search instance at most 8 h |
  | Structural checks (inverse tests, exhaustive bijectivity, dependency matrices, symmetry and invariant checks, `degree` records) | 6 h |
  | Frequency and avalanche tests, with the hours of the uniform controls at each size (R4) | 12 h |

  - A search gives a bound only when the solver proves it: an optimal or infeasible status with
    the proven dual bound used, or a search that exhausts its space within its cap. The best
    solution found is never a bound. A search that reaches its cap gives no bound, and its
    record says "inconclusive" (security.md §16.3). A candidate without an established R_bound at
    every claimable size within its budget is ineligible; R_bound at each claimable size comes from
    a bound computed at that size, so the reservation keeps every such search, 16×16 included, and a
    row that cannot hold the 16×16 search leaves the candidate without R_bound there (R12, "Bounds
    per size").
  - **Tool defects.** A tool defect is one of: a failed validation or re-validation; a
    disagreement between avalanche counts and dependency matrices (R4); a disagreement between
    two evaluators of one operation list (scalar, batch, C, model); a crash or an undocumented exit
    status; a reproduction that differs from its original on a field that
    enters a verdict, in the environment that made the original (R16); or a
    bug in the tool's code, shown by the faulty line and a test that fails
    before the fix and passes after. It is recorded with that evidence before any re-run
    (data-model §1, `exclusions_and_reruns`). A disliked result is none of these.
  - **Re-runs.** A run may be repeated only after a tool defect is found and recorded: one
    re-run per kind of evidence per candidate, across all sizes, and its time counts against the
    same budget. A second recorded defect in that kind leaves the evidence inconclusive, which
    makes the candidate ineligible, and the tool is fixed and validated again before any other
    candidate uses it. A candidate that fails an inverse or bijectivity test is investigated
    first: a recorded tool defect gets this one re-run; otherwise the candidate is rejected, logged
    with the failure and counted towards the stop rule. A search that reached its cap is never run
    again, with another tool or another version of the same one, except as this one re-run after a
    recorded tool defect, and a speed-up is not a defect (R12). A uniform control is run again only
    after a recorded tool defect in the control's own code (R4). A reproduction (R16) is not a
    re-run: it writes only its `reproduction` record, appends nothing to the candidate log and
    charges no candidate's row, a heavy one only the feature-wide row (below), so it
    can neither replace evidence nor add any. The original stands, and a
    reproduction that differs from it on a field that enters a verdict is a finding that blocks the
    candidate's eligibility, `blocked`, as an unverified hypothesis does (spec FR-060), until it is
    resolved; in the environment that made the original it is a tool defect, which gives this one
    re-run, a new measurement in the original's row, whose own result raises R by the round rule if
    it fires. A difference in a field that decides no verdict, such as a p-value, is reported and
    blocks nothing.
  - **Stricter changes during a candidate's runs.** A stricter change of a rule is applied first
    by recomputing the verdicts from saved outputs. New measurements it needs, such as more
    inputs, are a new measurement of the same kind under the changed rule, not a re-run: the
    old records stay, and the new hours count against the same row. Every firing already
    recorded stands, so a stricter change can only raise R or make a candidate ineligible,
    never undo a raise. If the row cannot hold the new run, that evidence is inconclusive and
    the candidate ineligible at that size. A budget lowered below the hours already used leaves
    zero hours: the results so far stand, and no further run of that row starts.
  - Each candidate's log entry records the hours used per row (data-model §3). Each record
    states the hours projected and used, the measured speed and the engine's code hash. Others
    reproduce the counts and verdicts of finished runs exactly, and an inconclusive outcome as
    "did not finish within the recorded budget on the machine of R1 with that engine", a fact
    about the run and not a property of the candidate; the final report says so.
  - **What else is charged.** Validation runs on published values (R12's table) charge no candidate:
    they have their own cap of 8 h per instance, as a search instance does, and a heavy one
    is charged to the feature-wide row (below). The cross-checks between
    kinds (R12) run on each candidate's own boxes, once per candidate and tool version, as the
    solver cross-checks of its trail row, each instance capped at 8 h; a failed cross-check is a
    tool defect. The D4 reduced-width searches are trail searches on
    their candidate and count against its trail row, and so do the rotation-amount searches of R15,
    at each width searched: each instance is capped at 8 h, and its projection reserves hours like
    any other run. The FUT-SEC-8 vector check and sweep fall under the demonstration's own budget
    row (spec, Pre-registered Design Protocol). A uniform control (R4) belongs to no candidate and
    runs once per test and size, but every candidate's 12 h row is charged, at each size, that
    size's control hours, whether the control ran for it or before it, and the row's reservation
    counts them by projection until they exist; the control projects first and runs only if every
    entered candidate's row can hold it, and it writes no candidate-log entry: the Budget guard
    reads the control records when it charges each row (cli contract).
  - **The feature-wide row.** Beside the six candidates' rows and the FUT-SEC-8 row, one
    feature-wide row of 66 h holds every heavy run that charges no candidate: validations and
    re-validations on published values (R12), heavy reproductions (R16) and FR-053's test with two
    worker counts. Each projects first, as every heavy run does, and is refused, exit 2, once its
    projection does not fit the hours left in the row. A heavy reproduction runs only on the owner's
    request, quoted with its date in its record; the agent never starts one on its own, and a light
    reproduction needs no request.
  - **Order of sizes.** Each kind of evidence runs at 4×4, then 8×8, then 16×16. A larger size
    starts only when the smaller one's run of that kind has finished without making the
    candidate ineligible, so a candidate that fails at 4×4 spends none of its 16×16 hours
    (FUT-GRID-5; checklist D8). Within a size the kinds run in plan phase 5's order (R4, "Rounds
    measured"), and a bias test extended to a raised R is a new measurement of its kind, charged to
    the 12 h row. The order counts evidence only: a probe writes nothing but its `projection`
    record, which is not evidence, so the probes at 8×8 and 16×16 that a 4×4 run's projection needs
    run before it, while evidence of that kind at a larger size still waits for the smaller size's
    run.
  - **The other family.** Once D4 has chosen a family (R6), the other family's candidates wait,
    their rows reserved: they are analysed at the production width, in this section's order, only if
    the chosen family ends with no eligible candidate, once every candidate of the chosen family has
    its final decision; otherwise each that was not analysed there is `ineligible`, with the reason
    "not analysed at the production width: D4 chose the other family".
  - **After a rise of R** (spec round rule). Every record that depends on R is made again at the new
    variant, each a new measurement of its kind, charged to its row where this section budgets the
    kind: first the constant table for the new R with its checks (R15); then the inverse and
    invariant checks (R13); then the `cost` records and the reference outputs (R5, R11); then the
    bias tests, extended to the new R (R4). The propagation through instantiate and its margin over
    R_f are computed again (R13). A check made again that fails or fires raises R again or makes the
    candidate `ineligible`, as its kind says, and the sequence repeats until R no longer rises; a
    row that cannot hold a run it needs leaves that evidence inconclusive and the candidate
    `ineligible`. The trail bounds, the dependency matrices and the `degree` records read no R and
    stand.
  - **Heavy runs.** A heavy run is any run that is of a kind this section budgets, uses more than
    one worker process or thread, or is projected to take, or last took, more than 10 minutes. Every
    heavy run takes the lock of R16, never overlaps another heavy run or any battery run, projects
    first and records `heavy_run` true (FR-045). The examples that FR-045 and the cli contract list
    are cases of this rule, and a test checks that every budgeted kind and every script with a
    worker option takes the lock. Every other kind is light: one this section does not budget that
    runs with one worker in under 10 minutes, such as the constants, the vectors and the constructed
    states, `mode_limits_v3.py`, the round rule, the D4 choice, the claim register and the re-check.
    The tests of User Story 4, R16 and FR-061 reproduce the light kinds, and a budgeted kind is
    reproduced only on the owner's request, quoted with its date in the reproduction record, as a
    heavy run charged to the feature-wide row (R16). FR-053's test with two worker counts
    is a heavy run: it runs a stated test operation list, takes the lock,
    projects first, charges no candidate, only the feature-wide row, and is not
    evidence. The test suite marks it heavy, so the suite passes only while no
    heavy run holds the lock, and otherwise fails naming the lock.
  - **Projection before every heavy run.** A timing run of at most 60 s on the candidate itself
    projects the run's hours from the counts of R4, R8 and R13. It is a `projection` record
    (data-model §1), like any timing probe: its inputs are the first inputs of the run it
    projects, its outputs other than timing are discarded unread, and the record says so; its
    time counts against the row of the run it projects. The run starts only if its projection, plus
    the probes of every run its row still needs (its own kind at every larger claimable size, and
    every other kind of the row at every claimable size), fits the hours left in its budget row;
    this reserves the hours of every later run without fixing a split. Each row's kinds run in a
    fixed order: the 12 h row the frequency test, then the avalanche test, each with its control;
    the 6 h row the inverse tests, exhaustive bijectivity, dependency matrices, symmetry and
    invariant checks and the `degree` records; the 48 h row first the solver cross-checks at w = 4
    and 8 on the candidate's boxes or nonlinear layer with the first amounts of its recorded space
    in tie order, fixed before the run, so that they need no search result (R12); then the
    rotation-amount searches and the D4 reduced-width searches, whose bound records count once those
    cross-checks have passed; then, once the amounts are chosen, the cross-checks of the chosen
    amounts scaled to w = 4 and 8, before any production-width search counts; then the box tables,
    the box-trail searches and the active-box or active-S-box counting. The order of sizes stays.
    Otherwise the engine is made faster first, with more worker processes or with a C evaluator
    generated from the same operation list. A C evaluator agrees with the scalar interpreter on
    the candidate's committed reference outputs for R8's 16 Π inputs before its first run (R11),
    not on the `phyco-v3` vectors, which exist only after selection. Counts and budgets never
    change to make a run fit, and the record keeps the projection beside the time used.
  - The most the feature can spend is six candidates × 66 h, the feature-wide row's 66 h and the
    FUT-SEC-8 row, which holds one pass per target: 462 h, about 19.3 days of runs, beside that
    pass. It is a cap: every heavy run is charged to one of these rows, and each row refuses a run
    once it is spent.
- **Stricter means**: every budget may only be lowered (stop rule), and a lowered budget applies
  as above; the order of sizes, the projection rule and the one re-run per kind stay.
- **Rationale**: the stop rule needs a budget that ends "evaluated". Solver time dominates; 8 h
  per instance keeps one stuck search from consuming a candidate's budget. A cap on the feature as a
  whole follows from the three-candidate limit and the feature-wide row, which bounds the heavy runs
  that charge no candidate.
- **Alternatives**: no budget (the stop rule could never fire); a budget in core-hours
  (multithreaded and single-threaded solvers would not compare).

## R8. Vector lengths at every size, large sizes included (FR-036, FR-054, FR-058) — protocol

- **Decision**:

  | Vectors | Every supported size and evidence variant | Every claimable size |
  |---------|------------------------------------------|----------------------|
  | Π and Π⁻¹ | 16 inputs: all-zero, all-one, alternating `0x55…`, a counting pattern and test states 0…11; the state after every phase of every round for the first 4 inputs, as `pi_trace` returns it; the output for all 16 | — |
  | Mode | — | 2 development keys (key and nonce 0, key and nonce 1) × 10,000 32-bit words, in generate requests of 1, 7, 64 and 1,000 words in that order, cycled, the last request taking what is left (nine cycles, then 1, 7, 64 and 280 words), with forget after each request; the header says `schedule=cyclic-truncated` (data-model §11) |
  | Long run | — | the SHA-256 of the first 2²⁰ output words for key and nonce 0, in requests of 4,096 words (FR-058 "long runs"), taken over FR-015's canonical serialization as 4·2²⁰ raw bytes, not over the `%08X` text lines, so that feature 006's C stream and the hardware export can reproduce it from their own output |
  | Constructed states | the edge states the design document lists (FR-054) | the same |

  - Every input comes from R3: keys, nonces and test states by index (keys and nonces 0 and 1,
    test states 0…11), and the fixed patterns and edge states as constructed inputs of R3's
    classes (1) and (2).
  - Tracing every phase, not only every round, lets an RTL mismatch be located to one stage
    (FR-036); lengths only grow, so this rule allows it.

  - Lengths are the same at 4×4, 8×8 and 16×16. The output per call of Π grows with n² (r = 768,
    3,840 and 16,128 bits), so the 320,000 bits of a 10,000-word vector take at least 417, 84
    and 20 calls of Π, plus one forget call per request. The timing probe of R4 measured 60 ns per
    pure-Python word operation, so at R = 32 and 32 word operations per node and round a call
    takes about 1 ms at 4×4 and 16 ms at 16×16, and the 2²⁰-word digest under a minute at every
    claimable size.
  - Generated files hold only deterministic content (data-model §11). The command (script and
    arguments, relative to the repository root), the interpreter, the model's SHA-256, the
    platform, the measured speed (calls of Π and words per second) and the generation time go
    to the sidecar `vectors/phyco-v3/MANIFEST.json`, one entry per generator run with its
    `record_id`, which `--check` does not compare; FR-036's "measured speed stated" is met there.
    `--check` writes a `generator-check` record under
    `reports/004-crypto-architecture-v3/generator-checks/` with the common fields (data-model §1),
    each generated file's path and SHA-256 and the verdict `match` or `differs`; SC-009's evidence
    is each generator's pair of such records, one per platform, which quickstart M1 to M3 and the
    final report cite. The sidecar is frozen with the vectors (data-model §13), as the record of the
    runs that produced them; after the freeze a generator runs only with `--check` or `--reproduce`,
    which write their records under the reports directory and never to the sidecar. If
    generating a file takes over an hour, it is generated once and its time recorded; its length is
    not reduced.
- **Stricter means**: lengths may only grow.
- **Rationale**: the spec allows shorter vectors at large sizes "where the model's speed limits a
  size". Because a call's output grows with the grid, speed does not limit the 10,000-word
  vectors at 16×16, so they stay full length. Traces are kept for step-by-step comparison
  (FR-057) and for the later RTL (FR-056).
- **Alternatives**: 10⁶-word mode vectors at every size (large files for little extra coverage;
  the long-run digest covers long runs); traces for every input (the files grow with R × b).

## R9. The target advantage for the output limits (FR-007, FR-010) — protocol

- **Decision**: the output limits per instantiation and per key, and the number of keys u, are
  powers of two at which the mode theorem's bound (R10), with Π modelled as a random
  permutation (FR-004), is at most

  ```text
  ε = 2⁻⁶⁴, evaluated at N = 2¹²⁸ offline evaluations of Π or Π⁻¹
  and with every online quantity (data, calls, instantiations, reseeds, keys) at its limit.
  ```

  - A committed script evaluates the bound at the limits and checks that doubling any one limit
    would push it above ε. Where limits trade against one another, the design document states
    its choice and the reason.
  - **Units.** The theorem's unit, calls of Π, is primary, and each limit is also given in bits
    at every claimable size. A request of n bits takes ⌈n/r⌉ output calls plus one forget call,
    and instantiate's calls are stated; `limits.json` lists both units (data-model §10).
  - **Nonces.** Two ways are allowed (FR-006). (1) A counter per key, never repeated or
    wrapped, kept by the caller across objects and devices. (2) Random 128-bit nonces, whose
    collision probability, at most q²/2¹²⁹ for q instantiations, becomes a term of the bound;
    random nonces get their own per-key instantiation limit, at most 2³², so the term stays
    within ε.
    A `Generator` cannot tell a random nonce from a counter value, so it holds every key at this
    smaller limit whatever nonces the caller uses: one instantiation counter per object, and the
    instantiate past the limit raises `LimitExceeded` and ends the object, as the other per-key
    limits do. Across objects with one key, the same limit is a usage rule for the caller, stated
    with the other per-key limits.
  - The bound is increasing in N, so it then holds for every adversary below the target strength.
  - The per-request limit is the smaller of the per-instantiation limit and 2¹⁹ bits, the largest
    request SP 800-90A allows its DRBGs. Within one request, a compromised state reveals the
    request's earlier blocks through Π⁻¹, so the request size bounds what a state compromise
    exposes before the next forget call. The design document may lower it, never raise it.
  - **Backtracking resistance** (FR-004): a state compromised between calls reveals nothing
    about output before the last forget call; one compromised within a request reveals that
    request's earlier blocks back to the last forget call, at most the per-request cap. For a
    first request that walk could reach instantiate's state and the key, so instantiate also
    ends with a forget call, in the form the theorem covers (R10). A state read by a probe or a
    fault in mid-request is the hardware form of this risk, deferred to feature 008 (T4,
    FR-008).
  - Every online quantity the bound counts (output, calls of Π, instantiations per key, reseeds)
    has a limit and a counter, and the model refuses any call that would pass one (FR-007). One
    `Generator` object is bound to one key and cannot be used after zeroize, so it enforces the
    per-key limits for its key. Across objects, processes and devices, the per-key limits and u
    are usage rules that the design document states for the caller; no single object sees them.
  - If no positive limit reaches ε (a term such as N/2^c needs c ≥ 192), the mode or the
    capacity changes (c may only rise); ε does not.
- **Stricter means**: ε may only fall, N may only rise, and the per-request cap and the
  random-nonce instantiation limit may only fall.
- **Rationale**: at the limits, an attack with 2¹²⁸ evaluations gains at most 2⁻⁶⁴, so its time
  over advantage stays at least 2¹⁹², well above 2¹²⁸. ε = 2⁻¹²⁸ is unreachable: a term such as
  N/2^c alone is 2⁻¹²⁸ at c = 256. 2⁻⁶⁴ is stricter than the 2⁻³² of SP 800-38D's IV-collision
  rule. Terms of the form M·N/2^c and u·N/2^k, typical of keyed-duplex bounds, would give limits
  of the order of 2⁶⁴ blocks per key and 2⁶⁴ keys at c = k = 256; the values come from the
  theorem once its paper is read (R10).
- **Alternatives**: ε = 2⁻³² (looser); stating the bound without ε (FR-007 asks for it); a limit
  set by hand (it must follow from the theorem).

## R10. The mode theorem and the reading list (FR-013, FR-004, FR-016)

- **Decision**: the mode chapter adopts the full-state keyed duplex of Daemen, Mennink and Van
  Assche (ASIACRYPT 2017) for keystream and multi-user security. For backtracking resistance
  across forget, it uses the result for exactly its forget construction: the sponge-based PRNG of
  Bertoni et al. (CHES 2010) or the forward security of Gaži and Tessaro (EUROCRYPT 2016),
  whichever matches it. Each call (instantiate, generate, forget, reseed) is mapped to the
  theorem's calls, and each precondition is listed with the design feature that meets it.
  - **Initialization.** Key and nonce are placed in the initial state at stated positions, and
    the rest of it is set to stated constants, as the full-state keyed duplex initializes
    (FR-013). Later inputs, the personalization string and the reseed input, are absorbed over
    the rate only (FR-018), and the mode chapter shows that this is a special case of the
    theorem's absorption.
  - **Instantiate ends with a forget call**, in the form the theorem covers, so that no state
    compromise walks back through Π⁻¹ to the key (R9).
  - **Reseed** is mapped to the theorem's absorption call with attacker-chosen input (T9;
    FR-016). A reseed never resets a counter (model contract).
  - Each of these is listed among the preconditions, "unverified" until its paper is read. If a
    paper's form differs, the design takes the paper's form in a new design-document version, or the
    feature stops (below).
- **Reading the papers is a download** (FR-046); the owner approved each file of R19 on
  2026-11-01. Until a paper is on disk and read, the mode chapter marks its use of that theorem
  "unverified", and L1 is not recorded while it is (FR-012): the security-target review may read
  Approved, and the "L1 recorded" row then reads "blocked", naming the missing paper. The owner
  design review and the freeze need every theorem the mode chapter uses `verified` in `limits.json`,
  with each precondition marked met in the mode chapter: `design_freeze.py create` exits 2
  otherwise, naming the theorem, and the freeze record holds `limits.json`'s SHA-256 and each
  theorem's status (data-model §13).
- **If a call does not match a theorem exactly**, the call is changed to the theorem's form
  (forget as a duplexing call that overwrites the outer part, reseed as a domain-separated
  absorption), or the feature stops (Edge Cases). A mode without a matching theorem is never
  adopted.
- **Rationale**: one assumption, Π, for every property (strategy note §4.2). Two of the three
  properties sought need different theorems, so the plan names both and makes the match a check.
- **Alternatives**: counter mode with feed-forward (D1 alternative; no forget call, and the input
  must be stored); one theorem for all properties (no single paper is known here to cover
  keystream, multi-user and backtracking for this exact mode).

## R11. One operation list per candidate

- **Decision**: each candidate is written once as an operation list, `research/004/ir.py`, from
  which every tool derives what it needs:
  - Only two operation forms exist: `dst ← dst ⊙ F(srcs)` with ⊙ ∈ {⊕, ⊞, ⊟}, dst ∉ srcs, and F
    built from rotations, shifts, bitwise functions and round constants; and `dst ← rotl(dst, k)`
    with k fixed. Both are invertible whatever F is, so a list made of them is bijective by
    construction wherever the phase rule below holds (FR-019), and the inverse list is generated
    mechanically. A list not made of these two forms is refused before any test.
  - A round is a sequence of phases (colour classes), and the updates within one phase read no lane
    that another update of the same phase writes. The loader checks this phase rule at every
    supported size, from the declared reads and writes after the neighbourhood is resolved, and
    refuses a list that breaks it, exit 2, before any test; a committed test runs the check on every
    list at every size, with a stated list that breaks the rule at one size only, which it must
    refuse. Both interpreters apply a phase as the hardware does, each update reading the values at
    the phase's start, which equals list order where the rule holds, checked on the vectors;
    bijectivity by construction, and with it spec FR-032's transfer from 2×2,
    rests on the rule at each size. A phase is a pipeline stage for FR-025:
    it takes one clock cycle, so a round of P phases takes P cycles, and carry chains are counted
    per phase (R5). A round may visit a colour class more than once, so P counts phases, not
    colours; in a three-colour schedule the classes form a proper colouring of the torus (R14).
  - **Channels.** A channel is one w-bit word passed from a node to a neighbour in one phase. A
    node receives at most four channels per phase, for example one from each neighbour or two
    from each of two, counted from the operation list, the linear layer between boxes included
    (FR-018).
  - **One structure at every width and size.** The list's structure (its operations, their
    forms and order, and the colour schedule's rule) is the same at every width and size. Only
    w, n and values derived from them by stated rules change: rotation amounts by the
    scaling rule and the placement of their K sets by its rule from n (R15),
    constants by the constant rule, the colour count by n's parity, food-node
    positions by their rule, c and the key and nonce lengths (R14). Anything else makes a
    different design, a new candidate (stop rule).
  - From the list: a scalar interpreter (Python integers) and a batch interpreter (numpy
    `uint64`, masked to w bits after every operation), the inverse, the dependency propagation
    (R13), the cost model (R5) and the bit-level trail models (R12).
  - **Reference outputs.** Before any evidence run on a candidate, the scalar and batch
    interpreters agree on reference outputs for R8's 16 Π inputs at every variant the candidate
    uses, computed by the scalar interpreter and committed with the candidate. A C evaluator
    must agree on the same outputs before its first run (R7). A disagreement between two evaluators
    is a tool defect. A rise of R makes a new variant, whose reference outputs are computed and
    checked before its first evidence run (R7, "After a rise of R").
  - Every rotation, shift and constant is a fixed value of the list (FR-020); nothing in the list
    can read data to choose an operation.
  - After selection, `phycoweb/model_v3.py` is written by hand from the design document for
    readability, and a test checks it against the interpreter on every committed vector and on
    every committed reference output (FR-035).
- **Rationale**: evaluation, inverse, diffusion, cost and trail bounds then describe one object,
  so a bound cannot drift from the code it bounds. The Feistel-type form is the strategy note's
  rule for invertible coupling (§5.1).
- **Alternatives**: hand-written code per candidate and per tool (several copies that can
  disagree); an external framework such as CASCADA (a download; its IR would not match the
  model).

## R12. Trail-bound tools and their validation (FR-038, FR-039)

- **Decision**:
  - Without any download: scipy's HiGHS solver (`scipy.optimize.milp`, present in scipy 1.15.3)
    for active-box and active-S-box counting and for bit-level models at small widths;
    self-written exhaustive tables (differential and linear) for boxes and S-boxes at reduced
    widths, in numpy or C; a self-written branch-and-bound trail search for ARX in C (WSL), with
    the exact models of addition (Lipmaa and Moriai, 2001; Wallén, 2003).
  - **Box widths.** Full difference and linear tables are computed for each distinct box of up to 16
    bits (w ≤ 8; FR-022), the K sets of rotation amounts making K boxes (R15). At w = 16 and 32,
    each distinct box's trail bounds come from the validated ARX search with the exact models of
    addition, each box within the 8 h per instance of R7 and the candidate's 48 h row, and the bound
    for Π follows by counting active boxes, each at the smallest of the K
    boxes' bounds. The active-box counting also checks the rationale's branch
    numbers or activation rule (R6).
  - **Solver settings**, fixed and recorded in every record: `mip_rel_gap` 0, the 8 h
    `time_limit`, and the proven dual bound (`mip_dual_bound`) used, never the best solution
    found. The feasibility and integrality tolerances and the thread count, which scipy's `milp`
    does not expose, are HiGHS's built-in values in the pinned scipy 1.15.3, recorded as such;
    scipy documents the algorithm as deterministic. Every MILP bound record states that its status
    rests on these built-in tolerances, and the design document and the final report say so beside
    R_bound. A floating-point weight becomes data-model §6's rational by rounding down to a multiple
    of 2⁻¹⁶, never up, which weakens the bound, and an active-box or active-S-box count is the
    integer at or below its proven dual bound, with no tolerance, so a dual bound of 9.9999999
    counts as 9; the record holds the float and the rounded value. A box lost to this rounding is
    recovered only by an exact method where one exists, the cross-checks at w = 4 and 8, never by
    rounding up.
  - **What counts as a bound.** Only a proven result: an optimal or infeasible status with the
    proven dual bound used, or a search that exhausts its space within its cap. A search that times
    out gives no bound, and its record says `inconclusive` (R7). A bound that sets R_bound is
    confirmed where an exact method exists: at w = 4 and 8 by the exhaustive tables (the
    cross-checks between kinds, below), with weights kept as rationals rounded down (Solver
    settings). At 16 and 32, and so at the production width R_bound comes from, no exact
    confirmation exists without a further tool, so those bounds are reported as proven by the solver
    within its tolerances, a limitation stated in each record's `limitations` (data-model §1).
  - **Trails.** A trail is a characteristic of Π, its difference or mask after every round with its
    exact weight, exhibited by a validated tool that searches Π at the size and width the round rule
    uses, the production width at a claimable size; it is held in data-model §6's `trail` record,
    which `round-rule.json` cites, and enters R_dist. A bound, a box's trail, an active-box or
    active-S-box count and a bound search's optimum are bounds, which enter R through R_bound; an
    optimal characteristic that a search of Π returns with its weight counts as a trail. So 2·R_dist
    counts only trails exhibited at the production width, and where none is, trail-based attacks
    enter R through R_bound + Δ.
  - **Bounds per size.** Before selection, every candidate's R_bound at each claimable size comes
    from a bound computed at that size, as the round rule's "at that size" reads, and the 48 h
    reservation keeps every such search (R7). A proof in the design document that carries a bound to
    a larger size for every claimable n, for example that every r-round trail at n×n activates at
    least as many boxes as at 4×4, checked by computing it at 8×8, may be written for the selected
    candidate only; it serves as a check beside the computed bounds, reported in the rationale, and
    replaces none. A candidate whose row cannot hold a 16×16 search has no R_bound there and is
    `ineligible`, as for any spent row.
  - Only with a separate approval, since R19 requests none: a SAT solver with Python bindings,
    or CryptoSMT or CASCADA, as a faster or independent cross-check.
  - **Fixed tool set** (**protocol**): the trail tools are those with a `re-found` validation record
    when the feature's first trail search starts, named by their rows in the table below (ARX
    search, active-S-box counting, long-trail active-box counting, exhaustive tables). Each version
    is identified by its exact hash and counts only with a `re-found` record of that hash, so a
    fixed or faster version of a named tool is the same tool and may serve searches not yet run,
    after its re-validation. None is added afterwards. A search that reached its cap is never run
    again, with another tool or another version of the same one, except as R7's one re-run after a
    recorded tool defect, and a speed-up is not a defect. This plan requests no solver
    download (R19), so the set is HiGHS and the self-written searches unless the owner approves
    one before that moment.
  - Each tool re-finds a published result of its kind before any of its results counts, and its
    validation record cites the paper, table and value, taken from a copy the owner provides or
    from the paper's download, approved on 2026-11-01 (R19). Every counted tool has one known
    result, each with a validation record (data-model §7), and a second fixed before its first
    validation (Second known results, below); the structural tools' known results
    are in R13, and the bias test's in R4.

    | Tool | Kind | Known result to re-find |
    |------|------|-------------------------|
    | ARX differential and linear search | ARX trails with the exact models of addition | the weights of the optimal trails of SPECK32 over the first rounds (Biryukov and Velichkov, 2014; Liu, Wang and Rijmen, 2016) |
    | Active S-box counting | MILP counting of active S-boxes | PRESENT: every 5-round differential characteristic has at least 10 active S-boxes, the stated minimum (Bogdanov et al., 2007) |
    | Long-trail active-box counting | MILP counting of active ARX-boxes | a published long-trail bound of SPARKLE (Beierle et al., 2020), from its published box bounds |
    | Exhaustive box and S-box tables | exhaustive tables | every entry of the PRESENT S-box's published difference and linear tables |

  - **What must match.** For each row, the exact published value over the stated rounds: for a
    trail search, the weight of the optimal trail, not the trail itself, since several trails
    can share a weight; for the S-box tables, every entry; for PRESENT, the stated minimum. Any
    difference is a failed validation.
    For a known result that is not a published value (S12 to S15, the FUT-SEC-8 recovery, and the
    known results of the structural tools and the cost model, R13), data-model §7 states the
    comparison: exact equality for every deterministic fact, and for a measured fraction a count in
    the binomial interval around the recorded fraction at the tool's sample size, with at most 0.005
    in each tail; anything else is `not re-found`.
  - **Cross-checks between kinds.** They run on each candidate's own boxes, once per candidate and
    tool version, as the solver cross-checks of that candidate's 48 h row, each instance capped at
    8 h (R7): for each distinct ARX-box of each ARX candidate at w = 4 and 8 (boxes of 8 and 16
    bits), the ARX search's optimal single-trail weight over r rounds of the box must equal the
    optimal trail weight computed from the exhaustive tables by a search over characteristics, the
    best product of one-round entries, for every r from 1 to the largest at which that computation
    finishes within its 8 h cap, one round equalling the table's best entry, before the search's
    results at w = 16 and 32 count; and the active-S-box counter's minimum over r rounds at 4×4 must
    equal the exhaustive minimum from each Boolean candidate's nonlinear-layer tables at w = 4,
    whatever its form, over the same range of r. Each record lists both values per r, compared by
    exact equality; a trail weight above a differential's weight, as clustering gives, is expected
    and not compared. They run first in the candidate's 48 h row, on the first amounts of its
    recorded space in tie order, fixed before the run, so that they need no search result; the
    rotation-amount and D4 searches count once they pass, and after the amounts are chosen, the
    chosen amounts scaled to w = 4 and 8 get cross-checks of their own before any
    production-width search counts (R7). A failed cross-check is a tool defect (R7). The validations
    of the table above, on published values, stay validation runs charged to no candidate, a heavy
    one to R7's feature-wide row. A tool used outside its validated kind writes `not evaluated`.
  - **Re-validation.** A tool is validated again after any change to its code (its SHA-256
    differs), a dependency upgrade, or a use at a word width, operation set or kind of model
    outside its validated kind. Each counted result cites the validation record of the tool's exact
    hash. A re-validated version of a named trail tool serves only searches not yet run (Fixed tool
    set).
  - **A failed validation.** The defect is recorded with its cause and fixed, and the tool is
    validated again on its second known result as well as the first, both fixed before its first
    validation (below), which the defect record cites, so that a fix cannot be tuned to one value. A
    tool whose first validation record says it has no second known result stays unvalidated after a
    failed validation, and its results are `not evaluated`, as for a value that cannot be obtained.
    Attempts are not limited in number, but each is recorded, and a heavy one is charged to R7's
    feature-wide row, which refuses it once spent. Results of the failed version never count;
    results already counted from an earlier validated version stand, since they cite its hash.
  - **Second known results.** Each counted tool's second known result is fixed before its first
    validation, with its source, in the provenance log beside the first (data-model §14): a second
    published value of its kind from R19's approved papers (paper, table and value) where one is
    there, or else a self-written result of its kind, written and logged before the tool is drafted,
    as R13's are. A tool with neither says so in its first validation record.
  - **A value that cannot be obtained.** If a known result's published value cannot be had, the
    tool stays unvalidated and its results `not evaluated`; the owner may provide the value with
    its source (R19). If no trail route is validated, no candidate can establish R_bound, none
    is eligible, and the feature recommends stopping (stop rule).
  - Every bound record says it bounds single trails under the usual independence assumptions;
    clustering, hulls and key-dependent effects are open for feature 005 (FR-038).
- **Stricter means**: known results, cross-checks and re-validation triggers may only be added,
  and the tool set stays fixed.
- **Rationale**: re-finding a known value is the lesson of `nistrng` (security.md §11.2). The
  reference designs are used only inside validation tools, never in Π (D6).
- **Alternatives**: trusting a published tool without re-finding a result (FR-039 forbids it).

## R13. Structural checks (FR-019, FR-029, FR-037)

- **Decision** (**protocol** for the counts):
  - **Phase rule**: before any other check, the loader's check of R11 runs at every supported size,
    and a committed test runs it on every operation list at every size, with a stated list that
    breaks the rule at one size only, which it must refuse (spec FR-019); whether the rule holds
    depends on n, since the neighbourhood is resolved per size (R14).
  - **Inverse**: Π⁻¹(Π(x)) = x and Π(Π⁻¹(x)) = x for the 16 vector inputs and 2¹⁰ test states at
    every supported size and variant.
  - **Exhaustive bijectivity**: 2×2 at w = 4 (b = 32), all 2³² inputs, through the batch
    interpreter, with a 2³²-bit (512 MiB) bitmap of outputs; the variant is bijective if the
    bitmap holds 2³² ones. A heavy run: about 1 h at R = 16 and 64 numpy operations per node and
    round, from the timing probe of R4, plus the bitmap.
  - **Dependency**: exact structural dependency, propagated through the operation list: XOR, AND,
    OR and NOT unite bit sets; rotations and shifts move them; output bit i of an addition or
    subtraction depends on bits 0…i of both operands. R_f and R_b are the first round counts at
    which every output bit depends on every input bit. A structural dependency that the avalanche
    test (R4) never observes fires there and raises R_dist, so a dependency that always cancels
    cannot pass silently. Where the matrices show no dependency, the avalanche test must observe
    no flip; a disagreement is a tool defect (R4). "Computed exactly" (FR-029) means this exact
    structural propagation, which over-approximates actual dependence: full structural
    dependence is necessary and not sufficient for full diffusion, and the avalanche test, with
    its cross-check, observes it.
  - **Through instantiate**: the calls of Π and rounds between key loading and the first output
    are stated, and the propagation through instantiate as a whole shows every state bit
    depending on every key and nonce bit before the first output, with the margin over R_f stated
    (FR-029). After a rise of R, the propagation and its margin are computed again for the new
    variant (R7, "After a rise of R").
  - **Food nodes**: per supported size, the design document states the number of food nodes, at
    least three in an asymmetric arrangement at every claimable size (Symmetry, below), their
    positions by the rule and the reason, for example the number of rounds until every
    lane depends on a constant injected in round 1, from this propagation.
  - **Symmetry**: at every supported size, no symmetry of the torus that moves a node may map a
    constant pattern to itself: no composition of translations, rotations by 90°, 180° and 270°,
    and reflections. Nor may rotating every word by the same amount k = 1…w − 1 map a round's
    constants to themselves: XOR, AND, NOT and rotations commute with that rotation and additions
    keep it with a fixed probability, so without shifts only the constants break it (rotational
    cryptanalysis). The spec names translations and rotations; reflections, compositions and
    word rotations are added. The patterns checked are each round's constants, the placement of the
    food nodes and every per-node constant, such as the rotation amounts, each pattern on its own;
    amounts equal at every node, which every translation maps to themselves, fail, so the amounts
    differ between nodes, K ≥ 2 sets placed by a rule from n (R15). One food node is fixed by a
    rotation about it and two by the half-turn about their midpoint, so the food-node rule takes at
    least three food nodes in an asymmetric arrangement, such as (0,0), (0,1) and (1,2), which no
    symmetry that moves a node maps to itself at 4×4, 8×8 and 16×16 (computed on 2026-11-01), so
    none maps to itself one set of amounts at those nodes against another elsewhere; at every
    claimable size this check stays as written. At 2×2 and 3×3, where every placement of food nodes,
    and so every placement of one set of amounts against another, has a symmetry that moves a node
    (computed the same day), the placements of the food nodes and of the amounts are checked
    together with the round constants as one pattern; the `symmetry` record says so, the size
    profile marks the variant, and no claim covers it (D3), as for the constants at 2×2 with w = 4
    below.
  - **Constants within a call**: no two constants of one call of Π are equal, equal up to a word
    rotation by k = 1…w − 1, complements of one another, or rotations of complements. The
    constant script checks this beside the symmetry checks (R15).
    The rule's reading order skips any word that is periodic (equal to its own rotation by some
    k = 1…w − 1) or related in one of these ways to a constant already taken in the same call (R15),
    so these relations hold by construction wherever one call needs no more constants than there are
    aperiodic classes under rotation and complement: 2 at w = 4, 16 at w = 8 and 2048 at w = 16,
    counted exhaustively on 2026-11-01, and far more at w = 32, so at every claimable size. Where a
    call needs more, as at 2×2 with w = 4 once one call needs three, the record of taken classes
    starts afresh each time every class has been used once, the script records every repeat, the
    size profile marks the variant, every check of this section still runs, and no claim covers it
    (D3). A periodic word is skipped because a word rotation maps it to itself; and without the skip
    even w = 16 would fail by chance, since 128 constants read plainly hold about 4 related pairs
    (4.86 × 10⁻⁴ per pair).
  - **Invariants**: on 2¹⁰ test states, after one round and after a full call: the sums modulo
    2^w and the XORs of the pressure lanes and of the vein lanes, and the same over each colour
    of the checkerboard (even n); and the S13 transport mode of
    `research/security/step_probes.py`, which adds 2 and −2 alternately to the pressure lanes,
    as an input difference. A form that keeps its value on every test state, or a difference that
    comes out unchanged on every test state, fails the check. A form that holds on more test
    states than its chance rate allows (2⁻ʷ for a w-bit sum or XOR; the null model of R4), by a
    binomial test at the bias rule's level, 0.005 divided by the number of forms and round
    counts tested, fails the check as a probabilistic invariant and raises R_dist at that round
    count.
  - **Algebraic degree**: for every candidate, and essential for the Boolean family, a `degree`
    record per claimable size, for Π and for Π⁻¹, computed in plan phase 5 after the other
    structural checks and before the frequency and avalanche tests. Each phase's degree comes from
    the operation list: from each box's or S-box's truth table where its width allows, otherwise
    from the stated degree of each operation, w − 1 for a w-bit addition, and a round of P phases
    counts the product of its phases' degrees. The count of r rounds is the product of the per-round
    counts, capped at b − 1, which needs no search tool. The stated w − 1 is an upper bound only
    where one operand is constant, since the top bit of the sum of two variable w-bit words has
    degree w (bit i has degree i + 1), so the record says that its count is the rule's, not an upper
    bound, and holds beside it an upper bound, w for an addition of two variable words, with the
    round counts at which that bound is at most 126. R_dist rises at every round count whose count d
    by the rule is at most 126, so no round count that the pre-registered rule raises is dropped: a
    zero-sum over a cube of dimension d + 1 costs 2^(d + 1), a distinguisher of the round rule like
    any other. The inside-out count adds to these: for each pair (r₁, r₂), with the rule's counts
    d_f(r₁) for Π and d_b(r₂) for Π⁻¹, a zero-sum built from a middle state over a subspace of
    dimension max(d_f, d_b) + 1, taken r₁ rounds forward and r₂ rounds backward, distinguishes
    r₁ + r₂ rounds at a cost of 2^(max(d_f, d_b) + 1) when max(d_f, d_b) is at most 126; the largest
    such r₁ + r₂ is recorded with its cost against 2¹²⁸ and raises R_dist as a forward or a backward
    count does. The derivation is validated under FR-039 on known results (below): it reproduces the
    rule's count exactly at w = 4, with the exact degree from the truth table reported beside it and
    the upper bound checked to be at least that degree, and a hand-derived inside-out count; the
    rationale cites the records.
  - **Call types**: where the call types draw on distinct constant streams (spec FR-023), the
    inverse tests, the symmetry checks, the checks of the constants within a call and the invariant
    checks run on each call type's permutation, or its stream, each record naming its call type, as
    the bias tests of R4 do, and R is the largest over the call types; the dependency matrices read
    no constant value and cover one permutation for all, each record stating that reason, as the
    trail bounds do (spec FR-023). Where the streams are not distinct, one permutation is covered.
  - **Order.** At each size these checks run after the trail bounds and before the frequency and
    avalanche tests, the `degree` records last among them (R4, "Rounds measured"). After a rise of
    R, the inverse tests, the invariant checks and the checks of the new constant table are made
    again at the new variant before the bias tests are extended (R7, "After a rise of R"); the
    dependency matrices and the `degree` records read no R and stand.
  - **Known results.** Each structural tool re-finds a known result before its results count
    (R12; data-model §7):

    | Tool | Known result to re-find |
    |------|-------------------------|
    | Symmetry check | S7's rotation structure of `phyco-v2`'s constants; and stated lists with planted torus symmetries (a translation, a rotation by 90° and a reflection) at n = 3 and 4, which it must find, and one with none, which it must clear |
    | Dependency propagation | the hand-derived matrices of a stated small operation list at 3×3 and at 4×4 |
    | Exhaustive bijectivity | a known permutation (2³² ones in the bitmap) and a stated map with collisions (fewer) |
    | Avalanche test | one planted result per path, each flagged exactly, bit for bit against its stated set at every round count tested: for the flip set, a stated variant that leaves one lane unmixed, every difference bit of that lane firing and no other; for the related-key and related-nonce set, a stated instantiation variant in which a stated key bit and a stated nonce bit never reach a stated lane; for the rotational pairs, a stated operation list in which one stated lane commutes with word rotation; and, without new inputs, its verdict code on every count 0 to N_a and its exact power at R4's δ_A (R4) |
    | Cost model (R5) | R5's hand-counted examples |
    | Degree bound | on a stated small operation list, for example one box at w = 4, over a few rounds: the rule's count, reproduced exactly, with the exact degree from its truth table reported beside it and the upper bound checked to be at least that degree; and a hand-derived inside-out count at w = 4, reproduced exactly |

    Each known result this feature writes itself, the small operation lists with their hand-derived
    matrices, the lists with planted symmetries and the one with none, the map with collisions, the
    variant with a planted gap, the instantiation variant with a key bit and a nonce bit
    that never reach a lane, the operation list with a lane that commutes
    with word rotation, R5's hand-counted examples and the small operation
    list of known degree with its hand-derived inside-out count, is written
    with its SHA-256 and entered in the provenance log (data-model §14) before
    the tool it validates is drafted, so its entry's `seq` comes before the tool's first entry; each
    structural tool's second known result is self-written in the same way, written and logged before
    the tool is drafted (R12, "Second known results"). The validation record cites
    both entries, and a test checks their order and that the hashes still
    match. What must match is stated per known result in data-model §7. Only the validation of tools
    whose behaviour does not depend on the neighbourhood transfers from 2×2 (box and S-box tables,
    the bijectivity bitmap, the cost model's counts), which is why the dependency propagation and
    the symmetry check are validated at 3×3 and 4×4 (FR-032).
- **Stricter means**: counts may only rise; symmetries, constant relations, forms and sources of
  R_dist may only be added.
- **Rationale**: structural dependency is the standard full-diffusion measure. Checking that it
  is observed as well rules out a dependency that always cancels.
- **Alternatives**: dependency estimated by sampling only (not exact, as FR-029 requires).

## R14. Supported sizes and variants (FR-017, FR-018, FR-032, FR-033)

- **Decision**:
  - Claimable sizes: 4×4, 8×8 and 16×16, at w = 32 and c = 256 with the frozen R (D3). Research
    sizes: 2×2, at every width with reduced capacity, and 3×3 if the design document specifies a
    three-colour schedule from the same generics; otherwise 3×3 is unsupported with that reason.
  - **Colour schedule.** The schedule is a function of n's parity, computed at elaboration from
    one stated rule (two colours for even n, three for odd n), so an odd n is the same core with
    another generic value. Without such a rule, odd sizes are unsupported, with the reason
    (FR-018). For odd n the rule gives a proper colouring of the torus, wrap-around links included,
    at every odd n from 3 to 15, checked link by link by a committed test: (i + j) mod 3 fails
    across the wrap at n = 7 and 13, while c(i, j) = (f(i) + f(j)) mod 3, with f a proper
    3-colouring of the n-cycle such as f(k) = k mod 2 for k < n − 1 and f(n − 1) = 2, holds at every
    odd n (FR-018).
  - **Keyed variants per size.** The list of supported sizes names each size's keyed variants:
    the production variant at every claimable size, and at 2×2 at least one keyed reduced
    variant, such as `n2-w16-R8-c64` with an 8-byte key and a 4-byte nonce (quickstart M6). A
    supported 3×3 gets one as well. Keyless variants are listed as permutation-only. FUT-GRID-2's
    "defined for every supported size" is met through the keyed variant each size has.
  - The research interface accepts every n from 2 to 16 for exploration, but n = 5, 6, 7 and
    9…15 have no vectors, R_f, R_b or bounds in this feature. Each is listed as an open item
    against FUT-GRID-1, with that reason (FR-018).
  - Widths: 4 (exhaustive checks, at 2×2 only), 8, 16 and 32. Rotation amounts are chosen at the
    D4 width (R6) and scale with w by the design document's rule, stated before the search
    (FR-024; R15). After scaling, every amount lies in 1 to w − 1 at every supported width; the
    constant script and the operation list refuse 0 and w, and where scaling would give 0 or w
    at w = 4, the rule names the allowed amount to use instead.
  - The operation list's structure is the same at every width and size, and only the values R11
    names change with w and n. Whether the phase rule of R11 holds depends on n, since the
    neighbourhood is resolved per size and at 2×2 a node's opposite neighbours coincide, so the
    loader checks it at every supported size (spec FR-019).
  - Variant ID: `<design>/n<n>-w<w>-R<R>-c<c>`, for example `cand-A1/n2-w16-R8-c64`, where the
    design is a candidate ID or, after selection, `phyco-v3`. The production interface accepts
    only the three production IDs and refuses every other ID with an error (FR-033).
  - **Keys of reduced variants** (FUT-GRID-2; checklist A7): a keyed variant of capacity c takes
    a c-bit key and a c/2-bit nonce, so 256 and 128 bits at every claimable size, and its row of
    the size profile checks FR-010's relations at s = c/2. c is a multiple of 16 as well as of w,
    so both lengths are whole bytes. A variant whose key and nonce leave no room in the state for
    the padding and domain bits is keyless: the research duplex refuses it, and only the
    permutation interface applies. The model contract and data-model §10 take these lengths.
    The key-loading interface is generic in c in the same way (FR-025): a c-bit key and a
    c/2-bit nonce, and none for a keyless variant.
- **Rationale**: the strategy note's table (§4.5). Every claimable size needs an established
  R_bound at the production width, so each one added costs trail searches. Powers of two keep
  the folded-torus layout regular. A key of c bits keeps key loading the same construction at
  every size, so evidence on reduced variants transfers, and a 2×2 state, 256 bits at w = 32
  and 32 bits at w = 4, could not hold a 256-bit key and a 128-bit nonce.
- **Alternatives**: every n from 2 to 16 supported (each claimable size needs its own R_bound,
  which would multiply the solver budget); a 256-bit key and 128-bit nonce everywhere, absorbed
  over several blocks where they do not fit (the construction changes at small sizes); keyless
  reduced variants only (key loading stays undefined at 2×2, against FUT-GRID-2).

## R15. Constants (FR-023, FR-024)

- **Decision**: round constants come from a maximal-length LFSR whose polynomial and seed the
  design document states. `scripts/gen_constants_v3.py` checks that the polynomial is primitive,
  reads the sequence in a stated order over (call type, round, food node), checks that within one
  call of Π no two constants are equal, equal up to a word rotation by k = 1…w − 1, complements of
  one another, or rotations of complements (R13), runs the symmetry checks of R13, and writes
  `phycoweb/constants_v3.py`. The design document states whether the call types draw on distinct
  constant streams (FR-023); where they do, the script's checks run on each call type's stream, and
  every kind of evidence whose result depends on the constants covers each call type's permutation
  (R4, R13). A table holds the constants of R rounds, so a rise of R generates the table again for
  the new R with every check of this section, and every record whose result depends on the constants
  names the SHA-256 of the table it read, so that a result on one table is never cited for another
  (spec round rule); with distinct streams, the reading order below makes a rise change every later
  call type's constants from round 1, so their results are measured again from round 1 (R4).
  - **The rule, fixed early** (**protocol**): the polynomial, seed, reading order and whether
    the call types draw on distinct streams are fixed by one stated rule before the first
    candidate is scored, and each candidate's instance of it before its first tool run,
    recorded in the candidate log's `parameters` (data-model §3). Its values follow; they become
    `settled` entries of the protocol change log before the first candidate is scored
    (data-model §18).
  - **The values** (**protocol**, settled on 2026-11-01). Degree 64; the polynomials x⁶⁴ + c(x) with
    c(0) = 1, taken in ascending order of the integer whose bits are c's coefficients; the first
    primitive one not on the frozen refused list below. Fibonacci form s(t + 64) = Σᵢ cᵢ·s(t + i)
    over GF(2), i = 0…63, with s(0)…s(63) the bits of ASCII `PhycoWeb`, most significant first
    (0x506879636F576562, 32 of 64 bits set), and output from s(64) on. Each table is read from the
    start of the output, w bits per word, most significant bit first, in the order call type (if the
    streams are distinct), round, food node, skipping any word that is periodic or related to a
    constant already taken in the same call (R13); where a call needs more constants than there are
    aperiodic classes, the record of taken classes starts afresh each time every class has been used
    once, and every repeat is recorded. The design document restates these values, and the script
    checks that the two agree.
  - **Refused constants.** The script holds a committed list of the polynomials and constant
    sets it refuses, each with its source, frozen with the rule before the first candidate is
    scored, its SHA-256 in the change-log entry that fixes the rule. It holds the polynomials and
    constant sets of R12's reference designs (SPECK32, PRESENT, SPARKLE) and of every design the
    strategy note, the spec, the plan, this document and security.md name, and the standard
    polynomials of degree 64 and 128: CMAC's R₆₄ and R₁₂₈ (SP 800-38B), GCM's (SP 800-38D), and the
    CRC-64 polynomials of ISO 3309 and ECMA-182. The check fails if the chosen polynomial is listed,
    or if a table contains a listed sequence. Each listed constant set is read as one bit string,
    its words in published order and most significant bit first, and a match is a run of consecutive
    table words of at least 64 bits (16 words at w = 4, 8 at w = 8, 4 at w = 16 and 2 at w = 32)
    equal to as many consecutive w-bit words of a listed string read from any multiple of w, under
    one of 2w transforms, each rotating every word of the run by the same k, k = 0…w − 1, with or
    without the complement of every word (k = 0 without the complement is the plain match), so that
    rotations of complements match, as in the relations of R13. The check covers every table
    the script writes, one per supported (n, w), and each call type's stream. Its record states the
    chance of an accidental match, at most T·L·2w·2⁻⁶⁴ for T table words and L listed words, so a
    failure shows reuse rather than chance. An addition to the list is proposed by the agent and
    approved by the owner as a stricter change in the protocol change log, since the list only
    grows, with the list's new SHA-256. Designs that the spec, the plan, this document or
    security.md name later are added when named, as the rationale's citations are, and the check
    runs again. A match makes each candidate whose polynomial or table it touches fail FR-023, an
    eligibility item, so that candidate is `ineligible` and the rules select among the others; a
    match in the shared polynomial touches every candidate and ends in a stop. The rule is never
    changed to escape a match. A match found after the freeze is a finding recorded at once in
    security.md and the report (FR-051), and `phyco-v3` stays as frozen. The
    standard polynomials matter: a plain search in ascending order finds x⁶⁴ + x⁴ + x³ + x + 1 first
    (computed on 2026-11-01), which is CMAC's R₆₄, a MAC's constant that re-decided feature-002
    FR-007 forbids, and also the CRC-64 polynomial of ISO 3309.
  - **Rotation amounts** come from a stated search over the possible amounts, ranked by the trail
    bounds they give. Amounts equal at every node fail the symmetry check (R13), so each candidate
    states K ≥ 2 sets of amounts and a placement rule from n whose placement has no symmetry of the
    torus that moves a node at any claimable size, such as one set at (0,0), (0,1) and (1,2) and
    another elsewhere (R13); a point of the search is an assignment of amounts to the K sets. The
    ranking is one rule for every candidate (**protocol**), recorded as a `settled` entry of the
    protocol change log before the first rotation search (data-model §18): the measure is the D4
    score's own, min(W_D, W_L) at the search width (R6), at one number of rounds for every
    candidate, fixed in that entry; ties go to the smallest amounts in the order that entry states;
    and an assignment ranks by its weakest box where the K sets make distinct boxes (R12). The space
    of amounts, K and the placement rule stay per candidate, recorded in its log entry with the
    width before its search. The search runs at the D4 width (R6): first at 16, the width R6 tries
    first, and again at 8, with the same recorded space, K and placement rule, under the same rule,
    as a new log entry, if R6's rule fixes the D4 width at 8, so that the scores at 8 use the
    amounts found at 8. The scaling rule to every other width is stated before it, and every scaled
    amount lies in 1 to w − 1 (R14). Its searches are trail searches on the candidate and count
    against its 48 h row, each instance capped at 8 h, and their bound records count only after the
    candidate's cross-checks on the first amounts of its space in tie order, which run
    first in that row (R7, R12); a space whose projection, with the row's
    other runs, does not fit the 48 h row is refused by the Budget guard (cli contract), so the
    search is inconclusive and the candidate `ineligible`, and a smaller space makes a new candidate
    within the stop rule. A point whose search reaches its cap has no bound and ranks below every
    point with both bounds, in the stated tie order among such points, and the full ranking records
    each point's bounds or `inconclusive`. If no point has both bounds at the search width, the
    candidate has no amounts there, so it is not scored at that width (R6). The amounts never change
    after a point's bound is seen. The full ranking is a committed record, and the amounts chosen
    are its first entry.
  - **Tables per size.** The frozen `phycoweb/constants_v3.py` holds one table per supported
    (n, w), and the script also writes each as JSON beside the vectors,
    `vectors/phyco-v3/constants_n<n>_w<w>.json`, frozen with them (data-model §11, §13).
    Feature 006 turns them into packages and the RTL selects one by its generics; the LFSR stays
    in the script. A size without a table cannot be built until one is generated by the same
    script.
  - **Where the constants live** (checklist A11): each food node holds its own constants, its
    column of the table, in a small ROM indexed by the round counter and, where the call types draw
    on distinct streams, by the call type that travels with the start signal (FR-025), so no data
    signal crosses the grid. Per supported size, the design document reports the number of food
    nodes, the ROM depth at each (R entries per call type, times the number of distinct constant
    streams), the word width and the total bits (R5). The core takes its clock as an input, on the
    device's clock network; clock generation belongs to feature 008's board wrapper (FR-025). Reset
    is synchronous and reaches the nodes through a registered fan-out tree whose latency is part of
    the reset sequence, and every zeroization trigger drives the same tree (FR-025). The round and
    phase counters are replicated, one copy at
    each food node or node, all started by that reset and running in lockstep, so no counter value
    crosses the grid (plan, Complexity Tracking). The LFSR exists only in the script; the
    hardware holds its output as a fixed table.
- **Stricter means**: the rule does not change once fixed; the refused list and the relations
  checked between constants may only grow, and a later addition to the list that matches makes each
  candidate it touches fail FR-023, never a change of the rule.
  - **How the LFSR is classed** (checklist C2): under feature-002 FR-007 as the spec re-decides
    it (D6), the LFSR is a published design method that yields a fixed table, not a standard
    PRNG in Π: no key, nonce or state enters it.
- **Rationale**: an LFSR is a stated rule that reproduces no published primitive's constants
  (D6). The script records which polynomials published designs use and refuses them. A ROM per
  food node keeps every data path local (Principle III; FR-018), where one central LFSR would
  need a grid-wide distribution tree; the cost model does not count the ROMs (R5).
- **Alternatives**: the digits of a mathematical constant (several published primitives use
  them); SHA-256 output (a value derived from a published primitive); a plain counter formula,
  which the re-decided rule allows by name (simpler, but successive constants differ in few
  bits); one central LFSR with a registered distribution tree (a grid-wide data path, to be
  justified like the output tree); a copy of the LFSR at each food node (local, but each copy
  must start at its own offset).

## R16. Records, storage and re-checks (FR-053, FR-061, FR-065; Edge Cases)

- **Decision**:
  - Every evidence record is JSON with the fields of security.md §17.2, the §11.6 items for
    statistical measurements, and the design-form disclaimer (FR-068), written by one module,
    `protocol/evidence.py`. Paths are under `reports/004-crypto-architecture-v3/`.
    Files committed there are limited to `.json`, `.jsonl`, `.md`, `.csv`, `.txt` and `.gz`: raw
    counts and p-values are JSON or gzip-compressed JSON, never `.npy`, and a solver's log is
    `.txt`, since `*.log` is ignored; `protocol/evidence.py` refuses any other suffix there (R18).
  - Records up to 10 MB, compressed with gzip, are committed. Larger outputs, such as full
    dependency matrices at 16×16 (about 32 MB per round and direction) and the synthetic sets of the
    bias test's validation (8,601,600 counts, about 60 MB as text; R3, R4), stay local, under
    `data/local/004/<record_id>/` and never under `reports/004-crypto-architecture-v3/`:
    `.gitignore` gains `data/local/` (R18), and each record's `outputs` gives their paths with
    `committed` false. `protocol/evidence.py` refuses a committed output above 10 MB, naming it; a
    test fails if any path under `data/local/` is tracked or a committed output exceeds 10 MB, and
    `git add` refuses an ignored path without `-f`, so a local-only output is not staged by
    accident. Their SHA-256 and the regenerating command are committed, together with per-round
    summaries. A local-only output must come from a deterministic command, so that its committed
    SHA-256 can be checked by regenerating it, and the record states that command's cost (heavy or
    not, hours projected). An output that is not deterministic, such as a solver log with timings,
    is never local-only: it is committed, compressed, or its verdict rests on a committed
    deterministic summary.
  - **Compressed files.** Every `.gz` file is written by `gzip.compress(data, compresslevel=9,
    mtime=0)`, so its header holds no file name and a zero time; on the probe of 2026-11-01 the two
    environments of R1 then wrote identical bytes. Its raw hash is over the compressed bytes, and
    its record also holds the SHA-256 of the uncompressed content, which a reproduction compares,
    since another zlib may compress differently; a `p_values` file is compared by its values
    instead, its `uncompressed_sha256` reported only (data-model §1). A test checks the header of
    every committed `.gz` file under this feature's paths, `reports/004-crypto-architecture-v3/`,
    `research/004/`, `vectors/phyco-v3/` and `baseline/phyco-v2/`; feature 003's 1,000 tracked `.gz`
    files, listed with their hashes in its `SHA256SUMS`, hold a file name and a nonzero time, are
    outside its scope and stay unchanged.
  - **Hashes.** Each hash is recorded beside its kind, `raw` or `lf-normalized`. Every new file
    is hashed over its raw bytes and is pinned to LF or `binary` (R18), so its raw and
    normalized content agree on every checkout. An existing `text=auto` file is hashed over its
    LF-normalized content. The CRLF-pinned freeze records of features 002 and 003 keep their
    recorded hashes over CRLF bytes.
    Every digest is written as 64 lower-case hex digits. `lf-normalized` means each CR LF pair
    replaced by LF on the file's bytes, as Git normalizes, with a lone CR kept; it is never computed
    from a file read in text mode, whose universal newlines also turn a lone CR into LF.
  - **Spec and research versions.** The first time a record cites a spec hash,
    `protocol/evidence.py` stores a copy of that spec as
    `reports/004-crypto-architecture-v3/spec-versions/<sha256>.md`,
    committed with the records, so every `spec_sha256` names content that is kept, whether or
    not a commit holds it (data-model §1). Every version of research.md that a record cites by
    `research_sha256` is kept the same way, as `research-versions/<sha256>.md`, since the values
    that decide verdicts live there. Every record also holds `protocol_seq` and
    `protocol_line_sha256`, the protocol change log's last entry when the run started (`none` before
    the log exists).
  - **Code at HEAD.** A run that writes evidence exits 2 unless every source file in its
    `code_sha256` matches HEAD, committed and unmodified, which constitution 1.3.0's standing
    authorization to commit makes routine. Data and report files may still be dirty, and the record
    lists the dirty paths; a binary is rebuilt from committed source, its hash reported only. Each
    record's code is then found at its `git_head`, and a test checks each `code_sha256` entry
    against the blob at that commit.
  - **Fixed-name files.** The files kept under a fixed name, `candidates/<id>/round-rule.json`,
    `security-target/parameters.json` and `limits.json`, the environment
    records, `downloads.json` and `review-package/MANIFEST.json`, are the stated exceptions to
    "never overwritten" (data-model introduction): before one changes, `protocol/evidence.py` keeps
    its current content as `<dir>/versions/<sha256>.json` beside it, and the new content holds
    `previous_sha256`. A record that cites one gives its path and SHA-256, and the re-check resolves
    either from the versions. The selection records are not among them: each is written once, and a
    later selection is a new record, `freeze/selection-<k>.json` (data-model §9).
  - **Reproduction.** Every script that writes evidence or generated files has a mode
    `--reproduce RECORD`, which runs the recorded command's configuration with its output directory
    replaced by `reproductions/<record_id>/<n>/` and writes a `reproduction` record there: the
    original's ID and SHA-256, each compared field with its outcome, the reported fields, and
    `match` or `differs`. It appends nothing to the candidate log, charges no candidate's budget row
    and is not a re-run under R7, so it can neither replace evidence nor add any; it is
    a heavy run where R7 says so, run only on the owner's request, quoted
    with its date in its record, and charged to R7's feature-wide row, and a
    difference is a finding, exit 1: the original stands, a difference in a field
    that enters a verdict blocks the candidate's eligibility, `blocked`, until it is resolved, as a
    tool defect of R7 where it arises in the environment that made the original, whose one re-run is
    new evidence in the original's row, and a difference in a field that decides no verdict, such as
    a p-value, is reported and blocks nothing. It compares the fields data-model §1 lists for
    its kind and reports every other field only, timings and raw solver logs among them; a different
    source hash makes it a new run, not a reproduction. A `p_values` file is compared by its values,
    within the tolerance data-model §1 defines, and decides nothing; every other `.gz` file is
    compared by its `uncompressed_sha256`. Its verdict is recomputed under the spec version, the
    research version and the protocol change-log entry the original cites
    (`spec-versions/<sha256>.md`, `research-versions/<sha256>.md`), so a later change cannot alter
    it. The tests of User Story 4 and FR-061, and the full re-runs below, call `--reproduce`.
  - `scripts/recheck_004.py` recomputes every verdict from the saved outputs and compares it with
    the recorded verdict (FR-065, SC-017). Every verdict is recomputable on a fresh clone from
    committed files, so the committed per-round summaries must suffice, for example R_f from the
    per-round flag "every output bit depends on every input bit". Local-only outputs serve only
    to re-derive a committed summary, which `recheck_004.py` also does when they are present;
    it lists both checks per kind. This re-check is the routine test of User Story 4. It recomputes
    each verdict under the rules in force at the protocol change-log entry its record cites and,
    where a later stricter change applies (FR-044), also under the current rules, listing both; a
    disagreement in either is reported. It is exempt from the environment guard of R1: it recomputes
    verdicts from committed counts by exact integer arithmetic (data-model §5) and imports only the
    standard library and those `protocol/` modules that do the same, which a test checks. Its
    `recheck` record holds the interpreter, platform and full `pip freeze` it ran with, and says
    when that environment is not one of R1's; a reproduction that re-runs evidence stays in R1's two
    environments. Full re-runs are reproductions (above), listed per kind with their cost: the light
    kinds of R7 always, a heavy kind only on the owner's request, one at a time, as a heavy run
    charged to R7's feature-wide row (FR-045).
  - Heavy runs take an exclusive lock, `data/heavy-run.lock`, which `.gitignore` gains, and
    refuse to start while another process holds it (FR-045).
  - **Writers of the hash-chained logs** (checklist D4): `research/004/candidates.jsonl`,
    `provenance.jsonl` and the protocol change log `research/004/protocol-changes.jsonl` are
    chained, each line holding the SHA-256 of the previous line's UTF-8 bytes as stored, its final
    LF included (data-model §3, §14 and §18). Every append takes a second lock,
    `data/log-append.lock`, by exclusive create, which `.gitignore` also gains. Holding it, the
    writer checks the chain up to the last line, appends one line chained to it and releases the
    lock. A writer that cannot take the lock within 10 s, or finds the chain broken, exits 2 and
    appends nothing, so two scripts never chain to the same last line.
  - **Stale locks.** Both locks hold the PID and that process's start time, the environment
    (`windows` or `wsl`), the host, the command and the time the lock was taken. A script that finds
    a lock exits 2, naming the lock and whether its holder still runs, checked in the lock's
    environment. Only `scripts/clear_lock.py LOCK`, run by the owner or at the owner's request,
    removes one, and only when no process with that PID and start time runs; it writes a
    `lock-cleared` record under `reports/004-crypto-architecture-v3/locks/` with the lock's content.
    A heavy run that died holding the lock then gets the `inconclusive` record that every started
    run writes (data-model §1).
  - **Protocol change log.** Each change of a pre-registered rule is one entry: the date, the
    rule, the old and new text, the reason, the direction, `stricter` in the rule's stated direction
    or `settled`, which fixes a case the protocol leaves open, only before any result
    it affects exists, with the owner's approval, and never looser than any reading of the existing
    text; the readings compared for a settled case; the approver, with the confirmation of the
    approval step, the last record ID that existed before it, so that "before any result it affects"
    can be checked, and the results known at the time (FR-044). Approving an entry is the owner's
    own act, which the agent never performs: the writer's approval step prints the SHA-256 of the
    entry, or of the first entries together when the log is created, and appends nothing unless
    standard input is an interactive terminal and the owner types its first 16 hex digits; the entry
    records that confirmation (data-model §18). The spec's Clarifications point to it.
  - **A broken chain** is repaired only with the owner's go-ahead, recorded as a row "Log
    repair <n>" of the spec's Review & Approval table that names the log, the `seq` of the break and
    the date, reads Approved and is committed; `repair_log.py --approval` names that row, and the
    script exits 2 unless the row reads Approved at HEAD and names the same log and position. The
    broken file is kept unchanged with its SHA-256; `scripts/repair_log.py` writes a `repair` entry
    with the break's position, its cause and what was restored. Entries after the break count only
    where the records they cite corroborate them, and the final report states the repair.
  - **The design freeze** (FR-043) runs in five steps: (1) the owner commits the feature files;
    (2) `design_freeze.py create` runs with `git_dirty` false and writes the record as `draft`;
    (3) the owner runs `design_freeze.py approve`, which prints `draft_sha256`, refuses unless
    standard input is an interactive terminal and the owner types its first 16 hex digits, writes
    the approval with that confirmation into it and changes nothing else (data-model §13); (4) the
    owner commits the record; (5) `validate`, which
    recomputes `draft_sha256` and every hash, exits 0. Dirty means a tracked file modified or an
    untracked file not ignored. Ignored files, the locks and the local-only outputs, do not count,
    and local-only outputs are in the record by SHA-256 anyway. Steps (1), (3) and (4) are the
    owner's own acts, which the agent never performs (spec FR-043).
- **Rationale**: the edge case on large records leaves the choice to the plan. 10 MB keeps the
  repository small; hashes keep every local record checkable.
- **Alternatives**: commit everything (hundreds of MB of matrices); keep only summaries (the
  verdicts could not be re-checked); serializing only heavy runs (a light script appending during
  a heavy run could break a chain).

## R17. The model, the second transcription and the tests (FR-035, FR-057, FR-058)

- **Decision**:
  - `phycoweb/model_v3.py` imports only the standard library, `phycoweb/constants_v3.py` and
    `phycoweb/selftest_v3.py`, the two data modules the generators write (data-model §11). It is
    integer-only and branch-free on data. It is marked model-only, RTL-pending, with model ID
    `phyco-v3` and the variant IDs of R14. A test parses it with
    `ast.parse(source, feature_version=(3, 8))`, a best-effort check of the constitution's
    Python 3.8+. The import test bans `time`, `random`, `os`, `sys`, `platform` and `secrets` in
    the model, as it bans numpy; the generators read the clock and the platform only for the
    sidecar record of R8, never for content.
  - **Python versions** (FR-035): the model supports Python 3.10 and 3.14, the two tested; 3.8,
    3.9 and 3.11 to 3.13 are "expected, not tested", since the model uses only the standard
    library and passes the 3.8 grammar check. The analysis tools need 3.10 or later and are
    tested on 3.10.11 and 3.14.4; the markers of `requirements.txt` start at 3.10, and a comment
    there says that the analysis tools need 3.10 or later and that the model alone needs only the
    standard library, so that "expected, not tested" on 3.8 and 3.9 concerns the model only, and
    that the markers admit 3.11 to 3.13 untested (R18).
  - The second transcription is `tests/v3_reference.py`, written from the design document alone in
    a separate session. That session starts only after the owner's recorded go-ahead. A person
    may write it, or a fresh agent session that the owner starts or authorizes; the provenance
    records name the session of each file (FR-057, FR-067). `tests/test_v3_transcription.py`
    compares the two step by step on every committed vector.
  - Tests use `unittest`, as in features 001–003: `python -W ignore -m unittest discover -s tests
    -t .`. The new tests cover FR-058's list, with property-based tests in Hypothesis 6.168.5,
    the last release that supports Python 3.10, whose download the owner approved on 2026-11-01
    (R19). If it cannot be obtained, its absence is an open item (FR-058). Hypothesis runs under
    a settings profile that the test package registers with `derandomize=True` and
    `database=None`, so every run tries the same examples and a failure replays by running
    again.
- **Rationale**: the precedent of `tests/v2_reference.py`. A separate session is what makes the
  check more than a re-reading of one's own code, and the common-mode caveat stays with the
  result.
- **Alternatives**: pytest (not installed; a download).

## R18. Repository hygiene (FR-042, FR-053, FR-068, FR-069)

- **Decision**:
  - `baseline/phyco-v2/` receives byte-exact copies of `phycoweb/model_v2.py`, `phycoweb/lut.py`,
    `fast/phyco_stream.c`, `fast/lut_table.h`, `specs/002-core-dynamics-redesign/design.md` and
    both `vectors/phyco-v2_*.hex`, with `MANIFEST.json` holding each file's SHA-256, source path
    and `git_head`. A new `scripts/archive_phyco_v2.py` writes it; the feature-001 script is left
    unchanged. `baseline/** -text` already keeps the copies byte-exact, except the two vector
    copies, which the later `*.hex text eol=lf` line governs, as `git check-attr` showed on
    2026-11-01; that is harmless while their sources stay LF, as they are.
  - `.gitattributes` gains `text eol=lf` for every Markdown file under
    `specs/004-crypto-architecture-v3/`, the spec among them, since every record holds the spec's
    SHA-256 (data-model §1), and for `vectors/phyco-v3/**`. Every file under
    `reports/004-crypto-architecture-v3/` and `research/004/`, and `protocol/*.json`, is pinned
    already (below): the provenance log, `protocol/claims.json`, the candidate log and the protocol
    change log, `research/004/tools/critical_counts.json`,
    `research/004/candidates/superseded.json`, each candidate's committed reference outputs and the
    self-written known results among them.
  - `.gitattributes` holds `reports/004-crypto-architecture-v3/** text eol=lf`, which covers
    solver logs, CSV and text outputs, followed by `*.gz binary`, so that compressed records are
    never treated as text. Files committed there are limited to `.json`, `.jsonl`, `.md`, `.csv`,
    `.txt` and `.gz` (R16), so the rule never makes a binary file text: a solver's log is `.txt`,
    since `*.log` is ignored, and `protocol/evidence.py` refuses any other suffix. Later lines take
    precedence, and `*.bin binary` already follows it. Both lines were added when the checklist
    choices were applied (2026-11-01); the 1,000 tracked `.gz` files of feature 003 were already
    stored as binary, so none changes, and R16's header test leaves them out.
    `research/004/** text eol=lf` and `protocol/*.json text eol=lf` follow the reports line, before
    the `*.hex`, `*.bin` and `*.gz` lines, so that those keep precedence; they were added when the
    second re-run's choices were applied (2026-11-01), while neither path held a file.
  - **Hashes and pins.** A new record or the review package hashes an existing `text=auto` file
    over its LF-normalized content and says so (`lf-normalized`, R16), so the hash is the same
    on every checkout, and no existing file's pin changes. A test lists every path whose hash a
    committed record, manifest or freeze record holds, and checks with `git check-attr text eol`
    that each has an explicit rule or `binary`, or that its record marks the hash
    `lf-normalized`; it also looks for a byte-order mark. It replaces the one-off check noted in
    `.gitattributes` on 2026-10-31, and it runs from plan phase 1 on, so that a path missed later
    fails it as soon as the first record that cites it is committed.
  - **Encoding.** Every new text file is UTF-8 without a byte-order mark. Scripts write with
    `encoding="utf-8"` and `newline="\n"`, and no hashed file is written by Windows PowerShell
    5.1, whose `Out-File -Encoding utf8` adds a byte-order mark.
  - `.gitattributes` also gains `*.mk text eol=lf` and `Makefile text eol=lf`, which cover the new
    `fast/seed_search.mk` and keep feature 003's `fast/Makefile` LF on a fresh checkout. Its bytes
    do not change: Git already holds it with LF line endings (checklist F12).
  - `.gitignore` gains, at setup (plan phase 1), the two locks of R16, `data/heavy-run.lock` and
    `data/log-append.lock`, and `data/local/`, where local-only outputs are written (R16), so that
    none of them shows in `git status` or counts as dirty.
  - `requirements.txt` loses its stale header and pins the two tested environments with markers:
    `numpy==2.2.6; python_version >= "3.10" and python_version < "3.14"`,
    `numpy==2.5.4; python_version >= "3.14"`, the same for scipy (1.15.3 and 1.18.1), and
    `nistrng==1.2.3` in both. With Hypothesis approved (R19), it adds `hypothesis==6.168.5`,
    `sortedcontainers==2.4.0` and `exceptiongroup==1.3.1; python_version < "3.11"`. A comment in the
    file says that the analysis tools need Python 3.10 or later and that the model alone needs only
    the standard library (R17), so FR-035's "expected, not tested" on older versions concerns the
    model only, and that its markers admit Python 3.11 to 3.13 untested. A new environment record is
    written only when the environment matches these pins, and `protocol/evidence.py` checks at start
    against that record as a whole (R1).
  - `protocol/disclaimer.py` gains `DESIGN_DISCLAIMER`, holding exactly the design-form
    disclaimer, the block directly under the spec's title, as at the top of this document;
    `DISCLAIMER` stays unchanged. The claim test compares every document's copy with the
    constant. No freeze of features 002 or 003 pins this file.
  - The claim and evidence register is `protocol/claims.json`. `tests/test_claims.py` runs FR-069's
    test as written, with its scope, rules, strength rule and allow-list: it checks README,
    security.md §1.1 and §15, and the disclaimers against the register, and scans every document of
    this feature, that is every Markdown file under `specs/004-crypto-architecture-v3/` and
    `reports/004-crypto-architecture-v3/`, the checklists and checklist-choices.md included, with
    README and security.md, and the comments and docstrings of the files FR-069 names, for the
    wording FR-050 forbids, "random" with its inflections and "high-entropy" among it (Principle
    IV), and for FR-069's other rules. "Near" and "beside" in its rules mean the same sentence or
    table row, every rule matches whole words, ignoring case, with FR-069's inflections, and every
    flagged line, a rule's own line included, passes only through an allow-list entry with its
    reason (data-model §15). A test runs every rule and every standing phrase on sample sentences
    that must and must not be flagged, the mapping chapter's rule among them, with FR-030's list and
    the words it gives for the arguments FR-030 forbids; the chapter is the design document's
    section headed "Slime-mould mapping", up to the next heading of the same level, and the test
    exits 1 if the heading is missing or appears twice.
- **Rationale**: these are the spec's named fixes (checklist groups E and F). Markers keep one
  file correct for both environments.
- **Alternatives**: two requirements files (more drift).

## R19. Downloads, approved by the owner on 2026-11-01 (FR-046)

On 2026-11-01 the owner approved every file in the two tables below, each as listed with its
source, size and licence ("Tool acquisition" in the spec's Review & Approval table). Nothing
else is covered: a file not listed here, the tools under "Not requested", or a file whose source
or licence differs from its row, or whose size differs from a size given in bytes, needs its
own permission. A tool's second known result (R12) comes from these papers
where one of its kind is there, fixed before the tool's first validation, so
that no paper is requested after a failed validation to supply one. Each
file is fetched when the task that uses it is reached. Nothing in this plan
depends on any of them; without them the work uses the tools of R12 and records each gap as an
open item. The requests below were prepared on 2026-11-01 from the hosts' pages and from header
requests, with no file body downloaded. A size comes from the server's header where it gave one,
and otherwise as the host lists it. The IACR ePrint archive, the IACR conference archive and the
ToSC journal site refused scripted requests (HTTP 403 or a bot check), and nothing was done to
get around that: for those papers the table names a copy elsewhere, or the owner downloads the
file in a browser into a new folder and gives its path.

**Papers.** Each is read and cited, kept locally with its SHA-256 and never committed, so its
licence does not touch the project's GPL-3.0.

| File | Source | Size | Licence | Use | Without it |
|------|--------|------|---------|-----|-----------------|
| `Daemen.pdf`: Daemen, Mennink and Van Assche, "Full-State Keyed Duplex With Built-In Multi-User Support", ASIACRYPT 2017 | https://ir.cwi.nl/pub/27254/Daemen.pdf (CWI repository, final version) | 604 kB, as CWI lists it | none stated by CWI; the ePrint version, 2017/498, is CC BY 4.0 | the mode theorem (R10) | the mode chapter stays "unverified"; L1 cannot be recorded |
| `SpongePRNG.pdf`: Bertoni, Daemen, Peeters and Van Assche, "Sponge-Based Pseudo-Random Number Generators", CHES 2010 | https://keccak.team/files/SpongePRNG.pdf | 238,714 bytes | none stated (authors' copy) | forget (R10) | as above |
| `169.pdf`: Gaži and Tessaro, "Provably Robust Sponge-Based PRNGs and KDFs", EUROCRYPT 2016 | https://eprint.iacr.org/2016/169.pdf; refused scripted requests, so the owner's browser | not given | CC BY 4.0 | forget (R10) | as above |
| `automatic-search-arx-trails.pdf`: Biryukov and Velichkov, "Automatic Search for Differential Trails in ARX Ciphers", CT-RSA 2014 | https://orbilu.uni.lu/bitstream/10993/17183/1/automatic-search-arx-trails.pdf (author postprint) | about 383 kB, as ORBilu lists it | none stated; the extended ePrint version, 2013/853, is CC BY 4.0 | SPECK32 differential trails (R12) | the owner provides the values with their source, or the tool stays unvalidated |
| `2657`, a PDF: Liu, Wang and Rijmen, "Automatic Search of Linear Trails in ARX with Applications to SPECK and Chaskey", ACNS 2016 | https://www.esat.kuleuven.be/cosic/publications/article-2657.pdf, redirected to the COSIC database | 458,069 bytes | none stated (COSIC copy) | SPECK32 linear trails (R12) | as above |
| `47270450.pdf`: Bogdanov et al., "PRESENT: An Ultra-Lightweight Block Cipher", CHES 2007 | https://www.iacr.org/archive/ches2007/47270450/47270450.pdf; refused scripted requests, so the owner's browser | not given | © IACR; no open licence stated | PRESENT's 5-round bound and S-box tables (R12) | as above |
| `main.pdf`: Beierle et al., "Lightweight AEAD and Hashing using the Sparkle Permutation Family", ToSC 2020(S1) | https://orbilu.uni.lu/bitstream/10993/41993/1/main.pdf (author preprint) | 1.02 MB, as ORBilu lists it | none stated on the record | the SPARKLE long-trail bound (R12) | as above |
| `AIS_31_Functionality_classes_for_random_number_generators_e_2024.pdf`: BSI, "A proposal for: Functionality classes for random number generators", version 3.0, 17 September 2024 | https://www.bsi.bund.de/SharedDocs/Downloads/EN/BSI/Certification/Interpretations/AIS_31_Functionality_classes_for_random_number_generators_e_2024.pdf?__blob=publicationFile&v=3 | 6 MB, as BSI lists it | © BSI, under BSI's terms of use | D8's functionality class | the class stays unconfirmed, as an open item |

**Software.** Installed from the downloaded files into the two existing environments. The
licences allow use in a GPL-3.0 project, and nothing here is committed or distributed. Each
file's SHA-256 is checked against PyPI's after download and recorded.

| File | Source | Size | Licence | Use | Without it |
|------|--------|------|---------|-----|-----------------|
| `hypothesis-6.168.5-cp310-abi3-win_amd64.whl` | PyPI | 684,616 bytes | MPL-2.0 | property tests (FR-058) on Windows; 6.168.5 is the last release for Python 3.10 | an open item (FR-058) |
| `hypothesis-6.168.5-cp310-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl` | PyPI | 1,157,262 bytes | MPL-2.0 | the same in WSL (Python 3.14) | as above |
| `sortedcontainers-2.4.0-py2.py3-none-any.whl` | PyPI | 29,575 bytes | Apache-2.0 | a Hypothesis dependency, both environments | as above |
| `exceptiongroup-1.3.1-py3-none-any.whl` | PyPI | 16,740 bytes | MIT | a Hypothesis dependency, Windows only (Python < 3.11) | as above |

**Not requested.** A SAT solver with PySAT (CaDiCaL or Kissat), Z3, OR-Tools CP-SAT, SCIP,
CryptoSMT and CASCADA. HiGHS in scipy and the self-written searches cover every validation
target of R12, a further tool would need its own validation, and the tool set is fixed when the
first trail search starts (R12). For a SAT cross-check before then, the files would be
`python_sat-1.9.dev17-cp310-cp310-win_amd64.whl` (1,924,781 bytes) and
`python_sat-1.9.dev17-cp314-cp314-manylinux_2_24_x86_64.manylinux_2_28_x86_64.whl`
(4,063,894 bytes), MIT, with their dependency `six`.

Every downloaded file is treated as untrusted: it goes into its own new directory, it is never
run from inside that directory, Python reading it runs with `-I`, and its SHA-256 and size are
recorded against its row.

A committed downloads manifest, `reports/004-crypto-architecture-v3/downloads.json`, holds from
setup on one entry per file of these tables, each with its name, source, size and licence and a
`status`: `approved`, not yet fetched, with no SHA-256, date or path; `fetched`, with its SHA-256,
download date and local path; or `not obtained`, with the reason. A value the owner provides gets an
entry of its own, `owner-provided`, with the owner's words, the source the owner names, the date and
the value's SHA-256, written by `scripts/owner_record.py owner-provided`, which the owner runs, an
owner's own act (spec FR-044): the script prints the entry's SHA-256 and writes nothing unless
standard input is an interactive terminal and the owner types its first 16 hex digits, and the entry
keeps `approved_by`, `approved_utc` and `approval_confirmed`. The owner then sets its Review &
Approval row, "Owner-provided value <n>", to Approved and commits it, and `validate_tool.py`'s
source guard accepts the entry only while that row reads Approved at HEAD. The
manifest keeps its fixed name: before it changes, its current content is
kept as `versions/<sha256>.json` beside it (R16). A validation record's `source` cites the manifest
entry: a `fetched` file's, with the paper's table and value, or an `owner-provided` one (data-model
§7). If a paper's value cannot be obtained, the tool it validates stays unvalidated and its results
`not evaluated` (R12); the owner may provide the value with its source, as an `owner-provided`
entry.
