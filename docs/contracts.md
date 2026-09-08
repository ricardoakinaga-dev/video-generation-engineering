# Canonical contracts and invariants

## Purpose

Define the shared vocabulary, field shapes, lifecycle statuses, evidence labels, and invariants that planning and adapter components use. This document remains the broader design source; the executable Python subset is implemented in `.agents/skills/video-generation-engineering/scripts` and is intentionally narrower than every documented future integration.

## Contract status

These are version-1 semantic contracts for the Skill. Fields marked `optional` may be omitted only when the owning requirement is inapplicable; material unknowns are represented explicitly instead of invented defaults. The package implements the planning, profile, runtime-boundary, provenance, media and observation checks described in its current references; broader provider/media capabilities remain conditional.

## Contents

- [Shared conventions](#shared-conventions)
- [Canonical names, aliases, and serialized enums](#canonical-names-aliases-and-serialized-enums)
- [Scene intent and reference contracts](#input-contract-sceneintent)
- [Scene, shot, and continuity contracts](#scene-plan-contracts)
- [Capability and execution contracts](#capability-contract-capabilityprofile)
- [Observation and invariants](#observation-contract-artifactobservation)
- [Canonical prompt view](#canonical-prompt-view)
- [Failure modes and open questions](#contract-failure-modes)

## Shared conventions

### Identity and versioning

- Every project has a stable `project_id`; every scene has `scene_id`; every entity, reference, beat, shot, anchor, capability profile, execution plan/attempt, observation, and issue has a stable type-prefixed ID.
- IDs are immutable. Revisions create a new `revision` or append a superseding record; they do not silently rewrite historical evidence.
- All time values use an explicit timezone for wall-clock records and a project timebase for media positions. Media positions are represented as seconds plus optional frame index; frame index alone is not portable across frame rates.
- Contracts carry `schema_version`. A consumer that does not understand a newer major version fails closed and reports the incompatibility.
- Paths/URIs are references, not proof that a file exists or is accessible. A hash, runtime observation, or artifact inspection is required for execution claims.

### Evidence and claim labels

```yaml
evidence:
  status: CONFIRMED        # CONFIRMED | INFERRED | PROPOSED | UNKNOWN
  claim_type: DECISION     # FACT | ASSUMPTION | HYPOTHESIS | DECISION
  confidence: HIGH         # HIGH | MEDIUM | LOW
  source_refs:
    - docs/research.md#SRC-COMFY-ROUTES
  observed_at: null
  limitations:
    - "Source documents capability; it does not prove this local installation."
```

`CONFIRMED` requires a direct current source or executed observation. `PROPOSED` is valid for design choices. `INFERRED` may guide planning but cannot be presented as provider support. `UNKNOWN` is a safe value, not an error to hide.

### Status vocabulary

The domain lifecycle uses these statuses:

```text
project: INTAKE → PLANNING → READY_FOR_GENERATION → GENERATING → REVIEW
         → ACCEPTED | REVISION_REQUIRED | ABORTED

shot:    PLANNED → READY → RUNNING → GENERATED → REVIEW
         → ACCEPTED | REGEN_REQUIRED | REJECTED | SUPERSEDED

capability: UNKNOWN | CONFIRMED | DEGRADED | UNSUPPORTED | EXPIRED
observation: NOT_RUN | PASS | PARTIAL | FAIL | BLOCKED
```

For an `ArtifactObservation`, each check also carries `required: true|false` and a result from `PASS | PARTIAL | FAIL | BLOCKED | NOT_RUN | WAIVED | NOT_APPLICABLE`. The aggregate `status` is computed, not chosen independently: `PASS` requires every required check to be `PASS`, with `WAIVED` allowed only when a formal human waiver records scope, reason, authority, and expiry. A required `PARTIAL`, `FAIL`, `BLOCKED`, or `NOT_RUN` prevents aggregate `PASS`; `FAIL` or `BLOCKED` takes precedence over `PARTIAL`. If no check was executed, the aggregate is `NOT_RUN`. An optional check that is incomplete may make the observation `PARTIAL`, but it cannot be silently omitted from the record. A pending `NOT_RUN` record is allowed only as an explicitly non-evidentiary QA record: it must state that no procedure executed, may leave `observed_at` and `procedure` null, and must have no executed checks; it cannot support `ACCEPTED` or any PASS claim. For every other observation result, `observed_at`, `procedure`, and the applicable checks are required.

`shot.lifecycle_status` and `ArtifactObservation.status` are different fields owned by different state machines. A QA value (`PASS`, `PARTIAL`, `FAIL`, or `BLOCKED`) must never be written into `shot.lifecycle_status`; the shot keeps one of the lifecycle values above and points to its collection and observation records through `generation_artifact_ref` and `artifact_observation_ref` when they exist. The `ignition` state in scene and continuity examples is a quoted string enum `"ON" | "OFF" | "STARTING" | "UNKNOWN"`, not a YAML boolean.

Allowed transitions are owned by the triggering evidence. A `PLAN_ONLY` shot may become `READY` from validated planned dependencies, but a shot cannot enter `RUNNING` when its required execution dependency state is unresolved, and no shot can enter `ACCEPTED` without current observations for its required criteria.

## Canonical names, aliases, and serialized enums

Focused documents may use a reader-friendly view name, but the following map is normative for Phase 1 serialization and validation:

| Canonical serialized concept | Reader-facing/domain alias | Scope and owner |
|---|---|---|
| `ScenePlan` | Scene Representation | model-independent planned scene; `architecture.md`/this contract |
| `SceneBible` | Scene Bible | one aggregate per scene revision; project contains many scenes |
| `ReferenceAsset` | Reference | input evidence asset; `contracts.md` owns fields and provenance |
| `RetentionRule` | reference retention policy | per entity/property/shot scope; `contracts.md` owns semantics |
| `ContinuityState` | continuity ledger entry | one state snapshot/delta at a scope boundary; a ledger is a collection |
| `CapabilityProfile` | `ModelProfile` | versioned model/runtime capability evidence; `model-adaptation.md` owns negotiation |
| `CanonicalPromptView` | PromptView | model-independent compiled projection; `CompiledPrompt` is the adapter-specific derived output |
| `ExecutionPlan` | execution recipe | plan aggregate containing `ExecutionStep` records; `comfyui-execution.md` owns runtime boundary |
| `ExecutionAttempt` | runtime attempt | immutable record of one submitted generation attempt and the exact profile/model/workflow/input/parameter context used |
| `GenerationArtifact` | collected artifact | runtime output plus collection/provenance metadata; never a QA result |
| `ArtifactObservation` | `QualityObservation` | executed or explicitly pending QA record linked to a `GenerationArtifact` |
| `ReferenceConflict` | reference conflict | issue record for incompatible asset/property values; never silently merged |
| `ShotGraph` | shot DAG | dependency aggregate whose edges carry state/anchor requirements |

Schema keys use `snake_case`; serialized enum values use uppercase. The canonical enums are `CONFIRMED | INFERRED | PROPOSED | UNKNOWN` for evidence, `LOCKED | FLEXIBLE | DERIVED | IGNORE` for retention, `CRITICAL | HIGH | MEDIUM | LOW` for priority/severity, `PLAN_ONLY | LOCAL_DRY_RUN | LOCAL_EXECUTE | CLOUD_EXECUTE` for execution mode, `PLANNED | OBSERVED` for state channel, `EXPLICIT | INFERRED | UNRESOLVED` for reference-conflict precedence, `OPEN | RESOLVED | BLOCKED | WAIVED` for issue/conflict status, and the lifecycle/status values listed above. Rights and consent use `CONFIRMED | UNKNOWN | RESTRICTED | REJECTED | NOT_APPLICABLE`. The legacy explanatory spelling `UNSPECIFIED` is accepted only as a one-to-one alias of `IGNORE` and is not a new policy.

### Serialized field ownership and projections

The YAML examples in this package use the same canonical serialized fields. In particular, `ShotSpec` uses `id`, `duration_s`, `dependency_ids`, and `start_state_ref`; `CapabilityProfile` uses `id` and the nested `supports.modes`, `supports.inputs`, and `supports.outputs` fields. Reader-facing names such as `shot_id`, `duration_seconds`, `dependencies`, `in_state_ref`, `profile_id`, `modes`, and `modalities` are not alternate wire formats. A legacy input may use them only through an explicitly named migration that converts every affected field to the canonical representation before validation; no document may emit a legacy object as if it were canonical.

## Input contract: `SceneIntent`

```yaml
scene_intent:
  schema_version: 1
  project_id: proj_001
  scene_id: scene_001
  title: "string"
  objective: "what the viewer should understand or feel"
  duration:
    target_seconds: 60
    allowed_range_seconds: [55, 65]
  target:
    platform: comfyui
    aspect_ratio: "16:9"
    delivery: "mp4 with stereo audio"
  genre: "luxury commercial"
  subjects: [subject_001]
  objects: [vehicle_001]
  environments: [environment_001]
  actions: ["approach vehicle", "enter", "drive away"]
  dialogue_required: true
  audio_required: true
  style_preferences: ["natural golden-hour commercial"]
  references: [ref_001, ref_002]
  hard_constraints:
    - "subject_001 identity and wardrobe retention"
  preferences:
    - "slow push-in during the final beat"
  unknowns:
    - "target video model not selected"
  evidence: {status: CONFIRMED, claim_type: FACT, confidence: HIGH}
```

Required semantic fields are `objective`, `duration`, and the entity/action inventory. A missing target model is acceptable at intake; it becomes a blocking unknown only when compiling an execution plan.

## Reference contracts

### `ReferenceAsset`

```yaml
reference_asset:
  id: ref_001
  kind: image                    # image | video | audio | text | 3d | other
  locator: "path or URI"
  content_hash: null
  roles: [character_identity, wardrobe]
  maps_to: [subject_001]
  provenance:
    source: "creator supplied"
    rights_status: UNKNOWN       # CONFIRMED | UNKNOWN | RESTRICTED | REJECTED | NOT_APPLICABLE
    consent_status: UNKNOWN      # CONFIRMED | UNKNOWN | RESTRICTED | REJECTED | NOT_APPLICABLE
  evidence: {status: PROPOSED, claim_type: ASSUMPTION, confidence: MEDIUM}
```

### `RetentionRule`

```yaml
retention_rule:
  entity_id: subject_001
  property: facial_identity
  policy: LOCKED                 # LOCKED | FLEXIBLE | DERIVED | IGNORE
  rationale: "recognizable recurring protagonist"
  anchor_refs: [ref_001]
  conflict_policy: "identity reference outranks style reference"
  qa_obligation: "compare identity in every shot where face is visible"
```

Property semantics:

- `LOCKED`: preserve as far as the selected workflow can support; failure is a QA issue, not a hidden relaxation.
- `FLEXIBLE`: preserve the category or intent while allowing variation.
- `DERIVED`: compute from another state or reference (for example, wardrobe state after a declared change).
- `IGNORE`: do not invent a constraint from this reference; the planner may choose a reversible default and label it.

Older notes may use `UNSPECIFIED`; it is a deprecated one-to-one alias of `IGNORE`, not a fifth policy. Fixture/adaptor serializers must emit `IGNORE`.

### `ReferenceConflict`

```yaml
reference_conflict:
  id: refconf_001
  scene_id: scene_001
  property: wardrobe.color
  candidates:
    - reference_id: ref_portrait
      value: blue
      role: identity
    - reference_id: ref_wardrobe
      value: red
      role: wardrobe
  precedence: UNRESOLVED
  severity: HIGH
  status: OPEN
  evidence_refs: [ref_portrait, ref_wardrobe]
  resolution_route: ask_or_preserve_branches
```

The conflict record is required whenever two references provide incompatible values for the same entity/property. `precedence: UNRESOLVED` blocks only the dependent decision; it does not erase either source or invent a merge.

## Scene plan contracts

### `SceneBible`

```yaml
scene_bible:
  schema_version: 1
  project_id: proj_001
  scene_id: scene_001
  revision: 1
  scope: CONTIGUOUS_SEQUENCE
  initial_state_ref: scene_bible:scene_001:initial
  initial_state:
    subject_001: {position: driveway, gaze: toward_vehicle, occupancy: {right_hand: empty}}
    vehicle_001: {door: closed, ignition: "OFF", position: driveway}
  visual_style: "string"
  camera_language: "string"
  time_of_day: "golden hour"
  geography: "driveway outside a modern house"
  lighting: "warm key from camera left; cool ambient fill"
  entities:
    - id: subject_001
      permanent_state:
        identity: {reference_ids: [ref_001], retention: LOCKED}
        wardrobe: {description: "...", retention: LOCKED}
        voice: {id: voice_001, retention: FLEXIBLE}
      prohibited_drift: ["hair color", "jacket pattern"]
  objects:
    - id: vehicle_001
      geometry_retention: LOCKED
      state: {door: closed, ignition: "OFF", position: driveway}
  environments:
    - id: environment_001
      anchors: ["front door", "driveway bend", "oak tree"]
  relationships: []
  continuity_rules: []
  audio_identity: {room_tone: "quiet outdoor ambience"}
```

The Scene Bible owns global invariants. A shot may create a local state delta, but it must cite the global rule it is satisfying or intentionally changing.

### `NarrativeBeat`

```yaml
narrative_beat:
  id: beat_004
  time: {start_s: 24, end_s: 31}
  purpose: "Subject commits to leaving"
  stimulus: "subject_002 challenges subject_001"
  action: "subject_001 approaches vehicle_001"
  reaction: null
  response: "subject_002 follows with amused concern"
  prerequisites: [beat_003]
  parallel_actions: []
  visible_event_ids: [event_approach]
```

The timeline is a narrative contract. It is not a final generation prompt and it may be split across multiple shots.

## Shot contract: `ShotSpec`

```yaml
shot:
  id: shot_005
  scene_id: scene_001
  revision: 1
  lifecycle_status: PLANNED
  generation_artifact_ref: null
  artifact_observation_ref: null
  duration_s: 6
  purpose: "Show hand-to-handle contact and door articulation"
  dependency_ids: [shot_004]
  active_subject_ids: [subject_001]
  supporting_subject_ids: [subject_002]
  start_state_ref: "continuity:shot_004:end"
  start_state_delta:
    vehicle_001.door: closed
  end_state_delta:
    vehicle_001.door: open
    subject_001.right_hand: door_handle
  narrative_beat_ids: [beat_005]
  action_primitives: [approach, reach, contact, pull, rotate_door]
  contact_graph_ref: contact:shot_005
  references: [ref_001, ref_002, anchor:shot_004:last_frame]
  camera:
    size: MEDIUM
    angle: EYE_LEVEL
    focal_length: 50mm_equivalent
    framing: MEDIUM_TRACKING
    focus: subject_001
    depth_of_field: SHALLOW
    motion_blur: NATURAL
    exposure: LOCKED_TO_SCENE
    lighting: "scene_bible:lighting"
    eyeline: subject_001
    movement: {type: LATERAL_TRACK, direction: LEFT_TO_RIGHT, phase: FOLLOW_APPROACH}
    screen_direction: LEFT_TO_RIGHT
    axis_policy: PRESERVE_180_AXIS
    edit_rhythm: HOLD_THROUGH_CONTACT
  lighting_ref: scene_bible:lighting
  dialogue_ids: []
  audio_event_ids: [door_handle_contact, door_open]
  generation_mode: I2V
  capability_requirements: [image_start, temporal_consistency, vehicle_geometry]
  constraints: [identity_drift, hand_handle_contact, door_articulation]
  acceptance_ids: [QG-05, QG-09, QG-13, QG-14]
```

Every shot has a start and end state. If the intended state is unknown, the shot remains `PLANNED` with an explicit unresolved field; it cannot be treated as ready by omission.

## Continuity state

```yaml
continuity_state:
  scope: shot_005
  state_channel: PLANNED
  inherited_from: shot_004:end
  entities:
    subject_001:
      permanent: {identity_ref: ref_001, wardrobe: "unchanged"}
      transient: {position: driveway_handle, pose: reaching, gaze: vehicle_001, emotion: amused}
      occupancy: {right_hand: door_handle, left_hand: empty}
    vehicle_001:
      geometry: "reference-locked"
      state: {door: closed, ignition: "OFF", wheels: stopped}
  world: {screen_direction: left_to_right, lighting: "unchanged", anchors: [driveway_bend]}
  camera:
    side: SUBJECT_LEFT
    angle: EYE_LEVEL
    focal_length: 50mm_equivalent
    framing: MEDIUM_TRACKING
    focus: subject_001
    depth_of_field: SHALLOW
    motion_blur: NATURAL
    exposure: LOCKED_TO_SCENE
    eyeline: subject_001
    lens_intent: 50mm_equivalent
    movement_phase: FOLLOW_APPROACH
    axis_policy: PRESERVE_180_AXIS
    edit_rhythm: HOLD_THROUGH_CONTACT
  dialogue: {next_turn: subject_002, previous_line_complete: true}
  audio: {room_tone: continuous, door_event_pending: true}
  temporal: {absolute_time_s: 24, daylight_progression: slow}
```

State domains are independent so a repair can change a pose without changing identity, or change camera position without silently changing world geography.

## Capability contract: `CapabilityProfile`

```yaml
capability_profile:
  schema_version: 1
  id: comfyui-wan22-native-v1
  provider: local_comfyui
  runtime: ComfyUI
  runtime_version: UNKNOWN
  model: Wan2.2-I2V-A14B
  integration_version: "profile-2026-09-07"
  profile_revision: 1
  status: PROPOSED
  evidence_refs: [docs/research.md#SRC-COMFY-WAN22]
  evidence:
    status: PROPOSED
    claim_type: FACT
    confidence: MEDIUM
    source_refs: [https://docs.comfy.org/tutorials/video/wan/wan2_2]
    accessed_at: 2026-09-07
  prompt_style: structured_natural_language
  preferred_prompt_density: profile_defined
  supports:
    modes: [T2V, I2V, TI2V, FLF2V]
    inputs: [text, image, start_image, end_image]
    outputs: [video]
    audio: {native_generation: UNKNOWN, mux_external_audio: PROPOSED}
    identity_conditioning: UNKNOWN
    arbitrary_reference_images: UNKNOWN
    camera_controls: {syntax: natural_language_or_workflow_control, status: UNKNOWN}
  controls:
    - seed
    - width
    - height
    - frame_count
    - fps
  limits:
    duration_s: {min: UNKNOWN, max: UNKNOWN}
    frame_count: {rule: "profile-specific"}
    resolution: UNKNOWN
    vram: UNKNOWN
  dependencies:
    nodes: UNKNOWN
    model_assets: UNKNOWN
  feature_evidence:
    text_to_video: {status: PROPOSED, source_ref: docs/research.md#SRC-COMFY-WAN22, checked_at: "2026-09-07", scope: official_workflow_not_local_probe, limitation: exact_runtime_unknown}
    image_to_video: {status: PROPOSED, source_ref: docs/research.md#SRC-COMFY-WAN22, checked_at: "2026-09-07", scope: official_workflow_not_local_probe, limitation: exact_runtime_unknown}
    first_last_frame: {status: PROPOSED, source_ref: docs/research.md#SRC-COMFY-FLF, checked_at: "2026-09-07", scope: official_workflow_not_local_probe, limitation: endpoint_and_quality_unknown}
    reference_conditioning: {status: UNKNOWN, source_ref: null, checked_at: "2026-09-07", scope: local_profile, limitation: arbitrary_reference_and_identity_behavior_unprobed}
    audio_dialogue_lip_sync: {status: UNKNOWN, source_ref: null, checked_at: "2026-09-07", scope: local_profile, limitation: joint_support_unprobed}
    camera_controls: {status: UNKNOWN, source_ref: null, checked_at: "2026-09-07", scope: local_profile, limitation: syntax_and_runtime_binding_unprobed}
    duration_resolution_frames_vram: {status: UNKNOWN, source_ref: null, checked_at: "2026-09-07", scope: local_profile, limitation: effective_limits_unprobed}
  recommended_strategy:
    default: plan_only_then_local_preflight
    long_form: short_segments_with_periodic_canonical_reanchor
    visible_dialogue: separate_audio_and_lip_sync_path_unless_profile_is_confirmed
    unknown_capability: degrade_or_block_with_human_decision
  known_failure_modes:
    - identity_drift
    - recursive_chain_degradation
    - frame_flicker
    - unsupported_node_or_model_asset
  validity:
    checked_at: "2026-09-07"
    recheck_when: [ComfyUI_update, model_update, custom_node_update, workflow_change]
```

This complete fixture is the canonical profile shape and content for `comfyui-wan22-native-v1` revision `1`. The adapter document repeats the same fixture for discoverability; any adapter-specific view must be an identified projection and must not change its modes, limits, evidence paths, or status values. Profile support is not transitive: `I2V` does not imply identity lock, end-frame support, audio generation, or arbitrary reference images. Each requested feature needs its own evidence.

## Execution contract: `ExecutionPlan`

```yaml
execution_plan:
  id: exec_scene_001_rev1
  authorization: PLAN_ONLY
  runtime: ComfyUI
  runtime_endpoint: null
  preflight:
    required_version: "profile-specific"
    required_nodes: []
    required_model_assets: []
    resource_budget: {vram: UNKNOWN, disk: UNKNOWN}
  shots:
    - shot_id: shot_005
      workflow_ref: "template or API-format workflow reference"
      mode: I2V
      input_assets: [ref_001, anchor:shot_004:last_frame]
      prompt_slots: {positive: "compiled view", negative: "selected constraints"}
      parameters: {seed: 42, width: 1280, height: 720, frames: UNKNOWN}
      output: {path_template: "shot_005.mp4", expected_duration_s: 6}
      fallback: "regenerate from canonical start keyframe if last-frame anchor drifts"
      proof: ["workflow validation", "artifact inspection", "continuity review"]
  assembly:
    order: [shot_001, shot_002, shot_003, shot_004, shot_005]
    audio_plan_ref: audio_scene_001
    output_contract: {container: mp4, audio: stereo_or_declared_silent}
```

`PLAN_ONLY` is the default. A future authorized execution mode must be explicit and must record the runtime, action, result, and artifacts.

Serialized execution modes use uppercase values: `PLAN_ONLY`, `LOCAL_DRY_RUN`, `LOCAL_EXECUTE`, and `CLOUD_EXECUTE`. Lowercase words in explanatory prose are not enum values.

## Execution attempt contract: `ExecutionAttempt`

`ExecutionPlan` describes intended work. Each runtime submission creates one append-only `ExecutionAttempt`, even when it fails or targets the same shot as an earlier attempt. The attempt is the canonical owner of the concrete execution context; its `id` and `attempt_index` distinguish retries and its fields are sealed after submission. `ExecutionAttempt.status` uses `SUBMITTED | RUNNING | SUCCEEDED | FAILED | CANCELLED | UNKNOWN`. A failed attempt remains historical and cannot be rewritten into a successful one.

```yaml
execution_attempt:
  schema_version: 1
  id: attempt_shot_002_001
  execution_plan_ref: exec_scene_001_rev1
  shot_id: shot_002
  attempt_index: 1
  status: SUCCEEDED
  started_at: "2026-09-08T08:00:00-03:00"
  ended_at: "2026-09-08T08:04:00-03:00"
  profile:
    id: comfyui-wan22-native-v1
    revision: 1
  model:
    id: Wan2.2-I2V-A14B
    version: "fixture-model-v1"
    asset_hash: "sha256:50b0b6a2bac409650b3d30fe81e88b31ed1dbfb62df402971e0930c169985cb5"
  runtime:
    provider: comfyui
    endpoint: local
    version: "fixture-comfyui-v1"
    node_inventory_hash: "sha256:f912352348b90a56ef3a080aea27f1022bdcbc85a512739b4e66dcfde76645e0"
  workflow:
    ref: workflows/shot_002_api.json
    content_hash: "sha256:8176bcc0dbd3e7abc0910578d5952d7f2df05bfccb54df880b26e6db8d56eb4e"
    prompt_ref: "scene_001_rev1:shot_002"
    queue_id: comfy_queue_001
  nodes:
    - id: load_image
      type: LoadImage
      version: "fixture-node-v1"
    - id: k_sampler
      type: KSampler
      version: "fixture-node-v1"
  inputs:
    - ref: ref_mara_portrait
      role: identity_reference
      content_hash: "sha256:73af5d7c92634021c9f26db097c0ecd91b36abefd3e58283b2a9741e4b7c469e"
    - ref: "anchor:shot_004:last_frame"
      role: temporal_anchor
      content_hash: "sha256:73af5d7c92634021c9f26db097c0ecd91b36abefd3e58283b2a9741e4b7c469e"
  parameters:
    seed: 18403
    bindings:
      width: 832
      height: 480
      frame_count: 81
      fps: 16
      sampler: euler
  progress_ref: "execution-events:attempt_shot_002_001"
  error_ref: null
  unknown_fields: []
```

The hash, version, queue, and timestamp values in this Phase 0 fixture are illustrative and are not runtime evidence. In an execution record, an unavailable value is represented as `null`, never as an empty string or guessed default, and its canonical dotted path is listed in `unknown_fields`. A required unknown profile/model version, workflow identity, input hash, or output content hash blocks QG-17 and any artifact acceptance; an unavailable optional seed or parameter prevents a reproducibility claim and is disclosed at the applicable gate.

## Artifact collection contract: `GenerationArtifact`

Collection and provenance are recorded separately from visual, audio, or continuity QA:

```yaml
generation_artifact:
  schema_version: 1
  id: art_shot_002_v01
  shot_id: shot_002
  execution_attempt_ref: attempt_shot_002_001
  artifact_ref: outputs/shot_002_v01.mp4
  content_hash: "sha256:c3b5516bb098506632dbbf60e1d2f989bbfda77d16306af1b4b57a1fca0c1334"
  collected_at: "2026-09-08T08:00:00-03:00"
  generation_status: GENERATED
  media:
    kind: video
    frame_count: observed
    fps: observed
    audio_track: present
  runtime:
    provider: comfyui
    endpoint: local
    workflow_hash: "sha256:8176bcc0dbd3e7abc0910578d5952d7f2df05bfccb54df880b26e6db8d56eb4e"
  quality_review:
    lifecycle: NOT_STARTED
    observation_ref: null
```

`GenerationArtifact` proves collection and provenance metadata only. `quality_review.lifecycle` is `NOT_STARTED | IN_PROGRESS | COMPLETE`; it is progress metadata, not a QA result. A shot remains `GENERATED` while a collected artifact waits for QA, becomes `REVIEW` when review starts, and receives `ACCEPTED` only through an accepted `ArtifactObservation`.

`execution_attempt_ref` is the authoritative link from a collected artifact to the immutable execution context that produced it. `artifact_ref` is only a locator and never identifies an artifact by itself. `content_hash` is the digest of the bytes at collection time, serialized as `algorithm:hex`; it is required for an acceptance-eligible collected artifact. The small `runtime.workflow_hash` field is a collection-time echo of the referenced attempt's `workflow.content_hash` and must match it; the attempt remains the canonical owner of workflow identity. If the current bytes at `artifact_ref` do not hash to `content_hash`, the artifact and every dependent observation are stale and must be recollected/revalidated before acceptance.

## Observation contract: `ArtifactObservation`

```yaml
artifact_observation:
  id: obs_shot_005_001
  shot_id: shot_005
  generation_artifact_ref: art_shot_005_001
  artifact_ref: "path or URI"
  observed_content_hash: "sha256:c3b5516bb098506632dbbf60e1d2f989bbfda77d16306af1b4b57a1fca0c1334"
  observed_at: "2026-09-07T20:00:00-03:00"
  procedure: "manual visual inspection plus media metadata check"
  status: PARTIAL
  checks:
    - id: QG-09
      required: true
      result: PARTIAL
      observation: "door opens, but hand contact is ambiguous"
      evidence: "frame/time reference"
  limitations:
    - "No automated identity embedding comparison available"
  repair_route: shot_005
```

An observation must identify which `GenerationArtifact` was inspected through `generation_artifact_ref`, retain the locator for operator use, record the digest seen during QA in `observed_content_hash`, and state what was inspected, when, by which procedure, and with what limitation. For an executed observation, `observed_content_hash` must equal the resolved artifact `content_hash`; a null or mismatched hash makes the observation non-acceptance evidence. A prompt or plan is not an artifact observation. If the bytes at the same path change later, the resolver detects the mismatch against the immutable artifact hash and marks the observation stale; it cannot remain accepted without a new collection/QA pass.

## State and transition invariants

1. State propagation is mode-specific: `PLAN_ONLY` traverses the latest valid planned state, while an execution path that crosses an artifact boundary requires the latest accepted observed state. Neither channel is silently promoted into the other.
2. A state delta must name the domain, property, prior value when known, next value, and cause/beat.
3. A shot cannot close with an end state that contradicts its declared visible action.
4. A `PLAN_ONLY` shot may become plan-ready from validated planned dependencies but cannot become artifact-`ACCEPTED`; a generation path cannot enter `RUNNING` when a required dependency state is unresolved or lacks the accepted observed boundary required by its profile.
5. A capability profile cannot claim support solely because a model name is present.
6. A `LOCKED` retention rule remains active until an explicit, reviewed scene change; generation drift is failure, not an implicit unlock.
7. Only the active speaker receives sustained speech articulation for its dialogue interval.
8. Audio event timestamps must fall within or intentionally bridge the visible event interval.
9. A `PASS` quality result requires a current executed observation appropriate to the criterion, and its aggregate check status must obey the observation rule above; predictions and prose explanations cannot satisfy it.
10. A recompiled prompt must preserve stable intent, state, references, and constraints unless the revision records a deliberate decision.
11. A fallback must disclose which requirement is weakened and what compensating review is required.
12. No execution plan may contain a secret, guessed endpoint, or unsupported node/model capability.

## Canonical prompt view

The conceptual output remains backwards-compatible with the blueprint:

```yaml
canonical_prompt_view:
  schema_version: 1
  canonical_revision: scene_001_rev1
  profile_reference: null
  sections:
    subject_and_identity: []
    setting_and_time: []
    action_sequence: []
    performance: []
    camera: []
    lighting_and_style: []
    audio_or_sync: []
    continuity: []
    constraints: []
    references: []
  mappings: []
  omissions: []
  presentation:
    subject_definitions: []
    environment_definitions: []
    summary: ""
    retention_analysis: []
    detailed_description: ""
    global_physical_constraints: []
    cinematography: {}
    overall_soundscape: {}
    negative_constraints: []
```

`sections`, `mappings`, and `omissions` are the normative canonical projection. The legacy blueprint presentation fields are nested under `presentation`; they are not a second top-level contract. `CompiledPrompt` remains the adapter-specific derived output. Structured attachments (shot table, state ledger, audio timeline, capability report, and QA checklist) carry the semantics that cannot safely fit in prose.

## Contract failure modes

| Failure | Signal | Repair |
|---|---|---|
| ID or revision is silently rewritten | historical evidence no longer resolves | create a superseding revision and preserve the old record |
| `UNKNOWN` is treated as a default | missing material field has no evidence or question | keep it unknown and route to the relevant gate |
| planned state is presented as observed | no artifact/procedure/timestamp | create an observation or downgrade the claim |
| execution provenance is missing or output bytes change | no immutable attempt link, required hash, or current hash match | retain the attempt, block acceptance, recollect if needed, and re-run affected QA |
| profile support is inferred transitively | mode support is used to imply identity/audio/lipsync support | add per-feature evidence or return `UNKNOWN` |

## Open questions and related documents

Phase 1 must decide the serialization format, schema-validation tooling, tolerance units for media checks, and migration policy for major contract versions. Domain ownership is in [`domain-model.md`](domain-model.md); state semantics are in [`state-model.md`](state-model.md); acceptance and oracle classes are in [`acceptance.md`](acceptance.md).
