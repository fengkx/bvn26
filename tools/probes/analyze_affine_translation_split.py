"""Require identical source-to-device transforms before comparing split translation paths."""
import argparse
from fractions import Fraction
import json
from pathlib import Path
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.run_nested_filters import unpack
from tools.probes.analyze_nearest_affine import inverse


def analyze(native,baseline):
    prior=json.loads(baseline.read_text());lookup={tuple(r['key'][i] for i in (0,3,16,17,18,19)):{'pixel':r['variants']['16/16'],'linear':r['key'][4:8]} for r in prior['rows'] if r['key'][1:3]==['0','0']};assert len(lookup)==40
    records=events(native);assert len(records)==377;source=[];groups={};samples=0;old_exact=0
    for kind,payload in records:
        v=payload.split(',')
        if kind=='source':assert int(v[0])==len(source)//16 and len(v)==33;source.extend(unpack(list(map(int,v[1:]))))
        elif kind=='sample':
            assert len(v)==23 and int(v[0])==samples;samples+=1;pixel=unpack(list(map(int,v[21:])))[0];assert pixel[2:]==[73,255]
            co=inverse(v[:17]);x,y=map(int,v[19:21]);assert all(1<=a*xx+b*yy+t<=15 for a,b,t in co for xx,yy in ((x,y),(x+1,y),(x,y+1),(x+1,y+1)))
            tx=Fraction(v[9])+Fraction(v[15]);ty=Fraction(v[10])+Fraction(v[16]);assert (tx,ty)==((128,128) if v[4]=='0' else (Fraction(577,4),Fraction(451,4)))
            key=tuple(v[i] for i in (1,4,17,18,19,20));g=groups.setdefault(key,{});split=(int(v[2]),int(v[3]));assert split not in g;assert v[5:9]==lookup[key]['linear'];g[split]={'child':v[9:11],'draw':v[15:17],'linear':v[5:9],'pixel':pixel}
            if split==(1,1):old_exact+=pixel==lookup[key]['pixel']
        else:assert [kind,payload]==['done','ok']
    assert source==[[x,y,73,255] for y in range(16) for x in range(16)] and samples==360 and len(groups)==40
    rows=[]
    for k,g in groups.items():
        assert set(g)=={(x,y) for x in range(3) for y in range(3)}
        rows.append({'key':list(k),'variants':{f'{x}/{y}':v for (x,y),v in g.items()},'all_equal':len({tuple(v['pixel']) for v in g.values()})==1})
    return {'source_texels_exact':256,'samples':360,'groups':40,'invariant_groups':sum(v['all_equal'] for v in rows),'old_baseline':{'samples':40,'exact':old_exact},'rows':rows,'affine_sampler_admitted':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=analyze(a.native,a.baseline);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n');print(r['old_baseline']);print('invariant groups',r['invariant_groups'],r['groups'])
