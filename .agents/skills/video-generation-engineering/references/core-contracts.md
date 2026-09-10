# Core contracts

Read for normalized intent, references, canonical planning and serialization. Contents: ownership; JSON boundary; reference decisions; review outcomes.

## Ownership and evidence

Scene intent owns what the creator wants. Scene Bible owns global invariants and starting geography. ShotSpec owns local coverage and changes. The continuity ledger owns propagated state. CapabilityProfile owns scoped model/runtime evidence. Prompt views are derived projections. ExecutionAttempt owns one submission context; GenerationArtifact owns collected bytes; ArtifactObservation owns what an executed procedure found.

Use stable type-prefixed IDs and integer revisions. Preserve earlier versions; never rewrite observations to make a repair appear successful. `schema_version: 1` is the implemented JSON major; unknown majors fail closed. Timestamps include timezone; media positions are seconds, optionally paired with frame index and FPS. SHA-256 digests use `sha256:hex`.

Evidence status is `CONFIRMED | INFERRED | PROPOSED | UNKNOWN`; claim type is `FACT | ASSUMPTION | HYPOTHESIS | DECISION`; confidence is `HIGH | MEDIUM | LOW`. Unknown is a valid planning result. A source proves only the feature and integration it actually describes. Credentials and private data are never part of a prompt or journal.

## Authored treatment and plan JSON

Use [the complete treatment example](../assets/templates/treatment.json) to see the executable shape. The aggregate is `ScenePlan`; its fields are:

| Field | Meaning |
|---|---|
| `schema_version`, `revision` | supported wire version and immutable scene revision |
| `execution_mode` | `PLAN_ONLY` for prepare/validate/compile; runtime has its own explicit commands |
| `scene_intent` | project_id, scene_id, title, objective, duration.target_seconds, target, subjects, objects, environments, actions, style_preferences, hard_constraints, preferences, unknowns, dialogue_required, audio_required |
| `scene_bible` | schema_version, scene_id, project_id, revision, initial_state_ref, nested initial_state, entities, geography, lighting, time_of_day, visual_style and camera_language |
| `references` | ReferenceAsset objects with id, kind, locator, roles, maps_to, provenance and evidence |
| `retention_rules` | entity_id, property, policy, rationale, anchor_refs, conflict_policy, qa_obligation |
| `reference_conflicts` | id, property, candidates, precedence, severity, status, evidence_refs, resolution_route |
| `shots` | canonical ShotSpec objects described below |
| `dialogue_timeline`, `audio_timeline` | authored intervals and sources; relative to their owning shot |
| `contact_graphs`, `constraints` | relevant physical relationships and scoped obligations |
| `shot_graph`, `continuity_states`, `narrative_timeline`, `reference_timeline`, `complexity`, `decision_diagnostics` | derived by prepare where absent; stored values are checked against canonical records |
| `generation_strategy`, `assembly_plan` | bounded reset strategy and explicit edit/delivery intent |

Each shot has `id`, `scene_id`, `revision`, `lifecycle_status`, `duration_s`, `purpose`, `dependency_ids`, `active_subject_ids`, `supporting_subject_ids`, `start_state_ref`, `start_state_delta`, `end_state_delta`, `action_primitives`, `camera`, `references`, `generation_mode`, `capability_requirements`, `constraints`, `acceptance_ids`, and optional performance/dialogue/audio/contact links. No legacy `duration_seconds` or `dependencies` aliases are emitted.

