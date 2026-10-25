"""Build continuous indexed/AS spans with long bitmap headers and native source readback."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import uuid
import zlib
from tools.probes.build_indexed_alpha_scalar import build as alpha_build
from tools.probes.build_bound_bitmap_component import ROOT,source_tags
from tools.probes.build_minimal_swf import tag
from tools.probes.inventory_bitmap_roundtrip import decode_lossless
from tools.probes.build_indexed_long_header import force_long

HARNESS=Path('tools/probes/flash_filters/indexed-bitmap-spans.as')


def build(output,ffdec):
    report=alpha_build(output,ffdec);native=output/'components/lanran';run='indexed-spans-'+uuid.uuid4().hex[:12]
    before=list(source_tags(native/'game/main.swf'));bitmap=next(p for code,p,_ in before if code==36 and struct.unpack_from('<H',p)[0]==7);cid,w,h,raw=decode_lossless(bitmap)
    script=(ROOT/HARNESS).read_text().replace('RUN',run).replace('SOURCE_BYTES',json.dumps([(a<<24)|(r<<16)|(g<<8)|b for r,g,b,a in raw],separators=(',',':')))
    (native/'scripts/frame_1/DoAction.as').write_text(script);shutil.copyfile(native/'game/main.swf',native/'variant-base.swf')
    subprocess.run(['java',f'-Duser.home={output}','-Djava.awt.headless=true','-jar',str(ffdec),'-importScript',str(native/'variant-base.swf'),str(native/'game/main.swf'),str(native/'scripts')],check=True,stdout=subprocess.DEVNULL)
    path=native/'game/main.swf';original=path.read_bytes();body=original[8:] if original[:3]==b'FWS' else zlib.decompress(original[8:]);offset=(5+4*(body[0]>>3)+7)//8+4;records=list(source_tags(path));index=next(i for i,v in enumerate(records) if v[0]==12)
    assert next(p for code,p,_ in records if code==36 and struct.unpack_from('<H',p)[0]==7)==bitmap
    changed=body[:offset]+b''.join((tag(56,struct.pack('<HH',1,7)+b'indexedSource\0') if i==index else b'')+v[2] for i,v in enumerate(records));path.write_bytes(b'FWS'+original[3:4]+struct.pack('<I',len(changed)+8)+changed)
    header=force_long(path)
    report.update({'header_intervention':header,'run_id':run,'harness_source':str(HARNESS),'harness_sha256':hashlib.sha256((ROOT/HARNESS).read_bytes()).hexdigest(),'indexed_export':{'bitmap_id':7,'name':'indexedSource','bitmap_payload_sha256':hashlib.sha256(bitmap).hexdigest()},'outputs_sha256':{'game/main.swf':hashlib.sha256(path.read_bytes()).hexdigest()}})
    (native/'build.json').write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--ffdec',type=Path,required=True);a=p.parse_args();r=build(a.output.resolve(),a.ffdec.resolve());print(r['run_id'])
