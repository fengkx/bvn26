"""Native byte-composition controls; this is not production admission."""
import argparse
import hashlib
import json
from pathlib import Path

PALETTES = ((0x606060, 0x81d3ef, 0x46c4ec), (0, 0xff8001, 0x3366cc),
            (0xffffff, 0x017ffe, 0xcc80aa), (0x3355cc, 0x80ff01, 0x7f0180))


def identities():
    for layout in range(3):
        for palette in range(4):
            for bi, back in enumerate((0, 1, 64, 128, 254, 255)):
                for fi, front in enumerate((0, 1, 2, 63, 127, 128, 254, 255)):
                    for oi, opacity in enumerate((0, 1, 25, 50, 99, 100)):
                        if layout and (bi % 2 == 0 or fi % 2 == 0 or oi % 2 == 0):
                            continue
                        for inner in ((25, 50, 100) if layout else (100,)):
                            yield [layout, palette, back, front, opacity, inner]


def decode(build, trace):
    rows = []
    expected = list(identities())
    done = False
    for line in trace.splitlines():
        p = line.split('|')
        if len(p) < 2 or p[:2] != ['AIREF', build['run_id']]:
            continue
        if len(p) != 8 or p[2:6] != [str(len(rows)), '0', '0', '0'] or done:
            raise ValueError('Missing, reordered or malformed native event')
        if p[6:] == ['done', 'ok']:
            done = True
            continue
        if p[6] != 'normal':
            raise ValueError('Unexpected native event')
        values = list(map(int, p[7].split(',')))
        if len(values) != 14 or len(rows) >= len(expected) or values[:6] != expected[len(rows)]:
            raise ValueError('Unexpected control identity or pixel fields')
        pixels = []
        for i in range(6, 14, 2):
            if not all(-2**31 <= n < 2**32 for n in values[i:i+2]):
                raise ValueError('Invalid packed pixel')
            if (values[i+1] >> 24) & 255 != 255:
                raise ValueError('Black-background readback is not opaque')
            # Black readback measures premultiplied RGB without lossy unpremultiplication.
            pixels.append([(values[i+1] >> shift) & 255 for shift in (16, 8, 0)]
                          + [(values[i] >> 24) & 255])
        rows.append({'key': values[:6], 'pixels': pixels})
    if not done or len(rows) != len(expected):
        raise ValueError('Incomplete native capture')
    return rows


def over(back, front):
    return [front[i] + back[i] * (256-front[3]) // 256 for i in range(4)]


def predict(row, vector):
    layout, palette, _, _, opacity, inner = row['key']
    back, middle, front, _ = row['pixels']
    outer = opacity * 256 // 100
    combined = outer * (inner * 256 // 100) // 256

    def shade(pixel, color, multiplier):
        alpha = pixel[3] * multiplier // 256
        if vector:
            return [((color >> s) & 255) * (alpha+1) // 256 for s in (16, 8, 0)] + [alpha]
        return [c * multiplier // 256 for c in pixel]

    m = shade(middle, PALETTES[palette][1], combined if layout == 2 else outer)
    f = shade(front, PALETTES[palette][2], combined)
    return over(back, over(m, f))


def analyze(directory, vector):
    build = json.loads((directory/'build.json').read_text())
    source = Path(build['source'])
    if hashlib.sha256(source.read_bytes()).hexdigest() != build['source_sha256']:
        raise ValueError('Native source hash changed')
    rows = decode(build, (directory/'native.log').read_text())
    for row in rows:
        row['predicted'] = predict(row, vector)
        row['delta'] = [a-b for a, b in zip(row['predicted'], row['pixels'][-1])]
    return {'samples': len(rows), 'exact': sum(not any(r['delta']) for r in rows),
            'max_channel_delta': max(abs(d) for r in rows for d in r['delta']),
            'production_admitted': False, 'rows': rows}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--vector', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.native, args.vector)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}))
    raise SystemExit(0 if result['exact'] == result['samples'] else 1)
