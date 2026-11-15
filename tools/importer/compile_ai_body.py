"""Compile the base BODY CPU functions without a runtime AS2 interpreter.

Only explicitly recognized statements and external host calls are admitted.
Source branches, local aliases, overwritten assignments and field increments
remain ordered. CPU specialization removes player guards; --player retains them.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import re

from compile_ai_predicates import ROOT, FUNCTION, PRELUDE, emit, normalize

NAMES = ('hurtSkill', 'dash', 'doDashX', 'onDashing', 'fangyux', 'beidax',
         'updateDirect', 'on_enterframe', 'initWudi', 'isHitBan', 'doHurtSkill')
FIELDS = set('hp sw ql dashQL 动作 goran hitBan touch dashX dashY dashing dashF '
             'hitNear htx yup hstm time hited tdtime jump wdFrame wdFrameX canhit airBody '
             '_lastX touchFloor jumped _initwudi wudi i hurtSkling jhp bdzl'.split())
OPPONENT = '_root.game["p" + pn]'
REFS = {
    OPPONENT + '.mc.动作': 'opponent_action', OPPONENT + '.mc.sw': 'opponent_sw',
    OPPONENT + '.mc.airBody': 'opponent_airBody',
    OPPONENT + '._x': 'opponent_x', OPPONENT + '._xscale': 'opponent_xscale',
    '_parent._x': 'x', '_parent._y': 'y', '_parent._xscale': 'xscale',
    '_parent.scale_X': 'scale_X', '_parent.vecx': 'vecx', '_parent.heavy': 'heavy',
    '_root.zhanting': 'root_paused', '_root.floorY': 'floorY',
    '_root.mapSizeX': 'mapSizeX', '_root.zhongli': 'gravity',
    OPPONENT + '.vecx': 'opponent_vecx', OPPONENT + '.heavy': 'opponent_heavy',
    '_root.wudi': 'root_wudi', '_root.modo': 'modo', '_parent.useAI': 'useAI',
    '_parent.isNaruto': 'is_naruto', '_parent.getDepth()': 'depth',
    OPPONENT + '.getDepth()': 'opponent_depth',
}
HOST_CALLS = {'applyColors'}


def expand_aliases(text: str, aliases: dict[str, str]) -> str:
    for alias, target in aliases.items():
        text = re.sub(r'\b' + re.escape(alias) + r'\b', lambda _: target, text)
    return text


def field_key(text: str) -> str:
    if text in FIELDS:
        return text
    if text in REFS:
        return REFS[text]
    raise ValueError('Unsupported BODY field: ' + text)


def expression(text: str, locals_: set[str], aliases: dict[str, str], extra_calls: frozenset[str] = frozenset()) -> str:
    text = expand_aliases(text, aliases)
    text = re.sub(r'kis\((换|冲|上|下)\)', lambda m: 'source_key(' + json.dumps(m[1], ensure_ascii=False) + ')', text)
    text = re.sub(r'([{,])(\w+):', r'\1"\2":', text)
    text = re.sub(r'_root\.game\["ban" \+ i\]', 'platform(i)', text)
    text = re.sub(r'(_loc\d+_)\._(x|y|width)', r'platform_field(\1,"\2")', text)
    text = text.replace('bdmn.hitTest(' + OPPONENT + '.mc.bdmn)', 'body_hit("bdmn")')
    for ref, field in sorted(REFS.items(), key=lambda item: -len(item[0])):
        text = text.replace(ref, 'value(' + json.dumps(field) + ')')
    # Tokenize strings as well, so field names inside generated value("x")
    # calls cannot be substituted for a second time.
    text = re.sub(r'"[^"\\]*(?:\\.[^"\\]*)*"|\b\w+\b',
                  lambda m: 'value(' + json.dumps(m[0], ensure_ascii=False) + ')'
                  if m[0] in FIELDS and m[0] not in locals_ else m[0], text)
    text = re.sub(r'\+\+value\("([^"]+)"\)', r'increment("\1")', text)
    tree = ast.parse(normalize(text), mode='eval').body
    return emit(tree, locals_, frozenset((*NAMES, *HOST_CALLS, *extra_calls, 'increment', 'platform', 'platform_field', 'defer_body', 'literal_object')))


def compile_function(name: str, params: str, body: str, extra_calls: frozenset[str] = frozenset(), *, player: bool = False) -> str:
    if not player:
        body = re.sub(r'(?m)^( +)if\(!_parent\.useAI\)\n\1\{\n.*?^\1\}\n', '', body, flags=re.S)
    parameters = [p.strip() for p in params.split(',') if p.strip()]
    locals_ = set(parameters)
    aliases: dict[str, str] = {}
    output = ['', 'func ' + name + '(' + ', '.join(p + ': Variant = null' for p in parameters) + ') -> Variant:']
    depth = 1
    expr = lambda s: expression(s, locals_, aliases, extra_calls)
    for raw in body.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line in ('{', '}'):
            depth += 1 if line == '{' else -1
            if depth < 1:
                raise ValueError('Unbalanced BODY function: ' + name)
            continue
        if m := re.fullmatch(r'var (\w+) = ' + re.escape(OPPONENT) + ';', line):
            aliases[m[1]] = OPPONENT
            continue
        line = expand_aliases(line, aliases)
        if line.startswith('if(') and line.endswith(')'):
            translated = 'if truth(' + expr(line[3:-1]) + '):'
        elif line.startswith('while(') and line.endswith(')'):
            translated = 'while truth(' + expr(line[6:-1]) + '):'
        elif line.startswith('else if(') and line.endswith(')'):
            translated = 'elif truth(' + expr(line[8:-1]) + '):'
        elif line == 'else':
            translated = 'else:'
        elif line.startswith('return ') and line.endswith(';'):
            translated = 'return ' + expr(line[7:-1])
        elif m := re.fullmatch(r'var (\w+)(?: = (.+))?;', line):
            locals_.add(m[1])
            translated = 'var ' + m[1] + ': Variant = ' + (expr(m[2]) if m[2] else 'null')
        elif m := re.fullmatch(r'(.+?) (\+=|-=|=) (.+);', line):
            target, op, rhs = m.groups()
            # The retained source contains one chained scalar assignment.
            if line == 'wdFrame = wdFrameX = 0;':
                translated = 'write_value("wdFrameX", 0)\n' + '\t' * depth + 'write_value("wdFrame", 0)'
            else:
                value = expr(rhs)
                if op != '=':
                    value = f'(number({expr(target)}) {op[0]} number({value}))'
                translated = target + ' = ' + value if target in locals_ else 'write_value(' + json.dumps(field_key(target)) + ', ' + value + ')'
        elif m := re.fullmatch(r'(\w+)\+\+;', line):
            translated = 'increment(' + json.dumps(field_key(m[1])) + ')'
        elif m := re.fullmatch(r'gotoAnd(Stop|Play)\((.+)\);', line):
            translated = 'adapter.goto_label(' + expr(m[2]) + ', ' + str(m[1] == 'Play').lower() + ')'
        elif line == 'play();':
            translated = 'adapter.play_body()'
        elif m := re.fullmatch(r'(_parent|' + re.escape(OPPONENT) + r')\.(moveX|moveY)\((.+)\);', line):
            translated = 'adapter.move_body(' + str(m[1] == OPPONENT).lower() + ', ' + json.dumps(m[2]) + ', ' + expr(m[3]) + ')'
        elif line == '_parent.showdow({R:20,G:-100,B:255});':
            translated = 'adapter.shadow({"R": 20, "G": -100, "B": 255})'
        elif m := re.fullmatch(r'_root.bsd\(pn,("\w+"),false\);', line):
            translated = 'adapter.super_start(' + m[1] + ', false)'
        elif line == '_root.bsw(pn,false);':
            translated = 'adapter.super_end(false)'
        elif line == 'trace("initwudi" + _root.modo + "," + _parent.useAI);':
            translated = 'adapter.trace_init(value("modo"), value("useAI"))'
        elif line == '_parent.swapDepths(' + OPPONENT + ');':
            translated = 'adapter.swap_depths()'
        elif m := re.fullmatch(r'_root.addChildXG\(_parent,("\w+"),([^,]+),([^,]+)\);', line):
            translated = 'adapter.child_effect(' + ', '.join(expr(v) for v in m.groups()) + ')'
        elif m := re.fullmatch(r'_root.addChildXG\(_parent,("\w+")\);', line):
            # Source addChildXG defaults offsetY to -25 and offsetX to 0.
            translated = 'adapter.child_effect(' + expr(m[1]) + ', -25, 0)'
        elif m := re.fullmatch(r'_root.addStgHit\(pn,("\w+"),(.+)\);', line):
            translated = 'adapter.stage_hit(' + expr(m[1]) + ', ' + expr(m[2]) + ')'
        elif m := re.fullmatch(r'(\w+)\((.*)\);', line):
            translated = expr(line[:-1])
        else:
            raise ValueError(f'Unsupported BODY statement in {name}: {line}')
        output.append('\t' * depth + translated)
    if depth != 1:
        raise ValueError('Unbalanced BODY function: ' + name)
    output.append('\treturn null')
    return '\n'.join(output) + '\n'


def compile_body(bundle: dict, sprite: int, *, player: bool = False, form_callbacks: bool = False, form_helpers: bool = False) -> tuple[str, dict]:
    from undefined_body_calls import resolve_undefined_body_calls
    undefined_calls = resolve_undefined_body_calls(bundle, sprite)
    form_callbacks = form_callbacks or form_helpers
    path = f'DefineSprite_{sprite}/frame_1/DoAction.as'
    if hashlib.sha256((ROOT / bundle['game_file']).read_bytes()).hexdigest() != bundle['swf_sha256']:
        raise ValueError('Retained BODY source hash mismatch')
    source = next(s['source'] for s in bundle['scripts'] if s['path'] == path)
    functions = {m[1]: (m[2], m[3]) for m in FUNCTION.finditer(source.replace('\r\n', '\n'))}
    callbacks = {}
    def defer(match: re.Match) -> str:
        name = f'doHurtSkill_timeout_{len(callbacks)}'
        callbacks[name] = ('', match[2])
        return match[1] + f'defer_body("{name}", {match[3]});'
    params, body = functions['doHurtSkill']
    body = re.sub(r'(?m)^( +)setTimeout\(function\(\)\n\1\{\n(.*?)^\1\}\n\1,(\d+)\);', defer, body, flags=re.S)
    if len(callbacks) != 2 or 'setTimeout' in body:
        raise ValueError('Unsupported hurt-skill timeout structure')
    functions['doHurtSkill'] = params, body
    header = '# Generated by tools/importer/compile_ai_body.py; do not edit.\n'
    header += PRELUDE.replace('var state: Dictionary', 'var state: Dictionary\nvar adapter: RefCounted')
    header = header.replace('assert(state.has(key), "Missing AI context field: " + key)\n\treturn state[key]', 'return adapter.read_field(key)')
    header = header.replace('state[key] = v', 'adapter.write_field(key, v)')
    header = header.replace('return state["body_hits"].get(key)', 'return adapter.body_hit(key)')
    header += '\nfunc increment(key: String) -> Variant:\n\tvar n := number(value(key)) + 1\n\twrite_value(key, n)\n\treturn n\n'
    # A platform handle is its positive source index, or undefined when absent.
    header += '\nfunc platform(index: Variant) -> Variant:\n\treturn adapter.platform(index)\n'
    header += '\nfunc platform_field(index: Variant, key: String) -> Variant:\n\treturn adapter.platform_field(index, key)\n'
    header += '\nfunc defer_body(method: String, delay: Variant) -> Variant:\n\tadapter.defer_body(method, delay)\n\treturn null\n'
    for name in sorted(HOST_CALLS):
        header += f'\nfunc {name}() -> Variant:\n\treturn adapter.body_service("{name}")\n'
    extra_calls = frozenset({'source_key'}) if player else frozenset()
    if player:
        header += '\nfunc source_key(key: String) -> Variant:\n\treturn adapter.source_key(key)\n'
    text = header + ''.join(compile_function(name, *functions[name], extra_calls, player=player) for name in NAMES)
    text += ''.join(compile_function(name, *signature, extra_calls, player=player) for name, signature in callbacks.items())
    compiled_names = list(NAMES)
    if form_callbacks:
        found = list(re.finditer(r'^feixue = function\(\)\n\{\n(.*?)^\};',
                             source.replace('\r\n', '\n'), re.M | re.S))
        callback = found[0] if len(found) == 1 else None
        root_source = FUNCTION.sub('', source.replace('\r\n', '\n'))
        receiver_writes = re.findall(r'(?m)^\s*(?:var\s+)?_this\s*=\s*([^;]+);', root_source)
        if receiver_writes != ['this']:
            raise ValueError(f"{bundle['game_file']}:{path}: uncompiled callback receiver binding")
        if callback is None or 'loseHp' not in functions:
            raise ValueError(f"{bundle['game_file']}:{path}: missing form callback/loseHp implementation")
        callback_body = callback[1].replace('_this.hp', 'hp').replace('_root.maxhp', 'maximum_health()')
        callback_body = re.sub(r'\bloseHp\(', 'live_lose_hp(', callback_body)
        try:
            text += '\nfunc maximum_health() -> Variant:\n\treturn adapter.maximum_health()\n'
            text += '\nfunc live_lose_hp(amount: Variant) -> Variant:\n\treturn adapter.call_live_body_function("loseHp", [amount])\n'
            text += compile_function('loseHp', *functions['loseHp'], player=player)
            text += compile_function('feixue', '', callback_body,
                                     frozenset({'live_lose_hp', 'maximum_health'}), player=player)
        except (ValueError, SyntaxError, KeyError) as error:
            raise ValueError(f"{bundle['game_file']}:{path}#feixue/loseHp: {error}") from error
        compiled_names += ['loseHp', 'feixue']
    if form_helpers:
        from compile_form_helpers import compile_helpers, NAMES as FORM_NAMES
        try:
            random_sites = {m[1]: bundle['game_file'].removeprefix('game/').removesuffix('.swf') + '#' + path + ':' + str(line)
                            for line, text_line in enumerate(functions['randAI'][1].splitlines(), 1)
                            if (m := re.fullmatch(r'\s*(attran|defran|goran|jumpran|bisharan) = Math.random\(\) \* _loc\d+_;', text_line))}
            text += compile_helpers(functions, compile_function, random_sites=random_sites)
        except (ValueError, SyntaxError, KeyError) as error:
            raise ValueError(f"{bundle['game_file']}:{path}#form_helpers: {error}") from error
        compiled_names += list(FORM_NAMES)
    for resolved in undefined_calls:
        text += ('\n# The retained source method is absent; keep an explicit call target.\n'
                 'func ' + resolved['name'] + '(_direction: Variant = null) -> Variant:\n\treturn null\n')
    metadata = {'status': 'compiled_not_integrated', 'functions': compiled_names,
                  'host_services': sorted(HOST_CALLS), 'callbacks': list(callbacks),
                  'scalar_fields': sorted(FIELDS), 'external_fields': sorted(set(REFS.values())), 'path': path,
                  'source_swf': bundle['game_file'], 'swf_sha256': bundle['swf_sha256'],
                  'source_sha256': hashlib.sha256(source.encode()).hexdigest()}
    if undefined_calls:
        metadata['undefined_body_calls'] = undefined_calls
    return text, metadata


def compile_player_body(bundle: dict, sprite: int, timeline: dict, *,
                        form_callbacks: bool = False, form_helpers: bool = False) -> tuple[str, dict]:
    code, metadata = compile_body(bundle, sprite, player=True,
                                  form_callbacks=form_callbacks, form_helpers=form_helpers)
    metadata['input_mode'] = 'source_player_branches_preserved'
    hooks = []
    for script in bundle['scripts']:
        if not script['path'].startswith(f'DefineSprite_{timeline["sprite_id"]}/'):
            continue
        compact = re.sub(r'\s+', '', script['source'])
        motion = re.fullmatch(
            r'onClipEvent\(enterFrame\)\{if\(_root\.zhanting==false\)\{'
            r'if\(_parent\._parent\._xscale>0\)\{_parent\._parent\._x\+=Math\.round\(_parent\.speed/(\d+)\);\}'
            r'else\{_parent\._parent\._x-=Math\.round\(_parent\.speed/\1\);\}\}\}', compact)
        if '_parent.beidax(' not in script['source'] and not motion:
            continue
        match = re.fullmatch(r'onClipEvent\(enterFrame\)\{\s*_parent.beidax\((true)?\);\s*\}\s*', script['source'])
        placement = re.fullmatch(r'DefineSprite_\d+/frame_(\d+)/PlaceObject2_(\d+)_(\d+)/CLIPACTIONRECORD onClipEvent\(enterFrame\).as', script['path'])
        if (not match and not motion) or not placement:
            raise ValueError('Unsupported player hurt callback: ' + script['path'])
        frame, controller_id, depth = map(int, placement.groups())
        members = [item['frame'] for item in timeline['frames'] if any(
            p.get('character_id') == controller_id and p['depth'] == depth and p['placed_frame'] == frame
            for p in item['display_list'])]
        if not members:
            raise ValueError('Missing player hurt placement: ' + script['path'])
        operation = {'flying': bool(match[1])} if match else {}
        if motion:
            method = f'placement_frame_{frame}_depth_{depth}'
            callback = script['source'].replace('\r\n', '\n').split('\n', 1)[1].rsplit('}', 1)[0]
            callback = callback.replace('_parent._parent.', '_parent.').replace('_parent.speed', 'value("speed")')
            code += compile_function(method, '', callback, player=True)
            operation = {'body_method': method, 'body_args': [], 'scope_binding': 'controller_parent_is_body'}
        hooks.append({'path': script['path'], 'method': 'enter_frame', 'depth': depth,
                      'placement_frame': frame, 'member_frames': members,
                      **operation, 'source_sha256': hashlib.sha256(script['source'].encode()).hexdigest()})
    metadata['hurt_hooks'] = hooks
    return code, metadata


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--fighter', default='yihu')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--player', action='store_true')
    parser.add_argument('--form-callbacks', action='store_true')
    parser.add_argument('--form-helpers', action='store_true')
    args = parser.parse_args()
    bundle = json.loads((ROOT / f'scripts/fighter/{args.fighter}.json').read_text())
    timeline = json.loads((ROOT / f'data/slices/{args.fighter}-base.timeline.json').read_text())
    code, metadata = compile_body(bundle, timeline['sprite_id'], player=args.player, form_callbacks=args.form_callbacks, form_helpers=args.form_helpers)
    if args.player:
        code, metadata = compile_player_body(bundle, timeline['sprite_id'], timeline,
                                            form_callbacks=args.form_callbacks, form_helpers=args.form_helpers)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'body.gd').write_text(code)
    (args.output / 'body.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'functions': len(NAMES), 'output': str(args.output)}))


if __name__ == '__main__':
    main()
