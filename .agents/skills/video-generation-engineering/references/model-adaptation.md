# Model adaptation

Read when selecting a model/runtime, compiling a target prompt or negotiating unsupported requirements. Profiles are data; core scene semantics do not change with a provider.

## Scoped capability evidence

Each profile records schema_version, id, provider, runtime/runtime_version, model/integration version, profile_revision, evidence status, supports.modes/inputs/outputs/audio/camera, controls, dependencies, limits, feature_evidence, known_failure_modes, fallback strategy and validity. Separate lifecycle expiry from evidence status. For executable negotiation, the helper requires a timezone-aware `validity.expires_at`, nonempty profile `evidence_refs`, and feature records with `CONFIRMED`, `source_ref`, `probe_ref`, scope and check date; both evidence references must be bound to the profile registry. The operator must resolve those probes to actual current evidence; a self-declared string is not independent proof.

Start with candidate profiles in [profiles/](../profiles/). They intentionally cannot authorize generation. A profile citation to a tutorial confirms only that tutorial's scope. Runtime node discovery confirms availability, not inference, identity, camera control or lip-sync quality. Record exact tested model asset hashes, workflow hash, dimensions, frame grid, FPS, runtime/node versions and hardware in the probe. A software/model/workflow change triggers revalidation.

H3 is not permanently forbidden or permanently supported: inspect the currently installed source and exact API contract. A local H3 integration may differ from a provider H3 API. Promote only tested leaf features, keeping reference identity, audio/lip-sync and visual quality separately scoped. Do not extrapolate one 5-second probe to 120-second continuous generation.

## Negotiation

For each shot intersect mode, required input/reference behavior, audio/sync, camera, duration, resolution, frame grid, controls and memory/resource envelope with confirmed profile evidence. Prefer feasible profiles by fit, continuity risk and user cost/latency preferences. Unknown critical support returns BLOCKED; optional degradation requires a visible change and compensating review.

Map T2V→text_to_video, I2V→image_to_video, TI2V→text_image_to_video, FLF2V→first_last_frame. Additional shot `capability_requirements` name exact feature_evidence keys; a shot with asset references also requires `reference_conditioning`, rather than inheriting it silently from a model name. An explicit `degradable_capability_requirements` list may produce `DEGRADED`, but execution still requires a separate approval. Frame-count rules are profile-defined integer multiple plus offset. FPS/frame duration must agree within a declared tolerance, never silently coerce an intended continuous take into cuts.

If the profile supports five seconds and the user requests a continuous minute, propose segmented canonical re-anchoring as a changed outcome or keep the continuous requirement blocked. For visible dialogue with unknown joint support, preserve the dialogue and propose separate audio/sync, cutaways or approved voiceover.

## Prompt compilation

The ten canonical sections are subject_and_identity, setting_and_time, action_sequence, performance, camera, lighting_and_style, audio_or_sync, continuity, constraints and references. Every section has an explicit mapping to model language, workflow input, audio stage or QA. Top-level `omissions` is authoritative. Optional omissions need reason; critical omissions block compilation. The blueprint presentation fields live under `presentation`.

The helper emits a lossless structured view; effective model prose remains a director task. Describe visible actions and camera behavior concretely, keep entity names stable, use the model's supported reference tags, and reduce competing actions. Seeds, negatives and image conditioning are controls, not preservation guarantees.

## External adapter boundary

The Hailuo candidate is a separate external profile. The [official MiniMax I2V contract](https://platform.minimax.io/docs/api-reference/video-generation-i2v), checked 2026-09-08, describes asynchronous creation via `/v1/video_generation` with model, prompt, duration, resolution and first-frame input. Account access and exact operational limits remain unprobed. Use the installed provider tool or an explicitly configured authenticated adapter; credentials stay in the environment/tool credential store. A provider request needs transfer/cost authority and an immutable submission record. The bundled CLI defaults to local ComfyUI and does not silently send a plan to a paid API.

The optional Hailuo adapter prepares requests offline with `hailuo-plan spec.json`. Spec contains `profile`, canonical `shot`, reviewed `prompt`, `resolution`, and for I2V `first_frame_image` plus `reference_provenance`. It supports its explicit 2.3/2.3-Fast/02 T2V/I2V subset, rejects unsupported mode/duration/resolution combinations and refuses prompt truncation. Automatic provider prompt optimization is disabled to preserve reviewed intent.

`hailuo-submit spec.json --destination runs --authorize-paid-call` requires a confirmed profile and `MINIMAX_API_KEY` outside artifacts. Image requests additionally need `--authorize-transfer`, explicit rights status and explicit consent status; identity-sensitive roles require confirmed scope, not an omitted flag. `hailuo-poll TASK_ID` queries the same task with a bounded timeout; the [official status contract](https://platform.minimax.io/docs/api-reference/video-generation-query) is checked 2026-09-08. Paid calls are never a fallback from ComfyUI. Transport records retain request hashes and task IDs but cannot substitute for unavailable provider model/runtime provenance or media acceptance. Retrieve completed files through the authenticated provider file tool/API, then collect hashes and QA; unprobed provider provenance remains a disclosed limitation.

## Extending support

Add a full versioned profile, a valid exact graph/request fixture, a positive negotiation case, unknown/unsupported/expired cases, and one operational probe before activation. Keep the runtime compilation mapping alongside the profile. Reference-conditioning, audio-driven, first/last-frame, post-processing and external delivery remain individually gated.
