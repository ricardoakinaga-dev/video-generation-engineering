# Phase 0 report

## Implemented package — 2026-09-08

The repository skill now exists at [SKILL.md](../.agents/skills/video-generation-engineering/SKILL.md). [Implementation results](../IMPLEMENTATION.md) record tested software, actual local ComfyUI execution and remaining media/provider limits. The Phase 0 design and historical gates below are preserved; they do not certify the implementation. See [ADR-011](adr/ADR-011-skill-implementation-and-evidence.md).

## Report status

This is the historical Phase 0 final handoff report. Its content status is `REMEDIATED_VERIFIED` after the documented audits and static re-audit. The earlier Gauntlet critic and finish transaction remain historical control-plane evidence for the pre-remediation artifact; they do not certify the current implementation. ADR-011 subsequently authorized the repository package, whose separate evidence is linked above.

## Phase 0 result

**Architecture status:** `READY WITH RISKS` (the current documentation passed the r4 remediation re-audit; runtime/media evidence remains future work, and no new independent Gauntlet verdict is claimed for this revision).

The documentation defines a model-independent generative-video engineering director that turns intent into scene/state/shot plans, adapts them to evidenced capabilities, prepares a ComfyUI execution recipe, and separates planned truth from observed artifact truth. As a historical Phase 0 report it does not certify runtime execution; the subsequently authorized executable subset is documented separately in [IMPLEMENTATION.md](../IMPLEMENTATION.md).

## Documentation created

- Navigation/scope: [`00-index.md`](00-index.md), [`vision-and-scope.md`](vision-and-scope.md), [`requirements.md`](requirements.md).
- Architecture/contracts: [`architecture.md`](architecture.md), [`domain-model.md`](domain-model.md), [`state-model.md`](state-model.md), [`contracts.md`](contracts.md), [`continuity-engine.md`](continuity-engine.md).
- Planning/directing: [`scene-and-continuity.md`](scene-and-continuity.md), [`directing.md`](directing.md), [`constraints.md`](constraints.md), [`pattern-library.md`](pattern-library.md).
- Model/runtime: [`model-adaptation.md`](model-adaptation.md), [`comfyui-execution.md`](comfyui-execution.md), [`research.md`](research.md).
- Proof: [`failure-and-evals.md`](failure-and-evals.md), [`golden-scenarios.md`](golden-scenarios.md), [`adversarial-scenarios.md`](adversarial-scenarios.md), [`acceptance.md`](acceptance.md), [`traceability.md`](traceability.md).
- Operations/boundaries: [`observability.md`](observability.md), [`safety-boundaries.md`](safety-boundaries.md), [`progressive-disclosure.md`](progressive-disclosure.md), [`proposed-skill-structure.md`](proposed-skill-structure.md), [`open-questions.md`](open-questions.md), [`roadmap.md`](roadmap.md).
- Decisions: [`adr/`](adr/).
- Original input: [`BLUEPRINT.md`](BLUEPRINT.md), preserved separately from the new master prompt.

## Major decisions

1. Documentation-first Phase 0 precedes production Skill creation.
2. The canonical scene/state model owns intent, identity, continuity, and evidence; prompts are compiled views.
3. Scene Model and Scene Bible are unified semantically but kept as distinct views to avoid duplicating global invariants in every shot.
4. Story, interaction, motion, camera, audio, and QA are logical responsibilities with separate failure criteria, not necessarily separate runtime services.
5. Model/runtime capabilities are versioned profiles with explicit evidence; repository support does not imply ComfyUI support.
6. Long-form work is a validated shot/segment graph with canonical re-anchors, not one unbounded prompt.
7. Script, visual performance, audio generation, and lip-sync are separate contracts.
8. Constraints distinguish generation guidance, runtime control, and QA assertion.
9. Pattern resources and deterministic scripts enter only after fixture-backed value is demonstrated.
10. External effects, likeness/voice use, private data, and publication remain explicit human/authorization boundaries.

## Blueprint changes

### Accepted

