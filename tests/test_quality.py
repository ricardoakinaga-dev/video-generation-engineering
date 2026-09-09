import copy
import json
import re
from datetime import datetime, timezone
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents/skills/video-generation-engineering"
sys.path.insert(0, str(SKILL / "scripts"))

from vge_core import ContractError, digest, file_hash
from vge_media import media_qa, run
from vge_quality import (
    AUDIO_LAYERS,
    CONTACT_PHASES,
    CONTINUITY_DIMENSIONS,
    SEMANTIC_DIMENSIONS,
    adapt_prompt,
    adapter_differential,
    analyze_prompt_density,
    build_repair_plan,
    maturity_report,
    profile_fingerprint,
    reanchor_decision,
    validate_audio_timeline,
    validate_causal_sequence,
    validate_contact_phases,
    validate_continuity_scorecard,
    validate_dialogue_contract,
    validate_editorial_acceptance,
    validate_feature_profile,
    validate_first_last_frame,
    validate_long_form_case,
    validate_object_ownership,
    validate_observation_contract,
    validate_semantic_observation,
    validate_repair_plan,
    validate_transition_contract,
    validate_vehicle_state,
)


QUALITY_ARTIFACT = ROOT / "verification/media/final/art_2898879072af4739b673efe71fafcc7e.mp4"
QUALITY_ARTIFACT_HASH = file_hash(QUALITY_ARTIFACT)
PROVENANCE_ROOT = Path(tempfile.mkdtemp(prefix="vge-quality-provenance-"))


def evidence(ref=None):
    ref = str(QUALITY_ARTIFACT) if ref is None else ref
    return [{"type": "FRAME", "ref": ref, "content_hash": QUALITY_ARTIFACT_HASH if ref == str(QUALITY_ARTIFACT) else digest(ref), "time_s": 0.5}]


def decision_evidence():
    return [{"ref": str(QUALITY_ARTIFACT), "content_hash": QUALITY_ARTIFACT_HASH}]


def quality_provenance(shot_id, artifact_id, media_ref=None, media_hash=None):
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", f"{shot_id}-{artifact_id}")
    media_ref = str(QUALITY_ARTIFACT) if media_ref is None else str(media_ref)
    media_hash = QUALITY_ARTIFACT_HASH if media_hash is None else media_hash
    shot_record = {"id": shot_id, "revision": 1, "acceptance_ids": ["QG-17"]}
    shot_ref = PROVENANCE_ROOT / f"{safe}-shot.json"
    shot_ref.write_text(json.dumps(shot_record, sort_keys=True), encoding="utf-8")
    attempt_id = f"attempt_{safe}"
    workflow_ref = PROVENANCE_ROOT / f"{safe}-workflow.json"
    workflow_ref.write_text("{}", encoding="utf-8")
    profile_snapshot = {"id": "profile-fixture", "profile_revision": 1}
    attempt_record = {"schema_version": 1, "id": attempt_id, "execution_plan_ref": "fixture-plan",
                      "shot_id": shot_id, "shot_contract_hash": digest(shot_record), "attempt_index": 1,
                      "status": "SUCCEEDED", "started_at": "2026-09-08T17:00:00+00:00",
                      "ended_at": "2026-09-08T17:00:01+00:00",
                      "profile": {**profile_snapshot, "revision": 1, "content_hash": digest(profile_snapshot)},
                      "model": {"id": "model-fixture", "version": "1", "asset_hash": QUALITY_ARTIFACT_HASH},
                      "runtime": {"provider": "fixture", "endpoint": "http://127.0.0.1:1", "version": "1",
                                  "node_inventory_hash": digest({}), "selected_device": "cuda:0",
                                  "resource_context_hash": digest([])},
                      "workflow": {"ref": str(workflow_ref), "queue_id": "queue-fixture",
                                   "content_hash": digest({}), "fingerprint": digest("fixture-workflow")},
                      "nodes": [{"id": "1", "type": "Fixture", "version": "1"}], "inputs": [],
                      "parameters": {"seed": 1}, "progress_ref": "events.jsonl", "unknown_fields": [],
                      "purpose": "GENERATION"}
    attempt_ref = PROVENANCE_ROOT / f"{safe}-attempt.json"
    attempt_ref.write_text(json.dumps(attempt_record, sort_keys=True), encoding="utf-8")
    artifact_record = {"schema_version": 1, "id": artifact_id, "shot_id": shot_id,
                       "execution_attempt_ref": attempt_id, "artifact_ref": media_ref,
                       "content_hash": media_hash, "generation_status": "GENERATED",
                       "media": {"kind": "video"}}
    artifact_ref = PROVENANCE_ROOT / f"{safe}-artifact.json"
    artifact_ref.write_text(json.dumps(artifact_record, sort_keys=True), encoding="utf-8")
    return {"attempt": {"id": attempt_id, "ref": str(attempt_ref), "content_hash": file_hash(attempt_ref)},
            "shot": {"id": shot_id, "ref": str(shot_ref), "content_hash": file_hash(shot_ref),
                     "contract_hash": digest(shot_record)},
                         "artifact": {"id": artifact_id, "record_ref": str(artifact_ref),
                         "record_content_hash": file_hash(artifact_ref), "media_ref": media_ref,
                         "media_content_hash": media_hash}}


def oracle(kind="FRAME", question="Does the observed frame satisfy the declared assertion?"):
    return {"kind": kind, "question": question, "version": "fixture-1"}


