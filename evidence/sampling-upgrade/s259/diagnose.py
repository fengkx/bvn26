"""Recompute the bounded s259 geometry-window evidence without resealing receipts."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import tarfile
import tempfile

from tools.sampling_geometry import collect
from tools.sampling_native import validate_capture

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
CASE = ROOT / 'evidence/sampling-upgrade/s232/yijiao__attack__neutral__ground__near.json'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def rows(text):
    return [line.split('|', 7) for line in text.splitlines()]


def selected(events, kind, terminal=60):
    return [(int(r[5]), r[7]) for r in events if r[6] == kind and 0 <= int(r[5]) <= terminal]


def diagnose():
    pins = json.loads((HERE / 'input-sha256.json').read_text())
    for path, expected in pins.items():
        if digest((ROOT / path).read_bytes()) != expected:
            raise ValueError('changed evidence input: ' + path)
    case = json.loads(CASE.read_text())
    old_dir = ROOT / 'evidence/sampling-upgrade/s232'
    old_text = gzip.decompress((old_dir / 'native-capture.log.gz').read_bytes()).decode()
    old = rows(old_text)
    report = {'production_admitted': False, 'native_parity_proven': False,
              'shared_builder_changed': False, 'trace_trimmed': False, 'runs': {}}
    with tempfile.TemporaryDirectory(prefix='s259-') as directory:
        trace = Path(directory) / 'native.log'
        trace.write_text(old_text)
        try:
            validate_capture(case, json.loads((old_dir / 'native-build.json').read_text()), trace)
        except ValueError as error:
            report['historical_rejection'] = str(error)
        else:
            raise ValueError('historical capture unexpectedly admitted')
        for name in ('normal', 'held'):
            base = HERE / name
            metadata = json.loads((base / 'native-build.json').read_text())
            with tarfile.open(base / 'native-build.tar.gz') as archive:
                if json.loads(archive.extractfile('build.json').read()) != metadata:
                    raise ValueError('archive metadata mismatch')
                for path, expected in metadata['outputs_sha256'].items():
                    if digest(archive.extractfile(path).read()) != expected:
                        raise ValueError('changed captured SWF: ' + path)
                diff = archive.extractfile('instrumentation.diff').read()
                if digest(diff) != metadata['instrumentation_sha256']:
                    raise ValueError('changed instrumentation diff')
                root = archive.extractfile('patches/main/frame_10/DoAction.as').read().decode()
            for path, expected in metadata['sources_sha256'].items():
                if digest((ROOT / path).read_bytes()) != expected:
                    raise ValueError('changed locked source: ' + path)
            text = gzip.decompress((base / 'native-capture.log.gz').read_bytes()).decode()
            trace.write_text(text)
            validate_capture(case, metadata, trace)
            events = rows(text)
            sources = set()
            for path in metadata['sources_sha256']:
                if path.startswith('scripts/') and path.endswith('.json'):
                    bundle = json.loads((ROOT / path).read_text())
                    sources.update(bundle['game_file'] + '#' + s['path'] for s in bundle['scripts'])
            geometry = collect(text.splitlines(), metadata['run_id'], 60, sources)
            done = next(i for i, r in enumerate(events) if r[6] == 'done')
            suffix = events[done + 1:]
            comparisons = {}
            for kind in ('state', 'helper_state', 'helper_clip_state', 'helper_lifecycle',
                         'input_next_display', 'key_read', 'random'):
                before, after = selected(old, kind), selected(events, kind)
                comparisons[kind] = {'historical_count': len(before), 'fresh_count': len(after),
                                     'tick_payload_equal': before == after}
            random_rows = [r for r in events if r[6] == 'random']
            missing = [{'tick': s['tick'], 'slot': slot} for s in geometry['samples']
                       for slot in ('p1', 'p2') if not any(
                           b['role'] == 'hurt' and f'.game.{slot}.' in b['path'] for b in s['boxes'])]
            report['runs'][name] = {
                'event_count': len(events), 'raw_sha256': digest(text.encode()),
                'receipt_capture_validation_exit': 0, 'samples': len(geometry['samples']),
                'boxes': sum(len(s['boxes']) for s in geometry['samples']),
                'missing_receivers': missing, 'done_event': events[done],
                'terminal_suffix': suffix,
                'terminal_geometry': [r for r in events if r[5] == '60' and r[6].startswith('geometry_')],
                'comparison_to_s232_ticks_0_60': comparisons,
                'key_reads_before_terminal_equal': selected(old, 'key_read', 59) == selected(events, 'key_read', 59),
                'random_events': random_rows,
                'random_callsite_order_equal': [r[7].split(',')[:2] for r in old if r[6] == 'random'] == [r[7].split(',')[:2] for r in random_rows],
                'root_observer': root[root.index('_root.aiYulongDisplayComplete = false;'):],
                'runtime_fighter_identity_proved': False,
            }
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    report = diagnose()
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print('S259_GEOMETRY_WINDOW_EVIDENCE_OK production_admitted=false native_parity_proven=false')


if __name__ == '__main__':
    main()