- The end-to-end pipeline from intent through model adaptation, execution planning, and validation.
- Scene Bible, narrative timeline, shot graph, continuity state, anchors, directing layers, model adapters, ComfyUI planning, long-form strategy, quality gates, evals, and progressive disclosure.
- The distinction between a generative-video engineering director and a prompt generator.

### Modified

- `LOCKED` is a retention target plus QA obligation, not a stochastic guarantee.
- Duration thresholds are continuous minimum structural floors for real-valued `t` in seconds: `0 < t ≤ 30` is the base, `30 < t ≤ 45` adds a narrative timeline, `45 < t < 60` adds Scene Bible/shot graph/planned propagation, `60 ≤ t < 90` adds applicable timelines, strategy, and assembly, and `90 ≤ t ≤ 120` adds branches, recovery checkpoints, a provenance manifest and human checkpoints; complexity and dependency risk can escalate planning earlier.
- FLF/chaining requires confirmed profile support, endpoint validation, reset strategy, and degradation budget.
- Audio/lip-sync is separable unless a concrete profile proves joint behavior.
- “Constraint” is split into generation hint, runtime control, input requirement, QA assertion, assembly rule, and rights/safety policy.
- Suggested file tree is consolidated where documents share a canonical owner, with focused files added only for missing review boundaries.

### Removed from Phase 0 implementation

- Production `SKILL.md`, `agents/openai.yaml`, production references/scripts/schemas, adapters, workflow generators, and executable ComfyUI integration.
- Assumed runtime/model guarantees, arbitrary provider policy, automatic uploads/queues, and generated media claims.

### Added

- Explicit domain/state contracts, 12 complete golden fixtures, 17 adversarial scenarios, observable diagnostics, modular safety/provenance boundaries, ADRs, open-question queue, file-by-file Skill structure justification, and the Phase 0 report.

## Critical risks

- No local ComfyUI/runtime/model target has been selected or probed; capability profiles remain evidence-bounded.
- Visual identity, contact, physics, camera, audio, and lip-sync acceptance require future artifact-level or qualified human review.
- External likeness, voice, private data, provider policy, and publication authority cannot be inferred by the Skill.
- The documentation is broad; implementation must preserve progressive disclosure and avoid loading every reference for simple tasks.

## Open questions

### Staged blockers

`OQ-B-001` is the only blocker before a plan-only Phase 1 skeleton: it defines the host/package invocation boundary. `OQ-B-004` gates model/profile activation in Phase 3, `OQ-B-003` gates external execution in Phase 4, and `OQ-B-002` gates artifact/media acceptance in Phase 5. The complete queue and required evidence are in [`open-questions.md`](open-questions.md); none of the later-stage answers is silently treated as resolved.

### Non-blockers

Schema inheritance for `Subject`, observation persistence shape, numeric drift tolerances, pattern/template thresholds, script boundary, profile file selection, and long-form manifest mechanics can be decided during Phase 1 fixtures without changing the product mission.

## Proposed final Skill structure

The minimal tree and each file's reason/trigger/decision value/breakage consequence are in [`proposed-skill-structure.md`](proposed-skill-structure.md). In summary: one concise `SKILL.md`, nine conditional references, optional templates, one optional deterministic validator, and optional `agents/openai.yaml` metadata.

## Implementation readiness

**Phase 1 — Skill Skeleton & Core Contracts:** `CONDITIONALLY READY` was the historical status at report time. It was later entered under the explicit authorization captured by ADR-011; see the implementation report for current package evidence.

## Verification and stop point

The previous documentation Gauntlet run, frozen bar, artifact fingerprints, independent critic records, and finish transaction remain historical evidence under `.gauntlet/`; their fingerprint predates the current implementation. Current package review evidence is recorded separately under `verification/` and must not be conflated with this historical Phase 0 report.

## Review evidence and repair record

The first fresh-context critic (`C1-Herschel-20260907`) reviewed the pre-fix artifact and returned `REJECT` with six material gap groups: incomplete adversarial fields; inconsistent failure/pattern/golden IDs; unprobed profiles marked `CONFIRMED`; untraceable NFRs; underspecified aggregate/reference-conflict/motion contracts; and a handoff that did not yet record its review evidence. The mutation sentinel was clean.

