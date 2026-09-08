# ADR-001: Documentation-first Phase 0

Status: ACCEPTED

Context: The master prompt explicitly prohibits production Skill implementation while the architecture, evidence, and failure boundaries are still hypotheses.

Decision: Complete a reviewed documentation package before creating production Skill resources or executing media workflows.

Alternatives Considered: Start with `SKILL.md` and discover contracts during implementation; create all suggested files mechanically.

Consequences: Decisions are reviewable and traceable; implementation is delayed until contracts and gates are stable.

Risks: Documentation can become stale or over-broad without fixture pressure.

Validation Evidence: `DOC-001`/`DOC-027` bar checks, [`acceptance.md`](../acceptance.md), and Phase 0 scenario/eval records.
