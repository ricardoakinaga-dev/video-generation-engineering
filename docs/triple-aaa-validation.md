# Triple-AAA production validation

Status: `CLOSED_WITH_RISKS_R1`

This document is the normative implementation companion for [`triple-aaa-quality-bar-r1.json`](triple-aaa-quality-bar-r1.json). It closes the gap between a valid canonical plan and a claim about generated audiovisual media. The implementation is deliberately conservative: an unobserved property remains unobserved.

## 1. Baseline audit

The pre-closure package already had a coherent canonical planning core, model-independent Scene Bible/shot/state contracts, ComfyUI submission safeguards, immutable attempt/artifact hashing, byte-level assembly and 102 passing software tests. The local runtime was observed at `127.0.0.1:8188` with ComfyUI `0.34.0`, H3 assets and a confirmed 5.1667-second H3 T2V/native-audio profile.

The audit found that the older checked-in H3 bundle is historical evidence, not current production acceptance: it lacks a complete shot contract hash, uses a plural media kind for an MP4, and does not carry semantic or transition acceptance. The old 15-second action material is also text-to-video despite a reference-conditioned intent. Those records remain unchanged; the new quality boundary reports them as `PARTIAL`, `NOT_OBSERVED` or `BLOCKED` rather than laundering history into PASS.

Primary audit evidence: `verification/h3-final-context.json`, `verification/h3-final-artifacts.json`, `verification/h3-observation.json`, `artifacts/vge_action_20260908/plan-rev2.json`, and the Hegel read-only audit packet. Historical `.gauntlet/` evidence is not reused as the current verdict.

## 2. Ownership and dependency direction

```text
vge.py                      (JSON CLI composition only)
  ├── vge_core.py           (canonical plan/state owner)
  ├── vge_quality.py ──────► vge_core.py
  ├── vge_evidence.py ─────► vge_core.py
  ├── vge_media.py ────────► vge_core.py, vge_evidence.py, vge_quality.py
  ├── vge_runtime.py ──────► vge_core.py, vge_evidence.py, vge_quality.py
  └── vge_provider.py ─────► vge_core.py, vge_runtime.py
```

`vge_core.py` owns authored and derived plan truth. `vge_quality.py` never mutates a plan and never reads a provider. `vge_media.py` does not decide identity or story. `vge_runtime.py` may bind a workflow and collect bytes but cannot mark semantic quality accepted. The CLI exposes these owners without becoming a second contract implementation.

The package remains standard-library-only. Production evidence, model files, local absolute paths and control-plane records remain outside the installable package payload.

## 3. Evidence contract

Every executed quality observation carries:

| Field | Rule |
|---|---|
| `artifact_id`, `artifact_ref`, `observed_content_hash` | exact collected artifact identity and bytes |
| `shot_id` and, where relevant, canonical revision | binds evidence to the planned shot |
| `category` | one of metadata, visual, temporal, audio, continuity, editorial |
| `oracle` | explicit question and oracle kind (`METADATA`, `FRAME`, `SEQUENCE`, `AUDIO`, `HUMAN`, `ALGORITHMIC`, `RUNTIME`, `DOCUMENT`) |
| `evidence` | non-empty exact frame/audio/report reference for PASS/FAIL/PARTIAL |
| `confidence` | HIGH/MEDIUM/LOW/UNKNOWN; PASS cannot use UNKNOWN |
| `limitations` | what the procedure cannot establish |

The accepted status set is `PASS`, `FAIL`, `PARTIAL`, `NOT_APPLICABLE`, `NOT_OBSERVED`, `NOT_RUN`, `UNKNOWN` and `BLOCKED`. Aggregation is monotonic toward risk: FAIL beats BLOCKED, which beats PARTIAL; PASS is impossible when required evidence is missing.

Specialized observed PASS contracts (contact, dialogue, audio timeline, first/last frame, re-anchor and completed repair) additionally require a `provenance` envelope. It must resolve existing bytes for a successful immutable attempt, the exact shot contract and a generated artifact record/media pair; the record must cross-bind attempt ID, shot ID, contract hash, artifact ID, locator and media hash. A valid hash string or an arbitrary existing file is not sufficient.

## 4. Shot and transition acceptance

A shot contract contains its canonical shot ID/revision and required acceptance questions. Its generation acceptance is bound to one immutable execution attempt and one artifact hash. Editorial acceptance is a separate human or qualified semantic decision.

An adjacent transition contains:

1. the previous shot/artifact binding;
2. the next shot/artifact binding;
3. the exact required state properties;
4. previous end state and next start state, equal for every required property;
5. a complete continuity scorecard for the next artifact;
6. actual bytes for both adjacent artifacts;
7. any known drift, repair owner and evidence references.

