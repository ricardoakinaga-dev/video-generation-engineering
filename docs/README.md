# video-generation-engineering-vNext

## Implemented package — 2026-09-08

The repository skill now exists at [SKILL.md](../.agents/skills/video-generation-engineering/SKILL.md). [Implementation results](../IMPLEMENTATION.md) record tested software, actual local ComfyUI execution and remaining media/provider limits. The Phase 0 design and historical gates below are preserved; they do not certify the implementation. See [ADR-011](adr/ADR-011-skill-implementation-and-evidence.md).

## Purpose

Provide the design source and historical boundary record for a model-agnostic generative-video engineering director. The executable repository package now lives under `.agents/skills/video-generation-engineering`; this folder explains what it owns, where evidence comes from, and which claims still require runtime or human review.

## Status

The expanded Phase 0 documentation is `REMEDIATED_VERIFIED` following the original audit, its second review, its third review [`AUDIT-docs-2026-09-08-r3.md`](../audit-artifacts/reports/AUDIT-docs-2026-09-08-r3.md), its fourth review [`AUDIT-docs-2026-09-08-r4.md`](../audit-artifacts/reports/AUDIT-docs-2026-09-08-r4.md), and a fresh focused static re-audit. The prior Gauntlet `FINISHED/PASS` record is historical for the pre-remediation artifact; a new independent process verdict is not claimed here. That audit preceded the implementation now linked above.

Use [`00-index.md`](00-index.md) as the canonical navigation hub. No model runtime, ComfyUI endpoint, paid API, upload, or media-generation job is invoked by this documentation phase.

This package turns [`BLUEPRINT.md`](BLUEPRINT.md) into a testable design for a generative-video engineering director. The design is intentionally model-agnostic at its core and capability-specific only at the adapter boundary. It plans work for ComfyUI and compatible runtimes; it does not render video, run a workflow, edit a timeline, train a model, or guarantee a generated result.

## Read this first

1. [`00-index.md`](00-index.md) is the navigation hub, source hierarchy, reading router, ADR index, and readiness status.
2. [`vision-and-scope.md`](vision-and-scope.md) defines the product problem, mission, users, durations, boundaries, and success.
3. [`requirements.md`](requirements.md) defines stable functional, governance, documentation, and quality requirements.
4. [`architecture.md`](architecture.md) defines the target pipeline, ownership, boundaries, and progressive-disclosure principles.
5. [`domain-model.md`](domain-model.md), [`state-model.md`](state-model.md), and [`contracts.md`](contracts.md) define entities, state classes, schemas, and invariants.
6. [`scene-and-continuity.md`](scene-and-continuity.md) and [`continuity-engine.md`](continuity-engine.md) define Scene Bible, timelines, shots, anchors, inheritance, conflicts, and repair.
7. [`directing.md`](directing.md), [`constraints.md`](constraints.md), and [`pattern-library.md`](pattern-library.md) define story, performance, interaction, motion, camera, audio, physics, and reusable structures.
8. [`model-adaptation.md`](model-adaptation.md) and [`comfyui-execution.md`](comfyui-execution.md) define capability profiles, prompt compilation, workflows, and the runtime boundary.
9. [`research.md`](research.md) records dated external evidence and what remains unverified.
10. [`failure-and-evals.md`](failure-and-evals.md), [`golden-scenarios.md`](golden-scenarios.md), and [`adversarial-scenarios.md`](adversarial-scenarios.md) define failure, golden, red-team, and oracle coverage.
11. [`acceptance.md`](acceptance.md) and [`traceability.md`](traceability.md) define gates, Phase 0 acceptance, and end-to-end coverage.
12. [`observability.md`](observability.md), [`safety-boundaries.md`](safety-boundaries.md), and [`progressive-disclosure.md`](progressive-disclosure.md) define diagnostics, safety, authorization, and context routing.
13. [`proposed-skill-structure.md`](proposed-skill-structure.md), [`open-questions.md`](open-questions.md), [`roadmap.md`](roadmap.md), and [`phase-0-report.md`](phase-0-report.md) preserve the Phase 0 handoff and its historical gates; the current implementation is linked at the top of each document.

## Canonical ownership

Each durable decision has one owner. Other documents link to it instead of restating a mutable rule.