The documented repairs are now applied: every adversarial case has an explicit outcome, reason, preserved intent, evidence gap, and next action; compact and expanded failure IDs and pattern/golden mappings are reconciled; candidate profiles are explicitly `PROPOSED` until exact runtime probes exist; NFRs have stable IDs and end-to-end traceability; aggregate/view concepts, `ReferenceConflict`, and motion fields are owned; and execution modes use the canonical uppercase enum values.

The second fresh-context critic (`C2-Volta-20260907`) reviewed the repaired candidate and returned `REJECT` for residual compact failure-table shape/ID drift, incomplete per-feature capability evidence, and vocabulary/scope/enum inconsistencies across contracts, profiles, Scene Bible, constraints, and camera examples. The repair pass added the complete alias map, explicit scene-revision scope, per-feature evidence statuses and limitations, uppercase serialized examples, complete camera-state fields, and oracle classes for evaluation categories.

The first final-critic attempt (`C3-Rawls-20260907`) reviewed that candidate in a sealed fresh context and returned `REJECT` for a missing abrupt-location-change adversarial fixture, residual unmapped status/enum examples, and incomplete long-document quality navigation. The follow-up repair added `ADV-017`, explicit precedence/issue/severity/rights enum mappings, aligned continuity and constraint examples, document-level contracts and contents sections, corrected the 32-criterion count, and clarified the `.agent` versus `.gauntlet` verification pointers.

At that time, the next distinct final critic (`C4-Pascal-20260907`) reviewed the repaired candidate in a sealed fresh context and returned `REJECT` for a malformed canonical prompt example, the absence of a single integrated retention matrix, combined adversarial evidence fields, four missing Contents sections, the stale 16-scenario handoff count, and the still-pending finish record. The follow-up repair nests the canonical sections and mapping, adds the four-policy retention matrix with conflict/priority/degradation risk, separates `evidence_gap` from `evidence_required` in every adversarial row, completes long-document navigation, normalizes the remaining `NOT_RUN` result and continuity vocabulary, and updates the handoff count.

The post-repair integrated candidate had these limitations by design: no ComfyUI/runtime/model probe, generated artifact, visual/audio oracle, rights clearance, or external execution was performed. Those are `NOT_RUN` future evidence, not hidden passes. The later historical finish transaction closed that earlier candidate; the remediation below changes the artifact and must not reuse that finish as current approval.

## Frozen review-bar inventory

The historical Gauntlet bar for this handoff contains 32 required criteria: `DOC-001` through `DOC-030`, `SAFE-001`, and `GAUNTLET-001`. The frozen definitions and their evidence methods are in `.gauntlet/bar.json`; executed statuses, fingerprints, critic packets, and limitations remain preserved in the control-plane history. Because the remediation changes the artifact, a future Gauntlet run must use a new identity rather than rewriting this history.
Before the historical finish transaction, the attempted final critic (`C5-Ptolemy-20260908`) did not return a usable verdict after an extended read-only inspection and was shut down; its incomplete attempt is not treated as evidence. The next distinct critic (`C6-Bacon-20260908`) found all content criteria through `DOC-029` and `SAFE-001` passing, but returned `REJECT` because it evaluated the expected pre-finish control-plane state as a failure for `DOC-030` and `GAUNTLET-001`. The subsequent historical finish transaction recorded the approved pre-remediation artifact; that sequence is preserved and is not reused as current evidence.

## Remediation of AUDIT-docs-2026-09-08

The audit report is preserved as the finding record. The following table records the closures applied after the first audit; it is historical context for that revision, not the latest re-audit verdict:

