<!--
Sync Impact Report
==================
Status: DRAFT for owner review, 2026-10-31. Not in force until the repository owner approves it
and authorizes the commit (Governance; Principle IX). Until then, version 1.1.0 applies.

Version change: 1.1.0 → 1.2.0
Bump rationale: MINOR. The Security Policy is materially expanded with binding rules. Every
change is stricter: no principle or section is removed or redefined, no existing requirement is
relaxed, and Principles I–IX keep their text and numbers.

Modified principles: none.

Modified sections:
  - Security Policy:
      - secret-generation use also needs (c): the security-strength requirements met;
      - adds the seed-entropy finding: phyco-v2 (design 1.0) and lut-v1 take a 64-bit seed, so
        any security level they have is at most 64 bits, below the 112-bit minimum;
      - adds rules: every new or changed model's specification states its bound; no strength
        above the bound may be stated; no cryptographic claim, evaluation or certification
        before FUT-SEC-1 to FUT-SEC-9 are met; meeting them is an algorithm change with a new
        model ID; cryptanalysis stays unrestricted; later amendments may only make the rules
        stricter;
      - adds requirements FUT-SEC-1 to FUT-SEC-9 from research/security/seed-entropy-bound.md
        §5, worded as MUST statements. FUT-SEC-9 also forbids describing any model as FIPS 140-3
        approved or as an SP 800-90A DRBG.
  - Development Workflow & Quality Gates: the Constitution Check also covers the Security
    Policy. The plans of features 001–003 already include that row.

Added sections: none (the new rules are part of the Security Policy).
Removed sections: none.

Templates requiring updates:
  - .specify/templates/plan-template.md: ✅ no edit needed (its Constitution Check reads this
    file at runtime)
  - .specify/templates/spec-template.md, tasks-template.md: ✅ no edit needed

Impact on existing artifacts (not edited here):
  - No result of features 001–003 changes, and no cryptographic claim exists, so no existing
    artifact violates the amendment.
  - specs/002-core-dynamics-redesign/design.md 1.0 does not state its bound and cannot be
    edited without changing its frozen hash. The bound rule applies to new or changed models;
    the research note records the bound for design 1.0 and lut-v1.
  - security.md §4 quotes the Security Policy "verbatim" and needs the amended text.
  - research/security/seed-entropy-bound.md (§5, §7) and security.md (§20.1, history) should
    record that FUT-SEC-1 to FUT-SEC-9 are binding from version 1.2.0.
  - Feature 003 (in progress): its plan was checked against 1.1.0. Its final report (T043)
    should cite 1.2.0 if the amendment is adopted first.

Follow-up TODOs: none deferred in this document.
-->

# PhycoWeb-PRNG Constitution

## Mission

Evaluate and verify PhycoWeb-PRNG as an experimental deterministic pseudo-random generator.
Its cryptographic suitability is unproven, and every project artifact MUST reflect that status
until the Security Policy below is satisfied.

## Core Principles

### I. Integer-Domain, Fully Specified Arithmetic (NON-NEGOTIABLE)

- All datapath arithmetic in the generator core MUST use bounded fixed-width integers
  (16-bit signed state, 32-bit output words unless a ratified spec says otherwise).
- IEEE-754 floating point, floating-point wrappers, and divider IP cores MUST NOT appear in the
  generator datapath, in either the reference model or the RTL.
- Fractional scaling MUST be expressed as explicit arithmetic bit-shifts (e.g., `>> 4`, `>> 8`).
  Shift steps MUST NOT be rewritten as variable multiplications or divisions.
- Every state element and operation MUST have its width, signedness, shift semantics
  (arithmetic vs logical), overflow behavior (wrap, saturate, mask), truncation/rounding rule,
  comparison semantics (signed vs unsigned), and update order defined in the specification.
  Behavior left implicit is a specification defect.
- Floating point is permitted only in offline analysis tooling (statistics, plotting, offline
  table generation whose integer output is committed) that never runs in the generator.

Rationale: the design's value is a zero-DSP, high-clock-rate FPGA core. Any non-integer,
multiplier, or under-specified path breaks synthesizability and model/RTL equivalence.

