# BLUEPRINT — video-generation-engineering-vNext

## Status

Architecture Blueprint / Pre-Implementation Specification

This blueprint defines the intended architecture, responsibilities, invariants, internal models, orchestration logic, quality requirements, and long-term direction for a future Codex Skill tentatively named:

`video-generation-engineering-vNext`

This document is the architectural source of truth for the documentation/design phase.

DO NOT implement the Skill yet.

The immediate goal is to use this blueprint to design and validate the complete documentation under `docs/` before creating the production Skill.

---

# 1. Mission

Build a State-of-the-Art Codex Skill capable of transforming a high-level creative request into a structured, coherent, executable generative-video production plan optimized for ComfyUI and modern video-generation models.

The Skill must not behave as a simple prompt generator.

It must behave as an:

GENERATIVE VIDEO ENGINEERING DIRECTOR

responsible for reasoning about:

* narrative intent;
* scene structure;
* subjects;
* character identity;
* reference images;
* environments;
* objects;
* vehicles;
* dialogue;
* acting/performance;
* human interaction;
* human-object interaction;
* animal interaction;
* blocking;
* motion;
* physical plausibility;
* anatomy;
* cinematography;
* camera continuity;
* lighting;
* temporal consistency;
* spatial consistency;
* emotional continuity;
* lip synchronization;
* voice continuity;
* sound design;
* shot decomposition;
* reference retention;
* model-specific prompting;
* ComfyUI execution strategy;
* multi-shot continuity;
* first/last-frame chaining;
* final assembly.

The Skill must support both short clips and structured longer-form scenes.

Target durations:

* 5–10 seconds
* 15–30 seconds
* 30–60 seconds
* 60–120 seconds

Long-form video must never be treated merely as one large prompt.

---

# 2. Core Architectural Principle

The Skill shall follow:

INTENT
→ MODEL
→ PLAN
→ STATE
→ SHOTS
→ CONTINUITY
→ CONSTRAINTS
→ MODEL ADAPTATION
→ PROMPT COMPILATION
→ EXECUTION PLAN
→ VALIDATION

Prompt generation happens near the end of the process.

The canonical prompt is an output representation, not the intelligence layer.

---

# 3. High-Level Pipeline

USER INTENT
↓
INTENT PARSER
↓
REFERENCE ANALYZER
↓
COMPLEXITY ANALYZER
↓
SCENE PLANNER
↓
SCENE BIBLE
↓
STORY ENGINE
↓
CHARACTER ENGINE
↓
WORLD ENGINE
↓
NARRATIVE TIMELINE
↓
SHOT PLANNER
↓
DIRECTOR LAYER
↓
CONTINUITY ENGINE
↓
CONSTRAINT ENGINE
↓
PROMPT COMPILER
↓
MODEL ADAPTER
↓
COMFYUI EXECUTION PLAN
↓
QUALITY GATES
↓
FINAL PRODUCTION PACKAGE

---

# 4. Core Modules

## 4.1 Intent Parser

Responsibilities:

* identify creative goal;
* detect duration;
* extract subjects;
* identify objects;
* identify environment;
* identify actions;
* detect dialogue requirements;
* detect style;
* detect camera requirements;
* detect audio requirements;
* detect provided references;
* identify unspecified but inferable production requirements;
* separate hard constraints from preferences.

Must produce a normalized scene intent.

---

## 4.2 Reference Analyzer

Responsibilities:

* identify all reference inputs;
* classify them;
* map references to subjects, objects, vehicles and environments;
* determine what information must be preserved;
* distinguish identity anchors from aesthetic references;
* create a reference retention matrix;
* detect conflicts between references;
* establish priority rules.

Possible categories:

* character identity;
* face;
* wardrobe;
* animal;
* product;
* vehicle;
* environment;
* lighting;
* composition;
* art direction;
* start frame;
* end frame.

---

# 5. Reference Retention Model

The system must explicitly determine which properties are:

LOCKED
FLEXIBLE
DERIVED
UNSPECIFIED

Example:

| Entity        | Identity | Geometry | Color | Wardrobe | Position | Lighting |
| ------------- | -------- | -------- | ----- | -------- | -------- | -------- |
| Subject 1     | LOCK     | LOCK     | LOCK  | LOCK     | FLEX     | FLEX     |
| Vehicle 1     | N/A      | LOCK     | LOCK  | N/A      | FLEX     | FLEX     |
| Environment 1 | N/A      | LOCK     | LOCK  | N/A      | LOCK     | LOCK     |

