# Safety, rights, and authorization boundaries

## Purpose

Define where the director must pause, minimize data, require evidence, or refuse an execution path. This is an architecture boundary for the current package, not a replacement for provider policy, legal review, or a general content policy.

## Authority discipline

The future Skill must not invent platform rules. Provider-specific restrictions are resolved from the current provider's official policies and capabilities at implementation time. The design uses general controls supported by authoritative guidance: moderation and human oversight, adversarial testing, and communicating limitations are recommended in the [official OpenAI safety guidance](https://developers.openai.com/api/docs/guides/safety-best-practices). Provenance checks are evidence about known signals, not proof of authenticity; the [official OpenAI content-provenance reference](https://developers.openai.com/api/reference/python/resources/content_provenance_checks/methods/create) states that missing signals do not establish that content is not generated.

## Boundary matrix

| Risk area | Intake requirement | Default behavior | Human boundary |
|---|---|---|---|
| Real-person likeness | identity/reference provenance and consent status | mark unknown/restricted; do not assume permission | block execution until authorized |
| Real-person voice | voice source, identity, consent, provider support | separate voice/audio path; no cloning assumption | explicit approval and provider-policy check |
| Impersonation/deception | stated audience and fictional/disclosure context | propose fictionalized or labeled treatment | review before publication/use |
| Copyrighted character/brand | source, license/permission, transformation intent | preserve reference status; do not claim clearance | rights review |
| Sexual/minor content | age/sexualization ambiguity and applicable policy | stop and apply current authoritative policy | do not proceed on inference |
| Unsafe physical action | real-world harm or dangerous imitation risk | preserve safe planning boundary; propose non-harmful alternative | human/safety review when material |
| Private data | PII/medical/location/voice metadata relevance | minimize, redact, or exclude unrelated data | review when exposure is possible |
| Provider restriction | current capability/policy evidence | mark `UNKNOWN`/`BLOCKED`; do not route around it silently | user chooses compliant alternative |
| External side effect | upload, paid call, queue, publish, delete | plan only | explicit authorization and tool boundary |

## Likeness and reference contract

```yaml
provenance_gate:
  asset_id: ref_person_001
  likeness_or_voice: true
  source: creator_supplied
  rights_status: UNKNOWN
  consent_status: UNKNOWN
  intended_use: identity_reference
  required_action: HUMAN_REVIEW_REQUIRED
  execution_allowed: false
```

The system separates provenance metadata from legal determination. `CONFIRMED` means the record or source confirms the stated fact; it does not mean the project is legally cleared. A user-supplied assertion can be recorded as an input claim, but high-risk execution still requires the declared review boundary.

## Content handling principles

1. Collect only the reference properties needed for the scene.
2. Keep unrelated private details out of prompts, logs, and artifacts.
3. Preserve asset hashes and provenance status without copying sensitive media into documentation.
4. Make external transfer, paid generation, publication, and deletion explicit actions requiring authorization.
5. Give reviewers enough source context to verify a decision and its limitation.
6. Treat absence of a provenance signal as `UNKNOWN`, never as proof of authenticity or permission.

## Safety architecture

Safety checks are modular stages around the canonical planner:

```text
intake risk → policy/provider lookup → reference/provenance gate
→ plan safety gate → optional generation moderation → human review
→ provenance/disclosure at assembly
```

Safety does not pollute every prompt with generic exclusions. A rights issue blocks a reference path; an anatomy issue becomes a constraint/QA assertion; a provider issue blocks capability negotiation. Each route remains explainable.

## Adversarial and escalation behavior

The adversarial fixtures in [`adversarial-scenarios.md`](adversarial-scenarios.md) cover identity swaps, deceptive media, private data, unsupported features, and overloaded action. The expected outcomes are `ASK`, `BLOCK`, `DEGRADED`, `SPLIT`, or `HUMAN_REVIEW_REQUIRED`, with preserved intent and a reason.

## Failure modes

| Failure | Signal | Repair |
|---|---|---|
| Consent assumed | unknown status treated as permission | block and request evidence |
| Policy invented | unsupported provider rule asserted | cite authoritative source or mark unknown |
| Provenance overclaimed | missing signal treated as authenticity | downgrade to unknown |
| Safety bypassed by adapter | blocked intent routed to another provider | carry boundary through negotiation |
| Private data echoed | unrelated identifying details appear in prompt/log | minimize/redact and review |

## Open questions

Provider-specific policy connectors, disclosure format, and organizational approval roles remain open. They must be resolved before external execution, not before a plan-only Phase 1 skeleton; the staged queue assigns that boundary to `OQ-B-003` and keeps artifact oracles/profile confirmation at their later phases. See [`open-questions.md`](open-questions.md).
