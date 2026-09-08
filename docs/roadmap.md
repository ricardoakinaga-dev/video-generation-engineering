# Roadmap and implementation boundary

## Implemented package — 2026-09-08

The repository skill now exists at [SKILL.md](../.agents/skills/video-generation-engineering/SKILL.md). [Implementation results](../IMPLEMENTATION.md) record tested software, actual local ComfyUI execution and remaining media/provider limits. The Phase 0 design and historical gates below are preserved; they do not certify the implementation. See [ADR-011](adr/ADR-011-skill-implementation-and-evidence.md).

The supplied blueprint asked for documentation and validation before a production Skill. That was the original Phase 0 boundary; ADR-011 records the later explicit authorization for the current repository package. The historical sequencing below remains useful for scope and future evidence, but it is not a statement that the package is absent.

## Purpose

Sequence the work from the documentation-first architecture to a future, explicitly authorized Skill implementation. The roadmap is a release boundary and readiness contract; it does not authorize any later phase by itself.

## Terminology and invariants

`Phase 0` means reviewed design documentation; `Phase 1` means the first production package skeleton; `Phase 2+` means implementation and runtime evidence. The invariant is that no later phase may silently weaken canonical state/evidence semantics or bypass the plan-only and authorization boundary.

## Phase 0 — documentation baseline (historical complete)

Deliverables:

- verbatim blueprint copy and numbered navigation hub;
- vision/scope, requirements, architecture, domain/state, contracts, Scene Bible/continuity, directing, constraints, adaptation, execution, pattern, research, failure/eval, acceptance, and traceability docs;
- complete golden/adversarial fixtures, observability, safety/authorization, progressive disclosure, ADRs, open questions, future Skill structure, and Phase 0 report;
- stable IDs, evidence statuses, source links, and Gauntlet/control-plane verification records;
- no production Skill, executable adapter/schema/workflow generator, runtime queue, upload, paid API call, or generated media **within the original Phase 0 deliverable**. The separately authorized current package and its bounded local evidence are documented in [IMPLEMENTATION.md](../IMPLEMENTATION.md).

Exit gate: `READY WITH RISKS` when static/integration checks and independent review pass, with runtime/media limitations and blockers recorded. `READY WITH RISKS` is not a claim of production or artifact readiness.

## Phase 1 — Skill skeleton (implemented in the current authorized package)

The current package implements this minimum shape under `.agents/skills/video-generation-engineering`:

- `SKILL.md` with concise activation description and workflow;
- optional references for the canonical contracts and gates;
- no model-specific claims without the research registry;
- plan-only behavior as the default;
- tests for invocation, progressive disclosure, and refusal of unsupported execution.

Entry criteria were Phase 0 completion, `OQ-B-001` handling, and the user's explicit implementation request. The package remains `PLAN_ONLY` by default and does not claim `OQ-B-002`, `OQ-B-003`, or `OQ-B-004` resolved. Exit evidence is recorded in [IMPLEMENTATION.md](../IMPLEMENTATION.md) and the current verification reports.

## Phase 2 — canonical planning engine

Implement intent normalization, Scene Bible, reference retention, complexity routing, shot/state graph, constraint selection, prompt view, and quality-gate reporting. Use golden cases before integrating a model.

Exit criteria: all G-001 through G-007 pass at the structural/planning tier, with unresolved cases reported rather than hidden.

## Phase 3 — model profiles and adapters

Implement versioned capability profiles and adapter negotiation for a small, evidence-backed subset. Start with one local ComfyUI profile and one external API profile; keep H3 and other unverified capabilities non-executable.

Entry criteria: `OQ-B-004` resolved for the selected profile subset. Exit criteria: compatibility reports, compiled prompt mappings, parameter validation, and adapter observations are reproducible in fixtures.

## Phase 4 — optional ComfyUI integration

Add local dry-run discovery, API-format workflow validation, explicit queue authorization, websocket/history recovery, artifact collection, and provenance. Cloud support remains a separate authenticated target.

Entry criteria: `OQ-B-003` resolved when an external transfer or provider path is in scope; a local-only dry-run path does not require that external-authority decision. Exit criteria: preflight and dry-run suites pass; execution remains opt-in and bounded.

## Phase 5 — long-form and production evaluation

Add validated shot chaining, re-anchoring, assembly, audio/lip-sync paths, artifact-level continuity checks, human-review checkpoints, and regression datasets.

Entry criteria: `OQ-B-002` resolved for the artifact/media gates in scope. Exit criteria: long-form golden cases pass agreed quality thresholds, provenance is complete, and failure rates are measured on a frozen evaluation set.

## Triple-AAA closure R2 — current implementation extension

The current authorized package adds a deterministic quality boundary without collapsing the historical phases: category-separated semantic observations, 14-dimension continuity scorecards, transition/re-anchor contracts, first/last-frame probes, dialogue/audio/contact contracts, mechanical media QA, feature-scoped expiration, workflow fingerprints, bounded repair budgets, adapter differential reports, long-form envelopes and independent release scoring. The exact local H3 R2V probe is recorded as capability evidence only; unavailable second-model and full ladder evidence remain blocked.

Exit criteria are frozen in [`triple-aaa-quality-bar-r2.json`](triple-aaa-quality-bar-r2.json) and the current final report. `TRIPLE_AAA_CANDIDATE` is not allowed while the production gate has unresolved media evidence.

## Phase transition failure modes

| Failure | Detection | Repair/decision |
|---|---|---|
| Phase 1 starts before Phase 0 evidence is integrated | acceptance/report/status mismatch | stop and return to the missing gate |
| Runtime confidence exceeds profile evidence | stale or unscoped capability record | revalidate profile or keep the path blocked |
| Implementation duplicates canonical contracts | package review finds divergent entities/statuses | consolidate or record an ADR before coding |
| Long-form behavior is added without artifact oracles | no fixture/observation path for continuity | add the eval and review boundary first |

## Explicit non-goals

- silently choosing or downloading models;
- claiming capabilities from marketing text without an operational contract;
- automatically queuing generation without authorization;
- treating one prompt or negative prompt as a continuity guarantee;
- replacing human review for identity, rights, story, or material quality decisions;
- using the historical Phase 0 docs as a substitute for the current package or its tests.

## Revalidation triggers

Revalidate affected docs and profiles when a model release, ComfyUI release, node schema, API contract, hardware target, rights requirement, or evaluation threshold changes. Record the reason, source, date, and impacted requirements.

## Open questions and related documents

Phase transition blockers are tracked in [`open-questions.md`](open-questions.md). The current implementation boundary is defined in [`architecture.md`](architecture.md) and [`proposed-skill-structure.md`](proposed-skill-structure.md); quality gates and evidence limits are in [`acceptance.md`](acceptance.md) and [`failure-and-evals.md`](failure-and-evals.md). This roadmap owns sequencing, not domain semantics.