Reference retention must be explicit rather than implied.

---

# 6. Complexity Analyzer

Every requested scene must be classified before shot planning.

Possible dimensions:

* number of human identities;
* number of animal identities;
* dialogue;
* lip-sync;
* emotional acting;
* multiple speakers;
* physical human-human interaction;
* human-object interaction;
* human-vehicle interaction;
* animal-human interaction;
* vehicle motion;
* articulated objects;
* environment motion;
* camera motion;
* shot duration;
* total project duration;
* reference count;
* continuity dependencies;
* VFX requirements.

Suggested classifications:

LOW
MEDIUM
HIGH
VERY_HIGH

The analyzer must influence production strategy.

Example:

VERY_HIGH:

* multiple people;
* dialogue;
* physical interaction;
* vehicle;
* long duration;
* moving camera.

Recommended strategy:

* multi-shot decomposition;
* explicit continuity state;
* reference anchoring;
* first/last frame propagation;
* separate audio/dialogue planning;
* model-specific execution.

---

# 7. Scene Model

The Skill must create a canonical internal scene representation before compiling prompts.

Example conceptual representation:

project:
duration: 60s
genre: luxury_commercial
target_platform: comfyui
target_model: minimax_h3

subjects:
subject_1:
type: human
identity_reference: picture_1
identity_lock: true
wardrobe_lock: true
voice_lock: true

objects:
vehicle_1:
type: sports_car
reference: picture_2
geometry_lock: true
appearance_lock: true

environment:
environment_1:
reference: picture_3
lighting: golden_hour
environment_lock: true

narrative:
objective: >
Subject 1 interacts with Subject 2,
enters vehicle 1,
starts the vehicle and drives away.

This internal representation must remain model-agnostic.

---

# 8. Scene Bible

For complex or long-form scenes, create a Scene Bible.

It must contain:

* visual style;
* subject definitions;
* immutable identity traits;
* wardrobe;
* object definitions;
* vehicle definitions;
* environment;
* lighting;
* time of day;
* geography;
* camera language;
* audio identity;
* voice identity;
* relationships;
* narrative context;
* continuity constraints;
* prohibited drift.

The Scene Bible acts as the global continuity source of truth.

---

# 9. Story Engine

Responsibilities:

* convert creative intent into narrative beats;
* maintain causal order;
* detect prerequisites;
* avoid action overload;
* plan stimulus → reaction → response;
* manage dramatic progression;
* separate simultaneous versus sequential actions;
* maintain narrative clarity.

Key rule:

Do not overload individual shots with too many concurrent actions.

Prefer:

SPEAK
→ REACT
→ MOVE
→ INTERACT

over:

SPEAK + WALK + TURN + OPEN OBJECT + COMPLEX CAMERA ORBIT simultaneously.

---

# 10. Narrative Timeline

Long-form scenes require a temporal plan before shot creation.

Example:

00:00–00:06
Establish scene.

00:06–00:13
Dialogue beat 1.

00:13–00:19
Dialogue response.

00:19–00:24
Reaction.

00:24–00:31
Approach vehicle.

00:31–00:38
Enter vehicle.

00:38–00:44
Interior beat.

00:44–00:49
Ignition.

00:49–00:55
Drive away.

00:55–01:00
Hero closing shot.

The timeline describes narrative beats.

It is not yet the final generation prompt.

---

# 11. Character Engine

Track permanent and transient state independently.

Permanent state:

* identity;
* facial structure;
* skin;
* hair;
* body proportions;
* wardrobe;
* accessories;
* voice identity.

Transient state:

* position;
* pose;
* gaze;
* emotion;
* expression;
* current action;
* hand occupancy;
* interaction target.

Character identity must remain stable across shots.

---

# 12. Relationship Model

For multi-character scenes, explicitly model relationships.

Examples:

subject_1:
relationship_to_subject_2: colleague

subject_2:
current_attention_target: subject_1

Dialogue and interaction planning must understand:

* speaker;
* listener;
* gaze;
* interpersonal distance;
* social intent;
* emotional response;
* turn-taking.

---

# 13. Dialogue Director

Dialogue must not be represented only as text.

Each line may contain:

* speaker;
* listener;
* line;
* intention;
* delivery;
* emotion;
* gaze target;
* body language;
* duration;
* pause;
* reaction;
* overlap rules;
* voice identity.

Example:

dialogue:
speaker: subject_2
listener: subject_1
line: "Are you really going to drive that?"
intention: playful_challenge
delivery: amused
gaze: subject_1
duration: 2.8s
listener_reaction: subtle_smile

---

# 14. Performance Director

Control:

* facial expression;
* micro-expression;
* gaze;
* eye movement;
* blinking;
* breathing;
* posture;
* head motion;
* body language;
* gestures;
* emotional transition;
* speaking performance;
* listening performance.

Reactions must occur after their stimulus.

No premature reaction.

---

# 15. Interaction Director

Model interactions between:

* human ↔ human;
* human ↔ animal;
* human ↔ object;
* human ↔ vehicle;
* animal ↔ object;
* vehicle ↔ environment.

Complex interaction must be decomposed into physically plausible steps.

Example:

enter_vehicle:

approach
→ decelerate
→ reach
→ hand contacts handle
→ activate handle
→ door rotates around hinge
→ body rotates
→ torso lowers
→ body enters cabin
→ legs enter
→ hand reaches door
→ door closes

Avoid opaque actions such as:

"She enters the car."

when physical decomposition improves generation reliability.

---

# 16. Contact Graph

For physically sensitive actions, track contact relationships.

Example:

Subject 1
↓ right_hand
Door Handle
↓ attached_to
Vehicle Door
↓ hinged_to
Vehicle

This graph may support:

* contact constraints;
* collision avoidance;
* hand consistency;
* object continuity;
* physically correct articulation.

---

# 17. Motion Director

Responsibilities:

* turn high-level actions into motion primitives;
* ensure acceleration/deceleration;
* preserve balance;
* preserve gravity;
* preserve object mechanics;
* avoid teleportation;
* maintain plausible velocities;
* coordinate subject motion with camera motion.

Motion must be temporally and physically coherent.

---

# 18. World Engine

Maintain:

* environment geometry;
* geography;
* road geometry;
* architecture;
* background objects;
* lighting direction;
* time of day;
* weather;
* depth;
* horizon;
* reflections;
* spatial anchors.

The world must not spontaneously restructure between shots unless explicitly requested.

---

# 19. Shot Planner

Convert narrative beats into executable shots.

Each shot must define:

* shot ID;
* duration;
* narrative purpose;
* start state;
* end state;
* subjects;
* active subject;
* dialogue;
* actions;
* interactions;
* camera;
* lighting;
* audio;
* continuity dependencies;
* required references;
* generation mode;
* complexity;
* negative constraints.

---

# 20. Shot Graph

Shots form a dependency graph.

Example:

SHOT_001
↓
SHOT_002
↓
SHOT_003
↓
SHOT_004

Dependencies must propagate state.

Example:

SHOT_004 end_state:
vehicle.door = open

SHOT_005 start_state:
inherit SHOT_004
vehicle.door = open

The next shot must never silently contradict the previous state.

---

# 21. Continuity Engine

This is a critical subsystem.

It must track:

IDENTITY STATE
WARDROBE STATE
POSITION STATE
POSE STATE
GAZE STATE
OBJECT STATE
VEHICLE STATE
ENVIRONMENT STATE
LIGHTING STATE
CAMERA STATE
EMOTIONAL STATE
DIALOGUE STATE
AUDIO STATE
TEMPORAL STATE

Shots inherit prior relevant state.

---

# 22. Continuity Anchors

Possible anchors:

* identity image;
* face reference;
* wardrobe reference;
* object reference;
* vehicle reference;
* environment reference;
* lighting reference;
* previous shot last frame;
* next shot first frame;
* voice identity;
* recurring audio signature.

The system must recommend anchor strategy per shot.

---

# 23. Cinematography Director

Reason about:

* shot size;
* camera position;
* camera angle;
* lens;
* focal length;
* camera movement;
* framing;
* composition;
* depth of field;
* focus;
* exposure;
* motion blur;
* visual rhythm;
* lighting;
* cinematic style.

Supported concepts should include:

* establishing shot;
* wide shot;
* medium shot;
* close-up;
* extreme close-up;
* two-shot;
* over-the-shoulder;
* reverse OTS;
* reaction shot;
* insert;
* tracking;
* dolly;
* crane;
* orbit;
* drone;
* vehicle mount;
* chase shot.

