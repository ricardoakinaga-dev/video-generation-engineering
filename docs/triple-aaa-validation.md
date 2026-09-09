# Triple-AAA production validation — R3

The current closure authority is [`triple-aaa-quality-bar-r3.json`](triple-aaa-quality-bar-r3.json), with the current matrix, scorecard and report in [`capability-matrix-r3.md`](capability-matrix-r3.md), [`triple-aaa-scorecard-r3.md`](triple-aaa-scorecard-r3.md) and [`triple-aaa-final-production-closure.md`](triple-aaa-final-production-closure.md). The R2 material below is retained as historical implementation context.

Status: `READY_WITH_RISKS`.

This document is the normative implementation companion for the frozen [`triple-aaa-quality-bar-r2.json`](triple-aaa-quality-bar-r2.json). The exact user prompt is preserved in [`master-prompt-triple-aaa-r2.txt`](master-prompt-triple-aaa-r2.txt). Its SHA-256 is `sha256:8759fbd444abb0578fa5d7b852e4ff2ca9d1a0437913b9ace1a233dfbec16e51`. The bar freezes the acceptance contract; it does not manufacture unavailable runtime or semantic evidence.

## 1. Scope and non-claims

The implementation turns intent into canonical scene/state data, shot dependencies, prompt sections, feature-scoped adaptation, ComfyUI execution records, collected artifacts, observations, transitions, repair decisions and assembly gates. It can prove deterministic software and exact local provenance. It cannot infer identity, physics, emotion, dialogue quality, lip-sync or editorial acceptance from a prompt, node list, contact sheet or ffprobe report.

The current release therefore uses `READY_WITH_RISKS`. `TRIPLE_AAA_PROVEN` is reserved for a fresh, production-backed package containing accepted LF-001, LF-002 and LF-003 evidence, multi-shot continuity, targeted repair, semantic/audio review, portable distribution and a fresh independent critic. No such proof is claimed here.

## 2. End-to-end ownership

```text
intent → references → complexity → reference route → Scene Bible → story/time
       → shot graph + continuity state → direction/constraints
       → canonical prompt → feature-scoped adapter → ComfyUI preflight
       → immutable attempt → collected artifact → media QA
       → semantic observation → transition QA → repair/re-anchor
       → assembly → editorial acceptance
```

`vge_core.py` owns authored and derived plan truth. `vge_quality.py` owns immutable quality contracts and never promotes a plan to observed truth. `vge_runtime.py` owns runtime discovery, workflow/device binding and queue reconciliation. `vge_evidence.py` owns attempts, artifacts and acceptance provenance. `vge_media.py` owns mechanical media QA and assembly mechanics. `vge.py` composes these owners; it is not a second domain model.

Progressive disclosure is also derived by `vge_core.py`: `reference_route` includes only the package references justified by canonical scene signals and records exclusions. The route is structural context guidance, not evidence that the host loaded a document.

The truth domains remain separate:

1. desired truth — what the creator wants;
2. planned truth — canonical scene, shot, state, prompt and workflow decisions;
3. observed truth — exact runtime facts, artifact bytes, semantic observations and human/editorial decisions.

Only the third domain can support an artifact-quality claim.

## 3. Evidence contract

An observed quality record carries, at minimum:

- stable `project_id`/`scene_id`/`shot_id` lineage where applicable;
- exact `artifact_id`, locator and SHA-256 content hash;
- timestamp and executed procedure;
- a category-specific oracle (`METADATA`, `FRAME`, `SEQUENCE`, `AUDIO`, `HUMAN`, `ALGORITHMIC`, `RUNTIME` or `DOCUMENT`);
- evidence references with exact hashes for `PASS`, `FAIL` or `PARTIAL` checks;
- confidence and limitations;
- the immutable attempt, shot-contract and generated-artifact provenance envelope for observed PASS contracts.

`NOT_OBSERVED`, `UNKNOWN`, `NOT_RUN` and `BLOCKED` are meaningful results. A locator without bytes, a declared hash without a matching file, a prompt, or runtime node presence is not acceptance evidence. Overwriting a referenced path invalidates the affected record.

