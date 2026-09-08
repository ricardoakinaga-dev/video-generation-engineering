# Golden scenarios

## Purpose

These are future-evaluable, known-good planning fixtures. They test decisions and invariants rather than exact prose. Each fixture has the same contract: input intent, references, risk analysis, expected planning decisions, continuity strategy, decomposition, constraints, output class, and failure conditions.

## Fixture contract

```yaml
golden_scenario:
  id: G-001
  input_intent: "..."
  references: []
  risk_analysis: []
  expected_planning_decisions: []
  continuity_strategy: []
  decomposition: []
  constraints: []
  output_class: SUPPORTED_PLAN
  failure_conditions: []
```

`SUPPORTED_PLAN` means the plan is internally complete, not that a stochastic model is guaranteed to produce a perfect artifact. A fixture may intentionally expect `DEGRADED_PLAN`, `BLOCKED`, or `HUMAN_REVIEW_REQUIRED` when that is the correct graceful behavior.

## Contents

The anchors below follow the adopted GitHub heading-slug convention: punctuation such as `—` is removed while the spaces around it remain, so the separator is represented by two hyphens.

- [G-001 — Simple cinematic portrait](#g-001--simple-cinematic-portrait)
- [G-002 — Veterinarian examining a dog](#g-002--veterinarian-examining-a-dog)
- [G-003 — Human/animal interaction](#g-003--humananimal-interaction)
- [G-004 — Two-character conversation](#g-004--two-character-conversation)
- [G-005 — Walking-and-talking](#g-005--walking-and-talking)
- [G-006 — Person handing an object](#g-006--person-handing-an-object-to-another-person)
- [G-007 — Product commercial](#g-007--product-commercial)
- [G-008 — Vehicle entry](#g-008--person-approaching-and-entering-a-vehicle)
- [G-009 — Automotive driving sequence](#g-009--automotive-driving-sequence)
- [G-010 — 30-second commercial](#g-010--30-second-commercial)
- [G-011 — 60-second dialogue/action commercial](#g-011--60-second-dialogueaction-commercial)
- [G-012 — Multi-reference high-complexity scene](#g-012--multi-reference-high-complexity-scene)

## G-001 — Simple cinematic portrait

- **Input intent:** A single adult subject stands in a quiet interior for six seconds, looks from window to camera, and conveys restrained optimism in a cinematic natural-light portrait.
- **References:** One optional portrait for broad identity/wardrobe; no motion or audio reference.
- **Risk analysis:** Low participant count and low interaction risk; medium identity risk if the face is prominent; low temporal dependency.
- **Expected planning decisions:** Route `CINEMATIC`; create one shot with subject, gaze change, framing, light direction, duration, and one identity retention rule; do not create a long-form timeline or contact graph.
- **Continuity strategy:** Establish a single entry/exit state; preserve face, hair, wardrobe, window geography, and screen direction within the shot.
- **Decomposition:** `settle → look_to_window → processing_beat → look_to_camera`; keep micro-expression direction observable and sparse.
- **Constraints:** No identity drift, no extra subjects, natural eye movement, stable background, no unmotivated camera jump.
- **Output class:** `SUPPORTED_PLAN`; one-shot prompt view plus minimal QA checklist.
- **Failure conditions:** Planner invents multiple shots, loads long-form references, treats a portrait reference as a pixel lock, or omits the gaze/action timing.

## G-002 — Veterinarian examining a dog

- **Input intent:** A veterinarian gently examines a seated dog’s front paw in a bright clinic, explains the finding to the owner, and the dog remains calm for ten seconds.
- **References:** Dog photo for species/markings; optional clinic reference; no voice reference required.
- **Risk analysis:** Two subjects, animal anatomy, human-animal contact, dialogue, and hand/paw geometry; medium-high interaction risk.
- **Expected planning decisions:** Route `PRODUCTION`; create a Scene Bible for dog markings and clinic anchors; separate examination action from dialogue if face/mouth timing conflicts; require contact graph.
- **Continuity strategy:** Carry paw identity, dog posture, veterinarian hand, owner position, exam table, and light direction; validate before/after paw state.
- **Decomposition:** `greet → stabilize_dog → reach_paw → contact → examine → release → explain → owner_reacts`; split close-up contact if needed.
- **Constraints:** Correct species anatomy, four paws, gentle contact, no extra limbs, hand/paw contact, active speaker only, no premature owner reaction.
- **Output class:** `SUPPORTED_PLAN` with conditional audio/lip-sync path.
- **Failure conditions:** Dog morphs species/markings, paw contact is claimed without contact phase, owner mouths the veterinarian’s line, or the exam result appears before inspection.

## G-003 — Human/animal interaction

- **Input intent:** A child tosses a soft ball to a friendly dog in a park; the dog runs after it and returns it in twelve seconds.
- **References:** Dog reference for coat pattern; optional park composition reference; child likeness status must be declared.
- **Risk analysis:** Human-animal motion, object flight/ownership, running path, child safety, and multiple reactions; high contact/occlusion risk.
- **Expected planning decisions:** Route `PRODUCTION`; use a ball ownership and trajectory state; choose short segments or coverage instead of one overloaded generation; declare whether child identity is critical.
- **Continuity strategy:** Carry child position, dog path, ball location/velocity phase, gaze target, and park anchors; re-anchor after the throw if the dog runs out of frame.
- **Decomposition:** `hold → aim → throw → ball_flight → dog_chase → pickup → return → handoff/reaction`; separate pickup if mouth/object contact is unstable.
- **Constraints:** Dog anatomy, plausible gait, ball trajectory, no duplicate dog/ball, safe child distance, visible cause for reaction.
- **Output class:** `SUPPORTED_PLAN` or `DEGRADED_PLAN` if ball-mouth contact is not confirmed by the target profile.
- **Failure conditions:** Dog returns before the throw, ball teleports, dog has human anatomy, or the plan assumes reliable animal-object contact without mitigation.

## G-004 — Two-character conversation

- **Input intent:** Two colleagues discuss a missed train on a platform for fifteen seconds; one is defensive, the other becomes sympathetic.
- **References:** Two optional portrait references; platform reference for geography; voice references are optional and rights-tagged.
- **Risk analysis:** Turn-taking, gaze, reaction ordering, two identities, camera axis, and dialogue timing; high performance/camera risk.
- **Expected planning decisions:** Route `PRODUCTION`; create speaker/listener intervals, stimulus → processing → reaction beats, shot coverage, and an audio plan separate from visual generation.
- **Continuity strategy:** Preserve identity, wardrobe, relative screen positions, eyelines, platform anchors, and emotional state transitions; record whose turn is next at every boundary.
- **Decomposition:** `establish_two_shot → line_A → processing/reaction_B → line_B → softened_reaction_A`; use singles/cutaways where lip-sync risk is high.
- **Constraints:** Active speaker articulates; listener reacts without sustained mouthing; preserve 180-degree axis; no overlapping lines unless explicit.
- **Output class:** `SUPPORTED_PLAN` with profile-dependent lip-sync status.
- **Failure conditions:** Speaker changes, listener mouths line, reactions precede lines, axis flips, or dialogue is pasted into one undifferentiated prompt.

## G-005 — Walking-and-talking

- **Input intent:** Two friends walk through a market while exchanging one short story and end beside a red awning after twenty seconds.
- **References:** Two identity references; market layout/awning reference; optional recorded dialogue.
- **Risk analysis:** Moving camera, walking gait, dialogue, eyeline, background continuity, and destination state; high temporal/camera risk.
- **Expected planning decisions:** Use a shot graph with a walking direction and destination anchor; split dialogue/action if the selected profile cannot keep faces and gait stable; plan audio separately.
- **Continuity strategy:** Carry route, relative spacing, feet phase, screen direction, awning location, line turn, and emotional progression; use a canonical re-anchor before the destination beat.
- **Decomposition:** `establish_route → walk/listen → speak/reaction → approach_awning → arrive`; record cut motivation and camera movement phase.
- **Constraints:** Foot-ground contact, no drift in clothing/identity, stable market geography, speaker/listener timing, no camera-axis contradiction.
- **Output class:** `SUPPORTED_PLAN` as multiple short segments with assembly and continuity QA.
- **Failure conditions:** Characters arrive early, walk backward without intent, background loops incorrectly, or line timing contradicts visible mouth/action windows.

## G-006 — Person handing an object to another person

- **Input intent:** A courier hands a sealed envelope to a recipient at a doorway; ownership changes clearly in eight seconds.
- **References:** Envelope/doorway reference; identity references only if recurring.
- **Risk analysis:** Hand geometry, occlusion, ownership transfer, gaze, and articulated doorway; high contact risk but bounded action.
- **Expected planning decisions:** Use `PAT-INTERACTION-TRANSFER`; model the contact graph and ownership state; choose a medium setup plus contact insert when needed.
- **Continuity strategy:** Carry envelope orientation, hand occupancy, body side, doorway anchor, and before/after ownership; validate transfer before the recipient reacts.
- **Decomposition:** `approach → orient → present → reach → contact → transfer → release → recipient_reacts`.
- **Constraints:** Two hands and one envelope, no duplicate object, plausible reach, contact points, no reaction before transfer, preserve screen direction.
- **Output class:** `SUPPORTED_PLAN` with explicit interaction QA.
- **Failure conditions:** Envelope changes shape, ownership is ambiguous, recipient reacts before contact, hands merge, or plan claims transfer from proximity alone.

## G-007 — Product commercial

- **Input intent:** A premium watch rotates on a stone surface while a hand places it beside a folded jacket; a product line appears in the final three seconds.
- **References:** Product turntable/photographs, material/brand guidance, typography asset supplied separately.
- **Risk analysis:** Product geometry/material retention, hand-object contact, reflections, text legibility, camera movement, and rights/provenance.
- **Expected planning decisions:** Separate product identity from environment/style references; use controlled shots and a post-composed text path unless the profile proves text rendering; route product QA as critical.
- **Continuity strategy:** Lock product geometry, dial/brand marks, hand/wrist relation, surface anchors, and rotation phase; never use a degraded frame as a product master without review.
- **Decomposition:** `hero_establish → rotation → hand_place → beauty_hold → text/packaging`; keep text outside stochastic generation by default.
- **Constraints:** No logo mutation, no extra watch hands, correct reflections, contact/occlusion, stable material, text/brand rights review.
- **Output class:** `SUPPORTED_PLAN` with assembly/post-processing for text.
- **Failure conditions:** Product shape changes, brand text is hallucinated, reflections break geometry, or an unapproved reference is used.

## G-008 — Person approaching and entering a vehicle

- **Input intent:** A driver crosses a wet driveway, opens a compact car, sits, starts it, and closes the door in fifteen seconds.
- **References:** Driver identity/wardrobe; vehicle geometry; driveway/wet-light reference.
- **Risk analysis:** Human-vehicle contact, articulated door, body rotation, seat/leg occlusion, ignition causality, rain and reflections; very high interaction risk.
- **Expected planning decisions:** Route `DIRECTOR` or high `PRODUCTION`; create Scene Bible, contact graph, state deltas, and split setup/contact/entry/result coverage; do not rely on one long prompt.
- **Continuity strategy:** Carry vehicle geometry, door state, hand occupancy, body position, ignition, wheel state, weather, and camera axis; canonical re-anchor before entry if the door/identity drifts.
- **Decomposition:** `approach → reach_handle → contact → open_door → orient_body → lower_torso → legs_in → hand_release → ignition → close_door`.
- **Constraints:** Correct hand/handle contact, no impossible body geometry, door articulation, feet/ground, vehicle stays fixed until ignition, wheel/road contact, no reflection contradictions.
- **Output class:** `SUPPORTED_PLAN` as several short segments with anchor/reset strategy.
- **Failure conditions:** Door is open without cause, driver appears seated before entry, car moves before ignition, vehicle morphs, or last-frame chaining is assumed without confirmed support.

## G-009 — Automotive driving sequence

- **Input intent:** A red hatchback leaves a city street, turns onto a coastal road, and passes a lighthouse at golden hour over twenty-five seconds.
- **References:** Vehicle geometry and color; coastal road/lighthouse geography; optional driving plate.
- **Risk analysis:** Vehicle identity, wheel rotation, road contact, camera chase, changing geography, lighting progression, and reflections; high physical/camera risk.
- **Expected planning decisions:** Use multiple shots and a route graph; distinguish vehicle geometry from wheel/suspension state; choose controlled camera coverage and a separate sound/engine layer.
- **Continuity strategy:** Carry route, heading, speed phase, wheel state, vehicle damage/marks, sun direction, road anchors, and camera side; re-anchor at the road/lighthouse transition.
- **Decomposition:** `departure → tracking → turn → side/low wheel coverage → coastal reveal → lighthouse pass`; no arbitrary camera teleport.
- **Constraints:** Wheels rotate with motion, tires contact road, no vehicle morphing, plausible turn radius, consistent shadows/reflections, no duplicate cars.
- **Output class:** `SUPPORTED_PLAN` or `DEGRADED_PLAN` with explicit profile limitations.
- **Failure conditions:** Car slides without cause, wheels remain static, road geometry changes, camera crosses axis invisibly, or the same vehicle loses identity.

## G-010 — 30-second commercial

- **Input intent:** A beverage brand commercial moves from a runner at dawn to a shared bottle at a finish line and ends on a product hero frame.
- **References:** Product packshot, athlete wardrobe/identity, dawn/finish-line references, approved brand assets.
- **Risk analysis:** 30-second assembly, product/identity retention, action-to-product transition, logo/text, crowd/background, audio and edit rhythm.
- **Expected planning decisions:** Require narrative timeline and shot graph; separate hero product shot, running coverage, handoff, end card, and audio mix; use approved text/packaging composition.
- **Continuity strategy:** Track athlete wardrobe and bottle state across shots, but permit crowd variation as flexible; use canonical product anchor before hero/end card.
- **Decomposition:** `hook → run → acceleration → handoff/drink → finish reaction → product hero → end card`; limit concurrent actions per shot.
- **Constraints:** Product geometry/logo, hand/bottle contact, plausible running, no crowd duplicates, timing to music, end-card rights review.
- **Output class:** `SUPPORTED_PLAN` with assembled multi-shot package.
- **Failure conditions:** Product label changes, handoff is unobservable, end card is generated as unreadable text, or a single prompt replaces the timeline.

## G-011 — 60-second dialogue/action commercial

- **Input intent:** A parent and teenager argue about leaving for school, discover a lost key in a car, reconcile, and drive away in sixty seconds.
- **References:** Two identity/wardrobe references, kitchen/driveway/car references, optional approved voices, key prop reference.
- **Risk analysis:** Dialogue, emotional transition, prop discovery, vehicle entry, multiple locations, audio/lip-sync, 60-second assembly, identity and state propagation.
- **Expected planning decisions:** Use `DIRECTOR`; create Scene Bible, narrative/dialogue/audio timelines, shot graph, contact graph for key/car, separate dialogue from performance/audio/lip-sync, and human review checkpoints.
- **Continuity strategy:** Track key ownership/location, wardrobe, emotional state, doorway/car geometry, speaker turn, camera axis, and audio bed; re-anchor at kitchen→driveway and before car entry.
- **Decomposition:** `setup → argument turns → search stimulus → key discovery → processing/reconciliation → walk → key handoff → vehicle entry → drive-away`; split high-density beats.
- **Constraints:** Active-speaker invariant, reaction ordering, key cannot teleport, handoff/contact, car door/ignition causality, identity and wardrobe, audio-event alignment.
- **Output class:** `SUPPORTED_PLAN` only with conditional capabilities; otherwise `DEGRADED_PLAN` with explicit external audio/lip-sync/editorial path.
- **Failure conditions:** Teen reacts before key discovery, speakers swap, key appears, car starts before entry, lip-sync is claimed without profile support, or continuity is not state-propagated.

## G-012 — Multi-reference high-complexity scene

- **Input intent:** A four-person rescue team with a dog, drone, damaged van, storm, radio dialogue, and a collapsing bridge must coordinate a rescue over ninety seconds.
- **References:** Four identity references, dog, van, bridge/environment, storm/light, radio/voice, and drone references with individual roles and retention priorities.
- **Risk analysis:** Many participants, animal/vehicle interaction, articulated equipment, weather, camera movement, dialogue/radio, physics, references with possible conflicts, 90-second assembly.
- **Expected planning decisions:** Route `DIRECTOR`; build full Scene Bible, entity/reference precedence, complexity vector, narrative and dialogue/audio timelines, shot DAG, contact graphs only for critical contacts, and fallback branches.
- **Continuity strategy:** Partition persistent identity/world/product anchors from transient rescue state; use validated segments, canonical keyframes, reset boundaries, and explicit degradation budgets.
- **Decomposition:** `establish → locate → radio stimulus → team response → dog search → drone/bridge reveal → van extraction → contact/rescue → collapse consequence → regroup`; split by causal and capability boundaries.
- **Constraints:** No duplicate team members/dog/van, identity and wardrobe, radio speaker timing, physical bridge/vehicle contact, weather/light progression, camera axis, safe depiction, provenance/consent.
- **Output class:** `HUMAN_REVIEW_REQUIRED` or `DEGRADED_PLAN` unless every critical capability and reference is confirmed; never silently promise one-pass generation.
- **Failure conditions:** Reference conflict is silently resolved, unsupported aerial/animal/audio capability is assumed, a member or vehicle morphs, rescue outcome precedes cause, or the plan hides unresolved dependencies.

## Scenario acceptance

A future implementation passes a golden scenario when it preserves the required decisions, state/invariants, output class, and failure conditions. Exact headings, sentence order, and prompt wording are not graded.

## Related documents

The failure and oracle definitions live in [`failure-and-evals.md`](failure-and-evals.md); adversarial variants are in [`adversarial-scenarios.md`](adversarial-scenarios.md); canonical fields are in [`contracts.md`](contracts.md).
