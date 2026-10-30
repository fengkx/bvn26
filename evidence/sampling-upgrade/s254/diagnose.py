"""Read-only s232 completion-boundary diagnosis; never seal or trim a capture."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import tarfile
import tempfile

from tools.sampling_native import validate_capture

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'evidence/sampling-upgrade/s232'


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
        'terminal_geometry_events': [r for r in rows if r['tick'] == first['tick']
                                     and r['kind'].startswith('geometry_')],
        'all_geometry_begin_count': sum(r['kind'] == 'geometry_begin' for r in rows),
        'all_geometry_end_count': sum(r['kind'] == 'geometry_end' for r in rows),
    }


def diagnose():
    hashes = json.loads((SOURCE / 'artifact-sha256.json').read_text())
    names = ('native-capture.log.gz', 'native-build.json', 'native-build.tar.gz',
             'yijiao__attack__neutral__ground__near.json')
    inputs = {}
    for name in names:
        actual = digest((SOURCE / name).read_bytes())
        if actual != hashes[name]:
            raise ValueError(f'changed retained input: {name}')
        inputs[str((SOURCE / name).relative_to(ROOT))] = actual
    metadata = json.loads((SOURCE / 'native-build.json').read_text())
    case = json.loads((SOURCE / names[-1]).read_text())
    with tarfile.open(SOURCE / 'native-build.tar.gz') as archive:
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
               'aiState("p2");', '_root.aiGeometrySample();',
               'if(aiFight >= 60)', 'aiEvent("done", "");', 'fscommand("quit");')
    positions = [observer.index(token) for token in ordered]
    if positions != sorted(positions) or 'capture_window_closed' in observer:
        raise ValueError('unexpected archived observation order')
    text = gzip.decompress((SOURCE / 'native-capture.log.gz').read_bytes()).decode()
    report = analyze(text, metadata['run_id'])
    with tempfile.TemporaryDirectory(prefix='s254-') as directory:
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
