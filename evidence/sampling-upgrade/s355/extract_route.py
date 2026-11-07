"""Bind original ones action bytes to a bounded numeric dispatch candidate."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import zlib

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load(path):
    spec = importlib.util.spec_from_file_location('s355_' + path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def source_callsite(raw):
    expected = json.loads((ROOT / 'manifest.json').read_text())['file_sha256']['game/main.swf']
    if sha(raw) != expected:
        raise ValueError('original SWF differs')
    data = raw if raw[:3] == b'FWS' else raw[:8] + zlib.decompress(raw[8:])
    if len(data) != struct.unpack_from('<I', data, 4)[0]:
        raise ValueError('SWF length mismatch')
    found = []

    def walk(pos, end, symbol=0):
        frame = 1
        while pos + 2 <= end:
            header = struct.unpack_from('<H', data, pos)[0]
            pos += 2
            code, size = header >> 6, header & 63
            if size == 63:
                size = struct.unpack_from('<I', data, pos)[0]
                pos += 4
            stop = pos + size
            if stop > end:
                raise ValueError('truncated tag')
            if code == 39:
                walk(pos + 4, stop, struct.unpack_from('<H', data, pos)[0])
            if symbol == 1813 and frame == 1 and code == 12:
                found.append((pos, data[pos:stop]))
            if code == 1:
                frame += 1
            pos = stop
            if code == 0:
                if pos != end:
                    raise ValueError('trailing timeline bytes')
                return
        raise ValueError('missing End')

    walk(8 + (5 + 4 * (data[8] >> 3) + 7) // 8 + 4, len(data))
    if len(found) != 1:
        raise ValueError('ambiguous timer action')
    offset, action = found[0]
    records = load(HERE.parent / 's292/diagnose.py').actions(action.hex())
    by_offset = {row['relative_offset']: row for row in records}
    # The full pool and containing DefineFunction2 header anchor this slice;
    # a bare opcode or text search cannot associate a caller.
    pool_raw = bytes.fromhex(by_offset[0]['hex'])[3:]
    count = struct.unpack_from('<H', pool_raw)[0]
    pool = [s.decode('utf8') for s in pool_raw[2:].split(b'\0')[:-1]]
    if len(pool) != count or [pool[i] for i in (3, 19, 21, 22)] != ['time', 'gs', 'gotoAndStop', '个']:
        raise ValueError('caller constant pool differs')
    header = bytes.fromhex(by_offset[176]['hex'])
    if header.hex() != '8e0800000000026a00db01':
        raise ValueError('function header differs')
    body_start = 176 + len(header)
    body_end = body_start + struct.unpack_from('<H', header, len(header) - 2)[0]
    window = action[629:662]
    if window.hex() != '96020008131c960500070100000047960700070100000008161c96020008155217':
        raise ValueError('ones operand/call sequence differs')
    if not body_start <= 629 < 662 <= body_end or by_offset[660]['opcode'] != 0x52:
        raise ValueError('call outside containing function')
    # No relative branch in the containing body enters the middle of the operand
    # window. This is a local static condition, not full reachability or execution.
    branches = []
    for row in records:
        p = row['relative_offset']
        if body_start <= p < body_end and row['opcode'] in (0x99, 0x9d):
            b = bytes.fromhex(row['hex'])
            target = p + len(b) + struct.unpack_from('<h', b, 3)[0]
            branches.append(dict(offset=p, opcode=row['opcode'], target=target))
            if 629 < target < 662:
                raise ValueError('branch enters caller operand window')
    return dict(swf='game/main.swf', swf_sha256=sha(raw), sprite=1813, frame=1,
                coordinates='uncompressed SWF offsets; not loaded PCs',
                action_offset=offset, action_hex=action.hex(), action_sha256=sha(action),
                constant_pool=pool, function_header_offset=176, function_header_hex=header.hex(),
                function_body_start=body_start, function_body_end_exclusive=body_end,
                caller_start=629, caller_end_exclusive=662, caller_hex=window.hex(),
                call_offset=660, call_uncompressed_offset=offset + 660, opcode=0x52,
                operand_sequence=['constant gs', 'GetVariable', 'integer 1', 'Add2',
                                  'argument count 1; constant 个', 'GetVariable',
                                  'constant gotoAndStop', 'CallMethod', 'Pop'],
                local_branches=branches, loaded_caller_association=None)


def extract(raw, binary):
    caller = source_callsite(raw)
    locked = json.loads((HERE.parent / 's303/native-audit.json').read_text())
    if sha(binary) != locked['binary_sha256']:
        raise ValueError('player differs from receipt')
    m = load(HERE.parent / 's303/audit_native.py')
    metadata = m.macho(binary)
    if metadata != locked['module']:
        raise ValueError('module metadata differs')
    base = locked['image_base']

    def region(start, end):
        offset = m.file_offset(metadata, base + start, end - start)
        b = binary[offset:offset + end - start]
        return dict(start=start, end_exclusive=end, file_offset=offset, hex=b.hex(), sha256=sha(b))

    for name in ('fetch_and_dispatch', 'dispatch_table', 'callmethod_candidate'):
        old = locked['regions'][name]
        if region(old['module_relative'], old['module_relative'] + old['size'])['hex'] != old['hex']:
            raise ValueError('retained native bytes differ')
    table = 0x12cf44
    entry = region(table + 4 * (caller['opcode'] - 4), table + 4 * (caller['opcode'] - 4) + 4)
    target = table + struct.unpack('<i', bytes.fromhex(entry['hex']))[0]
    if target != 0x124c2b:
        raise ValueError('numeric table destination differs')
    jump = region(0x124cbd, 0x124cc2)
    continuation = 0x124cc2 + struct.unpack_from('<i', bytes.fromhex(jump['hex']), 1)[0]
    if continuation != 0x1264db:
        raise ValueError('retained continuation differs')
    prefix = region(continuation, 0x1264ef)
    if prefix['hex'] != '498b85500d000080b85109000000488b45a07448':
        raise ValueError('continuation first branch differs')
    return dict(caller=caller, binary_receipt='evidence/sampling-upgrade/s303/native-audit.json',
                binary_sha256=sha(binary), module_uuid=metadata['uuid'], image_base=base,
                numeric_dispatch=dict(opcode=caller['opcode'], table=table, entry=entry, target=target,
                                      retained_jump=jump, continuation=continuation),
                new_native_prefix=prefix, first_branch_target=0x126537, fallthrough=0x1264ef,
                new_native_bytes=20, loaded_frame_entry_route=None, independent_outer_lifetime=None,
                limitation='Static caller operands and numeric dispatch candidate only; loaded method resolution, frame-entry effect and outer generations remain unproved.')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--binary', type=Path)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    receipt = json.loads((HERE.parent / 's303/native-audit.json').read_text())
    binary = args.binary or Path(receipt['binary'])
    result = extract((ROOT / 'game/main.swf').read_bytes(), binary.read_bytes())
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print('S355_STATIC_CALLER_ROUTE_EXTRACTED; loaded entry and lifetime unproved')


if __name__ == '__main__':
    main()
