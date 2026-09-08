# ADR-006: Long-form decomposition into validated segments

Status: ACCEPTED

Context: Short-video models and workflows have bounded temporal/context behavior; recursive extension can degrade identity and temporal detail.

Decision: Plan 30–120-second productions as causal shots/segments with timelines, re-anchors, state propagation, assembly, and recovery.

Alternatives Considered: One request at target duration; unbounded recursive frame extension.

Consequences: More assembly and QA steps, but errors are localized and repairable.

Risks: Cuts can reduce visual continuity; anchor and camera rules make the tradeoff explicit.

Validation Evidence: [`scene-and-continuity.md`](../scene-and-continuity.md), [`golden-scenarios.md`](../golden-scenarios.md), `DOC-016`.
