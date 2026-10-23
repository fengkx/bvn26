#!/usr/bin/env python3
"""Require complete, exact image and playhead comparisons for filter components."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def compare(output: Path) -> dict:
    subprocess.run([sys.executable, str(ROOT / 'evidence/characters/pain/visual-parity/review/probes/compare_components.py')],
                   cwd=ROOT, env={**os.environ, 'BVN_REVIEW_DIR': str(output)}, check=True)
    reports = json.loads((output / 'component-comparisons.json').read_text())
    expected = set()
    placements = 0
    for path in sorted((output / 'components').glob('*/cases.json')):
        cases = json.loads(path.read_text())
        placements += len(cases)
        expected.update((case['id'], tick) for case in cases for tick in case['samples'])
    images = [image for report in reports for image in report['images']]
    observed = {(image['case'], image['tick']) for image in images}
    if not expected or observed != expected or len(observed) != len(images):
        raise ValueError(f'Incomplete component image coverage: missing={sorted(expected - observed)} '
                         f'extra={sorted(observed - expected)}')
    matched = sum(image['max_error'] == 0 for image in images)
    clock_differences = sum(len(report['differences']) for report in reports)
    result = {'passed': matched == len(images) and clock_differences == 0,
              'placements': placements, 'images': len(images), 'images_matched': matched,
              'clock_samples': sum(report['clock_samples'] for report in reports),
              'clock_differences': clock_differences, 'sources': reports}
    (output / 'strict-comparison.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = compare(args.output.resolve())
    print(json.dumps({key: value for key, value in result.items() if key != 'sources'}))
    raise SystemExit(0 if result['passed'] else 1)
