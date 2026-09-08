"""Read-only documentation evidence for audit r5; JSON on stdout.

Uses the prior structural collector without changing historical results.
Fixture link comparisons are not an implementation of a runtime validator.
"""

import contextlib
import io
import json
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[2]
with contextlib.redirect_stdout(io.StringIO()):
    base = runpy.run_path(str(ROOT / "audit-artifacts/docs-2026-09-08-r2/check_docs.py"))
result = base["result"]
obj = base["obj"]
attempt = obj("docs/contracts.md", "execution_attempt")
case = obj("docs/comfyui-execution.md", "provenance_case")
attempts = {record["id"]: record for record in case["execution_attempts"]}
artifacts = {record["id"]: record for record in case["collected_artifacts"]}
observations = case["observations"]
same_id_example = attempts[attempt["id"]]
result["audit_revision"] = "r5"
result["complete_profile_parity"] = obj("docs/contracts.md", "capability_profile") == obj("docs/model-adaptation.md", "capability_profile")
result["collection_parity"] = obj("docs/contracts.md", "generation_artifact") == obj("docs/comfyui-execution.md", "generation_artifact")
result["provenance_case"] = {
    "attempt_count": len(attempts),
    "artifact_count": len(artifacts),
    "observation_count": len(observations),
    "artifact_attempt_links_resolve": all(a["execution_attempt_ref"] in attempts for a in artifacts.values()),
    "observation_links_and_hashes_match": all(
        o["generation_artifact_ref"] in artifacts
        and o["observed_content_hash"] == artifacts[o["generation_artifact_ref"]]["content_hash"]
        for o in observations
    ),
    "distinct_output_hashes": len({a["content_hash"] for a in artifacts.values()}),
    "distinct_output_locators": len({a["artifact_ref"] for a in artifacts.values()}),
}
result["repeated_attempt_fixture"] = {
    "id": attempt["id"],
    "different_top_level_fields": sorted(k for k in set(attempt) | set(same_id_example)
                                         if attempt.get(k) != same_id_example.get(k)),
    "canonical_inputs": attempt["inputs"],
    "execution_example_inputs": same_id_example["inputs"],
}
prior = json.loads((ROOT / "audit-artifacts/docs-2026-09-08-r4/evidence.json").read_text())
result["changes_since_r4"] = sorted(name for name, value in result["docs_sha256"].items()
                                    if value != prior["docs_sha256"].get(name))
print(json.dumps(result, ensure_ascii=False, indent=2))
