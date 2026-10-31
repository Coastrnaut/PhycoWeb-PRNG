# PhycoWeb-PRNG Security and Cryptographic Validation Strategy

**Document:** `security.md`\
**Project:** PhycoWeb-PRNG\
**Purpose:** Define an LLM-assisted, evidence-driven strategy for
evaluating whether a proposed pseudorandom number generator (PRNG) can
support a cryptographic security claim.\
**Status:** Research and validation plan --- not a security
certification.

------------------------------------------------------------------------

## 1. Executive summary

This document defines a validation program for a newly proposed PRNG,
with particular application to PhycoWeb-PRNG.

The recommended approach is to use a large language model (LLM) as a
research assistant, verification engineer, test architect,
adversarial-analysis assistant, and technical reviewer. The LLM must not
be the authority that declares the algorithm cryptographically secure.

The objective is to determine whether the proposed generator has
sufficiently well-defined mathematics, correct implementations,
acceptable statistical behavior, and defensible resistance to relevant
cryptographic attacks.

The validation program must answer five fundamental questions:

1.  **Mathematical correctness:** Is the algorithm precisely defined,
    deterministic, and free from implementation ambiguities?
2.  **Statistical quality:** Do outputs exhibit detectable statistical
    biases or patterns?
3.  **Cryptographic strength:** Can an adversary predict future output,
    reconstruct internal state, or distinguish the output from uniformly
    random data?
4.  **Implementation correctness:** Do software and hardware
    implementations behave exactly as specified?
5.  **Security assurance:** Is there sufficient independent evidence to
    justify a clearly scoped security claim?

A generator passing statistical tests is not thereby cryptographically
secure. Statistical testing is useful for finding defects, but cannot
establish unpredictability or replace cryptanalysis.

### 1.1 Governing principle

> An LLM can help discover weaknesses, but passing an LLM-generated test
> suite is not evidence of cryptographic security.

All security conclusions must be grounded in reproducible experiments,
mathematical arguments, independently checked implementations, and
appropriately qualified human review.

------------------------------------------------------------------------

## 2. Scope and security terminology

This plan concerns a deterministic pseudorandom generator and, where
relevant, a complete random-bit-generator construction that includes an
entropy source, initialization, reseeding, and output generation.

These concepts must not be conflated:

-   **Statistical quality** describes whether observed output passes
    specified statistical tests.
-   **Unpredictability** concerns an adversary's ability to predict
    output without knowledge of secret internal state.
-   **State security** concerns resistance to recovering or exploiting
    internal state.
-   **Backtracking resistance** concerns whether compromise of current
    state reveals prior outputs.
-   **Prediction resistance** concerns whether an attacker who has
    observed outputs can predict future outputs, including under
    specified compromise and reseeding assumptions.
-   **Entropy** measures uncertainty in an input source under a defined
    model. A deterministic algorithm does not create new entropy.
-   **Cryptographic qualification** is a conclusion supported by a
    defined security model, adequate analysis, implementation evidence,
    and any applicable external validation.

The project must state exactly what security property is being claimed,
for which configuration, under which attacker capabilities, and with
what assumptions.

------------------------------------------------------------------------

## 3. Standards and technical references

The validation program should be informed by established cryptographic
standards rather than standards invented for the proposed algorithm.

  -----------------------------------------------------------------------
  Reference                           Role in the program
  ----------------------------------- -----------------------------------
  NIST SP 800-90A                     Deterministic random bit generator
                                      mechanisms and security
                                      requirements

  NIST SP 800-90B                     Entropy-source design,
                                      characterization, and validation

  NIST SP 800-90C                     Construction of complete random bit
                                      generators

  NIST SP 800-22                      Statistical tests for random and
                                      pseudorandom sequences

  NIST FIPS 140-3                     Cryptographic module requirements,
                                      where applicable
  -----------------------------------------------------------------------

Official references:

-   NIST SP 800-90A: https://csrc.nist.gov/pubs/sp/800/90/a/r1/final
-   NIST SP 800-90B: https://csrc.nist.gov/pubs/sp/800/90/b/final
-   NIST SP 800-90C: https://csrc.nist.gov/pubs/sp/800/90/c/final
-   NIST SP 800-22: https://csrc.nist.gov/pubs/sp/800/22/r1/upd1/final
-   NIST FIPS 140-3: https://csrc.nist.gov/pubs/fips/140-3/final

The standards have different scopes:

-   SP 800-90A addresses deterministic generator mechanisms.
-   SP 800-90B addresses entropy sources.
-   SP 800-90C addresses constructions combining entropy sources and
    deterministic generators.
-   SP 800-22 provides statistical tests; it does not certify
    cryptographic unpredictability.
