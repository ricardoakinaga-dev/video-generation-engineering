# Long-form validation package — R3

This document owns the production ladder evidence envelope. A fixture can be structurally complete while its production status remains `BLOCKED`, `NOT_RUN` or `PARTIAL`; structural completeness is never audiovisual proof.

## Evidence graph

Each accepted case retains hash-bound records for:

`intent → plan revision → Scene Bible → shot DAG → continuity ledger → prompt/adapter mapping → feature profile → workflow fingerprint → attempts → artifacts → observations → transitions → re-anchor/repair → audio/dialogue → assembly → human checkpoint → editorial decision`.

Every referenced file must exist at validation time and its declared hash must match. Attempts are immutable; retries are new attempt records. A boundary input is not accepted merely because it was copied from an earlier output.

## Ladder and structural fixtures

| Case | Duration | Structural fixture | Current production status |
|---|---:|---|---|
| LF-001 | 10–15s | Vehicle entry: approach, handle contact, door articulation, entry, seat, door close; 13 independent acceptance dimensions and seven contact phases | `BLOCKED` |
| LF-002 | 20–30s | Two-person dialogue, speaker/listener behavior, stimulus-processing-reaction-response, object ownership, five dialogue channels and causal audio | `BLOCKED` |
| LF-003 | 45–60s | Recurring characters, Scene Bible, continuity ledger, eight-beat dependent shot plan, vehicle/object interaction, repair and editorial checkpoint | `BLOCKED` |
| LF-004 | 90–120s | Optional branches, recovery checkpoints, provenance manifest and editorial gate | `NOT_RUN` |

The machine-readable fixtures are [`LF-001.json`](../verification/long-form/LF-001.json), [`LF-002.json`](../verification/long-form/LF-002.json), [`LF-003.json`](../verification/long-form/LF-003.json) and [`LF-004.json`](../verification/long-form/LF-004.json). They deliberately retain `fixture_status: STRUCTURAL_ONLY` and `production_evidence_complete: false` until real evidence is collected.

### Latest LF-001 runtime observation

The controlled local A003 run produced a real 5.1667-second S01 MP4 at 384×224, 124 frames and 24 FPS. Its immutable attempt/artifact chain, mechanical media QA, 12-dimension semantic observation, 14-dimension continuity scorecard and explicit non-run editorial boundary are [`LF-001-S01-attempt-003.json`](../verification/long-form/LF-001-S01-attempt-003.json), [`LF-001-S01-artifact-003.json`](../verification/long-form/LF-001-S01-artifact-003.json), [`LF-001-S01-media-qa-003.json`](../verification/long-form/LF-001-S01-media-qa-003.json), [`LF-001-S01-semantic-observation-003.json`](../verification/long-form/LF-001-S01-semantic-observation-003.json), [`LF-001-S01-continuity-scorecard-003.json`](../verification/long-form/LF-001-S01-continuity-scorecard-003.json) and [`LF-001-S01-editorial-acceptance-003.json`](../verification/long-form/LF-001-S01-editorial-acceptance-003.json). Media integrity is `PASS`; semantic and continuity status are `PARTIAL`; editorial acceptance is `NOT_OBSERVED`. Only `APPROACH` and `PRE_CONTACT` were observed. This advances evidence for S01 only and does not satisfy LF-001 production acceptance.

## Acceptance rule

`validate_long_form_case()` accepts `PASS` only when:

1. all required intent, plan, Scene Bible, shot graph, continuity, audio/dialogue and checkpoint references are immutable hash-bound records;
2. the canonical plan shot order exactly matches the case and the shot graph/continuity records bind that same order;
3. `production_evidence_complete` is true;
4. every attempt is `SUCCEEDED` and hash-bound;
5. every artifact is accepted, has a current media reference and matches its media hash;
6. every artifact has exactly one accepted semantic observation and every adjacent pair has an accepted transition validated by the canonical transition contract;
7. the assembly record is a strict ordered manifest bound to all source-shot hashes;
8. current final media QA is `PASS` and a separate six-dimension human editorial acceptance is `PASS`.

Placeholder paths, a bare `production_evidence_complete: true`, rewritten transition locators/hashes, weak oracles, duplicated observations or a missing final QA/editorial record fail closed. Duplicating one five-second file, concatenating unaccepted media, or asserting continuity from prompt text cannot satisfy a ladder case.

## LF-001 acceptance dimensions

The vehicle-entry case has exactly 13 independent obligations: subject identity, wardrobe, vehicle geometry, vehicle color, door state, subject position, hand contact, body collision, seat state, environment, light direction, screen direction and temporal order. Each must be observed separately; a mechanically valid MP4 is not evidence for these dimensions.

## LF-002 dialogue and audio obligations

The dialogue case keeps semantics, voice, performance, lip-sync and mix separate. The active speaker may articulate the line; the listener's processing/reaction must precede the response unless overlap is intentionally scripted. Object ownership changes require contact and release. The audio timeline accounts for dialogue, foley, ambience, room tone, vehicle, animal, music, transition, non-diegetic sound and silence.

## LF-003 continuity and repair obligations

The multi-shot case requires a Scene Bible with identity anchors, wardrobe, relationships, environment, time/light, persistent objects, voice identity, visual style, camera language and prohibited drift. The continuity ledger tracks identity, wardrobe, hair, pose, gaze, hand occupancy, object location/ownership, vehicle, environment, lighting, screen direction, camera geography, emotion, dialogue, audio and time. A repair must preserve immutable failed attempts and unaffected siblings, then reobserve all downstream dependents.

## Current boundary

The local H3 runtime now has one additional observed short T2V/native-audio S01 segment, alongside the earlier exact-scope T2V and `PARTIAL` R2V records. It still does not provide accepted LF-001: S02/S03, all seven contact phases, transitions, repair/re-anchor and a 10–15-second accepted chain are missing. Dialogue/lip-sync, FLF and LF-003 production evidence also remain unavailable. The correct status is therefore `BLOCKED`, not a synthetic PASS. See the [LF-001 evidence r2](../verification/long-form/LF-001-evidence-r2.json), [current capability matrix](capability-matrix-r3.md) and [current Triple-AAA closure report](triple-aaa-final-production-closure.md).
