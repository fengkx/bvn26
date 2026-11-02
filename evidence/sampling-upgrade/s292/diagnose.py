"""Audit the archived ten-frame observer prerequisite, without synthesizing entry."""
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


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def prior_module():
    spec = importlib.util.spec_from_file_location('s292_prior', HERE.parent / 's282/diagnose.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digit_tags(raw):
    """Retain every tag in Sprite1810, with uncompressed file coordinates."""
    if raw[:3] not in (b'FWS', b'CWS'):
        raise ValueError('unsupported SWF')
    data = raw if raw[:3] == b'FWS' else raw[:8] + zlib.decompress(raw[8:])
    if len(data) != struct.unpack_from('<I', data, 4)[0]:
        raise ValueError('SWF length mismatch')
    found = []

    def walk(pos, end, selected=False):
        frame, rows = 1, []
        while pos + 2 <= end:
            offset = pos
            header = struct.unpack_from('<H', data, pos)[0]
            pos += 2
            code, size = header >> 6, header & 63
            if size == 63:
                if pos + 4 > end:
                    raise ValueError('truncated tag header')
                size = struct.unpack_from('<I', data, pos)[0]
                pos += 4
            stop = pos + size
            if stop > end:
                raise ValueError('truncated tag')
            payload = data[pos:stop]
            if selected:
                rows.append({'frame': frame, 'code': code, 'offset': offset,
                             'payload_offset': pos, 'payload_hex': payload.hex(),
                             'payload_sha256': sha(payload)})
            if code == 39:
                symbol, count = struct.unpack_from('<HH', payload)
                nested = walk(pos + 4, stop, symbol == 1810)
                if symbol == 1810:
                    if count != 10:
                        raise ValueError('digit frame count')
                    found.append(nested)
            pos = stop
            if code == 1:
                frame += 1
            if code == 0:
                if pos != end or (selected and frame != 11):
                    raise ValueError('invalid timeline end')
                return rows
        raise ValueError('missing timeline end')

    rect_size = (5 + 4 * (data[8] >> 3) + 7) // 8
    walk(8 + rect_size + 4, len(data))
    if len(found) != 1:
        raise ValueError('missing or ambiguous digit')
    return found[0]


def actions(payload):
    """Decode record boundaries only; no AVM interpretation or inferred dispatch."""
    raw = bytes.fromhex(payload)
    pos, rows = 0, []
    while pos < len(raw):
        start = pos
        opcode = raw[pos]
        pos += 1
        if opcode >= 128:
            if pos + 2 > len(raw):
                raise ValueError('truncated action header')
            size = struct.unpack_from('<H', raw, pos)[0]
            pos += 2 + size
        if pos > len(raw):
            raise ValueError('truncated action')
        rows.append({'relative_offset': start, 'opcode': opcode, 'hex': raw[start:pos].hex()})
        if opcode == 0:
            if pos != len(raw):
                raise ValueError('trailing action bytes')
            return rows
    raise ValueError('missing action end')


def byte_audit(original, archived):
    a, b = digit_tags(original), digit_tags(archived)
    project = lambda rows: [(r['frame'], r['code'], r['payload_hex']) for r in rows if r['code'] != 12]
    if project(a) != project(b):
        raise ValueError('non-action digit timeline changed')
    aa, bb = ([r for r in rows if r['code'] == 12] for rows in (a, b))
    if [(r['frame'], r['payload_hex']) for r in aa] != [(1, '0700')]:
        raise ValueError('original Stop/End or action inventory changed')
    if [r['frame'] for r in bb] != [1]:
        raise ValueError('archived action inventory changed')
    decoded = actions(bb[0]['payload_hex'])
    if [r['opcode'] for r in decoded[-2:]] != [7, 0] or sum(r['opcode'] == 7 for r in decoded) != 1:
        raise ValueError('archived terminal Stop/End changed')
    return {'original_swf_sha256': sha(original), 'archived_swf_sha256': sha(archived),
            'coordinates': 'Uncompressed SWF file offsets, not live dispatch PCs',
            'original_tags': a, 'archived_tags': b,
            'non_action_timeline_bytes_equal': True,
            'original_frame1_action_records': actions(aa[0]['payload_hex']),
            'archived_frame1_action_records': decoded,
            'terminal_stop_retained': True,
            'empty_frames_without_observer': list(range(2, 11)),
            'all_ten_frame_observer_present': False,
            'unchanged_action_execution_proved': False}


def control_audit(source, lifetime):
    groups = {}
    for name, first, last in [('retained', 27, 33), ('replacement', 34, 47),
                              ('encoded_retained', 48, 54), ('encoded_replacement', 55, 63)]:
        groups[name] = {'source_lines': [first, last],
                        'source': '\n'.join(source.splitlines()[first - 1:last])}
    for name in ('retained', 'encoded_retained'):
        block = groups[name]['source']
        if block.count('gotoAndStop(2);') != 1 or block.count('gotoAndStop(1);') != 1:
            raise ValueError('archived control changed')
        groups[name]['limitation'] = 'Two changed-target calls in one callback; not isolated repeated-target or frame2 entry proof.'
    for name in ('replacement', 'encoded_replacement'):
        if 'removeMovieClip();' not in groups[name]['source'] or 'duplicateMovieClip("__s274Control", 100001)' not in groups[name]['source']:
            raise ValueError('archived replacement changed')
        groups[name]['limitation'] = 'Encoded load/unload generation only; not all-frame entry or native allocation identity.'
    return {'archive_member': 's274-patches/frame_1/DoAction.as',
            'source_sha256': sha(source.encode()), 'groups': groups,
            'historical_boundaries': lifetime['control_boundaries'],
            'historical_retained_entries': lifetime['retained_entries'],
            'historical_lifecycle_events': lifetime['controls'],
            'independent_controls': {k: None for k in (
                'isolated_repeated_target_all_frames', 'isolated_changed_target_all_frames',
                'replacement_all_frames', 'observer_off_on_entry_order')},
            'actor_equality_is_entry_order_control': False}


def diagnose():
    for name, expected in json.loads((HERE / 'input-sha256.json').read_text()).items():
        if sha((ROOT / name).read_bytes()) != expected:
            raise ValueError('locked input changed: ' + name)
    prior = prior_module()
    historical = prior.diagnose()
    if historical != json.loads((HERE.parent / 's282/diagnosis.json').read_text()):
        raise ValueError('locked s282 diagnosis changed')
    with tarfile.open(HERE.parent / 's274/native-build.tar.gz') as archive:
        archived = archive.extractfile('game/main.swf').read()
        source = archive.extractfile('s274-patches/frame_1/DoAction.as').read().decode()
    lifetime = json.loads((HERE.parent / 's274/diagnosis.json').read_text())
    return {'slice': 's292', 'base': '3c6fc07e70dda6878e594c0f388f6e7066cc1f43',
            'scope': 'AFTER-s290 rank #2 only: Independent ones entry clock',
            'production_admitted': False, 'native_parity_proven': False,
            'observer_qualified': False, 'independent_child_clock_proved': False,
            'product_obligations_closed': 0, 'new_builds': 0, 'new_player_launches': 0,
            'new_captures': 0, 'new_images': 0,
            'historical': {k: historical[k] for k in ('run_id', 'raw_sha256', 'events_revalidated',
                'callback_count', 'natural_encoding_entry_joins', 'uninstrumented_target_windows')},
            'unobserved_frame1_windows': [r for r in historical['callback_windows']
                if r['classification'] == 'hook_present_no_entry_in_window'],
            'byte_audit': byte_audit((ROOT / 'game/main.swf').read_bytes(), archived),
            'control_audit': control_audit(source, lifetime),
            'capture_decision': 'Blocked before fresh ones-only capture: observer qualification absent.',
            'blocker': 'No all-ten-frame entry observer with preserved action execution and independent repeated/changed-target/replacement plus observer-off/on controls.',
            'exclusions': ['synthetic clock', 'scene/intro repair', 'HUD reset', 'images',
                           'cross-run tape', 'renderer change', 'other ranks']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--require-observer', action='store_true')
    parser.add_argument('--require-child-clock', action='store_true')
    args = parser.parse_args()
    result = diagnose()
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    if args.require_observer or args.require_child_clock:
        print('S292_ENTRY_OBSERVER_UNPROVED: ' + result['blocker'])
        return 1
    print('S292_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
