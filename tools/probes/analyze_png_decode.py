"""Constrain external PNG premultiplication separately from BitmapData constructors."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image
from tools.probes.build_png_decode_probe import pixels
from tools.probes.analyze_blur_kernel_heldout import ROOT
from tools.probes.run_nested_filters import unpack


def decode(native):
    build = json.loads((native/'build.json').read_text())
    assert hashlib.sha256((ROOT/build['source']).read_bytes()).hexdigest() == build['source_sha256']
    path = native/'game/probe.png'
    assert hashlib.sha256(path.read_bytes()).hexdigest() == build['outputs_sha256']['game/probe.png']
    image = Image.open(path)
    assert image.size == (256, 768) and image.mode == 'RGBA' and not image.info
    source = pixels()
    assert list(image.getdata()) == source
    assert hashlib.sha256(bytes(c for p in source for c in p)).hexdigest() == build['png_rgba_sha256']
    rows = [s.split('|') for s in (native/'native.log').read_text().splitlines() if s.startswith('AIREF|')]
    assert len(rows) == 770 and rows[0][6:] == ['loaded', '256,768,100,100,100'] and rows[-1][6:] == ['done', 'ok']
    for i, row in enumerate(rows):
        assert row[1] == build['run_id'] and row[2:6] == [str(i), '0', '0', '0']
    result = []
    for y, row in enumerate(rows[1:-1]):
        fields = row[7].split(',')
        assert row[6] == 'row' and fields[0] == str(y) and len(fields) == 513
        result.extend(unpack(list(map(int, fields[1:]))))
    assert [p[3] for p in result] == [p[3] for p in source]
    return source, result


def analyze(native):
    source, target = decode(native)
    models = {
        'alpha_plus_one_256': lambda c, a: c*(a+1)//256,
        'nearest_255': lambda c, a: (c*a+127)//255,
        'floor_255': lambda c, a: c*a//255,
        'opaque_or_floor_256': lambda c, a: c if a == 255 else c*a//256,
    }
    scores = {name: {'samples': len(source), 'exact': 0, 'max_delta': 0, 'failures': []} for name in models}
    for i, (pixel, native_pixel) in enumerate(zip(source, target)):
        for name, formula in models.items():
            actual = [formula(c, pixel[3]) for c in pixel[:3]]+[pixel[3]]
            score = scores[name]
            delta = max(abs(a-b) for a, b in zip(actual, native_pixel))
            score['max_delta'] = max(delta, score['max_delta'])
            if not delta:
                score['exact'] += 1
            else:
                score['failures'].append({'x': i%256, 'y': i//256, 'source': list(pixel), 'actual': actual, 'native': native_pixel})
    return {'scores': scores, 'passed_models': [name for name, score in scores.items() if not score['failures']],
            'source_rgba_exact': len(source), 'native_alpha_exact': len(source), 'candidate_admitted': False, 'production_admitted': False}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--native', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    r = analyze(args.native)
    args.output.write_text(json.dumps(r, separators=(',', ':'))+'\n')
    print({name: (s['exact'], s['samples'], s['max_delta']) for name, s in r['scores'].items()})
    print('passed_models', r['passed_models'])
