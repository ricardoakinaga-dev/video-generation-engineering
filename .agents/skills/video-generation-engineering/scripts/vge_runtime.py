"""ComfyUI API boundary: data-only graphs, explicit submission, no blind retry."""
from __future__ import annotations

import copy
import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit, quote
from urllib.request import Request, build_opener, HTTPRedirectHandler, ProxyHandler

from vge_core import ContractError, canonical, digest, file_hash, require, save, number, negotiate
from vge_evidence import validate_observation


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ContractError("Runtime redirect refused; configure the intended endpoint")


def _journal_uncertain(run, attempt_id, error):
    """Best-effort append-only marker after a POST whose outcome is not sealed."""
    try:
        save(run / "submission-uncertain.json", {"attempt_id": attempt_id, "status": "UNKNOWN", "error": type(error).__name__, "next_action": "Inspect queue/history by extra_data.vge_attempt_id; never automatically resubmit"})
    except (OSError, TypeError, ValueError):
        pass


def _runtime_name(value, label):
    """Validate the relative filename passed to ComfyUI, not a local path."""
    require(isinstance(value, str) and value and "\x00" not in value and "\\" not in value, f"{label} must be a relative runtime filename")
    parts = value.split("/")
    require(not value.startswith("/") and all(part not in ("", ".", "..") for part in parts), f"{label} must not contain traversal")
    return value


class ComfyClient:
    def __init__(self, endpoint, timeout=15, remote=False, token=None):
        url = urlsplit(endpoint)
        require(url.scheme in ("http", "https") and url.hostname and not url.username and not url.password and not url.query and not url.fragment, "Endpoint must be an explicit HTTP(S) URL without credentials/query")
        if not remote:
            require(url.hostname in ("127.0.0.1", "::1", "localhost"), "Local mode only permits loopback endpoints")
        else:
            require(url.scheme == "https", "Remote runtime requires HTTPS")
        require(number(timeout, True) and timeout <= 60, "Network timeout must be in (0,60]")
        if token is not None:
            require(isinstance(token, str) and token and "\r" not in token and "\n" not in token, "Runtime token must be a nonempty single-line value")
        self.endpoint, self.timeout = endpoint.rstrip("/"), timeout
        self.headers = {"Authorization": f"Bearer {token}"} if token else {}
        self.opener = build_opener(NoRedirect(), ProxyHandler({}))

    def request(self, route, body=None, binary=False):
        require(isinstance(route, str) and route.startswith("/") and not route.startswith("//"), "Invalid relative API route")
        headers = {**self.headers, "Accept": "application/json"}
        data = canonical(body).encode() if body is not None else None
        if data is not None:
            headers["Content-Type"] = "application/json"
        try:
            with self.opener.open(Request(self.endpoint+route, data=data, headers=headers), timeout=self.timeout) as response:
                content = response.read(128 * 1024 * 1024 + 1)
                require(len(content) <= 128 * 1024 * 1024, "Runtime response exceeds 128 MiB; retrieve large artifacts through approved local paths")
                return content if binary else json.loads(content)
        except HTTPError as exc:
            raise ContractError(f"Runtime HTTP {exc.code} for {route.split('?')[0]}; response omitted to protect credentials") from exc
        except (URLError, TimeoutError, UnicodeError, json.JSONDecodeError, OSError) as exc:
            raise ContractError(f"Runtime request failed ({type(exc).__name__}); submission may be uncertain") from exc

    def discover(self):
        stats = self.request("/system_stats")
        nodes = self.request("/object_info")
        return {"schema_version": 1, "endpoint": self.endpoint, "observed_at": datetime.now(timezone.utc).isoformat(),
                "system_stats": stats, "object_info": nodes, "node_inventory_hash": digest(nodes),
                "limitations": ["Node metadata confirms availability, not successful model inference or media quality"]}


