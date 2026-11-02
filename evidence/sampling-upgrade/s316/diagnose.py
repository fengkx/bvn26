"""Audit archived control operands and observation gaps, without native identity inference."""
import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = '03b2e5df67adeddfb4a293d7009cc0b885b040d7'
REQUIREMENTS = {
    'slot-reference': 'S316_SLOT_REFERENCE_UNPROVED',
    'content-clearing': 'S316_CONTENT_CLEARING_UNPROVED',
    'replacement': 'S316_REPLACEMENT_UNPROVED',
    'allocation-identity': 'S316_POOL_GENERATIONS_UNPROVED',
}


def audit_controls(raw, source_audit):
    rows = []
    for line in raw.splitlines():
        if not line.startswith('AIREF|'):
            continue
        tag, run, seq, clock, root, tick, kind, payload = line.split('|', 7)
        rows.append(dict(run=run, sequence=int(seq), clock_ms=int(clock),
                         root=int(root), tick=int(tick), kind=kind, payload=payload))
    if len(rows) != 8290 or [r['sequence'] for r in rows] != list(range(1, 8291)):
        raise ValueError('changed or incomplete historical event stream')
    if {r['run'] for r in rows} != {'s261-yijiao-r01'}:
        raise ValueError('cross-run events')
    controls = [r for r in rows if r['kind'] == 's261_control']
    expected = ['retained,true,true', 'replaced,true,false', 'retained_content_deleted,true,false']
    if [r['payload'] for r in controls] != expected or [r['sequence'] for r in controls] != [21, 22, 23]:
        raise ValueError('changed control observations')
    logs = source_audit['control_logs']
    statements = [
        '_root.aiEvent("s261_control", "retained," + (saved == host.slot) + "," + (host.slot.identity == token));',
        '_root.aiEvent("s261_control", "replaced," + (saved == host.slot) + "," + (host.slot.identity == token));',
        '_root.aiEvent("s261_control", "retained_content_deleted," + (retained == host.slot) + "," + (host.slot.identity == secondToken));',
    ]
    if [(r['line'], r['statement']) for r in logs] != list(zip([51, 55, 59], statements)):
        raise ValueError('changed control expression provenance')
    bindings = []
    for event, log, refs in zip(controls, logs, [
        {'left_reference': 'saved', 'property_reference': 'token', 'definition_lines': [48, 49, 50]},
        {'left_reference': 'saved', 'property_reference': 'token', 'definition_lines': [48, 49, 53, 54]},
        {'left_reference': 'retained', 'property_reference': 'secondToken', 'definition_lines': [53, 54, 56, 57, 58]},
    ]):
        bindings.append(dict(event=event, source_log=log, operands=refs,
                             independent_native_referents=None))
    operations = source_audit['control_operations_in_source_order']
    intervals = []
    for label, lo, hi, seqs in [('creation_before_first_log', 47, 50, [None, 21]),
                               ('remove_replace', 52, 54, [21, 22]),
                               ('property_delete', 56, 58, [22, 23]),
                               ('cleanup_after_final_log', 60, 60, [23, None])]:
        intervals.append({'name': label, 'source_operations': [r for r in operations if lo <= r['line'] <= hi],
                          'bracketing_control_sequences': seqs,
                          'native_pool_events': None, 'native_generation_order_proved': False})
    return {
        'event_count': len(rows), 'as2_sequence_contiguous': True,
        'control_bindings': bindings, 'unobserved_native_intervals': intervals,
        'equal_boolean_signals': {'sequences': [22, 23], 'signal': ['true', 'false'],
                                 'same_reference_operands': False, 'native_identity_implication': None},
        'before_after_unload_window': [r for r in rows if 24 <= r['sequence'] <= 33],
        'root8_root9_window': [r for r in rows if 36 <= r['sequence'] <= 48],
        'independent_native_layouts_derived': False,
        'uninterrupted_native_pool_coverage': False,
        'limitation': 'Contiguous AS2 logs prove logger ordering only. Equal booleans use different saved values; no native layout, allocation generation or pool coverage follows.',
    }


def diagnose():
    for path, expected in json.loads((HERE / 'input-sha256.json').read_text()).items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != expected:
            raise ValueError('locked input changed: ' + path)
    spec = importlib.util.spec_from_file_location('s307_locked', HERE.parent / 's307/diagnose.py')
    prior = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prior)
    replay = prior.diagnose()
    if replay != json.loads((HERE.parent / 's307/diagnosis.json').read_text()):
        raise ValueError('locked s307 diagnosis mismatch')
    with gzip.open(HERE.parent / 's261/native-capture.log.gz', 'rt') as stream:
        audit = audit_controls(stream.read(), replay['source_audit'])
    return {
        'base': BASE, 'scope': 'AFTER-s308 rank #8 only', 'status': 'honest_unproved',
        'production_admitted': False, 'native_parity_proven': False,
        'm0_02_status': 'pending', 'product_obligations_closed': 0,
        'locked_s307_reproduced': True, 'locked_s307_diagnosis': replay,
        'control_operand_and_interval_audit': audit,
        'native_observations': replay['native_observations'],
        'slot_reference_proved': False, 'content_clearing_proved': False,
        'replacement_proved': False, 'allocation_identity_proved': False,
        'actual_native_controls_executed': False,
        'new_builds': 0, 'new_player_launches': 0, 'new_process_attaches': 0,
        'new_captures': 0, 'new_symbol_queries': 0, 'other_ranks_executed': [],
        'requirement_failure_codes': REQUIREMENTS,
        'blocker': 'Independent native slot/reference layouts and live bindings are absent; actual clear/replacement/free/reuse lack uninterrupted ordered object-pool generations.',
        'next_discriminator': replay['next_discriminator'],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    for name in REQUIREMENTS:
        parser.add_argument('--require-' + name, action='store_true')
    args = parser.parse_args()
    try:
        report = diagnose()
    except (ValueError, KeyError, OSError, TypeError) as exc:
        parser.exit(1, 'S316_EVIDENCE_INVALID: ' + str(exc) + '\n')
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    failures = [code for name, code in REQUIREMENTS.items()
                if getattr(args, 'require_' + name.replace('-', '_'))]
    if failures:
        parser.exit(1, '\n'.join(failures) + ': ' + report['blocker'] + '\n')
    print('S316_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')


if __name__ == '__main__':
    main()
