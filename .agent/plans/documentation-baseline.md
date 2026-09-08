# Documentation baseline for video-generation-engineering-vNext — ExecPlan

<!-- engineering-framework: active_action_id=VGE-DOCS:VERIFY -->

## Purpose / Big Picture

Produce a complete, cross-linked documentation baseline under `docs/` from `docs/BLUEPRINT.md` for a future model-agnostic generative-video engineering Codex Skill. Success is a readable and testable architecture package that defines scope, contracts, state, continuity, model capability boundaries, ComfyUI planning, failures, evals, and acceptance. It must not create the production `SKILL.md` or execute media-generation jobs.

## Progress

- [x] (2026-09-07T20:52:41-03:00) Re-read the supplied blueprint and verified `docs/BLUEPRINT.md` is an exact copy of the attachment.
- [x] (2026-09-07T21:09:23-03:00) Create the normative documentation set and dated research record.
- [x] (2026-09-07T21:13:52-03:00) Run structural, link, syntax, coverage, and separated self-review checks; record evidence and remaining limitations.

## Surprises & Discoveries

- Observation: The target contains only `docs/BLUEPRINT.md`; it has no Git repository, source code, manifests, tests, CI, runtime, or repository instruction files.
  Evidence: `find . -maxdepth 3 -print`, `git status --short --branch`, and the blueprint copy comparison from the project root.
  Impact: The project is greenfield documentation. Validation must use artifact inspection, link/path checks, syntax checks, requirement coverage, and scenario oracles; no executable product behavior can be claimed.
- Observation: Official ComfyUI material documents multiple distinct video paths and warns that workflow/template availability depends on the installed version and node imports.
  Evidence: `docs/research.md` and the linked official ComfyUI pages.
  Impact: The target design needs a capability registry and runtime probe; model names alone cannot authorize an execution recipe.
- Observation: MiniMax H3 has an official announcement with multimodal context, native stereo audio, and a maximum of 15 seconds at 2K, but the public MiniMax video API reference documents Hailuo model names rather than a stable H3 API contract.
  Evidence: `docs/research.md` and its dated official sources.
  Impact: H3 is a research candidate, not a confirmed ComfyUI or API adapter; the docs must represent that uncertainty explicitly.

## Decision Log

- Decision: Preserve blueprint intent while downgrading unverified capability claims to `PROPOSED` or `UNKNOWN`.
  Context: The blueprint is an architecture input, not evidence that every future model or node supports the requested behavior.
  Alternatives: Copy claims as guarantees; or omit the model-specific concern entirely.
  Reason: A durable design must survive model churn and fail closed when evidence is absent.
  Consequences: Each model profile carries source, version/date, support status, and a validation method.
  Date/Author: 2026-09-07 / Codex
- Decision: Make the Scene Representation the canonical intelligence layer; prompts are compiled views.
  Context: A flat prompt cannot own narrative causality, state, references, or observed quality.
  Alternatives: Make the canonical prompt the source of truth; or generate prompts independently per shot.
  Reason: A model-independent intermediate representation allows adapters and repair loops without losing intent.
  Consequences: The future Skill outputs structured plan artifacts before any prompt text.
  Date/Author: 2026-09-07 / Codex
- Decision: Separate intended state, planned state, and observed artifact state.
  Context: Generation can violate the plan; treating the plan as evidence would hide drift.
  Alternatives: Trust declared state; or infer all state from media automatically.
  Reason: The distinction supports honest QA, targeted regeneration, and human review.
  Consequences: Acceptance never means “the prompt mentions the property”; it requires a current observation appropriate to the risk.
  Date/Author: 2026-09-07 / Codex
- Decision: Route by a complexity vector and dependency graph, with duration as an advisory signal.
  Context: A short interaction with two identities, dialogue, a vehicle, and a moving camera can exceed a long static portrait in risk.
  Alternatives: Use fixed duration thresholds only; or use a single scalar score.
  Reason: Complexity dimensions are non-aggregable when a single failure can defeat the scene.
  Consequences: High-risk dimensions elevate planning depth even for short clips.
  Date/Author: 2026-09-07 / Codex
- Decision: Treat audio as a first-class timeline that may be generated separately or jointly only when capability is confirmed.
  Context: ComfyUI has distinct silent, sound-to-video, and audio-composition paths.
  Alternatives: Put dialogue in the visual prompt only; or require native audio for every scene.
  Reason: A separable audio plan is the only portable design across model profiles.
  Consequences: Lip-sync requirements produce explicit preconditions and failure states, not promises.
  Date/Author: 2026-09-07 / Codex

## Outcomes & Retrospective

Closed on 2026-09-07 after a separated static self-review. The documentation package contains all planned owners plus an explicit section-level matrix for the 46 major blueprint sections and the 4.1/4.2 module subsections. Verification passed for the document set, YAML examples, Markdown links, requirement coverage, source references, known-bad fixtures, section coverage, control-plane JSON/JSONL, and blueprint byte equality.

