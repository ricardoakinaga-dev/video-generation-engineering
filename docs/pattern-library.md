# Pattern library

Patterns are reusable planning structures, not guaranteed model recipes. A pattern is admitted only when it names its preconditions, invariant, failure modes, and evaluation path. The pattern may be adapted or rejected by the capability negotiator.

## Pattern contract

```yaml
pattern:
  pattern_id: PAT-INTERACTION-TRANSFER
  name: explicit_object_transfer
  intent: make a hand-to-hand transfer causally and spatially legible
  preconditions:
    - two participants are identified
    - the object is visible or its state is declared
  structure: [approach, orient, contact, transfer, release, reaction]
  invariants:
    - ownership before and after is explicit
    - contact points are declared
    - the result state is observable
  risks: [hand_geometry, occlusion, premature_reaction]
  fallbacks: [split_coverage, closeup_contact_shot, human_review]
  eval_cases: [G-006]
  status: PROPOSED
```

## Core patterns

| ID | Pattern | Use | Required invariants | Primary eval |
|---|---|---|---|---|
| PAT-IDENTITY-ANCHOR | Identity anchor | Recurring subject across shots | Retention properties and re-anchor boundary are explicit | G-005 |
| PAT-STATE-CARRY | Validated state carry | Dependent shot chain | Latest valid outgoing state in the active channel is inherited: planned in `PLAN_ONLY`, accepted observed across an executed artifact boundary; no channel promotion | G-008, G-010 |
| PAT-INTERACTION-TRANSFER | Explicit object transfer | Two-person handoff or possession change | Contact, ownership, gaze, and result | G-006 |
| PAT-ARTICULATED-OBJECT | Articulated object action | Door, latch, drawer, tool, vehicle control | Approach/contact/articulation/end state | G-008, G-009 |
| PAT-DIALOGUE-REACTION | Dialogue with reaction | Turn-taking scene | Active speaker, listener reaction, timing | G-004 |
| PAT-ACTION-DIALOGUE-SPLIT | Split action and dialogue | Dense simultaneous performance | No premature reaction or unsupported lip-sync | G-005, G-011 |
| PAT-CAMERA-AXIS | Motivated axis transition | Coverage crosses established screen direction | Motivation, transition shot, or explicit intentional break | G-004, G-009 |
| PAT-FLF-REANCHOR | Conditional FLF transition | Known endpoint transition | Profile confirmation, endpoint QA, reset strategy | G-008 |
| PAT-LONGFORM-SEGMENT | Long-form validated segments | Scene beyond stable model window | Shot graph, state propagation, periodic canonical anchors | G-010, G-011, G-012 |
| PAT-AUDIO-SEPARATE | Separate audio assembly | Native audio is absent or untrusted | Layered audio timeline and sync acceptance | G-011, G-012 |
| PAT-ANIMAL-CONTACT | Bounded animal interaction | Animal touches or follows a prop/person | Plausible motion, safe contact, observable result | G-002, G-003 |

## Pattern selection

The planner selects a pattern when its preconditions match the scene risk. It must report the selected pattern ID, any omitted precondition, the adapted structure, and the fallback. A pattern is not selected merely because a keyword appears in the request.

Patterns compose through contracts. For example, `PAT-IDENTITY-ANCHOR` and `PAT-STATE-CARRY` can combine for a multi-shot character sequence, while `PAT-ACTION-DIALOGUE-SPLIT` can replace a dense `PAT-DIALOGUE-REACTION` shot when lip-sync or motion risk is high.

## Pattern lifecycle

```text
PROPOSED → FIXTURED → EVALUATED → ADMITTED → DEPRECATED
```

`ADMITTED` means the pattern has at least one golden or known-bad case, a documented invariant, and a review procedure. Admission does not mean a model will satisfy the pattern automatically. A pattern becomes `DEPRECATED` when its assumptions no longer match current profiles or when evidence shows it increases failure risk.

## Failure modes and open questions

| Failure | Detection | Repair |
|---|---|---|
| Keyword-triggered pattern selection | preconditions are absent or unverified | return to the core planner and record the omitted precondition |
| Pattern hides a canonical decision | pattern restates or changes a contract | link to the owner or reject admission |
| Pattern is admitted without evidence | no fixture, invariant, or review procedure | keep `PROPOSED` and add the missing eval |

Open questions include the minimum fixture count for admission, whether templates outperform instructions, and how deprecated patterns are versioned. The canonical contracts are in [`contracts.md`](contracts.md); fixtures and failure oracles are in [`golden-scenarios.md`](golden-scenarios.md) and [`failure-and-evals.md`](failure-and-evals.md); package routing is in [`progressive-disclosure.md`](progressive-disclosure.md).
