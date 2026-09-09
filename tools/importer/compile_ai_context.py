"""Compile source state writes and the base-form AI sensor instance graph."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[2]
FIELDS={'动作','khit','jump','jumped','canhit','sw','touch','touchFloor','hitBan',
        'dashQL','dashing','dashX','dashY','dashF','hurtSkling','hstm','wdFrame','wdFrameX',
        'wudi','beida','hited','hits','time','bs','airBody','speed','spd','jumpPower','fall',
        'htx','yup','tdtime','hitNear','_lastX','_initwudi','jhp','bdzl','inited','_lastvoice','_dievoicen'}
FUNCTION=re.compile(r'^function (\w+)\([^\n]*\)\r?\n\{.*?^\}',re.M|re.S)
ASSIGN=re.compile(r'^(?:var )?(\w+) = (-?\d+(?:\.\d+)?|true|false);$')
DECLARE=re.compile(r'^var (\w+);$')


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


def compile_context(bundle: dict,timeline: dict) -> dict:
    if hashlib.sha256((ROOT/bundle['game_file']).read_bytes()).hexdigest()!=bundle['swf_sha256']:
        raise ValueError('Retained source hash mismatch')
    if timeline['source_swf']['sha256']!=bundle['swf_sha256']:
        raise ValueError('Source and timeline hash mismatch')
    sprite=timeline['sprite_id']
    scripts={s['path']:s['source'] for s in bundle['scripts']}
    load_path=f'frame_1/PlaceObject2_{sprite}_1/CLIPACTIONRECORD onClipEvent(load).as'
    load_source=scripts[load_path]
    if re.search(r'\b(if|else|while|for)\b',load_source):
        raise ValueError('Conditional body load requires explicit compilation')
    load_writes=writes(load_source,load_path,function=True)
    powers={m[1]:int(m[2]) for m in re.finditer(
        r'^gjl1\.(\w+zl) = (\d+);',scripts['frame_1/DoAction.as'],re.M)}
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
    for frame in timeline['frames']:
        path=f'DefineSprite_{sprite}/frame_{frame["frame"]}/DoAction.as'
        text=root if frame['frame']==1 else scripts.get(path,'')
        events=writes(text,path)
        if frame['frame'] == 1 and any(event['field'] in ('inited', '_lastX') for event in events):
            raise ValueError('First-init projection conflicts with unconditional frame state writes')
        if events:frame_writes[str(frame['frame'])]=events
        calls=[]
        for number,line in enumerate(text.replace('\r\n','\n').splitlines(),1):
            match=re.fullmatch(r'_root\.(bsd|cbsd|bsw|cbsw)\(pn\);',line)
            face=re.fullmatch(r'_root\.showFace\(pn,"([^"]+)"\);',line)
            jump=re.fullmatch(r'gotoAnd(Play|Stop)\("([^"]+)"\);',line)
            energy=re.fullmatch(r'ql ([+-])= (\d+(?:\.\d+)?);',line)
            if energy:
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
    referenced=sorted(set(re.findall(r'_parent\.AImain\.(\w+)\.hitTest',scripts['DefineSprite_16/frame_1/DoAction.as'])))
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
    parser.add_argument('--fighter',choices=('minren','yihu'),required=True)
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