Camera choices must serve narrative purpose.

---

# 24. Camera Continuity

Track:

* screen direction;
* 180-degree rule;
* subject orientation;
* camera side;
* eye-line;
* focal consistency;
* movement continuity.

Avoid spatial confusion between adjacent shots unless intentionally used.

---

# 25. Audio Director

Audio must be designed as separate layers.

Possible layers:

DIALOGUE
VOICE
FOLEY
ENVIRONMENT
ROOM TONE
VEHICLE
ANIMAL
MUSIC
TRANSITIONS

Audio events must correspond temporally to visible events.

Example:

door_handle_contact
→ handle click

door closing
→ impact sound

engine ignition
→ ignition audio

vehicle acceleration
→ RPM increase

---

# 26. Lip-Sync Director

Track:

* active speaker;
* dialogue line;
* start time;
* end time;
* voice;
* phonetic timing when applicable;
* mouth motion;
* facial motion;
* head motion;
* listener behavior.

Invariant:

Only the speaking character performs sustained speech articulation.

Listeners may:

* breathe;
* blink;
* react;
* smile;
* move subtly.

Listeners must not silently mouth another character's words.

---

# 27. Constraint Engine

Generate relevant constraints dynamically.

Categories:

* human anatomy;
* animal anatomy;
* object geometry;
* vehicle geometry;
* vehicle physics;
* contact;
* collision;
* gravity;
* motion;
* temporal consistency;
* lighting;
* camera;
* dialogue;
* lip-sync;
* identity;
* reference retention.

Do not blindly emit every constraint for every scene.

Use scene-aware constraint selection.

---

# 28. Negative Constraint Taxonomy

Potential categories:

IDENTITY DRIFT
FACE MORPHING
ANATOMY ERRORS
HAND ERRORS
EXTRA LIMBS
MISSING LIMBS
OBJECT MORPHING
VEHICLE MORPHING
WHEEL ERRORS
CONTACT FAILURES
COLLISIONS
TELEPORTATION
FRAME FLICKER
CAMERA TELEPORTATION
ENVIRONMENT DRIFT
LIGHTING DRIFT
TEXT ARTIFACTS
WATERMARKS
LIP-SYNC ERRORS
DIALOGUE ERRORS

Negative constraints must target actual scene risk.

---

# 29. Canonical Prompt Format

The initial canonical output schema should support:

subject_definitions:

environment_definitions:

summary:

retention_analysis:

detailed_description:

global_physical_constraints:

cinematography:

overall_soundscape:

negative_constraints:

Additional structured sections may be introduced if research demonstrates value, but backwards compatibility with this conceptual template should be considered.

---

# 30. Prompt Compiler

The Prompt Compiler translates the model-independent scene representation into the selected prompt representation.

Inputs:

Scene Bible
+
Narrative Timeline
+
Shot Model
+
Dialogue
+
Performance
+
Interaction
+
Motion
+
Cinematography
+
Continuity
+
References
+
Constraints
+
Audio

Output:

Canonical or model-specific generation prompt.

---

# 31. Model Adapter Layer

The core architecture must remain model-agnostic.

Model profiles may later include:

* MiniMax H3;
* Wan;
* Hunyuan Video;
* Kling;
* Veo;
* Seedance;
* generic video models.

A model profile may define:

* prompt syntax;
* preferred prompt length;
* reference behavior;
* temporal limitations;
* dialogue behavior;
* audio support;
* camera behavior;
* image-to-video recommendations;
* text-to-video recommendations;
* first/last-frame support;
* known failure modes;
* recommended constraints.

Do not hard-code core reasoning specifically around one model.

---

# 32. ComfyUI Execution Planner

The Skill should eventually be able to recommend execution strategy.

Potential dimensions:

* T2V vs I2V;
* start frame;
* end frame;
* reference conditioning;
* identity conditioning;
* first/last-frame chaining;
* shot duration;
* resolution;
* interpolation;
* upscale;
* lip-sync;
* audio generation;
* FFmpeg assembly;
* post-processing.

Example:

SHOT 05

mode:
image-to-video

references:
subject_identity: Picture 1
vehicle: Picture 2

start_frame:
SHOT_04.last_frame

duration:
6 seconds

output:
shot_05.mp4

next:
extract final frame as continuity anchor for SHOT_06

