# Constraint system

Constraints are explicit controls and assertions attached to intent, scene entities, shots, capability profiles, and execution. They are not a universal list of negative prompts. Each constraint has a scope, a kind, a priority, an evidence status, and a validation method. Serialized enum values use the uppercase vocabulary in [`contracts.md`](contracts.md); lower-case words in prose are descriptive only.

## Contents

- [Taxonomy](#1-taxonomy)
- [Constraint families](#11-constraint-families)
- [Structure](#2-structure)
- [Precedence and conflict resolution](#3-precedence-and-conflict-resolution)
- [Negative and exclusion constraints](#4-negative-and-exclusion-constraints)
- [Constraint selection](#5-constraint-selection)
- [Rights, provenance, and human review](#6-rights-provenance-and-human-review)
- [Failure modes and repair routes](#7-failure-modes-and-repair-routes)
- [Open questions and related documents](#8-open-questions-and-related-documents)

## 1. Taxonomy

| Kind | Purpose | Example |
|---|---|---|
| `GENERATION_HINT` | Steer a model toward a desired result | “preserve the silver ring on the right hand” |
| `RUNTIME_CONTROL` | Bind a workflow or API parameter | width, height, seed, frame count, FPS |
| `INPUT_REQUIREMENT` | Require an asset or capability before execution | first frame, audio track, mask |
| `QA_ASSERTION` | Check an output after generation | “van remains on camera-left” |
| `ASSEMBLY_RULE` | Govern edit, audio, or transition behavior | no duplicate frames at join |
| `RIGHTS_SAFETY` | Restrict use or require provenance/consent | approved likeness reference |

These kinds are deliberately separate. A prompt hint cannot substitute for a runtime control, and a runtime control cannot guarantee a visual assertion.

## 1.1 Constraint families

| Family | Typical risk | Global examples | Shot-specific examples |
|---|---|---|---|
| Anatomy | malformed bodies, hands, feet, animal form | subject species, limb count, joint plausibility | hand reaches the correct handle |
| Contact/collision | near-contact mistaken for contact, intersections | interaction policy and safe contact | hand/paw/object contact points |
| Articulation/mechanics | doors, tools, wheels, suspension morph | vehicle/object geometry and parts | door angle, wheel rotation, latch phase |
| Gravity/force | floating, impossible acceleration, balance | world gravity/scale assumption | throw arc, fall, braking, recoil |
| Vehicle/road | sliding, static wheels, impossible turn | vehicle geometry, wheel count, road rules | speed phase, steering, tire-road contact |
| Environment/lighting | location, weather, shadow, reflection drift | Scene Bible anchors and lighting direction | rain intensity at a boundary |
| Temporal | flicker, state skip, recursive degradation | project timebase and frame policy | visible action interval and transition |
| Identity/reference | face, wardrobe, product, mark drift | retention matrix and provenance | property lock for the active shot |
| Cinematic | axis, eyeline, framing, exposure discontinuity | camera language and coverage policy | movement phase or motivated cut |

Global constraints define invariants that persist across the project/scene. Shot-specific constraints bind a local action, camera, asset, or observation. A local constraint may refine a global one but cannot silently weaken it; an intentional change creates a state transition and a new scope.

## 2. Structure

```yaml
constraint:
  constraint_id: con_identity_ring_001
  subject: char_mara
  kind: GENERATION_HINT
  statement: preserve silver ring on right hand
  priority: HIGH
  scope: [shot_001, shot_002, shot_003]
  evidence: {status: PROPOSED, claim_type: ASSUMPTION, confidence: MEDIUM}
  validation:
    method: human_or_vision_review
    blocking: true
  fallback: REANCHOR_WITH_REFERENCE
  status: PROPOSED
```

The canonical fields are:

- `constraint_id`: stable identifier;
- `subject`: entity, shot, transition, artifact, or project;
- `kind`: taxonomy value above;
- `statement`: human-readable intent;
- `parameters`: machine-readable values when applicable;
- `priority`: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`;
- `scope`: explicit target set;
- `evidence`: source of the constraint;
- `validation`: oracle, threshold, or review rule;
- `fallback`: downgrade, split, retry, re-anchor, or block;
- `status`: `PROPOSED`, `ACTIVE`, `SATISFIED`, `VIOLATED`, `WAIVED`.

## 3. Precedence and conflict resolution

The planner resolves conflicts in this order:

1. rights, safety, consent, and hard input requirements;
2. story causality and explicit user constraints;
3. identity and continuity invariants;
4. physical plausibility and interaction correctness;
5. camera, audio, and style preferences;
6. optimization preferences such as speed or cost.

Within one level, a narrower scope wins over a broad default and an explicit user statement wins over an inference. An unresolved conflict remains visible in the plan; it is not silently overwritten.

## 4. Negative and exclusion constraints

Negative constraints are phrased by failure mode and scope:

```yaml
- constraint_id: con_no_identity_drift
  kind: QA_ASSERTION
  statement: do not change Mara's hair length, jacket color, or ring hand
  scope: [sequence_01]
  validation: identity_comparison
  priority: CRITICAL
- constraint_id: con_no_unmotivated_camera_flip
  kind: QA_ASSERTION
  statement: do not cross the established action axis without a motivated transition
  scope: [shot_002, shot_003]
  validation: camera_continuity_review
  priority: HIGH
```

The compiler may translate these to model-specific negative conditioning, but the QA assertion remains authoritative because prompt negation is not a guarantee.

## 5. Constraint selection

Constraint selection is risk-based. The planner includes a compact set that addresses the active failure modes, rather than flooding every prompt with unrelated exclusions. Selection considers:

- identity and reference retention;
- participant count and contact risk;
- motion complexity and speed;
- text, dialogue, and lip-sync exposure;
- camera movement and axis changes;
- model capability and known failure modes;
- rights, provenance, and consent requirements.

The selected set is recorded so that an evaluation can distinguish a model failure from an omitted constraint.

## 6. Rights, provenance, and human review

Likeness, voice, copyrighted assets, and external references require explicit rights and consent statuses. A reference may be `CONFIRMED`, `UNKNOWN`, `RESTRICTED`, `REJECTED`, or `NOT_APPLICABLE`; `RESTRICTED` and `REJECTED` assets are blocked, while `UNKNOWN` requests review when the risk profile requires it. These serialized values are owned by [`contracts.md`](contracts.md).

Outputs should retain source references, model/version identifiers, workflow or API metadata, seeds where available, and any human approval decisions. Provenance metadata is an operational requirement, not a decorative annotation.

## 7. Failure modes and repair routes

| Failure | Detection | Repair |
|---|---|---|
| Universal negative-prompt bloat | selected constraints do not map to an active risk | remove unrelated exclusions and keep a risk-specific assertion |
| Guidance presented as enforcement | no runtime control or post-generation oracle | label the guidance and add the missing control/review |
| Shot rule silently weakens a global invariant | scope/precedence conflict | create an explicit state transition or block |
| Rights or provenance is missing | unknown/restricted asset reaches execution planning | stop at the safety gate and request evidence |

## 8. Open questions and related documents

Phase 1 must choose the machine-readable constraint schema, numeric tolerances for contact/temporal checks, and the boundary between model-assisted and human plausibility review. Domain/state semantics are in [`contracts.md`](contracts.md) and [`state-model.md`](state-model.md); safety ownership is in [`safety-boundaries.md`](safety-boundaries.md); failure/eval coverage is in [`failure-and-evals.md`](failure-and-evals.md).
