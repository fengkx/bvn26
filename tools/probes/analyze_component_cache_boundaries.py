"""Measure original component cache boundaries before combining authored inner transforms."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
from PIL import Image
from tools.probes.analyze_jiraiya_filter_boundary import ROOT,comparison
from tools.probes.analyze_blur_kernel_heldout import render
from tools.probes.run_nested_filters import unpack


def decode(native):
    build=json.loads((native/'build.json').read_text())
    for path,digest in [(build['source'],build['source_sha256']),(build['harness_source'],build['harness_sha256'])]:
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest
    path=native/'native.log';text=path.read_text() if path.exists() else gzip.decompress(path.with_suffix('.log.gz').read_bytes()).decode()
    events=[line.split('|') for line in text.splitlines() if line.startswith('AIREF|')]
    assert len(events)==3616 and events[-1][6:]==['done','ok']
    images={};matrices=[];access=[];props=[]
    for i,event in enumerate(events):
        assert event[1]==build['run_id'] and event[2:6]==[str(i),'0','0','0']
        kind,value=event[6:]
        if kind=='matrix':
            values=list(map(float,value.split(',')));assert len(values)==14 and values[0]==len(matrices)
            matrices.append(values)
        elif kind=='shape_access':access.append(value.split(','))
        elif kind=='props':props.append(value.split(','))
        elif kind=='row':
            label,y,values=value.split(',',2);pixels=images.setdefault(label,[])
            assert len(pixels)==int(y)*600
            values=list(map(int,values.split(',')));assert len(values)==1200
            pixels.extend(unpack(values))
        else:assert kind=='done'
    assert len(images)==9 and all(len(p)==240000 for p in images.values())
    assert len(props)==9 and len(access)==3 and len(matrices)==3
    return build,images,matrices,access,props


def analyze(native,output=None):
    build,images,matrices,access,props=decode(native)
    filter=build['case']['placement']['filters'][0];scores={}
    for i in range(3):
        for name,expected in [('authored',[True,1]),('clear',[False,0]),('cache',[True,0])]:
            row=props[i*3+('authored','clear','cache').index(name)]
            assert row[:3]==[f'{i}-{name}',str(expected[0]).lower(),str(expected[1])]
            if name=='authored':assert list(map(float,row[3:]))==[filter['blurX'],filter['blurY'],filter['passes']]
        scores[f'{i}-cache-vs-clear']=comparison(images[f'{i}-cache'],images[f'{i}-clear'])
        channels=[]
        for channel in range(4):
            image=[[images[f'{i}-cache'][y*600+x][channel] for x in range(600)] for y in range(400)]
            blurred=render(image,filter['blurX'],filter['blurY'],filter['passes'],'grouped')
            channels.append([v for row in blurred for v in row])
        candidate=[list(v) for v in zip(*channels)]
        scores[f'{i}-blur-cache-vs-authored']=comparison(candidate,images[f'{i}-authored'])
    pinned=[]
    for tick in build['case']['samples']:
        path=ROOT/'evidence/importer-loud-fail/r21/components'/Path(build['source']).stem/f"{build['case']['id']}-{tick:03d}.native.png"
        target=list(Image.open(path).convert('RGBA').getdata())
        actual=[[r+96*(256-a)//256,g+96*(256-a)//256,b+96*(256-a)//256,255] for r,g,b,a in images['1-authored']]
        pinned.append({'tick':tick,'reference':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),**comparison(actual,target)})
    if output:
        output.mkdir(parents=True,exist_ok=True)
        for name,pixels in images.items():Image.frombytes('RGBA',(600,400),bytes(c for p in pixels for c in p)).save(output/f'{name}.png')
    return {'matrices_and_local_bounds':matrices,'shape_access':access,'properties':props,'comparisons':scores,'pinned_comparisons':pinned,'source_derived_input_verified':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=analyze(a.native,a.output);(a.output/'analysis.json').write_text(json.dumps(r,separators=(',',':'))+'\n')
    print('shape access',r['shape_access'])
    for name,v in r['comparisons'].items():print(name,v['exact'],v['samples'],v['max_channel_delta'])
    print('pinned',[(v['exact'],v['samples']) for v in r['pinned_comparisons']])
