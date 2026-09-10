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
import subprocess
import sys
import tempfile
import zipfile

try:
    from tools.candidate_fingerprint import (
        EXCLUDED_NAMES as FINGERPRINT_EXCLUDED_NAMES,
        EXCLUSION_JUSTIFICATIONS,
        RELEASE_CRITICAL_SURFACES,
        candidate_files as candidate_scope_files,
        file_manifest as candidate_scope_manifest,
        manifest_digest as candidate_scope_digest,
        sentinel_record as candidate_sentinel_record,
    )
except ModuleNotFoundError:  # pragma: no cover - supports direct script execution
    from candidate_fingerprint import (
        EXCLUDED_NAMES as FINGERPRINT_EXCLUDED_NAMES,
        EXCLUSION_JUSTIFICATIONS,
        RELEASE_CRITICAL_SURFACES,
        candidate_files as candidate_scope_files,
        file_manifest as candidate_scope_manifest,
        manifest_digest as candidate_scope_digest,
        sentinel_record as candidate_sentinel_record,
    )


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents/skills/video-generation-engineering"
# Direct script execution places ``tools/`` (not the repository root) on
# sys.path.  Keep repository-level verification imports available in both
# ``python tools/release_audit.py`` and module/test execution.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
EXCLUDED_PARTS = {"__pycache__", ".git"}
BANNED_SUFFIXES = {".ckpt", ".pt", ".pth", ".bin", ".onnx", ".safetensors", ".gguf", ".ggml"}
PRIVATE_MEDIA_SUFFIXES = {".mp4", ".mov", ".mkv", ".webm", ".gif", ".wav", ".mp3", ".flac", ".png", ".jpg", ".jpeg"}
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)\b(?:aws_access_key_id|aws_secret_access_key|api[_-]?key|access[_-]?token|client_secret)\s*[:=]\s*['\"]?[A-Za-z0-9_./+:-]{12,}"),
    re.compile(r"(?i)\b(?:sk|key|token|secret)_[A-Za-z0-9]{20,}\b"),
)
SHA256_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")


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


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def _resolve_reference(value: str | Path) -> Path:
    path = Path(value)
    # Normalize the reference without following symlinks; validators reject
    # symlinked references so the measured bytes are the addressed file's own.
    return (ROOT / path).absolute() if not path.is_absolute() else path.absolute()


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and SHA256_PATTERN.fullmatch(value) is not None


def _public_validation(result: dict) -> dict:
    return {key: value for key, value in result.items() if key != "_record"}


def _critic_verdict(text: str) -> str | None:
    """Extract the standalone verdict from the critic's final-verdict section."""
    match = re.search(
        r"(?ims)^\s*#{1,6}\s*Final\s+verdict\s*$.*?^\s*[`*_~]*\s*"
        r"(PASS|REJECT|INCOMPLETE)\s*[`*_~]*\s*$",
        text,
    )
    return match.group(1).upper() if match else None


