# Assertion Outlines: the Proof Programme, the Scrutiny Game and AI-Drafted VHDL

Date: 2026-10-31.

**Status:** a proposal for owner review, drafted by the AI coding agent. These outlines argue for
plans. They are not results, and none of them is a security claim. The policy is in
[`security.md`](../security.md) 2.8 and the constitution 1.2.0
([`.specify/memory/constitution.md`](../.specify/memory/constitution.md)), which prevails. The
experiment of Outlines B and C is described in
[`research/engagement/scrutiny-game.md`](engagement/scrutiny-game.md), the rules that Outline D
argues for are in [`research/hardware/vhdl-genai.md`](hardware/vhdl-genai.md), and the next
steps for all of them are in [`next.md`](../next.md).

> Passing statistical batteries does not show cryptographic security. This generator must not be
> used to generate secrets; use an established cryptographic random-number generator for keys,
> nonces, tokens and salts.

> **The Truth.** When faced with adversity, maintain composure to creatively improve stakeholder
> engagement of diverse ideas and perspectives in engineering and learning.

## 1. How an AssertionOutline works

An AssertionOutline is an argument that wears its skeleton on the outside, like a lobster: easy
to inspect and hard to fake. It has **three claims, four reasons per claim and one piece of
evidence per reason**, twelve pieces of evidence in all, and each part has one job.

- A **claim** is arguable: a reasonable person could disagree with it, which is what makes it
  worth defending. "Random numbers look random" is not a claim. "This generator cannot carry a
  security claim" is.
- A **reason** answers the skeptic's question, "Why do you say that?", and passes the *because*
  test: "claim, because reason" reads as one sentence that a skeptic could still push on.
- A piece of **evidence** is real, cited and representative. The classic warning is the driver
  who drowned because a seat belt held them in a sinking car. The story is true, and it is still
  terrible evidence against seat belts, because it represents almost none of the crashes in which
  belts save lives. Evidence has to look like the whole picture, not its most dramatic corner.

Now picture a grand chessboard stretching as far as the eye can see. A claim is a square you say
you can hold. The reasons are the pieces you post around it, and the evidence is the ground under
each piece. A piece standing on painted ground falls the first time someone pushes it, and on this
board people push; that is what reviewers are for. Losing a square politely, and saying exactly
which push did it, makes the board better for everyone who plays on it next. That is the Truth
above, played as chess.

Two habits keep these outlines honest:

- every source says how it was checked (§8): full text, abstract or publisher's record, a
  project's own documentation, or only other people's summaries;
- every outline ends with its **counter-evidence and limits**, because a representative picture
  includes the parts that disagree.

## 2. Outline A: the proof programme is a ladder, not a leap

The cryptographic route of security.md §15 and §21, argued from evidence in this repository.
"Proof" here means what a cryptographer would accept as progress: reductions, bounds, attacks
tried and failed, and review by people who did not design the thing. It never means a document
that announces "secure"; leaps of that kind are how ciphers end up in museums.

**Claim A1. `phyco-v2` cannot carry a cryptographic claim, so the proof programme starts from a
new design.**

1. Because its 64-bit seed caps every security level at 64 bits, far below the 128-bit floor of
   FUT-SEC-1. A huge state behind a small seed is a mansion whose front door is a cat flap.
   - *Evidence:* security.md §9.2, S1–S3: at most 2⁶⁴ states are reachable at any step, so an
     exhaustive seed search costs about 2⁷² generator steps. Confirmed by specification; the
     generic attack has not been run ([`seed-entropy-bound.md`](security/seed-entropy-bound.md)).
2. Because its step merges states, so information leaks away at every step instead of being
   shuffled.
   - *Evidence:* S13: the vein decay D − (D >> 4) maps 16m + 15 and 16m + 16 to the same value,
     and about 41% of states have such a partner. Proof and experiment
     ([`step-probes.json`](security/step-probes.json)).
3. Because its veins are confined and biased, so a 2×2 ring that keeps them cannot hold the 2²⁵⁶
   secret states that a 128-bit claim needs (FUT-SEC-2).
   - *Evidence:* S15: from any state, every vein falls to at most 2³¹ within 16 steps and stays
     there, which leaves at most about 2²⁵² secret states, and about 2²⁴⁷ over the range S14
     observed; none of 62,982 checked vein-steps broke the bound
     ([`vein-descent.json`](security/vein-descent.json)).
