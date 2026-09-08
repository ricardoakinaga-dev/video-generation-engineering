# Phase 0 documentation from master prompt — ExecPlan

<!-- engineering-framework: active_action_id=VGE-P0:FINAL -->

## Purpose / Big Picture

Create and review the complete Phase 0 documentation-first architecture for `video-generation-engineering-vNext` from the supplied master prompt and the preserved `docs/BLUEPRINT.md`. The result is a coherent design package for a future generative-video engineering director. It must stop before creating the production Skill, executable schemas, model adapters, workflow generators, or ComfyUI integrations.

## Current state

The workspace is greenfield, has no Git repository, runtime, model files, test harness, or `AGENTS.md`, and already contains a first documentation baseline from the earlier blueprint. The new master prompt is broader than that baseline. The required index, explicit domain/state ownership, complete golden/adversarial scenario fixtures, ADRs, observability, safety boundaries, future Skill structure, open questions, traceability, and Phase 0 report are present. Four distinct fresh critics have completed with material repairs; one fifth attempt was incomplete, and a sixth critic found only the expected pre-finish control-plane ordering issue. The content audit is clean before the next distinct final critic.

The Gauntlet run is `vge-phase0-docs-20260907`, with the frozen bar in `.gauntlet/bar.json`. The bar has 32 required criteria (`DOC-001` through `DOC-030`, `SAFE-001`, and `GAUNTLET-001`), including a strict no-production-artifact boundary and an independent final-critic requirement. Subsequent documentary remediation rounds are recorded in the preserved audit reports; the current r4 round closes AUD-012 with an immutable execution-attempt and content-hash contract.

## Frozen scope and constraints

- In scope: research refresh, architecture challenge, documentation consolidation, requirements, domain/state model, continuity, Scene Bible, references, dialogue/performance/lip-sync, interaction/motion, cinematography, audio, constraints, prompt compilation, adapters, ComfyUI planning boundary, long-form strategy, failure taxonomy, gates, eval strategy, 12 complete golden scenarios, adversarial scenarios, observability, safety, progressive disclosure, ADRs, future Skill structure, open questions, traceability, acceptance, and Phase 0 report.
- Out of scope: production `SKILL.md`, `agents/openai.yaml`, production `references/`, production scripts, production schemas, model adapters, executable ComfyUI integration, workflow generator, model downloads, runtime calls, uploads, paid APIs, and generated media.
- Existing user work is preserved. Existing consolidated docs are refined or linked rather than mechanically replaced.
- Claims about OpenAI/Codex use official OpenAI sources only. External model/runtime claims carry source, date, applicability, confidence, and limitations.

## Architecture and ownership

`docs/00-index.md` owns navigation and deviations from the suggested file tree. Existing owners remain authoritative where they already provide coherent coverage: `requirements.md`, `architecture.md`, `contracts.md`, `scene-and-continuity.md`, `directing.md`, `constraints.md`, `model-adaptation.md`, `comfyui-execution.md`, `failure-and-evals.md`, `acceptance.md`, `traceability.md`, and `research.md`. New focused documents own the previously missing boundaries: `vision-and-scope.md`, `domain-model.md`, `continuity-engine.md`, `golden-scenarios.md`, `adversarial-scenarios.md`, `observability.md`, `safety-boundaries.md`, `progressive-disclosure.md`, `proposed-skill-structure.md`, `open-questions.md`, `phase-0-report.md`, and `adr/` decision records.

No document may create a second canonical definition of a contract. Focused documents link to shared contracts and state semantics; examples remain fixtures or explanations.

## Workstreams

1. `VGE-P0:FOUNDATION`: add the numbered index, vision/scope, domain model, explicit state model, and requirement classification.
2. `VGE-P0:PIPELINE`: strengthen continuity, scene/reference, dialogue/performance, interaction/motion, cinematography/audio/constraints, compiler, adapters, ComfyUI, and long-form cross-links.
3. `VGE-P0:PROOF`: add complete golden scenarios, adversarial cases, observability, safety boundaries, and the research metadata refresh.
4. `VGE-P0:PACKAGING`: add progressive-disclosure routing, future Skill structure, ADRs, open questions, traceability updates, acceptance updates, and the Phase 0 report.
5. `VGE-P0:GAUNTLET`: run deterministic checks, capture fingerprints, commission fresh read-only critics, repair the largest material gap, integrate, and obtain a distinct final critic.

## Concrete steps

1. `[VGE-P0:DISCOVER-BASELINE]` **Complete.** Record current files, instructions, hashes, runtime/tool availability, and the frozen bar.
2. `[VGE-P0:FOUNDATION]` **Complete.** Create the missing navigation, scope, domain, and state documents; align existing requirements and contracts.
3. `[VGE-P0:PIPELINE]` **Complete.** Add or refine focused documents and links without duplicating canonical rules.
4. `[VGE-P0:PROOF]` **Complete.** Write full golden/adversarial fixtures and observability/safety evidence.
5. `[VGE-P0:PACKAGING]` **Complete.** Write ADRs, future Skill tree, progressive-disclosure matrix, open questions, traceability, acceptance, and final report.
6. `[VGE-P0:RUN-VERIFY]` **Complete for the pre-fix baseline and repeated after repair.** Run YAML/JSON/link/ID/coverage/scope checks and the Gauntlet helper validation; preserve raw-result hashes.
7. `[VGE-P0:CRITIQUE-FIX]` **Complete.** C1, C2, C3, and C4 rejected material documentation gaps; clean mutation sentinels were recorded, focused repairs were applied, and the post-fix audits returned zero errors.
8. `[VGE-P0:FINAL]` **Complete.** C3 and C4 identified and repaired adversarial, enum, navigation, handoff, canonical-prompt, retention-matrix, and evidence-shape gaps. C6 confirmed the content bar but rejected the expected pre-finish state; the report distinguishes content readiness from the post-approval finish transaction. The historical finish remains immutable and is not reused after documentary remediation.
9. `[VGE-P0:R4-REMEDIATION]` **Complete.** Define the immutable `ExecutionAttempt`, bind `GenerationArtifact.execution_attempt_ref` and collection-time `content_hash`, bind QA through `ArtifactObservation.generation_artifact_ref` and `observed_content_hash`, document two attempts with a repeated output locator, and pass the r4 structural collector plus affected-case assertions.

## Validation plan

- Parse every fenced YAML/JSON example with a safe parser.
- Resolve every local Markdown link and check required headings/files.
- Extract and cross-check requirement, gate, eval, source, ADR, golden, and adversarial IDs.
- Compare the 25 Phase 0 acceptance items and all master-prompt topic lists against traceability.
- Verify the source metadata fields and official OpenAI-domain boundary.
- Verify known-good and known-bad scenario coverage.
- Verify no production artifact, external execution, upload, credential, or generated media was introduced.
- Attempt `doctor.py` for the explicitly used local skills (the installed Gauntlet package does not provide that helper), and run `gauntlet_state.py validate` with drift checking.
- Use artifact fingerprints before/after every read-only critic; a mutation invalidates the critic result.

## Expected handoff

The Phase 0 report must state architecture status as `READY WITH RISKS` unless later evidence proves otherwise, list all documents, accepted/modified/removed/added blueprint decisions, critical risks, blockers/non-blockers, the minimal future Skill tree, and whether Phase 1 may begin. It must explicitly say that Phase 1 is not started.
