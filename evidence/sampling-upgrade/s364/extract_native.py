"""Inspect packed method-name containers without assigning runtime identities."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RECEIPT = 'evidence/sampling-upgrade/s303/native-audit.json'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def occurrences(raw, needle):
    result, start = [], 0
    while True:
        start = raw.find(needle, start)
        if start < 0:
            return result
        result.append(start)
        start += 1


def sections(raw):
    result, pos = [], 32
    for _ in range(struct.unpack_from('<I', raw, 16)[0]):
        cmd, size = struct.unpack_from('<II', raw, pos)
        if size < 8 or pos + size > len(raw):
            raise ValueError('invalid load command')
        if cmd == 0x19:
            for i in range(struct.unpack_from('<I', raw, pos + 64)[0]):
                p = pos + 72 + 80 * i
                if p + 80 > pos + size:
                    raise ValueError('section outside command')
                name = raw[p:p + 16].split(b'\0')[0].decode('ascii')
                segment = raw[p + 16:p + 32].split(b'\0')[0].decode('ascii')
                address, length, offset = struct.unpack_from('<QQI', raw, p + 32)
                result.append(dict(name=name, segment=segment, address=address,
                                   size=length, file_offset=offset))
        pos += size
    return result


def extract(raw):
    receipt = json.loads((ROOT / RECEIPT).read_text())
    if sha(raw) != receipt['binary_sha256']:
        raise ValueError('binary differs from pinned receipt')
    spec = importlib.util.spec_from_file_location('s364_macho', HERE.parent / 's303/audit_native.py')
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    metadata = m.macho(raw)
    if metadata != receipt['module']:
        raise ValueError('module metadata differs')
    table = sections(raw)
    needle = b'gotoAndStop'
    matches = occurrences(raw, needle)
    contexts, candidates = [], []
    for offset in matches:
        start, end = raw.rfind(b'\0', 0, offset) + 1, raw.find(b'\0', offset)
        contexts.append(dict(file_offset=offset, context_start=offset - 16,
                             context_hex=raw[offset - 16:offset + len(needle) + 16].hex()))
        # Select only an entire comma-delimited member in a printable container.
        # Nearby byte values are not treated as an ABC or registration schema.
        container = raw[start:end]
        if end >= 0 and all(32 <= byte < 127 for byte in container) and needle in container.split(b','):
            candidates.append((start, end, container))
    if len(candidates) != 1:
        raise ValueError('expected one printable comma-delimited container')
    start, end, container = candidates[0]
    owners = [s for s in table if s['file_offset'] <= start and end < s['file_offset'] + s['size']]
    if len(owners) != 1:
        raise ValueError('ambiguous container section')
    owner = owners[0]
    address = owner['address'] + start - owner['file_offset']
    code = [s for s in table if s['segment'] == '__TEXT' and s['name'] == '__text']
    if len(code) != 1:
        raise ValueError('ambiguous code section')
    code = code[0]
    refs = []
    for p in range(code['file_offset'], code['file_offset'] + code['size'] - 6):
        if raw[p] in (0x48, 0x4c) and raw[p + 1] == 0x8d and raw[p + 2] & 0xc7 == 5:
            pc = code['address'] + p - code['file_offset']
            if pc + 7 + struct.unpack_from('<i', raw, p + 3)[0] == address:
                refs.append(dict(file_offset=p, address=pc, hex=raw[p:p + 7].hex()))
    members = container.decode('ascii').split(',')
    return dict(binary_receipt=RECEIPT, binary_sha256=sha(raw), binary_size=len(raw),
                module_uuid=metadata['uuid'], image_base=receipt['image_base'],
                ascii_matches=contexts,
                alternate_encoding_matches={enc: occurrences(raw, 'gotoAndStop'.encode(enc))
                                            for enc in ('utf-16le', 'utf-16be')},
                container=dict(file_offset=start, end_exclusive=end, hex=container.hex(),
                               sha256=sha(container), section=owner, address=address,
                               members=members, method_member_index=members.index('gotoAndStop'),
                               removal_name_member_index=members.index('removeMovieClip')),
                reference_search=dict(target=address, code_section=code,
                                      rip_lea_candidates=refs,
                                      exact_u64_file_offsets=occurrences(raw, struct.pack('<Q', address)),
                                      boundary='Only container start; seven-byte REX.W LEA RIP encodings in __text and exact little-endian u64 across disk. Not decoded instructions or exhaustive references.'),
                method_registration=None, loaded_method=None, frame_entry=None,
                independent_outer_lifetime=None,
                limitation='Packed names are disk text only. No opcode, text, address, helper or glyph is an executable or outer-generation identity.')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--binary', type=Path)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    receipt = json.loads((ROOT / RECEIPT).read_text())
    result = extract((args.binary or Path(receipt['binary'])).read_bytes())
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print('S364_PACKED_NAME_ROUTE_RECORDED; loaded entry and lifetime unproved')


if __name__ == '__main__':
    main()
