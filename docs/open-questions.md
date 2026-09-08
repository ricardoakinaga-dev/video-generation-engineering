# Open questions and decision queue

## Implementation decisions — 2026-09-08

OQ-B-001 is resolved: repository `.agents/skills/video-generation-engineering`, Codex IDE/CLI, automatic and explicit invocation, PLAN_ONLY default. OQ-B-004 is resolved only for the exact local H3 T2V probe (384×224, 124 frames, 24 FPS); other modes/profiles remain candidates. OQ-B-003 remains open for external transfers; the user authorized installed local ComfyUI execution. OQ-B-002 remains open for full audiovisual production acceptance; runtime metadata and sparse frames have bounded evidence. These are capability-specific limits, not a blocker to using the implemented planner.

N-002 uses separate immutable observations; N-005 uses portable Python JSON validators; N-007 uses immutable shot records and an assembly manifest. Numeric drift thresholds remain project-specific. See [ADR-011](adr/ADR-011-skill-implementation-and-evidence.md) and [implementation evidence](../IMPLEMENTATION.md). Historical staged questions follow.

## Purpose

Keep uncertainty visible without turning every unknown into a blocker. A question is blocking when Phase 1 cannot safely specify a contract or when the answer changes authorization, architecture, or an acceptance gate.

## Stage-gated blockers

The queue is staged by the first phase that needs each answer. A plan-only Phase 1 skeleton does not need a local GPU, media oracle, upload policy, or confirmed model profile. Those remain blockers at the later boundary where the corresponding capability or evidence is activated.

### Blocking before Phase 1 implementation

| ID | Question | Why blocking | Required evidence/authority | Owner |
|---|---|---|---|---|
| OQ-B-001 | What Phase 1 host/package contract and plan-only invocation boundary are supported first? | The skeleton cannot define its entrypoint, context routing, or refusal behavior without a target host contract | User/project decision plus local host/package inspection | Maintainer/operator |

### Blocking before model/profile activation (Phase 3)

| ID | Question | Why blocking | Required evidence/authority | Owner |
|---|---|---|---|---|
| OQ-B-004 | Which model/profile subset is allowed to become `CONFIRMED`? | Model claims and workflows must be versioned and probed before adapter activation | Current official docs plus local/API probe | Adapter owner |

### Blocking before external execution (Phase 4)

| ID | Question | Why blocking | Required evidence/authority | Owner |
|---|---|---|---|---|
| OQ-B-003 | Which references may be uploaded or sent to external providers, under what consent/provenance policy? | External execution and sensitive media authority are unresolved | User/org policy and provider terms | Rights/safety owner |

### Blocking before artifact/media acceptance (Phase 5)

| ID | Question | Why blocking | Required evidence/authority | Owner |
|---|---|---|---|---|
| OQ-B-002 | What artifact-level visual/audio oracles are available for identity, contact, camera, and lip-sync? | Media gates cannot be accepted beyond structural planning without an oracle or qualified review procedure | Approved datasets/tools and human-review procedure | QA owner |

## Non-blocking design questions

| ID | Question | Safe interim decision | Revisit when |
|---|---|---|---|
| OQ-N-001 | Is `Subject` a schema base or presentation grouping? | Keep a shared conceptual envelope; avoid inheritance commitment | First implementation fixtures |
| OQ-N-002 | Should observations be separate records or embedded gate results? | Use separate conceptual records in contracts | Persistence design |
| OQ-N-003 | What numeric tolerance language expresses spatial/timing drift? | Use domain-specific ranges with explicit units | Artifact QA dataset |
| OQ-N-004 | Which patterns deserve templates versus prose? | Admit only fixture-backed patterns | Repeated fixture authoring |
| OQ-N-005 | Should deterministic validation be a script or host-side checks? | Start instruction-only; add script only after repetition | Phase 1 contract tests |
| OQ-N-006 | Which provider/model profiles deserve dedicated references? | Load only evidence-backed profiles tied to a user need | Target selection |
| OQ-N-007 | How are assemblies for `90 ≤ t ≤ 120` seconds versioned and recovered? | Shot artifacts plus manifest and state ledger | Long-form integration |

## Decision protocol

For each question, record the decision, evidence date, affected requirements, rejected alternatives, and whether prior evidence becomes stale. A user/rights decision cannot be inferred from a technical convenience. A provider capability cannot be promoted from `PROPOSED` to `CONFIRMED` without current source or an executable probe.

## Related documents

Open questions are surfaced in [`00-index.md`](00-index.md), acceptance is defined in [`acceptance.md`](acceptance.md), and future sequencing is in [`roadmap.md`](roadmap.md).
