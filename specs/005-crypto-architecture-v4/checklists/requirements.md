# Specification Quality Checklist: Cryptographic Architecture, Second Design Round (phyco-v4)

> This feature makes no security claim. No PhycoWeb-PRNG model, `phyco-v4` included, may be used
> to generate secrets; use an established cryptographic random-number generator for keys,
> nonces, tokens and salts. Passing statistical tests does not show cryptographic security.

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-11-09
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

- Validated by the agent on 2026-11-09, in two passes, each item checked against the spec's text.
  The first pass failed four items, and the spec was changed for each before the second:
  - "Written for non-technical stakeholders": a plain-language paragraph, "In short", now opens
    the Context. The rest of the spec keeps the protocol's own terms (R_bound, trail, 2⁻¹²⁸), which
    feature 004's spec defines and FR-001 inherits; the readers are the owner and the reviewers.
  - "Scope is clearly bounded": an "Out of scope" paragraph now lists what feature 004 also left
    out (RTL, FUT-SEC-7's held-out programme, the full cryptanalysis campaign, L5's review,
    publication, any claim).
  - "Requirements are testable and unambiguous": FR-005 now says which bound searches the projection
    table lists (each reference design's, from r = 1 to the r its bounds are projected to pass
    2⁻¹²⁸, or R_max), and FR-006 how each cap follows from the table (at least the margin times the
    longest projected search of its size and kind).
  - "All functional requirements have clear acceptance criteria": SC-007 now covers FR-027's
    security.md and register changes.
- Evidence per item, second pass:
  - No implementation details: no requirement names a language, framework or API. The Assumptions
    name the machine of record (Python versions, WSL), inherited from feature 004's research R1, as
    an environment fact.
  - User value: the Context's "In short" and "Why a second round", and stories written for the
    owner and the reviewers.
  - Mandatory sections: User Scenarios & Testing, Requirements and Success Criteria are filled;
    Assumptions too.
  - No markers: none in the spec. The open choices are D1–D14, each with a default and an
    alternative, for the owner's decision at spec approval.
  - Testable: each FR names something checkable: a record, a row, a table, an order of commits, a
    recomputation. FR-022 and FR-025 inherit feature 004's requirements, which are as testable as
    they were there.
  - Measurable and technology-agnostic success criteria: SC-001 to SC-010 state percentages,
    orders, counts and ratios over records, rows, commits and documents.
  - Acceptance scenarios: five stories, with two or three scenarios each.
  - Edge cases: twelve, each with its handling.
  - Dependencies and assumptions: FR-001's table of baseline documents with their SHA-256, and the
    Assumptions section.
  - Acceptance criteria per FR: FR-004 to FR-009 through User Story 1, SC-001, SC-008 and SC-009;
    FR-010 to FR-013 through User Story 2 and SC-002; FR-014 to FR-021 through User Story 3 and
    SC-003 to SC-005; FR-022 to FR-024 through User Story 4 and SC-006; FR-025 through User Story 5
    and SC-010; FR-026 and FR-027 through SC-007; FR-028 through feature 004's derivation guard
    and its test; FR-029 through SC-009; FR-030 through the final report's table.
  - Primary flows: plan, security-target review, bound climbs, evidence with selection or a stop,
    then model, reviews and freeze.
- A last read-through after the second pass corrected four places, none changing an item's result:
  the edge case on a search beside a sum (a searched bound below a sum is no contradiction; a trail
  lighter than an established bound is), FR-009's wording on the calibration, FR-016's definition
  of W as a weight, and the line on B1 in the Context's table of changes.
- The claim test's wording rules (FR-069 of feature 004), applied by the agent to this spec, find
  only level names in rule statements (L1, L2, L5), the kind feature 004's claim register
  allow-lists; the claim test does not cover feature 005 until its plan extends it (FR-026).
- Items marked incomplete require spec updates before `/speckit-clarify` or `/speckit-plan`.
