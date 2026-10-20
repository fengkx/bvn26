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
    controller_aliases, OPPONENT,
)
from compile_ai_context import controller_scope_fields
from build_combat_model import (
    parse_clip_timeline,
    parse_child_stop_frames,
    parse_projectile_initialization,
    parse_projectile_motion,
    source_frame_counts,
)

LOCALS = {'js', 'jumpinggg', 'standed', 'allF', 'walkF', 'touchFloor'}
# These receiver functions are shared source, but their symbol id is not stable
# across fighters. Sakura wraps the receiver graphic in Sprite5; other forms
# commonly use Sprite2. Admit only this exact retained implementation.
RECEIVER_FUNCTIONS = ('gameRunning', 'beida', 'fangyu', 'checkHit', 'getHitObj', 'getStgHitObj')
RECEIVER_FUNCTION_HASHES = (
    'b7e98f01be5b46dd5d4aff0eee9ed8519e6dfcd69a3bd30b28945a8c6c6fcc59',
    'cfac66cedf7ee48ff42cde96a7af5cd79b3c9e98a9e7ea77489eacdafb8f2d30',
    '493c6a91d527ca22586f7df13f89e9aeebb7743d3df0fd7dc811b3f3a6296d48',
    'f3acf68293b1c7db2de74d30f08e78dc088574d70e9239ab0a14167aa21f3c88',
    '2721d4f385bc8c2d3fc9c50d9db681fa590fc74eadb3b5d41fa7492f7aea68c0',
    '1666e47b5258d54ec6e2c57bb0dbdbb42fff5a77ac19b21082859523ed5d7f75',
)
RECEIVER_CALLBACK = re.compile(
    r'onClipEvent\(enterFrame\)\{\s*(beida|fangyu)\(\);\s*\}\s*'
)
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

func source_key(key: String) -> Variant:
\treturn adapter.source_key(key)

