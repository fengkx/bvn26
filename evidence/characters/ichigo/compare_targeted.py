"""Compare retained original captures against the completed Godot batch."""
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'tools'), str(ROOT / 'tools/probes')]
from compare_mode_reference import compare
from test_move_cases import target_seen


def raw(path):
    data = path.read_bytes()
    return gzip.decompress(data) if path.suffix == '.gz' else data


def main():
    directory = Path(__file__).resolve().parent
    fixtures = json.loads((directory / 'native-all-batch.json').read_text())
    results = []
    for name in fixtures:
        fixture = Path(name)
        spec = json.loads(fixture.read_text())
        native = directory / 'native-targeted-r02' / (spec['id'] + '.json')
        if not native.exists():
            raise ValueError('Native case is not complete: ' + spec['id'])
        source = next(folder / spec['id'] / 'events.jsonl.gz'
                      for folder in [directory / 'original-r01', directory / 'original-forms-r02',
                                     directory / 'original-base-r02']
                      if (folder / spec['id'] / 'events.jsonl.gz').exists())
        comparison = compare(source, native)
        paths = {'fixture': fixture, 'source': source, 'native': native}
        results.append({'id': spec['id'], 'paths': {k: str(v.relative_to(ROOT)) for k, v in paths.items()},
                        'hashes': {k: hashlib.sha256(raw(v)).hexdigest() for k, v in paths.items()},
                        'target_seen': target_seen(spec, json.loads(native.read_text())),
                        'comparison': comparison})
    log = (directory / 'logs/native-all-r02.log').read_text()
    execution = {'complete_marker': 'MOVE_CASE_BATCH_OK 15' in log,
                 'script_errors': log.count('SCRIPT ERROR'),
                 'resource_loader_errors': log.count('No loader found'),
                 'other_error_lines': [line for line in log.splitlines() if line.startswith('ERROR:')],
                 'exit_residuals': [line for line in log.splitlines() if 'leaked' in line or 'still in use' in line]}
    (directory / 'comparisons.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')
    (directory / 'targeted-execution.json').write_text(json.dumps(execution, indent=2) + '\n')
    print(json.dumps({'cases':len(results), 'matched':sum(r['comparison']['status']=='matched' for r in results),
                      'states':sum(r['comparison']['source_states'] for r in results), 'execution':execution}))
    assert execution['complete_marker'] and not execution['script_errors'] and not execution['resource_loader_errors']
    assert all(r['comparison']['status'] == 'matched' for r in results)


if __name__ == '__main__':
    main()
