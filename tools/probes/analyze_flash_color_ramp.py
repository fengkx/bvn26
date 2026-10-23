#!/usr/bin/env python3
"""Measure native ColorMatrix ramps; inferred intervals are not runtime rules."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

PREFIX = 'AIREF|filter-color-arithmetic-ramp-r12|'


def analyze(text: str) -> dict:
    events = [line.split('|') for line in text.splitlines() if line.startswith(PREFIX)]
    if len(events) != 17 or any(len(event) != 8 for event in events):
        raise ValueError('Expected exactly 17 native ramp events')
    if [int(event[2]) for event in events] != list(range(17)) or events[-1][6:] != ['done', 'ok']:
        raise ValueError('Incomplete or reordered native ramp')
    rows = []
    for index, (opacity, mode) in enumerate((a, m) for a in (100, 80) for m in range(4)):
        samples = []
        for event, kind in zip(events[index * 2:index * 2 + 2], ('color', 'black')):
            values = list(map(int, event[7].split(',')))
            if event[6] != kind or values[:2] != [opacity, mode] or len(values) != 258:
                raise ValueError('Mismatched native ramp identity or sample count')
            samples.append(values[2:])
        alpha = 255 if opacity == 100 else 204
        if any((value >> 24) & 255 != alpha for value in samples[0]):
            raise ValueError('Unexpected source alpha in native ramp')
        if any((value >> 24) & 255 != 255 for value in samples[1]):
            raise ValueError('Native RGB must be observed over opaque black')
        rows.append({'opacity': opacity, 'mode': mode, 'premultiplied': [
            [(black >> 16) & 255, (black >> 8) & 255, black & 255, alpha]
            for black in samples[1]]})
    diagnostics = []
    coefficients = [-0.5946631, 1.0937881, 0.10156211]
    for row in rows[:4]:
        mode = row['mode']
        differences = []
        for value, pixel in enumerate(row['premultiplied']):
            expected_float = [
                -.5946631 * value + 1.0937881 * 127 + .5008749 * 170 + 9,
                -.5946631 * value + 128, 1.0937881 * value, .10156211 * value][mode]
            expected = max(0, min(255, math.floor(expected_float + .5)))
            if expected != pixel[0]:
                differences.append({'input': value, 'native_red': pixel[0], 'float_model_red': expected})
        diagnostic = {'opacity': 100, 'mode': mode, 'different_from_float_model': len(differences),
                      'differences': differences}
        if mode:
            offset = 128 if mode == 1 else 0
            interior = [(value, pixel[0]) for value, pixel in enumerate(row['premultiplied'])
                        if value and 0 < pixel[0] < 255]
            diagnostic['source_coefficient'] = coefficients[mode - 1]
            diagnostic['coefficient_interval_if_round_nearest_affine'] = [
                max((red - .5 - offset) / value for value, red in interior),
                min((red + .5 - offset) / value for value, red in interior)]
        diagnostics.append(diagnostic)
    return {'native_cases': 2048, 'native_events': 17,
            'model_note': 'Opaque float-model diagnostics only; intervals assume nearest-rounded affine output. '
                          'They do not identify the native algorithm or certify Godot parity.',
            'opaque_float_diagnostics': diagnostics}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-log', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = analyze(args.native_log.read_text())
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'native_cases': report['native_cases'], 'native_events': report['native_events'],
                      'float_model_different': sum(row['different_from_float_model']
                                                  for row in report['opaque_float_diagnostics'])}))
