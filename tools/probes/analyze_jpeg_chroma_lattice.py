"""Test fixed chroma lattice coordinates and rounding without output-selected paths."""
import argparse
from io import BytesIO
import json
import math
from pathlib import Path
import subprocess
from PIL import Image
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.build_jpeg_controls import controls
from tools.probes.analyze_jpeg_color_sequences import rgb


def interpolate(values,width,height,x,y,channel,alignment,rounding):
    u=x/2+alignment;v=y/2+alignment
    ix=math.floor(u);iy=math.floor(v);fx=u-ix;fy=v-iy
    def sample(px,py):return values[min(height-1,max(0,py))*width+min(width-1,max(0,px))][channel]
    top=sample(ix,iy)*(1-fx)+sample(ix+1,iy)*fx
    bottom=sample(ix,iy+1)*(1-fx)+sample(ix+1,iy+1)*fx
    value=top*(1-fy)+bottom*fy
    if rounding=='floor':return math.floor(value)
    if rounding=='nearest':return math.floor(value+.5)
    if rounding=='continuous':return value
    raise ValueError(rounding)


def analyze(native,executable,output):
    generated=controls();build=json.loads((native/'build.json').read_text());assert build['cases']==[c for c,_ in generated]
    targets=[]
    for kind,data in events(native):
        if kind=='case':targets.append([])
        elif kind=='row':targets[-1].extend([[(v>>s)&255 for s in (16,8,0)] for v in map(int,data.split(',')[1:])])
    output.mkdir(parents=True,exist_ok=True);rows=[]
    for (case,jpeg),target in zip(generated,targets):
        if case['subsampling']!=2:continue
        path=output/f"{case['id']}.jpg";path.write_bytes(jpeg)
        p=subprocess.run([str(executable),str(path)],check=True,capture_output=True)
        values=list(Image.open(BytesIO(p.stdout)).getdata());assert len(values)==1024
        lattice=[values[y*32+x] for y in range(0,32,2) for x in range(0,32,2)]
        assert all(values[y*32+x][1:]==lattice[(y//2)*16+x//2][1:] for y in range(32) for x in range(32))
        (output/f"{case['id']}.ycbcr.ppm").write_bytes(p.stdout)
        for alignment in (0,-.25):
            for rounding in ('floor','nearest','continuous'):
                failures=[]
                for i,expected in enumerate(target):
                    x=i%32;y=i//32
                    v=[values[i][0]]+[interpolate(lattice,16,16,x,y,c,alignment,rounding) for c in (1,2)]
                    actual=rgb(v,'floor-contributions')
                    if actual!=expected:failures.append({'x':x,'y':y,'ycbcr':v,'candidate':actual,'native':expected,'delta':[a-b for a,b in zip(actual,expected)]})
                rows.append({'case':case,'alignment':alignment,'rounding':rounding,'pixels':1024,'exact':1024-len(failures),
                             'max_channel_delta':max((max(map(abs,f['delta'])) for f in failures),default=0),'failures':failures})
    result={'rows':rows,'production_admitted':False}
    (output/'summary.json').write_text(json.dumps(result,indent=2)+'\n');return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native',type=Path,required=True)
    parser.add_argument('--dump',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();result=analyze(args.native,args.dump,args.output)
    for r in result['rows']:print(r['case']['id'],r['alignment'],r['rounding'],r['exact'],r['max_channel_delta'])
