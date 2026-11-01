# Research Note: The Scrutiny Game (Experiment E1)

Humor, emotional intelligence and a pseudo-random generator under public review.

Date: 2026-10-31.

**Status:** a proposal for owner review, drafted by the AI coding agent. No one has been
recruited, no ethics review has been requested, nothing has been published, and nothing here is
approved or a security claim. The argument for the experiment is in Outlines B and C of
[`research/assertion-outlines.md`](../assertion-outlines.md), and the next steps are in
[`next.md`](../../next.md) §7. The constitution 1.2.0
([`.specify/memory/constitution.md`](../../.specify/memory/constitution.md)) prevails over this
note.

> Passing statistical batteries does not show cryptographic security. This generator must not be
> used to generate secrets; use an established cryptographic random-number generator for keys,
> nonces, tokens and salts.

> **The Truth.** When faced with adversity, maintain composure to creatively improve stakeholder
> engagement of diverse ideas and perspectives in engineering and learning.

## 1. The idea

Picture a grand chessboard that runs to the horizon. On one side sits a new random-number
generator: a slime mould that learned to solder. On the other side sits everyone who will ever
try to break it. Public cryptographic scrutiny is that game, and designers lose squares in it all
the time. This project has fifteen findings on its scoresheet so far, each recorded with its
basis and classification (security.md §9.2, S1–S15). Losing a square well, without sulking,
flipping the board or blaming the opponent, is an emotional-intelligence skill. So is calming two
teammates who disagree about whether the lost square mattered.

E1 turns those real moments into a short game. Each round deals a scenario card: a reviewer's
blunt post, a teammate's defensive reply, a fan's over-excited announcement. The player
practises one skill on it: noticing their own reaction (self-awareness), reading someone else's
(empathy), or cooling a hot exchange (emotion regulation). A guide then debriefs the move, and
the guide's sense of humor is the variable under test: affiliative, gently self-deprecating,
sarcastic about the situation, or none at all. The generator itself deals the cards, from a
published seed, like a dealer who shuffles with every card face up.

The game asks three questions. Does practising on these cards improve how people understand and
manage emotions in hard technical conversations? Which kind of humor helps, and which hurts,
especially when the player is frustrated? And can a game like this bring kind, careful reviewers
to the board, where the generator needs them most?

## 2. Questions and hypotheses

The hypotheses are proposals for the pre-registration (§7), not findings.

| ID | Question | Proposed hypothesis |
|----|----------|---------------------|
| RQ1 | Does playing the game improve emotion understanding and management more than reading the same findings without the game? | A small gain in emotion management over the reading control, possibly too small for the pilot to detect |
| RQ2 | Does the guide's humor style change perceived support, enjoyment and task performance, above all after a frustrating card? | For perceived support, affiliative humor at least as good as no humor, and both better than sarcasm; self-deprecating humor raises effort but lowers enjoyment, as in Ceha et al. (2021) |
| RQ3 | How do players describe the game's effect on how they give and receive criticism? | Open; answered by thematic analysis (§6) |
| RQ4 | Do players go on to read the design documents? | Exploratory, and measured only with consent |

## 3. The board: scenario cards

Every card comes from something that really happened in this repository, so nobody has to invent
a villain; the project has supplied its own plot twists with admirable regularity. Each card
states its adversity, its cast, the skill it practises, the player's choices, the guide's
debrief in every humor style, and **what the project actually did**.

