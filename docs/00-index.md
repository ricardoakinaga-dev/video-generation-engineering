# Phase 0 documentation index

## Implemented package — 2026-09-08

The repository skill now exists at [SKILL.md](../.agents/skills/video-generation-engineering/SKILL.md). [Implementation results](../IMPLEMENTATION.md) record tested software, actual local ComfyUI execution and remaining media/provider limits. The R2 closure packet is [`triple-aaa-final-report.md`](triple-aaa-final-report.md); it does not promote unavailable production evidence. See [ADR-011](adr/ADR-011-skill-implementation-and-evidence.md) and [ADR-012](adr/ADR-012-triple-aaa-quality-boundary.md).

## Status

This is the navigation hub for the documentation-first architecture of `video-generation-engineering-vNext`. The documentation is `REMEDIATED_VERIFIED`; the current R2 implementation closure is `READY_WITH_RISKS`. The prior Gauntlet `FINISHED/PASS` record is historical and applies to the pre-remediation fingerprint, not to this revision. Runtime/media limits remain explicit and the package does not claim universal audiovisual quality.

## Purpose

These documents turn the master prompt and the preserved blueprint into a reviewable source of truth. They define the product boundary, canonical planning contracts, failure behavior, evaluation evidence, and implementation boundaries. They remain project design documents; the executable Skill is the separate package linked above.

## Source-of-truth hierarchy

When sources disagree, resolve them in this order and record the decision in an ADR or open question:

1. explicit current user/master-prompt requirements;
2. explicit safety, authorization, or provider constraints that apply to the requested operation;
3. accepted ADRs and normative requirements in this documentation package;
4. canonical contracts and observed runtime/artifact evidence;
5. the supplied `BLUEPRINT.md`, treated as an initial design hypothesis;
6. dated external research and design inferences;
7. examples, patterns, and future implementation proposals.

No lower-level document may silently override a higher-level contract. External claims use the evidence vocabulary in [`contracts.md`](contracts.md): `CONFIRMED`, `INFERRED`, `PROPOSED`, and `UNKNOWN`.

## Document map

| Document | Owns | Load when |
|---|---|---|
| [`BLUEPRINT.md`](BLUEPRINT.md) | Supplied initial design hypothesis | Comparing original intent or auditing drift |
| [`vision-and-scope.md`](vision-and-scope.md) | Problem, users, mission, scope, success, non-goals | Any product or boundary decision |
| [`requirements.md`](requirements.md) | Stable functional and non-functional requirements | Specifying or accepting behavior |
| [`architecture.md`](architecture.md) | Pipeline, layers, ownership, integration boundaries | Evaluating system shape |
| [`domain-model.md`](domain-model.md) | Canonical entities, fields, relationships, lifecycles | Adding or changing a domain concept |
| [`state-model.md`](state-model.md) | Immutable/persistent/transient/derived state | Propagating or repairing state |
| [`contracts.md`](contracts.md) | Shared schemas, statuses, evidence, invariants | Implementing any future module |
| [`scene-and-continuity.md`](scene-and-continuity.md) | Scene Bible, references, timelines, shots, anchors | Planning multi-shot or long-form work |
| [`continuity-engine.md`](continuity-engine.md) | Inheritance, conflict detection, repair | Checking adjacent-shot consistency |
| [`directing.md`](directing.md) | Story, character, performance, interaction, camera, audio | Turning intent into observable direction |
| [`constraints.md`](constraints.md) | Physics/constraint taxonomy and selection | Managing generation hints and QA assertions |
| [`model-adaptation.md`](model-adaptation.md) | Capability profiles and prompt compilation | Selecting or adapting a target model |
| [`comfyui-execution.md`](comfyui-execution.md) | ComfyUI planning/preflight boundary | Preparing an operator workflow |
| [`research.md`](research.md) | Dated external sources and inference limits | Reviewing any mutable capability claim |
| [`pattern-library.md`](pattern-library.md) | Evidence-driven reusable planning patterns | Reusing a proven decomposition |
| [`failure-and-evals.md`](failure-and-evals.md) | Failure taxonomy, oracles, repair loop | Designing tests or diagnosing drift |
| [`golden-scenarios.md`](golden-scenarios.md) | Twelve fully specified planning fixtures | Building or regression-testing the future Skill |
| [`adversarial-scenarios.md`](adversarial-scenarios.md) | Deliberate ambiguity and misuse cases | Red-teaming intake and planning |
| [`acceptance.md`](acceptance.md) | Quality gates and Phase 0 acceptance | Reviewing readiness |
| [`traceability.md`](traceability.md) | Goal → requirement → component → failure → gate → eval → implementation | Auditing coverage or drift |
| [`observability.md`](observability.md) | Concise decision evidence and diagnostics | Explaining a plan or repair |
| [`safety-boundaries.md`](safety-boundaries.md) | Safety, rights, privacy, authorization boundaries | Handling sensitive media or external effects |
| [`progressive-disclosure.md`](progressive-disclosure.md) | Conditional reference-routing matrix | Designing context-efficient Skill behavior |
| [`proposed-skill-structure.md`](proposed-skill-structure.md) | Smallest future production package | Starting Phase 1 design |
| [`roadmap.md`](roadmap.md) | Phased implementation sequence and gates | Planning later delivery |
| [`open-questions.md`](open-questions.md) | Blockers and non-blocking decisions | Resolving remaining uncertainty |
| [`phase-0-report.md`](phase-0-report.md) | Final status, decisions, risks, readiness, stop point | Handoff after this phase |
| [`triple-aaa-validation.md`](triple-aaa-validation.md) | Production evidence contracts and architecture closure | Quality, runtime or release work |
| [`capability-matrix-r1.md`](capability-matrix-r1.md) | Exact local capability scope and blockers | Selecting a model or feature |
| [`long-form-validation.md`](long-form-validation.md) | LF-001..LF-004 evidence envelope | Long-form generation or assembly |
| [`triple-aaa-scorecard.md`](triple-aaa-scorecard.md) | Independent release gates and maturity | Final readiness decision |
| [`master-prompt-triple-aaa-r2.txt`](master-prompt-triple-aaa-r2.txt) | Exact preserved user prompt | Auditing prompt fidelity |
| [`triple-aaa-quality-bar-r2.json`](triple-aaa-quality-bar-r2.json) | Frozen R2 quality bar and verdict policy | Auditing this closure |
| [`triple-aaa-quality-bar-r1.json`](triple-aaa-quality-bar-r1.json) | Historical R1 quality bar | Comparing prior closure only |
| [`triple-aaa-final-report.md`](triple-aaa-final-report.md) | Current R2 scores, evidence and remaining blockers | Release handoff |

