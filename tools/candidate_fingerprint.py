#!/usr/bin/env python3
"""Create a deterministic fingerprint for the current R9 release candidate.

The fingerprint covers source, tests, docs and textual verification records,
plus the R9 distribution archive.  Reviewer-owned records and the fingerprint
files themselves are deliberately excluded so a critic can be added after the
freeze without silently changing the reviewed candidate.  Generated media and
model weights are excluded from the byte scope; their hash-bound records remain
in scope.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SENTINEL = ROOT / ".gauntlet/bar.json"
EXCLUDED_NAMES = {
    "verification/candidate-fingerprint-r9-freeze.json",
    "verification/candidate-fingerprint-r9-final.json",
    "verification/triple-aaa-independent-critic-r9.md",
    "docs/triple-aaa-final-evidence-closure-r9.md",
    "docs/capability-matrix-r9.md",
    "docs/triple-aaa-scorecard-r9.md",
    "verification/software-triple-aaa-r9.json",
    "verification/docs-current-r9.json",
    "verification/distribution-triple-aaa-r9.json",
}
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
            "reason": "Reviewer-owned evidence is appended after freeze; textual provenance records remain covered."
        },
        "candidate_file_count": len(records),
        "files_sha256": records,
        "scope_sha256": manifest_digest(records),
        "mutation_sentinel": sentinel_record(),
        "limitations": [
            "The fingerprint proves byte identity for the declared source/evidence scope, not audiovisual semantic quality.",
            "Generated media and model weights are represented by hash-bound records and release exclusions, not copied into the candidate scope."
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
