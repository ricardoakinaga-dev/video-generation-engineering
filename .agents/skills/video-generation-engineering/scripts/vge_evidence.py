"""Immutable provenance and current observation acceptance."""
from datetime import datetime, timezone
import re

from vge_core import ContractError, digest, file_hash, indexed, load, require, string_list


def timestamp(value):
    require(isinstance(value, str), "Timestamp required")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractError("Invalid timestamp") from exc
    require(result.tzinfo is not None, "Timestamp requires timezone")
    return result


def hash_value(value):
    return isinstance(value, str) and bool(re.fullmatch(r"sha256:[0-9a-f]{64}", value))


def _clock(now):
    now = now or datetime.now(timezone.utc)
    require(isinstance(now, datetime) and now.tzinfo is not None and now.utcoffset() is not None, "Evaluation time requires timezone")
    return now


def aggregate(checks, artifact_id=None, now=None):
    now = _clock(now)
    indexed(checks, "checks")
    if not checks:
        return "NOT_RUN"
    results = []
    for check in checks:
        require(type(check.get("required")) is bool, "Every check needs explicit required boolean")
        result = check.get("result")
        require(result in ("PASS", "FAIL", "PARTIAL", "BLOCKED", "NOT_RUN", "WAIVED", "NOT_APPLICABLE"), "Invalid check result")
        if result == "WAIVED":
            waiver = check.get("waiver", {})
            require(isinstance(waiver, dict), f"{check['id']}: waiver must be an object")
            valid = all(waiver.get(k) for k in ("reason", "authority", "expires_at", "scope"))
            if valid:
                valid = timestamp(waiver["expires_at"]) > now and waiver["scope"] == {"artifact_id": artifact_id, "check_id": check["id"]}
            result = "PASS" if valid else "BLOCKED"
        if result == "NOT_APPLICABLE":
            result = "BLOCKED" if check["required"] or not check.get("reason") else "NOT_APPLICABLE"
        if result in ("PASS", "PARTIAL", "FAIL") and check.get("result") != "WAIVED":
            require(bool(check.get("evidence")), f"{check['id']}: executed check needs evidence")
        results.append(result)
    if "FAIL" in results:
        return "FAIL"
    if "BLOCKED" in results:
        return "BLOCKED"
    if all(r in ("NOT_RUN", "NOT_APPLICABLE") for r in results):
        return "NOT_RUN"
    if any(r in ("PARTIAL", "NOT_RUN") for r in results):
        return "PARTIAL"
    return "PASS" if any(c["required"] for c in checks) else "PARTIAL"