def validate_workflow(workflow, node_info):
    require(isinstance(workflow, dict) and workflow, "API workflow must be a nonempty object")
    require(isinstance(node_info, dict), "Runtime node metadata must be an object")
    require("nodes" not in workflow, "UI workflow export is not API-format JSON")
    issues, dependencies = [], {}
    for key, node in workflow.items():
        require(isinstance(key, str) and bool(key) and isinstance(node, dict), "Invalid API node")
        class_type = node.get("class_type")
        if not isinstance(class_type, str) or not class_type:
            issues.append(f"{key}: missing node type {class_type}")
            dependencies[key] = set()
            continue
        schema = node_info.get(class_type)
        if not isinstance(schema, dict) or not schema:
            issues.append(f"{key}: missing node type {class_type}")
            dependencies[key] = set()
            continue
        inputs = node.get("inputs")
        require(isinstance(inputs, dict), f"{key}: inputs must be an object")
        input_schema = schema.get("input", {})
        require(isinstance(input_schema, dict), f"{key}: node metadata input must be an object")
        required = input_schema.get("required", {})
        optional = input_schema.get("optional", {})
        require(isinstance(required, dict) and isinstance(optional, dict), f"{key}: node metadata required/optional inputs must be objects")
        spec = {**required, **optional}
        dependencies[key] = set()
        for field in required:
            require(isinstance(field, str) and field, f"{key}: node metadata has an invalid input name")
            if field not in inputs:
                issues.append(f"{key}.{field}: required input missing")
        for field, value in inputs.items():
            if field not in spec:
                issues.append(f"{key}.{field}: unknown input")
                continue
            entry = spec[field]
            require(isinstance(field, str) and field and isinstance(entry, (list, tuple)) and entry, f"{key}.{field}: malformed node input metadata")
            kind = entry[0]
            options = entry[1] if len(entry) > 1 else {}
            require(isinstance(options, dict), f"{key}.{field}: node input options must be an object")
            # Comfy API links are exactly [node-id string, output-index integer].
            is_link = isinstance(value, list) and len(value) == 2 and isinstance(value[0], str) and type(value[1]) is int
            if is_link and (isinstance(kind, list) or kind in ("COMBO", "COMFY_DYNAMICCOMBO_V3")):
                issues.append(f"{key}.{field}: enum/dynamic input cannot be a graph link")
                continue
            if is_link:
                source, index = value
                if source not in workflow:
                    issues.append(f"{key}.{field}: missing source {source}")
                    continue
                dependencies[key].add(source)
                source_type = workflow[source].get("class_type")
                source_schema = node_info.get(source_type, {}) if isinstance(source_type, str) else {}
                outputs = source_schema.get("output", []) if isinstance(source_schema, dict) else []
                require(isinstance(outputs, list), f"{source}: node metadata output must be an array")
                if not 0 <= index < len(outputs):
                    issues.append(f"{key}.{field}: output index out of range")
                elif not isinstance(kind, list) and kind != "*" and outputs[index] != "*" and not set(str(kind).split(",")) & set(str(outputs[index]).split(",")):
                    issues.append(f"{key}.{field}: linked output type mismatch")
            elif kind in ("COMBO", "COMFY_DYNAMICCOMBO_V3"):
                allowed = options.get("options", [])
                require(isinstance(allowed, list), f"{key}.{field}: dynamic options must be an array")
                allowed = [x.get("key") if isinstance(x, dict) else x for x in allowed]
                if value not in allowed:
                    issues.append(f"{key}.{field}: unavailable dynamic selection")
            elif isinstance(kind, list):
                if value not in kind:
                    issues.append(f"{key}.{field}: unavailable enum/model value")
            elif kind in ("INT", "FLOAT", "BOOLEAN", "STRING"):
                valid = type(value) is int if kind == "INT" else number(value) if kind == "FLOAT" else type(value) is bool if kind == "BOOLEAN" else isinstance(value, str)
                if not valid:
                    issues.append(f"{key}.{field}: invalid {kind}")
                elif kind in ("INT", "FLOAT"):
                    require(all(x not in options or number(options[x]) for x in ("min", "max")), f"{key}.{field}: invalid numeric node bounds")
                    if ("min" in options and value < options["min"]) or ("max" in options and value > options["max"]):
                        issues.append(f"{key}.{field}: outside node bounds")
            else:
                issues.append(f"{key}.{field}: {kind} requires a typed link")
    pending = set(dependencies)
    while pending:
        ready = {n for n in pending if not dependencies[n] & pending}
        if not ready:
            issues.append("Workflow contains a cycle")
            break
        pending -= ready
    if not any(isinstance(n, dict) and isinstance(n.get("class_type"), str) and isinstance(node_info.get(n.get("class_type")), dict) and node_info[n.get("class_type")].get("output_node") for n in workflow.values()):
        issues.append("Workflow has no output node")
    return {"status": "FAIL" if issues else "PASS", "issues": issues, "workflow_hash": digest(workflow), "scope": "API_GRAPH_METADATA", "limitations": ["Execution, VRAM fit, hidden/dynamic node validation and visual quality require a runtime probe"]}


