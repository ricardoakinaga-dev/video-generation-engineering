# Observability and debugging

## Purpose

Expose concise evidence for why the director selected a planning depth, split a shot, chose an anchor, downgraded a capability, or opened a repair. The output is decision evidence, not a hidden-reasoning transcript.

## Diagnostic contract

```yaml
decision_diagnostic:
  decision_id: DEC-0042
  stage: complexity_routing
  input_scope: scene_001
  result: DIRECTOR
  reasons:
    - multiple subjects
    - dialogue and lip-sync
    - physical vehicle interaction
    - 60-second dependency chain
  evidence_refs: [R-PLAN-01, R-PLAN-02, G-008, G-011]
  alternatives:
    - label: PRODUCTION
      rejected_because: long-form audio and state dependencies require deeper disclosure
  next_action: build_scene_bible_and_shot_graph
  confidence: MEDIUM
  limitations:
    - no runtime capability probe executed
```

The diagnostic record answers what happened, which evidence mattered, what alternative was rejected, and what the user can do next. It does not expose private chain-of-thought, hidden scratch work, or irrelevant intermediate token-level reasoning.

## Observable decision events

| Event | Required evidence | Useful output |
|---|---|---|
| `INTENT_NORMALIZED` | input fields, unknowns, assumptions | normalized scope and missing decisions |
| `REFERENCE_MAPPED` | asset role, property, provenance | retention matrix and conflicts |
| `DEPTH_ROUTED` | complexity vector and dependency edges | FAST/CINEMATIC/PRODUCTION/DIRECTOR plus reasons |
| `SHOT_SPLIT` | overloaded action or risk | old beat, new shots, preserved state |
| `ANCHOR_SELECTED` | profile and retained properties | anchor type, scope, reset condition |
| `CAPABILITY_RESOLVED` | profile evidence and requirement intersection | SUPPORTED/DEGRADED/BLOCKED plus gap |
| `EXECUTION_BLOCKED` | missing asset/node/auth/capability | operator repair or human decision |
| `EXECUTION_RECORDED` | immutable attempt ID, plan/profile/model/workflow/input/parameter context, unknowns | concrete attempt or explicit blocked/missing fields |
| `ARTIFACT_COLLECTED` | attempt ID, artifact ID/locator, collection-time content hash, media metadata | collected output bound to its execution attempt |
| `OBSERVATION_RECORDED` | artifact ID/ref, observed content hash, procedure/timestamp | pass/partial/fail with limitation; stale on hash mismatch |
| `REPAIR_OPENED` | failed gate and owning layer | smallest repair and re-evaluation path |

## Diagnostic levels

- `SUMMARY`: result, top reasons, blockers, and next action; default user-facing view.
- `DETAIL`: affected fields, dependencies, evidence refs, alternatives, and fallback.
- `AUDIT`: full stable IDs, hashes, source dates, state deltas, and raw-result links for maintainers.

Progressive disclosure applies to diagnostics too. A simple portrait should not print a full state ledger; a high-risk vehicle sequence should expose the relevant contact, camera, and state evidence.

## Redaction and provenance

Diagnostics may include IDs, hashes, non-sensitive descriptions, and source references. They must not echo credentials, private reference pixels/audio, access tokens, or unrelated personal data. Sensitive values are represented by a redacted locator and content hash where lawful and useful. Provenance and consent status are surfaced without asserting legal clearance.

## Debugging workflow

```text
observe decision → identify owner and evidence → reproduce with fixture
→ compare desired/planned/observed state → repair smallest layer
→ rerun focused gate → rerun affected regression set
```

When the reason is a model capability, inspect the versioned profile and runtime probe before changing the prompt. When it is a continuity issue, inspect the state delta and dependency edge before changing identity text. When it is a rights/safety issue, stop at the human boundary rather than optimizing the generation plan.

## Failure modes

| Failure | Signal | Repair |
|---|---|---|
| Opaque decision | result has no reason/evidence refs | add diagnostic record or mark unresolved |
| Reason dump | output exposes irrelevant private reasoning | replace with concise decision evidence |
| Stale diagnosis | source/profile/artifact changed | mark stale and rerun the check |
| Sensitive leakage | token/private content appears in logs | redact, rotate if necessary, open security issue |
| Oververbose output | low-risk task loads every diagnostic detail | apply summary/detail/audit levels |

## Open questions

The implementation must choose event storage format, correlation IDs across shot revisions, and redaction policy for user-supplied reference metadata. See [`open-questions.md`](open-questions.md).

## Related documents

Decision ownership is in [`architecture.md`](architecture.md); evidence and observation contracts are in [`contracts.md`](contracts.md); safety handling is in [`safety-boundaries.md`](safety-boundaries.md).