| Decision or contract | Canonical owner |
| --- | --- |
| Product outcome, non-goals, and requirements | [`requirements.md`](requirements.md) |
| Product vision, scope, duration bands, and boundaries | [`vision-and-scope.md`](vision-and-scope.md) |
| Target architecture and module boundaries | [`architecture.md`](architecture.md) |
| Canonical entities and relationships | [`domain-model.md`](domain-model.md) |
| Immutable/persistent/transient/derived state | [`state-model.md`](state-model.md) |
| Shared types, statuses, evidence, and invariants | [`contracts.md`](contracts.md) |
| Scene, shot, timeline, reference, and continuity semantics | [`scene-and-continuity.md`](scene-and-continuity.md) |
| Continuity inheritance, conflict detection, and repair | [`continuity-engine.md`](continuity-engine.md) |
| Story, performance, interaction, motion, camera, and audio direction | [`directing.md`](directing.md) |
| Constraint selection and negative prompts | [`constraints.md`](constraints.md) |
| Runtime/model capabilities and prompt adaptation | [`model-adaptation.md`](model-adaptation.md) |
| ComfyUI workflows, API boundary, and execution strategy | [`comfyui-execution.md`](comfyui-execution.md) |
| Reusable planning patterns and pattern lifecycle | [`pattern-library.md`](pattern-library.md) |
| External facts and source freshness | [`research.md`](research.md) |
| Failure taxonomy, scenarios, and eval oracles | [`failure-and-evals.md`](failure-and-evals.md) |
| Complete golden planning fixtures | [`golden-scenarios.md`](golden-scenarios.md) |
| Adversarial intake and planning cases | [`adversarial-scenarios.md`](adversarial-scenarios.md) |
| Quality gates and acceptance | [`acceptance.md`](acceptance.md) |
| Requirement and blueprint coverage | [`traceability.md`](traceability.md) |
| Concise decision diagnostics | [`observability.md`](observability.md) |
| Safety, provenance, and authorization boundaries | [`safety-boundaries.md`](safety-boundaries.md) |
| Conditional reference routing | [`progressive-disclosure.md`](progressive-disclosure.md) |
| Proposed future Skill package | [`proposed-skill-structure.md`](proposed-skill-structure.md) |
| Open decisions and blockers | [`open-questions.md`](open-questions.md) |
| Phase 0 handoff report | [`phase-0-report.md`](phase-0-report.md) |
| Future implementation sequence | [`roadmap.md`](roadmap.md) |

`BLUEPRINT.md` is the supplied design input and historical source of intent. It is not allowed to silently override the more precise contracts in this package. A contradiction is recorded as a decision or an open question, never resolved by wording drift.

## Evidence vocabulary

Every statement that can age or affect execution uses the following vocabulary from [`contracts.md`](contracts.md):

- `CONFIRMED`: directly supported by a current source or an executed local observation.
- `INFERRED`: a reasoned conclusion from confirmed evidence; it is not a provider guarantee.
- `PROPOSED`: a design choice for the future Skill that still needs implementation or evaluation.
- `UNKNOWN`: not established; the system must not use it as a capability assumption.

Claim type is separate from evidence status. `FACT`, `ASSUMPTION`, `HYPOTHESIS`, and `DECISION` describe what kind of statement is being made. Confidence describes confidence in the statement, not whether it has been executed.

## Product principle

The Skill is an engineering layer, not a prompt vending machine:

```text
INTENT
  → REFERENCES + COMPLEXITY
  → SCENE BIBLE
  → STORY + TIME
  → SHOTS + STATE
  → CONTINUITY + CONSTRAINTS
  → MODEL ADAPTATION
  → EXECUTION PLAN
  → OBSERVATION + VALIDATION
```

The canonical prompt is a compiled view of this plan. It is never the sole source of narrative truth, physical plausibility, identity, continuity, or quality evidence.

## What the design deliberately corrects

The blueprint is strong on coverage but contains hypotheses that need boundaries. This documentation therefore makes five corrections explicit:

1. A reference property marked `LOCKED` is a retention requirement, not a guarantee that a stochastic model will preserve it.
2. Duration alone does not determine planning depth. Complexity dimensions and dependency edges can escalate a short clip.
3. First/last-frame chaining is conditional on a confirmed model/runtime capability and requires periodic canonical re-anchoring; recursive reuse is not treated as lossless.
4. Audio and lip-sync are separate deliverables unless a specific profile proves joint generation and synchronization.
5. “Constraint” is split into generation guidance, runtime control, and QA assertion. A negative prompt cannot enforce physics or consent.

## Historical Phase 0 package boundary

The Phase 0 baseline originally described a future package containing a concise `SKILL.md`, optional references, optional deterministic helpers, and optional metadata. That historical boundary was superseded for the current authorized build by [ADR-011](adr/ADR-011-skill-implementation-and-evidence.md). The current package is separate from this documentation tree and is not certified merely because these docs exist. See the official [Build skills documentation](https://developers.openai.com/codex/skills/) for host behavior.

## Current limitations

The workspace has no Git history and does not ship model weights or a renderer. The current implementation includes deterministic tests, workflow fixtures, a locally probed ComfyUI/H3 profile and synthetic media checks; those bounded results do not establish universal model feasibility or visual/audio/editorial quality. External paid execution, transfer, lip-sync and long-form artifact acceptance remain conditional.

## Document contract

The key invariants are: the canonical scene/state representation precedes prompt compilation; `UNKNOWN` is never silently promoted; a lock is a QA target rather than a guarantee; and observed artifacts are separate from planned state. Common failure modes are prompt-only planning, unsupported capability claims, continuity drift, and unauthorized external effects; their owners and repairs are listed in [`failure-and-evals.md`](failure-and-evals.md), [`safety-boundaries.md`](safety-boundaries.md), and [`acceptance.md`](acceptance.md). The design decisions are indexed in [`00-index.md`](00-index.md); unresolved choices are in [`open-questions.md`](open-questions.md). This README is navigation and boundary guidance, not a second contract owner.
