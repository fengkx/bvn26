"""Extract the original Config option writes and input bounds, without guessed ranges."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]


def build() -> dict:
    bundle = json.loads((ROOT/'scripts/main.json').read_text())
    source = {s['path']: s['source'] for s in bundle['scripts']}
    prefix = 'DefineSprite_836/frame_1/'
    rows = []
    for name, child, depth in [('difficulty',691,1),('quality',698,6),('time',735,28),('health',709,11)]:
        path = prefix+f'PlaceObject2_{child}_{depth}/CLIPACTIONRECORD '
        enter = source[path+'onClipEvent(enterFrame).as']
        down = source[path+'onClipEvent(keyDown).as']
        writes = []
        for frame, field, value in re.findall(r'if\(cl == (\d+)\)\s*\{\s*_root\.([\w_]+) = ("[^"]+"|\d+);', enter):
            writes.append({'frame':int(frame),'field':field,'value':json.loads(value)})
        assert writes
        rows.append({'id':name,'row':int(re.search(r'cselect == (\d+)',enter)[1]),
                     'depth':depth,'writes':writes,
                     'left_guard':int(re.search(r'cl >= (\d+)',down)[1]),
                     'right_guard':int(re.search(r'cl <= (\d+)',down)[1]),
                     'sources':{event:source[path+f'onClipEvent({event}).as'] for event in ['load','keyDown','enterFrame']}})
    defaults = source['frame_7/DoAction.as']
    result={'source_sha256':bundle['swf_sha256'],'rows':sorted(rows,key=lambda row:row['row']),
            'defaults':{key:int(re.search(r'var '+key+r' = (\d+);',defaults)[1]) for key in ['AI','maxhp','maxtime']},
            'rendering': {'reference': 'https://airsdk.dev/reference/actionscript/3.0/flash/display/StageQuality.html',
                          'sample_grid': {'HIGH': 4, 'MEDIUM': 2, 'LOW': 1}},
            'selector_sources':{p:s for p,s in source.items() if p.startswith(prefix+'PlaceObject2_739_33/')},
            'panel_sources':{p:s for p,s in source.items() if p.startswith('DefineSprite_836/') and 'PlaceObject' not in p}}
    assert hashlib.sha256((ROOT/'game/main.swf').read_bytes()).hexdigest()==result['source_sha256']
    out=ROOT/'godot/generated/main/config';out.mkdir(parents=True,exist_ok=True)
    (out/'config.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return result


if __name__=='__main__':build()
