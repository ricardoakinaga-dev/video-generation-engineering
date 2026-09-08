# Progressive disclosure plan

## Purpose

Keep the Skill concise and context-efficient while ensuring that high-risk tasks load the guidance that materially changes their decisions. The implementation follows the official OpenAI Skill model: a directory has a required `SKILL.md` with `name` and `description`, optional references/scripts/assets/metadata, and full instructions load after the Skill is selected. See the [official Build skills documentation](https://developers.openai.com/codex/skills/).

## Routing layers

| Layer | Resource class | Load condition | Decision improved |
|---|---|---|---|
| 0 | Skill metadata | discovery/trigger evaluation | correct activation boundary |
| 1 | concise `SKILL.md` | every activated task | intake → plan → verify workflow |
| 2 | core contracts/quality | every non-trivial scene | state, evidence, gates, repair |
| 3 | scene/continuity | multiple shots, references, long-form | identity, state, anchors, timeline |
| 4 | dialogue/performance/audio | speech, singing, expressive interaction | speaker timing, reaction, sync path |
| 5 | interaction/physics/vehicle/animal | physical or articulated action | contact, anatomy, mechanics, decomposition |
| 6 | model profile | selected/requested model or runtime | supported mode, limits, syntax, fallback |
| 7 | ComfyUI execution | ComfyUI target or operator request | graph/preflight/authorization boundary |
| 8 | eval/pattern/observability | implementation, diagnosis, or review | fixture selection and evidence output |

## Explicit routing matrix

| User/task signal | Minimum loaded references | Do not load by default |
|---|---|---|
| Simple 5-second portrait | core contracts, directing, acceptance | long-form, vehicle, adapter internals |
| Dialogue scene | core, scene/continuity, directing, audio/lip-sync, failure/evals | vehicle/animal physics unless present |
| Vehicle entry/driving | core, scene/continuity, interaction/motion, constraints, pattern library | dialogue profile unless speech present |
| Human/animal contact | core, scene/continuity, interaction/motion, animal constraints, evals | long-form unless duration/dependency requires |
| 30–120-second sequence | core, Scene Bible, state, continuity, long-form, assembly/evals | unrelated specialist profiles |
| MiniMax target | core, model-adaptation, current MiniMax profile/research | local ComfyUI graph details unless target includes ComfyUI |
| ComfyUI target | core, model-adaptation, ComfyUI execution, current runtime profile | external API details unless fallback selected |
| Failure diagnosis | relevant domain owner, failure/evals, observability | entire package |

## Reference loading rules

1. Load a reference because a current task needs its decision, not because the blueprint names it.
2. A loaded reference must link back to one canonical contract and name the failure it reduces.
3. The core `SKILL.md` should route to a reference by concrete signal (`dialogue`, `vehicle`, `long-form`, model/runtime), not by a broad “read everything” instruction.
4. Model profiles remain dated and are not loaded as capability truth until their evidence is current.
5. Scripts are loaded/run only when deterministic repetition or artifact parsing justifies them.

## Failure modes

| Failure | Signal | Repair |
|---|---|---|
| Context bloat | all references loaded for a simple scene | narrow route by complexity/domain |
| Missing specialist guidance | high-risk task stays in core only | add trigger or ask targeted question |
| Stale profile loaded | validity date expired | mark profile stale and revalidate |
| Hidden dependency | reference assumes an unloaded contract | add explicit route/link |
| Over-fragmentation | thin files add no independent decision | consolidate and update index/ADR |

## Open questions

Exact host behavior for repository/user/admin Skill discovery and whether profile routing should be static metadata or dynamic reasoning must be confirmed during Phase 1. The official package shape is evidence; project routing policy is proposed.

## Related documents

The future package proposal is [`proposed-skill-structure.md`](proposed-skill-structure.md); architecture ownership is in [`architecture.md`](architecture.md); current evidence is in [`research.md`](research.md).
