"""Query buffer/cursor metadata on the receipt-pinned executable without launching it."""
import hashlib
import json
from pathlib import Path
import subprocess
import time

HERE = Path(__file__).resolve().parent


def main():
    receipt = json.loads((HERE.parent / 's266/native-receipt.json').read_text())
    binary = receipt['engine']
    digest = hashlib.sha256(Path(binary).read_bytes()).hexdigest()
    if digest != receipt['files'][binary]:
        raise ValueError('player differs from locked s266 receipt')
    prefix = ['lldb', '--batch', '-o', 'settings set target.preload-symbols false',
              '-o', f'target create --no-dependents "{binary}"']
    checks = []
    for name, query in (
        ('buffer-types', 'image lookup -t ActionBuffer'),
        ('buffer-data-types', 'image lookup -t ActionBufferData'),
        ('cursor-symbols', 'image lookup -r -n "(ActionBuffer|ActionExec|ActionContext|AS2.*(Execute|Activation))"'),
    ):
        command = prefix + ['-o', query]
        start = time.monotonic()
        result = subprocess.run(command, capture_output=True, timeout=45)
        raw = result.stdout + result.stderr
        (HERE / (name + '.txt')).write_bytes(raw)
        checks.append(dict(name=name, command=command, exit=result.returncode,
                           elapsed_seconds=time.monotonic() - start,
                           log=name + '.txt', sha256=hashlib.sha256(raw).hexdigest()))
    (HERE / 'facility.json').write_text(json.dumps(dict(binary=binary, binary_sha256=digest,
        checks=checks, launch_requested=False, movie_supplied=False,
        limitation='Name/type lookup only; failure does not rule out stripped-code analysis.'), indent=2) + '\n')


if __name__ == '__main__':
    main()