4. Because its statistical quality came from two added ARX terms, not from a component designed
   and analysed for mixing.
   - *Evidence:* S11: without the peristaltic rotation and vein-tone feedback (variant v001), the
     network locks onto the food forcing and fails all 15 SP 800-22 families
     ([`research/002/runs.jsonl`](002/runs.jsonl)).

**Claim A2. A keyless bio-inspired permutation inside a keyed duplex (Option A2) is the most
defensible route to a future claim.**

1. Because the mode's security then rests on one assumption that cryptanalysis can test: that the
   permutation behaves like a random one.
   - *Evidence:* Daemen, Mennink and Van Assche (2017) bound the security of the full-state keyed
     duplex, with built-in multi-user support, assuming a random permutation (ASIACRYPT 2017).
2. Because generic security is then set by a parameter, the capacity, which turns FUT-SEC-2 into
   a rule anyone can check with a calculator.
   - *Evidence:* Bertoni, Daemen, Peeters and Van Assche (2008): a sponge on a random permutation
     is indifferentiable from a random oracle up to about 2^(c/2) queries, so a 128-bit target
     needs a capacity c of at least 256 bits (EUROCRYPT 2008).
3. Because a permutation cannot merge states, the defect of S13 is excluded by construction, and
   the probe that found it becomes a regression test.
   - *Evidence:* the S13 probe ([`step_probes.py`](security/step_probes.py)) finds distinct
     states with the same successor in `phyco-v2`; on a bijection the same probe must find none,
     by definition.
4. Because it follows the shape that standards now take, so reviewers already know how to attack
   it.
   - *Evidence:* NIST SP 800-232 (final, 13 August 2025) standardises Ascon, built on one 320-bit
     permutation and chosen after a public competition (security.md 2.7 §6).

**Claim A3. The project's evidence ladder keeps any future claim honest.**

1. Because the protocol is frozen before the results exist, so the goalposts cannot move once the
   ball is in the air.
   - *Evidence:* the freeze record of battery attempt 1
     ([`freeze.json`](../reports/003-extended-batteries-calibration/attempt-1/freeze.json)) pins
     the SHA-256 of the models, tools and scripts, the held-out seed-set fingerprint and the
     failure rule (S = 101,210), approved by the owner on 2026-10-30, the day the attempt began.
2. Because a tool's silence counts only after it has re-found known answers.
   - *Evidence:* `nistrng` 1.2.3 returned p = 1 in every Non-Overlapping Template run and changed
     its input in the Binary Matrix Rank test. `scripts/repro_nistrng_defects.py` reproduces the
     defects, and security.md §12.5 turns the lesson into a rule.
3. Because a claim is worded in one place only, and withdrawn at once when an attack beats it.
   - *Evidence:* the claim register of security.md §15: every model is at L0 with no claim, and
     an attack below a claimed strength withdraws the claim immediately.
4. Because no claim can skip review by people who did not design it.
   - *Evidence:* the constitution's Security Policy forbids use for secrets without independent
     expert cryptographic review recorded in the repository, and level L5 of security.md §15
     makes that review a gate.

**Counter-evidence and limits.** A reduction is only as strong as its assumption, and only
cryptanalysis tests the assumption about the permutation; the generic bounds say nothing about
attacks on its structure, as the sponge's own designers point out. Designs with these properties
were built by experienced teams and still needed years of public analysis. And the ladder may end
at Option C, stopping, which would be a success of the method, not a failure of nerve.

## 3. Outline B: humor and emotional intelligence, laughing with and never at

**Claim B1. Kind humor works with emotional intelligence, and unkind humor works against it.**

1. Because people who use humor to keep their own spirits up tend to manage emotions better,
   while aggressive and self-defeating humor go with weaker emotion perception.
   - *Evidence:* Yip and Martin (2006), with the Humor Styles Questionnaire and an ability test of
     EI (the MSCEIT): self-enhancing humor went with managing emotions; aggressive humor with
     weaker emotion perception, emotional support and conflict management; self-defeating humor
     with weaker emotion perception. Secondary.
