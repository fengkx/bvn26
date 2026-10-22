"""Require an owner for every retained nested self-playhead instruction."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
SELF_CALL = re.compile(r'(?<![\w.])(stop|play|gotoAndPlay|gotoAndStop)\s*\(([^()]*)\)\s*;')
CONTROL_WORD = re.compile(r'(?<![\w.])(?:stop|play|gotoAndPlay|gotoAndStop)\s*\(')


def requirements(bundle: dict) -> dict:
    """Small build input: source hashes and required controls, never AS code."""
    records = []
    for script in bundle['scripts']:
        match = re.fullmatch(r'DefineSprite_(\d+)(?:_[^/]+)?/frame_(\d+)/DoAction.as', script['path'])
        text = script['source']
        if not match or not CONTROL_WORD.search(text):
            continue
        record = {'sprite': int(match[1]), 'frame': int(match[2]), 'path': script['path'],
                  'source_sha256': hashlib.sha256(text.encode()).hexdigest()}
        expected = []
        error = None
        calls = list(SELF_CALL.finditer(text))
        if re.search(r'\b(?:if|else|function|while|for|switch)\s*[({]', text):
            error = 'nested conditional/function playhead control needs an owner'
        elif len(calls) != len(CONTROL_WORD.findall(text)):
            error = 'unsupported nested playhead argument form'
        for call in calls:
            method, argument = call[1], call[2].strip()
            if method in ('stop', 'play') and not argument:
                expected.append({'op': method})
            elif method in ('gotoAndPlay', 'gotoAndStop'):
                if re.fullmatch(r'"[^"\n]+"', argument):
                    target = {'label': json.loads(argument)}
                elif re.fullmatch(r'[1-9]\d*', argument):
                    target = {'frame': int(argument)}
                else:
                    error = f'unsupported nested {method} argument {argument!r}'
                    continue
                expected.extend([{'op': 'goto', **target},
                                 {'op': 'play' if method == 'gotoAndPlay' else 'stop'}])
            else:
                error = f'unsupported nested {method} argument {argument!r}'
        record.update(expected=expected, error=error)
        records.append(record)
    return {'game_file': bundle['game_file'], 'swf_sha256': bundle['swf_sha256'], 'records': records}


def validate_requirements(timeline: dict, required: dict, delegates: list[dict] | None = None) -> None:
    if delegates is None:
        delegates = json.loads(Path(__file__).with_name('visual_control_owners.json').read_text())
    source = required['game_file']
    if timeline['source_swf']['sha256'] != required['swf_sha256']:
        raise ValueError(f'{source}: nested control source hash mismatch')
    definitions = {int(d['character_id']): d for d in timeline['definitions']}
    for record in required['records']:
        if record['sprite'] not in definitions:
            continue
        location = f"{source}/{record['path']}"
        if any(owner['swf_sha256'] == required['swf_sha256'] and owner['path'] == record['path']
               and owner['source_sha256'] == record['source_sha256'] and owner['reason'] and owner['consumer']
               for owner in delegates):
            continue
        if record['error']:
            raise ValueError(f"{location}: {record['error']}")
        events = definitions[record['sprite']].get('display_list_frame_events', [])
        frame = record['frame']
        actual = [control for event in (events[frame - 1] if len(events) >= frame else [])
                  for control in event.get('visual_controls', [])]
        if actual != record['expected']:
            raise ValueError(f"{location}: dropped/changed nested playhead control; "
                             f"expected {record['expected']!r}, compiled {actual!r}")


def validate_nested_controls(timeline: dict, bundle: dict, delegates: list[dict] | None = None) -> None:
    validate_requirements(timeline, requirements(bundle), delegates)


def validate_build_controls(timeline: dict, source: str) -> None:
    catalog = json.loads(Path(__file__).with_name('visual_control_requirements.json').read_text())
    digest = timeline.get('source_swf', {}).get('sha256')
    if digest is None:
        digest = catalog['_xml_sources'].get(timeline.get('source_xml', {}).get('sha256'))
        if digest:
            timeline = {**timeline, 'source_swf': {'sha256': digest}}
    if digest not in catalog:
        raise ValueError(f'{source}: missing reviewed visual control requirements for SWF {digest}')
    validate_requirements(timeline, catalog[digest])


if __name__ == '__main__':
    catalog = {}
    for path in sorted((ROOT / 'scripts').rglob('*.json')):
        bundle = json.loads(path.read_text())
        if 'swf_sha256' in bundle and 'scripts' in bundle:
            catalog[bundle['swf_sha256']] = requirements(bundle)
    catalog['_xml_sources'] = {}
    for path in sorted((ROOT / 'godot/generated').rglob('timeline.json')):
        timeline = json.loads(path.read_text())
        if timeline.get('source_swf'):
            catalog['_xml_sources'][timeline['source_xml']['sha256']] = timeline['source_swf']['sha256']
    Path(__file__).with_name('visual_control_requirements.json').write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + '\n')
