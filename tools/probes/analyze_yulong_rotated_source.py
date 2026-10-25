"""Bind original rotated Yulong fill bytes without changing source slots or reference images."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
from PIL import Image
from tools.probes.build_bound_bitmap_component import ROOT,source_tags
from tools.probes.inventory_bitmap_roundtrip import decode_lossless
from tools.probes.bitmap_half_even_candidate import interpolate
from tools.probes.analyze_component_cache_boundaries import decode
from tools.probes.analyze_component_glow_boundaries import glow
from tools.probes.analyze_jiraiya_filter_boundary import comparison


def source_leaf():
    evidence=ROOT/'evidence/importer-loud-fail/r132';info=json.loads((evidence/'summary.json').read_text())
    source=ROOT/info['case']['source']['path'];assert hashlib.sha256(source.read_bytes()).hexdigest()==info['case']['source']['sha256']
    tags={str(struct.unpack_from('<H',p)[0]):(code,p,r) for code,p,r in source_tags(source) if code in (2,36,39)}
    for cid,digest in info['raw_tag_sha256'].items():assert hashlib.sha256(tags[cid][2]).hexdigest()==digest
    assert [f['directed_edge_count'] for f in info['fills']]==[0,4]
    fill=info['fills'][1];m=fill['matrix'];assert [float(m[k]) for k in ['scaleX','rotateSkew0','rotateSkew1','scaleY','translateX','translateY']]==[0,20,-20,0,60,0]
    cid,w,h,raw=decode_lossless(tags['148'][1]);assert (w,h)==(34,3)
    assert hashlib.sha256(bytes(v for p in raw for v in p)).hexdigest()==fill['bitmap']['raw_rgba_sha256']
    assert fill['contours']==[[[3,0],[3,34],[0,34],[0,0]]]
    return info,raw


def render(info,raw,shift):
    case=info['case'];m=case['placement']['matrix'];n=case['normalization'];assert n['scale']==1
    # Retain independently proven child and draw translation consumption.
    tx=round(float(m['translateX'])/20*4)/4+math.trunc((n['x']+shift)*4)/4
    ty=round(float(m['translateY'])/20*4)/4+math.trunc(n['y']*4)/4
    out=[[0,0,0,0] for _ in range(600*400)];fringe=[]
    texel=lambda x,y:raw[max(0,min(2,y))*34+max(0,min(33,x))]
    for y in range(math.floor(ty),math.ceil(ty+34)):
        for x in range(math.floor(tx),math.ceil(tx+3)):
            # Exact inverse of the retained unit quarter-turn matrix; no texel permutation.
            u=y-ty;v=2+tx-x
            p=interpolate(u,v,texel,'byte')
            coverage=(min(x+1,tx+3)-max(x,tx))*(min(y+1,ty+34)-max(y,ty))
            assert coverage in (.125,.25,.375,.5,.75,1)
            value=[math.floor(c*coverage) for c in p];out[y*600+x]=value
            if coverage!=1:fringe.append({'x':x,'y':y,'coverage':coverage,'sample':p,'actual':value})
    return out,{'origin':[tx,ty],'fringe':fringe}


def analyze(output=None):
    info,raw=source_leaf();native=ROOT/'evidence/importer-loud-fail/r131/native';build,images,matrices,access,props=decode(native)
    assert build['case']==info['case'];rows=[];pinned=[]
    for i,shift in enumerate((-128,0,128)):
        candidate,metadata=render(info,raw,shift);filtered=glow(candidate,info['case']['placement']['filters'][0])
        row={'shift':shift,'input':comparison(candidate,images[f'{i}-cache']),'glow':comparison(filtered,images[f'{i}-authored']),**metadata}
        row['fringe_exact']=sum(v['actual']==images[f'{i}-cache'][v['y']*600+v['x']] for v in metadata['fringe'])
        if output:
            for name,pixels in [('input',candidate),('glow',filtered)]:Image.frombytes('RGBA',(600,400),bytes(c for p in pixels for c in p)).save(output/f'{i}-{name}.png')
        if i==1:
            composed=[[r+96*(256-a)//256,g+96*(256-a)//256,b+96*(256-a)//256,255] for r,g,b,a in filtered]
            for tick in info['case']['samples']:
                path=ROOT/f"evidence/importer-loud-fail/r21/components/yulong/{info['case']['id']}-{tick:03d}.native.png"
                pinned.append({'tick':tick,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),**comparison(composed,list(Image.open(path).convert('RGBA').getdata()))})
        rows.append(row)
    return {'rows':rows,'pinned':pinned,'original_fill_table':info['fills'],'source_derived_input_verified':False,'fractional_coverage_independently_verified':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True);r=analyze(a.output);(a.output/'analysis.json').write_text(json.dumps(r,separators=(',',':'))+'\n')
    for v in r['rows']:print(v['shift'],v['input']['exact'],v['glow']['exact'],v['fringe_exact'],len(v['fringe']))
