"""Build a minimal attachMovie first-frame and coordinate-property probe."""

import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess

from build_minimal_swf import rect, tag


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ffdec', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--probe', choices=['effect_attach', 'effect_order', 'effect_rename', 'timer_scope'], default='effect_attach')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    count = {'effect_attach': 1, 'effect_order': 4, 'effect_rename': 5, 'timer_scope': 1}[args.probe]
    sprite = tag(39, struct.pack('<HH', 1, count)
                 + (tag(12, b'\0') + tag(1)) * count + tag(0))
    exports = tag(56, struct.pack('<HH', 1, 1) + b'effect\0')
    body = rect(0, 20, 0, 20) + struct.pack('<HH', 30 * 256, 1)
    body += sprite + exports + tag(12, b'\0') + tag(1) + tag(0)
    base = args.output / 'base.swf'
    base.write_bytes(b'FWS' + bytes([8]) + struct.pack('<I', len(body) + 8) + body)
    sources = Path(__file__).parent / 'as2' / args.probe
    scripts = args.output / 'scripts'
    entries = [('root.as', 'frame_1/DoAction.as')]
    for frame in range(1, count + 1):
        source = 'effect.as' if count == 1 else f'effect_{frame}.as'
        entries.append((source, f'DefineSprite_1_effect/frame_{frame}/DoAction.as'))
    for source, target in entries:
        path = scripts / target
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((sources / source).read_bytes())
    output = args.output / 'effect.swf'
    with (args.output / 'build.log').open('w') as log:
        subprocess.run(['java', '-Djava.awt.headless=true', '-jar', str(args.ffdec),
                        '-importScript', str(base), str(output), str(scripts)],
                       check=True, stdout=log, stderr=subprocess.STDOUT)
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    report = {'status': 'built_not_run', 'swf_sha256': sha(output),
              'source_sha256': {path.name: sha(path) for path in sorted(sources.glob('*.as'))},
              'ffdec_sha256': sha(args.ffdec)}
    (args.output / 'build.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