## 4. Canonical contracts implemented

### Scene, shot, state and acceptance

The canonical plan retains Scene Bible entities, reference roles, locks, state deltas, causal beats, shot dependencies, camera geography, acceptance IDs and a repair owner. `START_STATE → ACTION → END_STATE` is required for material transitions. `validate_shot_acceptance()` now fails closed when an observation does not contain a result for every required acceptance check.

Adjacent transition acceptance requires different shot IDs, different artifact IDs, distinct artifact locator/hash pairs, equal declared boundary state, a complete continuity scorecard, an explicit hash-bound side-by-side comparison across all continuity dimensions and PASS observations for both artifacts. A generated boundary frame, state equality or a next-shot scorecard is not accepted merely because it is named as the next input; an absent comparison leaves the transition `PARTIAL` or `FAIL`.

### Continuity and semantic observation

The 14 independent continuity dimensions are `identity`, `wardrobe`, `hair`, `object_state_ownership`, `vehicle`, `environment`, `lighting`, `screen_direction`, `camera_geography`, `gaze`, `emotional`, `dialogue`, `temporal` and `audio`. Each dimension has its own oracle/result/evidence. Mixed PASS and unobserved dimensions aggregate to `PARTIAL`; a prompt cannot substitute for evidence.

Semantic artifact observations additionally require twelve explicit records: `identity`, `wardrobe`, `object_retention`, `environment`, `lighting`, `physics`, `interaction`, `camera`, `performance`, `dialogue`, `lip_sync` and `temporal_continuity`. Every record carries its own status, confidence, oracle, hash-bound evidence and limitations; missing or duplicate dimensions cannot pass.

### Physical interaction

The canonical contact sequence is:

`APPROACH → PRE_CONTACT → CONTACT → FORCE_OR_ARTICULATION → TRANSFER_OR_MOTION → RELEASE → RESULT`.

Each phase has timing, a visible assertion and, for observed status, an oracle and hash-bound evidence. `validate_contact_phases()` accepts the planning aliases `subject`/`target`/`effector`/`interaction_cause`/`success_criterion` and normalizes them to `actor`/`receiver`/`object_id`/`cause`/`expected_result`. Physics remains a QA assertion; prompt text is never proof.

`validate_object_ownership()` requires explicit contact/shared contact and release for a change of owner. `validate_vehicle_state()` rejects a moving vehicle with an inactive engine, an open door or absent road contact, and requires a cause for declared state changes.

### Dialogue, causality and audio

Dialogue keeps semantics, voice, performance, lip-sync and mix as five independent channels. It retains speaker, listener, line aliases, intent, delivery, emotion, gaze, timing, pauses, reaction delay, voice reference and sync mode. Sustained listener mouthing is rejected unless explicitly scripted. Visible speech cannot use `NOT_APPLICABLE` for voice or lip-sync.

The causal sequence is explicit: `STIMULUS → PROCESSING → REACTION → RESPONSE`. The validator rejects missing stages, duplicate stages, backwards ordering and unmarked overlaps. Dialogue contracts may bind an explicit `speaker_sequence`; a mismatch is rejected as a speaker swap, while sustained listener mouthing remains forbidden unless scripted.

The canonical audio layers are `dialogue`, `foley`, `ambience`, `room_tone`, `vehicle`, `animal`, `music`, `transition`, `non_diegetic` and `silence`. Every scoped timeline accounts for each layer as required or `not_applicable`; each event has timing, source, cause, priority, mix role, oracle and evidence. The planning alias `effects` maps to `foley`. A present audio stream proves only stream presence, not intelligibility, causality, mix quality or lip-sync.

### Profiles, adapters and ComfyUI

Capability evidence is feature-scoped. Confirmed feature entries require observed parameters, selected device, artifact and semantic-observation references with exact hashes, in addition to source/probe records, runtime/node/model/workflow identity and profile provenance. Runtime, node inventory, model, workflow, device, resource, commit, dirty-state, custom-node or behavioral changes trigger re-probing.

