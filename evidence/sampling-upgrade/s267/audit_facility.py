"""Inspect the pinned native executable without launching or attaching to a player."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

EXPECTED = '8d4c1f5934adae809b5f4ce4f6ca7c64d4260df46bb3eb9c41fe32be2ee905be'


def audit(binary, output):
    if hashlib.sha256(binary.read_bytes()).hexdigest() != EXPECTED:
        raise ValueError('Native executable differs from s261')
    output.mkdir(parents=True, exist_ok=False)
    commands = {
        'file': ['file', str(binary)],
        'defined-symbols': ['nm', '-U', str(binary)],
        'debug-info': ['dwarfdump', '--debug-info', str(binary)],
        'lldb-symbols': ['lldb', '--batch',
                         '-o', 'settings set target.preload-symbols false',
                         '-o', f'target create --no-dependents "{binary}"',
                         '-o', f'image lookup -r -n "MovieClip|Sprite|unloadMovie|ScriptObject" "{binary.name}"'],
    }
    checks = {}
    for name, command in commands.items():
        started = time.monotonic()
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=45)
            transcript = result.stdout + result.stderr
            code, timed_out = result.returncode, False
        except subprocess.TimeoutExpired as error:
            transcript = (error.stdout or b'') + (error.stderr or b'')
            transcript = transcript.decode(errors='replace')
            code, timed_out = None, True
        path = output / (name + '.txt')
        path.write_text(transcript)
        checks[name] = {'command': command, 'exit_code': code, 'timed_out': timed_out,
                        'elapsed_seconds': time.monotonic() - started,
                        'log': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    report = {'binary': str(binary), 'binary_sha256': EXPECTED,
              'new_player_launches': 0, 'process_attach_attempts': 0,
              'allocation_events_captured': 0, 'checks': checks,
              'limitation': 'Static symbol/type availability only; neither allocation identity nor absence of a possible reverse-engineered facility is proved.'}
    (output / 'audit.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    audit(args.binary, args.output)
