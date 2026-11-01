# Research Note: VHDL and Generative AI, Fast Drafts and Strict Judges

Date: 2026-10-31.

**Status:** a proposal for owner review, drafted by the AI coding agent, which declares an
interest: it is one of the language models this note is about. No RTL exists in this repository,
none of the tools below is installed, and nothing here is a security claim. The policy is in
[`security.md`](../../security.md) 2.8, whose section 13 adopts the essential rules of section 5
below, and the [constitution](../../.specify/memory/constitution.md) 1.2.0, which prevails. The
argument is set out as Outline D of [`research/assertion-outlines.md`](../assertion-outlines.md),
and the next steps are in [`next.md`](../../next.md).

**Scope:** how VHDL design is changing with language models and generative AI, the open-source
VHDL ecosystem, where the language itself is going, and what all of it means for roadmap stage 7
and features 006 and 008. The source material also described an automotive safety system-on-chip
with lockstep processors, ECC wrappers and a watchdog. At the owner's request that part is left
out: it answers a functional-safety question that this project does not ask.

> Passing statistical batteries does not show cryptographic security. This generator must not be
> used to generate secrets; use an established cryptographic random-number generator for keys,
> nonces, tokens and salts.

## 1. Summary

- Language models now draft VHDL in seconds, but VHDL is the hardware language they know less
  well. The benchmarks agree: models struggle with VHDL (VHDL-Eval, 2024), and their accuracy
  drops on multi-file designs, hierarchy and generating a module from its specification
  (VHDL-REPOBENCH, 2026). New datasets are closing the gap, one repository at a time.
- The field's answer is the tool in the loop: the model drafts, a deterministic tool reports, the
  model repairs, and an engineer approves (RTLFixer, 2024; Sigasi, 2026). Generated testbenches
  are judged the same way, by whether they catch deliberately broken designs (AutoBench, 2024).
- For this project the rule fits on a sticky note: **the AI drafts, the tools judge, the Python
  model is the oracle, and the owner approves.** Section 5 turns it into twelve rules, and
  security.md 2.8 §13 adopts the essential ones.
- The project's own model has sharp corners that an AI translation would cut itself on. The
  pressure differences need an arithmetic shift, and the vein value can reach exactly 2³¹ for one
  step (S12), where a VHDL-2008 INTEGER overflows, a signed comparison gives the opposite answer
  and an otherwise unused conductance class wakes up (section 5.2).
- VHDL itself is moving towards verification. VHDL-2019 added interfaces, richer file and
  environment access and a 64-bit minimum INTEGER, and IEEE P1076, approved on 26 March 2026, is
  drafting the next revision under the title "Verification and Hardware Design Language".
- The open ecosystem now covers the whole flow: simulation (GHDL, NVC), verification (VUnit,
  OSVVM, UVVM, cocotb), editing (VHDL-LS), synthesis checks and formal properties (Yosys with the
  GHDL plugin, SymbiYosys), and an open place-and-route flow for the board's XC7A100T (openXC7).
  For this project they are cross-checks; Vivado stays the reference for FUT-HW-2.

## 2. How VHDL design is changing

### 2.1 The data gap

Most work on language models for hardware has been done in Verilog, and VHDL is catching up. The
resources below are the ones checked for this note; how each was checked is in section 9.

| Resource | What it is | Scale | Finding or purpose |
|----------|------------|-------|--------------------|
| VHDL-Eval (Vijayaraghavan et al., IBM, LAD 2024) | Evaluation framework with self-verifying testbenches; some problems translated from Verilog sets | 202 problems | Models struggle with VHDL; zero-shot prompting, in-context learning and parameter-efficient fine-tuning compared as remedies |
| VHDL-REPOBENCH (Vijayaraghavan et al., arXiv, October 2026) | Repository-level benchmark with problem statements, module stubs and self-checking testbenches | about 100 repositories, 2,500 files and 500 testbenches | Moderate accuracy at line and block level; considerably lower on multi-file reasoning, hierarchy and specification-to-module generation |
| VHDLBench (Sakhreliya and Franklin, ISQED 2026) | Training and evaluation pairs made by masking modules, keeping the dependencies between files | 356 repositories, 39,000 files | Attributes the difficulty mainly to missing training data; fine-tuned 7B models beat their base models on structure, semantics and exact match |
| VHDLSuite (Shen et al., arXiv, June 2026) | Pipeline that converts Verilog designs and their testbenches into VHDL tasks, validated with VUnit and GHDL | over 200 problems, in a set it also calls VHDLBench (not the row above) | Singles out VHDL's stricter semantics; its numbers were not checked here |
| VHDL-Instruct (Drazic, Senouci and Benatallah, FORGE 2026) | An open training dataset for benchmarking and VHDL generation | Not checked. The source material says 18,500 circuits, but the publisher's page refused automated access and the Crossref record has no abstract | Named only |
| LLM_4_TestBench (NOKHAB-Lab, Hugging Face) | VHDL design and testbench pairs, checked with GHDL; MIT licence | 4,754 pairs | Training data for testbench generation |