| Card | Adversity (real source) | Cast | Skill practised |
|------|-------------------------|------|-----------------|
| The 64-bit elephant | A stranger posts that the seed has only 64 bits, so every seed can be tried in about 2⁷² steps (S1–S3) | the stranger; you | Self-awareness: notice the urge to defend, then thank and confirm |
| Merge conflict, the literal kind | A reviewer shows two states with the same successor (S13). One teammate shrugs; another declares the project doomed | two friends who disagree; you | Empathy, and mediating between two friends |
| Statistically fabulous | A fan announces that BigCrush passed, so the generator must be secure | the fan; you | Correcting a supporter without crushing them |
| The sarcastic review | "Bit 29 is always the complement of bit 30. Truly groundbreaking entropy." (S14) | the reviewer; you | Emotion regulation: answer the content, not the tone |
| The midnight battery | A test run overruns its projected time while a stakeholder asks for hourly updates (feature 003, battery attempt 1) | the stakeholder; you | Composure, and honest updates under pressure |
| Two right answers | Two requirements that each look right cannot both hold for a 2×2 grid with today's vein update (S15; security.md §20.1) | two engineers; the owner; you | Holding two perspectives before deciding |
| The tempting claim | A deadline looms, and a friend wants to call the design "cryptographically secure" | two friends; you | Integrity under pressure, without losing the friendship |
| The tool that lied | A test tool returned p = 1 in every run, and everyone was briefly delighted (the `nistrng` erratum) | the team; you | Suspecting good news, and owning a mistake |

The cast are composites: no card names a real reviewer or quotes one, and "the stranger" is
nobody in particular. Each card ends with what the project did, so players also learn how review
works in cryptography: the finding is recorded, the claim is withdrawn or never made, and the
next design is built so that the same mistake cannot happen twice.

One card is reserved and stays face down until it happens: **The first mismatch**, the day the
VHDL dealer deals a different card from the Python model. It is written only after the cause is
found and recorded (feature 006; security.md §13), and it practises owning a shared mistake
without blame, whether the culprit was a person, a simulator or the AI assistant that drafted the
line. The odds of drawing it are good: in hardware, the first mismatch is less a risk than a
tradition.

## 4. The guide's humor styles

There are four styles. People write every line, reviewers check it for kindness, and the pilot
tests it (§7). The styles follow the Humor Styles Questionnaire (Martin et al., 2003), with two
deliberate changes. Self-deprecation is mild and aimed at the project or the guide, never
excessive and never at the player. Sarcasm is aimed at the situation, never at the player or at
any person.

| Arm | Style | Example after "Merge conflict, the literal kind" |
|-----|-------|--------------------------------------------------|
| A | Affiliative | "Two states walked into a step function and only one walked out. We've all been in that meeting." |
| B | Gently self-deprecating, about the project or the guide | "Our step function merges states. In fairness, I merge browser tabs, and I've been doing it for years." |
| C | Sarcastic, about the situation only | "Ah yes, a step function that loses information. Exactly what every permutation dreams of becoming." |
| D | No humor | "Two states share a successor, so the step loses information. Here is what that means for the design." |

Rules for every arm:

- Empathy comes first: the debrief names the emotion and the skill before any joke.
- Humor can be switched off at any moment ("serious mode"), and the choice is respected without
  comment.
- When a player's check-in reports distress, or a message reads as real distress rather than
  game frustration, every arm drops the joke for that turn and shows a sincere message and the
  support contacts from the consent form. These turns are logged and analysed with the player's
  arm (intention to treat).
- No joke about any person, group, identity or health, or about anything outside the scenario.
- A joke never makes a fact less exact. If the joke and the fact compete for a sentence, the fact
  wins and the joke goes home early.

## 5. Who does what: the generator, the CSPRNG, the language model and the FPGA

