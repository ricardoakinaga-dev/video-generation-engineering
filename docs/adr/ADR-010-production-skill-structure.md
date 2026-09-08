# ADR-010: Minimal future production Skill structure

Status: PROPOSED

Context: The master prompt suggests many files, but official Skill guidance favors a required `SKILL.md` plus optional references/scripts/assets/metadata and progressive disclosure.

Decision: Use one concise procedural `SKILL.md`, a small set of conditional references, optional fixture-backed templates, an optional deterministic validator, and optional metadata.

Alternatives Considered: Ship the entire Phase 0 docs tree; create one resource per blueprint heading; make every helper a script.

Consequences: Less context overhead and clearer ownership; the production package must link to project evidence without copying all research.

Risks: Too much consolidation can hide a decision; file justification and scenario coverage are required before packaging.

Validation Evidence: [`proposed-skill-structure.md`](../proposed-skill-structure.md), [`progressive-disclosure.md`](../progressive-disclosure.md), `DOC-022`/`DOC-026`.
