# Video Generation Engineering — implementation ExecPlan

<!-- engineering-framework: active_action_id=VGE-BUILD-01 -->

## Purpose / Big Picture
Deliver the repository-scoped Codex skill specified by docs/, with usable direction, canonical planning, deterministic validation, model negotiation, runtime/provenance and media tooling, tested through real local boundaries where available. The user explicitly authorized full implementation on 2026-09-08. Production media quality is a measured outcome, not an AAA label we can self-award.

## Progress
- [x] Recovered Phase 0, r5 correction and archived reports; no Git repository exists.
- [x] Resolved OQ-B-001: repository `.agents/skills/video-generation-engineering`, Codex CLI/IDE, automatic discovery and explicit invocation, PLAN_ONLY default. Official skill docs checked 2026-09-08.
- [x] Build self-contained skill and a validated planning-to-prompt vertical slice.
- [x] Implement graph/state/QA/profile validation and regression fixtures.
- [x] Implement ComfyUI discovery, binding, bounded execution recovery, immutable provenance and media assembly.
- [x] Exercise installed runtime, frozen golden/adversarial cases, isolated package and review.
- [x] Record evidence, requirement coverage, limitations and delivery.

## Surprises & Discoveries
Phase 0 says no local runtime. Read-only discovery found `/home/ricardo/ComfyUI`, ComfyUI commit 56727514, server stopped, RTX 3060 12 GiB, H3 video weights and FFmpeg installed. Runtime/model support needs current probes. JSON Schema library is absent; the deterministic core will use Python standard library and reject malformed JSON explicitly.

## Decision Log
- Build the repository path already proposed in docs; do not install global duplicates.
- Preserve docs/BLUEPRINT.md and historical audit/control records. Phase 0 stop is superseded by the current explicit implementation request.
- Codex owns semantic direction and reference interpretation; helpers own reproducible graph/state/schema, provenance, runtime and media mechanics. Never infer real visual success from fixtures.
- Plan JSON is the portable script boundary; the shipped CLI intentionally accepts JSON only, with no PyYAML dependency. Model/provider-specific fields remain in profiles and adapter boundaries.
- External provider target/authority requested asynchronously. Local installed runtime tests are authorized; paid requests, uploads and model downloads require a selected scope.

## Outcomes & Retrospective
Implementation delivered: 90 tests pass, portable package and ZIP verified, real ComfyUI H3 generation collected, final current-code integration confirmed via cache. Independent code findings closed. Forward-use evidence covers 29 initial cases and eight revised responses; it is not universal semantic acceptance. Media remains PARTIAL and external modes remain unconfirmed. See IMPLEMENTATION.md and verification/software-release.json.

## Context and Orientation
Root is video-generation-engineering. docs/contracts.md owns wire names, docs/requirements.md owns requirements, docs/golden-scenarios.md and adversarial-scenarios.md own behavioral oracles. Historical process state is under .agent and .gauntlet. The package will be self-contained under .agents/skills/video-generation-engineering; tests and build evidence remain outside it.

## Scope and Constraints
T3_SYSTEM, GREENFIELD FEATURE, BUILD, MEDIUM risk, SYSTEM blast radius. Implement all planned responsibilities, with optional runtime capabilities activated only by exact evidence. Keep no credentials in artifacts. No blind submission retries. Human media/editorial and rights criteria cannot be replaced by structural tests. Skill instructions: engineering-framework, skill-creator, OpenAI Docs. No applicable AGENTS.md found.

## Architecture and Interfaces
Eight conditional references behind a concise SKILL.md. Python scripts provide plan preparation, validation, prompt compilation, capability negotiation, ComfyUI API graph preflight/binding/execution, immutable attempt/artifact records, ffprobe/FFmpeg assembly and export. JSON input/output and explicit nonzero errors. Tests exercise API and CLI plus local HTTP fake server and real synthetic media, with separately labeled runtime observations. Stable schema_version=1 and canonical contract fields retained; additional aggregate/transition fields documented.

## Milestones
1. A short scene can be prepared, validated and compiled without a runtime.
2. Long scenes, branched continuity, reference conflicts, dialogue/audio timing, malformed inputs, stale hashes and unconfirmed profiles have rejectable tests.
3. Discovered ComfyUI graphs can be checked and bound; submission is opt-in, journaled before network effects, and recoverable by ID without blind retry.
4. Accepted segments can be assembled, probed and hashed, with explicit separate editorial acceptance.
5. All requirements have implementation/evidence or an explicit pending external oracle; final review leaves no concealed blocker.

## Plan of Work
Build the shortest end-to-end planning path first. Add failure invariants, then runtime and media boundaries. Author focused references while matching executable contracts. Use small portable fixtures and known-bad mutations. Inspect actual outputs; review after integration and repair findings. Update the release report with exact verified limits.

## Concrete Steps
1. [VGE-BUILD-01] Create the package entrypoint, core contracts/reference and Python plan boundary in .agents/skills/video-generation-engineering.
2. Run python3 -m unittest discover -s tests -v after adding behavior fixtures.
3. Validate package metadata, links, CLI portability and real runtime/media probes; write verification/implementation report.

## Validation and Acceptance
| Criterion | Required | Procedure/environment | Expected observation | Evidence destination |
|---|---|---|---|---|
| VGE-Q1 | yes | skill-creator quick_validate + isolated package | valid metadata, all references resolve, no repo dependency | verification/ |
| VGE-Q2 | yes | golden/adversarial semantic cases and structural suite | preserve intended decisions; reject known-bad inputs | tests/ and verification/ |
| VGE-Q3 | yes | state/DAG/dialogue/reference mutation suite | no silent contradictions or observed-state promotion | tests/ |
| VGE-Q4 | yes | profile/compiler tests | no unknown support grants, omissions explicit | tests/ |
| VGE-Q5 | yes | fake HTTP and installed local runtime | graph preflight, bounded recovery, no automatic replay | verification/ |
| VGE-Q6 | yes | hash/observation/waiver tests | stale or unobserved media cannot be accepted | tests/ |
| VGE-Q7 | yes | real synthetic FFmpeg/ffprobe assembly | correct durations/FPS/codecs/audio, immutable manifest | verification/ |
| VGE-Q8 | yes | requirement mapping and distinct review | all 79 IDs accounted for, limitations visible | IMPLEMENTATION.md |
| VGE-MEDIA | yes for production-media readiness | generated video and qualified review | artifact identity/contact/lipsync/long-form gates pass | pending exact media oracle |

## Risks and Human Decisions
Installed model availability does not prove VRAM feasibility. Use bounded local probes; do not download models automatically. Cloud integration needs selected provider credentials and transfer scope. Visual quality requires qualified observations; maintain NOT_RUN until performed. Numeric drift tolerance remains project-specific. One-agent implementation review is not independent criticism.

## Idempotence and Recovery
Read current package, plan, state and verification before resuming. CLI writes should refuse collisions unless an explicit replace is allowed for derived files. Submission journal IDs are unique; uncertain submissions must be reconciled with history, never repeated automatically. Preserve original artifacts and append revisions. Do not rewrite historical Gauntlet PASS. Roll back only task-owned additions with user scope; no global environment changes.

## Artifacts and Evidence
- docs/: approved semantic baseline and scenario oracles.
- audit-artifacts/reports/AUDIT-docs-2026-09-08-r5.md: corrected last static finding.
- verification/: implementation test and runtime evidence (created during work).
