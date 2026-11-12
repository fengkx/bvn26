"""Bind a completed G0 Web export to exact artifact hashes and browser instrumentation."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil


def package(stage: Path, web: Path):
    for suffix in ('html', 'js', 'wasm', 'pck'):
        if not (web / f'index.{suffix}').is_file():
            raise ValueError(f'Missing index.{suffix}; export first')
    identity = json.loads((stage / 'g0/identity.json').read_text())
    for relative, expected in identity['files'].items():
        if relative == 'export_presets.cfg':
            continue  # Binding the local template is an explicit build step.
        if hashlib.sha256((stage / relative).read_bytes()).hexdigest() != expected:
            raise ValueError(f'Staged source changed after freezing: {relative}')
    identity['bound_export_presets_sha256'] = hashlib.sha256((stage / 'export_presets.cfg').read_bytes()).hexdigest()
    shutil.copy2(stage / 'g0/g0-browser.js', web / 'g0-browser.js')
    (web / 'g0-identity.json').write_text(json.dumps(identity, indent=2))
    artifacts = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in sorted(web.iterdir()) if p.is_file() and p.name != 'g0-artifacts.json'}
    (web / 'g0-artifacts.json').write_text(json.dumps(artifacts, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', type=Path, required=True)
    parser.add_argument('--web', type=Path, required=True)
    args = parser.parse_args()
    package(args.stage, args.web)
