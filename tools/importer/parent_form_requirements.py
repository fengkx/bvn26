"""Resolve parent-form dependencies without mistaking a parent jump for a body jump.

These records are requirements, not executable events. A caller must not emit a
runtime operation until replacement assets and lifecycle consumers are available.
"""
import hashlib
import re


def parent_form_requirement(bundle: dict, target_frame: int, source: str) -> dict:
    scripts = {s['path']: s['source'] for s in bundle['scripts']}
    pattern = re.compile(rf'frame_{target_frame}/PlaceObject[23]_(\d+)_(\d+)/CLIPACTIONRECORD onClipEvent\(load\)\.as')
    candidates = [(p, pattern.fullmatch(p)) for p in scripts if pattern.fullmatch(p)]
    if len(candidates) != 1:
        raise ValueError(f'{source}: parent frame {target_frame} needs one unambiguous body load, found {len(candidates)}')
    path, match = candidates[0]
    body = int(match[1])
    first = f'DefineSprite_{body}/frame_1/DoAction.as'
    if first not in scripts:
        raise ValueError(f'{source}: missing replacement body initialization: {first}')
    load = scripts[path]
    block = re.fullmatch(r'onClipEvent\(load\)\s*\{(.*?)\}\s*', load, re.S)
    if not block:
        raise ValueError(f'{source}: unsupported parent target load: {path}')
    declarations = []
    for line, text in enumerate(load.splitlines(), 1):
        statement = text.strip()
        if not statement or statement in ('onClipEvent(load){', '{', '}'):
            continue
        assignment = re.fullmatch(r'var (\w+) = (true|false|-?\d+|Key\.isDown);', statement)
        if not assignment:
            raise ValueError(f'{source}: uncompiled replacement load: {path}:{line}: {statement}')
        field, value = assignment.groups()
        operand = ({'binding': 'Key.isDown'} if value == 'Key.isDown' else
                   {'value': value == 'true'} if value in ('true', 'false') else {'value': int(value)})
        declarations.append({'field': field, **operand, 'line': line})
    return {'target_parent_frame': target_frame, 'target_body_sprite': body,
            'target_depth': int(match[2]), 'load_path': path,
            'load_sha256': hashlib.sha256(load.encode()).hexdigest(),
            'load_declarations': declarations, 'body_init_path': first,
            'body_init_sha256': hashlib.sha256(scripts[first].encode()).hexdigest(),
            'source_swf_sha256': bundle['swf_sha256'],
            'status': 'requires_replacement_runtime_and_assets'}
