"""Classify the complete s228 rejection; never admit a shortened capture."""
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
SOURCE = HERE.parent / 's228'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def verify_pins(root, pins):
    for name, expected in pins.items():
        if digest((root / name).read_bytes()) != expected:
            raise ValueError('changed retained input: ' + name)


def load_classifier():
    spec = importlib.util.spec_from_file_location('s269_classify', HERE.parent / 's269/classify.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def periods(rows):
    result = []
    for row in rows:
        key = (row['tick'], row['display'])
        if not result or key != (result[-1]['tick'], result[-1]['display']):
            result.append({'tick': key[0], 'display': key[1], 'events': []})
        result[-1]['events'].append(row)
    for period in result:
        period['kind_counts'] = dict(Counter(r['kind'] for r in period['events']))
    return result


def diagnose():
    verify_pins(ROOT, json.loads((HERE / 'input-sha256.json').read_text()))
    verify_pins(SOURCE, json.loads((SOURCE / 'artifact-sha256.json').read_text()))
    classifier = load_classifier()
    metadata = json.loads((SOURCE / 'native-build.json').read_text())
    if not metadata['sampling_doaction'] or any(metadata['sampling_' + name]
            for name in ('geometry', 'display', 'bitmap', 'clipaction', 'callsite')):
        raise ValueError('not standalone DoAction')
    with tarfile.open(SOURCE / 'native-build.tar.gz') as archive:
        if json.load(archive.extractfile('build.json')) != metadata:
            raise ValueError('archive metadata differs')
        diff = archive.extractfile('instrumentation.diff').read()
        if digest(diff) != metadata['instrumentation_sha256']:
            raise ValueError('changed instrumentation')
        for name, expected in metadata['outputs_sha256'].items():
            if digest(archive.extractfile(name).read()) != expected:
                raise ValueError('changed built SWF: ' + name)
    verify_pins(ROOT, metadata['sources_sha256'])
    added = '\n'.join(line[1:] for line in diff.decode().splitlines()
                      if line.startswith('+') and not line.startswith('+++'))
    start = added.index('onEnterFrame = function()\n{\n   aiDisplay++;')
    observer = added[start:added.index('\n};', start) + 3]
    tokens = ('aiDisplay++;', 'aiFight++;', 'aiHeld = {};',
              'aiEvent("input_next_display"', 'aiState("p1");', 'aiState("p2");',
              'aiEvent("doaction_sample", "root-observer");', 'if(aiFight >= 60)',
              'aiEvent("done", "");', 'fscommand("quit");')
    positions = [observer.index(token) for token in tokens]
    if positions != sorted(positions) or 'capture_window_closed' in observer:
        raise ValueError('unexpected root observer order')
    raw = gzip.decompress((SOURCE / 'native-capture.log.gz').read_bytes())
    report = classifier.analyze(raw.decode(), metadata['run_id'])
    with tempfile.TemporaryDirectory(prefix='s280-') as directory:
        path = Path(directory) / 'native.log'
        path.write_bytes(raw)
        case = json.loads((SOURCE / 'ichigo__attack__neutral__ground__near.json').read_text())
        try:
            validate_capture(case, metadata, path)
        except ValueError as error:
            rejection = str(error)
        else:
            raise ValueError('historical rejection unexpectedly admitted')
    if rejection != 'native evidence: events beyond completion boundary':
        raise ValueError('changed native rejection: ' + rejection)
    controls = {}
    for mode in ('normal', 'held'):
        base = HERE.parent / 's269' / mode
        meta = json.loads((base / 'native-build.json').read_text())
        text = gzip.decompress((base / 'native-capture.log.gz').read_bytes()).decode()
        prior = classifier.analyze(text, meta['run_id'])
        controls[mode] = {
            'event_count': prior['event_count'],
            'post_done_periods': periods(prior['terminal_period_callbacks'] + prior['later_root_events']),
            'all_action_sample_count': prior['all_action_sample_count'],
            'scope': 'locked s269 Sasuke callsite only; not s228 execution proof',
        }
    report.update(
        scope='AFTER-s272 rank 8 only', base='343d1dbb', selected_case='s228 standalone Ichigo zero-stage DoAction',
        raw_sha256=digest(raw), archived_root_observer=observer,
        instrumentation_sha256=metadata['instrumentation_sha256'],
        suffix_periods=periods(report['terminal_period_callbacks'] + report['later_root_events']),
        native_gate={'exit_code': 1, 'error': rejection},
        normal_quit_controls=controls, new_builds=0, new_captures=0,
        completion_fix_proved=False, terminal_callback_completeness_proved=False,
        production_admitted=False, native_parity_proven=False, admitted_samples=0,
        trace_trimmed=False, product_obligations_closed=0,
        next_discriminator='Independent opt-in s228 normal/held pair; guard before next root increment, preserve whole terminal period; separately report normal quit truncation and strict DoAction/full-AS failures.')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--strict-native', action='store_true')
    parser.add_argument('--require-completion-proof', action='store_true')
    args = parser.parse_args()
    report = diagnose()
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    if args.strict_native:
        print(report['native_gate']['error'])
        return 1
    if args.require_completion_proof:
        print('COMPLETION_UNPROVED: no independent s228 normal/held execution')
        return 1
    print('DIAGNOSIS_RECOMPUTED: complete historical suffix retained; no admission')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
