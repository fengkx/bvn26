"""Separate s239's target lookup failure from missing source lists or stamps."""
import argparse
import json
from pathlib import Path
from urllib.parse import unquote

from tools.probes.yulong_k1atm_observer import TARGET, validate_case
from tools.sampling_native import validate

SOURCE = 'game/fighter/yulong.swf#DefineSprite_2/frame_1/DoAction.as'
FIELDS = ('phase', 'path', 'present', 'frame', 'stamp_id', 'stamp_source', 'stamp_birth',
          'parent_path', 'parent_frame', 'parent_pn', 'target_path',
          'fs_defined', 'fs_length', 'fs_values', 'fz_defined', 'fz_length', 'fz_values',
          'stg_defined', 'stg_length', 'stg_values', 'get_hit_type', 'get_stage_hit_type',
          'grandparent_path', 'grandparent_pn')


def collect_provenance(lines):
    observations = []
    for line in lines:
        parts = line.split('|', 7)
        if len(parts) != 8:
            raise ValueError('malformed native event')
        if parts[6] != 'k1atm_provenance':
            continue
        values = parts[7].split(',')
        if len(values) != len(FIELDS):
            raise ValueError('incomplete k1atm provenance payload')
        row = dict(zip(FIELDS, map(unquote, values)))
        row.update(sequence=int(parts[2]), display=int(parts[4]), tick=int(parts[5]))
        if row['tick'] not in range(15, 20) or row['phase'] not in ('root_sample', 'source_after_stamp', 'source_list_check'):
            raise ValueError('unexpected k1atm provenance boundary')
        for flag in ('present', 'fs_defined', 'fz_defined', 'stg_defined'):
            if row[flag] not in ('true', 'false'):
                raise ValueError('invalid presence flag')
        if row['present'] == 'true':
            if row['path'] != TARGET or row['parent_path'] != TARGET.rsplit('.', 1)[0]:
                raise ValueError('wrong receiver/parent identity')
            if row['stamp_source'] not in (SOURCE, 'undefined'):
                raise ValueError('unexpected receiver stamp source')
            for prefix in ('fs', 'fz', 'stg'):
                if row[prefix + '_defined'] == 'true':
                    count = int(row[prefix + '_length'])
                    items = [] if row[prefix + '_values'] == '' else row[prefix + '_values'].split(',')
                    if count != len(items):
                        raise ValueError('list contents/length mismatch')
        elif row['path'] != 'undefined' or row['phase'] != 'root_sample':
            raise ValueError('unexpected absent receiver')
        observations.append(row)
    roots = [r for r in observations if r['phase'] == 'root_sample']
    if [r['tick'] for r in roots] != list(range(15, 20)):
        raise ValueError('missing/duplicate/out-of-order root samples')
    entries = [r for r in observations if r['phase'] == 'source_after_stamp']
    checks = [r for r in observations if r['phase'] == 'source_list_check']
    live = [r for r in roots if r['present'] == 'true']
    if len(entries) != 1 or not live or [r['tick'] for r in checks] != [r['tick'] for r in live]:
        raise ValueError('missing/duplicate source entry or source-list check')
    for root, check in zip(live, checks):
        if any(root[k] != check[k] for k in FIELDS[1:]) or root['sequence'] >= check['sequence']:
            raise ValueError('root/check observation mismatch')
    if any(r['stamp_id'] != entries[0]['stamp_id'] for r in live + checks):
        raise ValueError('changed receiver stamp identity')
    if entries[0]['sequence'] >= live[0]['sequence']:
        raise ValueError('source initializer not observed before first live sample')
    if any(a['sequence'] >= b['sequence'] for a, b in zip(observations, observations[1:])):
        raise ValueError('out-of-order provenance stream')
    failures = []
    for row in checks:
        failed = []
        if row['target_path'] == 'undefined':
            failed.append('target == undefined')
        for prefix, name in (('fs', '_fsArray'), ('fz', '_fzfsArray'), ('stg', 'stgks')):
            if row[prefix + '_defined'] == 'false':
                failed.append(name + ' == undefined')
        failures.append({'tick': row['tick'], 'failed_predicates': failed})
    return {'observations': observations, 'observation_complete': True,
            'source_list_failures': failures,
            'source_list_checks_complete': all(not r['failed_predicates'] for r in failures),
            'production_admitted': False, 'native_parity_proven': False,
            'scope': 'one source initializer and exact geometry predicate operands at the s239 nested path'}


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
        if not metadata.get('yulong_k1atm') or not metadata.get('sampling_geometry'):
            raise ValueError('missing k1atm provenance probe')
        report = collect_provenance(Path(receipt['trace']).read_text().splitlines())
        report['receipt_sha256'] = receipt_hash
        args.output.write_text(json.dumps(report, indent=2) + '\n')
        if not report['source_list_checks_complete']:
            raise ValueError('original source-list predicate still fails; see report')
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(1, f'k1atm provenance error: {error}\n')


if __name__ == '__main__':
    main()
