"""Bound a name-to-entry derivation attempt in the locked disk binary only."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct

HERE = Path(__file__).resolve().parent


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def occurrences(raw, needle):
    result, start = [], 0
    while True:
        offset = raw.find(needle, start)
        if offset < 0:
            return result
        result.append(offset)
        start = offset + 1


def extract(raw):
    locked = json.loads((HERE.parent / 's303/native-audit.json').read_text())
    if sha(raw) != locked['binary_sha256']:
        raise ValueError('binary differs from locked receipt')
    spec = importlib.util.spec_from_file_location('s337_macho', HERE.parent / 's303/audit_native.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    metadata = module.macho(raw)
    if metadata != locked['module']:
        raise ValueError('Mach-O metadata differs')
    rows = []
    needle = b'\0gotoAndStop\0'
    for offset in occurrences(raw, needle):
        name_offset = offset + 1
        segments = [s for s in metadata['segments'] if s['fileoff'] <= name_offset
                    and name_offset + len(needle) - 1 <= s['fileoff'] + s['filesize']]
        if len(segments) != 1:
            raise ValueError('name lacks unique file mapping')
        segment = segments[0]
        address = segment['vmaddr'] + name_offset - segment['fileoff']
        pointer = struct.pack('<Q', address)
        rows.append(dict(file_offset=name_offset, segment=segment['name'],
                         unslid_address=address, module_relative=address-locked['image_base'],
                         bounded_name_hex=needle.hex(), pointer_pattern_hex=pointer.hex(),
                         pointer_pattern_file_offsets=occurrences(raw, pointer)))
    return dict(binary_sha256=sha(raw), binary_size=len(raw), module_uuid=metadata['uuid'],
                image_base=locked['image_base'], name='gotoAndStop', matches=rows,
                search='Exact NUL-delimited name, then each unslid address as eight little-endian bytes across the disk file. No instruction decoding or relocation interpretation.',
                native_entry_site=None, outer_instance_lifetime_channel=None,
                limitation='Name bytes and address patterns are not executable references, a registration table, a function entry, or allocation identity. Relative/computed references are outside this bounded search. Absence is not impossibility.',
                new_player_launches=0, new_attaches=0, new_memory_reads=0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('binary', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(json.dumps(extract(args.binary.read_bytes()), indent=2) + '\n')
    print('S337_DISK_SEARCH_OK; target entry and lifetime remain unproved')


if __name__ == '__main__':
    main()
