# ADR-003: Model-agnostic core with versioned adapters

Status: ACCEPTED

Context: Model repositories, ComfyUI nodes, hosted APIs, and versions expose overlapping but non-identical capabilities.

Decision: Keep core intent/scene semantics provider-neutral; put syntax, limits, controls, evidence, and failure modes in versioned profiles.

Alternatives Considered: Hard-code Wan/ComfyUI behavior; treat model family marketing as an adapter contract.

Consequences: New profiles are additive; profile maintenance and revalidation are required.

Risks: Unknown capabilities can block useful work; explicit degraded fallbacks preserve honesty.

Validation Evidence: [`model-adaptation.md`](../model-adaptation.md), [`research.md`](../research.md), `DOC-003`/`DOC-014`.
