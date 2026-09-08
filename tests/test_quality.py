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
    CONTACT_PHASES,
    CONTINUITY_DIMENSIONS,
    adapt_prompt,
    adapter_differential,
    analyze_prompt_density,
    build_repair_plan,
    maturity_report,
    profile_fingerprint,
    reanchor_decision,
    validate_audio_timeline,
    validate_contact_phases,
    validate_continuity_scorecard,
    validate_dialogue_contract,
    validate_feature_profile,
    validate_first_last_frame,
    validate_long_form_case,
    validate_observation_contract,
    validate_semantic_observation,
    validate_repair_plan,
    validate_transition_contract,
)


QUALITY_ARTIFACT = ROOT / "verification/media/final/art_2898879072af4739b673efe71fafcc7e.mp4"
QUALITY_ARTIFACT_HASH = file_hash(QUALITY_ARTIFACT)
PROVENANCE_ROOT = Path(tempfile.mkdtemp(prefix="vge-quality-provenance-"))


def evidence(ref=None):
    ref = str(QUALITY_ARTIFACT) if ref is None else ref
    return [{"type": "FRAME", "ref": ref, "content_hash": QUALITY_ARTIFACT_HASH if ref == str(QUALITY_ARTIFACT) else digest(ref), "time_s": 0.5}]


def decision_evidence():
    return [{"ref": str(QUALITY_ARTIFACT), "content_hash": QUALITY_ARTIFACT_HASH}]


