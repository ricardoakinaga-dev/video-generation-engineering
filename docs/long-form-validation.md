# Long-form validation package

This document defines the evidence envelope for the production ladder and records the current honest boundary. The package can validate a case structurally without claiming that its media exists or is good.

## Required retained records

Each case retains: intent, plan revision, Scene Bible, shot DAG, continuity ledger, prompt/adapter mappings, feature profile, workflow fingerprint, immutable attempts, collected artifacts, per-category observations, transition scorecards, re-anchor/repair decisions, audio/dialogue timelines, assembly manifest, human checkpoints and final editorial decision.

## Ladder

| Case | Duration | Required production evidence | Current status |
|---|---:|---|---|
| LF-001 | 10–15s | physical interaction + seven contact phases + boundary frames | `BLOCKED` — exact local H3 envelope is 5.1667s and no accepted chain |
| LF-002 | 20–30s | LF-001 plus dialogue semantics/voice/performance/lip-sync/mix and causal audio | `BLOCKED` — no dialogue-capable evidence |
| LF-003 | 45–60s | dependent shots, transitions, re-anchor/repair budget and human checkpoint | `BLOCKED` — no accepted multi-shot production package |
| LF-004 | 90–120s | optional branches, recovery checkpoints, provenance manifest and editorial review | `NOT_RUN` |

## Acceptance rule

Duplicating a five-second file, concatenating unaccepted artifacts or deriving a continuity PASS from a prompt does not satisfy a ladder case. The case status can be `PASS` only if every required artifact and observation is hash-bound and the production evidence is complete. Otherwise the status is `PARTIAL`, `NOT_RUN`, `UNKNOWN` or `BLOCKED`.

The structural validator is `vge_quality.validate_long_form_case`; the executable package does not silently create fake production evidence. The local R2V probe is a capability measurement, not a long-form case until collection and semantic observation are complete.
