"""Retain all source frames and pin fresh strict compilation obligations."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools/importer'))
from compile_ai_context import compile_context
from frame_call_guard import calls_digest, validate_cached_frame_calls


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


bundle = json.loads((ROOT / 'scripts/fighter/sasukexz.json').read_text())
directory = ROOT / 'godot/generated/fighters/sasukexz'
timeline = json.loads((directory / 'timeline.json').read_text())
compiled = compile_context(bundle, timeline)
cached = json.loads((directory / 'ai.json').read_text())
assert compiled['frame_calls'] == cached['frame_calls']
requirements_path = ROOT / 'tools/importer/frame_call_requirements.json'
requirements = json.loads(requirements_path.read_text())
key = f"{bundle['swf_sha256']}:{timeline['sprite_id']}"
entry = {'source': bundle['game_file'], 'frames': {
    frame: calls_digest(calls) for frame, calls in compiled['frame_calls'].items()}}
for name in ('placement_filter_initialization', 'nested_stage_frames', 'parent_initial_values'):
    if compiled.get(name):
        entry[name] = compiled[name]
requirements[key] = entry
validate_cached_frame_calls(timeline, cached, requirements, directory=directory)
write(requirements_path, requirements)
scripts = {item['path']: item['source'] for item in bundle['scripts']}
source_timeline = json.loads((ROOT / 'data/slices/sasukexz-base.timeline.json').read_text())
frames = []
for frame in source_timeline['frames']:
    number = frame['frame']
    path = f'DefineSprite_727/frame_{number}/DoAction.as'
    frames.append({'frame': number, 'labels': frame['labels'],
                   'script_path': path if path in scripts else None,
                   'source': scripts.get(path, ''), 'changes': frame.get('changes', []),
                   'events': frame.get('events', []),
                   'compiled_calls': compiled['frame_calls'].get(str(number), [])})
write(Path(__file__).with_name('source-inventory.json'), {
    'source': bundle['game_file'], 'source_sha256': bundle['swf_sha256'],
    'body_sprite': 727, 'frames': frames,
    'scripts': bundle['scripts'], 'strict_compile_matches_cached_calls': True,
    'original_player_observation': 'pending'})
print(json.dumps({'frames': len(frames), 'scripts': len(scripts),
                  'compiled_call_frames': len(compiled['frame_calls']), 'guard': 'passed'}))
