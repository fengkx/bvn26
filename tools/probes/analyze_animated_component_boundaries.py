"""Require original animation clocks while measuring authored/clear/cache boundaries."""
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
    images={};matrices=[];clocks=[];props=[];restores=[]
    assert events[-1][6:]==['done','ok']
    for i,row in enumerate(events):
        assert row[1]==build['run_id'] and row[2:4]==[str(i),'0'] and row[5]=='0';tick=int(row[4]);kind,value=row[6:]
        if kind=='clock':
            name,frame=value.split(',');clocks.append({'frame':int(frame),'path':name,'tick':tick})
        elif kind=='matrix':
            v=list(map(float,value.split(',')));assert v[0]==tick and len(v)==13;matrices.append(v)
        elif kind=='props':props.append(value.split(','))
        elif kind=='restore':restores.append(value.split(','))
        elif kind=='row':
            label,y,values=value.split(',',2);assert label.startswith(str(tick)+'-');pixels=images.setdefault(label,[]);assert len(pixels)==int(y)*600
            v=list(map(int,values.split(',')));assert len(v)==1200;pixels.extend(unpack(v))
        else:assert kind=='done'
    samples=build['case']['samples'];assert len(images)==len(samples)*3 and all(len(v)==240000 for v in images.values())
    assert [int(v[0]) for v in matrices]==samples
    pinned=ROOT/'evidence/importer-loud-fail/r21/components'/Path(build['source']).stem/'clocks.json'
    expected=[v for v in json.loads(pinned.read_text()) if v['path'].startswith(build['case']['id']) and v['tick']<=max(samples)]
    assert clocks==expected,'Animation clock drift'
    for i,tick in enumerate(samples):
        frame=next(v['frame'] for v in clocks if v['tick']==tick and v['path']==build['case']['id']+'/'+str(build['case']['placement']['depth']))
        for j,(name,cache,count) in enumerate((('authored','true','1'),('clear','false','0'),('cache','true','0'))):
            v=props[i*3+j];assert v[:4]==[str(tick)+'-'+name,str(frame),cache,count]
            if name=='authored':assert list(map(float,v[4:]))==[build['case']['placement']['filters'][0][k] for k in ('blurX','blurY','passes')]
            else:assert len(v)==4
        assert restores[i]==[str(tick),str(frame),str(frame),'true','1']
    assert len(props)==len(samples)*3 and len(restores)==len(samples)
    return build,images,matrices,clocks,props,restores


def analyze(native,output=None):
    build,images,matrices,clocks,props,restores=decode(native);f=build['case']['placement']['filters'][0];rows=[]
    for tick in build['case']['samples']:
        cache=images[f'{tick}-cache'];channels=[]
        for channel in range(4):
            image=[[cache[y*600+x][channel] for x in range(600)] for y in range(400)]
            blurred=render(image,f['blurX'],f['blurY'],f['passes'],'grouped');channels.append([v for row in blurred for v in row])
        candidate=[list(v) for v in zip(*channels)]
        composed=[[r+96*(256-a)//256,g+96*(256-a)//256,b+96*(256-a)//256,255] for r,g,b,a in images[f'{tick}-authored']]
        path=ROOT/f"evidence/importer-loud-fail/r21/components/{Path(build['source']).stem}/{build['case']['id']}-{tick:03d}.native.png"
        rows.append({'tick':tick,'cache_vs_clear':comparison(cache,images[f'{tick}-clear']),'cache_to_authored':comparison(candidate,images[f'{tick}-authored']),'pinned':{'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),**comparison(composed,list(Image.open(path).convert('RGBA').getdata()))}})
    if output:
        output.mkdir(parents=True,exist_ok=True)
        for name,pixels in images.items():Image.frombytes('RGBA',(600,400),bytes(c for p in pixels for c in p)).save(output/f'{name}.png')
    return {'rows':rows,'clocks':clocks,'matrices':matrices,'properties':props,'restores':restores,'source_derived_input_verified':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=analyze(a.native,a.output);(a.output/'analysis.json').write_text(json.dumps(r,separators=(',',':'))+'\n')
    for v in r['rows']:print(v['tick'],v['cache_vs_clear']['exact'],v['cache_to_authored']['exact'],v['pinned']['exact'])
