"""Report the Chad s76 receiver discriminator without inventing missing exits."""
import argparse
import json
from pathlib import Path
from urllib.parse import unquote

from tools.probes.chad_lifecycle_observer import validate_case
from tools.sampling_native import validate

PHASES = ('caller_before', 'callee_enter', 'goto_before', 'goto_after',
          'callee_exit', 'caller_after', 'root_sample')
FIELDS = ('phase', 'saved_path', 'receiver', 'saved_receiver', 'saved_parent',
          'saved_frame', 'depth', 'parent_frame', 'occupant', 'same_occupant')


def collect_lifecycle(lines):
    observations = []
    for line in lines:
        parts = line.split('|', 7)
        if len(parts) != 8:
            raise ValueError('malformed event')
        if parts[6] != 'chad_lifecycle':
            continue
        fields = parts[7].split(',')
        if len(fields) != len(FIELDS) or fields[0] not in PHASES:
            raise ValueError('malformed lifecycle observation')
        row = dict(zip(FIELDS, map(unquote, fields)))
        row.update(sequence=int(parts[2]), display=int(parts[4]), tick=int(parts[5]))
        if row['tick'] != (11 if row['phase'] == 'root_sample' else 10):
            raise ValueError('lifecycle event outside selected boundary')
        if row['same_occupant'] not in ('true', 'false'):
            raise ValueError('invalid receiver equality observation')
        observations.append(row)
    phases = [row['phase'] for row in observations]
    if len(set(phases)) != len(phases) or phases != sorted(phases, key=PHASES.index):
        raise ValueError('duplicate/out-of-order lifecycle observations')
    for required in ('caller_before', 'callee_enter', 'goto_before', 'root_sample'):
        if required not in phases:
            raise ValueError('missing discriminator observation: ' + required)
    before = observations[0]
    if not before['saved_path'].startswith('_level0.game.p1.mc.'):
        raise ValueError('wrong receiver scope')
    if any(row['saved_path'] != before['saved_path'] or row['depth'] != before['depth'] for row in observations):
        raise ValueError('changed tracked receiver identity')
    missing = [phase for phase in PHASES if phase not in phases]
    return {'observations': observations, 'missing_boundaries': missing,
            'exit_observations_complete': not missing,
            'production_admitted': False, 'native_parity_proven': False,
            'scope': 'one Chad tick-10 invocation; no VM control-flow or full AS ownership proof'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        validate_case(args.case)
        receipt_hash = validate(args.case, args.receipt)
        receipt = json.loads(args.receipt.read_text())
        metadata = json.loads((Path(receipt['build']) / 'build.json').read_text())
        if not metadata.get('chad_lifecycle') or not metadata.get('sampling_callsite'):
            raise ValueError('missing Chad lifecycle instrumentation')
        report = collect_lifecycle(Path(receipt['trace']).read_text().splitlines())
        report['receipt_sha256'] = receipt_hash
        args.output.write_text(json.dumps(report, indent=2) + '\n')
        if not report['exit_observations_complete']:
            raise ValueError('unobserved exit boundaries: ' + ', '.join(report['missing_boundaries']))
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(1, f'Chad lifecycle evidence error: {error}\n')


if __name__ == '__main__':
    main()
