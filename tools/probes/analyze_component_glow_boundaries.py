"""Constrain original Glow input/composition using full native properties and retained byte math."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image
from tools.probes.analyze_component_cache_boundaries import decode
from tools.probes.analyze_jiraiya_filter_boundary import ROOT,comparison
from tools.probes.analyze_blur_kernel_heldout import render
from tools.probes.analyze_shadow_gain_paths import shadow_bytes


def glow(pixels,filter):
    assert filter['type']=='GLOWFILTER' and not filter.get('inner',False) and not filter.get('knockout',False)
    image=[[pixels[y*600+x][3] for x in range(600)] for y in range(400)]
    blurred=render(image,filter['blurX'],filter['blurY'],filter['passes'],'grouped')
    color=tuple(round(v*255) for v in filter['color'][:3]);alpha_byte=int(filter['color'][3]*255)
    table=[shadow_bytes(value,alpha_byte,filter['strength'],'premultiplied_color',color) for value in range(256)]
    return [[c+s*(256-p[3])//256 for c,s in zip(p,table[blurred[i//600][i%600]])] for i,p in enumerate(pixels)]


def analyze(native,output=None):
    build,images,matrices,access,props=decode(native);f=build['case']['placement']['filters'][0]
    assert f['type']=='GLOWFILTER';color=sum(round(v*255)<<shift for v,shift in zip(f['color'][:3],(16,8,0)))
    expected=[f['blurX'],f['blurY'],f['passes'],color,f['color'][3],f['strength']]
    scores={};pinned=[]
    for i in range(3):
        for j,(kind,cached,count) in enumerate((('authored',True,1),('clear',False,0),('cache',True,0))):
            row=props[i*3+j];assert row[:3]==[f'{i}-{kind}',str(cached).lower(),str(count)]
            if kind=='authored':assert list(map(float,row[3:9]))==expected and row[9:]==['false','false']
            else:assert len(row)==3
        scores[f'{i}-cache-vs-clear']=comparison(images[f'{i}-cache'],images[f'{i}-clear'])
        candidate=glow(images[f'{i}-cache'],f)
        scores[f'{i}-glow-cache-vs-authored']=comparison(candidate,images[f'{i}-authored'])
    actual=[[r+96*(256-a)//256,g+96*(256-a)//256,b+96*(256-a)//256,255] for r,g,b,a in images['1-authored']]
    for tick in build['case']['samples']:
        path=ROOT/'evidence/importer-loud-fail/r21/components'/Path(build['source']).stem/f"{build['case']['id']}-{tick:03d}.native.png"
        pinned.append({'tick':tick,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),**comparison(actual,list(Image.open(path).convert('RGBA').getdata()))})
    if output:
        output.mkdir(parents=True,exist_ok=True)
        for name,pixels in images.items():Image.frombytes('RGBA',(600,400),bytes(v for p in pixels for v in p)).save(output/f'{name}.png')
    return {'properties':props,'matrices_and_local_bounds':matrices,'shape_access':access,'comparisons':scores,'pinned_comparisons':pinned,'source_derived_input_verified':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=analyze(a.native,a.output);(a.output/'analysis.json').write_text(json.dumps(r,separators=(',',':'))+'\n')
    for name,v in r['comparisons'].items():print(name,v['exact'],v['samples'],v['max_channel_delta'])
    print('pinned',[(v['exact'],v['samples']) for v in r['pinned_comparisons']])
