"""Test source-size and mask-size dependence without changing sampled bytes or transforms."""
import argparse
from fractions import Fraction
import json
from pathlib import Path
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.run_nested_filters import unpack
from tools.probes.analyze_nearest_affine import inverse


def analyze(native):
    records=events(native);assert len(records)==785;sources={16:[],128:[]};groups={};samples=0
    for kind,payload in records:
        v=payload.split(',')
        if kind=='source':
            n,y=map(int,v[:2]);assert n in sources and y==len(sources[n])//n and len(v)==2+n*2;sources[n].extend(unpack(list(map(int,v[2:]))))
        elif kind=='sample':
            assert len(v)==29 and int(v[0])==samples;samples+=1
            source_size,mask_size=map(int,v[21:23]);assert source_size in sources and mask_size in sources
            assert list(map(Fraction,v[23:27]))==[0,0,mask_size,mask_size]
            pixel=unpack(list(map(int,v[27:])))[0];assert pixel[2:]==[73,255] and all(0<=c<16 for c in pixel[:2])
            co=inverse(v[:17]);x,y=map(int,v[19:21]);assert all(1<=a*xx+b*yy+t<=15 for a,b,t in co for xx,yy in ((x,y),(x+1,y),(x,y+1),(x+1,y+1)))
            group=groups.setdefault(tuple(v[1:21]),{});assert (source_size,mask_size) not in group;group[source_size,mask_size]=pixel
        else:assert [kind,payload]==['done','ok']
    for n,raw in sources.items():assert raw==[[x,y,73,255] for y in range(n) for x in range(n)]
    assert samples==640 and len(groups)==160;rows=[]
    for key,variants in groups.items():
        assert set(variants)=={(16,16),(16,128),(128,16),(128,128)}
        rows.append({'key':list(key),'variants':{f'{s}/{m}':p for (s,m),p in variants.items()},'all_equal':len({tuple(p) for p in variants.values()})==1})
    return {'source_texels_exact':16640,'samples':640,'groups':160,'invariant_groups':sum(v['all_equal'] for v in rows),'rows':rows,'affine_sampler_admitted':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=analyze(a.native);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n');print('invariant groups',r['invariant_groups'],r['groups'])
