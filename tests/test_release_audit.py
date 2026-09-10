import copy
import json
import tempfile
from pathlib import Path
import unittest

from tools.candidate_fingerprint import (
    RELEASE_CRITICAL_SURFACES,
    build_record,
    candidate_files,
    file_manifest,
    manifest_digest as candidate_manifest_digest,
    sentinel_record,
)
from tools.release_audit import (
    ROOT,
    build_archive,
    manifest,
    manifest_digest as package_manifest_digest,
    package_files,
    run_external_smoke,
    scan_package,
    validate_fingerprint_reference,
    validate_release_references,
    verify_archive,
)
from tools.verify import import_cycle_audit


class ReleaseAuditTests(unittest.TestCase):
    def test_import_cycle_audit_is_static_and_detects_cycles(self):
        self.assertEqual("PASS", import_cycle_audit(ROOT / ".agents/skills/video-generation-engineering/scripts")["status"])
        with tempfile.TemporaryDirectory(prefix="vge-cycle-audit-") as raw:
            root = Path(raw)
            (root / "a.py").write_text("import b\n", encoding="utf-8")
            (root / "b.py").write_text("from a import value\n", encoding="utf-8")
            result = import_cycle_audit(root)
            self.assertEqual("FAIL", result["status"])
            self.assertEqual([["a", "b", "a"]], result["cycles"])

    def test_candidate_fingerprint_covers_or_hash_binds_claim_surfaces(self):
        paths = candidate_files()
        records = file_manifest(paths)
        self.assertIn("dist/video-generation-engineering-triple-aaa-r9.zip", records)
        self.assertNotIn("verification/candidate-fingerprint-r9-final.json", records)
        self.assertNotIn("verification/candidate-fingerprint-r9-freeze.json", records)
        self.assertNotIn("verification/triple-aaa-independent-critic-r9.md", records)
        self.assertNotIn("verification/distribution-triple-aaa-r9.json", records)
        for path in (
            "docs/triple-aaa-final-evidence-closure-r9.md",
            "docs/capability-matrix-r9.md",
            "docs/triple-aaa-scorecard-r9.md",
            "verification/software-triple-aaa-r9.json",
            "verification/docs-current-r9.json",
        ):
            self.assertIn(path, records)
        record = build_record()
        coverage = record["release_critical_surfaces"]
        for path in RELEASE_CRITICAL_SURFACES:
            actual_hash = file_manifest([ROOT / path])[path]
            if path in records:
                self.assertEqual(actual_hash, coverage["in_scope"][path])
            else:
                self.assertEqual(actual_hash, coverage["exact_hash_bound_exclusions"][path])
        self.assertEqual(candidate_manifest_digest(records), record["scope_sha256"])
        self.assertEqual(".gauntlet/bar.json", sentinel_record()["path"])
        self.assertTrue(record["scope_policy"]["excluded_record_justifications"])

    def test_deterministic_skill_distribution_is_portable(self):
        paths = package_files()
        self.assertEqual([], scan_package(paths))
        records = manifest(paths)
        self.assertTrue(package_manifest_digest(records).startswith("sha256:"))
        with tempfile.TemporaryDirectory(prefix="vge-release-test-") as raw:
            archive = Path(raw) / "skill.zip"
            built = build_archive(archive, paths)
            self.assertEqual(len(paths), built["entry_count"])
            self.assertEqual(len(records), built["file_count"])
            self.assertEqual("PASS", verify_archive(archive, records)["status"])
            self.assertEqual("PASS", run_external_smoke(archive)["status"])

    def test_existing_archive_is_never_overwritten(self):
        paths = package_files()
        with tempfile.TemporaryDirectory(prefix="vge-release-test-") as raw:
            archive = Path(raw) / "existing.zip"
            original = b"preserve this unrelated archive"
            archive.write_bytes(original)
            with self.assertRaisesRegex(FileExistsError, "Refusing to overwrite existing archive"):
                build_archive(archive, paths)
            self.assertEqual(original, archive.read_bytes())

    def test_archive_members_must_match_manifest_exactly(self):
        paths = package_files()
        records = manifest(paths)
        with tempfile.TemporaryDirectory(prefix="vge-release-test-") as raw:
            archive = Path(raw) / "skill.zip"
            build_archive(archive, paths)

            missing_from_manifest = dict(records)
            omitted_name = sorted(missing_from_manifest)[0]
            del missing_from_manifest[omitted_name]
            missing_result = verify_archive(archive, missing_from_manifest)
            self.assertEqual("FAIL", missing_result["status"])
            self.assertTrue(any("absent from manifest" in error for error in missing_result["errors"]))

            missing_from_archive = dict(records)
            missing_from_archive[".agents/manifest-only.txt"] = "sha256:" + "0" * 64
            extra_result = verify_archive(archive, missing_from_archive)
            self.assertEqual("FAIL", extra_result["status"])
            self.assertTrue(any("missing manifest entries" in error for error in extra_result["errors"]))

    def test_release_references_bind_exact_content_and_scope(self):
        record = build_record()
        freeze = copy.deepcopy(record)
        freeze["observed_at"] = "2026-09-09T00:00:00+00:00"
        with tempfile.TemporaryDirectory(prefix="vge-release-test-") as raw:
            root = Path(raw)
            freeze_ref = root / "freeze.json"
            final_ref = root / "final.json"
            critic_ref = root / "critic.md"
            freeze_ref.write_text(json.dumps(freeze, indent=2) + "\n", encoding="utf-8")
            final_ref.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
            sentinel = record["mutation_sentinel"]
            critic_ref.write_text(
                "# Fresh independent review\n"
                "**Review mode:** fresh, read-only\n"
                "**Reviewer:** fixture-reviewer\n"
                "**Review window:** `2026-09-09T00:00:00+00:00` — `2026-09-09T00:01:00+00:00`\n\n"
                "## Independent freeze checks\n"
                f"- Candidate scope independently recomputed: {record['candidate_file_count']} files.\n"
                f"- Independent scope digest: `{record['scope_sha256']}`.\n"
                f"- Mutation sentinel: `{sentinel['path']}`, `{sentinel['content_hash']}`.\n"
                "\n## Criterion verdicts\n\n"
                "| Criterion | Status | Severity | Evidence |\n"
                "|---|---|---|---|\n"
                "| structural | PASS | Low | test report |\n\n"
                "## Critical conclusion\n\nThe fixture review is incomplete for production.\n\n"
                "## Supported claims\n\nStructural checks only.\n\n"
                "## Unsupported claims\n\nProduction audiovisual acceptance.\n\n"
                "## Final verdict\n\n**INCOMPLETE**\n",
                encoding="utf-8",
            )
            binding = validate_release_references(freeze_ref, final_ref, critic_ref)
            self.assertEqual("PASS", binding["status"])
            self.assertEqual(candidate_manifest_digest(record["files_sha256"]), record["scope_sha256"])
            self.assertTrue(binding["fingerprint_content_sha256"].startswith("sha256:"))
            self.assertTrue(binding["critic_content_sha256"].startswith("sha256:"))
            self.assertEqual(record["scope_sha256"], binding["freeze_scope_sha256"])

    def test_release_reference_validation_rejects_stale_scope(self):
        record = build_record()
        stale = copy.deepcopy(record)
        stale["files_sha256"]["tools/candidate_fingerprint.py"] = "sha256:" + "0" * 64
        stale["scope_sha256"] = candidate_manifest_digest(stale["files_sha256"])
        with tempfile.TemporaryDirectory(prefix="vge-release-test-") as raw:
            reference = Path(raw) / "stale.json"
            reference.write_text(json.dumps(stale, indent=2) + "\n", encoding="utf-8")
            result = validate_fingerprint_reference(reference)
            self.assertEqual("FAIL", result["status"])
            self.assertTrue(any("stale file hashes" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
