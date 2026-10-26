"""Hold the r116 support rule fixed on fractional geometry and cache-only inputs."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
from tools.probes.analyze_bitmap_cache_support_grid import ROOT,separate_bounds
from tools.probes.analyze_cache_device_origin import device_translation,raster_sample


def analyze(native):
    build=json.loads((native/'build.json').read_text())
    assert hashlib.sha256((ROOT/build['source']).read_bytes()).hexdigest()==build['source_sha256']
    path=native/'native.log'
    text=path.read_text() if path.exists() else gzip.decompress(path.with_suffix('.log.gz').read_bytes()).decode()
    events=[line.split('|') for line in text.splitlines() if line.startswith('AIREF|')]
    assert len(events)==3369 and events[-1][6:]==['done','ok']
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
            fields=value.split(',');assert len(fields)==11 and fields[9]=='true'
            key=list(map(float,fields[:9]));assert key[0]==len(cases) and int(fields[10])==key[6]
            cases.append({'key':key})
        elif kind=='matrix':
            values=list(map(float,value.split(',')));assert values==[0]*19+[255]
            cases[-1]['matrix']=values
        elif kind=='row':
            values=[int(v)&0xffffffff for v in value.split(',')];assert len(values)==800
            points=[x for x,v in enumerate(values) if v>>24]
            assert points
            if cases[-1]['key'][6]:
                assert points==list(range(points[0],points[-1]+1)) and all(v in (0,0xff000000) for v in values)
            cases[-1].update(row=values,support=[points[0],points[-1]+1])
        elif kind=='column':
            x,*values=map(int,value.split(','));values=[v&0xffffffff for v in values]
            assert len(values)==16 and x==cases[-1]['support'][0]
            cases[-1]['column']=values
        else:assert kind=='done'
    assert inputs==480 and len(cases)==960
    bounds=[];pixels=[]
    for plain,reveal in zip(cases[::2],cases[1::2]):
        assert plain['key'][1:6]==reveal['key'][1:6]
        _,minimum,width,scale,inner,outer,state,bmin,bmax=plain['key']
        predicted=separate_bounds(minimum,width,scale,inner,outer)
        bounds.append({'case':int(reveal['key'][0]),'predicted':predicted,'native':reveal['support'],'exact':predicted==reveal['support']})
        origin=predicted[0];translation=device_translation(scale,inner,outer,origin)
        failures=[];samples=0
        for x in range(800):
            # Exclude shape and source boundaries independently of output RGB.
            if not (outer+inner+max(minimum+2,2)*scale<=x and x+1<=outer+inner+min(minimum+width-2,58)*scale):continue
            samples+=1;v=plain['row'][x];target=[(v>>shift)&255 for shift in (16,8,0)]
            value=raster_sample(scale,translation,x-origin,0,60)
            if value!=target:failures.append({'x':x,'predicted':value,'native':target})
        pixels.append({'case':int(plain['key'][0]),'samples':samples,'exact':samples-len(failures),'failures':failures})
    return {'input_exact':inputs,'cases':cases,'bounds':bounds,'cache_interior':pixels,
            'source_cache_initializer_admitted':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=analyze(a.native);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n')
    print('bounds',sum(v['exact'] for v in r['bounds']),len(r['bounds']))
    print('cache',sum(v['exact'] for v in r['cache_interior']),sum(v['samples'] for v in r['cache_interior']))
