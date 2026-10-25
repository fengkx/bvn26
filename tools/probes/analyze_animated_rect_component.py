"""Compare source-frame-selected rectangle leaves with independent animated cache boundaries."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
from PIL import Image
from tools.probes.build_bound_bitmap_component import ROOT,source_tags
from tools.probes.analyze_rect_component_cache import render_cache
from tools.probes.analyze_bitmap_cache_support_grid import separate_bounds
from tools.probes.analyze_cache_device_origin import device_translation
from tools.probes.bitmap_half_even_candidate import row
from tools.probes.analyze_clipped_half_step import axis
from tools.probes.analyze_animated_component_boundaries import decode
from tools.probes.analyze_blur_kernel_heldout import render as blur
from tools.probes.analyze_jiraiya_filter_boundary import comparison


def blocked_fringe(leaf,properties):
    _,dsx,dsy,dx,dy,sx,sy,tx,ty,*_=properties
    assert dsx==dsy==sx==sy==1
    fx=float(leaf['fill_matrix']['translateX'])/20;fy=float(leaf['fill_matrix']['translateY'])/20
    ix=float(leaf['inner_matrix']['translateX'])/20;iy=float(leaf['inner_matrix']['translateY'])/20
    xb=separate_bounds(fx+ix,leaf['width'],sx,tx,dx);yb=separate_bounds(fy+iy,leaf['height'],sy,ty,dy)
    transform={'sx':sx,'sy':sy,'tx':device_translation(sx,tx,dx,xb[0])+round(ix*sx*4)/4,'ty':device_translation(sy,ty,dy,yb[0])+round(iy*sy*4)/4}
    left=transform['tx']+fx;right=left+leaf['width'];top=transform['ty']+fy;bottom=top+leaf['height'];raw=leaf['pixels_premultiplied'];w,h=leaf['width'],leaf['height'];failures=[]
    texel=lambda x,y:raw[max(0,min(h-1,y))*w+max(0,min(w-1,x))]
    for y in range(max(0,math.floor(top)),min(yb[1]-yb[0],math.ceil(bottom))):
        spec={**transform,'width':w,'height':h,'repeat':False,'fill_x':fx,'fill_y':fy,'shape_left':fx,'left':max(0,math.ceil(left)),'right':min(xb[1]-xb[0],math.floor(right)),'y':y}
        start,xs,yy,modes=row(spec)
        for x in range(max(0,math.floor(left)),min(xb[1]-xb[0],math.ceil(right))):
            if left<=x and x+1<=right and top<=y and y+1<=bottom:continue
            xx=xs[x-start] if start<=x<start+len(xs) else axis(sx,transform['tx'],x,'even')-fx
            footprint=[texel(math.floor(xx)+a,math.floor(yy)+b) for a,b in ((0,0),(1,0),(0,1),(1,1))]
            if any(p!=[0,0,0,0] for p in footprint):failures.append({'local':[x,y],'stage':[x+xb[0],y+yb[0]],'uv':[xx,yy],'footprint':footprint,'geometric_area':(min(x+1,right)-max(x,left))*(min(y+1,bottom)-max(y,top))})
    assert failures
    return {'x_bounds':xb,'y_bounds':yb,'local_transform':transform,'shape_edges':[left,top,right,bottom],'nontransparent_fringe':failures}


def analyze(fixture_path,native,output=None):
    fixture=json.loads(fixture_path.read_text());case=fixture['case'];source=ROOT/case['source']['path'];assert hashlib.sha256(source.read_bytes()).hexdigest()==case['source']['sha256']
    tags={str(struct.unpack_from('<H',p)[0]):r for code,p,r in source_tags(source) if code in (2,36,39)}
    for cid,digest in fixture['raw_tag_sha256'].items():assert hashlib.sha256(tags[cid]).hexdigest()==digest
    build,images,matrices,clocks,props,restores=decode(native);assert case==build['case'];f=case['placement']['filters'][0];rows=[]
    if output:output.mkdir(parents=True,exist_ok=True)
    for tick,matrix in zip(case['samples'],matrices):
        frame=next(v['frame'] for v in clocks if v['tick']==tick and v['path']==case['id']+'/'+str(case['placement']['depth']))
        state=fixture['frames'][frame-1];leaf={**fixture['leaves'][str(state['shape_id'])],'inner_matrix':state['inner_matrix']}
        try:pixels,metadata=render_cache(leaf,[tick,0]+matrix[1:])
        except AssertionError as error:
            if str(error)!='Unproven fractional coverage':raise
            rows.append({'tick':tick,'native_frame':frame,'shape_id':state['shape_id'],'status':'blocked','error':str(error),'location':f"{case['source']['path']}:DefineSprite_{case['symbol']}/frame_{frame}/DefineShape_{state['shape_id']}",'diagnosis':blocked_fringe(leaf,matrix)})
            continue
        channels=[]
        for channel in range(4):
            image=[[pixels[y*600+x][channel] for x in range(600)] for y in range(400)]
            filtered=blur(image,f['blurX'],f['blurY'],f['passes'],'grouped');channels.append([v for row in filtered for v in row])
        filtered=[list(v) for v in zip(*channels)]
        row={'tick':tick,'native_frame':frame,'shape_id':state['shape_id'],'metadata':metadata,'cache':comparison(pixels,images[f'{tick}-cache']),'authored':comparison(filtered,images[f'{tick}-authored'])}
        composed=[[r+96*(256-a)//256,g+96*(256-a)//256,b+96*(256-a)//256,255] for r,g,b,a in filtered]
        path=ROOT/f"evidence/importer-loud-fail/r21/components/{source.stem}/{case['id']}-{tick:03d}.native.png"
        row['pinned']={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),**comparison(composed,list(Image.open(path).convert('RGBA').getdata()))};rows.append(row)
        if output:
            for kind,data in [('cache',pixels),('authored',filtered)]:Image.frombytes('RGBA',(600,400),bytes(c for p in data for c in p)).save(output/f'{tick}-{kind}.png')
    return {'rows':rows,'source_animation_frames':fixture['frames'],'source_cpu_exact':all(v.get('status')!='blocked' and all(v[k]['exact']==v[k]['samples'] for k in ('cache','authored','pinned')) for v in rows),'gpu_binding_verified':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--fixture',type=Path,required=True);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=analyze(a.fixture,a.native,a.output);(a.output/'analysis.json').write_text(json.dumps(r,separators=(',',':'))+'\n')
    for v in r['rows']:print(v['tick'],v['shape_id'],v.get('error') or [v[k]['exact'] for k in ('cache','authored','pinned')])
    raise SystemExit(0 if r['source_cpu_exact'] else 1)