func power(key: String) -> Variant:
\treturn adapter.power_field(key)
'''
CALLS = {
    '_parent.resColor()': 'adapter.effect("resColor")',
    '_parent.updateDirect()': 'adapter.effect("updateDirect")',
    '_root.jumpxg(_parent._parent)': 'adapter.effect("jumpxg")',
    '_root.luodixg(_parent._parent)': 'adapter.effect("luodixg")',
    # Root bdfyxg(selfmc)/bdfyxg2(selfmc) require an explicit receiver. The
    # argument-less child calls cannot read selfmc.bdzl and take no switch arm.
    # They must not borrow the fighter's stale blocked-hit strength.
    'bdfyxg()': 'pass # Source guard-effect call has no receiver argument.',
    'bdfyxg2()': 'pass # Source guard-effect call has no receiver argument.',
}
def source_expression(source: str, locals_: set[str], scope_fields: set[str], call_aliases=None) -> str:
    for field in sorted(scope_fields, key=len, reverse=True):
        source = re.sub(
            rf'(?<![.\w])_parent\.{re.escape(field)}\b',
            f'value({json.dumps(field)})',
            source,
        )
    return expression(source, locals_, call_aliases)


def compile_body(
    name: str,
    params: str,
    body: str,
    *,
    unbound_calls=(),
    scope_fields: set[str] | None = None,
    call_aliases=None,
) -> str:
    params_list = [x.strip() for x in params.split(',') if x.strip()]
    locals_ = LOCALS | set(params_list)
    source_fields = scope_fields or set()
    # Resolve bounded container aliases offline. They denote stable fighter
    # wrappers throughout one callback; only mapped scalar members are emitted.
    container_aliases = {}

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
        alias = re.fullmatch(r'var (\w+) = (.+);', line)
        if alias and alias[2] in (OPPONENT, '_parent._parent'):
            if alias[1] in locals_ or alias[1] in container_aliases:
                raise ValueError('Container alias redeclared: ' + alias[1])
            container_aliases[alias[1]] = alias[2]
            continue
        for local, container in container_aliases.items():
            if re.match(rf'(?:var )?{re.escape(local)}\s*=', line):
                raise ValueError('Container alias reassigned: ' + local)
            line = re.sub(rf'(?<![.\w]){re.escape(local)}(?=\.)', lambda _: container, line)
        indent = '\t' * depth
        translated = []
        if line.startswith('if(') and line.endswith(')'):
            translated = ['if truth(' + source_expression(line[3:-1], locals_, source_fields, call_aliases) + '):']
        elif line.startswith('else if(') and line.endswith(')'):
            translated = ['elif truth(' + source_expression(line[8:-1], locals_, source_fields, call_aliases) + '):']
        elif line == 'else':
            translated = ['else:']
        elif line.startswith('return ') and line.endswith(';'):
            translated = ['return ' + source_expression(line[7:-1], locals_, source_fields, call_aliases)]
        elif match := re.fullmatch(r'var (\w+)(?: = (.+))?;', line):
            local, initial = match.groups()
            locals_.add(local)
            translated = [f'var {local}: Variant = ' + (source_expression(initial,locals_,source_fields, call_aliases) if initial else 'null')]
        elif match := re.fullmatch(r'(.+?) (\+=|-=|=) (.+);', line):
            target, op, rhs = match.groups()
            value = source_expression(rhs,locals_,source_fields, call_aliases)
            if op != '=':
                value = f'(number({source_expression(target,locals_,source_fields, call_aliases)}) {op[0]} number({value}))'
            if target in locals_:
                translated = [f'{target} = {value}']
            elif target in FIELDS:
                translated = [f'write_value("{FIELDS[target]}", {value})']
            else:
                raise ValueError(f'Unsupported assignment in {name}: {line}')
        elif match := re.fullmatch(r'_parent.gotoAnd(Play|Stop)\((.+)\);', line):
            mode, destination = match.groups()
            translated = ['adapter.goto_label(' + source_expression(destination,locals_,source_fields, call_aliases) + ', ' + str(mode=='Play').lower() + ')',
                          'if not adapter.controller_alive():', '\treturn null']
        elif line[:-1] in CALLS and line.endswith(';'):
            translated = [CALLS[line[:-1]]]
        elif match := re.fullmatch(r'_parent\._parent\.(moveX|moveY)\((.+)\);', line):
            translated = [f'adapter.move_axis("{match[1]}", ' + source_expression(match[2],locals_,source_fields, call_aliases) + ')']
        elif match := re.fullmatch(r'_parent\.(fangyux|beidax)\((.*)\);', line):
            args = source_expression(match[2],locals_,source_fields, call_aliases) if match[2] else ''
            translated = [f'adapter.body_call("{match[1]}", [{args}])',
                          'if not adapter.controller_alive():', '\treturn null']
        elif match := re.fullmatch(r'(fangyux|beidax)\((.*)\);', line):
            if match[1] not in unbound_calls or match[2]:
                raise ValueError('Unresolved controller-scope body call: ' + line)
            else:
                translated = ['pass # The original unqualified function is undefined in this scope.']
        elif match := re.fullmatch(r'(\w+)\((.*)\);',line):
            if match[1] not in {*NAMES,*DISPATCH_NAMES}:
                raise ValueError(f'Unsupported call in {name}: {line}')
            translated = [source_expression(line[:-1],locals_,source_fields, call_aliases)]
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
    frame_counts = source_frame_counts(timeline)
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
        clip = parse_clip_timeline(bundle, character, frame_counts)
        renames = clip.get('rename_frames', [])
        if not renames or not (placement['name'].endswith('atm') or any(
                r['instance_name'].endswith('atm') for r in renames)):
            continue
        clip['frame_count'] = definitions[character]['frame_count']
        timeline_events = []
        for child_frame, frame_events in enumerate(
                definitions[character].get('display_list_frame_events', []), 1):
            for event in frame_events:
                if event.get('type') == 'start_sound':
                    timeline_events.append({
                        'frame': child_frame,
                        'event': event,
                    })
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
            elif source != 'stop();' and not re.fullmatch(r'(?:this\.)?_name = "[^"]+";', source):
                raise ValueError('Uncompiled renamed attack timeline: ' + script['path'])
        result.append({'path': f'DefineSprite_{sprite}/frame_{placed_frame}/PlaceObject2_{character}_{depth}',
                       'method': 'enter_frame', 'depth': depth, 'placement_frame': placed_frame,
                       'member_frames': [f for f, _ in members],
                       'projectile': {'instance_name': placement['name'], 'frame_only': True,
                                      'source_sprite_id': character,
                                      'source_depth': depth,
                                      'source_placement_frame': placed_frame,
                                      'frame_events': events,
                                      'timeline_events': timeline_events, **clip}})
    return result


def receiver_source(bundle: dict, symbol: int) -> dict | None:
    """Return the exact supported shared receiver source, without symbol guesses."""
    path = f'DefineSprite_{symbol}/frame_1/DoAction.as'
    script = next((item for item in bundle['scripts'] if item['path'] == path), None)
    if script is None:
        return None
    source = script['source'].replace('\r\n', '\n')
    functions = {
        match[1]: match[0]
        for match in FUNCTION.finditer(source)
    }
    if any(name not in functions for name in RECEIVER_FUNCTIONS):
        return None
    hashes = tuple(hashlib.sha256(functions[name].encode()).hexdigest()
                   for name in RECEIVER_FUNCTIONS)
    if hashes != RECEIVER_FUNCTION_HASHES:
        return None
    return {
        'symbol_id': symbol,
        'script_path': path,
        'script_sha256': hashlib.sha256(script['source'].encode()).hexdigest(),
    }


def nested_controller_source(bundle: dict, symbol: int) -> tuple[dict, dict[str, tuple[str, str]]] | None:
    """Find a nested controller's own frame-one functions by retained source."""
    path = f'DefineSprite_{symbol}/frame_1/DoAction.as'
    script = next((item for item in bundle['scripts'] if item['path'] == path), None)
    if script is None:
        return None
    source = script['source'].replace('\r\n', '\n')
    return script, {m[1]: (m[2], m[3]) for m in FUNCTION.finditer(source)}


def compile_controller(bundle: dict, sprite: int, timeline: dict, *, player: bool = False) -> tuple[str,dict]:
    swf = ROOT / bundle['game_file']
    if hashlib.sha256(swf.read_bytes()).hexdigest() != bundle['swf_sha256']:
        raise ValueError('Retained source SWF hash mismatch')
    if timeline['source_swf']['sha256'] != bundle['swf_sha256'] or timeline['sprite_id'] != sprite:
        raise ValueError('Controller and timeline do not share the retained source')
    controller = controller_script(bundle, sprite)
    scope_fields = controller_scope_fields(bundle, sprite)
    canonical_hash = hashlib.sha256(controller['source'].encode()).hexdigest()
    # Later placements may host a different controller for another source
    # state. They are retained in the source timeline, but this compiled base
    # controller may only reuse aliases with identical source semantics.
    all_controller_aliases = controller_aliases(bundle, sprite)
    controller_ids = {
        int(re.search(r'DefineSprite_(\d+)', alias['path'])[1])
        for alias in all_controller_aliases
        if hashlib.sha256(alias['source'].encode()).hexdigest() == canonical_hash
    }
    excluded_controller_aliases = [
        {
            'path': alias['path'],
            'source_sha256': hashlib.sha256(alias['source'].encode()).hexdigest(),
            'reason': 'different_source_from_base_form_controller',
        }
        for alias in all_controller_aliases
        if hashlib.sha256(alias['source'].encode()).hexdigest() != canonical_hash
    ]
    source = controller['source']
    funcs = {m[1]:(m[2],m[3]) for m in FUNCTION.finditer(source.replace('\r\n','\n'))}
    text = '# Generated by tools/importer/compile_ai_controller.py; do not edit.\n' + HEADER
    for name in DISPATCH_NAMES:
        text += compile_body(name,*funcs[name], scope_fields=scope_fields)
    hooks = []
    unbound_call_sites = []
    compiled_nested_functions = {}
    for script in bundle['scripts']:
        match = re.fullmatch(rf'DefineSprite_{sprite}/frame_(\d+)/PlaceObject2_(\d+)_(\d+)/CLIPACTIONRECORD onClipEvent\(enterFrame\).as', script['path'])
        if not match:
            continue
        frame,controller_id,depth = map(int,match.groups())
        if controller_id not in controller_ids:
            continue
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
        text += compile_body(
            method, '', body.split('\n',1)[1].rsplit('}',1)[0],
            unbound_calls=unbound, scope_fields=scope_fields,
        )
        membership = []
        for f,display in enumerate(timeline['frames'],1):
            for placement in display['display_list']:
                if placement.get('character_id')==controller_id and placement['depth']==depth and placement['placed_frame']==frame:
                    membership.append(f)
        if not membership:
            raise ValueError(f'No matching display-list instance: {script["path"]}')
        hooks.append({'method':method,'path':script['path'],'controller_id':controller_id,
                      'placement_frame':frame,'depth':depth,'member_frames':membership})
    receiver_hooks = []
    receiver_ids = set()
    for script in bundle['scripts']:
        match = re.fullmatch(rf'DefineSprite_{sprite}/frame_(\d+)/PlaceObject2_(\d+)_(\d+)/CLIPACTIONRECORD onClipEvent\(enterFrame\).as', script['path'])
        if not match:
            continue
        callback = RECEIVER_CALLBACK.fullmatch(script['source'])
        counter = re.fullmatch(
            r'onClipEvent\(enterFrame\)\{\s*if\(checkHit\(\)\)\s*\{\s*'
            r'_parent\.gotoAndPlay\("([^"\n]+)"\);\s*\}\s*\}\s*', script['source'])
        if callback is None and counter is None:
            continue
        frame, symbol_id, depth = map(int, match.groups())
        source_info = receiver_source(bundle, symbol_id)
        if source_info is None:
            raise ValueError('Uncompiled receiver source: ' + script['path'])
        receiver_ids.add(symbol_id)
        members = [f['frame'] for f in timeline['frames'] if any(
            p.get('character_id') == symbol_id and p['depth'] == depth and p['placed_frame'] == frame
            for p in f['display_list'])]
        if not members:
            raise ValueError('Receiver placement missing: ' + script['path'])
        receiver_hooks.append({'path': script['path'], 'method': 'receive',
                               'receiver': callback[1] if callback else 'checkHit',
                               **({'counter_label': counter[1]} if counter else {}),
                               'placement_frame': frame,
                               'receiver_symbol_id': symbol_id,
                               'receiver_source_path': source_info['script_path'],
                               'receiver_source_sha256': source_info['script_sha256'],
                               'depth': depth, 'member_frames': members})
    projectile_hooks = []
    frame_counts = source_frame_counts(timeline)
    for script in bundle['scripts']:
        match = re.fullmatch(rf'DefineSprite_{sprite}/frame_(\d+)/PlaceObject2_(\d+)_(\d+)/CLIPACTIONRECORD onClipEvent\(enterFrame\).as', script['path'])
        if not match or int(match[2]) in (receiver_ids | controller_ids):
            continue
        # A placed child can own a source controller callback without being
        # the fighter's root input controller. Compile its callback against
        # the same source predicate ABI and retain its independent lifetime.
        body = script['source'].replace('\r\n', '\n')
        if (body.startswith('onClipEvent(enterFrame){\n') and body.endswith('}\n')
                and (re.search(r'\b(?:gameRunning|magichit\d?|bisha|nornalhit|skill\d?|bdfyxg2?|moveX|moveY)\s*\(', body)
                     or '_parent._parent._x' in body
                     or '_parent._parent._y' in body)):
            frame, character, depth = map(int, match.groups())
            nested = nested_controller_source(bundle, character)
            nested_aliases = {}
            nested_functions = {}
            if nested is not None:
                _, nested_functions = nested
                referenced = set(re.findall(r'(?<![.\w])([A-Za-z_]\w*)\s*\(', body))
                pending = [name for name in referenced if name in nested_functions]
                selected = set()
                while pending:
                    name = pending.pop()
                    if name in selected:
                        continue
                    selected.add(name)
                    pending.extend(
                        call for call in re.findall(r'(?<![.\w])([A-Za-z_]\w*)\s*\(', nested_functions[name][1])
                        if call in nested_functions and call not in selected
                    )
                nested_aliases = {name: f'child_{character}_{name}' for name in selected}
                nested_key = (character, hashlib.sha256(nested[0]['source'].encode()).hexdigest())
                compiled = compiled_nested_functions.setdefault(nested_key, set())
                for name in sorted(selected - compiled):
                    params, function_body = nested_functions[name]
                    text += compile_body(
                        nested_aliases[name], params, function_body,
                        scope_fields=scope_fields, call_aliases=nested_aliases,
                    )
                    compiled.add(name)
            method = f'child_frame_{frame}_depth_{depth}_controller_{character}'
            child_body = body.split('\n', 1)[1].rsplit('}', 1)[0]
            child_code = compile_body(
                method, '', child_body, scope_fields=scope_fields,
                call_aliases=nested_aliases,
            )
            membership = [
                f['frame'] for f in timeline['frames']
                if any(
                    p.get('character_id') == character
                    and p['depth'] == depth
                    and p['placed_frame'] == frame
                    for p in f['display_list']
                )
            ]
            if not membership:
                raise ValueError(f'Child controller placement missing: {script["path"]}')
            text += child_code
            hooks.append({
                'method': method, 'path': script['path'],
                'controller_id': character, 'placement_frame': frame,
                'depth': depth, 'member_frames': membership,
                'child_controller': True,
            })
            continue
        motion = parse_projectile_motion(script['source'])
        if motion is None:
            raise ValueError('Uncompiled child callback: ' + script['path'])
        frame, character, depth = map(int, match.groups())
        clip = parse_clip_timeline(bundle, character, frame_counts)
        clip.update(parse_child_stop_frames(bundle, timeline, character))
        if 'initial_variables' not in clip:
            load_path = script['path'].replace('onClipEvent(enterFrame)', 'onClipEvent(load)')
            load = next((s['source'] for s in bundle['scripts'] if s['path'] == load_path), '')
            initial = parse_projectile_initialization(load)
            if initial is None and load:
                raise ValueError('Uncompiled projectile initialization: ' + script['path'])
            if initial is not None:
                if 'initial_variables' in initial:
                    variables = initial['initial_variables']
                    if (any(name in ('local_x_factor', 'local_y_factor') for name in motion)
                            and 'movspeed' not in variables
                            and initial.get('initial_speed_field') != 'speed'):
                        raise ValueError('Projectile movement local is undeclared: ' + script['path'])
                clip.update({**initial, 'initial_motion_source': {
                    'source_path': load_path,
                    'source_sha256': hashlib.sha256(load.encode()).hexdigest(),
                }})
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
                 'excluded_controller_aliases': excluded_controller_aliases,
                 **({'unbound_call_sites': unbound_call_sites} if unbound_call_sites else {}),
                 'controller_scope_fields': sorted(scope_fields),
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
