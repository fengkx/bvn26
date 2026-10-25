"""Map source-proven diagnostic renders to exact pinned case/tick identities."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageChops
from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.analyze_rotated_placement_family import analyze as rotated_family


def inventory():
    evidence = ROOT/'evidence/importer-loud-fail'
    baseline = json.loads((evidence/'r21/component-pixels.json').read_text())
    bindings = {}

    def bind(case, tick, path, proof):
        key = (case, tick)
        assert key not in bindings
        bindings[key] = (path, proof)

    for row in json.loads((evidence/'r130/gpu/report.json').read_text())['images']:
        assert row['exact'] == row['samples']
        bind(row['case'], row['tick'], evidence/f"r130/gpu/{row['case']}/final-{[0,3].index(row['tick'])}.png", 'r130')
    case = json.loads((evidence/'r154/gpu/fixture.json').read_text())['case']
    for index, tick in enumerate(case['samples']):
        bind(case['id'], tick, evidence/f'r154/gpu/final-{index}.png', 'r154')
    for case_id in ('yulong-157-1-1', 'yulong-159-1-1'):
        for tick in (0, 3):
            bind(case_id, tick, evidence/f'r178/regression-normal/wrapper/{case_id}-{tick:03d}.png', 'r36/r178')
    alias = rotated_family(evidence/'r155/source', evidence/'r154/regression-rotated')
    assert alias == json.loads((evidence/'r155/summary.json').read_text())
    assert alias['shared_input_signature_verified']
    for row in alias['images']:
        bind(row['case'], row['tick'], evidence/'r154/regression-rotated/final-1.png', 'r155 source-placement equivalence')
    for case in json.loads((evidence/'r208/gpu/fixture.json').read_text())['cases']:
        bind(case['case_id'], case['tick'], evidence/f"r208/gpu/{case['folder']}/final.png", 'r208')
    rows = []
    for old in baseline['rows']:
        case, tick = old['case'], old['tick']
        who = case.split('-')[0]
        assert hashlib.sha256((ROOT/old['swf']).read_bytes()).hexdigest() == old['swf_sha256']
        native = evidence/f'r21/components/{who}/{case}-{tick:03d}.native.png'
        assert hashlib.sha256(native.read_bytes()).hexdigest() == old['native_png_sha256']
        row = {'case': case, 'tick': tick, 'source': old['swf'], 'source_sha256': old['swf_sha256'],
               'owner': old['owner_sprite'], 'frame': old['placement_frame'], 'depth': old['depth'], 'clip': old['clip'],
               'native_sha256': old['native_png_sha256'], 'historical_production_exact': old['exact'],
               'historical_production_channel_deltas': old['max_channel_delta'], 'diagnostic_bound': (case,tick) in bindings}
        if (case, tick) in bindings:
            path, proof = bindings[(case,tick)]
            actual = Image.open(path).convert('RGBA')
            target = Image.open(native).convert('RGBA')
            assert actual.size == target.size == (600,400)
            maxima = [high for low,high in ImageChops.difference(actual,target).getextrema()]
            assert maxima == [0]*4
            row.update({'diagnostic_exact': True, 'diagnostic_path': str(path.relative_to(ROOT)),
                        'diagnostic_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'source_binding_evidence': proof,
                        'max_rgba_delta': maxima})
        else:
            pending = {
                'jinye': 'Unbound 21-frame cacheAsBitmap graph; non-unit outer scale and cache/input boundaries not proved.',
                'orochimaru': 'Unbound one-frame clip342 at five owner placements; JPEG3 bitmap340 decoding, non-unit outer scale and Blur20 boundaries not proved.',
                'yijiao': 'Unbound 50-frame smooth affine ColorMatrix graph; outer scale and blendMode5 remain separate from identity matrix.'}
            row.update({'diagnostic_exact': False, 'pending_proof': pending[who]})
        rows.append(row)
    assert len(rows) == 54 and len(bindings) == 36
    assert set(bindings) <= {(r['case'],r['tick']) for r in rows}
    remaining = [r for r in rows if not r['diagnostic_bound']]
    return {'images':54, 'source_backed_diagnostic_exact':36, 'unbound_images':18,
            'remaining_by_source':dict(sorted(Counter(r['source'] for r in remaining).items())),
            'historical_production_exact':baseline['exact'], 'production_suite_rerun':False,
            'production_admitted':False, 'full_as_ownership_proved':False, 'rows':rows}


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();result=inventory()
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print({k:v for k,v in result.items() if k!='rows'})
