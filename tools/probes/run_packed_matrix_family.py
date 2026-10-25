"""Keep the source-backed live family intact while testing bounded packed matrix arithmetic."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from tools.probes.run_nearest_matrix_family import fixture as old_fixture, compare
from tools.probes.matrix_packed_candidate import coefficients
from tools.probes.build_bound_bitmap_component import ROOT


def fixture(output, native):
    spec = old_fixture(output, native)
    for case in spec['cases']:
        assert len(case['filters']) == 1 and case['filters'][0]['type'] == 'COLORMATRIXFILTER'
        case['packed_matrix_words'] = coefficients(case['filters'][0]['matrix'])
    (output/'fixture.json').write_text(json.dumps(spec, indent=2)+'\n')
    return spec


def run(godot, native, output):
    spec = fixture(output, native)
    for case in spec['cases']:
        for name in ('local', 'input', 'filtered', 'final'):
            (output/case['folder']/(name+'.png')).unlink(missing_ok=True)
    command = [str(godot), '--path', str(ROOT/'godot'), '--rendering-method', 'gl_compatibility',
               '--quit-after', '1200', '-s', str(ROOT/'godot/tests/packed_matrix_family_live.gd'),
               '--', str(output/'fixture.json'), str(output)]
    p = subprocess.run(command, capture_output=True, text=True, timeout=300)
    log = p.stdout+p.stderr
    (output/'godot.log').write_text(log)
    if p.returncode or 'ERROR' in log or 'PACKED_MATRIX_FAMILY_LIVE_OK cases=12' not in log:
        raise ValueError('Incomplete live packed-matrix family: '+log)
    result = compare(output, native)
    (output/'report.json').write_text(json.dumps(result, indent=2)+'\n')
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    files = ['tools/probes/run_packed_matrix_family.py', 'tools/probes/run_nearest_matrix_family.py',
             'tools/probes/run_nearest_matrix_component.py', 'tools/probes/matrix_packed_candidate.py',
             'godot/tests/packed_matrix_family_live.gd', 'godot/tests/packed_matrix_filter_group.gd',
             'godot/tests/packed_matrix_filter.gdshader', 'godot/tests/packed_matrix.gdshaderinc',
             'godot/tests/affine_component_coverage.gdshader', 'godot/filter_group.gd', 'godot/blend_group.gd',
             'godot/flash_filter.gdshader', 'godot/tests/native_nested_filter_composite.gdshader',
             'godot/tests/native_cxform.gdshaderinc', 'godot/tests/normal_composition.gdshaderinc']
    proof = {'command': command, 'exit': p.returncode, 'godot_sha256': sha(godot),
             'source_sha256': {name: sha(ROOT/name) for name in files},
             'readback_sha256': {str(p.relative_to(output)): sha(p) for p in output.rglob('*')
                                 if p.is_file() and p.name != 'provenance.json'},
             'production_admitted': False}
    (output/'provenance.json').write_text(json.dumps(proof, indent=2)+'\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--godot', type=Path, required=True)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = run(args.godot.resolve(), args.native.resolve(), args.output.resolve())
    print('exact', result['exact_images'], '/12', result['full_family_exact'])
    raise SystemExit(0 if result['full_family_exact'] else 1)