### 2.2 What goes wrong

Two kinds of evidence agree on the failure modes. The benchmarks find that models lose their way
across files and down hierarchies (VHDL-REPOBENCH). A tool vendor's account of AI agents writing
HDL adds the everyday version: a first attempt rarely finishes the job, unresolved references and
mismatched declarations are common, and a model left to diagnose its own errors may invent a
declaration or recreate a component that already exists (Sigasi, 30 July 2026, a vendor's article
about its own tool). VHDL's strict typing is what lets the language catch such errors early, and
it is plausibly also what a model trained mostly on Verilog trips over.

### 2.3 Tools in the loop

The pattern that works is old-fashioned engineering with a very fast intern: draft, compile, read
the error, fix, repeat, then let someone senior look. RTLFixer (Tsai, Liu and Ren, DAC 2024)
found that about 55% of the errors in model-written Verilog were syntax errors and, with retrieval
and ReAct prompting on compiler feedback, fixed about 98.5% of the compilation errors in 212
erroneous implementations. Sigasi describes the same loop for VHDL and SystemVerilog, with its
semantic analysis reporting diagnostics to the agent through the Model Context Protocol. It
recommends that deterministic tools, not the model, judge the output, and that an engineer
approve every change.

Two cautions. RTLFixer's results are for Verilog. And compiling is not the same as working: a
design that compiles has only proved that it is a design.

### 2.4 Testbenches written by models

Generated testbenches need judging too, or the model grades its own homework. AutoBench (Qiu et
al., MLCAD 2024) generates a testbench from the description of the design under test, part in HDL
and part as a Python checker. Its evaluation framework, AutoEval, counts a testbench in three
steps: it compiles (Eval0); it passes the golden design (Eval1); and, run against mutants of the
golden design, it agrees with the golden testbench on more than 80% of them (Eval2). On 156
problems from VerilogEval-Human, AutoBench reached 44.81% Eval2 pass@1 against 28.46% for direct
generation, and sequential circuits were much harder (26.00% against 7.73%). Judging tests by the
faults they catch is mutation analysis, which DeMillo, Lipton and Sayward introduced in 1978.

A survey with two of the same authors (Xu, Li and Schlichtmann, July 2026) describes front-end
design moving from local assistance towards agentic execution, with circuits and testbenches
generated from a shared specification. That is efficient, and it is also exactly how a misreading
of the specification gets into the design and into its judge at the same time. The remedy is an
oracle that did not read the specification the same way: here, the Python reference model and its
golden vectors, which exist before any RTL does.

### 2.5 Where a model helps, and where it must not be trusted

| Helps | Must not be trusted with |
|-------|--------------------------|
| Entity, port and generic boilerplate from the design document | Expected values |
| Testbench scaffolding around the oracle: vector readers, cocotb glue, reports | Its own verdict that a design is correct |
| Repairs driven by tool diagnostics | Timing, constant-time or side-channel arguments |
| A first RTL draft of the model's step, to be judged | Security arguments of any kind (security.md §16.3) |
| Comments, documentation and diagrams | The licence of code it reproduces from memory |

## 3. The open VHDL ecosystem

