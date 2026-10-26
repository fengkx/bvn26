"""Measure visible-raster dependence on independently extended left bounds."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
from tools.probes.analyze_bitmap_cache_width import ROOT


def analyze(native):
    build=json.loads((native/'build.json').read_text())
    assert hashlib.sha256((ROOT/build['source']).read_bytes()).hexdigest()==build['source_sha256']
    p=native/'native.log';text=p.read_text() if p.exists() else gzip.decompress(p.with_suffix('.log.gz').read_bytes()).decode()
    rows=[s.split('|') for s in text.splitlines() if s.startswith('AIREF|')]
    assert len(rows)==729 and rows[-1][6:]==['done','ok']
    cases=[];inputs=0
    for i,r in enumerate(rows):
        assert r[1]==build['run_id'] and r[2:6]==[str(i),'0','0','0']
        kind,value=r[6:]
        if kind=='source':
            label,width,y,*values=value.split(',')
            assert label=='shared' and width=='16' and int(y)==inputs//16 and len(values)==16
            for x,v in enumerate(values):
                assert int(v)&0xffffffff==0xff000000+x%2*255*65536+((x*37+17)%256)*256+113
                inputs+=1
        elif kind=='case':
            key=list(map(float,value.split(',')));assert len(key)==10 and key[0]==len(cases)
            assert key[8]==key[1]*key[6]+key[7] and key[9]==16*key[6]+key[7]
            cases.append({'key':key})
        elif kind=='cache':assert value in ('0,false','1,true')
        elif kind in ('clear','cached'):
            values=[int(v)&0xffffffff for v in value.split(',')];assert len(values)==512 and kind not in cases[-1]
            cases[-1][kind]=values
        else:assert kind=='done'
    assert len(cases)==144 and inputs==128
    base={tuple(c['key'][2:6]):c for c in cases if c['key'][1]==0}
    comparisons=[]
    for c in cases:
        i,minimum,mode,scale,inner,outer,*_=c['key'];reference=base[tuple(c['key'][2:6])]
        effective=round(inner*4)/4+math.trunc(outer*4)/4
        positions=[x for x in range(512) if effective+scale<=x and x+1<=effective+15*scale]
        for kind in ('clear','cached'):
            failed=[{'x':x,'actual_argb':c[kind][x],'baseline_argb':reference[kind][x]} for x in positions if c[kind][x]!=reference[kind][x]]
            comparisons.append({'case':int(i),'kind':kind,'mode':int(mode),'samples':len(positions),'exact':len(positions)-len(failed),'failures':failed})
    return {'input_exact':inputs,'cases':cases,'comparisons':comparisons,'candidate_admitted':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=analyze(a.native);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n')
    for mode in (0,1):
        for kind in ('clear','cached'):
            rows=[v for v in r['comparisons'] if v['mode']==mode and v['kind']==kind]
            print(mode,kind,sum(v['exact'] for v in rows),sum(v['samples'] for v in rows),sum(bool(v['failures']) for v in rows))
