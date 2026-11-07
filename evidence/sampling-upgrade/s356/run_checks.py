"""Record local evidence gates and unchanged predecessor regressions."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
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
    spec = importlib.util.spec_from_file_location('s356_checks', HERE / 'diagnose.py')
    d = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(d)
    base = ['python3', 'evidence/sampling-upgrade/s356/diagnose.py', '--output',
            'evidence/sampling-upgrade/s356/diagnosis.json']
    gates = [run('diagnosis', base)]
    for flag in d.GATES:
        gates.append(run(flag, base + ['--require-' + flag], 1))
    gates.append(run('all-proofs', base + ['--require-' + f for f in d.GATES], 1))
    (HERE / 'gates.json').write_text(json.dumps(gates, indent=2) + '\n')
    checks = []
    with tempfile.TemporaryDirectory(prefix='s356-reextract-') as tmp:
        output = Path(tmp) / 'debug-route.json'
        checks.append(run('reextract', ['python3', 'evidence/sampling-upgrade/s356/probe_debug_route.py',
                                        '--output', str(output)]))
        if output.read_bytes() != (HERE / 'debug-route.json').read_bytes():
            raise ValueError('Disk re-extraction differs')
        checks[-1]['entire_record_equal'] = True
    previous = json.loads((HERE.parent / 's347/project-checks.json').read_text())
    for record in previous:
        if record['name'].endswith('-tests'):
            checks.append(run(record['name'], ['python3'] + record['command'][1:]))
    checks.append(run('s356-tests', ['python3', '-m', 'unittest', 'discover', '-s',
                                    'evidence/sampling-upgrade/s356', '-p', 'test_*.py']))
    for name, command in [('integrity', ['python3', 'tools/verify.py']),
                          ('handoff', ['python3', 'tools/check_handoff.py']),
                          ('diff-check', ['git', 'diff', '--check'])]:
        checks.append(run(name, command))
    (HERE / 'project-checks.json').write_text(json.dumps(checks, indent=2) + '\n')
    print('All expected exits matched; re-extraction equal.')


if __name__ == '__main__':
    main()
