# Research record

## Research status

This is a dated baseline captured on 2026-09-07. External capabilities can change. A source supports only the claim stated in its row and does not prove a local installation, visual quality, rights clearance, or future behavior.

Evidence labels used here:

- `CONFIRMED`: the linked source directly states the claim at the time checked.
- `INFERRED`: a design implication derived from one or more confirmed facts.
- `PROPOSED`: a target architecture choice.
- `UNKNOWN`: the available sources do not establish the claim.

## Contents

- [Confirmed sources](#confirmed-sources)
- [Source metadata and freshness](#source-metadata-and-freshness)
- [Design inferences](#design-inferences)
- [Blueprint assumptions challenged](#blueprint-assumptions-challenged)
- [Revalidation policy](#revalidation-policy)
- [Research failure modes and repair](#research-failure-modes-and-repair)
- [Open questions and related documents](#open-questions-and-related-documents)

## Confirmed sources

| ID | Source | Confirmed claim | Boundary/limitation |
| --- | --- | --- | --- |
| SRC-OPENAI-SKILLS | [OpenAI/Codex Build skills](https://developers.openai.com/codex/skills/) | A Skill packages instructions, resources, and optional scripts; `SKILL.md` is required; references/assets/scripts/metadata are optional; Codex uses progressive disclosure and loads full instructions after selection. | Confirms package/discovery behavior, not this product's video architecture. |
| SRC-COMFY-OVERVIEW | [ComfyUI official documentation](https://docs.comfy.org/) | ComfyUI is a node-based interface/inference engine with local and cloud API surfaces. | A runtime/API existing in the ecosystem does not mean it is installed or authorized here. |
| SRC-COMFY-ROUTES | [ComfyUI server routes](https://docs.comfy.org/development/comfyui-server/comms_routes) | The local server exposes routes including `/prompt`, `/ws`, `/features`, `/system_stats`, `/object_info`, `/history`, and model/file routes. | Route availability and behavior are version-sensitive; a probe is still required. |
| SRC-COMFY-CLOUD | [Comfy Cloud API overview](https://docs.comfy.org/development/cloud/overview) | Cloud accepts API-format workflow JSON, creates asynchronous jobs, and exposes status/output operations. | The page labels the API experimental and requires account/authentication; it is not a license to call it. |
| SRC-COMFY-WAN21 | [ComfyUI Wan2.1 examples](https://docs.comfy.org/tutorials/video/wan/wan-video) | Official examples cover T2V and I2V workflows and describe a first/last-frame example family. | Templates require an updated ComfyUI and model files; exact local nodes/limits vary. |
| SRC-COMFY-WAN22 | [ComfyUI Wan2.2 native workflow](https://docs.comfy.org/tutorials/video/wan/wan2_2) | Official examples cover a hybrid TI2V-5B model, separate T2V/I2V 14B models, and a first/last-frame workflow; model assets and node setup are explicit. | The page warns that missing nodes can mean an outdated release or failed imports; it does not prove identity lock or arbitrary references. |
| SRC-COMFY-FLF | [ComfyUI Wan FLF2V example](https://docs.comfy.org/tutorials/video/wan/wan-flf) | A first/last-frame workflow takes two images and generates intermediate transition frames; the guide documents specific model/node/input constraints. | First/last-frame support does not imply reliable multi-shot continuity or lossless recursive chaining. |
| SRC-COMFY-HYI2V | [ComfyUI HunyuanImageToVideo node](https://docs.comfy.org/built-in-nodes/HunyuanImageToVideo) | The node accepts an optional start image and produces video latent conditioning with distinct guidance types. | The page notes its documentation is AI-generated; local node behavior must be probed. |
| SRC-COMFY-HY15 | [ComfyUI HunyuanVideo 1.5 tutorial](https://docs.comfy.org/tutorials/video/hunyuan/hunyuan-video-1-5) | The official tutorial advertises T2V/I2V workflow templates, 5–10 second generation, and profile-specific model assets. | Version, hardware, quality, and capability claims must be rechecked before a profile is activated. |
| SRC-COMFY-S2V | [ComfyUI Wan2.2 S2V example](https://docs.comfy.org/tutorials/video/wan/wan2-2-s2v) | An official native workflow describes audio-driven video, audio encoders, dialogue/singing use cases, and extension blocks with frame/audio timing. | This is a specific S2V workflow, not evidence that all models generate synchronized audio or arbitrary dialogue. |
| SRC-COMFY-AUDIO | [ComfyUI CreateVideo node](https://docs.comfy.org/built-in-nodes/CreateVideo) | A video can be assembled from images with an FPS and optional audio input. | Assembly support is not the same as audio generation or lip-sync. |
| SRC-WAN22 | [Wan2.2 official repository](https://github.com/Wan-Video/Wan2.2) | The project publishes T2V/I2V/TI2V, S2V, and Animate-related model/workflow families. | Repository capability and ComfyUI integration are separate claims. |
| SRC-HYUNYUAN | [HunyuanVideo official repository](https://github.com/Tencent-Hunyuan/HunyuanVideo) | The original repository documents prompt/video-length parameters and substantial resource requirements; it also links later I2V/1.5 work. | Resource figures are model/version-specific and cannot be generalized to all Hunyuan profiles. |
| SRC-MINIMAX-API | [MiniMax image-to-video API reference](https://platform.minimax.io/docs/api-reference/video-generation-i2v) | The API documents model-specific first-frame input, prompt length, camera command syntax, and duration/resolution combinations for Hailuo/I2V models. | This is an external API contract, not a local ComfyUI capability. It is asynchronous and provider-controlled. |
| SRC-MINIMAX-H3 | [MiniMax H3 announcement](https://minimaxi.com/blog/minimax-h3) | The announcement says H3 understands text/image/video/sound context, can output native stereo audiovisual content, and supports up to 15 seconds at 2K. | An announcement is not a complete public API or ComfyUI integration contract; H3 remains unverified for this package's execution boundary. |
| SRC-OPENAI-SAFETY | [OpenAI safety best practices](https://developers.openai.com/api/docs/guides/safety-best-practices) | Official guidance recommends moderation, adversarial testing/red-teaming, human oversight, and communicating model limitations. | This is general application guidance, not a complete policy for every video provider or content category. |
| SRC-OPENAI-PROVENANCE | [OpenAI content provenance check reference](https://developers.openai.com/api/reference/python/resources/content_provenance_checks/methods/create) | The API reference documents checks for known provenance signals and warns that a `not_detected` result does not prove content is not generated. | A provenance signal is not consent, legal clearance, or a universal detector. |
| SRC-OPENAI-DATA | [OpenAI data controls](https://developers.openai.com/api/docs/guides/your-data) | Official documentation describes endpoint-specific data retention/application-state behavior and warns that third-party MCP services have their own policies. | Retention and eligibility are account/endpoint/version-sensitive; this package does not make account-specific claims. |
| SRC-C2PA | [C2PA specifications](https://spec.c2pa.org/specifications/) | C2PA defines technical specifications for provenance and authenticity, including manifests and assertions for media workflows. | Provenance does not itself prove consent, truth, or legal clearance; it is a transparency/control layer. |
| SRC-NIST-SYNTHETIC | [NIST synthetic-content report](https://www.nist.gov/publications/reducing-risks-posed-synthetic-content-overview-technical-approaches-digital-content) | NIST surveys provenance, labeling, detection, testing, and risks including non-consensual synthetic depictions. | This informs governance requirements; it is not a product-specific legal determination. |
| SRC-STORYBOARDING | [Multi-Shot Character Consistency](https://arxiv.org/abs/2412.07750) | The paper treats multi-shot character consistency as a distinct problem and reports a method that balances identity retention with motion. | Research evidence supports the need for explicit cross-shot planning; it does not guarantee any runtime model. |
| SRC-LONGDIFF | [LongDiff, CVPR 2025](https://openaccess.thecvf.com/content/CVPR2025/papers/Li_LongDiff_Training-Free_Long_Video_Generation_in_One_Go_CVPR_2025_paper.pdf) | The paper identifies degradation of temporal consistency and visual detail when extending short-video models and uses shot/keyframe structure. | It supports risk framing, not a universal chaining algorithm. |
| SRC-VIDEORT | [VideoReTalking](https://arxiv.org/abs/2211.14758) | The work separates canonical-expression generation, audio-driven lip-sync, and face enhancement into distinct stages. | It is a talking-head research system; general scenes still need profile-specific validation. |

## Source metadata and freshness

All rows above were reviewed on 2026-09-07. `Official` means the publisher is the model/runtime/vendor owner or an official standards body; `Primary` means a paper or repository authored by the system's creators. Confidence applies to the row's narrow claim, not to local runtime behavior.

| ID | Publisher | Authority | Accessed | Applicable version/date | Confidence |
|---|---|---|---|---|---|
| SRC-OPENAI-SKILLS | OpenAI/ChatGPT Learn | Official | 2026-09-07 | Current page; redirected to `learn.chatgpt.com/docs/build-skills` | High |
| SRC-COMFY-OVERVIEW | ComfyUI | Official | 2026-09-07 | Current documentation | High |
| SRC-COMFY-ROUTES | ComfyUI | Official | 2026-09-07 | Current server routes documentation | High |
| SRC-COMFY-CLOUD | ComfyUI | Official | 2026-09-07 | Current Cloud API overview | High |
| SRC-COMFY-WAN21 | ComfyUI | Official | 2026-09-07 | Current Wan2.1 tutorial | High |
| SRC-COMFY-WAN22 | ComfyUI | Official | 2026-09-07 | Current Wan2.2 tutorial | High |
| SRC-COMFY-FLF | ComfyUI | Official | 2026-09-07 | Current Wan FLF tutorial | High |
| SRC-COMFY-HYI2V | ComfyUI | Official | 2026-09-07 | Current built-in node documentation | Medium |
| SRC-COMFY-HY15 | ComfyUI | Official | 2026-09-07 | Current HunyuanVideo 1.5 tutorial | High |
| SRC-COMFY-S2V | ComfyUI | Official | 2026-09-07 | Current Wan2.2 S2V tutorial | High |
| SRC-COMFY-AUDIO | ComfyUI | Official | 2026-09-07 | Current CreateVideo node documentation | High |
| SRC-WAN22 | Wan-Video | Primary repository | 2026-09-07 | Current repository; release-specific | High |
| SRC-HYUNYUAN | Tencent Hunyuan | Primary repository | 2026-09-07 | Current original repository; version-specific | High |
| SRC-MINIMAX-API | MiniMax | Official | 2026-09-07 | Current Hailuo/I2V API reference | High |
| SRC-MINIMAX-H3 | MiniMax | Official announcement | 2026-09-07 | Announcement dated 2026-07-31 | Medium |
| SRC-OPENAI-SAFETY | OpenAI | Official | 2026-09-07 | Current safety guidance | High |
| SRC-OPENAI-PROVENANCE | OpenAI | Official API reference | 2026-09-07 | Current content provenance endpoint reference | High |
| SRC-OPENAI-DATA | OpenAI | Official API guidance | 2026-09-07 | Current data-controls guidance | High |
| SRC-C2PA | C2PA | Official standards body | 2026-09-07 | Current specification index | High |
| SRC-NIST-SYNTHETIC | NIST | Official public research | 2026-09-07 | Current publication page | High |
| SRC-STORYBOARDING | CVPR/arXiv authors | Primary paper | 2026-09-07 | CVPR 2025/arXiv record | Medium |
| SRC-LONGDIFF | CVF/arXiv authors | Primary paper | 2026-09-07 | CVPR 2025 paper | Medium |
| SRC-VIDEORT | arXiv authors | Primary paper | 2026-09-07 | 2022 paper | Medium |

## Design inferences

| ID | Inference | Basis | Design consequence |
| --- | --- | --- | --- |
| INF-001 | A capability registry and runtime probe are necessary. | ComfyUI has versioned nodes/templates/API routes and warns about missing imports. | The adapter must fail closed and record evidence. |
| INF-002 | The canonical model must separate planning from observation. | Video generation remains stochastic; multi-shot research treats consistency as a separate problem. | A coherent plan never counts as artifact acceptance. |
| INF-003 | A shot graph is a better state carrier than a duration-only timeline. | Long-video work uses shots/keyframes, and interaction/camera/audio dependencies cross time. | Edges carry state/anchor dependencies. |
| INF-004 | Audio must be a separable track. | ComfyUI documents both optional audio muxing and specialized S2V/talking workflows. | Native audio is per-profile; external audio is valid. |
| INF-005 | Provenance and consent belong in intake. | C2PA and NIST identify provenance and synthetic-media misuse concerns. | Real likeness/voice/reference inputs create a human review boundary. |

## Blueprint assumptions challenged

1. **Duration-only routing is insufficient.** Keep explicit duration floors for minimum structural coverage, then let complexity and dependency edges raise the required plan depth before those floors.
2. **“Locked” is not enforcement.** It is a retention goal plus an acceptance criterion. Only a runtime control or artifact observation can support stronger language.
3. **First/last-frame chaining is not universal.** Wan examples confirm specific workflows; the core cannot assume every model supports an end frame or that decoded frames preserve all latent context.
4. **Native dialogue/audio is not universal.** A model may accept text, image, or audio in different combinations. The profile must expose separate `speech`, `audio_generation`, `lip_sync`, and `audio_mux` capabilities.
5. **MiniMax H3 is not yet a confirmed ComfyUI profile.** The official announcement is enough to register a research candidate, not enough to emit a ComfyUI workflow or promise API fields.
6. **The Skill is not an autonomous production backend.** Official Skill guidance supports instruction packages with optional resources/scripts; the product design therefore keeps external execution behind explicit authorization and a runtime boundary.

## Revalidation policy

Revalidate a source or profile when any of these occur: model name/version changes, ComfyUI update, node/template change, provider API change, output duration/resolution change, audio/lip-sync requirement, new reference modality, major failure observed, or a release decision. A stale profile becomes `EXPIRED` and may only produce a plan with an explicit limitation or a new confirmation.

## Research failure modes and repair

| Failure | Detection | Repair |
|---|---|---|
| Marketing statement treated as capability proof | source is not a scoped operational contract | downgrade to `INFERRED`/`UNKNOWN` and require a probe |
| Source has no date or applicability | metadata row is incomplete | re-open the source and record version/freshness |
| Official runtime feature is generalized to every profile | claim crosses model/version/workflow boundary | split the profile and revalidate each feature |
| Stale evidence drives execution | a revalidation trigger has fired | mark profile `EXPIRED` and block or plan with limitation |

## Open questions and related documents

The research owner does not decide product semantics; it supplies scoped evidence. Open profile/runtime questions are in [`open-questions.md`](open-questions.md); capability use is constrained by [`model-adaptation.md`](model-adaptation.md) and [`comfyui-execution.md`](comfyui-execution.md); source claims feed [`traceability.md`](traceability.md). The external links above are primary/official sources for their narrow claims, not universal guarantees.
