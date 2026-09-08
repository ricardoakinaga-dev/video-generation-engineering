# ADR-002: Canonical scene model before prompts

Status: ACCEPTED

Context: Prompt text cannot own persistent identity, state transitions, references, or observed artifact evidence.

Decision: Normalize intent into a model-independent scene/domain representation; compile prompt views late.

Alternatives Considered: One prompt per shot; provider-specific JSON as the canonical source.

Consequences: Adapters can change without rewriting intent; contracts and state ledgers add planning work.

Risks: The representation may grow beyond useful decision value; progressive disclosure and fixture coverage constrain it.

Validation Evidence: [`domain-model.md`](../domain-model.md), [`contracts.md`](../contracts.md), `G-001` through `G-012`.
