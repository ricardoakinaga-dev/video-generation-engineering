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

from vge_core import ContractError, file_hash, number, require, save
from vge_evidence import validate_observation
from vge_quality import aggregate_quality


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


def media_qa(path, audio_required=False, allow_black=False, allow_freeze=False, timeout=180):
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

    try:
        metadata = probe(path)
    except ContractError as exc:
        check("decode_integrity", "metadata", "FAIL", "Can the container be parsed by ffprobe?", "ffprobe rejected the artifact", str(exc))
        return {"schema_version": 1, "kind": "MEDIA_QA", "artifact_ref": str(path), "content_hash": content_hash,
                "observed_at": datetime.now(timezone.utc).isoformat(), "procedure": "SHA-256, ffprobe and bounded ffmpeg decode heuristics",
                "checks": checks, "status": "FAIL", "accepted": False, "limitations": limitations}

    valid_video = len(metadata["video_streams"]) == 1 and metadata["duration_s"] > 0 and metadata["fps"] and metadata["video_streams"][0].get("width", 0) > 0 and metadata["video_streams"][0].get("height", 0) > 0
    check("metadata_integrity", "metadata", "PASS" if valid_video else "FAIL", "Does the artifact expose one positive-duration video stream with dimensions and FPS?", "ffprobe stream/format metadata")
    if metadata["audio_streams"]:
        audio_duration = metadata["audio_streams"][0].get("duration")
        try:
            audio_duration = float(audio_duration) if audio_duration is not None else metadata["duration_s"]
        except (TypeError, ValueError):
            audio_duration = None
        aligned = audio_duration is not None and abs(audio_duration - metadata["duration_s"]) <= max(1 / (metadata["fps"] or 24), 0.05)
        check("audio_video_alignment", "audio", "PASS" if aligned else "FAIL", "Do declared audio and container durations align within one frame?", "ffprobe audio/video duration comparison")
    else:
        check("audio_video_alignment", "audio", "NOT_APPLICABLE" if not audio_required else "NOT_OBSERVED", "Is required audio present and aligned?", "No audio stream", "Audio stream is absent" if not audio_required else "Audio was required but no stream was observed")

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
    check("frozen_content", "temporal", "PASS" if allow_freeze or not freeze_found else "FAIL", "Does the artifact avoid unintended frozen intervals?", "freezedetect output", None if allow_freeze or not freeze_found else "freezedetect reported a frozen interval")
    status = aggregate_quality([{"result": item["result"]} for item in checks])
    return {"schema_version": 1, "kind": "MEDIA_QA", "artifact_ref": str(path), "content_hash": content_hash,
            "observed_at": datetime.now(timezone.utc).isoformat(), "procedure": "SHA-256, ffprobe and bounded ffmpeg decode heuristics",
            "checks": checks, "status": status, "accepted": status == "PASS", "limitations": limitations}


def assemble(manifest, output, preview=False):
    """Require uniform decoded formats; never silently convert a delivery decision."""
    require(isinstance(manifest, dict), "Assembly manifest must be an object")
    require(manifest.get("schema_version") == 1, "Unsupported assembly schema")
    segments = manifest.get("segments", [])
    require(bool(segments), "Assembly requires segments")
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
        command += ["-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-movflags", "+faststart", str(staged)]
        run(command, timeout=300)
        actual = probe(staged)
        require(abs(actual["duration_s"]-target) <= len(segments)/fps+0.08, "Encoded output duration failed validation")
        require(abs(actual["fps"]-fps) < 0.001, "Encoded FPS differs")
        require(actual["video_streams"][0]["codec_name"] == "h264", "Unexpected video codec")
        require((not audio and not any(bool(p["audio_streams"]) for p in inspections)) or actual["audio_streams"], "Assembly lost required segment or mux audio")
        # Hard-link is exclusive, same filesystem, and leaves no partial final pathname.
        os.link(staged, output)
    actual["artifact_ref"] = str(output)
    result = {"schema_version": 1, "kind": "PREVIEW" if preview else "ASSEMBLY_AWAITING_EDITORIAL_REVIEW", "artifact": actual,
              "source_artifacts": [{"id": s["artifact"]["id"], "content_hash": s["artifact"]["content_hash"]} for s in segments],
              "audio": {"path": str(Path(audio).resolve()), "content_hash": file_hash(audio)} if audio else None,
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
