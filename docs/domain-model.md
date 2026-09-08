# Canonical domain model

## Purpose

Define the smallest set of entities that own stable decisions, state, relationships, or evidence. The model is canonical before any prompt, node graph, or provider syntax.

## Modeling vocabulary

- **Entity:** a stable identified thing in the project or evidence system.
- **State:** a property whose value changes or is carried across time.
- **Relation:** a typed edge between entities, often with validity and direction.
- **Artifact:** an observed output or input object, never merely a path string.
- **Profile:** versioned capability evidence for a concrete model/runtime integration.

## Entity catalogue

| Entity | Responsibility | Required fields | Lifecycle | Key relations/invariants |
|---|---|---|---|---|
| `Project` | Owns delivery intent and review scope | `project_id`, title, owner, status | intake → accepted/aborted | Scenes belong to one project |
| `Scene` | Bounded dramatic/visual unit | `scene_id`, objective, timebase | planned → assembled | References one Scene Bible when required |
| `Subject` | General visible participant | `subject_id`, type, role | introduced → retired | Parent for character/animal when useful |
| `Character` | Human identity and performance state | identity, wardrobe, objective | introduced → recurring/retired | Identity is separate from pose and emotion |
| `Animal` | Animal identity and behavior | species, anatomy, temperament | introduced → active/retired | Species constraints are explicit |
| `Object` | Prop or articulated item | geometry, state, owner | introduced → used/retired | State transitions need a cause |
| `Vehicle` | Vehicle geometry and mechanics | model/shape, wheels, controls | introduced → moving/stopped | Geometry is separate from door/wheel state |
| `Environment` | World geometry and conditions | anchors, lighting, weather, time | established → transitioned | Recurring anchors persist unless changed |
| `Reference` | Input evidence or creative guide | locator/hash, kind, provenance | received → approved/restricted | Maps to properties, not “everything” |
| `ReferenceAnchor` | Reusable identity/world checkpoint | anchor ID, source artifact, scope | created → superseded | Must state what it anchors |
| `DialogueLine` | Scripted utterance and timing | speaker, text, listener, interval | drafted → voiced/accepted | One active speaker per interval by default |
| `PerformanceBeat` | Observable behavior/emotional change | actor, stimulus, reaction, timing | planned → observed | Reaction follows stimulus/processing |
| `Interaction` | Intentional relation/action between participants | actors, target, phases | planned → observed | Contact/ownership/end state for physical risk |
| `MotionPrimitive` | Atomic directed movement | actor, verb, target, direction, phase, timing, acceleration/deceleration, balance/gravity, mechanics constraints, start/termination conditions | planned → observed | Must have a feasible precondition and observable termination |
| `Shot` | Executable visual unit | ID, purpose, duration, states | planned → accepted/rejected | Has dependencies and acceptance criteria |
| `CameraState` | Camera geography and intent | side, axis, angle, focal length, framing, focus, depth of field, motion blur, exposure, lighting, eyeline, movement, edit rhythm | planned → observed | Axis/movement changes are motivated |
| `AudioEvent` | Timed sound or voice event | layer, source, interval, cause | planned → mixed/accepted | Visible causes align when diegetic |
| `ContinuityState` | State snapshot/delta across shots | scope, domains, evidence | inherited → accepted/superseded | Observed state cannot be replaced by planned state |
| `Constraint` | Guidance, control, assertion, or policy | kind, scope, priority, validation | proposed → satisfied/violated/waived | Precedence and fallback are explicit |
| `CapabilityProfile` (`ModelProfile` alias) | Capability evidence for integration | provider, version, modes, limits, feature evidence | unknown → confirmed/expired | Support is scoped and source-backed |
| `ExecutionStep` | Operator/runtime action | action, inputs, target, auth | planned → run/failed/skipped | External effects require authorization |
| `ExecutionAttempt` | One concrete runtime submission | immutable attempt ID/index, plan reference, profile/model/runtime/node/workflow/input/parameter context | submitted → running/succeeded/failed/cancelled | Every retry is a new attempt; unavailable fields are explicit unknowns |
| `GenerationArtifact` | Produced media or intermediate file | artifact ID, shot ID, execution-attempt reference, locator, collection-time content hash, provenance metadata | generated → collected/superseded | Locator is not identity; collection does not imply QA |
| `ArtifactObservation` (`QualityObservation` alias) | Evidence against a gate | observation ID, GenerationArtifact reference, locator, observed content hash, procedure, aggregate status, timestamp | not-run → pass/fail/partial | Hash must bind QA to the collected bytes; `NOT_RUN` is non-evidentiary |
| `Issue` | Repairable contradiction or failure | issue ID, owner, severity, route | open → repaired/waived/closed | Earliest preventable cause is retained |

