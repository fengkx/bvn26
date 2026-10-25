"""Measure cache-only and zero-blur images; properties alone do not prove materialization."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
from PIL import Image
from tools.probes.analyze_jiraiya_filter_boundary import ROOT,comparison
from tools.probes.analyze_jiraiya_materialized_blur import integer_blur
from tools.probes.analyze_jiraiya_buffer_origin import shifted
from tools.probes.run_nested_filters import unpack

KINDS=('authored','clear','cache','zero','restored')
SHIFTS=(-128,0,128)


def decode(native):
    b=json.loads((native/'build.json').read_text())
    for p,h in [(b['source'],b['source_sha256']),(b['harness_source'],b['harness_sha256'])]:assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h
    p=native/'native.log';text=p.read_text() if p.exists() else gzip.decompress(p.with_suffix('.log.gz').read_bytes()).decode()
    rows=[s.split('|') for s in text.splitlines() if s.startswith('AIREF|')]
    assert len(rows)==6019 and rows[-1][6:]==['done','ok'];images={};bounds=[];props=[]
    for i,row in enumerate(rows):
        assert row[1]==b['run_id'] and row[2:6]==[str(i),'0','0','0']
        if row[6]=='bounds':
            values=list(map(float,row[7].split(',')));assert values[0]==len(bounds) and values[1]==SHIFTS[len(bounds)];bounds.append(values)
        elif row[6]=='props':props.append(row[7].split(','))
        elif row[6]=='row':
            label,y,values=row[7].split(',',2);pixels=images.setdefault(label,[]);assert len(pixels)==int(y)*600
            v=list(map(int,values.split(',')));assert len(v)==1200;pixels.extend(unpack(v))
        else:assert row[6]=='done'
    assert set(images)=={f'{i}-{k}' for i in range(3) for k in KINDS} and all(len(v)==240000 for v in images.values())
    assert len(props)==15
    return images,bounds,props


def analyze(native,output):
    images,bounds,props=decode(native);scores={};output.mkdir(parents=True,exist_ok=True)
    old_root=ROOT/'evidence/importer-loud-fail/r99';pins=json.loads((old_root/'provenance.json').read_text())['evidence_sha256']
    for i,offset in enumerate(SHIFTS):
        for k in KINDS:
            pixels=images[f'{i}-{k}'];Image.frombytes('RGBA',(600,400),bytes(c for p in pixels for c in p)).save(output/f'{i}-{k}.png')
        for k,oldkind in [('authored','authored'),('clear','input')]:
            name=f'images/{(0,3,6)[i]}-{oldkind}.png';assert hashlib.sha256((old_root/name).read_bytes()).hexdigest()==pins[name]
            scores[f'{offset}-{k}-pinned']=comparison(images[f'{i}-{k}'],list(Image.open(old_root/name).convert('RGBA').getdata()))
        for a,b in [('cache','clear'),('zero','cache'),('restored','authored')]:
            scores[f'{offset}-{a}-vs-{b}']=comparison(images[f'{i}-{a}'],images[f'{i}-{b}'])
        for k in ('cache','zero'):
            scores[f'{offset}-{k}-shifted']=comparison(images[f'{i}-{k}'],shifted(images[f'1-{k}'],offset))
            scores[f'{offset}-blur-{k}-vs-authored']=comparison(integer_blur(images[f'{i}-{k}']),images[f'{i}-authored'])
    return {'bounds_and_filter_rect':bounds,'properties':props,'comparisons':scores,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=analyze(a.native,a.output);(a.output/'analysis.json').write_text(json.dumps(r,separators=(',',':'))+'\n');print('bounds',r['bounds_and_filter_rect']);print({k:(v['exact'],v['samples'],v['max_channel_delta']) for k,v in r['comparisons'].items()})
