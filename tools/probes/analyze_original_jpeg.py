"""Compare independently decoded original JPEG bytes with native bitmap readbacks."""
import argparse
from collections import Counter
import hashlib
from io import BytesIO
import json
from pathlib import Path
import struct
import zlib
from PIL import Image, features
from tools.probes.build_bound_bitmap_component import ROOT, source_tags
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.run_nested_filters import unpack


def analyze(native):
    build = json.loads((native / 'build.json').read_text())
    source = ROOT / build['original_source']['path']
    assert hashlib.sha256(source.read_bytes()).hexdigest() == build['original_source']['sha256']
    payload, raw = next((p, r) for c, p, r in source_tags(source)
                        if c == 35 and struct.unpack_from('<H', p)[0] == 340)
    assert hashlib.sha256(raw).hexdigest() == build['original_bitmap_tag_sha256']
    length = struct.unpack_from('<I', payload, 2)[0]
    jpeg = payload[6:6+length]
    alpha = zlib.decompress(payload[6+length:])
    image = Image.open(BytesIO(jpeg)).convert('RGB')
    width, height = image.size
    assert (width, height) == (186, 378)
    captured = events(native)
    assert captured[0] == ['dimensions', '186,378,true']
    assert len(captured) == height + 2
    target = []
    for y, (kind, data) in enumerate(captured[1:-1]):
        values = list(map(int, data.split(',')))
        assert kind == 'row' and values[0] == y and len(values) == 1 + width*2
        target.extend(unpack(values[1:]))
    assert [p[3] for p in target] == list(alpha)
    assert set(alpha) == {0, 255}
    predicted = [list(rgb) + [255] if a else [0]*4
                 for rgb, a in zip(image.getdata(), alpha)]
    failures = []
    histogram = Counter()
    for index, (actual, expected) in enumerate(zip(predicted, target)):
        if actual != expected:
            delta = [a-b for a,b in zip(actual, expected)]
            histogram.update(delta[:3])
            failures.append({'x': index % width, 'y': index // width,
                             'candidate': actual, 'native': expected, 'delta': delta})
    return {'source': build['original_source'], 'bitmap_tag_sha256': build['original_bitmap_tag_sha256'],
            'jpeg_sha256': hashlib.sha256(jpeg).hexdigest(), 'width': width, 'height': height,
            'decoder': {'Pillow': Image.__version__, 'jpeg': features.version('jpg'),
                        'libjpeg_turbo': features.version('libjpeg_turbo')},
            'pixels': len(target), 'exact': len(target)-len(failures),
            'alpha_exact': len(target), 'max_channel_delta': max((max(map(abs,f['delta'])) for f in failures), default=0),
            'signed_rgb_delta_histogram': dict(sorted(histogram.items())), 'failures': failures,
            'decoder_parity_proved': not failures, 'production_admitted': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.native)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print({k:v for k,v in result.items() if k != 'failures'})
