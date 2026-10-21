"""Compare native Flash integer-twip bounds with Godot geometry probe rows."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def compare(expected: list[dict], native_directory: Path) -> dict:
    cache = {}
    differences = []
    for sample in expected:
        case = sample['case']
        if case not in cache:
            rows = json.loads((native_directory / (case + '.json.geometry.json')).read_text())
            cache[case] = {row['tick']: row for row in rows}
        row = cache[case][sample['tick']]
        bounds = row['bounds'][sample['attack']]['global_bounds']
        # The probe serializes float32 render vectors. Recover their integer
        # twips for comparison; no tolerance or expansion is allowed.
        actual = [round(bounds['x'] * 20), round(bounds['y'] * 20),
                  round((bounds['x'] + bounds['width']) * 20),
                  round((bounds['y'] + bounds['height']) * 20)]
        if actual != sample['flash_twips']:
            differences.append({**sample, 'godot_twips': actual})
    return {'status': 'matched' if not differences else 'different',
            'rectangles': len(expected), 'differences': differences}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('expected', type=Path)
    parser.add_argument('native', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = compare(json.loads(args.expected.read_text()), args.native)
    if args.output:
        args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
    raise SystemExit(0 if result['status'] == 'matched' else 1)


if __name__ == '__main__':
    main()