def validate_attempt(attempt):
    require(isinstance(attempt, dict), "attempt must be an object")
    require(attempt.get("schema_version") == 1, "Unsupported attempt schema")
    for name in ("id", "execution_plan_ref", "shot_id", "shot_contract_hash", "profile", "model", "runtime", "workflow", "nodes", "parameters", "started_at", "progress_ref"):
        require(bool(attempt.get(name)), f"Missing attempt provenance: {name}")
    require(type(attempt.get("attempt_index")) is int and attempt["attempt_index"] > 0, "Invalid attempt index")
    require(attempt.get("status") in ("SUBMITTED", "RUNNING", "SUCCEEDED", "FAILED", "CANCELLED", "UNKNOWN"), "Invalid attempt status")
    timestamp(attempt["started_at"])
    require(hash_value(attempt.get("shot_contract_hash")), "Invalid shot_contract_hash")
    if attempt.get("ended_at") is not None:
        timestamp(attempt["ended_at"])
    if attempt.get("status") in ("SUCCEEDED", "FAILED", "CANCELLED"):
        require(attempt.get("ended_at") is not None, "Terminal attempt requires ended_at")
    for owner in ("profile", "model", "runtime", "workflow"):
        require(isinstance(attempt.get(owner), dict), f"Attempt {owner} must be an object")
    for path in ("profile.id", "profile.revision", "model.id", "model.version", "runtime.provider", "runtime.endpoint", "runtime.version", "workflow.ref", "workflow.queue_id"):
        owner, field = path.split(".")
        require(attempt[owner].get(field) not in (None, "", "UNKNOWN"), f"Unknown required provenance: {path}")
    require(type(attempt["profile"]["revision"]) is int and attempt["profile"]["revision"] > 0, "Invalid profile revision")
    if attempt.get("purpose") in ("CAPABILITY_PROBE", "GENERATION"):
        declared_profile_hash = attempt["profile"].get("content_hash")
        require(hash_value(declared_profile_hash), "Runtime attempt lacks exact profile content hash")
        profile_snapshot = dict(attempt["profile"])
        profile_snapshot.pop("content_hash", None)
        profile_snapshot.pop("revision", None)
        require(digest(profile_snapshot) == declared_profile_hash, "Runtime attempt profile snapshot hash mismatch")
        require(hash_value(attempt["workflow"].get("content_hash")), "Runtime attempt lacks exact workflow content hash")
        require(hash_value(attempt["workflow"].get("fingerprint")), "Runtime attempt lacks exact workflow fingerprint")
        require(digest(load(attempt["workflow"].get("ref"))) == attempt["workflow"]["content_hash"], "Runtime workflow content changed since submission")
        require(isinstance(attempt["runtime"].get("selected_device"), str) and attempt["runtime"]["selected_device"] not in ("", "UNKNOWN"), "Runtime attempt lacks selected device provenance")
        require(hash_value(attempt["runtime"].get("resource_context_hash")), "Runtime attempt lacks resource context hash")
    for owner, field in (("model", "asset_hash"), ("runtime", "node_inventory_hash"), ("workflow", "content_hash")):
        require(hash_value(attempt[owner].get(field)), f"Invalid {owner}.{field}")
    require(isinstance(attempt.get("inputs"), list), "inputs must be explicit, including [] for text-only")
    for item in attempt["inputs"]:
        require(isinstance(item, dict), "Each input provenance record must be an object")
        require(bool(item.get("ref")) and bool(item.get("role")) and hash_value(item.get("content_hash")), "Input lacks ref/role/hash")
    require(isinstance(attempt["nodes"], list), "nodes must be an array")
    for node in attempt["nodes"]:
        require(isinstance(node, dict), "Each node provenance record must be an object")
        require(all(node.get(k) not in (None, "", "UNKNOWN") for k in ("id", "type", "version")), "Node version provenance missing")
    unknown_fields = attempt.get("unknown_fields", [])
    string_list(unknown_fields, "unknown_fields")
    require(not unknown_fields, "Unknown execution fields prevent reproducibility/acceptance in this implementation")


