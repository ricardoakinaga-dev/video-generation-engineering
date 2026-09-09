# Traceability matrix

This matrix connects the supplied blueprint, requirements, canonical owners, acceptance gates, and evaluation cases. It is intentionally explicit so the implemented Skill and the R3 closure can be reviewed against the current prompt rather than against memory. The current prompt copies and frozen bar are [`master-closure-prompt-triple-aaa-20260909-part-1.txt`](master-closure-prompt-triple-aaa-20260909-part-1.txt), [`master-closure-prompt-triple-aaa-20260909-part-2.txt`](master-closure-prompt-triple-aaa-20260909-part-2.txt) and [`triple-aaa-quality-bar-r3.json`](triple-aaa-quality-bar-r3.json); R1/R2 material is historical.

## Purpose and document contract

This document owns cross-document coverage, not the domain semantics themselves. Its invariant is that every requirement and blueprint area points to one canonical owner, a rejectable gate, an eval/review path, and a future implementation boundary. Examples are the rows below; missing links, duplicate owners, stale IDs, and unsupported claims are failures. The package avoids repeating contract definitions here and instead links to their owners; source-backed facts and design hypotheses remain distinguished by the status vocabulary in [`contracts.md`](contracts.md).

## Contents

- [Blueprint-to-owner map](#1-blueprint-to-owner-map)
- [Numbered-section coverage](#2-numbered-section-coverage)
- [End-to-end master-prompt traceability](#5-end-to-end-master-prompt-traceability)
- [Non-functional requirement traceability](#51-non-functional-requirement-traceability)
- [Consistency invariants](#6-consistency-invariants-and-unresolved-questions)
- [Phase 0 acceptance trace](#8-phase-0-acceptance-trace)

## 1. Blueprint-to-owner map

| Blueprint area | Canonical owner | Requirements / gates | Eval coverage |
|---|---|---|---|
| Mission and operating model | `README.md`, `architecture.md` | R-GOV-01, QG-17 | G-001, G-009 |
| Intent parser | `requirements.md`, `contracts.md` | R-INT-01, R-INT-02, R-INT-03, R-INT-04, QG-01 | G-001, G-012 |
| Reference analyzer and retention | `scene-and-continuity.md`, `constraints.md` | R-REF-01, R-REF-02, R-REF-03, R-REF-04, QG-02/QG-05 | G-005, G-008 |
| Complexity analyzer and depth | `scene-and-continuity.md`, `architecture.md`, `vge_core.py` | R-PLAN-01, R-PLAN-02, R-PLAN-06, QG-04 | G-002, G-004, G-009, executable route/metamorphic tests |
| Scene Bible / story engine | `scene-and-continuity.md`, `directing.md` | R-PLAN-03, R-PLAN-04, R-PLAN-05, R-SCENE-01, R-SCENE-02, R-SCENE-03, R-SCENE-04, R-SCENE-05, QG-03 | G-003, G-009 |
| Character and relationships | `directing.md`, `contracts.md` | R-SHOT-01, R-SHOT-02, R-DIR-01, R-DIR-02, QG-11 | G-004, G-006 |
| Dialogue and performance | `directing.md`, `contracts.md` | R-DIR-03, R-DIR-04, QG-10/QG-11 | G-004, G-011 |
| Interaction, contact, motion | `scene-and-continuity.md`, `directing.md` | R-SHOT-03, R-SHOT-04, R-DIR-05, QG-08/QG-09 | G-003, G-004, G-010, G-011 |
| World, environment, shot, camera | `scene-and-continuity.md`, `directing.md` | R-SCENE-03, R-SCENE-05, R-SHOT-05, R-SHOT-06, R-SHOT-07, R-DIR-05, QG-06/QG-13 | G-002, G-009 |
| Continuity and anchors | `scene-and-continuity.md`, `contracts.md` | R-SCENE-04, R-SCENE-05, R-SHOT-02, R-SHOT-04, R-SHOT-05, R-SHOT-06, R-SHOT-07, QG-05, QG-06, QG-07 | G-005, G-008, G-009 |
| Audio and lip-sync | `directing.md`, `constraints.md` | R-DIR-06, R-DIR-07, R-CON-03, QG-12/QG-14 | G-004, G-005, G-011, G-012 |
| Constraint engine | `constraints.md`, `contracts.md` | R-CON-01, R-CON-02, R-CON-03, R-CON-04, QG-08/QG-16 | G-003, G-010, G-011 |
| Prompt compiler | `model-adaptation.md`, `contracts.md` | R-ADP-03, R-ADP-04, R-CON-03, R-CON-04, QG-16 | G-002, G-007 |
| Model adapters and negotiation | `model-adaptation.md`, `research.md` | R-ADP-01, R-ADP-02, R-ADP-03, R-ADP-04, R-ADP-05, QG-15 | G-008, G-012 |
| ComfyUI execution | `comfyui-execution.md`, `contracts.md`, `domain-model.md` | R-EXE-01, R-EXE-02, R-EXE-03, R-EXE-04, R-EXE-05, R-EXE-06, QG-17 | G-009, G-012 |
| Long-form generation | `scene-and-continuity.md`, `comfyui-execution.md` | R-LONG-01, R-LONG-02, R-LONG-03, R-LONG-04, QG-07/QG-17 | G-009 |
| Modes and progressive disclosure | `architecture.md`, `README.md`, `progressive-disclosure.md`, `vge_core.py` | R-PLAN-03, R-PLAN-06, R-QA-01 | G-001, G-004, G-009, route CLI and drift regression |
| Quality gates and failure taxonomy | `acceptance.md`, `failure-and-evals.md` | R-QA-01, R-QA-02, R-QA-03, R-QA-04, R-QA-05, R-QA-06, all gates | G-001..G-012 |
| Golden cases and evals | `failure-and-evals.md` | R-QA-04, R-QA-05, R-QA-06 | G-001..G-012 |
| Non-goals and governance | `README.md`, `constraints.md`, `roadmap.md` | R-GOV-01, R-QA-06 | governance review |

## 2. Numbered-section coverage

The major numbered sections in `BLUEPRINT.md` are covered individually below. Subsections 4.1 and 4.2 are included because they define separate module contracts.

| Blueprint section | Owner | Requirement / gate | Evidence path |
|---|---|---|---|
| 1 Mission | `README.md`, `requirements.md` | R-GOV-01, QG-01/QG-17 | documentation review |
| 2 Core Architectural Principle | `architecture.md` | R-SCENE-01, R-ADP-01, QG-15/QG-16 | architecture decisions |
| 3 High-Level Pipeline | `architecture.md` | R-PLAN-01, R-PLAN-02, R-EXE-01, QG-04/QG-17 | pipeline diagram and contracts |
| 4 Core Modules | `architecture.md` | R-SCENE-01, R-ADP-01, R-EXE-01, QG-15/QG-17 | module map |
| 4.1 Intent Parser | `requirements.md`, `contracts.md` | R-INT-01, R-INT-02, R-INT-03, R-INT-04, QG-01 | G-001, G-012 |
| 4.2 Reference Analyzer | `scene-and-continuity.md`, `constraints.md` | R-REF-01, R-REF-02, R-REF-03, R-REF-04, QG-02/QG-05 | G-005, G-008 |
| 5 Reference Retention Model | `contracts.md`, `scene-and-continuity.md` | R-REF-02, R-REF-04, QG-02/QG-05 | retention matrix |
| 6 Complexity Analyzer | `scene-and-continuity.md`, `architecture.md` | R-PLAN-01, R-PLAN-02, QG-04 | G-004, G-010 |
| 7 Scene Model | `contracts.md`, `scene-and-continuity.md` | R-SCENE-01, R-SCENE-03, R-SCENE-05, QG-03/QG-06 | canonical contracts |
| 8 Scene Bible | `scene-and-continuity.md` | R-SCENE-02, R-SCENE-05, QG-02/QG-03 | G-005, G-009 |
| 9 Story Engine | `directing.md`, `scene-and-continuity.md` | R-PLAN-04, R-PLAN-05, QG-03 | G-003, G-006 |
| 10 Narrative Timeline | `scene-and-continuity.md` | R-PLAN-03, R-LONG-01, R-LONG-02, QG-03/QG-07 | G-009 |
| 11 Character Engine | `directing.md`, `contracts.md` | R-DIR-01, R-DIR-03, QG-11 | G-006 |
| 12 Relationship Model | `directing.md`, `contracts.md` | R-SCENE-04, R-DIR-03, QG-09/QG-10 | G-004, G-006 |
| 13 Dialogue Director | `directing.md` | R-DIR-03, R-DIR-04, QG-10 | G-004, G-011 |
| 14 Performance Director | `directing.md` | R-DIR-03, R-DIR-04, QG-11 | G-004, G-011 |
| 15 Interaction Director | `directing.md`, `scene-and-continuity.md` | R-DIR-02, R-DIR-05, QG-08/QG-09 | G-004, G-011 |
| 16 Contact Graph | `scene-and-continuity.md` | R-DIR-02, R-SHOT-03, QG-08/QG-09 | G-003, G-004 |
| 17 Motion Director | `directing.md` | R-DIR-01, R-DIR-02, QG-08 | G-010, G-011 |
| 18 World Engine | `scene-and-continuity.md` | R-SCENE-05, QG-06/QG-08 | G-002, G-010 |
| 19 Shot Planner | `scene-and-continuity.md`, `contracts.md` | R-SHOT-01, R-SHOT-05, QG-04/QG-17 | G-002, G-009 |
| 20 Shot Graph | `scene-and-continuity.md`, `architecture.md` | R-SHOT-02, R-SHOT-03, QG-06/QG-07 | G-003, G-009 |
| 21 Continuity Engine | `scene-and-continuity.md`, `contracts.md` | R-SHOT-03, R-SHOT-04, QG-05/QG-06/QG-07 | G-005, G-009 |
| 22 Continuity Anchors | `scene-and-continuity.md` | R-SHOT-05, R-SHOT-06, QG-05/QG-07 | G-008 |
| 23 Cinematography Director | `directing.md` | R-DIR-05, QG-13 | G-002 |
| 24 Camera Continuity | `directing.md`, `scene-and-continuity.md` | R-DIR-05, R-SHOT-03, QG-06/QG-13 | G-002, G-009 |
| 25 Audio Director | `directing.md` | R-DIR-06, R-DIR-07, QG-14 | G-006, G-007 |
| 26 Lip-Sync Director | `directing.md`, `model-adaptation.md` | R-DIR-03, R-DIR-06, QG-12 | G-006, G-012 |
| 27 Constraint Engine | `constraints.md` | R-CON-01, R-CON-02, QG-08/QG-16 | G-010, G-011 |
| 28 Negative Constraint Taxonomy | `constraints.md` | R-CON-01, R-CON-02, QG-16 | G-003, G-012 |
| 29 Canonical Prompt Format | `contracts.md` | R-CON-03, R-CON-04, QG-16 | G-002 |
| 30 Prompt Compiler | `model-adaptation.md`, `contracts.md` | R-CON-04, R-ADP-03, R-ADP-04, QG-15/QG-16 | G-007, G-012 |
| 31 Model Adapter Layer | `model-adaptation.md`, `research.md` | R-ADP-01, R-ADP-02, R-ADP-03, R-ADP-04, R-ADP-05, QG-15 | G-008, G-012 |
| 32 ComfyUI Execution Planner | `comfyui-execution.md`, `contracts.md`, `domain-model.md` | R-EXE-01, R-EXE-02, R-EXE-03, R-EXE-04, R-EXE-05, R-EXE-06, QG-17 | G-009, G-012 |
| 33 Long-Form Strategy | `scene-and-continuity.md`, `comfyui-execution.md` | R-LONG-01, R-LONG-02, R-LONG-03, R-LONG-04, QG-07/QG-17 | G-009 |
| 34 Operating Modes | `architecture.md`, `scene-and-continuity.md` | R-PLAN-02, R-PLAN-03, R-LONG-04, QG-04 | G-001, G-009 |
| 35 Pattern Library | `pattern-library.md`, `architecture.md`, `roadmap.md` | R-QA-03, R-QA-04, QG-17 | G-001, G-004, G-010 |
| 36 Progressive Disclosure | `architecture.md`, `README.md` | R-QA-01, R-LONG-04, QG-01/QG-17 | documentation review |
| 37 Proposed Future Skill Shape | `architecture.md`, `roadmap.md` | R-EXE-03, R-QA-06, QG-17 | package-boundary review |
| 38 Quality Gates | `acceptance.md` | R-QA-01, R-QA-02, R-QA-05, QG-01 through QG-17 | G-001 through G-012 |
| 39 Eval Philosophy | `failure-and-evals.md` | R-QA-03, R-QA-04, QG-15/QG-17 | eval-tier policy |
| 40 Example Eval Families | `failure-and-evals.md` | R-QA-03, R-QA-04, QG-05/QG-10/QG-17 | G-005, G-006, G-009 |
| 41 Golden Cases | `failure-and-evals.md` | R-QA-04, R-QA-05, R-QA-06, QG-01 through QG-17 | G-001 through G-012 |
| 42 Failure Taxonomy | `failure-and-evals.md` | R-QA-02, R-QA-04, QG-08/QG-15/QG-17 | failure matrix |
| 43 Non-Goals | `requirements.md`, `roadmap.md` | R-GOV-01, R-EXE-03, QG-17 | non-goal review |
| 44 Documentation-First Requirement | `README.md`, `roadmap.md`, `acceptance.md` | R-QA-06, QG-17 | Definition of Done |
| 45 Design Standard | `architecture.md`, `acceptance.md` | R-QA-03, R-QA-05, QG-08/QG-15/QG-16/QG-17 | quality bar |
| 46 Fundamental Principle | `README.md`, `contracts.md` | R-QA-01, R-QA-02, QG-01/QG-17 | G-009 and observed-state invariant |

## 2.1 R3 closure trace

| R3 bar | Canonical owner | Executable evidence | Current boundary |
|---|---|---|---|
| R3-P0-03 resource margin | `vge_runtime.py` | resource guard regression and local resource observation | Blocks before POST below floor × margin |
| R3-P0-06 oracle discipline | `vge_quality.py` | semantic/continuity known-bad oracle tests | Strong oracle is required per claim; no semantic truth is inferred |
| R3-P0-07 contradiction gate | `vge_core.py`, `vge_quality.py` | contradiction and adapter-gate tests | Canonical state must be supplied and consistent |
| R3-P1/R3-P4/R3-P5 long-form ladder | `vge_quality.py`, long-form fixtures | strict hash-bound validator and real local evidence packet | LF-001/2/3 production remains blocked |
| R3-P8 independent critic | `verification/` | final frozen fingerprint, matrix and mutation sentinel | Fresh review is required after the last material mutation |
| R3-P9 distribution | `tools/verify.py`, release packet | fresh ZIP/CRC/path/secret/weight/CWD checks | Distribution cannot promote unavailable production evidence |

## 3. Requirement coverage rule

For this phase, each requirement must have:

```text
requirement → canonical owner → acceptance gate → evaluation path
```

If a requirement has no executable evaluation yet, its evaluation path is `documentation-review` or `future-runtime-eval`, with the limitation recorded. Missing ownership or missing acceptance is a documentation defect.

## 4. Evidence and drift

Each row can drift independently. A source may change while the contract remains stable; a model profile may change while the requirement remains stable; a gate may be refined after artifact evidence. Changes must update the owner document, source/revalidation note, and affected eval IDs.

Status vocabulary:

- `covered`: owner, gate, and evaluation path are present;
- `partial`: one path is documented but not yet verifiable;
- `stale`: evidence or contract needs revalidation;
- `blocked`: a critical dependency is unavailable;
- `waived`: a human decision records why coverage is intentionally deferred.

## 5. End-to-end master-prompt traceability

The following chain is the acceptance path for the current implementation. A range such as `R-INT-01..04` means every numbered requirement in that range inherits the row's owner, failure family, gate, eval/review path, and implementation target unless a more specific row above overrides it. Production rows remain evidence-limited; implementation coverage is not production acceptance.

| User goal | Requirement(s) | Architecture component | Failure mode | Quality gate | Eval/review path | Future implementation component |
|---|---|---|---|---|---|---|
| Turn creative intent into an actionable plan | `R-INT-01..04` | Intent normalizer and core scene contract | `F-INT-01`, `F-PRM-01` | QG-01, QG-03 | G-001, G-012, ADV-001 | `SKILL.md` intake route + `core-contracts.md` |
| Preserve reference meaning, identity, rights, and precedence | `R-REF-01..04`, `R-GOV-01` | Reference analyzer, retention matrix, safety gate | `F-REF-01..03`, `F-ID-01..03`, `F-GOV-01` | QG-02, QG-05 | G-005, G-007, G-012, ADV-002/009/013/015 | `continuity-and-long-form.md` + `safety-and-provenance.md` |
| Route planning depth by risk and causal complexity | `R-PLAN-01..06` | Complexity analyzer, progressive-disclosure router, narrative planner, shot planner | `F-SHOT-01`, `F-PER-01`, `F-TEMP-01`, `F-PKG-01` | QG-03, QG-04, QG-07, QG-17 | G-001, G-004, G-010, G-011, ADV-004/006 | `SKILL.md` routing + `progressive-disclosure.md` + `vge_core.py` |
| Establish a model-independent canonical scene/state model | `R-SCENE-01..05` | Scene Bible, entity model, state ledger | `F-SCENE-01`, `F-WLD-01..02`, `F-DOC-02` | QG-03, QG-05, QG-06 | G-003, G-007, G-012, static contract evals | `core-contracts.md` |
| Propagate state through dependent shots | `R-SHOT-01..07` | Shot DAG, continuity engine, anchor manager | `F-SCENE-01`, `F-TEMP-01`, `F-CAM-01`, `F-ID-01` | QG-05, QG-06, QG-07, QG-13 | G-005, G-008, G-009, G-010, ADV-006/007/008/017 | `continuity-and-long-form.md` |
| Direct observable story, performance, interaction, and motion | `R-DIR-01..07` | Directing layer, contact graph, motion primitives, camera/audio timelines | `F-AN-01..02`, `F-CON-01..02`, `F-PER-01`, `F-AUD-01` | QG-08, QG-09, QG-10, QG-11, QG-13, QG-14 | G-002, G-003, G-004, G-006, G-009, G-011 | `directing-and-audio.md` + `interaction-and-constraints.md` |
| Select only risk-shaped constraints and compile canonical intent | `R-CON-01..04` | Constraint selector and prompt compiler | `F-CON-03..04`, `F-PRM-01` | QG-08, QG-12, QG-16 | G-001, G-006, G-007, G-012, ADV-016 | `core-contracts.md` + `interaction-and-constraints.md` |
| Negotiate model/runtime capability honestly | `R-ADP-01..05` | Versioned capability registry and adapter negotiator | `F-MOD-01`, `F-QA-01` | QG-15, QG-16 | G-008, G-012, ADV-006/010/012 | `model-adaptation.md` |
| Prepare a ComfyUI plan without unauthorized execution | `R-EXE-01..06` | ComfyUI planner, preflight, immutable execution-attempt record, artifact/hash boundary | `F-EXE-01`, `F-GOV-01`, `F-DOC-03` | QG-14, QG-15, QG-17 | G-007, G-009, G-012, ADV-010/013/014/015 | `comfyui-execution.md` + `contracts.md` |
| Verify behavior, repair failures, and retain evidence | `R-QA-01..06` | Gate runner, observation record, repair loop, eval registry | `F-QA-01..02`, `F-DOC-01..02` | QG-01..17 as applicable | unit-like, scenario, adversarial, regression, long-form, model-adapter categories | `evaluation-and-repair.md` + `validate_plan.py` if justified |
| Support 30–120 second work as bounded assembly | `R-LONG-01..04` | Timeline, shot graph, state propagation, assembly policy | `F-TEMP-01`, `F-WLD-01`, `F-AUD-01` | QG-03, QG-07, QG-14, QG-17 | G-010, G-011, G-012, long-form continuity evals | `continuity-and-long-form.md` |
| Make Phase 0 reviewable and ready for a controlled handoff | `R-DOC-01` | Numbered index and source hierarchy | `F-DOC-01` | QG-17 | DOC-001, P0-01, P0-22..25, documentation review | project-level `SKILL.md` routing entry, after authorization |
| Document the named domain/state concepts without empty abstractions | `R-DOC-02` | Entity catalogue, state classes, contracts, invariants | `F-DOC-02`, `F-SCENE-01` | QG-03, QG-07 | DOC-005/006, P0-03..06, static contract review | `core-contracts.md` |
| Provide future-evaluable known-good and red-team fixtures | `R-DOC-03`, `R-DOC-04` | Golden/adversarial fixture registry and oracles | `F-DOC-02`, `F-QA-01` | QG-01, QG-04, QG-08, QG-15, QG-17 | G-001..G-012 and ADV-001..ADV-017 | `evaluation-and-repair.md` + fixture assets |
| Expose concise reasoning evidence and modular safety boundaries | `R-DOC-05` | Observability events, redaction, provenance, authorization gates | `F-QA-01`, `F-GOV-01` | QG-02, QG-15, QG-17 | DOC-024/025, P0-10, P0-19, safety/diagnostic review | `observability` and `safety-and-provenance` references |
| Record major decisions and remaining uncertainty | `R-DOC-06` | ADR set and blocker/non-blocker queue | `F-DOC-02`, `F-QA-01` | QG-17 | DOC-023, P0-22/23, ADR review | ADRs and maintainer decision log |
| Connect goal through implementation without losing ownership | `R-DOC-07` | This matrix plus canonical ownership/index | `F-DOC-01..02` | QG-17 | DOC-028, P0-02/24, integration review | `SKILL.md` workflow and package references |
| Produce an honest handoff and stop before Phase 1 | `R-DOC-08` | Phase 0 report, roadmap, scope guard | `F-DOC-03`, `F-QA-02` | QG-17 | DOC-029/030, P0-24/25, final Gauntlet critic | no implementation component until explicit Phase 1 authorization |

The future implementation names are proposals, not files created in this phase. The chain deliberately ends at a component boundary and then records the evidence limitation; it never treats a documentation row as runtime proof.

## 5.1. Non-functional requirement traceability

The quality attributes in `requirements.md` are requirements, not aspirations. Each has an owner, failure signal, gate, eval/review path, and future implementation target:

| NFR | Architecture component | Failure mode | Gate | Eval/review path | Future implementation component |
|---|---|---|---|---|---|
| `NFR-TRUTH-01` | evidence/status and capability registry | `F-QA-01` unsupported confidence | QG-15/QG-16/QG-17 | source/profile audit; KB-002 | `core-contracts.md` + `model-adaptation.md` |
| `NFR-COHERENCE-01` | scene/state/shot/continuity graph | `F-SCENE-01`, `F-CAM-01`, `F-TEMP-01` | QG-03/QG-05/QG-06/QG-07/QG-13/QG-14 | G-004/G-008/G-009/G-011 | `continuity-and-long-form.md` |
| `NFR-ACTION-01` | execution plan and operator handoff | `F-EXE-01` workflow invalid | QG-04/QG-15/QG-17 | G-008/G-009; preflight review | `comfyui-execution.md` |
| `NFR-REPAIR-01` | issue/repair route and smallest-owner policy | `F-QA-02` stale evidence | QG-07/QG-17 | known-bad repair loop; mutation sentinel | `evaluation-and-repair.md` |
| `NFR-MAINT-01` | canonical ownership/index and versioned contracts | `F-DOC-01`, `F-DOC-02` | QG-17 | ownership and cross-document review | `core-contracts.md` + ADR process |
| `NFR-CONTEXT-01` | progressive-disclosure router | `F-PKG-01` context bloat/fragmentation | QG-01/QG-17 | routing matrix review; simple-scene fixture G-001 | `SKILL.md` routing + conditional references |
| `NFR-DET-01` | stable IDs, typed state transitions, deterministic checks | `F-QA-02` stale/non-reproducible evidence | QG-07/QG-16/QG-17 | repeated static contract/eval runs | optional `validate_plan.py` |
| `NFR-EXT-01` | adapter boundary and canonical model | `F-MOD-01`, `F-DOC-02` | QG-15/QG-17 | model-adapter fixture and profile review | `model-adaptation.md` |
| `NFR-EXPL-01` | diagnostic/event and redaction layer | `F-OBS-01` opaque or leaking diagnostic | QG-01/QG-17 | observability review with DEC-0042 example | `observability` reference |
| `NFR-TEST-01` | gate/oracle and fixture registry | `F-QA-01`, `F-DOC-02` | QG-01..17 as applicable | unit-like, scenario, adversarial, regression, long-form, adapter evals | `evaluation-and-repair.md` |
| `NFR-DEGRADE-01` | capability negotiation and safety boundary | `F-MOD-01`, `F-GOV-01` | QG-02/QG-12/QG-15/QG-17 | ADV-006/010/013/016; known-bad fixtures | `model-adaptation.md` + `safety-and-provenance.md` |
| `NFR-DUP-01` | canonical owner table and ADR discipline | `F-DOC-01`, `F-DOC-02` | QG-17 | index/traceability/integration review | package references linked to one owner |
| `NFR-RIGHTS-01` | provenance, consent, disclosure, authorization | `F-GOV-01` | QG-02/QG-17 | ADV-013/014/015; human review | `safety-and-provenance.md` |

An NFR can be `DESIGN PASS` in Phase 0 while remaining unverified at runtime. The report must preserve that distinction.

## 6. Consistency invariants and unresolved questions

The integrated package must preserve these cross-document invariants:

- `LOCKED`, `FLEXIBLE`, `DERIVED`, and `IGNORE` retain the same meaning in contracts, Scene Bible, constraints, and fixtures; legacy `UNSPECIFIED` is only an alias.
- `UNKNOWN` capability is distinct from `UNSUPPORTED`, and neither is emitted as `SUPPORTED` without scoped evidence.
- `START_STATE → ACTION → END_STATE` and `STATE_DELTA` remain the continuity vocabulary across the state, scene, and shot documents.
- `FAST`, `CINEMATIC`, `PRODUCTION`, and `DIRECTOR` are derived depth labels, not separate reasoning engines.
- G-001 through G-012 refer to the same twelve fixtures in the golden owner, eval strategy, and report; ADV-001 through ADV-017 refer to the same red-team fixtures.
- Phase 0 documentation, `.agent/`/`.gauntlet/` process evidence, and future production Skill resources are separate scopes.
- Each collected `GenerationArtifact` references one immutable `ExecutionAttempt`; its content hash binds bytes to the attempt, and each `ArtifactObservation` records the hash seen during QA. A locator alone never identifies an output.

The remaining questions are not hidden in this matrix: blockers and non-blockers are canonical in [`open-questions.md`](open-questions.md), and any material contradiction discovered by review must become an ADR or a new question before implementation.

## 7. Related documents

The index and ownership table are in [`00-index.md`](00-index.md); requirements are in [`requirements.md`](requirements.md); gates and Phase 0 acceptance are in [`acceptance.md`](acceptance.md); current external evidence is in [`research.md`](research.md); and the final status handoff is in [`phase-0-report.md`](phase-0-report.md).

## 8. Phase 0 acceptance trace

This table keeps all 25 numbered acceptance items connected to an owner and a reviewable evidence path. `DESIGN PASS` means the requested documentation is present and structurally reviewable; it does not mean runtime or media evidence exists.

| ID | Canonical evidence | Review focus |
|---|---|---|
| P0-01 | `vision-and-scope.md`, `00-index.md` | problem, users, scope, and navigation |
| P0-02 | `requirements.md`, this matrix | stable IDs and end-to-end links |
| P0-03 | `architecture.md`, ADR-002/003 | pipeline and module ownership |
| P0-04 | `domain-model.md`, `contracts.md` | named entities and invariants |
| P0-05 | `state-model.md`, `continuity-engine.md` | state classes and transitions |
| P0-06 | `scene-and-continuity.md`, `contracts.md` | retention policies, conflicts, anchors |
| P0-07 | `directing.md` | dialogue/performance separation |
| P0-08 | `directing.md`, `constraints.md` | interaction/contact/motion decomposition |
| P0-09 | `directing.md` | cinematic and camera continuity |
| P0-10 | `directing.md`, `safety-boundaries.md` | audio/lip-sync and authorization |
| P0-11 | `model-adaptation.md`, `contracts.md` | canonical prompt view and mapping |
| P0-12 | `model-adaptation.md`, `research.md` | profile evidence and runtime limitation |
| P0-13 | `comfyui-execution.md` | plan/preflight/queue boundary |
| P0-14 | `scene-and-continuity.md`, `vision-and-scope.md` | 30/60/90/120-second policy |
| P0-15 | `failure-and-evals.md` | seven-field failure catalog |
| P0-16 | `acceptance.md` | rejectable gates and judgment classes |
| P0-17 | `failure-and-evals.md` | six evaluation categories and oracles |
| P0-18 | `golden-scenarios.md` | twelve complete golden fixtures |
| P0-19 | `adversarial-scenarios.md` | graceful ask/block/degrade/split/review |
| P0-20 | `progressive-disclosure.md` | conditional loading matrix |
| P0-21 | `proposed-skill-structure.md` | future package boundary, no implementation |
| P0-22 | `00-index.md`, `adr/` | ten major decision records |
| P0-23 | `open-questions.md` | blockers versus non-blockers |
| P0-24 | this matrix, integrated review record | no material contradiction remains |
| P0-25 | `00-index.md`, `phase-0-report.md`, scope audit | production boundary not crossed |