| Project | What it does | Licence, as checked | Possible use here |
|---------|--------------|---------------------|-------------------|
| GHDL | Open-source VHDL simulator: full support for 1987, 1993 and 2002, partial or most of 2008 (sources differ); writes GHW, VCD and FST waveforms for viewers such as GTKWave | GPL-2.0 | The simulator FUT-HW-1 names |
| NVC | VHDL compiler and simulator; VHDL-2008 by default, nearly all of it except PSL; VHDL-2019 experimental | not checked | A second, independent simulator |
| VUnit | Unit-testing framework for VHDL and SystemVerilog with a Python test runner | MPL-2.0; its bundled OSVVM part under Artistic 2.0 | Test runner for vector-driven testbenches |
| OSVVM | Libraries for constrained random tests, functional and "intelligent" coverage, scoreboards, verification components and scripting, with JUnit XML and HTML reports | not checked | Coverage of grid sizes and edge states |
| UVVM | Verification library and methodology with bus functional models and verification components, developed in cooperation with ESA since 2017 | not checked | Bus-level testbenches for the board's interfaces (feature 008) |
| cocotb | Testbenches written as Python coroutines; GHDL support experimental (GHDL 2.0 or later), NVC from 1.11.0 | not checked | The Python reference model as a live oracle |
| VHDL-LS (`rust_hdl`) | Language server: live syntax and type checking, missing and duplicate declarations, library mapping in `vhdl_ls.toml` | not checked | The first and fastest check of every draft |
| GHDL plugin for Yosys, with SymbiYosys | Experimental VHDL front end for Yosys; formal verification with PSL, whose support is partial; designs are checked with `ghdl --synth` first | not checked | Synthesis checks; formal properties on reduced widths |
| openXC7 | Open flow for 7-series parts (nextpnr-xilinx, Project X-Ray, fasm2frames), with a chip database for the XC7A100T in the CSG324 package and the Arty A7-100 among its example boards; not supported by the vendor | not checked | An open second opinion on fit, never the timing reference |
| PoC, "Pile of Cores" | VHDL library of arithmetic units, caches, clock-domain crossings, FIFOs, RAM wrappers and I/O controllers from TU Dresden's VLSI-EDA chair; the active fork is under the VHDL GitHub organization | Apache-2.0 since 2015 | Style reference; reuse only after rule R9 |
| Open Logic | Vendor-independent FPGA standard library in VHDL-2008 with no vendor primitives: FIFOs, clock-domain crossings, delay lines, interfaces, and fixed-point arithmetic consistent between Python and HDL; supported by GHDL | LGPL-based, with exceptions for FPGA use | A model of vendor-neutral IP (Principle III) |
| NEORV32 | RISC-V system-on-chip in platform-independent VHDL, configured by generics, with no vendor primitives; passes the official RISC-V architecture tests | not checked | Evidence that large vendor-neutral VHDL can be maintained in public |
| White Rabbit PTP core (CERN) | Ethernet MAC with the White Rabbit extension of PTP (IEEE 1588), for sub-nanosecond synchronization between White Rabbit switches and nodes | gateware CERN-OHL-W-2.0+; firmware and software LGPL-2.1-or-later | A model of open-hardware licensing for gateware; not needed by this generator |

The project is licensed under GPL-3.0. Running a tool does not put the design under the tool's
licence; copying a library's code into the repository can, so reused code needs its licence
checked for compatibility and recorded (rule R9). A licence marked "not checked" must be read in
the project's own repository before anything is downloaded.

## 4. Where VHDL itself is going

### 4.1 VHDL-2019

IEEE 1076-2019 was approved on 5 September 2019 and published on 23 December 2019. Its changes
include:

- interfaces through records and mode views, which declare a bundle of signals and their
  directions once;
- sequential block statements;
- file operations such as FILE_REWIND and FILE_SEEK, and files opened for reading and writing;
- additions to the ENV package: directories, GETENV, date and time, and the current file name and
  line;
- `open` for individual subelements in port maps, and pointers to protected types;
- conditional analysis, which lets one source carry tool-specific variants;
- a minimum range for INTEGER of 64 bits instead of 32 (Sigasi; AMD UG901 for Vivado synthesis;
  the normative text was not read).

Support is still uneven: NVC treats VHDL-2019 as experimental, Vivado synthesis supports the
64-bit integers, and GHDL's VHDL-2019 support was not checked for this note.

Mode views suit this project. A grid node talks to its neighbours through the same bundle of
signals on every side, which a mode view could declare once for any grid size (Principle III).
They can wait until every tool in the flow supports them.

### 4.2 The next revision: IEEE P1076

