"""Search a fixed set of AS2 route names in locked disk bytes, not live objects."""
import hashlib
import json
from pathlib import Path
import time
import struct

HERE = Path(__file__).resolve().parent
BINARY = Path('/Users/fengkx/me/code/flash-player/Flash Player.app/Contents/MacOS/Flash Player Debugger')
EXPECTED = '8d4c1f5934adae809b5f4ce4f6ca7c64d4260df46bb3eb9c41fe32be2ee905be'
ROUTES = {
    'parent_depth': ['_parent', 'getDepth', 'getInstanceAtDepth', 's261Parent', 's261Depth'],
    'saved_reference': ['s261Receiver'],
}


def search(data):
    rows = []
    for route, names in ROUTES.items():
        for name in names:
            for spelling in dict.fromkeys([name, name.lower()]):
                for encoding in ('ascii', 'utf-16-le'):
                    needle = spelling.encode(encoding)
                    offsets = []
                    start = 0
                    while (offset := data.find(needle, start)) >= 0:
                        offsets.append(offset)
                        start = offset + 1
                    rows.append(dict(route=route, source_name=name, spelling=spelling,
                                     encoding=encoding, needle_hex=needle.hex(),
                                     file_offsets=offsets))
    return rows


def collect():
    started = time.monotonic()
    data = BINARY.read_bytes()
    if hashlib.sha256(data).hexdigest() != EXPECTED:
        raise ValueError('Player differs from retained s325 binary')
    rows = search(data)
    sections = []
    if struct.unpack_from('<I', data)[0] != 0xfeedfacf:
        raise ValueError('Expected Mach-O 64')
    command = 32
    for _ in range(struct.unpack_from('<I', data, 16)[0]):
        kind, size = struct.unpack_from('<II', data, command)
        if kind == 0x19:
            for index in range(struct.unpack_from('<I', data, command+64)[0]):
                name, segment, address, length, offset = struct.unpack_from(
                    '<16s16sQQI', data, command+72+index*80)
                sections.append((segment.rstrip(b'\0').decode(), name.rstrip(b'\0').decode(),
                                 address, length, offset))
        command += size
    contexts = []
    for offset in sorted({o for row in rows for o in row['file_offsets']}):
        segment, section, address, length, file_start = next(
            s for s in sections if s[4] <= offset < s[4]+s[3])
        start, end = max(file_start, offset-48), min(file_start+length, offset+96)
        contexts.append(dict(file_offset=offset, segment=segment, section=section,
                             unslid_address=hex(address+offset-file_start),
                             context_start=start, context_hex=data[start:end].hex()))
    return dict(binary=str(BINARY), binary_sha256=EXPECTED, binary_size=len(data),
                search_kind='exact substring bytes; lowercase is a search variant, not an alias',
                rows=rows, contexts=contexts, wall_seconds=time.monotonic()-started,
                independent_native_observations=0, live_binding=None,
                limitation='Finite names/encodings only. Absence does not exclude encoded, interned, runtime-created or indirect lookup paths. A hit is not executable code, a resolver, a layout or a referent.')


if __name__ == '__main__':
    (HERE/'lookup-candidates.json').write_text(json.dumps(collect(), indent=2)+'\n')
