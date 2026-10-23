#!/usr/bin/env python3
"""Compare scalar ColorMatrix measurements without a channel tolerance."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

IDENTITIES = [(opacity, row, component)
              for opacity in (100, 80) for row in range(3) for component in range(4)]
PREFIX = 'AIREF|filter-color-arithmetic-r11|'


def native_samples(text: str) -> list[dict]:
    events = [line.split('|') for line in text.splitlines() if line.startswith(PREFIX)]
    if len(events) != 25 or [int(event[2]) for event in events] != list(range(25)):
        raise ValueError('Expected exactly 25 ordered native arithmetic events')
    if events[-1][6:] != ['done', 'ok']:
        raise ValueError('Missing native completion event')
    samples = []
    for event, identity in zip(events[:-1], IDENTITIES):
        if event[6] != 'sample':
            raise ValueError('Unexpected native arithmetic event')
        values = list(map(int, event[7].split(',')))
        if len(values) != 5 or tuple(values[:3]) != identity:
            raise ValueError('Mismatched native arithmetic case identity')
        color, black = values[3:]
        if (black >> 24) & 255 != 255:
            raise ValueError('Native RGB observation must use opaque black background')
        samples.append(dict(zip(('opacity', 'row', 'component'), identity)) | {
            'premultiplied': [(black >> 16) & 255, (black >> 8) & 255,
                              black & 255, (color >> 24) & 255]})
    return samples


def compare(native: list[dict], actual: list[dict]) -> dict:
    if len(native) != len(IDENTITIES):
        raise ValueError('Expected exactly 24 native arithmetic samples')
    if len(actual) != len(IDENTITIES):
        raise ValueError('Expected exactly 24 Godot arithmetic samples')
    cases = []
    for expected, observed, identity in zip(native, actual, IDENTITIES):
        if tuple(observed.get(k) for k in ('opacity', 'row', 'component')) != identity:
            raise ValueError('Mismatched Godot arithmetic case identity')
        pixel = observed.get('premultiplied')
        if not isinstance(pixel, list) or len(pixel) != 4 or any(
                type(channel) is not int or not 0 <= channel <= 255 for channel in pixel):
            raise ValueError('Expected four integer premultiplied RGBA channels')
        errors = [abs(a - b) for a, b in zip(expected['premultiplied'], pixel)]
        cases.append(expected | {'actual': pixel, 'different': sum(e != 0 for e in errors),
                                 'max_error': max(errors)})
    return {'passed': all(case['different'] == 0 for case in cases),
            'exact_cases': sum(case['different'] == 0 for case in cases),
            'cases': cases}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-log', type=Path, required=True)
    parser.add_argument('--godot-rows', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = compare(native_samples(args.native_log.read_text()),
                     json.loads(args.godot_rows.read_text()))
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'passed': report['passed'], 'exact_cases': report['exact_cases'],
                      'total_cases': len(report['cases'])}))
    raise SystemExit(0 if report['passed'] else 1)