def validate_fingerprint_reference(reference: str | Path) -> dict:
    """Validate a fingerprint's bytes, scope and claim-surface bindings."""
    path = _resolve_reference(reference)
    result = {"status": "FAIL", "ref": _display_path(path), "content_sha256": None, "errors": []}
    if not path.is_file() or path.is_symlink():
        result["errors"].append(f"fingerprint reference is unavailable or not a regular file: {path}")
        return result
    try:
        raw = path.read_bytes()
        result["content_sha256"] = sha256_bytes(raw)
        record = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        result["errors"].append(f"fingerprint reference is not valid UTF-8 JSON: {path} ({exc})")
        return result
    if not isinstance(record, dict):
        result["errors"].append("fingerprint reference must contain a JSON object")
        return result
    result["_record"] = record
    result["scope_sha256"] = record.get("scope_sha256")
    result["candidate_file_count"] = record.get("candidate_file_count")
    if record.get("schema_version") != 1:
        result["errors"].append("fingerprint schema_version must be 1")
    if record.get("id") != "candidate-fingerprint-r9":
        result["errors"].append("fingerprint id is not candidate-fingerprint-r9")
    if record.get("status") != "FROZEN":
        result["errors"].append("fingerprint status must be FROZEN")

    records = record.get("files_sha256")
    if not isinstance(records, dict):
        result["errors"].append("fingerprint files_sha256 must be an object")
        records = {}
    invalid_paths = []
    invalid_hashes = []
    for rel, digest in records.items():
        if not isinstance(rel, str) or Path(rel).is_absolute() or ".." in Path(rel).parts:
            invalid_paths.append(str(rel))
        if not _is_sha256(digest):
            invalid_hashes.append(str(rel))
    if invalid_paths:
        result["errors"].append("fingerprint contains unsafe paths: " + ", ".join(sorted(invalid_paths)))
    if invalid_hashes:
        result["errors"].append("fingerprint contains invalid SHA-256 records: " + ", ".join(sorted(invalid_hashes)))
    if record.get("candidate_file_count") != len(records):
        result["errors"].append("fingerprint candidate_file_count does not match files_sha256")
    if not _is_sha256(record.get("scope_sha256")):
        result["errors"].append("fingerprint scope_sha256 is not a valid SHA-256")
    elif candidate_scope_digest(records) != record.get("scope_sha256"):
        result["errors"].append("fingerprint scope_sha256 does not match files_sha256")

    actual_records = candidate_scope_manifest(candidate_scope_files())
    missing = sorted(set(actual_records) - set(records))
    unexpected = sorted(set(records) - set(actual_records))
    mismatched = sorted(
        rel for rel in set(actual_records) & set(records) if actual_records[rel] != records[rel]
    )
    if missing:
        result["errors"].append("fingerprint omits current candidate files: " + ", ".join(missing[:12]))
    if unexpected:
        result["errors"].append("fingerprint contains files outside current candidate scope: " + ", ".join(unexpected[:12]))
    if mismatched:
        result["errors"].append("fingerprint has stale file hashes: " + ", ".join(mismatched[:12]))
    if record.get("candidate_file_count") != len(actual_records):
        result["errors"].append("fingerprint candidate_file_count does not match current candidate scope")

    policy = record.get("scope_policy")
    if not isinstance(policy, dict):
        result["errors"].append("fingerprint scope_policy must be an object")
    else:
        excluded = policy.get("excluded_derivative_records")
        if sorted(excluded or []) != sorted(FINGERPRINT_EXCLUDED_NAMES):
            result["errors"].append("fingerprint exclusions do not match the current explicit policy")
        if policy.get("excluded_record_justifications") != {
            name: EXCLUSION_JUSTIFICATIONS[name] for name in sorted(FINGERPRINT_EXCLUDED_NAMES)
        }:
            result["errors"].append("fingerprint exclusions are missing exact justifications")

    expected_sentinel = candidate_sentinel_record()
    if record.get("mutation_sentinel") != expected_sentinel:
        result["errors"].append("fingerprint mutation sentinel is stale or malformed")

    coverage = record.get("release_critical_surfaces")
    if not isinstance(coverage, dict):
        result["errors"].append("fingerprint release_critical_surfaces binding is missing")
    else:
        expected_in_scope = {}
        expected_excluded = {}
        missing_surfaces = []
        for rel in RELEASE_CRITICAL_SURFACES:
            surface = ROOT / rel
            if not surface.is_file() or surface.is_symlink():
                missing_surfaces.append(rel)
                continue
            digest = file_hash(surface)
            if rel in actual_records:
                expected_in_scope[rel] = digest
            elif rel in FINGERPRINT_EXCLUDED_NAMES:
                expected_excluded[rel] = digest
            else:
                result["errors"].append(f"claim surface has no permitted coverage mode: {rel}")
        if missing_surfaces:
            result["errors"].append("release-critical claim surface is unavailable: " + ", ".join(missing_surfaces))
        if coverage.get("in_scope") != expected_in_scope:
            result["errors"].append("fingerprint in-scope claim-surface hashes are stale or incomplete")
        if coverage.get("exact_hash_bound_exclusions") != expected_excluded:
            result["errors"].append("fingerprint excluded claim-surface bindings are stale or incomplete")

    result["status"] = "PASS" if not result["errors"] else "FAIL"
    return result


