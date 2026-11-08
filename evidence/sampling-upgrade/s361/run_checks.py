"""Record local evidence gates and unchanged predecessor regressions."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONPATH='.')


def run(name, command, expected=0):
    start = time.monotonic()
    result = subprocess.run(command, cwd=ROOT, env=ENV, capture_output=True, timeout=120)
    (HERE / (name + '.txt')).write_bytes(result.stdout + result.stderr)
    record = dict(name=name, command=command, exit_code=result.returncode,
                  expected_exit=expected, passed=result.returncode == expected,
                  wall_seconds=time.monotonic() - start, log=name + '.txt')
    if not record['passed']:
        raise RuntimeError(record)
    return record


def main():
    spec = importlib.util.spec_from_file_location('s361_checks', HERE / 'diagnose.py')
    d = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(d)
    base = ['python3', 'evidence/sampling-upgrade/s361/diagnose.py', '--output',
            'evidence/sampling-upgrade/s361/diagnosis.json']
    gates = [run('diagnosis', base)]
    for flag in d.GATES:
        gates.append(run(flag, base + ['--require-' + flag], 0 if flag == 'process-window-association' else 1))
    gates.append(run('all-proofs', base + ['--require-' + f for f in d.GATES], 1))
    (HERE / 'gates.json').write_text(json.dumps(gates, indent=2) + '\n')
    checks = []
    previous = json.loads((HERE.parent / 's352/project-checks.json').read_text())
    for record in previous:
        if record['name'].endswith('-tests'):
            checks.append(run(record['name'], ['python3'] + record['command'][1:]))
    checks.append(run('s361-tests', ['python3', '-m', 'unittest', 'discover', '-s',
                                    'evidence/sampling-upgrade/s361', '-p', 'test_*.py']))
    for name, command in [('integrity', ['python3', 'tools/verify.py']),
                          ('handoff', ['python3', 'tools/check_handoff.py']),
                          ('diff-check', ['git', 'diff', '--check'])]:
        checks.append(run(name, command))
    (HERE / 'project-checks.json').write_text(json.dumps(checks, indent=2) + '\n')
    print('All expected exits matched; retained replay equal.')


if __name__ == '__main__':
    main()
