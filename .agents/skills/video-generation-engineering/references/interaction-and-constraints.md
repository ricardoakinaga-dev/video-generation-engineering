# Interaction and constraints

Read for hands, animal/human contact, transfer, articulated objects, vehicles, gravity or dense simultaneous motion.

## Physical decomposition

Use approach → orient → reach → contact → act → observe result → react → release as coverage candidates. Specify actor, target, direction, phase/timing, support/balance, acceleration, gravity, mechanical axis and termination condition. Include only phases needed to make the event readable; spread high-risk phases across shots.

A contact graph identifies participants, effector, target surface, contact interval, force/action direction, object ownership before/after, and a visible success criterion. A hand near a handle is not confirmed contact. Track occupancy so the same hand does not hold a cup and pull a door at once. A transfer needs prior owner, grasp/contact/release and resulting owner. A dog's fetch needs throw, flight, chase, pickup, return and handoff; never assume the ball returns before its cause.

For animals preserve species-specific anatomy, gait, markings and support. A human-like athletic motion request needs a feasible canine alternative or explicitly stylized intent. For veterinary examination, isolate stabilization, paw contact, inspection and release; prevent added limbs and premature diagnosis reactions.

For vehicle entry preserve door hinge/handle location, clearance, step/support, body occlusion, seat occupancy, closing and ignition. For a driving shot specify tire-road contact, wheel rotation, turn radius, acceleration/braking, road geometry, screen direction, shadows and reflections. A vehicle reference and locked brand with conflicting geometry needs a precedence decision.

## Constraint types and precedence

| Kind | What it can do |
|---|---|
| GENERATION_HINT | guide model language; not enforce physics |
| RUNTIME_CONTROL | bind a supported parameter |
| INPUT_REQUIREMENT | require an asset or feature |
| QA_ASSERTION | define an observation obligation |
| ASSEMBLY_RULE | define timing/join/delivery behavior |
| RIGHTS_SAFETY | encode scoped use/transfer authority |

Each constraint has `constraint_id`, subject, kind, statement, optional parameters, priority, scope, evidence, validation method/threshold, fallback and status. Priority is CRITICAL/HIGH/MEDIUM/LOW. Status is PROPOSED/ACTIVE/SATISFIED/VIOLATED/WAIVED.

Precedence: rights and hard input prerequisites; story causality and explicit user constraints; identity/continuity; physical plausibility; camera/audio/style preferences; optimization. Within a level apply explicit decisions. Narrower scope selects non-conflicting properties; competing values still require established precedence or a user decision. Preserve unresolved same-level conflicts.

Select families by risk: anatomy, contact/collision, articulation, gravity/force, vehicle/road, world/lighting, temporal, identity/reference and cinematic. A simple landscape does not need a hand anatomy checklist. A blanket “no errors” request becomes scoped generation hints plus concrete QA assertions and suitable coverage; no negative prompt is an enforcement guarantee.

## Reusable patterns

Use patterns only when they solve a demonstrated scenario: speaker/listener coverage; contact close-up; articulated entry; gaze-triggered reveal; chase/return with ownership; product hero reset; location reset; bounded long-form segment. State inputs, applicability, output state, known failure and review oracle. Do not grow a catalog from speculative variants. Regression examples stay in project tests, outside the default skill context.