def bind_workflow(workflow, bindings, node_info):
    require(isinstance(bindings, list), "bindings must be an array")
    result = copy.deepcopy(workflow)
    changes = []
    for binding in bindings:
        require(isinstance(binding, dict), "Each binding must be an object")
        require(all(k in binding for k in ("node_id", "input", "value", "source")), "Binding needs node_id/input/value/source")
        node, field = binding["node_id"], binding["input"]
        require(isinstance(node, str) and node and isinstance(field, str) and field and isinstance(binding["source"], str) and binding["source"], "Binding names/source must be nonempty strings")
        require(node in result and field in result[node]["inputs"], "Binding target does not exist")
        previous = result[node]["inputs"][field]
        result[node]["inputs"][field] = binding["value"]
        changes.append({**binding, "previous": previous})
    report = validate_workflow(result, node_info)
    require(report["status"] == "PASS", "; ".join(report["issues"]))
    return {"workflow": result, "changes": changes, "source_hash": digest(workflow), "validation": report}


def submit(client, workflow, context, destination, authorized=False, probe_mode=False):
    require(authorized is True, "Submission requires explicit authorization")
    require(isinstance(workflow, dict) and workflow, "Workflow must be a nonempty API object")
    for node_id, node in workflow.items():
        require(isinstance(node_id, str) and node_id and isinstance(node, dict) and isinstance(node.get("class_type"), str) and node["class_type"] and isinstance(node.get("inputs"), dict), "Workflow nodes require id, class_type and inputs")
    require(isinstance(context, dict), "Execution context required")
    for field in ("execution_plan_ref", "shot_id", "attempt_index", "profile", "model", "inputs", "parameters"):
        require(field in context, f"Missing execution context: {field}")
    require(isinstance(context["execution_plan_ref"], str) and context["execution_plan_ref"], "Invalid execution_plan_ref")
    require(isinstance(context["shot_id"], str) and context["shot_id"], "Invalid shot_id")
    require(type(context["attempt_index"]) is int and context["attempt_index"] > 0, "Invalid attempt index")
    context_profile = context["profile"]
    profile, shot = context.get("profile_record", {}), context.get("shot", {})
    require(isinstance(context_profile, dict) and isinstance(profile, dict) and isinstance(shot, dict), "Execution profile/shot records must be objects")
    require(isinstance(context.get("inputs"), list), "Execution inputs must be an array")
    require(isinstance(context["parameters"], dict), "Recorded execution parameters must be an object")
    require(shot.get("id") == context["shot_id"], "Context must resolve the exact shot")
    require(type(context_profile.get("revision")) is int and context_profile["revision"] > 0, "Invalid context profile revision")
    require(profile.get("id") == context_profile.get("id") and profile.get("profile_revision") == context_profile.get("revision"), "Profile identity/revision mismatch")
    compatibility = negotiate(shot, profile)
    if probe_mode:
        probe_budget = context.get("probe_budget", {})
        require(isinstance(probe_budget, dict) and isinstance(context.get("probe_purpose"), str) and context["probe_purpose"] and probe_budget.get("max_submissions") == 1, "A diagnostic probe needs a purpose and a one-submission budget")
    else:
        require(compatibility["status"] == "SUPPORTED", "; ".join(compatibility["gaps"]))
    profile_workflow_hash = profile.get("workflow_hash")
    if probe_mode and profile_workflow_hash in (None, "", "UNKNOWN"):
        profile_workflow_hash = None
    else:
        require(profile_workflow_hash == digest(workflow), "Workflow differs from the profile's probed graph; bind and revalidate the profile first")
    accepted_dependencies = context.get("accepted_dependencies", [])
    require(isinstance(accepted_dependencies, list), "accepted_dependencies must be an array")
    for bundle in accepted_dependencies:
        require(isinstance(bundle, dict) and isinstance(bundle.get("artifact"), dict) and isinstance(bundle.get("shot"), dict), "Each accepted dependency must contain an artifact and canonical shot bundle")
    predecessors = {b["artifact"].get("shot_id"): b for b in accepted_dependencies}
    expected_start = context.get("expected_start_state", {})
    if shot.get("dependency_ids"):
        require(isinstance(expected_start, dict) and bool(expected_start), "Dependent execution requires the resolved expected_start_state")
        require(all(value not in (None, "UNKNOWN") for value in expected_start.values()), "Expected dependency state is unresolved")
        require(all(expected_start.get(prop) == value for prop,value in shot.get("start_state_delta", {}).items()), "Expected state contradicts the shot start requirement")
    for dep in shot.get("dependency_ids", []):
        require(dep in predecessors, f"Missing accepted observed predecessor: {dep}")
        bundle = predecessors[dep]
        result = validate_observation(bundle["observation"], bundle["artifact"], bundle["attempt"], bundle["shot"])
        require(result["accepted"], f"Predecessor not accepted: {dep}")
        state = bundle["observation"].get("observed_end_state", {})
        require(bool(state), "Hash-bound observation must include observed_end_state")
        dependency_properties = shot.get("required_dependency_properties", {})
        require(isinstance(dependency_properties, dict), "required_dependency_properties must be an object")
        properties = dependency_properties.get(dep, list(expected_start))
        require(isinstance(properties, list) and all(isinstance(prop, str) and prop for prop in properties), "Dependency property scope must be an array of nonempty strings")
        require(bool(properties) and all(prop in expected_start for prop in properties), "Dependency property scope must resolve to expected state")
        for prop in properties:
            value = expected_start[prop]
            require(prop in state and state[prop] == value and value not in (None, "UNKNOWN"), f"Observed dependency state mismatch: {prop}")
    shot_parameters = shot.get("parameters", {})
    require(isinstance(shot_parameters, dict), "Shot parameters must be an object")
    require(context["parameters"].get("bindings") == shot_parameters, "Recorded parameter bindings differ from the negotiated shot")
    if "seed" in context["parameters"]:
        require(context["parameters"]["seed"] == shot.get("parameters", {}).get("seed"), "Recorded seed differs from negotiated shot")
    parameter_bindings = context.get("parameter_bindings", {})
    require(isinstance(parameter_bindings, dict), "parameter_bindings must be an object")
    for k, value in shot_parameters.items():
        binding = parameter_bindings.get(k)
        require(isinstance(binding, dict) and isinstance(binding.get("node_id"), str) and isinstance(binding.get("input"), str), f"Missing runtime parameter mapping: {k}")
        require(workflow.get(binding["node_id"], {}).get("inputs", {}).get(binding["input"]) == value, f"Workflow parameter differs from negotiated shot: {k}")
    observed = client.discover()
    require(isinstance(observed, dict) and isinstance(observed.get("system_stats"), dict) and isinstance(observed.get("object_info"), dict), "Runtime discovery response is malformed")
    system = observed["system_stats"].get("system", {})
    require(isinstance(system, dict), "Runtime system metadata is malformed")
    runtime_version = profile.get("runtime_version")
    if not (probe_mode and runtime_version in (None, "", "UNKNOWN")):
        require(runtime_version == system.get("comfyui_version"), "Runtime version differs from confirmed profile")
    inventory_hash = profile.get("node_inventory_hash")
    if not (probe_mode and inventory_hash in (None, "", "UNKNOWN")):
        require(isinstance(inventory_hash, str) and isinstance(observed.get("node_inventory_hash"), str) and inventory_hash == observed["node_inventory_hash"], "Node inventory differs from confirmed profile")
    validation = validate_workflow(workflow, observed["object_info"])
    require(validation["status"] == "PASS", "; ".join(validation["issues"]))
    # Context contains asset locations only locally; hashes are computed here, not trusted.
    inputs = []
    for asset in context["inputs"]:
        require(isinstance(asset, dict) and isinstance(asset.get("ref"), str) and asset["ref"] and isinstance(asset.get("role"), str) and asset["role"] and isinstance(asset.get("path"), str) and asset["path"], "Input asset needs ref/role/path")
        binding = asset.get("workflow_binding", {})
        require(isinstance(binding, dict) and isinstance(binding.get("node_id"), str) and isinstance(binding.get("input"), str), f"Input asset has no valid workflow binding: {asset['ref']}")
        runtime_name = asset.get("runtime_name", Path(asset["path"]).name)
        _runtime_name(runtime_name, f"Runtime name for {asset['ref']}")
        require(workflow.get(binding.get("node_id"), {}).get("inputs", {}).get(binding.get("input")) == runtime_name, f"Input asset has no matching workflow binding: {asset['ref']}")
        inputs.append({"ref": asset["ref"], "role": asset["role"], "content_hash": file_hash(asset["path"])})
    model = copy.deepcopy(context["model"])
    require(isinstance(model, dict), "Primary model record must be an object")
    require(isinstance(model.get("id"), str) and model["id"] and isinstance(model.get("version"), str) and model["version"] not in ("", "UNKNOWN"), "Primary model id/version provenance is required")
    require(isinstance(model.get("asset_path"), str) and model["asset_path"], "Primary model asset_path is required")
    binding = model.pop("workflow_binding", {})
    require(isinstance(binding, dict) and isinstance(binding.get("node_id"), str) and isinstance(binding.get("input"), str), "Primary model has no valid workflow binding")
    runtime_name = model.pop("runtime_name", Path(model["asset_path"]).name)
    _runtime_name(runtime_name, "Primary model runtime name")
    require(workflow.get(binding.get("node_id"), {}).get("inputs", {}).get(binding.get("input")) == runtime_name, "Primary model has no matching workflow binding")
    model["asset_hash"] = file_hash(model.pop("asset_path"))
    require(model["id"] == profile.get("model"), "Model identity differs from confirmed profile")
    model_asset_hash = profile.get("model_asset_hash")
    if not (probe_mode and model_asset_hash in (None, "", "UNKNOWN")):
        require(model["asset_hash"] == model_asset_hash, "Model differs from confirmed profile")
    if not probe_mode:
        expected = {x["ref"]: x["content_hash"] for x in profile.get("dependencies", {}).get("model_assets", [])}
        actual = {x["ref"]: x["content_hash"] for x in inputs}
        require(all(actual.get(ref) == value for ref,value in expected.items()), "Dependency asset differs from the probed profile")
    attempt_id = "attempt_" + uuid.uuid4().hex
    run = Path(destination) / attempt_id
    run.mkdir(parents=True, exist_ok=False)
    version = observed["system_stats"].get("system", {}).get("comfyui_version")
    node_versions = context.get("node_versions", {})
    require(isinstance(node_versions, dict), "node_versions must be an object")
    node_records = [{"id": key, "type": node["class_type"], "version": node_versions.get(node["class_type"])} for key, node in workflow.items()]
    unknown = (["runtime.version"] if not version else []) + [f"nodes.{i}.version" for i,n in enumerate(node_records) if not n["version"]]
    attempt = {"schema_version": 1, "id": attempt_id, "revision": 1, "execution_plan_ref": context["execution_plan_ref"], "shot_id": context["shot_id"], "shot_contract_hash": digest(shot), "attempt_index": context["attempt_index"], "status": "UNKNOWN",
               "started_at": datetime.now(timezone.utc).isoformat(), "ended_at": None, "profile": context["profile"], "model": model,
               "runtime": {"provider": "comfyui", "endpoint": client.endpoint, "version": version, "node_inventory_hash": observed["node_inventory_hash"]},
               "workflow": {"ref": str((run / "workflow.json").resolve()), "content_hash": digest(workflow), "prompt_ref": context["execution_plan_ref"], "queue_id": None},
               "nodes": node_records, "inputs": inputs, "parameters": context["parameters"], "progress_ref": str((run / "events.jsonl").resolve()), "error_ref": None, "unknown_fields": unknown + ["workflow.queue_id"]}
    attempt["purpose"] = "CAPABILITY_PROBE" if probe_mode else "GENERATION"
    save(run / "workflow.json", workflow)
    save(run / "attempt-001.json", attempt)
    save(run / "preflight.json", {"validation": validation, "compatibility": compatibility, "discovery_hash": digest(observed), "probe_purpose": context.get("probe_purpose") if probe_mode else None})
    # Intent is durably stored before the only POST. A lost reply or journal
    # failure after the POST leaves an explicit best-effort UNKNOWN marker.
    try:
        response = client.request("/prompt", {"prompt": workflow, "client_id": attempt_id, "extra_data": {"vge_attempt_id": attempt_id}})
        require(isinstance(response, dict), "Runtime submission response must be an object")
        require(isinstance(response.get("prompt_id"), str) and not response.get("node_errors"), "Submission rejected or lacks prompt ID; inspect runtime history before retry")
        accepted = copy.deepcopy(attempt)
        accepted.update(revision=2, supersedes_hash=digest(attempt), status="SUBMITTED")
        accepted["workflow"]["queue_id"] = response["prompt_id"]
        accepted["unknown_fields"] = unknown
        save(run / "attempt-002.json", accepted)
    except Exception as exc:
        _journal_uncertain(run, attempt_id, exc)
        if isinstance(exc, ContractError):
            raise
        raise ContractError("Runtime submission outcome or journal is uncertain; inspect the same queue marker before retry") from exc
    return {"attempt": accepted, "run_directory": str(run.resolve())}


