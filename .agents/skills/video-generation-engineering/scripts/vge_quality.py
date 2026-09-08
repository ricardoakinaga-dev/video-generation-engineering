"""Deterministic production-quality contracts for the video-generation Skill.

This module deliberately does not infer visual truth from prompts or metadata.  It
validates the shape and provenance of observations, continuity decisions, repair
budgets and adapter reports.  Media decoding remains in :mod:`vge_media` and
runtime authority remains in :mod:`vge_runtime`.
"""
from __future__ import annotations

import copy
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path

from vge_core import ContractError, canonical, digest, file_hash, indexed, number, require, repair_scope


QUALITY_STATUSES = (
    "PASS", "FAIL", "PARTIAL", "NOT_APPLICABLE", "NOT_OBSERVED", "NOT_RUN", "UNKNOWN", "BLOCKED"
)
SCORECARD_STATUSES = ("PASS", "FAIL", "PARTIAL", "NOT_APPLICABLE", "NOT_OBSERVED")
CONFIDENCE = ("HIGH", "MEDIUM", "LOW", "UNKNOWN")
OBSERVATION_CATEGORIES = ("metadata", "visual", "temporal", "audio", "continuity", "editorial")
ORACLE_KINDS = ("METADATA", "FRAME", "SEQUENCE", "AUDIO", "HUMAN", "ALGORITHMIC", "RUNTIME", "DOCUMENT")
CONTINUITY_DIMENSIONS = (
    "identity", "wardrobe", "hair", "object_state_ownership", "vehicle", "environment", "lighting",
    "screen_direction", "camera_geography", "gaze", "emotional", "dialogue", "temporal", "audio"
)
CONTACT_PHASES = (
    "APPROACH", "PRE_CONTACT", "CONTACT", "FORCE_OR_ARTICULATION", "TRANSFER_OR_MOTION", "RELEASE", "RESULT"
)
CAUSAL_STAGES = ("STIMULUS", "PROCESSING", "REACTION", "RESPONSE")
AUDIO_LAYERS = (
    "dialogue", "foley", "ambience", "room_tone", "vehicle", "animal", "music", "transition",
    "non_diegetic", "silence"
)
AUDIO_LAYER_ALIASES = {"effects": "foley"}
REANCHOR_ACTIONS = ("CONTINUE", "RE_ANCHOR", "RESET", "REGENERATE", "SPLIT")
REPAIR_OWNERS = (
    "reference_conditioning", "continuity", "cinematography", "adapter", "shot_decomposition",
    "dialogue", "audio", "performance", "human_review"
)
MATURITY_LEVELS = {
    0: "INTENT_ONLY",
    1: "STRUCTURAL_PLAN",
    2: "DETERMINISTIC_VERIFICATION",
    3: "RUNTIME_PROVENANCE",
    4: "AUDIOVISUAL_EVALUATION",
    5: "REPEATABLE_BOUNDED_PRODUCTION",
}


def _object(value, label):
    require(isinstance(value, dict), f"{label} must be an object")
    return value


def _nonempty(value, label):
    require(isinstance(value, str) and bool(value.strip()), f"{label} must be a nonempty string")
    return value


def _alias_value(record, names, label, required=True):
    """Read a canonical field while preserving backwards-compatible aliases."""
    present = [(name, record[name]) for name in names if name in record and record[name] is not None]
    if not present:
        require(not required, f"{label} is required")
        return None
    first = present[0][1]
    for name, value in present[1:]:
        require(value == first, f"{label} aliases disagree: {present[0][0]} vs {name}")
    return first


def _list(value, label, allow_empty=True):
    require(isinstance(value, list), f"{label} must be an array")
    require(allow_empty or bool(value), f"{label} must be nonempty")
    return value


def _status(value, label="status", allowed=QUALITY_STATUSES):
    require(value in allowed, f"{label} must be one of {', '.join(allowed)}")
    return value


def _hash(value, label):
    require(isinstance(value, str) and re.fullmatch(r"sha256:[0-9a-f]{64}", value), f"{label} must be a SHA-256 digest")
    return value


def _timestamp(value, label):
    _nonempty(value, label)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractError(f"{label} must be an ISO-8601 timestamp") from exc
    require(parsed.tzinfo is not None and parsed.utcoffset() is not None, f"{label} must include a timezone")
    return parsed


def _evidence(value, label, required=True):
    """Validate an evidence list while accepting a legacy short string."""
    if isinstance(value, str) and value:
        value = [{"type": "TEXT", "ref": value}]
    _list(value, label, allow_empty=not required)
    for index, item in enumerate(value):
        _object(item, f"{label}[{index}]")
        _nonempty(item.get("type"), f"{label}[{index}].type")
        _nonempty(item.get("ref"), f"{label}[{index}].ref")
        if "content_hash" in item:
            _hash(item["content_hash"], f"{label}[{index}].content_hash")
        if "time_s" in item:
            require(number(item["time_s"]) and item["time_s"] >= 0, f"{label}[{index}].time_s must be nonnegative")
    return value


def _oracle(value, label):
    _object(value, label)
    require(value.get("kind") in ORACLE_KINDS, f"{label}.kind must identify a supported oracle")
    _nonempty(value.get("question"), f"{label}.question")
    if "version" in value:
        _nonempty(value["version"], f"{label}.version")
    return value


def _verify_observed_bytes(ref, expected_hash, label, required=False):
    """Verify bytes when an observation claims an exact artifact.

    Structural reports may describe an unavailable artifact with a non-PASS
    status.  Any PASS, however, must be backed by bytes that exist now and
    hash to the declared value; a made-up locator or hash is never acceptance
    evidence.
    """
    path = Path(ref)
    if not path.is_file():
        require(not required, f"{label}: PASS requires existing artifact bytes")
        return False
    require(file_hash(path) == expected_hash, f"{label}: artifact bytes changed since observation")
    return True


def _verify_evidence_bytes(evidence, label, required=False):
    """Require hash-bound evidence for an observed quality claim."""
    for index, item in enumerate(evidence):
        if "content_hash" not in item:
            require(not required, f"{label}[{index}] needs content_hash")
            continue
        if required:
            _verify_observed_bytes(item["ref"], item["content_hash"], f"{label}[{index}]", required=True)


