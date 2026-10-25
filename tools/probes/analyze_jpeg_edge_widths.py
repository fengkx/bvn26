"""Compare coefficient-preserving image widths without edge-coordinate corrections."""
import argparse
import json
from pathlib import Path
import struct
import zlib
from tools.probes.build_jpeg_edge_widths import cases
from tools.probes.build_bound_bitmap_component import ROOT,source_tags
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.run_nested_filters import unpack
from tools.probes.analyze_jpeg_scaled_planes import compare


def analyze(native,executable,output):
    generated=cases();assert json.loads((native/'build.json').read_text())['cases']==[c for c,_,_ in generated]
    targets=[]
    for kind,data in events(native):
        if kind=='case':
            i,w,h,transparent=data.split(',');c=generated[len(targets)][0]
            assert [int(i),int(w),int(h),transparent]==[c['id'],c['width'],378,'true' if c['tag']==35 else 'false']
            targets.append([])
        elif kind=='row':
            v=list(map(int,data.split(',')));width=generated[len(targets)-1][0]['width']
            assert len(v)==1+width*2 and v[0]==len(targets[-1])//width
            targets[-1].extend(unpack(v[1:]))
        else:assert [kind,data]==['done','ok']
    assert len(targets)==7
    old=[]
    for _,data in events(ROOT/'evidence/importer-loud-fail/r210/native')[1:-1]:old.extend(unpack(list(map(int,data.split(',')))[1:]))
    assert targets[0]==old
    payload=next(p for c,p,_ in source_tags(ROOT/'game/fighter/orochimaru.swf') if c==35 and struct.unpack_from('<H',p)[0]==340)
    n=struct.unpack_from('<I',payload,2)[0];alpha=zlib.decompress(payload[6+n:])
    assert [p[3] for p in old]==list(alpha)
    rows=[]
    for (case,_,jpeg),target in zip(generated,targets):
        assert len(target)==case['width']*378
        assert jpeg.count(b'\xff\xd9\xff\xd8')==1
        seam=jpeg.index(b'\xff\xd9\xff\xd8');assert seam==572
        result=compare(jpeg[:seam]+jpeg[seam+4:],target,alpha if case['tag']==35 else [255]*len(target),2,executable,output/f"case{case['id']}")
        rows.append({'case':case,**result})
    comparisons=[];wide=targets[-1]
    for (case,_,_),target in zip(generated[1:-1],targets[1:-1]):
        differences=[];width=case['width']
        for i,pixel in enumerate(target):
            x=i%width;y=i//width
            if pixel!=wide[y*192+x]:differences.append({'x':x,'y':y,'narrow':pixel,'wide':wide[y*192+x]})
        comparisons.append({'width':width,'pixels':len(target),'exact':len(target)-len(differences),'differences':differences})
    same_jpeg2=targets[3]
    assert all(p[3]==0 or p==q for p,q in zip(old,same_jpeg2))
    result={'rows':rows,'overlap_vs_width192':comparisons,'original_unchanged_pixels':len(old),
            'jpeg2_matches_original_opaque_pixels':sum(a==255 for a in alpha),'production_admitted':False}
    (output/'summary.json').write_text(json.dumps(result,indent=2)+'\n');return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native',type=Path,required=True)
    parser.add_argument('--dump',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();r=analyze(args.native,args.dump,args.output)
    for row in r['rows']:print(row['case']['id'],row['case']['width'],row['exact'],row['pixels'],row['max_channel_delta'])
    for row in r['overlap_vs_width192']:print('overlap',row['width'],row['exact'],row['pixels'])
