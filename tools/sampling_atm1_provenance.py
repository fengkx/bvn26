"""Validate the bounded s64 helper stamp observation, retaining missing bindings."""
import argparse
import json
from pathlib import Path
from urllib.parse import unquote

from tools.probes.deidara_atm1_observer import LOAD_SOURCE, validate_case
from tools.sampling_native import validate

HELPER = '_level0.game.p1fz'
ATM1 = HELPER + '.atm1'
STAMP_SITE = 'game/fighter/fz/woailuo.swf#frame_44/DoAction.as'
FIELDS = ('phase', 'site', 'path', 'present', 'frame', 'helper_frame', 'depth',
          'stamp_id', 'stamp_source', 'stamp_birth')


def collect_provenance(lines):
    observations = []
    for line in lines:
        parts = line.split('|', 7)
        if len(parts) != 8:
            raise ValueError('malformed native event')
        if parts[6] != 'atm1_provenance':
            continue
        values = parts[7].split(',')
        if len(values) != len(FIELDS):
            raise ValueError('incomplete atm1 provenance payload')
        row = dict(zip(FIELDS, map(unquote, values)))
        row.update(sequence=int(parts[2]), display=int(parts[4]), tick=int(parts[5]))
        if row['tick'] not in range(56, 61) or row['present'] not in ('true', 'false'):
            raise ValueError('invalid atm1 observation boundary')
        phase = row['phase']
        if phase == 'root_sample':
            if row['site'] != 'root-before-geometry' or row['path'] != (ATM1 if row['present'] == 'true' else 'undefined'):
                raise ValueError('wrong root receiver/site')
        elif phase in ('load_before', 'load_after'):
            if row['site'] != LOAD_SOURCE or row['path'] != ATM1 or row['present'] != 'true':
                raise ValueError('wrong load source/receiver')
        elif phase in ('stamp_before', 'stamp_after'):
            if row['site'] != STAMP_SITE or row['path'] != HELPER or row['present'] != 'true':
                raise ValueError('unexpected stamp site/receiver; inspect raw evidence')
        else:
            raise ValueError('unknown atm1 provenance event')
        observations.append(row)
    samples = [r for r in observations if r['phase'] == 'root_sample']
    if [r['tick'] for r in samples] != list(range(56, 61)):
        raise ValueError('missing/duplicate/out-of-order root sample')
    # Require each site's pair, without imposing a cross-site scheduling order.
    for prefix in ('stamp', 'load'):
        pair = [r for r in observations if r['phase'].startswith(prefix + '_')]
        if [r['phase'] for r in pair] != [prefix + '_before', prefix + '_after']:
            raise ValueError('missing/duplicate/out-of-order source boundaries')
        before, after = pair
        if any(before[k] != after[k] for k in ('site', 'path', 'tick', 'display', 'depth', 'frame', 'helper_frame')):
            raise ValueError('source boundary identity changed')
    if any(a['sequence'] >= b['sequence'] for a, b in zip(observations, observations[1:])):
        raise ValueError('out-of-order provenance stream')
    present = [r for r in samples if r['present'] == 'true']
    if not present:
        raise ValueError('no live atm1 candidate observed')
    gaps = [{'tick': r['tick'], 'missing_fields': [f for f in ('stamp_id', 'stamp_source', 'stamp_birth') if r[f] == 'undefined']}
            for r in present]
    return {'observations': observations, 'observation_complete': True,
            'live_candidate_stamp_gaps': gaps,
            'stamp_binding_complete': all(not gap['missing_fields'] for gap in gaps),
            'production_admitted': False, 'native_parity_proven': False,
            'scope': 's64 source-bound load, parent stamp and root snapshots at ticks 56–60 only'}


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
        if not metadata.get('deidara_atm1') or not metadata.get('sampling_geometry'):
            raise ValueError('missing atm1 provenance probe')
        report = collect_provenance(Path(receipt['trace']).read_text().splitlines())
        report['receipt_sha256'] = receipt_hash
        args.output.write_text(json.dumps(report, indent=2) + '\n')
        if not report['stamp_binding_complete']:
            raise ValueError('atm1 stamp fields remain missing; see report')
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(1, f'atm1 provenance error: {error}\n')


if __name__ == '__main__':
    main()
