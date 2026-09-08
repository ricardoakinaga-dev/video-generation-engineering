# ADR-009: Instructions first, deterministic tools only by evidence

Status: PROPOSED

Context: The official Skill format supports instructions plus optional scripts, while this project has no stable schema library, runtime, or artifact harness yet.

Decision: Start with concise procedural instructions and references; add a deterministic validator or template only when a repeated check is stable, public-boundary relevant, and fixture-backed.

Alternatives Considered: Build a parser/validator immediately; put all behavior in prose forever.

Consequences: Lower initial package complexity and easier host portability; structural checks may remain manual until Phase 1 evidence justifies code.

Risks: Manual omission risk in early implementation; known-good/known-bad fixtures are the entry criterion for tools.

Validation Evidence: [`progressive-disclosure.md`](../progressive-disclosure.md), [`proposed-skill-structure.md`](../proposed-skill-structure.md), official [Build skills documentation](https://developers.openai.com/codex/skills/).
