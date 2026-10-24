#!/usr/bin/env python3
"""Strict whole-image native gate for the source-bound bitmap diagnostic."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.probes.build_bound_bitmap_component import validate_fixture


def native_images(text, run_id, cases, width, height):
    events = [line.split('|') for line in text.splitlines() if line.startswith('AIREF|')]
    if (len(events) != cases*height+1 or any(len(e) != 8 or e[1] != run_id for e in events)
            or [int(e[2]) for e in events] != list(range(len(events)))
            or events[-1][6:] != ['done', 'ok']):
        raise ValueError('Incomplete, duplicated or foreign native capture')
    images = [Image.new('RGBA', (width, height)) for _ in range(cases)]
    for index, event in enumerate(events[:-1]):
        if event[6] != 'row':
            raise ValueError('Unexpected native event')
        values = list(map(int, event[7].split(',')))
        case, y = divmod(index, height)
        if values[:2] != [case, y] or len(values) != width+2:
            raise ValueError('Native row identity/length mismatch')
        for x, word in enumerate(values[2:]):
            if not -0x80000000 <= word <= 0xffffffff:
                raise ValueError('Invalid ARGB word')
            word &= 0xffffffff
            images[case].putpixel((x, y), ((word >> 16) & 255, (word >> 8) & 255, word & 255, word >> 24))
    return images


def compare(build, rendered, output):
    fixture = validate_fixture(json.loads((build/'fixture.json').read_text()))
    metadata = json.loads((build/'build.json').read_text())
    digest = hashlib.sha256((build/'fixture.json').read_bytes()).hexdigest()
    if digest != metadata['fixture_sha256'] or fixture['production_admitted'] is not False:
        raise ValueError('Fixture hash/admission mismatch')
    root = Path(__file__).resolve().parents[2]
    if hashlib.sha256((root/fixture['source']).read_bytes()).hexdigest() != fixture['source_sha256']:
        raise ValueError('Locked source hash mismatch')
    width, height = fixture['target_size']
    images = native_images((build/'native.log').read_text(), metadata['run_id'], len(fixture['cases']), width, height)
    output.mkdir(parents=True, exist_ok=True)
    results = []
    for i, native in enumerate(images):
        visible = sum(alpha != 0 for alpha in native.getchannel('A').tobytes())
        if not visible:
            raise ValueError('Native component did not render any visible pixels')
        native.save(output/f'native-{i}.png')
        actual = Image.open(rendered/f'case-{i}.png').convert('RGBA')
        if actual.size != native.size:
            raise ValueError('GPU image dimensions differ')
        mismatch = []
        maxima = [0]*4
        changed = [0]*4
        exact_pixels = 0
        for j, (a, b) in enumerate(zip(native.getdata(), actual.getdata())):
            if a == b:
                exact_pixels += 1
                continue
            delta = [abs(v-w) for v, w in zip(a, b)]
            for k in range(4):
                maxima[k] = max(maxima[k], delta[k])
                changed[k] += delta[k] != 0
            mismatch.append({'x': j % width, 'y': j // width, 'native': a, 'godot': b})
        results.append({'case': i, 'transform_and_clip': fixture['cases'][i], 'exact': not mismatch,
                        'pixels': width*height, 'exact_pixels': exact_pixels, 'native_nonzero_alpha_pixels': visible,
                        'changed_channels': changed, 'max_delta': maxima, 'mismatches': mismatch})
    report = {'source': fixture['source'], 'shape': fixture['shape_id'], 'bitmap': fixture['bitmap_id'],
              'fixture_sha256': digest, 'images': len(results), 'images_exact': sum(r['exact'] for r in results),
              'pixels': sum(r['pixels'] for r in results), 'exact_pixels': sum(r['exact_pixels'] for r in results),
              'diagnostic_passed': all(r['exact'] for r in results), 'production_admitted': False,
              'results': results}
    (output/'comparison.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--rendered', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = compare(args.build, args.rendered, args.output)
    print(json.dumps({k: v for k, v in result.items() if k != 'results'}))
    sys.exit(0 if result['diagnostic_passed'] else 1)
