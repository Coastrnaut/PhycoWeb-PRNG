<!--
Sync Impact Report
==================
Version change: 1.0.0 → 1.1.0
Bump rationale: MINOR. User-supplied constitution text merged in: four principles and three
sections added, three principles materially expanded. No principle removed or redefined
incompatibly, and Principles I–V keep their numbers so existing spec references stay valid.

Modified principles:
  - I. Integer-Domain, Multiplierless Arithmetic
      → I. Integer-Domain, Fully Specified Arithmetic (adds: every width, signedness, shift,
        overflow, truncation, comparison and update order must be defined)
  - II. Bit-Accurate Reference Model Parity
      → II. Bit-Accurate Reference Model & Differential Testing (adds: reproducible model tests
        and Python/VHDL differential tests)
  - IV. Evidence-Based Randomness Claims
      → IV. Evidence-Based Claims (adds: statistical success ≠ cryptographic security; no
        suppressed failures or weakened acceptance criteria)
  - V. Reproducibility & Determinism
      → V. Reproducibility, Archival & Provenance (adds: preserve archived variants with
        SHA-256; record commands, tool versions, outputs, limitations, assumptions)
  - III. Synchronous, Localized, Vendor-Neutral RTL: unchanged

Added principles:
  - VI. Specification Before Implementation
  - VII. Requirements Traceability
  - VIII. Human Review Gates
  - IX. Explicit Authorization for Outward Actions

Added sections:
  - Mission
  - Security Policy
  - Phase Completion Reporting

Removed sections: none

Templates requiring updates:
  - .specify/templates/plan-template.md: ✅ no edit needed (its Constitution Check reads this
    file at runtime; plans must now check Principles I–IX)
  - .specify/templates/spec-template.md, tasks-template.md: ✅ no edit needed

Impact on existing feature specs/001-integer-lut-perturbation/spec.md (not edited here):
  - VIII: the spec is an algorithm change and needs a recorded human review before
    implementation.
  - V: the floating-point variant (readmee.md listing, plus the deleted MycoPRNG.py,
    nist_bench.py, nistrng_bench.py, phycoweb_nist_eval.py still in git history) must be
    archived with SHA-256 hashes. This conflicts with the spec assumption "previously deleted
    script files are not restored".
  - I: the spec must state how table values are produced (truncation toward zero vs rounding),
    the signedness of the saturation comparison (D > 4096), and the exact step/phase update
    order.
  - VII: tasks must reference FR/SC identifiers.

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
- PhycoWeb-PRNG MUST NOT be recommended or used for secret generation unless it has both
  (a) a documented, defensible design rationale and (b) independent expert cryptographic review,
  with both recorded in the repository.
- Documentation MUST state this restriction wherever usage of the generator is described.

## Development Workflow & Quality Gates

- Features follow the Spec Kit flow: specify → (clarify) → human review → plan → tasks →
  implement. Each plan MUST include a Constitution Check against Principles I–IX.
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

**Version**: 1.1.0 | **Ratified**: 2026-10-28 | **Last Amended**: 2026-10-28
