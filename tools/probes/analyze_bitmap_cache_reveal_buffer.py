"""Measure filtered alpha support with identity-filter controls and original readbacks."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
from tools.probes.analyze_bitmap_cache_width import ROOT
from tools.probes.analyze_cache_device_origin import device_translation, raster_sample

IDENTITY=[1,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,0,0,1,0]
REVEAL=[0,0,0,0,37,0,0,0,0,73,0,0,0,0,113,0,0,0,0,255]


def analyze(native):
    build=json.loads((native/'build.json').read_text());assert hashlib.sha256((ROOT/build['source']).read_bytes()).hexdigest()==build['source_sha256']
    p=native/'native.log';text=p.read_text() if p.exists() else gzip.decompress(p.with_suffix('.log.gz').read_bytes()).decode()
    rows=[s.split('|') for s in text.splitlines() if s.startswith('AIREF|')]
    assert len(rows)==433 and rows[-1][6:]==['done','ok']
    cases=[];inputs=0
    for i,r in enumerate(rows):
        assert r[1]==build['run_id'] and r[2:6]==[str(i),'0','0','0']
        kind,value=r[6:]
        if kind=='source':
            y,*values=map(int,value.split(','));assert y==inputs//60 and len(values)==60
            for x,v in enumerate(values):
                assert v&0xffffffff==0xff000000+x%2*255*65536+((x*37+17)%256)*256+113;inputs+=1
        elif kind=='case':
            fields=value.split(',');assert len(fields)==10 and fields[8]=='true'
            key=list(map(float,fields[:8]));assert key[0]==len(cases) and int(fields[9])==int(key[3]>0)
            cases.append({'key':key,'pixels':[]})
        elif kind=='matrix':
            values=list(map(float,value.split(',')));assert values==(IDENTITY if cases[-1]['key'][3]==1 else REVEAL)
            cases[-1]['matrix']=values
        elif kind=='row':
            y,*values=map(int,value.split(','));assert y==len(cases[-1]['pixels'])//800 and len(values)==800
            cases[-1]['pixels'] += [v&0xffffffff for v in values]
        else:assert kind=='done'
    assert inputs==480 and len(cases)==24 and all(len(c['pixels'])==12800 for c in cases)
    comparisons=[];rectangles=[]
    for plain,identity,reveal in zip(cases[::3],cases[1::3],cases[2::3]):
        assert plain['key'][1:3]==identity['key'][1:3]==reveal['key'][1:3]
        failed=[{'x':i%800,'y':i//800,'plain_argb':a,'identity_argb':b} for i,(a,b) in enumerate(zip(plain['pixels'],identity['pixels'])) if a!=b]
        comparisons.append({'case':int(plain['key'][0]),'samples':12800,'exact':12800-len(failed),'failures':failed})
        points=[(i%800,i//800) for i,v in enumerate(reveal['pixels']) if v>>24]
        left,top=min(x for x,y in points),min(y for x,y in points)
        right,bottom=max(x for x,y in points)+1,max(y for x,y in points)+1
        assert len(points)==(right-left)*(bottom-top)
        assert all(v==0 or v>>24==255 for v in reveal['pixels'])
        rectangles.append({'case':int(reveal['key'][0]),'minimum':plain['key'][1],'inner':plain['key'][2],'rectangle':[left,top,right,bottom],
                           'argb_counts':{hex(v):n for v,n in sorted(Counter(reveal['pixels']).items())}})
    measured_origin_checks=[]
    for rect,c in zip(rectangles,cases[::3]):
        inner=rect['inner'];origin=rect['rectangle'][0]
        translation=device_translation(7,inner,128,origin)
        positions=[x for x in range(800) if 128+inner+21<=x and x+1<=128+inner+385]
        failures=[]
        for x in positions:
            value=c['pixels'][7*800+x];target=[(value>>shift)&255 for shift in (16,8,0)]
            predicted=raster_sample(7,translation,x-origin,0,60)
            if predicted!=target:failures.append({'x':x,'predicted':predicted,'native':target})
        measured_origin_checks.append({'case':int(c['key'][0]),'measured_origin':origin,'samples':len(positions),'exact':len(positions)-len(failures),'failures':failures})
    return {'measured_origin_checks':measured_origin_checks,'input_exact':inputs,'cases':cases,'identity_comparisons':comparisons,'revealed_rectangles':rectangles,
            'cache_only_allocation_equivalence_proven':False,'candidate_admitted':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=analyze(a.native);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n')
    print('identity',sum(v['exact'] for v in r['identity_comparisons']),102400)
    for v in r['revealed_rectangles']:print(v['minimum'],v['inner'],v['rectangle'])
