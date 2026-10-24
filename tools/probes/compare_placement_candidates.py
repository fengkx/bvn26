"""Compare candidate placement compositing with native samples; no tolerance."""
import argparse
import json
from pathlib import Path


def compare(native: list, actual: list, kind: str) -> dict:
    if len(native) != len(actual):
        raise ValueError('Native/candidate case count mismatch')
    rows = []
    for index, (expected, observed) in enumerate(zip(native, actual)):
        reference = expected['premultiplied'] if kind == 'blend' else expected['pixels']
        if kind == 'shadow':
            reference = [v for pixel in reference for v in pixel]
            observed = [v for pixel in observed for v in pixel]
        if not reference or len(reference) != len(observed):
            raise ValueError(f'Case {index}: sample count mismatch')
        errors = [abs(a-b) for a,b in zip(reference, observed)]
        rows.append({'index': index, 'samples': len(errors),
                     'different': sum(e != 0 for e in errors), 'max_error': max(errors)})
    return {'passed': all(r['different'] == 0 for r in rows), 'cases': rows}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kind', choices=('blend', 'shadow'), required=True)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--actual', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = compare(json.loads(args.native.read_text()), json.loads(args.actual.read_text()), args.kind)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'passed': result['passed'], 'cases': len(result['cases']),
                      'exact': sum(r['different'] == 0 for r in result['cases'])}))
    raise SystemExit(0 if result['passed'] else 1)
