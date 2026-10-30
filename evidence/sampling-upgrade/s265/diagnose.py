"""Bound no-encoding placement observations; reject the unproved scene join."""
import argparse
import collections
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import tarfile
import tempfile
import xml.etree.ElementTree as ET

from tools.sampling_native import validate_capture

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SPEC = importlib.util.spec_from_file_location('s262_locked', HERE.parent / 's262/diagnose.py')
s262 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(s262)


def analyze(events):
    if any(e['kind'].startswith('bitmap_') for e in events):
        raise ValueError('images before state admission')
    life = [e for e in events if e['kind'] == 's265_life']
    entries = [e for e in events if e['kind'] == 's265_entry']
    states = [e for e in events if e['kind'] == 's265_state']
    actual = [e for e in life if e['value'].split(',')[1].endswith('.个')]
    if len(actual) != 1 or actual[0]['value'].split(',')[0::3] != ['load', '1']:
        raise ValueError('missing or changed authored placement load')
    _, path, depth, generation, _ = actual[0]['value'].split(',')
    if depth != '-16381':
        raise ValueError('wrong authored runtime depth')
    samples = [e for e in states if e['value'].startswith('sample,')]
    if not samples or [e['tick'] for e in samples if e['tick'] >= 0] != list(range(61)):
        raise ValueError('missing sample boundary')
    for event in samples:
        fields = event['value'].split(',')
        if fields[1:4] != [path, depth, generation] or event['sequence'] <= actual[0]['sequence']:
            raise ValueError('unbound sample generation')
    controls = [e for e in life if '.__s265Control,' in e['value']]
    if [(e['value'].split(',')[0], e['value'].split(',')[3]) for e in controls] != [
            ('load', '2'), ('unload', '2'), ('load', '3'), ('unload', '3')]:
        raise ValueError('missing retained/replaced lifecycle controls')
    phases = {e['value'].split(',')[0]: e for e in states if not e['value'].startswith('sample,')}
    if set(phases) != {'retained_before', 'retained_after', 'replace_before', 'replace_after'}:
        raise ValueError('incomplete control boundaries')
    for phase, expected in [('retained_before', '2'), ('retained_after', '2'), ('replace_before', '2'), ('replace_after', '3')]:
        if phases[phase]['value'].split(',')[2:4] != ['100001', expected]:
            raise ValueError('wrong control generation/depth')
    retained_entries = [e for e in entries if '.__s265Control,100001,2,1' in e['value']
                        and phases['retained_after']['sequence'] < e['sequence'] < phases['replace_before']['sequence']]
    if len(retained_entries) != 1:
        raise ValueError('missing retained target-frame entry')
    entry = retained_entries[0]
    previous = events[entry['sequence'] - 2]
    if previous['kind'] != 's265_no_encoding' or previous['value'] != 'after':
        raise ValueError('target entry not bound to no-encoding completion')
    for event in entries:
        fields = event['value'].split(',')
        if fields[0] == path and fields[1:3] != [depth, generation]:
            raise ValueError('frame1 confused with placement load')
    boundaries = [e for e in events if e['kind'] == 's265_no_encoding']
    if [(e['tick'], e['value']) for e in boundaries] != [v for e in samples for v in [(e['tick'], 'before'), (e['tick'], 'after')]]:
        raise ValueError('incomplete no-encoding boundaries')
    return {'authored_path': path, 'runtime_depth': int(depth), 'load': actual[0],
            'last_sample': samples[-1], 'observed_sample_count': len(samples),
            'fight_sample_count': 61, 'observed_load_generation': int(generation),
            'control_events': controls, 'control_boundaries': phases,
            'retained_target_entry': entry, 'preceding_boundary': previous,
            'bounded_no_encoding_lifetime_observed': True,
            'allocation_identity_beyond_observed_window_proved': False}


