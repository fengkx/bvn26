"""Recompute a historical paired phase diagnosis without resealing its receipt."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import statistics
import tarfile
import tempfile

from PIL import Image

from tools.probes.collect_ai_reference import decode_number
from tools.sampling_bitmap import collect, difference, godot_images
from tools.sampling_native import validate_capture

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PAIR = ROOT / 'evidence/sampling-upgrade/s220'
FIELDS = ('slot', 'frame', 'x', 'y', 'xscale', 'action', 'hp', 'ql', 'sw',
          'touch', 'touchFloor', 'hits', 'paused', 'hstm', 'hurtSkling')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def events_from(lines):
    events = []
    for line in lines:
        prefix, run, sequence, clock, display, tick, kind, value = line.split('|', 7)
        if prefix != 'AIREF':
            raise ValueError('foreign event')
        events.append(dict(run=run, sequence=int(sequence), time_ms=int(clock),
                           display=int(display), tick=int(tick), kind=kind, value=value))
    if [e['sequence'] for e in events] != list(range(1, len(events) + 1)):
        raise ValueError('broken event sequence')
    if any(b['time_ms'] < a['time_ms'] for a, b in zip(events, events[1:])):
        raise ValueError('nonmonotonic clock')
    return events


def state(event):
    values = event['value'].split(',')
    if len(values) != len(FIELDS):
        raise ValueError('incomplete actor state')
    # Preserve undefined explicitly; it is not proof of equality to JSON null.
    return {key: value if key == 'slot' or value == 'undefined' else
            value == 'true' if value in ('true', 'false') else decode_number(value)
            for key, value in zip(FIELDS, values)}


def paired_rows(events, godot_rows, tick):
    native = [e for e in events if e['tick'] == tick and e['kind'] == 'state']
    actual = [r for r in godot_rows if r['tick'] == tick]
    if [state(e)['slot'] for e in native] != ['p1', 'p2'] or [r['slot'] for r in actual] != ['p1', 'p2']:
        raise ValueError('missing or duplicate paired actor')
    differences = []
    for event, row in zip(native, actual):
        for key, value in state(event).items():
            if value != row[key]:
                differences.append(dict(tick=tick, slot=row['slot'], field=key,
                                        native=value, godot=row[key]))
    return differences


def diagnose():
    pins = json.loads((HERE / 'input-sha256.json').read_text())
    for path, expected in pins.items():
        if sha((ROOT / path).read_bytes()) != expected:
            raise ValueError('changed diagnosis input: ' + path)
    case_path = PAIR / 'sasuke__attack__neutral__ground__near.json'
    case = json.loads(case_path.read_text())
    original_case = ROOT / 'evidence/sampling-upgrade/s217' / case_path.name
    if original_case.read_bytes() != case_path.read_bytes():
        raise ValueError('changed original tape')
    metadata = json.loads((PAIR / 'native-build.json').read_text())
    receipt = json.loads((PAIR / 'native-receipt.json').read_text())
    raw = gzip.decompress((PAIR / 'native-capture.log.gz').read_bytes())
    if sha(raw) != receipt['files'][receipt['trace']] or sha(case_path.read_bytes()) != receipt['case_sha256']:
        raise ValueError('historical receipt binding failed')
    with tarfile.open(PAIR / 'native-build.tar.gz') as archive:
        if json.load(archive.extractfile('build.json')) != metadata:
            raise ValueError('archive build metadata differs')
        patch = archive.extractfile('instrumentation.diff').read()
        if sha(patch) != metadata['instrumentation_sha256']:
            raise ValueError('changed native instrumentation')
        if b'DefineSprite_1813/' in patch:
            raise ValueError('unexpected countdown instrumentation')
    timer = json.loads((ROOT / 'godot/generated/main/timeout/timer.json').read_text())
    source = json.loads((ROOT / 'scripts/main.json').read_text())
    original = [entry['source'] for entry in source['scripts'] if entry['path'] == timer['source']]
    if original != [timer['source_text']]:
        raise ValueError('countdown source differs from locked script')
    lines = raw.decode().splitlines()
    events = events_from(lines)
    with tempfile.TemporaryDirectory(prefix='bvn-s253-') as temp:
        directory = Path(temp)
        trace = directory / 'native.log'
        trace.write_bytes(raw)
        validate_capture(case, metadata, trace)
        with tarfile.open(PAIR / 'godot-capture.tar.gz') as archive:
            # Extract only named regular files, never archive-controlled paths.
            for name in ['bitmap.json'] + [f'{t:03d}.png' for t in range(61)]:
                (directory / name).write_bytes(archive.extractfile('frames/' + name).read())
            actual = godot_images(directory, case_path)
            mismatches = []
            prefix_differences = []
            final_rows = json.load(archive.extractfile('frames/state-060.json'))
            for tick in range(61):
                rows = json.load(archive.extractfile(f'frames/state-{tick:03d}.json'))
                if rows != final_rows[:2 * (tick + 1)]:
                    prefix_differences.append(tick)
                mismatches.extend(paired_rows(events, rows, tick))
        native = collect(lines, metadata['run_id'], case['frames'])
        for name, pixels in [('native-tick013.png', native[13]), ('godot-tick013.png', actual[13])]:
            with Image.open(PAIR / name) as image:
                if image.convert('RGBA').tobytes() != pixels:
                    raise ValueError('review image is not the paired frame: ' + name)
        comparisons = [dict(tick=t, **difference(n, g)) for t, (n, g) in enumerate(zip(native, actual))]
    retained = json.loads((PAIR / 'comparison.json').read_text())
    if comparisons != retained['frames']:
        raise ValueError('strict comparison changed from historical result')
    windows = []
    for tick in range(61):
        selected = [e for e in events if e['tick'] == tick]
        begin = [e for e in selected if e['kind'] == 'bitmap_begin']
        end = [e for e in selected if e['kind'] == 'bitmap_end']
        actors = [e for e in selected if e['kind'] == 'state']
        if len(begin) != 1 or len(end) != 1 or not all(e['sequence'] < begin[0]['sequence'] for e in actors):
            raise ValueError('unexpected root sampling order')
        windows.append(dict(tick=tick, display=begin[0]['display'],
                            state_sequences=[e['sequence'] for e in actors],
                            bitmap_begin_sequence=begin[0]['sequence'], bitmap_end_sequence=end[0]['sequence'],
                            begin_ms=begin[0]['time_ms'], end_ms=end[0]['time_ms'],
                            encoding_ms=end[0]['time_ms'] - begin[0]['time_ms']))
    return dict(slice='s253', case_id=case['id'], case_sha256=sha(case_path.read_bytes()),
                evidence_mode='retained paired capture; no fresh capture or receipt reseal',
                production_admitted=False, native_parity_proven=False, clock_fix_proved=False,
                common_visual_phase_proved=False, raw_capture_structure_exit=0,
                actor_fields=list(FIELDS[1:]), paired_actor_rows=122, actor_differences=mismatches,
                godot_restarted_prefix_differences=prefix_differences,
                native_sampling_windows=windows,
                native_bitmap_encoding_median_ms=statistics.median(w['encoding_ms'] for w in windows),
                native_tick_0_to_60_ms=windows[-1]['begin_ms'] - windows[0]['begin_ms'],
                strict_rgba=dict(exit=0 if all(r['exact'] for r in comparisons) else 1,
                                 exact_frames=sum(r['exact'] for r in comparisons), frames=61,
                                 different_channels=sum(r['different_channels'] for r in comparisons),
                                 different_pixels=sum(r['different_pixels'] for r in comparisons),
                                 max_channel_delta=max(r['max_channel_delta'] for r in comparisons)),
                tick_13_actor_states=[state(e) for e in events if e['tick'] == 13 and e['kind'] == 'state'],
                tick_13_visual_observation=dict(native_countdown=47, godot_countdown=59,
                                               method='human-readable original full images; not OCR or a gate'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--strict-rgba', action='store_true')
    args = parser.parse_args()
    report = diagnose()
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print('PHASE_DIAGNOSIS_OK; common_visual_phase_proved=false; strict_rgba_exit=' + str(report['strict_rgba']['exit']))
    if args.strict_rgba:
        raise SystemExit(report['strict_rgba']['exit'])


if __name__ == '__main__':
    main()