The smallest affected repair scope is the earliest changed shot and its descendants in the canonical DAG. Unaffected siblings are preserved and do not inherit stale acceptance.

## 5. Continuity scorecard

The following dimensions are independent obligations, not one aesthetic score:

| Dimension | Minimum oracle | Typical evidence |
|---|---|---|
| identity | FRAME/HUMAN | reference/shot boundary frames |
| wardrobe | FRAME/HUMAN | boundary frame pair |
| hair | FRAME/HUMAN | boundary frame pair |
| object state/ownership | FRAME/SEQUENCE | contact/result frames and ledger |
| vehicle | FRAME/SEQUENCE | vehicle geometry/state frames |
| environment | FRAME/HUMAN | establishing/boundary frames |
| lighting | FRAME/SEQUENCE | exposure/colour boundary samples |
| screen direction | SEQUENCE/HUMAN | motion path and axis notes |
| camera geography | SEQUENCE/HUMAN | frame pair plus blocking map |
| gaze | FRAME/SEQUENCE/HUMAN | face/gaze samples |
| emotional | HUMAN/SEQUENCE | performance review notes |
| dialogue | AUDIO/SEQUENCE/HUMAN | line timing, listener reaction, transcript |
| temporal | SEQUENCE/ALGORITHMIC | timestamps, freeze/decode report |
| audio | AUDIO/ALGORITHMIC/HUMAN | waveform/listening event evidence |

Each record is `PASS`, `FAIL`, `PARTIAL`, `NOT_APPLICABLE` or `NOT_OBSERVED`. A contact sheet is a navigation aid, never the sole evidence for a temporal, semantic, physics or lip-sync PASS.

## 6. Re-anchor and repair decisions

`reanchor_decision()` emits one of:

- `CONTINUE`: required dimensions observed and accepted;
- `RE_ANCHOR`: persistent identity/world state needs canonical reference/state conditioning;
- `RESET`: observed state contradicts the canonical handoff;
- `REGENERATE`: a localized camera, dialogue, audio or performance issue is repairable;
- `SPLIT`: the feature is unavailable or drift spans too many causal dimensions.

The decision records reasons, evidence references, confidence, limitations, selected repair owner and changed shot set. Prompt wording alone cannot trigger a decision.

Repair plans require nonnegative limits for regenerations, attempts, runtime, cost and human-review escalation. A repair plan is `AWAITING_AUTHORIZATION` unless explicit authorization is present. It cannot target preserved siblings, silently weaken hard constraints or exceed its frozen budget. A `COMPLETE` execution ledger is accepted only with measured usage, completion evidence and the same successful-attempt/shot/artifact provenance envelope; declarations without a ledger remain partial.

## 7. Physical interaction and first/last frame

Contact contracts must enumerate, in order: `APPROACH`, `PRE_CONTACT`, `CONTACT`, `FORCE_ARTICULATION`, `TRANSFER_MOTION`, `RELEASE`, `RESULT`. Each phase has an interval, an observable assertion and a causal source. A declaration-only contact is `PARTIAL`; `PASS` requires a hash-bound artifact, oracle and evidence for every phase. Physics is a QA assertion; “the prompt says it” is not evidence.

First/last-frame capability is scoped to a profile, workflow fingerprint and exact first/last input hashes. A confirmed probe must bind the delivered artifact to an existing byte hash and observe endpoint identity, motion path, object state and delivery through FRAME or SEQUENCE evidence whose references also carry exact hashes. Node metadata alone cannot activate the capability. Unsupported or unknown capability records cannot carry PASS checks.

## 8. Dialogue, performance and audio

Each dialogue line retains speaker, listener, text, intention, delivery, emotion, gaze, timing, pause and overlap policy. An observed dialogue contract binds to an existing artifact hash, and every observed channel carries hash-bound evidence. Its channels remain separate:

1. semantic meaning;
2. voice/source;
3. actor performance;
4. lip-sync;
5. mix.

Visible speech cannot mark lip-sync not applicable. Audio has its own timeline with dialogue, ambience, effects, music, silence and transition layers. Each event has start/end, source, cause, oracle and hash-bound evidence, while the explicit timeline binds an observed artifact and timestamp. The validator requires every canonical layer to be present or explicitly listed as `not_applicable`; an unscoped list is always `PARTIAL`. Audio stream presence proves only that a stream exists; it does not prove intelligibility, event causality or lip-sync.

## 9. Model profiles and adapters

