# ADR-005: Prompt as a compiled view

Status: ACCEPTED

Context: Different models need different prompt density, order, controls, and input modes, while creative intent must remain stable.

Decision: Compile canonical sections into a human-readable prompt and then a profile-specific representation with omission/change mapping.

Alternatives Considered: Store only final prompt; duplicate independent prompt instructions per model.

Consequences: Compiler mappings and unsupported-field reporting are first-class; prompts are easier to adapt and audit.

Risks: Compilation may drop nuance or create false confidence; QG-16 and adapter observations address this.

Validation Evidence: [`contracts.md`](../contracts.md), [`model-adaptation.md`](../model-adaptation.md), `DOC-013`.
