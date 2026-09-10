#!/usr/bin/env python3
"""Build and audit a deterministic, portable Skill distribution candidate.

The audit is intentionally offline: it never queues generation, downloads a
model, calls a provider, or mutates a runtime.  It proves package integrity
and structural portability only; audiovisual claims remain separately gated.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents/skills/video-generation-engineering"
EXCLUDED_PARTS = {"__pycache__", ".git"}
BANNED_SUFFIXES = {".ckpt", ".pt", ".pth", ".bin", ".onnx", ".safetensors", ".gguf", ".ggml"}
PRIVATE_MEDIA_SUFFIXES = {".mp4", ".mov", ".mkv", ".webm", ".gif", ".wav", ".mp3", ".flac", ".png", ".jpg", ".jpeg"}
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)\b(?:aws_access_key_id|aws_secret_access_key|api[_-]?key|access[_-]?token|client_secret)\s*[:=]\s*['\"]?[A-Za-z0-9_./+:-]{12,}"),
    re.compile(r"(?i)\b(?:sk|key|token|secret)_[A-Za-z0-9]{20,}\b"),
)


def sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def file_hash(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def package_files() -> list[Path]:
    if not SKILL.is_dir():
        raise RuntimeError(f"Skill root is unavailable: {SKILL}")
    result = []
    for path in sorted(SKILL.rglob("*")):
        if not path.is_file() or any(part in EXCLUDED_PARTS for part in path.parts) or path.suffix == ".pyc":
            continue
        result.append(path)
    return result


def relative_name(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def scan_package(paths: list[Path]) -> list[str]:
    errors = []
    workspace_markers = (str(ROOT), str(Path.home()))
    for path in paths:
        rel = relative_name(path)
        if path.is_symlink():
            errors.append(f"symlink is not portable: {rel}")
        if Path(rel).is_absolute() or ".." in Path(rel).parts:
            errors.append(f"unsafe archive path: {rel}")
        if path.suffix.lower() in BANNED_SUFFIXES:
            errors.append(f"model-weight file in package: {rel}")
        if path.suffix.lower() in PRIVATE_MEDIA_SUFFIXES:
            errors.append(f"private/generated media in package: {rel}")
        try:
            data = path.read_bytes()
            text = data.decode("utf-8", errors="ignore")
        except OSError as exc:
            errors.append(f"unreadable package file {rel}: {exc}")
            continue
        for marker in workspace_markers:
            if marker and marker in text:
                errors.append(f"absolute local path in package: {rel}")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                errors.append(f"secret-like value in package: {rel}")
                break
    return sorted(set(errors))


def manifest(paths: list[Path]) -> dict[str, str]:
    return {relative_name(path): file_hash(path) for path in paths}


def manifest_digest(records: dict[str, str]) -> str:
    return sha256_bytes(json.dumps(records, sort_keys=True, separators=(",", ":")).encode())


def _zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    return info


def build_archive(output: Path, paths: list[Path]) -> dict:
    if output.exists():
        output.unlink()
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in paths:
            name = relative_name(path)
            archive.writestr(_zip_info(name), path.read_bytes())
    return {"path": str(output.relative_to(ROOT)) if output.is_relative_to(ROOT) else str(output),
            "sha256": file_hash(output), "bytes": output.stat().st_size,
            "entry_count": len(paths), "file_count": len(paths)}


def verify_archive(archive_path: Path, records: dict[str, str]) -> dict:
    errors = []
    with zipfile.ZipFile(archive_path) as archive:
        entries = archive.infolist()
        names = [entry.filename for entry in entries]
        if names != sorted(names):
            errors.append("archive entries are not sorted")
        if len(names) != len(set(names)):
            errors.append("archive contains duplicate entries")
        for entry in entries:
            path = Path(entry.filename)
            if path.is_absolute() or ".." in path.parts:
                errors.append(f"unsafe archive entry: {entry.filename}")
            if entry.filename not in records:
                errors.append(f"archive entry is outside package manifest: {entry.filename}")
            if entry.filename.endswith("/") or (entry.external_attr >> 16) & 0o170000 == 0o120000:
                errors.append(f"non-regular archive entry: {entry.filename}")
            if entry.date_time != (1980, 1, 1, 0, 0, 0):
                errors.append(f"non-deterministic timestamp: {entry.filename}")
            if sha256_bytes(archive.read(entry)) != records.get(entry.filename):
                errors.append(f"archive content differs from manifest: {entry.filename}")
        if archive.testzip() is not None:
            errors.append("CRC test failed")
    return {"status": "PASS" if not errors else "FAIL", "errors": sorted(set(errors)),
            "unsafe_paths": "PASS" if not any("unsafe" in item for item in errors) else "FAIL",
            "crc_test": "PASS" if "CRC test failed" not in errors else "FAIL"}


def run_external_smoke(archive_path: Path) -> dict:
    with tempfile.TemporaryDirectory(prefix="vge-release-audit-") as raw:
        root = Path(raw)
        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(root)
        cli = root / ".agents/skills/video-generation-engineering/scripts/vge.py"
        template = root / ".agents/skills/video-generation-engineering/assets/templates/treatment.json"
        prepared = root / "prepared.json"
        checks = []
        commands = [
            [sys.executable, str(cli), "--help"],
            [sys.executable, str(cli), "prepare", str(template), "--output", str(prepared)],
            [sys.executable, str(cli), "validate", str(prepared)],
            [sys.executable, str(cli), "compile", str(prepared)],
        ]
        for command in commands:
            completed = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=60)
            checks.append({"command": " ".join(command), "returncode": completed.returncode,
                           "status": "PASS" if completed.returncode == 0 else "FAIL",
                           "stderr": completed.stderr[-1000:]})
        return {"status": "PASS" if all(item["status"] == "PASS" for item in checks) else "FAIL",
                "working_directory": "temporary directory outside repository", "checks": checks}


def run_compileall() -> dict:
    with tempfile.TemporaryDirectory(prefix="vge-release-compile-") as raw:
        env = dict(**__import__("os").environ)
        env["PYTHONPYCACHEPREFIX"] = str(Path(raw) / "pycache")
        completed = subprocess.run([sys.executable, "-m", "compileall", "-q", str(SKILL / "scripts")],
                                   cwd=ROOT, env=env, capture_output=True, text=True, timeout=60)
        return {"status": "PASS" if completed.returncode == 0 else "FAIL", "returncode": completed.returncode,
                "stderr": completed.stderr[-1000:]}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", default="dist/video-generation-engineering-triple-aaa-r9.zip")
    parser.add_argument("--report", default="verification/distribution-triple-aaa-r9.json")
    parser.add_argument("--critic-ref")
    parser.add_argument("--fingerprint-ref")
    args = parser.parse_args(argv)
    archive_path = (ROOT / args.archive).resolve() if not Path(args.archive).is_absolute() else Path(args.archive)
    report_path = (ROOT / args.report).resolve() if not Path(args.report).is_absolute() else Path(args.report)
    started = datetime.now(timezone.utc).isoformat()
    paths = package_files()
    records = manifest(paths)
    errors = scan_package(paths)
    archive = build_archive(archive_path, paths) if not errors else {"path": str(archive_path), "status": "NOT_BUILT"}
    archive_check = verify_archive(archive_path, records) if not errors else {"status": "BLOCKED", "errors": errors}
    smoke = run_external_smoke(archive_path) if archive_check.get("status") == "PASS" else {"status": "BLOCKED", "checks": []}
    compileall = run_compileall()
    critic = None
    for field, value in (("critic_ref", args.critic_ref), ("fingerprint_ref", args.fingerprint_ref)):
        if value:
            path = (ROOT / value).resolve() if not Path(value).is_absolute() else Path(value)
            if not path.is_file():
                errors.append(f"{field} is unavailable: {value}")
            else:
                if critic is None:
                    critic = {}
                critic[field] = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
    status = "PASS" if not errors and archive_check.get("status") == "PASS" and smoke.get("status") == "PASS" and compileall.get("status") == "PASS" else "FAIL"
    report = {
        "schema_version": 1, "id": "distribution-triple-aaa-r9", "observed_at": started,
        "completed_at": datetime.now(timezone.utc).isoformat(), "status": status,
        "scope": "FRESH_DETERMINISTIC_PORTABLE_SKILL_DISTRIBUTION",
        "package_scope": str(SKILL.relative_to(ROOT)), "package_manifest_sha256": manifest_digest(records),
        "package_file_count": len(records), "package_files_sha256": records,
        "archive": {**archive, "verification": archive_check}, "external_cwd_smoke": smoke,
        "compileall": compileall, "critic_binding": critic,
        "security": {"status": "PASS" if not errors else "FAIL", "errors": sorted(set(errors)),
                      "secret_value_scan": "PASS" if not any("secret" in error for error in errors) else "FAIL",
                      "model_weight_files": "PASS" if not any("weight" in error for error in errors) else "FAIL",
                      "private_media": "PASS" if not any("media" in error for error in errors) else "FAIL",
                      "absolute_workspace_paths": "PASS" if not any("absolute" in error for error in errors) else "FAIL"},
        "limitations": ["Package integrity and offline CLI smoke do not prove provider capability or audiovisual semantics.",
                        "The audit excludes project docs, generated media, credentials and model weights from the Skill archive.",
                        "A fresh independent critic and production evidence remain separate verdict gates."],
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key not in ("package_files_sha256",)},
                     ensure_ascii=False, indent=2))
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
