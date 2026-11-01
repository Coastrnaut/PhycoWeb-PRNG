# CLI Contracts

> This feature makes no security claim. No PhycoWeb-PRNG model, `phyco-v3` included, may be used
> to generate secrets; use an established cryptographic random-number generator for keys,
> nonces, tokens and salts. Passing statistical tests does not show cryptographic security.

Exit codes, as in feature 003: **0** success; **1** completed with a failing or non-PASS verdict
(by design); **2** refused by a guard (wrong namespace, missing approval, budget exhausted, a
fourth candidate, lock held, hash mismatch, existing record), and nothing is written; **3** tool
or I/O error. `REP=reports/004-crypto-architecture-v3`. Every record is written through
`protocol/evidence.py` ([data-model.md](../data-model.md) §1).

## Guards shared by every script

- **Inputs**: only the namespaces `dev` and `control` of `protocol/devinputs_v3.py`, and for
  US1 the feature-002 `dev` set; anything else exits 2 (FR-040).
- **Heavy runs** (`seed_search` sweeps, exhaustive bijectivity, trail searches, the frequency and
  avalanche tests): take `data/heavy-run.lock` with an exclusive create; if it exists, exit 2.
  The lock holds the PID, command and start time and is removed on exit (FR-045).
- **Order of US1**: any script that loads a key into a `phyco-v3` state exits 2 unless the
  "FUT-SEC-8 result review" row of the spec's Review & Approval table reads Approved (FR-003);
  `tests/test_protocol_004.py` fails if `phycoweb/model_v3.py` defines key loading before that.
- **Tool validation**: a result of a tool without a `re-found` validation record of its kind is
  written with `status` `not evaluated` and never counts (FR-039).
- **Budget**: a script refuses work on a candidate whose budget row is spent (R7), exit 2, and a
  search that reaches its per-instance cap writes `inconclusive`.

## `fast/build/seed_search` (C, WSL; built by `make -C fast -f seed_search.mk`)

```text
seed_search --check-vectors FILE [FILE ...]
seed_search --s0 S0 --s1 S1 --words W1 W2 W3 [--threads 32] [--progress SECONDS]
```

- `--check-vectors`: regenerates every word of each `phyco-v2` vector file from the seed in its
  header and compares; exit 0 only if all 10,000 words of every file match, 1 otherwise.
- Sweep: S0 and S1 are integers 0…65535 and W1 to W3 32-bit hex words; anything else exits 2.
  For every (s₂, s₃) it runs the 256-step warm-up and compares the first output words, dropping
  a candidate at its first mismatch.
- Output: one JSON object on stdout with the counts after one, two and three words, every
  three-word match, total steps, seconds, steps per second and threads. Progress goes to stderr.

## `scripts/fut_sec8.py` (WSL)

```text
fut_sec8.py --binary fast/build/seed_search --out-dir $REP/fut-sec-8 [--repeat-after-defect ID]
```

Takes the targets from `protocol.seedsets.load("dev", allow=("dev",))[:3]`, computes the
observations with `phycoweb/model_v2.py`, runs the vector check, then one sweep per target,
separates any extra three-word match with the fourth word, and writes the demonstration record
(data model §4). A second run exits 2 unless `--repeat-after-defect` names a recorded tool
defect (spec Edge Cases). Exit 1 if a target is not recovered.

## `scripts/archive_phyco_v2.py`

```text
archive_phyco_v2.py [--check]
```

Copies the files of data model §12 byte for byte into `baseline/phyco-v2/` and writes
`MANIFEST.json`. Exits 2 if the archive exists and differs; `--check` exits 1 on any mismatch
between a copy, its manifest hash and its live source.

## `scripts/validate_tool.py`

```text
validate_tool.py --tool NAME --known KNOWN_ID --out-dir $REP/validation
```

Runs the tool on its known result (`s12`, `s13-decay`, `s13-transport`, `s14`, `s15`,
`fut-sec-8`, or a published value such as `speck32-diff`, `speck32-lin`, `present-5r`,
`sparkle-box`) and writes a validation record (data model §7). Exit 1 if not re-found. A
published value needs its source recorded (paper, table, value) or exits 2.

## `scripts/evidence_v3.py`

```text
evidence_v3.py --candidate ID --kind KIND [--size N] [--width W] [--rounds R] --out-dir DIR
```

KIND is `inverse`, `bijectivity`, `dependency`, `frequency`, `avalanche`, `control`,
`symmetry`, `invariant` or `bound` (with `--bound-kind differential|linear --method M`). The
candidate must be in the log; a `bound` needs a validated tool. Writes one record of data model
§5 or §6 and its raw outputs, and appends an `evidence` entry to the candidate log. The counts
are those of research R4 and R13 and cannot be lowered by an option.

## `scripts/d4_choice.py`

```text
d4_choice.py --log research/004/candidates.jsonl --out $REP/d4/choice.json
```

Computes the D4 choice of research R6 from saved bound records. Exits 2 if `choice.json`
exists or if no entered set is recorded.

## `scripts/round_rule.py`

```text
round_rule.py --candidate ID           # writes candidates/<ID>/round-rule.json
round_rule.py --select                 # writes $REP/freeze/selection.json
```

R = max(2·R_dist, R_bound + 2, 2·max(R_f, R_b)) per claimable size, every input cited by record
ID. `--select` applies eligibility, the fallback to the other family and the stop rule; exit 1 if
the outcome is a stop.

## `scripts/mode_limits_v3.py`

```text
mode_limits_v3.py --out $REP/security-target/limits.json
```

Evaluates the theorem's bound at the limits stated in the design document with ε = 2⁻⁶⁴ and
N = 2¹²⁸ (research R9), and the doubling check. Exit 1 if the bound exceeds ε at the limits;
`theorem` is `unverified` until its paper has been read.

## Generators of constants and vectors

```text
gen_constants_v3.py [--check]                    # writes phycoweb/constants_v3.py
gen_vectors_v3.py [--check] [--variant ID ...]   # writes vectors/phyco-v3/ (research R8)
gen_constructed_v3.py [--check]                  # writes the constructed-state vectors
```

Each writes LF files and records its command, the model's SHA-256, the measured speed and the
generation time. `--check` regenerates in memory and exits 1 on any byte difference. After the
freeze, writing over a frozen file exits 2.

## `scripts/design_freeze.py`

```text
design_freeze.py create                 # writes $REP/freeze/freeze.json with status draft
design_freeze.py validate               # recomputes every hash
```

`create` exits 2 if the owner design review row is not Approved, if the external review row is
neither done nor "not arranged", or if `git_dirty` is true. `validate` exits 1 on any hash
mismatch, and 2 while `status` is `draft`.

## `scripts/recheck_004.py`

```text
recheck_004.py [--kind KIND]
```

Recomputes every verdict of the feature from saved outputs (FR-065) and compares it with the
recorded one. Exit 1 on any disagreement, with each listed.

## `scripts/check_claims.py`

```text
check_claims.py
```

Checks README, security.md §1.1 and §15 and the disclaimers against `protocol/claims.json`, that
every hand-written document of this feature carries the design-form disclaimer, and that
forbidden wording (FR-050) appears only in the rules that forbid it. Exit 1 on any finding
(SC-018). `tests/test_claims.py` runs it.
