# Next Steps: Feature 004 and Experiment E1

Date: 2026-10-31.

**Status:** a proposal for owner review, drafted by the AI coding agent. Nothing here is approved
yet, and nothing here is a security claim. The reasoning for feature 004 is in the research note
[`research/security/crypto-redesign-strategy.md`](research/security/crypto-redesign-strategy.md)
(the strategy note). The argument for both tracks, and for how AI-drafted VHDL will be checked,
is set out as four assertion outlines in
[`research/assertion-outlines.md`](research/assertion-outlines.md). Experiment E1 (section 7) is
described in [`research/engagement/scrutiny-game.md`](research/engagement/scrutiny-game.md), and
the rules for AI-assisted VHDL in
[`research/hardware/vhdl-genai.md`](research/hardware/vhdl-genai.md) (the hardware note). The
policy is in [`security.md`](security.md) 2.9 and the
[constitution](.specify/memory/constitution.md) 1.2.0, which prevails.

> Passing statistical batteries does not show cryptographic security. This generator must not be
> used to generate secrets; use an established cryptographic random-number generator for keys,
> nonces, tokens and salts.

> **The Truth.** When faced with adversity, maintain composure to creatively improve stakeholder
> engagement of diverse ideas and perspectives in engineering and learning.

## 1. Before the first prompt

1. Finish feature 003: T035 (battery attempt 1, still running on 2026-10-31) and T036–T044,
   including the owner reviews ⛔ T038 and ⛔ T044.
2. Run `/speckit-converge` on feature 003. The agent runs it automatically at that point.
3. Decide the questions in section 3, or leave them to `/speckit-clarify`.
4. Optionally, amend the constitution (section 2).
5. Approve the strategy note and the security.md 2.7 to 2.9 changes.
6. Optionally, read Outline A of the assertion outlines: it is the argument feature 004 starts to
   make, as a plan rather than a claim.

## 2. Optional: constitution amendment (`/speckit-constitution`)

From strategy note §9.1:

```text
Amend the constitution for the cryptographic redesign. MINOR: add a review gate to Principle VIII:
before the design freeze of any model intended to support a cryptographic claim, a review of its
specification and design rationale by an independent cryptographer MUST be recorded in the
repository. PATCH: clarify that Principle I's widths (16-bit signed state, 32-bit output words)
are defaults that a ratified spec may change, as phyco-v2's 32-bit state already does. The
Security Policy and FUT-SEC-1 to FUT-SEC-9 are unchanged, and may only become stricter.
```

## 3. Decisions for the owner or `/speckit-clarify`

From strategy note §8.4. The recommended choice comes first.

1. Mode: keyed duplex, or counter mode with feed-forward and fast key erasure.
2. Key: 256 bits, or 128 bits plus a 128-bit nonce.
3. Claimable sizes: from 4×4, with 2×2 as a reduced research variant, or wider nodes. This
   decides the FUT-SEC-2 and FUT-GRID-2 conflict at 2×2 (security.md §20.1, S15).
4. Nonlinearity: ARX, Boolean, or both explored and one chosen by a stated rule.
5. Frustrated Foraging: removed from the permutation, or kept and analysed (feature-002 FR-004
   and FR-005).
6. The FR-007 rule: standard modes allowed, standard primitives and their constants forbidden.
7. Prediction resistance: out of scope until a validated entropy source exists, or a separate
   entropy-source feature.
8. Certification route for FUT-SEC-9: independent academic cryptanalysis plus an AIS 20/31-style
   evaluation, after version 3.0 of the BSI functionality classes has been read (security.md §6).
9. External expertise: who reviews the design before the freeze, and who reviews the evidence for
   level L5 (security.md §7 and §15).

## 4. Feature 004 (`/speckit-specify`)

This is the prompt of strategy note §9.2, updated for security.md 2.9. Run `/speckit-specify`
with this text:

