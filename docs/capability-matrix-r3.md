# Capability matrix — Triple-AAA R3

This is the current scoped matrix for the repository candidate. `PASS` means the contract or evidence for that column passed; it is not a universal model claim. Runtime observations are bounded to the local ComfyUI profile, exact workflow, selected device and dated artifacts. `NOT_OBSERVED`, `NOT_RUN`, `UNKNOWN` and `BLOCKED` are not production PASS.

| Capability | Structural | Runtime | Artifact | Multi-shot | Production | Status |
|---|---|---|---|---|---|---|
| Scene planning | PASS | NOT_APPLICABLE | NOT_APPLICABLE | PASS (contract) | NOT_APPLICABLE | PASS (scoped) |
| Scene Bible | PASS | NOT_APPLICABLE | NOT_APPLICABLE | PASS (fixture) | NOT_OBSERVED | PASS (scoped) |
| Shot graph | PASS | NOT_APPLICABLE | NOT_APPLICABLE | PASS (contract) | NOT_OBSERVED | PASS (scoped) |
| Continuity ledger | PASS | PARTIAL | PARTIAL | BLOCKED | BLOCKED | PARTIAL |
| Reference retention | PASS | UNKNOWN | PARTIAL | BLOCKED | BLOCKED | PARTIAL |
| Prompt compiler | PASS | NOT_APPLICABLE | NOT_APPLICABLE | PASS (differential contract) | NOT_APPLICABLE | PASS (scoped) |
| H3 T2V | PASS | CONFIRMED (dated local scope) | PASS (mechanical) | BLOCKED | BLOCKED | PARTIAL |
| H3 R2V/I2V | PASS | PARTIAL | FAIL (semantic) | BLOCKED | BLOCKED | PARTIAL |
| First/last frame | PASS (contract) | UNKNOWN | NOT_OBSERVED | BLOCKED | BLOCKED | BLOCKED |
| Dialogue planning | PASS | NOT_APPLICABLE | NOT_OBSERVED | BLOCKED | BLOCKED | PARTIAL |
| Voice generation | PASS (contract) | UNKNOWN | NOT_OBSERVED | BLOCKED | BLOCKED | BLOCKED |
| Lip-sync | PASS (contract) | UNKNOWN | NOT_OBSERVED | BLOCKED | BLOCKED | BLOCKED |
| Layered audio | PASS | PARTIAL | NOT_OBSERVED | BLOCKED | BLOCKED | PARTIAL |
| Interaction/vehicle entry | PASS (fixture) | BLOCKED by resource floor | NOT_OBSERVED | BLOCKED | BLOCKED | BLOCKED |
| Semantic QA | PASS (contract) | NOT_APPLICABLE | PARTIAL | BLOCKED | BLOCKED | PARTIAL |
| Transition QA | PASS (contract) | NOT_APPLICABLE | PARTIAL | BLOCKED | BLOCKED | PARTIAL |
| Targeted repair/re-anchor | PASS (contract) | NOT_RUN | NOT_OBSERVED | BLOCKED | BLOCKED | PARTIAL |
| Assembly | PASS (strict contract) | NOT_APPLICABLE | PASS (fixture/mechanical) | BLOCKED | BLOCKED | PARTIAL |
| Editorial acceptance | PASS (human contract) | NOT_APPLICABLE | NOT_OBSERVED | BLOCKED | BLOCKED | BLOCKED |
| LF-001 vehicle entry | PASS (fixture) | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| LF-002 dialogue + interaction | PASS (fixture) | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| LF-003 dependent long form | PASS (fixture) | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| LF-004 extended branches | PASS (fixture) | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN |
| Second real adapter | PASS (differential contract) | BLOCKED | NOT_OBSERVED | BLOCKED | BLOCKED | BLOCKED |

## Evidence basis

- The local H3 T2V artifact is [`art_2898879072af4739b673efe71fafcc7e.mp4`](../verification/media/final/art_2898879072af4739b673efe71fafcc7e.mp4), SHA-256 `623f04987e1401623f6bb9e31c6823b23e56694719681d081e7484303538d124`, 384×224, 124 frames, 24 FPS and approximately 5.167 seconds.
- The local H3 R2V artifact has mechanical evidence but its declared veterinary identity/environment observation is semantic `FAIL`; it does not promote R2V/I2V.
- LF-001 A003 produced only S01 (approach/pre-contact) with mechanical `PASS` and semantic/continuity `PARTIAL`; S02/S03, complete contact chain, transition acceptance, repair and editorial acceptance are absent.
- The current resource snapshot is below the effective scheduling floor for the configured local workflow. The guard blocks before queue POST and does not cancel unrelated jobs.

## Decision

The matrix supports the Skill's planning, contracts, provenance and bounded local workflow. It does not support `TRIPLE_AAA_PROVEN` or `TRIPLE_AAA_CANDIDATE`; full production claims remain blocked until real LF-001, LF-002 and LF-003 evidence exists.
