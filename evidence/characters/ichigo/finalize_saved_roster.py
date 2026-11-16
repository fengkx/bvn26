"""Join accepted partial and resumed runs without hiding exit diagnostics."""
import json
from pathlib import Path
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
from test_move_cases import target_seen

EVIDENCE = Path(__file__).resolve().parent
PRIOR = ROOT.parent / '.cache/ichigo-lane3-saved-regression/flash-replay'
RESUMED = ROOT.parent / '.cache/ichigo-lane3-regression-resume/flash-replay'


def main():
    partial = json.loads((EVIDENCE / 'saved-roster-partial.json').read_text())
    resumed = json.loads((RESUMED / 'report.json').read_text())
    results = []
    for row in partial['results']:
        fixture = ROOT / row['fixture']
        native = PRIOR / row['id'] / (fixture.stem + '.json')
        states = json.loads(native.read_text())
        results.append({'id': row['id'], 'provenance': 'accepted_partial',
                        'execution': {'executed': True, 'exit': 0, 'timed_out': False,
                                      'states': len(states), 'target_seen': target_seen(json.loads(fixture.read_text()), states)},
                        'comparison': row['comparison']})
    results.extend({**row, 'provenance': 'resumed'} for row in resumed['results'])
    assert len(results) == len({row['id'] for row in results}) == 300
    assert all(row['execution']['executed'] and row['comparison']['status'] == 'matched'
               for row in results)
    exit_errors = []
    unexpected = []
    for row in results:
        folder = (PRIOR if row['provenance'] == 'accepted_partial' else RESUMED) / row['id']
        log = (folder / 'process.log').read_text()
        assert 'SCRIPT ERROR' not in log and 'MOVE_CASE_REFERENCE_OK' in log
        for line in log.splitlines():
            if line.startswith('ERROR:') or 'leaked at exit' in line:
                item = {'id': row['id'], 'line': line}
                exit_errors.append(item)
                if not any(text in line for text in ['still in use at exit', 'leaked at exit', 'RID allocations']):
                    unexpected.append(item)
    assert not unexpected, unexpected
    summary = {'status': 'exact_actor_states_matched_with_unaccepted_exit_residuals',
               'cases': 300, 'accepted_prior': len(partial['results']), 'resumed': len(resumed['results']),
               'source_states': sum(row['comparison']['source_states'] for row in results),
               'native_states': sum(row['comparison']['native_states'] for row in results),
               'resume_seconds': resumed['seconds'], 'exit_residuals': exit_errors,
               'target_not_seen': [row['id'] for row in results if not row['execution']['target_seen']],
               'scope': 'Preserved negative, overlap and interrupted fixtures; target absence is not counted as move coverage. Exit resource leaks remain unaccepted.'}
    (EVIDENCE / 'saved-roster-full-results.json').write_text(json.dumps({'summary': summary, 'results': results}, indent=2) + '\n')
    with tarfile.open(EVIDENCE / 'saved-roster-resumed.tar.gz', 'w:gz') as archive:
        archive.add(RESUMED, arcname='flash-replay')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
