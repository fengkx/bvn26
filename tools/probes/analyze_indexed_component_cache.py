"""Compare source-frame-selected rectangle leaves with independent animated cache boundaries."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
from PIL import Image
from tools.probes.build_bound_bitmap_component import ROOT,source_tags
from tools.probes.analyze_rect_component_cache import render_cache as baseline_cache
from tools.probes.indexed_rect_candidate import render_leaf
from tools.probes.rect_mask_binding import canonical_rect_mask
from tools.probes.inventory_bitmap_roundtrip import decode_lossless
from tools.probes.analyze_bitmap_cache_support_grid import separate_bounds
from tools.probes.analyze_cache_device_origin import device_translation
from tools.probes.bitmap_half_even_candidate import row
from tools.probes.analyze_clipped_half_step import axis
from tools.probes.analyze_animated_component_boundaries import decode
from tools.probes.analyze_blur_kernel_heldout import render as blur
from tools.probes.analyze_jiraiya_filter_boundary import comparison


from tools.probes.analyze_animated_rect_component import blocked_fringe


def render_cache(leaf,properties):
    # Reuse the pinned cache allocation and its fail-closed coverage validation.
    baseline,metadata=baseline_cache(leaf,properties)
    width,height=metadata['local_size']
    local=render_leaf({**leaf,'fill_masks':canonical_rect_mask(leaf)},metadata['local_transform'],(width,height))
    result=[[0]*4 for _ in range(240000)]
    xb,yb=metadata['x_bounds'],metadata['y_bounds']
    for y in range(height):
        for x in range(width):result[(yb[0]+y)*600+xb[0]+x]=local[y*width+x]
    return result,metadata


def analyze(fixture_path,native,output=None):
    fixture=json.loads(fixture_path.read_text());case=fixture['case'];source=ROOT/case['source']['path'];assert hashlib.sha256(source.read_bytes()).hexdigest()==case['source']['sha256']
    payloads={str(struct.unpack_from('<H',p)[0]):p for code,p,_ in source_tags(source) if code==36}
    tags={str(struct.unpack_from('<H',p)[0]):r for code,p,r in source_tags(source) if code in (2,36,39)}
    for cid,digest in fixture['raw_tag_sha256'].items():assert hashlib.sha256(tags[cid]).hexdigest()==digest
    build,images,matrices,clocks,props,restores=decode(native);assert case==build['case'];f=case['placement']['filters'][0];rows=[]
    if output:output.mkdir(parents=True,exist_ok=True)
    for tick,matrix in zip(case['samples'],matrices):
        frame=next(v['frame'] for v in clocks if v['tick']==tick and v['path']==case['id']+'/'+str(case['placement']['depth']))
        state=fixture['frames'][frame-1];leaf={**fixture['leaves'][str(state['shape_id'])],'inner_matrix':state['inner_matrix']}
        payload=payloads[str(leaf['bitmap_id'])];assert payload[2]==3
        cid,w,h,raw=decode_lossless(payload);assert [cid,w,h]==[leaf['bitmap_id'],leaf['width'],leaf['height']] and raw==leaf['pixels_premultiplied']
        leaf['indexed_storage_verified']=True
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
