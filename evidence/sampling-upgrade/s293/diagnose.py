"""Recheck s293's independent host archives without repairing the locked s284 pair."""
import argparse
from datetime import datetime
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
LOCKED = HERE.parent / 's284'
sys.path.insert(0, str(LOCKED))
spec = importlib.util.spec_from_file_location('s284_locked_diagnose', LOCKED / 'diagnose.py')
retained = importlib.util.module_from_spec(spec)
spec.loader.exec_module(retained)
CASE = retained.CASE


def digest(data):
    return hashlib.sha256(data).hexdigest()


def check_host(host, trace, metadata, check):
    prefix = ('AIREF|' + metadata['run_id'] + '|').encode()
    lines = [line for line in host.splitlines() if line.startswith(prefix)]
    selected = b'\n'.join(lines) + b'\n'
    if not lines or selected != trace:
        raise ValueError('S293_HOST_LOG_MISMATCH')
    if (check['equal'] is not True or check['trace_trimmed'] is not False
            or check['run_id'] != metadata['run_id'] or check['events'] != len(lines)
            or check['host_sha256'] != digest(host) or check['sha256'] != digest(trace)):
        raise ValueError('S293_HOST_RECORD_MISMATCH')
    return {'equal': True, 'events': len(lines), 'host_sha256': digest(host),
            'sha256': digest(trace), 'host_order_preserved': True}


def check_sequence(records, runs):
    if [r['mode'] for r in records] != ['normal', 'held']:
        raise ValueError('S293_PAIR_IDENTITY_INVALID')
    identities = [runs[mode]['run_id'] for mode in ('normal', 'held')]
    if len(set(identities)) != 2 or any(not identity.startswith('s293-') for identity in identities):
        raise ValueError('S293_PAIR_IDENTITY_INVALID')
    times = []
    for record in records:
        if record['build_exit'] != 0:
            raise ValueError('S293_BUILD_FAILED')
        if record['host_checked_at'] != runs[record['mode']]['host_log_equality']['checked_at']:
            raise ValueError('S293_CHECK_TIME_MISMATCH')
        times.extend(datetime.fromisoformat(record[key]) for key in (
            'started_at', 'qualified_at', 'launch_started_at', 'host_archived_at',
            'host_checked_at', 'receipt_validated_at', 'archiving_finished_at'))
    if times != sorted(times) or records[0]['host_checked_at'] >= records[1]['launch_started_at']:
        raise ValueError('S293_ARCHIVE_ORDER_UNPROVED')
    return True


def diagnose():
    for name, expected in json.loads((HERE / 'input-sha256.json').read_text()).items():
        if digest((ROOT / name).read_bytes()) != expected:
            raise ValueError('changed locked input: ' + name)
    retained.HERE = LOCKED
    historical = retained.diagnose()
    if historical != json.loads((LOCKED / 'diagnosis.json').read_text()):
        raise ValueError('S293_LOCKED_S284_DRIFT')
    # Reuse the unchanged archived-source, receipt, strict stream and coverage
    # checks. New host claims below are derived from bytes, not recorded booleans.
    retained.HERE = HERE
    try:
        report = retained.diagnose()
    finally:
        retained.HERE = LOCKED
    report.update(scope='AFTER-s290 rank #3 only',
                  base='5bdc9f619ca18c217110e8829149d82c060a3706',
                  locked_s284_diagnosis_equal=True,
                  locked_s284_independent_pair_proved=historical['independent_pair_proved'])
    for mode, run in report['runs'].items():
        base = HERE / mode
        metadata = json.loads((base / 'native-build.json').read_text())
        receipt = json.loads((base / 'receipt.json').read_text())
        if receipt['production_admitted'] is not False or receipt['native_parity_proven'] is not False:
            raise ValueError('S293_RECEIPT_ADMISSION_INVALID')
        run['run_id'] = metadata['run_id']
        run['independent_host_recheck'] = check_host(
            gzip.decompress((base / 'host-log.txt.gz').read_bytes()),
            gzip.decompress((base / 'native-capture.log.gz').read_bytes()),
            metadata, run['host_log_equality'])
    records = json.loads((HERE / 'execution.json').read_text())
    report['each_host_archived_and_checked_before_next_launch'] = check_sequence(records, report['runs'])
    report['independent_pair_proved'] = bool(report['independent_pair_proved'] and
        report['each_host_archived_and_checked_before_next_launch'])
    report['proof_scope'] = 'independently archived bounded normal/held pair only; not terminal callback completeness'
    report['other_ranks_executed'] = False
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--require-completion-proof', action='store_true')
    parser.add_argument('--require-terminal-completeness', action='store_true')
    parser.add_argument('--require-full-as', choices=('normal', 'held'))
    args = parser.parse_args()
    try:
        report = diagnose()
    except (ValueError, KeyError, OSError, TypeError) as error:
        print('S293_EVIDENCE_INVALID: ' + str(error))
        return 1
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    if args.require_completion_proof and not report['independent_pair_proved']:
        print('S293_INDEPENDENT_PAIR_UNPROVED'); return 1
    if args.require_terminal_completeness:
        print('S293_TERMINAL_CALLBACK_COMPLETENESS_UNPROVED'); return 1
    if args.require_full_as:
        print('S293_FULL_AS_UNPROVED: ' + report['runs'][args.require_full_as]['full_as_gate']['error']); return 1
    print('S293_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
