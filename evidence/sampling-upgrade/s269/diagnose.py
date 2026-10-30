"""Recompute the bounded s269 callsite-window evidence without resealing receipts."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import tarfile
import tempfile

from tools.sampling_doaction import collect, check_inventory
from tools.sampling_callsite import collect_calls
from tools.sampling_native import validate_capture

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
CASE = ROOT / 'evidence/sampling-upgrade/s223/sasuke__attack__neutral__ground__near.json'


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
    old_dir = ROOT / 'evidence/sampling-upgrade/s223'
    old_text = gzip.decompress((old_dir / 'rejected-completion-boundary.log.gz').read_bytes()).decode()
    old = rows(old_text)
    report = {'production_admitted': False, 'native_parity_proven': False,
              'shared_builder_changed': False, 'trace_trimmed': False, 'runs': {}}
    with tempfile.TemporaryDirectory(prefix='s269-') as directory:
        trace = Path(directory) / 'native.log'
        trace.write_text(old_text)
        try:
            with tarfile.open(old_dir / 'rejected-completion-boundary-build.tar.gz') as archive:
                old_meta = json.load(archive.extractfile('build.json'))
            validate_capture(case, old_meta, trace)
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
            actions = collect(text.splitlines(), metadata['run_id'], 60, check_inventory(metadata))
            calls = collect_calls(text.splitlines(), metadata['callsite_specification'], retain_incomplete=True)
            done = next(i for i, r in enumerate(events) if r[6] == 'done')
            suffix = events[done + 1:]
            comparisons = {}
            for kind in ('state', 'helper_state', 'helper_clip_state', 'helper_lifecycle',
                         'input_next_display', 'key_read', 'random'):
                before, after = selected(old, kind), selected(events, kind)
                comparisons[kind] = {'historical_count': len(before), 'fresh_count': len(after),
                                     'tick_payload_equal': before == after}
            random_rows = [r for r in events if r[6] == 'random']
            report['runs'][name] = {
                'event_count': len(events), 'raw_sha256': digest(text.encode()),
                'receipt_capture_validation_exit': 0, 'samples': len(actions['samples']),
                'unvisited': len(actions['unvisited']), 'uninstrumented': len(actions['uninstrumented']),
                'calls': calls, 'done_event': events[done],
                'terminal_suffix': suffix,
                'terminal_action_samples': [r for r in events if r[5] == '60' and r[6] == 'doaction_sample'],
                'comparison_to_s223_ticks_0_60': comparisons,
                'key_reads_before_terminal_equal': selected(old, 'key_read', 59) == selected(events, 'key_read', 59),
                'random_events': random_rows,
                'random_callsite_order_equal': [r[7].split(',')[:2] for r in old if r[6] == 'random'] == [r[7].split(',')[:2] for r in random_rows],
                'root_observer': root[root.index('_root.aiYulongDisplayComplete = false;'):],
                'runtime_fighter_identity_proved': False,
                'unchanged_callsite_specification': metadata['callsite_specification'] == old_meta['callsite_specification'],
                'unchanged_action_inventory': metadata['doaction_inventory'] == old_meta['doaction_inventory'],
                'unchanged_fighter_swfs': {path: value == old_meta['outputs_sha256'].get(path)
                                          for path, value in metadata['outputs_sha256'].items() if path != 'game/main.swf'},
            }
    held = report['runs']['held']
    phases = [r[7].split(',')[1] for r in held['terminal_suffix'] if r[6] == 'callsite']
    report['bounded_completion_cut_proved'] = (
        held['terminal_suffix'][-1][6] == 'capture_window_closed'
        and phases == ['predicate_before', 'true', 'call_before', 'call_after', 'end']
        and all(r['samples'] == 61 and r['unchanged_callsite_specification']
                and r['unchanged_action_inventory'] and all(r['unchanged_fighter_swfs'].values())
                and r['comparison_to_s223_ticks_0_60']['state']['tick_payload_equal']
                and r['comparison_to_s223_ticks_0_60']['input_next_display']['tick_payload_equal']
                for r in report['runs'].values()))
    if not report['bounded_completion_cut_proved']:
        raise ValueError('bounded completion control not proved')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    report = diagnose()
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print('S269_CALLSITE_WINDOW_EVIDENCE_OK production_admitted=false native_parity_proven=false')


if __name__ == '__main__':
    main()
