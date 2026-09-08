# Scene, narrative, and continuity model

This document defines the temporal and spatial planning layer between intent and shot execution. It turns a story into a directed graph of shots while preserving enough state for identity, object, location, action, and camera continuity.

## Contents

- [Scene Bible](#1-scene-bible)
- [Reference retention](#2-reference-retention)
- [Complexity and routing](#3-complexity-and-routing)
- [Narrative and shot graphs](#4-narrative-and-shot-graphs)
- [Continuity state](#5-continuity-state)
- [Interaction and contact planning](#6-interaction-and-contact-planning)
- [First/last-frame and chained generation](#7-firstlast-frame-and-chained-generation)
- [Long-form policy](#8-long-form-policy)
- [Duration profiles](#9-duration-profiles-30-60-90-and-120-seconds)
- [Failure modes and related documents](#11-failure-modes-and-related-documents)

## 1. Scene Bible

The Scene Bible is the durable source of truth for a scene revision or contiguous sequence within a project. It is not a prompt and it is not a generated image. A project may contain multiple Scene Bibles. It contains facts, desired facts, and unresolved choices that downstream plans may reference.

Every entity has a stable `entity_id`, a display name, a type, a permanence, a visual description, and an evidence status.

```yaml
scene_bible:
  project_id: proj_demo_001
  scene_id: scene_001
  revision: 1
  scope: CONTIGUOUS_SEQUENCE
  initial_state_ref: scene_bible:scene_001:initial
  initial_state:
    char_mara: {position: platform_left, gaze: toward_tracks, occupancy: {right_hand: empty}}
    prop_red_van: {position: curb_background, door_state: closed}
    world: {weather: rain_heavy, screen_direction: LEFT_TO_RIGHT}
  entities:
    - entity_id: char_mara
      type: character
      permanence: PERMANENT
      invariants:
        - short dark curls
        - yellow rain jacket
        - silver ring on right hand
      allowed_variants:
        - wet hair strands over forehead
        - jacket partially unzipped
      evidence: {status: CONFIRMED, claim_type: FACT, confidence: HIGH}
    - entity_id: prop_red_van
      type: vehicle
      permanence: PERSISTENT
      invariants:
        - compact red delivery van
        - visible white scratch above rear wheel
      evidence: {status: INFERRED, claim_type: ASSUMPTION, confidence: MEDIUM}
    - entity_id: loc_train_platform
      type: location
      permanence: PERSISTENT
      invariants:
        - covered suburban platform
        - wet concrete
        - tracks on camera-left side
      evidence: {status: CONFIRMED, claim_type: FACT, confidence: HIGH}
```

Permanence has operational meaning:

| Permanence | Meaning | Continuity policy |
|---|---|---|
| `PERMANENT` | Must remain stable for the project or sequence | Identity and invariants are checked on every dependent shot |
| `PERSISTENT` | Exists across a contiguous scene or sequence | State is carried until an explicit transition |
| `TRANSIENT` | Exists for one beat or shot | No cross-shot identity obligation unless promoted |
| `UNCERTAIN` | Mentioned or inferred but not resolved | Must be resolved, bounded, or marked intentionally ambiguous |

The Bible stores relationships as first-class data. A relationship has a source entity, target entity, type, direction, and validity interval. Examples include `holds`, `follows`, `looks_at`, `owns`, `is_inside`, `is_left_of`, `speaks_to`, and `threatens`.

## 2. Reference retention

Reference analysis produces a retention rule, not a promise that a model will reproduce pixels exactly. The planner distinguishes identity-critical, geometry-critical, style-critical, and optional references.

```yaml
retention_rules:
  - reference_id: ref_mara_portrait
    target_entity: char_mara
    retained_attributes:
      - face shape
      - short dark curls
      - silver ring on right hand
    priority: CRITICAL
    applies_to: [shot_001, shot_002, shot_003, shot_004]
    acceptable_drift: [expression, wetness, wardrobe_state]
    reanchor_after: shot_003
    status: PLANNED
```

The retention matrix must answer four questions before a reference-dependent shot is executable:

1. What is being retained?
2. Which shots depend on it?
3. What drift is acceptable?
4. When is a re-anchor required?

An asset can be used as an image input, a visual description, a retrieval hint, an identity embedding, a mask, or a human review reference. The chosen use is capability-dependent and is recorded in the execution plan.

The following is the integrated retention matrix fixture for a scene revision. `contracts.md` owns the field semantics; this matrix is the operational view that joins policy, priority, scope, conflict handling, acceptable degradation, and risk before a dependent shot can be marked executable.

| Policy | Entity/property example | Priority | Applies to | Conflict policy | Acceptable degradation | Degradation risk | Re-anchor or validation obligation |
|---|---|---|---|---|---|---|---|
| `LOCKED` | `char_mara.face_shape`, `char_mara.ring` | `CRITICAL` | `shot_001`–`shot_004` | Identity reference outranks style reference; unresolved conflict stays `OPEN` and blocks the dependent decision | None for the locked property; only explicitly flexible presentation may vary | Identity drift and cross-shot contamination | Compare every shot where visible; re-anchor before the next dependent shot after material drift |
| `FLEXIBLE` | `char_mara.expression`, wetness, wardrobe state | `MEDIUM` | `shot_001`–`shot_004` | Preserve the category and intent; resolve competing values by the reviewed scene priority | Bounded visual variation within the declared range | Appearance inconsistency mistaken for identity failure | Record the allowed range and review representative boundary shots |
| `DERIVED` | `vehicle_001.door_state` after a declared open action | `HIGH` | `shot_003`–`shot_004` | Derive from the latest valid state delta in the active `PLANNED` or `OBSERVED` channel; an observed contradiction creates a continuity conflict, never a silent overwrite | Recompute only after a named transition or repair | Stale state and false action causality | Validate the precondition, action, end state, and dependent boundary |
| `IGNORE` | Unrelated private or background reference attributes | `LOW` | All dependent shots unless explicitly scoped | Do not create a constraint from this source; retain the conflict record if another source makes the property material | Omit the attribute entirely from the compiled view | Privacy leakage or accidental identity injection | Exclude from prompt/reference bindings and run the redaction/relevance check |

If two policies or references disagree, the planner preserves both source records, records `ReferenceConflict.precedence` as `UNRESOLVED` until reviewed, and chooses `ASK`, `BLOCK`, or a bounded branch according to priority and degradation risk.

## 3. Complexity and routing

Complexity is a vector, not a single duration threshold. The baseline vector is:

```yaml
complexity:
  entity_count: 3
  identity_load: HIGH
  interaction_load: HIGH
  dialogue_load: MEDIUM
  camera_load: MEDIUM
  environment_load: MEDIUM
  motion_load: HIGH
  continuity_span: 4
  temporal_duration_seconds: 8
  audio_dependency: MEDIUM
```

Routing is derived from the vector and current capabilities:

| Profile | Use when | Required planning depth |
|---|---|---|
| `FAST` | One dominant subject, low continuity, low interaction | Intent, one shot, basic constraints |
| `CINEMATIC` | Controlled shot with meaningful camera or environment direction | Scene Bible, shot spec, camera/audio intent, QA gates |
| `PRODUCTION` | Multiple dependent shots, dialogue, or identity retention | Full continuity state, references, shot graph, model negotiation |
| `DIRECTOR` | Long-form, high ambiguity, dense interactions, or high failure cost | Full pipeline, alternatives, quality gates, human review checkpoints |

Duration can increase planning depth, but it never determines it alone. A three-second shot with two characters exchanging an object can require more planning than a ten-second static establishing shot.

## 4. Narrative and shot graphs

The narrative timeline records what changes in the story. The shot graph records where and how those changes are observed. They are separate because one narrative beat can span several shots, and one shot can contain several micro-actions.

```text
Narrative beat B1 ──observed by──> Shot 001 ──continuity──> Shot 002
        │                              │                     │
        └──── state delta ─────────────┴──────────────> Shot 003
```

Each beat has a causal purpose, entry state, exit state, action, emotional/tonal change, and dependencies. Each shot has a framing purpose, visible action, camera behavior, duration, and an incoming/outgoing continuity state.

```yaml
shot:
  id: shot_002
  scene_id: scene_001
  revision: 1
  narrative_beat_ids: [beat_01]
  purpose: reveal_mara_entering_platform
  duration_s: 4
  dependency_ids: [shot_001]
  active_subject_ids: [char_mara]
  supporting_subject_ids: []
  start_state_ref: "continuity:shot_001:end"
  start_state_delta:
    char_mara.position: platform_left
    prop_red_van.position: curb_background
  end_state_delta:
    char_mara.position: platform_right
    char_mara.gaze: toward_van
    world.weather: rain_heavy
  action_primitives: [walk, orient, look]
  references: [ref_mara_portrait, ref_platform]
  camera:
    framing: MEDIUM_TRACKING
    screen_direction: LEFT_TO_RIGHT
  constraints: [preserve_jacket, preserve_ring, preserve_van_scratch]
```

The graph must be acyclic for ordinary forward playback. A loop or flashback is represented as an explicit narrative transition with a new temporal context; it must not be hidden as an accidental continuity edge.

## 5. Continuity state

Continuity is divided into independently checkable domains:

- identity: appearance, wardrobe, age presentation, persistent marks;
- object: possession, orientation, damage, fill level, visibility;
- spatial: position, screen direction, relative geometry, occlusion;
- temporal: action phase, elapsed time, weather/light progression;
- camera: lens feel, axis, height, movement phase, cut motivation;
- audio: speaker, line phase, ambient bed, diegetic source;
- world: location, weather, time of day, physical state.

Each domain has a `KNOWN`, `INFERRED`, `UNKNOWN`, or `CONFLICTED` continuity status. These are continuity-domain values and are distinct from the evidence-status enum (`CONFIRMED`, `INFERRED`, `PROPOSED`, `UNKNOWN`) in [`contracts.md`](contracts.md). Unknown state is not silently promoted to fact. A shot may be executable with unknown state only when the relevant gate marks it non-blocking.

State deltas are explicit:

```yaml
state_delta:
  shot_id: shot_003
  before:
    mara_position: platform_right
    van_door: closed
  actions:
    - actor: char_mara
      verb: open
      target: prop_red_van
      contact_points: [right_hand, rear_door_handle]
  after:
    mara_position: beside_van
    van_door: open
    mara_hand: right_hand_on_door
```

This avoids the common failure in which a generated shot depicts an effect without a valid cause, for example a door already open when the preceding action said that the character opened it.

## 6. Interaction and contact planning

An interaction is a typed relation with participants, target, intent, contact points, action phases, and success conditions. Physical contact is never implied only by prose when it affects plausibility or continuity.

```yaml
interaction:
  interaction_id: int_001
  type: hand_to_object
  actor: char_mara
  target: prop_red_van
  contact_points: [right_hand, rear_door_handle]
  phases: [approach, reach, contact, pull, release]
  visible_success: door_open_and_hand_released
  risk: HIGH
```

For a two-person exchange, add both hands, object ownership before and after, gaze targets, body orientation, and the moment of transfer. If a model cannot reliably express the contact, the planner may split the action into setup, contact, and result shots rather than hiding the risk in a longer prompt.

## 7. First/last-frame and chained generation

First/last-frame (FLF) and chained I2V are conditional planning strategies. The planner chooses them only when the selected model profile confirms the required input and output contract.

The default chaining policy is:

1. Generate a keyframe or anchor for the shot entry.
2. Generate a short segment within the model's stable temporal range.
3. Validate the outgoing state against the planned state delta.
4. Re-anchor identity and geometry before the next segment when drift exceeds budget.
5. Carry forward only validated state, not every pixel artifact.

FLF is useful for a known transition between two visual states, but it does not by itself solve identity, action causality, or physically valid motion. If the capability profile lacks reliable FLF support, the plan must downgrade to keyframe chaining or become non-executable.

## 8. Long-form policy

Long-form output is assembled from validated shot artifacts. The default unit is a shot or short segment, not a single monolithic generation request. Assembly records ordering, transitions, frame rate, audio synchronization, and the continuity evidence used at each boundary.

The long-form planner must expose alternatives when a requested transition is under-specified:

- `direct`: one shot if the model can express the action safely;
- `split`: setup/contact/result shots;
- `anchor`: keyframe or reference reset before continuing;
- `reframe`: change camera coverage to hide an unstable transition;
- `human_review`: pause for approval when ambiguity affects story or identity.

The choice is a planning decision and must appear in the execution plan with its reason and fallback.

## 9. Duration profiles: 30, 60, 90, and 120 seconds

The duration bands below define minimum planning structures for the real-valued target duration `t` in seconds (`0 < t ≤ 120`); they do not assert that any provider can generate the duration in one request. Complexity and dependency risk can require a deeper profile before a floor is reached.

| Target duration | Minimum required structure | Typical strategy | Primary failure/recovery concern |
|---|---|---|---|
| `0 < t ≤ 30` seconds | shot purpose and state at material boundaries; add beats/graph when complexity requires | one shot or profile-supported segments; use a Scene Bible when identity/location recurs | overloaded beat, missing product/end state; split and re-evaluate |
| `30 < t ≤ 45` seconds | narrative timeline, plus the base structure | 4–8 shots or profile-supported segments; explicit causal beat order | hidden beats and missing transitions; split and re-evaluate |
| `45 < t < 60` seconds | narrative timeline, Scene Bible, shot graph, and explicit `PLANNED` state propagation | validated segments with canonical re-anchors at material transitions | state contradiction and reference decay; repair by split/re-anchor |
| `60 ≤ t < 90` seconds | all `t > 45` requirements plus reference/audio/dialogue timelines when applicable, generation strategy, and assembly plan | 8–16 validated segments with explicit assembly; static scenes may use one-node/minimal forms | dialogue/action density and stale anchors; repair by split/re-anchor |
| `90 ≤ t ≤ 120` seconds | all `t ≥ 60` requirements plus alternative branches, recovery checkpoints, provenance/assembly manifest, and human checkpoints | 12–32 segments grouped into validated sequences; no unbounded recursion | cross-sequence state divergence and audio/visual sync; reset from canonical references |

### Threshold rationale

The boundary is evaluated on the requested real-valued target duration: `t = 30` remains in the base floor; any `30 < t ≤ 45` adds the narrative timeline; any `45 < t < 60` adds the Scene Bible/shot graph/planned propagation; and `60 ≤ t < 90` adds the applicable reference/audio/dialogue, generation, and assembly records. At `t = 90`, the final band adds branches, recovery checkpoints, a provenance manifest and human checkpoints. A static low-risk piece may use one node and minimal state in those structures, but cannot omit them. Complexity can escalate a three-second vehicle/contact shot to the full interaction and continuity path before any duration floor applies.

### Long-form package

For any band above a single-shot plan, the package includes:

- narrative beats with causal order and time intervals;
- Scene Bible and reference retention matrix when entities recur;
- shot DAG with dependencies, start/end state, anchors, and risk;
- dialogue, performance, and audio timelines when applicable;
- model/profile negotiation and segment duration limits;
- canonical re-anchor and reset conditions;
- assembly order, frame-rate/audio alignment, and provenance metadata;
- repair/recovery routes for rejected or stale segments;
- human review checkpoints for material identity, rights, story, or quality decisions.

## 10. Open questions

The exact segment counts are illustrative planning ranges, not requirements. Phase 1 must replace them with profile- and fixture-backed observations where useful; until then, the complexity vector and dependency graph remain authoritative.

## 11. Failure modes and related documents

| Failure | Detection | Repair |
|---|---|---|
| Scene Bible omitted for dependent work | recurring entity/anchor has no durable owner | create the Bible or route to human review |
| Last frame is treated as complete state | anchor scope exceeds observed evidence | re-anchor from canonical references and validate domains separately |
| Shot skips a causal transition | state delta has no action/precondition | split the beat or declare a motivated time transition |
| Complexity label hides a dependency | duration is used without a risk vector/graph | escalate planning depth and record the reason |

Canonical entities and state classes are in [`domain-model.md`](domain-model.md) and [`state-model.md`](state-model.md); detailed inheritance/repair is in [`continuity-engine.md`](continuity-engine.md); long-form acceptance and failure oracles are in [`golden-scenarios.md`](golden-scenarios.md) and [`failure-and-evals.md`](failure-and-evals.md).
