"""Reject cached timelines whose source contains dropped placement behavior."""
from __future__ import annotations

import json
from pathlib import Path
import re

if __package__:
    from .import_guards import finite_numbers, validate_wrapper_fields
else:
    from import_guards import finite_numbers, validate_wrapper_fields


def placement_requirements(reports: list[dict]) -> dict:
    catalog = {}
    for report in reports:
        records = []
        for failure in report['failures']:
            match = re.search(r'/(root|DefineSprite_(\d+))/frame_(\d+)$', failure['source'])
            if not match:
                raise ValueError('Missing placement diagnostic location: ' + failure['source'])
            if not failure['construct'].startswith('PlaceObject') and failure['construct'] != 'morph ratio':
                continue
            records.append({'sprite': int(match[2] or 0), 'frame': int(match[3]), **failure})
        catalog[report['sha256']] = {'swf': report['source_swf'], 'records': records, 'obligations': report.get('placement_obligations', []),
                                  'clip_action_obligations': report.get('clip_action_obligations', []),
                                  'wrapper_obligations': report.get('wrapper_obligations', [])}
    return catalog


def validate_wrapper_obligation(wrapper: dict, fields: dict, source: str) -> None:
    validate_wrapper_fields(fields, source)
    for field in ('filters', 'blend_mode'):
        if field not in fields:
            continue
        finite_numbers(wrapper.get(field), f'{source}/{field}')
        actual = json.dumps(wrapper.get(field), sort_keys=True, allow_nan=False)
        expected = json.dumps(fields[field], sort_keys=True, allow_nan=False)
        if actual != expected:
            raise ValueError(f'{source}: dropped/changed wrapper {field}')


def load_placement_catalog() -> dict:
    return json.loads(Path(__file__).with_name('placement_requirements.json').read_text())


def validate_build_placements(timeline: dict, source: str, catalog: dict | None = None) -> None:
    if catalog is None:
        catalog = load_placement_catalog()
    digest = timeline.get('source_swf', {}).get('sha256')
    if digest is None:
        visual = json.loads(Path(__file__).with_name('visual_control_requirements.json').read_text())
        digest = visual['_xml_sources'].get(timeline.get('source_xml', {}).get('sha256'))
    if digest not in catalog:
        raise ValueError(f'{source}: missing placement audit for source SWF {digest}')
    for obligation in catalog[digest].get('wrapper_obligations', []):
        if obligation['character_id'] == timeline['sprite_id']:
            validate_wrapper_obligation(timeline.get('wrapper', {}), obligation['fields'],
                f"{source}: {catalog[digest]['swf']}/root/frame_{obligation['frame']}/depth_{obligation['depth']}")
    wrapper = timeline.get('wrapper')
    if wrapper:
        wrapper_source = (f"{source}: {catalog[digest]['swf']}/root/"
                          f"frame_{wrapper['root_frame']}/depth_{wrapper['depth']}")
        validate_wrapper_fields(wrapper, wrapper_source)
        for obligation in catalog[digest].get('obligations', []):
            if (obligation['sprite'] == 0 and obligation['frame'] == wrapper['root_frame']
                    and obligation['depth'] == wrapper['depth']):
                validate_wrapper_obligation(wrapper, obligation['fields'], wrapper_source)
    root_frames = {frame['frame'] for frame in timeline['frames']}
    nested = {d['character_id'] for d in timeline['definitions'] if d['type'] == 'DefineSpriteTag'}
    for record in catalog[digest]['records']:
        if record['sprite'] in nested or (record['sprite'] == timeline['sprite_id'] and
                                           any(record['frame'] <= frame <= record.get('last_frame', record['frame'])
                                               for frame in root_frames)):
            raise ValueError(f"{source}: {record['source']}: {record['error']}")

    definitions = {d['character_id']: d for d in timeline['definitions']}
    frames = {f['frame']: f['display_list'] for f in timeline['frames']}
    for obligation in catalog[digest].get('obligations', []):
        sprite, frame = obligation['sprite'], obligation['frame']
        if sprite != timeline['sprite_id'] and sprite not in nested:
            continue
        placements = None
        if sprite == timeline['sprite_id']:
            placements = frames.get(frame)
        elif sprite in nested:
            definition = definitions[sprite]
            display_frames = definition.get('display_list_frames')
            if display_frames is not None and frame <= len(display_frames):
                placements = display_frames[frame - 1]
            elif frame == 1:
                placements = definition.get('first_frame_display_list', [])
        if placements is None:
            raise ValueError(f"{source}: missing source timeline frame: {catalog[digest]['swf']} "
                             f"sprite {sprite} frame {frame} depth {obligation['depth']}")
        placement = next((p for p in placements if p['depth'] == obligation['depth']), None)
        if placement is None:
            raise ValueError(f"{source}: missing source placement {catalog[digest]['swf']} sprite {sprite} frame {frame} depth {obligation['depth']}")
        for field, expected in obligation['fields'].items():
            # Python considers True == 1; the renderer does not treat a numeric
            # bitmap-cache flag as an authored boolean. Preserve JSON types.
            finite_numbers(placement.get(field), f"{source}: {catalog[digest]['swf']} sprite {sprite} frame {frame} depth {obligation['depth']} {field}")
            actual = json.dumps(placement.get(field), sort_keys=True, allow_nan=False)
            wanted = json.dumps(expected, sort_keys=True, allow_nan=False)
            if actual != wanted:
                raise ValueError(f"{source}: dropped/changed {field}: {catalog[digest]['swf']} sprite {sprite} frame {frame} depth {obligation['depth']}")

    for obligation in catalog[digest].get('clip_action_obligations', []):
        sprite = obligation['sprite']
        if sprite != timeline['sprite_id'] and sprite not in nested:
            continue
        for frame in range(obligation['first_frame'], obligation['last_frame'] + 1):
            if sprite == timeline['sprite_id']:
                placements = frames.get(frame, [])
            else:
                definition = definitions[sprite]
                display_frames = definition.get('display_list_frames', [])
                placements = (display_frames[frame - 1] if frame <= len(display_frames)
                              else definition.get('first_frame_display_list', []) if frame == 1 else [])
            placement = next((p for p in placements if p['depth'] == obligation['depth']), None)
            if placement is None or placement.get('clip_actions') != obligation['clip_actions']:
                raise ValueError(f"{source}: dropped/changed clip_actions: {catalog[digest]['swf']} "
                                 f"sprite {sprite} frame {frame} depth {obligation['depth']}")