IEEE approved the project authorization request for P1076 on 26 March 2026. The project
supersedes 1076-2019, is run by the VHDL Analysis and Standardization Group, and is titled
"Standard for Verification and Hardware Design Language (VHDL)", although the description on the
same page still says "Hardware Description Language". The description says the revision brings
IEEE 1076.2, 1076.3, 1076.4 and 1164 into one document: the mathematical packages, the synthesis
packages such as `numeric_std`, the VITAL timing standard and `std_logic`. No draft or publication
date was found. A language that writes "verification" into its own name is telling designers
where it thinks the work is, and after section 2.4 it is hard to disagree.

### 4.3 What the project should do about it

- Write synthesizable RTL in VHDL-2008, the version GHDL, NVC (by default) and Vivado share, and
  record the language version of every file and every tool run.
- Never depend on the width of INTEGER. It is at least 32 bits under VHDL-2008 and at least 64
  under VHDL-2019, and its overflow is an error, not the 32-bit wrap-around the model uses. State
  words use `numeric_std` types of explicit width (rule R4).
- Adopt a VHDL-2019 feature, in a testbench first, only when GHDL, NVC and Vivado all support it,
  and record the decision.
- Look for a public P1076 draft when feature 006 is specified.

## 5. Rules for AI-assisted RTL in this project

### 5.1 The rules

The rule of thumb is: the AI drafts, the tools judge, the Python model is the oracle, and the
owner approves. None of this assumes that the drafts will be bad; it assumes that nobody, human
or model, is right by default. The rules apply to roadmap stage 7 (`phyco-v2`, if its RTL is ever
built), feature 006 (`phyco-v3`) and feature 008 (the board).

