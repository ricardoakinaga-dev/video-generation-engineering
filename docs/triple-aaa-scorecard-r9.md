# Triple-AAA Scorecard R9

Scores are diagnostic, claim-scoped indicators, not an average-based release gate. A high structural score cannot offset a required production blocker. The score is out of 100 and is paired with the strongest evidence status and its limitation.

| # | Category | Score | Evidence | Limitation / effect on verdict |
|---:|---|---:|---|---|
| 1 | Architecture cohesion | 90 | Ownership remains split across canonical core, quality, runtime, media, evidence, provider and CLI modules. | Mature structural boundary; no claim about generated footage. |
| 2 | Canonical truth and contradiction control | 92 | Canonical state is required, non-empty, hash-bound and checked for state, door, motion and ownership contradictions. | Vocabulary remains a deterministic contract, not a visual truth oracle. |
| 3 | Evidence provenance and lineage | 90 | Attempts, artifacts, observations, hashes, shot IDs and successful runtime provenance are bound in long-form validation. | Existing historical records still expose incomplete production chains. |
| 4 | Semantic QA discipline | 86 | Twelve dimensions, exact artifact bytes, derived evidence lineage and limitations are required. | The validator cannot see pixels or hear audio; human/oracle execution remains external. |
| 5 | Claim-specific oracle discipline | 88 | FLF, contact, dialogue/audio and semantic dimensions now require appropriate oracle families. | Oracle results still require real independent observation. |
| 6 | Prompt compiler and density | 88 | No silent truncation; preserve/unsupported classification and compression boundary are explicit. | Prompt compilation does not guarantee model behavior. |
| 7 | Adapter differential | 82 | Canonical-state hash and explicit semantic-preservation mapping proof are required. | Only one real runtime is currently evidenced; alternate adapter remains blocked. |
| 8 | Risk-scoped negative constraints | 86 | Vehicle, dialogue, audio and portrait risk families are selected explicitly and omissions are visible. | No A/B generation evidence proves model response to negatives. |
| 9 | Continuity state and shot graph | 90 | Scene Bible, Shot Graph, state deltas and dependency structures are represented and tested. | Observed multi-shot identity remains partial. |
| 10 | Transition verification | 88 | Adjacent transitions bind states, scorecards, semantic observations and distinct media hashes. | LF-001 T01 is partial and T02 fails. |
| 11 | Repairability and re-anchor | 75 | Smallest-owner routing, repair scope and hash-bound revalidation references are enforced. | No real repaired attempt and improvement proof were authorized. |
| 12 | Runtime authorization guards | 90 | POST boundaries require explicit authorization, workflow binding, profile and resource evidence; non-PASS quality exits nonzero. | Guards prevent unsafe execution; they do not create capability. |
| 13 | Resource and side-effect safety | 92 | Current read-only ComfyUI snapshot; no POST, cancellation, download, upload or queue mutation. | Runtime availability is not production acceptance. |
| 14 | H3 T2V runtime | 90 | Local ComfyUI 0.34.0, validated bundled workflow, H3 history and device/resource observations. | Scope is local H3 T2V; semantic and editorial claims remain separate. |
| 15 | H3 R2V/I2V semantic capability | 55 | Local inventory/workflow and historical artifacts exist. | Reference retention/identity/continuity are not closed. |
| 16 | FLF modes | 25 | Validator and schema coverage exist. | `FIRST_ONLY`, `LAST_ONLY`, and `FIRST_AND_LAST` are `NOT_RUN`. |
| 17 | Dialogue, audio and lip-sync | 30 | Separate contracts cover semantics, voice, performance, sync, foley, ambience and mix. | No real voice/audio/lip-sync artifact or listening review. |
| 18 | LF-001 vehicle-entry production | 35 | S01/S02 artifacts and mechanical checks exist; S03 and transition records remain bound. | S03 drift, T02 failure, preview-only assembly and no editorial acceptance. |
| 19 | LF-003 45–60 s production | 20 | Ten-shot structural ladder exists. | No accepted dependent-shot production chain, repair or editorial review. |
| 20 | Editorial and human acceptance | 35 | Editorial contract is separate and dimension-complete. | Current assembly is preview-only; human review is not observed. |
| 21 | Portability, security and distribution | 92 | Deterministic Skill archive, CRC/SHA, path/secret/media/weight scans, compile and external-CWD smoke. | Archive is structural; it does not prove audiovisual quality. |
| 22 | Independent review and mutation control | 90 | Final fresh non-inherited reviewer Dirac independently matched 464/464 files, the corrected candidate scope hash and the `.gauntlet/bar.json` sentinel in a timestamped read-only window. | The reviewer confirms the structural candidate but rejects production promotion; review quality cannot substitute for missing audiovisual evidence. |

## Score interpretation

The software candidate is `READY_WITH_RISKS` for the scoped structural/local-runtime capability. The overall release remains `PARTIAL` until LF-001, repair, FLF, LF-002, LF-003, the second adapter (or its justified blocked record), and the production gates satisfy the frozen bar. The fresh critic and final distribution accounting are complete; the scorecard intentionally does not average the remaining production blockers away.
