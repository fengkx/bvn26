"""Fail closed on the unfulfilled AFTER-s335 rank-4 consumer binding prerequisite."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
GATES = ('consumer-request', 'returned-consumed-ranges', 'pre-advance-target',
         'loader-attestation', 'wrong-resource-control')
BOUNDARIES = ('read-entry', 'read-return', 'consumer-use', 'pre-inline-advance',
              'initialization', 'target-use', 'unload', 'replacement')


def verify_pins(path):
    for name, digest in json.loads(path.read_text()).items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise ValueError('Locked input changed: ' + name)


def load_prior():
    spec = importlib.util.spec_from_file_location('locked_s330', HERE.parent / 's330/diagnose.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def replay():
    result = load_prior().diagnose()
    if result != json.loads((HERE.parent / 's330/diagnosis.json').read_text()):
        raise ValueError('Complete locked s330 replay changed')
    return result


def expected_attempt():
    # This is a blocked measurement record, not an interface accepting proof claims.
    return dict(
        slice='s339', scope='AFTER-s335 rank #4 only',
        status='blocked-before-live-binding',
        independent_channel=None, native_run=None, executed_caller=None,
        actual_p1_consumer=None, immutable_request_generation=None,
        executed_read_return=None, returned_buffer_ranges=None,
        consumed_buffer_ranges=None, target_before_inline_advance=None,
        partial_or_failed_read_behavior=None, uninterrupted_lifetime=None,
        observer_effects=None,
        boundaries=[dict(boundary=b, event=None, request_generation=None,
                         range_measurement=None, target_generation=None) for b in BOUNDARIES],
        normal_association_qualified=False, wrong_resource_control_executed=False,
        independent_observations=[],
        reason='Locked s330 supplies no independent executed-consumer/request resolver. '
               'No replacement resolver or live request/range/target trace was obtained in s339. '
               'Normal remains unqualified; wrong-resource control was not executed.')


def audit_attempt(record):
    if record != expected_attempt():
        raise ValueError('Unobserved consumer/request/range record changed; new proof requires independent review')


def diagnose():
    verify_pins(HERE / 'input-sha256.json')
    replay()
    attempt = json.loads((HERE / 'binding-attempt.json').read_text())
    audit_attempt(attempt)
    return dict(
        slice='s339', scope='AFTER-s335 rank #4 only',
        production_admitted=False, native_parity_proven=False, m0_02_status='pending',
        locked_s330_reproduced=True, replay_is_new_progress=False,
        repeated_static_or_interface_audit_is_new_proof=False,
        attempt=attempt, independent_native_observations=0,
        mechanism_obligations_closed=0, product_obligations_closed=0,
        gates={g: dict(proved=False, code='S339_' + g.upper().replace('-', '_') + '_UNPROVED')
               for g in GATES},
        new_builds=0, new_player_launches=0, new_attaches=0, new_memory_reads=0,
        new_helper_installations=0, new_captures=0, other_ranks_executed=[],
        next_required_evidence='Bind an actually executed P1 consumer to immutable request '
                               'generation, actual returned and consumed ranges including partial/failed '
                               'reads, and target before inline loadStep advance. Preserve same-request '
                               'initialization/use/unload/replacement and qualify observer effects. '
                               'Qualify normal before any wrong-resource control.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    for gate in GATES:
        parser.add_argument('--require-' + gate, action='store_true')
    args = parser.parse_args()
    try:
        result = diagnose()
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(1, 'S339_EVIDENCE_INVALID: ' + str(exc) + '\n')
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    failed = [result['gates'][g]['code'] for g in GATES
              if getattr(args, 'require_' + g.replace('-', '_'))]
    print('; '.join(failed) if failed else
          'S339_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')
    return int(bool(failed))


if __name__ == '__main__':
    raise SystemExit(main())