def _quality_provenance(value, label, shot_id=None, artifact_id=None, artifact_ref=None, artifact_hash=None):
    """Bind a quality PASS to a successful attempt, shot contract and generated bytes."""
    provenance = _object(value, label)
    attempt = _object(provenance.get("attempt"), f"{label}.attempt")
    shot = _object(provenance.get("shot"), f"{label}.shot")
    artifact = _object(provenance.get("artifact"), f"{label}.artifact")
    _nonempty(attempt.get("id"), f"{label}.attempt.id")
    _nonempty(attempt.get("ref"), f"{label}.attempt.ref")
    _hash(attempt.get("content_hash"), f"{label}.attempt.content_hash")
    _verify_observed_bytes(attempt["ref"], attempt["content_hash"], f"{label}.attempt", required=True)
    _nonempty(shot.get("id"), f"{label}.shot.id")
    _nonempty(shot.get("ref"), f"{label}.shot.ref")
    _hash(shot.get("content_hash"), f"{label}.shot.content_hash")
    _hash(shot.get("contract_hash"), f"{label}.shot.contract_hash")
    _verify_observed_bytes(shot["ref"], shot["content_hash"], f"{label}.shot", required=True)
    _nonempty(artifact.get("id"), f"{label}.artifact.id")
    _nonempty(artifact.get("record_ref"), f"{label}.artifact.record_ref")
    _hash(artifact.get("record_content_hash"), f"{label}.artifact.record_content_hash")
    _verify_observed_bytes(artifact["record_ref"], artifact["record_content_hash"], f"{label}.artifact.record", required=True)
    _nonempty(artifact.get("media_ref"), f"{label}.artifact.media_ref")
    _hash(artifact.get("media_content_hash"), f"{label}.artifact.media_content_hash")
    _verify_observed_bytes(artifact["media_ref"], artifact["media_content_hash"], f"{label}.artifact.media", required=True)
    try:
        attempt_record = json.loads(Path(attempt["ref"]).read_text(encoding="utf-8"))
        shot_record = json.loads(Path(shot["ref"]).read_text(encoding="utf-8"))
        artifact_record = json.loads(Path(artifact["record_ref"]).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError(f"{label} provenance JSON cannot be read") from exc
    _object(attempt_record, f"{label}.attempt.record")
    _object(shot_record, f"{label}.shot.record")
    _object(artifact_record, f"{label}.artifact.record")
    from vge_evidence import validate_attempt
    validate_attempt(attempt_record)
    require(attempt_record.get("id") == attempt["id"], f"{label}: attempt id does not match its immutable record")
    require(attempt_record.get("status") == "SUCCEEDED", f"{label}: quality PASS requires a successful attempt")
    require(shot_record.get("id") == shot["id"], f"{label}: shot id does not match its immutable record")
    require(digest(shot_record) == shot["contract_hash"], f"{label}: shot contract hash does not match its bytes")
    require(attempt_record.get("shot_contract_hash") == shot["contract_hash"], f"{label}: attempt is not bound to the shot contract")
    require(artifact_record.get("id") == artifact["id"], f"{label}: artifact id does not match its immutable record")
    require(artifact_record.get("execution_attempt_ref") == attempt["id"], f"{label}: artifact is not bound to the attempt")
    require(artifact_record.get("shot_id") == shot["id"], f"{label}: artifact is not bound to the shot")
    require(artifact_record.get("artifact_ref") == artifact["media_ref"], f"{label}: artifact media locator mismatch")
    require(artifact_record.get("content_hash") == artifact["media_content_hash"], f"{label}: artifact media hash mismatch")
    require(artifact_record.get("generation_status") == "GENERATED", f"{label}: quality PASS requires a generated artifact")
    media = _object(artifact_record.get("media"), f"{label}.artifact.record.media")
    require(media.get("kind") in ("video", "image", "audio", "gif"), f"{label}: generated artifact has no supported media kind")
    require(attempt_record.get("shot_id") == shot["id"], f"{label}: attempt/shot mismatch")
    if shot_id is not None:
        require(shot["id"] == shot_id, f"{label}: provenance shot differs from the quality record")
    if artifact_id is not None:
        require(artifact["id"] == artifact_id, f"{label}: provenance artifact differs from the quality record")
    if artifact_ref is not None:
        require(artifact["media_ref"] == artifact_ref, f"{label}: provenance artifact locator differs from the quality record")
    if artifact_hash is not None:
        require(artifact["media_content_hash"] == artifact_hash, f"{label}: provenance artifact hash differs from the quality record")
    return {"attempt_id": attempt["id"], "shot_id": shot["id"], "artifact_id": artifact["id"],
            "artifact_ref": artifact["media_ref"], "artifact_content_hash": artifact["media_content_hash"]}


def _check(check, label, allowed=QUALITY_STATUSES):
    _object(check, label)
    _nonempty(check.get("id"), f"{label}.id")
    _status(check.get("result"), f"{label}.result", allowed)
    _nonempty(check.get("category"), f"{label}.category")
    require(check["category"] in OBSERVATION_CATEGORIES, f"{label}.category is not a supported observation category")
    _oracle(check.get("oracle"), f"{label}.oracle")
    confidence = check.get("confidence", "UNKNOWN")
    require(confidence in CONFIDENCE, f"{label}.confidence is invalid")
    if check["result"] in ("PASS", "FAIL", "PARTIAL"):
        evidence = _evidence(check.get("evidence"), f"{label}.evidence")
        _verify_evidence_bytes(evidence, f"{label}.evidence", required=True)
    elif check["result"] in ("NOT_OBSERVED", "NOT_APPLICABLE", "NOT_RUN", "UNKNOWN", "BLOCKED"):
        _nonempty(check.get("reason"), f"{label}.reason")
        _evidence(check.get("evidence", []), f"{label}.evidence", required=False)
    if check["result"] == "PASS":
        require(confidence != "UNKNOWN", f"{label}: PASS cannot have UNKNOWN confidence")
    require(isinstance(check.get("limitations", []), list), f"{label}.limitations must be an array")
    return check


def aggregate_quality(checks):
    """Aggregate exact observed statuses without treating missing evidence as PASS."""
    _list(checks, "checks")
    if not checks:
        return "NOT_OBSERVED"
    results = [check.get("result") for check in checks]
    require(all(result in QUALITY_STATUSES for result in results), "Invalid quality check result")
    if "FAIL" in results:
        return "FAIL"
    if "BLOCKED" in results:
        return "BLOCKED"
    if "PARTIAL" in results:
        return "PARTIAL"
    if any(result in ("NOT_RUN", "UNKNOWN") for result in results):
        return "PARTIAL" if any(result == "PASS" for result in results) else "NOT_OBSERVED"
    if "NOT_OBSERVED" in results:
        return "PARTIAL" if any(result == "PASS" for result in results) else "NOT_OBSERVED"
    if all(result == "NOT_APPLICABLE" for result in results):
        return "NOT_APPLICABLE"
    return "PASS" if all(result in ("PASS", "NOT_APPLICABLE") for result in results) else "PARTIAL"


def validate_observation_contract(observation, artifact=None, required_categories=None):
    """Validate category-separated semantic/editorial observation evidence.

    The function binds every observation to the exact artifact locator and hash
    supplied by the caller.  It intentionally cannot inspect pixels or sound;
    its oracle/evidence fields describe how an external inspection was done.
    """
    _object(observation, "observation")
    require(observation.get("schema_version") == 1, "Unsupported quality observation schema")
    _nonempty(observation.get("id"), "observation.id")
    _nonempty(observation.get("shot_id"), "observation.shot_id")
    _nonempty(observation.get("artifact_id"), "observation.artifact_id")
    _nonempty(observation.get("artifact_ref"), "observation.artifact_ref")
    _hash(observation.get("observed_content_hash"), "observation.observed_content_hash")
    _timestamp(observation.get("observed_at"), "observation.observed_at")
    _nonempty(observation.get("procedure"), "observation.procedure")
    checks = _list(observation.get("checks"), "observation.checks", allow_empty=False)
    for index, check in enumerate(checks):
        _check(check, f"observation.checks[{index}]")
    categories = list(required_categories) if required_categories is not None else list(OBSERVATION_CATEGORIES)
    _list(categories, "required_categories", allow_empty=False)
    require(all(category in OBSERVATION_CATEGORIES for category in categories), "Unknown required observation category")
    present = {check["category"] for check in checks}
    missing = sorted(set(categories) - present)
    if missing:
        raise ContractError("Missing observation categories: " + ", ".join(missing))
    status = aggregate_quality(checks)
    require(observation.get("status") == status, "Observation quality aggregate is inconsistent")
    if artifact is not None:
        _object(artifact, "artifact")
        require(observation["artifact_id"] == artifact.get("id"), "Observation/artifact id mismatch")
        require(observation["artifact_ref"] == artifact.get("artifact_ref"), "Observation/artifact locator mismatch")
        require(observation["observed_content_hash"] == artifact.get("content_hash"), "Observation/artifact hash mismatch")
        _verify_observed_bytes(artifact["artifact_ref"], artifact["content_hash"], "artifact", required=status in ("PASS", "FAIL", "PARTIAL"))
    else:
        _verify_observed_bytes(observation["artifact_ref"], observation["observed_content_hash"], "observation", required=status in ("PASS", "FAIL", "PARTIAL"))
    if status == "PASS":
        _quality_provenance(observation.get("provenance"), "observation.provenance", shot_id=observation["shot_id"],
                            artifact_id=observation["artifact_id"], artifact_ref=observation["artifact_ref"],
                            artifact_hash=observation["observed_content_hash"])
    return {
        "status": status,
        "accepted": status == "PASS",
        "artifact_id": observation["artifact_id"],
        "categories_observed": sorted(present),
        "missing_categories": missing,
        "limitations": list(observation.get("limitations", [])),
    }


def validate_semantic_observation(observation, artifact=None, required_categories=None):
    """Explicit semantic-QA alias used by the CLI and release reports."""
    result = validate_observation_contract(observation, artifact, required_categories)
    if result["status"] == "PASS":
        checks = observation["checks"]
        require(all(check["oracle"]["kind"] in ORACLE_KINDS for check in checks), "Semantic PASS lacks a valid oracle")
    return result


def _dimension_record(record, label):
    _object(record, label)
    _nonempty(record.get("dimension"), f"{label}.dimension")
    require(record["dimension"] in CONTINUITY_DIMENSIONS, f"{label}.dimension is not canonical")
    _status(record.get("result"), f"{label}.result", SCORECARD_STATUSES)
    _oracle(record.get("oracle"), f"{label}.oracle")
    confidence = record.get("confidence", "UNKNOWN")
    require(confidence in CONFIDENCE, f"{label}.confidence is invalid")
    if record["result"] in ("PASS", "FAIL", "PARTIAL"):
        evidence = _evidence(record.get("evidence"), f"{label}.evidence")
        _verify_evidence_bytes(evidence, f"{label}.evidence", required=True)
    else:
        _nonempty(record.get("reason"), f"{label}.reason")
        _evidence(record.get("evidence", []), f"{label}.evidence", required=False)
    if record["result"] == "PASS":
        require(confidence != "UNKNOWN", f"{label}: PASS cannot have UNKNOWN confidence")
    require(isinstance(record.get("limitations", []), list), f"{label}.limitations must be an array")
    return record


def validate_continuity_scorecard(scorecard, artifact=None, required_dimensions=None):
    """Validate the 14-dimension continuity scorecard and its evidence boundary."""
    _object(scorecard, "scorecard")
    require(scorecard.get("schema_version") == 1, "Unsupported continuity scorecard schema")
    _nonempty(scorecard.get("id"), "scorecard.id")
    _nonempty(scorecard.get("shot_id"), "scorecard.shot_id")
    _nonempty(scorecard.get("artifact_id"), "scorecard.artifact_id")
    _nonempty(scorecard.get("artifact_ref"), "scorecard.artifact_ref")
    _hash(scorecard.get("observed_content_hash"), "scorecard.observed_content_hash")
    _timestamp(scorecard.get("observed_at"), "scorecard.observed_at")
    required = tuple(required_dimensions or CONTINUITY_DIMENSIONS)
    require(set(required) <= set(CONTINUITY_DIMENSIONS), "Unknown continuity dimension")
    dimensions = _list(scorecard.get("dimensions"), "scorecard.dimensions", allow_empty=False)
    seen = set()
    for index, dimension in enumerate(dimensions):
        _dimension_record(dimension, f"scorecard.dimensions[{index}]")
        require(dimension["dimension"] not in seen, f"Duplicate continuity dimension: {dimension['dimension']}")
        seen.add(dimension["dimension"])
    missing = sorted(set(required) - seen)
    require(not missing, "Missing continuity dimensions: " + ", ".join(missing))
    status = aggregate_quality([{"result": item["result"]} for item in dimensions])
    require(scorecard.get("status") == status, "Continuity scorecard aggregate is inconsistent")
    if artifact is not None:
        require(scorecard["artifact_id"] == artifact.get("id"), "Scorecard/artifact id mismatch")
        require(scorecard["artifact_ref"] == artifact.get("artifact_ref"), "Scorecard/artifact locator mismatch")
        require(scorecard["observed_content_hash"] == artifact.get("content_hash"), "Scorecard/artifact hash mismatch")
        _verify_observed_bytes(artifact["artifact_ref"], artifact["content_hash"], "scorecard artifact", required=status in ("PASS", "FAIL", "PARTIAL"))
    else:
        _verify_observed_bytes(scorecard["artifact_ref"], scorecard["observed_content_hash"], "scorecard", required=status in ("PASS", "FAIL", "PARTIAL"))
    if status == "PASS":
        _quality_provenance(scorecard.get("provenance"), "scorecard.provenance", shot_id=scorecard["shot_id"],
                            artifact_id=scorecard["artifact_id"], artifact_ref=scorecard["artifact_ref"],
                            artifact_hash=scorecard["observed_content_hash"])
    return {"status": status, "accepted": status == "PASS", "missing_dimensions": missing,
            "failed_dimensions": [d["dimension"] for d in dimensions if d["result"] == "FAIL"],
            "partial_dimensions": [d["dimension"] for d in dimensions if d["result"] == "PARTIAL"],
            "unobserved_dimensions": [d["dimension"] for d in dimensions if d["result"] == "NOT_OBSERVED"]}


def _artifact_binding(record, label):
    _object(record, label)
    _nonempty(record.get("shot_id"), f"{label}.shot_id")
    _nonempty(record.get("artifact_id"), f"{label}.artifact_id")
    _nonempty(record.get("artifact_ref"), f"{label}.artifact_ref")
    _hash(record.get("content_hash"), f"{label}.content_hash")
    return record


def validate_shot_acceptance(contract, artifact=None, observation=None, scorecard=None):
    """Validate a shot acceptance contract independently of editorial acceptance."""
    _object(contract, "shot_contract")
    require(contract.get("schema_version") == 1, "Unsupported shot acceptance schema")
    _nonempty(contract.get("shot_id"), "shot_contract.shot_id")
    require(type(contract.get("revision")) is int and contract["revision"] > 0, "Invalid shot contract revision")
    acceptance = _list(contract.get("acceptance_checks"), "shot_contract.acceptance_checks", allow_empty=False)
    indexed(acceptance, "shot_contract.acceptance_checks")
    for check in acceptance:
        _nonempty(check.get("id"), "shot acceptance check id")
        _nonempty(check.get("question"), f"shot acceptance {check['id']} question")
        require(check.get("required") is True, f"shot acceptance {check['id']} must be required")
    if artifact is not None:
        _artifact_binding({"shot_id": artifact.get("shot_id"), "artifact_id": artifact.get("id"),
                           "artifact_ref": artifact.get("artifact_ref"), "content_hash": artifact.get("content_hash")}, "artifact")
        require(artifact["shot_id"] == contract["shot_id"], "Shot/artifact mismatch")
    if observation is not None:
        validate_observation_contract(observation, artifact)
        observed_ids = {check["id"] for check in observation.get("checks", [])}
        required_observation_ids = {
            check.get("observation_check_id", check["id"]) for check in acceptance
        }
        require(required_observation_ids <= observed_ids,
                "Shot acceptance is missing a result for every required acceptance check")
    if scorecard is not None:
        validate_continuity_scorecard(scorecard, artifact)
    return {"status": "PASS" if observation and observation.get("status") == "PASS" and
            (scorecard is None or scorecard.get("status") == "PASS") else "NOT_OBSERVED",
            "shot_id": contract["shot_id"], "generation_acceptance": observation.get("status") if observation else "NOT_OBSERVED",
            "editorial_acceptance": "NOT_RUN"}


def validate_transition_contract(contract):
    """Bind adjacent shots, state handoff and continuity evidence."""
    _object(contract, "transition")
    require(contract.get("schema_version") == 1, "Unsupported transition schema")
    _nonempty(contract.get("id"), "transition.id")
    _nonempty(contract.get("previous_shot_id"), "transition.previous_shot_id")
    _nonempty(contract.get("next_shot_id"), "transition.next_shot_id")
    require(contract["previous_shot_id"] != contract["next_shot_id"], "A transition needs two different shots")
    previous = _artifact_binding(contract.get("previous_artifact"), "transition.previous_artifact")
    following = _artifact_binding(contract.get("next_artifact"), "transition.next_artifact")
    require(previous["shot_id"] == contract["previous_shot_id"], "Previous artifact/shot mismatch")
    require(following["shot_id"] == contract["next_shot_id"], "Next artifact/shot mismatch")
    require(previous["artifact_id"] != following["artifact_id"], "Transition requires distinct previous and next artifacts")
    require((previous["artifact_ref"], previous["content_hash"]) !=
            (following["artifact_ref"], following["content_hash"]),
            "Transition requires distinct previous and next artifact bytes")
    _verify_observed_bytes(previous["artifact_ref"], previous["content_hash"], "transition.previous_artifact", required=True)
    _verify_observed_bytes(following["artifact_ref"], following["content_hash"], "transition.next_artifact", required=True)
    required = _list(contract.get("required_state_properties"), "transition.required_state_properties", allow_empty=False)
    require(all(isinstance(item, str) and item for item in required), "Transition state properties must be strings")
    start = _object(contract.get("next_start_state"), "transition.next_start_state")
    end = _object(contract.get("previous_end_state"), "transition.previous_end_state")
    for prop in required:
        require(prop in start and prop in end, f"Transition lacks state property: {prop}")
        require(start[prop] == end[prop], f"Transition state mismatch: {prop}")
        require(start[prop] not in (None, "UNKNOWN"), f"Transition state unresolved: {prop}")
    scorecard = contract.get("continuity_scorecard")
    require(isinstance(scorecard, dict), "Transition requires a continuity scorecard")
    score_artifact = {"id": following["artifact_id"], "artifact_ref": following["artifact_ref"],
                      "content_hash": following["content_hash"]}
    score = validate_continuity_scorecard(scorecard, score_artifact)
    status = "PASS" if score["accepted"] and not contract.get("known_drift") else "FAIL"
    if status == "PASS":
        previous_observation = contract.get("previous_observation")
        next_observation = contract.get("next_observation")
        require(isinstance(previous_observation, dict) and isinstance(next_observation, dict),
                "PASS transition requires observations for both adjacent artifacts")
        previous_obs = validate_observation_contract(previous_observation, {
            "id": previous["artifact_id"], "artifact_ref": previous["artifact_ref"],
            "content_hash": previous["content_hash"]})
        next_obs = validate_observation_contract(next_observation, {
            "id": following["artifact_id"], "artifact_ref": following["artifact_ref"],
            "content_hash": following["content_hash"]})
        require(previous_obs["status"] == "PASS" and next_obs["status"] == "PASS",
                "PASS transition requires PASS observations for both adjacent artifacts")
        require(previous_observation["shot_id"] == previous["shot_id"] and
                next_observation["shot_id"] == following["shot_id"],
                "Transition observation/shot lineage mismatch")
    if contract.get("known_drift"):
        _nonempty(contract.get("drift_reason"), "transition.drift_reason")
    require(contract.get("status") == status, "Transition aggregate is inconsistent")
    return {"status": status, "accepted": status == "PASS", "transition_id": contract["id"],
            "repair_owner": contract.get("repair_owner"), "failed_dimensions": score["failed_dimensions"]}


def _decision_evidence(value, label):
    """Resolve a continuity decision to exact, existing evidence bytes."""
    refs = _list(value, label, allow_empty=False)
    normalized = []
    for index, item in enumerate(refs):
        _object(item, f"{label}[{index}]")
        _nonempty(item.get("ref"), f"{label}[{index}].ref")
        _hash(item.get("content_hash"), f"{label}[{index}].content_hash")
        _verify_observed_bytes(item["ref"], item["content_hash"], f"{label}[{index}]", required=True)
        normalized.append({"ref": item["ref"], "content_hash": item["content_hash"]})
    return normalized


def reanchor_decision(drift, shot_id, downstream_shot_ids=None):
    """Select a bounded continuity action from observed drift, never from a prompt alone."""
    _object(drift, "drift")
    _nonempty(shot_id, "shot_id")
    downstream = list(downstream_shot_ids or [])
    require(all(isinstance(item, str) and item for item in downstream), "downstream_shot_ids must contain strings")
    failed = set(_list(drift.get("failed_dimensions", []), "drift.failed_dimensions"))
    partial = set(_list(drift.get("partial_dimensions", []), "drift.partial_dimensions"))
    unobserved = set(_list(drift.get("unobserved_dimensions", []), "drift.unobserved_dimensions"))
    observed = set(_list(drift.get("observed_dimensions", []), "drift.observed_dimensions"))
    require(failed | partial | unobserved | observed <= set(CONTINUITY_DIMENSIONS), "Unknown drift dimension")
    evidence_refs = _decision_evidence(drift.get("evidence_refs", []), "drift.evidence_refs")
    require(failed or partial or unobserved or observed, "Re-anchor decision needs an observed dimension or explicit drift")
    _quality_provenance(drift.get("provenance"), "drift.provenance", shot_id=shot_id)
    capability = drift.get("capability_status", "CONFIRMED")
    require(capability in ("CONFIRMED", "PARTIAL", "UNKNOWN", "UNSUPPORTED", "BLOCKED"), "Invalid drift capability_status")
    reasons = []
    if drift.get("state_contradiction") is True:
        action, owner = "RESET", "continuity"
        reasons.append("Observed state contradicts the canonical handoff")
    elif capability in ("UNSUPPORTED", "BLOCKED"):
        action, owner = "SPLIT", "shot_decomposition"
        reasons.append("Required feature is unavailable for this runtime/profile")
    elif len(failed) >= 4:
        action, owner = "SPLIT", "shot_decomposition"
        reasons.append("Drift spans too many or identity-critical dimensions")
    elif failed & {"identity", "wardrobe", "hair", "object_state_ownership", "vehicle", "environment"}:
        action, owner = "RE_ANCHOR", "reference_conditioning"
        reasons.append("Persistent identity/world state needs a canonical re-anchor")
    elif failed & {"dialogue", "audio"}:
        action, owner = "REGENERATE", "dialogue" if "dialogue" in failed else "audio"
        reasons.append("Performance or audio evidence failed while scene state remains repairable")
    elif failed & {"screen_direction", "camera_geography", "lighting"}:
        action, owner = "REGENERATE", "cinematography"
        reasons.append("Spatial or photographic continuity failed")
    elif failed or partial:
        action, owner = "RE_ANCHOR", "continuity"
        reasons.append("Continuity evidence is incomplete or partially failed")
    elif unobserved:
        action, owner = "RE_ANCHOR", "continuity"
        reasons.append("Required continuity dimensions were not observed")
    else:
        action, owner = "CONTINUE", None
        reasons.append("No observed drift in the supplied scope")
        require(observed, "CONTINUE requires at least one observed continuity dimension")
    if drift.get("artifact_id"):
        _nonempty(drift["artifact_id"], "drift.artifact_id")
    return {
        "schema_version": 1,
        "decision_id": "DEC-REANCHOR-" + re.sub(r"[^A-Za-z0-9_-]", "_", shot_id),
        "shot_id": shot_id,
        "action": action,
        "repair_owner": owner,
        "changed_shot_ids": [shot_id] + downstream if action in ("RESET", "RE_ANCHOR", "SPLIT") else [shot_id],
        "preserve_downstream": action == "CONTINUE",
        "reasons": reasons,
        "evidence_refs": list(evidence_refs),
        "confidence": "HIGH" if action == "CONTINUE" and not unobserved else "MEDIUM",
        "limitations": list(drift.get("limitations", [])) + (["Decision is only as strong as the supplied observations"] if (failed or partial or unobserved) else []),
    }


def validate_first_last_frame(record):
    """Validate a first/last-frame capability probe, including actual endpoint checks."""
    _object(record, "first_last_frame")
    require(record.get("schema_version") == 1, "Unsupported first-last-frame schema")
    _nonempty(record.get("profile_id"), "first_last_frame.profile_id")
    _nonempty(record.get("shot_id"), "first_last_frame.shot_id")
    require(record.get("capability_status") in ("CONFIRMED", "PARTIAL", "UNSUPPORTED", "UNKNOWN"), "Invalid first-last-frame capability_status")
    _hash(record.get("workflow_hash"), "first_last_frame.workflow_hash")
    inputs = _object(record.get("inputs"), "first_last_frame.inputs")
    mode = record.get("mode", "FIRST_AND_LAST")
    require(mode in ("FIRST_ONLY", "LAST_ONLY", "FIRST_AND_LAST"), "Invalid first-last-frame mode")
    required_inputs = {
        "FIRST_ONLY": ("first_frame",),
        "LAST_ONLY": ("last_frame",),
        "FIRST_AND_LAST": ("first_frame", "last_frame"),
    }[mode]
    for key in required_inputs:
        item = _object(inputs.get(key), f"first_last_frame.inputs.{key}")
        _nonempty(item.get("ref"), f"{key}.ref")
        _hash(item.get("content_hash"), f"{key}.content_hash")
    checks = _list(record.get("checks"), "first_last_frame.checks", allow_empty=False)
    names = set()
    for index, check in enumerate(checks):
        _check(check, f"first_last_frame.checks[{index}]")
        names.add(check["id"])
    required = {"endpoint_identity", "motion_path", "object_state", "artifact_delivery"}
    require(required <= names, "First-last-frame probe lacks endpoint, motion, object and artifact checks")
    require(any(check["oracle"]["kind"] in ("FRAME", "SEQUENCE") for check in checks), "First-last-frame probe cannot rely on node metadata alone")
    status = aggregate_quality(checks)
    observed = status in ("PASS", "FAIL", "PARTIAL")
    if observed:
        _nonempty(record.get("artifact_ref"), "first_last_frame.artifact_ref")
        _hash(record.get("artifact_content_hash"), "first_last_frame.artifact_content_hash")
        _verify_observed_bytes(record["artifact_ref"], record["artifact_content_hash"], "first-last-frame artifact", required=True)
        for key in required_inputs:
            _verify_observed_bytes(inputs[key]["ref"], inputs[key]["content_hash"], f"first-last-frame {key}", required=True)
    if record["capability_status"] == "CONFIRMED":
        require(status == "PASS", "CONFIRMED first-last-frame capability requires passing observed checks")
        _quality_provenance(record.get("provenance"), "first_last_frame.provenance", shot_id=record["shot_id"],
                            artifact_ref=record["artifact_ref"], artifact_hash=record["artifact_content_hash"])
        for index, check in enumerate(checks):
            if check["result"] in ("PASS", "FAIL", "PARTIAL"):
                _verify_evidence_bytes(check["evidence"], f"first_last_frame.checks[{index}].evidence", required=True)
    if record["capability_status"] in ("UNSUPPORTED", "UNKNOWN"):
        require(status != "PASS", "Unavailable first-last-frame capability cannot have PASS evidence")
    return {"status": record["capability_status"], "checks_status": status,
            "accepted": record["capability_status"] == "CONFIRMED" and status == "PASS",
            "limitations": list(record.get("limitations", []))}


def validate_contact_phases(contact):
    """Require the causal contact sequence used for articulated/physical actions."""
    _object(contact, "contact")
    require(contact.get("schema_version") == 1, "Unsupported contact schema")
    _nonempty(contact.get("id"), "contact.id")
    _nonempty(contact.get("shot_id"), "contact.shot_id")
    actor = _alias_value(contact, ("actor", "subject"), "contact.actor")
    receiver = _alias_value(contact, ("receiver", "target"), "contact.receiver")
    object_id = _alias_value(contact, ("object_id", "effector"), "contact.object_id")
    cause = _alias_value(contact, ("cause", "interaction_cause"), "contact.cause")
    expected_result = _alias_value(contact, ("expected_result", "success_criterion"), "contact.expected_result")
    for value, field in ((actor, "actor"), (receiver, "receiver"), (object_id, "object_id"),
                         (cause, "cause"), (expected_result, "expected_result")):
        _nonempty(value, f"contact.{field}")
    phases = _list(contact.get("phases"), "contact.phases", allow_empty=False)
    observation_fields = ("artifact_ref", "artifact_content_hash", "observed_at", "procedure")
    observed_envelope = any(field in contact for field in observation_fields)
    if observed_envelope:
        for field in observation_fields:
            _nonempty(contact.get(field), f"contact.{field}")
        _hash(contact["artifact_content_hash"], "contact.artifact_content_hash")
        _timestamp(contact["observed_at"], "contact.observed_at")
        _verify_observed_bytes(contact["artifact_ref"], contact["artifact_content_hash"], "contact artifact", required=True)
    require([phase.get("phase") for phase in phases] == list(CONTACT_PHASES), "Contact phases must be ordered APPROACH through RESULT")
    for index, phase in enumerate(phases):
        _object(phase, f"contact.phases[{index}]")
        require(phase.get("phase") in CONTACT_PHASES, f"Unknown contact phase at {index}")
        for field in ("start_s", "end_s"):
            require(number(phase.get(field)) and phase[field] >= 0, f"contact.phases[{index}].{field} must be nonnegative")
        require(phase["end_s"] > phase["start_s"], f"contact.phases[{index}] must have positive duration")
        _nonempty(phase.get("observable_assertion"), f"contact.phases[{index}].observable_assertion")
        if observed_envelope:
            _oracle(phase.get("oracle"), f"contact.phases[{index}].oracle")
            evidence = _evidence(phase.get("evidence"), f"contact.phases[{index}].evidence")
            _verify_evidence_bytes(evidence, f"contact.phases[{index}].evidence", required=True)
        if index:
            require(phase["start_s"] >= phases[index - 1]["end_s"], "Contact phases overlap or go backwards")
    status = "PASS" if observed_envelope else "PARTIAL"
    if status == "PASS":
        _quality_provenance(contact.get("provenance"), "contact.provenance", shot_id=contact["shot_id"],
                            artifact_ref=contact["artifact_ref"], artifact_hash=contact["artifact_content_hash"])
    return {"status": status, "accepted": status == "PASS", "contact_id": contact["id"], "phase_count": len(phases),
            "canonical_bindings": {"actor": actor, "receiver": receiver, "object_id": object_id,
                                    "cause": cause, "expected_result": expected_result},
            "physics_policy": "Assertions require observation; prompt text is not proof",
            "limitations": [] if observed_envelope else ["Declared contact phases are not observed until an artifact and phase evidence are attached"]}


def validate_causal_sequence(sequence):
    """Validate stimulus -> processing -> reaction -> response ordering."""
    if isinstance(sequence, dict):
        events = _list(sequence.get("events"), "causal_sequence.events", allow_empty=False)
        required = sequence.get("required_stages", list(CAUSAL_STAGES))
    else:
        events = _list(sequence, "causal_sequence", allow_empty=False)
        required = list(CAUSAL_STAGES)
    required = _list(required, "causal_sequence.required_stages", allow_empty=False)
    require(all(stage in CAUSAL_STAGES for stage in required), "causal_sequence has an unknown stage")
    positions = {stage: index for index, stage in enumerate(required)}
    seen = set()
    ordered = []
    for index, event in enumerate(events):
        label = f"causal_sequence.events[{index}]"
        _object(event, label)
        _nonempty(event.get("id"), f"{label}.id")
        stage = event.get("stage", event.get("kind"))
        require(stage in CAUSAL_STAGES, f"{label}.stage is invalid")
        require(stage not in seen, f"Duplicate causal stage: {stage}")
        seen.add(stage)
        require(stage in positions, f"{label}.stage is not in required_stages")
        start = event.get("start_s")
        end = event.get("end_s")
        require(number(start) and number(end) and 0 <= start < end, f"{label} interval is invalid")
        ordered.append((start, end, positions[stage], stage, event))
    missing = [stage for stage in required if stage not in seen]
    require(not missing, "Causal sequence missing stages: " + ", ".join(missing))
    ordered_by_time = sorted(ordered, key=lambda item: (item[0], item[1]))
    require([item[2] for item in ordered_by_time] == sorted(item[2] for item in ordered_by_time),
            "Causal sequence violates stimulus -> processing -> reaction -> response order")
    for previous, following in zip(ordered_by_time, ordered_by_time[1:]):
        require(following[0] >= previous[0], "Causal sequence moves backwards in time")
        if following[0] < previous[1]:
            require(following[4].get("intentional_overlap") is True,
                    f"Causal stage {following[3]} overlaps {previous[3]} without explicit overlap")
    return {"status": "PASS", "accepted": True, "stages": [item[3] for item in ordered_by_time],
            "limitations": ["Causality validation is structural; it does not prove that an artifact shows the event."]}


def validate_object_ownership(record):
    """Reject ownership changes that occur without explicit contact and release."""
    _object(record, "object_ownership")
    require(record.get("schema_version") == 1, "Unsupported object ownership schema")
    _nonempty(record.get("id"), "object_ownership.id")
    _nonempty(record.get("object_id"), "object_ownership.object_id")
    for field in ("owner_before", "owner_after", "cause"):
        _nonempty(record.get(field), f"object_ownership.{field}")
    contact_state = record.get("contact_state")
    require(contact_state in ("NO_CONTACT", "PROXIMITY", "CONTACT", "SHARED_CONTACT", "RELEASED"),
            "object_ownership.contact_state is invalid")
    require(type(record.get("shared_contact")) is bool, "object_ownership.shared_contact must be boolean")
    require(type(record.get("release")) is bool, "object_ownership.release must be boolean")
    if record["shared_contact"]:
        require(contact_state == "SHARED_CONTACT", "shared_contact requires SHARED_CONTACT state")
    if contact_state == "SHARED_CONTACT":
        require(record["shared_contact"] is True, "SHARED_CONTACT requires shared_contact=true")
    if record["owner_before"] != record["owner_after"]:
        require(contact_state in ("CONTACT", "SHARED_CONTACT", "RELEASED"),
                "Object ownership cannot change from proximity alone")
        require(record["release"] is True, "Object ownership change requires an explicit release")
        require(record["cause"].strip().lower() not in ("proximity", "nearby", "gaze"),
                "Object ownership cannot change from proximity alone")
    if record["release"]:
        require(contact_state in ("SHARED_CONTACT", "RELEASED", "CONTACT"),
                "Release requires contact or shared-contact state")
    return {"status": "PASS", "accepted": True, "object_id": record["object_id"],
            "ownership_changed": record["owner_before"] != record["owner_after"],
            "limitations": ["Ownership validation is structural; contact and transfer still require artifact observation."]}


def validate_vehicle_state(record):
    """Validate only declared vehicle fields and their causal combinations."""
    _object(record, "vehicle_state")
    require(record.get("schema_version") == 1, "Unsupported vehicle state schema")
    _nonempty(record.get("id"), "vehicle_state.id")
    _nonempty(record.get("vehicle_id"), "vehicle_state.vehicle_id")
    field_names = (
        "vehicle_position", "velocity_phase", "wheel_state", "engine_state", "door_state",
        "steering_phase", "road_contact", "lights", "occupants"
    )
    state = record.get("state", record)
    _object(state, "vehicle_state.state")
    applicable = record.get("applicable_fields")
    if applicable is None:
        applicable = [field for field in field_names if field in state]
    _list(applicable, "vehicle_state.applicable_fields", allow_empty=False)
    require(set(applicable) <= set(field_names), "vehicle_state has an unknown applicable field")
    for field in applicable:
        require(field in state, f"vehicle_state missing applicable field: {field}")
        value = state[field]
        if field == "occupants":
            require(isinstance(value, (list, dict)), "vehicle_state.occupants must be an array or object")
        elif field == "road_contact":
            require(isinstance(value, bool) or (isinstance(value, str) and bool(value.strip())),
                    "vehicle_state.road_contact must be boolean or a nonempty status")
        else:
            _nonempty(value, f"vehicle_state.{field}")
    velocity = str(state.get("velocity_phase", "")).upper()
    engine = str(state.get("engine_state", "")).upper()
    door = str(state.get("door_state", "")).upper()
    road_contact = state.get("road_contact")
    if velocity in ("MOVING", "ACCELERATING", "CRUISING"):
        require(engine not in ("OFF", "STOPPED"), "A moving vehicle requires an active engine state")
        require(door not in ("OPEN", "FULLY_OPEN"), "A moving vehicle cannot have an open door")
        require(road_contact is not False, "A moving vehicle requires road contact")
    prior = record.get("prior_state")
    if prior is not None:
        _object(prior, "vehicle_state.prior_state")
        changed = [field for field in field_names if field in prior and field in state and prior[field] != state[field]]
        if changed:
            _nonempty(record.get("cause"), "vehicle_state.cause")
    return {"status": "PASS", "accepted": True, "vehicle_id": record["vehicle_id"],
            "applicable_fields": list(applicable),
            "limitations": ["Vehicle state validation is structural; physics and geometry require artifact observation."]}


def validate_dialogue_contract(dialogue):
    """Keep semantics, voice, performance, lip-sync and mix as separate channels."""
    _object(dialogue, "dialogue")
    require(dialogue.get("schema_version") == 1, "Unsupported dialogue contract schema")
    lines = _list(dialogue.get("lines"), "dialogue.lines", allow_empty=False)
    seen_line_ids = set()
    for index, line in enumerate(lines):
        label = f"dialogue.lines[{index}]"
        _object(line, label)
        line_id = _alias_value(line, ("id", "dialogue_id"), f"{label}.id")
        _nonempty(line_id, f"{label}.id")
        require(line_id not in seen_line_ids, f"Duplicate dialogue line id: {line_id}")
        seen_line_ids.add(line_id)
        shot_id = _alias_value(line, ("shot_id",), f"{label}.shot_id")
        speaker = _alias_value(line, ("speaker",), f"{label}.speaker")
        listener = _alias_value(line, ("listener",), f"{label}.listener")
        text = _alias_value(line, ("text", "line"), f"{label}.line")
        intention = _alias_value(line, ("intention", "intent"), f"{label}.intent")
        gaze = _alias_value(line, ("gaze", "gaze_target"), f"{label}.gaze_target")
        for value, field in ((shot_id, "shot_id"), (speaker, "speaker"), (listener, "listener"),
                             (text, "line"), (intention, "intent"), (line.get("delivery"), "delivery"),
                             (line.get("emotion"), "emotion"), (gaze, "gaze_target"),
                             (line.get("pause_policy"), "pause_policy"), (line.get("overlap_policy"), "overlap_policy")):
            _nonempty(value, f"{label}.{field}")
        start = _alias_value(line, ("start_s", "start"), f"{label}.start")
        end = _alias_value(line, ("end_s", "end"), f"{label}.end")
        require(number(start) and start >= 0, f"{label}.start must be nonnegative")
        require(number(end) and end >= 0, f"{label}.end must be nonnegative")
        require(end > start, f"{label} end must be after start")
        for field in ("pause_before", "pause_after", "reaction_delay"):
            if field in line and line[field] is not None:
                require(number(line[field]) and line[field] >= 0, f"{label}.{field} must be nonnegative")
        if line.get("reaction_at_s") is not None:
            require(number(line["reaction_at_s"]) and start <= line["reaction_at_s"] <= end, f"{label}.reaction_at_s outside line")
        if line.get("causality") is not None:
            validate_causal_sequence(line["causality"])
        for field in ("voice_reference", "listener_reaction", "gesture"):
            if field in line and isinstance(line[field], str):
                _nonempty(line[field], f"{label}.{field}")
        if "lip_sync_mode" in line:
            require(line["lip_sync_mode"] in ("NATIVE_CONFIRMED", "EXTERNAL_CONFIRMED", "PARTIAL", "UNSUPPORTED", "UNKNOWN"),
                    f"{label}.lip_sync_mode is invalid")
        if "listener_mouthing_explicit" in line:
            require(type(line["listener_mouthing_explicit"]) is bool, f"{label}.listener_mouthing_explicit must be boolean")
        mouthing = line.get("listener_mouthing", line.get("listener_articulation"))
        sustained_mouthing = mouthing is True or (isinstance(mouthing, str) and mouthing.upper() in ("SUSTAINED", "FULL_LINE", "ACTIVE_SPEECH"))
        require(not sustained_mouthing or line.get("listener_mouthing_explicit") is True,
                f"{label}: listener must not mouth the active speaker line without explicit scripting")
        channels = _object(line.get("channels"), f"{label}.channels")
        for channel in ("semantics", "voice", "performance", "lip_sync", "mix"):
            entry = _object(channels.get(channel), f"{label}.channels.{channel}")
            _status(entry.get("status"), f"{label}.channels.{channel}.status")
            _oracle(entry.get("oracle"), f"{label}.channels.{channel}.oracle")
            if entry["status"] in ("PASS", "FAIL", "PARTIAL"):
                evidence = _evidence(entry.get("evidence"), f"{label}.channels.{channel}.evidence")
                _verify_evidence_bytes(evidence, f"{label}.channels.{channel}.evidence", required=True)
            else:
                _nonempty(entry.get("reason"), f"{label}.channels.{channel}.reason")
        if line.get("visible_speech") is True:
            require(channels["lip_sync"]["status"] not in ("NOT_APPLICABLE",), f"{label}: visible speech needs a lip-sync channel")
            require(channels["voice"]["status"] not in ("NOT_APPLICABLE",), f"{label}: visible speech needs a voice channel")
            require(channels["voice"].get("audio_ref") or channels["voice"].get("evidence"), f"{label}: visible speech needs voice/audio evidence")
    status = aggregate_quality([{"result": line["channels"][channel]["status"]} for line in lines for channel in ("semantics", "voice", "performance", "lip_sync", "mix")])
    if status in ("PASS", "FAIL", "PARTIAL"):
        _nonempty(dialogue.get("artifact_ref"), "dialogue.artifact_ref")
        _hash(dialogue.get("artifact_content_hash"), "dialogue.artifact_content_hash")
        _verify_observed_bytes(dialogue["artifact_ref"], dialogue["artifact_content_hash"], "dialogue artifact", required=True)
    if status == "PASS":
        _quality_provenance(dialogue.get("provenance"), "dialogue.provenance", shot_id=_alias_value(lines[0], ("shot_id",), "dialogue.lines[0].shot_id"),
                            artifact_ref=dialogue["artifact_ref"], artifact_hash=dialogue["artifact_content_hash"])
    return {"status": status, "line_count": len(lines), "channels": ["semantics", "voice", "performance", "lip_sync", "mix"],
            "artifact_ref": dialogue.get("artifact_ref"), "artifact_content_hash": dialogue.get("artifact_content_hash")}


def validate_audio_timeline(timeline):
    """Validate independent audio layers and their causal mappings."""
    allowed = set(AUDIO_LAYERS)

    def normalize_layers(values, label):
        raw = _list(values, label)
        normalized = []
        for index, value in enumerate(raw):
            require(isinstance(value, str) and value, f"{label}[{index}] must be a nonempty string")
            normalized.append(AUDIO_LAYER_ALIASES.get(value, value))
        return normalized

    explicit_scope = isinstance(timeline, dict)
    if explicit_scope:
        events = _list(timeline.get("events"), "audio_timeline.events", allow_empty=False)
        required_layers = set(normalize_layers(timeline.get("required_layers", sorted(allowed)), "audio_timeline.required_layers"))
        not_applicable = set(normalize_layers(timeline.get("not_applicable_layers", []), "audio_timeline.not_applicable_layers"))
        require(required_layers | not_applicable == allowed, "Audio timeline must account for every canonical layer")
        require(not required_layers & not_applicable, "Audio required and not-applicable layers overlap")
        _nonempty(timeline.get("artifact_ref"), "audio_timeline.artifact_ref")
        _hash(timeline.get("artifact_content_hash"), "audio_timeline.artifact_content_hash")
        _timestamp(timeline.get("observed_at"), "audio_timeline.observed_at")
        _nonempty(timeline.get("procedure"), "audio_timeline.procedure")
        _verify_observed_bytes(timeline["artifact_ref"], timeline["artifact_content_hash"], "audio timeline artifact", required=True)
        _nonempty(timeline.get("shot_id"), "audio_timeline.shot_id")
    else:
        events = _list(timeline, "audio_timeline", allow_empty=False)
        required_layers, not_applicable = allowed, set()
    seen = set()
    for index, item in enumerate(events):
        _object(item, f"audio_timeline[{index}]")
        _nonempty(item.get("id"), f"audio_timeline[{index}].id")
        require(item["id"] not in seen, f"Duplicate audio id: {item['id']}")
        seen.add(item["id"])
        layer = AUDIO_LAYER_ALIASES.get(item.get("layer"), item.get("layer"))
        require(layer in allowed, f"audio_timeline[{index}].layer is invalid")
        require(number(item.get("start_s")) and number(item.get("end_s")) and 0 <= item["start_s"] < item["end_s"], f"audio_timeline[{index}] interval is invalid")
        _nonempty(item.get("cause"), f"audio_timeline[{index}].cause")
        _nonempty(item.get("source"), f"audio_timeline[{index}].source")
        if explicit_scope:
            _oracle(item.get("oracle"), f"audio_timeline[{index}].oracle")
            evidence = _evidence(item.get("evidence"), f"audio_timeline[{index}].evidence")
            _verify_evidence_bytes(evidence, f"audio_timeline[{index}].evidence", required=True)
            require(item.get("priority") not in (None, ""), f"audio_timeline[{index}].priority is required")
            _nonempty(item.get("mix_role"), f"audio_timeline[{index}].mix_role")
    present = {AUDIO_LAYER_ALIASES.get(item["layer"], item["layer"]) for item in events}
    missing_layers = sorted(required_layers - present)
    status = "PASS" if explicit_scope and not missing_layers else "PARTIAL"
    if status == "PASS":
        _quality_provenance(timeline.get("provenance"), "audio_timeline.provenance", shot_id=timeline["shot_id"],
                            artifact_ref=timeline["artifact_ref"], artifact_hash=timeline["artifact_content_hash"])
    return {"status": status, "layers": sorted(present), "required_layers": sorted(required_layers),
            "not_applicable_layers": sorted(not_applicable), "missing_layers": missing_layers,
            "event_count": len(events), "artifact_ref": timeline.get("artifact_ref") if explicit_scope else None,
            "artifact_content_hash": timeline.get("artifact_content_hash") if explicit_scope else None,
            "limitations": ["A timeline without an explicit scoped artifact/evidence envelope is partial"] if not explicit_scope else []}


def analyze_prompt_density(sections, limits=None):
    """Measure prompt density and explicit contradictions before adapter compression."""
    _object(sections, "prompt sections")
    limits = _object(limits or {}, "prompt limits")
    text_by_section = {}
    for key, value in sections.items():
        text = canonical(value) if not isinstance(value, str) else value
        text_by_section[key] = text
    text = "\n".join(text_by_section.values())
    words = re.findall(r"[\w'-]+", text, re.UNICODE)
    negative = set(re.findall(r"(?:no|without|never|not)\s+([A-Za-z][\w-]*)", text, re.IGNORECASE))
    positive = set(re.findall(r"\b(static|moving|open|closed|day|night|inside|outside|silent|speaking)\b", text, re.IGNORECASE))
    contradictions = sorted({f"{word}:negative_and_positive" for word in negative & {item.lower() for item in positive}})
    max_words = limits.get("max_words")
    require(max_words is None or (type(max_words) is int and max_words > 0), "prompt limits.max_words must be positive integer")
    status = "FAIL" if contradictions else "PASS"
    if max_words and len(words) > max_words:
        status = "FAIL"
    return {"status": status, "word_count": len(words), "character_count": len(text),
            "max_words": max_words, "section_word_counts": {key: len(re.findall(r"[\w'-]+", value, re.UNICODE)) for key, value in text_by_section.items()},
            "contradictions": contradictions,
            "limitations": ["Lexical density/contradiction analysis is a planning heuristic; it is not model behavior evidence"]}


def adapt_prompt(sections, adapter):
    """Compile a prompt with explicit adapter loss and no silent truncation."""
    _object(sections, "canonical prompt sections")
    _object(adapter, "prompt adapter")
    _nonempty(adapter.get("id"), "prompt adapter.id")
    preserve = adapter.get("preserve_sections", list(sections))
    _list(preserve, "prompt adapter.preserve_sections", allow_empty=False)
    unsupported = adapter.get("unsupported_sections", [])
    _list(unsupported, "prompt adapter.unsupported_sections")
    require(set(unsupported) <= set(sections), "Adapter marks an unknown section unsupported")
    omitted = sorted(set(unsupported))
    selected = [key for key in sections if key not in unsupported]
    compiled = "\n".join(f"{key}: {canonical(sections[key])}" for key in selected)
    max_words = adapter.get("max_words")
    density = analyze_prompt_density({key: sections[key] for key in selected}, {"max_words": max_words} if max_words else {})
    require(not max_words or density["word_count"] <= max_words, "Adapter would truncate prompt; declare compression or split the shot")
    mappings = [{"source": key, "target": adapter.get("mapping", {}).get(key, key), "status": "PRESERVED"} for key in selected]
    mappings += [{"source": key, "target": None, "status": "UNSUPPORTED", "reason": "Adapter declaration"} for key in omitted]
    return {"schema_version": 1, "adapter_id": adapter["id"], "source_hash": digest(sections),
            "positive_prompt": compiled, "mappings": mappings, "omissions": omitted,
            "density": density, "contradictions": density["contradictions"],
            "status": "DEGRADED" if omitted else "PASS",
            "limitations": ["Text compilation does not prove generation behavior"]}


def adapter_differential(canonical_sections, adapters):
    """Compare adapters against one canonical source, exposing loss explicitly."""
    _object(canonical_sections, "canonical_sections")
    _list(adapters, "adapters", allow_empty=False)
    compiled = [adapt_prompt(canonical_sections, adapter) for adapter in adapters]
    baseline = set(canonical_sections)
    reports = []
    for result in compiled:
        preserved = {item["source"] for item in result["mappings"] if item["status"] == "PRESERVED"}
        unsupported = sorted(baseline - preserved)
        reports.append({"adapter_id": result["adapter_id"], "source_hash": result["source_hash"],
                        "preserved_sections": sorted(preserved), "degraded_sections": unsupported,
                        "status": "PASS" if not unsupported else "DEGRADED", "omissions": result["omissions"]})
    return {"schema_version": 1, "canonical_hash": digest(canonical_sections), "adapters": reports,
            "status": "PASS" if all(item["status"] == "PASS" for item in reports) else "DEGRADED"}


def profile_fingerprint(profile):
    """Hash capability-critical identity, not mutable observations or expiry metadata."""
    _object(profile, "profile")
    fields = {
        key: copy.deepcopy(profile.get(key))
        for key in ("id", "profile_revision", "provider", "runtime", "runtime_version", "integration_version", "model",
                    "model_asset_hash", "node_inventory_hash", "workflow_hash", "workflow_fingerprint", "supports", "limits", "controls", "dependencies",
                    "runtime_context", "runtime_commit", "runtime_dirty", "custom_node_commits", "selected_device", "resource_context_hash")
        if key in profile
    }
    return digest(fields)


def profile_expiration_triggers(profile, observed=None):
    """Return deterministic reasons a feature-scoped profile must be re-probed."""
    _object(profile, "profile")
    observed = observed or {}
    _object(observed, "observed profile context")
    triggers = []
    for profile_key, observed_key, label in (("runtime_version", "runtime_version", "runtime version"),
                                               ("node_inventory_hash", "node_inventory_hash", "node inventory"),
                                               ("workflow_hash", "workflow_hash", "workflow graph"),
                                               ("workflow_fingerprint", "workflow_fingerprint", "workflow fingerprint"),
                                               ("model_asset_hash", "model_asset_hash", "model asset"),
                                               ("selected_device", "selected_device", "selected device"),
                                               ("resource_context_hash", "resource_context_hash", "resource context"),
                                               ("runtime_commit", "runtime_commit", "runtime commit"),
                                               ("runtime_dirty", "runtime_dirty", "runtime dirty state"),
                                               ("custom_node_commits", "custom_node_commits", "custom-node commits")):
        expected = profile.get(profile_key)
        actual = observed.get(observed_key)
        if actual not in (None, "", "UNKNOWN") and expected not in (None, "", "UNKNOWN") and actual != expected:
            triggers.append(label + " changed")
    expected_fp = profile.get("profile_fingerprint")
    actual_fp = observed.get("profile_fingerprint")
    if expected_fp and actual_fp and expected_fp != actual_fp:
        triggers.append("capability fingerprint changed")
    for trigger in observed.get("behavioral_changes", []):
        if isinstance(trigger, str) and trigger:
            triggers.append(trigger)
    return sorted(set(triggers))


def _profile_evidence_binding(evidence, field, label, base_dir=None):
    """Require a feature source/probe locator and verify its declared bytes."""
    value = evidence.get(field)
    declared_hash = evidence.get(field.replace("_ref", "_content_hash"))
    if isinstance(value, dict):
        declared_hash = declared_hash or value.get("content_hash")
        value = value.get("ref")
    _nonempty(value, f"{label}.{field}")
    _hash(declared_hash, f"{label}.{field.replace('_ref', '_content_hash')}")
    candidates = []
    ref_path = Path(value)
    if ref_path.is_absolute():
        candidates.append(ref_path)
    else:
        if base_dir is not None:
            base = Path(base_dir)
            candidates.extend((base / ref_path, base.parent / ref_path))
        candidates.append(Path.cwd() / ref_path)
        candidates.append(ref_path)
    resolved = next((candidate for candidate in candidates if candidate.is_file()), None)
    require(resolved is not None, f"{label}.{field} must point to an existing evidence file")
    _verify_observed_bytes(resolved, declared_hash, f"{label}.{field}", required=True)
    return resolved


def _validate_profile_probe_record(path, label):
    """Validate the minimum shape of a confirmed capability probe record."""
    try:
        record = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError(f"{label} probe record cannot be read") from exc
    _object(record, f"{label}.probe_record")
    require(record.get("schema_version") == 1, f"{label} probe record schema is unsupported")
    _nonempty(record.get("probe_id"), f"{label}.probe_record.probe_id")
    require(record.get("status") in ("PASS", "PASS_RUNTIME_GENERATION", "SUCCEEDED"), f"{label}.probe_record status is not a successful probe")
    _nonempty(record.get("artifact_ref"), f"{label}.probe_record.artifact_ref")
    _hash(record.get("artifact_hash"), f"{label}.probe_record.artifact_hash")
    artifact_candidates = [Path(record["artifact_ref"])]
    if not artifact_candidates[0].is_absolute():
        artifact_candidates.insert(0, Path(path).parent / artifact_candidates[0])
    artifact_path = next((candidate for candidate in artifact_candidates if candidate.is_file()), None)
    require(artifact_path is not None, f"{label} probe record artifact bytes are unavailable")
    _verify_observed_bytes(artifact_path, record["artifact_hash"], f"{label}.probe_record.artifact", required=True)
    runtime = _object(record.get("runtime"), f"{label}.probe_record.runtime")
    _nonempty(runtime.get("version"), f"{label}.probe_record.runtime.version")
    _hash(runtime.get("node_inventory_hash"), f"{label}.probe_record.runtime.node_inventory_hash")
    model = _object(record.get("model"), f"{label}.probe_record.model")
    _hash(model.get("asset_hash"), f"{label}.probe_record.model.asset_hash")
    _hash(record.get("workflow_hash"), f"{label}.probe_record.workflow_hash")
    return record


def validate_feature_profile(profile, feature, now=None, observed=None, base_dir=None):
    """Validate one feature's evidence and expiration independently of other features."""
    _object(profile, "profile")
    _nonempty(feature, "feature")
    status = profile.get("status")
    require(status in ("CONFIRMED", "PROPOSED", "INFERRED", "UNKNOWN", "EXPIRED", "UNSUPPORTED"), "Invalid profile status")
    evidence = _object(profile.get("feature_evidence", {}).get(feature), f"profile.feature_evidence.{feature}")
    feature_status = evidence.get("status")
    require(feature_status in ("CONFIRMED", "PARTIAL", "PROPOSED", "INFERRED", "UNKNOWN", "UNSUPPORTED", "EXPIRED"), f"Invalid feature status for {feature}")
    reasons = []
    if status == "CONFIRMED" or feature_status == "CONFIRMED":
        require(profile.get("schema_version") == 1, "Confirmed profile needs schema_version 1")
        for field in ("id", "provider", "runtime", "runtime_version", "integration_version", "model",
                      "model_asset_hash", "node_inventory_hash", "workflow_hash", "workflow_fingerprint",
                      "selected_device", "resource_context_hash"):
            _nonempty(profile.get(field), f"Confirmed profile.{field}")
            require(profile.get(field) not in ("UNKNOWN", "UNPROBED"), f"Confirmed profile.{field} cannot be UNKNOWN")
        for field in ("model_asset_hash", "node_inventory_hash", "workflow_hash", "workflow_fingerprint", "resource_context_hash"):
            _hash(profile[field], f"Confirmed profile.{field}")
        _hash(profile.get("profile_fingerprint"), "Confirmed profile.profile_fingerprint")
        if profile["profile_fingerprint"] != profile_fingerprint(profile):
            reasons.append("profile fingerprint changed")
        for field in ("scope", "checked_at"):
            _nonempty(evidence.get(field), f"Confirmed feature evidence.{field}")
        source_path = _profile_evidence_binding(evidence, "source_ref", "Confirmed feature evidence", base_dir)
        probe_path = _profile_evidence_binding(evidence, "probe_ref", "Confirmed feature evidence", base_dir)
        source_record = _validate_profile_probe_record(source_path, "Confirmed feature evidence.source_ref")
        probe_record = _validate_profile_probe_record(probe_path, "Confirmed feature evidence.probe_ref")
        for label, record in (("source", source_record), ("probe", probe_record)):
            if record["runtime"]["version"] != profile["runtime_version"]:
                reasons.append(f"confirmed feature evidence.{label} runtime version changed")
            if record["runtime"]["node_inventory_hash"] != profile["node_inventory_hash"]:
                reasons.append(f"confirmed feature evidence.{label} node inventory changed")
            if record["model"]["asset_hash"] != profile["model_asset_hash"]:
                reasons.append(f"confirmed feature evidence.{label} model changed")
            if record["workflow_hash"] != profile["workflow_hash"]:
                reasons.append(f"confirmed feature evidence.{label} workflow changed")
        refs = profile.get("evidence_refs", [])
        require(isinstance(refs, list) and all(isinstance(ref, str) and ref for ref in refs), "Confirmed profile.evidence_refs must be a nonempty string array")
        require(evidence["source_ref"] in refs and evidence["probe_ref"] in refs, "Confirmed feature evidence refs are not bound to profile.evidence_refs")
        for field in ("observed_parameters", "selected_device", "artifact_ref", "artifact_content_hash",
                      "observation_ref", "observation_content_hash"):
            require(field in evidence and evidence[field] not in (None, "", "UNKNOWN"),
                    f"Confirmed feature evidence.{field} is required")
        _object(evidence["observed_parameters"], "Confirmed feature evidence.observed_parameters")
        _nonempty(evidence["selected_device"], "Confirmed feature evidence.selected_device")
        artifact_path = _resolve_quality_path(evidence["artifact_ref"], "Confirmed feature evidence.artifact", base_dir)
        _hash(evidence["artifact_content_hash"], "Confirmed feature evidence.artifact_content_hash")
        _verify_observed_bytes(str(artifact_path), evidence["artifact_content_hash"],
                               "Confirmed feature evidence.artifact", required=True)
        observation_path = _resolve_quality_path(evidence["observation_ref"], "Confirmed feature evidence.observation", base_dir)
        _hash(evidence["observation_content_hash"], "Confirmed feature evidence.observation_content_hash")
        _verify_observed_bytes(str(observation_path), evidence["observation_content_hash"],
                               "Confirmed feature evidence.observation", required=True)
    validity = profile.get("validity", {})
    if isinstance(validity, dict) and validity.get("expires_at"):
        clock = now or datetime.now(timezone.utc)
        require(isinstance(clock, datetime) and clock.tzinfo is not None, "Profile validation time needs timezone")
        if _timestamp(validity["expires_at"], "profile.validity.expires_at") <= clock:
            reasons.append("profile validity expired")
    reasons.extend(profile_expiration_triggers(profile, observed))
    if status != "CONFIRMED":
        reasons.append("profile is not confirmed")
    if feature_status != "CONFIRMED":
        reasons.append(f"feature evidence is {feature_status}")
    if not reasons:
        result = "CONFIRMED"
    elif any("expired" in reason or "changed" in reason for reason in reasons):
        result = "EXPIRED"
    elif feature_status == "PARTIAL":
        result = "PARTIAL"
    else:
        result = "UNKNOWN"
    return {"status": result, "profile_id": profile.get("id"), "feature": feature,
            "profile_fingerprint": profile_fingerprint(profile), "reasons": reasons,
            "next_action": "Run a scoped capability probe and create a new profile revision" if reasons else None}


def validate_repair_budget(budget):
    _object(budget, "repair_budget")
    for field in ("max_regenerations", "max_attempts"):
        require(type(budget.get(field)) is int and budget[field] >= 0, f"repair_budget.{field} must be a nonnegative integer")
    for field in ("max_runtime_s", "max_cost_usd"):
        require(number(budget.get(field)) and budget[field] >= 0, f"repair_budget.{field} must be nonnegative")
    require(type(budget.get("human_review_threshold")) is int and budget["human_review_threshold"] >= 0, "repair_budget.human_review_threshold must be a nonnegative integer")
    if "authorized" in budget:
        require(type(budget["authorized"]) is bool, "repair_budget.authorized must be boolean")
    return budget


def build_repair_plan(plan, changed_shot_ids, findings, budget):
    """Create a smallest-owner repair plan from the canonical DAG."""
    _object(plan, "plan")
    changed_shot_ids = _list(changed_shot_ids, "changed_shot_ids", allow_empty=False)
    require(all(isinstance(item, str) and item for item in changed_shot_ids), "changed_shot_ids must contain strings")
    _list(findings, "repair findings", allow_empty=False)
    validate_repair_budget(budget)
    scope = repair_scope(plan, changed_shot_ids)
    routes = []
    for finding in findings:
        _object(finding, "repair finding")
        owner = finding.get("repair_owner") or finding.get("owner") or "human_review"
        require(owner in REPAIR_OWNERS, f"Unknown repair owner: {owner}")
        routes.append({"id": finding.get("id", f"finding_{len(routes)+1}"), "owner": owner,
                       "shot_id": finding.get("shot_id", changed_shot_ids[0]),
                       "reason": _nonempty(finding.get("reason", "Observed quality finding"), "repair finding reason")})
    affected = scope["affected_shot_ids"]
    require(all(route["shot_id"] in affected for route in routes), "Repair route may not mutate preserved siblings")
    requested = len(affected)
    require(requested <= max(1, budget["max_regenerations"]), "Repair exceeds max_regenerations budget")
    return {"schema_version": 1, "plan_revision": plan.get("revision"), "changed_shot_ids": changed_shot_ids,
            "affected_shot_ids": affected, "preserved_shot_ids": scope["preserved_shot_ids"], "routes": routes,
            "budget": copy.deepcopy(budget), "estimated_regenerations": requested,
            "status": "AUTHORIZED" if budget.get("authorized") is True else "AWAITING_AUTHORIZATION",
            "limitations": ["Cost/runtime estimates are declarations until a runtime ledger is attached"]}


def _validate_repair_ledger(ledger, budget, shot_id=None):
    """Validate measured repair usage before calling a repair plan complete."""
    _object(ledger, "repair_plan.execution_ledger")
    require(ledger.get("schema_version") == 1, "Unsupported repair execution ledger schema")
    require(ledger.get("status") in ("NOT_RUN", "RUNNING", "COMPLETE", "BLOCKED"), "Invalid repair execution ledger status")
    for field in ("attempts", "regenerations", "human_reviews"):
        require(type(ledger.get(field)) is int and ledger[field] >= 0, f"repair execution ledger.{field} must be a nonnegative integer")
    for field in ("runtime_s", "cost_usd"):
        require(number(ledger.get(field)) and ledger[field] >= 0, f"repair execution ledger.{field} must be nonnegative")
    require(ledger["regenerations"] <= budget["max_regenerations"], "Measured regenerations exceed repair budget")
    require(ledger["attempts"] <= budget["max_attempts"], "Measured attempts exceed repair budget")
    require(ledger["runtime_s"] <= budget["max_runtime_s"], "Measured runtime exceeds repair budget")
    require(ledger["cost_usd"] <= budget["max_cost_usd"], "Measured cost exceeds repair budget")
    require(ledger["human_reviews"] <= budget["human_review_threshold"] or ledger.get("human_review_completed") is True,
            "Human-review threshold requires an explicit completed checkpoint")
    _timestamp(ledger.get("observed_at"), "repair execution ledger.observed_at")
    evidence = _evidence(ledger.get("evidence", []), "repair execution ledger.evidence", required=ledger["status"] in ("COMPLETE", "BLOCKED"))
    _verify_evidence_bytes(evidence, "repair execution ledger.evidence", required=ledger["status"] in ("COMPLETE", "BLOCKED"))
    if ledger["status"] == "COMPLETE":
        _timestamp(ledger.get("completed_at"), "repair execution ledger.completed_at")
        _quality_provenance(ledger.get("provenance"), "repair execution ledger.provenance", shot_id=shot_id)
    return ledger


def validate_repair_plan(repair):
    _object(repair, "repair_plan")
    require(repair.get("schema_version") == 1, "Unsupported repair plan schema")
    changed = _list(repair.get("changed_shot_ids"), "repair_plan.changed_shot_ids", allow_empty=False)
    affected = _list(repair.get("affected_shot_ids"), "repair_plan.affected_shot_ids", allow_empty=False)
    preserved = _list(repair.get("preserved_shot_ids"), "repair_plan.preserved_shot_ids")
    require(set(changed) <= set(affected), "Repair changed shots must be affected")
    require(not set(affected) & set(preserved), "Repair affected/preserved sets overlap")
    validate_repair_budget(repair.get("budget"))
    require(type(repair.get("estimated_regenerations")) is int and 0 <= repair["estimated_regenerations"] <= repair["budget"]["max_regenerations"], "Repair regeneration budget exceeded")
    routes = _list(repair.get("routes"), "repair_plan.routes", allow_empty=False)
    for index, route in enumerate(routes):
        _object(route, f"repair_plan.routes[{index}]")
        require(route.get("owner") in REPAIR_OWNERS, f"repair_plan.routes[{index}].owner is invalid")
        require(route.get("shot_id") in affected, f"repair_plan.routes[{index}] targets a non-affected shot")
        _nonempty(route.get("reason"), f"repair_plan.routes[{index}].reason")
    require(repair.get("status") in ("AUTHORIZED", "AWAITING_AUTHORIZATION", "BLOCKED"), "Invalid repair plan status")
    ledger = repair.get("execution_ledger")
    if ledger is None:
        status = "BLOCKED" if repair["status"] == "BLOCKED" else "PARTIAL"
        ledger_status = "NOT_RUN"
    else:
        ledger_report = _validate_repair_ledger(ledger, repair["budget"], shot_id=changed[0])
        ledger_status = ledger_report["status"]
        status = "PASS" if ledger_status == "COMPLETE" and repair["status"] == "AUTHORIZED" else "BLOCKED" if ledger_status == "BLOCKED" else "PARTIAL"
    return {"status": status, "accepted": status == "PASS", "affected_shot_ids": affected, "preserved_shot_ids": preserved,
            "authorized": repair["status"] == "AUTHORIZED", "execution_ledger_status": ledger_status,
            "limitations": [] if ledger is not None else ["Repair usage remains unmeasured until an execution ledger is attached"]}


def _resolve_quality_path(ref, label, base_dir=None):
    _nonempty(ref, f"{label}.ref")
    raw = Path(ref)
    candidates = [raw] if raw.is_absolute() else []
    if base_dir is not None:
        base = Path(base_dir)
        candidates.extend((base / raw, base.parent / raw))
    candidates.extend((Path.cwd() / raw, raw))
    resolved = next((candidate.resolve() for candidate in candidates if candidate.is_file()), None)
    require(resolved is not None, f"{label}.ref must point to an existing file")
    return resolved


def _validate_long_form_file_ref(item, label, base_dir=None):
    _object(item, label)
    ref = item.get("ref", item.get("record_ref"))
    content_hash = item.get("content_hash", item.get("record_content_hash"))
    path = _resolve_quality_path(ref, label, base_dir)
    _hash(content_hash, f"{label}.content_hash")
    _verify_observed_bytes(str(path), content_hash, label, required=True)
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError(f"{label} must be a readable JSON record") from exc
    require(isinstance(record, dict), f"{label} JSON record must be an object")
    return path, record


def _normalize_quality_record_paths(record, record_path, label):
    """Resolve relative quality evidence paths against their record file."""
    normalized = copy.deepcopy(record)
    base_dir = Path(record_path).parent

    def resolve(value, field):
        return str(_resolve_quality_path(value, f"{label}.{field}", base_dir))

    if "artifact_ref" in normalized and normalized.get("artifact_ref") not in (None, ""):
        normalized["artifact_ref"] = resolve(normalized["artifact_ref"], "artifact_ref")
    for check in normalized.get("checks", []):
        if not isinstance(check, dict):
            continue
        evidence = check.get("evidence", [])
        if isinstance(evidence, str):
            evidence = [{"type": "TEXT", "ref": evidence}]
            check["evidence"] = evidence
        if isinstance(evidence, list):
            for item in evidence:
                if isinstance(item, dict) and item.get("ref"):
                    item["ref"] = resolve(item["ref"], "checks.evidence.ref")
    provenance = normalized.get("provenance")
    if isinstance(provenance, dict):
        for owner, fields in (("attempt", ("ref",)), ("shot", ("ref",)),
                              ("artifact", ("record_ref", "media_ref"))):
            section = provenance.get(owner)
            if isinstance(section, dict):
                for field in fields:
                    if section.get(field):
                        section[field] = resolve(section[field], f"provenance.{owner}.{field}")
    return normalized


def _normalize_scorecard_paths(record, record_path, label):
    """Resolve scorecard evidence without changing its declared hashes."""
    normalized = _normalize_quality_record_paths(record, record_path, label)
    for dimension in normalized.get("dimensions", []):
        if not isinstance(dimension, dict):
            continue
        evidence = dimension.get("evidence", [])
        if isinstance(evidence, str):
            evidence = [{"type": "TEXT", "ref": evidence}]
            dimension["evidence"] = evidence
        if isinstance(evidence, list):
            for item in evidence:
                if isinstance(item, dict) and item.get("ref"):
                    item["ref"] = str(_resolve_quality_path(item["ref"], f"{label}.dimensions.evidence.ref", Path(record_path).parent))
    return normalized


def _validate_long_form_production_evidence(case, base_dir=None):
    """Fail closed: a long-form PASS must resolve its complete evidence graph."""
    production = _object(case.get("production_evidence"), "long_form_case.production_evidence")
    required_sets = ["attempts", "artifacts", "observations", "transitions"]
    resolved = {key: [] for key in required_sets}
    for key in required_sets:
        entries = _list(production.get(key), f"long_form_case.production_evidence.{key}", allow_empty=False)
        for index, item in enumerate(entries):
            path, record = _validate_long_form_file_ref(item, f"production_evidence.{key}[{index}]", base_dir)
            require(record.get("schema_version") == 1, f"production_evidence.{key}[{index}] schema is unsupported")
            _nonempty(record.get("id"), f"production_evidence.{key}[{index}].id")
            resolved[key].append((path, record))

    from vge_evidence import validate_attempt
    attempt_ids = set()
    for index, (path, record) in enumerate(resolved["attempts"]):
        validate_attempt(record)
        require(record.get("status") == "SUCCEEDED", f"production_evidence.attempts[{index}] is not SUCCEEDED")
        attempt_ids.add(record["id"])

    artifact_ids = set()
    artifact_by_id = {}
    artifact_shots = set()
    for index, (path, record) in enumerate(resolved["artifacts"]):
        _nonempty(record.get("shot_id"), f"production_evidence.artifacts[{index}].shot_id")
        require(record.get("generation_status") == "GENERATED", f"production_evidence.artifacts[{index}] is not GENERATED")
        require(record.get("execution_attempt_ref") in attempt_ids,
                f"production_evidence.artifacts[{index}] is not bound to a successful attempt")
        media = _object(record.get("media"), f"production_evidence.artifacts[{index}].media")
        require(media.get("kind") in ("video", "image", "audio", "gif"),
                f"production_evidence.artifacts[{index}].media.kind is invalid")
        media_ref = record.get("artifact_ref")
        media_hash = record.get("content_hash")
        _nonempty(media_ref, f"production_evidence.artifacts[{index}].artifact_ref")
        _hash(media_hash, f"production_evidence.artifacts[{index}].content_hash")
        media_path = _resolve_quality_path(media_ref, f"production_evidence.artifacts[{index}].media", path.parent)
        _verify_observed_bytes(str(media_path), media_hash, f"production_evidence.artifacts[{index}].media", required=True)
        item_media_ref = production["artifacts"][index].get("media_ref")
        item_media_hash = production["artifacts"][index].get("media_content_hash")
        if item_media_ref is not None:
            require(str(_resolve_quality_path(item_media_ref, f"production_evidence.artifacts[{index}].media_ref", path.parent)) == str(media_path),
                    f"production_evidence.artifacts[{index}] media locator disagrees with its record")
        if item_media_hash is not None:
            require(item_media_hash == media_hash, f"production_evidence.artifacts[{index}] media hash disagrees with its record")
        require(record["id"] not in artifact_ids, f"Duplicate production artifact id: {record['id']}")
        artifact_ids.add(record["id"])
        artifact_by_id[record["id"]] = {"record": record, "path": media_path}
        artifact_shots.add(record["shot_id"])

    observed_artifacts = set()
    for index, (path, record) in enumerate(resolved["observations"]):
        normalized = _normalize_quality_record_paths(record, path, f"production_evidence.observations[{index}]")
        require(normalized.get("status") == "PASS", f"production_evidence.observations[{index}] must be PASS")
        _nonempty(normalized.get("artifact_id"), f"production_evidence.observations[{index}].artifact_id")
        require(normalized["artifact_id"] in artifact_by_id,
                f"production_evidence.observations[{index}] references an unknown artifact")
        artifact = artifact_by_id[normalized["artifact_id"]]
        require(normalized.get("artifact_ref") == str(artifact["path"]),
                f"production_evidence.observations[{index}] artifact locator mismatch")
        require(normalized.get("observed_content_hash") == artifact["record"].get("content_hash"),
                f"production_evidence.observations[{index}] artifact hash mismatch")
        validate_observation_contract(normalized)
        observed_artifacts.add(normalized["artifact_id"])

    transitioned_pairs = set()
    for index, (path, record) in enumerate(resolved["transitions"]):
        normalized = copy.deepcopy(record)
        require(normalized.get("status") == "PASS", f"production_evidence.transitions[{index}] must be PASS")
        previous = _object(normalized.get("previous_artifact"), f"production_evidence.transitions[{index}].previous_artifact")
        following = _object(normalized.get("next_artifact"), f"production_evidence.transitions[{index}].next_artifact")
        for side, artifact in (("previous", previous), ("next", following)):
            require(artifact.get("artifact_id") in artifact_by_id,
                    f"production_evidence.transitions[{index}] {side} artifact is unknown")
            known = artifact_by_id[artifact["artifact_id"]]
            artifact["artifact_ref"] = str(known["path"])
            artifact["content_hash"] = known["record"].get("content_hash")
        require(previous["artifact_id"] != following["artifact_id"],
                f"production_evidence.transitions[{index}] needs distinct artifacts")
        pair = (previous["artifact_id"], following["artifact_id"])
        require(pair not in transitioned_pairs, f"Duplicate production transition pair: {pair}")
        transitioned_pairs.add(pair)
        previous_observation = _normalize_quality_record_paths(
            _object(normalized.get("previous_observation"), f"production_evidence.transitions[{index}].previous_observation"),
            path, f"production_evidence.transitions[{index}].previous_observation")
        next_observation = _normalize_quality_record_paths(
            _object(normalized.get("next_observation"), f"production_evidence.transitions[{index}].next_observation"),
            path, f"production_evidence.transitions[{index}].next_observation")
        for observation, artifact in ((previous_observation, previous), (next_observation, following)):
            require(observation.get("artifact_id") == artifact["artifact_id"],
                    f"production_evidence.transitions[{index}] observation/artifact mismatch")
            observation["artifact_ref"] = artifact["artifact_ref"]
            observation["observed_content_hash"] = artifact["content_hash"]
            require(observation.get("status") == "PASS", f"production_evidence.transitions[{index}] observations must be PASS")
            validate_observation_contract(observation)
        scorecard = _normalize_scorecard_paths(
            _object(normalized.get("continuity_scorecard"), f"production_evidence.transitions[{index}].continuity_scorecard"),
            path, f"production_evidence.transitions[{index}].continuity_scorecard")
        scorecard["artifact_id"] = following["artifact_id"]
        scorecard["artifact_ref"] = following["artifact_ref"]
        scorecard["observed_content_hash"] = following["content_hash"]
        validate_continuity_scorecard(scorecard)

    assembly_path, assembly = _validate_long_form_file_ref(production.get("assembly"), "production_evidence.assembly", base_dir)
    require(assembly.get("schema_version") == 1, "production_evidence.assembly schema is unsupported")
    _nonempty(assembly.get("id"), "production_evidence.assembly.id")
    require(assembly.get("editorial_acceptance") in ("PASS", "ACCEPTED"),
            "production_evidence.assembly is not editorially accepted")
    require(assembly.get("mechanical_status") in ("PASS", "ACCEPTED"),
            "production_evidence.assembly lacks mechanical acceptance")
    segments = _list(assembly.get("segments"), "production_evidence.assembly.segments", allow_empty=False)
    require(all(isinstance(segment, dict) and segment.get("artifact_id") in artifact_ids for segment in segments),
            "production_evidence.assembly has an unbound segment")
    shot_ids = {shot for shot in case.get("shot_ids", []) if shot != "NOT_RUN"}
    require(shot_ids <= artifact_shots, "production evidence does not cover every case shot")
    require(artifact_ids <= observed_artifacts, "production evidence has an unobserved artifact")
    return {
        "attempts": len(production["attempts"]),
        "artifacts": len(production["artifacts"]),
        "observations": len(production["observations"]),
        "transitions": len(production["transitions"]),
        "assembly": True,
    }


def _validate_long_form_fixture(fixture, case_id):
    """Validate structural fixture content without treating it as runtime evidence."""
    _object(fixture, "long_form_case.fixture")
    _nonempty(fixture.get("scenario"), "long_form_case.fixture.scenario")
    _list(fixture.get("requirements"), "long_form_case.fixture.requirements", allow_empty=False)
    _list(fixture.get("known_bad"), "long_form_case.fixture.known_bad", allow_empty=False)
    if case_id == "LF-001":
        require(fixture.get("contact_phases") == list(CONTACT_PHASES),
                "LF-001 fixture must enumerate the canonical contact phases")
        dimensions = _list(fixture.get("acceptance_dimensions"), "LF-001 fixture.acceptance_dimensions", allow_empty=False)
        require(len(dimensions) == 13, "LF-001 fixture must have 13 independent acceptance dimensions")
    if case_id == "LF-002":
        require(set(fixture.get("dialogue_channels", [])) == {"semantics", "voice", "performance", "lip_sync", "mix"},
                "LF-002 fixture must separate all dialogue channels")
    if case_id == "LF-003":
        required_bible = {"characters", "identity_anchors", "wardrobe", "relationships", "environment",
                          "time_of_day", "light_direction", "persistent_objects", "voice_identity",
                          "visual_style", "camera_language", "prohibited_drift"}
        require(required_bible <= set(fixture.get("scene_bible_fields", [])),
                "LF-003 fixture Scene Bible is incomplete")
        require(len(fixture.get("continuity_fields", [])) >= 18,
                "LF-003 fixture continuity ledger is incomplete")
    if case_id == "LF-004":
        require(fixture.get("branches") and fixture.get("recovery_checkpoints") and fixture.get("editorial_gate"),
                "LF-004 fixture requires branches, recovery checkpoints and editorial gate")


def validate_long_form_case(case, base_dir=None):
    """Validate the long-form ladder and fail closed for production PASS."""
    _object(case, "long_form_case")
    require(case.get("schema_version") == 1, "Unsupported long-form case schema")
    _nonempty(case.get("id"), "long_form_case.id")
    duration = case.get("target_duration_s")
    require(number(duration, True) and duration <= 120, "long_form_case.target_duration_s must be in (0,120]")
    ranges = {"LF-001": (10, 15), "LF-002": (20, 30), "LF-003": (45, 60), "LF-004": (90, 120)}
    require(case["id"] in ranges, "Unknown long-form ladder id")
    low, high = ranges[case["id"]]
    require(low <= duration <= high, f"{case['id']} duration must be between {low} and {high} seconds")
    for field in ("intent_ref", "plan_ref", "scene_bible_ref", "shot_graph_ref", "continuity_ref", "evidence_ref"):
        _nonempty(case.get(field), f"long_form_case.{field}")
    shots = _list(case.get("shot_ids"), "long_form_case.shot_ids", allow_empty=False)
    require(all(isinstance(item, str) and item for item in shots), "long_form_case.shot_ids must contain strings")
    if case["id"] in ("LF-002", "LF-003", "LF-004"):
        require(case.get("audio_timeline_ref"), f"{case['id']} requires audio_timeline_ref")
    if case["id"] == "LF-002":
        require(case.get("dialogue_contract_ref"), "LF-002 requires dialogue_contract_ref")
    if case["id"] in ("LF-003", "LF-004"):
        require(case.get("repair_budget_ref") and case.get("human_checkpoint_ref"), f"{case['id']} requires bounded repair and human checkpoint refs")
    if case.get("fixture") is not None:
        _validate_long_form_fixture(case["fixture"], case["id"])
    status = case.get("status")
    require(status in ("PASS", "PARTIAL", "NOT_RUN", "BLOCKED", "UNKNOWN"), "Invalid long-form case status")
    evidence_summary = None
    if status == "PASS":
        require(case.get("production_evidence_complete") is True, "Long-form PASS requires complete production evidence")
        required_refs = ["intent_ref", "plan_ref", "scene_bible_ref", "shot_graph_ref", "continuity_ref", "evidence_ref"]
        if case["id"] in ("LF-002", "LF-003", "LF-004"):
            required_refs.append("audio_timeline_ref")
        if case["id"] == "LF-002":
            required_refs.append("dialogue_contract_ref")
        if case["id"] in ("LF-003", "LF-004"):
            required_refs.extend(("repair_budget_ref", "human_checkpoint_ref"))
        for field in required_refs:
            _resolve_quality_path(case[field], f"long_form_case.{field}", base_dir)
        evidence_summary = _validate_long_form_production_evidence(case, base_dir)
    return {"status": status, "id": case["id"], "duration_s": duration, "shot_count": len(shots),
            "production_evidence_complete": case.get("production_evidence_complete") is True,
            "production_evidence": evidence_summary}


def maturity_report(evidence):
    """Compute a conservative maturity level from explicit gate statuses."""
    _object(evidence, "maturity evidence")
    level = 0
    if evidence.get("structural") == "PASS":
        level = 1
    if level >= 1 and evidence.get("deterministic_tests") == "PASS":
        level = 2
    if level >= 2 and evidence.get("runtime_provenance") == "PASS":
        level = 3
    if level >= 3 and evidence.get("audiovisual") == "PASS":
        level = 4
    if level >= 4 and evidence.get("bounded_production") == "PASS" and evidence.get("independent_critic") == "PASS":
        level = 5
    return {"level": level, "name": MATURITY_LEVELS[level], "evidence": copy.deepcopy(evidence),
            "limitations": ["Maturity is bounded to the declared evidence scope"]}


__all__ = [
    "QUALITY_STATUSES", "SCORECARD_STATUSES", "CONTINUITY_DIMENSIONS", "CONTACT_PHASES", "CAUSAL_STAGES",
    "AUDIO_LAYERS", "AUDIO_LAYER_ALIASES", "REANCHOR_ACTIONS",
    "validate_observation_contract", "validate_semantic_observation", "validate_continuity_scorecard",
    "validate_shot_acceptance", "validate_transition_contract", "reanchor_decision", "validate_first_last_frame",
    "validate_contact_phases", "validate_causal_sequence", "validate_object_ownership", "validate_vehicle_state",
    "validate_dialogue_contract", "validate_audio_timeline", "aggregate_quality",
    "analyze_prompt_density", "adapt_prompt", "adapter_differential", "profile_fingerprint",
    "profile_expiration_triggers", "validate_feature_profile", "validate_repair_budget", "build_repair_plan",
    "validate_repair_plan", "validate_long_form_case", "maturity_report",
]