def diagnose():
    for name, expected in json.loads((HERE / 'input-sha256.json').read_text()).items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise ValueError('changed locked input: ' + name)
    raw = gzip.decompress((HERE / 'native-capture.log.gz').read_bytes())
    receipt = json.loads((HERE / 'native-receipt.json').read_text())
    if hashlib.sha256(raw).hexdigest() != receipt['files'][receipt['trace']]:
        raise ValueError('trace receipt mismatch')
    metadata = json.loads((HERE / 'native-build.json').read_text())
    with tarfile.open(HERE / 'native-build.tar.gz') as archive:
        if json.load(archive.extractfile('build.json')) != metadata:
            raise ValueError('build metadata mismatch')
        for name, expected in {**metadata['outputs_sha256'], 'instrumentation.diff': metadata['instrumentation_sha256']}.items():
            if hashlib.sha256(archive.extractfile(name).read()).hexdigest() != expected:
                raise ValueError('build archive mismatch: ' + name)
    for name, expected in metadata['sources_sha256'].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise ValueError('build source mismatch: ' + name)
    case = json.loads((HERE.parent / 's220/sasuke__attack__neutral__ground__near.json').read_text())
    with tempfile.TemporaryDirectory() as temp:
        trace = Path(temp) / 'trace.log'
        trace.write_bytes(raw)
        validate_capture(case, metadata, trace)
    events = s262.s258.s253.events_from(raw.decode().splitlines())
    result = analyze(events)
    contract = json.loads((HERE.parent / 's262/source-contract.json').read_text())
    changes = [(c['frame'], ET.fromstring(c['tag'])) for c in contract['symbols']['1813']['changes']]
    placement = [t.attrib for frame, t in changes if frame == 1 and t.get('name') == '个']
    if len(placement) != 1 or placement[0]['characterId'] != '1810' or placement[0]['placeFlagMove'] != 'false':
        raise ValueError('authored placement changed')
    old_raw = gzip.decompress((HERE.parent / 's262/native-capture.log.gz').read_bytes())
    old = s262.s258.s253.events_from(old_raw.decode().splitlines())
    def actors(stream):
        return [(e['tick'], e['value']) for e in stream if e['kind'] == 'state' and e['tick'] >= 0]
    if actors(events) != actors(old):
        raise ValueError('actor control differs from s262')
    historical = []
    seen = set()
    for event in old:
        if event['kind'] != 's262_init':
            continue
        old_path = event['value'].split(',')[0]
        if old_path.endswith('.个') and old_path in seen:
            previous = old[event['sequence'] - 2]
            if previous['kind'] != 'bitmap_end':
                raise ValueError('historical encoding boundary changed')
            historical.append({'entry': event, 'preceding_boundary': previous})
        seen.add(old_path)
    return dict(base='929161938e30a96179ec18c0206f5787bf2978c9', rank=2,
                production_admitted=False, native_parity_proven=False,
                common_visual_phase_proved=False, thin_state_admission_proved=False,
                encoded_lifetime_join_proved=False, scene_join_attempted=False,
                images_written=0, runtime_changed=False, events=len(events),
                actor_rows_equal_s262=len(actors(events)),
                event_counts=dict(collections.Counter(e['kind'] for e in events)),
                placement=placement[0], no_encoding=result,
                historical_encoded_reentries=historical,
                historical_callbacks=len([e for e in old if e['kind'] == 's258_countdown' and e['value'].startswith('fire_before,')]),
                fresh_callbacks=len([e for e in events if e['kind'] == 's258_countdown' and e['value'].startswith('fire_before,')]),
                missing=['No independent load/unload observation inside the locked s262 draw/encoding run.',
                         'No same-run natural digit frame1 reentry with load observation across encoding.',
                         'No admitted native-to-Godot intro/root/callback boundary contract; camera mismatch remains.'],
                next_discriminator='After explicit state-only admission for the observed placement, observe the same load/unload and retained/replaced controls across an in-memory draw/encoding boundary, without exporting images. Preserve target-entry and next-root order; do not transplant s262 callbacks. Then, only if that contract passes, join scene intro/root boundaries.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--require-scene-join', action='store_true')
    args = parser.parse_args()
    result = diagnose()
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({k: result[k] for k in ('events', 'actor_rows_equal_s262', 'fresh_callbacks', 'images_written', 'thin_state_admission_proved', 'common_visual_phase_proved', 'production_admitted', 'native_parity_proven')}))
    raise SystemExit(1 if args.require_scene_join and not result['thin_state_admission_proved'] else 0)


if __name__ == '__main__':
    main()