| Finding | Current closure |
|---|---|
| AUD-001 | `contracts.md` now owns the serialized field names and legacy migration boundary; the SceneSpec and capability examples in `scene-and-continuity.md` and `model-adaptation.md` emit the same canonical `ShotSpec`/`CapabilityProfile` fields. |
| AUD-002 | `continuity-engine.md` now defines initial state, `PLAN_ONLY` planned-channel traversal, execution observed-channel traversal, dry-run limits, and dependent-state invalidation after contradiction. |
| AUD-003 | The observation fixture is correctly `PARTIAL`; `contracts.md` and `acceptance.md` define aggregate status precedence and formal waiver requirements. |
| AUD-004 | `eval_G-004_v1` now checks dialogue speaker/listener, interval, reaction, and articulation semantics; transfer contact/ownership oracles are isolated in `eval_G-006_v1`, and traceability points Dialogue Director to G-004/G-011. |
| AUD-005 | `requirements.md`, `scene-and-continuity.md`, `architecture.md`, `vision-and-scope.md`, and `research.md` agree on continuous duration floors: `0 < t ≤ 30`, `30 < t ≤ 45`, `45 < t < 60`, and `60 ≤ t ≤ 120`; complexity can escalate earlier. |
| AUD-006 | `open-questions.md`, `roadmap.md`, `safety-boundaries.md`, and this report stage blockers at Phase 1, 3, 4, and 5 instead of requiring runtime/media/external evidence from the plan-only skeleton. |
| AUD-007 | The index, README, and this report expose `REMEDIATED_VERIFIED`, identify the old Gauntlet `FINISHED/PASS` as historical/stale for this fingerprint, and point to the current static re-audit without rewriting history. |
| AUD-008 | The twelve Golden-scenario contents links now use the adopted GitHub heading slugs with the preserved double-hyphen separator. |

The original static re-audit executed on 2026-09-08 in the local workspace with Python 3 and PyYAML: 39 Markdown files, 45 YAML blocks, zero YAML errors, zero broken local files/anchors, 66 requirements, 13 NFRs, 17 quality gates, 12 golden cases, 17 adversarial cases, 25 Phase 0 items, 39 expanded failure rows, 46 blueprint sections, and 10 ADRs. That evidence is retained for the first remediation revision and is superseded for the current content by the second-review re-audit below. `docs/BLUEPRINT.md` remains byte-for-byte unchanged at SHA-256 `62c04a55fe991a8f094db47d661ab6fa70fbe20e26f0adbfda402eba78f6fc1d`. No runtime, ComfyUI, model, media, rights, or external execution evidence was created; those remain future limitations.

## Remediation of AUDIT-docs-2026-09-08-r2

The second-review report is preserved unchanged as the finding record. The five remaining problems are closed in the current documentation revision:

| Finding | Current closure |
|---|---|
| AUD-001 residual — profile/contract divergence | `contracts.md` and `model-adaptation.md` now emit the same complete `CapabilityProfile` fixture for `comfyui-wan22-native-v1` revision `1`, including modes, limits, camera-control keys/status, nested feature evidence, and the sole canonical prompt `omissions` location. |
| AUD-002 residual — continuity/QA state mixing | `continuity-engine.md`, `state-model.md`, and `pattern-library.md` distinguish `shot.lifecycle_status` from `ArtifactObservation.status` and define channel-aware state carry plus permitted lifecycle effects. |
| AUD-006 residual — Phase 1 probe prerequisite | `model-adaptation.md` and `comfyui-execution.md` now keep Phase 1/2 plan-only and route profile activation to Phase 3, local preflight to Phase 4, and artifact/media acceptance to Phase 5. |
| AUD-009 — YAML `off` coercion | `contracts.md` defines ignition as a quoted string enum and all three examples use `ignition: "OFF"`. |
| AUD-005 residual — fractional duration gaps | `requirements.md`, `scene-and-continuity.md`, `vision-and-scope.md`, `architecture.md`, and this report use continuous real-valued intervals with explicit boundaries through `t ≤ 120`. |

The current focused re-audit was run in the local workspace with Python 3 and PyYAML. It found 39 Markdown files, 44 YAML blocks, zero YAML parse errors, zero broken local destinations, zero implicit non-boolean YAML booleans, exact profile fixture parity, top-level prompt omissions in both canonical views, and no residual Phase 1 probe requirement. Affected-case checks covered `t = 30`, `30.5`, `45`, `45.5`, `59.5`, `60`, `89.5`, `90`, and `120` seconds; active-channel state carry; lifecycle/QA separation; and quoted ignition parsing. The blueprint hash remains `62c04a55fe991a8f094db47d661ab6fa70fbe20e26f0adbfda402eba78f6fc1d`. No runtime, ComfyUI, model, media, rights, or external execution evidence was created, and no new independent Gauntlet verdict is claimed.

