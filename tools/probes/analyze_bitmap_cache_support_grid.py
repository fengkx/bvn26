"""Compare globally fixed geometry constructions with independently revealed alpha support."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT=Path(__file__).resolve().parents[2]


def f32(value):
    return struct.unpack('<f',struct.pack('<f',value))[0]


def predict(minimum,width,scale,inner,source_padding,device_padding):
    coefficient=f32(f32(4*f32(.05))*f32(scale))
    translation=round(inner*4)+512
    left=round(f32((minimum*20-source_padding)*coefficient))+translation-device_padding
    right=round(f32(((minimum+width)*20+source_padding)*coefficient))+translation+device_padding
    return [math.floor(left/4),math.floor(right/4)+1]


def separate_bounds(minimum,width,scale,inner,outer=128):
    coefficient=f32(f32(4*f32(.05))*f32(scale))
    left=round(f32(minimum*20*coefficient))
    right=round(f32((minimum+width)*20*coefficient))
    translation=math.floor((round(inner*4)+math.trunc(outer*4))/4)
    return [math.floor(left/4)+translation,math.ceil(right/4)+translation+1]


def analyze(native):
    build=json.loads((native/'build.json').read_text())
    assert hashlib.sha256((ROOT/build['source']).read_bytes()).hexdigest()==build['source_sha256']
    path=native/'native.log'
    text=path.read_text() if path.exists() else gzip.decompress(path.with_suffix('.log.gz').read_bytes()).decode()
    events=[line.split('|') for line in text.splitlines() if line.startswith('AIREF|')]
    assert len(events)==5193 and events[-1][6:]==['done','ok']
    cases=[];inputs=0
    for i,event in enumerate(events):
        assert event[1]==build['run_id'] and event[2:6]==[str(i),'0','0','0']
        kind,value=event[6:]
        if kind=='source':
            y,*values=map(int,value.split(','));assert y==inputs//60 and len(values)==60
            for x,v in enumerate(values):
                assert v&0xffffffff==0xff000000+x%2*255*65536+((x*37+17)%256)*256+113
                inputs+=1
        elif kind=='case':
            fields=value.split(',');assert len(fields)==10 and fields[8:]==['true','1']
            key=list(map(float,fields[:8]));assert key[0]==len(cases)
            cases.append({'key':key})
        elif kind=='matrix':
            values=list(map(float,value.split(',')))
            assert values==[0]*19+[cases[-1]['key'][5]]
            cases[-1]['matrix']=values
        elif kind=='row':
            values=[int(v)&0xffffffff for v in value.split(',')];assert len(values)==800
            points=[x for x,v in enumerate(values) if v>>24]
            assert points and points==list(range(points[0],points[-1]+1))
            assert all(v in (0,int(cases[-1]['key'][5])<<24) for v in values)
            cases[-1].update(row=values,support=[points[0],points[-1]+1])
        elif kind=='column':
            x,*values=map(int,value.split(','));values=[v&0xffffffff for v in values]
            assert len(values)==16 and x==cases[-1]['support'][0]
            assert [y for y,v in enumerate(values) if v>>24]==list(range(4,13))
            cases[-1]['column']=values
        else:assert kind=='done'
    assert inputs==480 and len(cases)==1296
    assert all(a['support']==b['support'] for a,b in zip(cases[::2],cases[1::2]))
    models={}
    for name,source_pad,device_pad in [('unexpanded',0,0),('source_one_twip',1,0),('device_one_subpixel',0,1),('separate_geometry_translation',0,0)]:
        failures=[]
        for c in cases:
            _,minimum,width,scale,inner,alpha,bmin,bmax=c['key']
            predicted=(separate_bounds(minimum,width,scale,inner) if name=='separate_geometry_translation'
                       else predict(minimum,width,scale,inner,source_pad,device_pad))
            if predicted!=c['support']:
                failures.append({'case':int(c['key'][0]),'key':c['key'][1:6],'predicted':predicted,'native':c['support']})
        models[name]={'samples':len(cases),'exact':len(cases)-len(failures),'failures':failures}
    return {'source_exact':inputs,'alpha_independent_groups':648,'cases':cases,'models':models,
            'measured_scope':'row y7 and first occupied column only','candidate_admitted':False,'production_admitted':False}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();result=analyze(args.native)
    args.output.write_text(json.dumps(result,separators=(',',':'))+'\n')
    print({name:(m['exact'],m['samples']) for name,m in result['models'].items()})
