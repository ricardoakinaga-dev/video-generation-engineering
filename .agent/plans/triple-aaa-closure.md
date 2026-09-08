# Triple-AAA Skill closure

Status: DONE_WITH_RISKS

## Objective

Implement the complete user-supplied production validation and architecture-closure requirements for the `video-generation-engineering` Skill, while preserving the existing coherent planning core and recording honest boundaries for unavailable providers or unobserved media quality.

## Scope and constraints

- Normative phase artifacts live in `docs/`; the user's `dorcs` is interpreted as `docs` because that is the repository's established documentation boundary.
- The historical `.gauntlet/` run and historical verification reports are immutable evidence. This closure uses `docs/triple-aaa-quality-bar-r1.json`, current `verification/` artifacts and fresh fingerprints.
- No paid provider calls, external uploads, model downloads or unapproved transfer occur.
- A capability or quality check is never promoted to PASS from metadata, node presence, a prompt, a contact sheet or an uninspected artifact.
- New package code is standard-library-only and must remain portable from a different working directory.

## Current baseline

- Repository: `main`, clean at the start of this closure, origin configured to the requested GitHub repository.
- Existing package and documentation: implementation already present; historical report records 102 passing tests and one exact local H3 T2V/native-audio evidence profile.
- Local runtime: ComfyUI 0.34.0 is available at `127.0.0.1:8188`, with H3 assets and no Wan weights. R2V/I2V/FLF/voice/lip-sync behavior is not presumed from node metadata.
- Frozen input hashes are recorded in `docs/triple-aaa-quality-bar-r1.json`.

## Architecture decisions

1. Preserve `vge_core.py` as the canonical planning/state owner; add a focused `vge_quality.py` for evidence contracts, continuity scorecards, transitions, re-anchors, FLF, semantic checks and bounded repair instead of scattering those invariants across CLI code.
2. Keep deterministic media heuristics in `vge_media.py`; they report observable bytes/metadata only and do not infer identity, physics, emotion or lip-sync.
3. Extend runtime discovery/fingerprinting only at the ComfyUI boundary; profiles remain feature-scoped and immutable by revision.
4. Keep production evidence separate from the installable Skill payload and from control-plane state.

## Work streams

1. Audit and freeze the bar (this plan, scout reports, baseline and fingerprints).
2. Implement deterministic quality contracts and CLI surface.
3. Complete runtime/profile/provenance boundaries and local capability evidence.
4. Add docs, traceability, maturity/release matrix and distribution evidence.
5. Add regression, fixture, metamorphic/property-like, integration, portability and media tests.
6. Run bounded local probes/inspection where safe; record NOT_RUN/UNKNOWN/BLOCKED honestly elsewhere.
7. Run architectural challenge, fresh independent critic and final release report.

## Verification gates

- `GATE-AUDIT`: frozen bar, baseline and limitations exist.
- `GATE-CONTRACTS`: known-good and known-bad deterministic quality contracts pass.
- `GATE-SOFTWARE`: full unit/integration suite, quick validation, package links and distribution CRC pass.
- `GATE-RUNTIME`: local discovery/preflight and exact capability probes are bound to immutable artifacts; unavailable features stay blocked.
- `GATE-MEDIA`: deterministic media QA and local artifact inspection have evidence-bound status.
- `GATE-ARCHITECTURE`: ownership/dependency direction, progressive disclosure and traceability are reviewed.
- `GATE-CRITIC`: fresh-context critic accepts the frozen bar and current evidence without mutating the repository.

## Active action

<!-- engineering-framework: completed_action_id=AAA-BUILD-01 -->

### AAA-BUILD-01 — Implement and test quality contracts

State: DONE

Concrete steps:

1. Add `vge_quality.py` with typed, deterministic validators and decision records.
2. Add media heuristics and runtime discovery/fingerprint extensions without changing historical artifacts.
3. Expose stable CLI commands and add fixtures/tests for good, bad and unknown evidence.
4. Run focused tests, then full regression.

Exit evidence: current source files, focused and full test output, `verification/software-triple-aaa-r13.json`, portable ZIP/CRC and external-CWD checks, R2V provenance enrichment, and the independent critic record in `verification/triple-aaa-independent-critic-r5.md`.

Closure decision: `READY_WITH_RISKS`. Architecture and deterministic verification pass in scope; production semantic/continuity evidence, long-form ladder cases, a second provider/model, and a clean post-hardening fresh critic remain outside the accepted boundary.

## Recovery protocol

If interrupted, read this plan and `.agent/state.json`, run `git status --short`, inspect the active marker, and continue from the smallest incomplete concrete step. Never rewrite historical `.gauntlet/` evidence or delete user files.

## Final handoff format

`docs/triple-aaa-final-report.md` must state `TRIPLE_AAA_CANDIDATE`, `READY_WITH_RISKS`, `PARTIAL` or `BLOCKED`, with independent architecture/verification/production scores, exact evidence paths and hashes, all unknowns, remaining gaps, and the next safe action.
