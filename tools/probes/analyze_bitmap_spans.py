#!/usr/bin/env python3
"""Measure native draw-context dependence without selecting a sampler hypothesis."""
import argparse
import json
from pathlib import Path


def analyze(text):
    identities = [(mode, width, start, scale, phase)
                  for mode in (0, 1) for scale in (2.5, 8) for phase in (-224, 224)
                  for width in (260, 520, 524, 768) for start in (0, 5, 17)]
    events = [line.split('|') for line in text.splitlines() if line.startswith('AIREF|')]
    if (len(events) != len(identities) + 1 or any(len(e) != 8 for e in events)
            or len({e[1] for e in events}) != 1
            or not events[0][1].startswith('filter-bitmap-spans-r24-')
            or [int(e[2]) for e in events] != list(range(len(events)))
            or events[-1][6:] != ['done', 'ok']):
        raise ValueError('Incomplete, mixed or duplicate native span capture')
    rows = {}
    for event, identity in zip(events, identities):
        values = event[7].split(',')
        if (event[6] != 'span' or len(values) != 5 + identity[1] - 16
                or tuple(map(float, values[:5])) != identity):
            raise ValueError('Native span identity/sample count mismatch')
        pixels = list(map(int, values[5:]))
        if any(not 0 <= pixel <= 0xffffff for pixel in pixels):
            raise ValueError('Invalid native RGB pixel')
        rows[identity] = pixels
    comparisons = []
    for mode in (0, 1):
        for scale in (2.5, 8):
            for phase in (-224, 224):
                pairs = [((mode, width, 0, scale, phase), (mode, 768, 0, scale, phase))
                         for width in (260, 520, 524)]
                pairs += [((mode, 520, start, scale, phase), (mode, 520, 0, scale, phase))
                          for start in (5, 17)]
                for left, right in pairs:
                    differences = []
                    for x, (a, b) in enumerate(zip(rows[left], rows[right]), 16):
                        # Exclude pixels outside either clip; an unpainted pixel is not a sampler comparison.
                        if x < max(left[2], right[2]) or a == b:
                            continue
                        rgb_a = [(a >> shift) & 255 for shift in (16, 8, 0)]
                        rgb_b = [(b >> shift) & 255 for shift in (16, 8, 0)]
                        differences.append({'x': x, 'y': 155, 'left_rgb': rgb_a, 'right_rgb': rgb_b,
                                            'max_delta': max(abs(a-b) for a, b in zip(rgb_a, rgb_b))})
                    comparisons.append({'left': left, 'right': right, 'differences': differences})
    return {'production_admitted': False, 'native_rows': len(rows),
            'comparisons': len(comparisons),
            'context_dependent_comparisons': sum(bool(c['differences']) for c in comparisons),
            'max_delta': max((d['max_delta'] for c in comparisons for d in c['differences']), default=0),
            'rows': comparisons}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-log', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = analyze(args.native_log.read_text())
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'rows'}))
    # This diagnoses context dependence; success is not renderer parity.
