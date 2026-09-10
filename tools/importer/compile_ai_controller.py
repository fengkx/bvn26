"""Compile standard controller dispatch and placement callbacks to native code.

The adapter owns timeline instance lifetime. A source goto applies its display
list immediately and queues the target DoAction. If it removes this controller,
all generated callers return before their next source statement.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from compile_ai_predicates import (
    ROOT, NAMES, DISPATCH_NAMES, FIELDS, FUNCTION, expression, compile_source, controller_script,
)
from build_combat_model import parse_clip_timeline, parse_projectile_motion

LOCALS = {'js', 'jumpinggg', 'standed', 'allF', 'walkF', 'touchFloor'}
HEADER = '''extends "predicates.gd"

# These initial values are the controller's original timeline declarations.
var js: Variant = 0
var jumpinggg: Variant = null
var standed: Variant = false
var allF: Variant = 0
var walkF: Variant = 0
var touchFloor: Variant
var adapter: RefCounted

func bind_adapter(target: RefCounted) -> void:
\tadapter = target
\ttouchFloor = adapter.resolve_controller_scope("touchFloor")

func value(key: String) -> Variant:
\treturn adapter.read_field(key)

func write_value(key: String, v: Variant) -> void:
\tadapter.write_field(key, v)

func sensor(key: String) -> Variant:
\treturn adapter.sensor_hit(key)

func body_hit(key: String) -> Variant:
\treturn adapter.body_hit(key)

func power(key: String) -> Variant:
\treturn adapter.power_field(key)
'''
CALLS = {
    '_parent.resColor()': 'adapter.effect("resColor")',
    '_parent.updateDirect()': 'adapter.effect("updateDirect")',
    '_root.jumpxg(_parent._parent)': 'adapter.effect("jumpxg")',
    '_root.luodixg(_parent._parent)': 'adapter.effect("luodixg")',
}


def compile_body(name: str, params: str, body: str, *, unbound_calls=()) -> str:
    params_list = [x.strip() for x in params.split(',') if x.strip()]
    locals_ = LOCALS | set(params_list)
    output = ['', 'func ' + name + '(' + ', '.join(p + ': Variant = null' for p in params_list) + ') -> Variant:']
    depth = 1
    for raw in body.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line == '{':
            depth += 1
            continue
        if line == '}':
            depth -= 1
            if depth < 1:
                raise ValueError(f'Unbalanced {name}')
            continue
        indent = '\t' * depth
        translated = []
        if line.startswith('if(') and line.endswith(')'):
            translated = ['if truth(' + expression(line[3:-1], locals_) + '):']
        elif line.startswith('else if(') and line.endswith(')'):
            translated = ['elif truth(' + expression(line[8:-1], locals_) + '):']
        elif line == 'else':
            translated = ['else:']
        elif line.startswith('return ') and line.endswith(';'):
            translated = ['return ' + expression(line[7:-1], locals_)]
        elif match := re.fullmatch(r'var (\w+)(?: = (.+))?;', line):
            local, initial = match.groups()
            locals_.add(local)
            translated = [f'var {local}: Variant = ' + (expression(initial,locals_) if initial else 'null')]
        elif match := re.fullmatch(r'(.+?) (\+=|-=|=) (.+);', line):
            target, op, rhs = match.groups()
            value = expression(rhs,locals_)
            if op != '=':
                value = f'(number({expression(target,locals_)}) {op[0]} number({value}))'
            if target in locals_:
                translated = [f'{target} = {value}']
            elif target in FIELDS:
                translated = [f'write_value("{FIELDS[target]}", {value})']
            else:
                raise ValueError(f'Unsupported assignment in {name}: {line}')
        elif match := re.fullmatch(r'_parent.gotoAnd(Play|Stop)\((.+)\);', line):
            mode, destination = match.groups()
            translated = ['adapter.goto_label(' + expression(destination,locals_) + ', ' + str(mode=='Play').lower() + ')',
                          'if not adapter.controller_alive():', '\treturn null']
        elif line[:-1] in CALLS and line.endswith(';'):
            translated = [CALLS[line[:-1]]]
        elif match := re.fullmatch(r'_parent\._parent\.(moveX|moveY)\((.+)\);', line):
            translated = [f'adapter.move_axis("{match[1]}", ' + expression(match[2],locals_) + ')']
        elif match := re.fullmatch(r'_parent\.(fangyux|beidax)\((.*)\);', line):
            args = expression(match[2],locals_) if match[2] else ''
            translated = [f'adapter.body_call("{match[1]}", [{args}])',
                          'if not adapter.controller_alive():', '\treturn null']
        elif match := re.fullmatch(r'(fangyux|beidax)\((.*)\);', line):
            if match[1] not in unbound_calls or match[2]:
                raise ValueError('Unresolved controller-scope body call: ' + line)
            translated = ['pass # The original unqualified function is undefined in this scope.']
        elif match := re.fullmatch(r'(\w+)\((.*)\);',line):
            if match[1] not in {*NAMES,*DISPATCH_NAMES}:
                raise ValueError(f'Unsupported call in {name}: {line}')
            translated = [expression(line[:-1],locals_)]
            if match[1] in DISPATCH_NAMES:
                translated += ['if not adapter.controller_alive():','\treturn null']
        else:
            raise ValueError(f'Unsupported statement in {name}: {line}')
        output.extend(indent + s for s in translated)
    if depth != 1:
        raise ValueError(f'Unbalanced {name}')
    output.append('\treturn null')
    return '\n'.join(output) + '\n'


def renamed_timeline_hooks(bundle: dict, sprite: int, timeline: dict, existing: list) -> list:
    """Retain attack clips that rename themselves without a motion callback."""
    owned = {(h['placement_frame'], h['depth']) for h in existing}
    definitions = {d['character_id']: d for d in timeline.get('definitions', [])}
    placements = {}
    for frame in timeline['frames']:
        for placement in frame['display_list']:
            key = (placement['placed_frame'], placement['depth'])
            if placement.get('name') and key not in owned:
                placements.setdefault(key, []).append((frame['frame'], placement))
    result = []
    for (placed_frame, depth), members in placements.items():
        placement = members[0][1]
        character = placement['character_id']
        clip = parse_clip_timeline(bundle, character)
        if not any(r['instance_name'].endswith('atm') for r in clip.get('rename_frames', [])):
            continue
        clip['frame_count'] = definitions[character]['frame_count']
        events = []
        for script in bundle['scripts']:
            match = re.fullmatch(rf'DefineSprite_{character}/frame_(\d+)/DoAction.as', script['path'])
            if not match:
                continue
            source = script['source'].strip()
            if source == '_root.shine();':
                events.append({'frame': int(match[1]), 'op': 'screen_flash',
                               'color_rgb24': 0xFFFFFF, 'source_path': script['path'],
                               'source_sha256': hashlib.sha256(script['source'].encode()).hexdigest()})
            elif source != 'stop();' and not re.fullmatch(r'this\._name = "[^"]+";', source):
                raise ValueError('Uncompiled renamed attack timeline: ' + script['path'])
        result.append({'path': f'DefineSprite_{sprite}/frame_{placed_frame}/PlaceObject2_{character}_{depth}',
                       'method': 'enter_frame', 'depth': depth, 'placement_frame': placed_frame,
                       'member_frames': [f for f, _ in members],
                       'projectile': {'instance_name': placement['name'], 'frame_only': True,
                                      'frame_events': events, **clip}})
    return result


def compile_controller(bundle: dict, sprite: int, timeline: dict, *, player: bool = False) -> tuple[str,dict]:
    swf = ROOT / bundle['game_file']
    if hashlib.sha256(swf.read_bytes()).hexdigest() != bundle['swf_sha256']:
        raise ValueError('Retained source SWF hash mismatch')
    if timeline['source_swf']['sha256'] != bundle['swf_sha256'] or timeline['sprite_id'] != sprite:
        raise ValueError('Controller and timeline do not share the retained source')
    controller = controller_script(bundle, sprite)
    controller_id = int(re.search(r'DefineSprite_(\d+)', controller['path'])[1])
    source = controller['source']
    funcs = {m[1]:(m[2],m[3]) for m in FUNCTION.finditer(source.replace('\r\n','\n'))}
    text = '# Generated by tools/importer/compile_ai_controller.py; do not edit.\n' + HEADER
    if player:
        text += '\nfunc source_key(key: String) -> Variant:\n\treturn adapter.source_key(key)\n'
    for name in DISPATCH_NAMES:
        text += compile_body(name,*funcs[name])
    hooks = []
    unbound_call_sites = []
    for script in bundle['scripts']:
        match = re.fullmatch(rf'DefineSprite_{sprite}/frame_(\d+)/PlaceObject2_{controller_id}_(\d+)/CLIPACTIONRECORD onClipEvent\(enterFrame\).as', script['path'])
        if not match:
            continue
        frame,depth = map(int,match.groups())
        body = script['source'].replace('\r\n','\n')
        if not body.startswith('onClipEvent(enterFrame){\n') or not body.endswith('}\n'):
            raise ValueError(f'Unexpected callback format: {script["path"]}')
        method = f'frame_{frame}_depth_{depth}'
        unbound = set(re.findall(r'(?<![\w.])(fangyux|beidax)\(', body))
        if unbound:
            main_path = ROOT / 'scripts/main.json'
            main = json.loads(main_path.read_text())
            for target in unbound:
                if target in funcs or any(re.search(r'\b' + target + r'\b', s['source']) for s in main['scripts']):
                    raise ValueError('Controller-scope body function requires explicit compilation: ' + target)
                unbound_call_sites.append({'path': script['path'], 'name': target,
                                           'resolution': 'undefined_controller_and_root_scope',
                                           'root_scope_bundle_sha256': hashlib.sha256(main_path.read_bytes()).hexdigest()})
        text += compile_body(method,'',body.split('\n',1)[1].rsplit('}',1)[0], unbound_calls=unbound)
        membership = []
        for f,display in enumerate(timeline['frames'],1):
            for placement in display['display_list']:
                if placement.get('character_id')==controller_id and placement['depth']==depth and placement['placed_frame']==frame:
                    membership.append(f)
        if not membership:
            raise ValueError(f'No matching display-list instance: {script["path"]}')
        hooks.append({'method':method,'path':script['path'],'placement_frame':frame,'depth':depth,'member_frames':membership})
    receiver_hooks = []
    for script in bundle['scripts']:
        match = re.fullmatch(rf'DefineSprite_{sprite}/frame_(\d+)/PlaceObject2_2_(\d+)/CLIPACTIONRECORD onClipEvent\(enterFrame\).as', script['path'])
        if not match:
            continue
        callback = re.fullmatch(r'onClipEvent\(enterFrame\)\{\s*(beida|fangyu)\(\);\s*\}\s*', script['source'])
        if not callback:
            raise ValueError('Uncompiled receiver callback: ' + script['path'])
        frame, depth = map(int, match.groups())
        members = [f['frame'] for f in timeline['frames'] if any(
            p.get('character_id') == 2 and p['depth'] == depth and p['placed_frame'] == frame
            for p in f['display_list'])]
        if not members:
            raise ValueError('Receiver placement missing: ' + script['path'])
        receiver_hooks.append({'path': script['path'], 'method': 'receive',
                               'receiver': callback[1], 'placement_frame': frame,
                               'depth': depth, 'member_frames': members})
    projectile_hooks = []
    for script in bundle['scripts']:
        match = re.fullmatch(rf'DefineSprite_{sprite}/frame_(\d+)/PlaceObject2_(\d+)_(\d+)/CLIPACTIONRECORD onClipEvent\(enterFrame\).as', script['path'])
        if not match or int(match[2]) in (2, controller_id):
            continue
        motion = parse_projectile_motion(script['source'])
        if motion is None:
            raise ValueError('Uncompiled child callback: ' + script['path'])
        frame, character, depth = map(int, match.groups())
        clip = parse_clip_timeline(bundle, character)
        if 'initial_speed' not in clip:
            load_path = script['path'].replace('onClipEvent(enterFrame)', 'onClipEvent(load)')
            load = next((s['source'] for s in bundle['scripts'] if s['path'] == load_path), '')
            initial = re.fullmatch(r'onClipEvent\(load\)\{\s*played = 0;\s*movspeed = _parent.speed(?: \* (\d+))?;\s*\}\s*', load)
            if not initial:
                raise ValueError('Uncompiled projectile initialization: ' + script['path'])
            clip.update({'initial_speed_field': 'speed', 'initial_speed_factor': int(initial[1] or 1),
                         'initial_played': 0, 'initial_motion_source': {
                             'source_path': load_path, 'source_sha256': hashlib.sha256(load.encode()).hexdigest()}})
        placements = [(f['frame'], p) for f in timeline['frames'] for p in f['display_list']
                      if p.get('character_id') == character and p['depth'] == depth and p['placed_frame'] == frame]
        if not placements:
            raise ValueError('Projectile placement missing: ' + script['path'])
        projectile_hooks.append({'path': script['path'], 'method': 'enter_frame',
                                 'depth': depth, 'placement_frame': frame,
                                 'member_frames': [f for f, _ in placements],
                                 'projectile': {'instance_name': placements[0][1]['name'], **clip, **motion}})
    projectile_hooks.extend(renamed_timeline_hooks(bundle, sprite, timeline, projectile_hooks))
    return text,{'status':'compiled_not_integrated','sprite_id':sprite,'hooks':hooks,
                 **({'unbound_call_sites': unbound_call_sites} if unbound_call_sites else {}),
                 'receiver_hooks':receiver_hooks,
                 'projectile_hooks':projectile_hooks,
                 'source_swf':{'path':bundle['game_file'],'sha256':bundle['swf_sha256']},
                 'source_sha256':hashlib.sha256(source.encode()).hexdigest()}


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument('--fighter',default='yihu')
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--player', action='store_true')
    args=parser.parse_args()
    bundle=json.loads((ROOT/f'scripts/fighter/{args.fighter}.json').read_text())
    timeline=json.loads((ROOT/f'data/slices/{args.fighter}-base.timeline.json').read_text())
    sprite=timeline['sprite_id']
    text,meta=compile_controller(bundle,sprite,timeline,player=args.player)
    meta['input_mode'] = 'player' if args.player else 'cpu'
    source=controller_script(bundle)['source']
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'predicates.gd').write_text(compile_source(source, player=args.player))
    (args.output/'controller.gd').write_text(text)
    (args.output/'controller.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'hooks':len(meta['hooks']),'functions':len(DISPATCH_NAMES),'output':str(args.output)}))


if __name__=='__main__':
    main()
