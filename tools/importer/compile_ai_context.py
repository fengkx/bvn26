"""Compile source state writes and the base-form AI sensor instance graph."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from compile_ai_predicates import controller_script
from compile_hit_receive import root_position_writes
from build_combat_model import parse_body_warp

ROOT=Path(__file__).resolve().parents[2]
FIELDS={'动作','khit','jump','jumped','canhit','sw','touch','touchFloor','hitBan',
        'dashQL','dashing','dashX','dashY','dashF','hurtSkling','hstm','wdFrame','wdFrameX',
        'wudi','beida','hited','hits','time','bs','airBody','speed','spd','jumpPower','fall',
        'htx','yup','tdtime','hitNear','_lastX','_initwudi','jhp','bdzl','inited','_lastvoice','_dievoicen',
        'Cbshit'}
FUNCTION=re.compile(r'^function (\w+)\([^\n]*\)\r?\n\{.*?^\}',re.M|re.S)
ASSIGN=re.compile(r'^(?:var )?(\w+) = (-?\d+(?:\.\d+)?|true|false);$')
DECLARE=re.compile(r'^var (\w+);$')
ROOT_CLIP_RENAME = re.compile(
    r'(?P<object>[A-Za-z_]\w*)\._name\s*=\s*"(?P<name>[^"]+)"\s*;'
)


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


def writes(source: str, path: str, *, function: bool=False) -> list[dict]:
    lines=source.replace('\r\n','\n').splitlines()
    result=[]
    for number,line in enumerate(lines,1):
        # Frame actions must be top-level. Function onBeHit0 is separately
        # admitted and has only unconditional writes, verified below.
        if function:line=line.strip()
        match=ASSIGN.fullmatch(line)
        if match and match[1] in FIELDS:
            result.append({'field':match[1],'value':json.loads(match[2]),'path':path,'line':number})
        elif line == 'var speed = spd;':
            result.append({'field':'speed','read_field':'spd','path':path,'line':number})
        elif re.match(r'^(?:var )?(\w+)\s*[+*/-]?=',line):
            target=re.match(r'^(?:var )?(\w+)',line)[1]
            if target in FIELDS:
                raise ValueError(f'Unsupported source-state assignment: {path}:{number}: {line}')
    return result



def conditional_frame_calls(text: str, path: str, frame: int) -> list[dict]:
    # Admit the complete source block, not a guessed label/frame exception.
    match = re.fullmatch(
        r'if\(_root\.game\["p" \+ pn\]\.mc\.hp > (-?\d+) && '
        r'_root\.game\["p" \+ pn\]\.mc\.动作 == (-?\d+)\)\s*'
        r'\{\s*gotoAnd(Play|Stop)\("([^"\n]+)"\);\s*play\(\);\s*\}\s*', text)
    if match:
        conditions = [{'field': 'opponent_hp', 'operator': 'gt', 'value': int(match[1])},
                      {'field': 'opponent_action', 'operator': 'eq', 'value': int(match[2])}]
        calls = [{'op': 'timeline_goto', 'label': match[4], 'play': match[3] == 'Play'},
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


def compile_context(bundle: dict,timeline: dict) -> dict:
    if hashlib.sha256((ROOT/bundle['game_file']).read_bytes()).hexdigest()!=bundle['swf_sha256']:
        raise ValueError('Retained source hash mismatch')
    if timeline['source_swf']['sha256']!=bundle['swf_sha256']:
        raise ValueError('Source and timeline hash mismatch')
    sprite=timeline['sprite_id']
    scripts={s['path']:s['source'] for s in bundle['scripts']}
    load_paths = [path for path in scripts if re.fullmatch(
        rf'frame_\d+/PlaceObject2_{sprite}_1/CLIPACTIONRECORD onClipEvent\(load\).as', path)]
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
    declarations=[m[1] for line in root.splitlines() if (m:=DECLARE.fullmatch(line)) and m[1] in FIELDS]
    frame_writes={}
    frame_calls={}
    frames_by_number = {int(item['frame']): item for item in timeline['frames']}
    root_rename_history: list[dict] = []
    for frame in timeline['frames']:
        path=f'DefineSprite_{sprite}/frame_{frame["frame"]}/DoAction.as'
        text=root if frame['frame']==1 else scripts.get(path,'')
        events=writes(text,path)
        if frame['frame'] == 1 and any(event['field'] in ('inited', '_lastX') for event in events):
            raise ValueError('First-init projection conflicts with unconditional frame state writes')
        if events:frame_writes[str(frame['frame'])]=events
        calls=conditional_frame_calls(text, path, frame["frame"])
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
            match=re.fullmatch(r'_root\.(bsd|cbsd|bsw|cbsw)\(pn\);',line)
            face=re.fullmatch(r'_root\.showFace\(pn,"([^"]+)"\);',line)
            jump=re.fullmatch(r'gotoAnd(Play|Stop)\("([^"]+)"\);',line)
            energy=re.fullmatch(r'ql ([+-])= (\d+(?:\.\d+)?);',line)
            if line == 'wankai_start();':
                calls.append({'op': 'inline_frame', 'path': path, 'line': number,
                              'frame': frame['frame'], 'calls': inline_frame_function(
                                  functions['wankai_start'], first_path + '#wankai_start', frame['frame'])})
            elif line == '_root.touchFloorEffect(_parent);':
                calls.append({**root_child_effect('touchFloorEffect'), 'path': path,
                              'line': number, 'frame': frame['frame']})
            elif re.fullmatch(r'_root\.shine\(\);', line):
                calls.append({'op': 'screen_flash', 'color_rgb24': 0xFFFFFF,
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
            elif jump:
                calls.append({'op':'timeline_goto','label':jump[2],'play':jump[1]=='Play',
                              'path':path,'line':number,'frame':frame['frame']})
            elif line in ('play();','stop();'):
                calls.append({'op':'timeline_play' if line=='play();' else 'timeline_stop',
                              'path':path,'line':number,'frame':frame['frame']})
            elif line == 'resColor();':
                calls.append({'op':'color_reset','path':path,'line':number,'frame':frame['frame']})
            elif color_write := re.fullmatch(r'var (_cgap|_csn) = (\d+);',line):
                calls.append({'op':'color_write','field_name':color_write[1],
                              'value':int(color_write[2]),'path':path,'line':number,'frame':frame['frame']})
        if calls:
            frame_calls[str(frame['frame'])]=calls
    hit=functions['onBeHit0']
    if re.search(r'\b(if|else|while|for)\b',hit):
        raise ValueError('onBeHit0 is no longer unconditional')
    hit_writes=writes(hit,first_path+'#onBeHit0',function=True)
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
            'main_floor_contact':floor_contact,
            'undefined_declarations':declarations,'frame_writes':frame_writes,
            'frame_calls':frame_calls,
            'function_writes':{'onBeHit0':hit_writes},
            'random_refresh':{'interval_ms':int(interval[1]),'difficulty_multiplier':int(multiplier[2]),
                              'assignments':random_writes,'init_path':first_path+'#initCtrl',
                              'sample_path':first_path+'#randAI'},
            'sensing':{'activation_frame':2,'placement':ai,'sensors':sensors,'definitions':list(closure.values()),
                       'missing_references':sorted(set(referenced)-{p['name'] for p in sensors})},
            'limits':['Conditional body-state writers still require the body runtime adapter.',
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
