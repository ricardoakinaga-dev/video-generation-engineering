# ADR-011 — Implemented skill boundary and evidence

Status: accepted for implementation on 2026-09-08 under the user's explicit full-build request.

## Context

Phase 0 and its audits specified a future skill. The user subsequently authorized implementation, testing and local ComfyUI use. The documentation-only stop no longer applies to this authorized build; historical Phase 0 evidence remains unchanged.

## Decision

Create the repository-scoped skill at `.agents/skills/video-generation-engineering`, supporting Codex IDE/CLI discovery and explicit invocation with PLAN_ONLY default. Keep nine conditional references and a small authored treatment example. Use standard-library Python for repeated deterministic checks and runtime mechanics; native FFmpeg/ffprobe are optional media dependencies.

The JSON ScenePlan aggregate contains the canonical version-1 objects. `ShotSpec.state_changes` explicitly serializes property/prior/next/cause alongside canonical start/end delta maps. Derived graph/state/timeline views are recomputed and checked. Required quality-gate IDs come from the shot's acceptance contract. No structural result promotes planned state into observed truth.

ExecutionAttempt progress uses append-only revisions with the same attempt ID, revision number and supersedes_hash. The submission intent is recorded before the network effect; the returned queue ID seals the submitted revision. A successful history can append a completion revision, but a FAILED/CANCELLED attempt cannot become successful. Artifacts refer to the attempt and immutable bytes; acceptance resolves the successful revision.

Local discovery found an installed ComfyUI/H3 setup. A scoped probe demonstrated one small T2V/audio workload. Confirm only that tested profile subset; other model/reference/FLF/audio-sync/media-quality claims remain conditional. Candidate paid-provider support is separate and never an automatic fallback.

## Alternatives

Instruction-only was insufficient for repeated state, hash, DAG and runtime-recovery invariants. A general service framework, mandatory schema dependency or embedded renderer would exceed the documented mission. Global installation would create unnecessary duplicate discovery; keep the requested project path.

## Consequences and validation

The skill is portable independently of docs/. Semantic direction remains an agent responsibility. Tests use known-bad mutations, a real local HTTP boundary, fake provider responses, native synthetic media and a separately recorded ComfyUI probe. Forward-use findings and remediation are retained. None certifies universal AAA visual quality, qualified consent, provider access or untested long-form media.

Current implementation/evidence: [implementation report](../../IMPLEMENTATION.md). Historical decisions and audit snapshots retain their original scope and dates.
