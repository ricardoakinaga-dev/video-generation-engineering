# Proposed production Skill structure

## Implemented package — 2026-09-08

The repository skill now exists at [SKILL.md](../.agents/skills/video-generation-engineering/SKILL.md). [Implementation results](../IMPLEMENTATION.md) record tested software, actual local ComfyUI execution and remaining media/provider limits. The Phase 0 design and historical gates below are preserved; they do not certify the implementation. See [ADR-011](adr/ADR-011-skill-implementation-and-evidence.md).

## Status and boundary

This file is the Phase 0 proposal and rationale for the package that was later authorized by ADR-011. The current production-scoped Skill is implemented at `../.agents/skills/video-generation-engineering`; the tree below is retained as the package-shape contract, not as a claim that implementation is still pending.

## Smallest effective tree

```text
video-generation-engineering/
└── .agents/skills/video-generation-engineering/
    ├── SKILL.md
    ├── references/
    │   ├── core-contracts.md
    │   ├── continuity-and-long-form.md
    │   ├── directing-and-audio.md
    │   ├── interaction-and-constraints.md
    │   ├── model-adaptation.md
    │   ├── comfyui-execution.md
    │   ├── evaluation-and-repair.md
    │   ├── observability.md
    │   └── safety-and-provenance.md
    ├── assets/
    │   └── templates/              # only if proven useful by fixtures
    ├── scripts/
    │   └── validate_plan.py        # optional; only for deterministic checks
    └── agents/openai.yaml          # optional metadata/dependencies
```

The package location follows the official local repository Skill convention described in the [OpenAI Build skills documentation](https://developers.openai.com/codex/skills/). The current layout has been revalidated by package checks; docs and historical audit assets remain outside the distributable package.

## File justification

| Resource | Why does it exist? | When loaded? | Decision improved | What breaks without it? |
|---|---|---|---|---|
| `SKILL.md` | Orchestrates intake, planning, adaptation, and verification | Every activated task | Keeps the workflow procedural and concise | No reliable activation or phase ordering |
| `core-contracts.md` | Shared IDs, states, evidence, invariants | Any non-trivial task | Prevents prompt/state terminology drift | Modules disagree on state and proof |
| `continuity-and-long-form.md` | State propagation, anchors, timeline, assembly | Multi-shot or >30s/dependent work | Prevents identity/temporal decay | Long-form collapses into unbounded prompts |
| `directing-and-audio.md` | Story, performance, dialogue, camera, audio/lip-sync | Dialogue, action, or expressive work | Makes behavior observable and synchronized | Lines/reactions/sound become ambiguous |
| `interaction-and-constraints.md` | Contact, motion, anatomy, vehicle/animal risks | Physical/articulated interactions | Selects risk-specific constraints | Prose falsely promises physics |
| `model-adaptation.md` | Capability profiles and compiler rules | Target model/runtime selected | Fails closed on unsupported features | Model syntax contaminates core intent |
| `comfyui-execution.md` | Workflow/preflight/authentication boundary | ComfyUI target | Distinguishes plan from queue/action | Unsupported graph assumptions or side effects |
| `evaluation-and-repair.md` | Gates, fixtures, observations, repair loop | Build, diagnose, review | Makes failure actionable and regression-safe | Success is judged by wording or file existence |
| `observability.md` | Concise decision diagnostics, levels and redaction | Implementation, diagnosis, review | Makes routing and blockers auditable without hidden reasoning | Operators cannot distinguish a reasoned block from an opaque failure |
| `safety-and-provenance.md` | Likeness, privacy, deception, consent, disclosure | Sensitive references or external effects | Preserves human authorization boundary | Unsafe or unapproved media path |
| `templates/` | Repeated fixture/plan skeletons | Only after repetition is proven | Reduces mechanical omission | No material breakage; can remain absent |
| `validate_plan.py` | Deterministic schema/link/invariant checks | Only if a stable repetitive check exists | Rejects malformed plans consistently | Manual checks may miss structural defects |
| `agents/openai.yaml` | Optional UI/dependency metadata | Host/package discovery | Better presentation or tool declarations | No core reasoning breakage; optional |

## What must remain outside the package initially

The full research archive, every golden narrative, provider marketing summaries, raw external documentation, generated workflow JSON, model weights, and visual QA datasets should remain project/evaluation assets until a later packaging decision proves their inclusion improves behavior without context bloat.

## Design principles

- Keep `SKILL.md` procedural and short; use progressive disclosure for domain detail.
- Prefer instructions over scripts unless deterministic behavior is hard to reproduce by reasoning.
- Keep model-specific claims in dated profiles; do not duplicate them in core references.
- Require a fixture and failure oracle before admitting a reusable pattern.
- Preserve plan-only default and explicit authorization for all external effects.

## Open questions

The final package name, repository path, script boundary, and metadata/dependency needs are non-blocking until Phase 1. They must be decided with the current official host guidance and fixture evidence.
