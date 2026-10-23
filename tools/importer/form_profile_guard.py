"""Validate reviewed native form graphs without source tools in the Web build."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FORMAT = 'bvn26-form-profiles-v1'
METHODS = {'wankai', 'doWanKai', 'initCtrl', 'randAI', 'feixue', 'loseHp'}
FORM_OPS = {'body_form_call', 'parent_form_goto', 'form_prepare_slot', 'form_start_interval'}


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def package_hashes(directory: Path) -> dict[str, str]:
    """Hash executable content, excluding the activation file and editor caches."""
    return {str(path.relative_to(directory)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(directory.rglob('*'))
            if path.is_file() and path.name not in ('form_profiles.json', 'candidate.json')
            and not path.name.endswith(('.uid', '.import'))
            and not any(part.startswith('.') for part in path.relative_to(directory).parts)}


def read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text())
    except (OSError, ValueError) as error:
        raise ValueError(f'{path}: missing or malformed form data') from error
    if not isinstance(value, dict):
        raise ValueError(f'{path}: form data must be an object')
    return value


def form_calls(calls):
    for call in calls:
        if call.get('op') in FORM_OPS:
            yield call
        for field in ('calls', 'else_calls'):
            yield from form_calls(call.get(field, []))


def validate_effect_dependencies(calls: list[dict], source: str, root: Path) -> None:
    for call in calls:
        if call.get('op') == 'frame_child_effect':
            clip = call.get('clip')
            effects = (root / 'godot/generated/effects').resolve()
            if (not isinstance(clip, str) or not clip or Path(clip).name != clip
                    or not (effects / clip / 'effect.json').is_file()):
                raise ValueError(f'{source}: missing compiled child effect {clip}')
        for field in ('calls', 'else_calls'):
            validate_effect_dependencies(call.get(field, []), source, root)


def inspect_form_manifest(directory: Path, root: Path = ROOT) -> tuple[dict, dict]:
    """Check package boundaries and files before either source audit or build."""
    directory = directory.resolve()
    base_root = (root / 'godot/generated/fighters').resolve()
    if directory.parent != base_root:
        raise ValueError(f'{directory}: form manifest must belong to a shipped fighter')
    manifest = read_json(directory / 'form_profiles.json')
    if manifest.get('format') != FORMAT or type(manifest.get('parent_frame')) is not int or manifest['parent_frame'] != 1:
        raise ValueError(f'{directory}: unsupported form manifest format/parent frame')
    profiles = manifest.get('profiles')
    if not isinstance(profiles, dict) or not profiles:
        raise ValueError(f'{directory}: empty form graph')
    nodes = {'1': {'directory': directory, 'sprite_id': manifest.get('base_sprite_id'),
                   'files': manifest.get('base_files')}}
    for frame, entry in profiles.items():
        if not frame.isdecimal() or str(int(frame)) != frame or int(frame) <= 1 or not isinstance(entry, dict):
            raise ValueError(f'{directory}: invalid parent frame {frame}')
        resource = entry.get('directory', '')
        if not isinstance(resource, str) or not resource.startswith('res://generated/forms/'):
            raise ValueError(f'{directory}: form target must be a production forms directory')
        target = (root / 'godot' / resource.removeprefix('res://')).resolve()
        if target.parent != (root / 'godot/generated/forms').resolve():
            raise ValueError(f'{directory}: escaped form target {resource}')
        nodes[frame] = {**entry, 'directory': target}
    for frame, node in nodes.items():
        target = node['directory']
        if not target.is_dir() or not isinstance(node.get('files'), dict) or not node['files']:
            raise ValueError(f'{target}: missing form package hashes')
        actual = package_hashes(target)
        if actual != node['files']:
            changed = sorted(key for key in set(actual) | set(node['files']) if actual.get(key) != node['files'].get(key))
            raise ValueError(f'{target}: changed/missing form package files: {changed[:8]}')
        if type(node.get('sprite_id')) is not int or node['sprite_id'] <= 0:
            raise ValueError(f'{target}: invalid form sprite ID')
        timeline, context = read_json(target / 'timeline.json'), read_json(target / 'ai.json')
        if not isinstance(context.get('frame_calls'), dict):
            raise ValueError(f'{target}: missing compiled form frame calls')
        for source_frame, calls in context['frame_calls'].items():
            validate_effect_dependencies(calls,
                f"{timeline.get('source_swf', {}).get('path')}:DefineSprite_{node['sprite_id']}/frame_{source_frame}", root)
        source = manifest.get('source_swf_sha256')
        if (timeline.get('sprite_id') != node['sprite_id'] or context.get('sprite_id') != node['sprite_id']
                or timeline.get('source_swf', {}).get('sha256') != source
                or context.get('source_swf', {}).get('sha256') != source):
            raise ValueError(f'{target}: form source/body identity mismatch')
        metadata = read_json(target / 'player_controller/body.json')
        if metadata.get('swf_sha256') != source or not METHODS.issubset(metadata.get('functions', [])):
            raise ValueError(f'{target}: missing source-bound BODY form functions')
        for name in ('fighter.json', 'assets.json', 'combat.json', 'hurt_voice.json', 'sound_segments.json',
                     'ai_hit_state.gd', 'player_controller/body.gd', 'player_controller/controller.gd',
                     'player_controller/controller.json', 'player_controller/predicates.gd'):
            if name not in node['files']:
                raise ValueError(f'{target}: missing form dependency {name}')
        for asset in read_json(target / 'assets.json').get('assets', []):
            resource = asset.get('path', '')
            if not isinstance(resource, str) or not resource:
                raise ValueError(f'{target}: invalid form asset path {resource}')
            asset_path = ((root / 'godot' / resource.removeprefix('res://'))
                          if resource.startswith('res://') else target / resource).resolve()
            if not asset_path.is_relative_to(target) or str(asset_path.relative_to(target)) not in node['files']:
                raise ValueError(f'{target}: unpinned form asset {resource}')
        node.update(timeline=timeline, context=context, body_metadata=metadata)
    return manifest, nodes


def validate_form_manifest(directory: Path, contract: dict, root: Path = ROOT) -> dict:
    manifest_path = directory / 'form_profiles.json'
    if not manifest_path.is_file() or hashlib.sha256(manifest_path.read_bytes()).hexdigest() != contract.get('manifest_sha256'):
        raise ValueError(f'{manifest_path}: missing/changed reviewed form manifest')
    manifest, nodes = inspect_form_manifest(directory, root)
    if set(nodes) != set(contract.get('nodes', {})):
        raise ValueError(f'{manifest_path}: changed reviewed form graph')
    for frame, node in nodes.items():
        expected = contract['nodes'][frame]
        source = f"{node['timeline']['source_swf']['path']}:DefineSprite_{node['sprite_id']}"
        if node['sprite_id'] != expected['sprite_id'] or node['body_metadata'].get('source_sha256') != expected['requirement']['body_init_sha256']:
            raise ValueError(f'{source}: changed form BODY initialization')
        if frame != '1':
            entry = manifest['profiles'][frame]
            if (digest(entry.get('requirement')) != digest(expected['requirement'])
                    or digest(entry.get('load_declarations')) != digest(expected['requirement']['load_declarations'])):
                raise ValueError(f'{source}: changed source load/parent target requirement')
        context = node['context']
        if digest([context.get('parent_initial_values', {})]) != expected['parent_initial_values_digest']:
            raise ValueError(f'{source}: changed form parent initialization')
        calls = context.get('frame_calls', {})
        if {key: digest(value) for key, value in calls.items()} != expected['frames']:
            raise ValueError(f'{source}: changed source-compiled form frame calls')
        for source_frame, actions in calls.items():
            for action in form_calls(actions):
                if action['op'] not in ('body_form_call', 'parent_form_goto'):
                    continue
                requirement = action.get('replacement', {})
                target = str(requirement.get('target_parent_frame'))
                if target not in contract['nodes'] or target == '1' or digest(requirement) != digest(contract['nodes'][target]['requirement']):
                    raise ValueError(f'{source}/frame_{source_frame}: unresolved form target {target}')
    return manifest