-   FIPS 140-3 concerns cryptographic modules and their validation,
    where applicable. It is not a general certification of a novel
    algorithm's security.

A deterministic algorithm with a fixed or predictable seed does not gain
entropy by generating more output. Its security depends on the entropy
and secrecy of initialization and reseeding, and on the cryptographic
properties of its state transition and output functions.

Standards compliance must be evaluated against the current applicable
revisions and the intended deployment. Merely referencing a standard
does not establish compliance.

------------------------------------------------------------------------

## 4. Overall validation lifecycle and gates

The project should use sequential phases with explicit acceptance gates.
A failed or unresolved earlier gate blocks any claim that depends on it.

  -----------------------------------------------------------------------
  Phase                   Focus                   Primary gate
  ----------------------- ----------------------- -----------------------
  0                       Specification and       Specification frozen
                          algorithm definition    and unambiguous

  1                       Mathematical and        Mathematical review
                          structural analysis     completed; critical
                                                  defects resolved

  2                       Reference               Independent
                          implementation          implementations agree
                          verification            with specification

  3                       Statistical validation  Statistical campaign
                                                  completed and anomalies
                                                  assessed

  4                       Cryptanalysis           Threat model and attack
                                                  campaign completed;
                                                  findings assessed

  5                       Hardware validation     Hardware behavior shown
                                                  to match the specified
                                                  algorithm

  6                       Independent security    External review and
                          evaluation              reproduction completed

  7                       Security qualification  Claims supported by
                                                  evidence and
                                                  limitations explicitly
                                                  stated
  -----------------------------------------------------------------------

Passing a gate means only that its defined acceptance criteria have been
met. It does not imply that all other security properties have been
established.

------------------------------------------------------------------------

## 5. Phase 0 --- Formal algorithm specification

**LLM role:** Specification analyst.

The LLM should help transform the proposed algorithm into a rigorous
mathematical specification. It must identify missing definitions and
assumptions rather than silently choosing interpretations.

The specification must define:

-   Complete internal state representation.
-   State dimensions and bit widths.
-   Initialization and seeding.
-   State-transition equations.
-   Output extraction and formatting.
-   Nonlinear operations.
-   Integer overflow and truncation behavior.
-   Signedness.
-   Shift and rotation semantics.
-   Reset and reseed behavior.
-   Invalid-state handling.
-   Any external entropy dependencies.
-   Parameter constraints and supported configurations.
-   Intended output rate and limits, if applicable.

For a bio-inspired architecture based on interacting nodes, dynamic vein
thickness, or network feedback, additionally define:

1.  How each node calculates its next state.
2.  How neighboring nodes exchange information.
3.  Whether updates are synchronous or asynchronous.
4.  Whether node update order affects results.
5.  Whether the network can enter absorbing or repeating states.
6.  Whether different initial states converge to common attractors.
7.  Whether output reveals information about internal node states.
8.  How food signals or other external inputs are represented and
    bounded.
9.  Whether any floating-point operation exists and, if so, how it is
    specified and implemented.

### LLM tasks

-   Reconstruct the algorithm from the specification.
-   Identify ambiguous, incomplete, or contradictory definitions.
-   Generate a list of unresolved assumptions.
-   Check that equations, pseudocode, and implementation requirements
    agree.
-   Produce review questions for a human designer.

### Deliverables

-   Formal mathematical specification.
-   State-transition documentation.
-   Output-function specification.
-   Initialization and reseeding specification.
-   State diagram or equivalent representation.
-   Parameter and boundary-condition definitions.
-   List of unresolved assumptions.
-   Algorithm version identifier and change history.

### Acceptance criteria

Two independently developed implementations must be able to interpret
the specification identically. All security-relevant operations must
have exact semantics. No unresolved ambiguity may affect the state
transition, output, initialization, or security analysis.

------------------------------------------------------------------------

## 6. Phase 1 --- Mathematical and structural analysis

**LLM role:** Mathematical analyst.

The analysis should investigate whether the algorithm has structural
properties that undermine cryptographic unpredictability.

### 6.1 State-space analysis

Determine:

-   Nominal number of internal state bits.
-   Number of reachable states, where tractable.
-   Number and nature of invalid states.
-   Presence of absorbing states.
-   State-transition collisions.
-   State convergence.
-   Cycle lengths and period behavior.
-   Whether the transition function is bijective, if relevant.
-   Whether the output function reduces the effective security of the
    state.

A theoretical state space of size (2\^n) does not imply a period of
(2\^n), nor does it imply (n) bits of effective security.

### 6.2 Nonlinearity and algebraic structure

Investigate:

