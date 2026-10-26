"""Discriminate nested translation consumption with independently varied outer scale/sign."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
from tools.probes.analyze_bitmap_nested_translation import ROOT,predict


def decode(native,count=540):
    b=json.loads((native/'build.json').read_text());assert hashlib.sha256((ROOT/b['source']).read_bytes()).hexdigest()==b['source_sha256']
    p=native/'native.log';text=p.read_text() if p.exists() else gzip.decompress(p.with_suffix('.log.gz').read_bytes()).decode()
    rows=[s.split('|') for s in text.splitlines() if s.startswith('AIREF|')]
    assert len(rows)==9+3*count and rows[-1][6:]==['done','ok']
    for i,r in enumerate(rows):assert r[1]==b['run_id'] and r[2:6]==[str(i),'0','0','0']
    for y,r in enumerate(rows[:8]):
        v=list(map(int,r[7].split(',')));assert r[6]=='source' and v[0]==y and len(v)==61
        for x,p in enumerate(v[1:]):assert p&0xffffffff==0xff000000+(x%2)*255*65536+((x*37+17)%256)*256+113
    cases=[]
    for i in range(count):
        block=rows[8+i*3:11+i*3];assert [r[6] for r in block]==['case','nested','direct']
        key=list(map(float,block[0][7].split(',')));assert key[0]==i and len(key)==10
        pairs={r[6]:[[(p>>s)&255 for s in (16,8,0)] for p in map(int,r[7].split(','))] for r in block[1:]}
        assert all(len(v)==600 for v in pairs.values());cases.append({'key':key,**pairs})
    return cases


def translations(inner,outer,scale,composed):
    q=lambda v:math.trunc(v*4)/4
    return {'composed_double':composed,'separate_quarters_before_scale':q(inner)*scale+q(outer),
            'inner_quarter_only':q(inner)*scale+outer,'separate_quarters_after_scale':q(inner*scale)+q(outer),
            'scaled_inner_quarter_only':q(inner*scale)+outer,
            'scaled_inner_nearest_even':round(inner*scale*4)/4+q(outer),
            'scaled_inner_nearest_away':math.copysign(math.floor(abs(inner*scale)*4+.5)/4,inner)+q(outer)}


def old_regression():
    from tools.probes.analyze_bitmap_nested_translation import decode as old_decode
    scores={m:{'samples':0,'exact':0,'failures':[]} for m in ('scaled_inner_nearest_even','scaled_inner_nearest_away')}
    for c in old_decode(ROOT/'evidence/importer-loud-fail/r95/native'):
        i,_,_,outer,scale,inner,_,_,composed=c['key']
        ts=translations(inner,outer,1,composed)
        for x in range(600):
            if x<composed+scale or x+1>composed+59*scale:continue
            for m,s in scores.items():
                p=predict(scale,ts[m],x);s['samples']+=1
                if p==c['nested'][x]:s['exact']+=1
                else:s['failures'].append({'case':int(i),'x':x,'actual':p,'native':c['nested'][x]})
    return scores


def analyze(native,case_count=540):
    cases=decode(native,case_count);names=translations(0,0,1,0)
    scores={path:{m:{'samples':0,'exact':0,'failures':[]} for m in names} for path in ('nested','direct')};different=[];excluded=[]
    for c in cases:
        i,requested_scale,requested_inner,outer,inner_scale,inner,outer_property,scale,composed,outer_scale=c['key']
        assert outer_property==outer
        models=translations(inner,outer,outer_scale,composed)
        for x in range(600):
            if x<composed+scale or x+1>composed+59*scale:
                excluded.append({'case':int(i),'x':x,'nested':c['nested'][x],'direct':c['direct'][x]});continue
            if c['nested'][x]!=c['direct'][x]:different.append({'case':int(i),'x':x,'nested':c['nested'][x],'direct':c['direct'][x]})
            for name,t in models.items():
                p=predict(scale,t,x)
                for path in scores:
                    s=scores[path][name];s['samples']+=1
                    if p==c[path][x]:s['exact']+=1
                    else:s['failures'].append({'case':int(i),'x':x,'actual':p,'native':c[path][x]})
    return {'input_exact':480,'cases':len(cases),'properties':[c['key'] for c in cases],'scores':scores,'nested_direct_differences':different,'excluded_mask_boundary_or_outside':excluded,'old_translation_regression':old_regression(),'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=analyze(a.native);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n');print({p:{m:(s['exact'],s['samples']) for m,s in v.items()} for p,v in r['scores'].items()});print('nested vs direct',len(r['nested_direct_differences']))
