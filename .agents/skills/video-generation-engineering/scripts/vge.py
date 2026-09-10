#!/usr/bin/env python3
"""Portable JSON CLI. Run --help; all writes create new files exclusively."""
import argparse
import json
import sys
from pathlib import Path

from vge_core import (
    ContractError, load, save, prepare, validate, compile_plan, negotiate, repair_scope,
    route_references, detect_canonical_contradictions, select_negative_constraints,
)
from vge_runtime import ComfyClient, validate_workflow, bind_workflow, submit, poll, collect
from vge_media import probe, assemble, contact_sheet, trim, validate_assembly_manifest
from vge_capture import capture_evidence
from vge_evidence import aggregate, validate_observation
from vge_provider import hailuo_request, hailuo_submit, hailuo_poll
from vge_quality import (validate_continuity_scorecard, validate_transition_contract, validate_semantic_observation,
                         reanchor_decision, validate_first_last_frame, validate_contact_phases,
                         validate_causal_sequence, validate_object_ownership, validate_vehicle_state,
                         validate_dialogue_contract, validate_audio_timeline, analyze_prompt_density, adapt_prompt,
                         adapter_differential, validate_feature_profile, build_repair_plan, validate_repair_plan,
                         validate_long_form_case, maturity_report, validate_editorial_acceptance,
                         prepare_first_last_frame_probe, validate_first_last_frame_suite,
                         validate_long_form_execution_envelope)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "validate", "compile", "route", "negotiate", "aggregate", "accept", "assemble", "repair-scope", "hailuo-plan", "hailuo-submit"):
        p = sub.add_parser(name)
        p.add_argument("input", help="JSON file")
        p.add_argument("--output", help="New JSON file; stdout when omitted")
        if name in ("compile", "negotiate"):
            p.add_argument("--profile", required=name == "negotiate")
        if name == "assemble":
            p.add_argument("--video", required=True)
            p.add_argument("--preview", action="store_true")
        if name == "hailuo-submit":
            p.add_argument("--destination", required=True)
            p.add_argument("--authorize-paid-call", action="store_true")
            p.add_argument("--authorize-transfer", action="store_true")
    p = sub.add_parser("hailuo-poll");p.add_argument("task_id");p.add_argument("--timeout",type=float,default=60);p.add_argument("--output")
    p = sub.add_parser("probe"); p.add_argument("input"); p.add_argument("--output")
    p = sub.add_parser("contact-sheet"); p.add_argument("input"); p.add_argument("image"); p.add_argument("--frames", type=int, default=8)
    p = sub.add_parser("trim", help="create an explicit derived media trim"); p.add_argument("input"); p.add_argument("output_path"); p.add_argument("--duration", type=float, required=True); p.add_argument("--report")
    p = sub.add_parser("media-qa"); p.add_argument("input"); p.add_argument("--output"); p.add_argument("--audio-required", action="store_true"); p.add_argument("--allow-black", action="store_true"); p.add_argument("--allow-freeze", action="store_true"); p.add_argument("--expected-duration", type=float); p.add_argument("--expected-fps", type=float); p.add_argument("--expected-width", type=int); p.add_argument("--expected-height", type=int); p.add_argument("--expected-frame-count", type=int); p.add_argument("--expected-codec"); p.add_argument("--expected-container")
    p = sub.add_parser("capture-evidence", help="capture hash-bound frames/audio without semantic acceptance")
    p.add_argument("input"); p.add_argument("--output-dir", required=True); p.add_argument("--frame", dest="frames", action="append", type=float, default=[])
    p.add_argument("--audio-window", dest="audio_windows", action="append", nargs=2, type=float, metavar=("START_S", "DURATION_S"), default=[])
    p.add_argument("--report")
    for name, help_text in (("scorecard", "continuity scorecard JSON"), ("transition", "adjacent transition JSON"),
                            ("semantic", "category-separated observation JSON"), ("shot-acceptance", "shot acceptance contract JSON"),
                            ("contact", "contact phases JSON"), ("dialogue", "dialogue contract JSON"), ("audio", "audio timeline JSON"),
                            ("causality", "stimulus-processing-reaction-response JSON"),
                            ("ownership", "object ownership transition JSON"), ("vehicle-state", "vehicle state JSON"),
                            ("repair-validate", "repair plan JSON"), ("long-form", "long-form ladder case JSON"),
                            ("case-envelope", "case-level long-form execution envelope JSON"),
                            ("maturity", "maturity evidence JSON"), ("adapter-diff", "adapter differential JSON"),
                            ("assembly-validate", "strict assembly manifest JSON"), ("editorial", "editorial acceptance JSON")):
        p = sub.add_parser(name, help=help_text); p.add_argument("input"); p.add_argument("--output")
    p = sub.add_parser("reanchor"); p.add_argument("input"); p.add_argument("--shot-id", required=True); p.add_argument("--downstream", nargs="*", default=[]); p.add_argument("--output")
    p = sub.add_parser("repair-plan"); p.add_argument("input"); p.add_argument("--output")
    p = sub.add_parser("prompt-density"); p.add_argument("input"); p.add_argument("--output")
    p = sub.add_parser("contradictions", help="canonical-state contradiction gate"); p.add_argument("input"); p.add_argument("--output")
    p = sub.add_parser("negative-select", help="scene-aware negative-constraint selection"); p.add_argument("input"); p.add_argument("--output")
    p = sub.add_parser("adapt-prompt"); p.add_argument("input"); p.add_argument("--adapter", required=True); p.add_argument("--output")
    p = sub.add_parser("profile-check"); p.add_argument("input"); p.add_argument("--feature", required=True); p.add_argument("--output")
    p = sub.add_parser("first-last-frame"); p.add_argument("input"); p.add_argument("--output")
    p = sub.add_parser("flf-suite", help="validate all three first/last-frame capability modes"); p.add_argument("input"); p.add_argument("--output")
    p = sub.add_parser("flf-probe", help="prepare a mode-specific FLF probe without executing generation"); p.add_argument("input"); p.add_argument("--output")
    for name in ("discover", "preflight", "bind", "submit", "poll", "collect"):
        p = sub.add_parser(name)
        p.add_argument("--endpoint", default="http://127.0.0.1:8188")
        p.add_argument("--output")
        if name in ("preflight", "bind", "submit"):
            p.add_argument("workflow")
        if name == "bind": p.add_argument("bindings")
        if name == "submit":
            p.add_argument("context"); p.add_argument("--destination", required=True); p.add_argument("--authorize-submit", action="store_true")
            p.add_argument("--probe", action="store_true", help="Explicit single diagnostic submission; does not assert profile support")
        if name == "poll":
            p.add_argument("prompt_id"); p.add_argument("--timeout", type=float, default=60)
        if name == "collect":
            p.add_argument("attempt"); p.add_argument("history"); p.add_argument("--destination", required=True)
    args = parser.parse_args(argv)
    try:
        cmd = args.command
        data = load(args.input) if hasattr(args, "input") and cmd not in ("probe", "contact-sheet", "media-qa", "trim", "capture-evidence") else None
        if cmd == "prepare": result = prepare(data)
        elif cmd == "validate": result = validate(data)
        elif cmd == "compile": result = compile_plan(data, load(args.profile) if args.profile else None)
        elif cmd == "route": result = route_references(prepare(data))
        elif cmd == "negotiate": result = negotiate(data, load(args.profile))
        elif cmd == "aggregate":
            aggregate_status = aggregate(data["checks"], data.get("artifact_id"))
            result = {"status": aggregate_status, "accepted": aggregate_status == "PASS"}
        elif cmd == "repair-scope": result = repair_scope(data["plan"], data["changed_shot_ids"])
        elif cmd == "hailuo-plan": result = hailuo_request(data)
        elif cmd == "hailuo-submit": result = hailuo_submit(data,args.destination,args.authorize_paid_call,args.authorize_transfer)
        elif cmd == "hailuo-poll": result = hailuo_poll(args.task_id,args.timeout)
        elif cmd == "accept": result = validate_observation(data["observation"], data["artifact"], data["attempt"], data["shot"])
        elif cmd == "probe": result = probe(args.input)
        elif cmd == "contact-sheet": result = contact_sheet(args.input, args.image, args.frames)
        elif cmd == "trim":
            result = trim(args.input, args.output_path, args.duration)
            if args.report: save(args.report, result)
        elif cmd == "media-qa":
            expected_resolution = [args.expected_width, args.expected_height] if args.expected_width is not None or args.expected_height is not None else None
            result = __import__("vge_media", fromlist=["media_qa"]).media_qa(
                args.input, args.audio_required, args.allow_black, args.allow_freeze,
                expected_duration_s=args.expected_duration, expected_fps=args.expected_fps,
                expected_resolution=expected_resolution, expected_frame_count=args.expected_frame_count,
                expected_codec=args.expected_codec, expected_container=args.expected_container)
        elif cmd == "capture-evidence":
            result = capture_evidence(args.input, args.output_dir, args.frames, args.audio_windows)
            if args.report:
                save(args.report, result)
        elif cmd == "scorecard": result = validate_continuity_scorecard(data)
        elif cmd == "transition": result = validate_transition_contract(data)
        elif cmd == "semantic": result = validate_semantic_observation(data)
        elif cmd == "shot-acceptance":
            result = __import__("vge_quality", fromlist=["validate_shot_acceptance"]).validate_shot_acceptance(
                data.get("contract", data), data.get("artifact"), data.get("observation"), data.get("scorecard"))
        elif cmd == "contact": result = validate_contact_phases(data)
        elif cmd == "causality": result = validate_causal_sequence(data)
        elif cmd == "ownership": result = validate_object_ownership(data)
        elif cmd == "vehicle-state": result = validate_vehicle_state(data)
        elif cmd == "dialogue": result = validate_dialogue_contract(data)
        elif cmd == "audio": result = validate_audio_timeline(data)
        elif cmd == "reanchor": result = reanchor_decision(data, args.shot_id, args.downstream)
        elif cmd == "repair-plan": result = build_repair_plan(data["plan"], data["changed_shot_ids"], data["findings"], data["budget"])
        elif cmd == "repair-validate": result = validate_repair_plan(data)
        elif cmd == "prompt-density": result = analyze_prompt_density(data.get("sections", data), data.get("limits", {}))
        elif cmd == "contradictions": result = detect_canonical_contradictions(data)
        elif cmd == "negative-select": result = select_negative_constraints(data)
        elif cmd == "adapt-prompt": result = adapt_prompt(data["sections"], load(args.adapter), canonical_state=data.get("canonical_state"))
        elif cmd == "profile-check": result = validate_feature_profile(data.get("profile", data), args.feature, observed=data.get("observed"), base_dir=Path(args.input).resolve().parent)
        elif cmd == "first-last-frame": result = validate_first_last_frame(data)
        elif cmd == "flf-suite": result = validate_first_last_frame_suite(data)
        elif cmd == "flf-probe": result = prepare_first_last_frame_probe(data)
        elif cmd == "long-form": result = validate_long_form_case(data, base_dir=Path(args.input).resolve().parent)
        elif cmd == "case-envelope": result = validate_long_form_execution_envelope(data, base_dir=Path(args.input).resolve().parent)
        elif cmd == "maturity": result = maturity_report(data)
        elif cmd == "adapter-diff": result = adapter_differential(data["canonical_sections"], data["adapters"], canonical_state=data.get("canonical_state"))
        elif cmd == "assembly-validate": result = validate_assembly_manifest(data)
        elif cmd == "editorial": result = validate_editorial_acceptance(data)
        elif cmd == "assemble": result = assemble(data, args.video, args.preview)
        else:
            client = ComfyClient(args.endpoint)
            if cmd == "discover": result = client.discover()
            elif cmd == "preflight": result = validate_workflow(load(args.workflow), client.discover()["object_info"])
            elif cmd == "bind": result = bind_workflow(load(args.workflow), load(args.bindings), client.discover()["object_info"])
            elif cmd == "submit": result = submit(client, load(args.workflow), load(args.context), args.destination, args.authorize_submit, args.probe)
            elif cmd == "poll": result = poll(client, args.prompt_id, args.timeout)
            elif cmd == "collect": result = collect(client, load(args.attempt), load(args.history), args.destination)
        if getattr(args, "output", None): save(args.output, result)
        else: print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        status = result.get("status") if isinstance(result, dict) else None
        if cmd == "prepare": status = result["validation"]["status"]
        exit_status = status
        if cmd == "accept" and result.get("accepted") is not True:
            exit_status = "BLOCKED"
        quality_gate_commands = {
            "aggregate", "scorecard", "transition", "semantic", "shot-acceptance", "contact", "dialogue", "audio",
            "causality", "ownership", "vehicle-state", "repair-validate", "long-form", "maturity",
            "adapter-diff", "assembly-validate", "editorial", "profile-check", "first-last-frame", "flf-suite",
            "flf-probe", "case-envelope", "media-qa",
        }
        non_accepting_quality_status = exit_status in (
            "FAIL", "FAILED", "BLOCKED", "UNKNOWN", "PARTIAL", "NOT_OBSERVED", "NOT_RUN",
            "EXPIRED", "DEGRADED", "UNSUPPORTED", "PROPOSED", "INFERRED", "NOT_APPLICABLE")
        if non_accepting_quality_status and getattr(args, "output", None):
            print(json.dumps({"status": status, "report": args.output, "next_action": "Inspect issues/gaps in the saved report; the output is not accepted"}), file=sys.stderr)
        return 2 if (exit_status in ("FAIL", "FAILED", "BLOCKED", "UNKNOWN") or
                      (cmd in quality_gate_commands and non_accepting_quality_status)) else 0
    except (ContractError, OSError, KeyError, TypeError, ValueError, AttributeError, IndexError) as exc:
        print(json.dumps({"status": "BLOCKED", "error": str(exc), "next_action": "Inspect the named contract or boundary; do not retry a submission blindly"}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
