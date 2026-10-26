"""Cross one static-derived packed arithmetic candidate against independent native rows."""
import argparse
import json
from pathlib import Path
from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.matrix_packed_candidate import render
from tools.probes.analyze_matrix_coefficient_pairs import decode as coefficients_decode
from tools.probes.analyze_matrix_binary_pairs import decode as binary_decode
from tools.probes.analyze_matrix_coefficient_brackets import decode as brackets_decode
from tools.probes.analyze_matrix_offset_brackets import decode as offsets_decode
from tools.probes.analyze_matrix_neighbor_alpha import decode as neighbors_decode
from tools.probes.analyze_matrix_span_origins import decode as origins_decode
from tools.probes.analyze_materialized_matrix_owner import decode as materialized_decode, comparison


def analyze():
    root = ROOT/'evidence/importer-loud-fail'
    reports = {}
    for round_name, decoder in [('r200', lambda p: coefficients_decode(p)[1]),
                                ('r201', binary_decode), ('r202', brackets_decode), ('r203', offsets_decode)]:
        cases = decoder(root/round_name/'native')
        actual, native = [], []
        for case in cases:
            actual.extend(render(case['source'], 4, case['matrix']))
            native.extend(case['filtered'])
        reports[round_name] = comparison(actual, native, 4)
    matrix, cases = neighbors_decode(root/'r198/native')
    actual, native = [], []
    for case in cases:
        actual.extend(render(case['source'], case['key'][1], matrix))
        native.extend(case['filtered'])
    reports['r198'] = comparison(actual, native, 1)
    matrix, cases = origins_decode(root/'r199/native')
    actual, native = [], []
    for case in cases:
        _, width, sx, dx, *_ = case['key']
        output = [[0]*4 for _ in range(64)]
        output[dx:dx+width] = render(case['source'][sx:sx+width], width, matrix)
        actual.extend(output)
        native.extend(case['filtered'])
    reports['r199'] = comparison(actual, native, 64)
    build, images, *_ = materialized_decode(root/'r197/native')
    matrix = build['case']['placement']['filters'][0]['matrix']
    width = build['cache_allocation'][2]
    for tick in (0, 8):
        output = render(images[(tick, 'source')], width, matrix)
        for api in ('apply', 'display'):
            reports[f'r197/{tick}/{api}'] = comparison(output, images[(tick, api)], width)
    return {'comparisons': reports, 'measured_rgba_exact': all(not s['failures'] for s in reports.values()),
            'execution_routing_verified': False, 'general_alpha_controls_complete': False,
            'gpu_advance_allowed': False, 'production_admitted': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = analyze()
    args.output.write_text(json.dumps(result, separators=(',', ':'))+'\n')
    print({key: (r['exact'], r['samples'], r['max_channel_delta']) for key, r in result['comparisons'].items()})
