#!/usr/bin/env python3
"""Inventory frame-call blockers without treating unresolved calls as harmless."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from compile_ai_context import compile_context
from audit_form_profiles import audit_form_manifest
from frame_call_guard import calls_digest, validate_cached_frame_calls

ROOT = Path(__file__).resolve().parents[2]


def audit() -> dict:
    candidates = []
    bundles = sorted((ROOT / 'scripts').rglob('*.json'))
    for path in bundles:
        bundle = json.loads(path.read_text())
        if 'scripts' not in bundle or 'game_file' not in bundle:
            continue
        for script in bundle['scripts']:
            for number, line in enumerate(script['source'].splitlines(), 1):
                if re.search(r'\bshunbuxg\s*\(|\bshine\s*\([^)]|\bgotoAnd(?:Play|Stop)\s*\([^"\s]', line):
                    candidates.append({'swf': bundle['game_file'], 'swf_sha256': bundle['swf_sha256'],
                                       'path': script['path'], 'line': number, 'text': line.strip(),
                                       'source_sha256': hashlib.sha256(script['source'].encode()).hexdigest(),
                                       'status': 'requires_scope_and_consumer_review'})
    contexts = []
    requirements = {}
    for path in sorted((ROOT / 'godot/generated/fighters').glob('*/timeline.json')):
        timeline = json.loads(path.read_text())
        source = timeline['source_swf']['path']
        bundle = json.loads((ROOT / (source.replace('game/', 'scripts/', 1).removesuffix('.swf') + '.json')).read_text())
        cached = json.loads(path.with_name('ai.json').read_text())
        row = {'source': source, 'timeline': str(path.relative_to(ROOT))}
        key = f"{bundle['swf_sha256']}:{timeline['sprite_id']}"
        try:
            form_contract = None
            if path.with_name('form_profiles.json').is_file():
                form_contract = audit_form_manifest(path.parent, bundle)
            compiled = compile_context(bundle, timeline, form_replacement=form_contract is not None)
            requirements[key] = {'source': source, 'frames': {frame: calls_digest(calls)
                                 for frame, calls in compiled['frame_calls'].items()}}
            if compiled.get('nested_stage_frames'):
                requirements[key]['nested_stage_frames'] = compiled['nested_stage_frames']
            if form_contract is not None:
                requirements[key]['form_profile_contract'] = form_contract
            if compiled.get('parent_initial_values'):
                requirements[key]['parent_initial_values'] = compiled['parent_initial_values']
            row['compile_status'] = 'passed'
            row['changed_frame_calls'] = [
                {'frame': frame, 'expected': compiled['frame_calls'].get(frame, []),
                 'cached': cached.get('frame_calls', {}).get(frame, [])}
                for frame in sorted(set(compiled['frame_calls']) | set(cached.get('frame_calls', {})), key=int)
                if compiled['frame_calls'].get(frame, []) != cached.get('frame_calls', {}).get(frame, [])]
            try:
                validate_cached_frame_calls(timeline, cached, requirements, directory=path.parent)
                row['cache_status'] = 'passed'
            except ValueError as error:
                row.update(cache_status='failed', cache_error=str(error))
        except ValueError as error:
            requirements[key] = {'source': source, 'error': str(error)}
            row.update(compile_status='failed', compile_error=str(error), cache_status='blocked')
        contexts.append(row)
    return {'status': 'incomplete_semantic_audit', 'candidate_scope':
            'All retained script bundles; candidates are not automatically unsupported: nested numeric controls may have native owners.',
            'candidates': candidates, 'shipped_contexts': contexts, 'requirements': requirements}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--write-requirements', type=Path)
    args = parser.parse_args()
    result = audit()
    if args.write_requirements:
        args.write_requirements.write_text(json.dumps(result['requirements'], ensure_ascii=False, indent=2) + '\n')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    passed = sum(row['compile_status'] == 'passed' for row in result['shipped_contexts'])
    print(json.dumps({'contexts': len(result['shipped_contexts']), 'compiled': passed,
                      'cache_passed': sum(row['cache_status'] == 'passed' for row in result['shipped_contexts']),
                      'candidates': len(result['candidates'])}))
    raise SystemExit(1 if any(row['cache_status'] != 'passed' for row in result['shipped_contexts']) else 0)
