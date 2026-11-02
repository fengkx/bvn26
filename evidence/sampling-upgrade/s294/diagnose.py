"""Qualify the retained Yulong observer before any paired controls (s294)."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tarfile
import zlib

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FUNCTIONS = ['gameRunning', 'beida', 'fangyu', 'checkHit', 'getHitObj', 'getStgHitObj']
EXCLUSIONS = ['ancestor pn', 'aliases', 'artificial hitTest/call', 'enlarged boxes',
              'other chains', 'eligibility rule', 'other ranks', 'production changes']


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def prior_module():
    spec = importlib.util.spec_from_file_location('s285_locked', HERE.parent / 's285/diagnose.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def action_block(raw):
    """Select only Sprite2 frame1; coordinates remain uncompressed file offsets."""
    if raw[:3] not in (b'FWS', b'CWS'):
        raise ValueError('unsupported SWF')
    data = raw if raw[:3] == b'FWS' else raw[:8] + zlib.decompress(raw[8:])
    if len(data) != struct.unpack_from('<I', data, 4)[0]:
        raise ValueError('SWF length mismatch')
    found = []

    def walk(pos, end, sprite=None):
        frame = 1
        while pos < end:
            if pos + 2 > end:
                raise ValueError('truncated tag header')
            header = struct.unpack_from('<H', data, pos)[0]
            pos += 2
            code, size = header >> 6, header & 63
            if size == 63:
                if pos + 4 > end:
                    raise ValueError('truncated long tag')
                size = struct.unpack_from('<I', data, pos)[0]
                pos += 4
            stop = pos + size
            if stop > end:
                raise ValueError('truncated tag')
            if code == 39:
                if size < 4:
                    raise ValueError('truncated sprite')
                walk(pos + 4, stop, struct.unpack_from('<H', data, pos)[0])
            if (sprite, frame, code) == (2, 1, 12):
                found.append((data, pos, stop))
            if code == 1:
                frame += 1
            pos = stop
            if code == 0:
                if size or pos != end:
                    raise ValueError('invalid End tag')
                return
        raise ValueError('missing End tag')

    rect_size = (5 + 4 * (data[8] >> 3) + 7) // 8
    walk(8 + rect_size + 4, len(data))
    if len(found) != 1:
        raise ValueError('missing or ambiguous nested action block')
    return found[0]


def function_inventory(raw):
    data, start, end = action_block(raw)
    pool, functions = [], []

    def string(pos, limit):
        stop = data.index(b'\0', pos, limit)
        return data[pos:stop].decode('utf-8'), stop + 1

    def records(pos, limit):
        rows = []
        while pos < limit:
            offset, op = pos, data[pos]
            pos += 1
            size = 0
            if op >= 128:
                if pos + 2 > limit:
                    raise ValueError('truncated action header')
                size = struct.unpack_from('<H', data, pos)[0]
                pos += 2
            stop = pos + size
            if stop > limit:
                raise ValueError('truncated action payload')
            row = {'offset': offset, 'opcode': op, 'end': stop,
                   'hex': data[offset:stop].hex()}
            if op in (0x99, 0x9d):
                if size != 2:
                    raise ValueError('invalid branch')
                row['branch_target'] = stop + struct.unpack_from('<h', data, pos)[0]
            rows.append(row)
            yield row, pos, stop
            pos = stop

    pos = start
    while pos < end:
        row, payload, stop = next(records(pos, end))
        op = row['opcode']
        if op == 0x88:
            count = struct.unpack_from('<H', data, payload)[0]
            cursor, pool = payload + 2, []
            for _ in range(count):
                value, cursor = string(cursor, stop)
                pool.append(value)
            if cursor != stop:
                raise ValueError('invalid pool boundary')
        elif op in (0x8e, 0x9b):
            name, cursor = string(payload, stop)
            count = struct.unpack_from('<H', data, cursor)[0]
            cursor += 2
            registers = flags = None
            if op == 0x8e:
                registers = data[cursor]
                flags = struct.unpack_from('<H', data, cursor + 1)[0]
                cursor += 3
            params = []
            for _ in range(count):
                register = data[cursor] if op == 0x8e else None
                cursor += int(op == 0x8e)
                param, cursor = string(cursor, stop)
                params.append({'name': param, 'register': register})
            size = struct.unpack_from('<H', data, cursor)[0]
            if cursor + 2 != stop or stop + size > end:
                raise ValueError('invalid function boundary')
            body = [r for r, _, _ in records(stop, stop + size)]
            if any(r['opcode'] in (0x8e, 0x9b, 0x8f, 0x94) for r in body):
                raise ValueError('unsupported nested action container')
            boundaries = {r['offset'] for r in body} | {stop + size}
            if any(r.get('branch_target', stop) not in boundaries for r in body):
                raise ValueError('branch outside instruction boundary')
            functions.append({'name': name, 'opcode': op, 'definition_offset': pos,
                              'header_hex': data[pos:stop].hex(),
                              'register_count': registers, 'flags': flags, 'parameters': params,
                              'body_offset': stop, 'body_length': size,
                              'body_sha256': sha(data[stop:stop + size]),
                              'body_hex': data[stop:stop + size].hex(),
                              'constant_pool': pool.copy(), 'instructions': body})
            stop += size
        pos = stop
    if [f['name'] for f in functions] != FUNCTIONS:
        raise ValueError('changed nested function inventory')
    return {'swf_sha256': sha(raw), 'doaction_offset': start,
            'doaction_sha256': sha(data[start:end]), 'functions': functions,
            'coordinates': 'Uncompressed SWF file offsets; not native PCs or loaded AVM cursors'}


def compare(original, archived):
    rows = []
    for source, built in zip(original['functions'], archived['functions'], strict=True):
        if source['name'] != built['name']:
            raise ValueError('misaligned function comparison')
        rows.append({'name': source['name'],
                     'activation_header_equal': all(source[k] == built[k] for k in ('opcode', 'register_count', 'flags', 'parameters')),
                     'complete_header_equal': source['header_hex'] == built['header_hex'],
                     'complete_body_equal': source['body_hex'] == built['body_hex'],
                     'constant_pool_equal': source['constant_pool'] == built['constant_pool']})
    return rows


def diagnose():
    for path, expected in json.loads((HERE / 'input-sha256.json').read_text()).items():
        if sha((ROOT / path).read_bytes()) != expected:
            raise ValueError('locked input mismatch: ' + path)
    prior = prior_module().diagnose()
    if prior != json.loads((HERE.parent / 's285/diagnosis.json').read_text()):
        raise ValueError('locked s285 diagnosis changed')
    with tarfile.open(HERE.parent / 's275/native-build.tar.gz') as archive:
        built = archive.extractfile('game/fighter/yulong.swf').read()
    original = function_inventory((ROOT / 'game/fighter/yulong.swf').read_bytes())
    archived = function_inventory(built)
    equality = compare(original, archived)
    return {'scope': 'AFTER-s290 rank #4 only; Sprite345 frame188 depth28 Sprite104/depth2 Sprite2; ticks15-22',
            'production_admitted': False, 'native_parity_proven': False,
            'observer_qualified': False, 'direct_removal_dispatch_proved': False,
            'nested_entry_proved': False, 'complete_activation_operand_preservation_proved': False,
            'product_obligations_closed': 0, 'new_builds': 0, 'new_player_launches': 0,
            'new_captures': 0, 'paired_controls': 0, 'exclusions': EXCLUSIONS,
            'locked_s285_reproduced': True, 'retained_events': prior['retained_events_revalidated'],
            'removal_tag_binding': prior['removal_tag_binding'],
            'compiled_nested_functions': {'original': original, 's275_archive': archived,
                                          'comparison': equality},
            'source_only_preservation': prior['nested_function_audit']['function_bodies_unchanged'],
            'observations': {key: None for key in ('loaded_action_buffer', 'dispatch_pc',
                'placement_allocation_identity', 'defining_activation', 'entry_receiver',
                'entry_arguments', 'operand_stack', 'registers', 'scope_chain',
                'direct_parent', 'nested_return_or_invalidated_continuation', 'perturbation_bound')},
            'blockers': ['S294_REMOVAL_DISPATCH_UNPROVED', 'S294_NESTED_ENTRY_UNPROVED',
                         'S294_ACTIVATION_OPERAND_PRESERVATION_UNPROVED'],
            'qualification_limit': 'Archived initialization observer has no nested entry hooks or direct removal-dispatch mapping. Static bytes cannot bind an executed activation. Paired controls remain blocked; silence is not nonexecution.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    for flag in ('observer-qualification', 'parent-removal', 'nested-entry', 'activation-preservation'):
        parser.add_argument('--require-' + flag, action='store_true')
    args = parser.parse_args()
    report = diagnose()
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    required = [(args.require_observer_qualification, 'observer_qualified', 'S294_OBSERVER_UNQUALIFIED'),
                (args.require_parent_removal, 'direct_removal_dispatch_proved', report['blockers'][0]),
                (args.require_nested_entry, 'nested_entry_proved', report['blockers'][1]),
                (args.require_activation_preservation, 'complete_activation_operand_preservation_proved', report['blockers'][2])]
    missing = [code for requested, field, code in required if requested and not report[field]]
    if missing:
        print('; '.join(missing))
        return 1
    print('S294_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
