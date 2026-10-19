"""Compile the retained standard AI predicates to native GDScript.

This is an offline, deliberately bounded source compiler. Unsupported source is
an error. Generated code has no parser, bytecode or ActionScript interpreter.
The context ABI is analysis-only until the battle adapter is verified.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
FUNCTION = re.compile(r"^function (\w+)\(([^)]*)\)\n\{\n(.*?)^\}", re.M | re.S)
NAMES = (
    "gameRunning", "wankai", "moveLeft", "moveRight", "airhit", "airMagichit",
    "holdJ", "holdU", "nornalhit", "combohitAI", "magichit1", "magichit2",
    "magichit3", "skill1", "skill2", "jump", "jumpDown", "rush", "hide",
    "defence", "standup", "zhaoHuan", "bisha", "bishaUP", "bishaAir",
    "bishaSuper", "isPoFangAct",
)
DISPATCH_NAMES = (
    "doAllAction", "doStand", "onJumping", "onDefence", "onDashing",
    "doDropDown", "moveX", "moveY",
)
OPPONENT = '_root.game["p" + _parent.pn]'
FIELDS = {
    '_parent._parent.useAI': 'useAI',
    OPPONENT + '.mc.动作': 'opponent_action',
    '_root.game["p" + _parent.pn + "fz"].动作': 'opponent_helper_action',
    OPPONENT + '.mc.sw': 'opponent_sw',
    OPPONENT + '._x': 'opponent_x', OPPONENT + '._y': 'opponent_y',
    OPPONENT + '._visible': 'opponent_visible',
    '_parent._parent._x': 'x', '_parent._parent._y': 'y',
    '_parent._parent.scale_X': 'scale_X', '_parent._parent._xscale': 'xscale',
    '_root.zhanting': 'root_paused',
    **{'_parent.' + key: key for key in (
        'attran', 'defran', 'goran', 'jumpran', 'bisharan', 'touchFloor', 'ql', 'canhit', 'sw',
        'speed', 'jumpPower', 'jumped', 'fall', 'khit', 'touch',
    )},
    '_root.zhongli': 'gravity',
}

# Scalar conversion is limited to the values used by these predicates. Missing
# numeric values remain NaN; missing booleans do not become an explicit false.
PRELUDE = '''extends RefCounted

var state: Dictionary

func _init(context: Dictionary) -> void:
\tstate = context

func value(key: String) -> Variant:
\tassert(state.has(key), "Missing AI context field: " + key)
\treturn state[key]

func sensor(key: String) -> Variant:
\treturn state["sensors"].get(key)

func body_hit(key: String) -> Variant:
\treturn state["body_hits"].get(key)

func write_value(key: String, v: Variant) -> void:
\tstate[key] = v

func power(key: String) -> Variant:
\treturn state["power"].get(key)

func number(v: Variant) -> float:
\tif v == null:
\t\treturn NAN
\tassert(v is bool or v is int or v is float)
\treturn float(v)

func truth(v: Variant) -> bool:
\tif v == null:
\t\treturn false
\tif v is bool:
\t\treturn v
\tif v is int or v is float:
\t\treturn not is_nan(float(v)) and v != 0
\tassert(v is String)
\treturn not v.is_empty()

func equal(a: Variant, b: Variant) -> bool:
\tif a == null or b == null:
\t\treturn a == null and b == null
\tif a is String and b is String:
\t\treturn a == b
\treturn number(a) == number(b)

func strict(a: Variant, b: Variant) -> bool:
\treturn typeof(a) == typeof(b) and equal(a, b)

func source_round(v: Variant) -> float:
\treturn floor(number(v) + 0.5)
'''


def normalize(expr: str) -> str:
    expr = re.sub(r'_parent\.kis\(_parent\.(左|右|上|下|斩|跳|冲|招|必杀|换)\)',
                  lambda match: 'source_key(' + json.dumps(match[1], ensure_ascii=False) + ')', expr)
    expr = re.sub(r'_parent\.AImain\.(\w+)\.hitTest\(' + re.escape(OPPONENT + '.mc.bdmn') + r'\)',
                  lambda m: f'sensor("{m[1]}")', expr)
    expr = re.sub(r'_parent\.(\w+)\.hitTest\(' + re.escape(OPPONENT + '.mc.bdmn') + r'\)',
                  lambda m: f'body_hit("{m[1]}")', expr)
    expr = expr.replace('_parent._parent._curGJL[name + "zl"]', 'power(name + "zl")')
    for source, target in sorted(FIELDS.items(), key=lambda item: -len(item[0])):
        expr = expr.replace(source, f'value("{target}")')
    expr = expr.replace('Math.abs', 'abs').replace('Math.round', 'source_round').replace('isNaN', 'is_nan')
    # The only strict comparison in these functions is combo === true.
    expr = expr.replace('combo === true', 'strict(combo, True)')
    expr = re.sub(r'\btrue\b', 'True', expr)
    expr = re.sub(r'\bfalse\b', 'False', expr)
    expr = re.sub(r'\bundefined\b', 'None', expr)
    expr = expr.replace('&&', ' and ').replace('||', ' or ')
    expr = re.sub(r'!(?!=)', 'not ', expr)
    # Source has one ternary, in rush's facing assignment.
    if '?' in expr:
        cond, branches = expr.split('?', 1)
        yes, no = branches.split(':', 1)
        expr = f'({yes}) if ({cond}) else ({no})'
    return expr.strip()


def emit(node: ast.AST, locals_: set[str], extra_calls: frozenset[str] = frozenset(), call_aliases: dict[str, str] | None = None) -> str:
    call_aliases = call_aliases or {}
    if isinstance(node, ast.Constant):
        if node.value is None:
            return 'null'
        if isinstance(node.value, bool):
            return str(node.value).lower()
        return json.dumps(node.value, ensure_ascii=False)
    if isinstance(node, ast.Name) and node.id in locals_:
        return node.id
    if isinstance(node, ast.Dict) and 'literal_object' in extra_calls:
        if any(not isinstance(key, ast.Constant) or not isinstance(key.value, str) for key in node.keys):
            raise ValueError('Only explicit source object keys are supported')
        return '{' + ', '.join(emit(key, locals_, extra_calls, call_aliases) + ': ' + emit(value, locals_, extra_calls, call_aliases)
                              for key, value in zip(node.keys, node.values)) + '}'
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        name = node.func.id
        if name not in {*NAMES, *DISPATCH_NAMES, *extra_calls, 'source_key', 'value', 'sensor', 'body_hit', 'power', 'strict', 'abs', 'is_nan', 'source_round'} or node.keywords:
            raise ValueError(f'Unsupported call: {ast.dump(node)}')
        args = [emit(arg, locals_, extra_calls, call_aliases) for arg in node.args]
        if name in {'abs', 'is_nan'}:
            args = ['number(' + arg + ')' for arg in args]
        return call_aliases.get(name, name) + '(' + ', '.join(args) + ')'
    if isinstance(node, ast.UnaryOp):
        val = emit(node.operand, locals_, extra_calls, call_aliases)
        if isinstance(node.op, ast.Not):
            return '(not truth(' + val + '))'
        if isinstance(node.op, ast.USub):
            return '(-number(' + val + '))'
    if isinstance(node, ast.BoolOp):
        op = ' and ' if isinstance(node.op, ast.And) else ' or '
        return '(' + op.join('truth(' + emit(v, locals_, extra_calls, call_aliases) + ')' for v in node.values) + ')'
    if isinstance(node, ast.Compare):
        # AS2 chained comparisons are left-associative, unlike Python chains.
        left = emit(node.left, locals_, extra_calls, call_aliases)
        for op, right_node in zip(node.ops, node.comparators):
            right = emit(right_node, locals_, extra_calls, call_aliases)
            if isinstance(op, (ast.Eq, ast.NotEq)):
                left = ('not ' if isinstance(op, ast.NotEq) else '') + f'equal({left}, {right})'
            else:
                symbol = {ast.Lt: '<', ast.Gt: '>', ast.LtE: '<=', ast.GtE: '>='}.get(type(op))
                if symbol is None:
                    raise ValueError(f'Unsupported comparison: {ast.dump(node)}')
                left = f'(number({left}) {symbol} number({right}))'
        return '(' + left + ')'
    if isinstance(node, ast.BinOp):
        a, b = emit(node.left, locals_, extra_calls, call_aliases), emit(node.right, locals_, extra_calls, call_aliases)
        if isinstance(node.op, ast.Add) and isinstance(node.right, ast.Constant) and isinstance(node.right.value, str):
            return f'({a} + {b})'
        op = {ast.Add: '+', ast.Sub: '-', ast.Mult: '*', ast.Div: '/'}.get(type(node.op))
        if op:
            return f'(number({a}) {op} number({b}))'
    if isinstance(node, ast.IfExp):
        return f'({emit(node.body, locals_, extra_calls, call_aliases)} if truth({emit(node.test, locals_, extra_calls, call_aliases)}) else {emit(node.orelse, locals_, extra_calls, call_aliases)})'
    raise ValueError(f'Unsupported AI expression: {ast.dump(node)}')


def expression(source: str, locals_: set[str], call_aliases: dict[str, str] | None = None) -> str:
    aliases = call_aliases or {}
    return emit(ast.parse(normalize(source), mode='eval').body, locals_, frozenset(aliases), aliases)


def compile_function(name: str, params: str, body: str, *, player: bool = False) -> str:
    # Specialize only the explicit player-input branch. Other guards stay in
    # source order, including ql and touchFloor checks before this branch.
    if not player:
        body = re.sub(r'(?m)^( +)if\(!_parent\._parent\.useAI\)\n\1\{\n.*?^\1\}\n', '', body, flags=re.S)
    params_list = [p.strip() for p in params.split(',') if p.strip()]
    locals_ = set(params_list)
    output = ['', f'func {name}(' + ', '.join(p + ': Variant = null' for p in params_list) + ') -> Variant:']
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
                raise ValueError(f'Unbalanced function: {name}')
            continue
        indent = '\t' * depth
        if line.startswith('if(') and line.endswith(')'):
            translated = 'if truth(' + expression(line[3:-1], locals_) + '):'
        elif line == 'else':
            translated = 'else:'
        elif line.startswith('return ') and line.endswith(';'):
            translated = 'return ' + expression(line[7:-1], locals_)
        elif re.fullmatch(r'var \w+;', line):
            local = line[4:-1]
            locals_.add(local)
            translated = f'var {local}: Variant = null'
        else:
            match = re.fullmatch(r'(.+?) = (.+);', line)
            if not match:
                raise ValueError(f'Unsupported AI statement in {name}: {line}')
            target, value = match.groups()
            if target in locals_:
                translated = target + ' = ' + expression(value, locals_)
            elif target in FIELDS:
                translated = f'write_value("{FIELDS[target]}", ' + expression(value, locals_) + ')'
            else:
                raise ValueError(f'Unsupported AI assignment: {line}')
        output.append(indent + translated)
    if depth != 1:
        raise ValueError(f'Unbalanced function: {name}')
    return '\n'.join(output) + '\n'


def compile_source(source: str, *, player: bool = False) -> str:
    funcs = {m[1]: (m[2], m[3]) for m in FUNCTION.finditer(source.replace('\r\n', '\n'))}
    missing = set(NAMES) - funcs.keys()
    if missing:
        raise ValueError(f'Missing source functions: {sorted(missing)}')
    header = '# Generated by tools/importer/compile_ai_predicates.py; do not edit.\n'
    header += '# Source SHA-256: ' + hashlib.sha256(source.encode()).hexdigest() + '\n'
    keys = '\nfunc source_key(key: String) -> Variant:\n\treturn value("key:" + key)\n' if player else ''
    return header + PRELUDE + keys + ''.join(compile_function(name, *funcs[name], player=player) for name in NAMES)


def controller_aliases(bundle: dict, sprite: int | None = None, *, base_only: bool = False) -> list[dict]:
    if sprite is None:
        loads = [re.match(r'frame_1/PlaceObject[23]_(\d+)_1/', s['path'])
                 for s in bundle['scripts']]
        ids = {int(m[1]) for m in loads if m}
        if len(ids) != 1:
            raise ValueError(f'Expected one root base-form placement, got {ids}')
        sprite = ids.pop()
    placement_pattern = rf'DefineSprite_{sprite}/frame_(\d+)/PlaceObject[23]_(\d+)_'
    placed = {
        int(m[2]) for s in bundle['scripts']
        if (m := re.match(placement_pattern, s['path']))
        and (not base_only or int(m[1]) == 1)
    }
    required_functions = set(NAMES) | set(DISPATCH_NAMES)
    candidates = [s for s in bundle['scripts']
                  if (m := re.fullmatch(r'DefineSprite_(\d+)/frame_1/DoAction.as', s['path']))
                  and int(m[1]) in placed
                  and 'function gameRunning()' in s['source']
                  and 'function moveLeft()' in s['source']
                  and required_functions.issubset(
                      match[1] for match in FUNCTION.finditer(
                          s['source'].replace('\r\n', '\n')
                      )
                  )]
    if not candidates:
        raise ValueError(f'Expected at least one placed input controller, got {len(candidates)}')
    if base_only:
        source_hashes = {hashlib.sha256(candidate['source'].encode()).hexdigest()
                         for candidate in candidates}
        if len(source_hashes) != 1:
            raise ValueError('Base-form input controllers do not share one exact source hash')
    return sorted(candidates, key=lambda candidate: candidate['path'])


def controller_script(bundle: dict, sprite: int | None = None) -> dict:
    """Return the controller active on the requested base-form placement."""
    return controller_aliases(bundle, sprite, base_only=True)[0]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--bundle', type=Path, default=ROOT / 'scripts/fighter/yihu.json')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    bundle = json.loads(args.bundle.read_text())
    if hashlib.sha256((ROOT / bundle['game_file']).read_bytes()).hexdigest() != bundle['swf_sha256']:
        raise ValueError('Retained source SWF hash mismatch')
    source = controller_script(bundle)['source']
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(compile_source(source))
    print(json.dumps({'functions': len(NAMES), 'output': str(args.output)}))


if __name__ == '__main__':
    main()