### II. Bit-Accurate Reference Model & Differential Testing

- The Python reference model is the golden model. It MUST mirror the RTL bit-for-bit: same
  widths, shift amounts, masking, update ordering, and disruption constants.
- The reference model MUST have reproducible automated tests, including committed golden output
  vectors for stated seeds.
- Where RTL exists, Python/VHDL differential tests MUST show identical output word sequences
  for the same seeds (minimum 10,000 words per seed).
- Every change to generator behavior MUST be made to the reference model and the RTL in the same
  change set, or be explicitly marked as model-only/RTL-pending in its spec.
- Any deliberate divergence MUST be documented, versioned, and accompanied by regenerated vectors.

Rationale: without exact parity, statistical results obtained in Python say nothing about the
hardware.

### III. Synchronous, Localized, Vendor-Neutral RTL

- All state, including the threshold supervisors ("Frustrated Foraging" monitors), MUST be
  registered on the system clock edge. Unbuffered combinational paths between adjacent channel
  structures MUST NOT be introduced.
- Node-to-node communication MUST be limited to direct grid neighbors; global broadcast signals
  across the grid MUST NOT be added without a documented timing justification.
- RTL MUST be behavioral and vendor-neutral (no vendor-specific primitives or block macros) and
  MUST synthesize with 0 DSP blocks.
- Designs SHOULD meet a ≥ 200 MHz target clock; any regression below target MUST be reported with
  the synthesis report that shows it.
- Grid size MUST be parameterizable (e.g., 2×2 through 16×16) without restructuring core logic.

Rationale: localized, registered logic is what lets the grid scale without timing bottlenecks
and keeps the core portable across Vivado, Quartus, and open toolchains.

### IV. Evidence-Based Claims

- No document, comment, or release note MAY describe the generator as "random",
  "high-entropy", or "cryptographically secure" beyond what committed evidence supports.
- Statistical-test success MUST NOT be presented as, or used to imply, cryptographic security.
- Statistical quality MUST be measured with the NIST SP 800-22 suite (via `nistrng` or an
  equivalent reference implementation) and SHOULD additionally use broader batteries
  (e.g., Dieharder, TestU01, PractRand).
- Test results MUST record seed, sample size, generator version/commit, and per-test p-values,
  and MUST be reproducible from the committed scripts.
- Failures MUST NOT be suppressed, and tests MUST NOT be selectively omitted, re-seeded until
  passing, or have acceptance criteria weakened to obtain a passing result. Any change to an
  acceptance criterion MUST be made in the spec, with justification, before the results are
  produced.

Rationale: novel PRNG designs commonly pass superficial tests while remaining predictable;
honesty about evidence protects downstream users.

### V. Reproducibility, Archival & Provenance

- For a given seed and configuration, the generator MUST produce an identical output sequence
  across runs, platforms, and supported Python versions.
- Every superseded algorithm variant MUST be preserved in an archive location (e.g.,
  `baseline/`) with its SHA-256 hash recorded in a committed inventory. Variants MUST NOT be
  discarded, even when replaced.
- Benchmarks, audits, and evaluations MUST be runnable from scripts in the repository with fixed
  seeds and pinned or documented dependency versions.
- Every evaluation and phase report MUST record the commands actually run, tool and dependency
  versions, raw or summarized test outputs, known limitations, and unresolved assumptions.
- Generated reports MUST be written to a dedicated output location (e.g., `reports/`) and MUST
  NOT overwrite source or baseline inputs.

Rationale: others can check parity (II) and claims (IV) only if results are reproducible and
their provenance is complete.

### VI. Specification Before Implementation

- Any algorithm, or change to an algorithm, MUST be specified (spec and plan approved) before it
  is implemented in the reference model or RTL.
- Code that implements behavior absent from an approved specification MUST NOT be merged.

Rationale: the specification, not the code, is the authority that model and RTL are checked
against.

### VII. Requirements Traceability

- Every task MUST reference the requirement(s) (FR/SC identifiers) it addresses.
- Every requirement MUST map to at least one task and to verification evidence (test, vector
  file, report, or review record) before the feature is declared complete.
- Requirements without verification evidence MUST be listed as open in the phase report.

