"""Compile the original menu controller and rasterize its authored presentation."""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from extract_timeline_geometry import extract_frames

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'godot/generated/main/title_menu'
PREFIX = 'DefineSprite_620/frame_1/PlaceObject2_619_28/'

def compile_function(name, source):
    lines = [f'func {name}(held: Dictionary = {{}}) -> void:']
    depth = 1
    source = source[source.index('{') + 1:source.rindex('}')]
    for raw in source.splitlines():
        line = raw.strip()
        if not line: continue
        if line == '{': depth += 1; continue
        if line == '}': depth -= 1; continue
        line = re.sub(r'_parent\["btm" \+ (select|i)\]\._y', r'positions[\1]', line)
        line = re.sub(r'_parent\.btm(\d+)\._y', r'positions[\1]', line)
        line = line.replace('_parent.anj', 'anj')
        line = line.replace('_root.txtst = 0;', 'hint_reset = true;').replace('_root.txt', 'hint')
        for key, slot in [('w','up'),('s','down'),('j','confirm')]:
            line = line.replace(f'Key.isDown(_root.{key})', f'bool(held.get("{slot}", false))')
        line = re.sub(r'_root.keysound([12]).start\(\);', r'sounds.append(\1);', line)
        line = line.replace('_parent["btm" + select].play();', 'confirmed_index = select;')
        if line.startswith(('if(', 'while(')):
            kind = line[:line.index('(')]
            line = kind + ' ' + line[len(kind)+1:-1] + ':'
        elif line == 'else': line = 'else:'
        else:
            assert line.endswith(';'), line
            line = line[:-1]
            line = re.sub(r'^(\w+)\+\+$', r'\1 += 1', line)
        assert '_root' not in line and '_parent' not in line, line
        lines.append('\t' * depth + line)
    assert depth == 1
    return '\n'.join(lines)

def build(workspace, jar, xml):
    bundle = json.loads((ROOT/'scripts/main.json').read_text())
    assert hashlib.sha256((ROOT/'game/main.swf').read_bytes()).hexdigest() == bundle['swf_sha256']
    report = json.loads((xml.parent/'export-report.json').read_text())
    expected = {f['path']:f['sha256'] for f in report['files']}
    assert hashlib.sha256(xml.read_bytes()).hexdigest() == expected[xml.name]
    assert report['source']['sha256'] == bundle['swf_sha256']
    sources = {s['path']:s['source'] for s in bundle['scripts']}
    OUT.mkdir(parents=True, exist_ok=True); workspace.mkdir(parents=True, exist_ok=True)
    java = ['java','-Djava.awt.headless=true']
    bounds = subprocess.check_output(java+['-cp',str(jar),str(ROOT/'tools/importer/MenuExport.java'),str(ROOT/'game/main.swf'),str(workspace/'background.swf')],text=True)
    subprocess.run(java+['-jar',str(jar),'-selectid','666,594,597,600,603,606,609,612,615,672','-export','sprite',str(workspace/'raster'),str(workspace/'background.swf')],check=True,stdout=subprocess.DEVNULL)
    rects={int(v[0]):list(map(int,v[1:])) for v in (line.split() for line in bounds.splitlines())}
    # JPEXS sprite export adds a five-pixel border around the sprite bounds.
    crop=(-rects[666][0]//20+5,-rects[666][1]//20+5)
    for frame in range(1,73):
        im=Image.open(workspace/f'raster/DefineSprite_666/{frame}.png')
        im.crop((*crop,crop[0]+600,crop[1]+400)).save(OUT/f'background-{frame}.png')
    shutil.copyfile(workspace/'raster/DefineSprite_672/1.png', OUT/'footer.png')
    names=['single','vs_com','versus','training','key_settings','about','more','exit']
    titles=['SINGLE PLAY','VS COM','VS MODE','TRAINING','SETTING','ABOUT','MORE GAME','EXIT']
    items=[]
    for i,sid in enumerate(range(594,616,3)):
        path=f'DefineSprite_{sid}/frame_15/DoAction.as'
        source=sources.get(path,'')
        mode=re.search(r'_root.modo = (\d+)',source)
        target=re.search(r'gotoAndStop\("([^"]+)"\)',source)
        files=sorted((workspace/f'raster/DefineSprite_{sid}').glob('*.png'),key=lambda p:int(p.stem))
        for f in files: shutil.copyfile(f,OUT/f'button-{i+1}-{f.stem}.png')
        items.append({'id':names[i],'title':titles[i],'modo':int(mode[1]) if mode else 0,'goto':target[1] if target else '', 'frames':len(files),'confirm_frame':int(re.search(r'frame_(\d+)',path)[1]) if source else 0,'source':path if source else None})
    timeline=extract_frames(xml,666)
    wheel=extract_frames(xml,620)
    placements={p['name']:p for p in wheel['frames'][0]['display_list'] if p.get('name','').startswith('btm')}
    mask=next(p for p in wheel['frames'][0]['display_list'] if p.get('clip_depth'))
    bounds = next(d['shape_bounds_twips'] for d in wheel['definitions'] if d['character_id'] == mask['character_id'])
    sounds = {}
    for tag in ET.parse(xml).getroot().findall("./tags/item[@type='ExportAssetsTag']"):
        for id_, name in zip(tag.find('tags'), tag.find('names')):
            if name.text in ['keysound1.mp3','keysound2.mp3']:
                source = next((xml.parent/'main_assets/sounds').glob(f'{id_.text}_*.mp3'))
                assert hashlib.sha256(source.read_bytes()).hexdigest() == expected[source.relative_to(xml.parent).as_posix()]
                shutil.copyfile(source, OUT/name.text)
                sounds[name.text] = int(id_.text)
    tags=ET.parse(xml).getroot().find('tags')
    ui={}
    for name in ['vertxt','downtxts']:
        tag=next(t for t in tags if t.get('name')==name)
        ui[name] = {k:int(v) for k,v in tag.find('matrix').attrib.items() if k in ['translateX','translateY']}
    hint=next(t for t in tags if t.get('spriteId')=='672')
    ui['hint']={k:int(v) for k,v in next(t for t in hint.find('subTags') if t.get('name')=='txt').find('matrix').attrib.items() if k in ['translateX','translateY']}
    ui['footer_bounds']=rects[672]
    spec={'ui':ui,'mask_bounds_twips':bounds,'sounds':sounds,'source_sha256':bundle['swf_sha256'],'items':items,'wheel_placements':placements,'mask':mask,
          'wheel_frames':[next((p for p in f['display_list'] if p['character_id']==620),None) for f in timeline['frames']],
          'source_scripts':{k:v for k,v in sources.items() if k.startswith(PREFIX) or k.startswith('DefineSprite_597/') or k.startswith('DefineSprite_666/')}}
    (OUT/'menu.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n')
    header='''# Generated from the locked Sprite 620 controller; do not edit.
extends RefCounted
var select: int = 1
var spd: float = 5
var an: int = 0
var anj: int = 0
var i: int = 0
var positions: Dictionary = {}
var hint: String = ""
var hint_reset: bool = false
var sounds: Array = []
var confirmed_index: int = 0
'''
    code=header+'\n'+compile_function('reset',sources[PREFIX+'CLIPACTIONRECORD onClipEvent(load).as'])+'\n\n'+compile_function('tick',sources[PREFIX+'CLIPACTIONRECORD onClipEvent(enterFrame).as'])+'\n'
    (OUT/'controller.gd').write_text(code)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,required=True);p.add_argument('--ffdec',type=Path,required=True);p.add_argument('--xml',type=Path,required=True);a=p.parse_args();build(a.workspace,a.ffdec,a.xml)
