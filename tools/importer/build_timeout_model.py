"""Compile the original countdown and timeout timeline using shared round tooling."""
import argparse
import hashlib
import json
from pathlib import Path
import re

from build_ko_assets import build as build_assets
from compile_ko import build as compile_timeline, compile_body

ROOT = Path(__file__).resolve().parents[2]


def build(workspace: Path) -> None:
    output = ROOT/'godot/generated/main/timeout'
    audit = ROOT/'evidence/config-timeout-source.json'
    build_assets(workspace, output, audit, 'timeover')
    compile_timeline(audit, output)
    sources = {s['path']: s['source'] for s in json.loads((ROOT/'scripts/main.json').read_text())['scripts']}
    path = 'DefineSprite_1813/frame_1/DoAction.as'
    source = sources[path]
    callback = re.search(r'time = function\(\)\s*\{(.*?)\};', source, re.S)[1]
    code = '# Generated from the original countdown callback.\nextends RefCounted\nvar adapter: RefCounted\n\n'
    (output/'timer.gd').write_text(code + compile_body('time', callback))
    unlimited, training = re.search(r'if\(_root.maxtime == (\d+) or _root.modo == (\d+)\)', source).groups()
    (output/'timer.json').write_text(json.dumps({'source':path,'sha256':hashlib.sha256(source.encode()).hexdigest(),
        'source_text':source,'interval_ms':int(re.search(r'setInterval\(time,(\d+)\)',source)[1]),
        'unlimited_value':int(unlimited),'training_mode':int(training)},indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    build(parser.parse_args().workspace)