| ID | Rule | Why |
|----|------|-----|
| R1 | Expected values come only from the Python reference model, its golden vectors (`vectors/`) and the independent C implementation; never from a drafting tool, and never edited to make a test pass | The oracle must not share the author's misreading (section 2.4) |
| R2 | Every draft climbs the same ladder, in order, and goes back to the start on any failure: analysis (VHDL-LS or the simulator's analyser); `ghdl --synth` for synthesizability; bit-exact simulation against the vectors in GHDL, and in NVC once its download is approved; exhaustive or formal equivalence on reduced widths; Vivado synthesis with 0 DSP blocks, no instantiated primitives, and its timing report | A design that compiles has only proved that it is a design (section 2.3) |
| R3 | The vectors include the model's sharp corners, from constructed states as well as from seeds (section 5.2) | A bug that lives at an edge passes every vector that never visits it |
| R4 | State and arithmetic use `numeric_std` `unsigned` or `signed` of explicit width; no INTEGER for state words; arithmetic right shifts through `signed`; every resize and wrap-around written out | INTEGER differs between VHDL-2008 and VHDL-2019, and cannot hold 2³¹ under VHDL-2008 |
| R5 | A testbench counts only after it has failed on a recorded catalogue of seeded mutants of the design, with every surviving mutant explained, for example as equivalent to the design | A testbench that has never failed has not shown that it can (AutoBench's Eval2; DeMillo et al., 1978) |
| R6 | The session that drafts a design does not write the only testbench that judges it, and the oracle side exists before the RTL | Common-mode risk (security.md §16.2) |
| R7 | Each file drafted or repaired with an AI tool is recorded with the tool and model, the date, the task ID and its review status, in the feature's evidence (security.md §17.2) | Provenance tells a later reviewer where to look hardest |
| R8 | Behavioural VHDL only: a vendor primitive, attribute or IP core suggested by a model is refused | Principle III and FUT-HW-1 |
| R9 | Code reused from a library, or generated code that closely matches one, has the library's licence checked against GPL-3.0 and recorded | A model can reproduce code it has seen, without the licence |
| R10 | Every tool download needs the owner's permission (name, source, size), is treated as untrusted until checked, and has its version recorded (security.md §19) | Standing rule |
| R11 | Synthesis, place-and-route, formal checks and long simulations are heavy runs and never overlap battery runs | Each gets the full CPU, and timings stay comparable |
| R12 | RTL starts only after ⛔ RTL start (Principle VIII, gate 2), and no AI-drafted change counts until a person has reviewed it | A gate is a decision, and decisions are the owner's |

### 5.2 The sharp corners of `phyco-v2`

This is the agent's reading of `phycoweb/model_v2.py` and S12, written down so that the first RTL
draft, whoever writes it, does not have to discover it the hard way.

- **Pressure differences shift arithmetically.** Step 3 shifts (p[k] − p[k+1]) mod 2³² right by
  one to four places and fills with ones when bit 31 is set (`_flux`). In VHDL that is
  `shift_right` on `signed`; on `unsigned` it fills with zeros. Negative differences are common,
  so the golden vectors catch this mistake quickly.
- **The vein value can reach exactly 2³¹, for one step.** S12 keeps every vein value in 0…2³¹,
  and class 2 can occur only at exactly D = 2³¹. At that edge, three things happen that happen
  nowhere else:
  - the conductance class, the top two bits of D, is 2, so the shift by three places is used
    only there;
  - INTEGER cannot hold the value under VHDL-2008's minimum range;
  - on veins 0 and 2, the Frustrated Foraging test D > THRESH (0x4D000000) is true as an
    unsigned comparison and false as a signed one, because 0x80000000 read as signed is negative.

  A design with any of these bugs agrees with the model on every vector that never visits the
  edge. The edge therefore needs vectors from constructed states on every channel, stepped in
  the model the way `research/security/vein_descent.py` already steps it from chosen states.
- **Class 3 exists only in constructed states.** From the reset values no vein reaches 3 × 2³⁰.
  A constructed state can start there, and its veins then fall to at most 2³¹ within 16 steps
  (S15). Those states are the class-3 vectors.

For `phyco-v3` (feature 006), the reduced variants of feature 004 play the same role: the
smallest can be compared exhaustively, corners and all.

### 5.3 Proposed workflow

For feature 006 and, with the board steps, feature 008:

1. Before ⛔ RTL start: the model, vectors and known-answer tests are frozen by feature 004; a
   script generates the constructed-state vectors of section 5.2; the mutant catalogue is
   written, by script or by hand, and kept with the testbenches.
2. ⛔ RTL start (Principle VIII, gate 2).
3. Draft from the design document with `numeric_std` types (R4), recording provenance (R7).
4. Climb the ladder of R2. A model may repair from tool diagnostics for a stated number of
   rounds; after that, a person takes over.
5. Run the mutant catalogue against the testbench (R5) and record the kill rate.
6. Review by the owner, or by the hardware role of security.md §16.2 once it is staffed.
7. Feature 008: Vivado post-route results (FUT-HW-2), and optionally an openXC7 fit as a
   cross-check; then the board, with on-board vectors and a long-run CRC (FUT-HW-4).
8. Record the tool versions, commands, hashes and every deviation (security.md §13 and §17).

## 6. Ideas

| Idea | Value | Note |
|------|-------|------|
| GHDL and NVC must agree | high | A simulator bug then has to repeat itself in an independent tool to hide an RTL bug |
| cocotb with the Python model as the live oracle | high | No expected value is copied by hand; GHDL support is experimental, NVC from 1.11.0 |
| Mutation-checked testbenches (R5) | high | The kill rate goes into the phase report |
| Constructed-state vectors for the corners of section 5.2 | high | Cheap: the Python side already exists |
| Formal properties on reduced widths with SymbiYosys | medium | Zeroization, fixed latency, equivalence; PSL support is partial |
| An open-flow fit with openXC7 next to Vivado | medium | Vivado stays the reference; a disagreement is a finding to explain |
| A repair log: how many rounds each AI draft needed, and what the tools caught | medium | Evidence about the method itself, and honest material for experiment E1 |
| VHDL-2019 mode views for the neighbour interfaces | later | Only once GHDL, NVC and Vivado all support them |
| An E1 card from the first RTL-versus-model mismatch | low | Written only after the cause is found and recorded ([scrutiny game](../engagement/scrutiny-game.md) §3) |

## 7. Developments to watch

| Development | Status on 2026-10-31 | Revisit |
|-------------|----------------------|---------|
| IEEE P1076, the next VHDL revision | PAR approved on 2026-03-26; no draft found | When feature 006 is specified |
| VHDL-2019 in open tools | NVC experimental; GHDL not checked | Before adopting any VHDL-2019 feature |
| VHDL datasets and benchmarks | VHDL-Eval, VHDL-REPOBENCH, VHDLBench, VHDLSuite, VHDL-Instruct | When choosing a drafting model: a good score is a reason to try a model, not to trust it |
| Agentic front-end design | Circuits and testbenches generated from one specification (Xu et al., 2026) | Whenever a tool offers to write both: rule R6 applies |
| Formal verification of VHDL in open tools | GHDL plugin for Yosys experimental; PSL support partial | Feature 006 |
| Open 7-series flows | openXC7 supports the XC7A100T in the CSG324 package | Feature 008 |

## 8. Limits

Most of the strongest results are for Verilog (RTLFixer, AutoBench), and that they carry over to
VHDL is assumed, not shown. Benchmark numbers age as fast as the models do. The Sigasi article is
the vendor's account of its own product. VHDL-Instruct's size could not be checked, and the 64-bit
INTEGER rule was read in secondary sources, not in the standard. A design that passes every check
above can still be wrong about timing, power and side channels, which only measurement shows
(security.md §13). And this note was drafted by a language model, which has an obvious interest
in section 2.3 and an equally obvious duty to section 2.2.

## 9. Sources

Checked on 2026-10-31 with the levels of the assertion outlines (§8 there): *Full text*,
*Abstract*, *Record* and *Secondary*, plus *Docs* for a project's or vendor's own pages, read
directly or in a search tool's extract.

Language models and HDL:

- DeMillo, R. A., Lipton, R. J., & Sayward, F. G. (1978). Hints on test data selection: help for
  the practicing programmer. *Computer*, 11(4), 34–41. doi:10.1109/C-M.1978.218136. Record and
  secondary.
- Drazic, P., Senouci, B., & Benatallah, B. (2026). VHDL-Instruct: training open dataset for LLMs
  benchmarking and HDL code generation. *FORGE '26*, Rio de Janeiro. doi:10.1145/3793655.3793710.
  Record (Crossref, without an abstract; the publisher's page refused automated access).
- NOKHAB-Lab. LLM_4_TestBench, a dataset on Hugging Face. Docs.
- Qiu, R., Zhang, G. L., Drechsler, R., Schlichtmann, U., & Li, B. (2024). AutoBench: automatic
  testbench generation and evaluation using LLMs for HDL design. *MLCAD 2024*.
  doi:10.1145/3670474.3685956; arXiv:2407.03891. Full text (HTML).
- Sakhreliya, A., & Franklin, M. (2026). VHDLBench: a dataset with rich contextual relationships
  for training custom LLMs. *ISQED 2026*. Abstract.
- Shen, Y., Shao, M., Zhao, Y., Yu, Z., Chen, B., Tam, Y.-C., & Shafique, M. (2026). VHDLSuite:
  unified pipeline for LLM VHDL generation with data synthesis and evaluation. arXiv:2606.13735.
  Abstract.
- Sigasi (30 July 2026). Can AI generate HDL? Vendor article. Docs.
- Tsai, Y.-D., Liu, M., & Ren, H. (2024). RTLFixer: automatically fixing RTL syntax errors with
  large language models. *DAC 2024*; arXiv:2311.16543. Abstract (arXiv v3).
- Vijayaraghavan, P., et al. (2024). VHDL-Eval: a framework for evaluating large language models
  in VHDL code generation. *LAD 2024*; arXiv:2406.04379. Abstract.
- Vijayaraghavan, P., Malhotra, A., Jadhav, A., Degan, E., & Mukherjee, V. (2026).
  VHDL-REPOBENCH: a repository-level benchmark for evaluating large language models on VHDL
  design generation. arXiv:2610.05380. Abstract.
- Xu, K., Li, B., & Schlichtmann, U. (2026). LLM for EDA in front-end design: challenges and
  opportunities. arXiv:2607.09616. Abstract.

The VHDL language:

- AMD. Vivado Design Suite User Guide: Synthesis (UG901), 2023.1, "64-bit Integers". Docs.
- IEEE 1076-2019, IEEE Standard for VHDL Language Reference Manual, approved on 5 September 2019
  and published on 23 December 2019. Record; its features from Sigasi's "What's new in VHDL-2019"
  articles and Aldec's webinar pages. Secondary.
- IEEE Standards Association. P1076, Standard for Verification and Hardware Design Language
  (VHDL); project authorization request approved on 26 March 2026. Record (project page).

Tools and libraries, all Docs (project pages and README files, mostly through search extracts):
GHDL; the GHDL plugin for Yosys; NVC; VUnit; OSVVM; UVVM, with its ESA cooperation from Aldec's
UVVM page and a guest article by Espen Tallaksen; cocotb; VHDL-LS (`rust_hdl`); openXC7; PoC;
Open Logic; NEORV32; and the White Rabbit PTP core on the Open Hardware Repository (ohwr.org).