def validate_observation(observation, artifact, attempt, shot, now=None):
    now = _clock(now)
    require(isinstance(observation, dict), "observation must be an object")
    require(isinstance(artifact, dict), "artifact must be an object")
    require(isinstance(shot, dict), "Acceptance requires the canonical shot contract")
    require(isinstance(shot.get("id"), str) and shot["id"], "Canonical shot id is required for acceptance")
    require(type(shot.get("revision")) is int and shot["revision"] > 0, "Canonical shot revision is required for acceptance")
    required_ids = string_list(shot.get("acceptance_ids"), "shot.acceptance_ids", allow_empty=False)
    require(len(required_ids) == len(set(required_ids)), "Canonical shot acceptance_ids must be unique")
    require(all(item in {f"QG-{i:02d}" for i in range(1, 18)} for item in required_ids), "Canonical shot acceptance_ids contains an unknown gate")
    validate_attempt(attempt)
    require(attempt["status"] == "SUCCEEDED", "Acceptance requires a completed successful attempt")
    require(attempt.get("purpose") != "CAPABILITY_PROBE", "Capability-probe artifacts are evidence for profile activation, not production acceptance")
    require(artifact.get("schema_version") == 1, "Unsupported artifact schema")
    require(isinstance(artifact.get("id"), str) and artifact["id"], "Artifact id is required")
    require(isinstance(artifact.get("artifact_ref"), str) and artifact["artifact_ref"], "Artifact locator is required")
    require(artifact.get("execution_attempt_ref") == attempt["id"], "Artifact/attempt mismatch")
    require(shot["id"] == attempt["shot_id"], "Canonical shot/attempt mismatch")
    from vge_core import digest
    require(digest(shot) == attempt["shot_contract_hash"], "Canonical shot differs from immutable execution attempt")
    require(artifact.get("shot_id") == attempt["shot_id"], "Artifact/attempt shot mismatch")
    require(artifact.get("generation_status") == "GENERATED", "Artifact must be a collected generated output")
    media = artifact.get("media")
    require(isinstance(media, dict) and isinstance(media.get("kind"), str) and media["kind"] in ("video", "image", "audio", "gif"), "Artifact media contract is missing")
    require(isinstance(artifact.get("runtime"), dict), "Artifact runtime must be an object")
    require(artifact["runtime"].get("workflow_hash") == attempt["workflow"]["content_hash"], "Workflow provenance mismatch")
    require(hash_value(artifact.get("content_hash")), "Artifact hash missing")
    require(timestamp(attempt["started_at"]) <= timestamp(attempt.get("ended_at")) <= timestamp(artifact.get("collected_at")), "Attempt/collection chronology invalid")
    require(file_hash(artifact["artifact_ref"]) == artifact["content_hash"], "Artifact bytes changed; recollect and re-observe")
    require(isinstance(observation.get("id"), str) and observation["id"], "Observation id is required")
    require(observation.get("generation_artifact_ref") == artifact.get("id"), "Observation/artifact mismatch")
    require(observation.get("shot_id") == artifact.get("shot_id"), "Observation/shot mismatch")
    require(observation.get("artifact_ref") == artifact["artifact_ref"], "Observation locator mismatch")
    require(observation.get("observed_content_hash") == artifact["content_hash"], "Observed hash mismatch")
    require(bool(observation.get("procedure")), "Executed observation requires procedure")
    require(isinstance(observation.get("repair_route"), str) and observation["repair_route"], "Executed observation requires repair_route")
    require(isinstance(observation.get("limitations", []), list), "Observation limitations must be an array")
    observed = timestamp(observation.get("observed_at"))
    require(timestamp(artifact.get("collected_at")) <= observed <= now, "Observation timestamp precedes collection or is in the future")
    checks = indexed(observation.get("checks", []), "checks")
    require(all(k in checks and checks[k].get("required") is True for k in required_ids), "Required checks missing or downgraded to optional")
    status = aggregate(list(checks.values()), artifact["id"], now)
    require(observation.get("status") == status, "Observation aggregate is inconsistent")
    return {"status": status, "accepted": status == "PASS", "artifact_id": artifact["id"], "limitations": observation.get("limitations", [])}


def lifecycle(current, event):
    """A pending QA event never regresses runtime lifecycle."""
    if event == "NOT_RUN":
        return current
    transitions = {("PLANNED", "PLAN_VALIDATED"): "READY", ("READY", "SUBMITTED"): "RUNNING",
                   ("RUNNING", "COLLECTED"): "GENERATED", ("GENERATED", "REVIEW_STARTED"): "REVIEW",
                   ("REVIEW", "QA_PASS"): "ACCEPTED", ("REVIEW", "QA_FAIL"): "REGEN_REQUIRED",
                   ("REVIEW", "QA_PARTIAL"): "REVIEW", ("ACCEPTED", "STALE"): "REGEN_REQUIRED"}
    require((current, event) in transitions, f"Illegal lifecycle transition: {current}/{event}")
    return transitions[current, event]
