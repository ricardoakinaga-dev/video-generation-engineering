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
from vge_quality import profile_expiration_triggers, profile_fingerprint


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ContractError("Runtime redirect refused; configure the intended endpoint")


def _journal_uncertain(run, attempt_id, error):
    """Best-effort append-only marker after a POST whose outcome is not sealed."""
    try:
        save(run / "submission-uncertain.json", {"attempt_id": attempt_id, "status": "UNKNOWN", "error": type(error).__name__, "next_action": "Inspect queue/history by extra_data.vge_attempt_id; never automatically resubmit"})
    except (OSError, TypeError, ValueError):
        pass


def _append_event(path, event):
    """Append a canonical JSONL runtime event without rewriting prior events."""
    require(isinstance(event, dict) and event.get("schema_version") == 1, "Runtime event must be schema version 1")
    with Path(path).open("a", encoding="utf-8") as handle:
        handle.write(canonical(event) + "\n")


def _runtime_name(value, label):
    """Validate the relative filename passed to ComfyUI, not a local path."""
    require(isinstance(value, str) and value and "\x00" not in value and "\\" not in value, f"{label} must be a relative runtime filename")
    parts = value.split("/")
    require(not value.startswith("/") and all(part not in ("", ".", "..") for part in parts), f"{label} must not contain traversal")
    return value


def _workflow_equivalent(expected, observed):
    """Compare an API graph structurally while tolerating JSON numeric coercion.

    ComfyUI may round-trip an integer widget as ``1.0`` in `/history`.  That
    representation change is not a graph mutation, but the sealed byte-level
    digest must remain unchanged and the returned graph hash is recorded
    separately at collection time.
    """
    if isinstance(expected, dict) and isinstance(observed, dict):
        return (set(expected) == set(observed)
                and all(_workflow_equivalent(expected[key], observed[key]) for key in expected))
    if isinstance(expected, list) and isinstance(observed, list):
        return len(expected) == len(observed) and all(
            _workflow_equivalent(left, right) for left, right in zip(expected, observed))
    if isinstance(expected, (int, float)) and not isinstance(expected, bool) \
            and isinstance(observed, (int, float)) and not isinstance(observed, bool):
        return expected == observed
    return type(expected) is type(observed) and expected == observed


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
        system = stats.get("system", {}) if isinstance(stats, dict) else {}
        devices = stats.get("devices", []) if isinstance(stats, dict) else []
        if not isinstance(system, dict):
            system = {}
        if not isinstance(devices, list):
            devices = []
        resources = [{"id": str(index), "device_id": f"cuda:{device.get('index', index)}", "name": device.get("name", "UNKNOWN"),
                      "type": device.get("type", "GPU"), "vram_total": device.get("vram_total"),
                      "vram_free": device.get("vram_free"), "observed": True}
                     for index, device in enumerate(devices) if isinstance(device, dict)]
        node_types = sorted(key for key in nodes if isinstance(key, str)) if isinstance(nodes, dict) else []
        return {"schema_version": 1, "endpoint": self.endpoint, "observed_at": datetime.now(timezone.utc).isoformat(),
                "system_stats": stats, "object_info": nodes, "node_inventory_hash": digest(nodes),
                "runtime_version": system.get("comfyui_version", "UNKNOWN"),
                "runtime_context": {"python_version": system.get("python_version", "UNKNOWN"),
                                    "pytorch_version": system.get("pytorch_version", "UNKNOWN"),
                                    "cuda_version": system.get("pytorch_version", "UNKNOWN").split("+")[-1] if isinstance(system.get("pytorch_version"), str) and "+" in system.get("pytorch_version", "") else "UNKNOWN",
                                    "runtime_commit": system.get("runtime_commit", system.get("comfyui_commit", "UNKNOWN")),
                                    "runtime_dirty": system.get("runtime_dirty", system.get("comfyui_dirty", "UNKNOWN")),
                                    "custom_node_commits": system.get("custom_node_commits", {})},
                "resource_inventory": resources,
                "node_types": node_types,
                "custom_node_inventory": {"status": "OBSERVED_NODE_TYPES_ONLY", "node_types": node_types},
                "limitations": ["Node metadata confirms availability, not successful model inference or media quality",
                                "ComfyUI API discovery does not enumerate every local model file; bind model hashes from the immutable profile/runtime context",
                                "Resource values are observations, not a guarantee that a queued graph will fit"]}


