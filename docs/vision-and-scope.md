# Vision and scope

## Purpose

Define the product outcome and boundary for the Codex Skill that acts as a generative-video engineering director. This document remains the product source; the current executable subset is linked from the repository README.

## Mission

Transform a creator's intent and references into a coherent, capability-aware production plan for short through approximately 120-second structured generative-video work. The plan explains scenes, entities, beats, shots, continuity, motion, camera, audio, model adaptation, execution prerequisites, and validation. It makes uncertainty visible and gives an operator a repairable next action.

The product is an engineering/orchestration layer. A prompt is one compiled output; it is not the canonical representation of story, identity, physics, continuity, or evidence.

## Problem

Generative-video workflows fail at boundaries that a single prompt cannot own: a reference is used for the wrong property, a character changes between shots, an action omits contact phases, dialogue is assigned to the wrong speaker, a camera crosses the axis without intent, audio has no visible cause, a workflow assumes an unavailable node, or a plan is treated as proof of an artifact. The Skill exists to turn these failure modes into explicit planning decisions and verifiable observations.

## Users and primary workflows

| User | Workflow | Product value |
|---|---|---|
| Creator/director | Idea → scene/shot plan | Causal, visual, and performance choices are visible |
| ComfyUI operator | Plan → workflow recipe | Inputs, nodes, assets, limits, and preflight are explicit |
| Editor/reviewer | Artifact → drift/repair | State and acceptance criteria identify what to regenerate |
| Skill maintainer | New model/pattern → profile/eval | Extensions do not rewrite the canonical scene model |
| Producer/rights reviewer | Reference/output → approval boundary | Likeness, voice, provenance, and external effects are surfaced |

## Inputs

The Skill may accept:

- natural-language creative intent;
- supplied image, video, audio, text, or 3D references;
- target duration, aspect ratio, delivery, and platform assumptions;
- selected or requested model/runtime;
- hard constraints, preferences, rights/provenance status, and review decisions;
- prior scene plans, shot observations, and accepted anchors.

An input is not presumed to be accessible or rights-cleared merely because a path or description exists. The plan records unknowns and prerequisites.

## Outputs

The minimum useful production package contains:

1. normalized intent and unresolved questions;
2. reference inventory and retention matrix;
3. complexity/risk assessment and derived depth label;
4. Scene Bible when justified;
5. narrative timeline and causal beats;
6. shot graph, state ledger, anchors, and continuity obligations;
7. direction for character, dialogue, performance, interaction, motion, camera, and audio;
8. dynamic constraints and QA assertions;
9. capability-resolved adapter plan and compiled prompt views;
10. ComfyUI/operator execution recipe with preflight and fallback;
11. assembly plan, acceptance checklist, observations, and repair routes.

## Duration and complexity scope

The architecture supports real-valued target durations `t` in the range `0 < t ≤ 120` seconds:

| Target | Planning expectation |
|---|---|
| `0 < t ≤ 30` seconds | Shot purpose and state at material boundaries; escalate for complexity |
| `30 < t ≤ 45` seconds | Base structure plus narrative timeline |
| `45 < t < 60` seconds | Narrative timeline, Scene Bible, shot graph, and explicit planned-state propagation |
| `60 ≤ t < 90` seconds | Above plus applicable reference/audio/dialogue timelines, generation strategy, assembly, re-anchors, and recovery |
| `90 ≤ t ≤ 120` seconds | Structured validated segments, provenance/assembly manifest, explicit operator assembly, and human review |

These are structural planning floors, not provider guarantees or hard model limits. A static panorama may use minimal one-node forms and omit inapplicable specialist timelines, but it still satisfies the applicable floor. The complexity vector can require production-level planning for a three-second vehicle interaction.

## Relationship to adjacent systems

- **Codex:** supplies instruction following, reasoning, file/workflow preparation, and optional tool boundaries. The Skill must be concise and progressively disclose domain references according to official OpenAI guidance.
- **ComfyUI:** is a target runtime/workflow surface. The Skill plans and preflights against observed capability; it is not a ComfyUI replacement or automatic queue by default.
- **Video models:** are replaceable providers behind versioned profiles. Model repositories, hosted APIs, and local ComfyUI nodes are separate evidence boundaries.
- **Editors/renderers:** consume shot artifacts and assembly instructions; the Skill does not become a non-linear editor or renderer.

## Success criteria

The product succeeds when a creator can inspect the intended film, an operator can identify a feasible workflow and prerequisites, and a reviewer can tell whether the artifact preserved critical requirements. A successful plan can also honestly return `DEGRADED`, `BLOCKED`, or `HUMAN_REVIEW_REQUIRED` when evidence or capability is insufficient.

## Non-goals

- generic screenplay generation without production state;
- one-shot prompt vending;
- guaranteed identity, physics, continuity, or lip-sync;
- automatic model download or provider recommendation without evidence;
- automatic upload, paid API call, queueing, publication, or deletion;
- voice cloning, likeness verification, legal clearance, or rights adjudication;
- replacing human editorial or safety judgment.

## Architecture challenge conclusions

- Scene Model and Scene Bible are unified conceptually through shared contracts, but the Bible remains a durable global-invariant view while the Scene Model carries normalized structure.
- Story Engine, Interaction Director, and Motion Director are logical responsibilities, not mandatory services. They remain separate in the plan because their failure or review criteria differ.
- Contact Graph is justified only for physical-risk interactions; it is omitted from low-risk static scenes.
- Audio and lip-sync remain separate because model support is profile-specific and assembly is a valid path.
- FAST/CINEMATIC/PRODUCTION/DIRECTOR are derived presentation/depth policies, not separate reasoning engines.

## Open questions

See [`open-questions.md`](open-questions.md) for unresolved choices around profile activation, visual oracles, artifact formats, and future runtime authority.
