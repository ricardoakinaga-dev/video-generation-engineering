# ADR-007: Separate script, performance, audio, and lip-sync

Status: ACCEPTED

Context: A model may support text, image, audio-driven motion, speech, or muxing in different combinations; text alone does not establish timing or mouth behavior.

Decision: Track script, visual performance, audio layers, and lip-sync as separate contracts with explicit synchronization and fallback.

Alternatives Considered: Assume native audiovisual generation; encode dialogue only as prompt prose.

Consequences: The plan can use external audio or a separate lip-sync pass; more artifacts and timing metadata are required.

Risks: Assembly complexity and voice/provenance risk increase; safety and audio gates remain explicit.

Validation Evidence: [`directing.md`](../directing.md), [`safety-boundaries.md`](../safety-boundaries.md), `G-004`, `G-011`.
