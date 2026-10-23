"""Reject stale cached frame calls using source-pinned compilation obligations."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def calls_digest(calls: list[dict]) -> str:
    return hashlib.sha256(json.dumps(calls, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def validate_cached_frame_calls(timeline: dict, cached: dict, catalog: dict | None = None) -> None:
    if catalog is None:
        catalog = json.loads(Path(__file__).with_name('frame_call_requirements.json').read_text())
    digest = timeline.get('source_swf', {}).get('sha256')
    key = f"{digest}:{timeline['sprite_id']}"
    if key not in catalog:
        raise ValueError(f'{key}: missing reviewed frame-call requirements')
    expected = catalog[key]
    source = expected['source']
    if expected.get('error'):
        raise ValueError(expected['error'])
    if cached.get('source_swf') != timeline['source_swf'] or cached.get('sprite_id') != timeline['sprite_id']:
        raise ValueError(f'{source}: cached frame-call source identity mismatch')
    if calls_digest([cached.get('parent_initial_values', {})]) != calls_digest([expected.get('parent_initial_values', {})]):
        raise ValueError(f'{source}:frame_1/DoAction.as: dropped/changed parent initial values')
    actual_calls = cached.get('frame_calls', {})
    for frame in sorted(set(actual_calls) | set(expected['frames']), key=int):
        wanted = expected['frames'].get(frame, calls_digest([]))
        if calls_digest(actual_calls.get(frame, [])) != wanted:
            path = f"DefineSprite_{timeline['sprite_id']}/frame_{frame}/DoAction.as"
            raise ValueError(f'{source}:{path}: dropped/changed cached frame calls')

    def require_effects(calls: list[dict], frame: str) -> None:
        for call in calls:
            if call.get('op') == 'frame_child_effect':
                clip = call['clip']
                asset = Path(__file__).resolve().parents[2] / 'godot/generated/effects' / clip / 'effect.json'
                if not asset.is_file():
                    raise ValueError(f"{source}:DefineSprite_{timeline['sprite_id']}/frame_{frame}: "
                                     f'missing compiled child effect {clip}')
            for field in ('calls', 'else_calls'):
                require_effects(call.get(field, []), frame)

    for frame, calls in actual_calls.items():
        require_effects(calls, frame)