2. Because kind and unkind humor can be told apart and measured, so a study knows which one it is
   testing.
   - *Evidence:* the Humor Styles Questionnaire (Martin et al., 2003): 32 items in four scales of
     eight, affiliative and self-enhancing (kind) against aggressive, which includes sarcasm and
     put-downs, and self-defeating (unkind). Record.
3. Because the pattern is not one study's luck.
   - *Evidence:* a meta-analysis (Schneider, Voracek and Tran, 2018) found that the four styles
     relate differently to mental health, with significant associations with anxiety, depression
     and optimism. Secondary.
4. Because laughing together is how strangers become a team, and reviewers are strangers until
   they are a team.
   - *Evidence:* Dunbar et al. (2012), six studies in the laboratory and at live comedy: pain
     thresholds, a proxy for endorphin release, were higher after laughter than after control
     conditions. Abstract.

**Claim B2. Humor helps in hard moments only when empathy comes first and the person can say
no.**

1. Because the style of an agent's humor changes what it does to a learner.
   - *Evidence:* Ceha et al. (2021), 58 participants teaching a virtual agent: affiliative humor
     raised motivation and effort, while self-defeating humor raised effort but made the task
     less enjoyable. Abstract.
2. Because sarcasm has a price, paid in conflict, unless trust has already been paid for.
   - *Evidence:* Huang, Gino and Galinsky (2015): sarcasm raised creativity on both sides and also
     raised conflict; between people who trusted each other it raised creativity without the
     extra conflict. Abstract and coverage.
3. Because humor can make a machine's failure easier to forgive, which matters most when the user
   is already frustrated.
   - *Evidence:* Xu and Liu (2022), six scenario experiments: humorous responses from AI agents
     increased customers' tolerance of service failures, through perceived warmth and
     competence. Abstract.
4. Because machine-made humor repeats itself, so the jokes in a study should be written, varied
   and reviewed by people.
   - *Evidence:* Jentzsch and Kersting (2023): asked for a joke 1,008 times, ChatGPT (GPT-3.5)
     produced variations of the same 25 jokes more than 90% of the time. Abstract.

**Claim B3. Emotional skills can be practised and measured, modestly, with scenario tasks.**

1. Because EI training works on average, if less spectacularly than its brochures.
   - *Evidence:* Mattingly and Kraiger (2019), a meta-analysis of 58 studies: a moderate positive
     effect, larger in published studies than in dissertations. Abstract.
2. Because tests built from situations measure the understanding and managing of emotions
   directly, instead of asking people how emotionally intelligent they feel.
   - *Evidence:* MacCann and Roberts (2008) introduced the STEU (understanding) and the STEM
     (management), scored against expert judgment. Record and secondary.
3. Because players' own words can be analysed by a stated method instead of quoted for applause.
   - *Evidence:* Braun and Clarke (2006) give a six-phase method for thematic analysis, with its
     pitfalls and quality criteria. Abstract.
4. Because fixing the plan before the data arrive keeps testing a hypothesis apart from finding
   one.
   - *Evidence:* Nosek et al. (2018), "The preregistration revolution": preregistration fixes the
     questions and the analysis before outcomes are seen, which makes the difference visible.
     Abstract.

**Counter-evidence and limits.** Most humor-style findings are correlations from self-reports,
not experiments. Ceha et al. had 58 participants, and the service-failure studies used scenarios
rather than real failures. Humor is not always the best repair: a study of service-robot failures
found polite apologies the stronger choice when the failure was serious (Cho et al., 2026). The
EI-training effect is smaller in unpublished work, a hint of publication bias. And what is funny
differs between people and cultures, which is why the pilot tests every line.

## 4. Outline C: the scrutiny game, with machines, dice and a public board

**Claim C1. In the game, emotions are reported by the player, never inferred by a machine.**

1. Because faces do not reliably reveal emotions.
   - *Evidence:* Barrett et al. (2019) reviewed the evidence for reading anger, disgust, fear,
     happiness, sadness and surprise from facial movements and found that it does not support the
     common view; a smile can signal submission rather than happiness. Abstract.
