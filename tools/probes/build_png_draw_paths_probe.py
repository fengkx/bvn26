"""Build independent mixed-alpha PNG controls for native draw boundaries."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_flash_filter_probe import build


def pixels():
    return [((x*37+y*17)%256, (x*19+y*29+3)%256, (x*71+y*11+127)%256, (x*13+y*7)%256)
            for y in range(64) for x in range(64)]


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--ffdec', type=Path, required=True)
    args = p.parse_args()
    report = build('png-draw-paths', args.output, args.ffdec)
    image = Image.new('RGBA', (64, 64))
    image.putdata(pixels())
    path = args.output/'game/probe.png'
    image.save(path, format='PNG')
    report['outputs_sha256']['game/probe.png'] = hashlib.sha256(path.read_bytes()).hexdigest()
    report['png_rgba_sha256'] = hashlib.sha256(bytes(c for p in pixels() for c in p)).hexdigest()
    (args.output/'build.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))
