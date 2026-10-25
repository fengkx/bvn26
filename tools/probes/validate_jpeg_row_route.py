"""Reject the independently measured eight-pixel route against original held-out bytes."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import struct
import zlib
from PIL import Image
from tools.probes.build_bound_bitmap_component import ROOT,source_tags
from tools.probes.build_jpeg_edge_widths import cases
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.run_nested_filters import unpack
from tools.probes.analyze_jpeg_row_partitions import routed_rgb


def validate(planes):
    evidence=ROOT/'evidence/importer-loud-fail/r217'
    prior=json.loads(gzip.decompress((evidence/'summary.json.gz').read_bytes()))
    generated=cases();assert [c for c,_,_ in generated]==json.loads((evidence/'native/build.json').read_text())['cases']
    targets=[]
    for kind,data in events(evidence/'native'):
        if kind=='case':targets.append([])
        elif kind=='row':targets[-1].extend(unpack(list(map(int,data.split(',')))[1:]))
    payload=next(p for c,p,_ in source_tags(ROOT/'game/fighter/orochimaru.swf') if c==35 and struct.unpack_from('<H',p)[0]==340)
    length=struct.unpack_from('<I',payload,2)[0];alpha=zlib.decompress(payload[6+length:])
    rows=[]
    for (case,_,_),target,old in zip(generated,targets,prior['rows']):
        folder=planes/f"case{case['id']}"
        paths=[folder/'scale1/c0.pgm',folder/'scale2/c1.pgm',folder/'scale2/c2.pgm']
        assert [hashlib.sha256(p.read_bytes()).hexdigest() for p in paths]==old['plane_sha256']
        images=[Image.open(p) for p in paths]
        assert all(im.size==(case['width'],378) for im in images)
        values=zip(*(im.getdata() for im in images));failures=[]
        for i,(v,expected) in enumerate(zip(values,target)):
            a=alpha[i] if case['tag']==35 else 255
            actual=routed_rgb(v,i%case['width'],case['width'],8)+[a] if a else [0]*4
            if actual!=expected:failures.append({'x':i%case['width'],'y':i//case['width'],'candidate':actual,'native':expected})
        rows.append({'case':case,'pixels':len(target),'exact':len(target)-len(failures),'failures':failures,'plane_sha256':old['plane_sha256']})
    return {'rows':rows,'pixels':sum(r['pixels'] for r in rows),'exact':sum(r['exact'] for r in rows),'production_admitted':False}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--planes',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();r=validate(args.planes);args.output.write_text(json.dumps(r,indent=2)+'\n');print(r['exact'],r['pixels'])
