"""Compile source state writes and the base-form AI sensor instance graph."""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from compile_ai_predicates import controller_script, FIELDS as PREDICATE_FIELDS
from compile_hit_receive import root_position_writes
from build_combat_model import parse_body_warp
from inspect_swf import inspect
from import_guards import allowed_frame_source, finite_numbers
from parent_form_requirements import parent_form_requirement

ROOT=Path(__file__).resolve().parents[2]
FIELDS={'动作','khit','jump','jumped','canhit','sw','touch','touchFloor','hitBan',
        'dashQL','dashing','dashX','dashY','dashF','hurtSkling','hstm','wdFrame','wdFrameX',
        'wudi','beida','hited','hits','time','bs','airBody','speed','spd','jumpPower','fall',
        'htx','yup','tdtime','hitNear','_lastX','_initwudi','jhp','bdzl','inited','_lastvoice','_dievoicen',
        'Cbshit'}
# Existing adapter bindings are live owner state, not missing timeline slots.
# In particular, allocating ql here would shadow energy writes and initialize
# a real fighter property to undefined when a form is activated.
HOST_FIELDS = {'hp'} | {
    expression.removeprefix('_parent.') for expression in PREDICATE_FIELDS
    if re.fullmatch(r'_parent\.\w+', expression)
}
FUNCTION=re.compile(r'^function (\w+)\([^\n]*\)\r?\n\{.*?^\}',re.M|re.S)
ASSIGN=re.compile(r'^(?:var )?(\w+) = (-?\d+(?:\.\d+)?|true|false);$')
DECLARE=re.compile(r'^var (\w+);$')
INITIALIZED_DECLARE=re.compile(r'^var (\w+) = (-?\d+(?:\.\d+)?|true|false);$')
POST_INCREMENT=re.compile(r'^(\w+)\+\+;$')
ROOT_CLIP_RENAME = re.compile(
    r'(?P<object>[A-Za-z_]\w*)\._name\s*=\s*"(?P<name>[^"]+)"\s*;'
)


def movement_expression(source: str, fields: set[str]) -> dict:
    """Compile arithmetic over current timeline fields, never source code to eval."""
    operators = {ast.Add: 'add', ast.Sub: 'subtract', ast.Mult: 'multiply', ast.Div: 'divide'}

    def compile_node(node: ast.AST) -> dict:
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            finite_numbers(node.value, 'wrapper movement expression: ' + source)
            return {'op': 'constant', 'value': node.value}
        if isinstance(node, ast.Name) and node.id in fields:
            return {'op': 'read', 'field_name': node.id}
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            return {'op': 'negate' if isinstance(node.op, ast.USub) else 'positive',
                    'operand': compile_node(node.operand)}
        if isinstance(node, ast.BinOp) and type(node.op) in operators:
            return {'op': operators[type(node.op)], 'left': compile_node(node.left),
                    'right': compile_node(node.right)}
        raise ValueError('Unsupported wrapper movement expression: ' + source)

    try:
        return compile_node(ast.parse(source, mode='eval').body)
    except SyntaxError as error:
        raise ValueError('Unsupported wrapper movement expression: ' + source) from error


def root_opponent_warp(text: str, path: str, frame: int) -> list[dict]:
    """Compile source writes that move the opponent player container.

    This is the authored `_root.game["p" + pn]` assignment used by Lee's
    reveal frame.  It is distinct from `_parent` body warps: the target is
    the other fighter container and both coordinates are copied verbatim.
    """
    single = re.fullmatch(r'_root\.game\["p" \+ pn\]\._([xy]) = _parent\._\1;\s*', text)
    if single:
        return [{'op': 'root_opponent_warp', 'copy_x': single[1] == 'x',
                 'copy_y': single[1] == 'y', 'path': path, 'line': 1, 'frame': frame}]
    lines = [line.strip() for line in text.replace('\r\n', '\n').splitlines()]
    if lines != [
        '_root.game["p" + pn]._visible = true;',
        '_root.game["p" + pn]._x = _parent._x;',
        '_root.game["p" + pn]._y = _parent._y;',
        '_root.焦点 = "all";',
    ]:
        return []
    return [{
        'op': 'root_opponent_warp', 'copy_x': True, 'copy_y': True,
        'visible': True, 'focus': 'all', 'path': path, 'line': 2,
        'frame': frame,
    }]


