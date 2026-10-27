"""Validate one source-bound native predicate/call-site observation dimension."""
import argparse
import json
from pathlib import Path
from urllib.parse import unquote

from tools.probes.callsite_observer import specification
from tools.sampling_doaction import check_inventory, collect, require_full_coverage
from tools.sampling_native import validate


def collect_calls(lines, spec, *, retain_incomplete=False):
    identity = spec['handler_id']
    pending = None
    invocations = []
    incomplete = []
    for line in lines:
        p = line.split('|', 7)
        kind, value = p[6:]
        if kind == 'clipaction_entry' and value.split(',')[0] == identity:
            if pending is not None:
                if not retain_incomplete:
                    raise ValueError('incomplete/reentrant selected invocation')
                incomplete.append(pending)
            pending = {'entry_sequence': int(p[2]), 'observer_tick': int(p[5]),
                       'instance': unquote(value.split(',')[1]), 'phases': []}
        elif kind == 'callsite':
            fields = value.split(',')
            if (len(fields) != 3 or fields[0] != identity or pending is None
                    or unquote(fields[2]) != pending['instance']):
                raise ValueError('unbound call-site observation')
            phase = fields[1]
            previous = [v['phase'] for v in pending['phases']]
            allowed = {(): ['predicate_before'], ('predicate_before',): ['true', 'false'],
                       ('predicate_before', 'true'): ['call_before'],
                       ('predicate_before', 'true', 'call_before'): ['call_after'],
                       ('predicate_before', 'true', 'call_before', 'call_after'): ['end'],
                       ('predicate_before', 'false'): ['end']}
            if phase not in allowed.get(tuple(previous), []):
                raise ValueError('missing/duplicate/out-of-order branch or call event')
            pending['phases'].append({'phase': phase, 'sequence': int(p[2])})
            if phase == 'end':
                pending['taken'] = previous[1] == 'true'
                invocations.append(pending)
                pending = None
        elif kind.startswith('callsite'):
            raise ValueError('unsupported call-site observation')
    if pending is not None:
        if not retain_incomplete:
            raise ValueError('missing selected invocation observations')
        incomplete.append(pending)
    if not invocations:
        raise ValueError('missing selected invocation observations')
    taken = sum(x['taken'] for x in invocations)
    return {'specification': spec, 'invocations': invocations, 'true_count': taken,
            'false_count': len(invocations)-taken, 'paired_call_count': taken,
            'incomplete_invocations': incomplete,
            'invocation_observations_complete': not incomplete,
            'both_branch_outcomes_observed': 0 < taken < len(invocations),
            'callee_body_ownership_proven': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        receipt_hash = validate(args.case, args.receipt)
        receipt = json.loads(args.receipt.read_text())
        metadata = json.loads((Path(receipt['build'])/'build.json').read_text())
        if not metadata.get('sampling_callsite'):
            raise ValueError('missing call-site probe')
        records = check_inventory(metadata)
        spec = specification(records)
        if metadata.get('callsite_specification') != spec:
            raise ValueError('dropped/changed call-site obligations')
        lines = Path(receipt['trace']).read_text().splitlines()
        report = collect(lines, metadata['run_id'], metadata['move_case']['frames'], records)
        report['selected_callsite'] = collect_calls(lines, spec, retain_incomplete=True)
        report.update(case_id=metadata['move_case']['id'], receipt_sha256=receipt_hash)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n')
        if not report['selected_callsite']['invocation_observations_complete']:
            raise ValueError('incomplete selected call-site boundaries; see report')
        require_full_coverage(report)
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(1, f'call-site evidence error: {error}\n')


if __name__ == '__main__':
    main()
