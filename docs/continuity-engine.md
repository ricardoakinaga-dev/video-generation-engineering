# Continuity engine specification

## Purpose

Turn a shot graph into a validated sequence of state transitions. The continuity engine is the primary defense against identity, object, spatial, temporal, camera, dialogue, audio, and world contradictions across shots.

## Contents

- [Purpose](#purpose)
- [Terminology](#terminology)
- [State domains](#state-domains)
- [Algorithm](#algorithm)
- [Inheritance rules](#inheritance-rules)
- [Conflict detection](#conflict-detection)
- [Valid transition](#valid-transition)
- [Invalid transition](#invalid-transition)
- [Anchor strategy](#anchor-strategy)
- [Repair contract](#repair-contract)
- [Failure modes](#failure-modes)
- [Related documents and open questions](#related-documents-and-open-questions)

## Terminology

- `START_STATE`: accepted or planned state entering a shot.
- `ACTION`: observable operations the shot intends to depict.
- `END_STATE`: state the shot claims to leave visible.
- `STATE_DELTA`: named changes caused by an action or declared transition.
- `STATE_CHANNEL`: `PLANNED` for a plan traversal or `OBSERVED` for an executed artifact observation.
- `INHERITANCE`: copying the latest valid state from a dependency in the active channel.
- `CONFLICT`: incompatible inherited, planned, or observed values.
- `REPAIR`: smallest change that restores an invariant or escalates to review.

## State domains

| Domain | Tracks | Typical evidence |
|---|---|---|
| Identity | face, hair, marks, wardrobe, voice identity | reference/visual review |
| Spatial | position, orientation, screen direction, occlusion | shot plan/frame review |
| Object | possession, orientation, articulation, damage | state delta/artifact |
| Interaction | contact points, ownership, gaze, force phase | contact graph/review |
| Temporal | action phase, elapsed time, weather/light progression | timeline/state ledger |
| Camera | axis, side, lens intent, movement phase, eyeline | camera plan/review |
| Dialogue | speaker, line interval, turn, reaction | script/audio/visual review |
| Audio | room tone, diegetic events, voice, mix, sync | audio timeline/media check |
| World | geography, anchors, lighting, weather, recurring background | Scene Bible/review |

## Algorithm

For each shot in topological order, the engine receives a propagation mode and keeps the state channel visible:

1. initialize the first shot from the Scene Bible's explicit `initial_state_ref` (or an equivalent declared scene-start state); if no initial state exists, create an unresolved `START_STATE` and keep the plan from becoming ready;
2. in `PLAN_ONLY`, select the latest valid **planned** `END_STATE` from each dependency and mark the new state channel `PLANNED`; this is a validated plan, not an accepted observation;
3. in an execution traversal that crosses an artifact boundary, select the latest accepted **observed** state from each required dependency; if it is absent, the dependent generation path is `BLOCKED` even when a planned state exists;
4. apply declared intentional transitions to the selected channel without converting planned state into observed state;
5. create `START_STATE` with domain-level evidence, channel, source references, and unresolved fields;
6. validate required references, anchors, participant states, and capabilities;
7. check that each action has a causal precondition and possible end state;
8. derive `END_STATE` and `STATE_DELTA` without mutating persistent invariants, then attach continuity obligations and acceptance gates;
9. after generation, register the collected `GenerationArtifact` for provenance; only after an executed QA procedure compare its `ArtifactObservation` to the plan and write an `OBSERVED` state from that executed observation;
10. record the executed quality result in `ArtifactObservation.status` according to the aggregate rule, then update `shot.lifecycle_status` only through the allowed shot lifecycle transitions; route a repair to the smallest owner without copying a QA value into the shot state.

The two outputs remain separate at every boundary:

| Evidence/result | Owning field | Permitted effect on a shot |
|---|---|---|
| `PLANNED`/`READY`, no artifact and no QA record | no `ArtifactObservation` | Preserve the current planning lifecycle; a plan-only shot cannot become artifact-accepted |
| `RUNNING`, no output yet | execution progress record, not QA | Preserve `RUNNING`; do not regress to `PLANNED`/`READY` and do not create an observation without an artifact/procedure |
| `GENERATED`, artifact collected, QA not started | `GenerationArtifact.quality_review.lifecycle: NOT_STARTED` | Preserve `GENERATED`; absence of QA does not change the shot lifecycle |
| `REVIEW`, pending QA record with `status: NOT_RUN` | `ArtifactObservation.status` | Preserve `REVIEW`; the pending record has no executed procedure/checks and cannot support acceptance |
| `PASS` | `ArtifactObservation.status` | After `GENERATED`/`REVIEW`, permit the lifecycle transition to `ACCEPTED` |
| `PARTIAL` or `FAIL` | `ArtifactObservation.status` | Keep the artifact in `REVIEW` and route to `REGEN_REQUIRED` or `REJECTED` by the repair decision |
| Pre-artifact `BLOCKED` | compatibility/issue result, not a shot status | Do not enter `RUNNING`; keep the shot `PLANNED`/`READY` until the blocker is resolved |
| Post-artifact `BLOCKED` | `ArtifactObservation.status` | Keep the shot in `REVIEW` with an explicit repair route; `BLOCKED` is never a shot lifecycle value |

The propagation decision is therefore explicit: `PLAN_ONLY` can produce a complete planned graph for shots that have no artifacts yet, while `LOCAL_EXECUTE` and `CLOUD_EXECUTE` cannot claim an observed boundary that has not been accepted. `LOCAL_DRY_RUN` may validate the workflow and bindings but remains plan-only for continuity and cannot mark a shot artifact-accepted.

For example, a two-shot plan with no generated artifacts is valid when its Scene Bible supplies the initial state:

```yaml
continuity_run:
  mode: PLAN_ONLY
  state_channel: PLANNED
  initial_state_ref: scene_bible:scene_001:initial
  shots:
    - id: shot_001
      dependency_ids: []
      start_state_ref: scene_bible:scene_001:initial
      end_state_delta: {char_mara.position: platform_center}
    - id: shot_002
      dependency_ids: [shot_001]
      start_state_ref: continuity:shot_001:planned_end
      end_state_delta: {char_mara.gaze: toward_train}
  artifact_observations: []
  result: PLANNED_GRAPH_ONLY
```

The result above does not assert that either action appeared in media. When a later accepted observation contradicts `shot_001`, the engine preserves the observation and planned state, marks that boundary `CONFLICTED`, and invalidates only the direct or transitive dependent planned states that consume the changed domain. Unrelated domain states and shots remain current; the affected suffix is replanned from the nearest stable ancestor.

The engine does not infer a missing historical state from a later frame without labeling that inference and checking whether the gap is material.

## Inheritance rules

- In `PLAN_ONLY`, inherit only the latest valid planned relevant state; in an execution traversal, inherit the latest accepted observed state required by the boundary—not an arbitrary earlier prompt or frame.
- Persistent invariants remain active until a reviewed scene transition changes them.
- Transient states advance through a named action or a declared cut/transition.
- An anchor carries only the properties it claims to carry; an image does not automatically anchor audio, physics, or identity.
- Observed contradictions are retained as evidence and cannot be “repaired” by rewriting the previous observation.

## Conflict detection

```yaml
continuity_conflict:
  conflict_id: CON-003
  boundary: shot_004 → shot_005
  domain: object
  inherited: prop_red_van.door_state=open
  planned: prop_red_van.door_state=closed
  cause_found: false
  severity: HIGH
  route: REPAIR_REQUIRED
```

Conflict severity is `CRITICAL` when it changes identity, story causality, rights/safety, or a user hard constraint; `HIGH` when it breaks physical or camera plausibility; `MEDIUM`/`LOW` when it affects optional style. `UNKNOWN` is distinct from conflict: unknown asks for evidence, while conflict has incompatible values. These serialized values follow [`contracts.md`](contracts.md).

## Valid transition

```text
Shot 004 END_STATE: Mara beside van; right hand free; rear door closed
Shot 005 ACTION: approach → reach → contact → pull
Shot 005 END_STATE: Mara beside van; right hand on handle; rear door open
Shot 006 START_STATE: rear door open; Mara's hand released; torso rotating inward
```

The hand release and torso rotation must be either visible in Shot 005 or explicitly covered by Shot 006's entry action. The next shot cannot assume both without an accepted state boundary.

## Invalid transition

```text
Shot 004 END_STATE: vehicle stopped, door closed
Shot 005 PROMPT: Mara is already seated, door open, van driving
```

This compresses approach, opening, entry, ignition, and driving into unobserved transitions. The repair is to split the action, change the shot purpose, or explicitly mark a time jump with a transition—not to keep the contradiction hidden in prose.

## Anchor strategy

The engine recommends one of:

- `canonical_reference`: reapply the stable identity/world reference;
- `accepted_last_frame`: use only when the profile and observed frame are sufficient;
- `first_last_frame`: use only with confirmed endpoint capability and endpoint QA;
- `keyframe_reset`: regenerate a canonical entry image before a new segment;
- `human_review`: require approval when no automatic anchor can preserve a critical property.

Recursive last-frame propagation is bounded by a drift budget and periodic canonical re-anchoring. A good-looking intermediate frame is not automatically a trustworthy anchor.

## Repair contract

```yaml
repair:
  issue_id: CON-003
  owner: continuity_engine
  preserve: [scene_intent, char_mara.identity, van.geometry]
  change: split_shot_005_into_setup_and_entry
  weakened_requirement: none
  new_dependencies: [shot_005a, shot_005b]
  recheck: [QG-06, QG-07, QG-08, QG-17]
  human_review: false
```

If a repair weakens a hard requirement, the outcome is `DEGRADED` or `BLOCKED` until a human accepts it. The continuity engine never silently promotes a flexible property to locked or vice versa.

## Failure modes

| Failure | Signal | Repair |
|---|---|---|
| Identity drift | invariant mismatch in dependent artifact | re-anchor/split/review |
| State contradiction | boundary values incompatible | add delta/transition or block |
| Temporal jump | action phase skipped | add bridge shot or declare time jump |
| Camera discontinuity | axis/side/movement phase breaks | motivate transition/reframe |
| Reference decay | anchor property weakens over chain | canonical reset and revalidate |
| False observation | plan treated as output proof | run artifact inspection |

## Related documents and open questions

The shared schema and invariant owner is [`contracts.md`](contracts.md); scene-level planning is [`scene-and-continuity.md`](scene-and-continuity.md); the state classes are [`state-model.md`](state-model.md). Open questions about tolerances and automatic visual oracles are in [`open-questions.md`](open-questions.md).