```text
Cryptographic redesign of PhycoWeb-PRNG, part 1: the security target, a permutation-based
architecture and the phyco-v3 design, up to a frozen design. This feature makes no security
claim; it prepares the evidence a later claim would need (constitution 1.2.0, Security Policy).
It aims at claim level L1 and starts L2 (security.md section 15).

Why: phyco-v2 cannot support any cryptographic claim. Its 64-bit seed caps security at 64 bits
(security.md S1-S3), its step merges states (S13), its veins are confined and biased (S12, S14),
a 2x2 ring that keeps its vein update cannot reach the 2^256 secret states FUT-SEC-2 requires for
a 128-bit claim (S15), and its mixing came from added terms rather than a designed component
(S11).

Scope, in order:
1. Reproduce phyco-v2's 64-bit seed bound on a reduced seed domain before any new key interface
   is implemented (FUT-SEC-8).
2. Specify the security target as requirements, not claims: the properties sought
   (indistinguishability and backtracking resistance; prediction resistance only with a
   validated entropy source, otherwise out of scope), a 128-bit target strength, key and nonce
   sizes, output limits per key and per key and nonce, a threat model extended for keys, nonces,
   multiple users and state compromise, and the generic bounds every parameter must respect.
3. Specify a keyless, bio-inspired permutation on a parameterised grid (FUT-GRID-1 to
   FUT-GRID-5): bijective by construction with a specified inverse; fixed operations only (no
   data-dependent control or shift amounts); full-range state words; round constants and
   rotations generated by stated rules that break grid symmetry and never repeat inside a call;
   at most one or two 32-bit carry chains per pipeline stage; and a round count fixed by a
   pre-registered rule from diffusion, proven trail bounds and a margin. Document the slime-mould
   mapping, but rest no security argument on it.
4. Specify a mode with a published security proof that reduces the generator to the permutation
   (keyed duplex recommended: instantiate, generate, forget, optional reseed), with padding and
   domain separation, and state which grid sizes are claimable, deciding the FUT-SEC-2 and
   FUT-GRID-2 conflict at 2x2 (security.md section 20.1); 2x2 is expected to become a reduced
   research variant.
5. Define reduced variants (word widths 8, 16 and 32, fewer rounds, small grids) from the same
   generics, which the production interface refuses.
6. Deliver: a design document with its design rationale (security.md section 8); a Python
   reference model of the permutation, its inverse and the mode; golden vectors and known-answer
   tests per size; structural evidence (inverse tests, exhaustive bijectivity on the smallest
   variant, exact diffusion in both directions, per-word bias, symmetry checks on the constants);
   and first proven or solver-computed trail bounds on reduced rounds, from tools first validated
   on known results, including re-finding S12-S15 on phyco-v2.
7. Use development keys only, log every candidate design, archive phyco-v2 in baseline/
   (Principle V), and end with an owner design review, an external design review if one can be
   arranged (security.md section 7), and the design freeze.

Carry FUT-SEC-1 to FUT-SEC-9 as requirements traced to tasks and evidence (Security Policy);
FUT-SEC-7's held-out statistical programme is delivered by a later feature and stays open in this
feature's report. Re-decide every carried-over feature-002 requirement (FR-001 to FR-009),
including the FR-007 rule on standard primitives and standard modes. Out of scope: RTL, the
held-out statistical programme, the full cryptanalysis campaign, external review, publication and
any security claim. Inputs: research/security/crypto-redesign-strategy.md, security.md 2.9
(sections 3, 5, 8, 9.2, 12, 15, 20.1 and 21), and research/security/seed-entropy-bound.md
section 5 with the section 5.3 checklist groups A to G.
```

## 5. After the spec

1. `/speckit-clarify`, for the decisions in section 3 that are still open.
2. `/speckit-plan`.
3. `/speckit-checklist`, once per focus area, before the tasks. The agent runs them after the
   plan with these prompts (strategy note §8.3):
   - security: "security: key, nonce, capacity, reachable state, FUT-SEC-1..9 by specification,
     claim wording, the Security Policy's order";
   - design rationale: "design rationale: every component, constant and round count justified;
     inverse specified; no security argument resting on the slime-mould mapping";
   - analysis: "analysis: tools validated on known results first; pre-registered metrics,
     budgets and baselines; reduced variants from the same generics";
   - protocol: "protocol: development keys only before the freeze; every variant logged;
     stricter-only";
   - hardware readiness: "hardware: carry chains per stage, constant time, zeroization, grid
     generics, the width, signedness and shift kind of every operation, FUT-GRID-1..5,
     FUT-HW-1..5";
   - reproducibility: "reproducibility: commands, versions, hashes, deterministic outputs, line
     endings".
