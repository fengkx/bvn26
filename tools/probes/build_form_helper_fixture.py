"""Generate source-owned BODY transformation helpers, not publishable profiles."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/importer'))
from compile_ai_body import compile_body

SOURCES = [('daitu', 458), ('minren', 764), ('Sasuke', 603), ('yihu', 638),
           ('Byakuya', 631), ('rifagu', 638), ('rukia', 533)]


def build(output):
    output.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, sprite in SOURCES:
        bundle = json.loads((ROOT / f'scripts/fighter/{name}.json').read_text())
        code, metadata = compile_body(bundle, sprite, player=True, form_helpers=True)
        filename = name.lower() + '.gd'
        (output / filename).write_text(code)
        rows.append({'fighter': name, 'script': filename, 'metadata': metadata})
    (output / 'sources.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    build(parser.parse_args().output)
