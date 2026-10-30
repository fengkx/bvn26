"""Validate bounded encoded lifetime observations without admitting scene images."""
import argparse
from collections import Counter
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import tarfile
import tempfile

from tools.sampling_native import validate_capture

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SPEC = importlib.util.spec_from_file_location('s274_locked_s265', HERE.parent / 's265/diagnose.py')
locked = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(locked)


def events_from(raw):
    return locked.s262.s258.s253.events_from(raw.decode().splitlines())


def analyze(events):
    if any(e['kind'].startswith('bitmap_') for e in events):
        raise ValueError('pixel export is forbidden')
    if len({e['run'] for e in events}) != 1:
        raise ValueError('mixed capture runs')
    if [e['sequence'] for e in events] != list(range(1, len(events) + 1)):
        raise ValueError('incomplete event sequence')
    def select(kind, prefix=''):
        return [e for e in events if e['kind'] == kind and e['value'].startswith(prefix)]
    life = select('s274_life')
    actual = [e for e in life if e['value'].split(',')[1].endswith('.个')]
    if len(actual) != 1 or actual[0]['value'].split(',')[0::3] != ['load', '1']:
        raise ValueError('authored load interval missing')
    _, path, depth, generation, _ = actual[0]['value'].split(',')
    if depth != '-16381':
        raise ValueError('authored depth mismatch')
    states = select('s274_state')
    samples = select('s274_state', 'sample,')
    if [e['tick'] for e in samples if e['tick'] >= 0] != list(range(61)):
        raise ValueError('sample window incomplete')
    for e in states:
        phase, p, d, g, frame = e['value'].split(',')
        if p == path and (d != depth or g != generation or not 1 <= int(frame) <= 10
                          or e['sequence'] <= actual[0]['sequence']):
            raise ValueError('unbound actual generation/frame')
    controls = [e for e in life if '.__s274Control,' in e['value']]
    if [(e['value'].split(',')[0], e['value'].split(',')[3]) for e in controls] != [
            ('load', '2'), ('unload', '2'), ('load', '3'), ('unload', '3'), ('load', '4'), ('unload', '4')]:
        raise ValueError('retained/replaced controls missing')
    phases = {e['value'].split(',')[0]: e for e in states if '.__s274Control,' in e['value']}
    expected = {'retained_before': '2', 'retained_after': '2', 'replace_before': '2', 'replace_after': '3',
                'encoded_retained_before': '3', 'encoded_retained_after': '3',
                'encoded_replace_before': '3', 'encoded_replace_after': '4'}
    if set(phases) != set(expected):
        raise ValueError('control boundaries incomplete')
    for phase, g in expected.items():
        if phases[phase]['value'].split(',')[2:4] != ['100001', g]:
            raise ValueError('control generation mismatch')
    entries = select('s274_entry')
    retained = []
    for phase, generation, tick in [('retained_after', '2', 1), ('encoded_retained_after', '3', 5)]:
        hits = [e for e in entries if e['tick'] == tick and e['value'].endswith(',100001,' + generation + ',1')]
        if len(hits) != 1 or hits[0]['sequence'] <= phases[phase]['sequence']:
            raise ValueError('retained target entry missing')
        retained.append(hits[0])
    admissions = select('s274_admission')
    if [(e['tick'], e['value']) for e in admissions] != [(t, 'true') for t in range(4, 61)]:
        raise ValueError('local state admission missing')
    windows = []
    for a in admissions:
        tick = a['tick']
        memory = [e for e in select('s274_memory') if e['tick'] == tick]
        if [e['value'] for e in memory] != ['draw_before', 'draw_after', 'encoding_after']:
            raise ValueError('draw/encoding boundaries incomplete')
        sizes = [e for e in select('s274_encoded_size') if e['tick'] == tick]
        before = [e for e in states if e['tick'] == tick and e['value'].startswith('draw_before,')]
        after = [e for e in states if e['tick'] == tick and e['value'].startswith('draw_after,')]
        if len(sizes) != 1 or int(sizes[0]['value']) <= 0 or len(before) != 1 or len(after) != 1:
            raise ValueError('encoded work/state missing')
        order = [a, before[0], *memory[:2], sizes[0], memory[2], after[0]]
        if [e['sequence'] for e in order] != sorted(e['sequence'] for e in order):
            raise ValueError('draw before admission or invalid order')
        if before[0]['value'].split(',')[1:] != after[0]['value'].split(',')[1:]:
            raise ValueError('state changed across synchronous memory work')
        if retained[0]['sequence'] >= a['sequence'] or phases['replace_after']['sequence'] >= a['sequence']:
            raise ValueError('encoding before control calibration')
        windows.append({'tick': tick, 'admission': a, 'before': before[0], 'after': after[0],
                        'draw': memory[:2], 'encoding_end': memory[2], 'encoded_characters': int(sizes[0]['value'])})
    if len(select('s274_memory')) != 3 * len(windows):
        raise ValueError('unadmitted memory work')
    if retained[1]['sequence'] <= windows[1]['encoding_end']['sequence']:
        raise ValueError('retained entry not observed after encoding')
    callbacks = select('s258_countdown', 'fire_before,')
    callback_afters = select('s258_countdown', 'fire_after,')
    if not callbacks or len(callbacks) != len(callback_afters):
        raise ValueError('callback pairs incomplete')
    for ordinal, (before, after) in enumerate(zip(callbacks, callback_afters), 1):
        b, a = map(locked.s262.s258.observed, (before, after))
        if (b['firing'], a['firing']) != (ordinal, ordinal) or b['sequence'] >= a['sequence']:
            raise ValueError('callback order mismatch')
        if any(r['timer'] != path.rsplit('.', 1)[0] or r['timer_frame'] != 1 for r in (b, a)):
            raise ValueError('callback placement mismatch')
        if any(b[k] not in ('true', 'false') or b[k] != a[k] for k in ('paused', 'p1_sw', 'p2_sw')):
            raise ValueError('callback guard mismatch')
        decrement = all(b[k] == 'false' for k in ('paused', 'p1_sw', 'p2_sw')) and b['modo'] != 4
        tm = b['gametime'] - int(decrement)
        if (a['gametime'], a['tens'], a['ones']) != (tm, max(0, tm) // 10 + 1, max(0, tm) % 10 + 1):
            raise ValueError('callback source-state mismatch')
    roots = select('input_next_display')
    joins = []
    for entry in entries:
        if not entry['value'].startswith(path + ',') or entry['sequence'] == actual[0]['sequence'] + 1:
            continue
        if entry['value'].split(',')[1:] != [depth, '1', '1']:
            raise ValueError('actual target entry lost generation')
        prior = [w for w in windows if w['encoding_end']['sequence'] < entry['sequence'] and w['tick'] == entry['tick']]
        next_root = next((e for e in roots if e['sequence'] > entry['sequence']), None)
        next_callback = next((e for e in callbacks if e['sequence'] > entry['sequence']), None)
        preceding_callback = next((e for e in reversed(callback_afters) if e['sequence'] < entry['sequence']), None)
        if preceding_callback and locked.s262.s258.observed(preceding_callback)['ones'] != 1:
            raise ValueError('target entry not selected by authored callback')
        joins.append({'entry': entry, 'encoding_end': prior[-1]['encoding_end'] if prior else None,
                      'preceding_callback': preceding_callback, 'next_root': next_root, 'next_callback': next_callback})
    complete = [j for j in joins if all(j.values())]
    return {'load': actual[0], 'last_sample': samples[-1], 'sample_count': len(samples),
            'controls': controls, 'control_boundaries': phases, 'retained_entries': retained,
            'encoding_windows': windows, 'actual_target_entries': joins, 'complete_entry_joins': len(complete),
            'callback_count': len(callbacks), 'bounded_encoded_lifetime_observed': bool(complete),
            'allocation_identity_beyond_observed_window_proved': False,
            'local_experiment_state_admitted': True,
            'thin_state_admission_proved': False, 'scene_state_admitted': False,
            'common_visual_phase_proved': False, 'production_admitted': False, 'native_parity_proven': False}


def diagnose():
    for name, expected in json.loads((HERE / 'input-sha256.json').read_text()).items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise ValueError('changed locked input: ' + name)
    raw = gzip.decompress((HERE / 'native-capture.log.gz').read_bytes())
    receipt = json.loads((HERE / 'native-receipt.json').read_text())
    if hashlib.sha256(raw).hexdigest() != receipt['files'][receipt['trace']]:
        raise ValueError('raw receipt mismatch')
    metadata = json.loads((HERE / 'native-build.json').read_text())
    with tarfile.open(HERE / 'native-build.tar.gz') as archive:
        if json.load(archive.extractfile('build.json')) != metadata:
            raise ValueError('build metadata mismatch')
        for name, expected in {**metadata['outputs_sha256'], 'instrumentation.diff': metadata['instrumentation_sha256']}.items():
            if hashlib.sha256(archive.extractfile(name).read()).hexdigest() != expected:
                raise ValueError('archive mismatch: ' + name)
    for name, expected in metadata['sources_sha256'].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise ValueError('build source mismatch: ' + name)
    case = json.loads((HERE.parent / 's220/sasuke__attack__neutral__ground__near.json').read_text())
    with tempfile.TemporaryDirectory() as temp:
        trace = Path(temp) / 'native.log'
        trace.write_bytes(raw)
        validate_capture(case, metadata, trace)
    events = events_from(raw)
    result = analyze(events)
    old = events_from(gzip.decompress((HERE.parent / 's265/native-capture.log.gz').read_bytes()))
    def actors(stream):
        return [(e['tick'], e['value']) for e in stream if e['kind'] == 'state' and e['tick'] >= 0]
    if actors(events) != actors(old):
        raise ValueError('actor control changed')
    return dict(result, base='ed5f1e13ecb0b95cea3e4df656ccda885f03418e', rank=2,
                events=len(events), event_counts=dict(Counter(e['kind'] for e in events)),
                actor_rows_equal_s265=len(actors(events)), images_written=0, scene_join_attempted=False,
                runtime_changed=False,
                next_discriminator='Bind independent child-clock and timer registration/intro boundaries in this same encoded run to a state-only scene observation. Require the complete scene admission contract before paired images; do not transplant callbacks, reset HUD, round camera values or change the renderer.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--require-state-admission', action='store_true')
    args = parser.parse_args()
    result = diagnose()
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({k: result[k] for k in ('events', 'callback_count', 'complete_entry_joins', 'bounded_encoded_lifetime_observed', 'thin_state_admission_proved', 'images_written', 'production_admitted', 'native_parity_proven')}))
    raise SystemExit(1 if args.require_state_admission and not result['thin_state_admission_proved'] else 0)


if __name__ == '__main__':
    main()