def compare_fingerprint_scopes(freeze: dict, final: dict) -> list[str]:
    """Return differences that invalidate a freeze/final fingerprint pair."""
    differences = []
    for field in ("candidate_file_count", "files_sha256", "scope_sha256", "mutation_sentinel",
                  "release_critical_surfaces"):
        if freeze.get(field) != final.get(field):
            differences.append(f"freeze/final fingerprint {field} differs")
    return differences


def validate_critic_reference(reference: str | Path, fingerprint: dict) -> dict:
    """Validate exact critic bytes, scope binding and the required review record."""
    path = _resolve_reference(reference)
    result = {"status": "FAIL", "ref": _display_path(path), "content_sha256": None,
              "verdict": None, "release_assurance_status": "INCOMPLETE", "errors": []}
    if not path.is_file() or path.is_symlink():
        result["errors"].append(f"critic reference is unavailable or not a regular file: {path}")
        return result
    try:
        raw = path.read_bytes()
        text = raw.decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        result["errors"].append(f"critic reference is not valid UTF-8 text: {path} ({exc})")
        return result
    result["content_sha256"] = sha256_bytes(raw)
    expected_scope = fingerprint.get("scope_sha256")
    expected_count = fingerprint.get("candidate_file_count")
    sentinel = fingerprint.get("mutation_sentinel")
    result["scope_sha256"] = expected_scope
    result["candidate_file_count"] = expected_count
    required_sections = (
        "Review mode", "Reviewer", "Review window", "Independent freeze checks",
        "Criterion verdicts", "Critical conclusion", "Supported claims",
        "Unsupported claims", "Final verdict",
    )
    for section in required_sections:
        if section.lower() not in text.lower():
            result["errors"].append(f"critic is missing required section: {section}")
    if not re.search(r"(?im)^\s*\|\s*Criterion\s*\|", text):
        result["errors"].append("critic criteria matrix is missing a Criterion column")
    if not re.search(r"(?im)^\s*\|\s*Criterion\s*\|\s*Status\s*\|", text):
        result["errors"].append("critic criteria matrix is missing a Status column")
    if not re.search(r"(?i)severity", text):
        result["errors"].append("critic is missing severity findings")
    if not re.search(r"(?i)evidence", text):
        result["errors"].append("critic is missing evidence references")
    if not re.search(r"(?i)\bfresh\b", text) or not re.search(r"(?i)\bread.only\b", text):
        result["errors"].append("critic is not explicitly marked fresh and read-only")
    verdict = _critic_verdict(text)
    result["verdict"] = verdict
    if verdict is None:
        result["errors"].append("critic final verdict must be PASS, REJECT or INCOMPLETE")
    if not _is_sha256(expected_scope) or expected_scope not in text:
        result["errors"].append("critic does not state the exact fingerprint scope digest")
    if not isinstance(sentinel, dict) or not sentinel.get("path") or not _is_sha256(sentinel.get("content_hash")):
        result["errors"].append("fingerprint mutation sentinel is unavailable for critic binding")
    else:
        if sentinel["path"] not in text or sentinel["content_hash"] not in text:
            result["errors"].append("critic does not state the exact mutation sentinel binding")
    if not isinstance(expected_count, int) or f"{expected_count} files" not in text:
        result["errors"].append("critic does not state the exact candidate file count")
    if "Independent scope digest" not in text or "Mutation sentinel" not in text:
        result["errors"].append("critic is missing the required independent scope binding labels")
    result["status"] = "PASS" if not result["errors"] else "FAIL"
    if verdict == "PASS" and result["status"] == "PASS":
        result["release_assurance_status"] = "PASS"
    elif verdict == "REJECT":
        result["release_assurance_status"] = "REJECT"
    else:
        result["release_assurance_status"] = "INCOMPLETE"
    return result


