"""Rebuild the native AS2 binary64 trace encoding probe without game assets."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from build_minimal_swf import build


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ffdec', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parents[2]
    sources = [root / 'tools/probes/as2/ai_reference/number.as',
               root / 'tools/probes/as2/number_encoding/cases.as']
    frame = args.output / 'scripts/frame_1/DoAction.as'
    frame.parent.mkdir(parents=True)
    frame.write_text('\n'.join(path.read_text() for path in sources))
    base = args.output / 'base.swf'
    base.write_bytes(build(1))
    output = args.output / 'number.swf'
    with (args.output / 'build.log').open('w') as log:
        subprocess.run(['java', '-Djava.awt.headless=true', '-jar', str(args.ffdec),
                        '-importScript', str(base), str(output), str(args.output / 'scripts')],
                       check=True, stdout=log, stderr=subprocess.STDOUT)
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    report = {'status': 'built_not_run', 'swf_sha256': sha(output),
              'sources_sha256': {str(path.relative_to(root)): sha(path) for path in sources},
              'ffdec_sha256': sha(args.ffdec)}
    (args.output / 'build.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
