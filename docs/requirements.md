# Product requirements

## Outcome

Given a high-level creative request and any supplied references, the Skill must produce an honest, structured, executable generative-video production plan. The plan must make narrative intent, entities, temporal beats, shot boundaries, continuity state, interaction mechanics, camera language, sound requirements, model/runtime capabilities, and verification obligations explicit before compiling model prompts.

The output is useful when a creator can understand the intended film, an operator can identify the required ComfyUI/model workflow, and a reviewer can verify whether each critical requirement was preserved in the generated artifacts.

## Document contract

This document owns normative product meaning and requirement IDs. `MUST`, `SHOULD`, and `MAY` are the decision vocabulary; the invariant is that unknowns, causal state, evidence, rights, and authorization are never silently promoted. Examples and failure interpretations appear in the acceptance and failure-policy sections; a missing owner, gate, eval path, or limitation is a requirements failure. Representation details belong to the linked canonical contracts, so this document does not create duplicate schemas.

## Contents

- [Users and use cases](#users-and-use-cases)
- [Functional requirements](#functional-requirements)
- [Non-goals](#non-goals)
- [Quality attributes](#quality-attributes)
- [Product acceptance](#product-acceptance)
- [Requirement interpretation and failure policy](#requirement-interpretation-and-failure-policy)
- [Open questions and related documents](#open-questions-and-related-documents)

## Users and use cases

| User | Need | Observable outcome |
| --- | --- | --- |
| Creator/director | Turn an idea into a coherent production design | A scene plan with beats, shots, camera, performance, sound, and references |
| ComfyUI operator | Know which workflow and inputs are needed | A capability-resolved execution plan with no invented nodes or model features |
| Editor/reviewer | Detect drift and choose what to regenerate | Per-shot acceptance criteria, continuity state, artifact observations, and repair actions |
| Skill maintainer | Extend support without destabilizing the core | Versioned adapters and references with evidence and explicit unsupported states |

## Functional requirements

### Normative levels

- `MUST` is release-blocking for the Skill or for the Phase 0 documentation gate.
- `SHOULD` is the default behavior unless a documented capability, cost, or human decision justifies a deviation.
- `MAY` is an optional extension that must not weaken a `MUST` invariant.

The existing functional requirements below are intentionally `MUST` requirements. Optional model features, runtime automation, and specialist pattern selection are expressed as `SHOULD`/`MAY` in their owning documents and never as assumed capability.

### Intake and intent

- **R-INT-01** The system MUST normalize creative intent into an explicit object containing objective, duration target, platform/output assumptions, subjects, objects, environment, actions, style, camera, dialogue, audio, references, hard constraints, preferences, and unresolved questions.
- **R-INT-02** The system MUST distinguish hard constraints from preferences and MUST preserve unknowns instead of silently filling material gaps.
- **R-INT-03** The system MUST identify prerequisites and causal order before writing shot prompts.
- **R-INT-04** The system MUST ask for clarification only when the missing choice changes safety, rights, product meaning, architecture, or the executable plan; otherwise it may use a reversible, labelled assumption.

### Reference analysis and retention

- **R-REF-01** The system MUST inventory each reference asset and map it to the entities or properties it is intended to inform.
- **R-REF-02** The system MUST classify retention per property as `LOCKED`, `FLEXIBLE`, `DERIVED`, or `IGNORE`, with rationale and evidence.
- **R-REF-03** The system MUST distinguish identity anchors from aesthetic/compositional references and MUST identify conflicts and precedence.
- **R-REF-04** The system MUST treat a retention lock as a target and QA obligation, not as a model guarantee; actual preservation requires artifact observation.
- **R-GOV-01** When likeness, voice, brand, or restricted media is involved, the system MUST surface provenance/consent requirements and a human review boundary.

### Complexity and narrative planning

- **R-PLAN-01** The system MUST classify complexity across identities, references, dialogue, lip-sync, interaction, articulated objects, motion, camera, duration, and VFX.
- **R-PLAN-02** The system MUST route planning depth using the complexity vector and dependency graph. Duration thresholds are normative minimum-structure floors, not the sole routing signal; complexity or dependency risk MUST be allowed to escalate planning earlier.
- **R-PLAN-03** The system MUST produce a narrative timeline for long-form or high-dependency work before shot compilation.
- **R-PLAN-04** The story plan MUST represent stimulus → reaction → response and MUST avoid premature reactions.
- **R-PLAN-05** The story plan MUST avoid overloading a shot with unrelated concurrent actions and MUST decompose action-heavy beats.
- **R-PLAN-06** The prepared plan MUST emit a deterministic progressive-disclosure route with package-relative references, inclusion reasons, explicit exclusions, and a limitation that route output is not proof of context loading.

### Canonical scene model

- **R-SCENE-01** The system MUST create a model-independent Scene Representation before prompt compilation.
- **R-SCENE-02** Complex work MUST create a Scene Bible containing immutable identity traits, wardrobe, objects, environment, lighting, geography, camera language, audio/voice identity, relationships, continuity rules, and prohibited drift.
- **R-SCENE-03** Permanent entity identity state MUST be represented separately from transient pose, position, gaze, emotion, occupancy, and action state.
- **R-SCENE-04** Relationships MUST include speaker/listener, attention, social intent, distance, and emotional response where multiple entities interact.
- **R-SCENE-05** World state MUST preserve geometry, spatial anchors, lighting direction, time, weather, depth, horizon, and recurring background objects unless a deliberate transition changes them.

### Shots, state, and continuity

- **R-SHOT-01** Each shot MUST define ID, duration, narrative purpose, start state, end state, active subject, actions, interactions, dialogue, camera, lighting, audio, required references, generation mode, dependencies, risk, and constraints.
- **R-SHOT-02** Shots MUST form a dependency graph whose edges carry relevant state deltas and required anchors.
- **R-SHOT-03** A shot MUST NOT silently contradict an inherited object, vehicle, subject, environment, lighting, camera, emotional, dialogue, audio, or temporal state.
- **R-SHOT-04** The system MUST distinguish planned state from observed artifact state and MUST route discrepancies to repair or human review.
- **R-SHOT-05** The system MUST recommend an anchor strategy per shot and MUST identify when a previous last frame is insufficient.
- **R-SHOT-06** First/last-frame chaining MUST be conditional on a confirmed capability and MUST include endpoint validation, reset strategy, and degradation risk.
- **R-SHOT-07** Long-form generation MUST be assembled from shots or model-supported extensions; it MUST NOT be represented as one unbounded prompt.

### Direction and performance

- **R-DIR-01** The system MUST translate high-level actions into physically plausible motion primitives with timing, acceleration/deceleration, balance, gravity, and object mechanics.
- **R-DIR-02** Human/object/vehicle/animal interactions MUST be decomposed into contacts, articulation, collision, and end-state checkpoints when the action is physically sensitive.
- **R-DIR-03** Dialogue lines MUST include speaker, listener, intention, delivery, emotion, gaze, duration, pause/overlap rules, and reaction timing.
- **R-DIR-04** Only the active speaker may perform sustained speech articulation for a line; listeners may react without silently mouthing the line.
- **R-DIR-05** Camera choices MUST serve narrative purpose and MUST track screen direction, eye-line, camera side, focal intent, and movement continuity.
- **R-DIR-06** Audio MUST be represented as timed layers and visible events MUST have corresponding sound events where relevant.
- **R-DIR-07** The system MUST express physical, anatomy, interaction, or cinematic requirements as either generation guidance, runtime control, or QA assertion; it MUST not imply that prose alone enforces them.

### Constraints and prompt compilation

- **R-CON-01** The constraint engine MUST select constraints from actual scene risks rather than emit a universal negative list.
- **R-CON-02** Constraint precedence MUST be explicit: safety/rights, hard intent, identity/geometry retention, continuity, physical plausibility, cinematic preferences, then optional style.
- **R-CON-03** The canonical output MUST remain compatible with the conceptual sections `subject_definitions`, `environment_definitions`, `summary`, `retention_analysis`, `detailed_description`, `global_physical_constraints`, `cinematography`, `overall_soundscape`, and `negative_constraints`.
- **R-CON-04** The Prompt Compiler MUST consume the canonical plan and emit a model-specific representation without changing intent or inventing capability.

### Model adaptation and execution

- **R-ADP-01** The core MUST remain model-agnostic; model-specific syntax and limitations MUST live in versioned profiles.
- **R-ADP-02** A profile MUST identify supported modes, input/output limits, reference behavior, audio behavior, camera controls, duration/resolution, dependencies, failure modes, evidence, and validity date.
- **R-ADP-03** Capability claims MUST be `CONFIRMED`, `INFERRED`, `PROPOSED`, or `UNKNOWN` and MUST cite a source or executable probe.
- **R-ADP-04** The adapter MUST compute the intersection of shot requirements and confirmed runtime capabilities and MUST return `SUPPORTED`, `DEGRADED`, or `BLOCKED` with reasons.
- **R-ADP-05** If a requested capability is not confirmed, the system MUST preserve the requested intent, disclose the gap, and propose a safe fallback or human decision.
- **R-EXE-01** The ComfyUI execution planner MUST describe a graph/workflow strategy, inputs, model assets, node dependencies, parameters, outputs, and verification without assuming that a graph is installed or executable.
- **R-EXE-02** The planner MUST support T2V, I2V, first/last-frame, reference conditioning, audio-driven, assembly, and post-processing only when a profile confirms them.
- **R-EXE-03** The planner MUST not store credentials, invoke paid APIs, upload references, or mutate external state without explicit user authorization and a supported tool boundary.
- **R-EXE-04** Execution artifacts MUST retain model/profile version, workflow identity, inputs, seeds/parameters when available, and output provenance.
- **R-EXE-05** A local ComfyUI plan MUST account for version, node availability, model files, VRAM/resource limits, frame constraints, and output encoding.
- **R-EXE-06** Final assembly MUST verify duration, frame rate, video/audio alignment, codec/container, and required provenance metadata before acceptance.

### Quality, evals, and repair

- **R-QA-01** The system MUST run or describe quality gates for intent, references, narrative, shots, identity, space, time, physics, interaction, dialogue, performance, lip-sync, camera, audio, model compatibility, prompt ambiguity, and execution completeness.
- **R-QA-02** A failed gate MUST produce detect → explain → repair → re-evaluate → compile behavior.
- **R-QA-03** Evals MUST observe behavior and invariants rather than exact headings, wording, or arbitrary negative-prompt counts.
- **R-QA-04** Evals MUST include known-bad cases that fail when a central invariant is violated.
- **R-QA-05** The system MUST distinguish generation acceptance from editorial acceptance and MUST record limitations when a visual/audio judgment remains manual.
- **R-QA-06** A final production package MUST include the scene plan, shot graph, continuity map, references, adapter plan, prompts, execution instructions, assembly plan, and validation checklist.

### Long-form and modes

Here `t` is the real-valued target duration in seconds; the supported planning scope is `0 < t ≤ 120`, so fractional durations use the same continuous boundaries as integer durations.

- **R-LONG-01** For `0 < t ≤ 30`, the system MUST still record shot purpose and state at material boundaries, but no duration-only long-form structure is required. For `30 < t ≤ 45`, it MUST add a narrative timeline. For `45 < t < 60`, it MUST additionally add a Scene Bible, shot graph, and explicit `PLANNED` state propagation.
- **R-LONG-02** For `60 ≤ t < 90`, the system MUST retain the preceding structures and add reference and dialogue/audio timelines when applicable, a generation strategy, and an assembly plan. For `90 ≤ t ≤ 120`, it MUST additionally expose alternative branches, recovery checkpoints, a provenance/assembly manifest and human checkpoints. A static scene may use one-node/minimal forms of those structures, but it may not waive the applicable duration floor.
- **R-LONG-03** Long-form strategy MUST support periodic canonical re-anchoring and must not rely on unbounded recursive frame propagation.
- **R-LONG-04** FAST, CINEMATIC, PRODUCTION, and DIRECTOR are presentation/depth policies, not separate reasoning engines; the planner may retain them only as derived labels.

### Phase 0 documentation and governance

- **R-DOC-01** The Phase 0 package MUST have a numbered navigation hub that states source hierarchy, document ownership, deviations from any suggested tree, unresolved decisions, ADRs, and implementation readiness.
- **R-DOC-02** The package MUST document the canonical domain entities, state classes, lifecycles, relationships, and invariants required by the master prompt without introducing abstractions that own no decision.
- **R-DOC-03** The package MUST fully specify the twelve required golden scenarios with input intent, references, risk, expected decisions, continuity, decomposition, constraints, output class, and failure conditions.
- **R-DOC-04** The package MUST include adversarial scenarios for ambiguity, conflicting references, impossible motion/camera, overloaded action, identity/vehicle inconsistency, unsupported capabilities, and excessive subjects, with graceful expected behavior.
- **R-DOC-05** The package MUST define concise decision observability and modular safety/authorization boundaries without exposing hidden reasoning or inventing provider policy.
- **R-DOC-06** Major architectural choices MUST have ADRs with context, alternatives, consequences, risks, and validation evidence; remaining decisions MUST be listed as blockers or non-blockers.
- **R-DOC-07** Traceability MUST connect user goal → requirement → architecture component → failure mode → quality gate → eval → future implementation component.
- **R-DOC-08** The final Phase 0 report MUST state architecture status, created documentation, blueprint changes, critical risks, open questions, proposed Skill structure, Phase 1 readiness, and the explicit stop point.

## Non-goals

The first production version is not:

- a video editor or non-linear editing system;
- a renderer, model-training system, or ComfyUI replacement;
- a generic screenplay-writing system;
- a voice-cloning framework or identity-verification service;
- a guarantee that a stochastic model will satisfy every plan constraint;
- an automatic external executor by default;
- a universal model benchmark or provider recommendation engine.

## Quality attributes

Each quality attribute is a non-functional requirement with a stable ID, an explicit normative level, and a rejectable review target:

| ID | Level | Attribute | Rejectable target |
|---|---|---|---|
| NFR-TRUTH-01 | MUST | Truthfulness | No unsupported capability or unobserved artifact property is presented as fact |
| NFR-COHERENCE-01 | MUST | Coherence | Causal, spatial, temporal, identity, emotional, and audio relationships remain explicit across shots |
| NFR-ACTION-01 | MUST | Actionability | An operator can identify inputs, workflow family, unresolved prerequisites, and outputs |
| NFR-REPAIR-01 | MUST | Repairability | A failed check points to a specific state, shot, constraint, or adapter decision |
| NFR-MAINT-01 | SHOULD | Maintainability | A maintainer can update one owner/profile without searching for hidden duplicate rules |
| NFR-CONTEXT-01 | SHOULD | Context efficiency | Simple scenes load concise guidance; specialist references load only when a decision needs them |
| NFR-DET-01 | SHOULD | Determinism | Repeated structural planning with the same versioned inputs yields stable IDs, routing, and gate results |
| NFR-EXT-01 | SHOULD | Extensibility | A new model adds a versioned profile without changing canonical scene/state semantics |
| NFR-EXPL-01 | MUST | Explainability | User-facing diagnostics expose concise reasons, evidence, alternatives, limitations, and next action without hidden reasoning dumps |
| NFR-TEST-01 | MUST | Testability | Each invariant has a structural, semantic, runtime, media, or human-review procedure and an oracle class |
| NFR-DEGRADE-01 | MUST | Graceful degradation | Unsupported or unknown capability produces an explicit fallback, `DEGRADED`, `BLOCKED`, or human decision |
| NFR-DUP-01 | SHOULD | Low duplication | Each mutable decision has one canonical owner and dependent documents link to it |
| NFR-RIGHTS-01 | MUST | Rights awareness | Likeness, voice, brand, private data, reference provenance, and authorization are surfaced before external execution |

## Product acceptance

The requirements are accepted only when the documentation package maps each requirement to a canonical owner and an observable eval or review procedure. See [`acceptance.md`](acceptance.md) and [`traceability.md`](traceability.md).

## Requirement interpretation and failure policy

The requirements are normative behavior targets for the Skill; they are not, by themselves, implementation evidence. Current scoped implementation evidence is in [IMPLEMENTATION.md](../IMPLEMENTATION.md). The most important invariants are preservation of unknowns, explicit causal/state transitions, model-independent canonical data, risk-shaped constraints, and fail-closed execution boundaries. Typical failures are an ambiguous intake, a missing state delta, a transitive capability claim, or an artifact accepted without observation; each must produce a named gate result and repair route rather than a polished generic prompt.

## Open questions and related documents

Open implementation choices are classified in [`open-questions.md`](open-questions.md). The canonical entity/state contracts are in [`domain-model.md`](domain-model.md), [`state-model.md`](state-model.md), and [`contracts.md`](contracts.md); requirement-to-gate/eval coverage is in [`traceability.md`](traceability.md). This document owns requirement meaning, while those documents own implementation-facing representations.