def _root_clip_rename_event(
    text: str,
    path: str,
    frame: int,
    frames_by_number: dict[int, dict],
    prior: list[dict],
) -> list[dict]:
    """Compile only unconditional root display-list identity assignments.

    The display list keeps the authored name for rendering.  The event carries
    the source identity (depth and placed-frame generation) so runtime lookup
    can invalidate the old name without guessing from the current frame.
    """
    lines = text.replace('\r\n', '\n').splitlines()
    result: list[dict] = []
    depth = 0
    for line_number, raw_line in enumerate(lines, 1):
        line = raw_line.strip()
        match = ROOT_CLIP_RENAME.fullmatch(line)
        if match is not None:
            if depth != 0:
                raise ValueError(
                    f"Unsupported controlled root rename: {path}:{line_number}"
                )
            object_name = match["object"]
            source_frame = frames_by_number.get(frame, {})
            records = [
                old for old in prior if old.get("current_name") == object_name
                and next(
                    (
                        item for item in source_frame.get("display_list", [])
                        if int(item.get("depth", -1)) == int(old["depth"])
                        and int(item.get("character_id", 0) or 0) == int(old["character_id"])
                        and int(item.get("placed_frame", frame)) == int(old["placed_frame"])
                    ),
                    None,
                ) is not None
            ]
            if not records:
                placements = [
                    item for item in source_frame.get("display_list", [])
                    if str(item.get("name", "") or "") == object_name
                    and not any(
                        old.get("depth") == int(item.get("depth", -1))
                        and old.get("character_id") == int(item.get("character_id", 0) or 0)
                        and old.get("placed_frame") == int(item.get("placed_frame", frame))
                        and old.get("current_name") != object_name
                        for old in prior
                    )
                ]
                if len(placements) == 1:
                    placement = placements[0]
                    record = {
                        "depth": int(placement["depth"]),
                        "character_id": int(placement.get("character_id", 0) or 0),
                        "placed_frame": int(placement.get("placed_frame", frame)),
                        "visual_name": object_name,
                        "current_name": object_name,
                    }
                    prior.append(record)
                else:
                    # An old source variable is undefined after _name changes.
                    # Ignore that no-op; reject other ambiguous/missing cases.
                    if not placements:
                        continue
                    raise ValueError(
                        f"Root rename target is not uniquely placed: {path}:{line_number}"
                    )
            elif len(records) == 1:
                record = records[0]
            else:
                raise ValueError(
                    f"Root rename target is not uniquely placed: {path}:{line_number}"
                )
            record = {
                "op": "root_clip_rename",
                "source_name": object_name,
                "instance_name": match["name"],
                "depth": int(record["depth"]),
                "character_id": int(record["character_id"]),
                "placed_frame": int(record["placed_frame"]),
                "path": path,
                "line": line_number,
                "frame": frame,
            }
            result.append(record)
            prior_record = next(old for old in prior if old is not record and (
                old.get("depth") == record["depth"]
                and old.get("character_id") == record["character_id"]
                and old.get("placed_frame") == record["placed_frame"]
            )) if any(
                old is not record and old.get("depth") == record["depth"]
                and old.get("character_id") == record["character_id"]
                and old.get("placed_frame") == record["placed_frame"]
                for old in prior
            ) else record
            prior_record["current_name"] = match["name"]
        depth += line.count("{") - line.count("}")
        if depth < 0:
            raise ValueError(f"Unbalanced root rename source: {path}")
    if depth != 0:
        raise ValueError(f"Unbalanced root rename source: {path}")
    return result


def writes(
    source: str,
    path: str,
    *,
    function: bool=False,
    controller_scope_fields: set[str] | None = None,
) -> list[dict]:
    state_fields = FIELDS | (controller_scope_fields or set())
    lines=source.replace('\r\n','\n').splitlines()
    result=[]
    for number,line in enumerate(lines,1):
        # Frame actions must be top-level. Function onBeHit0 is separately
        # admitted and has only unconditional writes, verified below.
        if function:line=line.strip()
        match=ASSIGN.fullmatch(line)
        declaration=INITIALIZED_DECLARE.fullmatch(line)
        if match and match[1] in state_fields:
            result.append({'field':match[1],'value':json.loads(match[2]),'path':path,'line':number})
        elif declaration and declaration[1] in state_fields:
            result.append({'field':declaration[1],'value':json.loads(declaration[2]),'path':path,'line':number})
        elif increment := POST_INCREMENT.fullmatch(line):
            if increment[1] in (controller_scope_fields or set()):
                result.append({'op':'increment','field':increment[1],'delta':1,'path':path,'line':number})
        elif line == 'var speed = spd;':
            result.append({'field':'speed','read_field':'spd','path':path,'line':number})
        elif re.match(r'^(?:var )?(\w+)\s*[+*/-]?=',line):
            target=re.match(r'^(?:var )?(\w+)',line)[1]
            if target in state_fields:
                raise ValueError(f'Unsupported source-state assignment: {path}:{number}: {line}')
    return result


def controller_scope_fields(bundle: dict, sprite: int, *, form_replacement: bool = False) -> set[str]:
    """Find bounded timeline scalar fields read through a controller parent."""
    path = f'DefineSprite_{sprite}/frame_1/DoAction.as'
    source = next((item['source'] for item in bundle['scripts'] if item['path'] == path), None)
    if source is None:
        raise ValueError('Missing controller source timeline: ' + path)
    root = FUNCTION.sub(lambda match: '\n' * match[0].count('\n'), source)
    declared = {
        match[1]
        for line in root.replace('\r\n', '\n').splitlines()
        if (match := DECLARE.fullmatch(line)) or (match := INITIALIZED_DECLARE.fullmatch(line))
    }
    referenced = {
        match[1]
        for item in bundle['scripts']
        if item['path'].startswith(f'DefineSprite_{sprite}/')
        for match in re.finditer(r'\b_parent\.(\w+)\b', item['source'])
    }
    fields = (declared & referenced) - FIELDS
    if form_replacement:
        fields |= implicit_controller_fields(bundle, sprite) - declared
    return fields


