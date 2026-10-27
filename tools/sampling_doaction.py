"""Case-bound native DoAction entry coverage; incomplete AS ownership rejects."""
import argparse
from collections import Counter
import json
from pathlib import Path
from urllib.parse import unquote

from tools.probes.doaction_observer import inventory
from tools.sampling_native import ROOT, validate


def check_inventory(metadata):
    if not metadata.get('sampling_doaction'):
        raise ValueError('missing DoAction probe')
    expected = []
    for path in metadata['sources_sha256']:
        if path.startswith('scripts/') and path.endswith('.json'):
            expected.extend(inventory(json.loads((ROOT / path).read_text())))
    if not expected or metadata.get('doaction_inventory') != expected:
        raise ValueError('dropped/changed source obligation in DoAction inventory')
    return expected


def collect(lines, run_id, frames, records):
    by_id = {r['id']: r for r in records}
    if len(by_id) != len(records) or not records:
        raise ValueError('empty/duplicate source obligations')
    entries, samples = [], []
    last_sequence = 0
    for line in lines:
        parts = line.split('|', 7)
        if len(parts) != 8 or parts[:2] != ['AIREF', run_id]:
            raise ValueError('foreign/malformed action event')
        sequence, display, tick = int(parts[2]), int(parts[4]), int(parts[5])
        if sequence != last_sequence + 1:
            raise ValueError('missing/duplicate event sequence')
        last_sequence = sequence
        kind, value = parts[6:]
        if kind == 'doaction_sample':
            if tick != len(samples) or value != 'root-observer':
                raise ValueError('missing/duplicate root sample')
            samples.append({'tick': tick, 'sequence': sequence, 'display': display})
        elif kind == 'doaction_entry':
            identity, instance, current_frame = value.split(',')
            if identity not in by_id or not by_id[identity]['instrumented'] or not instance:
                raise ValueError('unbound/unsupported action entry')
            entries.append({'id': identity, 'instance': unquote(instance),
                            'current_frame': int(current_frame), 'sequence': sequence,
                            'display': display, 'observer_tick': tick})
        elif kind.startswith('doaction_'):
            raise ValueError('unsupported action observation')
    if len(samples) != frames + 1 or not entries:
        raise ValueError('missing root samples or executed action entries')
    counts = Counter(e['id'] for e in entries)
    fight_counts = Counter(e['id'] for e in entries if e['observer_tick'] >= 0)
    return {'samples': samples, 'entries': entries,
            'visited': [dict(r, executions=counts[r['id']], fight_executions=fight_counts[r['id']])
                        for r in records if counts[r['id']]],
            'unvisited': [r for r in records if r['instrumented'] and not counts[r['id']]],
            'uninstrumented': [r for r in records if not r['instrumented']],
            'entry_capture_complete': True, 'full_as_coverage_complete': False,
            'statement_call_ownership_proven': False,
            'native_parity_proven': False, 'production_admitted': False}


def require_full_coverage(report):
    # Block entry does not witness calls inside functions or untaken branches.
    # Do not turn an empty visited/missing list into a false AS-consumer proof.
    raise ValueError(f"incomplete AS coverage: {len(report['unvisited'])} unvisited blocks, "
                     f"{len(report['uninstrumented'])} uninstrumented scripts; statement/call ownership unproven")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        receipt_hash = validate(args.case, args.receipt)
        receipt = json.loads(args.receipt.read_text())
        metadata = json.loads((Path(receipt['build']) / 'build.json').read_text())
        records = check_inventory(metadata)
        report = collect(Path(receipt['trace']).read_text().splitlines(), metadata['run_id'],
                         metadata['move_case']['frames'], records)
        report.update(case_id=metadata['move_case']['id'], receipt_sha256=receipt_hash)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
        require_full_coverage(report)
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(1, f'DoAction evidence error: {error}\n')


if __name__ == '__main__':
    main()