2. Because automated emotion reading has shown racial bias.
   - *Evidence:* Rhue (2018), 400 photographs of NBA players: Face++ rated Black players as
     angrier, and Microsoft's Face API as more contemptuous, than white players; the gap closed
     only as the smile widened. Abstract.
3. Because a major vendor withdrew the feature itself.
   - *Evidence:* Microsoft retired Azure Face's inference of emotional states under its
     Responsible AI Standard: unavailable to new customers from 21 June 2022, and to existing
     ones after 30 June 2023. Secondary.
4. Because the EU prohibits emotion inference in exactly the places a learning game lives.
   - *Evidence:* the AI Act, Article 5(1)(f), prohibits AI systems that infer the emotions of
     people in workplaces and education institutions, except for medical or safety reasons, from
     2 February 2025. Secondary.

**Claim C2. The generator serves the game as a public, reproducible dealer, never as a keeper of
secrets.**

1. Because shuffling cards in public is a use where predictability is harmless, which the project
   permits.
   - *Evidence:* security.md §4 allows "Reproducible test patterns and simulations where
     predictability is harmless" and forbids lotteries and "anything an adversary benefits from
     predicting".
2. Because assignment to study arms must stay hidden until it happens, which is a job for an
   established CSPRNG.
   - *Evidence:* CONSORT 2010 asks every randomised trial to report how its allocation sequence
     was generated (item 8a) and how it was concealed until assignment (item 9). Checklist.
3. Because a published seed lets anyone re-deal the hand and check it, card by card.
   - *Evidence:* `phyco-v2` is deterministic and bit-exact: golden vectors in
     [`vectors/`](../vectors/) are checked by `tests/test_vectors_v2.py`, and the independent C
     implementation is checked against the same vectors by `tests/test_fast_stream.py`.
4. Because the VHDL dealer may deal only after it matches the Python model bit for bit.
   - *Evidence:* the constitution's Principle II (bit-accurate reference model and differential
     testing) and Principle VIII, gate 2 (RTL start); security.md §15 makes VHDL equivalence part
     of level L4 (FUT-HW-1, FUT-HW-4).

**Claim C3. Public scrutiny of the generator is both the game's case study and the project's only
road to a claim.**

1. Because designers cannot judge their own ciphers.
   - *Evidence:* Schneier's "Memo to the Amateur Cipher Designer" (Crypto-Gram, 15 October 1998):
     anyone can design a cipher that they themselves cannot break, so a design earns trust only
     through other people's analysis. Secondary.
2. Because the field builds trust in public competitions.
   - *Evidence:* NIST's lightweight-cryptography competition took 56 first-round candidates in
     2019, selected Ascon on 7 February 2023, and published it as SP 800-232 in August 2025.
     Announcement and standard.
3. Because this project's own scrutiny has already written fifteen real plot twists, so the
   scenarios need no invention.
   - *Evidence:* security.md §9.2 records findings S1–S15, each with its basis and its
     classification, from the project's own analysis during features 001 to 003.
4. Because a sound design has to survive being known by everyone.
   - *Evidence:* Kerckhoffs (1883), *La cryptographie militaire*: a system must not require
     secrecy, and must be able to fall into the enemy's hands without harm. Secondary.

**Counter-evidence and limits.** The AI Act's reach is still being interpreted: the Commission's
guidelines limit Article 5(1)(f) to inference from biometric data, which leaves inference from
written text outside it (Future of Privacy Forum, 2026). That makes text inference legal there,
not accurate, so the game still does not do it. A deal from a published seed is fair only in the
statistical sense: it is predictable, on purpose, to anyone holding the seed. The VHDL dealer does
not exist yet. And public scrutiny is an outward action: nothing in this outline is posted, run or
announced without the owner's authorization for that specific action (Principle IX).

## 5. Outline D: VHDL and generative AI, fast drafts and strict judges

How the project will use language models for RTL, argued from the field's evidence and from the
project's own model. The rules it argues for are in section 5 of
[`research/hardware/vhdl-genai.md`](hardware/vhdl-genai.md) (the hardware note), and
security.md 2.8 §13 adopts the essential ones. No RTL exists yet, so every claim here is about a
plan.