def workflow_fingerprint(workflow, node_info=None):
    """Fingerprint graph topology plus node versions and generation-critical inputs."""
    require(isinstance(workflow, dict) and workflow, "Workflow must be a nonempty object")
    node_info = node_info if node_info is not None else {}
    require(isinstance(node_info, dict), "node_info must be an object")
    critical_names = ("ckpt_name", "model_name", "unet_name", "clip_name", "vae_name", "width", "height", "length",
                      "fps", "seed", "steps", "cfg", "sampler_name", "scheduler", "prompt", "first_frame", "last_frame",
                      "format", "format.codec", "format.codec.encoding", "format.codec.encoding.crf", "codec")
    nodes = []
    for node_id in sorted(workflow, key=str):
        node = workflow[node_id]
        require(isinstance(node, dict), f"Workflow node {node_id} must be an object")
        class_type = node.get("class_type")
        require(isinstance(class_type, str) and class_type, f"Workflow node {node_id} lacks class_type")
        schema = node_info.get(class_type, {})
        version = schema.get("version", schema.get("description_version", "UNKNOWN")) if isinstance(schema, dict) else "UNKNOWN"
        inputs = node.get("inputs", {})
        require(isinstance(inputs, dict), f"Workflow node {node_id}.inputs must be an object")
        critical = {key: inputs[key] for key in sorted(inputs) if key in critical_names}
        nodes.append({"id": str(node_id), "class_type": class_type, "version": version, "critical_inputs": critical})
    return digest({"topology": workflow, "nodes": nodes})


def _declared_min_free_vram(requirements):
    """Resolve the canonical free-VRAM floor without accepting ambiguity."""
    has_canonical = "min_free_vram_bytes" in requirements
    has_legacy = "min_vram_bytes" in requirements
    canonical_value = requirements.get("min_free_vram_bytes")
    legacy_value = requirements.get("min_vram_bytes")
    if has_canonical:
        require(number(canonical_value, True), "min_free_vram_bytes must be positive")
    if has_legacy:
        require(number(legacy_value, True), "min_vram_bytes must be positive")
    if has_canonical and has_legacy:
        require(canonical_value == legacy_value, "resource requirements contain conflicting VRAM floors")
    return canonical_value if has_canonical else legacy_value