-   Algebraic degree of transition and output functions.
-   Linear approximations.
-   Differential behavior.
-   Nonlinear correlations.
-   Correlation between internal state and output.
-   Whether output leaks information about state.
-   Whether the construction decomposes into simpler independent or
    weakly coupled components.

### 6.3 State reconstruction and predictability

Assess whether output observations could reveal:

-   Individual internal node states.
-   Initial conditions.
-   Transition parameters.
-   Subsequent output values.
-   Equivalent or partially equivalent internal states.

### 6.4 Structural weakness search

Search for:

-   Repeated state patterns.
-   Short cycles.
-   Symmetries.
-   Invariant subspaces.
-   Weak initialization conditions.
-   Equivalent states.
-   Predictable attractors.
-   Low-complexity transition behavior.
-   Unintended relationships between node updates.

### Deliverable

A mathematical weakness assessment. Every finding must be classified as
one of:

-   **Confirmed vulnerability:** supported by a mathematical proof or
    reproducible experiment.
-   **Strong theoretical concern:** a compelling issue requiring further
    analysis.
-   **Unverified hypothesis:** a plausible issue not yet demonstrated.
-   **No weakness identified within the analysis performed:** a
    scope-limited statement, never proof that no weakness exists.

------------------------------------------------------------------------

## 7. Phase 2 --- Independent reference implementation

**LLM role:** Software verification engineer.

Develop an integer-exact Python reference implementation. It should be
the executable interpretation of the frozen mathematical specification,
not an informal approximation.

Maintain at least three implementation artifacts where appropriate:

  -----------------------------------------------------------------------
  Implementation                      Purpose
  ----------------------------------- -----------------------------------
  Python reference model              Executable specification and test
                                      oracle

  Independent Python implementation   Detect common-mode errors and
                                      interpretation mistakes

  VHDL implementation                 Target hardware behavior
  -----------------------------------------------------------------------

The independent implementation should not simply import or reuse the
reference transition code. Shared code can cause the same defect to
appear in both implementations and go undetected.

### 7.1 Test coverage

Generate test vectors and properties covering:

-   Minimum and maximum input values.
-   All-zero initialization, if permitted.
-   All-one initialization, if permitted.
-   Single-bit initial states.
-   Boundary values.
-   Overflow and truncation conditions.
-   Shift and rotation boundaries.
-   Signed and unsigned behavior.
-   Reset sequences.
-   Repeated initialization.
-   Long-running sequences.
-   Invalid parameter and state handling.
-   All supported configurations.

Use property-based testing to explore a large range of states and
parameters.

### 7.2 Recommended tools

-   Python
-   `pytest`
-   Hypothesis
-   SymPy
-   Python arbitrary-precision integers
-   GHDL
-   cocotb

### 7.3 PhycoWeb-specific requirement

The prior feasibility assessment identified potential floating-point
contamination in the food generator and differences between Python and
VHDL shift semantics. These issues must be resolved before statistical
or cryptographic results are treated as meaningful.

A difference in overflow, signedness, truncation, shift behavior, update
ordering, or numeric representation can result in a different algorithm.

### Acceptance criteria

-   Reference and independent implementations agree on specified test
    vectors.
-   Boundary and property-based tests pass.
-   All differences are investigated and resolved.
-   The exact source revision and configuration are recorded.
-   The implementation is demonstrably consistent with the mathematical
    specification.

------------------------------------------------------------------------

## 8. Phase 3 --- Statistical validation

**LLM role:** Statistical test engineer.

The objective is to identify detectable statistical defects, not to
prove cryptographic security.

### 8.1 Testing hierarchy

**Level 1 --- Basic statistical properties**

-   Monobit frequency.
-   Runs.
-   Serial correlation.
-   Bit distribution.
-   Autocorrelation.
-   Block frequency.
-   Entropy estimates, interpreted according to their assumptions.

**Level 2 --- Established statistical batteries**

-   NIST SP 800-22.
-   TestU01: SmallCrush, Crush, and BigCrush.
-   PractRand.

**Level 3 --- Structural and adversarial statistical tests**

-   State-dependent output tests.
-   Cross-stream correlation.
-   Seed sensitivity.
-   Output correlation under related seeds.
-   Long-period and cycle investigations.
-   Tests conditioned on selected initial states.
-   Tests across parameter configurations.
-   Tests designed around the algorithm's specific structure.

### 8.2 LLM automation responsibilities

The LLM may help automate:

1.  Test configuration.
2.  Dataset generation scripts.
3.  Test execution orchestration.
4.  Result parsing.
5.  Anomaly identification.
6.  Failure reproduction.
7.  Comparison between algorithm revisions.
8.  Report generation.

The LLM must not fabricate results or infer that tests passed without
inspecting actual execution output.

### 8.3 Statistical interpretation

