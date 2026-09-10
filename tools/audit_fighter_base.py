"""Retain the source questions for a base fighter without asserting parity."""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def audit(fighter):
    paths = [f'scripts/fighter/{fighter}.json', f'data/slices/{fighter}-base.timeline.json',
             f'godot/generated/fighters/{fighter}/combat.json']
    bundle, timeline, model = [json.loads((ROOT / path).read_text()) for path in paths]
    prefix = f'DefineSprite_{timeline["sprite_id"]}/'
    scripts = [s for s in bundle['scripts'] if s['path'].startswith(prefix)]
    frame_scripts = {}
    callbacks = {}
    for script in scripts:
        match = re.fullmatch(prefix + r'frame_(\d+)/DoAction(?:_\d+)?\.as', script['path'])
        if match:
            frame_scripts.setdefault(int(match[1]), []).append(script)
        match = re.fullmatch(prefix + r'frame_(\d+)/PlaceObject[23]_(\d+)_(\d+)/CLIPACTIONRECORD onClipEvent\(enterFrame\).as', script['path'])
        if match:
            callbacks[tuple(map(int, match.groups()))] = script['path']
    labels = [entry for entry in model['command_catalog']['entries'] if entry['start_frame'] is not None]
    frames = []
    for frame in timeline['frames']:
        label = next(entry['label'] for entry in labels if entry['start_frame'] <= frame['frame'] <= entry['end_frame'])
        active = []
        for placement in frame['display_list']:
            key = (placement['placed_frame'], placement.get('character_id'), placement['depth'])
            if key in callbacks:
                active.append({'path': callbacks[key], 'placed_frame': key[0],
                               'eligible_next_display': frame['frame'] > key[0]})
        frames.append({'frame': frame['frame'], 'label': label,
                       'deferred': label == '万解',
                       'scripts': frame_scripts.get(frame['frame'], []),
                       'changes': frame['changes'], 'enter_frame_callbacks': active})
    return {'status': 'source_inventory_not_behavior_acceptance', 'fighter': fighter,
            'source_hashes': {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths},
            'source_swf': timeline['source_swf'], 'base_sprite': timeline['sprite_id'],
            'deferred_labels': ['万解'], 'frames': frames,
            'exits': model['action_exits'], 'fallthroughs': model['timeline_fallthroughs'],
            'cancel_windows': model['command_catalog'].get('cancel_windows', []),
            'invariants': ['Only the selected base sprite supplies callbacks and attack parameters.',
                           'New placements begin enterFrame callbacks on the following display.',
                           'A label end is not an implicit goto; exits and fallthroughs are separate.',
                           'Same-input original traces must establish expected states; setup is not an expectation.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('fighter')
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    result = audit(args.fighter)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'frames': len(result['frames']), 'status': result['status']}))


if __name__ == '__main__':
    main()
