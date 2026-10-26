"""Gate the diagnostic GPU arithmetic on explicit native rows, never CPU output textures."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
from PIL import Image
from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.matrix_packed_candidate import coefficients, render
from tools.probes.analyze_matrix_coefficient_pairs import decode as coefficient_decode
from tools.probes.analyze_matrix_binary_pairs import decode as binary_decode
from tools.probes.analyze_matrix_coefficient_brackets import decode as bracket_decode
from tools.probes.analyze_matrix_offset_brackets import decode as offset_decode
from tools.probes.analyze_matrix_neighbor_alpha import decode as neighbor_decode
from tools.probes.analyze_matrix_span_origins import decode as origin_decode
from tools.probes.analyze_materialized_matrix_owner import decode as materialized_decode
from tools.probes.analyze_matrix_all_alpha_pairs import decode as alpha_decode
from tools.probes.analyze_matrix_legacy_inputs import decode_scalar, decode_ramp


def specimens():
    root = ROOT/'evidence/importer-loud-fail'
    result = []

    def add(group, source, matrix, native, offsets=None):
        width = len(source)
        assert 0 < width <= 256
        offsets = list(range(width)) if offsets is None else offsets
        predicted = render(source, width, matrix)
        assert [predicted[x] for x in offsets] == native
        result.append({'group': group, 'source': source, 'matrix': matrix,
                       'native': native, 'offsets': offsets})

    for name, decoder in [('r200', lambda p: coefficient_decode(p)[1]), ('r201', binary_decode),
                          ('r202', bracket_decode), ('r203', offset_decode)]:
        for case in decoder(root/name/'native'):
            add(name, case['source'], case['matrix'], case['filtered'])
    for name, decoder in [('r198', neighbor_decode), ('r205', alpha_decode)]:
        matrix, cases = decoder(root/name/'native')
        for case in cases:
            add(name, case['source'], matrix, case['filtered'])
    matrix, cases = origin_decode(root/'r199/native')
    for case in cases:
        _, width, sx, dx, *_ = case['key']
        add('r199/processed', case['source'][sx:sx+width], matrix, case['filtered'][dx:dx+width])
    build, images, *_ = materialized_decode(root/'r197/native')
    width = build['cache_allocation'][2]
    matrix = build['case']['placement']['filters'][0]['matrix']
    for tick in (0, 8):
        source, target = images[(tick, 'source')], images[(tick, 'apply')]
        assert target == images[(tick, 'display')]
        for start in range(0, len(source), width):
            add(f'r197/{tick}', source[start:start+width], matrix, target[start:start+width])
    for row in decode_scalar(root/'r206/scalar'):
        # Only the captured interior sample is checked; repeated context supplies
        # the independently verified same-alpha neighboring pair.
        add('r206/scalar', [row['input']]*4, row['matrix'], [row['native']], [0])
    for row in decode_ramp(root/'r206/ramp'):
        for source, target in zip(row['source'], row['native']):
            add('r206/ramp', [source]*3, row['matrix'], [target], [0])
    return result


def fixture(output, rows):
    output.mkdir(parents=True, exist_ok=True)
    batches = []
    for start in range(0, len(rows), 1024):
        subset = rows[start:start+1024]
        name = f'batch{start//1024:03d}'
        source = bytearray()
        words = bytearray()
        for row in subset:
            pixels = row['source']
            source.extend(bytes(c for p in pixels for c in p))
            source.extend(bytes((256-len(pixels))*4))
            matrix = coefficients(row['matrix'])
            for column in range(5):
                words.extend(struct.pack('<4f', *(matrix[channel][column] for channel in range(4))))
            words.extend(struct.pack('<4f', len(pixels), 0, 0, 0))
        (output/(name+'.rgba')).write_bytes(source)
        (output/(name+'.words')).write_bytes(words)
        (output/(name+'.png')).unlink(missing_ok=True)
        batches.append({'name': name, 'start': start, 'height': len(subset)})
    result = {'batches': batches, 'row_count': len(rows), 'production_admitted': False}
    (output/'fixture.json').write_text(json.dumps(result, indent=2)+'\n')
    return result


def compare(output, spec, rows):
    groups = {}
    for batch in spec['batches']:
        image = Image.open(output/(batch['name']+'.png')).convert('RGBA')
        assert image.size == (256, batch['height'])
        for y, row in enumerate(rows[batch['start']:batch['start']+batch['height']]):
            group = groups.setdefault(row['group'], {'samples': 0, 'exact': 0, 'max_channel_delta': 0, 'failures': []})
            for x, expected in zip(row['offsets'], row['native']):
                actual = list(image.getpixel((x, y)))
                group['samples'] += 1
                group['exact'] += actual == expected
                group['max_channel_delta'] = max(group['max_channel_delta'], max(abs(a-b) for a,b in zip(actual,expected)))
                if actual != expected:
                    group['failures'].append({'row': batch['start']+y, 'x': x, 'actual': actual, 'native': expected})
    return {'comparisons': groups, 'exact': all(not r['failures'] for r in groups.values()),
            'production_admitted': False, 'actual_filter_group_binding_completed': False}


def run(godot, output):
    rows = specimens()
    spec = fixture(output, rows)
    command = [str(godot), '--path', str(ROOT/'godot'), '--rendering-method', 'gl_compatibility',
               '--quit-after', '2400', '-s', str(ROOT/'godot/tests/packed_matrix_rows.gd'), '--', str(output)]
    p = subprocess.run(command, capture_output=True, text=True, timeout=300)
    log = p.stdout+p.stderr
    (output/'godot.log').write_text(log)
    if p.returncode or 'ERROR' in log or f'PACKED_MATRIX_ROWS_OK batches={len(spec["batches"])}' not in log:
        raise ValueError('Incomplete packed-matrix GPU diagnostic: '+log)
    result = compare(output, spec, rows)
    (output/'report.json').write_text(json.dumps(result, indent=2)+'\n')
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    paths = ['tools/probes/run_packed_matrix_rows.py', 'tools/probes/matrix_packed_candidate.py',
             'godot/tests/packed_matrix_rows.gd', 'godot/tests/packed_matrix_rows.gdshader', 'godot/tests/packed_matrix.gdshaderinc']
    proof = {'command': command, 'exit': p.returncode, 'godot_sha256': sha(godot),
             'source_sha256': {name: sha(ROOT/name) for name in paths},
             'artifact_sha256': {p.name: sha(p) for p in output.iterdir() if p.is_file() and p.name != 'provenance.json'},
             'production_admitted': False}
    (output/'provenance.json').write_text(json.dumps(proof, indent=2)+'\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--godot', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = run(args.godot.resolve(), args.output.resolve())
    print({k: (v['exact'],v['samples'],v['max_channel_delta']) for k,v in result['comparisons'].items()})
    raise SystemExit(0 if result['exact'] else 1)