def quality_provenance(shot_id, artifact_id):
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", f"{shot_id}-{artifact_id}")
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
                       "execution_attempt_ref": attempt_id, "artifact_ref": str(QUALITY_ARTIFACT),
                       "content_hash": QUALITY_ARTIFACT_HASH, "generation_status": "GENERATED",
                       "media": {"kind": "video"}}
    artifact_ref = PROVENANCE_ROOT / f"{safe}-artifact.json"
    artifact_ref.write_text(json.dumps(artifact_record, sort_keys=True), encoding="utf-8")
    return {"attempt": {"id": attempt_id, "ref": str(attempt_ref), "content_hash": file_hash(attempt_ref)},
            "shot": {"id": shot_id, "ref": str(shot_ref), "content_hash": file_hash(shot_ref),
                     "contract_hash": digest(shot_record)},
            "artifact": {"id": artifact_id, "record_ref": str(artifact_ref),
                         "record_content_hash": file_hash(artifact_ref), "media_ref": str(QUALITY_ARTIFACT),
                         "media_content_hash": QUALITY_ARTIFACT_HASH}}


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
        contract = {"schema_version": 1, "id": "tr_1", "previous_shot_id": "shot_1", "next_shot_id": "shot_2",
                    "previous_artifact": {"shot_id": "shot_1", "artifact_id": "artifact_1", "artifact_ref": str(QUALITY_ARTIFACT), "content_hash": QUALITY_ARTIFACT_HASH},
                    "next_artifact": {"shot_id": "shot_2", "artifact_id": "artifact_2", "artifact_ref": str(QUALITY_ARTIFACT), "content_hash": QUALITY_ARTIFACT_HASH},
                    "required_state_properties": ["object.door", "subject.position"],
                    "previous_end_state": {"object.door": "open", "subject.position": "left"},
                    "next_start_state": {"object.door": "open", "subject.position": "left"},
                    "continuity_scorecard": scorecard(), "status": "PASS"}
        self.assertTrue(validate_transition_contract(contract)["accepted"])
        contract["previous_artifact"]["artifact_ref"] = "/tmp/vge-previous-transition-does-not-exist.mp4"
        with self.assertRaisesRegex(ContractError, "existing artifact bytes"):
            validate_transition_contract(contract)
        contract["previous_artifact"]["artifact_ref"] = str(QUALITY_ARTIFACT)
        contract["next_start_state"]["object.door"] = "closed"
        with self.assertRaisesRegex(ContractError, "state mismatch"):
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

    def test_first_last_frame_needs_actual_endpoint_checks(self):
        checks = []
        for check_id in ("endpoint_identity", "motion_path", "object_state", "artifact_delivery"):
            checks.append({"id": check_id, "category": "visual", "result": "PASS", "oracle": oracle("FRAME"), "confidence": "HIGH", "evidence": [{"type": "FRAME", "ref": str(QUALITY_ARTIFACT), "content_hash": QUALITY_ARTIFACT_HASH, "time_s": 0.5}], "limitations": []})
        record = {"schema_version": 1, "profile_id": "h3-r2v", "shot_id": "shot_flf", "capability_status": "CONFIRMED", "workflow_hash": digest("workflow"),
                  "inputs": {"first_frame": {"ref": str(QUALITY_ARTIFACT), "content_hash": QUALITY_ARTIFACT_HASH}, "last_frame": {"ref": str(QUALITY_ARTIFACT), "content_hash": QUALITY_ARTIFACT_HASH}},
                  "artifact_ref": str(QUALITY_ARTIFACT), "artifact_content_hash": QUALITY_ARTIFACT_HASH, "provenance": quality_provenance("shot_flf", "artifact_flf"),
                  "checks": checks}
        self.assertTrue(validate_first_last_frame(record)["accepted"])
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
        events = [{"id": "a_" + layer, "layer": layer, "start_s": 1, "end_s": 2, "cause": "fixture", "source": layer + ".wav", "oracle": oracle("AUDIO"), "evidence": evidence()} for layer in ("dialogue", "ambience", "effects", "music", "silence", "transition")]
        timeline = {"events": events, "required_layers": [item["layer"] for item in events], "not_applicable_layers": [], "shot_id": "shot_audio", "artifact_ref": str(QUALITY_ARTIFACT), "artifact_content_hash": QUALITY_ARTIFACT_HASH, "observed_at": datetime.now(timezone.utc).isoformat(), "procedure": "Bound audio timeline fixture inspection", "provenance": quality_provenance("shot_audio", "artifact_audio")}
        self.assertEqual("PASS", validate_audio_timeline(timeline)["status"])
        saved_audio_provenance = timeline.pop("provenance")
        with self.assertRaisesRegex(ContractError, "audio_timeline.provenance"):
            validate_audio_timeline(timeline)
        timeline["provenance"] = saved_audio_provenance
        events[0]["evidence"][0]["ref"] = "/tmp/vge-audio-evidence-does-not-exist.wav"
        with self.assertRaisesRegex(ContractError, "existing artifact bytes"):
            validate_audio_timeline(timeline)
        self.assertEqual("PARTIAL", validate_audio_timeline([events[0]])["status"])

    def test_prompt_adapter_is_loss_explicit_and_differential(self):
        sections = {"identity": {"subject": "courier"}, "motion": {"action": "walk"}, "audio": {"dialogue": "Ready"}}
        self.assertEqual("PASS", adapt_prompt(sections, {"id": "fixture", "preserve_sections": list(sections)})["status"])
        degraded = adapt_prompt(sections, {"id": "small", "unsupported_sections": ["audio"]})
        self.assertEqual("DEGRADED", degraded["status"]); self.assertEqual(["audio"], degraded["omissions"])
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
        self.assertEqual("PASS", validate_repair_plan(repair)["status"])
        saved_repair_provenance = repair["execution_ledger"].pop("provenance")
        with self.assertRaisesRegex(ContractError, "provenance"):
            validate_repair_plan(repair)
        repair["execution_ledger"]["provenance"] = saved_repair_provenance
        case = {"schema_version": 1, "id": "LF-003", "target_duration_s": 45, "intent_ref": "intent", "plan_ref": "plan", "scene_bible_ref": "bible", "shot_graph_ref": "graph", "continuity_ref": "continuity", "evidence_ref": "evidence", "shot_ids": ["a", "b"], "audio_timeline_ref": "audio", "repair_budget_ref": "repair", "human_checkpoint_ref": "human", "status": "PARTIAL", "production_evidence_complete": False}
        self.assertEqual("PARTIAL", validate_long_form_case(case)["status"])
        self.assertEqual(3, maturity_report({"structural": "PASS", "deterministic_tests": "PASS", "runtime_provenance": "PASS"})["level"])

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


if __name__ == "__main__":
    unittest.main()
