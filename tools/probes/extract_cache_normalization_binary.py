"""Pin cache-field setup and device-scale constants without asserting branch execution."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from tools.probes.extract_cache_affine_binary import BINARY_SHA256

SPANS = {
    'device_scale_constructor': (0x10015c991,0x10015c9ca),
    'origin_field_inverse': (0x10015e678,0x10015e6c8),
    'inverse_translation_store': (0x10015e795,0x10015e7cf),
    'float_axis_inverse': (0x10029df25,0x10029df69),
}


def extract(binary):
    data=binary.read_bytes();assert hashlib.sha256(data).hexdigest()==BINARY_SHA256
    segments=[];position=32
    for _ in range(struct.unpack_from('<I',data,16)[0]):
        command,size=struct.unpack_from('<II',data,position)
        if command==0x19:
            _,_,_,address,_,offset,length=struct.unpack_from('<II16sQQQQ',data,position);segments.append((address,offset,length))
        position+=size
    def read(start,length):
        offsets=[offset+start-base for base,offset,size in segments if base<=start and start+length<=base+size];assert len(offsets)==1
        return data[offsets[0]:offsets[0]+length]
    raw=read(0x10107ba48,4);assert raw==bytes.fromhex('cdcc4c3d')
    spans={}
    for name,(start,end) in SPANS.items():
        b=read(start,end-start);spans[name]={'start':hex(start),'end':hex(end),'bytes':b.hex(),'sha256':hashlib.sha256(b).hexdigest()}
    return {'binary_sha256':BINARY_SHA256,'device_scale_constant':{'address':'0x10107ba48','bits':'0x3d4ccccd','bytes':raw.hex()},'spans':spans,'specific_normalization_branch_verified':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--binary',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();a.output.write_text(json.dumps(extract(a.binary),indent=2)+'\n')
