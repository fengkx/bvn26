"""Build independent indexed/AS scalar sampling controls using identical binary-alpha four-corner texels."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import uuid
import zlib
from tools.probes.build_component_fill_api import build as fill_build
from tools.probes.build_bound_bitmap_component import ROOT,source_tags
from tools.probes.build_minimal_swf import tag
from tools.probes.inventory_bitmap_roundtrip import decode_lossless

HARNESS=Path('tools/probes/flash_filters/indexed-bitmap-scalar.as')


def build(output,ffdec):
    report=fill_build(output,ffdec);native=output/'components/lanran';run='indexed-alpha-'+uuid.uuid4().hex[:12]
    palette=[[0,0,0,0],[255,0,0,255],[0,255,0,255],[0,0,255,255]]
    raw=[palette[y%2*2+x%2] for y in range(65) for x in range(35)]
    indices=bytes(v for y in range(65) for v in [*(y%2*2+x%2 for x in range(35)),0])
    payload=struct.pack('<HBHHB',7,3,35,65,len(palette)-1)+zlib.compress(bytes(c for p in palette for c in p)+indices)
    assert decode_lossless(payload)==(7,35,65,raw)
    script=(ROOT/HARNESS).read_text().replace('RUN',run).replace('SOURCE_BYTES',json.dumps([(a<<24)|(r<<16)|(g<<8)|b for r,g,b,a in raw],separators=(',',':')))
    (native/'scripts/frame_1/DoAction.as').write_text(script)
    subprocess.run(['java',f'-Duser.home={output}','-Djava.awt.headless=true','-jar',str(ffdec),'-importScript',str(native/'base.swf'),str(native/'game/main.swf'),str(native/'scripts')],check=True,stdout=subprocess.DEVNULL)
    path=native/'game/main.swf';original=path.read_bytes();body=original[8:] if original[:3]==b'FWS' else zlib.decompress(original[8:]);offset=(5+4*(body[0]>>3)+7)//8+4;records=list(source_tags(path));targets=[i for i,(code,p,_) in enumerate(records) if code==36 and struct.unpack_from('<H',p)[0]==7];assert len(targets)==1;index=targets[0]
    changed=body[:offset]+b''.join(tag(36,payload) if i==index else v[2] for i,v in enumerate(records));path.write_bytes(b'FWS'+original[3:4]+struct.pack('<I',len(changed)+8)+changed);after=list(source_tags(path))
    assert [v[2] for i,v in enumerate(after) if i!=index]==[v[2] for i,v in enumerate(records) if i!=index]
    assert decode_lossless(after[index][1])==(7,35,65,raw)
    report.update({'run_id':run,'harness_source':str(HARNESS),'harness_sha256':hashlib.sha256((ROOT/HARNESS).read_bytes()).hexdigest(),'synthetic_source':{'bitmap_id':7,'format':3,'width':35,'height':65,'pattern':'binary_alpha_four_corners','raw_rgba_sha256':hashlib.sha256(bytes(c for p in raw for c in p)).hexdigest(),'palette':palette,'unchanged_other_tags':len(records)-1},'outputs_sha256':{'game/main.swf':hashlib.sha256(path.read_bytes()).hexdigest()}})
    (native/'build.json').write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--ffdec',type=Path,required=True);a=p.parse_args();r=build(a.output.resolve(),a.ffdec.resolve());print(r['run_id'])
