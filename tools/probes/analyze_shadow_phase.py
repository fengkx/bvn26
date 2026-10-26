"""Decode native shadow impulses and check the measured subpixel phase model."""
import argparse
import json
import math
from pathlib import Path

from analyze_placement_arithmetic import native_events


def decode(events, expected_count):
    if len(events) != expected_count:
        raise ValueError(f'Incomplete shadow phase capture: {len(events)}/{expected_count}')
    rows = []
    for event, text in events:
        values = text.split(',')
        if event != 'phase' or len(values) != 54:
            raise ValueError('Invalid shadow phase event')
        angle, distance, perturbation, observed_angle, observed_distance = map(float, values[:5])
        pixels = list(map(int, values[5:]))
        if any(not 0 <= value <= 255 for value in pixels):
            raise ValueError('Invalid shadow alpha')
        rows.append(dict(angle=angle, distance=distance, perturbation=int(perturbation),
                         observed_angle=observed_angle, observed_distance=observed_distance,
                         pixels=pixels))
    return rows


def impulse(row):
    angle = math.radians(row['observed_angle'])
    x, y = [math.copysign(math.floor(abs(component * row['observed_distance']) * 256 + 0.5),
                         component * row['observed_distance']) / 256
            for component in (math.cos(angle), math.sin(angle))]
    fx, fy = x % 1, y % 1
    weights = [int(256*(1-fx)*(1-fy)), int(256*fx*(1-fy)), int(256*(1-fx)*fy)]
    weights.append(256-sum(weights))
    pixels = [0]*49
    for (dx, dy), weight in zip(((0, 0), (1, 0), (0, 1), (1, 1)), weights):
        px, py = 3+math.floor(x)+dx, 3+math.floor(y)+dy
        if not (0 <= px < 7 and 0 <= py < 7):
            raise ValueError('Impulse extends outside capture')
        pixels[py*7+px] = 255*weight//256
    return pixels


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--trace', type=Path, required=True)
    parser.add_argument('--count', type=int, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    rows = decode(native_events(json.loads(args.build.read_text()), args.trace.read_text()), args.count)
    args.output.write_text(json.dumps(rows)+'\n')
    exact = sum(impulse(row) == row['pixels'] for row in rows)
    print(json.dumps({'cases': len(rows), 'exact': exact}))
    raise SystemExit(0 if exact == len(rows) else 1)
