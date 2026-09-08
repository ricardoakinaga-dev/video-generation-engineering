# ADR-008: Evidence-driven pattern library

Status: ACCEPTED

Context: Repeated interaction, dialogue, identity, and long-form structures can reduce omissions, but speculative templates create context bloat and false guarantees.

Decision: Admit a pattern only with preconditions, invariant, failure modes, fallback, and fixture/eval evidence.

Alternatives Considered: Copy every blueprint pattern into production; no reusable patterns.

Consequences: The library grows slowly and remains explainable; early Phase 1 may use prose.

Risks: Useful patterns may be delayed until fixtures exist; the roadmap allows incremental admission.

Validation Evidence: [`pattern-library.md`](../pattern-library.md), `G-001` through `G-012`, `DOC-022`.
