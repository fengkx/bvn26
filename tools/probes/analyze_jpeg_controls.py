"""Reject common decoder modes against independent native JPEG controls."""
import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path
import subprocess
from PIL import Image
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.build_jpeg_controls import controls


def analyze(native, executable, output):
    build=json.loads((native/'build.json').read_text())
    generated=controls()
    assert build['cases']==[c for c,_ in generated]
    captured=[]
    for kind,data in events(native):
        if kind=='case':
            i,w,h,transparent=data.split(',')
            assert [int(i),int(w),int(h),transparent]==[len(captured),32,32,'false']
            captured.append([])
        elif kind=='row':
            values=list(map(int,data.split(',')))
            assert values[0]==len(captured[-1])//32 and len(values)==33
            for value in values[1:]:
                assert (value>>24)&255==255
                captured[-1].append([(value>>s)&255 for s in (16,8,0)])
        else:assert [kind,data]==['done','ok']
    assert len(captured)==16 and all(len(r)==1024 for r in captured)
    output.mkdir(parents=True,exist_ok=True)
    rows=[]
    for (case,jpeg),target in zip(generated,captured):
        path=output/f"{case['id']}.jpg";path.write_bytes(jpeg)
        for dct in ('int','fast','float'):
            for smooth in (True,False):
                command=[str(executable),'-strict','-rgb','-dct',dct]+([] if smooth else ['-nosmooth'])
                p=subprocess.run(command+[str(path)],check=True,capture_output=True)
                actual=list(Image.open(BytesIO(p.stdout)).convert('RGB').getdata())
                failures=[{'x':i%32,'y':i//32,'candidate':list(a),'native':b,'delta':[v-w for v,w in zip(a,b)]}
                          for i,(a,b) in enumerate(zip(actual,target)) if list(a)!=b]
                rows.append({'case':case,'dct':dct,'smooth':smooth,'pixels':1024,'exact':1024-len(failures),
                             'max_channel_delta':max((max(map(abs,r['delta'])) for r in failures),default=0),
                             'failures':failures})
    result={'rows':rows,'native_pixels':16384,'decoder_executable_sha256':hashlib.sha256(executable.resolve().read_bytes()).hexdigest(),
            'production_admitted':False}
    (output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native',type=Path,required=True)
    parser.add_argument('--djpeg',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();result=analyze(args.native,args.djpeg,args.output)
    for row in result['rows']:print(row['case']['id'],row['case']['pattern'],row['case']['subsampling'],row['case']['quality'],row['dct'],row['smooth'],row['exact'],row['max_channel_delta'])