def observation(status="PASS"):
    checks = []
    for category in ("metadata", "visual", "temporal", "audio", "continuity", "editorial"):
        result = status
        item = {"id": "check_" + category, "category": category, "result": result,
                "oracle": oracle("METADATA" if category == "metadata" else "FRAME"),
                "confidence": "HIGH" if result == "PASS" else "MEDIUM", "evidence": evidence(), "limitations": []}
        if result != "PASS":
            item["reason"] = "Fixture observation is not accepted"
        checks.append(item)
    return {"schema_version": 1, "id": "obs_1", "shot_id": "shot_1", "artifact_id": "artifact_1",
            "artifact_ref": str(QUALITY_ARTIFACT), "observed_content_hash": QUALITY_ARTIFACT_HASH,
            "observed_at": datetime.now(timezone.utc).isoformat(), "procedure": "Bound fixture inspection",
            "checks": checks, "status": status, "limitations": ["Synthetic fixture"],
            "provenance": quality_provenance("shot_1", "artifact_1")}


def semantic_observation(status="PASS"):
    item = observation(status)
    categories = {
        "identity": "visual", "wardrobe": "visual", "object_retention": "visual",
        "environment": "visual", "lighting": "visual", "physics": "visual",
        "interaction": "visual", "camera": "visual", "performance": "visual",
        "dialogue": "audio", "lip_sync": "audio", "temporal_continuity": "temporal",
    }
    checks = []
    for dimension in SEMANTIC_DIMENSIONS:
        check = copy.deepcopy(item["checks"][0])
        check["id"] = "semantic_" + dimension
        check["category"] = categories[dimension]
        check["semantic_dimension"] = dimension
        checks.append(check)
    item["checks"] = checks
    return item


def editorial_acceptance(status="PASS"):
    checks = []
    for dimension in ("pacing", "acting", "camera", "emotion", "framing", "rhythm"):
        item = {"id": "editorial_" + dimension, "dimension": dimension, "category": "editorial",
                "result": status, "oracle": oracle("HUMAN", "Does the final cut satisfy the editorial criterion?"),
                "confidence": "HIGH" if status == "PASS" else "MEDIUM", "evidence": evidence(), "limitations": []}
        if status != "PASS":
            item["reason"] = "Editorial fixture is not accepted"
        checks.append(item)
    return {"schema_version": 1, "id": "editorial_1", "artifact_ref": str(QUALITY_ARTIFACT),
            "artifact_content_hash": QUALITY_ARTIFACT_HASH, "observed_at": datetime.now(timezone.utc).isoformat(),
            "procedure": "Independent editorial fixture review", "checks": checks, "status": status,
            "limitations": ["Human editorial fixture"]}


def scorecard(status="PASS"):
    dimensions = []
    for dimension in CONTINUITY_DIMENSIONS:
        result = status
        item = {"dimension": dimension, "result": result, "oracle": oracle(),
                "confidence": "HIGH" if result == "PASS" else "MEDIUM", "evidence": evidence(), "limitations": []}
        if result != "PASS":
            item["reason"] = "Fixture dimension is not fully observed"
        dimensions.append(item)
    return {"schema_version": 1, "id": "score_1", "shot_id": "shot_2", "artifact_id": "artifact_2",
            "artifact_ref": str(QUALITY_ARTIFACT), "observed_content_hash": QUALITY_ARTIFACT_HASH,
            "observed_at": datetime.now(timezone.utc).isoformat(), "dimensions": dimensions, "status": status,
            "provenance": quality_provenance("shot_2", "artifact_2")}


