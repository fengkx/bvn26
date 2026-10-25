"""Change only the scratch bitmap tag header from short to long, retaining payload and all other tags."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import zlib
from tools.probes.build_indexed_bitmap_readback import build as readback_build
from tools.probes.build_bound_bitmap_component import ROOT,source_tags
from tools.probes.native_lossless_tag import lossless2_tag


def force_long(path):
    path=path.resolve()
    if any(p==path or p in path.parents for p in (ROOT/'game',ROOT/'scripts')):raise ValueError('Cannot rewrite locked source')
    original=path.read_bytes();body=original[8:] if original[:3]==b'FWS' else zlib.decompress(original[8:]);offset=(5+4*(body[0]>>3)+7)//8+4;records=list(source_tags(path));indices=[i for i,(c,p,_) in enumerate(records) if c==36 and struct.unpack_from('<H',p)[0]==7];assert len(indices)==1;index=indices[0];code,payload,old=records[index]
    assert len(payload)<63 and len(old)==len(payload)+2
    replacement=lossless2_tag(payload)
    updated=body[:offset]+b''.join(replacement if i==index else v[2] for i,v in enumerate(records));path.write_bytes(b'FWS'+original[3:4]+struct.pack('<I',len(updated)+8)+updated);after=list(source_tags(path))
    assert [(c,p) for c,p,_ in after]==[(c,p) for c,p,_ in records]
    assert [r for i,(_,_,r) in enumerate(after) if i!=index]==[r for i,(_,_,r) in enumerate(records) if i!=index]
    sha=lambda b:hashlib.sha256(b).hexdigest()
    return {'bitmap_id':7,'payload_bytes':len(payload),'payload_sha256':sha(payload),'before_header_bytes':2,'after_header_bytes':6,'other_tags_byte_identical':True,'other_tag_count':len(records)-1,'before_swf_sha256':sha(original),'after_swf_sha256':sha(path.read_bytes())}


def build(output,ffdec):
    report=readback_build(output,ffdec);native=output/'components/lanran';proof=force_long(native/'game/main.swf');report['header_intervention']=proof;report['outputs_sha256']['game/main.swf']=proof['after_swf_sha256'];(native/'build.json').write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--ffdec',type=Path,required=True);a=p.parse_args();r=build(a.output.resolve(),a.ffdec.resolve());print(json.dumps(r['header_intervention'],indent=2))