def poll(client, prompt_id, timeout=60, interval=1):
    require(number(timeout, True) and timeout <= 3600 and number(interval, True), "Invalid polling bounds")
    require(isinstance(prompt_id, str) and prompt_id, "Prompt ID is required")
    deadline = time.monotonic() + timeout
    while True:
        data = client.request("/history/" + quote(prompt_id, safe=""))
        require(isinstance(data, dict), "Runtime history response must be an object")
        if prompt_id in data:
            record = data[prompt_id]
            require(isinstance(record, dict), "Runtime history record must be an object")
            status = record.get("status", {})
            require(isinstance(status, dict), "Runtime history status must be an object")
            status_str = status.get("status_str")
            if status_str in ("error", "failed"):
                return {"status": "FAILED", "prompt_id": prompt_id, "history": record}
            if status_str in ("cancelled", "canceled"):
                return {"status": "CANCELLED", "prompt_id": prompt_id, "history": record}
            if status.get("completed") is True and status_str in ("success", "completed"):
                return {"status": "SUCCEEDED", "prompt_id": prompt_id, "history": record}
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return {"status": "UNKNOWN", "prompt_id": prompt_id, "next_action": "Poll this same ID again; timeout does not cancel or authorize resubmission"}
        time.sleep(min(interval, remaining))


