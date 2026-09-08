# Capability matrix — Triple-AAA R2

Observed scope: local ComfyUI at `127.0.0.1:8188`, runtime `0.34.0`, exact H3 assets/workflows and the dated evidence in `verification/`. A status is scoped to that profile; it is not a universal model claim. `PASS` in Structural means the contract exists and rejects malformed data. `PASS` in Runtime or Artifact means the corresponding evidence was actually executed and hash-bound.

| Capability | Structural | Runtime | Artifact | Long-form | Status |
|---|---|---|---|---|---|
| Scene planning | PASS | NOT_APPLICABLE | NOT_APPLICABLE | PARTIAL | PASS (scoped) |
| Shot graph | PASS | NOT_APPLICABLE | NOT_APPLICABLE | PARTIAL | PASS (scoped) |
| Continuity state/ledger | PASS | PARTIAL | PARTIAL | BLOCKED | PARTIAL |
| Reference retention/re-anchor | PASS | UNKNOWN | PARTIAL | BLOCKED | PARTIAL |
| Prompt compiler | PASS | NOT_APPLICABLE | NOT_APPLICABLE | PARTIAL | PASS (scoped) |
| H3 T2V | PASS | CONFIRMED | PASS (mechanical) | BLOCKED | PARTIAL |
| H3 R2V/I2V | PASS | PARTIAL | FAIL (semantic) | BLOCKED | PARTIAL |
| First/last frame (FLF) | PASS | UNKNOWN | NOT_OBSERVED | BLOCKED | BLOCKED |
| Dialogue planning | PASS | NOT_APPLICABLE | NOT_OBSERVED | BLOCKED | PARTIAL |
| Voice generation | PASS | UNKNOWN | NOT_OBSERVED | BLOCKED | BLOCKED |
| Lip-sync | PASS | UNKNOWN | NOT_OBSERVED | BLOCKED | BLOCKED |
| Layered audio timeline | PASS | PARTIAL | NOT_OBSERVED | BLOCKED | PARTIAL |
| Vehicle interaction | PASS | UNKNOWN | NOT_OBSERVED | BLOCKED | BLOCKED |
| Artifact observation/semantic QA | PASS | PASS (contract) | PARTIAL | BLOCKED | PARTIAL |
| Transition QA | PASS | NOT_APPLICABLE | PARTIAL | BLOCKED | PARTIAL |
| Targeted repair | PASS | NOT_RUN | NOT_OBSERVED | BLOCKED | PARTIAL |
| Assembly/editorial gate | PASS (mechanical) | PARTIAL | PASS (mechanical) | BLOCKED | PARTIAL |
| LF-001 vehicle entry | PASS (fixture) | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| LF-002 dialogue + interaction | PASS (fixture) | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| LF-003 dependent multi-shot | PASS (fixture) | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| LF-004 extended branches | PASS (fixture) | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN |
| Second independent adapter | PASS (differential contract) | BLOCKED | NOT_OBSERVED | BLOCKED | BLOCKED |

## Exact local runtime evidence

- H3 T2V profile: [`comfyui-h3-local-probed.json`](../.agents/skills/video-generation-engineering/profiles/comfyui-h3-local-probed.json), feature-scoped `text_to_video` and `native_audio_generation` are `CONFIRMED` only for the recorded runtime, model, workflow, device and parameters.
- H3 T2V artifact: [`art_2898879072af4739b673efe71fafcc7e.mp4`](../verification/media/final/art_2898879072af4739b673efe71fafcc7e.mp4), SHA-256 `623f04987e1401623f6bb9e31c6823b23e56694719681d081e7484303538d124`, 384×224, 124 frames, 24 FPS, approximately 5.167 seconds.
- H3 R2V artifact: [`art_c7a1437df976419b98c5f73a41234c2d.mp4`](../verification/h3-r2v-collected-r2/art_c7a1437df976419b98c5f73a41234c2d.mp4), SHA-256 `973c979e1e0c0bc49d9ef30a3b1a4ee10821891d85fe6bcf151dcc92b210e598`; mechanical QA passes, semantic observation fails the declared veterinary identity/environment.
- The confirmed local profile requires exact source/probe, observed-parameter, device, artifact and observation hashes. It does not imply R2V, I2V, FLF, dialogue, voice or lip-sync.

## Decision

The matrix supports planning, contracts, runtime provenance and mechanical media QA. It does not support a Triple-AAA production verdict. The missing rows are intentionally `UNKNOWN`, `BLOCKED`, `NOT_OBSERVED` or `PARTIAL` until an authorized execution produces the required evidence.
