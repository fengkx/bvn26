"""Compare child and declared fill transform paths with source and geometry readbacks."""
import argparse
from fractions import Fraction
import json
from pathlib import Path
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.run_nested_filters import unpack
from tools.probes.analyze_nearest_affine import decode as old_decode,inverse


def analyze(native,old_native):
    source,original=old_decode(old_native);lookup={tuple(c['key'][1:5]):c for c in original};raw=[];cases=[];records=events(native);assert len(records)==13457
    for kind,payload in records:
        v=payload.split(',')
        if kind=='source':assert int(v[0])==len(raw)//16 and len(v)==33;raw.extend(unpack(list(map(int,v[1:]))))
        elif kind=='case':assert len(v)==24 and int(v[0])==len(cases);cases.append({'key':v,'pixels':[]})
        elif kind=='geometry':assert len(v)==12;cases[-1]['geometry']=v
        elif kind=='row':
            pixels=cases[-1]['pixels'];assert int(v[0])==len(pixels)//40 and len(v)==81;pixels.extend(unpack(list(map(int,v[1:]))))
        else:assert [kind,payload]==['done','ok']
    assert raw==source and len(cases)==320 and all(len(c['pixels'])==1600 for c in cases)
    prior_exact=0;rows=[];failures=[]
    for child,fill in zip(cases[::2],cases[1::2]):
        a,b=child['key'],fill['key'];assert a[1:5]==b[1:5] and a[5]=='0' and b[5]=='1' and a[18:]==b[18:]
        original_case=lookup[tuple(a[1:5])];assert a[6:12]==original_case['key'][5:11] and a[18:]==original_case['key'][11:]
        prior_exact+=sum(x==y for x,y in zip(child['pixels'],original_case['pixels']))
        def effective(k):
            ca,cb,cc,cd,ctx,cty=map(Fraction,k[6:12]);fa,fb,fc,fd,ftx,fty=map(Fraction,k[12:18])
            return [ca*fa+cc*fb,cb*fa+cd*fb,ca*fc+cc*fd,cb*fc+cd*fd,ca*ftx+cc*fty+ctx,cb*ftx+cd*fty+cty]
        assert effective(a)==effective(b)
        co=inverse(original_case['key']);row={'key':a[1:5],'declared_effective_matrix':[str(v) for v in effective(a)],'child_geometry':child['geometry'],'fill_geometry':fill['geometry'],'samples':1600,'exact':0,'interior_samples':0,'interior_exact':0,'max_channel_delta':0}
        for y in range(40):
            for x in range(40):
                p,q=child['pixels'][y*40+x],fill['pixels'][y*40+x];corners=[[aa*xx+bb*yy+t for aa,bb,t in co] for xx,yy in ((x,y),(x+1,y),(x,y+1),(x+1,y+1))];inside=all(1<=v<=15 for point in corners for v in point)
                row['exact']+=p==q;row['max_channel_delta']=max(row['max_channel_delta'],max(abs(v-w) for v,w in zip(p,q)))
                if inside:row['interior_samples']+=1;row['interior_exact']+=p==q
                if p!=q:failures.append({'key':a[1:5],'x':x,'y':y,'interior':inside,'child':p,'fill':q})
        rows.append(row)
    return {'source_texels_exact':256,'old_child_path':{'samples':256000,'exact':prior_exact},'path_comparison':{'samples':sum(r['samples'] for r in rows),'exact':sum(r['exact'] for r in rows),'interior_samples':sum(r['interior_samples'] for r in rows),'interior_exact':sum(r['interior_exact'] for r in rows),'max_channel_delta':max(r['max_channel_delta'] for r in rows)},'rows':rows,'failures':failures,'fill_matrix_is_declared_not_internal_readback':True,'affine_sampler_admitted':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--old-native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=analyze(a.native,a.old_native);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n');print(r['old_child_path']);print(r['path_comparison'])
