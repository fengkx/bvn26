"""Discriminate fill translation from independently held cache geometry."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
from tools.probes.analyze_cache_device_origin import device_translation, raster_sample, ROOT


def analyze(native):
    build=json.loads((native/'build.json').read_text())
    assert hashlib.sha256((ROOT/build['source']).read_bytes()).hexdigest()==build['source_sha256']
    p=native/'native.log';text=p.read_text() if p.exists() else gzip.decompress(p.with_suffix('.log.gz').read_bytes()).decode()
    rows=[s.split('|') for s in text.splitlines() if s.startswith('AIREF|')]
    assert len(rows)==1269 and rows[-1][6:]==['done','ok']
    cases=[];inputs=0
    for i,r in enumerate(rows):
        assert r[1]==build['run_id'] and r[2:6]==[str(i),'0','0','0']
        kind,value=r[6:]
        if kind=='source':
            y,*values=map(int,value.split(','));assert y==inputs//60 and len(values)==60
            for x,v in enumerate(values):
                assert v&0xffffffff==0xff000000+x%2*255*65536+((x*37+17)%256)*256+113;inputs+=1
        elif kind=='case':
            key=list(map(float,value.split(',')));assert len(key)==13 and key[0]==len(cases)
            _,mode,value,minimum,maximum,fill,fa,ft,scale,inner,outer,bmin,bmax=key
            assert fa==1 and ft==fill and fill==(0 if mode==2 else value)
            assert minimum==(-4 if mode==0 else value) and maximum==(64 if mode==0 else value+60)
            projected=[float(format(math.floor(x*20*scale+0.5)/20+inner,'.15g')) for x in (minimum,maximum)]
            assert [bmin,bmax]==projected
            cases.append({'key':key})
        elif kind=='cache':assert value in ('0,false','1,true')
        elif kind in ('clear','cached'):
            values=list(map(int,value.split(',')));assert len(values)==800 and kind not in cases[-1]
            cases[-1][kind]=[[(v>>s)&255 for s in (16,8,0)] for v in values]
        else:assert kind=='done'
    assert inputs==480 and len(cases)==252
    comparisons=[]
    for c in cases:
        i,mode,value,minimum,maximum,fill,_,_,scale,inner,outer,bmin,_=c['key']
        effective=round(inner*4)/4+math.trunc(outer*4)/4
        origin=math.floor(bmin-inner+effective)
        positions=[x for x in range(800) if effective+3*scale<=x and x+1<=effective+55*scale]
        for kind in ('clear','cached'):
            translation=effective if kind=='clear' else device_translation(scale,inner,outer,origin)
            failures=[]
            for x in positions:
                predicted=raster_sample(scale,translation,x if kind=='clear' else x-origin,fill,60)
                if predicted!=c[kind][x]:failures.append({'x':x,'predicted':predicted,'native':c[kind][x]})
            comparisons.append({'case':int(i),'mode':int(mode),'kind':kind,'samples':len(positions),'exact':len(positions)-len(failures),
                                'max_channel_delta':max((abs(a-b) for f in failures for a,b in zip(f['predicted'],f['native'])),default=0),'failures':failures})
    return {'input_exact':inputs,'cases':cases,'comparisons':comparisons,'candidate_admitted':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=analyze(a.native);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n')
    for mode in range(3):
        for kind in ('clear','cached'):
            rows=[v for v in r['comparisons'] if v['mode']==mode and v['kind']==kind]
            print(mode,kind,sum(v['exact'] for v in rows),sum(v['samples'] for v in rows),max(v['max_channel_delta'] for v in rows))
