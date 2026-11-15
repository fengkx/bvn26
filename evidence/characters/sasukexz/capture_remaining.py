"""Capture queued cases under the caller's exclusive desktop lock; stop on failure."""
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tools/probes'))
from compare_mode_reference import compare

sets = [
    ('cases', 'probe-r01', 'native-r01'),
    ('interaction-cases', 'probe-r01', 'native-interaction-r01'),
    ('negative-cases', 'probe-negative-r01', 'native-negative-r01'),
    ('lifecycle-cases', 'probe-lifecycle-r01', 'native-lifecycle-r01'),
    ('followup-cases-r02', 'probe-lifecycle-r01', 'native-followup-r02'),
]
results = []
for cases, probe, native in sets:
    for fixture in sorted((OUT / cases).glob('*.json')):
        case = json.loads(fixture.read_text())
        if case['id'] in ('sasukexz-upper-attack', 'sasukexz-repeat-followup'):
            continue
        state = subprocess.check_output(['ioreg', '-n', 'Root', '-d1'], text=True)
        unlocked = re.search(r'"IOConsoleLocked"\s*=\s*No\b', state) is not None
        if not unlocked:
            print('DESKTOP_LOCKED_OR_UNKNOWN_STOP', flush=True)
            raise SystemExit(2)
        directory = OUT / 'original-batch-r01'
        command = [sys.executable, str(ROOT / 'tools/test_move_references.py'),
                   '--probe', str(OUT / probe), '--cases', str(OUT / cases),
                   '--native', str(OUT / native), '--output', str(directory),
                   '--capture-runner', str(ROOT / 'tools/probes/capture_native_player.py'),
                   '--capture-only', '--allow-window-activation',
                   '--player-app', '/Volumes/Flash Player/Flash Player.app',
                   '--case-id', case['id']]
        run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        (OUT / 'logs' / (case['id'] + '-capture.log')).write_text(run.stdout + run.stderr)
        source = directory / case['id'] / 'events.jsonl'
        if run.returncode or not source.exists():
            print('CAPTURE_FAILED_STOP ' + case['id'], flush=True)
            raise SystemExit(1)
        result = compare(source, OUT / native / (case['id'] + '.json'))
        result.update(id=case['id'], fixture=str(fixture.relative_to(ROOT)),
                      source=str(source.relative_to(ROOT)),
                      native=str((OUT / native / (case['id'] + '.json')).relative_to(ROOT)))
        results.append(result)
        (OUT / 'batch-comparisons-r01.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps({'id':case['id'],'status':result['status'],'states':result['source_states'],
                          'first_difference':result['differences'][:1]}), flush=True)
        if result['status'] != 'matched':
            raise SystemExit(1)
print('CAPTURE_AND_COMPARE_COMPLETE', len(results), flush=True)
