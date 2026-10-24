#!/usr/bin/env python3
"""Require complete, exact image and playhead comparisons for filter components."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def validate_raster_inputs(folder: Path, cases: list[dict]) -> None:
    """Do not accept a missing native child as an unfiltered observation."""
    expected = {case['id'] for case in cases if case.get('raster_input_only')}
    if not expected:
        return
    events = [line.split('|') for line in (folder / 'native.log').read_text().splitlines()
              if line.startswith('AIREF|')]
    if any(event[6] == 'input_error' for event in events):
        raise ValueError('Native raster-input child lookup failed')
    observed = [event[7].split(',') for event in events if event[6] == 'raster_input']
    if (len(observed) != len(expected) or
            {row[0] for row in observed} != expected or
            any(row[1:] != ['0', 'false'] for row in observed)):
        raise ValueError('Missing or invalid native raster-input filter/cache observation')
    for case in cases:
        if case.get('raster_input_only') and any(
                key in case['placement'] for key in ('filters', 'cache_as_bitmap')):
            raise ValueError('Godot raster-input placement still contains filter/cache')


def compare(output: Path) -> dict:
    subprocess.run([sys.executable, str(ROOT / 'evidence/characters/pain/visual-parity/review/probes/compare_components.py')],
                   cwd=ROOT, env={**os.environ, 'BVN_REVIEW_DIR': str(output)}, check=True)
    reports = json.loads((output / 'component-comparisons.json').read_text())
    expected = set()
    placements = 0
    for path in sorted((output / 'components').glob('*/cases.json')):
        cases = json.loads(path.read_text())
        validate_raster_inputs(path.parent, cases)
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