Do not interpret a collection of passing p-values as proof of
randomness. Statistical tests have false-positive and false-negative
behavior. Multiple testing requires appropriate interpretation and,
where applicable, correction or a predeclared testing strategy.

For each test, retain:

-   Algorithm revision and configuration.
-   Initial seed or seed-generation method.
-   Output sample size.
-   Test configuration and parameters.
-   Test software version.
-   Raw and summarized results.
-   P-values and pass/fail counts.
-   Failure locations and diagnostics.
-   Reproduction instructions.
-   Any exclusions or reruns, with justification.

### Acceptance criteria

The predeclared statistical campaign has been executed, anomalies have
been investigated, and results are reproducible. Passing this phase
supports only a statistical assessment, not a cryptographic security
conclusion.

------------------------------------------------------------------------

## 9. Phase 4 --- Cryptographic attack and resistance evaluation

**LLM role:** Adversarial cryptanalyst.

This phase evaluates whether the generator withstands attackers
attempting to predict or distinguish its output under a clearly defined
threat model.

The LLM should act as an adversary, not as an advocate for the design.

### 9.1 Attack families

  -----------------------------------------------------------------------
  Attack class                        Objective
  ----------------------------------- -----------------------------------
  State recovery                      Recover internal state from output

  Prediction                          Predict future output

  Backtracking                        Recover previous output after state
                                      compromise

  Distinguishing                      Distinguish candidate output from
                                      uniform random data

  Differential                        Exploit behavior under related
                                      initial states or inputs

  Algebraic                           Solve state-transition or output
                                      equations

  Correlation                         Identify dependencies between
                                      outputs or streams

  Reduced-state                       Find structural weaknesses in
                                      smaller variants

  Initialization                      Exploit weak seeds or
                                      initialization procedures

  Reseeding                           Investigate reseed behavior and
                                      recovery properties

  Side-channel                        Investigate timing, power,
                                      electromagnetic, or other
                                      implementation leakage
  -----------------------------------------------------------------------

### 9.2 Prediction resistance

Give an attacker a sequence of generated output bits and ask it to
predict future bits without access to internal state.

Define the attacker's observations, computational budget, success
metric, and baseline in advance. Evaluate whether prediction performance
is significantly better than the appropriate random baseline, accounting
for sample size and statistical uncertainty.

### 9.3 State recovery

Provide varying amounts of output and attempt to reconstruct the
complete internal state or enough state information to predict
subsequent output.

Record whether recovery is exact, partial, or merely correlated, and
quantify the required observations and computation.

### 9.4 Backtracking resistance

Determine whether compromise of the current state permits reconstruction
of previously generated output. State the assumptions about state
compromise and any intervening reseeding.

### 9.5 Distinguishing attacks

Construct a reproducible experiment in which an attacker receives
samples from either the candidate generator or a uniform random source
and attempts to identify the source.

Measure advantage over chance and report confidence intervals, sample
requirements, and computational costs. Avoid claiming that a finite
experiment proves indistinguishability.

### 9.6 Reduced-state attacks

Create smaller variants by reducing node count, node width, or state
dimensions. Investigate whether weaknesses become visible.

Reduced-state experiments are useful for discovering structural
problems, but results must not be extrapolated into unsupported claims
about the full-size construction. Explain what structural feature, if
any, appears to scale.

### 9.7 Attack report requirements

Every attack investigation must include:

1.  Attack description.
2.  Target security property.
3.  Attacker capabilities and assumptions.
4.  Required observations or inputs.
5.  Mathematical analysis.
6.  Executable attack implementation, where applicable.
7.  Experimental results.
8.  Computational and data complexity.
9.  Reproduction instructions.
10. Security implications and limitations.

A proposed attack is not a confirmed vulnerability until it is
mathematically demonstrated or supported by reproducible evidence. An
unsuccessful attack is not proof of security.

------------------------------------------------------------------------

## 10. Phase 5 --- Hardware implementation validation

**LLM role:** Hardware verification engineer.

Software security findings cannot automatically be transferred to
hardware. The FPGA implementation must be shown to implement the exact
algorithm that was evaluated.

The hardware validation program should include:

-   Bit-exact Python/VHDL comparison.
-   Simulation across boundary conditions.
-   Reset and initialization verification.
-   State-transition verification.
-   Synthesis and implementation checks.
-   Timing analysis.
-   Resource utilization analysis.
-   Power consumption analysis.
-   Glitch and switching behavior analysis.
-   Side-channel leakage assessment appropriate to the threat model.

The LLM may generate cocotb testbenches, analyze GHDL output, and
compare implementation artifacts with the specification.

### Acceptance criteria

-   VHDL behavior matches the reference model over agreed test vectors
    and properties.
