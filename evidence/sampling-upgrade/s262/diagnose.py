"""Join the bounded visual extension to its own callback/bitmap tape, fail closed."""
import argparse
import collections
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import tarfile

from tools.sampling_native import validate_capture

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
spec = importlib.util.spec_from_file_location('s258', HERE.parent / 's258/diagnose.py')
s258 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s258)
FIELDS = ('role', 'path', 'depth', 'frame', 'total', 'init_serial', 'init_display',
          'x', 'y', 'xscale', 'yscale', 'rotation', 'alpha', 'visible')


def visual_snapshots(events, tape):
    snapshots = []
    pending = None
    initializations = {}
    serial = 0
    for index, event in enumerate(events):
        kind = event['kind']
        if kind == 's262_init':
            path, symbol, depth, observed_serial, display = event['value'].split(',')
            serial += 1
            if int(observed_serial) != serial or int(display) != event['display']:
                raise ValueError('invalid initialization sequence')
            initializations[path] = (symbol, depth, observed_serial, display)
        elif kind == 's262_begin':
            if pending is not None:
                raise ValueError('overlapping visual snapshot')
            pending = {'tick': event['tick'], 'display': event['display'],
                       'firing': int(event['value']), 'begin_sequence': event['sequence'], 'nodes': {}}
        elif kind == 's262_visual':
            if pending is None or event['tick'] != pending['tick'] or event['display'] != pending['display']:
                raise ValueError('unbound visual node')
            parts = event['value'].split(',')
            if len(parts) != len(FIELDS):
                raise ValueError('incomplete visual node')
            row = dict(zip(FIELDS, parts))
            if row['role'] in pending['nodes']:
                raise ValueError('duplicate visual role')
            pending['nodes'][row['role']] = row
        elif kind == 's262_end':
            if pending is None or int(event['value']) != pending['firing']:
                raise ValueError('invalid visual end')
            snapshot = tape['snapshots'][len(snapshots)]['before']
            if (event['tick'], event['display']) != (pending['tick'], pending['display']):
                raise ValueError('visual boundary changed')
            if (events[index + 1]['sequence'] != snapshot['sequence']
                    or snapshot['firing'] != pending['firing']):
                raise ValueError('visual snapshot not adjacent to callback snapshot')
            nodes = pending['nodes']
            for role in ('timer', 'timer/十', 'timer/个', 'hud', 'camera', 'root'):
                if role not in nodes:
                    raise ValueError('missing visual role: ' + role)
            for role, field in [('timer', 'timer_frame'), ('timer/十', 'tens'), ('timer/个', 'ones')]:
                node = nodes[role]
                symbol = '1813' if role == 'timer' else '1810'
                if initializations.get(node['path']) != (symbol, node['depth'], node['init_serial'], node['init_display']):
                    raise ValueError('unbound initialization observation')
                if int(nodes[role]['frame']) != snapshot[field]:
                    raise ValueError('digit/timer frame join mismatch')
            pending['end_sequence'] = event['sequence']
            snapshots.append(pending)
            pending = None
        elif pending is not None:
            raise ValueError('interrupted visual observation')
    if pending is not None or [s['tick'] for s in snapshots] != list(range(61)):
        raise ValueError('missing visual snapshot')
    return snapshots


def diagnose():
    raw = gzip.decompress((HERE / 'native-capture.log.gz').read_bytes())
    receipt = json.loads((HERE / 'native-receipt.json').read_text())
    if hashlib.sha256(raw).hexdigest() != receipt['files'][receipt['trace']]:
        raise ValueError('trace hash mismatch')
    meta = json.loads((HERE / 'native-build.json').read_text())
    with tarfile.open(HERE / 'native-build.tar.gz') as archive:
        if json.load(archive.extractfile('build.json')) != meta:
            raise ValueError('build archive mismatch')
        for name, digest in {**meta['outputs_sha256'], 'instrumentation.diff': meta['instrumentation_sha256']}.items():
            if hashlib.sha256(archive.extractfile(name).read()).hexdigest() != digest:
                raise ValueError('archived build hash mismatch')
    for name, digest in meta['sources_sha256'].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise ValueError('source changed: ' + name)
    case = json.loads(s258.PAIR.joinpath('sasuke__attack__neutral__ground__near.json').read_text())
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp) / 'native.log'
        path.write_bytes(raw)
        validate_capture(case, meta, path)
    events = s258.s253.events_from(raw.decode().splitlines())
    tape = s258.replay(events)
    snapshots = visual_snapshots(events, tape)
    old = s258.s253.events_from(gzip.decompress((HERE.parent / 's258/native-capture.log.gz').read_bytes()).decode().splitlines())
    actor = lambda stream: [(e['tick'], e['value']) for e in stream if e['kind'] == 'state' and e['tick'] >= 0]
    if actor(events) != actor(old):
        raise ValueError('actor control differs from locked s258')
    images = s258.collect(raw.decode().splitlines(), meta['run_id'], 60)
    inits = [e for e in events if e['kind'] == 's262_init']
    return {'base': '624ca5e0', 'rank': 4, 'production_admitted': False, 'native_parity_proven': False,
            'common_visual_phase_proved': False, 'lifetime_proved': False, 'clock_adapter_implemented': False,
            'events': len(events), 'bitmap_frames': len(images), 'actor_rows_equal_s258': len(actor(events)),
            'event_counts': dict(collections.Counter(e['kind'] for e in events)), 'initializations': inits,
            'tape': tape, 'snapshots': snapshots,
            'unproved': ['Frame1 execution serial is not allocation identity or PlaceObject/MOVE history.',
                         'HUD enumeration is bounded to depth5; source-complete coverage is unproved.',
                         'Native pre-fight root/callback order has no proved join to the Godot intro.',
                         'Camera and HUD values require independent comparison before imaging.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    result = diagnose()
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('tape', 'snapshots', 'initializations')}))


if __name__ == '__main__':
    main()
