"""Read static candidate bytes from the installed native player, without execution."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

ADDRESSES = {'maximum':0x1010870d0,'normalizer':0x1010870e0,
             'denominator_bias':0x1010870f0,'multiplier_scale':0x101085890}
EXPECTED = {'maximum':0x437f0000,'normalizer':0x3b808081,
            'denominator_bias':0x37808081,'multiplier_scale':0x3b800000}


def extract(path):
    data = path.read_bytes()
    if data[:4]!=bytes.fromhex('cffaedfe'):
        raise ValueError('Expected little-endian 64-bit Mach-O')
    segments = []
    position = 32
    for _ in range(struct.unpack_from('<I',data,16)[0]):
        command,size = struct.unpack_from('<II',data,position)
        if command==0x19:
            _,_,_,address,_,offset,length = struct.unpack_from('<II16sQQQQ',data,position)
            segments.append((address,offset,length))
        position += size
    def read(address,size):
        for base,offset,length in segments:
            if base<=address and address+size<=base+length:
                return data[offset+address-base:offset+address-base+size]
        raise ValueError('Static address is outside file-backed segments')
    constants = {}
    for name,address in ADDRESSES.items():
        raw = read(address,4)
        bits = struct.unpack('<I',raw)[0]
        if bits!=EXPECTED[name]:
            raise ValueError('Native binary constant differs from inspected build')
        constants[name] = {'address':hex(address),'bits':bits,'bytes':raw.hex()}
    spans = {}
    for name,start,end in (('parameter_loads',0x1001fc3b7,0x1001fc465),
                           ('color_arithmetic',0x1001fc51b,0x1001fc594),
                           ('integer_conversion',0x1001fc5bc,0x1001fc5ef)):
        raw = read(start,end-start)
        spans[name] = {'start':hex(start),'end':hex(end),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':raw.hex()}
    return {'binary_path':str(path),'binary_sha256':hashlib.sha256(data).hexdigest(),
            'constants':constants,'instruction_spans':spans,'execution_routing_verified':False,
            'scope':'Static candidate only; no runtime invocation inferred from disassembly.'}


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    args.output.write_text(json.dumps(extract(args.binary),indent=2)+'\n')