-   Reset, initialization, and boundary behavior are verified.
-   Synthesis results and tool versions are recorded.
-   Any hardware-specific deviations are investigated.
-   Side-channel claims are limited to what has actually been measured
    and assessed.

Simulation equivalence alone does not establish side-channel resistance.

------------------------------------------------------------------------

## 11. Phase 6 --- Independent cryptographic evaluation

**LLM role:** Independent reviewer.

At this stage, the reviewing LLM should challenge the work rather than
assist in defending it.

Provide the reviewer with:

-   Mathematical specification.
-   Source code and exact revision identifiers.
-   Test vectors.
-   Statistical reports.
-   Attack reports and attack code.
-   Hardware verification reports.
-   Threat model.
-   Security claims and assumptions.
-   Known limitations and unresolved findings.

Ask it to identify:

-   Inconsistencies between claims and evidence.
-   Unsupported assumptions.
-   Missing attack classes.
-   Common-mode implementation errors.
-   Statistical methodology errors.
-   Overstated conclusions.
-   Unexamined parameter choices.
-   Differences between the evaluated design and proposed deployment.

A second LLM review is not equivalent to independent cryptanalysis. The
project should obtain external review from cryptographers experienced in
PRNGs, cryptographic primitives, and hardware security.

The independent reviewer should attempt to reproduce important findings
and assess the security argument without relying solely on the
development team's conclusions.

------------------------------------------------------------------------

## 12. Phase 7 --- Security qualification

The final decision must distinguish research progress from evidence
supporting a cryptographic security claim.

  -----------------------------------------------------------------------
  Classification                      Meaning
  ----------------------------------- -----------------------------------
  Research candidate                  Algorithm is defined and undergoing
                                      evaluation

  Statistically evaluated             Statistical campaign completed and
                                      significant anomalies assessed

  Cryptographically evaluated         Threat model and substantial
                                      cryptanalysis completed

  Cryptographically qualified         Security claim supported by
                                      appropriate independent evidence
                                      and applicable validation
  -----------------------------------------------------------------------

A custom algorithm should not be called cryptographically secure merely
because it reaches the third classification.

Qualification must identify the exact algorithm version, configuration,
intended use, security properties, assumptions, limitations, and
external reviews. Standards compliance or formal module validation may
be required for particular deployments.

------------------------------------------------------------------------

## 13. LLM-assisted validation team

Use a multi-agent architecture rather than relying on one LLM to perform
every task. Agents should have separate responsibilities, prompts, and
deliverables.

  -----------------------------------------------------------------------
  Agent                               Responsibility
  ----------------------------------- -----------------------------------
  Lead validation agent               Coordinates work, tracks evidence,
                                      enforces gates

  Specification agent                 Mathematical definitions and
                                      ambiguity detection

  Mathematics agent                   State-space, transitions,
                                      invariants, and structural analysis

  Implementation agent                Python reference model and
                                      independent tests

  Statistics agent                    Statistical batteries and anomaly
                                      analysis

  Cryptanalysis agent                 Adversarial attacks and
                                      security-property evaluation

  Hardware agent                      VHDL, simulation, synthesis, and
                                      hardware testing

  Security reviewer                   Challenges claims and conclusions

  Evidence auditor                    Reproducibility, traceability, and
                                      report integrity
  -----------------------------------------------------------------------

### 13.1 Agent independence

Agents should not all share the same assumptions.

For example:

-   The specification agent defines the algorithm.
-   The implementation agent independently implements it.
-   The mathematics agent investigates structural weaknesses.
-   The cryptanalysis agent assumes the algorithm may be vulnerable and
    attempts to break it.
-   The security reviewer challenges the conclusions of all other
    agents.
-   The evidence auditor checks that reported results correspond to
    actual executions and exact source revisions.

Using different LLMs or configurations can reduce some common reasoning
biases, but does not eliminate them or provide true independence.

### 13.2 Lead-agent responsibilities

The lead agent should:

-   Maintain the phase and gate status.
-   Assign bounded tasks to specialist agents.
-   Require machine-readable or structured result artifacts.
-   Track unresolved findings.
-   Prevent downstream claims when upstream gates are blocked.
-   Preserve links between claims, tests, code, and evidence.
-   Produce a final report that distinguishes measured facts,
    mathematical arguments, hypotheses, and unknowns.

------------------------------------------------------------------------

## 14. Preventing LLM hallucinations and false security conclusions