Rationale: traceability shows that each claim of completeness is backed by evidence.

### VIII. Human Review Gates

- A human reviewer MUST approve, with the approval recorded, before:
  1. any change to generator algorithm behavior (spec approval and result review),
  2. the start of RTL development for a feature,
  3. any security- or randomness-quality claim is published.
- AI agents MUST stop and request review at these gates rather than proceeding on their own
  judgment.

Rationale: algorithm and security decisions in an experimental generator carry risk that
automated checks cannot assess.

### IX. Explicit Authorization for Outward Actions

- No contributor or agent MAY commit, push, publish, tag, or release without explicit
  authorization from the repository owner for that specific action.
- Authorization for one action does not extend to later or different actions.

Rationale: outward-facing actions are hard to reverse and must remain under the owner's control.

## Technical Constraints

- **Reference model & tooling**: Python 3.8+; `numpy` for integer arrays (explicit dtypes
  required, e.g., `np.int32`); `scipy` and `nistrng` for statistical analysis only.
- **Hardware**: synthesizable VHDL targeting standard FPGA toolchains (AMD/Xilinx Vivado,
  Intel Quartus Prime) with vendor-neutral behavioral code; simulation testbenches MUST be runnable
  with an open-source simulator (e.g., GHDL).
- **Resource targets**: 0 DSP blocks; registers/LUTs only; ≥ 200 MHz target clock.
- **Licensing**: all contributions are licensed under GPL-3.0; third-party code MUST be
  GPL-3.0-compatible.
- **Dependencies**: new runtime dependencies in the generator core require justification in the
  feature plan; analysis-only dependencies MUST NOT be imported by the core model.

## Security Policy

- Real secret generation (keys, nonces, tokens, salts) MUST use an established cryptographic
  random-number generator (e.g., the operating system CSPRNG or a NIST SP 800-90A DRBG).
- PhycoWeb-PRNG MUST NOT be recommended or used for secret generation unless it has all of
  (a) a documented, defensible design rationale, (b) independent expert cryptographic review,
  and (c) evidence that it meets the security-strength requirements below, with all three
  recorded in the repository.
- Documentation MUST state this restriction wherever usage of the generator is described.

**Security strength and seed entropy.** A deterministic generator's output is fixed by its seed
and its public algorithm, so no security level can exceed the seed's entropy, however large the
internal state. `phyco-v2` (design 1.0) and `lut-v1` take a seed of four 16-bit words, 64 bits in
total, so any security level they have is at most 64 bits. That is below the 112-bit minimum for
approved cryptographic use (NIST SP 800-57 Part 1 Rev. 5; SP 800-131A Rev. 2). The derivation is
in `research/security/seed-entropy-bound.md`.

- The specification of every new or changed generator model MUST state its seed or key entropy
  in bits, its secret state reachable from the seed, and the upper bound these place on any
  security level.
- No artifact MAY state or imply a security strength above a model's bound. A bound is a
  ceiling, not an achieved level: stating one, such as "at most 64 bits", reports a limitation
  and is not a claim.
- No cryptographic claim (a security property such as unpredictability or backtracking
  resistance, or a security strength in bits) MAY be made for any model, and no cryptographic
  evaluation or certification intended to support one MAY be pursued, until the model meets
  FUT-SEC-1 to FUT-SEC-9 below with the evidence recorded in the repository. The claim then
  still needs owner approval (Principle VIII, gate 3).
- Meeting FUT-SEC-1 to FUT-SEC-9 is an algorithm change. It needs an approved specification
  (Principle VI) and a new model ID, and that specification MUST carry FUT-SEC-1 to FUT-SEC-9
  as requirements traced to tasks and evidence (Principle VII).
- Cryptanalysis and attack demonstrations that look for weaknesses make no claim and are not
  restricted by this policy. Their results MUST be reported (Principle IV).
- Later amendments MAY make these requirements stricter and MUST NOT weaken them.

Requirements before any cryptographic claim, evaluation or certification:

- **FUT-SEC-1 Key entropy.** The generator MUST accept a key with at least 128 bits of entropy.
  No claimed strength MAY be below 112 bits, and no seed or key search or time–memory trade-off
  attack MAY cost less than the claimed strength.
