"""Compare globally fixed nested-matrix consumption constructions on independent scalar ramps."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
from tools.probes.analyze_clipped_half_step import axis
from tools.probes.analyze_blur_kernel_heldout import ROOT


def decode(native):
    build=json.loads((native/'build.json').read_text());assert hashlib.sha256((ROOT/build['source']).read_bytes()).hexdigest()==build['source_sha256']
    p=native/'native.log';text=p.read_text() if p.exists() else gzip.decompress(p.with_suffix('.log.gz').read_bytes()).decode()
    rows=[s.split('|') for s in text.splitlines() if s.startswith('AIREF|')];assert len(rows)==549 and rows[-1][6:]==['done','ok']
    for i,r in enumerate(rows):assert r[1]==build['run_id'] and r[2:6]==[str(i),'0','0','0']
    for y,r in enumerate(rows[:8]):
        v=list(map(int,r[7].split(',')));assert r[6]=='source' and v[0]==y and len(v)==61
        for x,p in enumerate(v[1:]):assert p&0xffffffff==0xff000000+(x%2)*255*65536+((x*37+17)%256)*256+113
    cases=[]
    for i in range(180):
        block=rows[8+i*3:11+i*3];assert [r[6] for r in block]==['case','nested','direct']
        key=list(map(float,block[0][7].split(',')));assert key[0]==i and len(key)==9
        pairs={r[6]:[[(p>>s)&255 for s in (16,8,0)] for p in map(int,r[7].split(','))] for r in block[1:]}
        assert all(len(v)==600 for v in pairs.values());cases.append({'key':key,**pairs})
    return cases


def texel(x):
    x=max(0,min(59,x));return [x%2*255,(x*37+17)%256,113]


def predict(scale,translation,x):
    q=axis(scale,translation,x,'even');i=math.floor(q);f=math.floor((q-i)*256);a,b=texel(i),texel(i+1)
    return [(v*(256-f)+w*f)//256 for v,w in zip(a,b)]


def analyze(native):
    cases=decode(native)
    modes=('composed_double','outer_twip_nearest','outer_twip_truncate','composed_twip_nearest','composed_twip_truncate','separate_quarters','inner_quarter_only')
    scores={path:{m:{'samples':0,'exact':0,'failures':[]} for m in modes} for path in ('nested','direct')}
    different=[];excluded=[]
    for case in cases:
        i,requested_scale,requested_inner,outer,scale,inner,outer_property,composed_scale,composed=case['key']
        assert outer_property==outer and composed_scale==scale
        translations={'composed_double':composed,'outer_twip_nearest':inner+math.floor(outer*20+.5)/20,'outer_twip_truncate':inner+math.trunc(outer*20)/20,'composed_twip_nearest':math.floor(composed*20+.5)/20,'composed_twip_truncate':math.trunc(composed*20)/20,'separate_quarters':math.trunc(outer*4)/4+math.trunc(inner*4)/4,'inner_quarter_only':outer+math.trunc(inner*4)/4}
        for x in range(600):
            # Keep one whole source texel away from both mask boundaries.
            if x<composed+scale or x+1>composed+59*scale:
                excluded.append({'case':int(i),'x':x,'nested':case['nested'][x],'direct':case['direct'][x]});continue
            if case['nested'][x]!=case['direct'][x]:different.append({'case':int(i),'x':x,'nested':case['nested'][x],'direct':case['direct'][x]})
            for mode,translation in translations.items():
                p=predict(scale,translation,x)
                for path in scores:
                    s=scores[path][mode];s['samples']+=1
                    if p==case[path][x]:s['exact']+=1
                    else:s['failures'].append({'case':int(i),'x':x,'actual':p,'native':case[path][x]})
    return {'input_exact':480,'cases':len(cases),'properties':[c['key'] for c in cases],'scores':scores,'nested_direct_differences':different,'excluded_mask_boundary_or_outside':excluded,'production_admitted':False}


def source_leaf_heldout():
    from tools.probes.analyze_jiraiya_bitmap_binding import decode as leaf_decode
    from tools.probes.analyze_jiraiya_filter_boundary import decode as reference,comparison
    from tools.probes.bitmap_half_even_candidate import row,interpolate
    fixture,_=leaf_decode(ROOT/'evidence/importer-loud-fail/r89/native')
    native,_,_=reference(ROOT/'evidence/importer-loud-fail/r93/native')
    # The independent controls constrain this two-level translation construction.
    case=json.loads((ROOT/'evidence/importer-loud-fail/r21/components/jiraiya/cases.json').read_text())[0]
    m=case['placement']['matrix'];normal=case['normalization']
    assert normal['scale']==1 and not any(float(m.get(k,0)) for k in ('rotateSkew0','rotateSkew1'))
    c={'sx':round(m['scaleX']*65536)/65536,'sy':round(m['scaleY']*65536)/65536,
       'tx':math.trunc(normal['x']*4)/4+math.trunc(m['translateX']/20*4)/4,
       'ty':math.trunc(normal['y']*4)/4+math.trunc(m['translateY']/20*4)/4}
    sw,sh=fixture['width'],fixture['height']
    def texel(x,y):return fixture['pixels_premultiplied'][max(0,min(sh-1,y))*sw+max(0,min(sw-1,x))]
    output=[[0]*4 for _ in range(600*400)]
    left=c['tx'];right=left+sw*c['sx'];top=c['ty']+.8*c['sy'];bottom=c['ty']+58.8*c['sy']
    for y in range(math.floor(top),math.ceil(bottom)):
        spec={**c,'width':sw,'height':sh,'repeat':False,'fill_y':.8,'shape_left':0,'left':math.ceil(left),'right':math.floor(right),'y':y}
        start,xs,yy,modes=row(spec)
        for x in range(math.floor(left),math.ceil(right)):
            xx=xs[x-start] if start<=x<start+len(xs) else axis(c['sx'],c['tx'],x,'even')
            mode=modes[x-start] if start<=x<start+len(xs) else 'byte'
            if x<left or x+1>right or y<top or y+1>bottom:
                assert all(texel(math.floor(xx)+dx,math.floor(yy)+dy)==[0,0,0,0] for dx,dy in ((0,0),(1,0),(0,1),(1,1)))
            output[y*600+x]=interpolate(xx,yy,texel,mode)
    return {'effective_draw':c,'comparison':comparison(output,native['cleared']['rgba']),'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=analyze(a.native);r['source_leaf_heldout']=source_leaf_heldout();a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n');print({p:{m:(s['exact'],s['samples']) for m,s in v.items()} for p,v in r['scores'].items()});print('nested vs direct',len(r['nested_direct_differences']))
