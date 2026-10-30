"""Validate and replay only observed countdown firings, never wall-clock deadlines."""
import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics
import tarfile
import tempfile

from tools.sampling_native import validate_capture
from tools.sampling_bitmap import collect

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PAIR = HERE.parent / 's220'
spec = importlib.util.spec_from_file_location('s253', HERE.parent / 's253/diagnose.py')
s253 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s253)
FIELDS = ('phase', 'firing', 'receiver', 'timer', 'interval_id', 'gametime',
          'paused', 'p1_sw', 'p2_sw', 'modo', 'tens', 'ones', 'timer_frame')


def observed(event):
    values = event['value'].split(',')
    if len(values) != len(FIELDS):
        raise ValueError('incomplete countdown observation')
    row = dict(zip(FIELDS, values))
    for key in ('firing', 'gametime', 'modo', 'tens', 'ones', 'timer_frame'):
        row[key] = int(row[key])
    return {**event, **row}


def replay(events):
    """A source-scoped audit model; not an engine scheduling or full HUD adapter."""
    rows = [observed(e) for e in events if e['kind'] == 's258_countdown']
    if [r['phase'] for r in rows[:2]] != ['register_before', 'register_after']:
        raise ValueError('missing registration')
    first, registration = rows[:2]
    if first['firing'] != 0 or registration['firing'] != 0 or registration['interval_id'] == 'undefined':
        raise ValueError('invalid registration')
    current = {k: registration[k] for k in ('gametime', 'tens', 'ones')}
    if current != {k: first[k] for k in current}:
        raise ValueError('registration changed state')
    count = 0
    pending = None
    snapshot = None
    snapshots = []
    firings = []
    for row in rows[2:]:
        if (row['timer'], row['interval_id'], row['timer_frame']) != (registration['timer'], registration['interval_id'], 1):
            raise ValueError('timer identity/frame changed')
        phase = row['phase']
        if phase == 'fire_before':
            if pending is not None or snapshot is not None or row['firing'] != count + 1:
                raise ValueError('missing/overlapping firing or snapshot')
            if current != {k: row[k] for k in current}:
                raise ValueError('unobserved countdown state change')
            if any(row[k] not in ('true', 'false') for k in ('paused', 'p1_sw', 'p2_sw')):
                raise ValueError('unproved callback guard type')
            pending = row
            count += 1
            decrement = all(row[k] == 'false' for k in ('paused', 'p1_sw', 'p2_sw')) and row['modo'] != 4
            current['gametime'] -= int(decrement)
            tm = max(0, current['gametime'])
            current.update(tens=tm // 10 + 1, ones=tm % 10 + 1)
        elif phase == 'fire_after':
            if pending is None or row['firing'] != count or current != {k: row[k] for k in current}:
                raise ValueError('callback replay mismatch or missing before')
            if any(row[k] != pending[k] for k in ('paused', 'p1_sw', 'p2_sw', 'modo')):
                raise ValueError('guard changed inside callback')
            firings.append({'before': pending, 'after': row})
            pending = None
        elif phase in ('snapshot_before', 'snapshot_after'):
            if pending is not None or row['firing'] != count or current != {k: row[k] for k in current}:
                raise ValueError('snapshot does not match proved event replay')
            if phase == 'snapshot_before':
                if snapshot is not None:
                    raise ValueError('duplicate snapshot')
                snapshot = row
            else:
                if snapshot is None or row['sequence'] != snapshot['sequence'] + 1 or row['tick'] != snapshot['tick']:
                    raise ValueError('missing or interrupted snapshot')
                snapshots.append({'before': snapshot, 'after': row, 'replayed': current.copy()})
                snapshot = None
        else:
            raise ValueError('unexpected countdown phase')
    if pending is not None or snapshot is not None or not firings:
        raise ValueError('incomplete tape')
    if [s['before']['tick'] for s in snapshots] != list(range(61)):
        raise ValueError('missing snapshot tick')
    for s in snapshots:
        e = events[s['after']['sequence']]
        if e['kind'] != 'bitmap_begin' or (e['tick'], e['display']) != (s['before']['tick'], s['before']['display']):
            raise ValueError('snapshot not bound to unchanged bitmap boundary')
    return dict(registration=rows[:2], firings=firings, snapshots=snapshots,
                firing_count=count, blocked_firings=sum(f['before']['gametime'] == f['after']['gametime'] for f in firings),
                replay_scope='gametime and digit frames only; timeout side effects and full visual state unproved')


def diagnose():
    for name, expected in json.loads((HERE / 'input-sha256.json').read_text()).items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise ValueError('changed input: ' + name)
    raw = gzip.decompress((HERE / 'native-capture.log.gz').read_bytes())
    receipt = json.loads((HERE / 'native-receipt.json').read_text())
    if hashlib.sha256(raw).hexdigest() != receipt['files'][receipt['trace']]:
        raise ValueError('trace differs from receipt')
    metadata = json.loads((HERE / 'native-build.json').read_text())
    with tarfile.open(HERE / 'native-build.tar.gz') as archive:
        if json.load(archive.extractfile('build.json')) != metadata:
            raise ValueError('build archive mismatch')
        for name, digest in {**metadata['outputs_sha256'], 'instrumentation.diff': metadata['instrumentation_sha256']}.items():
            if hashlib.sha256(archive.extractfile(name).read()).hexdigest() != digest:
                raise ValueError('archived build hash mismatch')
    case = json.loads((PAIR / 'sasuke__attack__neutral__ground__near.json').read_text())
    with tempfile.TemporaryDirectory() as temp:
        trace = Path(temp) / 'native.log'
        trace.write_bytes(raw)
        validate_capture(case, metadata, trace)
    events = s253.events_from(raw.decode().splitlines())
    tape = replay(events)
    # This validates complete bitmap rows without any offset or image selection.
    images = collect(raw.decode().splitlines(), metadata['run_id'], 60)
    old = s253.events_from(gzip.decompress((PAIR / 'native-capture.log.gz').read_bytes()).decode().splitlines())
    states = lambda stream: [(e['tick'], e['value']) for e in stream if e['kind'] == 'state' and e['tick'] >= 0]
    differences = [{'new': a, 's220': b} for a, b in zip(states(events), states(old)) if a != b]
    starts = [e for e in events if e['kind'] == 'bitmap_begin']
    ends = [e for e in events if e['kind'] == 'bitmap_end']
    return dict(base='230830ed', production_admitted=False, native_parity_proven=False,
                common_visual_phase_proved=False, clock_adapter_implemented=False,
                events=len(events), bitmap_frames=len(images), actor_rows=len(states(events)),
                actor_differences_from_s220=differences,
                encoding_median_ms=statistics.median(b['time_ms']-a['time_ms'] for a,b in zip(starts,ends)),
                tape=tape)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    result = diagnose()
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'tape'}))


if __name__ == '__main__':
    main()