4. `/speckit-tasks`, `/speckit-analyze`, then `/speckit-implement`. The work stops at every ⛔
   gate for the owner.

## 6. Later features

Features 005 to 009 follow in order (strategy note §8.2; security.md §22, stage 5a). Their
prompts are in strategy note §9.3.

| Feature | Goal | Claim level |
|---------|------|-------------|
| 005 | Internal cryptanalysis with validated tools | L2 |
| 006 | Implementations and equivalence | L4 |
| 007 | Statistical re-validation on unused held-out key sets | L3 |
| 008 | Hardware validation on the Arty A7-100T; can run alongside 007 | — |
| 009 | External review and the claim decision | L5, then L6 |

An attack on the full design at any point sends the work back to 004 with a new model ID, or
stops it (Option C, security.md §21).

Features 006 and 008, and roadmap stage 7 if `phyco-v2` is ever built in RTL, follow the rules
for AI-assisted VHDL in section 5 of the hardware note, which security.md 2.8 §13 adopts: the AI
drafts, the tools judge, the Python model is the oracle, and the owner approves. The prompts for
006 and 008 in strategy note §9.3 carry them.

Experiment E1 (section 7) runs beside these features. It shares no gates with them and changes no
claim level.

## 7. Experiment E1: the Scrutiny Game (proposed)

E1 is a scenario game about public cryptographic scrutiny. Players practise self-awareness,
empathy and emotion regulation on cards built from the project's real findings, and the humor
style of the game's guide is the variable under test. The generator deals the cards in public
from a published seed, which is a permitted use (security.md §4); allocation to arms, prize draws
and participant codes use the operating-system CSPRNG instead, because they must not be
predictable. The design is in
[`research/engagement/scrutiny-game.md`](research/engagement/scrutiny-game.md), and the argument
for it is in Outlines B and C of
[`research/assertion-outlines.md`](research/assertion-outlines.md).

E1 is a separate track: it needs none of feature 004's gates, feature 004 needs none of its
gates, and it changes no claim level. It does involve people, so it has gates of its own, and
the first of them comes before any code. Think of it as the friendly match played beside the
tournament: different rules, same board, and nobody's rating changes.

### 7.1 Before the E1 prompt

1. Finish feature 003 and run `/speckit-converge` on it (section 1), so that the tooling never
   points at two unfinished features at once.
2. Decide where E1 runs. The constitution's Mission covers evaluating the generator, not research
   with people, so running E1 from this repository needs the amendment in section 7.2. The
   alternative is a separate repository that uses the generator as a dependency.
3. Find the ethics body: a research ethics committee or institutional review board that will
   review the study before anyone is recruited.
4. Decide the questions in section 7.4, or leave them to `/speckit-clarify`.

### 7.2 Constitution amendment for E1 (`/speckit-constitution`)

Needed only if E1 runs from this repository:

```text
Amend the constitution for experiment E1. MINOR: extend the Mission with a second, separate
objective: studying how humor and emotional intelligence help people give and receive public
scrutiny of the generator, without changing any claim about it. Add a Human Participants
Policy: no study with people MAY recruit anyone before a research ethics committee or
institutional review board has approved it and the owner has approved its start, with both
approvals recorded in the repository; participants MUST be adults who gave informed consent,
and MAY withdraw at any time; emotions MUST be self-reported, never inferred from faces, voices
or other biometric data; humor MUST NOT target a participant, a real person or a group, and
MUST stop for any participant who reports distress; personal data MUST be minimal and
pseudonymous and MUST be kept out of the repository; the generator MAY only do public,
reproducible work where predictability is harmless, and allocation to study arms, prize draws
and participant codes MUST use an established CSPRNG. The Security Policy is unchanged and may
only become stricter.
```

### 7.3 Experiment E1 (`/speckit-specify`)

Run `/speckit-specify` with `SPECIFY_FEATURE_DIRECTORY=specs/e1-scrutiny-game` set, so that E1
takes no feature number and the cryptographic stages keep 004 to 009 (security.md §22). The
setting is written to `.specify/feature.json`, which then points at E1; before running a command
for the other track, set `SPECIFY_FEATURE_DIRECTORY` to that track's directory again.

