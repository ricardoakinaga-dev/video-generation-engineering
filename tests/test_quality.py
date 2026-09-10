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

from vge_core import ContractError, digest, file_hash, detect_canonical_contradictions, select_negative_constraints, validate_canonical_state
from vge_media import media_qa, run
from vge_capture import capture_evidence
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
    validate_cross_shot_comparison,
    validate_dialogue_contract,
    validate_editorial_acceptance,
    validate_feature_profile,
    validate_first_last_frame,
    prepare_first_last_frame_probe,
    validate_long_form_execution_envelope,
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


def audio_evidence(ref=None):
    ref = str(QUALITY_ARTIFACT) if ref is None else ref
    content_hash = QUALITY_ARTIFACT_HASH if ref == str(QUALITY_ARTIFACT) else digest(ref)
    return [{"type": "AUDIO", "ref": ref, "content_hash": content_hash, "time_s": 0.5}]


def decision_evidence():
    return [{"ref": str(QUALITY_ARTIFACT), "content_hash": QUALITY_ARTIFACT_HASH}]


def quality_provenance(shot_id, artifact_id, media_ref=None, media_hash=None,
                       runtime_provider="local_comfyui", runtime_endpoint="http://127.0.0.1:8188"):
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
                      "runtime": {"provider": runtime_provider, "endpoint": runtime_endpoint, "version": "1",
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
    history_ref = PROVENANCE_ROOT / f"{safe}-history.json"
    history_outputs = {"1": {"videos": [{"filename": Path(media_ref).name, "subfolder": "", "type": "output"}]}}
    history_ref.write_text(json.dumps({"status": "SUCCEEDED", "prompt_id": "queue-fixture",
                                       "history": {"status": {"completed": True, "status_str": "success"},
                                                    "outputs": history_outputs}}, sort_keys=True), encoding="utf-8")
    event_ref = PROVENANCE_ROOT / f"{safe}-events.jsonl"
    event_ref.write_text(json.dumps({"schema_version": 1, "event_id": "event-submitted",
                                     "attempt_id": attempt_id, "queue_id": "queue-fixture",
                                     "status": "SUBMITTED"}, sort_keys=True) + "\n" +
                         json.dumps({"schema_version": 1, "event_id": "event-collected",
                                     "attempt_id": attempt_id, "queue_id": "queue-fixture",
                                     "status": "COLLECTED", "history_content_hash": file_hash(history_ref),
                                     "artifact_ids": [artifact_id]}, sort_keys=True) + "\n", encoding="utf-8")
    attempt_record["collection"] = {
        "schema_version": 1, "status": "COLLECTED", "collector": "vge_runtime.collect",
        "prompt_id": "queue-fixture", "history_ref": str(history_ref),
        "history_content_hash": file_hash(history_ref), "history_output_hash": digest(history_outputs),
        "event_log_ref": str(event_ref), "event_log_content_hash": file_hash(event_ref),
        "output_entries": [{"artifact_id": artifact_id, "node_id": "1", "bucket": "videos",
                            "filename": Path(media_ref).name, "subfolder": "", "type": "output",
                            "content_hash": media_hash}],
        "artifacts": [{"id": artifact_id, "record_ref": str(artifact_ref),
                       "record_content_hash": file_hash(artifact_ref), "artifact_ref": media_ref,
                       "content_hash": media_hash}],
        "collected_at": "2026-09-08T17:00:02+00:00",
    }
    attempt_record["artifacts"] = copy.deepcopy(attempt_record["collection"]["artifacts"])
    attempt_ref.write_text(json.dumps(attempt_record, sort_keys=True), encoding="utf-8")
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
        kind = "FRAME"
        if dimension == "dialogue":
            kind = "AUDIO"
        elif dimension in ("lip_sync", "temporal_continuity"):
            kind = "MULTI_FRAME" if dimension == "lip_sync" else "SEQUENCE"
        check["oracle"] = oracle(kind)
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
            "procedure": "Independent editorial fixture review", "reviewer": {
                "id": "reviewer-fixture", "role": "editorial-reviewer",
                "authority": "fixture-review-scope", "attestation": "fixture-attested",
            }, "decision": status, "checks": checks, "status": status,
            "limitations": ["Human editorial fixture"]}


def scorecard(status="PASS"):
    dimensions = []
    for dimension in CONTINUITY_DIMENSIONS:
        result = status
        kind = "AUDIO" if dimension == "audio" else "SEQUENCE" if dimension == "temporal" else "HUMAN"
        item = {"dimension": dimension, "result": result, "oracle": oracle(kind),
                "confidence": "HIGH" if result == "PASS" else "MEDIUM", "evidence": evidence(), "limitations": []}
        if result != "PASS":
            item["reason"] = "Fixture dimension is not fully observed"
        dimensions.append(item)
    return {"schema_version": 1, "id": "score_1", "shot_id": "shot_2", "artifact_id": "artifact_2",
            "artifact_ref": str(QUALITY_ARTIFACT), "observed_content_hash": QUALITY_ARTIFACT_HASH,
            "observed_at": datetime.now(timezone.utc).isoformat(), "dimensions": dimensions, "status": status,
            "provenance": quality_provenance("shot_2", "artifact_2")}


