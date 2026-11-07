"""Resolve only s348's first opaque call through the pinned Mach-O import tables."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TARGET = 0xfb680a


def load_macho():
    spec = importlib.util.spec_from_file_location('s358_macho', HERE.parent / 's303/audit_native.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def extract(raw):
    locked = json.loads((HERE.parent / 's303/native-audit.json').read_text())
    digest = hashlib.sha256(raw).hexdigest()
    if digest != locked['binary_sha256']:
        raise ValueError('binary differs from locked receipt')
    macho = load_macho()
    metadata = macho.macho(raw)
    if metadata != locked['module']:
        raise ValueError('Mach-O metadata differs')
    base = locked['image_base']
    spans = {}

    def span(name, offset, size):
        if offset < 0 or size < 0 or offset + size > len(raw):
            raise ValueError('out-of-file span: ' + name)
        data = raw[offset:offset + size]
        spans[name] = dict(file_offset=offset, size=size, hex=data.hex())
        return data

    prior = json.loads((HERE.parent / 's348/native-route.json').read_text())
    anchor = prior['regions']['exit_callee']
    data = span('retained_exit_callee', macho.file_offset(metadata, base + anchor['start'], 50), 50)
    if data.hex() != anchor['hex']:
        raise ValueError('retained s348 anchor differs')
    if data[17] != 0xe8 or anchor['start'] + 22 + struct.unpack_from('<i', data, 18)[0] != TARGET:
        raise ValueError('first call target differs')

    sections, symtab, dysymtab = [], None, None
    offset = 32
    for _ in range(struct.unpack_from('<I', raw, 16)[0]):
        command, size = struct.unpack_from('<II', raw, offset)
        if command == 0x19:
            for index in range(struct.unpack_from('<I', raw, offset + 64)[0]):
                position = offset + 72 + index * 80
                if position + 80 > offset + size:
                    raise ValueError('section outside segment command')
                address, length = struct.unpack_from('<QQ', raw, position + 32)
                if address <= base + TARGET < address + length:
                    sections.append((position, address, length))
        elif command == 2:
            symtab = struct.unpack_from('<4I', span('symtab_command', offset, size), 8)
        elif command == 11:
            dysymtab = struct.unpack_from('<18I', span('dysymtab_command', offset, size), 8)
        offset += size
    if len(sections) != 1 or symtab is None or dysymtab is None:
        raise ValueError('ambiguous or missing import metadata')
    position, address, length = sections[0]
    section = span('stub_section', position, 80)
    fileoff, _, _, _, flags, first, stride, _ = struct.unpack_from('<8I', section, 48)
    if flags & 0xff != 8 or stride != 6 or (base + TARGET - address) % stride:
        raise ValueError('target is not an aligned six-byte symbol stub')
    index = (base + TARGET - address) // stride
    indirect_index = first + index
    indirectoff, indirectcount = dysymtab[12:14]
    if indirect_index >= indirectcount:
        raise ValueError('indirect index outside table')
    symbol_index = struct.unpack('<I', span('indirect_entry', indirectoff + 4 * indirect_index, 4))[0]
    symoff, nsyms, stroff, strsize = symtab
    if symbol_index >= nsyms:
        raise ValueError('special or invalid indirect symbol index')
    nlist = span('symbol_entry', symoff + 16 * symbol_index, 16)
    string_index, symbol_type, sect, desc, value = struct.unpack('<IBBHQ', nlist)
    if string_index >= strsize:
        raise ValueError('symbol string outside table')
    start = stroff + string_index
    end = raw.find(b'\0', start, stroff + strsize)
    if end < 0:
        raise ValueError('unterminated symbol')
    symbol = span('symbol_string', start, end + 1 - start)[:-1].decode('ascii')
    stub = span('first_stub', fileoff + index * stride, stride)
    if stub[:2] != b'\xff\x25':
        raise ValueError('unexpected stub instruction')
    pointer = TARGET + 6 + struct.unpack_from('<i', stub, 2)[0]
    return dict(binary_sha256=digest, binary_size=len(raw), module_uuid=metadata['uuid'],
                image_base=base, first_call_target=TARGET, stub_index=index,
                indirect_index=indirect_index, symbol_index=symbol_index,
                symbol=symbol, symbol_type=symbol_type, symbol_section=sect,
                symbol_description=desc, symbol_value=value,
                pointer_slot_module_relative=pointer, spans=spans,
                kind='static_import_association_not_executed_or_consumed_bytes',
                live_pointer_value=None, loaded_provider=None, live_request_resolver=None,
                new_player_launches=0, new_attaches=0, new_memory_reads=0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    receipt = json.loads((HERE.parent / 's266/native-receipt.json').read_text())
    binary = args.binary or Path(receipt['engine'])
    record = extract(binary.read_bytes())
    args.output.write_text(json.dumps(record, indent=2) + '\n')
    print('S358_IMPORT_ASSOCIATION_EXTRACTED ' + record['symbol'] + '; live binding unproved')


if __name__ == '__main__':
    main()
