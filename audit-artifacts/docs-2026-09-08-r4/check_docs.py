"""Read-only evidence for docs audit r4. Run from the workspace with PyYAML.

Reuses r2 structural checks; does not overwrite historical evidence or docs.
Output is inspection evidence, not an automatic acceptance verdict.
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
canonical = obj("docs/contracts.md", "generation_artifact")
runtime = obj("docs/comfyui-execution.md", "generation_artifact")
canonical_observation = obj("docs/contracts.md", "artifact_observation")
observations = [block["artifact_observation"] for block in base["blocks"]["docs/comfyui-execution.md"]
                if isinstance(block, dict) and "artifact_observation" in block]
result["audit_revision"] = "r4"
result["complete_profile_parity"] = obj("docs/contracts.md", "capability_profile") == obj("docs/model-adaptation.md", "capability_profile")
result["collection_parity"] = canonical == runtime
result["collection_shape"] = {
    "fields": sorted(canonical),
    "runtime_fields": sorted(canonical["runtime"]),
    "artifact_ref": canonical["artifact_ref"],
    "workflow_hash": canonical["runtime"]["workflow_hash"],
}
result["execution_observations"] = [
    {"id": record["id"], "status": record["status"],
     "missing_canonical_fields": sorted(set(canonical_observation) - set(record)),
     "has_timestamp": record["observed_at"] is not None,
     "has_procedure": record["procedure"] is not None,
     "check_count": len(record["checks"])} for record in observations
]
prior = json.loads((ROOT / "audit-artifacts/docs-2026-09-08-r3/evidence.json").read_text())
result["changes_since_r3"] = sorted(name for name, value in result["docs_sha256"].items()
                                    if value != prior["docs_sha256"].get(name))
print(json.dumps(result, ensure_ascii=False, indent=2))
