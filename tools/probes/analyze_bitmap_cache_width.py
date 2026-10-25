"""Separate source width, painted span and reported bounds using native prefix controls."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
from tools.probes.analyze_bitmap_nested_translation import ROOT
from tools.probes.analyze_clipped_half_step import axis

WIDTHS=(16,32,35,36,37,38,60,64)


def decode(native):
    b=json.loads((native/'build.json').read_text());assert hashlib.sha256((ROOT/b['source']).read_bytes()).hexdigest()==b['source_sha256']
    p=native/'native.log';text=p.read_text() if p.exists() else gzip.decompress(p.with_suffix('.log.gz').read_bytes()).decode()
    rows=[s.split('|') for s in text.splitlines() if s.startswith('AIREF|')]
    assert len(rows)==1993 and rows[-1][6:]==['done','ok'];cases=[];inputs=0
    for i,r in enumerate(rows):
        assert r[1]==b['run_id'] and r[2:6]==[str(i),'0','0','0']
        if r[6]=='source':
            label,width,y,*values=r[7].split(',');width=int(width);y=int(y)
            assert width==(64 if label=='shared' else WIDTHS[int(label)]) and 0<=y<8 and len(values)==width
            for x,v in enumerate(values):assert int(v)&0xffffffff==0xff000000+x%2*255*65536+((x*37+17)%256)*256+113;inputs+=1
        elif r[6]=='case':
            key=list(map(float,r[7].split(',')));assert key[0]==len(cases) and len(key)==12;cases.append({'key':key})
        elif r[6]=='cache':assert r[7] in ('0,false','1,true')
        elif r[6] in ('clear','cached'):
            values=list(map(int,r[7].split(',')));assert len(values)==1024 and r[6] not in cases[-1]
            cases[-1][r[6]]=[[(v>>s)&255 for s in (16,8,0)] for v in values]
        else:assert r[6]=='done'
    assert len(cases)==384 and inputs==3056 and all(set(c)=={'key','clear','cached'} for c in cases)
    return cases,inputs


def sample(scale,translation,x,width):
    q=axis(scale,translation,x,'even');i=math.floor(q);f=math.floor((q-i)*256)
    def texel(at):
        at=max(0,min(width-1,at));return [at%2*255,(at*37+17)%256,113]
    a,b=texel(i),texel(i+1);return [(v*(256-f)+w*f)//256 for v,w in zip(a,b)]


def compare_samples(actual,baseline,positions):
    failures=[{'x':x,'actual':actual[x],'baseline':baseline[x]} for x in positions if actual[x]!=baseline[x]]
    return {'samples':len(positions),'exact':len(positions)-len(failures),'max_channel_delta':max((abs(a-b) for r in failures for a,b in zip(r['actual'],r['baseline'])),default=0),'failures':failures}


def analyze(native):
    cases,inputs=decode(native);base={};lookup={};models=[];prefix=[];mode_pairs=[]
    for c in cases:
        i,width,mode,source_width,_,_,outer,scale,inner,bmin,bmax,painted=c['key']
        assert source_width==(width if mode==0 else 64) and painted==(16 if mode==2 else width)
        assert bmin==inner and bmax==float(format(width*scale+inner,'.15g'))
        key=(int(mode),scale,inner,outer);lookup[(int(width),*key)]=c
        if width==16:base[key]=c
    for c in cases:
        i,width,mode,source_width,_,_,outer,scale,inner,bmin,bmax,painted=c['key'];effective=round(inner*4)/4+math.trunc(outer*4)/4
        positions=[x for x in range(1024) if effective+scale<=x and x+1<=effective+(painted-1)*scale]
        origin=math.floor(effective)
        for kind in ('clear','cached'):
            candidate=[[0,0,0] for _ in range(1024)]
            for x in positions:candidate[x]=sample(scale,effective if kind=='clear' else effective-origin,x if kind=='clear' else x-origin,int(source_width))
            models.append({'case':int(i),'kind':kind,**compare_samples(candidate,c[kind],positions)})
        common=[x for x in positions if x+1<=effective+15*scale]
        ref=base[(int(mode),scale,inner,outer)]
        prefix.append({'case':int(i),'width':int(width),'mode':int(mode),'scale':scale,'inner':inner,'outer':outer,
                       'clear':compare_samples(c['clear'],ref['clear'],common),'cached':compare_samples(c['cached'],ref['cached'],common)})
        if mode!=0:
            ref=lookup[(int(width),0,scale,inner,outer)]
            mode_pairs.append({'case':int(i),'width':int(width),'mode':int(mode),'scale':scale,
                               'clear':compare_samples(c['clear'],ref['clear'],common),'cached':compare_samples(c['cached'],ref['cached'],common)})
    return {'input_exact':inputs,'properties':[c['key'] for c in cases],'models':models,'width_prefix':prefix,'mode_prefix':mode_pairs,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=analyze(a.native);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n')
    for kind in ('clear','cached'):
        scores=[v for v in r['models'] if v['kind']==kind];print(kind,sum(v['exact'] for v in scores),sum(v['samples'] for v in scores))
        for name in ('width_prefix','mode_prefix'):print(name,kind,sum(bool(v[kind]['failures']) for v in r[name]),len(r[name]))
