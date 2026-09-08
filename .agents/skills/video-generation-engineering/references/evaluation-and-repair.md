# Evaluation, repair and delivery

Read for validation, failed generations, media QA, acceptance and assembly.

## Gates and evidence

| Gates | Required judgment |
|---|---|
| QG-01 intent; QG-02 references/rights | structure plus semantic clarification and scoped rights review |
| QG-03 narrative; QG-04 shot load | prerequisite structure plus causal/coverage judgment |
| QG-05 identity | actual frames against approved anchors; human review for material decisions |
| QG-06 geography; QG-07 temporal/state | declared boundary checks plus visible spatial/temporal review |
| QG-08 physics; QG-09 interaction | contact/action structure plus media plausibility |
| QG-10 dialogue; QG-11 performance | speaker/timing plus observed acting/reaction |
| QG-12 lip-sync | exact adapter evidence plus face/audio alignment |
| QG-13 camera; QG-14 audio | camera/event structure plus sequence/listening review |
| QG-15 compatibility; QG-16 compiler | confirmed feature intersection; preserved mappings/omissions |
| QG-17 execution | graph/input/auth/provenance/recovery plus observed runtime outcome |

Every gate record states status, evidence, procedure, limitation and repair_route. Planning checks can pass their structural scope; they cannot give media gates PASS. Use NOT_RUN when no procedure ran. For executed checks use PASS/PARTIAL/FAIL/BLOCKED with concrete frame/time/file evidence.

## Observation acceptance

An executed ArtifactObservation has id, shot_id, generation_artifact_ref, artifact_ref, observed_content_hash, observed_at, procedure, status, checks, limitations and repair_route. Checks include id, required boolean, result, evidence and observation. Acceptance must receive the canonical `shot` object and derives required IDs exclusively from `shot.acceptance_ids`; a caller-supplied checklist cannot downgrade or replace that contract.

PASS requires all required checks to pass or have a formal human waiver with reason, authority, expiry and exact artifact/check scope. Missing checks, an optional-only checklist, required NOT_APPLICABLE, expired/mismatched waiver, PARTIAL, FAIL, BLOCKED or NOT_RUN cannot yield acceptance. The helper recomputes aggregates and verifies actual local bytes, artifact/attempt/shot links and workflow hash. Recorded human authority still needs operator verification; a JSON string does not authenticate a person.

```bash
python3 scripts/vge.py aggregate checks.json
python3 scripts/vge.py accept acceptance-bundle.json
python3 scripts/vge.py probe artifact.mp4 --output metadata.json
python3 scripts/vge.py contact-sheet artifact.mp4 frames.jpg --frames 8
```

Media commands prefer native system FFmpeg/ffprobe to sandboxed desktop wrappers. Override with explicit executable paths in `VGE_FFMPEG` and `VGE_FFPROBE` when needed. `repair-scope` accepts `{plan, changed_shot_ids}` and returns the affected descendant subgraph, unaffected shots and required rechecks without changing evidence.

An acceptance bundle contains observation, artifact, attempt and the canonical `shot` object (`id`, `revision` plus `acceptance_ids`). The immutable attempt carries `shot_contract_hash`, so a forged or stale shot cannot replace the gate set. A legacy `required_checks` field may be retained as a display record, but the validator does not trust it. A pending NOT_RUN record may have null procedure/time/hash and no executed checks; it remains non-evidentiary and never regresses a RUNNING/GENERATED/REVIEW lifecycle. ACCEPTED requires full current evidence. Changed bytes invalidate dependent observations and anchors.

## Diagnose and repair

Detect → explain → repair → re-evaluate → compile. Name the earliest actionable owner: intake, reference assignment, story, continuity, directing, constraint, adapter, runtime or QA. Preserve scene intent and hard requirements. Repair the smallest affected shot/subgraph; do not regenerate already accepted independent shots. Record requirement weakened, alternative chosen, new dependencies, recheck gates and authority if needed.

Examples: missed hand contact → isolate the grasp with clearer framing and reference; state teleport → add a cause/bridge; speaker swap → separate turns and active-speaker windows; reference drift → canonical reset; unknown feature → retain requirement and change profile or disclose degradation. Fixing prompt wording is insufficient when the graph/state itself contradicts the story.

## Assembly boundary

```bash
python3 scripts/vge.py assemble assembly.json --video preview.mp4 --preview
python3 scripts/vge.py assemble accepted-assembly.json --video delivery.mp4
```

Manifest: schema_version, fps, target_duration_s, optional audio_path and ordered segments. Each segment contains artifact; final mode additionally needs observation, attempt and the canonical shot contract. The implementation checks current hashes, matching dimensions/FPS, durations, audio presence/alignment, encodes H.264/AAC MP4 and probes the result. Differences require an explicit conversion decision. Source evidence is retained in the new manifest.

Preview mode is explicitly unaccepted. Final assembly uses accepted segments but still leaves editorial_acceptance NOT_RUN until joins, narrative rhythm, sound, disclosures and final continuity are reviewed. Metadata cannot establish those. Contact sheets are sparse samples, not exhaustive motion or lip-sync tests. Use qualified human/media procedures appropriate to each gate.

## Behavioral regression cases

Validate simple landscapes, veterinary contact, fetch/return, two-person dialogue, walking-and-talking, vehicle entry, gaze-follow, product shots, driving, a 30-second spot, 60-second dialogue/action and a 90-second multi-reference rescue. Grade preserved intent, dependencies, state, source decisions, failure behavior and output class, not headings or exact prose.

Challenge ambiguity, contradictory wardrobe, species motion, overloaded shots, premature reaction, excessive continuous duration, unexplained axis/location changes, door-state contradiction, identity swap, unconfirmed joint audio, missing group roles, vehicle/brand conflict, unsupported likeness use, deceptive publication, unrelated private data and generic “no errors” constraints. Return the specific evidence gap and next step, not a generic refusal.
