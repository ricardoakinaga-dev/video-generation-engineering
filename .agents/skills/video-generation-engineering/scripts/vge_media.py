"""Local media inspection and explicit preview/final assembly using FFmpeg."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

from vge_core import ContractError, file_hash, hash_value, number, require, save
from vge_evidence import validate_observation
from vge_quality_common import aggregate_quality


def run(command, timeout=120):
    command = list(command)
    require(bool(command), "Media command must not be empty")
    if command[0] in ("ffmpeg", "ffprobe"):
        name = command[0]
        command[0] = os.environ.get("VGE_" + name.upper()) or shutil.which(name, path=os.defpath) or shutil.which(name) or name
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ContractError(f"Media tool failed: {type(exc).__name__}") from exc
    require(result.returncode == 0, f"Media tool exited {result.returncode}: {result.stderr[-1600:]}")
    return result.stdout


def probe(path):
    path = Path(path).resolve(strict=True)
    result = json.loads(run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)]))
    require(isinstance(result, dict) and isinstance(result.get("streams"), list) and isinstance(result.get("format"), dict), "ffprobe response is missing streams or format")
    require(all(isinstance(stream, dict) and isinstance(stream.get("codec_type"), str) for stream in result["streams"]), "ffprobe stream metadata is malformed")
    videos = [s for s in result["streams"] if s["codec_type"] == "video"]
    audios = [s for s in result["streams"] if s["codec_type"] == "audio"]
    fps = float(Fraction(videos[0].get("avg_frame_rate", "0/1"))) if videos else None
    return {"artifact_ref": str(path), "content_hash": file_hash(path), "observed_at": datetime.now(timezone.utc).isoformat(),
            "procedure": "ffprobe streams and format; SHA-256 of local bytes", "duration_s": float(result["format"].get("duration", 0)),
            "fps": fps, "video_streams": videos, "audio_streams": audios,
            "format": result["format"].get("format_name"), "status": "PARTIAL",
            "limitations": ["Metadata does not establish identity, lip-sync, contact, story or editorial quality"]}


def _capture(command, timeout=120):
    """Run a media inspection command without a shell and retain diagnostics."""
    command = list(command)
    require(bool(command), "Media command must not be empty")
    if command[0] in ("ffmpeg", "ffprobe"):
        name = command[0]
        command[0] = os.environ.get("VGE_" + name.upper()) or shutil.which(name, path=os.defpath) or shutil.which(name) or name
    try:
        result = subprocess.run(command, capture_output=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ContractError(f"Media tool failed: {type(exc).__name__}") from exc
    return result.returncode, result.stdout, result.stderr.decode("utf-8", errors="replace")[-8000:]


def _qa_evidence(path, content_hash, details):
    return [{"type": "MEDIA_BYTES", "ref": str(path), "content_hash": content_hash, "details": details}]


def _count_video_frames(path, timeout=180):
    """Count decoded video frames without trusting a container-only field."""
    code, stdout, _ = _capture(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
                                "-show_entries", "stream=nb_read_frames", "-of", "default=nw=1:nk=1", str(path)], timeout=timeout)
    if code != 0:
        return None
    try:
        value = int(stdout.decode("utf-8", errors="replace").strip().splitlines()[0])
    except (IndexError, TypeError, ValueError):
        return None
    return value if value > 0 else None


def media_qa(path, audio_required=False, allow_black=False, allow_freeze=False, timeout=180,
             expected_duration_s=None, expected_fps=None, expected_resolution=None,
             expected_frame_count=None, expected_codec=None, expected_container=None):
    """Run deterministic byte/metadata/decode heuristics against one media artifact.

    The result is intentionally limited: a PASS means the declared mechanical
    checks passed, never that the scene has correct identity, acting, physics,
    continuity, story or lip-sync.
    """
    path = Path(path).resolve(strict=True)
    content_hash = file_hash(path)
    checks = []
    limitations = [
        "Mechanical media QA cannot establish identity, emotion, physics, story, continuity or lip-sync",
        "Black/freeze detection is heuristic and must be interpreted against the declared creative intent",
    ]

    def check(check_id, category, result, question, details, reason=None):
        item = {"id": check_id, "category": category, "result": result,
                "oracle": {"kind": "METADATA" if category == "metadata" else "ALGORITHMIC", "question": question, "version": "ffmpeg-local"},
                "confidence": "HIGH" if result in ("PASS", "FAIL") else "UNKNOWN",
                "evidence": _qa_evidence(path, content_hash, details) if result in ("PASS", "FAIL", "PARTIAL") else [],
                "limitations": list(limitations)}
        if reason:
            item["reason"] = reason
        checks.append(item)

    if expected_duration_s is not None:
        require(number(expected_duration_s, True), "expected_duration_s must be positive")
    if expected_fps is not None:
        require(number(expected_fps, True), "expected_fps must be positive")
    if expected_resolution is not None:
        require(isinstance(expected_resolution, (list, tuple)) and len(expected_resolution) == 2
                and all(type(value) is int and value > 0 for value in expected_resolution),
                "expected_resolution must be [width, height]")
    if expected_frame_count is not None:
        require(type(expected_frame_count) is int and expected_frame_count > 0,
                "expected_frame_count must be positive")
    if expected_codec is not None:
        require(isinstance(expected_codec, str) and expected_codec, "expected_codec must be nonempty")
    if expected_container is not None:
        require(isinstance(expected_container, str) and expected_container, "expected_container must be nonempty")

    def unknown(check_id, category, question, reason):
        check(check_id, category, "NOT_OBSERVED", question, reason, reason)

    check("artifact_hash", "metadata", "PASS", "Are the exact artifact bytes bound by SHA-256?", {"sha256": content_hash})
    try:
        metadata = probe(path)
    except ContractError as exc:
        check("file_readable", "metadata", "FAIL", "Can the media file be read and parsed?", "ffprobe rejected the artifact", str(exc))
        check("decode_integrity", "metadata", "FAIL", "Can the container be parsed by ffprobe?", "ffprobe rejected the artifact", str(exc))
        for check_id, category, question in (
            ("duration", "metadata", "Does the artifact expose a positive duration?"),
            ("fps", "metadata", "Does the artifact expose a positive frame rate?"),
            ("resolution", "metadata", "Does the artifact expose positive video dimensions?"),
            ("frame_count", "metadata", "Can the decoded video frame count be observed?"),
            ("codec", "metadata", "Does the artifact expose a video codec?"),
            ("container", "metadata", "Does the artifact expose a container format?"),
            ("audio_stream", "audio", "Is the declared audio stream present?"),
            ("audio_duration", "audio", "Does the audio stream expose a positive duration?"),
            ("av_duration_mismatch", "audio", "Do audio and video durations align?"),
            ("black_frames", "visual", "Does the artifact avoid unintended black intervals?"),
            ("freeze_frames", "temporal", "Does the artifact avoid unintended frozen intervals?"),
        ):
            unknown(check_id, category, question, "Media metadata was unavailable")
        return {"schema_version": 1, "kind": "MEDIA_QA", "artifact_ref": str(path), "content_hash": content_hash,
                "observed_at": datetime.now(timezone.utc).isoformat(), "procedure": "SHA-256, ffprobe and bounded ffmpeg decode heuristics",
                "checks": checks, "frame_count": None, "status": "FAIL", "accepted": False, "limitations": limitations}

    video = metadata["video_streams"][0] if len(metadata["video_streams"]) == 1 else {}
    duration = metadata["duration_s"]
    fps = metadata["fps"]
    width, height = video.get("width", 0), video.get("height", 0)
    video_codec = video.get("codec_name")
    container = metadata.get("format")
    frame_count = _count_video_frames(path, timeout)
    valid_video = len(metadata["video_streams"]) == 1 and duration > 0 and fps and width > 0 and height > 0
    check("file_readable", "metadata", "PASS", "Can the media file be read and parsed?", "ffprobe parsed the artifact")
    check("metadata_integrity", "metadata", "PASS" if valid_video else "FAIL", "Does the artifact expose one positive-duration video stream with dimensions and FPS?", "ffprobe stream/format metadata")
    duration_ok = duration > 0 and (expected_duration_s is None or abs(duration - expected_duration_s) <= max(1 / (fps or 24), 0.05))
    check("duration", "metadata", "PASS" if duration_ok else "FAIL", "Does the artifact duration satisfy the declared contract?", {"observed_s": duration, "expected_s": expected_duration_s}, "Duration is missing or outside the declared tolerance" if not duration_ok else None)
    fps_ok = bool(fps) and (expected_fps is None or abs(fps - expected_fps) < 0.001)
    check("fps", "metadata", "PASS" if fps_ok else "FAIL", "Does the artifact FPS satisfy the declared contract?", {"observed": fps, "expected": expected_fps}, "FPS is missing or outside the declared contract" if not fps_ok else None)
    resolution_ok = width > 0 and height > 0 and (expected_resolution is None or (width, height) == tuple(expected_resolution))
    check("resolution", "metadata", "PASS" if resolution_ok else "FAIL", "Does the artifact resolution satisfy the declared contract?", {"observed": [width, height], "expected": expected_resolution}, "Resolution is missing or outside the declared contract" if not resolution_ok else None)
    frame_ok = frame_count is not None and (expected_frame_count is None or frame_count == expected_frame_count)
    check("frame_count", "metadata", "PASS" if frame_ok else "FAIL", "Does the decoded frame count satisfy the declared contract?", {"observed": frame_count, "expected": expected_frame_count}, "Frame count is unavailable or outside the declared contract" if not frame_ok else None)
    codec_ok = isinstance(video_codec, str) and bool(video_codec) and (expected_codec is None or video_codec == expected_codec)
    check("codec", "metadata", "PASS" if codec_ok else "FAIL", "Does the video codec satisfy the declared contract?", {"observed": video_codec, "expected": expected_codec}, "Video codec is missing or outside the declared contract" if not codec_ok else None)
    container_ok = isinstance(container, str) and bool(container) and (expected_container is None or expected_container in container.split(","))
    check("container", "metadata", "PASS" if container_ok else "FAIL", "Does the container satisfy the declared contract?", {"observed": container, "expected": expected_container}, "Container is missing or outside the declared contract" if not container_ok else None)
    if metadata["audio_streams"]:
        audio_duration = metadata["audio_streams"][0].get("duration")
        try:
            audio_duration = float(audio_duration) if audio_duration is not None else None
        except (TypeError, ValueError):
            audio_duration = None
        check("audio_stream", "audio", "PASS", "Is the declared audio stream present?", "ffprobe audio stream metadata")
        audio_ok = audio_duration is not None and audio_duration > 0
        check("audio_duration", "audio", "PASS" if audio_ok else "FAIL", "Does the audio stream expose a positive duration?", {"observed_s": audio_duration}, "Audio duration is missing or non-positive" if not audio_ok else None)
        aligned = audio_duration is not None and abs(audio_duration - duration) <= max(1 / (fps or 24), 0.05)
        check("audio_video_alignment", "audio", "PASS" if aligned else "FAIL", "Do declared audio and container durations align within one frame?", "ffprobe audio/video duration comparison", "Audio/video durations are misaligned" if not aligned else None)
        check("av_duration_mismatch", "audio", "PASS" if aligned else "FAIL", "Do audio and video durations align within one frame?", "ffprobe audio/video duration comparison", "Audio/video durations are misaligned" if not aligned else None)
    else:
        absence = "Audio stream is absent" if not audio_required else "Audio was required but no stream was observed"
        result = "NOT_APPLICABLE" if not audio_required else "NOT_OBSERVED"
        check("audio_stream", "audio", result, "Is the declared audio stream present?", "No audio stream", absence)
        check("audio_duration", "audio", result, "Does the audio stream expose a positive duration?", "No audio stream", absence)
        check("audio_video_alignment", "audio", result, "Is required audio present and aligned?", "No audio stream", absence)
        check("av_duration_mismatch", "audio", result, "Do audio and video durations align within one frame?", "No audio stream", absence)

    # pix_th is a normalized luma threshold, not a percentage of black pixels.
    # 0.10 catches genuinely near-black frames without classifying ordinary SDR
    # material as black (0.98 would make almost every frame a false positive).
    filter_graph = "blackdetect=d=0.5:pix_th=0.10,freezedetect=n=0.003:d=1"
    code, _, diagnostics = _capture(["ffmpeg", "-nostdin", "-v", "info", "-i", str(path), "-vf", filter_graph, "-an", "-f", "null", "-"], timeout=timeout)
    decoded = code == 0
    check("decode_integrity", "temporal", "PASS" if decoded else "FAIL", "Can bounded ffmpeg decoding traverse the video?", "ffmpeg null decode" if decoded else diagnostics, None if decoded else "ffmpeg decode failed")
    black_found = "black_start:" in diagnostics or "black_end:" in diagnostics
    freeze_found = "freeze_start:" in diagnostics or "freeze_end:" in diagnostics
    check("black_content", "visual", "PASS" if allow_black or not black_found else "FAIL", "Does the artifact avoid unintended black intervals?", "blackdetect output", None if allow_black or not black_found else "blackdetect reported a black interval")
    check("black_frames", "visual", "PASS" if allow_black or not black_found else "FAIL", "Does the artifact avoid unintended black frames?", "blackdetect output", None if allow_black or not black_found else "blackdetect reported a black interval")
    check("frozen_content", "temporal", "PASS" if allow_freeze or not freeze_found else "FAIL", "Does the artifact avoid unintended frozen intervals?", "freezedetect output", None if allow_freeze or not freeze_found else "freezedetect reported a frozen interval")
    check("freeze_frames", "temporal", "PASS" if allow_freeze or not freeze_found else "FAIL", "Does the artifact avoid unintended freeze frames?", "freezedetect output", None if allow_freeze or not freeze_found else "freezedetect reported a frozen interval")
    status = aggregate_quality([{"result": item["result"]} for item in checks])
    return {"schema_version": 1, "kind": "MEDIA_QA", "artifact_ref": str(path), "content_hash": content_hash,
            "observed_at": datetime.now(timezone.utc).isoformat(), "procedure": "SHA-256, ffprobe and bounded ffmpeg decode heuristics",
            "checks": checks, "frame_count": frame_count, "status": status, "accepted": status == "PASS", "limitations": limitations}


def trim(path, output, duration_s):
    """Create a new, hashable derived segment with an explicit duration trim."""
    source = Path(path).resolve(strict=True)
    output = Path(output).resolve()
    require(number(duration_s, True) and duration_s > 0, "Trim duration must be positive")
    require(not output.exists(), "Trim output exists; use a new revision")
    source_probe = probe(source)
    require(source_probe["video_streams"] and source_probe["duration_s"] > 0, "Trim source must contain a video")
    require(duration_s <= source_probe["duration_s"] + 1 / max(source_probe.get("fps") or 24, 1) + 0.02,
            "Trim duration cannot exceed the source duration")
    output.parent.mkdir(parents=True, exist_ok=True)
    run(["ffmpeg", "-nostdin", "-v", "error", "-n", "-i", str(source), "-t", str(duration_s),
         "-map", "0:v:0", "-map", "0:a:0?", "-c:v", "libx264", "-crf", "18",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-movflags", "+faststart", str(output)], timeout=300)
    actual = probe(output)
    fps = source_probe.get("fps") or actual.get("fps") or 24
    require(abs(actual["duration_s"] - duration_s) <= 1 / fps + 0.08, "Trimmed duration failed validation")
    require(actual.get("fps") is not None and abs(actual["fps"] - fps) < 0.001, "Trimmed FPS differs from source")
    require(len(actual["video_streams"]) == 1, "Trimmed output must contain exactly one video stream")
    require(bool(actual["audio_streams"]) == bool(source_probe["audio_streams"]), "Trim changed the declared audio presence")
    return {"schema_version": 1, "kind": "TRIMMED_MEDIA", "source": source_probe,
            "artifact": actual, "target_duration_s": duration_s,
            "procedure": "Explicit ffmpeg duration trim with H.264/AAC remux and post-trim ffprobe validation",
            "status": "PASS", "accepted": True,
            "limitations": ["Derived media preserves source bytes only by lineage; it does not add semantic or editorial acceptance."]}


def validate_assembly_manifest(manifest, inspections=None, final_artifact=None):
    """Validate ordered shot lineage before and after a mechanical assembly."""
    require(isinstance(manifest, dict), "Assembly manifest must be an object")
    require(manifest.get("schema_version") == 1, "Unsupported assembly schema")
    require(isinstance(manifest.get("id"), str) and manifest["id"], "Assembly manifest needs id")
    segments = manifest.get("segments")
    require(isinstance(segments, list) and bool(segments), "Assembly requires segments")
    shot_order = manifest.get("shot_order")
    require(isinstance(shot_order, list) and shot_order, "Assembly manifest needs explicit shot_order")
    require(all(isinstance(shot_id, str) and shot_id for shot_id in shot_order),
            "Assembly shot_order must contain nonempty shot ids")
    require(len(shot_order) == len(set(shot_order)), "Assembly shot_order contains duplicated shots")
    require(len(shot_order) == len(segments), "Assembly shot_order and segments differ")
    require(number(manifest.get("fps"), True), "Assembly manifest needs positive fps")
    require(number(manifest.get("target_duration_s"), True), "Assembly manifest needs positive target_duration_s")

    seen = set()
    artifact_ids = set()
    for index, segment in enumerate(segments):
        label = f"assembly.segments[{index}]"
        require(isinstance(segment, dict), f"{label} must be an object")
        shot_id = segment.get("shot_id")
        require(isinstance(shot_id, str) and shot_id, f"{label}.shot_id is required")
        require(shot_id not in seen, f"Duplicate assembly shot: {shot_id}")
        seen.add(shot_id)
        require(shot_id == shot_order[index], f"{label}.shot_id is out of explicit shot order")
        artifact = segment.get("artifact")
        require(isinstance(artifact, dict), f"{label}.artifact is required")
        require(isinstance(artifact.get("id"), str) and artifact["id"], f"{label}.artifact.id is required")
        require(artifact["id"] not in artifact_ids, f"Duplicate assembly artifact: {artifact['id']}")
        artifact_ids.add(artifact["id"])
        require(isinstance(artifact.get("artifact_ref"), str) and artifact["artifact_ref"], f"{label}.artifact.artifact_ref is required")
        require(hash_value(artifact.get("content_hash")), f"{label}.artifact.content_hash must be SHA-256")
        require(Path(artifact["artifact_ref"]).is_file(), f"{label}.artifact bytes are unavailable")
        require(file_hash(artifact["artifact_ref"]) == artifact["content_hash"],
                f"{label}.artifact changed since manifest")
        require(number(segment.get("duration_s"), True), f"{label}.duration_s is required")
        require(number(segment.get("fps"), True), f"{label}.fps is required")
        resolution = segment.get("resolution")
        require(isinstance(resolution, dict) and type(resolution.get("width")) is int and resolution["width"] > 0
                and type(resolution.get("height")) is int and resolution["height"] > 0,
                f"{label}.resolution must contain positive width and height")
        require("audio_source" in segment, f"{label}.audio_source is required")
        audio_source = segment["audio_source"]
        if isinstance(audio_source, dict):
            require(isinstance(audio_source.get("ref"), str) and audio_source["ref"],
                    f"{label}.audio_source.ref is required")
            require(hash_value(audio_source.get("content_hash")),
                    f"{label}.audio_source.content_hash must be SHA-256")
            require(Path(audio_source["ref"]).is_file(), f"{label}.audio_source bytes are unavailable")
            require(file_hash(audio_source["ref"]) == audio_source["content_hash"],
                    f"{label}.audio_source changed since manifest")
        else:
            require(isinstance(audio_source, str) and audio_source,
                    f"{label}.audio_source must be a locator, MASTER_TRACK or NONE")
            if audio_source == "MASTER_TRACK":
                require(isinstance(manifest.get("audio_path"), str) and manifest["audio_path"],
                        "MASTER_TRACK requires manifest.audio_path")
        require("transition" in segment, f"{label}.transition is required")
        transition = segment["transition"]
        if isinstance(transition, dict):
            status = transition.get("status", "DECLARED")
            require(isinstance(status, str) and status, f"{label}.transition.status is required")
            if status not in ("NONE", "NOT_APPLICABLE", "END"):
                require(number(transition.get("start_s"), False) and number(transition.get("end_s"), False),
                        f"{label}.transition needs start_s/end_s")
                require(transition["start_s"] >= 0 and transition["end_s"] <= segment["duration_s"],
                        f"{label}.transition timing exceeds the segment")
                require(transition["end_s"] >= transition["start_s"],
                        f"{label}.transition timing is reversed")
        else:
            require(isinstance(transition, str) and transition, f"{label}.transition must be explicit")
        source_attempt = segment.get("source_attempt")
        require(isinstance(source_attempt, dict) and isinstance(source_attempt.get("id"), str) and source_attempt["id"],
                f"{label}.source_attempt.id is required")
        if isinstance(segment.get("attempt"), dict) and isinstance(segment["attempt"].get("id"), str):
            require(source_attempt["id"] == segment["attempt"]["id"],
                    f"{label}.source_attempt is not bound to attempt")
        repair_lineage = segment.get("repair_lineage")
        require(isinstance(repair_lineage, list), f"{label}.repair_lineage must be an array")
        for lineage_index, lineage in enumerate(repair_lineage):
            require((isinstance(lineage, str) and lineage) or
                    (isinstance(lineage, dict) and isinstance(lineage.get("id"), str) and lineage["id"]),
                    f"{label}.repair_lineage[{lineage_index}] needs an id")
        if isinstance(segment.get("shot"), dict):
            require(segment["shot"].get("id") == shot_id, f"{label}.shot is not bound to shot_id")

    require(seen == set(shot_order), "Assembly shot order does not cover exactly the declared shots")
    if inspections is not None:
        require(isinstance(inspections, list) and len(inspections) == len(segments),
                "Assembly inspections must cover every segment")
        for index, (segment, inspection) in enumerate(zip(segments, inspections)):
            video = inspection.get("video_streams", [{}])[0] if isinstance(inspection, dict) and inspection.get("video_streams") else {}
            observed_resolution = (video.get("width"), video.get("height"))
            declared_resolution = (segment["resolution"]["width"], segment["resolution"]["height"])
            require(observed_resolution == declared_resolution,
                    f"assembly.segments[{index}] resolution does not match artifact")
            require(abs(inspection.get("fps", 0) - segment["fps"]) < 0.001,
                    f"assembly.segments[{index}] fps does not match artifact")
            require(abs(inspection.get("duration_s", 0) - segment["duration_s"]) <= max(1 / segment["fps"], 0.05),
                    f"assembly.segments[{index}] duration does not match artifact")
    if final_artifact is not None:
        require(isinstance(final_artifact, dict), "Final assembly artifact must be an object")
        require(isinstance(final_artifact.get("artifact_ref"), str) and final_artifact["artifact_ref"],
                "Final assembly artifact needs artifact_ref")
        require(hash_value(final_artifact.get("content_hash")),
                "Final assembly artifact content_hash must be SHA-256")
        require(Path(final_artifact["artifact_ref"]).is_file(), "Final assembly artifact bytes are unavailable")
        require(file_hash(final_artifact["artifact_ref"]) == final_artifact["content_hash"],
                "Final assembly artifact changed before binding")
        expected_sources = [{"shot_id": segment["shot_id"], "artifact_id": segment["artifact"]["id"],
                            "content_hash": segment["artifact"]["content_hash"]} for segment in segments]
        require(final_artifact.get("source_shots") == expected_sources,
                "Final assembly artifact is not bound to every ordered source shot hash")
    return {"status": "PASS", "accepted": True, "shot_count": len(segments),
            "shot_order": list(shot_order), "final_artifact_bound": final_artifact is not None}


def assemble(manifest, output, preview=False):
    """Require uniform decoded formats; never silently convert a delivery decision."""
    validate_assembly_manifest(manifest)
    segments = manifest["segments"]
    output = Path(output).resolve()
    require(output.suffix.lower() == ".mp4", "This encoder supports explicit MP4 delivery")
    require(not output.exists(), "Output exists; use a new revision")
    require(not Path(str(output)+".manifest.json").exists(), "Output manifest exists; use a new revision")
    inspections = []
    for segment in segments:
        require(isinstance(segment, dict) and isinstance(segment.get("artifact"), dict), "Each assembly segment needs an artifact object")
        artifact = segment["artifact"]
        require(isinstance(artifact.get("id"), str) and artifact["id"] and isinstance(artifact.get("artifact_ref"), str) and artifact["artifact_ref"], "Segment artifact needs id and artifact_ref")
        require(isinstance(artifact.get("content_hash"), str) and artifact["content_hash"], "Segment artifact needs content_hash")
        require(file_hash(artifact["artifact_ref"]) == artifact["content_hash"], "Segment changed since collection")
        if not preview:
            require(isinstance(segment.get("shot"), dict), "Final assembly needs the canonical shot contract per segment")
            result = validate_observation(segment["observation"], artifact, segment["attempt"], segment["shot"])
            require(result["accepted"], "Final assembly requires accepted segment observations")
        inspection = probe(artifact["artifact_ref"])
        require(len(inspection["video_streams"]) == 1, "Exactly one video stream required per segment")
        inspections.append(inspection)
    validate_assembly_manifest(manifest, inspections=inspections)
    first = inspections[0]
    fmt = lambda p: (p["video_streams"][0]["width"], p["video_streams"][0]["height"], p["fps"])
    require(all(fmt(p) == fmt(first) for p in inspections), "Resolve width/height/FPS differences before assembly")
    fps = manifest.get("fps")
    require(number(fps, True) and abs(fps-first["fps"]) < 0.001, "Manifest FPS does not match segments")
    duration = sum(p["duration_s"] for p in inspections)
    target = manifest.get("target_duration_s")
    require(number(target, True) and abs(duration-target) <= len(segments)/fps + 0.02, "Segment duration does not match target")
    audio = manifest.get("audio_path")
    if audio:
        require(isinstance(audio, str) and audio, "audio_path must be a nonempty path")
        sound = probe(audio)
        require(sound["audio_streams"], "Audio track has no audio stream")
        require(abs(sound["duration_s"]-target) <= 1/fps + 0.05, "Audio duration does not align; trim/pad explicitly before mux")
    else:
        has_audio = [bool(p["audio_streams"]) for p in inspections]
        require(not any(has_audio) or all(has_audio), "Mixed silent/audio segments require an explicit continuous audio track")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="vge-assembly-", dir=output.parent) as tmp:
        tmp = Path(tmp)
        # Neutral symlink names avoid concat quoting/injection issues in user filenames.
        entries = []
        for i, segment in enumerate(segments):
            name = f"segment_{i:04d}.mp4"
            (tmp / name).symlink_to(Path(segment["artifact"]["artifact_ref"]).resolve())
            entries.append(f"file '{name}'")
        (tmp / "inputs.txt").write_text("\n".join(entries)+"\n")
        staged = tmp / "assembled.mp4"
        command = ["ffmpeg", "-nostdin", "-v", "error", "-n", "-f", "concat", "-safe", "1", "-i", str(tmp/"inputs.txt")]
        if audio:
            command += ["-i", str(Path(audio).resolve()), "-map", "0:v:0", "-map", "1:a:0"]
        else:
            command += ["-map", "0:v:0", "-map", "0:a:0?"]
        command += ["-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-t", str(target), "-movflags", "+faststart", str(staged)]
        run(command, timeout=300)
        actual = probe(staged)
        require(abs(actual["duration_s"]-target) <= len(segments)/fps+0.08, "Encoded output duration failed validation")
        require(abs(actual["fps"]-fps) < 0.001, "Encoded FPS differs")
        require(actual["video_streams"][0]["codec_name"] == "h264", "Unexpected video codec")
        require((not audio and not any(bool(p["audio_streams"]) for p in inspections)) or actual["audio_streams"], "Assembly lost required segment or mux audio")
        # Hard-link is exclusive, same filesystem, and leaves no partial final pathname.
        os.link(staged, output)
    actual["artifact_ref"] = str(output)
    final_binding = {"artifact_ref": str(output), "content_hash": actual["content_hash"],
                     "source_shots": [{"shot_id": s["shot_id"], "artifact_id": s["artifact"]["id"],
                                       "content_hash": s["artifact"]["content_hash"]} for s in segments]}
    validate_assembly_manifest(manifest, inspections=inspections, final_artifact=final_binding)
    result = {"schema_version": 1, "id": manifest["id"], "shot_order": list(manifest["shot_order"]),
              "kind": "PREVIEW" if preview else "ASSEMBLY_AWAITING_EDITORIAL_REVIEW", "artifact": actual,
              "segments": [{"shot_id": s["shot_id"], "artifact_id": s["artifact"]["id"],
                            "artifact_ref": s["artifact"]["artifact_ref"], "content_hash": s["artifact"]["content_hash"],
                            "duration_s": s["duration_s"], "fps": s["fps"], "resolution": s["resolution"],
                            "audio_source": s["audio_source"], "transition": s["transition"],
                            "source_attempt": s["source_attempt"], "repair_lineage": s["repair_lineage"]} for s in segments],
              "source_artifacts": [{"id": s["artifact"]["id"], "shot_id": s["shot_id"], "content_hash": s["artifact"]["content_hash"]} for s in segments],
              "final_artifact_binding": final_binding,
              "audio": {"path": str(Path(audio).resolve()), "content_hash": file_hash(audio)} if audio else None,
              "mechanical_status": "PASS", "technical_acceptance": "PASS", "semantic_acceptance": "NOT_RUN",
              "generation_acceptance": "NOT_RUN" if preview else "SEGMENTS_ACCEPTED", "editorial_acceptance": "NOT_RUN"}
    save(str(output)+".manifest.json", result)
    return result


def contact_sheet(path, output, frames=8):
    require(type(frames) is int and 1 <= frames <= 32, "Contact sheet frames must be 1..32")
    metadata = probe(path)
    require(metadata["video_streams"] and metadata["duration_s"] > 0, "Contact sheet needs a video")
    require(not Path(output).exists(), "Contact sheet exists")
    run(["ffmpeg", "-nostdin", "-v", "error", "-n", "-i", str(Path(path).resolve()), "-vf",
         f"fps={frames/metadata['duration_s']},scale=320:-1,tile=4x{(frames+3)//4}", "-frames:v", "1", str(Path(output).resolve())])
    return {"source_hash": metadata["content_hash"], "contact_sheet": str(Path(output).resolve()), "requested_frames": frames,
            "limitation": "Sparse samples support review; they do not prove temporal or lip-sync quality"}
