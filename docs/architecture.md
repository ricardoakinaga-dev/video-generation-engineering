# Target architecture

## Purpose

Define the smallest set of logical responsibilities that can turn creative intent into an honest, continuity-aware, model-adapted video production plan. This remains the target architecture source; the current executable subset and its boundaries are implemented separately in [`.agents/skills/video-generation-engineering`](../.agents/skills/video-generation-engineering/SKILL.md).

## Terminology

- `ScenePlan` is the model-independent planned representation.
- `ShotGraph` records causal/dependency edges between shots.
- `ContinuityState` is one inherited or observed state record; `ContinuityLedger` is the collection that carries those records across edges.
- `CapabilityProfile` describes one concrete model/runtime integration.
- `CanonicalPromptView` is the model-independent compiled projection; `CompiledPrompt` is an adapter-specific derived form.
- `ExecutionPlan` is an authorized-or-plan-only handoff; it is not a queued job.
- `ExecutionAttempt` is the immutable record of one concrete runtime submission; retries are separate attempts.

## Contents

- [Architectural position](#architectural-position)
- [Pipeline](#pipeline)
- [Layers and ownership](#layers-and-ownership)
- [Module map](#module-map)
- [Boundary contracts](#boundary-contracts)
- [Three truth domains](#three-truth-domains)
- [Planning depth](#planning-depth)
- [Progressive disclosure](#progressive-disclosure)
- [Design decisions](#design-decisions)
- [Example handoff](#example-handoff)
- [Failure modes and repair routes](#failure-modes-and-repair-routes)

## Architectural position

`video-generation-engineering-vNext` is an instruction-led planning system. Its durable intelligence is the model-independent scene representation and the state/verification discipline around it. Prompt text is compiled late, and execution is an optional adapter boundary.

The architecture is deliberately smaller than the blueprint's vocabulary. The blueprint names many concerns that must be reasoned about; it does not require one service, agent, class, or file per concern. A module is justified only when it owns a stable decision, changes independently, or requires a distinct evidence boundary.

## Pipeline

```text
creative request + references
              │
              ▼
       Intent Normalizer
              │ normalized intent
              ▼
    Reference + Complexity Analysis
              │ retention matrix + risk vector
              ▼
       Scene Planning Core
    ┌─────────┼──────────┐
    ▼         ▼          ▼
 Scene Bible  Story/Time  World/Entities
    └─────────┼──────────┘
              │ canonical scene plan
              ▼
         Shot Graph + State Ledger
              │ shot contract + anchors
              ▼
      Direction and Constraint Layer
              │ shot intent
              ▼
        Capability Negotiator
              │ supported/degraded/blocked
              ▼
          Prompt Compiler
              │ canonical + adapted view
              ▼
       ComfyUI Execution Planner
              │ plan + optional operator/external action
              ▼
       ExecutionAttempt → GenerationArtifact
              │ collected bytes + provenance
              ▼
     ArtifactObservation + QA Gates
              │ repair or acceptance
              └───────────────┘
```

The return edge is selective. A failed artifact observation repairs the smallest owning layer: prompt/constraint for ambiguity, shot plan for overload, continuity for contradiction, reference plan for drift, or adapter plan for capability mismatch. It does not rewrite the user's intent silently.

## Layers and ownership

| Layer | Owns | Produces | Does not own |
| --- | --- | --- | --- |
| Intent | Creative goal, constraints, preferences, unknowns | `SceneIntent` | Model syntax or workflow nodes |
| Reference | Asset classification, property retention, conflicts, anchors | `ReferencePlan` | Actual identity preservation |
| Complexity | Risk vector and required planning depth | `ComplexityAssessment` | Narrative content |
| Scene planning | Entities, world, relationships, timeline, causality | `ScenePlan`/`SceneBible` | Provider capability |
| Shot/state | Shot boundaries, dependencies, state deltas, inherited state | `ShotGraph`/`ContinuityState[]` | Prompt prose as truth |
| Direction | Story beats, performance, interaction, motion, camera, audio | `ShotDirection` | Model execution |
| Constraints | Scene-aware controls and QA assertions | `ConstraintSet` | Universal negative prompts |
| Adapter | Capability evidence, model-specific compilation | `AdapterPlan` | Core narrative decisions |
| Execution | Workflow, operator instructions, and immutable attempt provenance | `ExecutionPlan` / `ExecutionAttempt` | Automatic external side effects by default |
| Verification | Artifact observations, gates, repair route | `QualityReport` | Predicted success |

## Module map

The following modules are logical responsibilities, not a required runtime decomposition.

| Logical module | Canonical input | Canonical output | Trigger |
| --- | --- | --- | --- |
| Intent Parser | User request, attachments, answers | `SceneIntent` | Always |
| Reference Analyzer | `SceneIntent.references` | `ReferencePlan` | Any reference or identity-sensitive request |
| Complexity Analyzer | Intent, reference count, action graph | `ComplexityAssessment` | Always; depth varies |
| Scene Planner | Intent, reference plan, complexity | `ScenePlan` | Any non-trivial scene |
| Scene Bible Manager | Scene plan | `SceneBible` | Multi-shot, recurring entity, or long-form work |
| Story Engine | Intent, timeline target | `NarrativeBeat[]` | Narrative or action request |
| Entity/World Engine | References, scene plan | entity/world definitions | Any entity or environment |
| Dialogue/Performance Director | Beats, speakers, voice/audio requirements | dialogue/performance tracks | Dialogue, singing, or expressive acting |
| Interaction/Motion Director | Actions, contact graph, world geometry | motion/contact plans | Physical interaction or articulated object |
| Shot Planner | Beats, direction, complexity | `ShotGraph` | Always after narrative planning |
| Continuity Engine | Shot graph, prior observations | state inheritance and anchors | Any dependent shot; mandatory for long-form |
| Cinematography Director | Narrative purpose, world, continuity | camera plan | Any visual generation; depth varies |
| Audio Director | Dialogue, events, environment | audio timeline | Audio requested or visible events need sound |
| Constraint Engine | Risk vector, shot plan, profile | selected constraints | Before compilation |
| Prompt Compiler | Canonical plan, constraints | `CanonicalPromptView` | Last model-independent stage |
| Model Adapter | `CanonicalPromptView`, capability registry | adapted prompt/execution inputs | Selected target model/runtime |
| ComfyUI Planner | Adapter plan, local/runtime facts | workflow recipe | ComfyUI target |
| Execution Recorder | Authorized submission and runtime result | `ExecutionAttempt` | When a runtime submission starts; every retry is distinct |
| Quality Gate Runner | Plan, artifacts, observations | quality report and repair route | Before acceptance and after generation |

## Boundary contracts

Every handoff must include:

- stable `project_id`, `scene_id`, and version;
- source references and evidence status for material claims;
- required inputs and explicit unknowns;
- output object and owner;
- failure status with a repair route;
- whether the output is intended state, planned state, capability evidence, or observed artifact state.

The full field contracts live in [`contracts.md`](contracts.md). A module may enrich an object but may not silently change its semantics or erase an unknown.

## Three truth domains

The architecture prevents a common category error by using three domains:

1. **Desired truth** — what the creator wants: intent, hard constraints, aesthetic preferences, and retention goals.
2. **Planned truth** — how the production plan represents that desire: scene state, shot state, prompts, workflow, and expected outputs.
3. **Observed truth** — what the runtime/artifact actually shows: available nodes, generated media, audio alignment, visual review, and provenance.

Only observed truth can support an artifact acceptance claim. A plan may be internally coherent and still fail in generation. An `ExecutionAttempt` records the concrete runtime context, a collected `GenerationArtifact` proves collection and binds the output bytes to that attempt, and the linked `ArtifactObservation` records the executed QA result and the bytes inspected. A generated artifact may look plausible while violating a locked identity or a causal requirement. Both facts must be retained.

## Planning depth

The future Skill may expose four labels, but they are derived presentation policies:

| Derived label | Minimum behavior |
| --- | --- |
| `FAST` | Normalize intent, identify material unknowns, produce one-shot plan when risk is low |
| `CINEMATIC` | Add shot purpose, camera language, visual rhythm, lighting, and sound direction |
| `PRODUCTION` | Add references, shot graph, continuity ledger, execution plan, and QA checklist |
| `DIRECTOR` | Add narrative/audio timelines, state propagation, repair loops, assembly, and long-form controls |

The label cannot lower a requirement imposed by complexity, risk, or the duration floors in [`requirements.md`](requirements.md). A short vehicle interaction may require `PRODUCTION`; a long static panorama may remain `CINEMATIC` as a presentation label, but at `45 < t < 60` it still receives the required minimal Scene Bible, shot graph, and planned propagation, and at `t ≥ 60` it also receives the applicable assembly records.

## Progressive disclosure

The future package should use the following routing:

```text
Layer 1: concise skill metadata and trigger boundary
Layer 2: SKILL.md orchestration and core invariants
Layer 3: shared scene/continuity/quality references
Layer 4: conditional references (dialogue, vehicle, animal, audio, long-form)
Layer 5: target-model profile and ComfyUI workflow guidance
Layer 6: deterministic helpers and templates only when proven useful
```

The initial Skill catalog description must be concise and scoped. The full instruction file should route to references rather than carry all cinematography, model, and failure knowledge. The official [Build skills documentation](https://developers.openai.com/codex/skills/) confirms the package shape and that selected Skills load the full `SKILL.md`; this design preserves that boundary.

## Design decisions

| ID | Decision | Rejected alternative | Consequence |
| --- | --- | --- | --- |
| AD-001 | Canonical scene model before prompts | Prompt as intelligence layer | More structured planning, less prompt-only ambiguity |
| AD-002 | Model-independent core plus versioned adapters | Hard-code one model | Adapters require evidence and maintenance |
| AD-003 | Intended/planned/observed state are separate | Treat plan as proof | QA must inspect actual artifacts |
| AD-004 | Shot graph with state deltas | Flat shot list | Dependency and contradiction checks become possible |
| AD-005 | Complexity vector and graph routing | Duration-only thresholds | Short high-risk scenes escalate |
| AD-006 | Audio timeline is separable | Assume native audiovisual generation | Silent + external audio is a valid plan |
| AD-007 | Runtime capability negotiation | Emit nodes from model name | Unsupported workflows fail closed |
| AD-008 | Human gate for rights and external effects | Automatic execution/likeness use | Consent and authorization remain explicit |
| AD-009 | Failure repair targets smallest owner | Rewrite entire prompt blindly | Repairs are explainable and less destructive |
| AD-010 | Pattern library is evidence-driven | Pre-populate every pattern | Avoids speculative package bloat |

## Extensibility rules

Adding a new model or workflow must not require changing `SceneIntent`, `ScenePlan`, or continuity semantics unless the new capability reveals a genuine domain requirement. A profile may add syntax, limits, controls, failure modes, and evidence, but it may not reinterpret `LOCKED`, `speaker`, `start_state`, `end_state`, or observed QA.

Adding a pattern requires at least one golden case, a documented reusable invariant, a failure mode it reduces, and an eval or review procedure. Otherwise it remains an example, not a library primitive.

## Human and external boundary

The future Skill may prepare an execution plan automatically. It must stop before any material external effect that has not been explicitly authorized: uploading personal/reference media, calling paid services, invoking a ComfyUI server, cloning or synthesizing a real person's voice/likeness, publishing content, or deleting/regenerating user artifacts. Safe inspection and local plan generation may continue around that boundary.

## Example handoff

For a person entering a reference-locked vehicle, the intent layer records the goal and hard identity requirement; the Scene Bible owns the person, vehicle, and geography; the shot/state layer splits approach, contact, entry, and driving; the constraint layer selects hand-handle, door-articulation, wheel/road, and identity checks; the adapter reports whether the selected profile can accept the required references; and the execution layer ends in a plan-only workflow with preflight and repair routes. No prompt section is allowed to replace those records.

## Failure modes and repair routes

| Failure | Detection | Smallest owning repair |
|---|---|---|
| Prompt is used as the only scene model | missing entities/state/ownership records | scene/contracts owner |
| One shot is overloaded | complexity vector exceeds profile/coverage budget | story/shot planner |
| Capability is inferred from a model name | no scoped evidence or profile date | adapter/research owner |
| Artifact is treated as proof of the plan | no observed-state record, immutable attempt link, or content-hash match | verification/observability owner |
| External action happens without authority | execution mode or authorization is absent | safety/execution boundary |

## Open questions and related documents

The main unresolved architecture choices are the first executable runtime, artifact-level oracles, and the boundary between static routing and dynamic Skill reasoning. They are recorded in [`open-questions.md`](open-questions.md). Contracts and invariants are canonical in [`contracts.md`](contracts.md); quality gates are in [`acceptance.md`](acceptance.md); future package routing is in [`progressive-disclosure.md`](progressive-disclosure.md) and [`proposed-skill-structure.md`](proposed-skill-structure.md).
