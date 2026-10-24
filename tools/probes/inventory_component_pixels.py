"""Report exact per-channel component differences with pinned source locations."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[2]


def inventory(directory):
    rows = []
    for path in sorted((directory/'components').glob('*/cases.json')):
        clocks = json.loads((directory/'godot'/path.parent.name/'clocks.json').read_text())
        frames = {(r['path'], r['tick']): r['frame'] for r in clocks}
        for case in json.loads(path.read_text()):
            source = ROOT/case['source']['path']
            if hashlib.sha256(source.read_bytes()).hexdigest() != case['source']['sha256']:
                raise ValueError(f'Source hash mismatch: {source}')
            for tick in case['samples']:
                name = f"{case['id']}-{tick:03d}"
                native = directory/'comparisons'/path.parent.name/(name+'.native.png')
                actual = directory/'godot'/path.parent.name/(name+'.png')
                with Image.open(native) as image:
                    reference = image.convert('RGB')
                with Image.open(actual) as image:
                    observed = image.convert('RGB')
                if reference.size != observed.size:
                    raise ValueError(f'Image size mismatch: {name}')
                delta = ImageChops.difference(reference, observed)
                histogram = delta.histogram()
                changed = {channel: sum(histogram[i*256+1:(i+1)*256])
                           for i, channel in enumerate('RGB')}
                maxima = dict(zip('RGB', [high for low, high in delta.getextrema()]))
                worst = max(maxima.values())
                samples = []
                if worst:
                    for index in range(reference.width * reference.height):
                        position = (index % reference.width, index // reference.width)
                        a, b = reference.getpixel(position), observed.getpixel(position)
                        if max(abs(x-y) for x,y in zip(a,b)) == worst:
                            samples.append({'x': index % reference.width, 'y': index // reference.width,
                                            'native_rgb': list(a), 'runtime_rgb': list(b)})
                            if len(samples) == 4:
                                break
                rows.append({'case': case['id'], 'swf': case['source']['path'],
                             'swf_sha256': case['source']['sha256'], 'owner_sprite': case['owner'],
                             'placement_frame': case['source_frame'], 'depth': case['placement']['depth'],
                             'clip': case['symbol'], 'tick': tick,
                             'runtime_wrapper_frame': frames[(case['id'],tick)],
                             'runtime_clip_frame': frames.get((case['id']+'/'+str(case['placement']['depth']),tick)),
                             'different_channels': changed, 'max_channel_delta': maxima,
                             'worst_samples': samples, 'exact': worst == 0,
                             'native_png_sha256': hashlib.sha256(native.read_bytes()).hexdigest(),
                             'runtime_png_sha256': hashlib.sha256(actual.read_bytes()).hexdigest()})
    if not rows:
        raise ValueError('No component cases')
    return {'images': len(rows), 'exact': sum(row['exact'] for row in rows), 'rows': rows}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = inventory(args.directory.resolve())
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'rows'}))
    raise SystemExit(0 if result['images'] == result['exact'] else 1)
