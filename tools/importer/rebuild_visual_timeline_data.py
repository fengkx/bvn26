"""Refresh visual controls and blend fields without changing combat compilation.

Cached XML uses the pinned source_xml hash. Missing exports are generated
from the immutable SWF with the specified JPEXS executable jar.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from extract_timeline_geometry import build_frames, extract_wrapper_placement


def merge_controls(events, source_events):
    for event in source_events:
        if not event.get('visual_controls'):
            continue
        prior = next((old for old in events if old.get('sha256') == event.get('sha256')), None)
        if prior is None:
            events.append(event.copy())
        else:
            prior['visual_controls'] = event['visual_controls']
    return events


def update_frames(frames, source_frames):
    by_frame = {f['frame']: f for f in source_frames}
    for frame in frames:
        source = by_frame[frame['frame']]
        for key in ['display_list', 'changes']:
            if key not in frame:
                continue
            for old, new in zip(frame.get(key, []), source.get(key, []), strict=True):
                for field in ['depth', 'character_id', 'placed_frame', 'matrix', 'color_transform', 'name']:
                    if field in old and field in new:
                        assert old[field] == new[field], (frame['frame'], field, old[field], new[field])
                if 'blend_mode' in new:
                    old['blend_mode'] = new['blend_mode']
        frame['events'] = merge_controls(frame.get('events', []), source['events'])


def rebuild(path: Path, root: ET.Element):
    data = json.loads(path.read_text())
    sprites = {int(t.attrib['spriteId']): t for t in root.findall('./tags/item')
               if t.get('type') == 'DefineSpriteTag'}
    sprite_id = data['sprite_id']
    tags = root.findall('./tags/item') if sprite_id == 0 else sprites[sprite_id].findall('./subTags/item')
    update_frames(data['frames'], build_frames(tags))
    if sprite_id != 0:
        wrapper = extract_wrapper_placement(root, sprite_id)
        if wrapper and 'blend_mode' in wrapper:
            data.setdefault('wrapper', {})['blend_mode'] = wrapper['blend_mode']
    for definition in data['definitions']:
        if definition['type'] != 'DefineSpriteTag':
            continue
        frames = build_frames(sprites[definition['character_id']].findall('./subTags/item'))
        if 'display_list_frames' not in definition:
            # Some stage slices intentionally retain only a static first frame.
            update_frames([{'frame': 1, 'display_list': definition.get('first_frame_display_list', [])}], frames)
            continue
        old_frames = [{'frame': i + 1, 'display_list': placements}
                      for i, placements in enumerate(definition['display_list_frames'])]
        update_frames(old_frames, frames)
        definition['first_frame_display_list'] = old_frames[0]['display_list'] if old_frames else []
        prior_events = definition.get('display_list_frame_events', [[] for _ in frames])
        events = [merge_controls(old, frame['events']) for old, frame in zip(prior_events, frames, strict=True)]
        if 'display_list_frame_events' in definition or any(events):
            definition['display_list_frame_events'] = events
        labels = {label: f['frame'] for f in frames for label in f['labels']}
        if labels:
            definition['frame_labels'] = labels
    temporary = path.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--xml-cache', type=Path, required=True)
    parser.add_argument('--ffdec', type=Path, required=True)
    parser.add_argument('--cached-paths', type=Path)
    parser.add_argument('--generated', type=Path, default=Path('godot/generated'))
    args = parser.parse_args()
    args.xml_cache.mkdir(parents=True, exist_ok=True)
    cached = {}
    if args.cached_paths:
        for name in args.cached_paths.read_text().splitlines():
            path = Path(name)
            cached[hashlib.sha256(path.read_bytes()).hexdigest()] = path
    roots = {}
    for path in sorted(args.generated.rglob('timeline.json')):
        data = json.loads(path.read_text())
        digest = data['source_xml']['sha256']
        if digest not in roots:
            xml = cached.get(digest)
            if xml is None:
                source = data['source_swf']
                swf = Path(source['path'])
                assert hashlib.sha256(swf.read_bytes()).hexdigest() == source['sha256']
                xml = args.xml_cache / (source['sha256'] + '.xml')
                if not xml.exists():
                    subprocess.run(['java', '-Djava.awt.headless=true', '-jar', str(args.ffdec),
                                    '-swf2xml', str(swf), str(xml)], check=True,
                                   stdout=subprocess.DEVNULL)
                # Export versions can differ; update_frames checks every retained
                # placement field before adding the new source-derived metadata.
            roots[digest] = ET.parse(xml).getroot()
        rebuild(path, roots[digest])
        print(path, flush=True)


if __name__ == '__main__':
    main()
