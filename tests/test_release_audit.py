import tempfile
from pathlib import Path
import unittest

from tools.release_audit import (
    ROOT,
    build_archive,
    manifest,
    manifest_digest,
    package_files,
    run_external_smoke,
    scan_package,
    verify_archive,
)
from tools.candidate_fingerprint import candidate_files, file_manifest, manifest_digest, sentinel_record


class ReleaseAuditTests(unittest.TestCase):
    def test_candidate_fingerprint_is_hash_bound_and_excludes_reviewer_record(self):
        paths = candidate_files()
        records = file_manifest(paths)
        self.assertIn("dist/video-generation-engineering-triple-aaa-r9.zip", records)
        self.assertNotIn("verification/candidate-fingerprint-r9-final.json", records)
        self.assertNotIn("verification/triple-aaa-independent-critic-r9.md", records)
        self.assertNotIn("docs/triple-aaa-final-evidence-closure-r9.md", records)
        self.assertTrue(manifest_digest(records).startswith("sha256:"))
        self.assertEqual(".gauntlet/bar.json", sentinel_record()["path"])

    def test_deterministic_skill_distribution_is_portable(self):
        paths = package_files()
        self.assertEqual([], scan_package(paths))
        records = manifest(paths)
        self.assertTrue(manifest_digest(records).startswith("sha256:"))
        with tempfile.TemporaryDirectory(prefix="vge-release-test-") as raw:
            archive = Path(raw) / "skill.zip"
            built = build_archive(archive, paths)
            self.assertEqual(29, built["entry_count"])
            self.assertEqual("PASS", verify_archive(archive, records)["status"])
            self.assertEqual("PASS", run_external_smoke(archive)["status"])


if __name__ == "__main__":
    unittest.main()