class QualityContractTests(unittest.TestCase):
    def test_observation_requires_exact_categories_and_hash(self):
        report = validate_observation_contract(observation())
        self.assertTrue(report["accepted"])
        forged = observation(); forged["observed_content_hash"] = digest("forged")
        artifact = {"id": "artifact_1", "artifact_ref": str(QUALITY_ARTIFACT), "content_hash": QUALITY_ARTIFACT_HASH}
        with self.assertRaisesRegex(ContractError, "hash"):
            validate_observation_contract(forged, artifact)
        missing = observation(); missing["checks"] = missing["checks"][:-1]
        with self.assertRaisesRegex(ContractError, "Missing observation categories"):
            validate_observation_contract(missing)

    def test_semantic_pass_requires_existing_artifact_bytes(self):
        forged = observation()
        forged["artifact_ref"] = "/tmp/vge-quality-artifact-that-does-not-exist.mp4"
        with self.assertRaisesRegex(ContractError, "existing artifact bytes"):
            validate_observation_contract(forged)
        with self.assertRaisesRegex(ContractError, "existing artifact bytes"):
            validate_semantic_observation(forged)

    def test_semantic_observation_requires_explicit_twelve_dimensions(self):
        item = semantic_observation()
        result = validate_semantic_observation(item)
        self.assertTrue(result["accepted"])
        missing = copy.deepcopy(item)
        missing["checks"] = [check for check in missing["checks"] if check["semantic_dimension"] != "identity"]
        with self.assertRaisesRegex(ContractError, "Missing semantic observation dimensions"):
            validate_semantic_observation(missing)
        duplicate = copy.deepcopy(item)
        duplicate["checks"][-1]["semantic_dimension"] = SEMANTIC_DIMENSIONS[0]
        with self.assertRaisesRegex(ContractError, "Duplicate semantic observation dimension"):
            validate_semantic_observation(duplicate)

    def test_long_form_pass_requires_semantic_observations(self):
        def write_json(path, value):
            path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True), encoding="utf-8")

        def file_ref(path):
            return {"ref": str(path), "content_hash": file_hash(path)}

        def build_case(factory, root):
            refs = {}
            for name in ("intent", "plan", "bible", "graph", "continuity", "evidence", "audio", "repair", "human"):
                path = root / f"{name}.json"
                write_json(path, {"id": name})
                refs[name] = str(path)

            attempts, artifacts, observations, shot_records = [], [], [], []
            for shot_id, artifact_id in (("shot_1", "artifact_1"), ("shot_2", "artifact_2")):
                provenance = quality_provenance(shot_id, artifact_id)
                attempts.append({"ref": provenance["attempt"]["ref"], "content_hash": provenance["attempt"]["content_hash"]})
                artifacts.append({"ref": provenance["artifact"]["record_ref"],
                                  "content_hash": provenance["artifact"]["record_content_hash"],
                                  "media_ref": str(QUALITY_ARTIFACT), "media_content_hash": QUALITY_ARTIFACT_HASH})
                record = factory()
                record.update(id=f"obs_{shot_id}", shot_id=shot_id, artifact_id=artifact_id,
                              provenance=quality_provenance(shot_id, artifact_id))
                path = root / f"{record['id']}.json"
                write_json(path, record)
                observations.append(file_ref(path))
                shot_records.append((record, provenance))

            transition = {
                "schema_version": 1,
                "id": "transition_1",
                "status": "PASS",
                "previous_artifact": {"artifact_id": "artifact_1"},
                "next_artifact": {"artifact_id": "artifact_2"},
                "previous_observation": json.loads((root / "obs_shot_1.json").read_text(encoding="utf-8")),
                "next_observation": json.loads((root / "obs_shot_2.json").read_text(encoding="utf-8")),
                "continuity_scorecard": scorecard(),
            }
            transition_path = root / "transition.json"
            write_json(transition_path, transition)
            assembly = {
                "schema_version": 1,
                "id": "assembly_1",
                "technical_acceptance": "PASS",
                "semantic_acceptance": "PASS",
                "editorial_acceptance": "PASS",
                "mechanical_status": "PASS",
                "shot_order": ["shot_1", "shot_2"],
                "segments": [
                    {"shot_id": "shot_1", "artifact_id": "artifact_1", "duration_s": 22.5, "fps": 24,
                     "resolution": {"width": 384, "height": 224}, "audio_source": "NONE", "transition": "CUT",
                     "source_attempt": {"id": shot_records[0][1]["attempt"]["id"]}, "repair_lineage": []},
                    {"shot_id": "shot_2", "artifact_id": "artifact_2", "duration_s": 22.5, "fps": 24,
                     "resolution": {"width": 384, "height": 224}, "audio_source": "NONE", "transition": "END",
                     "source_attempt": {"id": shot_records[1][1]["attempt"]["id"]}, "repair_lineage": []},
                ],
                "final_artifact_binding": {
                    "artifact_ref": str(QUALITY_ARTIFACT),
                    "content_hash": QUALITY_ARTIFACT_HASH,
                    "source_shots": [
                        {"shot_id": "shot_1", "artifact_id": "artifact_1", "content_hash": QUALITY_ARTIFACT_HASH},
                        {"shot_id": "shot_2", "artifact_id": "artifact_2", "content_hash": QUALITY_ARTIFACT_HASH},
                    ],
                },
            }
            assembly_path = root / "assembly.json"
            write_json(assembly_path, assembly)
            return {
                "schema_version": 1,
                "id": "LF-003",
                "target_duration_s": 45,
                "intent_ref": refs["intent"], "plan_ref": refs["plan"], "scene_bible_ref": refs["bible"],
                "shot_graph_ref": refs["graph"], "continuity_ref": refs["continuity"], "evidence_ref": refs["evidence"],
                "shot_ids": ["shot_1", "shot_2"], "audio_timeline_ref": refs["audio"],
                "repair_budget_ref": refs["repair"], "human_checkpoint_ref": refs["human"],
                "status": "PASS", "production_evidence_complete": True,
                "production_evidence": {
                    "attempts": attempts, "artifacts": artifacts, "observations": observations,
                    "transitions": [file_ref(transition_path)], "assembly": file_ref(assembly_path),
                },
            }

        with tempfile.TemporaryDirectory(prefix="vge-lf-semantic-contract-") as raw:
            root = Path(raw)
            valid = build_case(semantic_observation, root)
            self.assertEqual("PASS", validate_long_form_case(valid, base_dir=root)["status"])
            invalid = build_case(observation, root)
            with self.assertRaisesRegex(ContractError, "semantic_dimension"):
                validate_long_form_case(invalid, base_dir=root)

    def test_editorial_acceptance_is_separate_and_dimension_complete(self):
        result = validate_editorial_acceptance(editorial_acceptance())
        self.assertTrue(result["accepted"])
        missing = editorial_acceptance()
        missing["checks"] = missing["checks"][:-1]
        with self.assertRaisesRegex(ContractError, "Missing editorial acceptance dimensions"):
            validate_editorial_acceptance(missing)
        nonhuman = editorial_acceptance()
        nonhuman["checks"][0]["oracle"] = oracle("FRAME")
        with self.assertRaisesRegex(ContractError, "HUMAN oracle"):
            validate_editorial_acceptance(nonhuman)

    def test_unobserved_is_not_pass(self):
        item = observation("NOT_OBSERVED")
        for check in item["checks"]:
            check["evidence"] = []
            check["reason"] = "No frame or audio oracle was run"
        self.assertEqual("NOT_OBSERVED", validate_observation_contract(item)["status"])

    def test_continuity_scorecard_covers_all_dimensions(self):
        self.assertTrue(validate_continuity_scorecard(scorecard())["accepted"])
        partial = scorecard("PARTIAL")
        self.assertEqual("PARTIAL", validate_continuity_scorecard(partial)["status"])
        missing = scorecard(); missing["dimensions"] = missing["dimensions"][:-1]
        with self.assertRaisesRegex(ContractError, "Missing continuity dimensions"):
            validate_continuity_scorecard(missing)

    def test_transition_binds_state_and_scorecard(self):
        next_media = PROVENANCE_ROOT / "transition-next.mp4"
        shutil.copyfile(QUALITY_ARTIFACT, next_media)
        next_media_hash = file_hash(next_media)
        previous_observation = observation()
        next_observation = observation()
        next_observation.update(id="obs_2", shot_id="shot_2", artifact_id="artifact_2",
                                artifact_ref=str(next_media), observed_content_hash=next_media_hash,
                                provenance=quality_provenance("shot_2", "artifact_2", next_media, next_media_hash))
        for check in next_observation["checks"]:
            check["evidence"] = [{"type": "FRAME", "ref": str(next_media), "content_hash": next_media_hash, "time_s": 0.5}]
        next_scorecard = scorecard()
        next_scorecard.update(artifact_ref=str(next_media), observed_content_hash=next_media_hash,
                              provenance=quality_provenance("shot_2", "artifact_2", next_media, next_media_hash))
        contract = {"schema_version": 1, "id": "tr_1", "previous_shot_id": "shot_1", "next_shot_id": "shot_2",
                    "previous_artifact": {"shot_id": "shot_1", "artifact_id": "artifact_1", "artifact_ref": str(QUALITY_ARTIFACT), "content_hash": QUALITY_ARTIFACT_HASH},
                    "next_artifact": {"shot_id": "shot_2", "artifact_id": "artifact_2", "artifact_ref": str(next_media), "content_hash": next_media_hash},
                    "required_state_properties": ["object.door", "subject.position"],
                    "previous_end_state": {"object.door": "open", "subject.position": "left"},
                    "next_start_state": {"object.door": "open", "subject.position": "left"},
                    "continuity_scorecard": next_scorecard,
                    "previous_observation": previous_observation,
                    "next_observation": next_observation,
                    "status": "PASS"}
        self.assertTrue(validate_transition_contract(contract)["accepted"])
        same_artifact = copy.deepcopy(contract)
        same_artifact["next_artifact"]["artifact_ref"] = same_artifact["previous_artifact"]["artifact_ref"]
        same_artifact["next_artifact"]["content_hash"] = same_artifact["previous_artifact"]["content_hash"]
        with self.assertRaisesRegex(ContractError, "distinct previous and next artifact bytes"):
            validate_transition_contract(same_artifact)
        contract["previous_artifact"]["artifact_ref"] = "/tmp/vge-previous-transition-does-not-exist.mp4"
        with self.assertRaisesRegex(ContractError, "existing artifact bytes"):
            validate_transition_contract(contract)
        contract["previous_artifact"]["artifact_ref"] = str(QUALITY_ARTIFACT)
        contract["next_start_state"]["object.door"] = "closed"
        with self.assertRaisesRegex(ContractError, "state mismatch"):
            validate_transition_contract(contract)

    def test_transition_pass_requires_both_observations(self):
        next_media = PROVENANCE_ROOT / "transition-missing-observation-next.mp4"
        shutil.copyfile(QUALITY_ARTIFACT, next_media)
        next_media_hash = file_hash(next_media)
        next_scorecard = scorecard()
        next_scorecard.update(artifact_ref=str(next_media), observed_content_hash=next_media_hash,
                              provenance=quality_provenance("shot_2", "artifact_2", next_media, next_media_hash))
        contract = {"schema_version": 1, "id": "tr_missing_obs", "previous_shot_id": "shot_1", "next_shot_id": "shot_2",
                    "previous_artifact": {"shot_id": "shot_1", "artifact_id": "artifact_1", "artifact_ref": str(QUALITY_ARTIFACT), "content_hash": QUALITY_ARTIFACT_HASH},
                    "next_artifact": {"shot_id": "shot_2", "artifact_id": "artifact_2", "artifact_ref": str(next_media), "content_hash": next_media_hash},
                    "required_state_properties": ["object.door"],
                    "previous_end_state": {"object.door": "open"},
                    "next_start_state": {"object.door": "open"},
                    "continuity_scorecard": next_scorecard, "status": "PASS"}
        with self.assertRaisesRegex(ContractError, "both adjacent artifacts"):
            validate_transition_contract(contract)

    def test_reanchor_selects_smallest_owner_and_split_for_capability_gap(self):
        result = reanchor_decision({"failed_dimensions": ["identity"], "partial_dimensions": [], "unobserved_dimensions": [], "evidence_refs": decision_evidence(), "provenance": quality_provenance("shot_2", "artifact_2")}, "shot_2", ["shot_3"])
        self.assertEqual("RE_ANCHOR", result["action"]); self.assertEqual("reference_conditioning", result["repair_owner"])
        result = reanchor_decision({"failed_dimensions": [], "partial_dimensions": [], "unobserved_dimensions": ["identity"], "capability_status": "BLOCKED", "evidence_refs": decision_evidence(), "provenance": quality_provenance("shot_2", "artifact_2")}, "shot_2")
        self.assertEqual("SPLIT", result["action"])
        with self.assertRaisesRegex(ContractError, "existing artifact bytes"):
            reanchor_decision({"failed_dimensions": [], "partial_dimensions": [], "unobserved_dimensions": [], "observed_dimensions": ["identity"], "evidence_refs": [{"ref": "/tmp/vge-reanchor-evidence-does-not-exist.png", "content_hash": QUALITY_ARTIFACT_HASH}], "provenance": quality_provenance("shot_2", "artifact_2")}, "shot_2")
        with self.assertRaisesRegex(ContractError, "provenance"):
            reanchor_decision({"failed_dimensions": [], "partial_dimensions": [], "unobserved_dimensions": [], "observed_dimensions": ["identity"], "evidence_refs": decision_evidence()}, "shot_2")
        recursive = reanchor_decision({"failed_dimensions": [], "partial_dimensions": [], "unobserved_dimensions": [],
                                       "observed_dimensions": ["identity"], "anchor_kind": "accepted_last_frame",
                                       "generated_chain_depth": 2, "evidence_refs": decision_evidence(),
                                       "provenance": quality_provenance("shot_2", "artifact_recursive")}, "shot_2", ["shot_3"])
        self.assertEqual("RE_ANCHOR", recursive["action"])
        self.assertEqual("reference_conditioning", recursive["repair_owner"])
        self.assertEqual(["shot_2", "shot_3"], recursive["changed_shot_ids"])

    def test_first_last_frame_needs_actual_endpoint_checks(self):
        checks = []
        for check_id in ("endpoint_identity", "motion_path", "object_state", "artifact_delivery"):
            checks.append({"id": check_id, "category": "visual", "result": "PASS", "oracle": oracle("FRAME"), "confidence": "HIGH", "evidence": [{"type": "FRAME", "ref": str(QUALITY_ARTIFACT), "content_hash": QUALITY_ARTIFACT_HASH, "time_s": 0.5}], "limitations": []})
        record = {"schema_version": 1, "profile_id": "h3-r2v", "shot_id": "shot_flf", "capability_status": "CONFIRMED", "workflow_hash": digest("workflow"),
                  "inputs": {"first_frame": {"ref": str(QUALITY_ARTIFACT), "content_hash": QUALITY_ARTIFACT_HASH}, "last_frame": {"ref": str(QUALITY_ARTIFACT), "content_hash": QUALITY_ARTIFACT_HASH}},
                  "artifact_ref": str(QUALITY_ARTIFACT), "artifact_content_hash": QUALITY_ARTIFACT_HASH, "provenance": quality_provenance("shot_flf", "artifact_flf"),
                  "checks": checks}
        self.assertTrue(validate_first_last_frame(record)["accepted"])
        first_only = copy.deepcopy(record)
        first_only["mode"] = "FIRST_ONLY"
        first_only["inputs"].pop("last_frame")
        self.assertTrue(validate_first_last_frame(first_only)["accepted"])
        last_only = copy.deepcopy(record)
        last_only["mode"] = "LAST_ONLY"
        last_only["inputs"].pop("first_frame")
        self.assertTrue(validate_first_last_frame(last_only)["accepted"])
        record["artifact_ref"] = "/tmp/vge-flf-artifact-does-not-exist.mp4"
        with self.assertRaisesRegex(ContractError, "existing artifact bytes"):
            validate_first_last_frame(record)
        record["artifact_ref"] = str(QUALITY_ARTIFACT)
        record["checks"][0]["evidence"][0]["ref"] = "/tmp/vge-flf-evidence-does-not-exist.png"
        with self.assertRaisesRegex(ContractError, "existing artifact bytes"):
            validate_first_last_frame(record)
        record["checks"][0]["evidence"][0]["ref"] = str(QUALITY_ARTIFACT)
        record["checks"][0]["oracle"] = oracle("METADATA", "Is the FLF node present?")
        for check in record["checks"]: check["oracle"] = oracle("METADATA", "Is the FLF node present?")
        with self.assertRaisesRegex(ContractError, "metadata alone"):
            validate_first_last_frame(record)

    def test_contact_dialogue_and_audio_contracts_separate_channels(self):
        phases = []
        for index, phase in enumerate(CONTACT_PHASES):
            phases.append({"phase": phase, "start_s": index, "end_s": index + .5, "observable_assertion": "fixture assertion"})
        contact = {"schema_version": 1, "id": "contact_1", "shot_id": "shot_contact", "actor": "a", "receiver": "b", "object_id": "door", "cause": "hand pushes", "expected_result": "door open", "phases": phases}
        self.assertEqual("PARTIAL", validate_contact_phases(contact)["status"])
        for phase in phases:
            phase.update(oracle=oracle("FRAME"), evidence=evidence())
        contact.update(artifact_ref=str(QUALITY_ARTIFACT), artifact_content_hash=QUALITY_ARTIFACT_HASH,
                       observed_at=datetime.now(timezone.utc).isoformat(), procedure="Bound contact fixture inspection",
                       provenance=quality_provenance("shot_contact", "artifact_contact"))
        self.assertEqual("PASS", validate_contact_phases(contact)["status"])
        alias_contact = copy.deepcopy(contact)
        alias_contact.pop("actor")
        alias_contact.pop("receiver")
        alias_contact.pop("object_id")
        alias_contact.pop("cause")
        alias_contact.pop("expected_result")
        alias_contact.update(subject="a", target="b", effector="door", interaction_cause="hand pushes", success_criterion="door open")
        self.assertEqual("PASS", validate_contact_phases(alias_contact)["status"])
        saved_contact_provenance = contact.pop("provenance")
        with self.assertRaisesRegex(ContractError, "contact.provenance"):
            validate_contact_phases(contact)
        contact["provenance"] = saved_contact_provenance
        channels = {channel: {"status": "PASS", "oracle": oracle("AUDIO" if channel in ("voice", "mix") else "FRAME"), "evidence": evidence()} for channel in ("semantics", "voice", "performance", "lip_sync", "mix")}
        channels["voice"]["audio_ref"] = "voice.wav"
        dialogue = {"schema_version": 1, "artifact_ref": str(QUALITY_ARTIFACT), "artifact_content_hash": QUALITY_ARTIFACT_HASH, "provenance": quality_provenance("shot_1", "artifact_dialogue"), "lines": [{"id": "line_1", "shot_id": "shot_1", "speaker": "a", "listener": "b", "text": "Ready.", "start_s": 1, "end_s": 2, "intention": "warn", "delivery": "quiet", "emotion": "focused", "gaze": "listener", "pause_policy": "none", "overlap_policy": "none", "visible_speech": True, "channels": channels}]}
        self.assertEqual("PASS", validate_dialogue_contract(dialogue)["status"])
        saved_dialogue_provenance = dialogue.pop("provenance")
        with self.assertRaisesRegex(ContractError, "dialogue.provenance"):
            validate_dialogue_contract(dialogue)
        dialogue["provenance"] = saved_dialogue_provenance
        channels["semantics"]["status"] = "FAIL"
        channels["semantics"]["reason"] = "Forced semantic rejection"
        self.assertEqual("FAIL", validate_dialogue_contract(dialogue)["status"])
        channels["semantics"]["status"] = "PASS"
        channels["semantics"]["evidence"][0]["ref"] = "/tmp/vge-dialogue-evidence-does-not-exist.wav"
        with self.assertRaisesRegex(ContractError, "existing artifact bytes"):
            validate_dialogue_contract(dialogue)
        channels["semantics"]["evidence"][0]["ref"] = str(QUALITY_ARTIFACT)
        dialogue["artifact_ref"] = "/tmp/vge-dialogue-artifact-does-not-exist.mp4"
        with self.assertRaisesRegex(ContractError, "existing artifact bytes"):
            validate_dialogue_contract(dialogue)
        dialogue["artifact_ref"] = str(QUALITY_ARTIFACT)
        events = [{"id": "a_" + layer, "layer": layer, "start_s": 1, "end_s": 2,
                   "cause": "fixture", "source": layer + ".wav", "priority": "HIGH",
                   "mix_role": "DIEGETIC" if layer != "silence" else "NONE",
                   "oracle": oracle("AUDIO"), "evidence": evidence()} for layer in AUDIO_LAYERS]
        timeline = {"events": events, "required_layers": [item["layer"] for item in events],
                    "not_applicable_layers": [], "shot_id": "shot_audio", "artifact_ref": str(QUALITY_ARTIFACT),
                    "artifact_content_hash": QUALITY_ARTIFACT_HASH, "observed_at": datetime.now(timezone.utc).isoformat(),
                    "procedure": "Bound audio timeline fixture inspection", "provenance": quality_provenance("shot_audio", "artifact_audio")}
        self.assertEqual("PASS", validate_audio_timeline(timeline)["status"])
        saved_audio_provenance = timeline.pop("provenance")
        with self.assertRaisesRegex(ContractError, "audio_timeline.provenance"):
            validate_audio_timeline(timeline)
        timeline["provenance"] = saved_audio_provenance
        events[0]["evidence"][0]["ref"] = "/tmp/vge-audio-evidence-does-not-exist.wav"
        with self.assertRaisesRegex(ContractError, "existing artifact bytes"):
            validate_audio_timeline(timeline)
        self.assertEqual("PARTIAL", validate_audio_timeline([events[0]])["status"])
        self.assertEqual("foley", validate_audio_timeline([{"id": "legacy_effect", "layer": "effects",
                         "start_s": 1, "end_s": 2, "cause": "fixture", "source": "effects.wav"}])["layers"][0])

    def test_prompt_adapter_is_loss_explicit_and_differential(self):
        sections = {"identity": {"subject": "courier"}, "motion": {"action": "walk"}, "audio": {"dialogue": "Ready"}}
        self.assertEqual("PASS", adapt_prompt(sections, {"id": "fixture", "preserve_sections": list(sections)})["status"])
        degraded = adapt_prompt(sections, {"id": "small", "unsupported_sections": ["audio"]})
        self.assertEqual("DEGRADED", degraded["status"]); self.assertEqual(["audio"], degraded["omissions"])
        with self.assertRaisesRegex(ContractError, "truncate"):
            adapt_prompt(sections, {"id": "tiny", "max_words": 1})
        diff = adapter_differential(sections, [{"id": "fixture"}, {"id": "small", "unsupported_sections": ["audio"]}])
        self.assertEqual("DEGRADED", diff["status"])
        self.assertTrue(analyze_prompt_density({"constraints": "not open and static"})["contradictions"])

    def test_profile_repair_long_form_and_maturity(self):
        profile = {"schema_version": 1, "id": "p", "profile_revision": 1, "provider": "fixture", "runtime": "local", "runtime_version": "1", "integration_version": "1", "model": "m", "model_asset_hash": digest("model"), "node_inventory_hash": digest("nodes"), "workflow_hash": digest("workflow"), "workflow_fingerprint": digest("workflow-fingerprint"), "selected_device": "cuda:0", "resource_context_hash": digest("resources"), "status": "CONFIRMED", "evidence_refs": [str(QUALITY_ARTIFACT)], "feature_evidence": {"text_to_video": {"status": "CONFIRMED", "source_ref": str(QUALITY_ARTIFACT), "source_content_hash": QUALITY_ARTIFACT_HASH, "probe_ref": str(QUALITY_ARTIFACT), "probe_content_hash": QUALITY_ARTIFACT_HASH, "scope": "fixture", "checked_at": "2099-01-01"}}, "validity": {"expires_at": "2099-01-01T00:00:00+00:00"}}
        probe_record = {"schema_version": 1, "probe_id": "fixture-profile-probe", "status": "PASS_RUNTIME_GENERATION",
                        "artifact_ref": str(QUALITY_ARTIFACT), "artifact_hash": QUALITY_ARTIFACT_HASH,
                        "runtime": {"version": "1", "node_inventory_hash": digest("nodes")},
                        "model": {"asset_hash": digest("model")}, "workflow_hash": digest("workflow")}
        probe_ref = PROVENANCE_ROOT / "fixture-profile-probe.json"
        probe_ref.write_text(json.dumps(probe_record, sort_keys=True), encoding="utf-8")
        profile["evidence_refs"] = [str(probe_ref)]
        profile["feature_evidence"]["text_to_video"].update(source_ref=str(probe_ref), source_content_hash=file_hash(probe_ref),
                                                              probe_ref=str(probe_ref), probe_content_hash=file_hash(probe_ref))
        profile["feature_evidence"]["text_to_video"].update(
            observed_parameters={"width": 64, "height": 64, "frame_count": 24, "fps": 24},
            selected_device="cuda:0", artifact_ref=str(QUALITY_ARTIFACT), artifact_content_hash=QUALITY_ARTIFACT_HASH,
            observation_ref=str(probe_ref), observation_content_hash=file_hash(probe_ref))
        profile["profile_fingerprint"] = profile_fingerprint(profile)
        self.assertEqual("CONFIRMED", validate_feature_profile(profile, "text_to_video")["status"])
        forged_profile = copy.deepcopy(profile); forged_profile["selected_device"] = "UNKNOWN"
        with self.assertRaisesRegex(ContractError, "cannot be UNKNOWN"):
            validate_feature_profile(forged_profile, "text_to_video")
        profile["runtime_version"] = "2"
        self.assertEqual("EXPIRED", validate_feature_profile(profile, "text_to_video", observed={"runtime_version": "1"})["status"])
        profile["runtime_version"] = "1"
        for field in ("workflow_fingerprint", "selected_device", "resource_context_hash"):
            observed = {field: "cuda:1" if field == "selected_device" else digest("changed-" + field)}
            self.assertEqual("EXPIRED", validate_feature_profile(profile, "text_to_video", observed=observed)["status"], field)
        partial = copy.deepcopy(profile)
        partial["runtime_version"] = "1"
        partial["feature_evidence"]["text_to_video"]["status"] = "PARTIAL"
        self.assertEqual("PARTIAL", validate_feature_profile(partial, "text_to_video")["status"])
        plan = {"revision": 1, "shots": [{"id": "a", "dependency_ids": []}, {"id": "b", "dependency_ids": ["a"]}, {"id": "c", "dependency_ids": []}]}
        repair = build_repair_plan(plan, ["a"], [{"id": "f", "shot_id": "a", "repair_owner": "continuity", "reason": "drift"}], {"max_regenerations": 2, "max_attempts": 3, "max_runtime_s": 60, "max_cost_usd": 0, "human_review_threshold": 1, "authorized": False})
        self.assertEqual("AWAITING_AUTHORIZATION", repair["status"]); self.assertEqual("PARTIAL", validate_repair_plan(repair)["status"])
        repair["status"] = "AUTHORIZED"
        repair["execution_ledger"] = {"schema_version": 1, "status": "COMPLETE", "attempts": 1, "regenerations": 1, "runtime_s": 10, "cost_usd": 0, "human_reviews": 0, "observed_at": datetime.now(timezone.utc).isoformat(), "completed_at": datetime.now(timezone.utc).isoformat(), "evidence": evidence(), "provenance": quality_provenance("a", "artifact_repair")}
        self.assertEqual("BLOCKED", validate_repair_plan(repair)["status"])
        repair["transition_revalidation"].update(status="PASS", validated_pairs=["a->b"], evidence_refs=["transition:a->b"])
        self.assertEqual("PASS", validate_repair_plan(repair)["status"])
        saved_repair_provenance = repair["execution_ledger"].pop("provenance")
        with self.assertRaisesRegex(ContractError, "provenance"):
            validate_repair_plan(repair)
        repair["execution_ledger"]["provenance"] = saved_repair_provenance
        case = {"schema_version": 1, "id": "LF-003", "target_duration_s": 45, "intent_ref": "intent", "plan_ref": "plan", "scene_bible_ref": "bible", "shot_graph_ref": "graph", "continuity_ref": "continuity", "evidence_ref": "evidence", "shot_ids": ["a", "b"], "audio_timeline_ref": "audio", "repair_budget_ref": "repair", "human_checkpoint_ref": "human", "status": "PARTIAL", "production_evidence_complete": False}
        self.assertEqual("PARTIAL", validate_long_form_case(case)["status"])
        placeholder_pass = copy.deepcopy(case)
        placeholder_pass.update(status="PASS", production_evidence_complete=True)
        with self.assertRaisesRegex(ContractError, "existing file"):
            validate_long_form_case(placeholder_pass)
        self.assertEqual(3, maturity_report({"structural": "PASS", "deterministic_tests": "PASS", "runtime_provenance": "PASS"})["level"])

    def test_causality_ownership_vehicle_and_dialogue_known_bad_cases(self):
        sequence = {"events": [
            {"id": "stimulus", "stage": "STIMULUS", "start_s": 0, "end_s": 1},
            {"id": "processing", "stage": "PROCESSING", "start_s": 1, "end_s": 2},
            {"id": "reaction", "stage": "REACTION", "start_s": 2, "end_s": 3},
            {"id": "response", "stage": "RESPONSE", "start_s": 3, "end_s": 4},
        ]}
        self.assertEqual("PASS", validate_causal_sequence(sequence)["status"])
        bad_sequence = copy.deepcopy(sequence)
        bad_sequence["events"][2]["start_s"] = 0.5
        with self.assertRaisesRegex(ContractError, "stimulus.*processing.*reaction"):
            validate_causal_sequence(bad_sequence)
        ownership = {"schema_version": 1, "id": "ownership_ok", "object_id": "envelope",
                     "owner_before": "a", "contact_state": "SHARED_CONTACT", "shared_contact": True,
                     "release": True, "owner_after": "b", "cause": "a hands envelope to b"}
        self.assertTrue(validate_object_ownership(ownership)["accepted"])
        ownership["contact_state"] = "PROXIMITY"
        ownership["shared_contact"] = False
        with self.assertRaisesRegex(ContractError, "proximity alone"):
            validate_object_ownership(ownership)
        vehicle = {"schema_version": 1, "id": "vehicle_ok", "vehicle_id": "van",
                   "applicable_fields": ["vehicle_position", "velocity_phase", "engine_state", "door_state", "road_contact", "occupants"],
                   "state": {"vehicle_position": "curb", "velocity_phase": "STATIONARY", "engine_state": "OFF",
                              "door_state": "CLOSED", "road_contact": True, "occupants": []}}
        self.assertTrue(validate_vehicle_state(vehicle)["accepted"])
        vehicle["state"]["velocity_phase"] = "MOVING"
        with self.assertRaisesRegex(ContractError, "active engine"):
            validate_vehicle_state(vehicle)
        geometry = copy.deepcopy(vehicle)
        geometry["state"]["velocity_phase"] = "STATIONARY"
        geometry["state"]["geometry"] = "van-v2"
        geometry["applicable_fields"].append("geometry")
        geometry["prior_state"] = {"geometry": "van-v1"}
        geometry["cause"] = "repair"
        with self.assertRaisesRegex(ContractError, "geometry_transition_ref"):
            validate_vehicle_state(geometry)
        geometry["geometry_transition_ref"] = "human-review-vehicle-v2"
        self.assertTrue(validate_vehicle_state(geometry)["accepted"])
        dialogue = {"schema_version": 1, "lines": [{"dialogue_id": "line_alias", "shot_id": "shot_1",
                    "speaker": "a", "listener": "b", "line": "Ready.", "intent": "warn",
                    "delivery": "quiet", "emotion": "focused", "start": 1, "end": 2,
                    "pause_before": 0.2, "pause_after": 0.2, "overlap_policy": "none", "gaze_target": "listener",
                    "pause_policy": "explicit",
                    "voice_reference": "voice-a", "lip_sync_mode": "UNKNOWN", "channels": {
                        channel: {"status": "UNKNOWN", "oracle": oracle("AUDIO" if channel in ("voice", "mix") else "FRAME"),
                                  "reason": "not run", "evidence": []}
                        for channel in ("semantics", "voice", "performance", "lip_sync", "mix")}}]}
        self.assertEqual("NOT_OBSERVED", validate_dialogue_contract(dialogue)["status"])
        dialogue["speaker_sequence"] = ["b"]
        with self.assertRaisesRegex(ContractError, "speaker sequence"):
            validate_dialogue_contract(dialogue)
        dialogue.pop("speaker_sequence")
        dialogue["lines"][0]["listener_mouthing"] = True
        with self.assertRaisesRegex(ContractError, "listener must not mouth"):
            validate_dialogue_contract(dialogue)

    def test_confirmed_profile_and_continue_need_evidence(self):
        minimal = {"id": "minimal", "status": "CONFIRMED", "feature_evidence": {"text_to_video": {"status": "CONFIRMED"}}}
        with self.assertRaisesRegex(ContractError, "Confirmed profile"):
            validate_feature_profile(minimal, "text_to_video")
        with self.assertRaisesRegex(ContractError, "evidence_refs"):
            reanchor_decision({"failed_dimensions": [], "partial_dimensions": [], "unobserved_dimensions": [], "observed_dimensions": ["identity"]}, "shot_1")


