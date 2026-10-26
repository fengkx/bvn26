"""Change only a scratch bitmap tag's encoding, preserving decoded bytes and every other tag."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import zlib
from tools.probes.build_component_fill_api import build as fill_build
from tools.probes.build_bound_bitmap_component import ROOT,source_tags
from tools.probes.build_minimal_swf import tag
from tools.probes.inventory_bitmap_roundtrip import decode_lossless


def rewrite(path,bitmap_id):
    path=path.resolve()
    if any(p==path or p in path.parents for p in (ROOT/'game',ROOT/'scripts')):raise ValueError('Cannot rewrite locked source')
    original=path.read_bytes();body=original[8:] if original[:3]==b'FWS' else zlib.decompress(original[8:]);offset=(5+4*(body[0]>>3)+7)//8+4
    records=list(source_tags(path));targets=[(i,p) for i,(code,p,_) in enumerate(records) if code==36 and struct.unpack_from('<H',p)[0]==bitmap_id];assert len(targets)==1
    index,payload=targets[0];assert payload[2]==3;cid,w,h,pixels=decode_lossless(payload)
    argb=bytes(c for r,g,b,a in pixels for c in (a,r,g,b));replacement=struct.pack('<HBHH',cid,5,w,h)+zlib.compress(argb)
    assert decode_lossless(replacement)==(cid,w,h,pixels)
    updated=body[:offset]+b''.join(tag(36,replacement) if i==index else record[2] for i,record in enumerate(records))
    path.write_bytes(b'FWS'+original[3:4]+struct.pack('<I',len(updated)+8)+updated)
    after=list(source_tags(path));assert len(after)==len(records)
    unchanged=[r[2] for i,r in enumerate(records) if i!=index]
    assert [r[2] for i,r in enumerate(after) if i!=index]==unchanged
    assert after[index][0]==36 and decode_lossless(after[index][1])==(cid,w,h,pixels)
    sha=lambda value:hashlib.sha256(value).hexdigest()
    return {'bitmap_id':cid,'width':w,'height':h,'before_format':3,'after_format':5,'decoded_rgba_sha256':sha(bytes(c for p in pixels for c in p)),'before_swf_sha256':sha(original),'after_swf_sha256':sha(path.read_bytes()),'before_bitmap_tag_sha256':sha(records[index][2]),'after_bitmap_tag_sha256':sha(after[index][2]),'unchanged_tag_count':len(unchanged),'unchanged_tags_sha256':sha(b''.join(unchanged)),'all_other_tags_byte_identical':True}


def build(output,ffdec):
    report=fill_build(output,ffdec);native=output/'components/lanran';variant=rewrite(native/'game/main.swf',7)
    report['encoding_variant']=variant;report['outputs_sha256']['game/main.swf']=variant['after_swf_sha256']
    (native/'build.json').write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--ffdec',type=Path,required=True);a=p.parse_args();r=build(a.output.resolve(),a.ffdec.resolve());print(json.dumps(r['encoding_variant'],indent=2))
