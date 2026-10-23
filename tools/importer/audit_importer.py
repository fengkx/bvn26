"""Audit locked SWFs without retaining large XML exports or changing game output.

Every failure retains its source location. This is an inventory, not proof that
all AS semantics have a native consumer. Exit nonzero when a guard rejects input.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import xml.etree.ElementTree as ET

from extract_timeline_geometry import placement_delta, visual_control_actions
from compile_ai_context import compile_context
from visual_control_guard import validate_build_controls
from placement_build_guard import placement_requirements

ROOT = Path(__file__).resolve().parents[2]


def audit_xml(root: ET.Element, source: str) -> dict:
    failures = []
    counts = Counter()
    action_inventory = []
    obligations = []
    clip_obligations = []
    wrapper_obligations = []
    wrapper_characters = set()
    definitions = {int(t.get('spriteId')): t for t in root.findall('./tags/item')
                   if t.get('type') == 'DefineSpriteTag'}
    all_definitions = {}
    for t in root.findall('./tags/item'):
        for key in ('characterID', 'shapeId', 'spriteId'):
            if t.get(key) is not None:
                all_definitions[int(t.get(key))] = t.get('type')
    timelines = [('root', root.findall('./tags/item'))] + [
        (f'DefineSprite_{key}', value.findall('./subTags/item'))
        for key, value in definitions.items()]
    for owner, tags in timelines:
        frame = 1
        display = {}
        field_state = {}
        clip_state = {}
        last_clip_ranges = {}
        for tag in tags:
            kind = tag.get('type')
            location = f'{source}/{owner}/frame_{frame}'
            if kind == 'ShowFrameTag':
                for depth, actions in clip_state.items():
                    previous = last_clip_ranges.get(depth)
                    if (previous is not None and previous['last_frame'] == frame - 1
                            and previous['clip_actions'] == actions):
                        previous['last_frame'] = frame
                    else:
                        interval = {'sprite': 0 if owner == 'root' else int(owner.split('_')[1]),
                                    'first_frame': frame, 'last_frame': frame, 'depth': int(depth),
                                    'clip_actions': actions}
                        clip_obligations.append(interval)
                        last_clip_ranges[depth] = interval
                for depth, fields in field_state.items():
                    if fields:
                        obligations.append({'sprite': 0 if owner == 'root' else int(owner.split('_')[1]),
                                            'frame': frame, 'depth': int(depth), 'fields': fields.copy()})
                frame += 1
            elif kind in ('RemoveObjectTag', 'RemoveObject2Tag'):
                field_state.pop(tag.get('depth'), None)
                clip_state.pop(tag.get('depth'), None)
                display.pop(tag.get('depth'), None)
            elif kind and kind.startswith('PlaceObject'):
                counts['placements'] += 1
                counts[f'placement_tag:{kind}'] += 1
                try:
                    delta = placement_delta(tag, location)
                    depth = tag.get('depth')
                    character = delta.get('character_id')
                    if owner == 'root' and character is not None and character not in wrapper_characters:
                        wrapper_characters.add(character)
                        fields = {key: delta[key] for key in
                                  ('filters', 'color_transform', 'cache_as_bitmap', 'clip_depth', 'ratio') if key in delta}
                        if fields:
                            wrapper_obligations.append({'character_id': character, 'frame': frame,
                                                        'depth': int(depth), 'fields': fields})
                    previous = field_state.get(depth, {}) if delta['move'] else {}
                    if not delta['move']:
                        clip_state.pop(depth, None)
                    if 'clip_actions' in delta:
                        clip_state[depth] = delta['clip_actions']
                    field_state[depth] = {**previous, **{key: delta[key] for key in
                        ('filters', 'cache_as_bitmap', 'blend_mode', 'color_transform') if key in delta}}
                except ValueError as error:
                    failures.append({'source': location, 'construct': kind, 'error': str(error),
                                     'depth': int(tag.get('depth')),
                                     'placement_xml': ET.tostring(tag, encoding='unicode').strip()})
                depth = tag.get('depth')
                if tag.get('characterId'):
                    display[depth] = int(tag.get('characterId'))
                if tag.get('ratio'):
                    target = all_definitions.get(display.get(depth))
                    counts[f'ratio_target:{target}'] += 1
                    if target and target.startswith('DefineMorphShape'):
                        failures.append({'source': location, 'construct': 'morph ratio',
                                         'error': 'Morph interpolation has no native renderer'})
                for record in tag.findall('./clipActions/clipActionRecords/item'):
                    flags = record.find('eventFlags')
                    if flags is not None:
                        for flag, value in flags.attrib.items():
                            if value == 'true':
                                counts[f'clip_action:{flag}'] += 1
            elif kind == 'DoActionTag':
                counts['action_blocks'] += 1
                encoded = tag.get('actionBytes', '')
                try:
                    controls = visual_control_actions(encoded)
                    if not controls:
                        action_inventory.append({'source': location,
                            'sha256': hashlib.sha256(encoded.encode('ascii')).hexdigest(),
                            'status': 'requires_nonvisual_owner_review'})
                except ValueError as error:
                    failures.append({'source': location, 'construct': kind, 'error': str(error)})
    return {'source_swf': source, 'counts': dict(sorted(counts.items())),
            'failures': failures, 'placement_obligations': obligations,
            'clip_action_obligations': clip_obligations, 'wrapper_obligations': wrapper_obligations,
            'nonvisual_action_blocks': action_inventory}


def skip_sites() -> list[dict]:
    sites = []
    for path in sorted((ROOT / 'tools/importer').glob('*.py')):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            reason = None
            if isinstance(node, (ast.Continue, ast.Pass)):
                reason = type(node).__name__
            elif isinstance(node, ast.Return):
                if node.value is None or isinstance(node.value, ast.Constant) and node.value.value is None:
                    reason = 'return None'
                elif isinstance(node.value, (ast.List, ast.Dict)) and not (
                    node.value.elts if isinstance(node.value, ast.List) else node.value.keys):
                    reason = 'return empty'
            if reason:
                sites.append({'path': str(path.relative_to(ROOT)), 'line': node.lineno,
                              'construct': reason, 'status': 'requires_review'})
    return sites


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ffdec', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--write-placement-requirements', type=Path)
    args = parser.parse_args()
    reports = []
    with tempfile.TemporaryDirectory(prefix='bvn-loud-audit-') as directory:
        scratch = Path(directory)
        for swf in sorted((ROOT / 'game').rglob('*.swf')):
            xml = scratch / 'source.xml'
            subprocess.run(['java', f'-Duser.home={scratch}', '-Djava.awt.headless=true',
                            '-jar', str(args.ffdec), '-swf2xml', str(swf), str(xml)],
                           check=True, stdout=subprocess.DEVNULL)
            report = audit_xml(ET.parse(xml).getroot(), str(swf.relative_to(ROOT)))
            report['sha256'] = hashlib.sha256(swf.read_bytes()).hexdigest()
            reports.append(report)
            xml.unlink()
            print(report['source_swf'], len(report['failures']), 'failures', flush=True)
    if args.write_placement_requirements:
        args.write_placement_requirements.write_text(
            json.dumps(placement_requirements(reports), ensure_ascii=False, indent=2) + '\n')
    shipped = []
    for path in sorted((ROOT / 'godot/generated/fighters').glob('*/timeline.json')):
        timeline = json.loads(path.read_text())
        source = timeline['source_swf']['path']
        bundle = json.loads((ROOT / source.replace('game/', 'scripts/').replace('.swf', '.json')).read_text())
        row = {'timeline': str(path.relative_to(ROOT)), 'source_swf': source}
        try:
            context = compile_context(bundle, timeline)
            previous = json.loads((path.parent / 'ai.json').read_text())
            row.update(status='passed', unchanged=context == previous)
        except (ValueError, OSError) as error:
            row.update(status='failed', error=str(error))
        shipped.append(row)
    visual_checks = []
    for path in sorted((ROOT / 'godot/generated').rglob('timeline.json')):
        try:
            validate_build_controls(json.loads(path.read_text()), str(path.relative_to(ROOT)))
            visual_checks.append({'path': str(path.relative_to(ROOT)), 'status': 'passed'})
        except ValueError as error:
            visual_checks.append({'path': str(path.relative_to(ROOT)), 'status': 'failed', 'error': str(error)})
    result = {'visual_checks': visual_checks, 'status': 'incomplete_semantic_audit', 'swfs': reports,
              'shipped_contexts': shipped, 'skip_sites': skip_sites()}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    raise SystemExit(1 if any(r['failures'] for r in reports) or
                     any(r['status'] == 'failed' for r in shipped) else 0)


if __name__ == '__main__':
    main()
