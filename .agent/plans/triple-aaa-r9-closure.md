# Triple-AAA Evidence Closure R9 — state-of-the-art hardening

<!-- engineering-framework: active_action_id=VGE-TRIPLE-AAA-R9:PRODUCTION-EVIDENCE-BOUNDARY -->

## Purpose

Implement the three user-supplied Triple-AAA Evidence Closure prompts against the existing brownfield Skill, preserving the architecture and every historical failure while strengthening only demonstrated evidence, acceptance, portability and release-accounting gaps. The result must be truthful: local structural quality can be proven independently from audiovisual production.

## Source and frozen bar

- User sources: `/home/ricardo/.codex/attachments/dab130ba-0490-4d7a-8327-f4eefd4c9f6a/pasted-text-{1,2,3}.txt`
- Repository copies: `docs/master-prompt-triple-aaa-evidence-closure-20260909-part-{1,2,3}.txt`
- Frozen bar: `docs/triple-aaa-quality-bar-r9.json`
- Original source hashes: part 1 `60e20d753558dc877f1477ee0625dc7f9a22fd9d6068dbf519c14199d3be4b2c`; part 2 `7de047adb66fee247330629e2c5ed07b57d5b9d5739089468a4921a04ac9d1f3`; part 3 `311bbb58ad4ed8c2a60aee8539bd3f7a122ad7366361ab240f9233ecc19ebf65`.
- Repository copies preserve parts 1–2 byte-for-byte; part 3 has one final LF added by `apply_patch`, recorded explicitly in the bar.

## Current classification

- Project: BROWNFIELD; work mode: FEATURE with audit/release review overlays; lifecycle: AUDIT; activity: VERIFY; tier: T3_SYSTEM; risk: MEDIUM; blast radius: SYSTEM.
- Authorization: local repository implementation and safe read-only runtime inspection. No new paid call, upload, publication, voice/likeness transfer, large model download or destructive queue mutation is authorized by this request.
- Baseline: `tools/verify.py` PASS, 157 tests PASS, no failures/errors/skips, with current R9 prompt copies, structural hardening and release tooling recorded. Existing R8/R6 audiovisual boundary remains historical/current evidence to re-audit, not automatic PASS.

## Quality bar and gates

1. Preserve the five truth layers and fail-closed semantic/oracle boundaries.
2. Close P0 structural/evidence regressions before adding production scope.
3. Keep LF-001, repair, FLF, LF-002, LF-003 and second-adapter claims at the strongest status current evidence supports.
4. Produce a current matrix, maturity report, 22-category scorecard, complete closure report, fresh final critic and post-critic portable distribution.

## Concrete Steps

1. [VGE-TRIPLE-AAA-R9:PRODUCTION-EVIDENCE-BOUNDARY] — obtain authorized runtime and editorial observations for the remaining real Triple-AAA acceptance boundary. **BLOCKED — external authority and production evidence required.**
2. [VGE-TRIPLE-AAA-R9:BASELINE-AUDIT] — complete the fresh baseline, reconcile current control state, and record the bar/candidate fingerprint before implementation. **DONE.**
3. [VGE-TRIPLE-AAA-R9:CONTRACT-HARDENING] — implement only evidence-backed gaps in production acceptance, compiler differential, release packaging and their regressions. **DONE.**
4. [VGE-TRIPLE-AAA-R9:REPORTING] — update current capability/maturity/score/report artifacts with exact statuses, claims, blockers and rejected overengineering. **DONE.**
5. [VGE-TRIPLE-AAA-R9:FULL-VERIFY] — rerun focused checks, full regression, compile, Skill validation, offline package checks, external-CWD smoke and scans. **DONE.**
6. [VGE-TRIPLE-AAA-R9:FINAL-CRITIC] — freeze the candidate and obtain a fresh non-inherited read-only critic with a reviewer-owned fingerprint and mutation sentinel. **DONE.**
7. [VGE-TRIPLE-AAA-R9:DISTRIBUTION] — build and validate a new portable distribution from the frozen candidate and bind it to the critic/fingerprint. **DONE.**
8. [VGE-TRIPLE-AAA-R9:HANDOFF] — record the final verdict, preserve blockers, commit and push only the integrated verified candidate. **DONE.**

## Architecture and ownership

Keep canonical planning in `vge_core.py`, deterministic quality contracts in `vge_quality.py`, runtime identity/guards in `vge_runtime.py`, media checks in `vge_media.py`, evidence/provenance in `vge_evidence.py`, provider authorization in `vge_provider.py`, and CLI routing in `vge.py`. A small repository release helper is allowed only if it closes the demonstrated reproducibility/scan gap and does not enter the portable Skill payload.

## Implementation hypotheses

- Production acceptance must bind every semantic observation to the artifact's shot lineage and successful attempt; otherwise a caller could supply a semantically complete observation for the wrong shot.
- Prompt adapter differential must expose preserved canonical-state identity explicitly; section-name preservation alone is insufficient evidence of semantic invariance.
- Portable distribution should have one deterministic, fail-closed builder/validator instead of relying on undocumented shell history.

## Validation strategy

- Focused: new known-bad tests for observation shot/attempt lineage, adapter canonical-state invariance, deterministic package scans/build and unsafe package members.
- Regression: `PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 python3 -B -m unittest discover -s tests -v`; `PYTHONDONTWRITEBYTECODE=1 python3 -B tools/verify.py --output <new verification record>`.
- Static/runtime-safe: compileall or equivalent no-bytecode syntax check, Skill doctor/quick validation, import DAG, docs/link checks, secret/credential/weight/private-media/absolute-path scans, external-CWD CLI help→prepare→validate→compile smoke.
- Audiovisual: no new generation submission until a fresh explicit resource/authority boundary exists; current production remains evidence-scoped and cannot be promoted by structural changes.

## Recovery and stop rules

Preserve current and historical R1–R8 artifacts. A runtime timeout remains tied to its original queue ID; do not resubmit automatically. A failed/partial/unknown artifact remains immutable. If the fresh critic is unavailable, record incomplete independent review and cap the verdict; if it rejects, classify findings and perform one bounded fix/retest cycle per changed hypothesis. Stop at a truthful READY_WITH_RISKS/PARTIAL/BLOCKED verdict when an external production or authority blocker remains.

## Decisions

- Do not redesign the canonical model or add speculative model adapters/patterns.
- Do not intentionally corrupt a successful media artifact to manufacture a repair case.
- Do not convert mechanical media PASS, node availability, prompt quality, test PASS or local runtime health into audiovisual production acceptance.
- Reject score averaging as a way to hide any required P1–P6 blocker.

## Expected final artifacts

- Current report: `docs/triple-aaa-final-evidence-closure-r9.md`.
- Matrix: `docs/capability-matrix-r9.md`.
- Diagnostic scorecard: `docs/triple-aaa-scorecard-r9.md`.
- Baseline/verification records: `verification/software-triple-aaa-r9.json`, `verification/docs-current-r9.json`, `verification/candidate-fingerprint-r9-*.json`, `verification/triple-aaa-independent-critic-r9.md`, `verification/distribution-triple-aaa-r9.json`.
- Distribution: `dist/video-generation-engineering-triple-aaa-r9.zip`.

## Completion signal

The integrated repository has the preserved prompts, frozen R9 bar, current evidence report/matrix/maturity/scorecard, complete regression evidence, a fresh critic result or an explicit blocked/incomplete record, and a distribution whose hashes match the frozen candidate. Production claims remain limited to observed artifacts and valid oracles.