def validate_release_references(freeze_ref=None, fingerprint_ref=None, critic_ref=None) -> dict:
    """Validate optional freeze/final/critic references as one binding."""
    requested = any(value is not None for value in (freeze_ref, fingerprint_ref, critic_ref))
    if not requested:
        return {"status": "NOT_REQUESTED", "errors": []}

    binding = {"status": "FAIL", "errors": []}
    final_validation = None
    freeze_validation = None
    if fingerprint_ref is None:
        binding["errors"].append("fingerprint_ref is required when release references are supplied")
    else:
        final_validation = validate_fingerprint_reference(fingerprint_ref)
        binding["fingerprint"] = _public_validation(final_validation)
        binding["fingerprint_ref"] = final_validation["ref"]
        binding["fingerprint_content_sha256"] = final_validation.get("content_sha256")
        binding["fingerprint_scope_sha256"] = final_validation.get("scope_sha256")
        binding["fingerprint_candidate_file_count"] = final_validation.get("candidate_file_count")
        binding["errors"].extend("fingerprint: " + error for error in final_validation["errors"])

    if freeze_ref is not None:
        freeze_validation = validate_fingerprint_reference(freeze_ref)
        binding["freeze"] = _public_validation(freeze_validation)
        binding["freeze_ref"] = freeze_validation["ref"]
        binding["freeze_content_sha256"] = freeze_validation.get("content_sha256")
        binding["freeze_scope_sha256"] = freeze_validation.get("scope_sha256")
        binding["errors"].extend("freeze: " + error for error in freeze_validation["errors"])
        if fingerprint_ref is None:
            binding["errors"].append("freeze_ref requires fingerprint_ref for freeze/final scope comparison")

    if final_validation and freeze_validation:
        final_record = final_validation.get("_record")
        freeze_record = freeze_validation.get("_record")
        if final_record and freeze_record:
            binding["freeze_final_scope"] = {
                "status": "PASS" if not compare_fingerprint_scopes(freeze_record, final_record) else "FAIL",
                "differences": compare_fingerprint_scopes(freeze_record, final_record),
            }
            binding["errors"].extend(binding["freeze_final_scope"]["differences"])

    if critic_ref is not None:
        if final_validation and final_validation.get("_record"):
            critic_validation = validate_critic_reference(critic_ref, final_validation["_record"])
            binding["critic"] = critic_validation
            binding["critic_record_binding_status"] = critic_validation["status"]
            binding["release_assurance_status"] = critic_validation.get("release_assurance_status", "INCOMPLETE")
            binding["critic_ref"] = critic_validation["ref"]
            binding["critic_content_sha256"] = critic_validation.get("content_sha256")
            binding["errors"].extend("critic: " + error for error in critic_validation["errors"])
            if critic_validation.get("verdict") != "PASS":
                binding["errors"].append(
                    "critic final verdict must be PASS for release assurance; "
                    f"observed {critic_validation.get('verdict') or 'MISSING'}"
                )
        else:
            binding["errors"].append("critic_ref requires a valid fingerprint_ref for exact scope validation")

    binding["errors"] = sorted(set(binding["errors"]))
    binding["status"] = "PASS" if not binding["errors"] else "FAIL"
    return binding


def build_archive(output: Path, paths: list[Path]) -> dict:
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"Refusing to overwrite existing archive: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in paths:
            name = relative_name(path)
            archive.writestr(_zip_info(name), path.read_bytes())
    return {"status": "BUILT",
            "path": str(output.relative_to(ROOT)) if output.is_relative_to(ROOT) else str(output),
            "sha256": file_hash(output), "bytes": output.stat().st_size,
            "entry_count": len(paths), "file_count": len(paths)}


def describe_existing_archive(archive_path: Path) -> dict:
    """Describe a shipped archive so reference validation can remain in-scope.

    The candidate fingerprint intentionally includes the distribution archive.
    Moving that archive away just to rebuild it would make the frozen scope
    appear incomplete, so the release audit verifies an existing archive
    without overwriting it.  ``verify_archive`` remains the authoritative
    byte/member check below.
    """
    result = {"status": "EXISTING", "path": str(archive_path),
              "sha256": None, "bytes": None, "entry_count": None, "file_count": None}
    if not archive_path.is_file() or archive_path.is_symlink():
        result["status"] = "MISSING"
        return result
    result["sha256"] = file_hash(archive_path)
    result["bytes"] = archive_path.stat().st_size
    try:
        with zipfile.ZipFile(archive_path) as archive:
            count = len(archive.infolist())
    except (OSError, zipfile.BadZipFile):
        result["status"] = "INVALID"
        return result
    result["entry_count"] = count
    result["file_count"] = count
    return result


