"""Read-only structural evidence for the second docs audit; not a plan validator.

Run from the workspace root with Python 3 and PyYAML. JSON is written to stdout.
Anchor checks use a GitHub-style slug convention, not a browser rendering test.
"""

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

import yaml


ROOT = Path(__file__).resolve().parents[2]
FILES = sorted((ROOT / "docs").rglob("*.md"))
FENCE = re.compile(r"^```[^\n]*\n.*?^```", re.M | re.S)
YAML_FENCE = re.compile(r"^```ya?ml\s*\n(.*?)^```", re.M | re.S)


def anchors(source):
    clean = FENCE.sub("", source)
    result = set(re.findall(r'<a\s+(?:id|name)=[\"\']([^\"\']+)', clean))
    counts = Counter()
    for heading in re.findall(r"^#{1,6}\s+(.+)$", clean, re.M):
        slug = re.sub(r"<[^>]+>", "", heading).lower()
        slug = re.sub(r"[^\w\- ]", "", slug).replace(" ", "-")
        number = counts[slug]
        counts[slug] += 1
        result.add(slug + (f"-{number}" if number else ""))
    return result


texts = {path: path.read_text() for path in FILES}
anchor_map = {path: anchors(text) for path, text in texts.items()}
blocks = {}
errors = []
implicit_booleans = []
manifest = {}
local_count = 0
link_errors = []

for path, source in texts.items():
    name = str(path.relative_to(ROOT))
    manifest[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    blocks[name] = []
    for match in YAML_FENCE.finditer(source):
        line = source[:match.start(1)].count("\n") + 1
        try:
            blocks[name].append(yaml.safe_load(match.group(1)))
            # YAML nodes retain scalar spelling and resolution type.
            def visit(node):
                if isinstance(node, yaml.ScalarNode):
                    if node.tag.endswith(":bool") and node.value.lower() not in ("true", "false"):
                        implicit_booleans.append({"file": name, "line": line + node.start_mark.line,
                                                  "literal": node.value, "resolved_type": "boolean"})
                elif isinstance(node, yaml.SequenceNode):
                    for child in node.value:
                        visit(child)
                elif isinstance(node, yaml.MappingNode):
                    for key, value in node.value:
                        visit(key)
                        visit(value)
            node = yaml.compose(match.group(1), Loader=yaml.SafeLoader)
            if node is not None:
                visit(node)
        except yaml.YAMLError as exc:
            errors.append({"file": name, "line": line, "error": str(exc)})
    for match in re.finditer(r"\[[^\]\n]*\]\(([^)\n]+)\)", FENCE.sub("", source)):
        target = match.group(1).strip("<>")
        url = urlsplit(target)
        if url.scheme or url.netloc:
            continue
        local_count += 1
        destination = (path.parent / unquote(url.path)).resolve() if url.path else path
        if not destination.exists():
            link_errors.append({"file": name, "target": target, "kind": "file"})
        elif url.fragment and destination.suffix == ".md":
            targets = anchor_map.get(destination)
            if targets is None:
                targets = anchors(destination.read_text())
            if unquote(url.fragment) not in targets:
                link_errors.append({"file": name, "target": target, "kind": "anchor"})


def obj(file, key):
    return next(block[key] for block in blocks[file] if isinstance(block, dict) and key in block)


contract_profile = obj("docs/contracts.md", "capability_profile")
adapter_profile = obj("docs/model-adaptation.md", "capability_profile")
contract_view = obj("docs/contracts.md", "canonical_prompt_view")
adapter_view = obj("docs/model-adaptation.md", "canonical_prompt_view")
observation = obj("docs/contracts.md", "artifact_observation")
requirements = set(re.findall(r"\b(?:R-[A-Z]+-\d+|NFR-[A-Z]+-\d+)\b", texts[ROOT / "docs/requirements.md"]))
trace = texts[ROOT / "docs/traceability.md"]
result = {
    "observed_at": datetime.now(timezone.utc).isoformat(),
    "scope": "structural documentation inspection; no runtime or external source validation",
    "python": sys.version.split()[0], "pyyaml": yaml.__version__,
    "documents": len(FILES), "yaml_blocks": sum(map(len, blocks.values())), "yaml_errors": errors,
    "local_markdown_links": local_count, "local_link_errors": link_errors,
    "requirements": len(requirements), "missing_traceability_ids": sorted(x for x in requirements if x not in trace),
    "implicit_yaml_booleans": implicit_booleans,
    "profile_comparison": {
        "same_id_revision": (contract_profile["id"], contract_profile["profile_revision"]) == (adapter_profile["id"], adapter_profile["profile_revision"]),
        "contract_modes": contract_profile["supports"]["modes"],
        "adapter_modes": adapter_profile["supports"]["modes"],
        "contract_limit_keys": sorted(contract_profile["limits"]),
        "adapter_limit_keys": sorted(adapter_profile["limits"]),
        "contract_camera_keys": sorted(contract_profile["supports"]["camera_controls"]),
        "adapter_camera_keys": sorted(adapter_profile["supports"]["camera_controls"]),
    },
    "prompt_view_omissions": {
        "contract_has_top_level": "omissions" in contract_view,
        "adapter_has_top_level": "omissions" in adapter_view,
        "adapter_nested_only": "omissions" in adapter_view.get("compiled_view", {}),
    },
    "observation_example": {"aggregate": observation["status"], "checks": [x["result"] for x in observation["checks"]]},
    "docs_sha256": manifest,
}
print(json.dumps(result, indent=2, ensure_ascii=False))