## Supporting aggregates and records

These concepts appear in the architecture graph and contracts but are not additional visible participant types. They are explicitly classified here so Phase 1 does not invent a second boundary:

| Concept | Classification | Responsibility and required fields | Lifecycle/invariant |
|---|---|---|---|
| `NarrativeBeat` | temporal record | cause, purpose, stimulus, action, reaction, response, interval, prerequisites | planned → observed/repaired; reaction cannot precede cause without an explicit overlap |
| `SceneBible` | scene aggregate | scene/version, global entity state, references, retention, geography, lighting, relationships, prohibited drift | draft → accepted/superseded; one canonical owner per scene revision |
| `ShotGraph` | dependency aggregate | graph ID, shot IDs, directed edges, required state domains, anchors | planned → validated; ordinary playback is acyclic and transitions are explicit |
| `ExecutionPlan` | plan aggregate | plan ID, authorization mode, target, preflight, steps/shots, assembly, provenance | plan-only → preflight/authorized/blocked; no external effect without authority; actual submissions become attempts |
| `CanonicalPromptView` (`PromptView` alias) | compiled projection | canonical revision, profile reference, sections, mappings, omissions | compiled → reviewed; cannot author story, state, or capability truth |
| `ReferenceConflict` | issue record | conflict ID, asset/property values, precedence, severity, resolution route, evidence | open → resolved/blocked; conflicting references are never silently merged |

The `ArtifactObservation` (`QualityObservation` alias) and `Issue` rows in the main catalogue are likewise records about evidence and repair, not substitutes for the collected artifact or canonical plan.

## Relationship graph

```text
Project ─contains─> Scene ─plans─> NarrativeBeat ─observed_by─> Shot
   │                   │                                      │
   │                   ├─has─> SceneBible ─defines─> Entity    │
   │                   └─uses─> Reference ─anchors─> State     │
   │                                                          │
   └─delivers─> ExecutionPlan ─targets─> CapabilityProfile
                                      │
                                      ├─compiled_from─> CanonicalPromptView
                                      └─creates─> ExecutionAttempt ─produces─> GenerationArtifact
                                                                          │
                                                                          └─inspected_by─> ArtifactObservation ─opens─> Issue
```

## Required relationship semantics

- `speaker` and `listener` are directed and interval-bounded; a scene with dialogue must not infer turn-taking from text order alone.
- `owns`, `holds`, `inside`, `left_of`, `looks_at`, and `touches` carry state or temporal validity when used for continuity.
- `depends_on` connects shots and carries the state domains required at the boundary.
- `anchors` names the properties retained by a frame/reference; it never means pixel equality.
- `creates` connects an execution plan to one immutable attempt per runtime submission; `produces` connects that attempt to a collected artifact, never merely to an expected path.
- `GenerationArtifact.execution_attempt_ref` is the authoritative provenance edge; `artifact_ref` is a locator, while `content_hash` identifies the collected bytes.
- `ArtifactObservation.generation_artifact_ref` and `observed_content_hash` bind QA to one collected artifact and its bytes; a hash mismatch makes the observation stale.

## Abstraction decisions

The model intentionally does not create separate entities for every blueprint noun. Story, world, camera, and audio remain fields or logical modules until they require independent lifecycle/evidence. `Subject` is useful as a common identity envelope, while `Character` and `Animal` add distinct behavior and anatomy constraints. `ExecutionAttempt` is a record rather than a new service: it is separated from `ExecutionPlan` because actual submissions, retries, and failures are historical facts. `QualityObservation` is separated from `GenerationArtifact` because an artifact can exist without being accepted.

## Invariants

1. Stable IDs are immutable; revisions supersede rather than silently rewrite evidence.
2. Permanent identity state is not stored in transient pose/position fields.
3. Every state-changing interaction names a cause, before value when known, and after value.
4. A model profile cannot inherit support from a model name or repository alone.
5. A path/URI is not an artifact observation until existence, metadata, and procedure are recorded.
6. Every collected artifact references one immutable execution attempt; failed attempts remain retained and are never rewritten.
7. A quality pass is invalid without current evidence appropriate to the criterion and a matching current content hash.

## Example: vehicle entry

The vehicle is an entity with persistent geometry, while `door_state`, `wheel_state`, `occupant`, and `ignition` are transient. A `human_vehicle` interaction links Mara's hand to the handle and transitions the door state before a later shot inherits it. The full example and repair rules live in [`continuity-engine.md`](continuity-engine.md).

## Open questions

The future implementation must decide whether `Subject` is a true base schema or only a presentation grouping, and whether `QualityObservation` should be a separate persisted record or an embedded gate result. See [`open-questions.md`](open-questions.md).
