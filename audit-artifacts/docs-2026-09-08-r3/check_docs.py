"""Third audit evidence collector. Read-only; writes JSON to stdout.

Reuses the second audit's structural checks without overwriting its evidence.
No runtime, semantic gate implementation, or external source validation.
"""

import contextlib
import io
import json
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[2]
with contextlib.redirect_stdout(io.StringIO()):
    previous = runpy.run_path(str(ROOT / "audit-artifacts/docs-2026-09-08-r2/check_docs.py"))

result = previous["result"]
obj = previous["obj"]
result["audit_revision"] = "r3"
result["complete_profile_parity"] = (
    obj("docs/contracts.md", "capability_profile")
    == obj("docs/model-adaptation.md", "capability_profile")
)
canonical = obj("docs/contracts.md", "artifact_observation")
runtime = obj("docs/comfyui-execution.md", "artifact_observation")
result["observation_shapes"] = {
    "canonical_fields": sorted(canonical),
    "runtime_example_fields": sorted(runtime),
    "canonical_fields_absent_in_runtime_example": sorted(set(canonical) - set(runtime)),
    "runtime_generation_status": runtime["generation_status"],
    "runtime_validation_status": runtime["validation_status"],
}
result["baseline_changes"] = sorted(
    name for name, fingerprint in result["docs_sha256"].items()
    if fingerprint != json.loads(
        (ROOT / "audit-artifacts/docs-2026-09-08-r2/evidence.json").read_text()
    )["docs_sha256"].get(name)
)
print(json.dumps(result, ensure_ascii=False, indent=2))