The main rejected assumptions are recorded in `docs/research.md`: retention locks are QA targets rather than stochastic guarantees; duration is not the sole routing signal; FLF/chaining is capability-conditional; audio/lip-sync may be separate; and H3 is not an executable confirmed adapter. The workspace has no runtime, model assets, generated artifacts, Git history, or test harness, so runtime compatibility and visual/audio quality remain future validation work.

The next action is intentionally deferred: after an explicit implementation request, begin Phase 1 of `docs/roadmap.md` by creating and testing the minimal production Skill skeleton.

## Context and Orientation

Project root: `/home/ricardo/Área de trabalho/video-generation-engineering`. Product input: `docs/BLUEPRINT.md`, copied from the supplied attachment. The product is a future instruction package for Codex that plans generative-video production for ComfyUI and compatible model runtimes. It is not a renderer, NLE, trainer, ComfyUI replacement, voice-cloning framework, or generic screenplay writer.

`docs/README.md` is the entry point. `requirements.md`, `architecture.md`, and `contracts.md` own normative product and technical decisions. `scene-and-continuity.md`, `directing.md`, and `constraints.md` own domain rules. `model-adaptation.md` and `comfyui-execution.md` own capability and execution boundaries. `failure-and-evals.md`, `acceptance.md`, and `traceability.md` own proof and coverage. `research.md` owns external evidence.

## Scope and Constraints

- In scope: research, challenge of the blueprint, requirements, target architecture, contracts, scene/shot/state model, continuity and anchor strategy, directing guidance, dynamic constraints, model adaptation, ComfyUI execution planning, failure taxonomy, golden cases, behavioral evals, acceptance criteria, traceability, and a future implementation roadmap.
- Out of scope: production `SKILL.md`, `agents/openai.yaml`, scripts used by the Skill, ComfyUI workflow JSON, model installation, model/API execution, generated media, renderer/editor implementation, automatic uploads, voice cloning, and distribution.
- Applicable instructions: `/home/ricardo/.agents/skills/engineering-framework/SKILL.md`, its loaded engineering references, and `/home/ricardo/.codex/skills/.system/openai-docs/SKILL.md`; no target `AGENTS.md` was found.
- Requirements/decisions: `docs/BLUEPRINT.md`, `docs/requirements.md`, `docs/architecture.md`, `docs/contracts.md`.
- Tier/risk/blast radius: `T3_SYSTEM`, `MEDIUM`, `SYSTEM`; multiple architectural boundaries and future session continuity justify durable planning even though this phase is reversible documentation.
- Authorization constraints: research and local documentation edits are authorized; external generation, paid API calls, uploads, and production Skill creation are not.

## Architecture and Interfaces

The target flow is:

`creative request → normalized intent → reference inventory → complexity/risk → Scene Bible → narrative timeline → shot graph → continuity state → per-shot plan → capability-resolved adapter plan → ComfyUI recipe → quality gates → production package`.

The canonical representation is model-independent. A capability record says what a runtime/profile is evidenced to support; an execution recipe says how an operator could run it; an artifact observation says what actually occurred. None may be silently substituted for another. The active documentation action is `VGE-DOCS:VERIFY`, and the first Concrete Steps item remains aligned with that pointer while the task is active.

## Milestones

### Milestone 1 — Foundation and evidence

- Outcome: Index, requirements, architecture, contracts, and research record exist and are cross-linked.
- Scope/dependencies: Blueprint plus official and primary research sources.
- Demonstration: A newcomer can locate canonical ownership and distinguish fact, inference, proposal, and unknown.
- Acceptance/evidence: Internal links resolve; research entries include source, date, claim, status, and limitation.

### Milestone 2 — Production planning model

- Outcome: Scene Bible, timeline, shot graph, state/anchor model, specialized direction rules, and constraints are defined.
- Scope/dependencies: Milestone 1; contracts must agree with all specialized docs.
- Demonstration: Vehicle entry, two-person dialogue, and 60-second multi-shot cases can be represented without hidden transitions.
- Acceptance/evidence: Examples are syntactically valid or explicitly illustrative; forbidden contradictions and repair routes are named.

### Milestone 3 — Adapter and proof boundary

- Outcome: Capability policy, ComfyUI execution plan, failure taxonomy, golden cases, evals, acceptance, traceability, and roadmap are complete.
- Scope/dependencies: Milestones 1–2.
- Demonstration: A known-bad flat prompt or unsupported H3-ComfyUI assumption fails a stated oracle.
- Acceptance/evidence: All blueprint sections have an owner and evidence path; separated self-review finds no blocking documentation gap.

## Plan of Work

Write normative vocabulary and ownership first. Then write the model-independent planning model and continuity rules. Add directing and constraint guidance as consumers of those contracts. Finish with capability negotiation, ComfyUI boundaries, and proof artifacts. Keep all mutable claims linked to their canonical source; do not duplicate rules in examples. After editing, run static checks and inspect known-bad cases. Repair the largest requirement or contradiction gap first, then rerun the complete documentation verification.

## Completed Work

- Created the cross-linked normative documentation set under `docs/`, including the blueprint copy, requirements, architecture, contracts, research, scene/continuity, directing, constraints, model adaptation, ComfyUI execution, failure/evals, acceptance, traceability, and roadmap documents.
- Added a section-by-section matrix for all 46 major blueprint sections plus the two Core Modules subsections.
- Kept the future production Skill, workflow JSON, runtime execution, model assets, and generated media out of scope.

