"""Compare fixed YCbCr contribution orders on unsubsampled native controls."""
import argparse
from collections import Counter
import hashlib
from io import BytesIO
import json
import math
from pathlib import Path
import subprocess
from PIL import Image
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.build_jpeg_controls import controls


def rgb(v,sequence):
    y,cb,cr=v;cb-=128;cr-=128
    r=1.402*cr;g1=.344136*cb;g2=.714136*cr;b=1.772*cb
    if sequence=='floor-contributions': values=(y+math.floor(r),y-math.floor(g1)-math.floor(g2),y+math.floor(b))
    elif sequence=='truncate-contributions': values=(y+math.trunc(r),y-math.trunc(g1)-math.trunc(g2),y+math.trunc(b))
    elif sequence=='floor-total': values=(math.floor(y+r),math.floor(y-g1-g2),math.floor(y+b))
    elif sequence=='nearest-total': values=(math.floor(y+r+.5),math.floor(y-g1-g2+.5),math.floor(y+b+.5))
    else:raise ValueError(sequence)
    return [min(255,max(0,n)) for n in values]


def analyze(native,executable,output):
    build=json.loads((native/'build.json').read_text());generated=controls()
    assert build['cases']==[c for c,_ in generated]
    targets=[]
    for kind,data in events(native):
        if kind=='case':targets.append([])
        elif kind=='row':targets[-1].extend([[(v>>s)&255 for s in (16,8,0)] for v in map(int,data.split(',')[1:])])
        else:assert [kind,data]==['done','ok']
    output.mkdir(parents=True,exist_ok=True);rows=[]
    for (case,jpeg),target in zip(generated,targets):
        if case['mode']!='RGB' or case['subsampling']!=0:continue
        assert len(target)==1024
        path=output/f"{case['id']}.jpg";path.write_bytes(jpeg)
        p=subprocess.run([str(executable),str(path)],check=True,capture_output=True)
        image=Image.open(BytesIO(p.stdout));assert image.size==(32,32)
        values=list(image.getdata())
        (output/f"{case['id']}.ycbcr.ppm").write_bytes(p.stdout)
        for sequence in ('floor-contributions','truncate-contributions','floor-total','nearest-total'):
            failures=[]
            for i,(v,expected) in enumerate(zip(values,target)):
                actual=rgb(v,sequence)
                if actual!=expected:failures.append({'x':i%32,'y':i//32,'ycbcr':v,'candidate':actual,'native':expected,'delta':[a-b for a,b in zip(actual,expected)]})
            rows.append({'case':case,'sequence':sequence,'pixels':1024,'exact':1024-len(failures),
                         'max_channel_delta':max((max(map(abs,f['delta'])) for f in failures),default=0),'failures':failures})
    totals=Counter()
    for row in rows:totals[row['sequence']]+=row['exact']
    result={'rows':rows,'exact_by_sequence':dict(totals),'pixels_per_sequence':6144,
            'component_dump_executable_sha256':hashlib.sha256(executable.read_bytes()).hexdigest(),
            'production_admitted':False}
    (output/'summary.json').write_text(json.dumps(result,indent=2)+'\n');return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native',type=Path,required=True)
    parser.add_argument('--dump',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();result=analyze(args.native,args.dump,args.output);print(result['exact_by_sequence'])