def implicit_controller_fields(bundle: dict, sprite: int) -> set[str]:
    """Retain undeclared scalar reads; AVM1 does not synthesize a zero value."""
    placement = re.compile(
        rf'DefineSprite_{sprite}/frame_\d+/PlaceObject[23]_\d+_\d+/'
        r'CLIPACTIONRECORD onClipEvent\(enterFrame\)\.as')
    numeric_read = re.compile(r'(?<![.\w])_parent\.([^\W\d_]\w*)\s*(?:<=|>=|<|>)\s*-?\d+(?:\.\d+)?(?![\w.])')
    return {match[1] for item in bundle['scripts'] if placement.fullmatch(item['path'])
            for match in numeric_read.finditer(item['source'])} - FIELDS - HOST_FIELDS



def conditional_frame_calls(text: str, path: str, frame: int) -> list[dict]:
    parent = re.fullmatch(
        r'if\(_parent\.(\w+) == (true|false)\)\s*\{\s*'
        r'_root\.(cbsw|bsw)\(pn\);\s*bs = 0;\s*\}\s*', text)
    if parent:
        return [{'op': 'parent_conditional_frame', 'path': path, 'line': 1, 'frame': frame,
                 'field_name': parent[1], 'value': json.loads(parent[2]),
                 'calls': [{'op': 'super_end', 'kind': parent[3]},
                           {'op': 'frame_field', 'field_name': 'bs', 'operator': '=', 'value': 0}]}]
    control = re.fullmatch(
        r'if\((\w+) == (true|false|-?\d+)\)\s*\{\s*(stop|play)\(\);\s*\}\s*', text)
    if control and control[1] in FIELDS:
        return [{'op': 'conditional_frame', 'path': path, 'line': 1, 'frame': frame,
                 'conditions': [{'field': control[1], 'operator': 'eq',
                                 'value': json.loads(control[2])}],
                 'calls': [{'op': 'timeline_' + control[3]}]}]
    visibility = re.fullmatch(
        r'if\(_root\.game\["p" \+ pn\]\.mc\.hp > (-?\d+) && '
        r'_root\.game\["p" \+ pn\]\.mc\.动作 == (-?\d+)\)\s*'
        r'\{\s*_root\.game\["p" \+ pn\]\._visible = (true|false);\s*\}'
        r'(?:\s*else\s*\{\s*gotoAnd(Play|Stop)\("([^"\n]+)"\);\s*play\(\);\s*\})?\s*', text)
    if visibility:
        event = {'op': 'conditional_frame', 'path': path, 'line': 1, 'frame': frame,
                 'conditions': [{'field': 'opponent_hp', 'operator': 'gt', 'value': int(visibility[1])},
                                {'field': 'opponent_action', 'operator': 'eq', 'value': int(visibility[2])}],
                 'calls': [{'op': 'opponent_visibility', 'value': visibility[3] == 'true'}]}
        if visibility[4]:
            event['else_calls'] = [{'op': 'timeline_goto', 'label': visibility[5],
                                    'play': visibility[4] == 'Play'}, {'op': 'timeline_play'}]
        return [event]
    visible_jump = re.fullmatch(
        r'if\(_root\.game\["p" \+ pn\]\._visible == (true|false)\)\s*'
        r'\{\s*gotoAnd(Play|Stop)\("([^"\n]+)"\);\s*play\(\);\s*\}\s*', text)
    if visible_jump:
        return [{'op': 'conditional_frame', 'path': path, 'line': 1, 'frame': frame,
                 'conditions': [{'field': 'opponent_visible', 'operator': 'eq', 'value': visible_jump[1] == 'true'}],
                 'calls': [{'op': 'timeline_goto', 'label': visible_jump[3], 'play': visible_jump[2] == 'Play'},
                           {'op': 'timeline_play'}]}]
    # Admit the complete source block, not a guessed label/frame exception.
    contact = re.fullmatch(
        r'if\(_root\.game\["p" \+ pn\]\.mc\.hp <= (-?\d+)\)\s*'
        r'\{\s*return undefined;\s*\}\s*'
        r'if\(_root\.game\["p" \+ pn\]\.mc\.动作 == (-?\d+)\)\s*'
        r'\{\s*gotoAnd(Play|Stop)\("([^"\n]+)"\);\s*play\(\);\s*return undefined;\s*\}\s*'
        r'if\((\w+)\.hitTest\(_root\.game\["p" \+ pn\]\.mc\.bdmn\)\)\s*'
        r'\{\s*gotoAnd\3\("\4"\);\s*play\(\);\s*\}\s*', text)
    if contact:
        return [{'op': 'conditional_frame', 'path': path, 'line': 1, 'frame': frame,
                 'conditions': [{'field': 'opponent_hp', 'operator': 'gt', 'value': int(contact[1])}],
                 'alternatives': [
                     {'field': 'opponent_action', 'operator': 'eq', 'value': int(contact[2])},
                     {'instance': contact[5], 'operator': 'eq', 'value': True}],
                 'calls': [{'op': 'timeline_goto', 'label': contact[4], 'play': contact[3] == 'Play'},
                           {'op': 'timeline_play'}]}]
    match = re.fullmatch(
        r'if\((?:(\w+) && )?_root\.game\["p" \+ pn\]\.mc\.hp > (-?\d+) && '
        r'_root\.game\["p" \+ pn\]\.mc\.动作 == (-?\d+)\)\s*'
        r'\{\s*gotoAnd(Play|Stop)\("([^"\n]+)"\);\s*play\(\);\s*\}\s*', text)
    if match:
        conditions = [{'field': 'opponent_hp', 'operator': 'gt', 'value': int(match[2])},
                      {'field': 'opponent_action', 'operator': 'eq', 'value': int(match[3])}]
        if match[1]:
            conditions.insert(0, {'field': match[1], 'operator': 'eq', 'value': True})
        calls = [{'op': 'timeline_goto', 'label': match[5], 'play': match[4] == 'Play'},
                 {'op': 'timeline_play'}]
    else:
        state = re.fullmatch(
            r'if\((\w+)\s*==\s*(true|false|-?\d+(?:\.\d+)?)\)\s*'
            r'\{\s*gotoAnd(Play|Stop)\("([^"]+)"\);\s*play\(\);\s*\}\s*', text)
        if not state or state[1] not in FIELDS:
            return []
        literal = state[2]
        value = (literal == 'true' if literal in ('true', 'false')
                 else float(literal) if '.' in literal else int(literal))
        # Conditions consume the same named source-state field API as ordinary
        # predicates; the host resolves it from AiSourceState rather than
        # inventing a separate role-specific branch.
        conditions = [{'field': state[1], 'operator': 'eq', 'value': value}]
        calls = [{'op': 'timeline_goto', 'label': state[4], 'play': state[3] == 'Play'},
                 {'op': 'timeline_play'}]
    return [{'op': 'conditional_frame', 'path': path, 'line': 1, 'frame': frame,
             'conditions': conditions, 'calls': calls}]


