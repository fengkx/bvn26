"""Recheck one callback-name operand candidate; never infer a loaded callback."""
import argparse
import bisect
import hashlib
import importlib.util
import json
from pathlib import Path
import struct

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
START, END = 0x100096147, 0x10009615d
CODE = bytes.fromhex('488d15c28e1001488dbd30fdffff4c89eee833c40300')


def load_decoder():
    spec = importlib.util.spec_from_file_location('retained_relative_decoder', HERE.parent / 's360/resolve_relative.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def facts():
    return dict(start=START, end_exclusive=END, bytes_hex=CODE.hex(),
                sha256=hashlib.sha256(CODE).hexdigest(),
                instruction_lengths=[7, 7, 3, 5],
                name_operand=dict(next_rip=START + 7,
                    displacement=struct.unpack_from('<i', CODE, 3)[0],
                    target=START + 7 + struct.unpack_from('<i', CODE, 3)[0], register='rdx'),
                other_operands=['rdi = rbp - 0x2d0', 'rsi = r13'],
                direct_call=dict(address=END - 5,
                    target=END + struct.unpack_from('<i', CODE, 18)[0]),
                instruction_boundary_from_function_entry_proven=False,
                semantics='Local decoding from a byte-pattern candidate only; no executed-path or native type assertion')


def extract(raw):
    receipt = json.loads((HERE.parent / 's343/lookup-candidates.json').read_text())
    if hashlib.sha256(raw).hexdigest() != receipt['binary_sha256']:
        raise ValueError('Player differs from receipt')
    metadata = json.loads((HERE.parent / 's351/reference-attempt.json').read_text())
    header = bytes.fromhex(metadata['load_commands_hex'])
    if raw[:len(header)] != header:
        raise ValueError('Section mapping differs')
    text = next(s for s in metadata['sections'] if s['section'] == '__text')
    strings = next(s for s in metadata['sections'] if s['section'] == '__cstring')
    begin, end = strings['file_offset'], strings['file_offset'] + strings['size']
    needle = b'\0onEnterFrame\0'
    hits, cursor = [], begin
    while (offset := raw.find(needle, cursor, end)) >= 0:
        hits.append(offset + 1)
        cursor = offset + 1
    if hits != [0x119f010]:
        raise ValueError('Exact callback-name occurrence changed')
    target = strings['address'] + hits[0] - strings['file_offset']
    decoder = load_decoder()
    candidates = decoder.relative_candidates(raw, text['file_offset'], text['address'], text['size'], [target])
    if len(candidates) != 1 or candidates[0]['address'] != START:
        raise ValueError('Name-reference candidate changed')
    cursor, stream = 32, None
    for _ in range(struct.unpack_from('<I', raw, 16)[0]):
        kind, length = struct.unpack_from('<II', raw, cursor)
        if kind == 0x26:
            stream_offset, stream_size = struct.unpack_from('<II', raw, cursor + 8)
            stream = raw[stream_offset:stream_offset + stream_size]
        cursor += length
    if stream is None:
        raise ValueError('Missing function metadata')
    starts = decoder.function_starts(stream, 0x100000000)
    index = bisect.bisect_right(starts, START) - 1
    offset = text['file_offset'] + START - text['address']
    if raw[offset:offset + len(CODE)] != CODE:
        raise ValueError('Local candidate bytes changed')
    return dict(binary_sha256=receipt['binary_sha256'], binary_size=len(raw),
                search_sections=[strings, text],
                method='Exact NUL-delimited ASCII in __TEXT,__cstring, then REX.W RIP-LEA byte candidates in __TEXT,__text; unique candidate selected',
                name=dict(text='onEnterFrame', file_offset=hits[0], address=target,
                          bytes_hex=b'onEnterFrame\0'.hex()),
                candidates=candidates,
                function_metadata=dict(preceding_start=starts[index], next_start=starts[index + 1],
                    stream_offset=stream_offset, stream_size=stream_size,
                    stream_sha256=hashlib.sha256(stream).hexdigest()),
                local_decode=facts(), loaded_closure_body=None, owner_generation=None,
                activation=None, matched_dispatcher_continuation=None, replacement_survival=None,
                native_observations=[], successor_expansions=0,
                limitation='Name address is not callback identity. Function metadata does not establish the local candidate as a reachable instruction boundary. No callee or successor decoded; no live launch, attach, off/on or terminal inventory.')


def audit_record(record):
    expected = json.loads((HERE / 'native-route.json').read_text())
    if record != expected or record['local_decode'] != facts():
        raise ValueError('Callback-name candidate record changed')
    for key in ('loaded_closure_body', 'owner_generation', 'activation',
                'matched_dispatcher_continuation', 'replacement_survival'):
        if record[key] is not None:
            raise ValueError('Disk evidence promoted to identity')
    if record['native_observations']:
        raise ValueError('Unobserved execution')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    receipt = json.loads((HERE.parent / 's343/lookup-candidates.json').read_text())
    result = extract((args.binary or Path(receipt['binary'])).read_bytes())
    if args.check:
        audit_record(result)
    if args.output:
        args.output.write_text(json.dumps(result, indent=2) + '\n')
    print('S366_CALLBACK_NAME_OPERANDS_OK; loaded channel unproved')


if __name__ == '__main__':
    main()
