"""Separate cache placement invariance from source-coordinate initialization."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
from tools.probes.analyze_bitmap_nested_translation import ROOT,texel
from tools.probes.analyze_clipped_half_step import axis


def decode(native,count=378,width=600):
    b=json.loads((native/'build.json').read_text());assert hashlib.sha256((ROOT/b['source']).read_bytes()).hexdigest()==b['source_sha256']
    p=native/'native.log';text=p.read_text() if p.exists() else gzip.decompress(p.with_suffix('.log.gz').read_bytes()).decode()
    rows=[s.split('|') for s in text.splitlines() if s.startswith('AIREF|')]
    assert len(rows)==9+count*5 and rows[-1][6:]==['done','ok']
    for i,r in enumerate(rows):assert r[1]==b['run_id'] and r[2:6]==[str(i),'0','0','0']
    for y,r in enumerate(rows[:8]):
        v=list(map(int,r[7].split(',')));assert r[6]=='source' and v[0]==y and len(v)==61
        for x,p in enumerate(v[1:]):assert p&0xffffffff==0xff000000+(x%2)*255*65536+((x*37+17)%256)*256+113
    cases=[]
    for i in range(count):
        block=rows[8+i*5:13+i*5];assert [r[6] for r in block]==['case','cache','clear','cache','cached']
        assert block[1][7]=='0,false' and block[3][7]=='1,true'
        key=list(map(float,block[0][7].split(',')));assert len(key)==9 and key[0]==i
        images={r[6]:[[(p>>s)&255 for s in (16,8,0)] for p in map(int,r[7].split(','))] for r in (block[2],block[4])}
        assert all(len(v)==width for v in images.values());cases.append({'key':key,**images})
    return cases


def sample(scale,translation,x,minimum):
    q=axis(scale,translation,x,'even')-minimum;i=math.floor(q);f=math.floor((q-i)*256)
    a,b=texel(i),texel(i+1);return [(v*(256-f)+w*f)//256 for v,w in zip(a,b)]


def analyze(native,case_count=378,width=600,group_size=6,base_shift=4):
    cases=decode(native,case_count,width)
    placement={kind:{rule:{'samples':0,'exact':0,'exact_rows':0,'failures':[]} for rule in ('floor','even','up')} for kind in ('clear','cached')}
    models={name:{'samples':0,'exact':0,'failures':[]} for name in ('global_uncached','local_bounds_before_consumption','local_bounds_after_consumption','local_node_zero','cache_consumed_bounds','cache_authored_bounds','cache_node_plus_outer_bounds')}
    for c in cases:
        i,minimum,requested_scale,requested_tx,outer,scale,inner,bmin,bmax=c['key'];base=cases[int(i)//group_size*group_size]
        assert base['key'][4]==base_shift
        for rule,shift in [('floor',math.floor(outer)-base_shift),('even',round(outer)-base_shift),('up',math.floor(outer+.5)-base_shift)]:
            for kind in placement:
                s=placement[kind][rule];failed=False
                for x,target in enumerate(c[kind]):
                    p=base[kind][x-shift] if 0<=x-shift<width else [0,0,0]
                    s['samples']+=1
                    if p==target:s['exact']+=1
                    else:
                        failed=True;s['failures'].append({'case':int(i),'x':x,'actual':p,'native':target})
                s['exact_rows']+=not failed
        effective=round(inner*4)/4+math.trunc(outer*4)/4
        origins={'global_uncached':0,'local_bounds_before_consumption':math.floor(bmin),
                 'local_bounds_after_consumption':math.floor(minimum*scale+round(inner*4)/4),'local_node_zero':0,'cache_consumed_bounds':math.floor(minimum*scale+effective),
                 'cache_authored_bounds':math.floor(bmin+outer),'cache_node_plus_outer_bounds':math.floor(bmin)+math.floor(outer)}
        for x in range(width):
            if x<minimum*scale+effective+scale or x+1>(minimum+59)*scale+effective:continue
            for name,origin in origins.items():
                if name=='global_uncached':p=sample(scale,effective,x,minimum)
                elif name.startswith('cache_'):p=sample(scale,effective-origin,x-origin,minimum)
                else:p=sample(scale,round(inner*4)/4-origin,x-math.floor(outer+.5)-origin,minimum)
                target=c['clear'] if name=='global_uncached' else c['cached'];s=models[name];s['samples']+=1
                if p==target[x]:s['exact']+=1
                else:s['failures'].append({'case':int(i),'x':x,'actual':p,'native':target[x]})
    return {'input_exact':480,'properties':[c['key'] for c in cases],'placement':placement,'models':models,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=analyze(a.native);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n');print({k:{m:(v['exact_rows'],v['exact'],v['samples']) for m,v in s.items()} for k,s in r['placement'].items()});print({k:(v['exact'],v['samples']) for k,v in r['models'].items()})