Capability profiles are feature-scoped. A confirmed H3 T2V/native-audio observation does not imply R2V, I2V, FLF, reference conditioning, dialogue/lip-sync or camera-control support. `profile_fingerprint()` includes model/runtime/node/workflow/dependency/limit identity and is persisted/checked for confirmed profiles. Confirmed feature sources and probes must be existing files with declared hashes, and must be bound through `evidence_refs`. Re-probe triggers include runtime version, node inventory, workflow graph, model asset, resource context, runtime commit/dirty state, custom-node commits and observed behavioral changes.

Prompt adaptation is loss-explicit. Density and lexical contradiction checks run before compression. Every adapter mapping is `PRESERVED` or `UNSUPPORTED`/`DEGRADED`; truncation without a declared omission or split is rejected. The adapter differential compares multiple adapters against the same canonical sections.

## 10. ComfyUI and provenance

Discovery records runtime version, full node inventory hash, observed resource inventory and node type inventory. Workflow validation checks API graph schema, links, output node and dynamic selections. `workflow_fingerprint()` additionally binds topology, node versions and generation-critical inputs. Submission is explicit and single-shot; the selected device must resolve to the observed inventory; uncertain outcomes reconcile the same queue ID. New attempts carry a full profile snapshot/content hash and a workflow content/fingerprint binding. Collection normalizes runtime output kinds (`images` → `image`, `videos` → `video`, etc.) and carries shot contract hash, workflow hash/fingerprint, profile revision, model hash, input hashes and artifact hash.

Discovery or preflight never becomes a production PASS. Local runtime evidence is valid only for the exact endpoint, model assets, workflow and timestamp observed.

## 11. Mechanical media QA and semantic QA

`media-qa` runs SHA-256, ffprobe, bounded decode, audio/video duration comparison, black detection and freeze detection. It can report corruption or mechanical anomalies. It cannot prove identity, emotion, contact, physics, story, camera geography, dialogue, editorial quality or lip-sync.

Semantic QA must name an oracle and retain frame/audio/sequence/human evidence against exact bytes. If no suitable oracle was run, use `NOT_OBSERVED` or `NOT_RUN`. A final assembly can be mechanically valid while editorial acceptance remains `NOT_RUN`.

## 12. Long-form ladder and maturity

| Case | Required claim |
|---|---|
| LF-001, 10–15s | one physical interaction, start/end state and complete contact evidence |
| LF-002, 20–30s | dialogue plus interaction, five dialogue channels and audio timeline |
| LF-003, 45–60s | dependent multi-shot production, continuity, transitions, repair budget and human checkpoint |
| LF-004, 90–120s | optional branches, recovery checkpoints, provenance manifest and editorial review |

The maturity model is conservative: Level 0 intent only; Level 1 structural plan; Level 2 deterministic verification; Level 3 runtime provenance; Level 4 audiovisual evaluation; Level 5 repeatable bounded production with an independent critic. The current closure may reach different levels for different scopes; one local 5-second inference cannot certify Level 5.

## 13. Evaluation matrix

| Family | Good case | Bad/metamorphic case | Gate |
|---|---|---|---|
| continuity | all 14 dimensions observed | remove one dimension; mutate boundary state | CONTRACTS |
| transition | equal state and accepted scorecard | state mismatch; forged artifact hash | CONTRACTS |
| FLF | four endpoint checks with frame evidence | metadata-only PASS | CONTRACTS |
| dialogue/audio | separate channels and causal layers | visible speech with N/A lip-sync; negative time | CONTRACTS |
| contact | seven ordered phases | overlap, reorder or missing result | CONTRACTS |
| repair | descendants changed, siblings preserved | budget overflow or preserved target | CONTRACTS |
| prompt/adapter | canonical sections preserved | contradiction or silent omission | VERIFICATION |
| media | decodable aligned fixture | corrupt/black/frozen fixture | MEDIA |
| runtime | exact workflow/profile fingerprint | changed node/model/resource | RUNTIME |
| portability | external-CWD CLI/package | missing link, absolute internal dependency | DISTRIBUTION |
| metamorphic/property-like | permutation-independent IDs and repeated hashes | duplicate dimensions, changed source hash | VERIFICATION |

## 14. Safety and release rule

No external transfer, paid provider, voice clone, likeness-sensitive reference or publication is authorized by this document. Rights, consent, disclosure and human review remain mandatory when those scopes are introduced. Local absolute paths are evidence metadata, not portable package dependencies.

The final report must state architecture, verification and production scores independently. `TRIPLE_AAA_CANDIDATE` is permitted only when all three are PASS, the exact evidence is available, distribution is portable and a fresh independent critic accepts the frozen bar. Otherwise use `READY_WITH_RISKS`, `PARTIAL` or `BLOCKED` with explicit deductions.
