#!/usr/bin/env python3
"""Reproduce offline package, behavior, provenance, HTTP and native-media checks.

Does not queue generation, call a provider, download models or change the skill.
"""
import argparse
import ast
import contextlib
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import unittest
from urllib.parse import unquote, urlsplit

ROOT=Path(__file__).resolve().parents[1]
SKILL=ROOT/'.agents/skills/video-generation-engineering'


def import_cycle_audit(root=None):
    """Find cycles in the Skill's static local-module import graph."""
    root = Path(root or (SKILL / 'scripts')).resolve()
    modules = {path.stem: path for path in root.glob('*.py') if path.is_file() and path.name != '__init__.py'}
    graph = {name: set() for name in modules}
    errors = []
    for name, path in modules.items():
        try:
            tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
        except (OSError, SyntaxError, UnicodeError) as exc:
            errors.append(f'{name}: cannot parse for import-cycle audit ({type(exc).__name__})')
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    candidate = alias.name.split('.')[0]
                    if candidate in modules:
                        graph[name].add(candidate)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                candidate = node.module.split('.')[0]
                if candidate in modules:
                    graph[name].add(candidate)

    cycles = []
    visiting, visited = set(), set()

    def visit(name, path):
        if name in visiting:
            cycle = path[path.index(name):]
            normalized = tuple(cycle)
            reverse = tuple(reversed(cycle))
            if normalized not in cycles and reverse not in cycles:
                cycles.append(normalized)
            return
        if name in visited:
            return
        visiting.add(name)
        for dependency in sorted(graph[name]):
            visit(dependency, path + [dependency])
        visiting.remove(name)
        visited.add(name)

    for name in sorted(graph):
        visit(name, [name])
    for cycle in cycles:
        errors.append('import cycle: ' + ' -> '.join(cycle))
    return {'status': 'PASS' if not errors else 'FAIL', 'modules': sorted(modules),
            'cycles': [list(cycle) for cycle in cycles], 'errors': sorted(errors),
            'scope': str(root)}


def production_media_summary():
    """Re-check checked-in media mechanically without promoting semantic quality."""
    sys.path.insert(0, str(SKILL/'scripts'))
    try:
        from vge_media import media_qa
    except Exception as exc:
        return {"status": "BLOCKED", "error": type(exc).__name__, "artifacts": [],
                "limitations": ["Quality module could not be imported"]}
    artifacts = []
    roots = [ROOT/'artifacts', ROOT/'verification']
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob('*')):
            if not path.is_file() or path.suffix.lower() not in ('.mp4', '.mov', '.mkv', '.webm', '.gif'):
                continue
            try:
                report = media_qa(path, allow_black=True)
                artifacts.append({"path": str(path.relative_to(ROOT)), "content_hash": report["content_hash"],
                                  "status": report["status"], "checks": {item["id"]: item["result"] for item in report["checks"]}})
            except Exception as exc:
                artifacts.append({"path": str(path.relative_to(ROOT)), "status": "BLOCKED", "error": type(exc).__name__})
    if not artifacts:
        status = "NOT_RUN"
    elif any(item["status"] == "BLOCKED" for item in artifacts):
        status = "BLOCKED"
    elif any(item["status"] == "FAIL" for item in artifacts):
        status = "PARTIAL"
    elif any(item["status"] in ("PARTIAL", "NOT_OBSERVED") for item in artifacts):
        status = "PARTIAL"
    else:
        status = "PASS"
    return {"status": status, "artifacts": artifacts,
            "limitations": ["This is mechanical media QA only; semantic identity, physics, emotion, story, continuity, editorial quality and lip-sync remain separate observations"]}


def manifest():
    return {str(p.relative_to(SKILL)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(SKILL.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output');args=parser.parse_args()
    started=datetime.now(timezone.utc).isoformat();before=manifest();errors=[];links=0
    import_audit = import_cycle_audit()
    if import_audit['status'] != 'PASS':
        errors.append('Import-cycle audit failed')
    text=(SKILL/'SKILL.md').read_text()
    front=re.match(r'\A---\n(.*?)\n---\n',text,re.S)
    if not front or not re.search(r'^name: video-generation-engineering$',front[1],re.M) or not re.search(r'^description: .{20,}',front[1],re.M):errors.append('Invalid skill frontmatter')
    for p in SKILL.rglob('*.md'):
        clean=re.sub(r'^```[^\n]*\n.*?^```','',p.read_text(),flags=re.M|re.S)
        for target in re.findall(r'\[[^\]\n]*\]\(([^)\n]+)\)',clean):
            url=urlsplit(target.strip('<>'))
            if url.scheme or url.netloc:continue
            links+=1;dest=(p.parent/unquote(url.path)).resolve() if url.path else p.resolve()
            if not dest.is_relative_to(SKILL.resolve()):errors.append(f'Package dependency escapes skill: {p.name}/{target}')
            elif not dest.exists():errors.append(f'Missing resource: {p.name}/{target}')
            elif url.fragment and dest.suffix=='.md':
                anchors={re.sub(r'[^\w\- ]','',h.lower()).replace(' ','-') for h in re.findall(r'^#{1,6}\s+(.+)$',dest.read_text(),re.M)}
                if unquote(url.fragment) not in anchors:errors.append(f'Missing anchor: {target}')
    # Pin the repository root as unittest's import root so every checked-in
    # test module is discovered consistently with the documented full-suite
    # command, including tests added outside the original package subset.
    sys.path.insert(0,str(ROOT))
    sys.path.insert(0,str(ROOT/'tests'))
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'), pattern='test*.py', top_level_dir=str(ROOT/'tests'))
    stream=io.StringIO()
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    if result.skipped:errors.append('Suite unexpectedly skipped tests')
    if not result.wasSuccessful():errors.append('Behavior suite failed')
    after=manifest()
    if after!=before:errors.append('Product changed during verification')
    quality = production_media_summary()
    report={'schema_version':1,'observed_at':started,'completed_at':datetime.now(timezone.utc).isoformat(),'status':'FAIL' if errors else 'PASS',
            'scope':'OFFLINE_PACKAGE_AND_EXECUTABLE_CONTRACTS','python':sys.version.split()[0],'tests_run':result.testsRun,'failures':len(result.failures),'errors':errors,'skipped':len(result.skipped),
            'local_package_links':links,'package_manifest_sha256':hashlib.sha256(json.dumps(after,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
            'package_files_sha256':after,'test_output':stream.getvalue(),
            'limitations':['Unit/integration tests and fake provider are not real paid-provider execution','Native synthetic media tests do not certify generated-media quality','Independent forward-use and real ComfyUI generation have separate dated evidence'],
            'production_media_quality': quality,
            'import_cycle_audit': import_audit,
            'production_gate_status': 'PARTIAL' if quality['status'] not in ('PASS',) else 'MECHANICAL_ONLY',
            'quality_policy': 'Mechanical media findings are reported separately from offline software status; semantic PASS requires category/oracle/evidence-bound observations.'}
    if args.output:
        p=Path(args.output);p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('x') as f:json.dump(report,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('test_output','package_files_sha256')},ensure_ascii=False,indent=2))
    if errors:print(stream.getvalue(),file=sys.stderr)
    return bool(errors)


if __name__=='__main__':sys.exit(main())
