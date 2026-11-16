"""Retry only incomplete source captures after acquiring the external lane lock."""
import json
from pathlib import Path
import shutil
import subprocess
import sys

root = Path(__file__).resolve().parents[3]
evidence = root / 'evidence/characters/ichigo'
cache = root.parent / '.cache'
prior = cache / 'ichigo-lane3-original-form-actions-r01/results.json'
results = json.loads(prior.read_text())
print(type(results).__name__, flush=True)
rows = results if isinstance(results, list) else results['results']
failed = {row['id'] for row in rows if row['status'] != 'captured_source_only'}
cases = cache / 'ichigo-lane3-form-retry-cases'
cases.mkdir(exist_ok=False)
for case in (evidence / 'form-action-cases').glob('*.json'):
    if json.loads(case.read_text())['id'] in failed:
        shutil.copyfile(case, cases / case.name)
if failed:
    subprocess.run([sys.executable, 'tools/test_move_references.py', '--probe',
                    str(cache / 'ichigo-lane3-timer-probe-r02'), '--cases', str(cases),
                    '--native', str(cache / 'ichigo-lane3-native'), '--output',
                    str(cache / 'ichigo-lane3-original-form-actions-r02'), '--capture-runner',
                    str(evidence / 'capture_with_budget.py'), '--capture-only',
                    '--allow-window-activation', '--player-app',
                    '/Users/fengkx/me/code/flash-player/Flash Player.app'], cwd=root, check=True)
print('FORM_RETRY_COMPLETE', len(failed))
