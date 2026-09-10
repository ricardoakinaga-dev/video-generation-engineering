"""Capture hash-bound frame and audio evidence from an existing local artifact.

Capture is an evidence-acquisition step, not a semantic oracle. The returned
records retain the source locator/hash and are intentionally not marked PASS;
an appropriate visual/audio/human observation must still judge them.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from vge_core import file_hash, number, require
from vge_media import probe, run


def _source(path):
    source = Path(path).resolve(strict=True)
    require(source.is_file(), "Evidence source must be a regular file")
    metadata = probe(source)
    require(metadata.get("duration_s", 0) > 0, "Evidence source must have a positive duration")
    return source, metadata, file_hash(source)


def _output(path):
    target = Path(path).resolve()
    require(not target.exists(), "Evidence output exists; use a new revision")
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def _time(value, label):
    require(number(value) and value >= 0, f"{label} must be nonnegative")
    return float(value)


def _stream_snapshot(stream, fields):
    return {field: stream.get(field) for field in fields if field in stream}


def capture_frame(source_path, time_s, output_path):
    """Extract one timestamped frame and return a derived evidence item."""
    source, metadata, source_hash = _source(source_path)
    require(metadata.get("video_streams"), "Frame evidence requires a video stream")
    time_s = _time(time_s, "frame timestamp")
    require(time_s < metadata["duration_s"], "Frame timestamp must be before source duration")
    output = _output(output_path)
    run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(source), "-ss", f"{time_s:.6f}",
         "-frames:v", "1", "-an", "-c:v", "png", "-f", "image2", "-n", str(output)], timeout=180)
    require(output.is_file() and output.stat().st_size > 0, "Frame capture produced no bytes")
    derived = probe(output)
    return {
        "type": "FRAME", "ref": str(output), "content_hash": file_hash(output), "time_s": time_s,
        "source_ref": str(source), "source_content_hash": source_hash,
        "source_video_stream": _stream_snapshot(metadata["video_streams"][0],
                                                 ("index", "codec_name", "width", "height", "pix_fmt", "avg_frame_rate", "time_base")),
        "derived_media": _stream_snapshot(derived.get("video_streams", [{}])[0],
                                           ("codec_name", "width", "height", "pix_fmt")),
        "capture_procedure": "ffmpeg accurate seek after input decode; one PNG frame; SHA-256 source and derived bytes",
        "captured_at": datetime.now(timezone.utc).isoformat(), "status": "CAPTURED",
        "oracle": {"kind": "FRAME", "question": "Which pixels are present at the declared timestamp?", "version": "ffmpeg-local-capture"},
        "limitations": ["Capture proves byte acquisition and timestamp request only; it does not judge identity, physics, continuity or editorial quality"],
    }


def capture_audio_window(source_path, start_s, duration_s, output_path):
    """Extract one bounded PCM audio window and return derived evidence."""
    source, metadata, source_hash = _source(source_path)
    start_s = _time(start_s, "audio window start")
    duration_s = _time(duration_s, "audio window duration")
    require(duration_s > 0, "Audio window duration must be positive")
    require(start_s + duration_s <= metadata["duration_s"] + 0.02, "Audio window exceeds source duration")
    require(metadata.get("audio_streams"), "Audio evidence requires an audio stream")
    output = _output(output_path)
    run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(source), "-ss", f"{start_s:.6f}",
         "-t", f"{duration_s:.6f}", "-map", "0:a:0", "-vn", "-c:a", "pcm_s16le",
         "-ar", "48000", "-ac", "2", "-f", "wav", "-n", str(output)], timeout=180)
    require(output.is_file() and output.stat().st_size > 44, "Audio capture produced no PCM bytes")
    derived = probe(output)
    return {
        "type": "AUDIO_WINDOW", "ref": str(output), "content_hash": file_hash(output),
        "time_s": start_s, "duration_s": duration_s,
        "source_ref": str(source), "source_content_hash": source_hash,
        "source_audio_stream": _stream_snapshot(metadata["audio_streams"][0],
                                                 ("index", "codec_name", "sample_rate", "channels", "channel_layout", "time_base", "duration")),
        "derived_audio_stream": _stream_snapshot(derived.get("audio_streams", [{}])[0],
                                                  ("codec_name", "sample_rate", "channels", "channel_layout", "duration")),
        "capture_procedure": "ffmpeg bounded audio extraction to stereo 48 kHz PCM WAV; SHA-256 source and derived bytes",
        "captured_at": datetime.now(timezone.utc).isoformat(), "status": "CAPTURED",
        "oracle": {"kind": "AUDIO", "question": "What audio signal is present in the declared window?", "version": "ffmpeg-local-capture"},
        "limitations": ["Capture proves byte acquisition and timing window only; it does not judge intelligibility, speaker identity, mix, causality or lip-sync"],
    }


def capture_evidence(source_path, output_dir, frame_times=None, audio_windows=None):
    """Capture a non-empty evidence set into a new directory without overwrite."""
    frame_times = [] if frame_times is None else list(frame_times)
    audio_windows = [] if audio_windows is None else list(audio_windows)
    require(frame_times or audio_windows, "Capture requires at least one frame or audio window")
    source, metadata, source_hash = _source(source_path)
    output_root = Path(output_dir).resolve()
    require(not output_root.exists(), "Evidence output directory exists; use a new revision")
    output_root.mkdir(parents=True, exist_ok=True)
    frames = [capture_frame(source, value, output_root / f"frame-{index:03d}.png")
              for index, value in enumerate(frame_times)]
    audio = []
    for index, window in enumerate(audio_windows):
        require(isinstance(window, (list, tuple)) and len(window) == 2, "Audio windows must be [start_s, duration_s]")
        audio.append(capture_audio_window(source, window[0], window[1], output_root / f"audio-{index:03d}.wav"))
    return {
        "schema_version": 1, "kind": "MEDIA_EVIDENCE_CAPTURE", "source_ref": str(source),
        "source_content_hash": source_hash, "source_duration_s": metadata["duration_s"],
        "source_media_metadata": {"format": metadata.get("format"), "fps": metadata.get("fps"),
                                  "video_streams": metadata.get("video_streams", []),
                                  "audio_streams": metadata.get("audio_streams", [])},
        "frames": frames, "audio_windows": audio,
        "captured_at": datetime.now(timezone.utc).isoformat(), "status": "CAPTURED",
        "semantic_acceptance": "NOT_RUN",
        "procedure": "Hash-bound local frame/audio extraction with immutable new output paths",
        "limitations": ["This record is acquisition evidence only; semantic and human acceptance must reference these exact bytes with claim-appropriate oracles"],
    }
