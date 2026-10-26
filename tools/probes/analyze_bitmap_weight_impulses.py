#!/usr/bin/env python3
"""Inspect independent corner responses, without selecting production span arithmetic."""
import argparse
from collections import defaultdict
import json
from pathlib import Path


def analyze(text):
    expected = [(corner, mode, scale, tx, ty, start, length)
                for mode in (0, 1) for corner in range(4) for scale in (2.5, 5, 8)
                for tx in (-.5, .75) for ty in (.25, -.25)
                for start in (3, 4, 5) for length in (1, 4, 5)]
    events = [line.split('|') for line in text.splitlines() if line.startswith('AIREF|')]
    if (len(events) != len(expected)+1 or any(len(e) != 8 for e in events)
            or len({e[1] for e in events}) != 1
            or not events[0][1].startswith('filter-bitmap-weight-impulses-r26-')
            or [int(e[2]) for e in events] != list(range(len(events)))
            or events[-1][6:] != ['done', 'ok']):
        raise ValueError('Incomplete, mixed or duplicate impulse capture')
    groups = defaultdict(dict)
    constant = samples = 0
    for event, identity in zip(events, expected):
        values = event[7].split(',')
        if (event[6] != 'weight' or len(values) != 7+identity[-1]
                or tuple(map(float, values[:7])) != identity):
            raise ValueError('Impulse identity/sample count mismatch')
        pixels = list(map(int, values[7:]))
        if any(not 0 <= pixel <= 0xffffff for pixel in pixels):
            raise ValueError('Invalid RGB pixel')
        for offset, pixel in enumerate(pixels):
            groups[(*identity[1:], offset)][identity[0]] = pixel >> 16 & 255
            constant += (pixel & 255) == 113
            samples += 1
    rows = [{'identity': key, 'corner_red': [values[c] for c in range(4)]}
            for key, values in groups.items()]
    isolated = []
    for row in rows:
        mode, scale, tx, ty, start, length, offset = row['identity']
        if (mode, scale, start, length, offset) != (0, 5, 4, 1, 0):
            continue
        # Conditional inference within the existing byte-weight family. Zero/255
        # responses are ambiguous, so this inference only uses interior weights.
        red = row['corner_red']
        if not all(0 < value < 255 for value in red):
            raise ValueError('Ambiguous corner response for isolated control')
        weights = [value+1 for value in red]
        solutions = []
        for fx in range(256):
            for fy in range(256):
                candidate = [(256-fx)*(256-fy)//256, fx*(256-fy)//256, (256-fx)*fy//256]
                candidate.append(256-sum(candidate))
                if candidate == weights:
                    solutions.append([fx, fy])
        isolated.append({'identity': row['identity'], 'corner_red': red,
                         'weights_if_byte_family': weights, 'byte_fraction_solutions': solutions})
    return {'production_admitted': False, 'native_rows': len(expected), 'samples': samples,
            'constant_channel_exact': constant, 'four_corner_groups': len(rows),
            'isolated_scalar_controls': isolated, 'rows': rows}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-log', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = analyze(args.native_log.read_text())
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'rows'}))
