"""Require valid indexed input and compare fixed continuous-span arithmetic globally."""
import argparse
import hashlib
import json
import math
from pathlib import Path
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.bitmap_half_even_candidate import row,interpolate
from tools.probes.run_nested_filters import unpack
from tools.probes.build_bound_bitmap_component import ROOT


def decode(native):
    build=json.loads((native/'build.json').read_text());assert hashlib.sha256((ROOT/build['harness_source']).read_bytes()).hexdigest()==build['harness_sha256']
    records=events(native);assert len(records)==7812;source=[];indexed=[];samples=[[],[]];loaded=[]
    for kind,payload in records:
        v=payload.split(',')
        if kind in ('source','indexed_source'):
            pixels=source if kind=='source' else indexed;assert len(v)==71 and int(v[0])==len(pixels)//35;pixels.extend(unpack(list(map(int,v[1:]))))
        elif kind=='loaded':loaded.append(v)
        elif kind in ('sample0','sample1'):
            epoch=int(kind[-1]);key=list(map(float,v[:13]));length=int(v[14]);assert len(v)==15+2*length and key[0]==epoch*3840+len(samples[epoch]) and v[13]=='false'
            samples[epoch].append({'key':key,'length':length,'pixels':unpack(list(map(int,v[15:])))})
        else:assert [kind,payload]==['done','ok']
    palette=[[0,0,0,0],[255,0,0,255],[0,255,0,255],[0,0,255,255]];expected=[palette[y%2*2+x%2] for y in range(65) for x in range(35)]
    assert source==indexed==expected and loaded==[['35','65','true']] and all(len(v)==3840 for v in samples)
    assert build['header_intervention']['after_header_bytes']==6
    return source,samples


def full_product(u,v,texel):
    ix,iy=math.floor(u),math.floor(v);fx,fy=math.floor((u-ix)*256),math.floor((v-iy)*256)
    weights=[(256-fx)*(256-fy),fx*(256-fy),(256-fx)*fy,fx*fy]
    pixels=[texel(ix+a,iy+b) for a,b in ((0,0),(1,0),(0,1),(1,1))]
    return [sum(w*p[k] for w,p in zip(weights,pixels))//65536 for k in range(4)]


def analyze(native):
    source,epochs=decode(native);scores={};excluded=0;before_after=0;before_after_samples=0;api_scores=[]
    texel=lambda x,y:source[max(0,min(64,y))*35+max(0,min(34,x))]
    for a,b in zip(*epochs):
        assert a['key'][1:]==b['key'][1:] and a['length']==b['length'];before_after+=sum(p==q for p,q in zip(a['pixels'],b['pixels']));before_after_samples+=a['length']
    for epoch,cases in enumerate(epochs):
        api_pixels=api_exact=0
        for a,b in zip(cases[::2],cases[1::2]):
            assert a['key'][1]==0 and b['key'][1]==1 and a['key'][2:12]==b['key'][2:12] and a['length']==b['length']
            api_pixels+=a['length'];api_exact+=sum(p==q for p,q in zip(a['pixels'],b['pixels']))
        api_scores.append({'epoch':epoch,'samples':api_pixels,'exact':api_exact})
        for case in cases:
            _,api,fx,fy,sx,sy,cx,cy,dx,dy,left,y,_=case['key'];left=int(left);y=int(y);length=case['length']
            tx=round(cx*4)/4+math.trunc(dx*4)/4;ty=round(cy*4)/4+math.trunc(dy*4)/4
            shape_left=tx+fx*sx;shape_right=shape_left+35*sx;shape_top=ty+fy*sy;shape_bottom=shape_top+65*sy
            c={'sx':sx,'sy':sy,'tx':tx,'ty':ty,'fill_x':fx,'fill_y':fy,'width':35,'height':65,'repeat':False,'shape_left':fx,'left':left,'right':min(left+length,math.ceil(shape_right)),'y':y}
            start,xs,v,modes=row(c)
            for offset,target in enumerate(case['pixels']):
                x=left+offset
                if not (shape_left<=x and x+1<=shape_right and shape_top<=y and y+1<=shape_bottom):excluded+=1;continue
                j=x-start;assert 0<=j<len(xs);u=xs[j];bulk=modes[j]!='byte'
                candidates={'admitted_vertical_bulk':interpolate(u,v,texel,modes[j]),'horizontal_bulk':interpolate(u,v,texel,'horizontal' if bulk else 'byte'),'byte_all':interpolate(u,v,texel,'byte'),'full_product_bulk':full_product(u,v,texel) if bulk else interpolate(u,v,texel,'byte')}
                for name,actual in candidates.items():
                    score=scores.setdefault(f'api{int(api)}-{name}',{'samples':0,'exact':0,'max_channel_delta':0,'failures':[]})
                    score['samples']+=1;score['exact']+=actual==target;score['max_channel_delta']=max(score['max_channel_delta'],max(abs(a-b) for a,b in zip(actual,target)))
                    if actual!=target:score['failures'].append({'epoch':epoch,'key':case['key'],'length':length,'x':x,'uv':[u,v],'bulk':bulk,'actual':actual,'native':target})
    return {'native_source_exact':2275,'before_after':{'samples':before_after_samples,'exact':before_after},'api_comparisons':api_scores,'scores':scores,'excluded_fringe_or_outside':excluded,'indexed_continuous_sampler_admitted':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=analyze(a.native);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n');print('before/after',r['before_after']);print('api',r['api_comparisons'])
    for k,v in r['scores'].items():print(k,v['exact'],v['samples'],v['max_channel_delta'])
