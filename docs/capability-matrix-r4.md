# Capability Matrix — Triple-AAA R4 final scope

The matrix is deliberately scoped to observed evidence. `PROVEN` means proven for the named scope, not universally. `PARTIAL` means some layers or artifacts exist but the acceptance envelope is incomplete. The status column uses only the six states frozen by the R4 bar.

| Capability | Owner | Structural | Runtime | Artifact | Multi-shot | Production | Status | Blocker |
|---|---|---|---|---|---|---|---|---|
| Scene Planning | core/director | PROVEN | NOT_APPLICABLE | PROVEN | PROVEN | NOT_APPLICABLE | PROVEN | None in deterministic scope |
| Scene Bible | core/director | PROVEN | NOT_APPLICABLE | PARTIAL | PARTIAL | BLOCKED | PARTIAL | LF-003 has a structural Bible; no accepted long-form production |
| Shot Graph | core/director | PROVEN | NOT_APPLICABLE | PARTIAL | PARTIAL | BLOCKED | PARTIAL | Only LF-001 has current runtime-linked shots |
| Continuity | quality/evidence | PROVEN | PARTIAL | PARTIAL | PARTIAL | BLOCKED | PARTIAL | S01/S02 pass bounded scorecards; S03 and T02 remain partial/failed |
| Reference Retention | core/runtime | PROVEN | UNKNOWN | PARTIAL | BLOCKED | BLOCKED | PARTIAL | Current LF-001 runs are T2V; reference-image identity is unproven |
| Prompt Compiler | core/quality | PROVEN | NOT_APPLICABLE | PROVEN | PROVEN | NOT_APPLICABLE | PROVEN | Structural compiler evidence only; it does not prove model behavior |
| H3 T2V | runtime/evidence | PROVEN | PROVEN | PROVEN | PARTIAL | PARTIAL | PROVEN | Proven only for the exact local H3/ComfyUI profile and observed scope |
| H3 R2V/I2V | runtime/evidence | PROVEN | UNKNOWN | PARTIAL | BLOCKED | BLOCKED | UNKNOWN | No current accepted reference-conditioned run |
| FLF | quality/runtime | PROVEN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | FIRST_ONLY, LAST_ONLY and FIRST_AND_LAST were not executed |
| Re-anchor | quality/evidence | PROVEN | PARTIAL | PROVEN | PARTIAL | BLOCKED | PARTIAL | Decision and bounded plan exist; repair execution is awaiting authorization |
| Dialogue | quality | PROVEN | NOT_RUN | NOT_RUN | BLOCKED | BLOCKED | BLOCKED | LF-002 has no dialogue-capable runtime evidence |
| Voice | provider boundary | PROVEN | UNKNOWN | NOT_RUN | BLOCKED | BLOCKED | BLOCKED | No authorized voice asset or provider run |
| Lip-sync | quality/provider | PROVEN | UNKNOWN | NOT_RUN | BLOCKED | BLOCKED | BLOCKED | No face/audio artifact or confirmed capability |
| Audio | media/quality | PROVEN | PARTIAL | PARTIAL | PARTIAL | BLOCKED | PARTIAL | Native H3 stream/foley is mechanically observed; no listening/mix acceptance |
| Resource Safety | runtime/evidence | PROVEN | PROVEN | PROVEN | PARTIAL | PARTIAL | PROVEN | Scoped to guarded local ComfyUI submissions; no foreign queue cancellation |
| Interaction | quality/director | PROVEN | PROVEN | PARTIAL | PARTIAL | BLOCKED | PARTIAL | S01/S02 action is readable; S03 artifacts prevent chain promotion |
| Vehicle Entry | quality/runtime | PROVEN | PROVEN | PARTIAL | PARTIAL | BLOCKED | PARTIAL | S01/S02 accepted; S03/T02 fail the production gate |
| Semantic QA | quality/evidence | PROVEN | NOT_APPLICABLE | PARTIAL | PARTIAL | BLOCKED | PARTIAL | Sampled semantic review exists; no dense/editorial acceptance |
| Transition QA | quality/evidence | PROVEN | NOT_APPLICABLE | PARTIAL | PARTIAL | BLOCKED | PARTIAL | T01 PARTIAL: cross-shot comparison NOT_OBSERVED; T02 FAIL because S03 is partial |
| Repair | quality/evidence | PROVEN | NOT_RUN | PARTIAL | PARTIAL | BLOCKED | PARTIAL | Natural drift was localized and re-anchor planned; no repair regeneration executed |
| Assembly | media/evidence | PROVEN | NOT_APPLICABLE | PARTIAL | PARTIAL | BLOCKED | PARTIAL | 15s preview passes mechanical QA but is not semantically promoted |
| LF-001 | director/runtime/evidence | PROVEN | PROVEN | PARTIAL | PARTIAL | BLOCKED | PARTIAL | S01/S02 accepted; S03 partial; final chain and editorial acceptance absent |
| LF-002 | director/audio/provider | PROVEN | NOT_RUN | NOT_RUN | BLOCKED | BLOCKED | BLOCKED | Dialogue, voice, lip-sync and mix evidence absent |
| LF-003 | director/evidence/media | PROVEN | NOT_RUN | NOT_RUN | BLOCKED | BLOCKED | BLOCKED | 50s plan exists; no dependent production chain or checkpoint |
| LF-004 | director/evidence | PROVEN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | Deferred until shorter ladder is accepted |
| Second Adapter | core/provider | PROVEN | NOT_RUN | NOT_RUN | BLOCKED | BLOCKED | BLOCKED | Only structural differential fixture; no second real runtime |
| Independent Critic | gauntlet | PROVEN | NOT_APPLICABLE | PARTIAL | PARTIAL | PARTIAL | PARTIAL | Fresh review is evidence of review, not a production acceptance substitute |

## Evidence pointers

- Frozen authority and prompt copy: `docs/triple-aaa-quality-bar-r4.json`, `docs/master-prompt-triple-aaa-final-production-closure-20260909.txt`.
- Runtime profile and resource guard: `verification/profiles/comfyui-h3-lf001-r4-v2.json`, `verification/comfyui-r4-baseline-20260909-a001.json`.
- Current read-only runtime/resource/workflow audit: `verification/comfyui-r4-live-state-20260909.json` (server up, H3 workflow valid, queue observed without mutation; not production proof).
- LF-001 case, transitions, repair decision and assembly: `verification/long-form/LF-001-r4-case.json`, `LF-001-T01-r4-transition-validation.json`, `LF-001-T02-r4-transition-validation.json`, `LF-001-S03-r4-reanchor-decision.json`, `LF-001-r4-assembly-preview-r2.json`.
- Deferred ladders: `verification/long-form/LF-002-r4-case.json`, `LF-003-r4-case.json`, `FLF-r4-evidence.json` and `verification/adapter-differential-r4.json`.

The R4 capability result is `PARTIAL`: the software Skill is ready with risks for the proven scope, while the audiovisual production pillar is not a Triple-AAA pass.
