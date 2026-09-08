# ComfyUI execution and recovery

Read before touching a runtime, binding an API graph, submitting, recovering or collecting. The scripts are local-first; optional remote adapters must use explicit target/credentials/authorization.

## Modes

PLAN_ONLY contacts no runtime. LOCAL_DRY_RUN reads metadata and checks an API-format graph. LOCAL_EXECUTE additionally queues the selected graph and collects outputs. CLOUD_EXECUTE requires a selected authenticated provider and transfer/cost authority. Authorization persists within the current task's scope; do not request it repeatedly. Installing custom nodes, downloading weights and publishing are separate actions.

Commands below run from the skill directory:

```bash
python3 scripts/vge.py discover --output discovery.json
python3 scripts/vge.py preflight workflow-api.json
python3 scripts/vge.py bind workflow-api.json bindings.json --output bound.json
python3 scripts/vge.py submit workflow-api.json context.json --destination runs --authorize-submit --output submitted.json
python3 scripts/vge.py poll QUEUE_ID --timeout 60 --output history.json
python3 scripts/vge.py collect runs/ATTEMPT_ID/attempt-002.json history.json --destination artifacts
```

The `bind` result wraps the graph under `workflow` and includes change records; export that graph to a new API JSON file for submission. `poll` may be repeated for the same ID. UNKNOWN after timeout is not cancellation or failure. Do not rerun `submit` as a polling substitute.

To establish a new capability, use `submit --probe --authorize-submit` with `probe_purpose` and `probe_budget: {max_submissions: 1}` in the context. A candidate may leave workflow/runtime/node/model hashes unknown for this one explicit probe; graph/asset checks still run, it records CAPABILITY_PROBE and retains the failed compatibility report. It never promotes the candidate automatically. Inspect the result and create a scoped profile revision with actual evidence. Ordinary submissions still require confirmed compatibility.

## Discover and validate

Inspect `/system_stats` and `/object_info` through the selected endpoint. Record version, available node schemas/model enums, device/VRAM and inventory hash. Optional feature/model routes depend on the deployment. Use installed tools when they provide a better-supported discovery path. The [official route documentation](https://docs.comfy.org/development/comfyui-server/comms_routes) explains the server boundary; current local metadata is authoritative for installed node inputs.

An API graph maps node IDs to `class_type` and `inputs`; UI nodes/links JSON requires a deliberate conversion. Never guess widget ordering for an unfamiliar node. Each link is `[source_node_id, output_index]`. Check node availability, required fields, supported enum/model selections, type compatibility, range bounds, cycles and output nodes. Dynamic/custom-node inputs may need node-specific or runtime validation. A static PASS proves graph metadata compatibility only.

Bindings name node_id, input, value and source. Record previous/new values and source workflow hash. Verify dimensions, duration/frame grid/FPS, batch/memory limits, loaded models, audio path and encoding. Reject rather than silently lowering quality to fit memory; propose a bounded alternative if needed.

## Context, attempts and outputs

The submission context contains execution_plan_ref, shot_id, attempt_index, profile identity/revision, full profile record and shot requirements, model identity/version/asset_path, input ref/role/path records, node_versions and parameters. Compatibility is recomputed before execution. The primary model hash and all supplied inputs are computed from local files. Include VAE, encoder, LoRA and projection weights as execution input assets so the context retains every model dependency.

Use `profile_record` for the complete profile and `shot` for the canonical shot. `profile` is only `{id, revision}`. Every asset, including `model`, supplies `workflow_binding: {node_id, input}` and optionally `runtime_name` when the runtime uses a relative subfolder. That binding must equal the selected filename in the graph. `parameter_bindings` maps each canonical shot parameter to `{node_id, input}`. The immutable attempt also stores a `shot_contract_hash`, which acceptance must match against the canonical shot's revision and gate set. Matching dependency hashes, workflow hash and node inventory are required for ordinary generation; changes need a new scoped probe/profile revision.

The run directory is unique. `attempt-001.json` records submission intent before the POST; a lost response leaves an UNKNOWN record. `attempt-002.json` appends the returned queue ID, references the earlier record hash, and seals the submitted context. Later progress/outcome records are additional events/revisions, never edits to existing files. This append-only revision convention reconciles status progress with immutable execution context.

Artifacts link to the attempt ID, shot, workflow hash and bytes digest, with collection timestamp. Distinct attempts/outputs have distinct IDs even if a provider reuses a filename. Collection means GENERATED, not ACCEPTED. Unknown node/model/runtime provenance blocks reproducibility and acceptance until resolved by evidence, without guessing historical values.

`collect` appends an `ATTEMPT_ID-completed.json` revision in the artifact directory before creating collection records. Resolve that successful completion revision for acceptance; a SUBMITTED or UNKNOWN attempt cannot support acceptance. Collection failure leaves a completed runtime record and partial local collection evidence, not a new generation request.

## Failure and recovery

Classify environment, asset, capability, graph, authorization, execution, transport and collection failures. Preserve the failing graph and diagnostic. A POST timeout may have queued work: inspect `/queue` and `/history` using `extra_data.vge_attempt_id`, recover its prompt_id, then poll. Never blindly repeat a POST. A successful response with node_errors is not a valid completion.

Websocket events may provide progress through an available ComfyUI tool; history polling is the bundled portable fallback. Polling is bounded and uses finite per-request timeouts. A polling timeout leaves the runtime job alone. Cancel only the specific owned job through a supported API/tool; do not interrupt someone else's queue. A process crash does not make a submission safe to replay.

The bundled collector limits one response to 128 MiB. For larger outputs, use the runtime's approved local output path, compute its hash and create the same artifact contract; do not increase limits or follow external URLs blindly. Output paths are untrusted data, and collection refuses traversal.
