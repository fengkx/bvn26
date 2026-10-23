#!/usr/bin/env python3
"""Build isolated native Flash filter probes from checked-in ActionScript."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess

from build_minimal_swf import rect, tag

FIXTURES = Path(__file__).with_name('flash_filters')
ROOT = Path(__file__).resolve().parents[2]


def build(case: str, output: Path, ffdec: Path) -> dict:
    output = output.resolve()
    for locked in (ROOT / 'game', ROOT / 'scripts'):
        if output == locked or locked in output.parents:
            raise ValueError(f'Probe output cannot overwrite locked input: {output}')
    source = FIXTURES / f'{case}.as'
    text = source.read_text()
    run_id = re.search(r'AIREF\|([^|]+)\|', text)[1]
    extent = 70 if case == 'blur-small' else 160
    (output / 'scripts/frame_1').mkdir(parents=True, exist_ok=True)
    (output / 'game').mkdir(exist_ok=True)
    shutil.copy2(source, output / 'scripts/frame_1/DoAction.as')
    body = (rect(0, extent * 20, 0, extent * 20)
            + struct.pack('<HH', 30 * 256, 1) + tag(12, b'\0') + tag(1) + tag(0))
    (output / 'base.swf').write_bytes(b'FWS' + bytes([8]) + struct.pack('<I', len(body) + 8) + body)
    subprocess.run(['java', f'-Duser.home={output}', '-Djava.awt.headless=true',
                    '-jar', str(ffdec.resolve()), '-importScript', str(output / 'base.swf'),
                    str(output / 'game/main.swf'), str(output / 'scripts')], check=True)
    report = {'run_id': run_id, 'case': case,
              'source': str(source.relative_to(ROOT)),
              'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
              'ffdec_sha256': hashlib.sha256(ffdec.read_bytes()).hexdigest(),
              'outputs_sha256': {'game/main.swf': hashlib.sha256(
                  (output / 'game/main.swf').read_bytes()).hexdigest()}}
    (output / 'build.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=sorted(p.stem for p in FIXTURES.glob('*.as')), required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--ffdec', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.case, args.output, args.ffdec), indent=2))