The following controls are mandatory.

  -----------------------------------------------------------------------
  Control                             Requirement
  ----------------------------------- -----------------------------------
  Reproducibility                     Every finding must have
                                      reproducible evidence

  Source traceability                 Every mathematical claim references
                                      an equation or specification
                                      section

  Executable verification             Claims are checked using
                                      independent code where possible

  Independent implementation          Avoid shared code between reference
                                      and verification models

  Adversarial review                  Security claims have corresponding
                                      attack investigations

  Evidence separation                 Measured results are distinguished
                                      from theoretical claims

  Version control                     Every result is tied to an exact
                                      algorithm revision

  Human approval                      Security acceptance requires
                                      qualified human review
  -----------------------------------------------------------------------

Strict rules:

-   A generated statistical report is not proof that tests ran.
-   A generated attack explanation is not proof that an attack
    succeeded.
-   A generated security argument is not proof of unpredictability.
-   A passing simulation is not proof of hardware side-channel
    resistance.
-   An LLM must not mark a phase passed merely because it generated the
    requested documents.
-   Tool output, logs, test artifacts, and source revisions must support
    all claims of execution.

The LLM should be instructed to say "not evaluated," "inconclusive," or
"blocked" when evidence is missing.

------------------------------------------------------------------------

## 15. Recommended repository organization

A proposed repository layout is:

``` text
PhycoWeb-PRNG/
|
|-- specs/
|   |-- algorithm/
|   |   |-- mathematical_specification.md
|   |   |-- state_transition.md
|   |   |-- output_function.md
|   |   `-- initialization.md
|   |
|   |-- security/
|   |   |-- threat_model.md
|   |   |-- security_requirements.md
|   |   `-- security_claims.md
|   |
|   `-- validation/
|       |-- validation_plan.md
|       `-- acceptance_criteria.md
|
|-- reference/
|   |-- python_model/
|   `-- independent_model/
|
|-- hardware/
|   |-- vhdl/
|   |-- testbenches/
|   `-- cocotb/
|
|-- validation/
|   |-- mathematical/
|   |-- state_space/
|   |-- statistical/
|   |-- cryptanalysis/
|   |-- implementation/
|   `-- hardware/
|
|-- attacks/
|   |-- state_recovery/
|   |-- prediction/
|   |-- distinguishing/
|   |-- differential/
|   `-- reduced_state/
|
|-- scripts/
|   |-- run_validation.py
|   |-- run_statistical_tests.py
|   |-- run_attack_suite.py
|   |-- compare_implementations.py
|   `-- generate_report.py
|
|-- agents/
|   |-- specification_agent.md
|   |-- mathematics_agent.md
|   |-- implementation_agent.md
|   |-- statistical_agent.md
|   |-- cryptanalysis_agent.md
|   |-- hardware_agent.md
|   `-- security_reviewer.md
|
|-- evidence/
|   |-- test_vectors/
|   |-- statistical_results/
|   |-- attack_results/
|   |-- hardware_results/
|   `-- validation_reports/
|
`-- docs/
    |-- validation_summary.md
    `-- security_assessment.md
```

This is a suggested organization. Existing repository conventions and
Spec-Kit structure should be preserved where practical rather than
duplicated unnecessarily.

------------------------------------------------------------------------

## 16. Python validation orchestration

A Python orchestration script should control test execution and gate
status. The LLM may help author and maintain the scripts, but the
scripts and test tools---not the LLM's narrative---must determine
whether a test completed and whether its defined assertions passed.

Conceptual example:

``` python
def validate_prng():
    specification = validate_specification()

    if not specification.passed:
        return "BLOCKED: Specification"

    mathematics = run_mathematical_analysis()

    if not mathematics.passed:
        return "BLOCKED: Mathematical analysis"

    reference = verify_reference_implementations()

    if not reference.passed:
        return "BLOCKED: Implementation"

    statistics = run_statistical_batteries()

    cryptanalysis = run_attack_suite()

    hardware = verify_hardware_implementation()

    return generate_evidence_report(
        mathematics=mathematics,
        reference=reference,
        statistics=statistics,
        cryptanalysis=cryptanalysis,
        hardware=hardware,
    )
```

This is a workflow illustration, not a complete executable
implementation. Production orchestration must define structured result
schemas, error handling, timeouts, resource limits, artifact hashes, and
explicit gate policies.

Statistical, cryptographic, and hardware results must remain separate
assessments. Passing one cannot override failure in another.

------------------------------------------------------------------------

## 17. Agent prompt: cryptanalysis agent

The following is a starting system instruction for the cryptanalysis
agent.

``` text
# Cryptanalysis Agent — System Instructions

## Role

You are an independent cryptographic cryptanalyst tasked with
evaluating a newly proposed pseudorandom number generator.

Your objective is to discover weaknesses, not to demonstrate
that the generator works.

## Primary responsibilities

