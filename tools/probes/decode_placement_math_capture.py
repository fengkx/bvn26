"""Decode native placement arithmetic probes without reconstructing lost RGB bits."""
import argparse
import json
import math
from pathlib import Path
from analyze_placement_arithmetic import native_events

BACKS = [0x3366cc, 0x007fff, 0x80ff01]
FRONTS = [0xcc80aa, 0xff8000, 0x407ffe]


def rgba(packed):
    return [(packed >> shift) & 255 for shift in (16, 8, 0, 24)]


def decode(events, kind):
    expected_count = {'ramp': 3072, 'boundary': 336, 'layered': 192, 'extended': 256, 'impulse': 136}[kind]
    if len(events) != expected_count:
        raise ValueError(f'Incomplete {kind} capture: {len(events)} events')
    rows = []
    for event, text in events:
        values = text.split(',')
        if kind in ('ramp', 'boundary', 'layered'):
            if event != {'ramp': 'blend', 'boundary': 'boundary', 'layered': 'layered'}[kind]:
                raise ValueError('Unexpected blend event')
            mode, pair, ba, fa, *samples = map(int, values)
            row = {'mode': [7, 13][mode], 'back': 0x808080 if kind == 'boundary' else BACKS[pair],
                   'front': pair*65793 if kind == 'boundary' else FRONTS[pair],
                   'back_alpha': ba, 'front_alpha': fa, 'opacity': 100}
            if kind != 'layered':
                b, bp, s, sp, output, black = map(rgba, samples)
                # beginFill's percentage conversion can truncate the requested
                # alpha. Render the observed byte, not a different input byte.
                row.update(back_alpha=b[3], front_alpha=s[3], requested_front_alpha=fa,
                           back_premultiplied=bp[:3]+b[3:], front_premultiplied=sp[:3]+s[3:])
            else:
                opacity, output, black = samples
                row.update(under=0x203040, opacity=opacity)
                output, black = rgba(output), rgba(black)
            row['premultiplied'] = black[:3] + output[3:]
        elif kind == 'extended':
            if event != 'shadow' or len(values) != 1030:
                raise ValueError('Invalid shadow sample')
            angle, distance, alpha, color, strength, blur, *pixels = values
            row = {'angle': float(angle)*math.pi/180, 'distance': float(distance),
                   'source_alpha': int(alpha), 'color': [v/255 for v in rgba(int(color))[:3]]+[1],
                   'strength': float(strength), 'blur': float(blur),
                   'pixels': [rgba(int(v)) for v in pixels]}
        else:
            if event != 'impulse' or len(values) != 20:
                raise ValueError('Invalid impulse sample')
            diagonal, step, requested, source, *pixels = map(int, values)
            row = {'diagonal': diagonal, 'step': step, 'requested_alpha': requested,
                   'source_alpha': rgba(source)[3], 'pixels': [rgba(v) for v in pixels]}
        rows.append(row)
    return rows


def blend_bytes(back, front, mode):
    """Measured model; production shader uses the same integer numerators."""
    ba, sa = back[3], front[3]
    result = []
    for bp, sp in zip(back[:3], front[:3]):
        if mode == 7:
            numerator = (bp+sp)*255 - 2*min(bp*sa, sp*ba)
        elif mode == 13:
            base = (bp+sp)*255 - bp*sa - sp*ba
            if 2*bp <= ba:
                numerator = base + 2*bp*sp
            else:
                numerator = base + sa*ba - 2*(ba-bp)*(sa-sp) - int(sa > 0 and ba > 0)
        else:
            raise ValueError(f'Unsupported diagnostic blend mode {mode}')
        result.append(numerator//255)
    return result + [((sa+ba)*255-sa*ba)//255]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kind', choices=('ramp', 'boundary', 'layered', 'extended', 'impulse'), required=True)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--trace', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    rows = decode(native_events(json.loads(args.build.read_text()), args.trace.read_text()), args.kind)
    args.output.write_text(json.dumps(rows) + '\n')
    print(json.dumps({'kind': args.kind, 'cases': len(rows)}))
