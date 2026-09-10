#!/usr/bin/env python3
"""Create a deterministic fingerprint for the current R9 release candidate.

The fingerprint covers source, tests, docs and textual verification records,
plus the R9 distribution archive.  Only self-referential fingerprint records,
the post-freeze reviewer record, and the post-freeze distribution report are
excluded.  Those exclusions are explicit and are bound byte-for-byte by the
post-freeze release audit.  Generated media and model weights are excluded
from the byte scope; their hash-bound records remain in scope.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SENTINEL = ROOT / ".gauntlet/bar.json"

# These are claim-bearing surfaces rather than incidental documentation.  The
# post-freeze reviewer and distribution reports remain outside the
# self-referential candidate scope; release_audit binds their exact bytes after
# the candidate fingerprint is frozen.
RELEASE_CRITICAL_SURFACES = (
    "docs/triple-aaa-final-evidence-closure-r9.md",
    "docs/capability-matrix-r9.md",
    "docs/triple-aaa-scorecard-r9.md",
    "verification/software-triple-aaa-r9.json",
    "verification/docs-current-r9.json",
)

EXCLUSION_JUSTIFICATIONS = {
    "verification/candidate-fingerprint-r9-freeze.json":
        "Self-referential freeze record; its declared candidate scope is independently recomputed.",
    "verification/candidate-fingerprint-r9-final.json":
        "Self-referential final record; its declared candidate scope is independently recomputed.",
    "verification/triple-aaa-independent-critic-r9.md":
        "Post-freeze reviewer-owned record; its exact bytes and scope binding are validated by release_audit.",
    "verification/distribution-triple-aaa-r9.json":
        "Post-freeze generated distribution report; its exact bytes and archive/package bindings are validated by release_audit.",
}
EXCLUDED_NAMES = set(EXCLUSION_JUSTIFICATIONS)
MEDIA_SUFFIXES = {".mp4", ".mov", ".mkv", ".webm", ".gif", ".wav", ".mp3", ".flac",
                  ".png", ".jpg", ".jpeg", ".zip", ".ckpt", ".pt", ".pth", ".bin",
                  ".onnx", ".safetensors", ".gguf", ".ggml"}


def sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def candidate_files() -> list[Path]:
    roots = [ROOT / ".agent", ROOT / ".agents", ROOT / "docs", ROOT / "tests",
             ROOT / "tools", ROOT / "verification", ROOT / "dist"]
    files = []
    for base in roots:
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or path.is_symlink():
                continue
            rel = path.relative_to(ROOT).as_posix()
            if rel in EXCLUDED_NAMES or "__pycache__" in path.parts or path.suffix == ".pyc":
                continue
            if rel.startswith("dist/") and rel != "dist/video-generation-engineering-triple-aaa-r9.zip":
                continue
            # Keep textual records and source in the fingerprint.  The binary
            # artifact itself is represented by its immutable verification
            # record and never gets accidentally packaged into this scope.
            if path.suffix.lower() in MEDIA_SUFFIXES and rel != "dist/video-generation-engineering-triple-aaa-r9.zip":
                continue
            files.append(path)
    return sorted(set(files), key=lambda item: item.relative_to(ROOT).as_posix())


def file_manifest(paths: list[Path]) -> dict[str, str]:
    return {path.relative_to(ROOT).as_posix(): sha256_bytes(path.read_bytes()) for path in paths}


def manifest_digest(records: dict[str, str]) -> str:
    return sha256_bytes(json.dumps(records, sort_keys=True, separators=(",", ":")).encode())


def sentinel_record() -> dict:
    if not SENTINEL.is_file():
        raise RuntimeError(f"Mutation sentinel is unavailable: {SENTINEL}")
    return {"path": SENTINEL.relative_to(ROOT).as_posix(), "content_hash": sha256_bytes(SENTINEL.read_bytes())}


def release_critical_surface_records(records: dict[str, str]) -> dict:
    """Return explicit coverage for every release-critical claim surface."""
    in_scope = {}
    exact_hash_bound_exclusions = {}
    missing = []
    for rel in RELEASE_CRITICAL_SURFACES:
        path = ROOT / rel
        if not path.is_file() or path.is_symlink():
            missing.append(rel)
            continue
        digest = sha256_bytes(path.read_bytes())
        if rel in records:
            if records[rel] != digest:
                raise RuntimeError(f"Candidate manifest hash mismatch for claim surface: {rel}")
            in_scope[rel] = digest
        else:
            raise RuntimeError(f"Release-critical claim surface is outside the candidate scope: {rel}")
    if missing:
        raise RuntimeError("Release-critical claim surface is unavailable: " + ", ".join(sorted(missing)))
    return {
        "policy": "Each release-critical claim surface is included in the candidate manifest. Post-freeze reviewer/distribution records are validated by release_audit after the candidate is frozen.",
        "in_scope": in_scope,
        "exact_hash_bound_exclusions": exact_hash_bound_exclusions,
    }


def build_record() -> dict:
    paths = candidate_files()
    records = file_manifest(paths)
    return {
        "schema_version": 1,
        "id": "candidate-fingerprint-r9",
        "status": "FROZEN",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "scope_policy": {
            "included_roots": [".agent", ".agents", "docs", "tests", "tools", "verification", "dist/r9 archive"],
            "included_distribution": "dist/video-generation-engineering-triple-aaa-r9.zip",
            "excluded_derivative_records": sorted(EXCLUDED_NAMES),
            "excluded_binary_suffixes": sorted(MEDIA_SUFFIXES),
            "excluded_record_justifications": {
                name: EXCLUSION_JUSTIFICATIONS[name] for name in sorted(EXCLUDED_NAMES)
            },
            "reason": "Only self-referential and post-freeze generated/reviewer-owned records are excluded; all release-critical claim surfaces remain in the candidate scope."
        },
        "candidate_file_count": len(records),
        "files_sha256": records,
        "scope_sha256": manifest_digest(records),
        "mutation_sentinel": sentinel_record(),
        "release_critical_surfaces": release_critical_surface_records(records),
        "limitations": [
            "The fingerprint proves byte identity for the declared source/evidence scope, not audiovisual semantic quality.",
            "Generated media and model weights are represented by hash-bound records and release exclusions, not copied into the candidate scope.",
            "Post-freeze reviewer and distribution records are not part of the self-referential manifest; their exact bytes and scope claims must be validated by the release audit."
        ]
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="verification/candidate-fingerprint-r9-final.json")
    args = parser.parse_args(argv)
    record = build_record()
    output = Path(args.output)
    if not output.is_absolute():
        output = ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in record.items() if key != "files_sha256"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