## Concrete Steps

1. [x] [VGE-DOCS:VERIFY] Run link, heading, ID, example-syntax, blueprint-coverage, and out-of-scope checks from the project root; retain failures as evidence and repair their causes.
2. [x] [VGE-DOCS:CLOSE] Perform a temporally separated self-review against `docs/acceptance.md`, append current verification evidence, and either close the docs task or leave one executable implementation-preparation action.

## Validation and Acceptance

| Criterion | Required | Procedure/environment | Expected observation | Evidence destination |
| --- | --- | --- | --- | --- |
| DOC-001 | Yes | Enumerate planned files and resolve every relative Markdown link | Complete doc set exists; no broken internal link | `.agent/verification.jsonl` |
| DOC-002 | Yes | Parse valid JSON/YAML examples and inspect explicitly illustrative pseudocode labels | Examples do not silently claim machine validity | `.agent/verification.jsonl` |
| DOC-003 | Yes | Compare blueprint section list with `traceability.md` and `acceptance.md` | Sections 1–46 map to an owner, requirement, and evidence path | `.agent/verification.jsonl` |
| DOC-004 | Yes | Inspect contracts and state docs together | Desired, planned, and observed state are distinct; invalid transitions are explicit | `.agent/verification.jsonl` |
| DOC-005 | Yes | Cross-check model/ComfyUI docs against dated research | Unsupported/version-sensitive capabilities are gated or marked unknown | `.agent/verification.jsonl` |
| DOC-006 | Yes | Exercise golden and known-bad cases against eval oracles | Oracles judge invariants/behavior, not keyword presence | `.agent/verification.jsonl` |
| DOC-007 | Yes | Fresh self-review after final edits | No blocking documentation gap; limitations and future boundary are explicit | `.agent/verification.jsonl` and plan |

## Risks and Human Decisions

| Risk/decision | Evidence/confidence | Controls | Residual/authority | Trigger |
| --- | --- | --- | --- | --- |
| Model and node capabilities change | Current official docs are versioned/time-sensitive | Dated profiles, runtime probe, fail-closed status | Maintainer must revalidate before release | Model/ComfyUI update |
| Lock language is mistaken for a guarantee | Generation is probabilistic | Define locks as target retention requirements; require observation | Human review remains necessary | Identity/product-critical scene |
| Audio/lip-sync path differs by model | Official ComfyUI exposes distinct audio-driven workflows | Separate audio timeline and preconditions | Native support is profile-specific | Dialogue, singing, or voice identity |
| Recursive chaining degrades quality | Long-video research identifies temporal/detail degradation | Canonical re-anchors, keyframes, reset boundaries, QA | Regeneration/editorial correction may remain necessary | Multi-shot dependency chain |
| Likeness/voice/reference rights are unclear | Provenance guidance and provider terms | Consent/provenance intake and human stop | Legal authority external to this design | Real person, brand, voice, or restricted asset |

## Idempotence and Recovery

The documentation process is local and reversible. Re-running it must not call a model, upload a file, or modify files outside the named project. On interruption, inspect the current docs and this plan before repeating work; no Git baseline exists, so use file listing, hashes, and verification records. If a capability cannot be confirmed, retain the plan and mark it `PROPOSED`/`UNKNOWN`; never retry an unsupported execution path by assumption. A failed check is preserved and repaired through one coherent change before the broad suite is rerun.

## Artifacts and Evidence

- `docs/README.md`: entry point and ownership map.
- `docs/requirements.md`: product requirements and non-goals.
- `docs/architecture.md`: target architecture, decisions, modules, and disclosure strategy.
- `docs/contracts.md`: canonical schemas, lifecycle states, evidence labels, and invariants.
- `docs/scene-and-continuity.md`: Scene Bible, timeline, shot graph, references, state, anchors, and long-form chaining.
- `docs/directing.md`: story, character, dialogue, performance, interaction, motion, cinematography, camera, and audio direction.
- `docs/constraints.md`: dynamic constraint taxonomy and selection policy.
- `docs/model-adaptation.md`: capability profiles, negotiation, prompt compilation, and unsupported-feature policy.
- `docs/comfyui-execution.md`: ComfyUI workflow/API boundary and operator execution plan.
- `docs/pattern-library.md`: evidence-driven reusable planning patterns and lifecycle.
- `docs/research.md`: dated external facts, sources, confidence, and limitations.
- `docs/failure-and-evals.md`: failure taxonomy, golden cases, eval schema, and behavioral oracles.
- `docs/acceptance.md`: gates, quality bar, and documentation Definition of Done.
- `docs/traceability.md`: blueprint-to-requirement-to-evidence coverage.
- `docs/roadmap.md`: future implementation phases and exit gates.
- `.agent/verification.jsonl`: current executed verification records.

Plan revision note, 2026-09-07: recreated after the explicit continuation signal; the blueprint remains copied verbatim, and production implementation remains out of scope. The documentation set was completed before the final verification action.