| Job | Done by | Why |
|-----|---------|-----|
| Dealing the card order, and the order of the end-of-session questionnaires | the `phyco-v2` reference model, from a published study seed | Public and reproducible, where predictability is harmless: a permitted use (security.md §4). Anyone can re-deal and check |
| Assigning players to arms | the operating-system CSPRNG (Python `secrets`) | Allocation must stay hidden until it happens (CONSORT 2010, items 8–10), and a predictable allocation is "anything an adversary benefits from predicting" (security.md §4: **no**) |
| Prize draws, if players are thanked that way | the operating-system CSPRNG | A draw is a lottery (security.md §4: **no**) |
| Participant codes and any tokens | the operating-system CSPRNG | They are secrets (Security Policy) |
| Characters and humor lines in the pilot | people, then reviewers | Language-model humor repeats itself (Jentzsch & Kersting, 2023), and a controlled experiment needs controlled lines |
| Free-text characters, later and only if wanted | a language model held to each arm's style guide, with every output logged and a manipulation check | Phase 4 only (§10). A local model is preferred; an external service only with consent, a data agreement and no personal data |
| Dealing live at an event | the VHDL implementation on the Arty A7-100T | Only after ⛔ RTL start and equivalence evidence (Principle VIII, gate 2; level L4). It must deal exactly the hand the Python model deals from the same seed, and any of its RTL drafted with an AI tool follows the rules of security.md §13 ([`research/hardware/vhdl-genai.md`](../hardware/vhdl-genai.md)) |

The study seed comes from the operating-system CSPRNG and is published in the pre-registration.
It is neither a development seed nor a held-out seed, and nothing from E1 feeds any acceptance
decision. security.md §4 notes that an established non-cryptographic PRNG is usually the better
choice for simulation work. E1 uses `phyco-v2` on purpose, because the generator is the subject
of the game: it is the one card in the deck that knows exactly what it is not for.

An allocation list made in advance can be committed to without being revealed. Before
enrolment, publish in the pre-registration the SHA-256 hash of the list joined with a secret
256-bit salt from the CSPRNG; after the study, publish the list and the salt. Anyone can then
check that the allocation was fixed in advance, and nobody could have predicted it.

## 6. Measures

Emotions are reported by the player, never inferred. There is no camera, no microphone, and no
automated emotion analysis of anything a player writes. Outline C of the assertion outlines gives
the reasons: faces do not reliably reveal emotions (Barrett et al., 2019); commercial emotion
recognition rated Black players' faces as angrier or more contemptuous than white players' faces
(Rhue, 2018); Microsoft began retiring emotion inference from its face service in 2022; and the
EU AI Act prohibits emotion inference in workplaces and education institutions from
2 February 2025.

| Measure | When | Instrument | Note |
|---------|------|------------|------|
| Emotion understanding | before and after | STEU (MacCann & Roberts, 2008) | Ability test built from situations; research-use terms to be confirmed with the authors |
| Emotion management | before and after | STEM (MacCann & Roberts, 2008) | Primary outcome. The control arm takes the same tests, so it also controls for practice effects |
| Humor style | before | HSQ (Martin et al., 2003) | Moderator: effects can depend on the player's own style (Ceha et al., 2021) |
| Momentary feeling | after each card | one self-report item, and an optional word of the player's choosing | Self-report only |
| Perceived support and enjoyment | after each card | short items written for the pre-registration | |
| Manipulation check | at the end | how funny, kind and sarcastic the guide seemed | Shows whether the arms differed as intended |
| What changed, in the player's words | at the end | three open questions | Thematic analysis (Braun & Clarke, 2006) by two coders, blind to arm where possible |

No instrument is downloaded or licensed until its terms have been read and the owner has given
permission for that file.

## 7. Design and analysis

- **Pilot, for feasibility.** About 20 to 40 adults, across the four humor arms and the reading
  control. It asks whether the cards make sense, whether each joke lands as its intended style
  (the manipulation check), whether anyone finds a line hurtful, how long a session takes, and
  how the scores spread. A pilot can tell whether the jokes land. It cannot tell which humor
  style is best, and it will not be asked to.
- **Confirmatory study.** Pre-registered (Nosek et al., 2018), between participants, with its
  size set by a power analysis on the pilot. For scale: telling two arms apart at d = 0.3 with
  80% power and a two-sided 5% level takes about 175 players per arm, fewer when the pre-test is
  a covariate. Five arms of that size is a lot of players. Testing fewer arms well beats testing
  five arms badly, and the pre-registration says which it chose.