def verify_archive(archive_path: Path, records: dict[str, str]) -> dict:
    errors = []
    with zipfile.ZipFile(archive_path) as archive:
        entries = archive.infolist()
        names = [entry.filename for entry in entries]
        manifest_names = set(records)
        archive_names = set(names)
        if names != sorted(names):
            errors.append("archive entries are not sorted")
        if len(names) != len(set(names)):
            errors.append("archive contains duplicate entries")
        missing = sorted(manifest_names - archive_names)
        unexpected = sorted(archive_names - manifest_names)
        if missing:
            errors.append("archive is missing manifest entries: " + ", ".join(missing))
        if unexpected:
            errors.append("archive contains entries absent from manifest: " + ", ".join(unexpected))
        if names != sorted(records):
            errors.append("archive member order/set does not exactly match manifest")
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
            "crc_test": "PASS" if "CRC test failed" not in errors else "FAIL",
            "archive_entry_count": len(names), "manifest_entry_count": len(records)}


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


def run_import_cycle_check() -> dict:
    """Run the same static local-module cycle check used by project verification."""
    try:
        from tools.verify import import_cycle_audit
        return import_cycle_audit(SKILL / "scripts")
    except Exception as exc:  # pragma: no cover - defensive release boundary
        return {"status": "FAIL", "cycles": [], "errors": [f"import-cycle audit could not run: {type(exc).__name__}: {exc}"]}


