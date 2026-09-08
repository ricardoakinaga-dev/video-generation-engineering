# Continuity and long-form direction

Read for dependent shots, state changes, branching, duration >30s and repair of long sequences.

## Structure floors

For real-valued duration t: 0 < t ≤ 30 requires shot purpose and boundary state; 30 < t ≤ 45 adds a narrative timeline; 45 < t < 60 adds Scene Bible, shot graph and PLANNED state propagation; 60 ≤ t < 90 adds applicable reference/dialogue/audio timelines, generation strategy and assembly; 90 ≤ t ≤ 120 additionally requires explicit alternatives, recovery checkpoints, a pending/complete provenance manifest and human checkpoints. Complexity can require these earlier. A static 90-second scene can have a one-node graph; it still needs the structures. Above 120 seconds, propose a project of separately validated scenes rather than silently extrapolating these limits.

FAST, CINEMATIC, PRODUCTION and DIRECTOR describe depth/presentation, not different engines. Evaluate identities, references, dialogue, lip-sync, contact, articulated objects, motion, camera, duration and VFX. Dense 10-second action can need DIRECTOR coverage. Helper routing is a deterministic suggestion; the director escalates when actual dependencies justify it.

## State and graph

Separate permanent identity, persistent wardrobe/world/geometry, transient pose/gaze/emotion/occupancy, and derived prompt/preview state. Track relationships including holds, follows, looks_at, owns, is_inside, is_left_of and speaks_to with scope and interval. The Scene Bible owns global invariants, not a copy in every prompt.

`dependency_ids` forms an acyclic graph. Story/edit order may differ from generation order; declare both. At each boundary:

1. Resolve every predecessor and required property.
2. In PLAN_ONLY inherit planned state. For a generated-media dependency, require accepted observed state and current hashes for the relevant properties.
3. Compare start requirements against inherited values. Two branch parents disagreeing about one property require a merge decision, not last-writer-wins.
4. Apply only declared changes with known prior, next and causal action/transition.
5. Preserve locked properties unless an explicitly reviewed scene transition changes them.
6. Export end state and link downstream shots to that boundary.

Example: closed door → reach → contact handle → pull → open door. A later driving shot cannot assume entry, closing and ignition happened without coverage or an explicit elapsed-time cut. A hand release, key handoff or emotional change is a state transition too. A location jump needs a new scene or declared geographic/time transition.

## Anchors and reset budget

Anchor types: canonical_reference, accepted_last_frame, first_last_frame, keyframe_reset and human_review. Each carries only named properties. An image cannot automatically anchor voice or physics. Accepted last frames need a current artifact/observation link and the selected profile's confirmed input support. FLF also requires confirmed endpoint support and endpoint QA.

The helper proposes a canonical reset every three shots; this is an explicit reversible planning default, not a measured model limit. Set a project-specific budget for maximum chain length, allowed identity/world drift, and review frequency before generation. Re-anchor at location changes, occlusions, contact failures and high-risk identities even before that interval. Never feed an unvalidated frame recursively because it looks attractive.

## Assembly and repair

For a 60-second dialogue/action spot, build setup, turn-taking, processing/reaction, discovery, reconciliation, transfer, entry and departure as distinct causal coverage. For 90–120 seconds, partition into validated segments with canonical entry frames, explicit reset points, continuous room tone and an edit manifest.

A changed reference, profile, shot end state or rejected anchor invalidates every dependent descendant, not independent sibling branches. Preserve accepted unaffected shots. Replan from the nearest stable ancestor, create a new revision, and recheck geometry/time/contact/audio at all touched joins. The helper's recomputation is planned truth only; execution uses current observations.

Before final delivery verify shot order, total duration, FPS, codec/container, join frames, audio alignment, provenance and editorial intent. Interpolation/upscale are optional separate stages requiring evidence and post-stage review; neither erases source defects.
