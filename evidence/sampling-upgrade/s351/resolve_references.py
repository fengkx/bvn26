"""Attempt address references to locked s343 text; never infer a resolver from data."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

HERE = Path(__file__).resolve().parent


def references(raw, address):
    needle = struct.pack('<Q', address)
    hits, start = [], 0
    while (offset := raw.find(needle, start)) >= 0:
        hits.append(offset)
        start = offset + 1
    return hits


def extract(raw):
    locked = json.loads((HERE.parent / 's343/lookup-candidates.json').read_text())
    digest = hashlib.sha256(raw).hexdigest()
    if digest != locked['binary_sha256']:
        raise ValueError('Player differs from locked s343 receipt')
    if raw[:8] != bytes.fromhex('cffaedfe07000001'):
        raise ValueError('Expected x86_64 Mach-O')
    count, size = struct.unpack_from('<II', raw, 16)
    offset, sections, dyld = 32, [], []
    for _ in range(count):
        kind, length = struct.unpack_from('<II', raw, offset)
        if length < 8 or offset + length > 32 + size:
            raise ValueError('Invalid load command')
        if kind == 0x19:
            for i in range(struct.unpack_from('<I', raw, offset + 64)[0]):
                pos = offset + 72 + i * 80
                name, segment, addr, length_, fileoff, align, reloff, nreloc, flags = struct.unpack_from('<16s16sQQIIIII', raw, pos)
                sections.append(dict(segment=segment.rstrip(b'\0').decode(),
                                     section=name.rstrip(b'\0').decode(), address=addr,
                                     size=length_, file_offset=fileoff, relocation_offset=reloff,
                                     relocation_count=nreloc, flags=flags,
                                     section_header_hex=raw[pos:pos + 80].hex()))
        if kind in (0x22, 0x80000022):
            dyld.append(dict(command=kind, fields=list(struct.unpack_from('<10I', raw, offset + 8)),
                             interpreted=False))
        offset += length
    if offset != 32 + size:
        raise ValueError('Incomplete load commands')
    targets = []
    for context in locked['contexts']:
        start = context['context_start']
        value = bytes.fromhex(context['context_hex'])
        if raw[start:start + len(value)] != value:
            raise ValueError('Locked context differs')
        address = int(context['unslid_address'], 16)
        targets.append(dict(address=address, file_offset=context['file_offset'],
                            absolute_u64_occurrences=references(raw, address)))
    return dict(binary_sha256=digest, binary_size=len(raw),
                load_commands_hex=raw[:32 + size].hex(), sections=sections,
                section_relocation_count=sum(s['relocation_count'] for s in sections),
                dyld_info=dyld, targets=targets,
                method='All byte alignments, exact little-endian u64 address equality to five locked s343 locations; section relocation metadata only',
                executable_association=None, saved_reference_dereference=None,
                live_generations=None, controls_executed=False,
                limitation='No RIP-relative, relative table, dyld rebase/bind stream or enclosing-list-base resolution. No hits cannot prove no references. Section relocation absence is not absence of dynamic fixups.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    record = extract(args.binary.read_bytes())
    if args.check and record != json.loads((HERE / 'reference-attempt.json').read_text()):
        raise ValueError('Reference attempt changed')
    if args.output:
        args.output.write_text(json.dumps(record, indent=2) + '\n')
    print('S351_REFERENCE_ATTEMPT_OK; executable association and saved dereference unproved')


if __name__ == '__main__':
    main()
