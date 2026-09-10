"""Deterministic planning mechanics. Creative decisions belong to the director."""
from __future__ import annotations

import copy
import hashlib
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path


class ContractError(ValueError):
    pass


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return "sha256:" + hashlib.sha256(canonical(value).encode()).hexdigest()


def file_hash(path):
    h = hashlib.sha256()
    try:
        with Path(path).open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                h.update(chunk)
    except (OSError, TypeError, ValueError) as exc:
        raise ContractError(f"Cannot hash file: {path}") from exc
    return "sha256:" + h.hexdigest()


def load(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ContractError(f"Duplicate key: {key}")
            result[key] = value
        return result
    try:
        return json.loads(Path(path).read_text(), object_pairs_hook=pairs,
                          parse_constant=lambda x: (_ for _ in ()).throw(ContractError(f"Nonfinite number: {x}")))
    except (OSError, ValueError) as exc:
        raise ContractError(str(exc)) from exc


def save(path, value):
    """Create exclusively: evidence and derived plans never silently overwrite."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def number(value, positive=False):
    return type(value) in (int, float) and math.isfinite(value) and (not positive or value > 0)


def hash_value(value):
    return isinstance(value, str) and bool(re.fullmatch(r"sha256:[0-9a-f]{64}", value))


def require(condition, message):
    if not condition:
        raise ContractError(message)


def indexed(records, label):
    require(isinstance(records, list), f"{label} must be an array")
    result = {}
    for r in records:
        require(isinstance(r, dict) and isinstance(r.get("id"), str) and bool(r["id"]), f"{label}: missing id")
        require(r["id"] not in result, f"{label}: duplicate id {r['id']}")
        result[r["id"]] = r
    return result


def optional_list(owner, key, label=None):
    """Return an optional array without treating malformed values as empty."""
    if key not in owner:
        return []
    records = owner[key]
    require(isinstance(records, list), f"{label or key} must be an array")
    return records


def string_list(value, label, allow_empty=True):
    require(isinstance(value, list), f"{label} must be an array")
    require(all(isinstance(item, str) and bool(item) for item in value), f"{label} must contain nonempty strings")
    require(allow_empty or bool(value), f"{label} must be nonempty")
    return value


def object_value(value, label):
    require(isinstance(value, dict), f"{label} must be an object")
    return value


def ordered(shots):
    nodes = indexed(shots, "shots")
    result, pending = [], set(nodes)
    for key, shot in nodes.items():
        deps = shot.get("dependency_ids", [])
        require(isinstance(deps, list) and all(isinstance(d, str) for d in deps), f"{key}: invalid dependency_ids")
        require(len(deps) == len(set(deps)), f"{key}: duplicate dependency")
        require(all(d in nodes for d in deps), f"{key}: missing dependency")
    while pending:
        ready = sorted(key for key in pending if not set(nodes[key].get("dependency_ids", [])) & pending)
        require(ready, "Shot graph contains a cycle")
        result.extend(ready)
        pending.difference_update(ready)
    return result


def flatten(value, prefix=""):
    result = {}
    for key, item in value.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(item, dict):
            result.update(flatten(item, path))
        else:
            result[path] = item
    return result


def _path_value(record, path):
    """Read an explicitly named canonical field, including dotted keys."""
    if not isinstance(record, dict):
        return None
    if path in record:
        return record[path]
    current = record
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _first_path_value(record, paths):
    for path in paths:
        value = _path_value(record, path)
        if value is not None:
            return value
    return None


def _text_values(value):
    """Flatten authored action/camera values for conservative phrase checks."""
    if isinstance(value, str):
        yield value.lower()
    elif isinstance(value, dict):
        for item in value.values():
            yield from _text_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from _text_values(item)


def _contains_term(value, terms):
    text = " ".join(_text_values(value))
    return any(re.search(rf"(?<![a-z]){re.escape(term.lower())}(?![a-z])", text) for term in terms)


def _relation_endpoint(value, names):
    if isinstance(value, dict):
        for name in names:
            candidate = value.get(name)
            if isinstance(candidate, str) and candidate:
                return candidate
        return None
    return value if isinstance(value, str) and value else None


def _relation_records(value):
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        return [value]
    return []


def _relation_phases(value):
    phases = []
    for key in ("phase", "phases", "stage", "stages", "action", "actions", "type"):
        candidate = value.get(key) if isinstance(value, dict) else None
        if isinstance(candidate, str):
            phases.append(candidate.upper())
        elif isinstance(candidate, list):
            phases.extend(str(item).upper() for item in candidate if isinstance(item, str))
    return set(phases)


def _approach_relations(state):
    relations = []
    for key in ("interaction", "interactions", "contact_graphs", "action_sequence.interactions",
                "action_sequence", "actions", "action_primitives"):
        for item in _relation_records(_path_value(state, key)):
            if "APPROACH" not in _relation_phases(item):
                continue
            actor = _relation_endpoint(item, ("actor", "subject", "source", "agent", "performer"))
            target = _relation_endpoint(item, ("target", "target_object", "object_id", "object", "receiver"))
            if actor and target:
                relations.append(item | {"_actor": actor, "_target": target})
    return relations


def _held_relations(state):
    relations = []

    def add(actor, target, effector=None):
        if actor and target and str(target).upper() not in {"FREE", "EMPTY", "NONE", "UNKNOWN"}:
            relations.append((actor, target, effector))

    def scan_occupancy(actor, occupancy):
        if isinstance(occupancy, dict):
            for hand, value in occupancy.items():
                if isinstance(value, str):
                    add(actor, value, hand)
                elif isinstance(value, dict):
                    target = _relation_endpoint(value, ("object_id", "target", "entity_id", "id"))
                    status = str(value.get("status", value.get("state", "HELD"))).upper()
                    if target and status not in {"FREE", "EMPTY", "NONE", "RELEASED"}:
                        add(actor, target, hand)
        elif isinstance(occupancy, list):
            for item in occupancy:
                if not isinstance(item, dict):
                    continue
                target = _relation_endpoint(item, ("object_id", "target", "entity_id", "id"))
                hand = _relation_endpoint(item, ("hand", "effector", "limb"))
                status = str(item.get("status", item.get("state", "HELD"))).upper()
                if target and status not in {"FREE", "EMPTY", "NONE", "RELEASED"}:
                    add(actor, target, hand)

    for key in ("relationships", "continuity.relationships", "holds"):
        for item in _relation_records(_path_value(state, key)):
            relation_type = str(item.get("type", "holds")).lower()
            if relation_type in {"holds", "hold", "carrying", "carries"}:
                add(_relation_endpoint(item, ("source", "actor", "subject", "owner")),
                    _relation_endpoint(item, ("target", "object_id", "object", "receiver")),
                    _relation_endpoint(item, ("effector", "hand", "limb")))

    for state_key in ("initial_state", "state", "continuity.initial_state"):
        snapshot = _path_value(state, state_key)
        if not isinstance(snapshot, dict):
            continue
        for actor, record in snapshot.items():
            if not isinstance(record, dict):
                continue
            actor_id = record.get("id", actor)
            scan_occupancy(actor_id, record.get("hand_occupancy", record.get("hands")))
            for hand, value in record.items():
                if hand in {"left_hand", "right_hand", "hand_left", "hand_right"}:
                    scan_occupancy(actor_id, {hand: value})

    subject = _path_value(state, "subject")
    if isinstance(subject, dict):
        scan_occupancy(subject.get("id", "subject"), subject.get("hand_occupancy", subject.get("hands")))
    return relations


def _approach_is_explained(relation, held_effector):
    explanation_values = []
    for key in ("reason", "purpose", "cause", "exception", "operation"):
        explanation_values.extend(_text_values(relation.get(key)))
    explanation = " ".join(explanation_values)
    if _contains_term(explanation, ("carry", "carries", "reposition", "release", "transfer", "handoff")):
        return True
    approach_effector = _relation_endpoint(relation, ("effector", "hand", "limb"))
    return bool(approach_effector and held_effector and approach_effector != held_effector)


DIALOGUE_CAUSAL_STAGES = ("STIMULUS", "PROCESSING", "REACTION", "RESPONSE")
DIALOGUE_STRATEGY_STATUSES = {
    "PROPOSED", "UNKNOWN", "DEGRADED", "NATIVE_CONFIRMED", "EXTERNAL_CONFIRMED", "FAILED", "UNSUPPORTED"
}


def _dialogue_alias(record, names, label):
    present = [(name, record[name]) for name in names if name in record and record[name] is not None]
    require(present, f"{label} is required")
    value = present[0][1]
    for name, candidate in present[1:]:
        require(candidate == value, f"{label} aliases disagree: {present[0][0]} vs {name}")
    return value


def validate_dialogue_reaction_order(value, label="dialogue.reaction_order"):
    """Validate the explicit stimulus -> processing -> reaction -> response chain."""
    if isinstance(value, dict) and value.get("status") in ("NOT_APPLICABLE", "OFFSCREEN"):
        require(isinstance(value.get("reason"), str) and bool(value["reason"].strip()),
                f"{label}.reason is required when reaction order is not applicable")
        return {"status": value["status"], "reason": value["reason"]}
    if isinstance(value, dict):
        events = value.get("events")
        required = value.get("required_stages", list(DIALOGUE_CAUSAL_STAGES))
    else:
        events = value
        required = list(DIALOGUE_CAUSAL_STAGES)
    require(isinstance(events, list) and bool(events), f"{label}.events must be a nonempty array")
    require(isinstance(required, list) and bool(required), f"{label}.required_stages must be a nonempty array")
    require(required == list(DIALOGUE_CAUSAL_STAGES),
            f"{label}.required_stages must be STIMULUS, PROCESSING, REACTION, RESPONSE")
    seen = set()
    ordered = []
    for index, event in enumerate(events):
        event_label = f"{label}.events[{index}]"
        require(isinstance(event, dict), f"{event_label} must be an object")
        require(isinstance(event.get("id"), str) and bool(event["id"]), f"{event_label}.id is required")
        stage = event.get("stage", event.get("kind"))
        require(stage in DIALOGUE_CAUSAL_STAGES, f"{event_label}.stage is invalid")
        require(stage not in seen, f"{label} contains duplicate stage {stage}")
        seen.add(stage)
        start, end = event.get("start_s"), event.get("end_s")
        require(number(start) and number(end) and 0 <= start < end, f"{event_label} interval is invalid")
        ordered.append((start, end, DIALOGUE_CAUSAL_STAGES.index(stage), stage, event))
    missing = [stage for stage in DIALOGUE_CAUSAL_STAGES if stage not in seen]
    require(not missing, f"{label} is missing stages: {', '.join(missing)}")
    ordered.sort(key=lambda item: (item[0], item[1]))
    require([item[2] for item in ordered] == sorted(item[2] for item in ordered),
            f"{label} violates stimulus -> processing -> reaction -> response order")
    for previous, following in zip(ordered, ordered[1:]):
        if following[0] < previous[1]:
            require(following[4].get("intentional_overlap") is True,
                    f"{label} stages overlap without intentional_overlap")
    return {"status": "PASS", "stages": [item[3] for item in ordered]}


def _normalize_dialogue_strategy(value, label, source_name):
    if isinstance(value, str):
        require(bool(value.strip()), f"{label} must be nonempty")
        return value
    require(isinstance(value, dict), f"{label} must be a string or object")
    if "status" in value:
        require(value["status"] in DIALOGUE_STRATEGY_STATUSES, f"{label}.status is invalid")
    for key in ("strategy", "mode", "reference", "path", "reason"):
        if key in value:
            require(isinstance(value[key], str) and bool(value[key].strip()), f"{label}.{key} must be nonempty")
    if "status" not in value and not any(isinstance(value.get(key), str) and value[key].strip()
                                         for key in ("strategy", "mode", "reference", "path")):
        require(False, f"{label} needs a strategy, reference, path or status")
    return copy.deepcopy(value)


def normalize_dialogue_line(line, label="dialogue"):
    """Normalize prompt dialogue aliases while requiring causal plan declarations."""
    require(isinstance(line, dict), f"{label} must be an object")
    dialogue_id = _dialogue_alias(line, ("dialogue_id", "id"), f"{label}.dialogue_id")
    shot_id = _dialogue_alias(line, ("shot_id",), f"{label}.shot_id")
    speaker = _dialogue_alias(line, ("speaker",), f"{label}.speaker")
    listener = _dialogue_alias(line, ("listener", "target_listener"), f"{label}.listener")
    text = _dialogue_alias(line, ("line", "text"), f"{label}.line")
    intent = _dialogue_alias(line, ("intent", "intention"), f"{label}.intent")
    start = _dialogue_alias(line, ("start_s", "start"), f"{label}.start_s")
    end = _dialogue_alias(line, ("end_s", "end"), f"{label}.end_s")
    for value, field in ((dialogue_id, "dialogue_id"), (shot_id, "shot_id"), (speaker, "speaker"),
                         (listener, "listener"), (text, "line"), (intent, "intent")):
        require(isinstance(value, str) and bool(value.strip()), f"{label}.{field} must be nonempty")
    listener_is_explicitly_absent = str(listener).upper() in {"NONE", "OFFSCREEN", "NOT_APPLICABLE"}
    require(speaker != listener or listener_is_explicitly_absent,
            f"{label}.speaker and listener must be distinct")
    require(number(start) and start >= 0, f"{label}.start_s must be nonnegative")
    require(number(end) and end > start, f"{label}.end_s must be after start")

    listener_reaction = line.get("listener_reaction")
    require(listener_reaction is not None, f"{label}.listener_reaction is required")
    if isinstance(listener_reaction, dict) and listener_reaction.get("status") in ("NOT_APPLICABLE", "OFFSCREEN"):
        require(isinstance(listener_reaction.get("reason"), str) and bool(listener_reaction["reason"].strip()),
                f"{label}.listener_reaction.reason is required when not applicable")
    elif isinstance(listener_reaction, str):
        require(bool(listener_reaction.strip()), f"{label}.listener_reaction must be nonempty")
    else:
        require(isinstance(listener_reaction, dict) and bool(listener_reaction),
                f"{label}.listener_reaction must be a nonempty string or object")

    reaction_order = _dialogue_alias(line, ("reaction_order", "causality"), f"{label}.reaction_order")
    reaction_order_report = validate_dialogue_reaction_order(reaction_order, f"{label}.reaction_order")
    if reaction_order_report.get("status") == "PASS":
        reaction_events = reaction_order.get("events") if isinstance(reaction_order, dict) else reaction_order
        response_events = [event for event in reaction_events if event.get("stage", event.get("kind")) == "RESPONSE"]
        require(response_events, f"{label}.reaction_order must declare a RESPONSE event")
        if not line.get("intentional_overlap"):
            require(all(event["start_s"] >= end for event in response_events),
                    f"{label}.reaction_order response must follow line end")
    if "voice_strategy" in line:
        voice_strategy = _normalize_dialogue_strategy(line["voice_strategy"], f"{label}.voice_strategy", "voice_strategy")
    elif "voice_reference" in line:
        voice_strategy = {"status": "PROPOSED", "reference": line["voice_reference"], "source": "voice_reference"}
        _normalize_dialogue_strategy(voice_strategy, f"{label}.voice_strategy", "voice_reference")
    else:
        require(False, f"{label}.voice_strategy is required")
    if "lip_sync_strategy" in line:
        lip_sync_strategy = _normalize_dialogue_strategy(line["lip_sync_strategy"], f"{label}.lip_sync_strategy", "lip_sync_strategy")
    elif "lip_sync_mode" in line:
        lip_sync_strategy = {"status": line["lip_sync_mode"], "source": "lip_sync_mode"}
        _normalize_dialogue_strategy(lip_sync_strategy, f"{label}.lip_sync_strategy", "lip_sync_mode")
    elif "lip_sync_path" in line:
        lip_sync_strategy = {"status": "PROPOSED", "path": line["lip_sync_path"], "source": "lip_sync_path"}
        _normalize_dialogue_strategy(lip_sync_strategy, f"{label}.lip_sync_strategy", "lip_sync_path")
    else:
        require(False, f"{label}.lip_sync_strategy is required")

    normalized = copy.deepcopy(line)
    normalized.update({
        "dialogue_id": dialogue_id, "id": dialogue_id, "shot_id": shot_id,
        "speaker": speaker, "listener": listener, "target_listener": listener,
        "line": text, "text": text, "intent": intent, "intention": intent,
        "start_s": start, "start": start, "end_s": end, "end": end,
        "listener_reaction": copy.deepcopy(listener_reaction),
        "reaction_order": copy.deepcopy(reaction_order),
        "voice_strategy": voice_strategy, "lip_sync_strategy": lip_sync_strategy,
        "_reaction_order_report": reaction_order_report,
    })
    return normalized


def detect_canonical_contradictions(state):
    """Find contradictions before prompt compilation.

    This is intentionally a small, explicit gate over authored state.  It does
    not interpret arbitrary prose as truth and it never rewrites a plan.  The
    director repairs the returned canonical fields before asking for a prompt.
    """
    require(isinstance(state, dict), "canonical state must be an object")
    source = state.get("canonical_state") if isinstance(state.get("canonical_state"), dict) else state
    contradictions = []

    def add(code, fields, reason, repair_route):
        contradictions.append({"id": code, "fields": list(fields), "reason": reason,
                               "repair_route": repair_route})

    door = _first_path_value(source, (
        "vehicle.door_state", "vehicle.door", "vehicle_door_state", "door_state", "door"
    ))
    entry_door = _first_path_value(source, (
        "interaction.door_during_entry", "interaction.entry_door_state",
        "entry.door_state", "entry_door_state"
    ))
    if str(door).upper() in ("CLOSED", "SHUT") and str(entry_door).upper() in ("OPEN", "OPENED"):
        add("DOOR_ENTRY_STATE", ("vehicle.door_state", "entry_door_state"),
            "A closed door cannot simultaneously be the open door used for entry",
            "Repair the canonical door phase/state or split the action")
    action_values = _first_path_value(source, ("action_sequence", "actions", "action_primitives", "interaction", "interactions"))
    if str(door).upper() in ("CLOSED", "SHUT") and _contains_term(action_values, (
        "through open door", "entering through open door", "already open door"
    )):
        add("DOOR_ENTRY_PROSE", ("door_state", "action_sequence"),
            "The canonical action says entry uses an open door while the declared door is closed",
            "Repair canonical state/action causality before compilation")

    motion_values = [
        _path_value(source, path) for path in (
            "vehicle.motion_state", "vehicle.velocity_phase", "vehicle.motion",
            "motion_state", "velocity_phase", "vehicle_motion_state"
        )
    ]
    normalized_motion = {str(value).upper() for value in motion_values if value is not None}
    moving_states = {"MOVING", "ACCELERATING", "IN_MOTION", "DRIVING"}
    stationary_states = {"PARKED", "STATIONARY", "STOPPED"}
    if normalized_motion & moving_states and normalized_motion & stationary_states:
        add("VEHICLE_MOTION_STATE", ("vehicle.motion_state", "vehicle.velocity_phase"),
            "The vehicle is declared parked/stationary and moving at the same time",
            "Repair the canonical motion state or add a causal transition")

    subject_position = _first_path_value(source, ("subject.position", "subject_position", "position"))
    seated_state = _first_path_value(source, ("subject.seated_state", "seated_state", "subject.seated"))
    if str(subject_position).upper() in ("OUTSIDE", "EXTERIOR") and str(seated_state).upper() in ("SEATED", "INSIDE"):
        add("SUBJECT_SEATING_STATE", ("subject.position", "subject.seated_state"),
            "The subject is declared outside and already seated/inside",
            "Repair the entry state sequence or split the shot")

    time_value = _first_path_value(source, ("time_of_day", "setting.time_of_day", "environment.time_of_day", "time"))
    lighting_value = _first_path_value(source, ("lighting", "lighting_and_style.lighting", "environment.lighting"))
    if _contains_term(time_value, ("night",)) and _contains_term(lighting_value, ("golden_hour", "golden hour")):
        add("TIME_LIGHTING", ("time_of_day", "lighting"),
            "Night and a golden-hour lighting lock are mutually incompatible without an explicit transition",
            "Repair the canonical time/lighting state")

    camera = _first_path_value(source, ("camera",))
    movement = _first_path_value(camera, ("movement", "movement.type", "type")) if isinstance(camera, dict) else None
    camera_text = " ".join(_text_values(camera))
    if (_contains_term(movement, ("static",)) or _contains_term(camera_text, ("static",))) and _contains_term(camera_text, ("orbit",)):
        add("CAMERA_MOTION", ("camera.movement",),
            "A static camera cannot also perform a continuous orbit",
            "Repair the camera movement declaration or split the coverage")

    turns = _first_path_value(source, ("dialogue_turns", "turns", "dialogue"))
    if isinstance(turns, dict):
        turns = turns.get("lines", turns.get("turns", []))
    if isinstance(turns, list):
        for index, left in enumerate(turns):
            if not isinstance(left, dict):
                continue
            for right in turns[index + 1:]:
                if not isinstance(right, dict) or left.get("speaker") == right.get("speaker"):
                    continue
                left_start, left_end = left.get("start_s", left.get("start")), left.get("end_s", left.get("end"))
                right_start, right_end = right.get("start_s", right.get("start")), right.get("end_s", right.get("end"))
                overlap = number(left_start) and number(left_end) and number(right_start) and number(right_end) and left_start < right_end and right_start < left_end
                policies = {str(left.get("overlap_policy", "")).upper(), str(right.get("overlap_policy", "")).upper()}
                exclusive = left.get("exclusive") is True or right.get("exclusive") is True or policies & {"NONE", "EXCLUSIVE", "NO_OVERLAP"}
                if overlap and exclusive:
                    add("DIALOGUE_EXCLUSIVE_TURN", ("dialogue_turns",),
                        f"Exclusive dialogue turns overlap for speakers {left.get('speaker')} and {right.get('speaker')}",
                        "Repair the turn intervals/speakers or explicitly authorize overlap")
                    break

    wardrobe_locked = source.get("wardrobe_locked") is True
    locked_properties = source.get("locked_properties", [])
    if isinstance(locked_properties, list):
        wardrobe_locked = wardrobe_locked or any(str(item).lower() in ("wardrobe", "clothing") for item in locked_properties)
    wardrobe_changes = source.get("wardrobe_changes", source.get("wardrobe_change"))
    if wardrobe_locked and wardrobe_changes:
        changes = wardrobe_changes if isinstance(wardrobe_changes, list) else [wardrobe_changes]
        unexplained = [item for item in changes if not isinstance(item, dict) or not (item.get("cause") or item.get("review_ref"))]
        if unexplained:
            add("LOCKED_WARDROBE_CHANGE", ("wardrobe_locked", "wardrobe_changes"),
                "A locked wardrobe changes without a causal or reviewed transition",
                "Repair the canonical wardrobe state or attach a reviewed transition")

    if isinstance(source.get("contradictions"), list) and source["contradictions"]:
        for item in source["contradictions"]:
            add("DECLARED_CONTRADICTION", ("contradictions",),
                str(item) if isinstance(item, str) else "The canonical state declares an unresolved contradiction",
                "Resolve the canonical contradiction before compilation")

    ownership = _first_path_value(source, ("ownership", "object_ownership", "interaction.ownership"))
    if isinstance(ownership, dict):
        owner_before = ownership.get("owner_before", ownership.get("before"))
        owner_after = ownership.get("owner_after", ownership.get("after"))
        contact = ownership.get("shared_contact") is True or str(ownership.get("contact_state", "")).upper() in {
            "CONTACT", "SHARED_CONTACT", "HANDOFF", "TRANSFER"
        }
        cause = ownership.get("cause") or ownership.get("handoff") or ownership.get("transfer_ref")
        if owner_before not in (None, "UNKNOWN") and owner_after not in (None, "UNKNOWN") and owner_before != owner_after and not contact and not cause:
            add("OWNERSHIP_TRANSFER", ("ownership.owner_before", "ownership.owner_after", "ownership.contact_state"),
                "Object ownership changes without a contact/handoff cause",
                "Add a visible contact transition or keep ownership unchanged")

    held = _held_relations(source)
    for approach in _approach_relations(source):
        for actor, target, effector in held:
            if actor == approach["_actor"] and target == approach["_target"] and not _approach_is_explained(approach, effector):
                add("APPROACH_HELD_TARGET", ("interaction.actor", "interaction.target", "hand_occupancy"),
                    f"{actor} approaches {target} while the same actor already holds that object",
                    "Release, transfer, reposition or use a distinct effector before approaching the target")
                break

    return {
        "schema_version": 1,
        "status": "FAIL" if contradictions else "PASS",
        "contradictions": contradictions,
        "next_action": "Repair canonical state before prompt compilation" if contradictions else None,
        "limitations": ["This gate checks explicit canonical fields and bounded authored phrases; it is not an audiovisual oracle"],
    }


def validate_canonical_state(state):
    """Fail closed when the canonical state is internally contradictory."""
    report = detect_canonical_contradictions(state)
    if report["status"] != "PASS":
        reasons = "; ".join(item["reason"] for item in report["contradictions"])
        require(False, "Canonical state contradictions: " + reasons)
    return report


NEGATIVE_CONSTRAINT_FAMILIES = {
    "IDENTITY": ("identity", "subject", "character", "face", "likeness", "wardrobe", "reference"),
    "ANATOMY": ("anatomy", "body", "limb", "proportion", "joint"),
    "HANDS": ("hand", "hands", "finger", "grip"),
    "CONTACT": ("contact", "touch", "collision", "grasp", "handoff", "reach", "interaction"),
    "OBJECT": ("object", "prop", "ownership", "retain", "carry"),
    "VEHICLE": ("vehicle", "car", "van", "door", "wheel", "road", "driver"),
    "ENVIRONMENT": ("environment", "location", "background", "geography", "weather", "lighting"),
    "TEMPORAL": ("temporal", "continuity", "state", "before", "after", "duration", "transition"),
    "CAMERA": ("camera", "orbit", "static", "framing", "lens", "shot", "screen_direction"),
    "DIALOGUE": ("dialogue", "speaker", "listener", "line", "turn", "voice"),
    "LIP_SYNC": ("lip_sync", "lip-sync", "mouth", "phoneme", "speech"),
    "AUDIO": ("audio", "sound", "foley", "ambience", "mix", "diegetic", "sfx"),
    "TEXT": ("text", "logo", "sign", "caption", "lettering"),
}


def select_negative_constraints(scene):
    """Select only risk-relevant negative-constraint families.

    The result is metadata for a director/adapter, not a universal negative
    prompt.  Untyped declarations are omitted instead of being silently
    applied to every scene.
    """
    require(isinstance(scene, dict), "scene for negative constraint selection must be an object")
    declared = scene.get("negative_constraints", [])
    require(isinstance(declared, list), "negative_constraints must be an array")
    explicit = scene.get("negative_constraint_families", scene.get("risk_families", []))
    if isinstance(explicit, dict):
        explicit = [key for key, value in explicit.items() if value is True]
    require(isinstance(explicit, list), "negative_constraint_families must be an array")
    explicit = {str(item).upper() for item in explicit if str(item).strip()}
    risk_source = copy.deepcopy(scene)
    risk_source.pop("negative_constraints", None)
    risk_source.pop("negative_constraint_families", None)
    risk_source.pop("risk_families", None)
    scene_text = " ".join(_text_values(risk_source)).lower()
    selected_families = [
        family for family, cues in NEGATIVE_CONSTRAINT_FAMILIES.items()
        if family in explicit or any(re.search(rf"(?<![a-z]){re.escape(cue.lower())}(?![a-z])", scene_text) for cue in cues)
    ]
    selected, omitted = [], []
    for index, item in enumerate(declared):
        if isinstance(item, dict):
            family = str(item.get("family", item.get("kind", ""))).upper()
            value = copy.deepcopy(item)
            text = " ".join(_text_values(item))
        elif isinstance(item, str) and item.strip():
            family = next((candidate for candidate, cues in NEGATIVE_CONSTRAINT_FAMILIES.items()
                           if any(re.search(rf"(?<![a-z]){re.escape(cue.lower())}(?![a-z])", item.lower()) for cue in cues)), "")
            value = {"constraint": item}
        else:
            family, value = "", item
        if family in selected_families:
            value.setdefault("family", family)
            value["selection_reason"] = "Scene risk activates this family"
            selected.append(value)
        else:
            omitted.append({"index": index, "family": family or None,
                            "reason": "Family is not active for the declared scene risk"})
    return {
        "schema_version": 1,
        "status": "PASS",
        "selected_families": selected_families,
        "selected": selected,
        "omitted": omitted,
        "limits": {"generic_untyped_constraints": "OMIT", "unrelated_families": "OMIT"},
        "limitations": ["Negative constraints are generation hints; semantic QA remains authoritative"],
    }


def duration_floor(seconds):
    require(number(seconds, True) and seconds <= 120, "duration must be finite and 0 < seconds <= 120")
    fields = ["shots"]
    if seconds > 30:
        fields += ["narrative_timeline"]
    if seconds > 45:
        fields += ["scene_bible", "shot_graph", "continuity_states"]
    if seconds >= 60:
        fields += ["generation_strategy", "assembly_plan"]
    if seconds >= 90:
        fields += ["alternative_branches", "recovery_checkpoints", "provenance_manifest", "human_checkpoints"]
    return fields


def issue(code, path, reason, action, outcome="BLOCK", gate="QG-07", evidence_gap=None):
    return {"id": code, "path": path, "severity": "HIGH", "outcome": outcome,
            "reason": reason, "preserved_intent": "Keep the declared scene objective and hard constraints",
            "evidence_gap": evidence_gap or reason, "evidence_required": [action],
            "next_action": action, "repair_route": path, "gate": gate}


def decision_diagnostic(decision_id, stage, input_scope, result, reasons, evidence_refs, alternatives, next_action, confidence, limitations):
    """Return concise decision evidence without exposing hidden reasoning."""
    return {"decision_id": decision_id, "stage": stage, "input_scope": input_scope, "result": result,
            "reasons": list(reasons), "evidence_refs": list(evidence_refs), "alternatives": list(alternatives),
            "next_action": next_action, "confidence": confidence, "limitations": list(limitations)}


def _complexity_vector(intent, shots, references, dialogue, contacts):
    """Compute routing inputs from canonical authored records."""
    movement_types = []
    for shot in shots:
        camera = shot.get("camera", {})
        movement = camera.get("movement", {}) if isinstance(camera, dict) else {}
        movement_types.append(movement.get("type", "UNKNOWN") if isinstance(movement, dict) else "UNKNOWN")
    visible_speech = sum(item.get("visible_speech") is True for item in dialogue if isinstance(item, dict))
    return {
        "identities": len(intent.get("subjects", [])),
        "references": len(references),
        "dialogue": len(dialogue),
        "lip_sync": visible_speech,
        "interaction": len(contacts),
        "articulated_objects": len(intent.get("objects", [])),
        "motion": sum(len(shot.get("action_primitives", [])) for shot in shots),
        "camera": len(set(movement_types)),
        "camera_movement": sum(item not in ("STATIC", "NONE", "UNKNOWN") for item in movement_types),
        "dependency_edges": sum(len(shot.get("dependency_ids", [])) for shot in shots),
        "duration": intent["duration"]["target_seconds"],
        "vfx": intent.get("vfx", "UNKNOWN"),
    }


def _route_complexity(intent, shots, complexity):
    """Route by duration plus causal, performance and production load."""
    duration = complexity["duration"]
    reasons = []
    if duration >= 60:
        reasons.append("duration requires bounded long-form structure")
    if complexity["identities"] >= 4:
        reasons.append("four or more persistent identities")
    if complexity["dialogue"] and complexity["lip_sync"]:
        reasons.append("visible dialogue adds performance and synchronization work")
    if complexity["dependency_edges"]:
        reasons.append("dependency edges require state propagation")
    if complexity["interaction"]:
        reasons.append("contact/interaction phases need causal coverage")
    if complexity["camera_movement"]:
        reasons.append("moving camera adds spatial continuity load")
    if duration >= 60 or complexity["identities"] >= 4 or len(shots) > 8 or (complexity["dialogue"] >= 2 and complexity["lip_sync"]):
        mode = "DIRECTOR"
    elif len(shots) > 2 or complexity["identities"] > 1 or complexity["dialogue"] or complexity["interaction"] or complexity["dependency_edges"]:
        mode = "PRODUCTION"
    elif complexity["references"] or complexity["motion"] > 4 or complexity["camera_movement"]:
        mode = "CINEMATIC"
    else:
        mode = "FAST"
    if not reasons:
        reasons.append("single-shot low-causal-load treatment")
    return mode, reasons


REFERENCE_CATALOG = (
    ("core", "references/core-contracts.md"),
    ("continuity", "references/continuity-and-long-form.md"),
    ("directing_audio", "references/directing-and-audio.md"),
    ("interaction_constraints", "references/interaction-and-constraints.md"),
    ("model_adaptation", "references/model-adaptation.md"),
    ("comfyui_execution", "references/comfyui-execution.md"),
    ("evaluation_repair", "references/evaluation-and-repair.md"),
    ("production_quality", "references/production-quality.md"),
    ("observability", "references/observability.md"),
    ("safety_provenance", "references/safety-and-provenance.md"),
)


def _contains_comfyui(value):
    """Inspect only explicit runtime/provider fields, never free-form prose."""
    if isinstance(value, str):
        return "comfyui" in value.lower() or value.lower() == "comfy"
    if isinstance(value, dict):
        return any(_contains_comfyui(value.get(key)) for key in
                   ("runtime", "runtime_target", "execution", "execution_target", "provider", "backend"))
    return False


def _reference_route(plan, complexity=None):
    """Derive a small, explainable reference-loading recommendation.

    This is a structural routing record for the host/agent context loader. It
    does not claim that a host actually loaded any reference or that a model
    can satisfy the routed capability.
    """
    require(isinstance(plan, dict), "plan must be an object")
    intent = object_value(plan.get("scene_intent", {}), "scene_intent")
    shots = plan.get("shots", [])
    require(isinstance(shots, list), "shots must be an array")
    references = plan.get("references", [])
    require(isinstance(references, list), "references must be an array")
    dialogue = plan.get("dialogue_timeline", [])
    contacts = plan.get("contact_graphs", [])
    audio = plan.get("audio_timeline", [])
    require(isinstance(dialogue, list), "dialogue_timeline must be an array")
    require(isinstance(contacts, list), "contact_graphs must be an array")
    require(isinstance(audio, list), "audio_timeline must be an array")
    complexity = complexity or _complexity_vector(intent, shots, references, dialogue, contacts)
    routed_mode, _ = _route_complexity(intent, shots, complexity)
    duration = complexity["duration"]
    entities = plan.get("scene_bible", {}).get("entities", [])
    entity_types = {str(entity.get("type", "")).lower() for entity in entities if isinstance(entity, dict)}
    capability_requirements = {
        item
        for shot in shots
        if isinstance(shot, dict)
        for item in shot.get("capability_requirements", [])
        if isinstance(item, str)
    }
    action_text = {
        str(action).lower()
        for shot in shots
        if isinstance(shot, dict)
        for action in shot.get("action_primitives", [])
        if isinstance(action, str)
    }
    interaction_signal = bool(contacts) or any(
        isinstance(shot, dict) and shot.get("contact_graph_ref") for shot in shots
    ) or bool({"vehicle", "animal", "articulated", "articulated_object"} & entity_types) or bool(
        {"contact", "collision", "physics", "articulation", "vehicle_geometry", "animal_anatomy"}
        & capability_requirements
    ) or bool({"contact", "collision", "articulate", "transfer", "handoff", "examine", "reach"} & action_text)
    dialogue_signal = bool(dialogue) or intent.get("dialogue_required") is True or bool(
        {"dialogue", "audio_dialogue_lip_sync", "lip_sync", "voice"} & capability_requirements
    )
    audio_signal = bool(audio) or intent.get("audio_required") is True or dialogue_signal
    dependent_action = complexity["dependency_edges"] > 0
    long_form_signal = duration > 30 or len(shots) > 1 or dependent_action
    continuity_signal = long_form_signal or dialogue_signal or interaction_signal
    moving_camera = complexity["camera_movement"] > 0
    target = intent.get("target", {}) if isinstance(intent.get("target", {}), dict) else {}
    model_signal = any(
        plan.get(key) not in (None, "", "UNKNOWN")
        for key in ("model", "model_id", "profile", "profile_id", "selected_profile", "provider")
    ) or any(
        intent.get(key) not in (None, "", "UNKNOWN")
        for key in ("model", "model_id", "profile", "profile_id", "selected_profile", "provider")
    ) or any(
        target.get(key) not in (None, "", "UNKNOWN")
        for key in ("model", "model_id", "profile", "profile_id", "selected_profile", "provider")
    ) or bool(capability_requirements) or any(
        isinstance(shot, dict) and shot.get("generation_mode", "T2V") != "T2V" for shot in shots
    )
    comfy_signal = _contains_comfyui(plan) or _contains_comfyui(target)
    constraints = plan.get("constraints", [])
    safety_signal = any(
        isinstance(ref, dict) and (
            ref.get("sensitive") is True or
            bool({"face", "likeness", "voice", "voice_identity", "character_identity", "identity_reference"}
                 & set(ref.get("roles", [])))
        )
        for ref in references
    ) or any(
        isinstance(constraint, dict) and constraint.get("kind") == "RIGHTS_SAFETY"
        for constraint in constraints if isinstance(constraints, list)
    ) or any(
        intent.get(key) is True for key in ("external_transfer", "publication", "consent_required", "rights_required")
    )
    production_signal = duration >= 45 or len(shots) > 2 or bool(plan.get("human_checkpoints"))

    signals = {
        "duration_s": duration,
        "shot_count": len(shots),
        "dialogue": dialogue_signal,
        "audio": audio_signal,
        "moving_camera": moving_camera,
        "interaction": interaction_signal,
        "long_form": long_form_signal,
        "model_selection_or_capability": model_signal,
        "comfyui_execution": comfy_signal,
        "production_quality": production_signal,
        "safety_or_provenance": safety_signal,
    }
    reasons = {
        "core": ["Required for every authored scene contract"],
        "directing_audio": ["Camera, purpose and performance decisions are present in every scene"],
        "evaluation_repair": ["Acceptance and bounded repair are required even for a simple shot"],
        "observability": ["Routing and unresolved decisions need concise inspectable diagnostics"],
        "continuity": ["Multi-shot, dialogue or physical state requires explicit continuity guidance"],
        "interaction_constraints": ["Contact, articulation or vehicle/animal mechanics are in scope"],
        "model_adaptation": ["A selected model, non-T2V mode or capability requirement needs scoped adaptation"],
        "comfyui_execution": ["The request names an explicit ComfyUI/runtime execution target"],
        "production_quality": ["Duration or shot count crosses the production-quality review boundary"],
        "safety_provenance": ["Rights, consent, likeness, voice or external-transfer risk is explicit"],
    }
    # Core is the only baseline for a simple authored scene. Specialist
    # references are activated by a concrete decision signal; loading review
    # and observability guidance ceremonially makes routing expensive without
    # improving the simple-shot decision.
    required = {"core"}
    if dialogue_signal or audio_signal or moving_camera or long_form_signal:
        required.add("directing_audio")
    if continuity_signal:
        required.add("continuity")
    if interaction_signal:
        required.add("interaction_constraints")
    if model_signal:
        required.add("model_adaptation")
    if comfy_signal:
        required.add("comfyui_execution")
    if production_signal:
        required.add("production_quality")
    if safety_signal:
        required.add("safety_provenance")
    if any(plan.get(key) is True for key in ("review_required", "evaluation_required", "repair_required")):
        required.add("evaluation_repair")
    if any(plan.get(key) is True for key in ("audit_required", "observability_required")):
        required.add("observability")
    exclusions = {
        "directing_audio": "No dialogue, audio, moving-camera or long-form directing decision",
        "continuity": "No multi-shot, dialogue, physical-interaction or long-form signal",
        "interaction_constraints": "No contact, articulated-object, vehicle, animal or physical-action signal",
        "model_adaptation": "No selected model, non-T2V mode or capability requirement",
        "comfyui_execution": "No explicit ComfyUI/runtime execution target",
        "production_quality": "No long-form production-quality signal",
        "safety_provenance": "No explicit rights, consent, likeness, voice or transfer risk",
        "evaluation_repair": "No explicit evaluation, review or repair decision",
        "observability": "No explicit audit or observability decision",
    }
    required_records = []
    excluded_records = []
    for key, path in REFERENCE_CATALOG:
        if key in required:
            required_records.append({"id": key, "path": path, "reasons": reasons[key]})
        else:
            excluded_records.append({"id": key, "path": path, "reason": exclusions.get(key, "No current decision requires this reference")})
    return {
        "schema_version": 1,
        "status": "STRUCTURAL",
        "presentation_mode": routed_mode,
        "required_references": required_records,
        "excluded_references": excluded_records,
        "signals": signals,
        "limitations": [
            "This is a deterministic context-loading recommendation, not proof that a host loaded the files",
            "Reference routing does not establish model capability, runtime availability or media quality",
        ],
    }


def route_references(plan):
    """Public structural progressive-disclosure route for a prepared plan."""
    return _reference_route(plan)


def _validation_diagnostics(plan, errors):
    intent = plan.get("scene_intent", {}) if isinstance(plan, dict) else {}
    project = intent.get("project_id", "unknown") if isinstance(intent, dict) else "unknown"
    scene = intent.get("scene_id", "unknown") if isinstance(intent, dict) else "unknown"
    revision = plan.get("revision", "unknown") if isinstance(plan, dict) else "unknown"
    scope = f"{project}:{scene}:rev{revision}"
    limits = ["Structural validation only; no runtime, media, identity, physics or editorial judgment"]
    if not errors:
        return [decision_diagnostic(f"DEC-PLAN-{project}-{scene}-R{revision}", "plan_validation", scope, "PASS",
                                    ["Declared structural and causal invariants passed"],
                                    ["QG-01", "QG-03", "QG-07"], [],
                                    "Compile the plan or negotiate a versioned capability profile", "HIGH", limits)]
    return [decision_diagnostic(f"DEC-{item['id']}-{index+1}-{project}-{scene}-R{revision}", "plan_validation", scope,
                                item["outcome"], [item["reason"]], [item["gate"]], [], item["next_action"], "HIGH", limits)
            for index, item in enumerate(errors)]


def validate(plan):
    """Validate structural and declared semantic relationships, never media quality."""
    errors = []
    def add(*args, **kwargs):
        errors.append(issue(*args, **kwargs))
    require(isinstance(plan, dict), "plan must be an object")
    require(type(plan.get("schema_version")) is int and plan["schema_version"] == 1, "unsupported schema_version")
    require(type(plan.get("revision")) is int and plan["revision"] > 0, "plan revision must be a positive integer")
    intent = plan.get("scene_intent")
    require(isinstance(intent, dict), "scene_intent required")
    duration = intent.get("duration", {})
    require(isinstance(duration, dict), "scene_intent.duration must be an object")
    seconds = duration.get("target_seconds")
    floors = duration_floor(seconds)
    for key in ("project_id", "scene_id", "objective", "subjects", "objects", "environments", "actions", "hard_constraints", "preferences", "unknowns"):
        if key not in intent or (key in ("objective", "scene_id", "project_id") and not intent[key]):
            add("INTAKE", f"scene_intent.{key}", "Required intent field missing", "Supply the field or an explicit unresolved choice", "ASK", "QG-01")
    for key in ("project_id", "scene_id", "objective"):
        if key in intent:
            require(isinstance(intent[key], str) and bool(intent[key]), f"scene_intent.{key} must be a nonempty string")
    for key in ("subjects", "objects", "environments", "actions", "hard_constraints", "preferences", "unknowns"):
        string_list(intent.get(key), f"scene_intent.{key}")
    for key in ("dialogue_required", "audio_required"):
        if key in intent:
            require(type(intent[key]) is bool, f"scene_intent.{key} must be boolean")
    if "target" in intent:
        object_value(intent["target"], "scene_intent.target")
    require(bool(intent["actions"]) and bool(intent["subjects"] or intent["objects"] or intent["environments"]), "Intent requires actions and an entity/environment inventory")
    for key in floors:
        if not plan.get(key):
            add("DURATION_FLOOR", key, f"Structure required for {seconds}s", "Add the applicable structure", gate="QG-04")
    shots = indexed(plan.get("shots", []), "shots")
    require(shots, "at least one shot required")
    order = ordered(list(shots.values()))
    bible = object_value(plan.get("scene_bible", {}), "scene_bible")
    initial_state = object_value(bible.get("initial_state", {}), "scene_bible.initial_state")
    initial_state_ref = bible.get("initial_state_ref")
    if not isinstance(initial_state_ref, str) or not initial_state_ref:
        add("INITIAL_STATE_REF", "scene_bible.initial_state_ref", "Initial state reference is missing", "Declare the canonical scene-bible initial state reference", "ASK", "QG-07")
    entities = indexed(bible.get("entities", []), "entities")
    persistent_entities = set()
    for entity in entities.values():
        require(entity.get("permanence") in ("PERMANENT", "PERSISTENT", "TRANSIENT", "UNCERTAIN"), f"{entity['id']}: invalid permanence")
        require(isinstance(entity.get("description"), str) and entity["description"], f"{entity['id']}: entity description is required")
        if entity["permanence"] in ("PERMANENT", "PERSISTENT"):
            persistent_entities.add(entity["id"])
        if "permanent_state" in entity:
            object_value(entity["permanent_state"], f"{entity['id']}.permanent_state")
        if "invariants" in entity:
            string_list(entity["invariants"], f"{entity['id']}.invariants")
    for eid in intent["subjects"] + intent["objects"] + intent["environments"]:
        if eid not in entities:
            add("INTENT_ENTITY_LINK", "scene_intent", f"Missing entity definition: {eid}", "Define the entity before shot compilation", "ASK", "QG-01")
    complex_scene = seconds > 45 or len(shots) > 1 or len(intent["subjects"]) > 1
    if complex_scene:
        for field in ("project_id", "scene_id", "revision", "scope", "visual_style", "camera_language", "geography", "lighting", "time_of_day"):
            value = bible.get(field)
            if field in ("revision",) and type(value) is int and value > 0:
                continue
            if field not in bible or value in (None, ""):
                add("SCENE_BIBLE_FIELD", f"scene_bible.{field}", "Complex work needs an explicit Scene Bible field", "Complete the Scene Bible before shot compilation", "ASK", "QG-03")
            elif field != "revision" and not isinstance(value, str):
                add("SCENE_BIBLE_FIELD", f"scene_bible.{field}", "Scene Bible continuity field must be a nonempty string", "Normalize the Scene Bible field", "ASK", "QG-03")
        for field in ("relationships", "continuity_rules", "prohibited_drift"):
            if field not in bible or not isinstance(bible[field], list):
                add("SCENE_BIBLE_FIELD", f"scene_bible.{field}", "Complex work needs an explicit Scene Bible collection", "Declare relationships, continuity rules and prohibited drift", "ASK", "QG-03")
        if intent.get("audio_required") or intent.get("dialogue_required"):
            if not isinstance(bible.get("audio_identity"), dict) or not bible["audio_identity"]:
                add("SCENE_BIBLE_FIELD", "scene_bible.audio_identity", "Dialogue/audio work needs an explicit audio identity", "Declare voice, room-tone or an explicit external audio path", "ASK", "QG-10")
    references = optional_list(plan, "references")
    refs = indexed(references, "references")
    contacts = indexed(optional_list(plan, "contact_graphs"), "contact_graphs")
    constraints = optional_list(plan, "constraints")
    for constraint in constraints:
        require(isinstance(constraint, dict), "Each constraint must be an object")
        require(isinstance(constraint.get("constraint_id"), str) and constraint["constraint_id"], "Constraint IDs must be present and unique")
    constraint_ids = {c["constraint_id"] for c in constraints}
    require(len(constraint_ids) == len(constraints), "Constraint IDs must be present and unique")
    for constraint in constraints:
        require(constraint.get("kind") in ("GENERATION_HINT", "RUNTIME_CONTROL", "INPUT_REQUIREMENT", "QA_ASSERTION", "ASSEMBLY_RULE", "RIGHTS_SAFETY"), "Unknown constraint kind")
        require(constraint.get("priority") in ("CRITICAL", "HIGH", "MEDIUM", "LOW"), "Unknown constraint priority")
        require(isinstance(constraint.get("statement"), str) and constraint["statement"], "Constraint lacks statement")
        string_list(constraint.get("scope"), f"{constraint['constraint_id']}.scope", allow_empty=False)
        require(isinstance(constraint.get("validation"), dict) and constraint["validation"], "Constraint lacks validation")
    initial = flatten(bible.get("initial_state", {}))
    retention_rules = optional_list(plan, "retention_rules")
    locked = set()
    for r in retention_rules:
        require(isinstance(r, dict), "Each retention rule must be an object")
        require(isinstance(r.get("entity_id"), str) and r["entity_id"], "Retention rule needs entity_id")
        require(isinstance(r.get("property"), str) and r["property"], "Retention rule needs property")
        if r.get("policy") not in ("LOCKED", "FLEXIBLE", "DERIVED", "IGNORE") or r.get("entity_id") not in entities:
            add("RETENTION", "retention_rules", "Invalid policy or entity", "Resolve entity/property retention", "ASK", "QG-02")
        if r.get("policy") == "LOCKED":
            locked.add(f"{r['entity_id']}.{r['property']}")
        if r.get("policy") == "LOCKED" and (not r.get("anchor_refs") or not r.get("qa_obligation")):
            add("LOCK_WITHOUT_QA", "retention_rules", "Lock lacks anchor or QA obligation", "Add scoped anchors and media comparison", gate="QG-05")
        anchor_refs = r.get("anchor_refs", [])
        string_list(anchor_refs, "retention_rules.anchor_refs")
        for ref in anchor_refs:
            if ref not in refs:
                add("REFERENCE_LINK", "retention_rules", f"Missing anchor {ref}", "Supply the reference asset", gate="QG-02")
    for ref in refs.values():
        for field in ("kind", "locator", "content_hash", "evidence"):
            if field not in ref:
                add("REFERENCE_FIELD", ref["id"], f"Reference field is missing: {field}", "Complete the ReferenceAsset contract", "ASK", "QG-02")
        if ref.get("kind") not in ("image", "video", "audio", "text", "3d", "other"):
            add("REFERENCE_FIELD", ref["id"], "Reference kind is invalid", "Use image, video, audio, text, 3d or other", "ASK", "QG-02")
        if not isinstance(ref.get("locator"), str) or not ref.get("locator"):
            add("REFERENCE_FIELD", ref["id"], "Reference locator is missing", "Provide a reviewed path or URI without treating it as proof of access", "ASK", "QG-02")
        if ref.get("content_hash") is not None and not hash_value(ref.get("content_hash")):
            add("REFERENCE_FIELD", ref["id"], "Reference content_hash is invalid", "Record sha256 bytes or explicit null when not collected", "ASK", "QG-02")
        string_list(ref.get("roles", []), f"{ref['id']}.roles")
        string_list(ref.get("maps_to", []), f"{ref['id']}.maps_to")
        provenance = ref.get("provenance", {})
        if not isinstance(provenance, dict):
            add("REFERENCE_PROVENANCE", ref["id"], "Reference provenance must be an object", "Declare source, rights and consent scope", "ASK", "QG-02")
            provenance = {}
        for field in ("source", "rights_status", "consent_status"):
            if field not in provenance:
                add("REFERENCE_PROVENANCE", ref["id"], f"Reference provenance field is missing: {field}", "Declare source, rights and consent scope", "ASK", "QG-02")
        if "source" in provenance and (not isinstance(provenance["source"], str) or not provenance["source"]):
            add("REFERENCE_PROVENANCE", ref["id"], "Reference provenance source is empty", "Identify the source without exposing private data", "ASK", "QG-02")
        rights_states = ("CONFIRMED", "UNKNOWN", "RESTRICTED", "REJECTED", "NOT_APPLICABLE")
        for field in ("rights_status", "consent_status"):
            if field in provenance and provenance[field] not in rights_states:
                add("REFERENCE_PROVENANCE", ref["id"], f"Invalid {field}", "Use the canonical provenance status", "ASK", "QG-02")
        evidence_record = ref.get("evidence")
        if not isinstance(evidence_record, dict):
            add("REFERENCE_EVIDENCE", ref["id"], "Reference evidence record is missing", "Declare evidence status, claim type and confidence", "ASK", "QG-02")
            evidence_record = {}
        if evidence_record.get("status") not in ("CONFIRMED", "INFERRED", "PROPOSED", "UNKNOWN"):
            add("REFERENCE_EVIDENCE", ref["id"], "Reference evidence status is invalid or missing", "Use CONFIRMED, INFERRED, PROPOSED or UNKNOWN", "ASK", "QG-02")
        if evidence_record.get("claim_type") not in ("FACT", "ASSUMPTION", "HYPOTHESIS", "DECISION"):
            add("REFERENCE_EVIDENCE", ref["id"], "Reference evidence claim_type is invalid or missing", "Declare the claim type", "ASK", "QG-02")
        if evidence_record.get("confidence") not in ("HIGH", "MEDIUM", "LOW"):
            add("REFERENCE_EVIDENCE", ref["id"], "Reference evidence confidence is invalid or missing", "Declare evidence confidence", "ASK", "QG-02")
        if not ref.get("roles") or not ref.get("maps_to") or any(e not in entities for e in ref.get("maps_to", [])):
            add("REFERENCE_ROLE", ref["id"], "Reference mapping or role unresolved", "Assign source properties to existing entities", "ASK", "QG-02")
        if "sensitive" in ref:
            require(type(ref["sensitive"]) is bool, f"{ref['id']}.sensitive must be boolean")
        risky_roles = {"character_identity", "face", "likeness", "voice", "voice_identity", "identity_reference"}
        identity_reference = bool(ref.get("sensitive")) or bool(risky_roles.intersection(ref.get("roles", [])))
        if identity_reference:
            if provenance.get("rights_status") not in ("CONFIRMED", "NOT_APPLICABLE"):
                add("RIGHTS", ref["id"], "Identity/likeness/voice reference lacks confirmed rights scope", "Provide scoped rights evidence or remove the identity binding", gate="QG-02")
            if provenance.get("consent_status") not in ("CONFIRMED", "NOT_APPLICABLE"):
                add("RIGHTS", ref["id"], "Identity/likeness/voice reference lacks confirmed consent scope", "Provide scoped consent or remove likeness/voice", gate="QG-02")
    conflicts = optional_list(plan, "reference_conflicts")
    for conflict in conflicts:
        require(isinstance(conflict, dict), "Each reference conflict must be an object")
        require(isinstance(conflict.get("id"), str) and conflict["id"], "Reference conflict needs id")
        if conflict.get("status") != "RESOLVED":
            add("REFERENCE_CONFLICT", conflict.get("id", "reference_conflicts"), "Reference precedence is unresolved", "Resolve precedence or preserve explicit branches", "ASK", "QG-02")
    ends, elapsed = {}, 0.0
    for key in order:
        shot = shots[key]
        dependency_ids = string_list(shot.get("dependency_ids", []), f"{key}.dependency_ids")
        string_list(shot.get("active_subject_ids", []), f"{key}.active_subject_ids")
        string_list(shot.get("supporting_subject_ids", []), f"{key}.supporting_subject_ids")
        string_list(shot.get("references", []), f"{key}.references")
        string_list(shot.get("capability_requirements", []), f"{key}.capability_requirements")
        string_list(shot.get("degradable_capability_requirements", []), f"{key}.degradable_capability_requirements")
        shot_constraints = string_list(shot.get("constraints", []), f"{key}.constraints")
        acceptance_ids = string_list(shot.get("acceptance_ids", []), f"{key}.acceptance_ids")
        start_delta = object_value(shot.get("start_state_delta", {}), f"{key}.start_state_delta")
        end_delta = object_value(shot.get("end_state_delta", {}), f"{key}.end_state_delta")
        state_changes = optional_list(shot, "state_changes", f"{key}.state_changes")
        transition = object_value(shot.get("transition", {}), f"{key}.transition")
        if "review_ref" in transition:
            require(isinstance(transition["review_ref"], str) and transition["review_ref"], f"{key}: transition.review_ref must be a nonempty string")
        parameters = object_value(shot.get("parameters", {}), f"{key}.parameters")
        required_dependency_properties = object_value(shot.get("required_dependency_properties", {}), f"{key}.required_dependency_properties")
        require(number(shot.get("duration_s"), True), f"{key}: invalid duration_s")
        require(shot.get("generation_mode") in ("T2V", "I2V", "TI2V", "FLF2V", "R2V"), f"{key}: invalid generation_mode")
        require(shot.get("risk") in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"), f"{key}: invalid risk")
        elapsed += shot["duration_s"]
        if shot.get("scene_id") != intent.get("scene_id"):
            add("SCENE_LINK", key, "Shot belongs to another scene", "Use the owning scene_id")
        for field in ("purpose", "start_state_ref", "action_primitives", "camera", "acceptance_ids"):
            if not shot.get(field):
                add("SHOT_FIELD", f"{key}.{field}", "Shot is underspecified", "Add an explicit shot decision", "ASK", "QG-04")
        for field in ("active_subject_ids", "supporting_subject_ids", "references", "generation_mode", "capability_requirements", "risk", "start_state_delta", "end_state_delta"):
            if field not in shot:
                add("SHOT_FIELD", f"{key}.{field}", "Shot contract field is missing", "Declare the field explicitly, including an empty collection when inapplicable", "ASK", "QG-04")
        require(isinstance(shot.get("camera"), dict), f"{key}: camera must be an object")
        for field in ("size", "angle", "focal_length", "framing", "focus", "depth_of_field", "motion_blur", "exposure", "lighting", "eyeline", "movement", "screen_direction", "axis_policy", "edit_rhythm"):
            if field not in shot["camera"] or shot["camera"][field] in (None, ""):
                add("CAMERA_FIELD", f"{key}.camera.{field}", "Camera continuity field is missing", "Declare camera geography and movement continuity", "ASK", "QG-13")
        require(isinstance(shot["camera"].get("movement", {}), dict), f"{key}: camera.movement must be an object")
        string_list(shot.get("action_primitives"), f"{key}: actions", allow_empty=False)
        required_gates = acceptance_ids
        if len(required_gates) != len(set(required_gates)) or any(g not in {f"QG-{i:02d}" for i in range(1,18)} for g in required_gates):
            add("ACCEPTANCE_CONTRACT", key, "Unknown or duplicate required gate IDs", "Supply the applicable canonical gates", gate="QG-17")
        for cid in shot_constraints:
            if cid not in constraint_ids:
                add("CONSTRAINT_LINK", key, f"Missing scoped constraint {cid}", "Define the constraint and its review oracle", gate="QG-16")
        if shot.get("contact_graph_ref"):
            require(isinstance(shot["contact_graph_ref"], str), f"{key}: contact_graph_ref must be a string")
            contact = contacts.get(shot["contact_graph_ref"])
            if not contact or contact.get("shot_id") != key or not all(contact.get(k) for k in ("actor", "target", "effector", "phases", "success_criterion")):
                add("CONTACT_GRAPH", key, "Contact graph is missing or incomplete", "Define actor/target/effector/phases and visible success", gate="QG-09")
            else:
                require(all(isinstance(contact.get(k), str) and contact[k] for k in ("shot_id", "actor", "target", "effector", "success_criterion")), f"{key}: contact graph identifiers must be nonempty strings")
                string_list(contact["phases"], f"{key}.contact_graph.phases", allow_empty=False)
                if contact["actor"] not in entities or contact["target"] not in entities or any(x not in shot["action_primitives"] for x in contact["phases"]):
                    add("CONTACT_CAUSE", key, "Contact actors or phases do not resolve", "Bind contact to the actual entities and shot actions", gate="QG-09")
        if shot.get("lifecycle_status") not in ("PLANNED", "READY"):
            add("STATE_CHANNEL", key, "Planning validator cannot attest runtime lifecycle", "Use observed artifact validation for runtime records")
        deps = dependency_ids
        expected_refs = {f"continuity:{d}:end" for d in deps} if deps else {initial_state_ref}
        if shot.get("start_state_ref") not in expected_refs and not (len(deps) > 1 and shot.get("start_state_ref") == f"continuity:{key}:merged"):
            add("STATE_REF", key, "start_state_ref does not resolve to a dependency or initial state", "Resolve the referenced state")
        state = copy.deepcopy(initial)
        inherited = {}
        for dep in deps:
            for prop, value in ends[dep].items():
                if prop in inherited and inherited[prop] != value:
                    add("MERGE_CONFLICT", key, f"Dependencies disagree about {prop}", "Resolve the branch state before merging")
                inherited[prop] = value
        state.update(inherited)
        for prop, value in state.items():
            if value is None or value == "UNKNOWN":
                add("UNRESOLVED_STATE", key, f"Material boundary state {prop} is unresolved", "Resolve the state or declare an intentional bounded ambiguity", "ASK")
        for prop, value in start_delta.items():
            if state.get(prop, "UNKNOWN") != value:
                add("START_CONTRADICTION", key, f"{prop}: inherited {state.get(prop, 'UNKNOWN')!r}, requested {value!r}", "Add a causal transition in the preceding shot or repair state")
        changes = state_changes
        applied = set()
        for change in changes:
            require(isinstance(change, dict) and all(k in change for k in ("property", "prior", "next", "cause")), f"{key}: state_changes need property/prior/next/cause")
            prop = change["property"]
            require(isinstance(prop, str) and prop, f"{key}: state_changes property must be a nonempty string")
            require(isinstance(change["cause"], str) and change["cause"], f"{key}: state_changes cause must be a nonempty string")
            if prop in applied:
                add("DUPLICATE_DELTA", key, f"Repeated delta for {prop}", "Split phases into separate state boundaries")
            applied.add(prop)
            if state.get(prop, "UNKNOWN") != change["prior"]:
                add("DELTA_PRECONDITION", key, f"Wrong prior state for {prop}", "Use actual inherited state")
            if change["prior"] in (None, "UNKNOWN"):
                add("UNRESOLVED_PRECONDITION", key, f"Prior state of {prop} is unknown", "Resolve the material precondition before this transition", "ASK")
            if change["cause"] not in shot.get("action_primitives", []) and change["cause"] != transition.get("id"):
                add("MISSING_CAUSE", key, f"No visible action/declared transition causes {prop}", "Name the causal action or reviewed transition")
            if prop in locked and not transition.get("review_ref"):
                add("LOCK_CHANGED", key, f"Locked property changed: {prop}", "Retain invariant or record a reviewed transition", gate="QG-05")
            root, _, leaf = prop.partition(".")
            identity_tokens = {"identity", "identity_ref", "face", "likeness", "voice", "appearance", "wardrobe", "geometry"}
            if root in persistent_entities and (leaf in identity_tokens or any(token in leaf for token in identity_tokens)) and not transition.get("review_ref"):
                add("PERSISTENT_CHANGE", key, f"Persistent identity/geometry property changed without a reviewed transition: {prop}", "Add an explicit transition.review_ref and human review, or keep the invariant", "HUMAN_REVIEW_REQUIRED", "QG-05")
            state[prop] = change["next"]
        for prop, value in end_delta.items():
            if state.get(prop, "UNKNOWN") != value:
                add("END_CONTRADICTION", key, f"End state {prop} lacks matching cause/delta", "Add the causal state change")
        for prop, value in state.items():
            if value is None or value == "UNKNOWN":
                add("UNRESOLVED_END_STATE", key, f"End state {prop} is unresolved", "Resolve the material end state before prompt compilation", "ASK")
        ends[key] = state
        for eid in shot.get("active_subject_ids", []) + shot.get("supporting_subject_ids", []):
            if eid not in entities:
                add("ENTITY_LINK", key, f"Unknown entity {eid}", "Resolve the entity roster", "ASK", "QG-01")
        for rid in shot.get("references", []):
            if rid not in refs and rid not in {f"anchor:{d}:last_frame" for d in deps}:
                add("REFERENCE_LINK", key, f"Unknown reference {rid}", "Resolve asset or dependency anchor", gate="QG-02")
        if shot.get("camera", {}).get("axis_policy") == "CROSS_AXIS" and not shot.get("camera", {}).get("cut_motivation"):
            add("AXIS", key, "Axis crossing has no motivation", "Add neutral coverage or motivate transition", "SPLIT", "QG-13")
        if len(shot.get("action_primitives", [])) > 8:
            add("SHOT_LOAD", key, "More than eight action phases need a reviewed load budget", "Split or provide validated coverage", "SPLIT", "QG-04")
    # Derived representations are checked against their canonical owners.
    if "shot_graph" in plan:
        graph = object_value(plan["shot_graph"], "shot_graph")
        graph_nodes = string_list(graph.get("nodes", []), "shot_graph.nodes")
        graph_edges = graph.get("edges", [])
        require(isinstance(graph_edges, list), "shot_graph.edges must be an array")
        for edge in graph_edges:
            require(isinstance(edge, dict), "shot_graph edges must be objects")
        expected_edges = {(d,s["id"]) for s in shots.values() for d in s.get("dependency_ids", [])}
        actual_edges = {(e.get("from"), e.get("to")) for e in graph_edges}
        if set(graph_nodes) != set(shots) or actual_edges != expected_edges or any(e.get("state_channel") != "PLANNED" for e in graph_edges):
            add("GRAPH_DRIFT", "shot_graph", "Derived graph disagrees with ShotSpec dependencies", "Rebuild graph from canonical shot dependencies")
        for edge in graph_edges:
            target = shots.get(edge.get("to"), {})
            if not isinstance(edge.get("from"), str) or not isinstance(edge.get("to"), str) or edge.get("from") not in shots or edge.get("to") not in shots:
                add("GRAPH_EDGE", "shot_graph", "Graph edge does not resolve to canonical shots", "Rebuild the dependency edge from ShotSpec")
                continue
            string_list(edge.get("state_properties", []), "shot_graph.state_properties")
            string_list(edge.get("anchor_refs", []), "shot_graph.anchor_refs")
            require(isinstance(edge.get("state_delta", {}), dict), "shot_graph.state_delta must be an object")
            if edge.get("state_properties") != sorted(target.get("start_state_delta", {})) or edge.get("state_delta") != target.get("start_state_delta", {}) or edge.get("anchor_refs") != sorted(target.get("references", [])):
                add("GRAPH_EDGE", f"shot_graph.{edge.get('to')}", "Dependency edge omits required state delta or anchor scope", "Rebuild the edge from the canonical target shot", gate="QG-07")
    continuity_states = optional_list(plan, "continuity_states")
    for state_record in continuity_states:
        require(isinstance(state_record, dict), "continuity_states entries must be objects")
        key = state_record.get("scope")
        if key not in ends or state_record.get("state_channel") != "PLANNED" or ("end_state" in state_record and state_record["end_state"] != ends[key]):
            add("LEDGER_DRIFT", "continuity_states", "Stored state disagrees with causal recomputation or channel", "Recompute planned ledger; keep observations separate")
    if continuity_states and (len(continuity_states) != len(shots) or {s.get("scope") for s in continuity_states} != set(shots)):
        add("LEDGER_COVERAGE", "continuity_states", "Each shot needs exactly one planned boundary record", "Rebuild the complete planned ledger")
    assembly = object_value(plan["assembly_plan"], "assembly_plan") if "assembly_plan" in plan else {}
    edit_order = assembly.get("shot_ids", order)
    string_list(edit_order, "assembly_plan.shot_ids")
    if len(edit_order) != len(shots) or set(edit_order) != set(shots):
        add("ASSEMBLY_ORDER", "assembly_plan", "Assembly must contain each shot exactly once", "Declare complete edit order")
    if "target_duration_s" in assembly:
        require(number(assembly["target_duration_s"], True), "assembly_plan.target_duration_s must be positive")
    if "target_duration_s" in assembly and assembly["target_duration_s"] != seconds:
        add("ASSEMBLY_DURATION", "assembly_plan", "Assembly target differs from intent", "Keep the requested duration or record an approved revision")
    if abs(elapsed - seconds) > 0.001:
        add("TOTAL_DURATION", "assembly_plan", f"Shot total {elapsed:g}s differs from target {seconds:g}s", "Allocate shot durations explicitly", gate="QG-04")
    timeline = optional_list(plan, "narrative_timeline")
    if timeline:
        indexed(timeline, "narrative_timeline")
        clock = 0
        if [b.get("shot_id") for b in timeline] != edit_order:
            add("TIMELINE_ORDER", "narrative_timeline", "Timeline does not follow the declared edit order", "Resolve story order explicitly", gate="QG-03")
        for beat in timeline:
            require(isinstance(beat.get("time"), dict), f"{beat['id']}: timeline time must be an object")
            shot = shots.get(beat.get("shot_id"), {})
            start, end = beat.get("time", {}).get("start_s"), beat.get("time", {}).get("end_s")
            if not number(start) or not number(end) or abs(start-clock) > 0.001 or abs((end-start)-shot.get("duration_s", 0)) > 0.001:
                add("TIMELINE_INTERVAL", beat["id"], "Timeline has a gap, overlap or duration mismatch", "Reallocate intervals consistently", gate="QG-03")
            clock = end if number(end) else clock
    raw_lines = optional_list(plan, "dialogue_timeline")
    lines = []
    for index, raw_line in enumerate(raw_lines):
        line = copy.deepcopy(raw_line) if isinstance(raw_line, dict) else {}
        aliases = {
            "id": ("dialogue_id",),
            "text": ("line",),
            "intention": ("intent",),
            "start_s": ("start",),
            "end_s": ("end",),
            "listener": ("target_listener",),
        }
        for canonical_name, names in aliases.items():
            if canonical_name not in line:
                for name in names:
                    if name in line:
                        line[canonical_name] = line[name]
                        break
        line.setdefault("id", f"dialogue_invalid_{index}")
        lines.append(line)
    indexed(lines, "dialogue_timeline")
    for line in lines:
        key = line.get("shot_id")
        if key not in shots or line.get("speaker") not in shots.get(key, {}).get("active_subject_ids", []):
            add("SPEAKER", line["id"], "Speaker/shot assignment unresolved", "Assign an active speaker and listener", "ASK", "QG-10")
            continue
        if not isinstance(line.get("listener"), str) or line["listener"] not in entities or line["listener"] == line.get("speaker"):
            add("LISTENER", line["id"], "Dialogue listener is missing or unresolved", "Assign a distinct listener or declare a reviewed voiceover path", "ASK", "QG-10")
        for field in ("intention", "delivery", "emotion", "gaze"):
            if not isinstance(line.get(field), str) or not line[field]:
                add("DIALOGUE_FIELD", f"{line['id']}.{field}", "Dialogue performance field is missing", "Declare intention, delivery, emotion and gaze", "ASK", "QG-10")
        for field in ("pause_policy", "overlap_policy"):
            value = line.get(field)
            if not ((isinstance(value, str) and bool(value)) or (isinstance(value, dict) and bool(value))):
                add("DIALOGUE_FIELD", f"{line['id']}.{field}", "Dialogue pause/overlap policy is missing", "Declare the timing behavior explicitly", "ASK", "QG-10")
        if "reaction_at_s" not in line or (line.get("reaction_at_s") is not None and not number(line.get("reaction_at_s"))):
            add("DIALOGUE_FIELD", f"{line['id']}.reaction_at_s", "Dialogue reaction timing is missing or invalid", "Declare a reaction time or explicit null", "ASK", "QG-11")
        require(isinstance(line.get("text"), str) and bool(line["text"]), f"{line['id']}: dialogue text is required")
        if "visible_speech" in line:
            require(type(line["visible_speech"]) is bool, f"{line['id']}: visible_speech must be boolean")
        if "intentional_overlap" in line:
            require(type(line["intentional_overlap"]) is bool, f"{line['id']}: intentional_overlap must be boolean")
        start, end = line.get("start_s"), line.get("end_s")
        if not number(start) or not number(end) or not (0 <= start < end <= shots[key]["duration_s"]):
            add("DIALOGUE_TIME", line["id"], "Line interval is outside shot", "Resolve dialogue timing", "ASK", "QG-10")
        reaction = line.get("reaction_at_s")
        if number(reaction) and number(end) and reaction < end and not line.get("intentional_overlap"):
            add("REACTION_ORDER", line["id"], "Reaction precedes completed line without explicit overlap", "Declare interruption or move reaction", "ASK", "QG-11")
        if line.get("visible_speech") and (not line.get("audio_source") or not line.get("lip_sync_path")):
            add("LIP_SYNC_PATH", line["id"], "Visible speech requires separate audio and synchronization paths", "Provide audio and confirmed sync adapter or propose voiceover", "DEGRADED", "QG-12")
        try:
            normalize_dialogue_line(line, f"dialogue_timeline.{line['id']}")
        except ContractError as exc:
            add("DIALOGUE_CONTRACT", line["id"], str(exc),
                "Declare listener reaction, causal order, voice strategy and lip-sync strategy explicitly",
                "ASK", "QG-10")
    for i, left in enumerate(lines):
        for right in lines[i+1:]:
            if left.get("shot_id") == right.get("shot_id") and all(number(x.get(k)) for x in (left, right) for k in ("start_s", "end_s")):
                if max(left["start_s"], right["start_s"]) < min(left["end_s"], right["end_s"]) and not (left.get("intentional_overlap") and right.get("intentional_overlap")):
                    add("SPEECH_OVERLAP", left["id"], "Overlapping speech without a designed overlap", "Encode overlap or separate the turns", "ASK", "QG-10")
    audio_timeline = optional_list(plan, "audio_timeline")
    indexed(audio_timeline, "audio_timeline")
    for audio in audio_timeline:
        shot = shots.get(audio.get("shot_id"), {})
        if not all(number(audio.get(k)) for k in ("start_s", "end_s")) or not (0 <= audio["start_s"] < audio["end_s"] <= shot.get("duration_s", 0)):
            add("AUDIO_TIME", audio.get("id", "audio_timeline"), "Audio event is outside shot", "Re-time or explicitly split a bridge event", gate="QG-14")
        if audio.get("layer") == "effects" and audio.get("cause") not in shot.get("action_primitives", []):
            add("AUDIO_CAUSE", audio.get("id", "audio_timeline"), "Diegetic sound lacks visible cause", "Bind event to action or mark non-diegetic", gate="QG-14")
    if intent.get("dialogue_required") and not lines:
        add("DIALOGUE_MISSING", "dialogue_timeline", "Required dialogue has no turns", "Add speaker, listener, timing, performance and audio path", "ASK", "QG-10")
    if intent.get("audio_required") and not audio_timeline:
        add("AUDIO_MISSING", "audio_timeline", "Required sound has no layer/event plan", "Add sources, mix and timing", "ASK", "QG-14")
    reference_timeline = optional_list(plan, "reference_timeline")
    if seconds >= 60 and refs and not reference_timeline:
        add("REFERENCE_TIMELINE", "reference_timeline", "Long-form references need scoped timing", "Map reference use to shots", gate="QG-02")
    diagnostics = optional_list(plan, "decision_diagnostics")
    diagnostic_fields = {"decision_id", "stage", "input_scope", "result", "reasons", "evidence_refs", "alternatives", "next_action", "confidence", "limitations"}
    for diagnostic in diagnostics:
        require(isinstance(diagnostic, dict), "decision_diagnostics entries must be objects")
        require(diagnostic_fields <= set(diagnostic), "Decision diagnostic is missing required fields")
        for field in ("decision_id", "stage", "input_scope", "result", "next_action"):
            require(isinstance(diagnostic[field], str) and diagnostic[field], f"decision_diagnostics.{field} must be a nonempty string")
        require(diagnostic["confidence"] in ("HIGH", "MEDIUM", "LOW"), "Invalid decision diagnostic confidence")
        for field in ("reasons", "evidence_refs", "alternatives", "limitations"):
            string_list(diagnostic[field], f"decision_diagnostics.{field}")
    if seconds >= 90:
        if "alternative_branches" in plan:
            branches = plan["alternative_branches"]
            require(isinstance(branches, list) and bool(branches), "alternative_branches must be a nonempty array")
            indexed(branches, "alternative_branches")
            for branch in branches:
                require(branch.get("strategy") in ("direct", "split", "anchor", "reframe", "human_review"), "Invalid alternative branch strategy")
                require(isinstance(branch.get("status"), str) and branch["status"], "Alternative branch status is required")
                require(isinstance(branch.get("reason"), str) and branch["reason"], "Alternative branch reason is required")
                require(isinstance(branch.get("fallback"), str) and branch["fallback"], "Alternative branch fallback is required")
        if "recovery_checkpoints" in plan:
            checkpoints = plan["recovery_checkpoints"]
            require(isinstance(checkpoints, list) and bool(checkpoints), "recovery_checkpoints must be a nonempty array")
            indexed(checkpoints, "recovery_checkpoints")
            for checkpoint in checkpoints:
                require(checkpoint.get("after_shot_id") in shots, "Recovery checkpoint must resolve to a shot")
                for field in ("trigger", "action"):
                    require(isinstance(checkpoint.get(field), str) and checkpoint[field], f"Recovery checkpoint {field} is required")
        if "provenance_manifest" in plan:
            manifest = object_value(plan["provenance_manifest"], "provenance_manifest")
            require(manifest.get("schema_version") == 1, "Unsupported provenance manifest schema")
            require(type(manifest.get("plan_revision")) is int and manifest["plan_revision"] == plan["revision"], "Provenance manifest revision mismatch")
            require(manifest.get("status") in ("PENDING", "COMPLETE"), "Invalid provenance manifest status")
            string_list(manifest.get("required_records"), "provenance_manifest.required_records", allow_empty=False)
        if "human_checkpoints" in plan:
            human = plan["human_checkpoints"]
            require(isinstance(human, list) and bool(human), "human_checkpoints must be a nonempty array")
            indexed(human, "human_checkpoints")
            for checkpoint in human:
                require(isinstance(checkpoint.get("stage"), str) and checkpoint["stage"], "Human checkpoint stage is required")
                require(isinstance(checkpoint.get("scope"), list) and checkpoint["scope"], "Human checkpoint scope is required")
                string_list(checkpoint["scope"], "human_checkpoints.scope", allow_empty=False)
                require(type(checkpoint.get("required")) is bool, "Human checkpoint required must be boolean")
    strategy = object_value(plan["generation_strategy"], "generation_strategy") if "generation_strategy" in plan else {}
    if len(shots) > 1 and (not strategy.get("reanchor_every_shots") or strategy.get("reanchor_every_shots", 0) > 8):
        add("UNBOUNDED_CHAIN", "generation_strategy", "No bounded canonical re-anchor policy", "Set a project-specific reset interval and drift review", gate="QG-05")
    if plan.get("execution_mode", "PLAN_ONLY") != "PLAN_ONLY":
        add("MODE_BOUNDARY", "execution_mode", "Planning API only supports PLAN_ONLY", "Use explicit runtime subcommand with preflight and authorization", gate="QG-17")
    computed_complexity = _complexity_vector(intent, list(shots.values()), references, lines, list(contacts.values()))
    if "complexity" in plan:
        authored_complexity = object_value(plan["complexity"], "complexity")
        if authored_complexity != computed_complexity:
            add("COMPLEXITY_DRIFT", "complexity", "Stored routing vector disagrees with canonical authored records", "Recompute complexity and rerun depth routing", "ASK", "QG-04")
    if "presentation_mode" in plan:
        require(plan["presentation_mode"] in ("FAST", "CINEMATIC", "PRODUCTION", "DIRECTOR"), "Invalid presentation_mode")
        routed_mode, _ = _route_complexity(intent, list(shots.values()), computed_complexity)
        if plan["presentation_mode"] != routed_mode:
            add("ROUTING_DRIFT", "presentation_mode", "Stored depth label disagrees with complexity routing", "Use the computed depth or record a reviewed routing override", "ASK", "QG-04")
    if "reference_route" in plan:
        authored_route = object_value(plan["reference_route"], "reference_route")
        if authored_route != _reference_route(plan, computed_complexity):
            add("REFERENCE_ROUTE_DRIFT", "reference_route", "Stored progressive-disclosure route disagrees with canonical scene signals", "Recompute the structural route and load only the required references", "ASK", "QG-04")
    return {"status": "FAIL" if errors else "PASS", "scope": "STRUCTURAL_PLAN_ONLY", "issues": errors,
            "diagnostics": _validation_diagnostics(plan, errors), "shot_order": order, "end_states": ends,
            "limitations": ["Does not verify visual identity, physics, editorial quality or model feasibility"]}


def prepare(treatment):
    """Enrich an authored treatment; never write a story from keyword guesses."""
    require(isinstance(treatment, dict), "treatment must be an object")
    plan = copy.deepcopy(treatment)
    plan.setdefault("schema_version", 1)
    plan.setdefault("revision", 1)
    plan.setdefault("execution_mode", "PLAN_ONLY")
    plan.setdefault("references", [])
    intent = object_value(plan.get("scene_intent"), "scene_intent")
    require(isinstance(intent.get("scene_id"), str) and intent["scene_id"], "scene_intent.scene_id must be a nonempty string")
    duration = object_value(intent.get("duration"), "scene_intent.duration")
    require(number(duration.get("target_seconds"), True), "scene_intent.duration.target_seconds must be positive")
    bible = object_value(plan.get("scene_bible"), "scene_bible")
    shots = plan.get("shots")
    require(isinstance(shots, list), "shots must be an array")
    bible.setdefault("initial_state_ref", f"scene_bible:{intent['scene_id']}:initial")
    for shot in shots:
        require(isinstance(shot, dict), "Each shot must be an object")
        require(isinstance(shot.get("id"), str) and shot["id"], "Each shot needs a nonempty id")
        require(number(shot.get("duration_s"), True), f"{shot['id']}: invalid duration_s")
        string_list(shot.get("dependency_ids", []), f"{shot['id']}.dependency_ids")
        string_list(shot.get("action_primitives", []), f"{shot['id']}.action_primitives")
        changes = optional_list(shot, "state_changes", f"{shot['id']}.state_changes")
        for change in changes:
            require(isinstance(change, dict) and all(k in change for k in ("property", "prior", "next", "cause")), f"{shot['id']}: state_changes need property/prior/next/cause")
            require(isinstance(change["property"], str) and change["property"], f"{shot['id']}: state_changes property must be a nonempty string")
            require(isinstance(change["cause"], str) and change["cause"], f"{shot['id']}: state_changes cause must be a nonempty string")
        if "camera" in shot:
            object_value(shot["camera"], f"{shot['id']}.camera")
    for key in ("references", "retention_rules", "reference_conflicts", "dialogue_timeline", "audio_timeline", "contact_graphs", "constraints"):
        optional_list(plan, key)
    order = ordered(shots)
    for shot in shots:
        shot.setdefault("scene_id", intent["scene_id"])
        shot.setdefault("revision", plan["revision"])
        shot.setdefault("lifecycle_status", "PLANNED")
        shot.setdefault("generation_artifact_ref", None)
        shot.setdefault("artifact_observation_ref", None)
        deps = shot.setdefault("dependency_ids", [])
        shot.setdefault("start_state_ref", f"continuity:{deps[0]}:end" if len(deps) == 1 else f"continuity:{shot['id']}:merged" if deps else bible["initial_state_ref"])
        shot.setdefault("start_state_delta", {})
        shot.setdefault("end_state_delta", {c["property"]: c["next"] for c in shot.get("state_changes", [])})
    if "shot_graph" not in plan:
        plan["shot_graph"] = {"nodes": order, "edges": [{"from": dep, "to": s["id"], "state_channel": "PLANNED", "state_properties": sorted(s.get("start_state_delta", {})), "state_delta": copy.deepcopy(s.get("start_state_delta", {})), "anchor_refs": sorted(s.get("references", []))} for s in shots for dep in s.get("dependency_ids", [])]}
    plan.setdefault("assembly_plan", {"shot_ids": order, "target_duration_s": intent["duration"]["target_seconds"], "fps": None, "codec": None, "container": None, "audio_alignment": "REQUIRES_REVIEW"})
    require(isinstance(plan["assembly_plan"], dict) and isinstance(plan["assembly_plan"].get("shot_ids"), list), "assembly_plan requires shot_ids: an ordered array of canonical shot IDs; omit assembly_plan to derive it")
    string_list(plan["assembly_plan"]["shot_ids"], "assembly_plan.shot_ids", allow_empty=False)
    require(len(plan["assembly_plan"]["shot_ids"]) == len(order) and set(plan["assembly_plan"]["shot_ids"]) == set(order), "assembly_plan.shot_ids must contain each shot exactly once")
    plan.setdefault("generation_strategy", {"type": "SHORT_SEGMENTS", "reanchor_every_shots": 3, "evidence_status": "PROPOSED", "drift_budget": "PROJECT_REVIEW_REQUIRED"})
    if intent["duration"]["target_seconds"] >= 90:
        plan.setdefault("alternative_branches", [{"id": "branch_direct", "strategy": "direct", "status": "PRIMARY", "reason": "Use the authored shot graph when each transition remains feasible", "fallback": "human_review"}])
        plan.setdefault("recovery_checkpoints", [{"id": "recovery_boundary_001", "after_shot_id": order[-1], "trigger": "Rejected, stale or continuity-conflicted segment", "action": "Re-anchor from the nearest accepted canonical boundary and revalidate descendants"}])
        plan.setdefault("provenance_manifest", {"schema_version": 1, "plan_revision": plan["revision"], "status": "PENDING", "required_records": ["profile", "model", "runtime", "workflow", "inputs", "artifacts"], "next_action": "Attach immutable runtime and artifact records before delivery"})
        plan.setdefault("human_checkpoints", [{"id": "human_delivery_review", "stage": "pre_delivery", "scope": ["identity", "rights", "story", "audio", "editorial_quality"], "required": True}])
    timeline, clock = [], 0.0
    by_id = indexed(shots, "shots")
    for key in plan["assembly_plan"]["shot_ids"]:
        s = by_id[key]
        timeline.append({"id": f"beat_{key}", "shot_id": key, "time": {"start_s": clock, "end_s": clock+s["duration_s"]}, "purpose": s.get("purpose", ""), "action": s.get("action_primitives", []), "prerequisites": s.get("dependency_ids", [])})
        clock += s["duration_s"]
    plan.setdefault("narrative_timeline", timeline)
    plan.setdefault("reference_timeline", [{"shot_id": s["id"], "reference_ids": s.get("references", [])} for s in shots])
    dialogue = optional_list(plan, "dialogue_timeline")
    normalized_dialogue = []
    for index, line in enumerate(dialogue):
        require(isinstance(line, dict), "dialogue_timeline entries must be objects")
        try:
            normalized_dialogue.append(normalize_dialogue_line(line, f"dialogue_timeline[{index}]"))
        except ContractError:
            # Planning remains diagnostic for incomplete authored dialogue.  The
            # validation report carries the blocking contract issue; compilation
            # still refuses the unresolved line later.
            normalized_dialogue.append(copy.deepcopy(line))
    plan["dialogue_timeline"] = normalized_dialogue
    dialogue = normalized_dialogue
    contacts = optional_list(plan, "contact_graphs")
    for contact in contacts:
        require(isinstance(contact, dict), "contact_graphs entries must be objects")
    complexity = _complexity_vector(intent, shots, plan["references"], dialogue, contacts)
    if "complexity" in plan:
        object_value(plan["complexity"], "complexity")
    else:
        plan["complexity"] = complexity
    routed_mode, route_reasons = _route_complexity(intent, shots, complexity)
    plan.setdefault("presentation_mode", routed_mode)
    plan.setdefault("reference_route", _reference_route(plan, complexity))
    plan.setdefault("decision_diagnostics", [decision_diagnostic(
        f"DEC-ROUTE-{intent.get('project_id', 'unknown')}-{intent['scene_id']}-R{plan['revision']}",
        "complexity_routing", f"{intent.get('project_id', 'unknown')}:{intent['scene_id']}:rev{plan['revision']}",
        plan["presentation_mode"], route_reasons, ["R-PLAN-01", "R-PLAN-02", "QG-04"],
        ["FAST", "CINEMATIC", "PRODUCTION", "DIRECTOR"],
        "Load the routed references and resolve any blocked complexity gate", "HIGH",
        ["Routing is structural; it does not prove model feasibility or media quality"])])
    # Generate states before validating the duration floor; validate independently recomputes them.
    if "continuity_states" not in plan:
        plan["continuity_states"] = [{"scope": s["id"], "state_channel": "PLANNED", "inherited_from": s["start_state_ref"]} for s in shots]
    report = validate(plan)
    for state in plan["continuity_states"]:
        if isinstance(state, dict) and state.get("scope") in report["end_states"]:
            state.setdefault("end_state", report["end_states"][state["scope"]])
    plan["validation"] = report
    return plan


SECTIONS = ("subject_and_identity", "setting_and_time", "action_sequence", "performance", "camera", "lighting_and_style", "audio_or_sync", "continuity", "constraints", "references")


def compile_plan(plan, profile=None):
    report = validate(plan)
    require(report["status"] == "PASS", "Plan has blocking issues; validate and repair before compilation")
    if profile is not None:
        require(isinstance(profile, dict), "profile must be an object")
        require(isinstance(profile.get("id"), str) and profile["id"], "profile.id is required when compiling an adapted view")
    bible = plan["scene_bible"]
    outputs = []
    all_entities = copy.deepcopy(bible["entities"])
    scene_reference_assets = copy.deepcopy(plan.get("references", []))
    scene_reference_ids = [ref["id"] for ref in scene_reference_assets]
    compiled_dialogue = []
    for index, line in enumerate(plan.get("dialogue_timeline", [])):
        try:
            compiled_dialogue.append(normalize_dialogue_line(line, f"dialogue_timeline[{index}]"))
        except ContractError as exc:
            require(False, f"dialogue_timeline[{index}] cannot be compiled: {exc}")
    for shot in plan["shots"]:
        active_ids = list(shot.get("active_subject_ids", []))
        supporting_ids = list(shot.get("supporting_subject_ids", []))
        compiled_ids = active_ids + [item for item in supporting_ids if item not in active_ids]
        shot_reference_ids = list(shot.get("references", []))
        all_reference_ids = list(dict.fromkeys(scene_reference_ids + shot_reference_ids))
        shot_contacts = [copy.deepcopy(contact) for contact in plan.get("contact_graphs", []) if isinstance(contact, dict) and contact.get("shot_id") == shot["id"]]
        sections = {
            "subject_and_identity": {"entities": all_entities, "active_entity_ids": active_ids, "supporting_entity_ids": supporting_ids, "unreferenced_entity_ids": [e["id"] for e in all_entities if e["id"] not in compiled_ids], "retention": copy.deepcopy(plan.get("retention_rules", [])), "relationships": copy.deepcopy(bible.get("relationships", [])), "prohibited_drift": copy.deepcopy(bible.get("prohibited_drift", []))},
            "setting_and_time": {"scene_intent": copy.deepcopy(plan["scene_intent"]), **{k: copy.deepcopy(bible.get(k, "UNKNOWN")) for k in ("project_id", "scene_id", "revision", "scope", "geography", "time_of_day", "lighting", "visual_style", "camera_language", "continuity_rules", "audio_identity")}},
            "action_sequence": {"shot_id": shot["id"], "purpose": shot["purpose"], "actions": shot["action_primitives"], "motion_primitives": copy.deepcopy(shot.get("motion_primitives", [])), "interactions": shot_contacts, "state_changes": copy.deepcopy(shot.get("state_changes", []))}, "performance": copy.deepcopy(shot.get("performance", [])),
            "camera": shot["camera"], "lighting_and_style": {"scene": bible.get("visual_style", "UNKNOWN"), "camera_language": bible.get("camera_language", "UNKNOWN"), "lighting": bible.get("lighting", "UNKNOWN")},
            "audio_or_sync": {"identity": copy.deepcopy(bible.get("audio_identity", {})), "dialogue": [x for x in compiled_dialogue if x["shot_id"] == shot["id"]], "audio": [x for x in plan.get("audio_timeline", []) if x["shot_id"] == shot["id"]]},
            "continuity": {"initial_state_ref": bible.get("initial_state_ref"), "initial_state": copy.deepcopy(bible.get("initial_state", {})), "relationships": copy.deepcopy(bible.get("relationships", [])), "start": shot["start_state_ref"], "start_delta": copy.deepcopy(shot.get("start_state_delta", {})), "end": report["end_states"][shot["id"]], "end_delta": copy.deepcopy(shot.get("end_state_delta", {})), "changes": copy.deepcopy(shot.get("state_changes", []))},
            "constraints": {"hard": plan["scene_intent"]["hard_constraints"], "global": copy.deepcopy(plan.get("constraints", [])), "shot": shot.get("constraints", []), "prohibited_drift": copy.deepcopy(bible.get("prohibited_drift", []))},
            "references": {"assets": scene_reference_assets, "scene_reference_ids": scene_reference_ids, "shot_reference_ids": shot_reference_ids, "all_reference_ids": all_reference_ids, "retention_rules": copy.deepcopy(plan.get("retention_rules", []))}}
        canonical_gate = validate_canonical_state({
            "continuity": sections["continuity"],
            "action_sequence": sections["action_sequence"],
            "camera": sections["camera"],
            "setting_and_time": sections["setting_and_time"],
            "dialogue": sections["audio_or_sync"]["dialogue"],
        })
        negative_selection = select_negative_constraints({
            "subject_and_identity": sections["subject_and_identity"],
            "setting_and_time": sections["setting_and_time"],
            "action_sequence": sections["action_sequence"],
            "camera": sections["camera"],
            "audio_or_sync": sections["audio_or_sync"],
            "continuity": sections["continuity"],
            "constraints": sections["constraints"],
            "negative_constraints": copy.deepcopy(shot.get("negative_constraints", [])),
            "negative_constraint_families": copy.deepcopy(shot.get("negative_constraint_families", [])),
        })
        sections["constraints"]["negative_selection"] = negative_selection
        omissions = []
        view = {"schema_version": 1, "shot_id": shot["id"], "canonical_revision": f"{plan['scene_intent']['scene_id']}_rev{plan['revision']}", "profile_reference": profile["id"] if profile else None, "sections": sections,
                "mappings": [{"canonical_section": k, "compiled_representation": f"positive_prompt.{k}", "status": "PROPOSED"} for k in SECTIONS], "omissions": omissions,
                "canonical_coverage": {"scene_entity_ids": [e["id"] for e in all_entities], "compiled_entity_ids": [e["id"] for e in all_entities], "scene_reference_ids": scene_reference_ids, "compiled_reference_ids": all_reference_ids, "intent_fields": sorted(plan["scene_intent"]), "scene_bible_fields": sorted(bible), "shot_fields": sorted(shot)},
                "canonical_contradiction_gate": canonical_gate,
                "presentation": {"subject_definitions": sections["subject_and_identity"], "environment_definitions": sections["setting_and_time"], "summary": shot["purpose"], "retention_analysis": plan.get("retention_rules", []), "detailed_description": sections["action_sequence"], "global_physical_constraints": plan.get("constraints", []), "cinematography": sections["camera"], "overall_soundscape": sections["audio_or_sync"], "negative_constraints": negative_selection["selected"], "negative_constraint_selection": negative_selection}}
        view["compiled_view"] = {"profile_reference": view["profile_reference"], "positive_prompt": sections, "text": "\n".join(f"{k}: {canonical(v)}" for k, v in sections.items()), "compiled_omissions": omissions, "deliberate_changes": [], "unresolved": []}
        if profile:
            view["compatibility"] = negotiate(shot, profile)
            view["compiled_view"]["unresolved"] = view["compatibility"]["gaps"]
            if view["compatibility"]["status"] != "SUPPORTED":
                omissions.extend({"path": "capability", "reason": gap, "status": view["compatibility"]["status"], "required": True} for gap in view["compatibility"]["gaps"])
        outputs.append(view)
    statuses = [item.get("compatibility", {}).get("status", "SUPPORTED") for item in outputs]
    return {"schema_version": 1, "plan_hash": digest(plan), "execution_mode": "PLAN_ONLY",
            "status": "BLOCKED" if "BLOCKED" in statuses else "DEGRADED" if "DEGRADED" in statuses else "PASS", "prompts": outputs}


def negotiate(shot, profile, now=None):
    require(isinstance(shot, dict), "shot must be an object")
    require(isinstance(profile, dict), "profile must be an object")
    require(isinstance(profile.get("id"), str) and profile["id"], "Profile id is required")
    require(type(profile.get("schema_version")) is int and profile["schema_version"] == 1, "Unsupported profile schema")
    for field in ("provider", "runtime", "runtime_version", "model", "integration_version"):
        require(isinstance(profile.get(field), str) and profile[field], f"Profile {field} is required")
    require(number(shot.get("duration_s"), True), "Shot duration must be finite and positive")
    now = now or datetime.now(timezone.utc)
    require(isinstance(now, datetime) and now.tzinfo is not None and now.utcoffset() is not None, "Negotiation time requires timezone")
    gaps = []
    require(profile.get("status") in ("CONFIRMED", "PROPOSED", "INFERRED", "UNKNOWN", "EXPIRED", "UNSUPPORTED"), "Invalid profile status")
    if profile.get("status") != "CONFIRMED":
        gaps.append("Profile is not confirmed for execution")
    require(type(profile.get("profile_revision")) is int and profile["profile_revision"] > 0, "Invalid profile_revision")
    evidence_refs = profile.get("evidence_refs", [])
    string_list(evidence_refs, "Profile evidence_refs", allow_empty=False)
    validity = profile.get("validity", {})
    require(isinstance(validity, dict), "Profile validity must be an object")
    try:
        raw_expiry = validity.get("expires_at")
        require(isinstance(raw_expiry, str), "Profile has no valid expiry")
        expiry = datetime.fromisoformat(raw_expiry.replace("Z", "+00:00"))
        require(expiry.tzinfo is not None, "Profile expiry requires timezone")
        if expiry <= now:
            gaps.append("Profile evidence expired")
    except (ContractError, KeyError, TypeError, ValueError, OverflowError):
        gaps.append("Profile has no valid expiry")
    supports = profile.get("supports", {})
    require(isinstance(supports, dict), "Profile supports must be an object")
    modes = supports.get("modes", [])
    string_list(modes, "Profile supports.modes", allow_empty=False)
    for field in ("inputs", "outputs"):
        string_list(supports.get(field), f"Profile supports.{field}", allow_empty=False)
    for field in ("audio", "camera_controls", "identity_conditioning"):
        require(field in supports and supports[field] not in (None, ""), f"Profile supports.{field} is required")
    mode = shot.get("generation_mode", "T2V")
    require(isinstance(mode, str) and mode, "Shot generation_mode must be a nonempty string")
    if mode not in modes:
        gaps.append(f"Unsupported mode: {mode}")
    mode_feature = {"T2V": "text_to_video", "I2V": "image_to_video", "FLF2V": "first_last_frame", "TI2V": "text_image_to_video", "R2V": "reference_conditioning"}.get(mode, mode)
    requirements = string_list(shot.get("capability_requirements", []), "Shot capability_requirements")
    if shot.get("references"):
        require(isinstance(shot.get("references"), list), "Shot references must be an array")
        if "reference_conditioning" not in requirements:
            requirements = requirements + ["reference_conditioning"]
    degradable_requirements = string_list(shot.get("degradable_capability_requirements", []), "Shot degradable_capability_requirements")
    require(set(degradable_requirements) <= set(requirements), "Degradable capability must also be a declared capability requirement")
    evidence = profile.get("feature_evidence", {})
    require(isinstance(evidence, dict), "Profile feature_evidence must be an object")
    allowed_evidence_statuses = ("CONFIRMED", "PARTIAL", "INFERRED", "PROPOSED", "UNKNOWN", "EXPIRED", "UNSUPPORTED")
    for feature, record in evidence.items():
        require(isinstance(feature, str) and feature, "Profile feature names must be nonempty strings")
        require(isinstance(record, dict), f"Feature evidence must be an object: {feature}")
        require(record.get("status") in allowed_evidence_statuses, f"Invalid feature evidence status: {feature}")
        for field in ("source_ref", "probe_ref", "scope", "checked_at"):
            if field in record and record[field] is not None:
                require(isinstance(record[field], str) and record[field], f"Invalid feature evidence {field}: {feature}")
        if record["status"] != "UNKNOWN":
            require(bool(record.get("source_ref") or record.get("probe_ref")), f"Feature evidence needs a source or probe: {feature}")
    degraded_gaps = []
    for feature in sorted(set(requirements + [mode_feature])):
        record = evidence.get(feature, {})
        if not isinstance(record, dict) or record.get("status") != "CONFIRMED" or not record.get("source_ref") or not record.get("probe_ref"):
            gap = f"Unconfirmed feature: {feature}"
            gaps.append(gap)
            if feature in degradable_requirements:
                degraded_gaps.append(gap)
        elif not isinstance(record.get("scope"), str) or not record["scope"] or not isinstance(record.get("checked_at"), str) or not record["checked_at"]:
            gap = f"Feature evidence lacks scope/date: {feature}"
            gaps.append(gap)
            if feature in degradable_requirements:
                degraded_gaps.append(gap)
        elif record["source_ref"] not in evidence_refs or record["probe_ref"] not in evidence_refs:
            gap = f"Feature evidence refs are not bound to profile evidence_refs: {feature}"
            gaps.append(gap)
            if feature in degradable_requirements:
                degraded_gaps.append(gap)
    limits = profile.get("limits", {})
    require(isinstance(limits, dict), "Profile limits must be an object")
    bounds = limits.get("duration_s", {})
    require(isinstance(bounds, dict), "Profile limits.duration_s must be an object")
    low, high = bounds.get("min"), bounds.get("max")
    if not number(low, True) or not number(high, True):
        gaps.append("Unknown duration envelope")
    elif not low <= shot["duration_s"] <= high:
        gaps.append(f"Duration {shot['duration_s']} outside [{low}, {high}]")
    bindings = shot.get("parameters", {})
    require(isinstance(bindings, dict), "Shot parameters must be an object")
    controls = profile.get("controls", [])
    string_list(controls, "Profile controls")
    frame_rule = limits.get("frame_count", {})
    require(isinstance(frame_rule, dict), "Profile limits.frame_count must be an object")
    if "frame_count" in bindings:
        frames = bindings["frame_count"]
        multiple, offset = frame_rule.get("multiple"), frame_rule.get("offset", 0)
        if type(frames) is not int or frames < 1 or type(multiple) is not int or multiple < 1 or type(offset) is not int or (frames-offset) % multiple:
            gaps.append("Invalid or unconfirmed frame-count rule")
    for k, v in bindings.items():
        if not isinstance(k, str) or not k:
            gaps.append("Parameter names must be nonempty strings")
            continue
        if k not in controls:
            gaps.append(f"Unsupported parameter: {k}")
        if not number(v):
            gaps.append(f"Non-numeric parameter: {k}")
        if k in ("width", "height", "fps", "frame_count") and not number(v, True):
            gaps.append(f"Parameter must be positive: {k}")
        if k in ("width", "height", "frame_count", "seed") and type(v) is not int:
            gaps.append(f"Parameter must be integer: {k}")
        if k == "seed" and number(v) and v < 0:
            gaps.append("Seed must be nonnegative")
        if k in ("width", "height"):
            resolution = limits.get("resolution", {})
            bound = resolution.get(k, {}) if isinstance(resolution, dict) else {}
            if not isinstance(bound, dict) or not all(number(bound.get(x), True) for x in ("min", "max")):
                gaps.append(f"Unknown resolution envelope: {k}")
            elif number(v) and not bound["min"] <= v <= bound["max"]:
                gaps.append(f"Resolution outside profile: {k}")
            multiple = bound.get("multiple") if isinstance(bound, dict) else None
            if multiple is not None and (type(multiple) is not int or multiple < 1 or not number(v) or v % multiple):
                gaps.append(f"Invalid resolution multiple: {k}")
        if k == "fps":
            allowed = limits.get("fps", [])
            if not isinstance(allowed, list) or v not in allowed:
                gaps.append("Unconfirmed FPS")
    if type(bindings.get("frame_count")) is int and number(bindings.get("fps"), True):
        if abs(bindings["frame_count"] / bindings["fps"] - shot["duration_s"]) > 1/bindings["fps"] + 1e-9:
            gaps.append("Frame count/FPS does not match duration within one frame")
    hard_gaps = [gap for gap in gaps if gap not in degraded_gaps]
    status = "BLOCKED" if hard_gaps else "DEGRADED" if degraded_gaps else "SUPPORTED"
    return {"status": status, "profile_reference": profile["id"], "gaps": gaps,
            "fallback": "Preserve intent; obtain explicit approval for the named degraded feature or use a confirmed profile" if status == "DEGRADED" else "Preserve intent; propose shorter segments, a confirmed profile or separate audio/sync; obtain approval for weakened requirements" if gaps else None}


def repair_scope(plan, changed_shot_ids):
    nodes = indexed(plan["shots"], "shots")
    require(bool(changed_shot_ids) and all(s in nodes for s in changed_shot_ids), "Repair requires existing changed shots")
    affected = set(changed_shot_ids)
    while True:
        more = {s for s in nodes if set(nodes[s].get("dependency_ids", [])) & affected} - affected
        if not more:
            break
        affected |= more
    return {"schema_version": 1, "source_plan_hash": digest(plan), "affected_shot_ids": [s for s in ordered(plan["shots"]) if s in affected],
            "preserved_shot_ids": sorted(set(nodes)-affected), "recheck": sorted({g for s in affected for g in nodes[s].get("acceptance_ids", [])}),
            "next_action": "Repair the earliest affected boundary in a new scene revision; revalidate descendants and preserve unaffected evidence", "weakened_requirements": []}