The prompt compiler preserves ten canonical sections and exposes omissions, contradictions and adapter loss. `adapter_differential()` compares adapters against the same canonical source; it is structural evidence only until each adapter has a real runtime/artifact probe.

ComfyUI execution records bind the inspected graph, model, profile, device, parameters, queue ID, attempt, output and artifact bytes. Uncertain submission is reconciled by the same queue ID. Preflight and discovery do not become generation or semantic PASS. The live local preflight is recorded in [`verification/comfyui-preflight-r2.json`](../verification/comfyui-preflight-r2.json); both bundled H3 API workflows pass the current node catalog after the `SaveVideo` dynamic-combo contract was corrected.

### Long-form, repair and assembly

`validate_long_form_case()` accepts a production `PASS` only when every logical reference resolves, every attempt is `SUCCEEDED`, every artifact/observation/transition record is accepted and hash-bound, and the assembly record has separate technical, semantic and editorial acceptance plus final-artifact binding to every ordered source shot hash. Placeholder references plus `production_evidence_complete=true` are rejected. Structural fixtures are intentionally separate from production evidence.

Repair is bounded by regenerations, attempts, runtime, cost and human-review budgets. It preserves immutable failed attempts and unaffected siblings, then requires re-observation and downstream transition revalidation before a completed repair can pass. Re-anchor decisions also reject an unbounded generated-frame chain and route back to a canonical reference. Vehicle state can carry a geometry identity, but a geometry change requires an explicit reviewed transition. Mechanical media QA emits separate checks for readability, duration, FPS, resolution, frame count, codec, container, audio stream/duration, A/V mismatch, decode, black/freeze and SHA-256. Strict assembly validates shot order, duplicate/missing shots, transition timing, lineage and final-artifact binding; editorial acceptance remains a separate human gate with pacing, acting, camera, emotion, framing and rhythm dimensions.

## 5. Independent gates and maturity

| Gate | Current result | Boundary |
|---|---|---|
| Architecture | `PASS (scoped)` | Ownership, canonical state, routing, safety and traceability are implemented. |
| Verification | `PASS (scoped)` | 134 deterministic tests, compile/skill/docs checks, package verification and known-bad regressions. |
| Production | `PARTIAL/BLOCKED` | Local H3 artifacts have exact provenance and mechanical QA; required LF cases, semantic dialogue/lip-sync and second adapter remain unaccepted. |

Maturity is conservative: Level 0 intent, Level 1 structural plan, Level 2 deterministic verification, Level 3 runtime provenance, Level 4 audiovisual evaluation and Level 5 repeatable bounded production with a fresh critic. Current global maturity is Level 3 with bounded audiovisual observations; Level 5 is not claimed.

## 6. Evaluation families

The executable regression suite covers canonical contracts, malformed inputs, state/graph mutations, progressive-disclosure route drift, metamorphic scene invariants, contact/audio/dialogue known-bad cases, twelve-dimension semantic observations, placeholder LF PASS rejection, profile evidence, transition identity, strict assembly lineage, editorial acceptance, repair budgets and transition revalidation, adapter omission, runtime fakes, provenance mismatch, granular media checks, corruption/black/freeze and external-CWD operation. Real production evaluation remains separately marked in [`long-form-validation.md`](long-form-validation.md), [`capability-matrix-r1.md`](capability-matrix-r1.md) and the [final closure report](triple-aaa-final-report.md).

## 7. Safety and release rule

No paid call, upload, voice clone, likeness transfer, publication or model-weight download is authorized by this closure. Credentials remain outside artifacts. Rights, consent and human review are mandatory before sensitive or external actions. A lower-level plan may not override the frozen bar or promote an unavailable feature.

The final evidence package is [`triple-aaa-final-report.md`](triple-aaa-final-report.md), with the exact matrix in [`capability-matrix-r1.md`](capability-matrix-r1.md), scores in [`triple-aaa-scorecard.md`](triple-aaa-scorecard.md), long-form envelopes in [`../verification/long-form/`](../verification/long-form/) and the preserved source prompt in [`master-prompt-triple-aaa-r2.txt`](master-prompt-triple-aaa-r2.txt).