## Remediation of AUDIT-docs-2026-09-08-r3

The third-review report is preserved unchanged as the finding record. Its two remaining post-generation problems are closed in the current documentation revision:

| Finding | Current closure |
|---|---|
| AUD-010 — `NOT_RUN` versus shot lifecycle | `continuity-engine.md`, `state-model.md`, `contracts.md`, and `comfyui-execution.md` now distinguish no artifact (`PLANNED`/`READY`), running without output (`RUNNING`), collected artifact awaiting QA (`GENERATED` with `quality_review.lifecycle: NOT_STARTED`), review in progress (`REVIEW`), and a pending non-evidentiary `ArtifactObservation.status: NOT_RUN`. QA status never regresses or overwrites the shot lifecycle. |
| AUD-011 — collection record versus QA observation | `GenerationArtifact` now has its own canonical collection/provenance contract. The ComfyUI example uses that record for collection, then links a separate canonical `ArtifactObservation` for pending and completed QA, preserving `id`, `shot_id`, `artifact_ref`, procedure, timestamp, checks, limitations, and repair route. |

The current focused re-audit was run in the local workspace with Python 3 and PyYAML using the preserved structural collector plus affected-case assertions. It found 39 Markdown files, 48 YAML blocks, 378 local Markdown links with zero broken destinations, zero YAML parse errors, zero implicit non-boolean YAML booleans, exact `GenerationArtifact` fixture parity between `contracts.md` and `comfyui-execution.md`, canonical observation fields in both pending and completed QA records, and explicit lifecycle cases for `PLANNED`, `RUNNING`, `GENERATED`, and `REVIEW`. The pending record has `observed_at: null`, `procedure: null`, and empty checks; the completed record has an executed procedure and `PARTIAL` result. The blueprint hash remains `62c04a55fe991a8f094db47d661ab6fa70fbe20e26f0adbfda402eba78f6fc1d`. No runtime, ComfyUI, model, media, rights, or external execution evidence was created, and no new independent Gauntlet verdict is claimed.

## Remediation of AUDIT-docs-2026-09-08-r4

The fourth-review report is preserved unchanged as the finding record. Its new post-generation problem is closed in the current documentation revision:

| Finding | Current closure |
|---|---|
| AUD-012 — incomplete collection provenance | `contracts.md` now owns an immutable `ExecutionAttempt` contract containing the plan reference, per-attempt identity, profile/model/runtime/node/workflow context, inputs, parameters, queue/progress references, and explicit `unknown_fields`. `GenerationArtifact.execution_attempt_ref` and its collection-time `content_hash` bind each output to one attempt. `ArtifactObservation.generation_artifact_ref` and `observed_content_hash` bind QA to those bytes; a locator is never identity. `comfyui-execution.md` includes two attempts for one shot, with distinct context and hashes even when the output path repeats, plus the stale-hash/recollection rule. |

Unknown execution values use `null` plus a canonical dotted path in `ExecutionAttempt.unknown_fields`; required missing profile/model version, workflow identity, input hash, or output hash blocks QG-17 and artifact acceptance. Optional missing seeds/parameters are disclosed and prevent a reproducibility claim. A current-byte hash mismatch invalidates dependent observations and requires recollection and affected QA. No implicit filename linkage remains.

The r4 focused re-audit was run in the local workspace with Python 3 and PyYAML using the r4 collector plus affected-case assertions. It found 39 Markdown files, 50 YAML blocks, zero YAML parse errors, zero broken local destinations, zero implicit non-boolean YAML booleans, complete profile parity, exact `GenerationArtifact` fixture parity, complete `ExecutionAttempt` provenance in the two-attempt fixture, distinct artifact hashes for the repeated output locator, matching observation hashes, and explicit stale-hash rejection semantics. The blueprint hash remains `62c04a55fe991a8f094db47d661ab6fa70fbe20e26f0adbfda402eba78f6fc1d`. No runtime, ComfyUI, model, media, rights, or external execution evidence was created, and no new independent Gauntlet verdict is claimed.
