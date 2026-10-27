"""Exact opaque RGBA comparison at the one-cell root observation boundary."""
import argparse
import json
from pathlib import Path
import re

from PIL import Image
from tools.sampling_native import sha, validate

WIDTH, HEIGHT = 600, 400
HEADER = '600,400,RGBA8,opaque-black,root-observer'


def decode_row(encoded, width=WIDTH):
    pixels = bytearray()
    for run in encoded.split(';')[:-1]:
        if not re.fullmatch(r'[0-9a-f]{8}:[1-9][0-9]*', run):
            raise ValueError('malformed pixel run')
        argb, count = run.split(':')
        count = int(count)
        if count > width or len(pixels) // 4 + count > width:
            raise ValueError('pixel row overflow')
        a, r, g, b = bytes.fromhex(argb)
        if a != 255:
            raise ValueError('native alpha is not opaque')
        pixels.extend(bytes((r, g, b, a)) * count)
    if not encoded.endswith(';') or len(pixels) != width * 4:
        raise ValueError('missing pixels')
    return bytes(pixels)


def collect(lines, run_id, frames):
    images, current, row_index = [], None, 0
    for line in lines:
        parts = line.split('|', 7)
        if len(parts) != 8 or parts[:2] != ['AIREF', run_id]:
            raise ValueError('foreign/malformed bitmap event')
        tick, kind, value = int(parts[5]), parts[6], parts[7]
        if not kind.startswith('bitmap_'):
            continue
        if kind == 'bitmap_begin':
            if current is not None or tick != len(images) or value != HEADER:
                raise ValueError('missing/duplicate frame or incompatible pixel semantics')
            current, row_index = bytearray(), 0
        elif current is None or tick != len(images):
            raise ValueError('bitmap event outside frame')
        elif kind == 'bitmap_row':
            row, encoded = value.split(',', 1)
            if int(row) != row_index or row_index >= HEIGHT:
                raise ValueError('missing/duplicate/out-of-order row')
            current.extend(decode_row(encoded))
            row_index += 1
        elif kind == 'bitmap_end':
            if value != str(HEIGHT) or row_index != HEIGHT:
                raise ValueError('missing bitmap rows')
            images.append(bytes(current))
            current = None
        else:
            raise ValueError('unsupported bitmap event')
    if current is not None or len(images) != frames + 1:
        raise ValueError('missing bitmap frames')
    return images


def difference(expected, actual, width=WIDTH):
    if len(expected) != len(actual) or len(actual) % 4:
        raise ValueError('incompatible RGBA byte sizes')
    different, pixels, maximum, first = 0, 0, 0, None
    for i in range(0, len(actual), 4):
        delta = [abs(expected[i+c] - actual[i+c]) for c in range(4)]
        if any(delta):
            pixels += 1
            different += sum(d != 0 for d in delta)
            maximum = max(maximum, *delta)
            if first is None:
                first = {'x': (i//4) % width, 'y': (i//4)//width,
                         'native': list(expected[i:i+4]), 'godot': list(actual[i:i+4])}
    return {'different_channels': different, 'different_pixels': pixels,
            'max_channel_delta': maximum, 'first_difference': first, 'exact': different == 0}


def godot_images(directory, case_path):
    case = json.loads(case_path.read_text())
    manifest = json.loads((directory / 'bitmap.json').read_text())
    expected = {'case_id': case['id'], 'case_sha256': sha(case_path), 'width': WIDTH,
                'height': HEIGHT, 'phase': 'root-observer', 'format': 'RGBA8',
                'background': 'opaque-black', 'production_admitted': False,
                'native_parity_proven': False}
    if any(manifest.get(k) != v for k, v in expected.items()):
        raise ValueError('Godot case/size/color/alpha/phase mismatch')
    runner = Path(__file__).resolve().parents[1] / 'godot/tests/move_case_reference.gd'
    if manifest['runner_sha256'] != sha(runner):
        raise ValueError('changed Godot capture runner')
    records = manifest['images']
    if [r['tick'] for r in records] != list(range(case['frames'] + 1)):
        raise ValueError('missing/duplicate Godot frames')
    result = []
    for r in records:
        if r['file'] != f"{r['tick']:03d}.png":
            raise ValueError('unexpected Godot image path')
        path = directory / r['file']
        if sha(path) != r['sha256']:
            raise ValueError('changed Godot image')
        with Image.open(path) as image:
            if image.size != (WIDTH, HEIGHT) or image.mode != 'RGBA':
                raise ValueError('Godot image size/format mismatch')
            rgba = image.tobytes()
        if any(a != 255 for a in rgba[3::4]):
            raise ValueError('Godot alpha is not opaque')
        result.append(rgba)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--godot', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        receipt_hash = validate(args.case, args.receipt)
        receipt = json.loads(args.receipt.read_text())
        metadata = json.loads((Path(receipt['build']) / 'build.json').read_text())
        if not metadata.get('sampling_bitmap'):
            raise ValueError('missing native BitmapData probe')
        native = collect(Path(receipt['trace']).read_text().splitlines(),
                         metadata['run_id'], metadata['move_case']['frames'])
        actual = godot_images(args.godot, args.case)
        results = [dict(tick=tick, **difference(n, g)) for tick, (n, g) in enumerate(zip(native, actual))]
        report = {'case_id': metadata['move_case']['id'], 'receipt_sha256': receipt_hash,
                  'godot_manifest_sha256': sha(args.godot / 'bitmap.json'),
                  'frames': results, 'exact_frames': sum(r['exact'] for r in results),
                  'native_parity_proven': False, 'production_admitted': False}
        args.output.write_text(json.dumps(report, indent=2) + '\n')
        if not all(r['exact'] for r in results):
            raise ValueError(f"pixel mismatch: {report['exact_frames']}/{len(results)} exact frames; see report")
        print('BITMAP_BYTE_GATE_OK', len(results))
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(1, f'bitmap evidence error: {error}\n')


if __name__ == '__main__':
    main()
