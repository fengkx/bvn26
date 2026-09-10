"""Archive retained originals and recompare a completed native batch exactly."""
import argparse
import gzip
import json
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).parent / 'probes'))
from compare_mode_reference import compare, read_text, source_rows, compare_root_position, cancellation_observation
from audit_move_acceptance import audit


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases', type=Path, required=True)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--references', type=Path, action='append', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--defer-label', action='append', default=[])
    args = parser.parse_args()
    cases = [json.loads(p.read_text()) for p in sorted(args.cases.glob('*.json'))]
    by_id = {case['id']: case for case in cases}
    native_results = json.loads((args.native / 'results.json').read_text())
    if {row['id'] for row in native_results} != set(by_id):
        raise ValueError('Native batch is incomplete or belongs to another fixture matrix')
    originals = {}
    for root in args.references:
        index = root / 'results.json'
        if not index.exists():
            index = root / 'reference-results.json'
        for row in json.loads(index.read_text()):
            folder = root / row['id']
            if not folder.exists():
                folder = root / 'references' / row['id']
            if row['id'] in originals and originals[row['id']][0]['status'] != 'capture_failed':
                raise ValueError('Multiple valid originals require explicit selection: ' + row['id'])
            originals[row['id']] = row, folder
    args.output.mkdir(parents=True, exist_ok=False)
    write_json(args.output / 'cases.json', cases)
    write_json(args.output / 'native-results.json', native_results)
    references = []
    for name, (previous, folder) in originals.items():
        if previous['status'] == 'capture_failed':
            references.append(previous)
            continue
        destination = args.output / 'references' / name
        destination.mkdir(parents=True)
        for path in folder.iterdir():
            if not path.is_file():
                continue
            # Keep the earlier comparison and native trace alongside the new one.
            target = destination / path.name
            if path.suffix == '.gz':
                shutil.copy(path, target)
            else:
                with gzip.open(str(target) + '.gz', 'wb') as stream:
                    stream.write(path.read_bytes())
        events = folder / 'events.jsonl'
        if not events.exists():
            events = folder / 'events.jsonl.gz'
        native = args.native / (name + '.json')
        result = compare(events, native)
        build_path = folder / 'build.json'
        if not build_path.exists(): build_path = folder / 'build.json.gz'
        build = json.loads(read_text(build_path))
        if build.get('presentation_probe'):
            presentation = Path(str(native) + '.presentation.json')
            root_result = compare_root_position(events, presentation)
            with gzip.open(destination / 'root-position-current.json.gz', 'wt') as stream:
                json.dump(root_result, stream)
            with gzip.open(destination / 'native-presentation-current.json.gz', 'wb') as stream:
                stream.write(presentation.read_bytes())
            result['root_position'] = root_result['status']
            if root_result['status'] != 'matched': result['status'] = 'different'
        case = by_id[name]
        if 'window_boundary' in case:
            result['cancellation'] = cancellation_observation(source_rows(events), case)
            if result['cancellation']['status'] != 'calibrated':
                result['status'] = 'invalid_calibration'
        low, high = case['target_frames']
        def reached(rows):
            return any(row['slot'] == case['slot'] and low is not None
                       and low <= row['frame'] <= high for row in rows)
        result['target_seen'] = reached(json.loads(read_text(native)))
        result['source_target_seen'] = reached(source_rows(events))
        if result['status'] == 'matched' and not result['source_target_seen'] and low is not None and case['scenario'] != 'energy_below':
            result['status'] = 'unexercised'
        with gzip.open(destination / 'native-current.json.gz', 'wb') as stream:
            stream.write(native.read_bytes())
        with gzip.open(destination / 'comparison-current.json.gz', 'wt') as stream:
            json.dump(result, stream)
        references.append({key: value for key, value in result.items() if key != 'differences'}
                          | {'id': name, 'different_states': len(result['differences'])})
    write_json(args.output / 'reference-results.json', references)
    coverage = audit(cases, native_results, references, args.defer_label)
    write_json(args.output / 'coverage.json', coverage)
    print(json.dumps({'status': coverage['status'], 'case_counts': coverage['case_counts']}))


if __name__ == '__main__':
    main()