def resource_status(discovery, requirements=None):
    """Classify observed local resources without pretending to predict execution.

    ``min_free_vram_bytes`` is the canonical requirement.  The older
    ``min_vram_bytes`` spelling remains accepted for standalone callers, but a
    runtime submission must provide one of them and bind it to its selected
    device.  The optional safety margin is deliberately visible in the
    returned report; it is a policy threshold, not a claim that inference will
    fit.
    """
    require(isinstance(discovery, dict), "discovery must be an object")
    requirements = requirements or {}
    require(isinstance(requirements, dict), "resource requirements must be an object")
    observed = discovery.get("resource_inventory", [])
    require(isinstance(observed, list), "discovery.resource_inventory must be an array")
    min_free_vram = _declared_min_free_vram(requirements)
    safety_margin = requirements.get("safety_margin", 1.2)
    require(number(safety_margin, True) and safety_margin >= 1, "safety_margin must be finite and >= 1")
    selected = requirements.get("device_id") or requirements.get("selected_device")
    if selected is not None:
        require(isinstance(selected, str) and selected, "selected device must be a nonempty string")
        selected_records = [item for item in observed if isinstance(item, dict) and (item.get("device_id") == selected or item.get("id") == selected or str(item.get("name", "")).startswith(selected))]
        known = [item for item in selected_records if number(item.get("vram_free"), True)]
    else:
        known = [item for item in observed if isinstance(item, dict) and number(item.get("vram_free"), True)]
    if not known:
        status = "UNKNOWN"
        gaps = ["No comparable free-VRAM observation"]
    elif min_free_vram is not None and max(item["vram_free"] for item in known) < min_free_vram:
        status = "BLOCKED"
        gaps = ["Observed free VRAM is below the declared minimum"]
    elif min_free_vram is not None and max(item["vram_free"] for item in known) < min_free_vram * safety_margin:
        status = "DEGRADED"
        gaps = ["Observed free VRAM has less than the declared safety margin"]
    else:
        status = "SUPPORTED"
        gaps = []
    observed_free = max((item["vram_free"] for item in known), default=None)
    return {"status": status, "selected_device": selected, "requirements": requirements,
            "effective_min_free_vram_bytes": min_free_vram,
            "effective_required_free_vram_bytes": min_free_vram * safety_margin if min_free_vram is not None else None,
            "observed_free_vram_bytes": observed_free, "observed_resources": known,
            "gaps": gaps, "limitations": ["A resource snapshot is not an execution guarantee",
                                            "Free VRAM can change between this snapshot and runtime execution"]}


def validate_profile_runtime(profile, discovery, workflow=None, feature=None, model_asset_hash=None):
    """Check feature-scoped profile identity against a fresh runtime snapshot."""
    require(isinstance(profile, dict), "profile must be an object")
    require(isinstance(discovery, dict), "discovery must be an object")
    selected_device = discovery.get("selected_device")
    if not selected_device and isinstance(workflow, dict):
        for node in workflow.values():
            if not isinstance(node, dict) or not isinstance(node.get("inputs"), dict):
                continue
            candidate = node["inputs"].get("device")
            if isinstance(candidate, str) and candidate:
                selected_device = candidate
                break
    if not selected_device:
        selected_device = profile.get("selected_device")
    observed = {"runtime_version": discovery.get("runtime_version"), "node_inventory_hash": discovery.get("node_inventory_hash"),
                "selected_device": selected_device}
    stable_resources = [{key: item.get(key) for key in ("id", "device_id", "type", "vram_total")}
                        for item in discovery.get("resource_inventory", []) if isinstance(item, dict)]
    observed["resource_context_hash"] = digest(stable_resources)
    runtime_context = discovery.get("runtime_context", {})
    if isinstance(runtime_context, dict):
        observed.update({key: runtime_context.get(key) for key in ("runtime_commit", "runtime_dirty", "custom_node_commits") if key in runtime_context})
    observed_model_hash = model_asset_hash or discovery.get("model_asset_hash")
    if observed_model_hash:
        observed["model_asset_hash"] = observed_model_hash
    if workflow is not None:
        observed["workflow_hash"] = digest(workflow)
        observed["workflow_fingerprint"] = workflow_fingerprint(workflow, discovery.get("object_info", {}))
    if discovery.get("profile_fingerprint"):
        observed["profile_fingerprint"] = discovery["profile_fingerprint"]
    triggers = profile_expiration_triggers(profile, observed)
    feature_report = None
    if feature:
        from vge_quality import validate_feature_profile
        feature_report = validate_feature_profile(profile, feature, observed=observed)
        triggers.extend(feature_report["reasons"])
    return {"status": "EXPIRED" if triggers else "CURRENT", "profile_id": profile.get("id"),
            "observed": observed, "expiration_triggers": sorted(set(triggers)), "feature": feature_report,
            "limitations": ["Runtime identity checks do not establish successful inference or audiovisual quality"]}


