"""Decode original Flash raster samples and compare declared native phase images."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools/probes'))
from PIL import Image
from tools.sampling_bitmap import collect, difference
from compare_mode_reference import compare

probe = json.loads((OUT / 'probe-visual-r01/build.json').read_text())
source_dir = OUT / 'original-visual-r01'
images = collect((source_dir / 'original.log').read_text().splitlines(), probe['run_id'], 80)
ticks = [0, 11, 15, 40, 43, 60, 80]
results = []
for tick in ticks:
    path = source_dir / f'{tick:03d}.png'
    Image.frombytes('RGBA', (600,400), images[tick]).save(path)
    native_path = OUT / 'native-visual-r01' / f'{tick:03d}.png'
    with Image.open(native_path) as image:
        pixels = image.convert('RGBA').tobytes()
    results.append({'tick':tick,'comparison':difference(images[tick],pixels,600),
                    'source':str(path.relative_to(ROOT)), 'native':str(native_path.relative_to(ROOT)),
                    'hashes':{'source_png':hashlib.sha256(path.read_bytes()).hexdigest(),
                              'native_png':hashlib.sha256(native_path.read_bytes()).hexdigest()}})
comparison = compare(source_dir / 'collected/events.jsonl', OUT / 'native-visual-r01/state-080.json')
report = {'scope':'Seven same-tick original BitmapData.draw(root) and Godot viewport images. Native image replays are separate matches; not continuous-lifecycle evidence. No pixel tolerance or exclusions.',
          'actor_states':comparison,'images':results,'pixel_parity':all(r['comparison']['exact'] for r in results),
          'audio':'not_captured','native_parity_proven':False,'production_admitted':False}
(OUT / 'visual-comparisons-r01.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'actor_states':comparison['status'],'pixel_parity':report['pixel_parity'],'different_pixels':{r['tick']:r['comparison']['different_pixels'] for r in results}}))
