# Acceptance and quality gates

The documentation baseline is accepted only when the system can explain what it knows, what it plans, what it cannot execute, and how a human can verify the result.

## Purpose and document contract

This document owns rejectable quality gates and Phase 0 acceptance, while [`contracts.md`](contracts.md) owns shared field semantics and [`traceability.md`](traceability.md) owns cross-document coverage. Each gate names its input, pass/fail evidence, judgment class, and repair route. Examples include the gate contracts, known-bad fixtures, and the 25-item matrix; missing evidence or a silent production artifact fails the phase. The quality rubric is package-level by design and does not duplicate domain definitions.

## Contents

- [Quality gates](#1-quality-gates)
- [Gate execution contracts](#gate-execution-contracts)
- [Judgment class by gate](#judgment-class-by-gate)
- [Documentation quality bar](#2-documentation-quality-bar)
- [Phase 0 acceptance matrix](#3-phase-0-acceptance-matrix)
- [Definition of done](#4-definition-of-done-for-this-phase)
- [Verification procedure](#5-verification-procedure)

## 1. Quality gates

| Gate | Blocking question | Minimum evidence |
|---|---|---|
| QG-01 Intent completeness | Is the desired outcome actionable? | actors, action, outcome, ambiguity record |
| QG-02 Reference mapping | Does every reference have a target and retention rule? | asset map and scope |
| QG-03 Narrative coherence | Do beats have cause, purpose, and state change? | beat graph and exit conditions |
| QG-04 Shot feasibility | Can each shot be represented within its complexity budget? | shot spec and routing decision |
| QG-05 Identity continuity | Are identity invariants carried and testable? | continuity state and retention matrix |
| QG-06 Spatial continuity | Are position, orientation, and screen direction coherent? | spatial state and camera axis |
| QG-07 Temporal continuity | Do action phases and object states advance causally? | state deltas and dependencies |
| QG-08 Physical plausibility | Can bodies, objects, forces, and contacts coexist? | interaction graph and risk treatment |
| QG-09 Interaction plausibility | Are contact, ownership, gaze, and reactions explicit? | interaction contract |
| QG-10 Dialogue coherence | Are speaker, listener, timing, and reaction resolved? | dialogue line contracts |
| QG-11 Performance coherence | Do behavior and emotion produce observable direction? | performance notes tied to actions |
| QG-12 Lip-sync feasibility | Is there a credible sync path for visible speech? | audio source and adapter capability |
| QG-13 Camera continuity | Does coverage preserve or motivate axis/movement changes? | camera sequence plan |
| QG-14 Audio-event coherence | Do audio events have declared causes/timing? | layered audio plan |
| QG-15 Model compatibility | Can the selected profile satisfy critical requirements? | capability profile and compatibility report |
| QG-16 Prompt ambiguity | Did compilation preserve meaning without unsupported claims? | canonical-to-compiled mapping |
| QG-17 Execution completeness | Can a human or authorized runtime execute and recover the plan? | workflow, inputs, preflight, fallback |

Critical gates are QG-01, QG-02, QG-05, QG-07, QG-08, QG-15, and QG-17. A project may waive a critical gate only with an explicit human decision and recorded reason.

### Gate execution contracts

| Gate | Purpose/input | Pass criteria | Fail example | Repair | Oracle |
|---|---|---|---|---|---|
| QG-01 | Normalize intent and unknowns | Objective, actors, actions, outcome, constraints, and material questions are explicit | “Make it cinematic” with no subject/action/outcome | Ask or label reversible assumption | structural/semantic |
| QG-02 | Map references and rights | Every asset has role, property scope, retention, provenance, and conflict status | Portrait silently used as vehicle geometry | Rebind, ask precedence, or block | structural/human |
| QG-03 | Check story causality | Beats have purpose, stimulus, action, reaction/response order, and exit state | Reaction occurs before its cause | Add processing beat or split | semantic/review |
| QG-04 | Check shot load | Complexity vector and dependencies fit selected profile/coverage | One shot contains dialogue, vehicle entry, drone, and product reveal | Split, reframe, or downgrade | structural/semantic |
| QG-05 | Check identity retention | Locked properties are carried, anchored, and observed where required | Face/wardrobe changes across dependent shots | Re-anchor, regenerate, or review | media/human |
| QG-06 | Check spatial geography | Positions, screen direction, eyelines, anchors, and axis are coherent | Character crosses room/axis without transition | Add bridge/reframe or declare intentional change | structural/review |
| QG-07 | Check temporal/state causality | State deltas explain every material transition | Door is open in next shot with no opening action | Add action/transition or split | structural/semantic |
| QG-08 | Check physical plausibility | Anatomy, contact, collision, force, articulation, and mechanics have a plausible path | Hand is near handle but door result is asserted | Add contact coverage, reframe, or block | semantic/media/human |
| QG-09 | Check interaction semantics | Participants, contact, ownership, gaze, and result are explicit | Object changes owner between cuts with no transfer | Add contact graph and transfer state | structural/review |
| QG-10 | Check dialogue coherence | Speaker/listener, interval, line, turn-taking, pause/overlap, and reaction are resolved | Listener mouths another speaker’s line | Reassign/split/voiceover | structural/review |
| QG-11 | Check performance direction | Emotion is observable through timed behavior tied to stimulus | “Be emotional” with no physical behavior | Add performance beat or human review | semantic/human |
| QG-12 | Check lip-sync path | Visible speech has speaker, audio source, timing, face visibility, and supported adapter | Native perfect lip-sync assumed from text-only profile | Separate audio/lip-sync or block | capability/media |
| QG-13 | Check camera continuity | Shot purpose, framing, axis, eyeline, lens feel, and movement phase agree | Camera crosses axis without motivation | Add motivation/reframe/accept intentional break | structural/review |
| QG-14 | Check audio-event coherence | Layers, causes, timing, room tone, and mix/assembly are explicit | Door sound occurs before visible latch with no intent | Re-time, replace, or mark non-diegetic | structural/media |
| QG-15 | Check model compatibility | Confirmed profile intersects critical mode, input, control, limit, and rights requirements | FLF workflow emitted for unknown end-frame support | Alternate profile, degrade, or block | deterministic/capability |
| QG-16 | Check prompt compilation | Canonical sections map to compiled view; omissions/changes are disclosed | Compiler drops identity or invents node capability | Repair mapping or return unresolved | structural/review |
| QG-17 | Check execution completeness | Inputs, graph/API, assets, parameters, auth, outputs, immutable attempt provenance, content hashes, fallback, and recovery are listed | Queue assumed ready without node/model preflight or a byte-to-attempt link | Preflight/repair/request authorization; stale-hash recollection when needed | deterministic/operator |

Every gate record includes `status`, `evidence`, `procedure`, `limitation`, and `repair_route`. `PASS` is unavailable for artifact-level criteria until the appropriate runtime/media/human observation exists. The observation aggregate follows [`contracts.md`](contracts.md): a required `PARTIAL`, `FAIL`, `BLOCKED`, or `NOT_RUN` prevents aggregate `PASS`; only a formal, scoped, time-bounded human waiver can exclude a required check. `PASS` therefore means every required check passed or was formally waived, not merely that an inspection was attempted. A collected `GenerationArtifact` is not QA evidence; it becomes acceptance-relevant only through its linked `ArtifactObservation`, whose content hash must match the collected artifact and immutable `ExecutionAttempt`. A path overwrite or missing attempt/provenance field is stale/non-acceptance evidence, while `NOT_RUN` remains non-evidentiary and does not regress the shot lifecycle.

### Judgment class by gate

The gate oracle is explicit about what can be deterministic in a future validator and what requires semantic, model-assisted, media, or human judgment:

| Gate | Judgment class |
|---|---|
| QG-01 | deterministic structural checks plus semantic clarification/review |
| QG-02 | deterministic mapping/provenance checks plus human rights review |
| QG-03 | semantic graph review; deterministic prerequisite checks |
| QG-04 | deterministic complexity/dependency checks plus model/profile feasibility |
| QG-05 | media comparison and human review for material identity decisions |
| QG-06 | deterministic state/axis checks plus frame/review oracle |
| QG-07 | deterministic state-delta and temporal-order checks |
| QG-08 | semantic/contact checks plus media or human plausibility review |
| QG-09 | deterministic contact/ownership fields plus media/review oracle |
| QG-10 | deterministic speaker/timing checks plus semantic/review oracle |
| QG-11 | semantic performance review and human judgment when quality is material |
| QG-12 | deterministic capability intersection plus media lip-sync review |
| QG-13 | deterministic camera-state checks plus sequence review |
| QG-14 | deterministic event/timestamp checks plus media mix review |
| QG-15 | deterministic profile/requirement intersection |
| QG-16 | deterministic canonical-to-compiled mapping plus semantic review |
| QG-17 | deterministic preflight/provenance checks plus authorized operator review |

## 2. Documentation quality bar

The quality rubric below is separate from the frozen Gauntlet criterion IDs (`DOC-001` through `DOC-030`) so that a local editorial rubric cannot silently redefine a required acceptance criterion.

| ID | Requirement |
|---|---|
| QUAL-001 | Every blueprint concept has a canonical owner document |
| QUAL-002 | Every executable claim has evidence status or a source |
| QUAL-003 | Unknown, proposed, and confirmed capability states are distinct |
| QUAL-004 | Contracts use stable IDs and explicit lifecycle/status values |
| QUAL-005 | Requirements map to acceptance gates and evaluation cases |
| QUAL-006 | Execution docs preserve plan/runtime/artifact boundaries |
| QUAL-007 | Non-goals and revalidation conditions are visible |

### Second documentation review checklist

An independent review must inspect the complete docs tree for these failure classes and record `PASS`, `PARTIAL`, or `FAIL` with a file/section pointer:

| Check | Reject when |
|---|---|
| Purpose and ownership | a document introduces a decision without naming its canonical owner |
| Terminology and invariants | a term, lifecycle, or state class changes meaning between owners |
| Evidence discipline | a mutable provider/model claim lacks source, date, applicability, confidence, or limitation |
| Requirement coverage | a requirement lacks an owner, gate, eval/review path, or future implementation target |
| Failure completeness | a central failure has no cause, detection, prevention, mitigation, repair, or eval |
| Scenario completeness | a golden/adversarial fixture omits its input, risk, expected behavior, or oracle |
| Overengineering | a file/module/pattern has no independent decision or fixture-backed value |
| Underspecification | a major boundary says what to do but not how to detect failure or repair it |
| Duplication and contradiction | two documents claim canonical ownership or disagree on a status/threshold |
| Progressive disclosure | a simple task would load specialist material without a material decision benefit |
| Safety and authorization | external effects, likeness, voice, private data, or provenance are assumed rather than gated |
| Phase boundary | a production Skill, executable adapter, workflow generator, or runtime mutation appears in Phase 0 |

This checklist is a review procedure, not a hidden reasoning transcript. It exposes evidence and decisions that a maintainer can verify.

## 3. Phase 0 acceptance matrix

| ID | Acceptance item | Owner/evidence | Required result |
|---|---|---|---|
| P0-01 | Problem and scope are unambiguous | `vision-and-scope.md`, `00-index.md` | PASS |
| P0-02 | Major requirements have stable IDs | `requirements.md`, `traceability.md` | PASS |
| P0-03 | Architecture is documented | `architecture.md` | PASS |
| P0-04 | Canonical domain model is documented | `domain-model.md`, `contracts.md` | PASS |
| P0-05 | State and continuity are explicit | `state-model.md`, `continuity-engine.md` | PASS |
| P0-06 | Reference retention is explicit | `scene-and-continuity.md`, `contracts.md` | PASS |
| P0-07 | Dialogue/performance architecture is explicit | `directing.md` | PASS |
| P0-08 | Interaction/motion architecture is explicit | `directing.md`, `constraints.md` | PASS |
| P0-09 | Cinematography architecture is explicit | `directing.md` | PASS |
| P0-10 | Audio/lip-sync architecture is explicit | `directing.md`, `safety-boundaries.md` | PASS |
| P0-11 | Prompt compilation architecture is explicit | `model-adaptation.md`, `contracts.md` | PASS |
| P0-12 | Model adapter contract is explicit | `model-adaptation.md`, `research.md` | PASS with runtime limitation |
| P0-13 | ComfyUI execution-planning boundary is explicit | `comfyui-execution.md` | PASS with runtime limitation |
| P0-14 | Long-form strategy is documented | `scene-and-continuity.md`, `vision-and-scope.md` | PASS |
| P0-15 | Failure taxonomy exists | `failure-and-evals.md` | PASS |
| P0-16 | Quality gates exist | this document | PASS |
| P0-17 | Eval strategy exists | `failure-and-evals.md` | PASS |
| P0-18 | Golden scenarios exist | `golden-scenarios.md` | PASS |
| P0-19 | Adversarial scenarios exist | `adversarial-scenarios.md` | PASS |
| P0-20 | Progressive disclosure strategy exists | `progressive-disclosure.md` | PASS |
| P0-21 | Historical package-shape rationale exists and matches the authorized package | `proposed-skill-structure.md`, ADR-011 | PASS, package implementation verified separately |
| P0-22 | Major choices have ADRs | `adr/`, `00-index.md` | PASS |
| P0-23 | Open questions are explicit | `open-questions.md` | PASS |
| P0-24 | No material contradictory architecture remains | `traceability.md`, integration/final critics | PASS or CONDITIONAL PASS |
| P0-25 | No production Skill started prematurely | scope/file audit | PASS |

The acceptance matrix is a Phase 0 design gate. It does not turn a source-backed plan into proof of generated media quality.

The `Required result` column states the intended static-design outcome. The executed verdict, limitations, and not-run runtime/media checks belong in [`phase-0-report.md`](phase-0-report.md) after integration and the final independent critic.

## 4. Definition of done for this phase

This documentation phase is complete when:

- the blueprint is preserved verbatim at `docs/BLUEPRINT.md`;
- the numbered docs index, scope, requirements, architecture, domain/state, contracts, scene, continuity, directing, constraints, adaptation, execution, pattern, research, golden, adversarial, eval, acceptance, traceability, observability, safety, progressive-disclosure, future structure, open questions, roadmap, report, and ADR documents exist;
- all requirements are mapped to at least one owner and one gate;
- all major assumptions are marked confirmed, inferred, proposed, unknown, or pending;
- internal links and referenced IDs resolve;
- examples are syntactically valid YAML where presented as YAML;
- no external paid call, upload, or unrequested mutation has been performed in the Phase 0 evidence; the separately authorized package and bounded local execution are recorded in `IMPLEMENTATION.md`;
- the next implementation gate and remaining risks are explicit.

## 5. Verification procedure

The phase verification is a bounded static audit:

1. enumerate all documents and compare the index against the filesystem;
2. parse YAML examples with a safe parser, or mark non-YAML snippets as pseudocode;
3. extract requirement, gate, source, and evaluation IDs;
4. verify every requirement has an owner, a gate, and an evaluation path or an explicit reason;
5. verify all local Markdown links point to existing files;
6. verify `docs/BLUEPRINT.md` remains byte-for-byte identical to the supplied attachment;
7. inspect the final diff and record commands/results in `.agent/verification.jsonl`.

The audit cannot prove actual model quality or runtime compatibility. Those require later dry runs and artifact-level evaluation.

## Open questions and related documents

The acceptance owner does not choose domain semantics or provider capabilities. Remaining tolerances, runtime targets, and approval roles are tracked in [`open-questions.md`](open-questions.md); the canonical ownership/navigation map is [`00-index.md`](00-index.md); and the integrated requirement chain is [`traceability.md`](traceability.md). A failure in this document routes to the smallest owner rather than being waived by a generic status.
