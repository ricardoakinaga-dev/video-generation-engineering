# Directing layer

The directing layer translates intent and scene state into actionable guidance for story, performance, camera, interaction, motion, and audio. It is model-agnostic: it describes the desired result before a model adapter decides how to encode it.

## Contents

- [Story engine](#1-story-engine)
- [Character and relationship direction](#2-character-and-relationship-direction)
- [Dialogue and performance](#3-dialogue-and-performance)
- [Interaction decomposition](#4-interaction-decomposition)
- [Motion direction](#5-motion-direction)
- [Cinematography and camera continuity](#6-cinematography-and-camera-continuity)
- [Audio and lip-sync direction](#7-audio-and-lip-sync-direction)
- [Failure modes and repair routes](#8-failure-modes-and-repair-routes)
- [Open questions and related documents](#9-open-questions-and-related-documents)

## 1. Story engine

The story engine preserves causality and dramatic purpose at shot level. Each beat should answer:

- what changes;
- who causes the change;
- what the audience must notice;
- what state must be true at the end;
- why the next beat depends on it.

Action density is estimated separately from duration. A beat with one visible action can be low density even when long; a short beat containing approach, contact, dialogue, reaction, and camera movement is high density.

```yaml
beat:
  beat_id: beat_01
  dramatic_function: reveal_and_commit
  cause: Mara recognizes the van
  action: Mara crosses the platform and opens the rear door
  audience_focus: recognition_then_hand_contact
  emotional_change: guarded_to_decisive
  exit_condition: door_open_and_Mara_inside
```

The story engine may propose a shot split when the action density, number of participants, or continuity risk exceeds the selected model's stable range.

## 2. Character and relationship direction

Character state is represented as a combination of stable identity, current physical state, objective, emotional state, attention, and action readiness. Relationships add power, trust, distance, and immediate intention.

```yaml
character_direction:
  character_id: char_mara
  objective: retrieve_the_case
  emotional_state: controlled_urgency
  attention_target: prop_red_van
  physical_state: wet_and_breathless
  performance_notes:
    - keep shoulders guarded until the door opens
    - release tension only after contact succeeds
```

Relationship direction is not a personality label alone. It must influence observable behavior: distance, gaze duration, turn-taking, interruption, posture, and willingness to make contact.

## 3. Dialogue and performance

Dialogue is decomposed into semantic content, speaker, timing, delivery, gaze, gesture, and reaction. Text alone is insufficient for a multi-character shot.

```yaml
dialogue_line:
  line_id: line_001
  speaker: char_mara
  text: "Is it still there?"
  target_listener: char_jo
  delivery: low_breathless_question
  start_condition: after_mara_sees_van
  end_condition: before_hand_reaches_handle
  required_reaction: Jo looks at the case, then at Mara
  audio_mode: generated_or_recorded
```

The planner must flag unresolved speaker assignment, overlapping lines, impossible timing, and dialogue that requires a face close-up unavailable in the shot plan.

Performance intent includes micro-behavior only when it is useful and observable. Avoid stacking dozens of adjectives; prefer a small set of physical instructions tied to an action or emotional transition.

## 4. Interaction decomposition

Interactions are written as action phases, not as a compressed verb phrase:

```text
approach → orient → reach → contact → act → observe result → react → release
```

Not every phase must appear in one shot. The director chooses coverage based on story importance, contact risk, model capability, and continuity budget. The prompt compiler receives the selected phases and their visible success condition.

## 5. Motion direction

Motion uses a small vocabulary of primitives with constraints:

- translate, rotate, accelerate, decelerate;
- reach, grasp, pull, push, release;
- turn head, shift gaze, step, kneel, rise;
- breathe, recoil, brace, follow, overtake;
- camera pan, tilt, dolly, truck, orbit, crane, rack focus.

Every important motion has an actor, target, direction, approximate phase, and termination condition. “Dynamic movement” is not an executable motion specification.

```yaml
motion_primitive:
  primitive_id: move_driver_to_handle
  actor: char_driver
  verb: reach
  target: vehicle_001.rear_door_handle
  phase: contact
  timing: {start_s: 2.0, duration_s: 0.8}
  acceleration: eased_in_out
  balance: maintain_support_on_left_foot
  gravity: grounded
  mechanics: hand_follows_handle_axis; door_resists_until_latch_release
  start_condition: driver_is_beside_vehicle
  termination_condition: right_hand_contacts_handle
```

The timing, acceleration/deceleration, balance/gravity, and mechanics fields are planning obligations, not numeric guarantees from a model. If the profile cannot represent or observe them, the shot is split, downgraded, or routed to review.

## 6. Cinematography and camera continuity

Camera direction has two layers: shot-level composition and sequence-level continuity. Shot-level direction covers subject priority, framing, lens feel, camera height, depth, light, and movement. Sequence-level direction covers axis, screen direction, movement phase, cut motivation, and visual rhythm.

```yaml
camera:
  shot_id: shot_002
  framing: MEDIUM_TRACKING
  angle: EYE_LEVEL
  focal_length: 35mm_equivalent
  focus: char_mara
  depth_of_field: MODERATE
  motion_blur: NATURAL
  exposure: LOCKED_TO_SCENE
  lighting: scene_bible_lighting
  eyeline: prop_red_van
  subject_priority: [char_mara, prop_red_van]
  lens_feel: NATURAL_35MM
  camera_height: EYE_LEVEL
  movement:
    type: LATERAL_TRACK
    direction: RIGHT_TO_LEFT
    phase: FOLLOW_APPROACH
  axis_policy: PRESERVE_180_AXIS
  edit_rhythm: HOLD_THROUGH_CONTACT
  cut_motivation: reveal_van_at_gaze_target
```

Camera movement must not contradict actor movement or the continuity state. If the camera crosses the axis intentionally, the plan records the transition and provides a visual motivation or neutralizing shot.

## 7. Audio and lip-sync direction

Audio is planned as layers:

1. dialogue or vocal performance;
2. diegetic effects tied to visible causes;
3. ambience and room tone;
4. score or non-diegetic music;
5. synchronization and mix metadata.

Audio can be generated, supplied, or assembled separately. A video model that accepts audio is not assumed to generate every audio layer or to provide reliable lip-sync. The plan records the audio source and synchronization strategy per layer.

```yaml
audio:
  dialogue: { mode: supplied, asset_ref: audio_line_001, sync: phoneme_or_model }
  effects:
    - event: van_door_latch
      source: generated_or_library
      trigger: door_open_and_hand_released
  ambience: { asset_ref: rain_platform_loop, loopable: true }
  mix_target: stereo
```

Lip-sync is a separate feasibility decision. It requires speaker assignment, face visibility, duration, phonetic timing, and a compatible generation or post-processing path. A talking-head path and an action-heavy path may need different adapters.

## 8. Failure modes and repair routes

| Failure | Detection | Repair |
|---|---|---|
| Adjective-only performance | no observable behavior tied to a beat | add a sparse physical performance beat |
| Contact is asserted by proximity | no contact point or result checkpoint | split setup/contact/result coverage |
| Dialogue and action compete for one mouth window | interval or active-speaker conflict | split coverage, use cutaway/voiceover, or use a validated lip-sync path |
| Camera movement breaks geography | axis/eyeline/movement phase conflict | motivate, reframe, or add a transition |
| Audio event has no cause | event is not tied to a visible or declared source | re-time, replace, or mark non-diegetic |

## 9. Open questions and related documents

The first profile with reliable visible speech, the tolerance for human-review performance judgments, and the preferred representation of phonetic timing remain open. Shared fields and statuses are in [`contracts.md`](contracts.md); continuity semantics are in [`continuity-engine.md`](continuity-engine.md); audio/profile evidence is in [`model-adaptation.md`](model-adaptation.md) and [`research.md`](research.md).