- **FUT-SEC-2 Reachable secret state.** The secret state reachable through key and IV loading
  MUST be at least twice the claimed strength, in bits (time–memory–data trade-off).
- **FUT-SEC-3 Stream separation.** If one key may produce more than one stream, a nonce or IV
  with defined uniqueness rules MUST separate the streams.
- **FUT-SEC-4 Reseeding.** If prediction resistance is claimed, the generator MUST have a reseed
  input fed from a validated entropy source (SP 800-90B).
- **FUT-SEC-5 Initialization analysis.** Key and IV loading and the warm-up MUST be analysed for
  related-key, related-IV and weak-key behaviour.
- **FUT-SEC-6 Output limit.** The maximum output per key, and per key and IV, MUST be specified
  and covered by the analysis.
- **FUT-SEC-7 Re-validation.** The model MUST have a new model ID, golden vectors and a design
  freeze, and MUST be evaluated with the complete statistical programme on unused held-out seed
  sets. Results of earlier models do not carry over.
- **FUT-SEC-8 Demonstration first.** Before a redesigned key interface is implemented, the
  64-bit bound MUST be reproduced on a reduced seed domain (for example two seed words fixed,
  2³² candidates): the seed recovered from three output words, and the cost per candidate
  measured.
- **FUT-SEC-9 Certification route.** The target scheme MUST be named, for example independent
  academic cryptanalysis plus an AIS 20/31-style evaluation. No model MAY be described as
  FIPS 140-3 approved or as an SP 800-90A DRBG; deployments that need approved random numbers
  MUST use an approved DRBG (`security.md` §21, Option B).

Rationale: statistical results cannot lift a generator above its seed entropy, and a security
claim made before these conditions hold would mislead anyone who relies on it.

## Development Workflow & Quality Gates

- Features follow the Spec Kit flow: specify → (clarify) → human review → plan → tasks →
  implement. Each plan MUST include a Constitution Check against Principles I–IX and the
  Security Policy.
- A change to generator behavior is complete only when all of the following hold:
  1. Human review of the algorithm change recorded (Principle VIII).
  2. Superseded variant archived with SHA-256 hash (Principle V).
  3. Reference model updated and its tests pass.
  4. Model/RTL equivalence vectors regenerated and differential tests passing (Principle II), or
     the change is explicitly flagged RTL-pending.
  5. Statistical evaluation re-run with results committed (Principle IV).
  6. Synthesis resource/timing results recorded when RTL changes (Principle III).
  7. Traceability from requirements to tasks to evidence complete (Principle VII).
- Code review MUST verify: no floating point or multipliers in the datapath, fully specified
  arithmetic semantics, clocked supervisors, and that documentation claims match recorded
  evidence.
- AI coding agents operating in this repository are bound by this constitution exactly as human
  contributors are.

## Phase Completion Reporting

Every completed phase (spec, plan, tasks, implementation, evaluation) MUST end with a report
stating:

- files created or modified,
- requirements addressed (by identifier),
- tests actually run (exact commands) and their pass/fail results,
- open issues and unresolved assumptions,
- security concerns,
- a recommendation to **proceed**, **revise**, or **stop**.

A phase report MUST NOT claim a test passed unless it was run in that phase and its output
recorded.

## Governance

- This constitution supersedes conflicting guidance in other repository documents, including the
  README and agent bootstrapping directives.
- Amendments MUST be made via `/speckit-constitution` (or an equivalent edit), reviewed by the
  repository owner, and committed only with explicit authorization (Principle IX), stating the
  version change and rationale.
- Versioning follows semantic versioning: MAJOR for removing or redefining a principle in a
  backward-incompatible way; MINOR for adding a principle/section or materially expanding
  guidance; PATCH for clarifications and wording fixes.
- Compliance is reviewed at every plan's Constitution Check and at every pull request. Any
  violation MUST be either fixed or recorded with justification in the plan's Complexity Tracking
  section.
- Existing code or specs that predate an amendment and violate a principle MUST be tracked as
  follow-up items rather than silently grandfathered.

**Version**: 1.2.0 | **Ratified**: 2026-10-28 | **Last Amended**: 2026-10-31
