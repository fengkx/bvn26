"""Build a native external-PNG decoder probe with independently authored RGBA bytes."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_flash_filter_probe import build


def pixels():
    return [(17, x, 223, a) if palette == 0 else (x, 255, 1, a) if palette == 1 else (0, 127, x, a)
            for palette in range(3) for a in range(256) for x in range(256)]


def png(path):
    image = Image.new('RGBA', (256, 768))
    image.putdata(pixels())
    image.save(path, format='PNG')
    decoded = Image.open(path)
    assert decoded.mode == 'RGBA' and not decoded.info and list(decoded.getdata()) == pixels()


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--ffdec', type=Path, required=True)
    args = p.parse_args()
    report = build('png-byte-decode', args.output, args.ffdec)
    path = args.output/'game/probe.png'
    png(path)
    report['outputs_sha256']['game/probe.png'] = hashlib.sha256(path.read_bytes()).hexdigest()
    report['png_rgba_sha256'] = hashlib.sha256(bytes(c for p in pixels() for c in p)).hexdigest()
    (args.output/'build.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))
