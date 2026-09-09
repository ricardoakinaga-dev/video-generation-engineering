# ComfyUI execution boundary

This document defines how an execution plan may target ComfyUI while keeping planning, runtime discovery, queueing, and artifact validation separate.

## Contents

- [Execution modes](#1-execution-modes)
- [Runtime discovery](#2-runtime-discovery)
- [Workflow representation](#3-workflow-representation)
- [Preflight-to-artifact flow](#4-preflight-to-artifact-flow)
- [Local and Cloud boundaries](#5-local-and-cloud-boundaries)
- [Resource and frame validation](#6-resource-and-frame-validation)
- [Optional downstream stages](#7-optional-downstream-stages)
- [Artifact collection and provenance](#8-artifact-collection-and-provenance)
- [Failure modes and repair routes](#9-failure-modes-and-repair-routes)
- [Open questions and related documents](#10-open-questions-and-related-documents)

## 1. Execution modes

| Mode | Behavior | Default |
|---|---|---|
| `PLAN_ONLY` | Emit a validated workflow plan and required inputs; do not contact a runtime | Yes |
| `LOCAL_DRY_RUN` | Validate graph shape, node types, bindings, and available metadata when a local server is present; do not queue generation | Opt-in |
| `LOCAL_EXECUTE` | Submit to a local ComfyUI server and collect artifacts | Explicit opt-in |
| `CLOUD_EXECUTE` | Submit an API-format workflow to ComfyUI Cloud or another approved endpoint | Explicit opt-in, authenticated |

The blueprint's default behavior is plan-first. An execution request must include the selected mode, target, user authorization, and artifact destination.

## 2. Runtime discovery

When a runtime is available, preflight records the observed environment before binding a workflow:

```text
/features       feature flags and server capabilities
/system_stats   runtime and device information
/object_info    installed node metadata and input schemas
/models         available model files when exposed by the runtime
/history        prior prompt/artifact records when needed for recovery
/ws             progress and execution events when supported
```

The route set is a discovery aid, not a guarantee that every deployment exposes every route. The execution plan records endpoint availability, ComfyUI version if known, node inventory hash, device profile, and timestamp.

## 3. Workflow representation

The canonical execution artifact is an API-format workflow plus a human-readable plan. The workflow must be treated as data, not as a hard-coded assumption about one node graph.

```yaml
execution_target:
  provider: comfyui
  mode: PLAN_ONLY
  workflow_format: api_json
  workflow_ref: workflows/shot_002_api.json
  required_nodes:
    - LoadImage
    - KSampler
    - VAEDecode
    - CreateVideo
  required_assets:
    - ref_mara_portrait
    - model:Wan2.2
```

The graph builder validates node names, input types, linked outputs, required assets, and profile-specific controls. It never assumes that a node exists merely because a model repository supports a feature.

The current ComfyUI API uses flat dotted keys for nested `COMFY_DYNAMICCOMBO_V3` inputs (for example, `format: mp4` plus `format.codec: auto`); the package validator expands the selected schema before checking required children. The bundled H3 workflows were preflighted against the live local node catalog on 2026-09-08 and are recorded in [`verification/comfyui-preflight-r2.json`](../verification/comfyui-preflight-r2.json). This is graph/runtime-schema evidence only, not inference or media-quality evidence.

## 4. Preflight-to-artifact flow

```text
plan → preflight → prepare inputs → choose graph → bind parameters
     → validate graph → create immutable ExecutionAttempt
     → [optional queue] → observe progress
     → collect artifact → inspect metadata → run QA → assemble/export
```

Preflight failures are classified as `environment`, `asset`, `capability`, `graph`, or `authorization` failures. A missing model, missing node, incompatible dimensions, or unauthenticated Cloud request produces a repairable plan error rather than a vague generation failure.

## 5. Local and Cloud boundaries

Local ComfyUI exposes server routes for queueing, websocket events, history, metadata, and system discovery in its documented server API. Cloud execution uses an API-format workflow and asynchronous job behavior, with authentication and deployment-specific limits. These paths share the canonical plan but have different credentials, retries, and artifact retrieval behavior.

The adapter must preserve:

- endpoint and provider;
- workflow JSON hash or reference;
- prompt/queue identifier when returned;
- model and node versions;
- input asset hashes;
- parameter bindings and seed;
- progress/error events;
- output artifact hashes and media metadata.

The execution-context values above are persisted in the immutable [`ExecutionAttempt`](contracts.md#execution-attempt-contract-executionattempt) record created for each submission; output hashes and media metadata are owned by the linked `GenerationArtifact`. A retry gets a new attempt ID even when it targets the same shot or output locator; the collected artifact points back to that attempt rather than relying on the filename.

## 6. Resource and frame validation

Before execution, validate the relationship among duration, FPS, frame count, resolution, memory profile, and the selected workflow. Duration is not the only routing factor; frame count and interaction/continuity risk may force a split even when duration is short.

The plan must expose estimated cost and risk where the runtime can provide them, and must include a bounded fallback: lower resolution, shorter segment, lower batch size, alternate profile, or human review. A fallback that changes story, identity, or synchronization must be marked as a material change. For `LOCAL_EXECUTE`, `resource_budget` must bind the exact device and a minimum free-VRAM threshold (plus any safety margin) to a profile/probe or an operator decision. The executor takes a fresh snapshot and blocks before queueing when the selected device is unknown or below that threshold; a pass remains a scheduling guard, not an inference guarantee.

## 7. Optional downstream stages

The execution plan may include downstream stages, but each is a separate capability and artifact boundary:

| Stage | Input | Output | Activation rule |
|---|---|---|---|
| interpolation/frame-rate conversion | validated frames/video | revised frame sequence | only when motion/temporal quality risk is acceptable |
| upscale | validated video | higher-resolution video | only when the upscale path is available and does not hide source defects |
| audio generation | script/voice/event plan | audio track | only with a confirmed audio profile or approved external path |
| lip-sync | face-visible video + approved audio | synchronized video | only with a confirmed/validated adapter and human/media QA |
| assembly/mux | video segments + audio layers | delivery container | always explicit for multi-shot output; verify duration/FPS/alignment |
| provenance/disclosure | accepted artifacts + metadata | manifest/labelled delivery | required when project policy, provider, or rights workflow demands it |

Interpolation and upscale are not automatic quality fixes. The plan records their rationale, expected risk, profile/tool evidence, and post-stage acceptance checks.

## 8. Artifact collection and provenance

Collection first creates a `GenerationArtifact`, which records that the runtime produced media and preserves its provenance. It is not an `ArtifactObservation` and it does not contain a QA result:

```yaml
generation_artifact:
  schema_version: 1
  id: art_shot_002_v01
  shot_id: shot_002
  execution_attempt_ref: attempt_shot_002_001
  artifact_ref: outputs/shot_002_v01.mp4
  content_hash: "sha256:c3b5516bb098506632dbbf60e1d2f989bbfda77d16306af1b4b57a1fca0c1334"
  collected_at: "2026-09-08T08:00:00-03:00"
  generation_status: GENERATED
  media:
    kind: video
    frame_count: observed
    fps: observed
    audio_track: present
  runtime:
    provider: comfyui
    endpoint: local
    workflow_hash: "sha256:8176bcc0dbd3e7abc0910578d5952d7f2df05bfccb54df880b26e6db8d56eb4e"
  quality_review:
    lifecycle: NOT_STARTED
    observation_ref: null
```

The values in the fixtures below are illustrative and are not runtime evidence. If the runtime omits a required provenance value, record `null` and its dotted path in `unknown_fields` on the `ExecutionAttempt`; do not guess. Missing profile/model version, workflow identity, required input hash, or collected output hash blocks QG-17 and artifact acceptance. A missing optional seed or parameter is disclosed and blocks a reproducibility claim.

The following fixture shows two attempts for the same shot. Each attempt carries its own profile/model/node/workflow/input/parameter context; each collected artifact binds to exactly one attempt and each observation binds to exactly one artifact. The repeated output locator is intentional:

```yaml
provenance_case:
  shot_id: shot_002
  execution_attempts:
    - schema_version: 1
      id: attempt_shot_002_001
      execution_plan_ref: exec_scene_001_rev1
      shot_id: shot_002
      attempt_index: 1
      status: SUCCEEDED
      started_at: "2026-09-08T08:00:00-03:00"
      ended_at: "2026-09-08T08:04:00-03:00"
      profile: {id: comfyui-wan22-native-v1, revision: 1}
      model:
        id: Wan2.2-I2V-A14B
        version: "fixture-model-v1"
        asset_hash: "sha256:50b0b6a2bac409650b3d30fe81e88b31ed1dbfb62df402971e0930c169985cb5"
      runtime: {provider: comfyui, endpoint: local, version: "fixture-comfyui-v1", node_inventory_hash: "sha256:f912352348b90a56ef3a080aea27f1022bdcbc85a512739b4e66dcfde76645e0"}
      workflow: {ref: workflows/shot_002_api.json, content_hash: "sha256:8176bcc0dbd3e7abc0910578d5952d7f2df05bfccb54df880b26e6db8d56eb4e", prompt_ref: "scene_001_rev1:shot_002", queue_id: comfy_queue_001}
      nodes:
        - {id: load_image, type: LoadImage, version: "fixture-node-v1"}
        - {id: k_sampler, type: KSampler, version: "fixture-node-v1"}
      inputs:
        - {ref: ref_mara_portrait, role: identity_reference, content_hash: "sha256:73af5d7c92634021c9f26db097c0ecd91b36abefd3e58283b2a9741e4b7c469e"}
        - {ref: "anchor:shot_004:last_frame", role: temporal_anchor, content_hash: "sha256:73af5d7c92634021c9f26db097c0ecd91b36abefd3e58283b2a9741e4b7c469e"}
      parameters: {seed: 18403, bindings: {width: 832, height: 480, frame_count: 81, fps: 16, sampler: euler}}
      progress_ref: "execution-events:attempt_shot_002_001"
      error_ref: null
      unknown_fields: []
    - schema_version: 1
      id: attempt_shot_002_002
      execution_plan_ref: exec_scene_001_rev1
      shot_id: shot_002
      attempt_index: 2
      status: SUCCEEDED
      started_at: "2026-09-08T08:10:00-03:00"
      ended_at: "2026-09-08T08:14:00-03:00"
      profile: {id: comfyui-wan22-native-v1, revision: 1}
      model:
        id: Wan2.2-I2V-A14B
        version: "fixture-model-v2"
        asset_hash: "sha256:8e138df9a025a20526355d65e17cecf02038c6d22e52da5ec88c3b3bdcae2540"
      runtime: {provider: comfyui, endpoint: local, version: "fixture-comfyui-v2", node_inventory_hash: "sha256:f1946da3046d9b5d0d090598354420ce32014584cf4d215f5c73671673bb97e2"}
      workflow: {ref: workflows/shot_002_api.json, content_hash: "sha256:78506c2417b95aa75582ffdbe6a8fdfed0d836a3a48b44455dc1bdcacbea175e", prompt_ref: "scene_001_rev1:shot_002", queue_id: comfy_queue_002}
      nodes:
        - {id: load_image, type: LoadImage, version: "fixture-node-v2"}
        - {id: k_sampler, type: KSampler, version: "fixture-node-v2"}
      inputs:
        - {ref: ref_mara_portrait, role: identity_reference, content_hash: "sha256:73af5d7c92634021c9f26db097c0ecd91b36abefd3e58283b2a9741e4b7c469e"}
      parameters: {seed: 18404, bindings: {width: 832, height: 480, frame_count: 81, fps: 16, sampler: euler}}
      progress_ref: "execution-events:attempt_shot_002_002"
      error_ref: null
      unknown_fields: []
  collected_artifacts:
    - {id: art_shot_002_v01, execution_attempt_ref: attempt_shot_002_001, artifact_ref: outputs/shot_002_v01.mp4, content_hash: "sha256:c3b5516bb098506632dbbf60e1d2f989bbfda77d16306af1b4b57a1fca0c1334"}
    - {id: art_shot_002_v02, execution_attempt_ref: attempt_shot_002_002, artifact_ref: outputs/shot_002_v01.mp4, content_hash: "sha256:567d7e8a864365c1c2c7787e8606af3614bc1c52abfaf5546801524061b6755e"}
  observations:
    - id: obs_shot_002_001
      generation_artifact_ref: art_shot_002_v01
      artifact_ref: outputs/shot_002_v01.mp4
      observed_content_hash: "sha256:c3b5516bb098506632dbbf60e1d2f989bbfda77d16306af1b4b57a1fca0c1334"
      observed_at: "2026-09-08T08:15:00-03:00"
      procedure: "illustrative visual and media-metadata QA"
      status: PARTIAL
      checks: [{id: QG-09, required: true, result: PARTIAL, observation: "fixture contact remains ambiguous", evidence: "fixture frame reference"}]
      limitations: ["Fixture only; no runtime or media inspection executed"]
      repair_route: shot_002
    - id: obs_shot_002_002
      generation_artifact_ref: art_shot_002_v02
      artifact_ref: outputs/shot_002_v01.mp4
      observed_content_hash: "sha256:567d7e8a864365c1c2c7787e8606af3614bc1c52abfaf5546801524061b6755e"
      observed_at: "2026-09-08T08:20:00-03:00"
      procedure: "illustrative visual and media-metadata QA"
      status: PARTIAL
      checks: [{id: QG-09, required: true, result: PARTIAL, observation: "fixture contact remains ambiguous", evidence: "fixture frame reference"}]
      limitations: ["Fixture only; no runtime or media inspection executed"]
      repair_route: shot_002
```

The same `artifact_ref` does not collapse these records: the immutable attempt IDs, artifact IDs, and content hashes keep the two byte sets distinct. A resolver compares the current bytes at the locator with the selected `GenerationArtifact.content_hash` and the observation's `observed_content_hash`; a mismatch marks the observation stale, requires recollection and re-running affected QA, and cannot leave the shot `ACCEPTED`.

When the artifact exists but QA has not started, the shot remains `GENERATED` and `quality_review.lifecycle` remains `NOT_STARTED`; it must not regress to `PLANNED`/`READY`. Opening QA moves the shot to `REVIEW`. A pending `ArtifactObservation` may use `status: NOT_RUN` only with `observed_at: null`, `procedure: null`, an empty `checks` list, and an explicit non-evidentiary limitation. It does not fabricate an inspection or support `ACCEPTED`.

For example, if the QA record is created before the procedure runs:

```yaml
artifact_observation:
  id: obs_shot_002_001
  shot_id: shot_002
  generation_artifact_ref: art_shot_002_v01
  artifact_ref: outputs/shot_002_v01.mp4
  observed_content_hash: null
  observed_at: null
  procedure: null
  status: NOT_RUN
  checks: []
  limitations:
    - "QA procedure has not executed; this record is not evidence"
  repair_route: shot_002
```

After a real QA procedure executes, the collection record points to the canonical observation and the observation carries the result:

```yaml
generation_artifact_update:
  generation_artifact_ref: art_shot_002_v01
  quality_review:
    lifecycle: COMPLETE
    observation_ref: obs_shot_002_001
```

The linked canonical observation is a separate record:

```yaml
artifact_observation:
  id: obs_shot_002_001
  shot_id: shot_002
  generation_artifact_ref: art_shot_002_v01
  artifact_ref: outputs/shot_002_v01.mp4
  observed_content_hash: "sha256:c3b5516bb098506632dbbf60e1d2f989bbfda77d16306af1b4b57a1fca0c1334"
  observed_at: "2026-09-08T08:15:00-03:00"
  procedure: "manual visual inspection plus media metadata check"
  status: PARTIAL
  checks:
    - id: QG-09
      required: true
      result: PARTIAL
      observation: "example: contact remains ambiguous"
      evidence: "frame/time reference"
  limitations:
    - "Example fixture; no automated identity comparison"
  repair_route: shot_002
```

The system must not mark a plan `complete` merely because the queue accepted it. Completion requires artifact collection and the applicable quality gates, or an explicit human-approved waiver.

## 9. Failure modes and repair routes

| Failure | Detection | Repair |
|---|---|---|
| Missing node/model asset | discovery or graph validation does not find a dependency | choose an evidenced workflow/profile or block |
| Graph accepted but artifact is not validated | no collected metadata/observation | retain the plan as pending and run the applicable gate |
| Cloud/local boundary is conflated | endpoint, auth, or workflow contract is unspecified | split the execution plan and re-run preflight |
| Fallback changes a hard requirement silently | no material-change record | disclose, request approval, or return `DEGRADED` |
| Queue/upload happens without authority | mode or authorization is absent | stop and require explicit authorization |

## 10. Open questions and related documents

The first supported ComfyUI version, local node inventory, resource budget, artifact storage policy, and cloud authorization boundary remain open after Phase 0. A plan-only Phase 1 or Phase 2 may name these as `UNKNOWN` without probing or executing them. The selected profile and its capability evidence are resolved at the Phase 3 activation gate (`OQ-B-004`); local node/resource preflight belongs to Phase 4, artifact storage and media acceptance to Phase 5 (`OQ-B-002`), and cloud authorization to the external-execution gate (`OQ-B-003`). Official route/source records are in [`research.md`](research.md); capability semantics are in [`model-adaptation.md`](model-adaptation.md); the shared execution contract is in [`contracts.md`](contracts.md).