def _expanded_input_specs(input_schema, inputs):
    """Expand selected V3 dynamic-combo children into flat dotted API fields."""
    require(isinstance(input_schema, dict), "Runtime node metadata input must be an object")
    required = input_schema.get("required", {})
    optional = input_schema.get("optional", {})
    require(isinstance(required, dict) and isinstance(optional, dict), "Runtime node metadata inputs must be objects")
    expanded, required_fields = {}, set()

    def visit(prefix, entry, is_required):
        expanded[prefix] = entry
        if is_required:
            required_fields.add(prefix)
        if not isinstance(entry, (list, tuple)) or not entry or entry[0] != "COMFY_DYNAMICCOMBO_V3":
            return
        options = entry[1].get("options", []) if len(entry) > 1 and isinstance(entry[1], dict) else []
        if not isinstance(options, list):
            return
        selected = inputs.get(prefix)
        option = next((item for item in options if isinstance(item, dict) and item.get("key") == selected), None)
        if option is None:
            return
        child_schema = option.get("inputs", {})
        if not isinstance(child_schema, dict):
            return
        child_required = child_schema.get("required", {})
        child_optional = child_schema.get("optional", {})
        if not isinstance(child_required, dict) or not isinstance(child_optional, dict):
            return
        for child_name, child_entry in child_required.items():
            visit(f"{prefix}.{child_name}", child_entry, True)
        for child_name, child_entry in child_optional.items():
            visit(f"{prefix}.{child_name}", child_entry, False)

    for name, entry in required.items():
        visit(name, entry, True)
    for name, entry in optional.items():
        visit(name, entry, False)
    return expanded, required_fields


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
        spec, required_fields = _expanded_input_specs(input_schema, inputs)
        dependencies[key] = set()
        for field in required_fields:
            require(isinstance(field, str) and field, f"{key}: node metadata has an invalid input name")
            if field not in inputs:
                issues.append(f"{key}.{field}: required input missing")
        for field, value in inputs.items():
            entry = spec.get(field)
            if entry is None:
                # ComfyUI's auto-grow inputs are materialized as names such as
                # ref_images.ref_image_0 although only the group appears in
                # object_info. Resolve the template before type-checking the link.
                for group, candidate in spec.items():
                    if not isinstance(candidate, (list, tuple)) or not candidate or candidate[0] != "COMFY_AUTOGROW_V3":
                        continue
                    options = candidate[1] if len(candidate) > 1 else {}
                    template = options.get("template", {}) if isinstance(options, dict) else {}
                    prefix = options.get("prefix", "") if isinstance(options, dict) else ""
                    if isinstance(template, dict) and isinstance(prefix, str) and field.startswith(group + ".") and field.split(".", 1)[1].startswith(prefix):
                        template_input = template.get("input", {}).get("required", {}) if isinstance(template.get("input", {}), dict) else {}
                        if len(template_input) == 1:
                            entry = next(iter(template_input.values()))
                        break
            if entry is None:
                issues.append(f"{key}.{field}: unknown input")
                continue
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
    return {"status": "FAIL" if issues else "PASS", "issues": issues, "workflow_hash": digest(workflow),
            "workflow_fingerprint": workflow_fingerprint(workflow, node_info), "scope": "API_GRAPH_METADATA",
            "limitations": ["Execution, VRAM fit, hidden/dynamic node validation and visual quality require a runtime probe"]}


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
    if context_profile.get("content_hash") is not None:
        require(context_profile.get("content_hash") == digest(profile), "Caller profile content hash differs from the resolved profile record")
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
    accepted_dependency_refs = context.get("accepted_dependency_refs", [])
    require(isinstance(accepted_dependency_refs, list), "accepted_dependency_refs must be an array")
    for dependency_ref in accepted_dependency_refs:
        require(isinstance(dependency_ref, str) and dependency_ref, "accepted dependency reference must be a nonempty path")
        dependency_path = Path(dependency_ref)
        require(dependency_path.is_file(), f"Accepted dependency bundle is unavailable: {dependency_ref}")
        try:
            dependency_bundle = json.loads(dependency_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ContractError(f"Accepted dependency bundle cannot be read: {dependency_ref}") from exc
        require(isinstance(dependency_bundle, dict), "Accepted dependency bundle must be an object")
        accepted_dependencies.append(dependency_bundle)
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
    selected_device = context.get("selected_device")
    if selected_device is None:
        for node in workflow.values():
            if isinstance(node, dict) and node.get("class_type") == "ClipProjLoader" and isinstance(node.get("inputs"), dict):
                selected_device = node["inputs"].get("device")
                break
    require(isinstance(selected_device, str) and selected_device and selected_device != "UNKNOWN", "A selected device must be declared")
    selected_records = [item for item in observed.get("resource_inventory", []) if isinstance(item, dict) and
                        item.get("device_id") == selected_device]
    require(selected_records, "Selected device is not present in observed resource inventory")
    resource_requirements = context.get("resource_requirements")
    require(isinstance(resource_requirements, dict), "Execution context must declare resource_requirements")
    require(_declared_min_free_vram(resource_requirements) is not None,
            "resource_requirements must declare min_free_vram_bytes")
    declared_device = resource_requirements.get("device_id") or resource_requirements.get("selected_device")
    require(declared_device == selected_device, "resource_requirements must bind the selected device")
    resource_report = resource_status(observed, resource_requirements)
    # A degraded snapshot is still below the declared scheduling threshold.
    # The caller may record/inspect that state, but it cannot turn it into a
    # queue submission by setting an override in execution context.
    require(resource_report["status"] == "SUPPORTED",
            "; ".join(resource_report["gaps"]) or "Selected runtime resource is not supported")
    runtime_version = profile.get("runtime_version")
    if not (probe_mode and runtime_version in (None, "", "UNKNOWN")):
        require(runtime_version == system.get("comfyui_version"), "Runtime version differs from confirmed profile")
    inventory_hash = profile.get("node_inventory_hash")
    if not (probe_mode and inventory_hash in (None, "", "UNKNOWN")):
        require(isinstance(inventory_hash, str) and isinstance(observed.get("node_inventory_hash"), str) and inventory_hash == observed["node_inventory_hash"], "Node inventory differs from confirmed profile")
    validation = validate_workflow(workflow, observed["object_info"])
    require(validation["status"] == "PASS", "; ".join(validation["issues"]))
    profile_workflow_fingerprint = profile.get("workflow_fingerprint")
    if not (probe_mode and profile_workflow_fingerprint in (None, "", "UNKNOWN")) and profile_workflow_fingerprint is not None:
        require(profile_workflow_fingerprint == validation["workflow_fingerprint"], "Workflow fingerprint differs from confirmed profile")
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
    profile_device = profile.get("selected_device")
    if profile_device not in (None, "", "UNKNOWN", "UNPROBED"):
        require(profile_device == selected_device, "Selected device differs from the resolved profile")
    stable_resources = [{key: item.get(key) for key in ("id", "device_id", "type", "vram_total")}
                        for item in observed.get("resource_inventory", []) if isinstance(item, dict)]
    resource_context_hash = digest(stable_resources)
    profile_resource_hash = profile.get("resource_context_hash")
    if not (probe_mode and profile_resource_hash in (None, "", "UNKNOWN", "UNPROBED")) and profile_resource_hash is not None:
        require(profile_resource_hash == resource_context_hash, "Observed resources differ from the resolved profile")
    profile_identity = copy.deepcopy(profile)
    profile_identity["revision"] = context_profile["revision"]
    profile_identity["content_hash"] = digest(profile)
    attempt = {"schema_version": 1, "id": attempt_id, "revision": 1, "execution_plan_ref": context["execution_plan_ref"], "shot_id": context["shot_id"], "shot_contract_hash": digest(shot), "attempt_index": context["attempt_index"], "status": "UNKNOWN",
               "started_at": datetime.now(timezone.utc).isoformat(), "ended_at": None, "profile": profile_identity, "model": model,
               "runtime": {"provider": "comfyui", "endpoint": client.endpoint, "version": version, "node_inventory_hash": observed["node_inventory_hash"], "selected_device": selected_device, "resource_context_hash": resource_context_hash, "resource_snapshot": observed.get("resource_inventory", []), "resource_status": resource_report, "runtime_context": observed.get("runtime_context", {})},
               "workflow": {"ref": str((run / "workflow.json").resolve()), "content_hash": digest(workflow), "fingerprint": validation["workflow_fingerprint"], "prompt_ref": context["execution_plan_ref"], "queue_id": None},
               "nodes": node_records, "inputs": inputs, "parameters": context["parameters"], "progress_ref": str((run / "events.jsonl").resolve()), "error_ref": None, "unknown_fields": unknown + ["workflow.queue_id"]}
    attempt["purpose"] = "CAPABILITY_PROBE" if probe_mode else "GENERATION"
    save(run / "workflow.json", workflow)
    save(run / "attempt-001.json", attempt)
    save(run / "preflight.json", {"validation": validation, "compatibility": compatibility, "resource_status": resource_report,
                                  "discovery_hash": digest(observed), "probe_purpose": context.get("probe_purpose") if probe_mode else None})
    _append_event(run / "events.jsonl", {"schema_version": 1, "event_id": "event-intent-recorded", "attempt_id": attempt_id,
                                          "status": "INTENT_RECORDED", "observed_at": attempt["started_at"], "source": "vge_runtime.submit"})
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
        _append_event(run / "events.jsonl", {"schema_version": 1, "event_id": "event-submitted", "attempt_id": attempt_id,
                                              "queue_id": response["prompt_id"], "status": "SUBMITTED",
                                              "observed_at": datetime.now(timezone.utc).isoformat(), "source": "vge_runtime.submit"})
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
    sealed_graph_path = Path(attempt["workflow"]["ref"])
    require(sealed_graph_path.is_file(), "Sealed workflow graph is unavailable")
    try:
        sealed_workflow = json.loads(sealed_graph_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError("Sealed workflow graph cannot be read") from exc
    require(isinstance(submitted_prompt, list) and len(submitted_prompt) >= 3
            and submitted_prompt[1] == history["prompt_id"]
            and _workflow_equivalent(sealed_workflow, submitted_prompt[2]),
            "Runtime history does not match the sealed workflow")
    out = Path(destination)
    out.mkdir(parents=True, exist_ok=True)
    history_path = out / (attempt["id"] + "-history.json")
    save(history_path, history)
    completed = copy.deepcopy(attempt)
    completed.update(status="SUCCEEDED", revision=attempt.get("revision", 1)+1, supersedes_hash=digest(attempt), ended_at=datetime.now(timezone.utc).isoformat())
    records = []
    output_entries = []
    outputs_by_node = raw.get("outputs", {})
    require(isinstance(outputs_by_node, dict), "Runtime history outputs must be an object")
    for node, outputs in outputs_by_node.items():
        require(isinstance(outputs, dict), "Runtime node outputs must be objects")
        for kind in ("images", "gifs", "videos", "audio"):
            entries = outputs.get(kind, [])
            require(isinstance(entries, list), f"Runtime {kind} outputs must be an array")
            for output in entries:
                # ComfyUI's historical output bucket is not a media type: an
                # MP4 may be returned under ``images``. Classify by the sealed
                # filename extension and retain the runtime bucket separately.
                suffix = Path(output.get("filename", "")).suffix.lower() if isinstance(output, dict) else ""
                media_kind = "video" if suffix in (".mp4", ".mov", ".mkv", ".webm") else "gif" if suffix == ".gif" else "audio" if suffix in (".wav", ".mp3", ".flac", ".m4a", ".ogg") else "image"
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
                artifact = {"schema_version": 1, "id": aid, "shot_id": attempt["shot_id"], "execution_attempt_ref": attempt["id"], "artifact_ref": str(path.resolve()), "content_hash": file_hash(path), "collected_at": datetime.now(timezone.utc).isoformat(), "generation_status": "GENERATED", "media": {"kind": media_kind, "runtime_output_kind": kind},
                            # Keep the execution binding directly on the
                            # immutable artifact record as well as in the
                            # runtime envelope.  This makes the collected
                            # record self-describing for independent review.
                            "shot_contract_hash": attempt["shot_contract_hash"],
                            "profile_id": attempt["profile"].get("id"),
                            "profile_revision": attempt["profile"].get("revision"),
                            "profile_content_hash": attempt["profile"].get("content_hash"),
                            "model_asset_hash": attempt["model"].get("asset_hash"),
                            "input_hashes": copy.deepcopy(attempt.get("inputs", [])),
                            "runtime": {"provider": "comfyui", "endpoint": client.endpoint, "workflow_hash": attempt["workflow"]["content_hash"], "runtime_history_workflow_hash": digest(submitted_prompt[2]), "workflow_fingerprint": attempt["workflow"].get("fingerprint"), "shot_contract_hash": attempt["shot_contract_hash"], "profile_id": attempt["profile"].get("id"), "profile_revision": attempt["profile"].get("revision"), "profile_content_hash": attempt["profile"].get("content_hash"), "model_asset_hash": attempt["model"].get("asset_hash"), "input_hashes": copy.deepcopy(attempt.get("inputs", [])), "selected_device": attempt["runtime"].get("selected_device"), "resource_context_hash": attempt["runtime"].get("resource_context_hash"), "runtime_context": copy.deepcopy(attempt["runtime"].get("runtime_context", {}))}, "runtime_output": {"node_id": str(node), "bucket": kind, "filename": name, "subfolder": folder, "type": output.get("type", "output"), "content_hash": file_hash(path)}, "quality_review": {"lifecycle": "NOT_STARTED", "observation_ref": None}}
                save(out / (aid + ".json"), artifact)
                records.append(artifact)
                output_entries.append({"artifact_id": aid, "node_id": str(node), "bucket": kind,
                                       "filename": name, "subfolder": folder,
                                       "type": output.get("type", "output"),
                                       "content_hash": artifact["content_hash"]})
    require(records, "Job completed without collectible outputs")
    progress_path = Path(attempt["progress_ref"])
    require(progress_path.is_file(), "Runtime event log is unavailable for collection")
    _append_event(progress_path, {"schema_version": 1, "event_id": "event-collected", "attempt_id": attempt["id"],
                                  "queue_id": history["prompt_id"], "status": "COLLECTED",
                                  "history_ref": str(history_path.resolve()),
                                  "history_content_hash": file_hash(history_path),
                                  "artifact_ids": [item["id"] for item in records],
                                  "observed_at": completed["ended_at"], "source": "vge_runtime.collect"})
    completed["collection"] = {
        "schema_version": 1, "status": "COLLECTED", "collector": "vge_runtime.collect",
        "prompt_id": history["prompt_id"], "history_ref": str(history_path.resolve()),
        "history_content_hash": file_hash(history_path), "history_output_hash": digest(outputs_by_node),
        "event_log_ref": str(progress_path.resolve()), "event_log_content_hash": file_hash(progress_path),
        "output_entries": output_entries,
        "artifacts": [{"id": item["id"], "record_ref": str((out / (item["id"] + ".json")).resolve()),
                       "record_content_hash": file_hash(out / (item["id"] + ".json")),
                       "artifact_ref": item["artifact_ref"], "content_hash": item["content_hash"]}
                      for item in records],
        "collected_at": completed["ended_at"],
    }
    completed["artifacts"] = copy.deepcopy(completed["collection"]["artifacts"])
    validate_attempt(completed)
    save(out / (attempt["id"] + "-completed.json"), completed)
    return records
