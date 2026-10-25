"""Require original animation clocks while measuring authored/clear/cache boundaries."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
from PIL import Image
from tools.probes.analyze_jiraiya_filter_boundary import ROOT,comparison
from tools.probes.run_nested_filters import unpack


def decode(native):
    build=json.loads((native/'build.json').read_text())
    assert build['source'] == 'game/fighter/fz/jinye.swf'
    assert build['case']['placement']['ratio'] == 40 and build['case']['placement']['cache_as_bitmap'] is True
    assert not build['case']['placement'].get('filters')
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
    samples=build['case']['samples'];assert len(images)==len(samples)*4 and all(len(v)==240000 for v in images.values())
    assert [int(v[0]) for v in matrices]==samples
    pinned=ROOT/'evidence/importer-loud-fail/r21/components'/'jinye'/'clocks.json'
    expected=[v for v in json.loads(pinned.read_text()) if v['path'].startswith(build['case']['id']) and v['tick']<=max(samples)]
    assert clocks==expected,'Animation clock drift'
    for i,tick in enumerate(samples):
        frame=next(v['frame'] for v in clocks if v['tick']==tick and v['path']==build['case']['id']+'/'+str(build['case']['placement']['depth']))
        for j,(name,cache,count) in enumerate((('authored','true','0'),('stage','true','0'),('clear','false','0'),('cache','true','0'))):
            v=props[i*4+j];assert v[:4]==[str(tick)+'-'+name,str(frame),cache,count]
            assert len(v)==4
        assert restores[i]==[str(tick),str(frame),str(frame),'true','0']
    assert len(props)==len(samples)*4 and len(restores)==len(samples)
    return build,images,matrices,clocks,props,restores


def analyze(native):
    build,images,matrices,clocks,props,restores=decode(native);rows=[]
    for tick in build['case']['samples']:
        authored=images[f'{tick}-authored'];cache=images[f'{tick}-cache'];clear=images[f'{tick}-clear']
        composed=[[r+96*(256-a)//256,g+96*(256-a)//256,b+96*(256-a)//256,255] for r,g,b,a in authored]
        path=ROOT/f"evidence/importer-loud-fail/r21/components/jinye/{build['case']['id']}-{tick:03d}.native.png"
        rows.append({'tick':tick,'cache_vs_clear':comparison(cache,clear),'cache_vs_authored':comparison(cache,authored),'nonzero_cache_pixels':sum(any(p) for p in cache),'normal_composite_vs_stage':comparison(composed,images[f'{tick}-stage']),'pinned':{'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),**comparison(images[f'{tick}-stage'],list(Image.open(path).convert('RGBA').getdata()))}})
    return {'case':build['case'],'rows':rows,'matrix_readbacks':matrices,'cache_property_readbacks':props,'clocks_exact':len(clocks),'restores':restores,'production_admitted':False,'source_sampler_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=analyze(a.native);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n')
    for row in r['rows']:print(row['tick'],row['nonzero_cache_pixels'],[(k,row[k]['exact'],row[k]['samples'],row[k]['max_channel_delta']) for k in ('cache_vs_clear','cache_vs_authored','pinned')])