**Claim D1. Language models can draft VHDL, but they cannot yet be trusted to judge it.**

1. Because VHDL is the hardware language they know less well.
   - *Evidence:* VHDL-Eval (Vijayaraghavan et al., 2024), 202 problems with self-verifying
     testbenches: the models tested struggled with VHDL, and the authors compared zero-shot
     prompting, in-context learning and parameter-efficient fine-tuning as remedies. Abstract.
2. Because they lose their way where real designs live: across files and down hierarchies.
   - *Evidence:* VHDL-REPOBENCH (Vijayaraghavan et al., 2026), about 100 repositories, 2,500
     files and 500 testbenches: moderate accuracy at line and block level, considerably lower on
     multi-file reasoning, hierarchy and generating a module from its specification. Abstract.
3. Because what they lack is data, and the data is only now being gathered.
   - *Evidence:* VHDLBench (Sakhreliya and Franklin, ISQED 2026) attributes the difficulty mainly
     to missing training data, and 7B models fine-tuned on its 39,000 files from 356
     repositories beat their base models. Abstract.
4. Because a first draft has errors that a model, left alone, may misdiagnose.
   - *Evidence:* Sigasi (30 July 2026): generated HDL rarely finishes in one attempt, and a model
     may answer an unresolved reference by inventing a declaration or recreating an existing
     component, so the vendor puts deterministic analysis in the loop. A vendor's article about
     its own tool. Docs.

**Claim D2. Deterministic tools and an independent oracle can turn fast drafts into evidence.**

1. Because compiler feedback lets a model repair most of its own syntax errors.
   - *Evidence:* RTLFixer (Tsai, Liu and Ren, DAC 2024): about 55% of the errors in
     model-written Verilog were syntax errors, and with retrieval and ReAct prompting on compiler
     feedback it fixed about 98.5% of the compilation errors in 212 erroneous implementations.
     Abstract.
2. Because a testbench can be judged by whether it catches deliberately broken designs.
   - *Evidence:* AutoBench (Qiu et al., MLCAD 2024): its Eval2 runs a generated testbench against
     mutants of the golden design; on 156 problems, AutoBench reached 44.81% Eval2 pass@1
     against 28.46% for direct generation. Full text.
3. Because flows now write a circuit and its testbench from one specification, so the judge has
   to come from somewhere else.
   - *Evidence:* Xu, Li and Schlichtmann (2026) survey front-end design moving from local
     assistance to agentic execution, with circuits and testbenches generated from a shared
     specification. Abstract.
4. Because two independent open simulators can now disagree before a person has to.
   - *Evidence:* NVC, an open simulator independent of GHDL, runs nearly all of VHDL-2008
     except PSL by default, and cocotb drives both (GHDL 2.0 or later, experimentally; NVC
     from 1.11.0), so one Python testbench can ask both. Docs.

**Claim D3. VHDL is becoming a verification language too, and the project should follow it
carefully: portable VHDL-2008 with explicit types now, newer features only when every tool has
them.**

1. Because the standard itself now puts verification in its name.
   - *Evidence:* IEEE P1076, whose project authorization request was approved on 26 March 2026,
     is titled "Standard for Verification and Hardware Design Language (VHDL)" and brings 1076.2,
     1076.3, 1076.4 and 1164 into one document. Record.
2. Because VHDL-2019 changed the size of a basic type, so code that leans on INTEGER means
   different things in different versions.
   - *Evidence:* VHDL-2019 raised the minimum range of INTEGER from 32 to 64 bits, according to
     Sigasi's VHDL-2019 overview and AMD's Vivado synthesis guide (UG901); the standard's text
     was not read. Docs.
3. Because support for VHDL-2019 is still uneven.
   - *Evidence:* NVC, which runs nearly all of VHDL-2008, still treats VHDL-2019 as
     experimental. Docs.
4. Because the project's own model has corners that a careless choice of type would cut.
   - *Evidence:* S12 allows a vein value of `phyco-v2` to reach exactly 2³¹, for one step. There
     a VHDL-2008 INTEGER overflows, a signed comparison with the foraging threshold gives the
     opposite answer, and conductance class 2, otherwise unused, is exercised
     (`phycoweb/model_v2.py`; the hardware note, §5.2). Proof (S12) and reading of the model.