Do not invent unsupported model capabilities.

Model-specific capabilities must be documented and validated before use.

---

# 33. Long-Form Strategy

Suggested baseline policy:

<= 10s:
single shot may be acceptable.

10–20s:
analyze complexity before deciding.

20–30s:
prefer decomposition for complex action.

> 30s:
> require narrative timeline.

> 45s:
> require Scene Bible + Shot Graph + Continuity Map.

> =60s:
> require:

* narrative timeline;
* Scene Bible;
* reference plan;
* shot graph;
* explicit state propagation;
* dialogue timeline if applicable;
* audio timeline;
* generation strategy;
* assembly plan.

These thresholds are initial hypotheses and must be validated during documentation/research.

---

# 34. Operating Modes

Future operating modes may include:

FAST

Purpose:
minimal planning for simple requests.

CINEMATIC

Purpose:
strong cinematography and prompt generation.

PRODUCTION

Purpose:
multi-shot planning, continuity and execution.

DIRECTOR

Purpose:
full 30–120 second orchestration.

The documentation phase must determine whether these modes are useful or unnecessary complexity.

Do not preserve them merely because they exist in this blueprint.

---

# 35. Pattern Library

Potential reusable pattern domains:

dialogue/

* two-person-dialogue
* question-answer
* greeting
* argument
* emotional-conversation
* walking-and-talking
* sitting-and-talking

human-interaction/

* handshake
* hug
* object-exchange
* door-opening
* seated-interaction

vehicles/

* approach-vehicle
* open-door
* enter-vehicle
* exit-vehicle
* ignition
* drive-away
* highway-driving
* parking

animals/

* human-animal-contact
* examination
* animal-walking
* feeding
* pet-owner-interaction

veterinary/

* physical-examination
* auscultation
* animal-restraint
* veterinarian-owner-conversation
* diagnostics
* treatment

commercial/

* hero-product
* product-reveal
* product-demonstration
* lifestyle-ad
* automotive-commercial
* veterinary-commercial

cinematic/

* establishing
* reveal
* reaction
* hero-ending
* chase
* montage

Only patterns with demonstrated reusable value should eventually be added.

Avoid bloating the Skill with speculative patterns.

---

# 36. Progressive Disclosure

The final Skill must follow progressive disclosure.

Layer 1:
Skill metadata / triggering information.

Layer 2:
Concise SKILL.md orchestration instructions.

Layer 3:
References loaded only when applicable.

Examples:

If the scene contains a vehicle:
load vehicle-related guidance.

If the scene contains dialogue:
load dialogue and lip-sync guidance.

If the target is MiniMax:
load MiniMax-specific profile.

If long-form:
load long-form continuity guidance.

Do not force all domain knowledge into SKILL.md.

---

# 37. Proposed Future Skill Shape

This is provisional and must be validated during documentation.

video-generation-engineering-vNext/
│
├── SKILL.md
├── agents/
│   └── openai.yaml
│
├── references/
│   ├── architecture.md
│   ├── scene-model.md
│   ├── continuity.md
│   ├── cinematography.md
│   ├── dialogue-performance.md
│   ├── interaction-motion.md
│   ├── audio-lipsync.md
│   ├── constraints.md
│   ├── long-form.md
│   ├── comfyui.md
│   └── model-profiles/
│
├── scripts/
│   └── only deterministic helpers that prove useful
│
└── assets/
└── only actual reusable output assets/templates if justified

Do not create directories simply to satisfy this blueprint.

The documentation phase must determine the minimal effective structure.

---

# 38. Quality Gates

The future Skill should validate:

GATE 1 — Intent completeness
GATE 2 — Reference mapping
GATE 3 — Narrative coherence
GATE 4 — Shot feasibility
GATE 5 — Identity continuity
GATE 6 — Spatial continuity
GATE 7 — Temporal continuity
GATE 8 — Physical plausibility
GATE 9 — Interaction plausibility
GATE 10 — Dialogue coherence
GATE 11 — Performance coherence
GATE 12 — Lip-sync feasibility
GATE 13 — Camera continuity
GATE 14 — Audio-event coherence
GATE 15 — Model compatibility
GATE 16 — Prompt ambiguity
GATE 17 — Execution completeness

When validation fails:

DETECT
→ EXPLAIN
→ REPAIR
→ RE-EVALUATE
→ COMPILE

---

# 39. Eval Philosophy

