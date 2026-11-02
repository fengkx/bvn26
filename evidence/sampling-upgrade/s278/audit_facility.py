"""Probe debugger availability on the receipt-pinned player, without a movie."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

BINARY = '/Volumes/Flash Player/Flash Player.app/Contents/MacOS/Flash Player Debugger'
EXPECTED = '8d4c1f5934adae809b5f4ce4f6ca7c64d4260df46bb3eb9c41fe32be2ee905be'


def audit(output, launch=False):
    if hashlib.sha256(Path(BINARY).read_bytes()).hexdigest() != EXPECTED:
        raise ValueError('Player differs from s266 receipt')
    output.mkdir(parents=True, exist_ok=False)
    prefix = ['lldb', '--batch', '-o', 'settings set target.preload-symbols false',
              '-o', f'target create --no-dependents "{BINARY}"']
    queries = {
        'instruction-breakpoints': ['breakpoint set --shlib "Flash Player Debugger" --func-regex "(ActionCallMethod|ActionPop|ActionSetMember|DoAction|ExecuteAction|AVM1|ActionScript.*(execute|interpret))"', 'breakpoint list'],
        'action-exec-type': ['image lookup -t "ActionExec"'],
        'activation-type': ['image lookup -t "Activation"'],
    }
    if launch:
        queries = {'native-entry': ['process launch --stop-at-entry',
                                  'register read rip rsp rbp', 'thread backtrace', 'process kill']}
    checks = {}
    for name, commands in queries.items():
        command = prefix + [arg for c in commands for arg in ('-o', c)]
        start = time.monotonic()
        result = subprocess.run(command, capture_output=True, timeout=45)
        raw = result.stdout + result.stderr
        path = output / (name + '.txt')
        path.write_bytes(raw)
        checks[name] = {'command': command, 'exit_code': result.returncode,
                        'elapsed_seconds': round(time.monotonic() - start, 6),
                        'log': path.name, 'sha256': hashlib.sha256(raw).hexdigest()}
    report = {'binary': BINARY, 'binary_sha256': EXPECTED, 'checks': checks,
              'launch_requested': launch, 'movie_supplied': False,
              'limit': 'Native CPU registers are not AVM1 PC/operand stack/registers or defining activation. No movie execution is requested.'}
    (output / 'audit.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--launch', action='store_true')
    args = parser.parse_args()
    audit(args.output, args.launch)