- **Primary analysis.** Post-test emotion management adjusted for the pre-test, game against
  reading control. Secondary: the humor arms on perceived support, enjoyment and emotion
  management. Effect sizes come with confidence intervals, and every pre-registered outcome is
  reported, the dull ones included: Principle IV, applied to people.
- **Expectations.** Across 58 studies, EI training has a moderate positive effect, larger in
  published studies than in dissertations (Mattingly & Kraiger, 2019). A one-hour game should
  expect less. A null result is a result, and it gets the same care as a positive one.

Threats to validity, and the counter-moves:

- Players may guess the hypothesis and play along: neutral instructions, and a control that also
  teaches the findings.
- Taking the same test twice is practice: the control arm takes it twice too.
- Joke quality, not joke style, could drive any effect: every line is pilot-tested, and the
  manipulation check shows how each arm actually came across.
- Who signs up: people who already like cryptography and jokes. The report describes the sample
  and does not generalise beyond it.
- The designer is also the experimenter: pre-registration, and coding blind to arm where
  possible.
- An AI drafted these cards and jokes: people rewrite and review them before the pilot. Given
  what Jentzsch and Kersting (2023) found about machine humor, the AI agrees.

## 8. Ethics, consent and safety

Before anyone is recruited:

- approval by a research ethics committee or an institutional review board; which body, and how
  it classifies E1, is settled with that body;
- informed consent, from adults only: taking part is voluntary, players can leave at any time
  without giving a reason, and their data are deleted on request;
- a debrief after the session that explains the humor arms;
- the distress rule of §4, with support contacts checked by the ethics body;
- data minimisation: pseudonymous codes, no names in the data, no recordings, storage outside
  this repository, and only aggregate, anonymised results ever committed;
- accessibility and inclusion: plain language, screen-reader-friendly text, no content that needs
  a joke to be understood, and humor lines reviewed by people of different backgrounds, because
  a joke that charms in one place can be a diplomatic incident in another.

Where players are in the EU, data-protection law applies to their personal data. The ethics body,
and legal advice where needed, decide what that requires; this note is not legal advice.

## 9. Gates

| Gate | Before | Who decides |
|------|--------|-------------|
| Specification | any code, scenario deck or instrument in the repository (Principle VI) | owner (spec approval) |
| Constitution scope | running E1 from this repository, whose Mission covers the generator, not research with people (next.md §7.2) | owner (amendment) |
| ⛔ Ethics approval | any recruitment | the ethics body, then the owner |
| ⛔ Pilot start | the first participant | owner |
| ⛔ Each outward action | pre-registration, recruitment posts, publication, any public event (Principle IX) | owner, for that action |
| ⛔ RTL start | the VHDL dealer (Principle VIII, gate 2) | owner |
| Claims check | any public text about the generator: the disclaimer present, and no randomness-quality or security claim (Principle VIII, gate 3) | owner |

E1 never blocks feature 004, never borrows its gates, and runs nothing heavy while a battery or
solver run has the CPU.

## 10. Phases

1. Now: this note and the assertion outlines. No participants and no code.
2. Specification (next.md §7.3); the ethics package (consent, debrief, distress rule, data plan);
   scenario deck version 0, written by people; the humor style guide.
3. The pilot, then a pre-registered confirmatory study with the arms the pilot justifies.
4. Optional: language-model characters, with logged outputs, a manipulation check and the same
   safety rules.
5. Optional, with feature 009 (security.md §22, stage 5a.6): a public scrutiny event at which
   reviewers play the cards before reviewing the real design; after level L4, the FPGA dealer.

## 11. What E1 is not

- Not evidence about the generator's quality or security. Nothing in E1 changes a claim level
  (security.md §15).
- Not a lottery, and not a way to keep secrets.
- Not therapy, and not a crisis service.
- Not emotion detection.
- Not a reason to rush feature 004. The chessboard will wait; being a metaphor, it is very
  patient.

## 12. Sources

Every source cited here is listed, with how it was checked on 2026-10-31, in §8 of
[`research/assertion-outlines.md`](../assertion-outlines.md).