## Recommended reading order

### Full architecture review

`vision-and-scope → requirements → architecture → domain-model → state-model → contracts → scene-and-continuity → continuity-engine → directing → constraints → model-adaptation → comfyui-execution → failure-and-evals → acceptance → traceability`.

### Simple short scene

`vision-and-scope → contracts → architecture → acceptance`; do not load long-form or specialist references unless the risk vector activates them.

### Dialogue or performance scene

`contracts → scene-and-continuity → directing → constraints → model-adaptation → failure-and-evals`.

### Vehicle or articulated-object scene

`contracts → scene-and-continuity → directing → constraints → pattern-library → failure-and-evals`.

### Long-form scene

`scene-and-continuity → state-model → continuity-engine → directing → comfyui-execution → golden-scenarios → acceptance`.

### Future Skill packaging

`progressive-disclosure → proposed-skill-structure → roadmap → open-questions → phase-0-report` plus the relevant domain references.

## ADR index

| ADR | Decision |
|---|---|
| [`ADR-001`](adr/ADR-001-documentation-first.md) | Documentation-first Phase 0 boundary |
| [`ADR-002`](adr/ADR-002-canonical-scene-model.md) | Canonical model-independent scene representation |
| [`ADR-003`](adr/ADR-003-model-agnostic-adapters.md) | Versioned model adapters and evidence status |
| [`ADR-004`](adr/ADR-004-continuity-state-and-shot-graph.md) | Explicit state ledger and shot graph |
| [`ADR-005`](adr/ADR-005-prompt-compiler.md) | Prompt as compiled view |
| [`ADR-006`](adr/ADR-006-long-form-decomposition.md) | Validated long-form shot decomposition |
| [`ADR-007`](adr/ADR-007-dialogue-audio-separation.md) | Script, performance, audio, and lip-sync separation |
| [`ADR-008`](adr/ADR-008-pattern-library.md) | Evidence-driven pattern library |
| [`ADR-009`](adr/ADR-009-instructions-vs-tools.md) | Instructions versus deterministic helpers |
| [`ADR-010`](adr/ADR-010-production-skill-structure.md) | Minimal future production Skill structure |
| [`ADR-011`](adr/ADR-011-skill-implementation-and-evidence.md) | Skill implementation and bounded evidence |
| [`ADR-012`](adr/ADR-012-triple-aaa-quality-boundary.md) | Separate production evidence from canonical planning |

## Architecture status

| Area | Phase 0 status | Evidence boundary |
|---|---|---|
| Product scope and requirements | Specified | Documentation inspection |
| Canonical scene/state/continuity model | Specified | Contracts and scenario fixtures |
| Model and ComfyUI capabilities | Profiled conservatively | Dated local runtime probes; feature-scoped confirmation only |
| Failure and evaluation strategy | Implemented for deterministic boundaries | Golden/known-bad/adversarial structural fixtures plus runtime limits |
| Repository Skill package | Implemented; R2 closure `READY_WITH_RISKS` | 133 tests, local ComfyUI evidence and frozen R2 bar |
| Generated media quality | Mechanically evaluated; semantic acceptance remains partial | Exact H3 T2V/R2V artifacts, separated observations and long-form blockers |

## Deviations from the suggested tree

The master prompt explicitly permits consolidation. This package keeps the existing coherent owners (`requirements`, `architecture`, `contracts`, `scene-and-continuity`, `directing`, `constraints`, `model-adaptation`, `comfyui-execution`, `research`, `failure-and-evals`, `acceptance`, `traceability`, and `roadmap`) and adds focused documents only where the prior baseline lacked a reviewable boundary. This avoids 30 thin files that duplicate state and terminology.

The package-shape rationale is documented separately in [`proposed-skill-structure.md`](proposed-skill-structure.md); the Phase 0 docs are not copied into the executable package automatically. The current package has its own focused `references/` set and keeps research/audit material in this project tree. The current Triple-AAA closure is tracked separately from the historical Phase 0 verdict; production evidence is scoped to exact local artifacts and is not inferred from this index.

## Implementation readiness

The historical Phase 0 content gate is complete enough to support the explicitly authorized repository implementation recorded in [ADR-011](adr/ADR-011-skill-implementation-and-evidence.md). `OQ-B-004`, `OQ-B-003`, and `OQ-B-002` remain staged blockers for unconfirmed model capabilities, external execution, and artifact/media acceptance respectively; the current package does not silently resolve them.

## Verification pointer

The historical documentation Gauntlet remains under `.gauntlet/`. The current implementation bar, fingerprints, critic packets and release reports are recorded under `verification/`; the project-level control plane remains under `.agent/`. These are process evidence, not production Skill content.
