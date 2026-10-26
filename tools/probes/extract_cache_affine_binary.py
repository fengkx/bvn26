"""Pin static affine instructions; this does not prove cache execution routing."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

BINARY_SHA256 = '8d4c1f5934adae809b5f4ce4f6ca7c64d4260df46bb3eb9c41fe32be2ee905be'
SPANS = {
    'fixed_compose_translation': (0x10029db0e, 0x10029db56),
    'float_inverse_axis': (0x10029df25, 0x10029df79),
    'fixed_inverse_axis': (0x10029e02f, 0x10029e0fe),
}


def extract(path):
    data = path.read_bytes()
    assert hashlib.sha256(data).hexdigest() == BINARY_SHA256
    assert data[:4] == bytes.fromhex('cffaedfe')
    segments = []
    position = 32
    for _ in range(struct.unpack_from('<I',data,16)[0]):
        command,size = struct.unpack_from('<II',data,position)
        if command == 0x19:
            _,_,_,address,_,offset,length = struct.unpack_from('<II16sQQQQ',data,position)
            segments.append((address,offset,length))
        position += size
    spans = {}
    for name,(start,end) in SPANS.items():
        matches = [(offset+start-base,end-start) for base,offset,length in segments if base<=start and end<=base+length]
        assert len(matches) == 1
        offset,length = matches[0]
        raw = data[offset:offset+length]
        spans[name] = {'start':hex(start),'end':hex(end),'bytes':raw.hex(),'sha256':hashlib.sha256(raw).hexdigest()}
    return {'binary_sha256':BINARY_SHA256,'spans':spans,'execution_routing_verified':False,
            'scope':'Static affine candidate; no claim that the cache probe executes these branches.'}


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--binary',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();a.output.write_text(json.dumps(extract(a.binary),indent=2)+'\n')
