"""Read-only s223 callsite completion-boundary diagnosis; never seal or trim a capture."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import tarfile
import tempfile

from tools.sampling_native import validate_capture
from tools.sampling_callsite import collect_calls

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'evidence/sampling-upgrade/s223'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def analyze(text, run_id):
    rows = []
    for line in text.splitlines():
        parts = line.split('|', 7)
        if len(parts) != 8 or parts[:2] != ['AIREF', run_id]:
            raise ValueError('malformed or foreign event')
        row = dict(zip(('sequence', 'clock_ms', 'display', 'tick'), map(int, parts[2:6])))
        row.update(kind=parts[6], payload=parts[7])
        if row['sequence'] != len(rows) + 1:
            raise ValueError('broken event sequence')
        if rows and row['clock_ms'] < rows[-1]['clock_ms']:
            raise ValueError('nonmonotonic clock')
        rows.append(row)
    dones = [r for r in rows if r['kind'] == 'done']
    if not dones:
        raise ValueError('missing done')
    first = dones[0]
    suffix = rows[first['sequence']:]
    terminal = []
    later = []
    for row in suffix:
        if (row['tick'], row['display']) == (first['tick'], first['display']):
            if later:
                raise ValueError('terminal period reappears after later root')
            terminal.append(row)
        else:
            later.append(row)
    return {
        'event_count': len(rows), 'done_events': dones,
        'terminal_period_callbacks': terminal, 'later_root_events': later,
        'terminal_kind_counts': dict(Counter(r['kind'] for r in terminal)),
        'later_kind_counts': dict(Counter(r['kind'] for r in later)),
        'terminal_action_samples': [r for r in rows if r['tick'] == first['tick']
                                     and r['kind'] == 'doaction_sample'],
        'all_action_sample_count': sum(r['kind'] == 'doaction_sample' for r in rows),
    }


def diagnose():
    hashes = json.loads((SOURCE / 'artifact-sha256.json').read_text())
    names = ('rejected-completion-boundary.log.gz', 'rejected-completion-boundary-build.tar.gz',
             'sasuke__attack__neutral__ground__near.json')
    inputs = {}
    for name in names:
        actual = digest((SOURCE / name).read_bytes())
        if actual != hashes[name]:
            raise ValueError(f'changed retained input: {name}')
        inputs[str((SOURCE / name).relative_to(ROOT))] = actual
    with tarfile.open(SOURCE / 'rejected-completion-boundary-build.tar.gz') as archive:
        metadata = json.load(archive.extractfile('build.json'))
    case = json.loads((SOURCE / names[-1]).read_text())
    if not metadata['sampling_callsite'] or any(metadata[k] for k in ('sampling_geometry', 'sampling_display', 'sampling_bitmap')):
        raise ValueError('not the selected standalone callsite mode')
    with tarfile.open(SOURCE / 'rejected-completion-boundary-build.tar.gz') as archive:
        if json.loads(archive.extractfile('build.json').read()) != metadata:
            raise ValueError('archive metadata differs')
        diff = archive.extractfile('instrumentation.diff').read()
        if digest(diff) != metadata['instrumentation_sha256']:
            raise ValueError('changed instrumentation')
        for name, expected in metadata['outputs_sha256'].items():
            if digest(archive.extractfile(name).read()) != expected:
                raise ValueError(f'changed built SWF: {name}')
    for name, expected in metadata['sources_sha256'].items():
        if digest((ROOT / name).read_bytes()) != expected:
            raise ValueError(f'changed locked source: {name}')
    added = '\n'.join(line[1:] for line in diff.decode().splitlines()
                      if line.startswith('+') and not line.startswith('+++'))
    start = added.index('onEnterFrame = function()\n{\n   aiDisplay++;')
    end = added.index('\n};', start) + 3
    observer = added[start:end]
    # The archive binds this order to the captured build, not to today's template.
    ordered = ('aiDisplay++;', 'aiFight++;', 'aiHeld = {};',
               'aiEvent("input_next_display"', 'aiState("p1");',
               'aiState("p2");', 'aiEvent("doaction_sample", "root-observer");',
               'if(aiFight >= 60)', 'aiEvent("done", "");', 'fscommand("quit");')
    positions = [observer.index(token) for token in ordered]
    if positions != sorted(positions) or 'capture_window_closed' in observer:
        raise ValueError('unexpected archived observation order')
    text = gzip.decompress((SOURCE / 'rejected-completion-boundary.log.gz').read_bytes()).decode()
    report = analyze(text, metadata['run_id'])
    with tempfile.TemporaryDirectory(prefix='s269-historical-') as directory:
        trace = Path(directory) / 'native.log'
        trace.write_text(text)
        try:
            validate_capture(case, metadata, trace)
        except ValueError as error:
            rejection = str(error)
        else:
            raise ValueError('retained rejected capture unexpectedly admitted')
    if rejection != 'native evidence: events beyond completion boundary':
        raise ValueError(f'changed gate failure: {rejection}')
    calls = collect_calls(text.splitlines(), metadata['callsite_specification'], retain_incomplete=True)
    report['selected_calls'] = {k: v for k, v in calls.items() if k != 'invocations'}
    report['selected_calls']['complete_count'] = len(calls['invocations'])
    report['terminal_invocations'] = [v for v in calls['invocations'] if v['observer_tick'] == 60]
    report.update(input_sha256=inputs, raw_sha256=digest(text.encode()),
                  archived_root_observer=observer,
                  instrumentation_sha256=metadata['instrumentation_sha256'],
                  native_gate={'exit_code': 1, 'error': rejection},
                  production_admitted=False, native_parity_proven=False,
                  trace_trimmed=False, fresh_capture=False, admitted_samples=0)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--strict-native', action='store_true')
    args = parser.parse_args()
    report = diagnose()
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(report['native_gate']['error'])
    return report['native_gate']['exit_code'] if args.strict_native else 0


if __name__ == '__main__':
    raise SystemExit(main())
