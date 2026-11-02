# Specification Quality Checklist: Cryptographic Architecture and phyco-v3 Design

> This feature makes no security claim. No PhycoWeb-PRNG model, `phyco-v3` included, may be used
> to generate secrets; use an established cryptographic random-number generator for keys,
> nonces, tokens and salts. Passing statistical tests does not show cryptographic security.

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-11-01
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Notes

- Iteration 1 (2026-11-01): all items pass. No [NEEDS CLARIFICATION] marker was needed: each of
  the nine owner decisions in strategy note §8.4 has a recommended option, which the spec adopts
  as defaults D1–D9 (section "Decisions Taken as Defaults") for `/speckit-clarify` or the spec
  approval to confirm or change.
- The Python reference model (Principle II, and named in the request), the existing C stream
  (the basis of the FUT-SEC-8 search tool, stated as an assumption), SHA-256 records, and
  `.gitattributes` and `requirements.txt` (repository files that checklist group F asks to fix)
  are fixed project conventions or the subject of the feature, so naming them is not treated as
  an implementation detail. No language, framework or code structure is chosen for new work,
  beyond the constraints that iteration 3 records.
- The stakeholders are the repository owner and cryptographic reviewers. The cryptographic
  vocabulary is the subject matter and is defined in security.md §3, §5 and §12.
- The request bundles seven scope items, hence, in iteration 1, 53 functional requirements in ten
  groups and five user stories in the request's order. Every security-relevant number (s = 128,
  key 256, nonce 128, c ≥ 256, Δ = 2, the bias threshold 0.005/S, the FUT-SEC-8 targets) is
  fixed in the spec, before any design result exists.
- Measurable checks done for iteration 1: every prose line is at most 100 characters; the file
  uses LF line endings only; FR-001 to FR-053 are numbered without gaps, and every FR cited in
  the tables exists.
- Iteration 2 (2026-11-01), after the update input "consider all text and items in
  crypto-redesign-strategy.md, security.md, seed-entropy-bound.md, and vhdl-genai.md": the spec
  was revised in place rather than split into a new feature. Every section and item of the four
  documents now has a requirement or a disposition (new section "Input coverage"). Added:
  FR-054 to FR-069 in three new groups (verification and translation readiness; findings,
  evidence and review; claims discipline), SC-016 to SC-020, decision D10 (which ideas of
  strategy note §10 are adopted), a tasks-approval row, five acceptance scenarios, six edge
  cases, five key entities and four assumptions. 23 existing requirements were sharpened, among
  them FR-004 (the target stated relative to a random permutation), FR-027 (explicit widths, no
  dependence on an integer range) and FR-038 (single-trail bounds only). All items still pass,
  and no [NEEDS CLARIFICATION] marker was needed.
- Naming `numeric_std`, VHDL-2008 and VHDL-2019 (constraints from security.md §13 and the
  hardware note), Hypothesis (an example, used only if its download is approved) and
  `tests/v2_reference.py` (the precedent for the second transcription) records project
  constraints and precedents, not a choice of implementation for new work.
- Measurable checks done for iteration 2: every prose line is at most 100 characters; LF line
  endings only, with no trailing spaces; FR-001 to FR-069 and SC-001 to SC-020 are numbered
  without gaps; every FR, SC and decision cited exists; the forbidden wording appears only in
  the rules that forbid it.
- Iteration 3 (2026-11-01), after the clarification of D1–D10, the plan and the owner's answers
  to both runs of checklist choices (235 rows, each answered with its recommended option): the
  spec now pre-registers how evidence is produced, recorded and reproduced, and how the
  reference model handles its key, and names what that needs. Among the names: the model's
  interface (`Generator`, `ResearchDuplex`, `CallSequenceError`) and the `bytearray` copy of the
  key that zeroization overwrites (FR-025); the modules the model's import test bans (FR-035);
  record formats and settings, such as `gzip.compress(data, compresslevel=9, mtime=0)` and the
  test with `git check-attr text eol` (FR-053), and `derandomize=True` and `database=None` for
  the property-based tests (FR-058); the paths, scripts and subcommands that write, lock and
  freeze records (FR-041, FR-043 to FR-045), and `scripts/repair_log.py --approval` in section
  "Review & Approval"; and VHDL's `unsigned(w − 1 downto 0)` (FR-027). SC-003, SC-007 and SC-009
  name the file, the field and the platform their checks read: `parameters.json`, `created_utc`
  and WSL.
- These names fix what a record holds, which settings make an output reproducible and where a
  check looks, all before any result exists; they choose no language, framework or code
  structure for new work beyond what a record cites or a test checks. They are therefore treated
  as pre-registered protocol, not as implementation detail. By the owner's decision of 2026-11-01
  the three items on implementation details ("No implementation details (languages, frameworks,
  APIs)", "Success criteria are technology-agnostic", "No implementation details leak into
  specification") are read this way and stay checked, and all 16 items pass.
- Measurable checks done for iteration 3: every prose line is at most 100 characters; LF line
  endings only, with no trailing spaces and no byte-order mark; FR-001 to FR-069 and SC-001 to
  SC-020 are each defined once, in order, and every FR, SC and decision D1–D10 cited exists; no
  [NEEDS CLARIFICATION] marker remains; "secure", "unbreakable" and "provably" appear only in
  the rules that forbid them (FR-030, FR-050, FR-069, SC-015), and every other "proven" names
  its object.