`acceptance_ids` references the predefined [QG-01 through QG-17 gates](evaluation-and-repair.md#gates-and-evidence), not invented descriptive IDs. Choose applicable gates while authoring: dialogue normally includes QG-10/QG-11/QG-12/QG-14 in addition to identity/state/camera/compatibility/provenance criteria. A submitted `ExecutionAttempt` stores `shot_contract_hash`; acceptance must resolve the same shot revision and gate set rather than trusting a caller-provided checklist.

The complexity vector and `presentation_mode` are derived from duration, identities, references, dialogue/lip-sync, interactions, motion, camera movement and dependency edges. A stored vector or route that disagrees with those records is a blocking routing issue. `validation.diagnostics` and `decision_diagnostics` expose concise stage, scope, result, reasons, evidence references, alternatives, next action, confidence and limitations.

The implementation adds `state_changes`, a list of `{property, prior, next, cause}` records, to make the canonical delta-cause requirement executable. `property` is a dotted path such as `vehicle_001.door`; `cause` names a shot action primitive or a declared `transition.id`. A reviewed invariant change also requires `transition.review_ref`. Start/end delta maps remain canonical; they are checked against these causal records. A missing material prior state remains `UNKNOWN` and is not plan-ready. Dialogue records are normalized at the same boundary: speaker/listener identity, listener reaction, the timed stimulus-processing-reaction-response chain, voice strategy and lip-sync strategy are required declarations. Legacy aliases are input-compatible but never silently promoted to runtime or media evidence.

`prepare` fills mechanical IDs/references, derives timelines from authored shot durations and computes planned end states. It never invents entity identities, causal actions, dialogue or runtime support. `validate` reports structured issues with gate, reason, preserved intent, evidence gap, next action and repair path. `compile` refuses a structurally failed plan and emits the ten canonical sections with top-level mappings and omissions. All generated plan lifecycle remains PLANNED/READY; runtime evidence has a separate validator.

Canonical compilation is fail-closed: `validate_canonical_state()` rejects contradictory door/motion/seating, temporal-lighting, camera-motion, dialogue-turn and declared state combinations before adapter work. `adapt_prompt()` and `adapter_differential()` require that validated state. Negative constraints are selected by explicit scene-risk families and are returned with selected/omitted rationale; an omitted family is a disclosed limitation, never a hidden prompt loss.

Omit derived structures from a treatment to let `prepare` create them. To override edit/reset decisions explicitly, use these exact shapes (not `shot_order` or `max_chain_length`):

```json
{
  "assembly_plan": {
    "shot_ids": ["shot_001", "shot_002"],
    "target_duration_s": 12,
    "fps": 24,
    "codec": "h264",
    "container": "mp4",
    "audio_alignment": "REQUIRES_REVIEW"
  },
  "generation_strategy": {
    "type": "SHORT_SEGMENTS",
    "reanchor_every_shots": 3,
    "evidence_status": "PROPOSED",
    "drift_budget": "PROJECT_REVIEW_REQUIRED"
  }
}
```

`assembly_plan.shot_ids` must include each authored shot exactly once. This planning structure is distinct from the media assembly command's manifest, whose `segments` contain collected artifact/observation/attempt bundles.

## Reference decisions

Map a portrait to face/wardrobe only as intended; it does not supply vehicle geometry. Separate character identity from pose, camera style and composition. Reference conflicts name both candidates and retain their source links. Apply explicit user precedence. Narrower scope may select non-conflicting properties; for competing values it is only a proposed priority until the user establishes precedence. Preserve unresolved conflicts as `ASK` or separate branches.

`LOCKED` needs an anchor and QA obligation. `FLEXIBLE` names a permitted range. `DERIVED` names its causal source. `IGNORE` excludes irrelevant attributes from bindings and prompts. Deprecated `UNSPECIFIED` is not emitted. The director must inspect reference relevance and remove unrelated private data before compiling; string field validation cannot perform that judgment.

## Outcomes

`SUPPORTED_PLAN`: usable plan with explicit future runtime/media checks. `DEGRADED_PLAN`: a named requirement needs a disclosed fallback. `BLOCKED`: a hard prerequisite remains unsatisfied. `HUMAN_REVIEW_REQUIRED`: material judgment/authority cannot be automated. An adversarial decision also records `ASK | BLOCK | DEGRADED | SPLIT | HUMAN_REVIEW_REQUIRED` plus a specific reason, evidence gap, evidence required, preserved intent and next action.

### Decision routing

Keep planning `decision` separate from `execution_status`. Apply the narrowest outcome that addresses the actual issue:

| Issue | Planning decision | Concrete next step |
|---|---|---|
| Ambiguous entity roles, competing reference values, unspecified overlap, or geography | ASK | Resolve the specific material assignment/precedence/transition; retain alternatives |
| Shot overload or unmotivated camera-axis crossing with feasible coverage | SPLIT | Propose causal shots or neutralizing/motivated transition coverage |
| Requested duration/combined feature exceeds evidenced capability; species motion needs reinterpretation; blanket negative constraints lack controls | DEGRADED | Offer a specific segmented, separate audio/sync, feasible-motion or risk-scoped alternative; identify each weakened requirement |
| Inherited state contradiction or unverified consent for the requested real-person likeness/voice binding | BLOCK | Stop that dependent state/binding until repaired or authorized; keep unrelated fictional planning available |
| Identity transformation or potentially deceptive publication requires a material narrative/editorial decision | HUMAN_REVIEW_REQUIRED | Resolve transition, authority and disclosure before enabling that path |
| Irrelevant private reference data | DEGRADED | Remove/redact unrelated properties and preserve the scene-relevant intent |

A wardrobe reference's narrower role is a possible proposed precedence, not authority to resolve a supplied blue/red conflict silently. Ask which value governs unless that priority is already explicit. A segmented minute is a degraded alternative to a continuous minute, not fulfillment of its continuity requirement. Unknown joint audio support should produce a concrete separate-audio/sync plan while its execution remains blocked. If no permitted alternative preserves the material objective, explain the scoped BLOCK instead.
