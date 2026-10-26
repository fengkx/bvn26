"""Measure signed orthogonal and unit-shear factorizations without route selection."""
import argparse
import json
from pathlib import Path

from tools.probes.analyze_jinye_axis_factorization import analyze as compare_native_factorizations
from tools.probes.decode_jinye_signed_factorization import decode

EXPECTED_FACTORS = tuple(range(-1, 9))


def analyze(native):
    result = compare_native_factorizations(native, decoder=decode, expected_factors=EXPECTED_FACTORS,
                                          retained_rounds=tuple(range(232, 239)))
    result['factor_family_metadata'] = {'orthogonal': [0, 1, 2, 3, 4], 'unit_shear': [5, 6, 7, 8],
                                        'classification_selected_rendering_path': False}
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.native)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, separators=(',', ':'))+'\n')
    print(json.dumps({key: result[key] for key in ('totals', 'groups', 'baseline_gate_passed')}, indent=2))
    if not result['baseline_gate_passed']:
        raise SystemExit(1)