Evals must test observable behavior and invariants rather than exact wording.

Bad eval:

"Prompt contains heading 'cinematography'."

Better eval:

"Adjacent shots preserve subject screen direction unless a deliberate spatial transition is declared."

Bad eval:

"Prompt contains five negative constraints."

Better eval:

"A vehicle-entry scene identifies door articulation, contact, collision and vehicle geometry as high-risk invariants."

---

# 40. Example Eval Families

## Identity retention

Given:
same character across 8 shots.

Verify:

* stable identity requirements;
* persistent wardrobe;
* reference anchor propagation;
* no accidental character substitution.

## Dialogue

Given:
two-character conversation.

Verify:

* speaker/listener distinction;
* turn order;
* reaction after stimulus;
* listener does not mouth speaker dialogue;
* gaze targets remain coherent.

## Vehicle entry

Verify:

* correct action decomposition;
* hand-handle contact;
* door articulation;
* body/vehicle collision prevention;
* final seated state;
* continuity into next shot.

## Long-form 60s

Verify:

* Scene Bible exists;
* narrative timeline exists;
* shots cover full intended duration;
* continuity states propagate;
* references remain mapped;
* object states do not contradict prior shots;
* dialogue remains causal;
* audio events align with visible events.

---

# 41. Golden Cases

Documentation should define representative golden scenarios:

1. Single-person cinematic portrait.
2. Human + animal interaction.
3. Veterinary examination.
4. Two-person dialogue.
5. Walking-and-talking.
6. Product advertisement.
7. Person entering vehicle.
8. Automotive sequence.
9. 30-second commercial.
10. 60-second dialogue/action scene.
11. Multi-reference image-to-video project.
12. Failure-prone high-complexity scene.

Golden cases should be used to reason about architecture before implementation.

---

# 42. Failure Taxonomy

Document likely failures such as:

* identity drift;
* character duplication;
* wardrobe drift;
* face deformation;
* anatomy failure;
* hand-object failure;
* object morphing;
* vehicle geometry drift;
* wheel inconsistency;
* collision/intersection;
* broken continuity;
* environment drift;
* lighting drift;
* incorrect parallax;
* camera discontinuity;
* dialogue overlap;
* lip-sync instability;
* reaction timing errors;
* temporal flicker;
* over-constrained prompts;
* excessive prompt verbosity;
* conflicting instructions;
* model capability mismatch.

Each failure family should eventually map to:

DETECTION
MITIGATION
PREVENTION
EVAL

---

# 43. Non-Goals

The initial Skill should not automatically become:

* a video editor;
* a full NLE;
* a renderer;
* a model-training system;
* a ComfyUI replacement;
* a generic screenplay-writing system;
* a voice-cloning framework;
* a generic image-generation skill.

It is a generative-video engineering and orchestration Skill.

Scope can evolve only when evidence justifies it.

---

# 44. Documentation-First Requirement

Before implementation:

1. research the domain;
2. challenge this blueprint;
3. identify weak assumptions;
4. define architecture;
5. define contracts;
6. define invariants;
7. define failure taxonomy;
8. define eval strategy;
9. define production workflows;
10. define model adaptation;
11. define progressive-disclosure strategy;
12. define acceptance criteria.

Only after documentation is coherent should implementation begin.

---

# 45. Design Standard

Target:

State of the Art / AAA quality.

This does NOT mean maximum file count or maximum complexity.

AAA means:

* clear architecture;
* strong reasoning;
* minimal unnecessary complexity;
* reliable decisions;
* explicit contracts;
* progressive disclosure;
* testable behavior;
* evidence-backed model profiles;
* robust failure handling;
* long-form continuity;
* high-quality examples;
* maintainability;
* extensibility;
* low ambiguity;
* measurable acceptance criteria.

Prefer:

small + precise + validated

over:

large + impressive-looking + redundant.

---

# 46. Fundamental Principle

Never treat long-form generative video as a single prompt-generation problem.

Treat it as:

STORY
+
STATE
+
REFERENCES
+
SHOTS
+
CONTINUITY
+
PERFORMANCE
+
DIALOGUE
+
INTERACTION
+
PHYSICS
+
CAMERA
+
AUDIO
+
MODEL ADAPTATION
+
GENERATION
+
ASSEMBLY
+
VERIFICATION

The Skill must function as the engineering layer connecting these concerns.
