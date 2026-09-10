# Capability Matrix R9

This is the current, claim-scoped matrix for `VGE-TRIPLE-AAA-R9-EVIDENCE-CLOSURE`. A `PROVEN` cell means that the referenced structural, runtime, or artifact evidence proves only that layer. It does not promote a mechanical check, fixture, prompt, profile name, or local runtime health into semantic production acceptance.

| Capability | Structural | Runtime | Artifact | Multi-shot | Production | Maturity | Status | Blocker / boundary |
|---|---|---|---|---|---|---|---|---|
| Scene Planning | PROVEN | NOT_RUN | PROVEN | PROVEN | NOT_APPLICABLE | L1 `STRUCTURALLY_VALIDATED` | PROVEN | Canonical planning records are validated; no video claim follows. |
| Scene Bible | PROVEN | NOT_RUN | PROVEN | PARTIAL | NOT_APPLICABLE | L1 `STRUCTURALLY_VALIDATED` | PROVEN | Required identity, environment, lighting, voice and drift fields are structural; observed continuity remains partial. |
| Shot Graph | PROVEN | NOT_RUN | PROVEN | PARTIAL | NOT_APPLICABLE | L1 `STRUCTURALLY_VALIDATED` | PROVEN | Ordered dependencies and state deltas are represented; no dependent production chain is closed. |
| Continuity state | PROVEN | NOT_RUN | PARTIAL | PARTIAL | BLOCKED | L2 `RUNTIME_EXECUTED` | PARTIAL | LF-001 runtime records exist, but S03 drift and T02 failure remain. |
| Reference Retention | PROVEN | PARTIAL | PARTIAL | PARTIAL | BLOCKED | L2 `RUNTIME_EXECUTED` | PARTIAL | R2V/I2V records and inventory exist; reference identity/retention is not accepted. |
| Canonical Contradiction Gate | PROVEN | NOT_RUN | PROVEN | PROVEN | NOT_APPLICABLE | L1 `STRUCTURALLY_VALIDATED` | PROVEN | State, ownership, door, motion and approach-held-target contradictions fail before compilation. |
| Prompt Compiler | PROVEN | NOT_RUN | PROVEN | PROVEN | NOT_APPLICABLE | L1 `STRUCTURALLY_VALIDATED` | PROVEN | Density, truncation, canonical-state identity, loss and remapping contracts are explicit. |
| Risk-Based Constraints | PROVEN | NOT_RUN | PROVEN | PROVEN | NOT_APPLICABLE | L1 `STRUCTURALLY_VALIDATED` | PROVEN | Vehicle, dialogue, audio and portrait risk families are selected by scene risk. |
| H3 T2V | PROVEN | PROVEN | PROVEN | NOT_APPLICABLE | PARTIAL | L3 `ARTIFACT_OBSERVED` | PROVEN (scoped) | Historical local ComfyUI/workflow and hash-bound output records are observed; the shipped summary profile is `UNKNOWN`/`EXTERNAL_ONLY` for portability, and semantics/editorial remain separate. |
| H3 R2V/I2V | PROVEN | PARTIAL | PARTIAL | PARTIAL | BLOCKED | L2 `RUNTIME_EXECUTED` | PARTIAL | Existing workflow/profile/artifacts do not close reference retention and identity observations. |
| FLF `FIRST_ONLY` | PROVEN | NOT_RUN | NOT_RUN | NOT_APPLICABLE | BLOCKED | L1 `STRUCTURALLY_VALIDATED` | NOT_RUN | `flf-probe` can prepare the mode and `flf-suite` requires it; no endpoint execution or artifact exists. |
| FLF `LAST_ONLY` | PROVEN | NOT_RUN | NOT_RUN | NOT_APPLICABLE | BLOCKED | L1 `STRUCTURALLY_VALIDATED` | NOT_RUN | `flf-probe` can prepare the mode and `flf-suite` requires it; no endpoint execution or artifact exists. |
| FLF `FIRST_AND_LAST` | PROVEN | NOT_RUN | NOT_RUN | NOT_APPLICABLE | BLOCKED | L1 `STRUCTURALLY_VALIDATED` | NOT_RUN | `flf-probe` can prepare the mode and `flf-suite` requires it; no endpoint execution or artifact exists. |
| Re-anchor | PROVEN | NOT_RUN | PROVEN | PARTIAL | BLOCKED | L1 `STRUCTURALLY_VALIDATED` | PARTIAL | Decision and route exist; no authorized new generation or accepted downstream revalidation exists. |
| Dialogue | PROVEN | NOT_RUN | NOT_RUN | NOT_APPLICABLE | BLOCKED | L1 `STRUCTURALLY_VALIDATED` | BLOCKED | Canonical speaker/listener, reaction, causal-order and voice/lip strategy declarations are enforced; no real line-level semantic artifact/review. |
| Voice | PROVEN | NOT_RUN | NOT_RUN | NOT_APPLICABLE | BLOCKED | L1 `STRUCTURALLY_VALIDATED` | BLOCKED | Actual audio-stream binding is enforced; no authorized voice artifact or listening review. |
| Lip-sync | PROVEN | NOT_RUN | NOT_RUN | NOT_APPLICABLE | BLOCKED | L1 `STRUCTURALLY_VALIDATED` | BLOCKED | Visible speech requires paired face-frame/audio evidence; no sync observation exists. |
| Audio | PROVEN | NOT_RUN | NOT_RUN | NOT_APPLICABLE | BLOCKED | L1 `STRUCTURALLY_VALIDATED` | BLOCKED | Timeline and stream checks are strict; no accepted dialogue/mix artifact exists. |
| Interaction | PROVEN | NOT_RUN | PARTIAL | PARTIAL | BLOCKED | L2 `RUNTIME_EXECUTED` | PARTIAL | Causality, contact, ownership and vehicle contracts pass structurally; semantic observation is incomplete. |
| Vehicle Entry | PROVEN | PROVEN (H3 T2V) | PARTIAL | PARTIAL | BLOCKED | L3 `ARTIFACT_OBSERVED` | PARTIAL | S01/S02 records exist; S03 drift, T02 failure, repair and editorial closure remain. |
| Semantic QA | PROVEN | NOT_RUN | PARTIAL | PARTIAL | BLOCKED | L2 `RUNTIME_EXECUTED` | PARTIAL | Hash/oracle/lineage rules are fail-closed; existing semantic evidence is not a production PASS. |
| Transition QA | PROVEN | NOT_RUN | PARTIAL | PARTIAL | BLOCKED | L2 `RUNTIME_EXECUTED` | PARTIAL | T01 is partial and T02 fails; PASS needs distinct artifacts and semantic observations. |
| Repair | PROVEN | NOT_RUN | PARTIAL | PARTIAL | BLOCKED | L1 `STRUCTURALLY_VALIDATED` | BLOCKED | Distinct parent/new attempts, artifacts, diagnosis/owner/delta, chronological before/after observations and affected transitions are required; no real repair ran. |
| Assembly | PROVEN | NOT_RUN | PARTIAL | PARTIAL | BLOCKED | L3 `ARTIFACT_OBSERVED` | PARTIAL | Preview assembly and final-artifact lineage are validated; editorial acceptance is not observed. |
| LF-001, 15 s vehicle entry | PROVEN | PROVEN (scoped) | PARTIAL | PARTIAL | BLOCKED | L3 `ARTIFACT_OBSERVED` | PARTIAL | S03 drift, T02 failure, preview-only assembly and missing editorial closure. |
| LF-002, 20–30 s dialogue | PROVEN | NOT_RUN | NOT_RUN | NOT_APPLICABLE | BLOCKED | L1 `STRUCTURALLY_VALIDATED` | BLOCKED | No dialogue-capable production artifact, listening review or accepted sync evidence. |
| LF-003, 45–60 s long form | PROVEN | NOT_RUN | NOT_RUN | NOT_RUN | BLOCKED | L1 `STRUCTURALLY_VALIDATED` | BLOCKED | Ordered case envelope exists as a recorder; no accepted dependent 6–12-shot production chain. |
| LF-004 optional extension | PROVEN | NOT_RUN | NOT_RUN | NOT_APPLICABLE | NOT_APPLICABLE | L0 `DOCUMENTED` | NOT_APPLICABLE | Optional extension was not authorized or required for this run. |
| Second Adapter | PROVEN | NOT_RUN | NOT_RUN | NOT_APPLICABLE | BLOCKED | L1 `STRUCTURALLY_VALIDATED` | BLOCKED | Structural differential now requires collected runtime/problem/artifact evidence; no authorized alternate runtime or model download exists. |
| Portable Skill distribution | PROVEN | PROVEN (external-CWD smoke) | PROVEN | NOT_APPLICABLE | NOT_APPLICABLE | L1 `STRUCTURALLY_VALIDATED` | READY_WITH_RISKS | Package integrity and portability are covered separately from production semantics. |

## Interpretation

- The software/Skill surface is `READY_WITH_RISKS` inside the proven local H3 T2V and offline-contract scope.
- The overall Triple-AAA production claim is `PARTIAL`, not `TRIPLE_AAA_PROVEN`, because the required P1–P6 production rows are not closed.
- The exact source hashes, runtime snapshot, queue safety statement, and release binding are in [`triple-aaa-final-evidence-closure-r9.md`](triple-aaa-final-evidence-closure-r9.md) and [`triple-aaa-quality-bar-r9.json`](triple-aaa-quality-bar-r9.json).
- Queue discovery is a hash-bound point-in-time observation only; it does not reserve capacity or authorize queue mutation.
