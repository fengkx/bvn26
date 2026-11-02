"""Recompute the independent s228 pair; preserve negative admission gates."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import tarfile
import tempfile

from qualify import qualify
from tools.sampling_doaction import check_inventory, collect, require_full_coverage
from tools.sampling_native import validate_capture

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CASE = HERE.parent / 's228/ichigo__attack__neutral__ground__near.json'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def selected(rows, kind, terminal=60):
    return [(int(r[5]), r[7]) for r in rows if r[6] == kind and 0 <= int(r[5]) <= terminal]


def diagnose():
    for name, expected in json.loads((HERE / 'input-sha256.json').read_text()).items():
        if digest((ROOT / name).read_bytes()) != expected:
            raise ValueError('changed retained input: ' + name)
    for name, expected in json.loads((HERE / 'capture-sha256.json').read_text()).items():
        if digest((HERE / name).read_bytes()) != expected:
            raise ValueError('changed capture artifact: ' + name)
    case = json.loads(CASE.read_text())
    old_meta = json.loads((HERE.parent / 's228/native-build.json').read_text())
    old_text = gzip.decompress((HERE.parent / 's228/native-capture.log.gz').read_bytes()).decode()
    old = [line.split('|', 7) for line in old_text.splitlines()]
    report = {'scope': 'AFTER-s281 rank 3 only', 'base': 'd58aee18fb5c94de66e556851c6f15f21f329f63',
              'production_admitted': False, 'native_parity_proven': False,
              'trace_trimmed': False, 'product_obligations_closed': 0, 'runs': {}}
    with tempfile.TemporaryDirectory(prefix='s284-diagnose-') as directory:
        trace = Path(directory) / 'native.log'
        trace.write_text(old_text)
        try:
            validate_capture(case, old_meta, trace)
        except ValueError as error:
            report['historical_rejection'] = str(error)
        else:
            raise ValueError('historical rejection unexpectedly passed')
        for mode in ('normal', 'held'):
            base = HERE / mode
            meta = json.loads((base / 'native-build.json').read_text())
            receipt = json.loads((base / 'receipt.json').read_text())
            build = Path(directory) / mode
            build.mkdir()
            with tarfile.open(base / 'native-build.tar.gz') as archive:
                for member in archive.getmembers():
                    if not member.isfile():
                        continue
                    target = build / member.name
                    if not target.resolve().is_relative_to(build.resolve()):
                        raise ValueError('unsafe archive path')
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(archive.extractfile(member).read())
            if json.loads((build / 'build.json').read_text()) != meta:
                raise ValueError('archive metadata mismatch')
            qualification = qualify(build, mode == 'held', receipt['build'])
            text = gzip.decompress((base / 'native-capture.log.gz').read_bytes()).decode()
            trace.write_text(text)
            validate_capture(case, meta, trace)
            if receipt['files'][receipt['trace']] != digest(text.encode()):
                raise ValueError('receipt trace mismatch')
            for name in ('build.json', 'instrumentation.diff', *meta['outputs_sha256']):
                if receipt['files'][str(Path(receipt['build']) / name)] != digest((build / name).read_bytes()):
                    raise ValueError('receipt build mismatch: ' + name)
            events = [line.split('|', 7) for line in text.splitlines()]
            actions = collect(text.splitlines(), meta['run_id'], 60, check_inventory(meta))
            try:
                require_full_coverage(actions)
            except ValueError as error:
                full_as = str(error)
            else:
                raise ValueError('full-AS unexpectedly passed')
            done = next(i for i, row in enumerate(events) if row[6] == 'done')
            suffix = events[done + 1:]
            comparisons = {kind: {'historical_count':len(selected(old,kind)),
                'fresh_count':len(selected(events,kind)),
                'tick_payload_equal':selected(old,kind)==selected(events,kind)}
                for kind in ('state','helper_state','helper_clip_state','helper_lifecycle',
                             'input_next_display','key_read','random')}
            report['runs'][mode] = {
                'qualification': qualification, 'event_count': len(events),
                'strict_native_capture_exit': 0, 'doaction_entry_capture_exit': 0,
                'samples': len(actions['samples']), 'entries':len(actions['entries']),
                'unvisited':len(actions['unvisited']), 'uninstrumented':len(actions['uninstrumented']),
                'full_as_gate': {'exit_code':1, 'error':full_as},
                'done':events[done], 'terminal_suffix':suffix,
                'terminal_kind_counts':dict(Counter(row[6] for row in suffix)),
                'host_log_equality': json.loads((base/'host-log-equality.json').read_text()),
                'comparison_to_s228_ticks_0_60':comparisons,
                'key_reads_before_terminal_equal':selected(old,'key_read',59)==selected(events,'key_read',59),
                'random_rows':[r for r in events if r[6]=='random'],
                'random_callsite_order_equal':[r[7].split(',')[:2] for r in old if r[6]=='random']==[r[7].split(',')[:2] for r in events if r[6]=='random'],
                'root_observer':(build/'patches/main/frame_10/DoAction.as').read_text().split('_root.aiS284DoActionComplete = false;',1)[1],
            }
    held = report['runs']['held']
    report['held_closure_observed'] = bool(held['terminal_suffix']) and held['terminal_suffix'][-1][6]=='capture_window_closed'
    report['normal_quit_truncation'] = {'normal_terminal_kinds':report['runs']['normal']['terminal_kind_counts'],
        'held_terminal_kinds':held['terminal_kind_counts'],
        'interpretation':'Normal quit can truncate the terminal period; absence is not callback completeness. Counts are run-specific.'}
    report['bounded_window_observed'] = report['held_closure_observed'] and all(r['samples']==61 for r in report['runs'].values())
    report['independent_pair_proved'] = report['bounded_window_observed'] and all(
        r['host_log_equality']['equal'] is True and all(r['comparison_to_s228_ticks_0_60'][k]['tick_payload_equal']
        for k in ('state','helper_state','helper_clip_state','helper_lifecycle','input_next_display'))
        for r in report['runs'].values())
    report['terminal_callback_completeness_proved'] = False
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--require-completion-proof', action='store_true')
    parser.add_argument('--strict-historical', action='store_true')
    args = parser.parse_args()
    report = diagnose()
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n')
    if args.strict_historical:
        print(report['historical_rejection']); return 1
    if args.require_completion_proof and not report['independent_pair_proved']:
        print('COMPLETION_UNPROVED: independent pair requirements remain unmet'); return 1
    print('S284_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
