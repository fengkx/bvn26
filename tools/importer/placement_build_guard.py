"""Reject cached timelines whose source contains dropped placement behavior."""
from __future__ import annotations

import json
from pathlib import Path
import re


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
        catalog[report['sha256']] = {'swf': report['source_swf'], 'records': records, 'obligations': report.get('placement_obligations', [])}
    return catalog


def validate_build_placements(timeline: dict, source: str) -> None:
    catalog = json.loads(Path(__file__).with_name('placement_requirements.json').read_text())
    digest = timeline.get('source_swf', {}).get('sha256')
    if digest is None:
        visual = json.loads(Path(__file__).with_name('visual_control_requirements.json').read_text())
        digest = visual['_xml_sources'].get(timeline.get('source_xml', {}).get('sha256'))
    if digest not in catalog:
        raise ValueError(f'{source}: missing placement audit for source SWF {digest}')
    root_frames = {frame['frame'] for frame in timeline['frames']}
    nested = {d['character_id'] for d in timeline['definitions'] if d['type'] == 'DefineSpriteTag'}
    for record in catalog[digest]['records']:
        if record['sprite'] in nested or (record['sprite'] == timeline['sprite_id'] and
                                           record['frame'] in root_frames):
            raise ValueError(f"{source}: {record['error']}")

    definitions = {d['character_id']: d for d in timeline['definitions']}
    frames = {f['frame']: f['display_list'] for f in timeline['frames']}
    for obligation in catalog[digest].get('obligations', []):
        sprite, frame = obligation['sprite'], obligation['frame']
        placements = None
        if sprite == timeline['sprite_id'] and frame in frames:
            placements = frames[frame]
        elif sprite in nested:
            definition = definitions[sprite]
            display_frames = definition.get('display_list_frames')
            if display_frames is not None and frame <= len(display_frames):
                placements = display_frames[frame - 1]
            elif frame == 1:
                placements = definition.get('first_frame_display_list', [])
        if placements is None:
            continue
        placement = next((p for p in placements if p['depth'] == obligation['depth']), None)
        if placement is None:
            raise ValueError(f"{source}: missing source placement {catalog[digest]['swf']} sprite {sprite} frame {frame} depth {obligation['depth']}")
        for field, expected in obligation['fields'].items():
            if placement.get(field) != expected:
                raise ValueError(f"{source}: dropped/changed {field}: {catalog[digest]['swf']} sprite {sprite} frame {frame} depth {obligation['depth']}")