def inline_frame_function(source: str, path: str, frame: int) -> list[dict]:
    """Compile a complete straight-line function, preserving statement order."""
    body = source[source.index('{') + 1:source.rindex('}')]
    result = []
    for number, raw in enumerate(body.splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        origin = {'path': path, 'line': number, 'frame': frame}
        assignment = re.fullmatch(r'(\w+) (=|-=) (-?\d+|true|false);', line)
        service = re.fullmatch(r'_root\.(bsd|cbsd|bsw|cbsw)\(pn\);', line)
        if assignment and assignment[1] in FIELDS | {'ql'}:
            result.append({'op': 'frame_field', 'field_name': assignment[1],
                           'operator': assignment[2], 'value': json.loads(assignment[3]), **origin})
        elif service:
            result.append({'op': 'super_start' if service[1].endswith('sd') else 'super_end',
                           'kind': service[1], **origin})
        else:
            raise ValueError(f'Uncompiled frame function statement: {path}: {line}')
    return result


def root_child_effect(name: str) -> dict:
    main = json.loads((ROOT / 'scripts/main.json').read_text())
    script = next(s for s in main['scripts'] if s['path'] == 'frame_8/DoAction.as')
    functions = {m[1]: m[0] for m in FUNCTION.finditer(script['source'])}
    source = functions[name]
    match = re.fullmatch(r'function \w+\((\w+)\)\s*\{\s*addChildXG\(\1,"(\w+)",(-?\d+),(-?\d+)\);\s*\}', source)
    if not match:
        raise ValueError('Uncompiled root child-effect wrapper: ' + name)
    return {'op': 'frame_child_effect', 'clip': match[2], 'offset_y': int(match[3]),
            'offset_x': int(match[4]), 'wrapper_path': 'scripts/main.json#' + script['path'] + '#' + name,
            'wrapper_sha256': hashlib.sha256(source.encode()).hexdigest()}


def parent_initial_values(bundle: dict, frame_calls: dict, *, form_replacement: bool = False) -> dict:
    scripts = {item['path']: item['source'] for item in bundle['scripts']}
    parent_fields = {event['field_name'] for calls in frame_calls.values() for event in calls
                     if event['op'] in ('parent_frame_field', 'parent_conditional_frame')}
    if form_replacement:
        # BODY form helpers share the wrapper-owned flag declared by the SWF.
        parent_fields.add("万解")
    parent_state = {}
    for field in sorted(parent_fields):
        declaration = re.findall(rf'^var {re.escape(field)} = (true|false);$',
                                 scripts['frame_1/DoAction.as'].replace('\r\n', '\n'), re.M)
        if len(declaration) != 1:
            raise ValueError(f"{bundle['game_file']}:frame_1/DoAction.as: missing/ambiguous parent boolean initializer: {field}")
        parent_state[field] = json.loads(declaration[0])
    return parent_state


def form_initialization(source: str, location: str) -> dict:
    top_level = FUNCTION.sub('', source)
    compact = re.sub(r'"(?:\\.|[^"\\])*"|\s+',
                     lambda match: match[0] if match[0].startswith('"') else '', top_level)
    statements = ('resColor();_parent.scale_X=_parent._xscale<=0?-1:1;'
                  '_parent._visible=true;_visible=true;varinited;'
                  'if(!inited){trace("inited");inited=true;_lastX=0;'
                  'pn=_parent._name!="p1"?1:2;doWanKai();'
                  'if(!_parent.万解){updateDirect();}}')
    if compact.count(statements) != 1:
        raise ValueError(f'{location}: unsupported replacement initialization/order')
    return {'wrapper_scale_from_xscale': True, 'wrapper_visible': True,
            'body_visible': True, 'bind_opponent_slot': True, 'call_doWanKai': True,
            'update_direct_unless_transformed': True,
            'source_sha256': hashlib.sha256(source.encode()).hexdigest()}


def compile_context(bundle: dict,timeline: dict, *, form_replacement: bool = False) -> dict:
    if hashlib.sha256((ROOT/bundle['game_file']).read_bytes()).hexdigest()!=bundle['swf_sha256']:
        raise ValueError('Retained source hash mismatch')
    if timeline['source_swf']['sha256']!=bundle['swf_sha256']:
        raise ValueError('Source and timeline hash mismatch')
    sprite=timeline['sprite_id']
    scripts={s['path']:s['source'] for s in bundle['scripts']}
    load_paths = [path for path in scripts if re.fullmatch(
        rf'frame_\d+/PlaceObject[23]_{sprite}_1/CLIPACTIONRECORD onClipEvent\(load\).as', path)]
    if len(load_paths) != 1:
        raise ValueError('Expected one form load: ' + str(load_paths))
    load_path = load_paths[0]
    form_frame = int(re.match(r'frame_(\d+)', load_path)[1])
    load_source=scripts[load_path]
    if re.search(r'\b(if|else|while|for)\b',load_source):
        raise ValueError('Conditional body load requires explicit compilation')
    load_writes=writes(load_source,load_path,function=True)
    powers={m[1]:int(m[2]) for m in re.finditer(
        rf'^gjl{form_frame}\.(\w+zl) = (\d+);',scripts['frame_1/DoAction.as'],re.M)}
    if not powers:
        raise ValueError('Missing base form attack powers')
    first_path=f'DefineSprite_{sprite}/frame_1/DoAction.as'
    functions={m[1]:m[0] for m in FUNCTION.finditer(scripts[first_path])}
    floor_branch = re.search(
        r'var (_loc\d+_) = _parent\._y;\s*if\(\1 == _root\.floorY\)\s*'
        r'\{\s*touch = (true|false);\s*touchFloor = (true|false);\s*return undefined;\s*\}',
        functions['on_enterframe'])
    if not floor_branch:
        raise ValueError('Unrecognized exact main-floor contact branch')
    floor_contact = {'comparison': 'equal', 'path': first_path + '#on_enterframe',
                     'source_sha256': hashlib.sha256(functions['on_enterframe'].encode()).hexdigest(),
                     'writes': [{'field': 'touch', 'value': floor_branch[2] == 'true'},
                                {'field': 'touchFloor', 'value': floor_branch[3] == 'true'}]}
    random_function=functions['randAI']
    multiplier=re.search(r'var (\w+) = (\d+) \* _root\.AI;',random_function)
    interval=re.search(r'setInterval\(randAI,(\d+)\)',functions['initCtrl'])
    if not multiplier or not interval:
        raise ValueError('Unsupported AI timer or random multiplier')
    assignments=list(re.finditer(r'(\w+) = Math\.random\(\) \* '+re.escape(multiplier[1])+r';',random_function))
    if len(assignments)!=5:
        raise ValueError('Unexpected AI random assignment count')
    function_offset=scripts[first_path].index(random_function)
    origin=bundle['game_file'].removeprefix('game/').removesuffix('.swf')
    random_writes=[]
    for assignment in assignments:
        offset=function_offset+assignment.start()
        index=len(re.findall(r'Math\.random\(\)',scripts[first_path][:offset]))+1
        random_writes.append({'field':assignment[1],'site':f'{origin}#{first_path}:{index}'})
    # Blank function text keeps the original line indices for every root write.
    root=FUNCTION.sub(lambda m:'\n'*m[0].count('\n'),scripts[first_path].replace('\r\n','\n'))
    initial = re.search(r'if\(!inited\)\n\{\n   trace\("inited"\);\n   inited = true;\n   _lastX = (\d+);\n', root)
    if not initial:
        raise ValueError('Unrecognized first-initialization state guard')
    initialization_state = {
        'guard': 'inited', 'frame': 1, 'path': first_path,
        'line': root[:initial.start()].count('\n') + 1,
        'writes': [{'field': 'inited', 'value': True},
                   {'field': '_lastX', 'value': int(initial[1])}],
        'limits': ['This projects scalar state only; pn binding, doWanKai and updateDirect remain host-owned.'],
    }
    hit_test_pattern = re.compile(
        r'^(\w+) = (\w+)\.hitTest\(_root\.game\["p" \+ pn\]\.mc\.bdmn\);$', re.M)
    hit_fields = {match[1] for path, text in scripts.items()
                  if path.startswith(f'DefineSprite_{sprite}/') and path.endswith('/DoAction.as')
                  for match in hit_test_pattern.finditer(text.replace('\r\n', '\n'))}
    scoped_fields = controller_scope_fields(bundle, sprite, form_replacement=form_replacement) | hit_fields
    state_fields = FIELDS | scoped_fields
    declarations=[
        m[1] for line in root.splitlines()
        if ((m:=DECLARE.fullmatch(line)) or (m:=INITIALIZED_DECLARE.fullmatch(line)))
        and m[1] in state_fields
        and not INITIALIZED_DECLARE.fullmatch(line)
    ]
    if form_replacement:
        # A missing property read has an explicit undefined scalar slot. Its
        # increment and comparison consumers preserve NaN, never default zero.
        declarations = sorted(set(declarations) | (implicit_controller_fields(bundle, sprite) - {
            match[1] for line in root.splitlines()
            if (match := INITIALIZED_DECLARE.fullmatch(line))
        }))
    child_labels = None
    frame_writes={}
    frame_calls={}
    frames_by_number = {int(item['frame']): item for item in timeline['frames']}
    root_rename_history: list[dict] = []
    for frame in timeline['frames']:
        path=f'DefineSprite_{sprite}/frame_{frame["frame"]}/DoAction.as'
        text=root if frame['frame']==1 else scripts.get(path,'')
        if form_replacement and frame['frame'] != 1:
            from compile_form_frames import compile_form_frame
            form_calls = compile_form_frame(bundle, text, path, frame['frame'], form_frame)
            if form_calls is not None:
                frame_calls[str(frame['frame'])] = form_calls
                continue
        if frame['frame'] != 1:
            for number, statement in enumerate(text.splitlines(), 1):
                if re.search(r'\bwankai\s*\(', statement):
                    definition = functions.get('wankai', '')
                    digest = hashlib.sha256(definition.encode()).hexdigest()
                    raise ValueError(f"{bundle['game_file']}:{path}:{number}: uncompiled form replacement call: "
                                     f"{statement.strip()}; definition {first_path}#wankai sha256={digest}; "
                                     "requires wrapper transfer, interval lifetime and parent replacement consumer")
                if re.search(r'_parent\.中转\b', statement):
                    raise ValueError(f"{bundle['game_file']}:{path}:{number}: uncompiled wrapper transfer: {statement.strip()}")
                if re.match(r'\s*_parent\.万解\s*[+*/-]?=', statement) and not re.fullmatch(
                        r'_parent\.万解 = (true|false);', statement):
                    raise ValueError(f"{bundle['game_file']}:{path}:{number}: uncompiled parent boolean write: {statement.strip()}")
                if re.search(r'\bsetInterval\s*\(', statement):
                    raise ValueError(f"{bundle['game_file']}:{path}:{number}: uncompiled frame timer: {statement.strip()}")
        scalar_text = hit_test_pattern.sub(lambda match: ' ' * len(match[0]), text.replace('\r\n', '\n'))
        events=writes(scalar_text,path,controller_scope_fields=scoped_fields)
        if frame['frame'] == 1 and any(event['field'] in ('inited', '_lastX') for event in events):
            raise ValueError('First-init projection conflicts with unconditional frame state writes')
        if events:frame_writes[str(frame['frame'])]=events
        calls=conditional_frame_calls(text, path, frame["frame"])
        for match in hit_test_pattern.finditer(text.replace('\r\n', '\n')):
            calls.append({'op': 'frame_hit_test', 'field_name': match[1],
                          'instance': match[2], 'path': path, 'frame': frame['frame'],
                          'line': text.replace('\r\n', '\n')[:match.start()].count('\n') + 1})
        reveal = re.fullmatch(r'_root\.game\["p" \+ pn\]\._visible = (true|false);\s*', text)
        if reveal:
            calls.append({'op': 'opponent_visibility', 'value': reveal[1] == 'true',
                          'path': path, 'frame': frame['frame'], 'line': 1})
        if frame['frame'] != 1 and re.search(r'\bif\(', text) and 'gotoAnd' in text and not calls:
            raise ValueError('Uncompiled conditional frame jump: ' + path)
        # Root display-list identity changes are source events.  They must be
        # consumed in the same FIFO as other frame calls, rather than inferred
        # from the current frame when collision is queried.
        source_text = scripts.get(path, '')
        calls.extend(_root_clip_rename_event(
            source_text, path, frame['frame'], frames_by_number, root_rename_history
        ))
        calls.extend({'op': 'root_position', 'path': path, 'frame': frame['frame'], **write}
                     for write in root_position_writes(text))
        calls.extend(root_opponent_warp(text, path, frame['frame']))
        # Keep root container warps on the source frame-script FIFO.  A child
        # callback may jump to another label before this root DoAction is
        # drained; consuming the event by its queued source frame preserves
        # the authored order without tying scheduling to a combat field.
        if frame['frame'] != 1:
            warp = parse_body_warp(text)
            if warp is not None:
                warp_line = next(
                    (number for number, line in enumerate(
                        text.replace('\r\n', '\n').splitlines(), 1)
                     if '_parent._xscale' in line or '_parent._x =' in line or '_parent._y =' in line),
                    1,
                )
                calls.append({'op': 'body_warp', 'warp': warp, 'path': path,
                              'line': warp_line, 'frame': frame['frame']})
        for number,line in enumerate(text.replace('\r\n','\n').splitlines(),1):
            before = len(calls)
            match=re.fullmatch(r'_root\.(bsd|cbsd|bsw|cbsw)\(pn\);',line)
            face=re.fullmatch(r'_root\.showFace\(pn,"([^"]+)"\);',line)
            jump=re.fullmatch(r'gotoAnd(Play|Stop)\("([^"]+)"\);',line)
            energy=re.fullmatch(r'ql ([+-])= (\d+(?:\.\d+)?);',line)
            movement=re.fullmatch(r'_parent\.(moveX|moveY)\((.+)\);',line)
            if re.search(r'_parent\.(?:moveX|moveY)\s*\(', line) and not movement:
                raise ValueError(f"Uncompiled wrapper movement: {bundle['game_file']}:{path}:{number}: {line}")
            if line == 'wankai_start();':
                calls.append({'op': 'inline_frame', 'path': path, 'line': number,
                              'frame': frame['frame'], 'calls': inline_frame_function(
                                  functions['wankai_start'], first_path + '#wankai_start', frame['frame'])})
            elif child_effect := re.fullmatch(r'_root\.(touchFloorEffect|shunbuxg)\(_parent\);', line):
                calls.append({**root_child_effect(child_effect[1]), 'path': path,
                              'line': number, 'frame': frame['frame']})
            elif flash := re.fullmatch(r'_root\.shine\((\d*)\);', line):
                color = int(flash[1]) if flash[1] else 0xFFFFFF
                if not 0 <= color <= 0xFFFFFF:
                    raise ValueError(f"{bundle['game_file']}:{path}:{number}: unsupported shine color {color}")
                calls.append({'op': 'screen_flash', 'color_rgb24': color,
                              'path': path, 'line': number, 'frame': frame['frame']})
            elif movement:
                wrapper = next((m[0] for m in FUNCTION.finditer(scripts['frame_1/DoAction.as'])
                                if m[1] == movement[1]), '')
                expected = ('function moveX(spd){_X=_X+spd*scale_X;}' if movement[1] == 'moveX'
                            else 'function moveY(spd){_Y=_Y+spd;}')
                if re.sub(r'\s+', '', wrapper) != re.sub(r'\s+', '', expected):
                    raise ValueError('Unsupported wrapper movement implementation: ' + movement[1])
                # Preserve literal events; expression operands read state when
                # the ordered frame event executes, not at import time.
                operand = ({'pixels': float(movement[2])}
                           if re.fullmatch(r'-?\d+(?:\.\d+)?', movement[2])
                           else {'pixels_expression': movement_expression(movement[2], FIELDS | scoped_fields)})
                calls.append({'op': 'wrapper_move', 'axis': movement[1], **operand,
                              'path': path, 'line': number, 'frame': frame['frame']})
            elif energy:
                calls.append({'op':'energy_delta','delta':float(energy[2]) * (1 if energy[1]=='+' else -1),
                              'path':path,'line':number,'frame':frame['frame']})
            elif match:
                calls.append({'op':'super_start' if match[1].endswith('sd') else 'super_end',
                              'kind':match[1],'path':path,'line':number,'frame':frame['frame']})
            elif face:
                calls.append({'op':'show_face','face_label':face[1],
                              'path':path,'line':number,'frame':frame['frame']})
            elif parent_write := re.fullmatch(r'_parent\.(万解) = (true|false);', line):
                calls.append({'op': 'parent_frame_field', 'field_name': parent_write[1],
                              'value': json.loads(parent_write[2]), 'path': path,
                              'line': number, 'frame': frame['frame']})
            elif parent_jump := re.fullmatch(r'_parent.gotoAnd(Play|Stop)\((\d+)\);', line):
                location = f"{bundle['game_file']}:{path}:{number}"
                requirement = parent_form_requirement(bundle, int(parent_jump[2]), location)
                raise ValueError(f"{location}: uncompiled frame call: {line} "
                                 f"requires parent frame {requirement['target_parent_frame']} replacement "
                                 f"body {requirement['target_body_sprite']} at depth {requirement['target_depth']}; "
                                 f"load {requirement['load_path']}; missing replacement runtime/assets")
            elif numeric_jump := re.fullmatch(r'gotoAnd(Play|Stop)\((\d+)\);', line):
                target = int(numeric_jump[2])
                if target not in frames_by_number:
                    raise ValueError(f"{bundle['game_file']}:{path}:{number}: numeric goto target {target} is not retained")
                # Cross-label numeric jumps need the destination action metadata
                # consumer as well as a playhead change. Reject until verified.
                label_starts = sorted(int(f['frame']) for f in timeline['frames'] if f.get('labels'))
                source_span = max((n for n in label_starts if n <= frame['frame']), default=1)
                target_span = max((n for n in label_starts if n <= target), default=1)
                if source_span != target_span:
                    raise ValueError(f"{bundle['game_file']}:{path}:{number}: numeric goto across label spans is unimplemented: {target}")
                calls.append({'op': 'timeline_goto_frame', 'target_frame': target,
                              'play': numeric_jump[1] == 'Play',
                              'path': path, 'line': number, 'frame': frame['frame']})
            elif jump:
                calls.append({'op':'timeline_goto','label':jump[2],'play':jump[1]=='Play',
                              'path':path,'line':number,'frame':frame['frame']})
            elif line in ('play();','stop();'):
                calls.append({'op':'timeline_play' if line=='play();' else 'timeline_stop',
                              'path':path,'line':number,'frame':frame['frame']})
            elif follow := re.fullmatch(r'followMc\((\w+),(true|false),(true|false),(true|false)\);', line):
                # The optional flags have meaning only for this verified shared source body.
                if hashlib.sha256(functions['followMc'].encode()).hexdigest() != '1f4dfc7ebc190914ee78d796cde1c64abfb1ab0871670ff8c78959fc0929d612':
                    raise ValueError('Unsupported followMc implementation: ' + first_path)
                calls.append({'op': 'follow_clip', 'instance': follow[1],
                              'place_x': follow[2] == 'true', 'place_y': follow[3] == 'true',
                              'front_only': follow[4] == 'true', 'path': path, 'line': number,
                              'frame': frame['frame'],
                              'function_sha256': hashlib.sha256(functions['followMc'].encode()).hexdigest()})
            elif child_jump := re.fullmatch(r'(\w+)\.gotoAnd(Play|Stop)\("([^"\n]+)"\);', line):
                if child_labels is None:
                    child_labels = {int(t['name'].removeprefix('sprite_')): {l['label']: l['frame'] for l in t['labels']}
                                    for t in inspect(ROOT / bundle['game_file'])['timelines'] if t['name'].startswith('sprite_')}
                targets = []
                for placement in frame['display_list']:
                    cid = int(placement.get('character_id', 0) or 0)
                    aliases = {placement.get('name')}
                    aliases.update(m[1] for p, body in scripts.items() if p.startswith(f'DefineSprite_{cid}/')
                                   for m in re.finditer(r'_name = "([^"\n]+)";', body))
                    if child_jump[1] in aliases and child_jump[3] in child_labels.get(cid, {}):
                        targets.append({'authored_name': placement['name'], 'character_id': cid,
                                        'target_frame': child_labels[cid][child_jump[3]]})
                if len(targets) != 1:
                    raise ValueError('Ambiguous child timeline jump: ' + path)
                calls.append({'op': 'child_timeline_goto', 'instance': child_jump[1],
                              'play': child_jump[2] == 'Play', **targets[0],
                              'path': path, 'line': number, 'frame': frame['frame']})
            elif line == 'resColor();':
                calls.append({'op':'color_reset','path':path,'line':number,'frame':frame['frame']})
            elif line == 'updateDirect();':
                calls.append({'op':'update_direct','path':path,'line':number,'frame':frame['frame']})
            elif color_write := re.fullmatch(r'var (_cgap|_csn) = (\d+);',line):
                calls.append({'op':'color_write','field_name':color_write[1],
                              'value':int(color_write[2]),'path':path,'line':number,'frame':frame['frame']})
            owned = re.match(
                r'^(?:_parent\.(?:moveX|moveY)|_root\.(?:bsd|cbsd|bsw|cbsw|showFace|touchFloorEffect)|'
                r'_root\.(?:shine|shunbuxg)|(?:\w+\.)?(?:gotoAndPlay|gotoAndStop|play|stop)|'
                r'followMc|resColor|updateDirect|wankai_start)\s*\(', line.lstrip())
            if frame['frame'] != 1 and owned and len(calls) == before and not allowed_frame_source(
                    bundle, path, text, form_frame):
                # Whole-block conditional compilation already owns its calls.
                if not any(event.get('op') in ('conditional_frame', 'parent_conditional_frame') for event in calls):
                    raise ValueError(f"{bundle['game_file']}:{path}:{number}: uncompiled frame call: {line}")
        if calls:
            frame_calls[str(frame['frame'])]=calls
    parent_state = parent_initial_values(bundle, frame_calls, form_replacement=form_replacement)
    hit=functions['onBeHit0']
    if re.search(r'\b(if|else|while|for)\b',hit):
        raise ValueError('onBeHit0 is no longer unconditional')
    hit_writes=writes(hit,first_path+'#onBeHit0',function=True,
                      controller_scope_fields=scoped_fields)
    definitions={d['character_id']:d for d in timeline['definitions']}
    ai=next(p for p in timeline['frames'][0]['display_list'] if p.get('name')=='AImain')
    definition=definitions[ai['character_id']]
    if definition['frame_count']!=2 or definition['display_list_frames'][0]:
        raise ValueError('Unexpected AI activation timeline')
    sensors=definition['display_list_frames'][1]
    closure={}
    def visit(cid):
        if cid in closure:return
        d=definitions[cid];closure[cid]=d
        for child in d.get('referenced_character_ids',[]):visit(child)
    for p in sensors:visit(p['character_id'])
    referenced=sorted(set(re.findall(r'_parent\.AImain\.(\w+)\.hitTest',controller_script(bundle, sprite)['source'])))
    return {'format':'bvn26-ai-context-v1','status':'source_compiled_partial',
            'source_swf':timeline['source_swf'],'sprite_id':sprite,
            'load_writes':load_writes,'base_power_fields':powers,
            'initialization_state':initialization_state,
            **({'form_initialization': form_initialization(scripts[first_path],
                 f"{bundle['game_file']}:{first_path}")} if form_replacement else {}),
            'main_floor_contact':floor_contact,
            'undefined_declarations':declarations,'controller_scope_fields':sorted(scoped_fields),
            'frame_writes':frame_writes,
            'frame_calls':frame_calls,
            **({'parent_initial_values': parent_state} if parent_state else {}),
            'function_writes':{'onBeHit0':hit_writes},
            'random_refresh':{'interval_ms':int(interval[1]),'difficulty_multiplier':int(multiplier[2]),
                              'assignments':random_writes,'init_path':first_path+'#initCtrl',
                              'sample_path':first_path+'#randAI'},
            'sensing':{'activation_frame':2,'placement':ai,'sensors':sensors,'definitions':list(closure.values()),
                       'missing_references':sorted(set(referenced)-{p['name'] for p in sensors})},
            'limits':['Conditional body-state writers still require the body runtime adapter.',
                      'Controller-scope increment events require runtime source-state support before integration.',
                      'Undefined declarations initialize new instances only; revisiting frame 1 preserves existing values.']}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--fighter',required=True)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    bundle=json.loads((ROOT/f'scripts/fighter/{args.fighter}.json').read_text())
    timeline=json.loads((ROOT/f'data/slices/{args.fighter}-base.timeline.json').read_text())
    result=compile_context(bundle,timeline)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'fighter':args.fighter,'state_frames':len(result['frame_writes']),
                      'sensors':len(result['sensing']['sensors']),'missing':result['sensing']['missing_references']}))


if __name__=='__main__':main()