def collect(client, attempt, history, destination):
    require(isinstance(attempt, dict), "attempt must be an object")
    require(isinstance(history, dict), "history result must be an object")
    require(history.get("status") == "SUCCEEDED", "Only completed jobs can be collected")
    require(attempt.get("status") in ("SUBMITTED", "RUNNING", "SUCCEEDED"), "A failed, cancelled or unresolved attempt cannot be rewritten as successful")
    from vge_evidence import validate_attempt
    validate_attempt(attempt)
    require(isinstance(history.get("prompt_id"), str) and history["prompt_id"], "History prompt_id is required")
    require(history.get("prompt_id") == attempt["workflow"]["queue_id"], "History/attempt queue mismatch")
    raw = history.get("history", {})
    require(isinstance(raw, dict), "Runtime history payload must be an object")
    history_status = raw.get("status", {})
    require(isinstance(history_status, dict) and history_status.get("completed") is True and history_status.get("status_str") == "success", "History does not confirm successful completion")
    submitted_prompt = raw.get("prompt", [])
    require(isinstance(submitted_prompt, list) and len(submitted_prompt) >= 3 and submitted_prompt[1] == history["prompt_id"] and digest(submitted_prompt[2]) == attempt["workflow"]["content_hash"], "Runtime history does not match the sealed workflow")
    out = Path(destination)
    out.mkdir(parents=True, exist_ok=True)
    completed = copy.deepcopy(attempt)
    completed.update(status="SUCCEEDED", revision=attempt.get("revision", 1)+1, supersedes_hash=digest(attempt), ended_at=datetime.now(timezone.utc).isoformat())
    save(out / (attempt["id"] + "-completed.json"), completed)
    records = []
    outputs_by_node = raw.get("outputs", {})
    require(isinstance(outputs_by_node, dict), "Runtime history outputs must be an object")
    for node, outputs in outputs_by_node.items():
        require(isinstance(outputs, dict), "Runtime node outputs must be objects")
        for kind in ("images", "gifs", "videos", "audio"):
            entries = outputs.get(kind, [])
            require(isinstance(entries, list), f"Runtime {kind} outputs must be an array")
            for output in entries:
                require(isinstance(output, dict), "Runtime output record must be an object")
                name = output.get("filename", "")
                require(name and Path(name).name == name and "\\" not in name, "Unsafe runtime output filename")
                folder = output.get("subfolder", "")
                require(isinstance(folder, str), "Unsafe runtime output subfolder")
                require(not Path(folder).is_absolute() and ".." not in Path(folder).parts and "\\" not in folder, "Unsafe runtime output subfolder")
                require(output.get("type", "output") in ("output", "temp"), "Refuse collection from runtime input directory")
                body = client.request("/view?" + urlencode({"filename": name, "subfolder": folder, "type": output.get("type", "output")}), binary=True)
                require(isinstance(body, (bytes, bytearray)), "Runtime artifact response must be bytes")
                aid = "art_" + uuid.uuid4().hex
                path = out / (aid + Path(name).suffix)
                with path.open("xb") as f:
                    f.write(body)
                artifact = {"schema_version": 1, "id": aid, "shot_id": attempt["shot_id"], "execution_attempt_ref": attempt["id"], "artifact_ref": str(path.resolve()), "content_hash": file_hash(path), "collected_at": datetime.now(timezone.utc).isoformat(), "generation_status": "GENERATED", "media": {"kind": kind}, "runtime": {"provider": "comfyui", "endpoint": client.endpoint, "workflow_hash": attempt["workflow"]["content_hash"]}, "quality_review": {"lifecycle": "NOT_STARTED", "observation_ref": None}}
                save(out / (aid + ".json"), artifact)
                records.append(artifact)
    require(records, "Job completed without collectible outputs")
    return records