**Counter-evidence and limits.** Most of the strongest results are for Verilog, and that they
carry over to VHDL is assumed, not shown. Benchmark numbers age as fast as the models do, and the
vendor article is the vendor's account of its own product. A design that passes every
deterministic check can still be wrong about timing, power and side channels, which only
measurement shows (security.md §13). Tools are not infallible judges either: this project has
already met one that lied (`nistrng`, Claim A3), which is why the hardware note's rule R2 adds a
second simulator once its download is approved. And this outline was drafted by a language model,
which has an obvious interest in Claim D2 and an equally obvious duty to Claim D1.

## 6. What the first drafts taught us

The topic arrived with three example outlines, and the VHDL material for Outline D with claims of
its own. They were a generous start, and checking a generous start is exactly what reviewers are
for, so here is what the check found. No blame attaches: published science wobbles too, as the
first row shows.

| Example evidence | What it turned out to be | Used here? |
|------------------|--------------------------|------------|
| Abel and Kruger (2010), cited for humor and empathy | A study of smile intensity in 1952 baseball photographs and lifespan. A pre-registered replication (Dufner et al., 2018) did not reproduce it | No |
| A University of Maryland video study | Miller's 2005 study of 20 volunteers: blood-vessel function improved after a comedy and worsened after a war film. A cardiovascular finding, not an emotional-intelligence one | No |
| Endorphins released by laughter | Supported for social laughter (Dunbar et al., 2012; Manninen et al., 2017) as a bonding mechanism, not as a measure of EI | Yes, as bonding (B1, reason 4) |
| Martin et al. (2003) | Real, and central: the Humor Styles Questionnaire. It classes sarcasm as aggressive humor, which cuts against praising sarcasm | Yes (B1, reason 2) |
| Martin and Lefcourt (1983); Kuiper, Martin and Olinger (1993) | Humor as a moderator of stress, and as coping; not checked here, and not needed by these outlines | No |
| Cognitive services that "accurately" recognise emotions | Contradicted by the evidence of Claim C1 | Argued the opposite |
| Sarcasm and self-deprecation as safe ways to engage | Mixed: sarcasm raises conflict without trust (Huang et al., 2015), and self-defeating humor lowers enjoyment (Ceha et al., 2021) | Tested as arms, with safeguards |
| VHDL-Instruct, a dataset of 18,500 circuits | The paper exists (FORGE '26, by its Crossref record), but the count could not be checked: the publisher's page refused automated access, and the record has no abstract | Named, without the count (hardware note §2.1) |
| Repair loops with GHDL or Sigasi in them | Shown with compiler feedback for Verilog (RTLFixer, 2024); described for VHDL by a vendor for its own tool (Sigasi, 2026); GHDL validates VHDL benchmarks (VHDLSuite) rather than repairing designs | Yes, with an independent oracle (D2) |
| An automotive safety system-on-chip with lockstep processors, ECC wrappers and a watchdog | A functional-safety design, outside this project's question | Left out at the owner's request |

## 7. Checklist for a new outline

- [ ] Exactly three claims, each one a reasonable person could dispute.
- [ ] Exactly four reasons per claim, each passing the *because* test.
- [ ] Exactly one piece of evidence per reason: real, cited, representative, and labelled with how
  it was checked.
- [ ] Counter-evidence and limits stated.
- [ ] No security claim, and the disclaimer wherever the generator's use is described (Security
  Policy).
- [ ] The Truth: does the outline invite a push on every square, and would its author lose one
  gracefully?

## 8. Sources

Checked on 2026-10-31. *Full text* means the paper itself was read. *Abstract* means the abstract
or the publisher's record was read. *Record* means only the bibliographic details and the
instrument's description were checked. *Secondary* means the findings were checked only in other
people's summaries, so the full text must be read before a specification quotes figures. *Docs*
means a project's or vendor's own pages were read, directly or in a search tool's extract.

Cryptography:

- Bertoni, G., Daemen, J., Peeters, M., & Van Assche, G. (2008). On the indifferentiability of the
  sponge construction. *EUROCRYPT 2008*, LNCS 4965, 181–197. Record and the authors' slides.
- Daemen, J., Mennink, B., & Van Assche, G. (2017). Full-state keyed duplex with built-in
  multi-user support. *ASIACRYPT 2017*, LNCS 10625, 606–637; IACR ePrint 2017/498. Abstract.
- Kerckhoffs, A. (1883). La cryptographie militaire. *Journal des sciences militaires*, IX, 5–38
  and 161–191. Secondary.
- NIST (7 February 2023). Announcement of the selection of the Ascon family for lightweight
  cryptography. Announcement and secondary.
- NIST SP 800-232 (final, 13 August 2025): https://csrc.nist.gov/pubs/sp/800/232/final. Checked
  for security.md 2.7.
- Schneier, B. (1998). Memo to the amateur cipher designer. *Crypto-Gram*, 15 October 1998.
  Secondary, with Schneier's own 2011 post on "Schneier's Law".

Humor, emotion and emotional intelligence:

- Abel, E. L., & Kruger, M. L. (2010). Smile intensity in photographs predicts longevity.
  *Psychological Science*, 21(4). doi:10.1177/0956797610363775. Secondary (replication record).
- Barrett, L. F., Adolphs, R., Marsella, S., Martinez, A. M., & Pollak, S. D. (2019). Emotional
  expressions reconsidered: challenges to inferring emotion from human facial movements.
  *Psychological Science in the Public Interest*, 20(1), 1–68. doi:10.1177/1529100619832930.
  Abstract.
- Ceha, J., Lee, K. J., Nilsen, E., Goh, J., & Law, E. (2021). Can a humorous conversational agent
  enhance learning experience and outcomes? *CHI '21*; arXiv:2108.11259. Abstract and the
  authors' summary.
- Cho, M., Bae, J., Cho, E., & Bae, S. H. K. (2026). Polite or playful? How service robot type and
  apology style influence negative word-of-mouth after service failures. *Computers in Human
  Behavior*, 181, 108995. doi:10.1016/j.chb.2026.108995. Abstract.
- Dufner, M., et al. (2018). Does smile intensity in photographs really predict longevity? A
  replication and extension of Abel and Kruger (2010). *Psychological Science*, 29(1).
  doi:10.1177/0956797617734315. Abstract.
- Dunbar, R. I. M., et al. (2012). Social laughter is correlated with an elevated pain threshold.
  *Proceedings of the Royal Society B*, 279, 1161–1167. doi:10.1098/rspb.2011.1373. Abstract.
- Huang, L., Gino, F., & Galinsky, A. D. (2015). The highest form of intelligence: sarcasm
  increases creativity for both expressers and recipients. *Organizational Behavior and Human
  Decision Processes*, 131, 162–177. doi:10.1016/j.obhdp.2015.07.001. Abstract and coverage.
- Jentzsch, S., & Kersting, K. (2023). ChatGPT is fun, but it is not funny! Humor is still
  challenging large language models. *WASSA 2023*; arXiv:2306.04563. Abstract.
- MacCann, C., & Roberts, R. D. (2008). New paradigms for assessing emotional intelligence: theory
  and data. *Emotion*, 8(4), 540–551. Record and secondary.
- Manninen, S., et al. (2017). Social laughter triggers endogenous opioid release in humans.
  *Journal of Neuroscience*, 37(25), 6125–6131. doi:10.1523/JNEUROSCI.0688-16.2017. Abstract.
- Martin, R. A., Puhlik-Doris, P., Larsen, G., Gray, J., & Weir, K. (2003). Individual differences
  in uses of humor and their relation to psychological well-being: development of the Humor
  Styles Questionnaire. *Journal of Research in Personality*, 37, 48–75. Record.
- Mattingly, V., & Kraiger, K. (2019). Can emotional intelligence be trained? A meta-analytical
  investigation. *Human Resource Management Review*, 29(2), 140–155. Abstract.
- Miller, M. (2005). Laughter and blood-vessel function, University of Maryland Medical Center,
  presented in March 2005. Press coverage only.
