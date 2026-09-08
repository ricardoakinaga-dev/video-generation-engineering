# ADR-004: Explicit continuity state and shot graph

Status: ACCEPTED

Context: Long-form and multi-shot work fails when each shot is an independent prompt or when planned state is confused with observed output.

Decision: Represent shots as a dependency graph with domain-level state deltas, accepted anchors, and separate desired/planned/observed truth.

Alternatives Considered: Flat shot list; recursive last-frame propagation; monolithic long prompt.

Consequences: Boundary validation and targeted repair become possible; graph/state bookkeeping is necessary.

Risks: Bad observations can propagate if acceptance gates are weak; the observation contract and reset strategy limit this.

Validation Evidence: [`state-model.md`](../state-model.md), [`continuity-engine.md`](../continuity-engine.md), `G-003`, `G-008`, `G-009`.
