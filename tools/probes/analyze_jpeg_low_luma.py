"""Reject low-luma hypotheses against independently encoded/read-back YCbCr."""
import argparse
import json
from pathlib import Path
from PIL import Image
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.build_jpeg_low_luma import controls
from tools.probes.analyze_jpeg_scaled_planes import compare


def analyze(native,executable,output):
    generated=controls();build=json.loads((native/'build.json').read_text())
    assert build['cases']==[c for c,_ in generated]
    targets=[]
    for kind,data in events(native):
        if kind=='case':
            i,w,h,transparent=data.split(',');assert [int(i),int(w),int(h),transparent]==[len(targets),16,16,'false']
            targets.append([])
        elif kind=='row':
            v=list(map(int,data.split(',')));assert len(v)==17 and v[0]==len(targets[-1])//16
            targets[-1].extend([[(n>>s)&255 for s in (16,8,0,24)] for n in v[1:]])
        else:assert [kind,data]==['done','ok']
    assert len(targets)==448 and all(len(t)==256 for t in targets)
    rows=[]
    for (case,jpeg),target in zip(generated,targets):
        folder=output/f"case{case['id']}"
        result=compare(jpeg,target,[255]*256,case['subsampling'],executable,folder)
        paths=[folder/'scale1/c0.pgm']+[folder/f"scale{2 if case['subsampling']==2 else 1}/c{c}.pgm" for c in (1,2)]
        channels=[set(Image.open(p).getdata()) for p in paths]
        assert all(len(c)==1 for c in channels)
        result['decoded_ycbcr']=[next(iter(c)) for c in channels]
        assert result['decoded_ycbcr']==case['ycbcr']
        rows.append({'case':case,**result})
    result={'rows':rows,'pixels':sum(r['pixels'] for r in rows),'exact':sum(r['exact'] for r in rows),
            'production_admitted':False}
    (output/'summary.json').write_text(json.dumps(result,indent=2)+'\n');return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native',type=Path,required=True)
    parser.add_argument('--dump',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();r=analyze(args.native,args.dump,args.output);print(r['exact'],r['pixels'])
