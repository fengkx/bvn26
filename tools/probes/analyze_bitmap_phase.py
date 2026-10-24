#!/usr/bin/env python3
"""Reject or measure an isolated bitmap sampling candidate against native Flash.

This is a CPU diagnostic, not a production shader or a component parity gate.
The extended capture intentionally tests generalization beyond power-of-two scales.
"""
import argparse
import json
import math
from pathlib import Path


def candidate(alpha, scale, phase, extended):
    tx = math.trunc(phase / 256 * 4) / 4
    ty = math.trunc(-phase / 512 * 4) / 4 if extended else 0
    x = (math.floor(scale) + .5 - tx) / scale - .5
    y = (math.floor(scale) + .5 - ty) / scale - .5
    x = math.floor(x * 256) / 256
    y = math.floor(y * 256) / 256
    weights = [math.floor(value * 256) for value in
               ((1 - x) * (1 - y), x * (1 - y), (1 - x) * y)]
    weights.append(256 - sum(weights))
    return [alpha * (weights[i] + weights[3]) // 256 for i in range(3)]


def analyze(text, *, extended=False):
    prefix = 'filter-bitmap-phase-extended-r22-' if extended else 'filter-bitmap-phase-r22-'
    events = [line.split('|') for line in text.splitlines() if line.startswith('AIREF|')]
    scales = (2.5, 3, 5, 8) if extended else (2, 4, 8)
    identities = [(alpha, scale) for alpha in (255, 128) for scale in scales]
    phases = range(-256 if extended else 0, 256)
    if (len(events) != len(identities) + 1 or any(len(e) != 8 for e in events) or
            len({e[1] for e in events}) != 1 or not events[0][1].startswith(prefix) or
            [int(e[2]) for e in events] != list(range(len(events))) or
            events[-1][6:] != ['done', 'ok']):
        raise ValueError('Incomplete, duplicate or mixed native bitmap phase capture')
    groups = []
    for event, (alpha, scale) in zip(events, identities):
        values = event[7].split(',')
        if (event[6] != 'phase' or len(values) != len(phases) + 2 or
                list(map(float, values[:2])) != [alpha, scale]):
            raise ValueError('Native bitmap phase identity/sample count mismatch')
        failures = []
        pixels = list(map(int, values[2:]))
        if any(not 0 <= pixel <= 0xffffff for pixel in pixels):
            raise ValueError('Invalid native RGB pixel')
        for phase, pixel in zip(phases, pixels):
            native = [(pixel >> shift) & 255 for shift in (16, 8, 0)]
            predicted = candidate(alpha, scale, phase, extended)
            if native != predicted:
                failures.append({'phase': phase, 'native_rgb': native, 'candidate_rgb': predicted,
                                 'max_delta': max(abs(a-b) for a,b in zip(native, predicted))})
        groups.append({'alpha': alpha, 'scale': scale, 'samples': len(phases),
                       'exact': len(phases) - len(failures),
                       'max_delta': max((f['max_delta'] for f in failures), default=0),
                       'failures': failures})
    return {'candidate_only': True, 'production_admitted': False,
            'passed': all(not g['failures'] for g in groups),
            'samples': sum(g['samples'] for g in groups), 'exact': sum(g['exact'] for g in groups),
            'groups': groups}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-log', type=Path, required=True)
    parser.add_argument('--extended', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.native_log.read_text(), extended=args.extended)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'groups'}))
    raise SystemExit(0 if result['passed'] else 1)