- Rhue, L. (2018). Racial influence on automated perceptions of emotions. SSRN working paper
  3281765. Abstract.
- Schneider, M., Voracek, M., & Tran, U. S. (2018). "A joke a day keeps the doctor away?"
  Meta-analytical evidence of differential associations of habitual humor styles with mental
  health. *Scandinavian Journal of Psychology*, 59, 289–300. Secondary.
- Xu, X., & Liu, J. (2022). Artificial intelligence humor in service recovery. *Annals of Tourism
  Research*, 95, 103439. doi:10.1016/j.annals.2022.103439. Abstract.
- Yip, J. A., & Martin, R. A. (2006). Sense of humor, emotional intelligence, and social
  competence. *Journal of Research in Personality*, 40. doi:10.1016/j.jrp.2005.08.005.
  Secondary.

Methods, ethics and law:

- Braun, V., & Clarke, V. (2006). Using thematic analysis in psychology. *Qualitative Research in
  Psychology*, 3(2), 77–101. Abstract.
- CONSORT 2010 statement, checklist items 8–10 (sequence generation, allocation concealment,
  implementation). Checklist read. CONSORT 2025 (Hopewell et al., April 2025) restructured the
  checklist; check its item numbers before a specification cites them.
- European Union (2024). Regulation (EU) 2024/1689, the AI Act, Article 5(1)(f), applying from
  2 February 2025. Secondary.
- Future of Privacy Forum (24 March 2026). Red lines under the EU AI Act: unpacking the
  prohibition of emotion recognition in the workplace and education institutions. Read.
- Microsoft (June 2022). Responsible AI Standard, and the retirement of the Azure Face
  capabilities that infer emotional states. Secondary: press coverage quoting Microsoft.
- Nosek, B. A., Ebersole, C. R., DeHaven, A. C., & Mellor, D. T. (2018). The preregistration
  revolution. *PNAS*, 115(11), 2600–2606. doi:10.1073/pnas.1708274114. Abstract.

VHDL, hardware and AI-assisted design (§9 of the hardware note lists the rest):

- AMD. Vivado Design Suite User Guide: Synthesis (UG901), 2023.1, "64-bit Integers". Docs.
- cocotb and NVC documentation, on simulator support and on VHDL-2008 and VHDL-2019 coverage.
  Docs.
- Drazic, P., Senouci, B., & Benatallah, B. (2026). VHDL-Instruct: training open dataset for LLMs
  benchmarking and HDL code generation. *FORGE '26*. doi:10.1145/3793655.3793710. Record
  (Crossref).
- IEEE Standards Association. P1076, Standard for Verification and Hardware Design Language
  (VHDL); project authorization request approved on 26 March 2026. Record.
- Qiu, R., Zhang, G. L., Drechsler, R., Schlichtmann, U., & Li, B. (2024). AutoBench: automatic
  testbench generation and evaluation using LLMs for HDL design. *MLCAD 2024*; arXiv:2407.03891.
  Full text.
- Sakhreliya, A., & Franklin, M. (2026). VHDLBench: a dataset with rich contextual relationships
  for training custom LLMs. *ISQED 2026*. Abstract.
- Sigasi (30 July 2026). Can AI generate HDL? Vendor article; and Sigasi's VHDL-2019 overview.
  Docs.
- Tsai, Y.-D., Liu, M., & Ren, H. (2024). RTLFixer: automatically fixing RTL syntax errors with
  large language models. *DAC 2024*; arXiv:2311.16543. Abstract.
- Vijayaraghavan, P., et al. (2024). VHDL-Eval: a framework for evaluating large language models
  in VHDL code generation. *LAD 2024*; arXiv:2406.04379. Abstract.
- Vijayaraghavan, P., Malhotra, A., Jadhav, A., Degan, E., & Mukherjee, V. (2026).
  VHDL-REPOBENCH: a repository-level benchmark for evaluating large language models on VHDL
  design generation. arXiv:2610.05380. Abstract.
- Xu, K., Li, B., & Schlichtmann, U. (2026). LLM for EDA in front-end design: challenges and
  opportunities. arXiv:2607.09616. Abstract.
