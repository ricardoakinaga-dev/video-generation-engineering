# State model

## Purpose

Define what persists, what changes, what is computed, and what counts as evidence across a scene and its generated artifacts. This is the state contract used by the continuity engine.

## Four state classes

| Class | Meaning | Example | Mutation rule |
|---|---|---|---|
| `IMMUTABLE` | Historical fact or ID that cannot be rewritten | `project_id`, source hash, original user line | Create a revision or superseding record |
| `PERSISTENT` | Intended invariant carried across a declared scope | character identity, vehicle geometry, world anchor | Change only through explicit reviewed transition |
| `TRANSIENT` | Current pose, position, occupancy, action, or event state | hand on handle, door open, gaze target | Must advance through an action/state delta |
| `DERIVED` | Computed from other state/evidence | complexity label, frame count, retention risk | Recompute when inputs change; never hand-edit as fact |

## Canonical examples

```yaml
state_ledger:
  char_mara:
    identity: {class: PERSISTENT, value: ref_mara_v1, evidence: planned}
    wardrobe: {class: PERSISTENT, value: yellow_rain_jacket, evidence: planned}
    position: {class: TRANSIENT, value: platform_right, evidence: observed}
    gaze: {class: TRANSIENT, value: van_rear_door, evidence: planned}
    identity_risk: {class: DERIVED, value: high, inputs: [retention, visibility, drift_history]}
  prop_red_van:
    geometry: {class: PERSISTENT, value: van_ref_v1, evidence: planned}
    door_state: {class: TRANSIENT, value: open, evidence: observed}
    wheel_state: {class: TRANSIENT, value: stopped, evidence: observed}
  environment_platform:
    anchors: {class: PERSISTENT, value: [tracks_left, shelter_column_3]}
    weather: {class: TRANSIENT, value: heavy_rain, evidence: observed}
    time_of_day: {class: PERSISTENT, value: night, change_requires: declared_transition}
```

## Planned versus observed state

Every field may carry separate `planned`, `observed`, and `confidence` values. Planned state says what the shot was supposed to show. Observed state says what the artifact or runtime actually showed. A planned `door_state: open` cannot be used as evidence that the output door opened.

In the example below, `planned` and `observed` are state channels, not values from the evidence-status enum. Evidence status remains `CONFIRMED`, `INFERRED`, `PROPOSED`, or `UNKNOWN` when a field needs claim metadata.

```text
desired truth → planned state → runtime/artifact observation
      │              │                    │
      └──────────────┴───── repair does not erase history
```

## State transitions

An action transition contains:

```yaml
state_delta:
  delta_id: delta_001
  scope: shot_003
  cause: interaction:int_open_van
  before:
    prop_red_van.door_state: closed
    char_mara.right_hand: free
  action: [reach, contact, pull]
  after:
    prop_red_van.door_state: open
    char_mara.right_hand: door_handle
  evidence: planned
```

Transitions are valid when the action can cause the after state, the domains required by the next shot are complete enough, and no inherited state is contradicted. A transition is invalid when a state changes without cause, an object appears in two incompatible locations, or an actor reacts before the stimulus exists.

## Lifecycle states

```text
project: INTAKE → PLANNING → READY_FOR_GENERATION → GENERATING → REVIEW
         → ACCEPTED | REVISION_REQUIRED | ABORTED
shot:    PLANNED → READY → RUNNING → GENERATED → REVIEW
         → ACCEPTED | REGEN_REQUIRED | REJECTED | SUPERSEDED
observation: NOT_RUN → PASS | PARTIAL | FAIL | BLOCKED
```

`UNKNOWN` is an evidence value, not a lifecycle state. A required unknown blocks readiness when the relevant gate cannot tolerate it.

`shot.lifecycle_status` and `ArtifactObservation.status` must remain separate. The former records where the shot is in its production lifecycle (`PLANNED`, `READY`, `RUNNING`, `GENERATED`, `REVIEW`, `ACCEPTED`, `REGEN_REQUIRED`, `REJECTED`, or `SUPERSEDED`); the latter records the aggregate QA result (`NOT_RUN`, `PASS`, `PARTIAL`, `FAIL`, or `BLOCKED`). QA never writes its result into the shot lifecycle field.

The absence cases are also distinct: a `PLANNED`/`READY` shot without an artifact has no QA observation; a `RUNNING` shot without output remains `RUNNING`; and a `GENERATED` shot with a collected artifact but no inspection remains `GENERATED` while its collection record is `NOT_STARTED` (or a pending QA record is `NOT_RUN`). Starting review changes the lifecycle to `REVIEW`; only an accepted observation can lead to `ACCEPTED`.

An `ExecutionAttempt` is immutable runtime evidence between the plan and the collected artifact. It records one submission's profile/model/runtime/node/workflow/input/parameter context and receives a new ID for every retry. `GenerationArtifact.execution_attempt_ref` identifies the attempt that produced it, while `artifact_ref` is only a locator and `content_hash` identifies the bytes collected at that point. An `ArtifactObservation` must carry the artifact reference and the hash observed during QA; a path overwrite or hash mismatch invalidates the observation and requires recollection and revalidation before acceptance.

## Valid and invalid examples

| Transition | Result | Reason |
|---|---|---|
| Shot 4 ends with `door=open`; Shot 5 starts `door=open` | Valid | State is inherited without contradiction |
| Shot 4 ends `door=open`; Shot 5 starts `door=closed` with a visible close action | Valid | Intervening action declares the change |
| Shot 4 ends `door=open`; Shot 5 starts `door=closed` with no cause | Invalid | Silent contradiction |
| Character looks at a van; next shot reacts to a sound not declared in the audio/beat state | Invalid or unresolved | Stimulus is missing |
| Output shows a hand near a handle; plan claims contact is complete | Observation partial | Visual proximity is not contact proof |

## Repair policy

Repair the smallest owning layer: add a missing state delta, split a dense interaction, re-anchor identity/geometry, reframe camera coverage, adjust audio timing, switch profile, or request human review. Preserve the original desired and planned states, record the changed fields, and re-evaluate the affected downstream states.

## Open questions

The implementation must choose a serialization for tri-state planned/observed fields and a tolerance language for continuous values such as position, exposure, and timing. These remain open in [`open-questions.md`](open-questions.md).
