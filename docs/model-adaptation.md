# Model adaptation and prompt compilation

The model-adaptation layer negotiates a model-specific execution strategy without changing the canonical scene intent. It separates what the director wants from what a model, workflow, or API can actually accept.

## 1. Capability profile

Every adapter exposes a versioned capability profile. Capability is evidence-backed and scoped to a concrete integration, not just to a model family.

The canonical serialized name is `CapabilityProfile`; `ModelProfile` is the reader-facing/domain alias retained by the original blueprint. Likewise, the compiler emits a `CanonicalPromptView`, while `CompiledPrompt` names the adapter-specific derived form. The shared aliases and enum vocabulary are owned by [`contracts.md`](contracts.md).

## Contents

- [Capability profile](#1-capability-profile)
- [Research candidate registry](#2-initial-registry-of-research-candidates)
- [Negotiation algorithm](#3-negotiation-algorithm)
- [Canonical prompt view](#4-canonical-prompt-view-canonicalpromptview)
- [Parameter binding](#5-parameter-binding)
- [Adapter contract and boundaries](#6-adapter-contract)
- [Failure modes and repair ownership](#8-failure-modes-and-repair-ownership)

```yaml
capability_profile:
  schema_version: 1
  id: comfyui-wan22-native-v1
  provider: local_comfyui
  runtime: ComfyUI
  runtime_version: UNKNOWN
  model: Wan2.2-I2V-A14B
  integration_version: "profile-2026-09-07"
  profile_revision: 1
  status: PROPOSED
  evidence_refs: [docs/research.md#SRC-COMFY-WAN22]
  evidence:
    status: PROPOSED
    claim_type: FACT
    confidence: MEDIUM
    source_refs: [https://docs.comfy.org/tutorials/video/wan/wan2_2]
    accessed_at: 2026-09-07
  prompt_style: structured_natural_language
  preferred_prompt_density: profile_defined
  supports:
    modes: [T2V, I2V, TI2V, FLF2V]
    inputs: [text, image, start_image, end_image]
    outputs: [video]
    audio: {native_generation: UNKNOWN, mux_external_audio: PROPOSED}
    identity_conditioning: UNKNOWN
    arbitrary_reference_images: UNKNOWN
    camera_controls: {syntax: natural_language_or_workflow_control, status: UNKNOWN}
  controls:
    - seed
    - width
    - height
    - frame_count
    - fps
  dependencies:
    nodes: UNKNOWN
    model_assets: UNKNOWN
  limits:
    duration_s: {min: UNKNOWN, max: UNKNOWN}
    frame_count: {rule: "profile-specific"}
    resolution: UNKNOWN
    vram: UNKNOWN
  feature_evidence:
    text_to_video: {status: PROPOSED, source_ref: docs/research.md#SRC-COMFY-WAN22, checked_at: "2026-09-07", scope: official_workflow_not_local_probe, limitation: exact_runtime_unknown}
    image_to_video: {status: PROPOSED, source_ref: docs/research.md#SRC-COMFY-WAN22, checked_at: "2026-09-07", scope: official_workflow_not_local_probe, limitation: exact_runtime_unknown}
    first_last_frame: {status: PROPOSED, source_ref: docs/research.md#SRC-COMFY-FLF, checked_at: "2026-09-07", scope: official_workflow_not_local_probe, limitation: endpoint_and_quality_unknown}
    reference_conditioning: {status: UNKNOWN, source_ref: null, checked_at: "2026-09-07", scope: local_profile, limitation: arbitrary_reference_and_identity_behavior_unprobed}
    audio_dialogue_lip_sync: {status: UNKNOWN, source_ref: null, checked_at: "2026-09-07", scope: local_profile, limitation: joint_support_unprobed}
    camera_controls: {status: UNKNOWN, source_ref: null, checked_at: "2026-09-07", scope: local_profile, limitation: syntax_and_runtime_binding_unprobed}
    duration_resolution_frames_vram: {status: UNKNOWN, source_ref: null, checked_at: "2026-09-07", scope: local_profile, limitation: effective_limits_unprobed}
  recommended_strategy:
    default: plan_only_then_local_preflight
    long_form: short_segments_with_periodic_canonical_reanchor
    visible_dialogue: separate_audio_and_lip_sync_path_unless_profile_is_confirmed
    unknown_capability: degrade_or_block_with_human_decision
  known_failure_modes:
    - identity_drift
    - recursive_chain_degradation
    - frame_flicker
    - unsupported_node_or_model_asset
  validity:
    checked_at: "2026-09-07"
    recheck_when: [ComfyUI_update, model_update, custom_node_update, workflow_change]
```

The profile's nested `feature_evidence` map prevents the profile-level tutorial citation from being mistaken for proof that every leaf capability works in the local integration. It is owned by the canonical fixture above; this document does not emit a second copy.

The profile distinguishes evidence status (`CONFIRMED`, `INFERRED`, `PROPOSED`, `UNKNOWN`) from lifecycle status (`ACTIVE`, `EXPIRED`, `DEPRECATED`). A repository capability is not automatically a ComfyUI capability, and an API feature is not automatically available in a local workflow. A feature marked `PROPOSED` is a source-backed design candidate, not an executable support claim.

The minimum profile contract is: concrete runtime/model identity, revision and validity date, source and confidence, per-feature support status, input/output modes, effective limits, controls, dependencies, known failure modes, and a recommended fallback strategy. A summary registry row may omit detail only when it links to a full profile record. `UNSUPPORTED` is a confirmed negative capability; `UNKNOWN` means the evidence is insufficient and must not be treated as support.

## 2. Initial registry of research candidates

This registry is a documentation baseline. It is intentionally conservative and must be revalidated before implementation or execution.

| Candidate profile | Profile status | Source-backed scope | Important unknowns or boundary |
|---|---|---|---|
| `wan2.2-comfyui-native` | `PROPOSED` | Official ComfyUI T2V/I2V/TI2V/FLF2V tutorials and native workflow path | Exact local node graph, runtime version, VRAM, identity retention, arbitrary reference count, audio behavior |
| `wan2.2-s2v-comfyui` | `PROPOSED` | Audio-driven speech/singing workflow with audio encoder and extension blocks | Exact integration/version, general-purpose audiovisual generation, arbitrary dialogue scenes, quality thresholds |
| `hunyuanvideo-1.5-comfyui` | `PROPOSED` | Official ComfyUI T2V/I2V workflow family, profile-specific 5–10 second examples | Exact integration/version, hardware, VRAM, temporal range, lip-sync/audio, identity guarantees |
| `minimax-hailuo-api` | `PROPOSED` | External API T2V/I2V, first-frame input, model-specific duration/resolution, camera command syntax | API version/access, full request contract, long-form guarantees, local ComfyUI execution |
| `minimax-h3-research` | `PROPOSED` | Official announcement describes multimodal audiovisual context and native stereo output | Stable public API, model access, ComfyUI integration, parameters, reproducibility, limits |

These are candidate IDs, not executable capability grants. The detailed record above is also `PROPOSED` because the sources confirm tutorial/API scope but no exact local runtime probe has been run. Each candidate must receive a full versioned record, per-feature evidence, and an adapter test before it can become `CONFIRMED` or `UNSUPPORTED`. The `minimax-h3-research` entry remains a research watch item until a concrete public contract and adapter test exist.

## 3. Negotiation algorithm

Given a canonical `SceneIntent`, the adapter negotiator:

1. identifies hard requirements and evidence obligations;
2. computes the complexity and risk vector;
3. filters profiles by provider, modality, required controls, and rights boundary;
4. checks duration, frame count, resolution, audio, reference, and workflow limits;
5. ranks feasible profiles by fit, continuity risk, cost, latency, and reproducibility;
6. selects a primary profile and records alternatives;
7. declares every downgrade, split, external dependency, or human-review step;
8. emits a compiled prompt view and an execution plan;
9. blocks when no profile satisfies critical requirements.

No adapter may silently drop a critical requirement. It may transform it, downgrade it, split the shot, or return `unresolved` with a reason.

## 4. Canonical prompt view (`CanonicalPromptView`)

The compiler starts from canonical sections and then applies a profile-specific transformation:

```yaml
canonical_prompt_view:
  schema_version: 1
  canonical_revision: scene_001_rev1
  profile_reference: comfyui-wan22-native-v1
  sections:
    subject_and_identity: [char_mara invariants]
    setting_and_time: [wet suburban platform, night rain]
    action_sequence: [approach, reach, open rear door]
    performance: [controlled urgency, visible hesitation before contact]
    camera: [medium lateral track, preserve action axis]
    lighting_and_style: [naturalistic sodium-vapor practicals]
    audio_or_sync: [door latch event, supplied dialogue line]
    continuity: [carry van scratch and ring]
    constraints: [critical active constraints]
    references: [retention rules and input assets]
  mappings:
    - canonical_section: subject_and_identity
      compiled_representation: positive_prompt.subject
      status: PROPOSED
    - canonical_section: setting_and_time
      compiled_representation: positive_prompt.setting
      status: PROPOSED
    - canonical_section: action_sequence
      compiled_representation: positive_prompt.action
      status: PROPOSED
    - canonical_section: performance
      compiled_representation: positive_prompt.performance
      status: PROPOSED
    - canonical_section: camera
      compiled_representation: positive_prompt.camera
      status: PROPOSED
    - canonical_section: lighting_and_style
      compiled_representation: positive_prompt.style
      status: PROPOSED
    - canonical_section: audio_or_sync
      compiled_representation: audio_timeline_and_sync_inputs
      status: PROPOSED
    - canonical_section: continuity
      compiled_representation: state_and_anchor_bindings
      status: PROPOSED
    - canonical_section: constraints
      compiled_representation: runtime_controls_and_qa_assertions
      status: PROPOSED
    - canonical_section: references
      compiled_representation: reference_bindings
      status: PROPOSED
  omissions: []
  compiled_view:
    profile_reference: comfyui-wan22-native-v1
    representation: adapter_specific_prompt_and_bindings
    compiled_omissions: []
    deliberate_changes: []
    unresolved: []
```

`canonical_prompt_view` is one object whose canonical sections are nested under `sections`. `mappings` makes the projection to the adapter-specific `CompiledPrompt` explicit, and the top-level `omissions` list is the single normative omission location. The `compiled_view` block is a planned representation, not evidence that this profile has been executed locally; its `compiled_omissions` list is adapter-specific metadata and is not a replacement for the canonical list. Profile compilers may reorder, condense, translate, or remove unsupported optional sections. They must retain a mapping from each canonical section to its compiled representation and record omissions.

The compiler must not claim that a negative prompt, a seed, or an input image guarantees an outcome. Those are controls or evidence sources, not proofs.

## 5. Parameter binding

Parameter binding is explicit and typed:

```yaml
parameter_binding:
  width: { value: 832, source: user_or_profile_default, unit: pixels }
  height: { value: 480, source: profile_default, unit: pixels }
  frame_count: { value: 81, source: duration_and_fps, unit: frames }
  fps: { value: 16, source: profile_default, unit: frames_per_second }
  seed: { value: 18403, source: user, reproducibility: requested }
```

Bindings record source, coercion, validation, and whether the value is reproducibility-critical. If the requested value is outside the profile, the adapter returns a bounded alternative and a visible change record.

## 6. Adapter contract

An adapter implements the following conceptual operations:

```text
discover(profile_context) -> CapabilityProfile
validate(intent, profile) -> CompatibilityReport
compile(intent, state, profile) -> CanonicalPromptView
bind(canonical_prompt_view, profile) -> ParameterBindings
build_execution_plan(canonical_prompt_view, bindings, profile) -> ExecutionPlan
record_execution_attempt(execution_plan, runtime_submission) -> ExecutionAttempt
collect(execution_attempt, output) -> GenerationArtifact
observe(artifact, profile) -> ArtifactObservation
```

`record_execution_attempt` seals the concrete profile/model/workflow/input/parameter context for one submission, and `collect` binds the returned bytes to that attempt through a content hash. `observe` is as important as `compile`: the system must learn whether a profile actually met the plan, resolving the artifact's immutable attempt link and comparing the hash captured during QA. Observations feed failure taxonomy and evals without rewriting the original intent.

## 7. Adapter boundaries

Adapters do not own story decisions, identity truth, or final acceptance. They own translation to a concrete model/workflow/API and report capability limits. The director remains responsible for choosing a fallback, splitting a shot, or requesting human review.

## 8. Failure modes and repair ownership

| Failure | Earliest preventable cause | Repair owner | Evidence needed |
|---|---|---|---|
| Profile overclaims a feature | source or probe was not scoped to the exact runtime/version | model-adaptation maintainer | dated source or executable probe |
| Compiler drops a canonical section | profile mapper has no omission record | prompt compiler | canonical-to-compiled diff |
| Workflow selects an unknown node | profile was treated as executable without preflight | ComfyUI planner/operator | runtime discovery and workflow validation |
| Long-form chain accumulates drift | no bounded segment or canonical re-anchor | continuity/shot planner | boundary observations |
| Audio/lip-sync is assumed native | profile summary conflates video and audio support | audio director/adapter | model-specific capability evidence |

Repairs must preserve the canonical intent and disclose any weakened requirement. The adapter may return `SUPPORTED`, `DEGRADED`, or `BLOCKED`; it may not turn `UNKNOWN` into `SUPPORTED` through wording alone.

## 9. Open questions and related documents

The exact local Wan node graph, supported frame ranges, VRAM envelope, identity-retention behavior, and audio/lip-sync path remain open. They are tracked in [`open-questions.md`](open-questions.md) and are required at the Phase 3 profile-activation gate (`OQ-B-004`), with local runtime preflight deferred to Phase 4 and artifact/media acceptance to Phase 5. Phase 1 and Phase 2 may carry this profile as `PROPOSED`/`UNKNOWN` for plan-only work and must not treat it as executable support. Canonical field semantics are in [`contracts.md`](contracts.md); source freshness is in [`research.md`](research.md); failure/eval ownership is in [`failure-and-evals.md`](failure-and-evals.md).
