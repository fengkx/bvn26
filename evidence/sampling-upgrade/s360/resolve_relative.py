"""Bound RIP-relative address formation; do not infer a native object resolver."""
import argparse
import bisect
import hashlib
import json
from pathlib import Path
import struct

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TARGETS = (0x10107C9C2, 0x10119EFE1)
# Instruction boundaries independently inspected with LLDB from LC_FUNCTION_STARTS.
LENGTHS = (1, 3, 2, 1, 3, 7, 3, 5, 3, 2, 2, 7, 3, 5, 2, 2, 7, 3, 5, 2, 2, 7, 3, 5, 3, 3, 1, 2, 1, 1)
EXPECTED_CODE = '554889e54156534889f3488d356f0014014889dfe887dcf9ff41b60184c07538488d3515f80d014889dfe871dcf9ff84c07525488d35e7f20d014889dfe85edcf9ff84c07512488d35f5f70d014889dfe84bdcf9ff4188c64488f05b415e5dc3'


def relative_candidates(raw, file_offset, address, size, targets):
    result = []
    for offset in range(file_offset, file_offset + size - 6):
        if raw[offset] not in (0x48, 0x4c) or raw[offset + 1] != 0x8d or raw[offset + 2] & 0xc7 != 5:
            continue
        displacement = struct.unpack_from('<i', raw, offset + 3)[0]
        pc = address + offset - file_offset
        target = pc + 7 + displacement
        if target in targets:
            result.append(dict(file_offset=offset, address=pc, target=target,
                               displacement=displacement, bytes_hex=raw[offset:offset + 7].hex()))
    return result


def function_starts(stream, base):
    starts, pos, current = [], 0, base
    while pos < len(stream):
        delta, shift = 0, 0
        while True:
            if pos >= len(stream) or shift > 63:
                raise ValueError('Invalid function-start ULEB')
            byte = stream[pos]
            pos += 1
            delta |= (byte & 127) << shift
            shift += 7
            if not byte & 128:
                break
        if not delta:
            return starts
        current += delta
        starts.append(current)
    raise ValueError('Missing function-start terminator')


def extract(raw):
    locked = json.loads((HERE.parent / 's351/reference-attempt.json').read_text())
    digest = hashlib.sha256(raw).hexdigest()
    if digest != locked['binary_sha256']:
        raise ValueError('Player differs from pinned receipt')
    text = next(s for s in locked['sections'] if s['section'] == '__text')
    # Load-command equality binds the retained section mapping to this disk image.
    header = bytes.fromhex(locked['load_commands_hex'])
    if raw[:len(header)] != header:
        raise ValueError('Section mapping changed')
    cursor, base, stream = 32, None, None
    for _ in range(struct.unpack_from('<I', raw, 16)[0]):
        kind, length = struct.unpack_from('<II', raw, cursor)
        if kind == 0x19 and raw[cursor + 8:cursor + 24].rstrip(b'\0') == b'__TEXT':
            base = struct.unpack_from('<Q', raw, cursor + 24)[0]
        if kind == 0x26:
            stream_offset, stream_size = struct.unpack_from('<II', raw, cursor + 8)
            stream = raw[stream_offset:stream_offset + stream_size]
        cursor += length
    if base is None or stream is None:
        raise ValueError('Missing function boundaries')
    starts = function_starts(stream, base)
    candidates = relative_candidates(raw, text['file_offset'], text['address'], text['size'], TARGETS)
    for candidate in candidates:
        index = bisect.bisect_right(starts, candidate['address']) - 1
        candidate['containing_function_start'] = starts[index]
        candidate['next_function_start'] = starts[index + 1]
        candidate['distance_from_start'] = candidate['address'] - starts[index]
        candidate['instruction_boundary_validated'] = False
    # Choose the shortest prefix to decode, not adjacency or assumed semantics.
    selected = min(candidates, key=lambda c: (c['distance_from_start'], c['address']))
    begin, end = selected['containing_function_start'], selected['next_function_start']
    offset = begin - text['address'] + text['file_offset']
    code = raw[offset:offset + end - begin]
    if code.hex() != EXPECTED_CODE or sum(LENGTHS) != len(code):
        raise ValueError('Selected code requires a new boundary audit')
    instructions, cursor = [], 0
    for length in LENGTHS:
        instructions.append(dict(address=begin + cursor, bytes_hex=code[cursor:cursor + length].hex()))
        cursor += length
    if selected['address'] not in [i['address'] for i in instructions]:
        raise ValueError('Candidate is not an instruction boundary')
    selected['instruction_boundary_validated'] = True
    return dict(binary_sha256=digest, binary_size=len(raw),
                method='Exact 7-byte REX.W LEA RIP+disp32 encodings at all alignments in __TEXT,__text for two locked addresses; no names or absolute-pointer search',
                search_section=text, targets=list(TARGETS), candidates=candidates,
                function_starts=dict(command='LC_FUNCTION_STARTS', file_offset=stream_offset,
                    size=stream_size, sha256=hashlib.sha256(stream).hexdigest(), base=base),
                selection_rule='Minimum distance from LC_FUNCTION_STARTS predecessor, then address',
                selected_function=dict(start=begin, end=end, bytes_hex=code.hex(), instructions=instructions),
                relative_code_association=dict(instruction_address=selected['address'],
                    next_rip=selected['address'] + 7, signed_displacement=selected['displacement'],
                    target=selected['target'], destination_register='rsi',
                    following_argument_move='rbx -> rdi', call_address=begin + 61,
                    call_target=begin + 66 + struct.unpack_from('<i', code, 62)[0]),
                parent_depth_resolver=None, saved_reference_dereference=None, live_generations=None,
                controls_executed=False,
                limitation='Only one candidate instruction boundary decoded; other hits remain byte-pattern candidates. LEA passes text address, not parent object. Callee semantics, depth lookup, saved-value representation and actual execution remain unknown. Other encodings, relative tables and enclosing-list bases are not searched.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    binary = args.binary or Path(json.loads((HERE.parent / 's343/lookup-candidates.json').read_text())['binary'])
    result = extract(binary.read_bytes())
    if args.check and result != json.loads((HERE / 'relative-attempt.json').read_text()):
        raise ValueError('Disk recheck differs')
    if args.output:
        args.output.write_text(json.dumps(result, indent=2) + '\n')
    print('S360_RELATIVE_BYTES_OK; native resolver and saved dereference unproved')


if __name__ == '__main__':
    main()
