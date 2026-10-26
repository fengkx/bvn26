"""Reject fixed row group hypotheses against independent geometry/color controls."""
import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess
from PIL import Image
from tools.probes.build_jpeg_row_partitions import controls
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.analyze_jpeg_color_sequences import rgb


def routed_rgb(value,x,width,group):
    return rgb(value,'floor-contributions' if x < width//group*group else 'nearest-total')


def analyze(native,executable,output):
    generated=controls();assert json.loads((native/'build.json').read_text())['cases']==[c for c,_ in generated]
    targets=[]
    for kind,data in events(native):
        if kind=='case':
            i,w,h,transparent=data.split(',');case=generated[len(targets)][0]
            assert [int(i),int(w),int(h),transparent]==[case['id'],case['width'],8,'false']
            targets.append([])
        elif kind=='row':
            values=list(map(int,data.split(',')));width=generated[len(targets)-1][0]['width']
            assert values[0]==len(targets[-1])//width and len(values)==width+1
            targets[-1].extend([[(v>>s)&255 for s in (16,8,0)] for v in values[1:]])
        else:assert [kind,data]==['done','ok']
    assert len(targets)==864
    output.mkdir(parents=True,exist_ok=True);rows=[];totals=Counter()
    for (case,jpeg),target in zip(generated,targets):
        width=case['width'];assert len(target)==width*8
        folder=output/f"case{case['id']}";folder.mkdir(exist_ok=True)
        path=folder/'input.jpg';path.write_bytes(jpeg)
        for scale in ((1,2) if case['subsampling']==2 else (1,)):
            destination=folder/f'scale{scale}';destination.mkdir(exist_ok=True)
            p=subprocess.run([str(executable),str(path),str(destination),str(scale)],capture_output=True,check=True)
            (destination/'decode.log').write_bytes(p.stderr)
        paths=[folder/'scale1/c0.pgm']+[folder/f"scale{2 if case['subsampling']==2 else 1}/c{c}.pgm" for c in (1,2)]
        channels=[set(Image.open(p).getdata()) for p in paths]
        assert all(len(c)==1 for c in channels)
        actual_input=[next(iter(c)) for c in channels];assert actual_input==case['ycbcr']
        for group in (1,4,8,16):
            failures=[]
            for i,expected in enumerate(target):
                actual=routed_rgb(actual_input,i%width,width,group)
                if actual!=expected:failures.append({'x':i%width,'y':i//width,'candidate':actual,'native':expected,'delta':[a-b for a,b in zip(actual,expected)]})
            exact=len(target)-len(failures);totals[group]+=exact
            rows.append({'case':case,'group':group,'pixels':len(target),'exact':exact,'failures':failures})
    result={'rows':rows,'exact_by_group':dict(totals),'pixels_per_group':sum(len(t) for t in targets),'production_admitted':False}
    (output/'summary.json').write_text(json.dumps(result,indent=2)+'\n');return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native',type=Path,required=True)
    parser.add_argument('--dump',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();r=analyze(args.native,args.dump,args.output);print(r['exact_by_group'],r['pixels_per_group'])
