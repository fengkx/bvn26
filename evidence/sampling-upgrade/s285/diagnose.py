"""Audit one Yulong placement's removal and nested observation gaps (s285)."""
import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import struct
import tarfile
import zlib
from urllib.parse import unquote

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
NESTED = 'DefineSprite_2/frame_1/DoAction.as'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def retained_module():
    spec = importlib.util.spec_from_file_location('s275_diagnosis', HERE.parent / 's275/diagnose.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def removal_tags(raw):
    """Locate authored tags in decompressed-file coordinates, never native PCs."""
    if raw[:3] not in (b'FWS', b'CWS'):
        raise ValueError('unsupported SWF')
    data = raw if raw[:3] == b'FWS' else raw[:8] + zlib.decompress(raw[8:])
    if len(data) != struct.unpack_from('<I', data, 4)[0]:
        raise ValueError('SWF length mismatch')
    found = []

    def walk(start, end, sprite):
        pos, frame, index = start, 1, 0
        while pos + 2 <= end:
            offset = pos
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
                child = struct.unpack_from('<H', data, pos)[0]
                walk(pos + 4, stop, child)
            if (sprite, frame, code) in ((345, 194, 28), (104, 5, 28)):
                if size != 2:
                    raise ValueError('invalid RemoveObject2 payload')
                depth = struct.unpack_from('<H', data, pos)[0]
                if depth != (28 if sprite == 345 else 2):
                    raise ValueError('changed removal depth')
                found.append({'sprite': sprite, 'frame': frame, 'depth': depth,
                              'tag_index': index, 'uncompressed_offset': offset,
                              'tag_hex': data[offset:stop].hex(),
                              'tag_sha256': sha(data[offset:stop])})
            pos = stop
            index += 1
            if code == 1:
                frame += 1
            if code == 0:
                if pos != end:
                    raise ValueError('trailing timeline bytes')
                return
        raise ValueError('missing End tag')

    rect_bytes = (5 + 4 * (data[8] >> 3) + 7) // 8
    walk(8 + rect_bytes + 4, len(data), None)
    if len(found) != 2:
        raise ValueError('missing selected removal tags')
    return sorted(found, key=lambda row: row['sprite'])


def nested_audit(source, archived):
    source = source.replace('\r\n', '\n')
    archived = archived.replace('\r\n', '\n')
    if not archived.startswith(source):
        raise ValueError('nested function bodies differ from source')
    suffix = archived[len(source):]
    expected = ('\n_root.aiGeoStamp(this, "game/fighter/yulong.swf#DefineSprite_2/frame_1/DoAction.as");\n'
                '\nif(String(this) == "_level0.game.p1.mc.k1atm.mian") '
                '_root.aiK1Observe("source_after_stamp",this,_root.game["p" + this._parent.pn]);\n')
    if suffix != expected:
        raise ValueError('unclassified nested instrumentation')
    names = re.findall(r'^function (\w+)\(', source, re.M)
    if names != ['gameRunning', 'beida', 'fangyu', 'checkHit', 'getHitObj', 'getStgHitObj']:
        raise ValueError('changed nested function inventory')
    return {'source_path': NESTED, 'source_sha256': sha(source.encode()),
            'archived_source_sha256': sha(archived.encode()),
            'function_bodies_unchanged': True, 'functions': names,
            'entry_or_operand_hooks': [], 'initialization_only_suffix': suffix,
            'direct_invocation_observed': None,
            'operand_sites': [line.strip() for line in source.splitlines()
                              if '_parent.pn' in line or 'this.hitTest(' in line],
            'context': 'this is Sprite2 mian; direct _parent is Sprite104, not Sprite345'}


def correlate(lines):
    retained_module().observations(lines)
    rows = []
    for line in lines:
        p = line.split('|', 7)
        if 15 <= int(p[5]) <= 22:
            rows.append({'sequence': int(p[2]), 'time_ms': int(p[3]),
                         'display': int(p[4]), 'tick': int(p[5]), 'kind': p[6],
                         'fields': [unquote(v) for v in p[7].split(',')]})
    boundaries = [r for r in rows if r['kind'] == 's275_boundary']
    slots = [r for r in boundaries if r['fields'][0] == 'root_slot']
    brackets = []
    for slot in slots:
        states = [r for r in rows if r['kind'] == 'state' and r['tick'] == slot['tick']
                  and r['fields'][0] == 'p1']
        if len(states) != 1 or states[0]['sequence'] >= slot['sequence']:
            raise ValueError('missing or reordered P1 state/slot join')
        brackets.append({'tick': slot['tick'], 'body_frame': int(states[0]['fields'][1]),
                         'state_sequence': states[0]['sequence'], 'slot': slot})
    last, absent = brackets[-2:]
    if (last['tick'], last['body_frame'], last['slot']['fields'][1],
        absent['tick'], absent['body_frame'], absent['slot']['fields'][1]) != (
            21, 193, '_level0.game.p1.mc.abcd', 22, 194, 'undefined'):
        raise ValueError('changed parent removal bracket')
    spans = []
    for tick in range(16, 21):
        values = [r for r in rows if r['kind'] == 's275_value' and r['tick'] == tick]
        spans.append({'tick': tick, 'first_sequence': values[0]['sequence'],
                      'last_sequence': values[-1]['sequence'], 'records': len(values),
                      'logged_span_ms': values[-1]['time_ms'] - values[0]['time_ms']})
    return {'body_slot_joins': brackets, 'lifecycle_boundaries': boundaries,
            'observer_value_spans': spans,
            'direct_removal_dispatch': None, 'direct_nested_invocation': None}


def diagnose():
    for path, expected in json.loads((HERE / 'input-sha256.json').read_text()).items():
        if sha((ROOT / path).read_bytes()) != expected:
            raise ValueError('locked input mismatch: ' + path)
    retained = retained_module().diagnose()
    source = next(s['source'] for s in json.loads((ROOT / 'scripts/fighter/yulong.json').read_text())['scripts'] if s['path'] == NESTED)
    with tarfile.open(HERE.parent / 's275/native-build.tar.gz') as archive:
        observed = archive.extractfile('game/fighter/yulong.swf').read()
        nested = archive.extractfile('patches/fighter/yulong/' + NESTED).read().decode()
    original_tags = removal_tags((ROOT / 'game/fighter/yulong.swf').read_bytes())
    observed_tags = removal_tags(observed)
    if [(r['sprite'], r['frame'], r['depth'], r['tag_hex']) for r in original_tags] != [
            (r['sprite'], r['frame'], r['depth'], r['tag_hex']) for r in observed_tags]:
        raise ValueError('changed authored removal bytes')
    lines = gzip.decompress((HERE.parent / 's275/native-capture.log.gz').read_bytes()).decode().splitlines()
    return {'scope': 'AFTER-s281 rank 4 only; Sprite345 frame188 placement; ticks15-22',
            'base': '3a5ce953', 'production_admitted': False, 'native_parity_proven': False,
            'runtime_binding_proved': False, 'parent_removal_dispatch_proved': False,
            'direct_nested_invocation_proved': False, 'observer_perturbation_qualified': False,
            'product_obligations_closed': 0, 'new_builds': 0, 'new_captures': 0,
            'retained_events_revalidated': retained['events'],
            'actor_rows_equal_s247': retained['actor_rows_equal_s247'],
            'removal_tag_binding': {'original': original_tags, 's275_build': observed_tags,
                                    'coordinate_system': 'uncompressed SWF file offsets, not dispatch PCs'},
            'nested_function_audit': nested_audit(source, nested),
            'correlation': correlate(lines),
            'observer_qualification': {
                'outer_opcode_projection_equal': retained['opcode_projection_equal'],
                'actor_input_key_payloads_equal': all(retained[k] for k in ('actor_rows_equal_s247', 'input_rows_equal_s247', 'key_read_rows_equal_s247')),
                'random_rows_equal': retained['random_rows_equal_s247'],
                'timing_control_pairs': 0,
                'limits': ['Logged spans include original evaluation and tracing; not observer latency or a perturbation bound.',
                           'No paired unobserved/direct-dispatch control; equal actor payloads do not qualify dispatch timing.',
                           'Nested bodies have no entry/operand hooks; absent invocation records mean unknown, not never invoked.',
                           'No dispatch hook or native PC mapping; source tag and root bracket do not prove exact removal.']},
            'geometry_exit_code': retained['geometry_exit_code'], 'geometry_error': retained['geometry_error']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--require-parent-removal', action='store_true')
    parser.add_argument('--require-nested-invocation', action='store_true')
    parser.add_argument('--require-observer-qualification', action='store_true')
    parser.add_argument('--require-geometry', action='store_true')
    args = parser.parse_args()
    report = diagnose()
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    requirements = ((args.require_parent_removal, 'parent_removal_dispatch_proved'),
                    (args.require_nested_invocation, 'direct_nested_invocation_proved'),
                    (args.require_observer_qualification, 'observer_perturbation_qualified'))
    missing = [key for requested, key in requirements if requested and not report[key]]
    if args.require_geometry and report['geometry_exit_code']:
        missing.append(report['geometry_error'])
    print('S285_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')
    if missing:
        print('UNPROVED: ' + '; '.join(missing))
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