class MediaQualityTests(unittest.TestCase):
    def test_media_qa_observes_real_fixture_and_corrupt_bytes(self):
        if not shutil.which("ffmpeg"):
            self.skipTest("ffmpeg unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); video = root / "fixture.mp4"
            run(["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i", "testsrc2=size=64x64:rate=24:duration=1", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(video)])
            report = media_qa(video, allow_black=True)
            self.assertIn(report["status"], ("PASS", "PARTIAL"))
            self.assertTrue(any(item["id"] == "decode_integrity" for item in report["checks"]))
            black = root / "black.mp4"
            run(["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i", "color=c=black:size=64x64:rate=24:duration=1", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(black)])
            self.assertEqual("FAIL", media_qa(black)["status"])
            bad = root / "bad.mp4"; bad.write_bytes(b"not a media file")
            self.assertEqual("FAIL", media_qa(bad)["status"])

    def test_media_qa_emits_granular_contract_checks(self):
        if not shutil.which("ffmpeg"):
            self.skipTest("ffmpeg unavailable")
        report = media_qa(QUALITY_ARTIFACT, expected_duration_s=5.1666667,
                          expected_fps=24, expected_resolution=[384, 224],
                          expected_frame_count=124, expected_codec="h264", expected_container="mp4")
        checks = {item["id"]: item for item in report["checks"]}
        for check_id in ("file_readable", "duration", "fps", "resolution", "frame_count", "codec",
                         "container", "audio_stream", "audio_duration", "audio_video_alignment",
                         "av_duration_mismatch", "decode_integrity", "black_frames", "freeze_frames", "artifact_hash"):
            self.assertIn(check_id, checks)
        self.assertEqual("PASS", report["status"])
        self.assertEqual(124, report["frame_count"])
        self.assertEqual("PASS", checks["audio_stream"]["result"])
        self.assertEqual("PASS", checks["av_duration_mismatch"]["result"])
        self.assertEqual("FAIL", media_qa(QUALITY_ARTIFACT, expected_fps=30)["status"])
        self.assertEqual("FAIL", media_qa(QUALITY_ARTIFACT, expected_frame_count=125)["status"])
        self.assertEqual("FAIL", media_qa(QUALITY_ARTIFACT, expected_resolution=[32, 32])["status"])
        self.assertEqual("FAIL", media_qa(QUALITY_ARTIFACT, expected_codec="vp9")["status"])
        self.assertEqual("FAIL", media_qa(QUALITY_ARTIFACT, expected_container="mkv")["status"])


if __name__ == "__main__":
    unittest.main()
