"""Diagnostic arithmetic models, not admitted production rendering semantics."""
import argparse
import json
import math
from pathlib import Path


def native_events(build: dict, trace: str) -> list:
    events = []
    for line in trace.splitlines():
        parts = line.split('|')
        if len(parts) == 8 and parts[:2] == ['AIREF', build['run_id']]:
            if int(parts[2]) != len(events):
                raise ValueError('Missing or reordered native event')
            events.append(parts[6:])
    if not events or events[-1] != ['done', 'ok']:
        raise ValueError('Incomplete capture')
    return events[:-1]


def decode_grid(events: list) -> list:
    if len(events) != 256:
        raise ValueError('Expected 256 overlay rows')
    rows = []
    for index, (kind, value) in enumerate(events):
        row, raw = value.split(':')
        packed = [int(v) & 0xffffffff for v in raw.split(',')]
        if kind != 'row' or int(row) != index or len(packed) != 256:
            raise ValueError('Invalid overlay row')
        if any(p != 0xff000000 | ((p & 255) * 65793) for p in packed):
            raise ValueError('Overlay grid is not opaque grayscale')
        rows.append([p & 255 for p in packed])
    return rows


def opaque_overlay_channel(back: int, front: int) -> int:
    if back < 128:
        return 2 * back * front // 255
    return 254 - 2 * (255 - back) * (255 - front) // 255


def grid_report(rows: list, gpu: list | None = None) -> dict:
    differences = []
    gpu_differences = []
    for front, row in enumerate(rows):
        for back, native in enumerate(row):
            actual = opaque_overlay_channel(back, front)
            if native != actual:
                differences.append([back, front, native, actual])
            if gpu is not None:
                expected = [native, native, native, 255]
                if expected != gpu[front][back]:
                    gpu_differences.append([back, front, expected, gpu[front][back]])
    return {'pixels': sum(map(len, rows)), 'model_differences': differences,
            'gpu_differences': gpu_differences if gpu is not None else None}


def decode_shadows(events: list) -> list:
    cases = []
    for kind, value in events:
        angle, distance, *raw = value.split(',')
        if kind != 'shadow' or len(raw) != 1024:
            raise ValueError('Invalid shadow sample')
        cases.append({'angle': float(angle) * math.pi / 180,
                      'distance': float(distance),
                      'pixels': [[(int(v) >> s) & 255 for s in (16, 8, 0, 24)] for v in raw]})
    if len(cases) != 12:
        raise ValueError('Expected 12 shadow cases')
    return cases


def shadow_report(cases: list, blur: bool) -> dict:
    def sample(x, y):
        if not blur:
            return 255 if 8 <= x < 16 and 8 <= y < 16 else 0
        nx = max(0, min(15, x + 1) - max(8, x - 1) + 1)
        ny = max(0, min(15, y + 1) - max(8, y - 1) + 1)
        return (85 * nx * ny) // 3

    result = []
    for case in cases:
        dx = math.cos(case['angle']) * case['distance']
        dy = math.sin(case['angle']) * case['distance']
        differences = []
        for y in range(32):
            for x in range(32):
                xx, yy = math.floor(x - dx), math.floor(y - dy)
                u, v = x - dx - xx, y - dy - yy
                value = (sample(xx, yy) * (1-u) * (1-v) + sample(xx+1, yy) * u * (1-v)
                         + sample(xx, yy+1) * (1-u) * v + sample(xx+1, yy+1) * u * v)
                # Numerical epsilon only at integer floating-point boundaries;
                # expected/actual channel comparison remains strictly exact.
                actual = math.floor(value + 1e-5)
                native = case['pixels'][y*32+x][3]
                if native != actual:
                    differences.append([x, y, native, actual])
        result.append({'angle': case['angle'], 'distance': case['distance'],
                       'differences': differences})
    return {'exact': sum(not c['differences'] for c in result), 'cases': result}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kind', choices=('overlay', 'shadow-mask', 'shadow-offset'), required=True)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--trace', type=Path, required=True)
    parser.add_argument('--gpu', type=Path)
    parser.add_argument('--samples', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    events = native_events(json.loads(args.build.read_text()), args.trace.read_text())
    if args.kind == 'overlay':
        samples = decode_grid(events)
        report = grid_report(samples, json.loads(args.gpu.read_text()) if args.gpu else None)
        passed = not report['model_differences'] and not report['gpu_differences']
    else:
        samples = decode_shadows(events)
        report = shadow_report(samples, args.kind == 'shadow-mask')
        passed = report['exact'] == len(samples)
    args.samples.write_text(json.dumps(samples) + '\n')
    args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'passed': passed, 'report': str(args.report)}))
    raise SystemExit(0 if passed else 1)
