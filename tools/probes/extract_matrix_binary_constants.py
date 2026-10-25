"""Pin independently inspected matrix instructions; do not claim runtime invocation."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

PLAYER_SHA256 = '8d4c1f5934adae809b5f4ce4f6ca7c64d4260df46bb3eb9c41fe32be2ee905be'
CONSTANTS = {
    'coefficient_scale': (0x10106cb6c, '00000045'),
    'offset_scale': (0x10106cb70, '00008040'),
    'input_bias_words': (0x10106cb30, '7f00'*8),
    'premultiply_bias_words': (0x10106cae0, '0100'*8),
    'maximum_words': (0x10106cac0, 'ff00'*8),
    'alpha_mask_words': (0x10106cad0, '000000000000ff00'*2),
}
SPANS = {
    'coefficient_conversion': (0x100016999, 0x100016ae2),
    'offset_conversion': (0x100016ae2, 0x100016b46),
    'pair_alpha_and_input': (0x100017d70, 0x100017df9),
    'term_products_and_premultiply': (0x100017df9, 0x100017e9f),
    'scalar_remainder': (0x100018030, 0x100018101),
    'scalar_unpremultiply': (0x100153680, 0x1001536e5),
    'reciprocal_table_initialization': (0x1001f3d9a, 0x1001f3ded),
}


def extract(path):
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != PLAYER_SHA256:
        raise ValueError('Unreviewed native player binary')
    assert data[:4] == bytes.fromhex('cffaedfe')
    segments = []
    position = 32
    for _ in range(struct.unpack_from('<I', data, 16)[0]):
        command, size = struct.unpack_from('<II', data, position)
        if command == 0x19:
            _, _, _, address, _, offset, length = struct.unpack_from('<II16sQQQQ', data, position)
            segments.append((address, offset, length))
        position += size

    def read(address, size):
        for base, offset, length in segments:
            if base <= address and address+size <= base+length:
                return data[offset+address-base:offset+address-base+size]
        raise ValueError('Address outside file-backed Mach-O segments')

    constants = {}
    for name, (address, expected) in CONSTANTS.items():
        raw = read(address, len(bytes.fromhex(expected)))
        assert raw.hex() == expected
        constants[name] = {'address': hex(address), 'bytes': raw.hex()}
    spans = {}
    for name, (start, end) in SPANS.items():
        raw = read(start, end-start)
        spans[name] = {'start': hex(start), 'end': hex(end), 'bytes': raw.hex(),
                       'sha256': hashlib.sha256(raw).hexdigest()}
    return {'binary_sha256': digest, 'constants': constants, 'instruction_spans': spans,
            'execution_routing_verified': False, 'production_admitted': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(json.dumps(extract(args.binary), indent=2)+'\n')