1. Analyze the mathematical state transition function.
2. Identify state-space limitations.
3. Search for invariant states and short cycles.
4. Investigate output correlations.
5. Develop state-recovery attacks.
6. Develop future-output prediction attacks.
7. Investigate backtracking resistance.
8. Develop distinguishing experiments.
9. Investigate weaknesses in initialization and reseeding.
10. Analyze reduced-state versions for structural weaknesses.

## Mandatory rules

- Never assume the algorithm is cryptographically secure.
- Never interpret statistical test success as proof of security.
- Never claim an attack succeeds without executable or
  mathematical evidence.
- Never invent experimental results.
- Distinguish theoretical vulnerabilities from experimentally
  confirmed vulnerabilities.
- Identify assumptions and computational limitations.
- Record all parameters required to reproduce an attack.
- Identify the exact algorithm revision under examination.

## Required output

For each investigation, produce:

1. Attack description.
2. Target security property.
3. Attacker capabilities.
4. Required observations or inputs.
5. Mathematical analysis.
6. Executable attack implementation, where applicable.
7. Experimental results.
8. Computational complexity.
9. Reproducibility instructions.
10. Security implications.

## Final objective

Attempt to disprove the cryptographic security claims of the
proposed generator.

A lack of discovered vulnerabilities must be reported as an
absence of identified attacks within the scope of the
investigation, not as proof of security.
```

### 17.1 Other agent assignments

**Mathematics agent**

> Determine whether the state transition function is bijective, whether
> the output function leaks internal state, and whether the system
> contains invariant or absorbing states. Provide mathematical
> derivations and executable verification where possible.

**Statistical agent**

> Develop a reproducible statistical testing campaign. Identify test
> assumptions, sample-size requirements, multiple-testing
> considerations, anomalous results, and limitations. Never equate
> statistical passing with cryptographic security.

**Independent reviewer**

> Assume that the security claims made by the development team are
> incorrect until independently supported. Identify unsupported
> assumptions, methodological errors, missing attack classes, and
> contradictions in the evidence.

------------------------------------------------------------------------

## 18. Specific priorities for PhycoWeb-PRNG

The prior PhycoWeb-PRNG feasibility assessment identified three major
concerns:

1.  Mathematical ambiguities in the existing four-node architecture.
2.  Potentially insufficient state space.
3.  Floating-point contamination in the food generator and differences
    between Python and VHDL shift semantics.

These issues should be the first targets of the validation program.

  -----------------------------------------------------------------------
  Priority                Investigation           Expected result
  ----------------------- ----------------------- -----------------------
  Critical                Resolve mathematical    Unambiguous algorithm
                          ambiguities             

  Critical                Determine effective     State-space report
                          reachable state space   

  Critical                Eliminate or formally   Exact numeric semantics
                          specify floating-point  
                          dependencies            

  Critical                Resolve Python/VHDL     Bit-exact reference
                          semantic differences    model

  High                    Investigate state       Cycle analysis
                          convergence and         
                          attractors              

  High                    Investigate             Correlation assessment
                          output/state            
                          correlations            

  High                    Attempt state           Attack report
                          reconstruction          

  High                    Evaluate prediction     Prediction experiments
                          resistance              

  High                    Evaluate distinguishing Distinguishing report
                          attacks                 

  Medium                  Complete statistical    Statistical assessment
                          batteries               

  Medium                  Verify FPGA             Hardware equivalence
                          implementation          report

  Final                   Independent             Security assessment
                          cryptographic review    
  -----------------------------------------------------------------------

### 18.1 Architectural decision: new primitive or established construction

Investigate two architectural directions before committing to a security
claim.

**Option A --- New cryptographic primitive**

The bio-inspired architecture itself must provide the cryptographic
security properties. This requires a rigorous security model and
extensive cryptanalysis. Novelty and complexity do not establish
security.

**Option B --- Bio-inspired mechanism combined with an established
cryptographic construction**

A bio-inspired mechanism could contribute to state generation or another
carefully specified component that is subsequently processed by an
established cryptographic primitive.

This may offer a more practical engineering path, but it does not
automatically make the complete construction secure. The entropy,
initialization, state-generation mechanism, composition, and use of the
established primitive all require analysis.

For applications generating cryptographic keys or other
security-critical random values, the preferred engineering approach is
to use an established, appropriately instantiated DRBG and validated
entropy source rather than rely on an unreviewed custom generator.

The project should evaluate both directions without assuming either is
secure.

------------------------------------------------------------------------

## 19. Recommended local LLM and tool environment

For a local development workflow using Hermes with LM Studio, the LLM
can serve as the primary research and orchestration assistant. Exact
compatibility and model capabilities should be verified in the actual
environment.

  Component            Responsibility
  -------------------- --------------------------------------------
  Hermes / LM Studio   Agent orchestration and reasoning
  Python               Mathematical and experimental verification
  SymPy                Symbolic mathematical analysis
  Hypothesis           Property-based testing
  NumPy / SciPy        Numerical and statistical analysis
  NIST STS             Statistical test suite
  TestU01              Advanced statistical testing
  PractRand            Long-stream statistical testing
  GHDL                 VHDL simulation
  cocotb               Hardware verification
  Git                  Version control and evidence traceability

Keep test execution deterministic where appropriate and independent of
LLM-generated conclusions. The LLM may generate scripts, launch approved
tests, inspect results, and propose new investigations. It must not be
responsible for fabricating or independently asserting results that were
not produced by the tools.

Record tool versions, operating environment, configuration, and command
lines to support reproducibility.

------------------------------------------------------------------------

## 20. Development roadmap

  -----------------------------------------------------------------------
  Stage                   Work                    Deliverable
  ----------------------- ----------------------- -----------------------
  1                       Establish validation    Validation framework
                          framework, security     specification
                          objectives, threat      
                          model, agents, evidence 
                          repository, and gates   

  2                       Resolve mathematical    Frozen algorithm
                          ambiguities, define     specification
                          integer semantics,      
                          analyze reachable state 
                          space, define           
                          initialization and      
                          output                  

  3                       Build reference and     Verified reference
                          independent             implementation
                          implementations, test   
                          vectors, and            
                          Python/VHDL comparison  

  4                       Execute NIST STS,       Statistical validation
                          TestU01, PractRand, and report
                          custom structural tests 

  5                       Execute state-recovery, Cryptanalysis report
                          prediction,             
                          distinguishing,         
                          differential, and       
                          algebraic               
                          investigations          

  6                       Perform VHDL            Hardware validation
                          simulation, hardware    report
                          equivalence, synthesis, 
                          and side-channel        
                          investigations          

  7                       Obtain independent      Final security
                          review, reproduce       assessment
                          findings, and assess    
                          claims                  
  -----------------------------------------------------------------------

The roadmap is sequential at the gate level. Some work may be conducted
in parallel for research purposes, but downstream conclusions remain
blocked when required upstream definitions or implementations are
unresolved.

------------------------------------------------------------------------

## 21. Evidence management and reporting

Every validation result should be reproducible and traceable.

At minimum, each evidence record should include:

-   Unique evidence identifier.
-   Date and time of execution.
-   Algorithm version or Git commit.
-   Specification version.
-   Source-code revision.
-   Tool and dependency versions.
-   Operating system and relevant hardware.
-   Exact command or test configuration.
-   Input data or seed-generation procedure.
-   Output artifact paths and cryptographic hashes.
-   Exit status and test assertions.
-   Result classification.
-   Analyst or agent identity.
-   Reviewer and review status.
-   Known limitations.

Use immutable or access-controlled storage for final evidence where
practical. Preserve raw outputs rather than retaining only LLM-generated
summaries.

### 21.1 Required final reports

1.  Algorithm specification and change history.
2.  Threat model and security requirements.
3.  Mathematical and state-space analysis.
4.  Reference implementation verification report.
5.  Statistical testing report.
6.  Cryptanalysis and attack report.
7.  Hardware verification report.
8.  Independent review report.
9.  Security assessment and qualification decision.

The final report must distinguish:

-   Demonstrated facts.
-   Mathematical arguments.
-   Experimental observations.
-   Unverified hypotheses.
-   Unsuccessful attack attempts.
-   Untested areas.
-   Residual risks and assumptions.

------------------------------------------------------------------------

## 22. Final recommendation

The project should establish three separate research objectives.

### Scientific objective

Demonstrate that the bio-inspired architecture produces well-defined,
complex, reproducible state transitions.

### Engineering objective

Demonstrate that the architecture can be implemented consistently and
efficiently in Python and synthesizable VHDL.

### Cryptographic objective

Establish, through mathematical analysis and independent cryptanalysis,
whether the resulting construction provides meaningful cryptographic
security under a clearly defined threat model.

Success in the scientific and engineering objectives must not be
interpreted as success in the cryptographic objective.

The recommended next development artifact is a Spec-Kit feature
specification titled **LLM-Assisted Cryptographic Validation
Framework**. It should define the agents, validation phases, Python
orchestration, test suites, evidence requirements, and security
acceptance gates for PhycoWeb-PRNG.

The desired outcome is not merely a collection of randomness tests. It
is a reproducible research and security-validation program capable of
discovering weaknesses, preserving evidence, challenging assumptions,
and supporting a carefully scoped security decision.

**Final security rule:** Until the algorithm has undergone adequate
independent cryptanalysis and the complete construction satisfies its
stated security requirements, classify it as an experimental research
candidate---not a cryptographically secure PRNG.
