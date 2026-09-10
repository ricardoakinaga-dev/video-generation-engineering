# Story, performance, camera and audio

Read when behavior, dialogue, expressive acting, moving coverage or sound changes a planning decision.

## Observable direction

A beat states purpose, cause, visible action, audience focus, emotional change and exit state. Keep stimulus → perception/processing → reaction → response explicit. Every character has an immediate objective, attention target, physical state and sparse observable behavior. Relationships affect gaze, distance, posture, turn-taking and willingness to make contact. Replace adjective stacks with actions: release shoulder tension after recognition; look at the key before answering.

For two-person dialogue, author establishing geography, line A, processing/reaction B, line B and response A. Preserve speaker/listener and screen positions through coverage. For walking-and-talking, also track route, destination anchor, spacing, gait phase, camera movement and arrival state. If speech plus movement overloads a profile, propose singles, cutaways or separate voiceover without silently changing intent.

## Camera contract

Specify size/framing, angle/height, focal_length/lens intent, focus, depth_of_field, motion_blur, exposure, lighting, eyeline, movement type/direction/phase, screen_direction, axis_policy and edit_rhythm. A moving shot explains what the movement reveals. Motivate an axis crossing or add neutral coverage; a numeric camera command is not a story rationale. Use camera-left/right consistently relative to the established view, not interchangeable with character-left/right.

Treat light direction, weather, reflections, practicals and time progression as scene state. Deliberate changes need a beat or cut. Camera preferences never silently weaken identity, causality or contact readability.

## Dialogue JSON

Each `dialogue_timeline` item contains `dialogue_id`/`id`, `shot_id`, `speaker`, `listener`/`target_listener`, `line`/`text`, `start_s`/`start`, `end_s`/`end`, delivery/performance notes, `listener_reaction`, `reaction_order`, `voice_strategy` and `lip_sync_strategy`. The canonical reaction order is an explicit, timed `STIMULUS → PROCESSING → REACTION → RESPONSE` chain; a `RESPONSE` starts at or after the line end unless intentional overlap is declared. `voice_reference` and `lip_sync_mode` remain accepted input aliases and are normalized into strategy declarations; `PROPOSED`, `UNKNOWN`, `FAILED` and legacy `UNSUPPORTED` describe capability/evidence state, not generated-media proof. A voiceover or offscreen listener uses an explicit `NOT_APPLICABLE`/`OFFSCREEN` status and reason. Optional `reaction_at_s` precedes the end only with `intentional_overlap: true`. Both overlapping lines must explicitly declare overlap. Times are relative to the owning shot. The planner reports incomplete authored declarations; the compiler refuses them and emits only the normalized canonical representation.

`visible_speech: true` also needs `audio_source`, `lip_sync_path`, face-visibility coverage and compatible feature evidence. Sustained speech articulation belongs to the active speaker; listener expressions are reactions. Test phonetic synchronization from actual audio and face-visible frames. Never infer joint video/audio/lip-sync support from a model's input-audio feature.

## Audio layers

Keep dialogue/vocal performance, foley, ambience, room tone, vehicle, animal, score, transition, non-diegetic sound and silence separate. An `audio_timeline` item has `id`, `shot_id`, `layer`, `start_s`, `end_s`, source, cause, priority and mix role. The planning alias `effects` is normalized to `foley`; its cause names a visible action primitive. Split cross-shot bridge records into timed pieces with an explicit bridge relationship. Record event offsets against visible latch/step/impact intervals; intentional offscreen or non-diegetic events state the exception.

Choose generated, supplied or separately produced audio per layer. Check source rights, channels/sample rate, duration, loudness target, room-tone continuity and synchronization. A source that is still unknown stays unknown; do not invent dialogue, a voice identity or a music license to fill a form. Supplied recordings may drive timing rather than be squeezed into arbitrary shot durations.

## Delivery decisions

Lip-sync, audio generation, interpolation, upscale and mux are separate capabilities and artifacts. Use a confirmed tool/profile when available; otherwise provide the exact input/output contract and mark the stage pending. Preserve original tracks and versions. A metadata-valid mux still needs listening and frame-alignment review before editorial acceptance.