def cross_shot_comparison(previous_ref=None, previous_hash=None, next_ref=None, next_hash=None, status="PASS"):
    previous_ref = str(QUALITY_ARTIFACT) if previous_ref is None else str(previous_ref)
    previous_hash = QUALITY_ARTIFACT_HASH if previous_hash is None else previous_hash
    next_ref = previous_ref if next_ref is None else str(next_ref)
    next_hash = previous_hash if next_hash is None else next_hash
    dimensions = []
    for dimension in CONTINUITY_DIMENSIONS:
        kind = "HUMAN" if dimension == "audio" else "TRANSITION"
        item = {"dimension": dimension, "result": status, "oracle": oracle(kind),
                "confidence": "HIGH" if status == "PASS" else "MEDIUM", "limitations": []}
        if status == "PASS":
            item["evidence"] = [
                {"type": "FRAME", "ref": previous_ref, "content_hash": previous_hash, "time_s": 0.5},
                {"type": "FRAME", "ref": next_ref, "content_hash": next_hash, "time_s": 0.5},
            ]
        else:
            item["reason"] = "No side-by-side cross-shot oracle was run in this fixture"
            item["evidence"] = []
        dimensions.append(item)
    return {
        "schema_version": 1,
        "id": "comparison_1",
        "previous_shot_id": "shot_1",
        "next_shot_id": "shot_2",
        "previous_artifact": {"shot_id": "shot_1", "artifact_id": "artifact_1",
                               "artifact_ref": previous_ref, "content_hash": previous_hash},
        "next_artifact": {"shot_id": "shot_2", "artifact_id": "artifact_2",
                           "artifact_ref": next_ref, "content_hash": next_hash},
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "procedure": "Independent side-by-side adjacent-shot comparison fixture",
        "dimensions": dimensions,
        "status": status if status != "NOT_OBSERVED" else "NOT_OBSERVED",
        "limitations": ["Fixture comparison; not a visual claim about production media."],
    }


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
        unrelated = copy.deepcopy(item)
        unrelated_ref = ROOT / "verification/media/art_c1c52b6492b04dc1847edbe3d028bab7.mp4"
        unrelated["checks"][0]["evidence"][0].update(ref=str(unrelated_ref), content_hash=file_hash(unrelated_ref))
        with self.assertRaisesRegex(ContractError, "not bound to the observed artifact"):
            validate_semantic_observation(unrelated)

    def test_long_form_pass_requires_semantic_observations(self):
        def write_json(path, value):
            path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True), encoding="utf-8")

        def file_ref(path):
            return {"ref": str(path), "content_hash": file_hash(path)}

        def build_case(factory, root):
            refs = {}
            canonical_ref_names = [
                ("intent_ref", "intent"), ("plan_ref", "plan"),
                ("scene_bible_ref", "bible"), ("shot_graph_ref", "graph"),
                ("continuity_ref", "continuity"), ("evidence_ref", "evidence"),
                ("audio_timeline_ref", "audio"), ("repair_budget_ref", "repair"),
                ("human_checkpoint_ref", "human"),
            ]
            for name in ("intent", "plan", "bible", "graph", "continuity", "evidence", "audio", "repair", "human"):
                path = root / f"{name}.json"
                record = {"schema_version": 1, "id": name, "revision": 1,
                          "case_id": "LF-003", "scene_id": "scene-fixture"}
                if name == "plan":
                    record["shots"] = [{"id": "shot_1"}, {"id": "shot_2"}]
                if name in ("graph", "continuity"):
                    record["shot_ids"] = ["shot_1", "shot_2"]
                write_json(path, record)
                refs[name] = file_ref(path)

            attempts, artifacts, observations, shot_records = [], [], [], []
            for shot_id, artifact_id in (("shot_1", "artifact_1"), ("shot_2", "artifact_2")):
                media_path = QUALITY_ARTIFACT
                if shot_id == "shot_2":
                    media_path = root / "shot_2.mp4"
                    shutil.copyfile(ROOT / "verification/media/art_c1c52b6492b04dc1847edbe3d028bab7.mp4", media_path)
                media_hash = file_hash(media_path)
                record = factory()
                provenance = quality_provenance(shot_id, artifact_id, media_path, media_hash,
                                                runtime_provider="local_comfyui", runtime_endpoint="http://127.0.0.1:8188")
                attempts.append({"ref": provenance["attempt"]["ref"], "content_hash": provenance["attempt"]["content_hash"]})
                artifacts.append({"ref": provenance["artifact"]["record_ref"],
                                  "content_hash": provenance["artifact"]["record_content_hash"],
                                  "media_ref": str(media_path), "media_content_hash": media_hash})
                record.update(id=f"obs_{shot_id}", shot_id=shot_id, artifact_id=artifact_id,
                              artifact_ref=str(media_path), observed_content_hash=media_hash,
                              provenance=provenance)
                for check in record["checks"]:
                    for item in check.get("evidence", []):
                        item["ref"] = str(media_path)
                        item["content_hash"] = media_hash
                path = root / f"{record['id']}.json"
                write_json(path, record)
                observations.append(file_ref(path))
                shot_records.append((record, provenance))

            next_scorecard = scorecard()
            next_media = root / "shot_2.mp4"
            next_media_hash = file_hash(next_media)
            next_scorecard.update(artifact_ref=str(next_media), observed_content_hash=next_media_hash,
                                  provenance=quality_provenance("shot_2", "artifact_2", next_media, next_media_hash,
                                                               runtime_provider="local_comfyui", runtime_endpoint="http://127.0.0.1:8188"))
            for dimension in next_scorecard["dimensions"]:
                for item in dimension.get("evidence", []):
                    item["ref"] = str(next_media)
                    item["content_hash"] = next_media_hash
            transition = {
                "schema_version": 1,
                "id": "transition_1",
                "status": "PASS",
                "previous_shot_id": "shot_1", "next_shot_id": "shot_2",
                "previous_artifact": {"shot_id": "shot_1", "artifact_id": "artifact_1",
                                       "artifact_ref": str(QUALITY_ARTIFACT), "content_hash": QUALITY_ARTIFACT_HASH},
                "next_artifact": {"shot_id": "shot_2", "artifact_id": "artifact_2",
                                   "artifact_ref": str(next_media), "content_hash": next_media_hash},
                "required_state_properties": ["object.door", "subject.position"],
                "previous_end_state": {"object.door": "open", "subject.position": "left"},
                "next_start_state": {"object.door": "open", "subject.position": "left"},
                "previous_observation": json.loads((root / "obs_shot_1.json").read_text(encoding="utf-8")),
                "next_observation": json.loads((root / "obs_shot_2.json").read_text(encoding="utf-8")),
                "continuity_scorecard": next_scorecard,
                "cross_shot_comparison": cross_shot_comparison(
                    str(QUALITY_ARTIFACT), QUALITY_ARTIFACT_HASH, str(next_media), next_media_hash),
            }
            transition_path = root / "transition.json"
            write_json(transition_path, transition)
            final_media_qa_path = root / "final-media-qa.json"
            final_media_qa = media_qa(QUALITY_ARTIFACT)
            final_media_qa["id"] = "final_media_qa_1"
            write_json(final_media_qa_path, final_media_qa)
            final_semantic = semantic_observation()
            final_semantic.update(id="final_semantic_1", shot_id="assembly_1", artifact_id="assembly_1",
                                  artifact_ref=str(QUALITY_ARTIFACT), observed_content_hash=QUALITY_ARTIFACT_HASH,
                                  provenance=quality_provenance("assembly_1", "assembly_1"))
            final_semantic_path = root / "final-semantic.json"
            write_json(final_semantic_path, final_semantic)
            editorial_path = root / "editorial.json"
            write_json(editorial_path, editorial_acceptance())
            assembly = {
                "schema_version": 1,
                "id": "assembly_1",
                "fps": 24, "target_duration_s": 45,
                "technical_acceptance": "PASS",
                "semantic_acceptance": "PASS",
                "editorial_acceptance": "PASS",
                "mechanical_status": "PASS",
                "shot_order": ["shot_1", "shot_2"],
                "segments": [
                    {"shot_id": "shot_1", "artifact": {"id": "artifact_1", "artifact_ref": str(QUALITY_ARTIFACT), "content_hash": QUALITY_ARTIFACT_HASH}, "duration_s": 22.5, "fps": 24,
                     "resolution": {"width": 384, "height": 224}, "audio_source": "NONE", "transition": "CUT",
                     "source_attempt": {"id": shot_records[0][1]["attempt"]["id"]}, "repair_lineage": []},
                    {"shot_id": "shot_2", "artifact": {"id": "artifact_2", "artifact_ref": str(next_media), "content_hash": next_media_hash}, "duration_s": 22.5, "fps": 24,
                     "resolution": {"width": 384, "height": 224}, "audio_source": "NONE", "transition": "END",
                     "source_attempt": {"id": shot_records[1][1]["attempt"]["id"]}, "repair_lineage": []},
                ],
                "final_artifact_binding": {
                    "artifact_ref": str(QUALITY_ARTIFACT),
                    "content_hash": QUALITY_ARTIFACT_HASH,
                    "source_shots": [
                        {"shot_id": "shot_1", "artifact_id": "artifact_1", "content_hash": QUALITY_ARTIFACT_HASH},
                        {"shot_id": "shot_2", "artifact_id": "artifact_2", "content_hash": next_media_hash},
                    ],
                },
                "semantic_observation": file_ref(final_semantic_path),
            }
            assembly_path = root / "assembly.json"
            write_json(assembly_path, assembly)
            case = {
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
                    "final_media_qa": file_ref(final_media_qa_path),
                    "final_semantic_observation": file_ref(final_semantic_path),
                    "editorial_acceptance": file_ref(editorial_path),
                },
            }
            records = {
                field: {"id": json.loads(Path(refs[name]["ref"]).read_text(encoding="utf-8"))["id"],
                        "content_hash": refs[name]["content_hash"]}
                for field, name in canonical_ref_names
            }
            manifest = [{"field": field, "record_id": records[field]["id"],
                         "content_hash": records[field]["content_hash"]}
                        for field, _ in canonical_ref_names]
            bundle = {"case_id": "LF-003", "scene_id": "scene-fixture", "revision": 1,
                      "records": records}
            bundle["content_hash"] = digest({"case_id": bundle["case_id"],
                                              "scene_id": bundle["scene_id"],
                                              "revision": bundle["revision"],
                                              "records": manifest})
            case["canonical_bundle"] = bundle
            return case

        with tempfile.TemporaryDirectory(prefix="vge-lf-semantic-contract-") as raw:
            root = Path(raw)
            valid = build_case(semantic_observation, root)
            self.assertEqual("PASS", validate_long_form_case(valid, base_dir=root)["status"])

            canonical_ref_names = [
                ("intent_ref", "intent"), ("plan_ref", "plan"),
                ("scene_bible_ref", "bible"), ("shot_graph_ref", "graph"),
                ("continuity_ref", "continuity"), ("evidence_ref", "evidence"),
                ("audio_timeline_ref", "audio"), ("repair_budget_ref", "repair"),
                ("human_checkpoint_ref", "human"),
            ]

            def refresh_canonical_bundle(candidate):
                records = {}
                for field, _ in canonical_ref_names:
                    ref = candidate[field]
                    path = Path(ref["ref"])
                    record = json.loads(path.read_text(encoding="utf-8"))
                    ref["content_hash"] = file_hash(path)
                    records[field] = {"id": record["id"], "content_hash": ref["content_hash"]}
                candidate["canonical_bundle"]["records"] = records
                manifest = [{"field": field, "record_id": records[field]["id"],
                             "content_hash": records[field]["content_hash"]}
                            for field, _ in canonical_ref_names]
                bundle = candidate["canonical_bundle"]
                bundle["content_hash"] = digest({"case_id": bundle["case_id"],
                                                   "scene_id": bundle["scene_id"],
                                                   "revision": bundle["revision"],
                                                   "records": manifest})

            for field, record_key, mismatched_value, expected_error in (
                ("intent_ref", "case_id", "LF-OTHER", "record.case_id"),
                ("scene_bible_ref", "scene_id", "scene-other", "record.scene_id"),
                ("plan_ref", "revision", 2, "record.revision"),
            ):
                mismatched = build_case(semantic_observation, root)
                record_path = Path(mismatched[field]["ref"])
                record = json.loads(record_path.read_text(encoding="utf-8"))
                record[record_key] = mismatched_value
                write_json(record_path, record)
                refresh_canonical_bundle(mismatched)
                with self.assertRaisesRegex(ContractError, expected_error):
                    validate_long_form_case(mismatched, base_dir=root)

            bundle_mismatch = build_case(semantic_observation, root)
            bundle_mismatch["canonical_bundle"]["records"]["plan_ref"]["id"] = "wrong-plan"
            with self.assertRaisesRegex(ContractError, "does not match the referenced record"):
                validate_long_form_case(bundle_mismatch, base_dir=root)

            unsealed = build_case(semantic_observation, root)
            unsealed_attempt = Path(unsealed["production_evidence"]["attempts"][0]["ref"])
            unsealed_record = json.loads(unsealed_attempt.read_text(encoding="utf-8"))
            unsealed_record.pop("collection")
            unsealed_record.pop("artifacts", None)
            write_json(unsealed_attempt, unsealed_record)
            unsealed["production_evidence"]["attempts"][0]["content_hash"] = file_hash(unsealed_attempt)
            with self.assertRaisesRegex(ContractError, "collection"):
                validate_long_form_case(unsealed, base_dir=root)
            lineage_bad = build_case(semantic_observation, root)
            assembly_ref = Path(lineage_bad["production_evidence"]["assembly"]["ref"])
            assembly_record = json.loads(assembly_ref.read_text(encoding="utf-8"))
            assembly_record["segments"][1]["source_attempt"]["id"] = assembly_record["segments"][0]["source_attempt"]["id"]
            write_json(assembly_ref, assembly_record)
            lineage_bad["production_evidence"]["assembly"]["content_hash"] = file_hash(assembly_ref)
            with self.assertRaisesRegex(ContractError, "source attempt is not bound"):
                validate_long_form_case(lineage_bad, base_dir=root)
            fixture_case = build_case(semantic_observation, root)
            fixture_attempt = Path(fixture_case["production_evidence"]["attempts"][0]["ref"])
            fixture_record = json.loads(fixture_attempt.read_text(encoding="utf-8"))
            fixture_record["runtime"]["provider"] = "fixture"
            write_json(fixture_attempt, fixture_record)
            fixture_case["production_evidence"]["attempts"][0]["content_hash"] = file_hash(fixture_attempt)
            with self.assertRaisesRegex(ContractError, "fixture/synthetic"):
                validate_long_form_case(fixture_case, base_dir=root)
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

    def test_cross_shot_comparison_is_explicit_and_hash_bound(self):
        next_media = PROVENANCE_ROOT / "comparison-next.mp4"
        shutil.copyfile(QUALITY_ARTIFACT, next_media)
        next_media_hash = file_hash(next_media)
        observed = cross_shot_comparison(str(QUALITY_ARTIFACT), QUALITY_ARTIFACT_HASH,
                                         next_media, next_media_hash, "NOT_OBSERVED")
        result = validate_cross_shot_comparison(observed)
        self.assertEqual("NOT_OBSERVED", result["status"])
        self.assertFalse(result["accepted"])
        missing = copy.deepcopy(observed)
        missing["dimensions"] = missing["dimensions"][:-1]
        with self.assertRaisesRegex(ContractError, "Missing cross-shot comparison dimensions"):
            validate_cross_shot_comparison(missing)
        accepted = cross_shot_comparison(str(QUALITY_ARTIFACT), QUALITY_ARTIFACT_HASH,
                                         next_media, next_media_hash, "PASS")
        self.assertTrue(validate_cross_shot_comparison(accepted)["accepted"])
        forged = copy.deepcopy(accepted)
        forged["next_artifact"]["content_hash"] = digest("forged")
        with self.assertRaisesRegex(ContractError, "artifact bytes changed"):
            validate_cross_shot_comparison(forged)

    def test_transition_binds_state_and_scorecard(self):
        next_media = PROVENANCE_ROOT / "transition-next.mp4"
        shutil.copyfile(ROOT / "verification/media/art_c1c52b6492b04dc1847edbe3d028bab7.mp4", next_media)
        next_media_hash = file_hash(next_media)
        previous_observation = semantic_observation()
        next_observation = semantic_observation()
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
                    "cross_shot_comparison": cross_shot_comparison(
                        str(QUALITY_ARTIFACT), QUALITY_ARTIFACT_HASH, str(next_media), next_media_hash),
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
        shutil.copyfile(ROOT / "verification/media/art_c1c52b6492b04dc1847edbe3d028bab7.mp4", next_media)
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
                    "continuity_scorecard": next_scorecard,
                    "cross_shot_comparison": cross_shot_comparison(
                        str(QUALITY_ARTIFACT), QUALITY_ARTIFACT_HASH, str(next_media), next_media_hash),
                    "status": "PASS"}
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
            kind = "SEQUENCE" if check_id in ("motion_path", "object_state") else "METADATA" if check_id == "artifact_delivery" else "FRAME"
            checks.append({"id": check_id, "category": "visual", "result": "PASS", "oracle": oracle(kind), "confidence": "HIGH", "evidence": [{"type": "FRAME", "ref": str(QUALITY_ARTIFACT), "content_hash": QUALITY_ARTIFACT_HASH, "time_s": 0.5}], "limitations": []})
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
        with self.assertRaisesRegex(ContractError, "too weak|metadata alone"):
            validate_first_last_frame(record)

    def test_flf_probe_preparation_is_explicitly_not_run(self):
        spec = {"schema_version": 1, "probe_id": "flf-test", "profile_id": "profile-test",
                "shot_id": "shot-test", "mode": "FIRST_AND_LAST",
                "endpoint": "http://127.0.0.1:8188", "model": {"id": "model-test", "version": "1"},
                "parameters": {"seed": 1}, "workflow_hash": digest("flf-workflow"),
                "inputs": {"first_frame": {"ref": str(QUALITY_ARTIFACT), "content_hash": QUALITY_ARTIFACT_HASH},
                           "last_frame": {"ref": str(QUALITY_ARTIFACT), "content_hash": QUALITY_ARTIFACT_HASH}}}
        result = prepare_first_last_frame_probe(spec)
        self.assertEqual("NOT_RUN", result["status"])
        self.assertFalse(result["accepted"])
        self.assertEqual("NOT_RUN", result["probe"]["capability_status"])
        for check in result["probe"]["checks"]:
            self.assertEqual("NOT_RUN", check["result"])

    def test_flf_probe_cli_does_not_promote_metadata_to_capability(self):
        with tempfile.TemporaryDirectory(prefix="vge-flf-probe-cli-") as raw:
            root = Path(raw)
            spec = {"schema_version": 1, "probe_id": "flf-cli", "profile_id": "profile-test",
                    "shot_id": "shot-test", "mode": "FIRST_ONLY", "endpoint": "http://127.0.0.1:8188",
                    "model": {"id": "model-test", "version": "1"}, "parameters": {"seed": 1},
                    "workflow_hash": digest("flf-workflow"),
                    "inputs": {"first_frame": {"ref": str(QUALITY_ARTIFACT), "content_hash": QUALITY_ARTIFACT_HASH}}}
            source = root / "probe.json"
            source.write_text(json.dumps(spec), encoding="utf-8")
            completed = subprocess.run([sys.executable, str(SKILL / "scripts/vge.py"), "flf-probe", str(source)],
                                       capture_output=True, text=True, check=False)
            self.assertEqual(2, completed.returncode)
            result = json.loads(completed.stdout)
            self.assertEqual("NOT_RUN", result["status"])

    def test_case_execution_envelope_requires_ordered_lineage(self):
        envelope = {"schema_version": 1, "id": "case-envelope-1", "case_id": "LF-001",
                    "project_id": "project-1", "scene_id": "scene-1", "shot_order": ["a", "b"],
                    "shots": [{"shot_id": "a", "dependency_ids": [], "state_start": {"door": "closed"},
                               "state_end_declared": {"door": "open"}, "status": "NOT_RUN"},
                              {"shot_id": "b", "dependency_ids": ["a"], "state_start": {"door": "open"},
                               "state_end_declared": {"door": "closed"}, "status": "NOT_RUN"}],
                    "transitions": [], "assembly": {"status": "NOT_RUN"}, "status": "NOT_RUN"}
        result = validate_long_form_execution_envelope(envelope)
        self.assertEqual("NOT_RUN", result["status"])
        self.assertFalse(result["accepted"])
        bad = copy.deepcopy(envelope)
        bad["status"] = "PASS"
        with self.assertRaisesRegex(ContractError, "every shot|adjacent transition"):
            validate_long_form_execution_envelope(bad)

    def test_contact_dialogue_and_audio_contracts_separate_channels(self):
        phases = []
        for index, phase in enumerate(CONTACT_PHASES):
            phases.append({"phase": phase, "start_s": index, "end_s": index + .5, "observable_assertion": "fixture assertion"})
        contact = {"schema_version": 1, "id": "contact_1", "shot_id": "shot_contact", "actor": "a", "receiver": "b", "object_id": "door", "cause": "hand pushes", "expected_result": "door open", "phases": phases}
        self.assertEqual("PARTIAL", validate_contact_phases(contact)["status"])
        for phase in phases:
            phase.update(oracle=oracle("FRAME" if phase["phase"] in ("APPROACH", "PRE_CONTACT") else "SEQUENCE"), evidence=evidence())
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
        channel_oracles = {"semantics": "AUDIO", "voice": "AUDIO", "performance": "SEQUENCE", "lip_sync": "SEQUENCE", "mix": "AUDIO"}
        channels = {channel: {"status": "PASS", "oracle": oracle(channel_oracles[channel]),
                              "evidence": audio_evidence() if channel in ("semantics", "voice", "mix") else evidence()}
                    for channel in channel_oracles}
        channels["voice"]["audio_ref"] = str(QUALITY_ARTIFACT)
        channels["lip_sync"]["paired_evidence"] = evidence() + audio_evidence()
        dialogue = {"schema_version": 1, "artifact_ref": str(QUALITY_ARTIFACT), "artifact_content_hash": QUALITY_ARTIFACT_HASH, "provenance": quality_provenance("shot_1", "artifact_dialogue"), "lines": [{"id": "line_1", "shot_id": "shot_1", "speaker": "a", "listener": "b", "text": "Ready.", "start_s": 1, "end_s": 2, "intention": "warn", "delivery": "quiet", "emotion": "focused", "gaze": "listener", "pause_policy": "none", "overlap_policy": "none", "listener_reaction": "listener remains attentive", "reaction_order": {"events": [{"id": "stimulus_1", "stage": "STIMULUS", "start_s": 0.5, "end_s": 0.8}, {"id": "processing_1", "stage": "PROCESSING", "start_s": 0.8, "end_s": 1.0}, {"id": "reaction_1", "stage": "REACTION", "start_s": 1.2, "end_s": 1.4}, {"id": "response_1", "stage": "RESPONSE", "start_s": 2.0, "end_s": 2.2}]}, "voice_strategy": {"status": "NATIVE_CONFIRMED", "reference": "fixture_voice"}, "lip_sync_strategy": {"status": "EXTERNAL_CONFIRMED", "path": "fixture_lip_sync"}, "visible_speech": True, "channels": channels}]}
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
                   "oracle": oracle("AUDIO"), "evidence": audio_evidence()} for layer in AUDIO_LAYERS]
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
        canonical_state = {"scene_id": "fixture"}
        self.assertEqual("PASS", adapt_prompt(sections, {"id": "fixture", "preserve_sections": list(sections)}, canonical_state=canonical_state)["status"])
        degraded = adapt_prompt(sections, {"id": "small", "unsupported_sections": ["audio"]}, canonical_state=canonical_state)
        self.assertEqual("DEGRADED", degraded["status"]); self.assertEqual(["audio"], degraded["omissions"])
        with self.assertRaisesRegex(ContractError, "classify every canonical section"):
            adapt_prompt(sections, {"id": "ambiguous", "preserve_sections": ["identity"]}, canonical_state=canonical_state)
        with self.assertRaisesRegex(ContractError, "preserve and omit"):
            adapt_prompt(sections, {"id": "overlap", "preserve_sections": ["identity", "audio"],
                                   "unsupported_sections": ["audio"]}, canonical_state=canonical_state)
        with self.assertRaisesRegex(ContractError, "remapping"):
            adapt_prompt(sections, {"id": "remapped", "mapping": {"identity": "motion"}},
                         canonical_state=canonical_state)
        with self.assertRaisesRegex(ContractError, "truncate"):
            adapt_prompt(sections, {"id": "tiny", "max_words": 1}, canonical_state=canonical_state)
        with self.assertRaisesRegex(ContractError, "requires canonical state"):
            adapt_prompt(sections, {"id": "fixture"})
        diff = adapter_differential(sections, [{"id": "fixture"}, {"id": "small", "unsupported_sections": ["audio"]}], canonical_state=canonical_state)
        self.assertEqual("DEGRADED", diff["status"])
        self.assertTrue(all(item["canonical_semantics_preserved"] for item in diff["adapters"]))
        self.assertEqual(digest(canonical_state), diff["canonical_state_hash"])
        self.assertTrue(analyze_prompt_density({"constraints": "not open and static"})["contradictions"])

    def test_canonical_prompt_gate_rejects_state_contradictions(self):
        state = {
            "vehicle": {"door_state": "CLOSED", "motion_state": "PARKED"},
            "entry_door_state": "OPEN",
            "subject": {"position": "OUTSIDE", "seated_state": "SEATED"},
            "time_of_day": "NIGHT",
            "lighting": "GOLDEN_HOUR",
            "camera": {"movement": {"type": "STATIC", "path": "ORBIT"}},
        }
        report = detect_canonical_contradictions(state)
        self.assertEqual("FAIL", report["status"])
        self.assertTrue({"DOOR_ENTRY_STATE", "SUBJECT_SEATING_STATE", "TIME_LIGHTING", "CAMERA_MOTION"} <=
                        {item["id"] for item in report["contradictions"]})
        with self.assertRaisesRegex(ContractError, "Canonical state contradictions"):
            validate_canonical_state(state)
        with self.assertRaisesRegex(ContractError, "Canonical state contradictions"):
            adapt_prompt({"identity": {"subject": "adult"}}, {"id": "fixture"}, canonical_state=state)
        ownership = detect_canonical_contradictions({
            "ownership": {"owner_before": "a", "owner_after": "b", "contact_state": "PROXIMITY"}
        })
        self.assertIn("OWNERSHIP_TRANSFER", {item["id"] for item in ownership["contradictions"]})
        motion = detect_canonical_contradictions({"vehicle": {"motion_state": "PARKED", "velocity_phase": "ACCELERATING"}})
        self.assertIn("VEHICLE_MOTION_STATE", {item["id"] for item in motion["contradictions"]})
        held_target = detect_canonical_contradictions({
            "subject": {"id": "subject_001", "hand_occupancy": {"right_hand": "object_001"}},
            "interaction": {"actor": "subject_001", "target": "object_001", "phases": ["APPROACH"]},
        })
        self.assertIn("APPROACH_HELD_TARGET", {item["id"] for item in held_target["contradictions"]})
        handoff = detect_canonical_contradictions({
            "subject": {"id": "subject_001", "hand_occupancy": {"right_hand": "object_001"}},
            "interaction": {"actor": "subject_002", "target": "object_001", "phases": ["APPROACH"]},
        })
        self.assertNotIn("APPROACH_HELD_TARGET", {item["id"] for item in handoff["contradictions"]})
        different_effector = detect_canonical_contradictions({
            "subject": {"id": "subject_001", "hand_occupancy": {"right_hand": "object_001"}},
            "interaction": {"actor": "subject_001", "target": "object_001", "effector": "left_hand", "phases": ["APPROACH"]},
        })
        self.assertNotIn("APPROACH_HELD_TARGET", {item["id"] for item in different_effector["contradictions"]})

    def test_negative_constraints_are_scene_risk_scoped(self):
        scene = {
            "action_sequence": ["adult approaches a vehicle and reaches the door handle"],
            "vehicle": {"door": "closed"},
            "negative_constraints": [
                {"family": "VEHICLE", "constraint": "no impossible door geometry"},
                {"family": "DIALOGUE", "constraint": "no speaker swap"},
            ],
        }
        result = select_negative_constraints(scene)
        self.assertEqual("PASS", result["status"])
        self.assertIn("VEHICLE", result["selected_families"])
        self.assertEqual(["VEHICLE"], [item["family"] for item in result["selected"]])
        self.assertEqual("DIALOGUE", result["omitted"][0]["family"])
        audio = select_negative_constraints({
            "audio_timeline": [{"layer": "ambience", "source": "room tone"}],
            "negative_constraints": [{"family": "AUDIO", "constraint": "no clipped mix"}],
        })
        self.assertIn("AUDIO", audio["selected_families"])
        self.assertEqual("AUDIO", audio["selected"][0]["family"])

    def test_cli_quality_partial_is_nonzero(self):
        case = ROOT / "verification/long-form/LF-001-r4-case.json"
        command = [sys.executable, str(SKILL / "scripts/vge.py"), "long-form", str(case)]
        completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        self.assertNotEqual(0, completed.returncode)
        self.assertIn('"status": "PARTIAL"', completed.stdout)

    def test_semantic_qa_rejects_weak_oracle_for_strong_claim(self):
        item = semantic_observation()
        item["checks"][0]["oracle"] = oracle("METADATA", "Does metadata prove identity?")
        with self.assertRaisesRegex(ContractError, "weak|allowed"):
            validate_semantic_observation(item)

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
        observed = {"runtime_version": "1", "node_inventory_hash": digest("nodes"),
                    "workflow_hash": digest("workflow"), "workflow_fingerprint": digest("workflow-fingerprint"),
                    "model_asset_hash": digest("model"), "selected_device": "cuda:0",
                    "resource_context_hash": digest("resources")}
        self.assertEqual("CONFIRMED", validate_feature_profile(profile, "text_to_video", observed=observed)["status"])
        self.assertEqual("UNKNOWN", validate_feature_profile(profile, "text_to_video")["status"])
        self.assertEqual("UNKNOWN", validate_feature_profile(profile, "text_to_video", observed={"unrelated": True})["status"])
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
        failed_provenance = quality_provenance("a", "artifact_repair_failed")
        repaired_media = PROVENANCE_ROOT / "artifact_repair_new.mp4"
        shutil.copyfile(ROOT / "verification/media/art_c1c52b6492b04dc1847edbe3d028bab7.mp4", repaired_media)
        repaired_media_hash = file_hash(repaired_media)
        new_provenance = quality_provenance("a", "artifact_repair_new", repaired_media, repaired_media_hash)
        new_attempt_path = Path(new_provenance["attempt"]["ref"])
        new_attempt_record = json.loads(new_attempt_path.read_text(encoding="utf-8"))
        new_attempt_record["parent_attempt_id"] = failed_provenance["attempt"]["id"]
        new_attempt_path.write_text(json.dumps(new_attempt_record, sort_keys=True) + "\n", encoding="utf-8")
        new_provenance["attempt"]["content_hash"] = file_hash(new_attempt_path)
        before_path = PROVENANCE_ROOT / "repair-before.json"
        before_path.write_text(json.dumps({"schema_version": 1, "id": "repair-before", "status": "FAIL",
                                           "artifact_id": "artifact_repair_failed",
                                           "artifact_ref": str(QUALITY_ARTIFACT),
                                           "observed_content_hash": QUALITY_ARTIFACT_HASH}, sort_keys=True), encoding="utf-8")
        after_path = PROVENANCE_ROOT / "repair-after.json"
        after_path.write_text(json.dumps({"schema_version": 1, "id": "repair-after", "status": "PASS",
                                          "artifact_id": "artifact_repair_new",
                                          "artifact_ref": str(repaired_media),
                                          "observed_content_hash": repaired_media_hash}, sort_keys=True), encoding="utf-8")
        ref = lambda path: {"ref": str(path), "content_hash": file_hash(path)}
        repair["execution_ledger"] = {"schema_version": 1, "status": "COMPLETE", "attempts": 2, "regenerations": 1, "runtime_s": 10, "cost_usd": 0, "human_reviews": 0, "observed_at": datetime.now(timezone.utc).isoformat(), "completed_at": datetime.now(timezone.utc).isoformat(), "evidence": evidence(), "provenance": failed_provenance,
            "lineage": {"failed_attempt": ref(failed_provenance["attempt"]["ref"]), "new_attempt": ref(new_provenance["attempt"]["ref"]),
                        "failed_artifact": ref(failed_provenance["artifact"]["record_ref"]), "new_artifact": ref(new_provenance["artifact"]["record_ref"]),
                        "failed_dimension": "identity", "before_observation": ref(before_path), "after_observation": ref(after_path),
                        "improvement": {"dimension": "identity", "before": "FAIL", "after": "PASS", "reason": "Re-anchored generation restored the declared identity dimension"},
                        "adjacent_transition_results": [{"pair": "a->b", "status": "PASS", "evidence": evidence()}]}}
        self.assertEqual("BLOCKED", validate_repair_plan(repair)["status"])
        repair["transition_revalidation"].update(
            status="PASS", validated_pairs=["a->b"],
            evidence_refs=[{"pair": "a->b", "ref": str(QUALITY_ARTIFACT), "content_hash": QUALITY_ARTIFACT_HASH}])
        self.assertEqual("PASS", validate_repair_plan(repair)["status"])
        same_parent = copy.deepcopy(repair)
        same_parent["execution_ledger"]["lineage"]["new_attempt"] = same_parent["execution_ledger"]["lineage"]["failed_attempt"]
        with self.assertRaisesRegex(ContractError, "distinct failed and new attempts"):
            validate_repair_plan(same_parent)
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
        self.assertEqual(0, maturity_report({"structural": "PASS", "deterministic_tests": "PASS", "runtime_provenance": "PASS"})["level"])
        gate_types = {"structural": "CONTRACT", "deterministic_tests": "TEST_REPORT",
                      "runtime_provenance": "RUNTIME", "audiovisual": "MEDIA_BYTES",
                      "bounded_production": "PRODUCTION_CASE", "independent_critic": "CRITIC"}
        gate = lambda key: {"status": "PASS", "gate_id": {
                                      "structural": "STRUCTURAL_VALIDATION",
                                      "deterministic_tests": "DETERMINISTIC_VERIFICATION",
                                      "runtime_provenance": "RUNTIME_EXECUTION",
                                      "audiovisual": "ARTIFACT_OBSERVATION",
                                      "bounded_production": "MULTI_SHOT_ACCEPTANCE",
                                      "independent_critic": "INDEPENDENT_CRITIC",
                                  }[key], "scope": "fixture-scope", "criteria": "fixture criterion",
                                  "observed_at": datetime.now(timezone.utc).isoformat(),
                                  "procedure": key, "limitations": [], "evidence": [
                                      {"type": gate_types[key], **item} for item in decision_evidence()]}
        validated = maturity_report({key: gate(key) for key in gate_types})
        self.assertEqual(5, validated["level"])
        self.assertEqual("PASS", validated["status"])

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
                    "listener_reaction": "listener remains attentive", "causality": {"events": [
                        {"id": "stimulus_alias", "stage": "STIMULUS", "start_s": 0.5, "end_s": 0.8},
                        {"id": "processing_alias", "stage": "PROCESSING", "start_s": 0.8, "end_s": 1.0},
                        {"id": "reaction_alias", "stage": "REACTION", "start_s": 1.2, "end_s": 1.4},
                        {"id": "response_alias", "stage": "RESPONSE", "start_s": 2.0, "end_s": 2.2},
                    ]}, "voice_reference": "voice-a", "lip_sync_mode": "UNKNOWN", "channels": {
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
    def test_capture_evidence_is_hash_bound_and_not_semantic_acceptance(self):
        with tempfile.TemporaryDirectory(prefix="vge-capture-test-") as raw:
            report = capture_evidence(QUALITY_ARTIFACT, Path(raw) / "evidence", [0.2, 1.0], [[0.1, 0.4]])
            self.assertEqual("CAPTURED", report["status"])
            self.assertEqual("NOT_RUN", report["semantic_acceptance"])
            self.assertEqual(QUALITY_ARTIFACT_HASH, report["source_content_hash"])
            self.assertEqual(2, len(report["frames"]))
            self.assertEqual(1, len(report["audio_windows"]))
            self.assertTrue(report["source_media_metadata"]["audio_streams"])
            self.assertIn("source_audio_stream", report["audio_windows"][0])
            self.assertIn("derived_audio_stream", report["audio_windows"][0])
            for item in report["frames"] + report["audio_windows"]:
                self.assertEqual(str(QUALITY_ARTIFACT), item["source_ref"])
                self.assertEqual(QUALITY_ARTIFACT_HASH, item["source_content_hash"])
                self.assertTrue(Path(item["ref"]).is_file())
                self.assertTrue(item["content_hash"].startswith("sha256:"))
            with self.assertRaisesRegex(ContractError, "exists"):
                capture_evidence(QUALITY_ARTIFACT, Path(raw) / "evidence", [0.2], [])
            with self.assertRaisesRegex(ContractError, "before source duration"):
                capture_evidence(QUALITY_ARTIFACT, Path(raw) / "another-evidence", [5.167], [])

    def test_capture_evidence_cli_public_path(self):
        with tempfile.TemporaryDirectory(prefix="vge-capture-cli-test-") as raw:
            output_dir = Path(raw) / "evidence"
            completed = subprocess.run(
                [sys.executable, str(SKILL / "scripts/vge.py"), "capture-evidence", str(QUALITY_ARTIFACT),
                 "--output-dir", str(output_dir), "--frame", "0.2", "--audio-window", "0.1", "0.4"],
                capture_output=True, text=True, check=False)
            self.assertEqual(0, completed.returncode, completed.stderr)
            result = json.loads(completed.stdout)
            self.assertEqual("CAPTURED", result["status"])
            self.assertEqual("NOT_RUN", result["semantic_acceptance"])

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
