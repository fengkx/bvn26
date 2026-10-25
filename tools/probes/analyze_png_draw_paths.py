"""Independent mixed-alpha PNG draw controls, with no per-pixel choice of arithmetic."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image
from tools.probes.build_png_draw_paths_probe import pixels
from tools.probes.analyze_blur_kernel_heldout import ROOT
from tools.probes.run_nested_filters import unpack

STAGES = ('full', 'direct_black', 'single_clip', 'redraw')


def analyze(native):
    build = json.loads((native/'build.json').read_text())
    assert hashlib.sha256((ROOT/build['source']).read_bytes()).hexdigest() == build['source_sha256']
    path = native/'game/probe.png'
    assert hashlib.sha256(path.read_bytes()).hexdigest() == build['outputs_sha256']['game/probe.png']
    image = Image.open(path)
    assert image.size == (64,64) and image.mode == 'RGBA' and not image.info and list(image.getdata()) == pixels()
    assert hashlib.sha256(bytes(c for p in pixels() for c in p)).hexdigest() == build['png_rgba_sha256']
    events = [s.split('|') for s in (native/'native.log').read_text().splitlines() if s.startswith('AIREF|')]
    assert len(events) == 258 and events[0][6:] == ['loaded', '64,64,100,100,100'] and events[-1][6:] == ['done', 'ok']
    for i, row in enumerate(events):
        assert row[1] == build['run_id'] and row[2:6] == [str(i), '0', '0', '0']
    stages = {}
    for si, stage in enumerate(STAGES):
        values = []
        for y, row in enumerate(events[si*64+1:si*64+65]):
            fields = row[7].split(',')
            assert row[6] == 'row' and fields[:2] == [stage, str(y)] and len(fields) == 130
            values.extend(unpack(list(map(int, fields[2:]))))
        stages[stage] = values
    predicted = [[c if p[3] == 255 else c*p[3]//256 for c in p[:3]]+[p[3]] for p in pixels()]
    scores = {}
    for stage, actual in stages.items():
        target = [p[:3]+[255] if stage == 'direct_black' else p for p in predicted]
        failures = [{'x': i%64, 'y': i//64, 'actual': p, 'predicted': q}
                    for i, (p,q) in enumerate(zip(actual,target)) if p != q]
        scores[stage] = {'exact': 4096-len(failures), 'samples':4096, 'failures':failures}
    equivalence = {stage: sum(p[:3] == q[:3] and (stage == 'direct_black' or p[3] == q[3]) for p,q in zip(stages['full'], stages[stage])) for stage in STAGES[1:]}
    return {'source_rgba_exact':4096, 'scores':scores, 'native_equivalence':equivalence,
            'bounded_external_png_passed':all(not s['failures'] for s in scores.values()),
            'internal_decoder_attribution_proven':False, 'production_admitted':False}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--native', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args=p.parse_args()
    r=analyze(args.native)
    args.output.write_text(json.dumps(r,indent=2)+'\n')
    print({k:(s['exact'],s['samples']) for k,s in r['scores'].items()})
    print(r['native_equivalence'])
