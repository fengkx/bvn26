"""Measure aligned integer-translation controls before choosing an implicit buffer origin."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
from PIL import Image
from tools.probes.analyze_jiraiya_filter_boundary import ROOT,decode as reference,comparison
from tools.probes.analyze_jiraiya_bitmap_binding import decode as leaf_reference
from tools.probes.run_nested_filters import unpack
from tools.probes.bound_bitmap_candidate import render_leaf

SHIFTS=(-128,-17,-1,0,1,17,128)


def decode(native):
    b=json.loads((native/'build.json').read_text())
    for p,h in [(b['source'],b['source_sha256']),(b['harness_source'],b['harness_sha256'])]:assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h
    p=native/'native.log';text=p.read_text() if p.exists() else gzip.decompress(p.with_suffix('.log.gz').read_bytes()).decode()
    rows=[s.split('|') for s in text.splitlines() if s.startswith('AIREF|')]
    assert len(rows)==5608 and rows[-1][6:]==['done','ok'];props=[];images={}
    for i,row in enumerate(rows):
        assert row[1]==b['run_id'] and row[2:6]==[str(i),'0','0','0']
        if row[6]=='props':
            values=list(map(float,row[7].split(',')));assert values[0]==len(props) and values[1]==SHIFTS[len(props)] and values[-3:]==[15,0,3];props.append(values)
        elif row[6]=='row':
            label,y,values=row[7].split(',',2);pixels=images.setdefault(label,[]);assert len(pixels)==int(y)*600
            v=list(map(int,values.split(',')));assert len(v)==1200;pixels.extend(unpack(v))
        else:assert row[6]=='done'
    assert len(images)==14 and all(len(v)==240000 for v in images.values())
    return images,props


def shifted(pixels,offset):
    output=[[0]*4 for _ in range(240000)]
    for y in range(400):
        for x in range(max(0,offset),min(600,600+offset)):
            output[y*600+x]=pixels[y*600+x-offset]
    return output


def analyze(native,output):
    images,props=decode(native);refs,_,_=reference(ROOT/'evidence/importer-loud-fail/r93/native')
    leaf,_=leaf_reference(ROOT/'evidence/importer-loud-fail/r89/native');scores={};output.mkdir(parents=True,exist_ok=True)
    for i,offset in enumerate(SHIFTS):
        for kind,ref in [('authored','authored'),('input','cleared')]:
            pixels=images[f'{i}-{kind}'];scores[f'{offset}-{kind}-aligned']=comparison(pixels,shifted(refs[ref]['rgba'],offset))
            Image.frombytes('RGBA',(600,400),bytes(c for p in pixels for c in p)).save(output/f'{i}-{kind}.png')
        _,_,sx,sy,tx,ty,inner_sx,inner_sy,inner_tx,inner_ty,*_=props[i]
        effective={'sx':sx*inner_sx,'sy':sy*inner_sy,'tx':round(inner_tx*sx*4)/4+math.trunc(tx*4)/4,'ty':round(inner_ty*sy*4)/4+math.trunc(ty*4)/4}
        candidate=render_leaf(leaf,effective,(600,400));scores[f'{offset}-input-model']=comparison(candidate,images[f'{i}-input'])
    return {'properties':props,'comparisons':scores,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=analyze(a.native,a.output);(a.output/'analysis.json').write_text(json.dumps(r,separators=(',',':'))+'\n');print({k:(v['exact'],v['samples'],v['max_channel_delta']) for k,v in r['comparisons'].items()})