def run_project_verification() -> dict:
    """Run the complete offline verification suite in an isolated report path."""
    with tempfile.TemporaryDirectory(prefix="vge-release-verify-") as raw:
        report_path = Path(raw) / "verify.json"
        env = dict(__import__("os").environ)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        completed = subprocess.run(
            [sys.executable, str(ROOT / "tools/verify.py"), "--output", str(report_path)],
            cwd=ROOT, env=env, capture_output=True, text=True, timeout=180,
        )
        report = None
        if report_path.is_file():
            try:
                report = json.loads(report_path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                report = None
        return {
            "status": "PASS" if completed.returncode == 0 and isinstance(report, dict)
                      and report.get("status") == "PASS" else "FAIL",
            "returncode": completed.returncode,
            "report_status": report.get("status") if isinstance(report, dict) else "UNAVAILABLE",
            "tests_run": report.get("tests_run") if isinstance(report, dict) else None,
            "failures": report.get("failures") if isinstance(report, dict) else None,
            "errors": report.get("errors", []) if isinstance(report, dict) else ["verification report unavailable"],
            "import_cycle_status": report.get("import_cycle_audit", {}).get("status") if isinstance(report, dict) else None,
            "stderr": completed.stderr[-2000:],
        }


def run_docs_validation() -> dict:
    """Run the latest read-only documentation/link/contract audit."""
    checker = ROOT / "audit-artifacts/docs-2026-09-08-r5/check_docs.py"
    completed = subprocess.run([sys.executable, str(checker)], cwd=ROOT,
                               capture_output=True, text=True, timeout=60)
    result = None
    if completed.returncode == 0:
        try:
            result = json.loads(completed.stdout)
        except json.JSONDecodeError:
            result = None
    structural_ok = isinstance(result, dict) and not any((
        result.get("yaml_errors"), result.get("local_link_errors"),
        result.get("missing_traceability_ids"), result.get("implicit_yaml_booleans"),
    ))
    parity_ok = isinstance(result, dict) and result.get("complete_profile_parity") is True \
        and result.get("collection_parity") is True
    provenance = result.get("provenance_case", {}) if isinstance(result, dict) else {}
    provenance_ok = isinstance(provenance, dict) and all(provenance.get(key) is True for key in (
        "artifact_attempt_links_resolve", "observation_links_and_hashes_match"))
    return {
        "status": "PASS" if completed.returncode == 0 and structural_ok and parity_ok and provenance_ok else "FAIL",
        "returncode": completed.returncode,
        "audit_revision": result.get("audit_revision") if isinstance(result, dict) else None,
        "documents": result.get("documents") if isinstance(result, dict) else None,
        "yaml_errors": result.get("yaml_errors", []) if isinstance(result, dict) else ["documentation audit did not return JSON"],
        "local_link_errors": result.get("local_link_errors", []) if isinstance(result, dict) else [],
        "missing_traceability_ids": result.get("missing_traceability_ids", []) if isinstance(result, dict) else [],
        "implicit_yaml_booleans": result.get("implicit_yaml_booleans", []) if isinstance(result, dict) else [],
        "complete_profile_parity": result.get("complete_profile_parity") if isinstance(result, dict) else None,
        "collection_parity": result.get("collection_parity") if isinstance(result, dict) else None,
        "provenance_case": provenance,
        "stderr": completed.stderr[-2000:],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", default="dist/video-generation-engineering-triple-aaa-r9.zip")
    parser.add_argument("--report", default="verification/distribution-triple-aaa-r9.json")
    parser.add_argument("--freeze-ref", help="frozen candidate fingerprint to compare with the final reference")
    parser.add_argument("--critic-ref")
    parser.add_argument("--fingerprint-ref", help="final candidate fingerprint to validate")
    args = parser.parse_args(argv)
    archive_path = (ROOT / args.archive).resolve() if not Path(args.archive).is_absolute() else Path(args.archive)
    report_path = (ROOT / args.report).resolve() if not Path(args.report).is_absolute() else Path(args.report)
    started = datetime.now(timezone.utc).isoformat()
    paths = package_files()
    records = manifest(paths)
    package_errors = scan_package(paths)
    errors = list(package_errors)
    reference_binding = validate_release_references(args.freeze_ref, args.fingerprint_ref, args.critic_ref)
    if reference_binding["status"] == "FAIL":
        errors.extend("release reference: " + error for error in reference_binding["errors"])

    archive = {"path": str(archive_path), "status": "NOT_BUILT"}
    # A non-PASS reviewer is an assurance failure, not a reason to suppress
    # independent package-integrity, smoke, compile or docs measurements.
    if not package_errors:
        if archive_path.exists() or archive_path.is_symlink():
            archive = describe_existing_archive(archive_path)
            if archive["status"] == "INVALID":
                errors.append(f"existing archive is not a valid ZIP: {archive_path}")
            elif archive["status"] == "MISSING":
                errors.append(f"existing archive is unavailable: {archive_path}")
        else:
            try:
                archive = build_archive(archive_path, paths)
            except FileExistsError as exc:
                errors.append(str(exc))
    archive_check = (
        verify_archive(archive_path, records)
        if archive.get("status") in ("BUILT", "EXISTING")
        else {"status": "BLOCKED", "errors": sorted(set(errors))}
    )
    smoke = run_external_smoke(archive_path) if archive_check.get("status") == "PASS" else {"status": "BLOCKED", "checks": []}
    compileall = run_compileall()
    import_cycle = run_import_cycle_check()
    project_verification = run_project_verification()
    docs_validation = run_docs_validation()
    status = "PASS" if not errors and archive_check.get("status") == "PASS" and smoke.get("status") == "PASS" and compileall.get("status") == "PASS" and import_cycle.get("status") == "PASS" and project_verification.get("status") == "PASS" and docs_validation.get("status") == "PASS" else "FAIL"
    report = {
        "schema_version": 1, "id": "distribution-triple-aaa-r9", "observed_at": started,
        "completed_at": datetime.now(timezone.utc).isoformat(), "status": status,
        "scope": "FRESH_DETERMINISTIC_PORTABLE_SKILL_DISTRIBUTION",
        "package_scope": str(SKILL.relative_to(ROOT)), "package_manifest_sha256": manifest_digest(records),
        "package_file_count": len(records), "package_files_sha256": records,
        "archive": {**archive, "verification": archive_check}, "external_cwd_smoke": smoke,
        "compileall": compileall, "import_cycle_audit": import_cycle,
        "project_verification": project_verification, "docs_validation": docs_validation,
        "critic_binding": reference_binding,
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
