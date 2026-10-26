"""Audit raw bitmap units and bound operand-precision changes without pixel fitting."""
import argparse
from collections import Counter
from fractions import Fraction
import gzip
import hashlib
import json
from pathlib import Path
import struct

from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.analyze_jinye_smooth_leaf import source_geometry, compose
from tools.probes.analyze_jinye_source_factorization import raw_geometry
from tools.probes.analyze_jinye_translation_controls import models_for
from tools.probes.analyze_jinye_smooth_controls import interior_geometry


def f32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


def row_displacement(first, second, points):
    return [max((abs((a*x+b*y+t+o)-(aa*x+bb*y+tt+oo)) for x, y, _ in points), default=0)
            for (a,b,t,o),(aa,bb,tt,oo) in zip(first, second)]


def changed_sample_addresses(first, second, points):
    def address(rows, x, y):
        return tuple((a*x+b*y+t+offset-32768)//256 for a, b, t, offset in rows)
    return sum(address(first, x, y) != address(second, x, y) for x, y, _ in points)


def analyze():
    native = ROOT/'evidence/importer-loud-fail/r221/native/fixture.json'
    raw_path = ROOT/'evidence/importer-loud-fail/r236/native/fixture.json'
    cells_path = ROOT/'evidence/importer-loud-fail/r232/analysis.json.gz'
    fixture = json.loads(native.read_text())
    raw = json.loads(raw_path.read_text())
    cells = json.loads(gzip.decompress(cells_path.read_bytes()))
    rows = []
    for spec in fixture['cases']:
        shape = next(s for s in fixture['shapes'] if s['id'] == spec['shape'])
        source = next(s for s in raw['shapes'] if s['source_shape'] == spec['shape'] and s['factor_id'] == -1)
        fill, _ = raw_geometry(source['parsed'])
        direct, polygon = source_geometry(spec, shape)
        # Preserve actual binary64 operands here so only raw-tag unit recovery differs.
        child = compose(list(map(Fraction, spec['outer'])), list(map(Fraction, spec['matrix'])))
        raw_direct = compose(compose(list(map(Fraction, spec['draw'])), child), fill)
        if direct != raw_direct:
            raise ValueError('XML fill recovery differs from unchanged source raw tag')
        models, _, _ = models_for(spec, shape)
        altered = {**spec, 'draw': [f32(v) for v in spec['draw']]}
        float_models, _, _ = models_for(altered, shape)
        _, points = interior_geometry(tuple(direct), tuple(polygon), (600, 400))
        rows.append({'shape': spec['shape'], 'raw_fill_pixel_matrix': list(map(str, fill)),
                     'raw_fill_and_xml_recovery_exact': True,
                     'draw_float32_is_only_a_precision_hypothesis': True,
                     'float32_draw_max_fixed_coordinate_change': {name: row_displacement(model, float_models[name], points)
                                                                   for name, model in models.items()},
                     'float32_draw_changed_8bit_sampling_addresses': {name: changed_sample_addresses(model, float_models[name], points) for name, model in models.items()},
                     'coordinate_unit': '1/65536 source pixel', 'geometry_samples': len(points)})
    measured = []
    for case in cells['cases']:
        if case['clip_id'] != 0 or case['cached']:
            continue
        models = {}
        for name, model in case['models'].items():
            histogram = Counter(((a[0]-b[0])//2, (a[1]-b[1])//6) for _,_,a,b in model['failures'])
            models[name] = {'samples': model['samples'], 'exact': model['exact'],
                            'failed_compatible_source_cell_delta_histogram': [[list(key), value] for key, value in sorted(histogram.items())]}
        measured.append({'shape': case['shape'], 'scale': case['scale'], 'models': models})
    return {'source_unit_audit': rows, 'retained_native_nearest_cell_measurements': measured,
            'inputs': [{'path': str(p.relative_to(ROOT)), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                       for p in (native, raw_path, cells_path)],
            'source_alpha_remeasured': False, 'rendering_model_tested': False,
            'precision_hypothesis_admitted': False, 'fitted_coefficients': False,
            'candidate_admitted': False, 'gpu_advance_allowed': False, 'production_admitted': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = analyze()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result['source_unit_audit'], indent=2))
