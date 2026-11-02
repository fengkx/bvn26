"""Bounded static resolver and allocator-import audit on the s261 executable."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

BINARY = Path('/Volumes/Flash Player/Flash Player.app/Contents/MacOS/Flash Player Debugger')
EXPECTED = '8d4c1f5934adae809b5f4ce4f6ca7c64d4260df46bb3eb9c41fe32be2ee905be'


def audit(output):
    if hashlib.sha256(BINARY.read_bytes()).hexdigest() != EXPECTED:
        raise ValueError('Player differs from s261 receipt')
    output.mkdir(parents=True, exist_ok=False)
    prefix = ['lldb', '--batch', '-o', 'settings set target.preload-symbols false',
              '-o', f'target create --no-dependents "{BINARY}"']
    commands = {
        'module-uuid': ['dwarfdump', '--uuid', str(BINARY)],
        'indirect-symbols': ['otool', '-Iv', str(BINARY)],
        'resolver-breakpoints': prefix + ['-o', 'breakpoint set --shlib "Flash Player Debugger" --func-regex "(GetInstanceAtDepth|getInstanceAtDepth|GetDisplayObject|GetMember|MovieClipObject|MovieClipRef|ResolvePath|ResolveTarget|UnloadMovie|unloadMovie)"', '-o', 'breakpoint list'],
        'reference-type': prefix + ['-o', 'image lookup -t "MovieClipObject"'],
        'allocator-stubs': prefix + ['-o', 'image lookup -r -n "^(malloc|calloc|realloc|free)$" "Flash Player Debugger"'],
    }
    checks = {}
    for name, command in commands.items():
        start = time.monotonic()
        result = subprocess.run(command, capture_output=True, timeout=45)
        raw = result.stdout + result.stderr
        path = output / (name + '.txt')
        path.write_bytes(raw)
        checks[name] = {'command': command, 'exit_code': result.returncode,
                        'elapsed_seconds': round(time.monotonic() - start, 6),
                        'log': path.name, 'sha256': hashlib.sha256(raw).hexdigest()}
    report = {'binary': str(BINARY), 'binary_sha256': EXPECTED, 'checks': checks,
              'player_launches': 0, 'new_captures': 0, 'allocation_events_observed': 0,
              'limitation': 'Import stubs are candidates only: no slot, saved reference, object layout or native generation is resolved.'}
    (output / 'audit.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    audit(parser.parse_args().output)
