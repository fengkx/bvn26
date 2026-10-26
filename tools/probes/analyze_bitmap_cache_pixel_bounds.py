"""Check whether public pixel bounds identify the failing cache raster origin."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
from tools.probes.analyze_bitmap_cache_width import ROOT


def analyze(native):
    build=json.loads((native/'build.json').read_text());assert hashlib.sha256((ROOT/build['source']).read_bytes()).hexdigest()==build['source_sha256']
    p=native/'native.log';text=p.read_text() if p.exists() else gzip.decompress(p.with_suffix('.log.gz').read_bytes()).decode()
    rows=[s.split('|') for s in text.splitlines() if s.startswith('AIREF|')]
    assert len(rows)==153 and rows[-1][6:]==['done','ok']
    cases=[];inputs=0
    for i,r in enumerate(rows):
        assert r[1]==build['run_id'] and r[2:6]==[str(i),'0','0','0']
        kind,value=r[6:]
        if kind=='source':
            y,*values=map(int,value.split(','));assert y==inputs//60 and len(values)==60
            for x,v in enumerate(values):
                assert v&0xffffffff==0xff000000+x%2*255*65536+((x*37+17)%256)*256+113;inputs+=1
        elif kind=='case':
            key=list(map(float,value.split(',')));assert len(key)==10 and key[0]==len(cases)
            cases.append({'key':key,'bounds':[]})
        elif kind=='cache':assert value in ('0,false','1,true')
        elif kind in ('before','after'):
            fields=value.split(',');assert fields[0]=='object' and len(fields)==5
            cases[-1]['bounds'].append({'phase':kind,'rectangle':list(map(float,fields[1:]))})
        elif kind in ('clear','cached'):
            values=list(map(int,value.split(',')));assert len(values)==800 and kind not in cases[-1]
            cases[-1][kind]=values
        else:assert kind=='done'
    assert inputs==480 and len(cases)==16
    invariant=0;comparisons=[]
    for c in cases:
        assert len(c['bounds'])==4
        ref=c['bounds'][0]['rectangle']
        assert ref==[math.trunc(c['key'][8]),4*c['key'][3],math.trunc(c['key'][9]-c['key'][8]),8]
        for b in c['bounds']:
            invariant+=b['rectangle']==ref
        if c['key'][3]==1:
            prior=cases[int(c['key'][0])-1];assert prior['key'][1:3]==c['key'][1:3] and prior['key'][3]==0
            local=prior['bounds'][0]['rectangle']
            comparisons.append({'case':int(c['key'][0]),'kind':'bounds_translation','samples':1,'exact':int(ref==[local[0]+128,local[1]+4,*local[2:]]),'local':local,'root':ref})
            for kind in ('clear','cached'):
                failed=[{'x':x,'parent_rgb':a,'root_rgb':b} for x,(a,b) in enumerate(zip(prior[kind],c[kind])) if a!=b]
                comparisons.append({'case':int(c['key'][0]),'kind':kind,'samples':800,'exact':800-len(failed),'failures':failed})
    return {'input_exact':inputs,'cases':cases,'public_bounds_invariant':invariant,'comparisons':comparisons,
            'hidden_cache_allocation_verified':False,'candidate_admitted':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=analyze(a.native);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n')
    print('bounds',r['public_bounds_invariant'],64)
    for kind in ('clear','cached'):
        rows=[v for v in r['comparisons'] if v['kind']==kind];print(kind,sum(v['exact'] for v in rows),sum(v['samples'] for v in rows))
