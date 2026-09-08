# Failure taxonomy and evaluation strategy

Evaluation measures whether the director preserved intent, feasibility, and continuity—not merely whether a video file was produced. Every failure has a detection oracle, a mitigation, and a prevention signal.

## Document contract

This document owns the failure vocabulary, fixture expectations, oracle classes, and repair loop. The compact table is a routing index and the expanded catalog is the seven-field failure record; they must remain ID-consistent. Examples are the golden, known-bad, and adversarial cases below. A missing cause, detection, prevention, mitigation, repair, or eval is a failure; provider/media limitations remain explicitly unrun rather than implied to pass. Canonical entity/state semantics stay in [`contracts.md`](contracts.md) and are linked instead of duplicated.

## Contents

- [Failure taxonomy](#1-failure-taxonomy)
- [Expanded failure catalog](#11-expanded-failure-catalog)
- [Golden cases and evaluation record](#2-golden-cases)
- [Known-bad fixtures](#4-known-bad-fixtures)
- [Repair loop and metrics](#5-repair-loop)
- [Evaluation tiers and categories](#7-evaluation-tiers)
- [Open questions and related documents](#9-open-questions-and-related-documents)

## 1. Failure taxonomy

| ID | Failure | Detection | Mitigation | Prevention signal |
|---|---|---|---|---|
| F-INT-01 | Ambiguous intent | Missing actor/action/outcome or conflicting directives | Ask, branch, or mark unresolved | Intent completeness gate |
| F-REF-01 | Reference misassignment | Asset is linked to wrong entity or purpose | Rebind and invalidate dependent plans | Reference retention matrix |
| F-REF-02 | Reference retention failure | Critical property is absent or drifts across dependent shots | Re-anchor, split, or human review | Identity continuity gate |
| F-SCENE-01 | State contradiction | Entry state differs from prior exit state | Repair delta or split transition | State graph validation |
| F-SHOT-01 | Overloaded shot | Too many actors, actions, or dependencies for profile | Split coverage or downgrade | Complexity routing |
| F-PHY-01 | Impossible contact | Hands, object, or body geometry cannot satisfy contact graph | Reframe, split, or reject | Interaction plausibility gate |
| F-CAM-01 | Camera discontinuity | Axis, screen direction, or movement phase breaks | Add transition, reframe, or accept intentional break | Camera continuity gate |
| F-TEMP-01 | Temporal jump | Action phase or object state skips without cause | Add bridge shot or reset state | Temporal continuity gate |
| F-DLG-01 | Dialogue ambiguity | Speaker, listener, timing, or reaction unresolved | Reassign, split, or use voiceover | Dialogue coherence gate |
| F-LIP-01 | Lip-sync mismatch | Phoneme timing or visible mouth motion does not align | Separate audio/lip-sync pass | Lip-sync feasibility gate |
| F-AUD-01 | Audio-cause mismatch | Sound event lacks visible or declared cause | Re-time, replace, or mark non-diegetic | Audio-event coherence gate |
| F-MOD-01 | Capability mismatch | Workflow/model cannot accept required mode or input | Negotiate another profile or block | Model compatibility gate |
| F-EXE-01 | Workflow invalid | Missing node, asset, type, or route | Repair graph/preflight | Execution completeness gate |
| F-QA-01 | Unsupported confidence | Claim is stronger than evidence | Downgrade status or request review | Evidence status convention |
| F-QA-02 | Stale or self-approved evidence | Fingerprint mismatch, missing independent critic, or stale round | Rerun fresh critic and retest | Gauntlet process gate |
| F-DOC-01 | Documentation ownership gap | Unresolved owner/link in index or traceability | Assign owner or consolidate | Documentation review |
| F-DOC-02 | Cross-document contradiction | Consistency audit finds conflicting status, threshold, or entity meaning | Choose owner, update links, record ADR | Integration review |
| F-DOC-03 | Premature production artifact | Forbidden file or external side effect appears | Stop phase and record boundary decision | Scope audit |
| F-PKG-01 | Context bloat or over-fragmentation | Routing/ownership review finds unnecessary load or empty split | Narrow route or consolidate | Progressive-disclosure review |
| F-OBS-01 | Opaque or leaking diagnostic | Diagnostic audit finds missing evidence refs or redaction failure | Add concise evidence or redact | Observability review |
| F-GOV-01 | Provenance/consent gap | Reference or output lacks required rights record | Block or obtain approval | Rights constraint |

Failures may have multiple causes. Record the earliest preventable cause and any downstream symptoms separately so evals do not reward a late workaround as a clean plan.

## 1.1 Expanded failure catalog

The following catalog expands the compact taxonomy into the required failure contract: failure, cause, detection signal, prevention, mitigation, repair, and eval. Shared gates may be reused; the failure-specific signal must remain visible.

| ID | Failure | Cause | Detection | Prevention | Mitigation | Repair | Eval |
|---|---|---|---|---|---|---|---|
| F-INT-01 | Ambiguous intent | actor, action, outcome, or directive is missing/conflicted | required field or contradiction is detected | intent completeness gate and labelled unknowns | ask or branch | update `SceneIntent` without inventing a hard choice | G-001/ADV-001 |
| F-REF-01 | Reference misassignment | asset is mapped to the wrong entity/property | role/property map conflicts with input | reference inventory and retention matrix | rebind or isolate asset | repair reference plan and invalidate dependents | G-007/ADV-001 |
| F-REF-02 | Reference retention failure | critical property is omitted from dependent shot state | locked property is absent or drifts in observation | explicit retention policy and anchor scope | re-anchor or human review | restore canonical reference and recheck affected shots | G-005/ADV-002 |
| F-SCENE-01 | State contradiction | planned entry state differs from accepted dependency exit | boundary comparison reports incompatible values | state delta and topological continuity check | add transition or split | repair smallest state owner | G-008/ADV-008 |
| F-SHOT-01 | Overloaded shot | participant/action/dependency load exceeds coverage/profile budget | complexity vector and feasibility check exceed threshold | risk-shaped shot routing | split or downgrade | create a causal shot DAG and preserve state edges | G-010/ADV-004 |
| F-PHY-01 | Impossible contact | proximity, force, or geometry is asserted without a feasible path | contact graph or media review fails | motion primitives and contact checkpoints | reframe or split | repair contact phases and end-state cause | G-002/G-006/ADV-003 |
| F-ID-01 | Identity drift | weak/recursive reference conditioning | face/mark mismatch | retention matrix and anchor | re-anchor/regenerate | reset from canonical reference | G-005 |
| F-ID-02 | Face drift | visibility, pose, or profile limit | face comparison fails | profile risk and coverage | close-up or alternate profile | split face-visible shot | G-005 |
| F-ID-03 | Wardrobe drift | transient state omitted or model variation | color/garment mismatch | persistent wardrobe state | reference/reframe | repair state ledger | G-005 |
| F-AN-01 | Anatomy/hand/foot error | overloaded motion or weak contact | malformed limb/ground contact | primitives and targeted constraints | shorten/reframe | split contact/result | G-002/G-011 |
| F-AN-02 | Animal anatomy error | species behavior treated as human | species/limb mismatch | animal-specific profile/risk | simplify behavior | human review or alternate coverage | G-002/G-003 |
| F-ENT-01 | Duplicate subject | ambiguous count/role | extra actor/animal/vehicle | entity inventory | crop/reject | clarify entity graph | G-004/G-012 |
| F-OBJ-01 | Object morphing | geometry not retained | shape/mark change | object reference | replace shot | canonical object anchor | G-006/G-007 |
| F-VEH-01 | Vehicle morphing | model/geometry conflict | silhouette/mark change | vehicle geometry anchor | cut to detail/replace | rebind reference/profile | G-008/G-009 |
| F-VEH-02 | Wheel/road error | motion state omitted | static wheels, sliding, no contact | vehicle physics constraints | change coverage | add wheel/road checkpoint | G-009 |
| F-CON-01 | Contact failure | proximity mistaken for contact | no shared contact point | contact graph | insert contact shot | revise phases/ownership | G-002/G-006 |
| F-CON-02 | Collision/intersection | incompatible paths/occlusion | body/object intersects | geometry/trajectory plan | reframe/split | repair spatial delta | G-003/G-008 |
| F-WLD-01 | Environment drift | anchors not carried | recurring background changes | Scene Bible/world anchors | reset keyframe | update anchor scope | G-005/G-009 |
| F-WLD-02 | Lighting drift | time/weather/light state omitted | shadow/exposure direction changes | world lighting state | cut/regrade/review | add transition or constraint | G-007/G-009 |
| F-CAM-01 | Camera discontinuity | axis/movement phase absent | eyeline/screen direction break | camera continuity plan | motivate/reframe | add transition shot | G-002/G-005 |
| F-TEMP-01 | Temporal jump | recursive degradation or hidden state | frame/state comparison | segment/re-anchor | shorten/reset | repair boundary delta | G-009 |
| F-DLG-01 | Dialogue timing error | script lacks intervals/turns | speaker/line mismatch | dialogue contract | split/use VO | retime/reassign | G-004/G-011 |
| F-LIP-01 | Lip-sync failure | unsupported audio/face timing | mouth/phoneme mismatch | capability check | separate lip-sync | alternate profile/post-pass | G-004/G-011 |
| F-AUD-01 | Voice/audio drift | identity/source not retained | voice or mix mismatch | audio identity/provenance | external track | replace/approve | G-011 |
| F-PER-01 | Reaction ordering error | no processing beat | reaction before stimulus | stimulus→reaction→response | add pause/cut | repair beat graph | G-004/G-011 |
| F-MOD-01 | Model mismatch | required mode/input not supported | compatibility report blocked | profile negotiation | alternate/degrade | update profile/plan | G-008/G-012 |
| F-PRM-01 | Prompt contradiction | canonical sections compiled inconsistently | mapping diff/semantic review | compiler mapping | recompile | repair canonical owner | G-007 |
| F-CON-03 | Overconstraint | universal negative list | conflicting/low-feasibility plan | risk-shaped selection | remove optional controls | reprioritize constraints | G-001/G-012 |
| F-CON-04 | Underconstraint | material risk omitted | missing assertion/oracle | risk vector | add targeted constraint | update selection rule | G-008/G-010 |
| F-REF-03 | Reference conflict | multiple sources lack precedence | conflict record | role/property mapping | ask or preserve branches | review precedence | G-007/G-012 |
| F-EXE-01 | Workflow invalid | missing node, asset, type, route, or binding | preflight/graph validation fails | runtime discovery and typed binding | choose compatible workflow or block | repair graph/profile/input contract | G-009/ADV-010 |
| F-QA-01 | Unsupported confidence | a plan or source claim is stronger than evidence | evidence status/source audit fails | explicit statuses and observation contract | downgrade or request review | add source/probe or mark unknown | DOC-003/DOC-014 |
| F-GOV-01 | Provenance/consent gap | permission assumed | unknown/restricted status | intake boundary | block/review | obtain evidence or remove asset | ADV-013 |
| F-DOC-01 | Documentation ownership gap | a concept is split across unlinked owners | broken index/traceability link | canonical ownership table | consolidate/link | assign one owner | documentation review |
| F-DOC-02 | Cross-document contradiction | duplicated vocabulary or threshold drifts | consistency audit | source hierarchy and ADR | pause implementation | update owner and dependents | integration review |
| F-DOC-03 | Premature production artifact | documentation boundary ignored | forbidden production file or side effect | Phase 0 scope guard | stop phase | remove unauthorized artifact only with explicit approval | scope audit |
| F-QA-02 | Stale/self-approved evidence | critic saw a different artifact or builder self-approves | fingerprint mismatch or missing fresh critic | sealed packets and mutation sentinel | invalidate result | rerun fresh critic and retest | GAUNTLET-001 |
| F-PKG-01 | Context bloat or over-fragmentation | routing loads irrelevant or empty resources | simple-scene route or ownership audit fails | progressive disclosure matrix | narrow/consolidate | update route and index | G-001/DOC-022 |
| F-OBS-01 | Opaque or leaking diagnostic | evidence is absent or sensitive metadata is echoed | diagnostic/redaction review | summary/detail/audit levels | redact or enrich evidence | repair observability contract | DOC-024/ADV-015 |

No failure row claims that a prompt phrase can enforce the outcome. Prevention is a plan/control decision; detection is observation against an oracle; repair may still require regeneration or human review.

## 2. Golden cases

Golden cases are small, deterministic planning fixtures. They exercise the director before expensive generation.

| Case | Scenario | Expected behavior |
|---|---|---|
| G-001 | Simple cinematic portrait | CINEMATIC plan; identity/reference assumptions are explicit; no unnecessary specialist loading |
| G-002 | Veterinarian examining a dog | Human/animal interaction, contact, anatomy, and reaction are bounded |
| G-003 | Human/animal interaction | Species-aware motion and contact graph are explicit |
| G-004 | Two-character conversation | Speaker/listener, turn-taking, gaze, reaction, and mouth-window rules are explicit |
| G-005 | Walking and talking | Action/dialogue split, camera continuity, and state carry are explicit |
| G-006 | Person handing an object | Contact phases, ownership transfer, and visible result are explicit |
| G-007 | Product commercial | Product/reference retention, camera purpose, audio/event, and brand risks are explicit |
| G-008 | Person entering a vehicle | Approach/contact/articulation/entry state and vehicle geometry are explicit |
| G-009 | Automotive driving sequence | Vehicle/road mechanics, camera, environment, and continuity are bounded |
| G-010 | 30-second commercial | Beat timeline, shot graph, assembly, and re-anchor policy are explicit |
| G-011 | 60-second dialogue/action commercial | Dialogue, performance, audio/lip-sync, interaction, and recovery are separated |
| G-012 | Multi-reference high-complexity scene | Reference precedence, complexity escalation, profile negotiation, and human gates are explicit |

## 3. Evaluation record

```yaml
evaluation:
  eval_id: eval_G-004_v1
  case_id: G-004
  input_ref: evals/golden/G-004.yaml
  expected:
    required_requirements: [R-SHOT-03, R-SHOT-04, R-QA-02]
    forbidden_behaviors:
      - implicit ownership transfer
      - unvalidated contact claim
  oracles:
    - type: structural
      assertion: dialogue.turns is non_empty and every turn declares speaker and listener
    - type: structural
      assertion: every dialogue interval declares start, end, line, and active speaker
    - type: semantic
      assertion: reaction follows the stimulus and the next turn follows the completed line
    - type: review
      assertion: only the active speaker has sustained articulation; listener gaze and reaction are observable
  result: NOT_RUN
```

The corresponding transfer case uses different oracles and must not be substituted for the conversation case:

```yaml
evaluation:
  eval_id: eval_G-006_v1
  case_id: G-006
  input_ref: evals/golden/G-006.yaml
  expected:
    required_requirements: [R-SHOT-03, R-SHOT-04, R-DIR-02]
    forbidden_behaviors:
      - ownership change inferred from proximity alone
      - reaction before visible transfer
  oracles:
    - type: structural
      assertion: interaction.contact_points is non_empty
    - type: structural
      assertion: state_delta.after.object_owner is declared and differs from before.owner
    - type: review
      assertion: contact, release, and recipient reaction are visibly ordered
  result: NOT_RUN
```

Oracles are divided into structural, semantic, runtime, media, and human-review classes. A structural pass does not prove visual quality. A generated artifact pass does not prove the plan was correct. Results keep those dimensions separate.

## 4. Known-bad fixtures

Known-bad fixtures must fail for the invariant they intentionally violate. They prevent a planner from receiving credit for producing a polished-looking but unsafe or incoherent plan.

| Fixture | Intentional violation | Expected result | Gate/oracle |
|---|---|---|---|
| KB-001 | Four dependent shots use independent prompts with no identity state or retention plan | `BLOCKED` or `REVISION_REQUIRED` | QG-02/QG-05; identity continuity |
| KB-002 | FLF is selected for a profile whose end-frame support is `UNKNOWN` | `BLOCKED` | QG-15; capability intersection |
| KB-003 | G-004 listener is directed to mouth the active speaker's full line | `REVISION_REQUIRED` | QG-10/QG-11; dialogue speaker/timing oracle |
| KB-004 | G-006 ownership changes from proximity without contact/release evidence | `REVISION_REQUIRED` | QG-08/QG-09; transfer contact/ownership oracle |
| KB-005 | Execution plan assumes a custom node without runtime discovery or evidence | `BLOCKED` | QG-17; workflow preflight |
| KB-006 | A likeness reference has no provenance or consent status | `BLOCKED` or human review | QG-02; rights/provenance constraint |

## 5. Repair loop

A failed gate follows the same observable loop:

```text
detect → explain → repair smallest owning layer → re-evaluate → recompile
```

The repair record names the failed gate, evidence, owner, changed fields, preserved fields, new risk, and next oracle. If the repair weakens a hard requirement, the plan becomes `DEGRADED` or `BLOCKED` and requests a human decision; it does not silently pass.

## 6. Metrics

The initial scorecard tracks:

- requirement coverage and traceability completeness;
- unresolved critical fields per plan;
- capability mismatch rate;
- state contradiction rate;
- identity-retention pass rate on dependent shots;
- interaction/contact plausibility pass rate;
- camera and temporal continuity pass rate;
- dialogue speaker/timing consistency;
- audio-event alignment;
- execution preflight error rate;
- artifact provenance completeness;
- human-review override and waiver rate.

Metrics are reported with confidence and sample size. A plan that avoids difficult cases by returning generic failures must not score as successful; blocked outcomes are evaluated against the expected case behavior.

## 7. Evaluation tiers

1. **Static contract tests** validate schemas, invariants, lifecycle transitions, and requirement IDs.
2. **Golden planning tests** validate deterministic parsing, routing, state deltas, and adapter negotiation.
3. **Workflow dry runs** validate graph binding and runtime preflight where a ComfyUI instance exists.
4. **Artifact tests** inspect duration, frames, audio, metadata, and selected visual/continuity assertions.
5. **Human review** evaluates story, performance, aesthetics, plausibility, and material deviations.

The system must publish which tiers ran. “Validated” without a tier is not a meaningful status.

## 8. Evaluation categories

| Category | What it tests | Primary oracle class | Example evidence |
|---|---|---|---|
| Unit-like contract evals | schemas, statuses, invariants, stable IDs, precedence | deterministic structural | valid/invalid state transitions |
| Scenario evals | end-to-end planning behavior for representative scenes | structural + semantic | G-001 through G-012 |
| Adversarial evals | graceful ask/block/degrade/split/review behavior | semantic + safety/human review | ADV-001 through ADV-017 |
| Regression evals | previously passing cases after a rule/profile change | deterministic fixture/diff | frozen golden subset and bar hash |
| Long-form continuity evals | state propagation, anchors, assembly, recovery | structural + media + human | G-009/G-011/G-012 at 30–120s bands |
| Model-adapter evals | capability intersection, prompt mapping, parameter binding | deterministic profile/compatibility + runtime when available | profile fixtures and compatibility reports |

Scoring remains gate-first. A categorical score may prioritize repairs, but it cannot average away a failed critical gate or turn missing evidence into a pass.

## 9. Open questions and related documents

The implementation still needs fixture storage, oracle interfaces, media-review thresholds, and a decision on how much human review can be standardized. These are tracked in [`open-questions.md`](open-questions.md). Shared entities and state are defined in [`domain-model.md`](domain-model.md), [`state-model.md`](state-model.md), and [`contracts.md`](contracts.md); gates are owned by [`acceptance.md`](acceptance.md); coverage is maintained in [`traceability.md`](traceability.md).