```text
Experiment E1, the Scrutiny Game: a pre-registered study of humor and emotional intelligence in
public cryptographic scrutiny, with PhycoWeb-PRNG as its case study. This feature makes no claim
about the generator and changes no claim level (security.md section 15).

Why: the generator can earn trust only through public scrutiny (security.md sections 7 and 15,
level L5), and scrutiny is hard on the people who give and receive it. Players practise
self-awareness, empathy and emotion regulation on scenario cards built from the project's real
findings and events (security.md section 9.2, S1-S15), and the humor style of the game's guide
is the variable under test: affiliative, gently self-deprecating about the project, sarcastic
about the situation only, or none, against a reading control.

Scope, in order:
1. Research questions, hypotheses, outcomes and an analysis plan ready for pre-registration:
   emotion understanding and management before and after (STEU and STEM, if their research-use
   terms allow), humor style as a moderator (HSQ), perceived support, enjoyment, a manipulation
   check, and open answers analysed by thematic analysis.
2. A pilot of about 20 to 40 adults for feasibility, and a confirmatory design sized by a power
   analysis on the pilot; the number of arms may shrink to what the power allows.
3. The scenario deck: cards written by people, each with its adversity, cast, skill, choices, a
   debrief in every humor style, and what the project actually did; composites only, with no
   real reviewer named or quoted.
4. A humor style guide and safety rules: empathy before any joke, humor off at the player's
   request, no joke about a person or group, no joke on a turn where the player reports
   distress, and support contacts checked by the ethics body.
5. Randomness roles: phyco-v2 deals the card order and the questionnaire order from a published
   study seed (a permitted, harmless use; security.md section 4); allocation to arms, prize
   draws and participant codes use the operating-system CSPRNG; no development or held-out seed
   is used, and nothing from E1 feeds any acceptance decision.
6. No emotion inference: self-report only, with no camera, no microphone and no automated
   emotion analysis; language-model characters only in a later, optional phase, with every
   output logged.
7. An ethics package (consent, debrief, distress rule, data plan) and a local, offline prototype
   of the game for the pilot, with tests that the deal is reproducible from the seed.

Gates: no recruitment before ethics approval and the owner's approval of the start; every
outward action (pre-registration, recruitment, publication, events) needs the owner's
authorization for that action (Principle IX); public text about the generator carries the
disclaimer and makes no randomness-quality or security claim (Principle VIII, gate 3); a VHDL
dealer only after the RTL-start gate, and only once it deals exactly the hand the Python model
deals from the same seed (security.md section 13). Out of scope: any security claim, any change
to the generator or its protocol, emotion recognition, and lotteries. Inputs:
research/engagement/scrutiny-game.md, research/assertion-outlines.md (Outlines B and C) and
security.md sections 4, 9.2 and 15.
```

### 7.4 Decisions for the owner or `/speckit-clarify`

Where there is a recommended choice, it comes first.

1. Where E1 runs: this repository with the amendment of section 7.2, or a separate repository.
2. Which ethics body reviews it.
3. Arms in the pilot: all four humor styles and the reading control, or fewer.
4. Instruments: STEU and STEM, or another validated measure whose terms allow this use.
5. Thanks for players: none, a fixed token of thanks, or a prize draw run by the CSPRNG.
6. Language-model characters: never, or a later phase with a local model.

### 7.5 After the E1 spec

1. `/speckit-clarify`, then `/speckit-plan`.
2. `/speckit-checklist`, once per focus area, before the tasks. The agent runs them after the plan
   with these prompts:
   - ethics: "ethics: consent, withdrawal, debrief, distress rule, ethics approval before
     recruitment, adults only";
   - humor safety: "humor safety: empathy first, opt-out, no targets, distress override, every
     line reviewed";
   - measurement: "measurement: validated instruments and their terms, pre-registration, power,
     manipulation check, thematic analysis";
   - randomness: "randomness: phyco-v2 only for the public deal; CSPRNG for allocation, draws and
     codes; the disclaimer; no held-out seeds";
   - data protection: "data: minimal, pseudonymous, outside the repository, deleted on request,
     no biometric data";
   - inclusion: "inclusion: plain language, accessibility, cultural review of every joke".
3. `/speckit-tasks`, `/speckit-analyze`, then `/speckit-implement`. The work stops at every ⛔
   gate: ethics approval, pilot start, each outward action, and RTL start.
