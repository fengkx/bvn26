"""Fail closed on the unfulfilled AFTER-s344 rank-4 consumer binding prerequisite."""
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
    spec = importlib.util.spec_from_file_location('locked_s339', HERE.parent / 's339/diagnose.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def replay():
    result = load_prior().diagnose()
    if result != json.loads((HERE.parent / 's339/diagnosis.json').read_text()):
        raise ValueError('Complete locked s339 replay changed')
    return result


def expected_attempt():
    # This is a blocked measurement record, not an interface accepting proof claims.
    return dict(
        slice='s348', scope='AFTER-s344 rank #4 only',
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
        reason='Locked s339 supplies no independent executed-consumer/request resolver. '
               'The independent wrapper-exit callee route reaches opaque external transfers, not a live resolver. '
               'Normal remains unqualified; wrong-resource control was not executed.')


def audit_attempt(record):
    if record != expected_attempt():
        raise ValueError('Unobserved consumer/request/range record changed; new proof requires independent review')


def audit_route():
    route = json.loads((HERE / 'native-route.json').read_text())
    region = route['regions']['exit_callee']
    raw = bytes.fromhex(region['hex'])
    expected = bytes.fromhex('554889e54156534889fb4c8d73384c89f7e8d4dab100c64378014c89f7e8d4dab1004883c3084889df5b415e5de95edab100')
    if region['start'] != 0x498d20 or region['end_exclusive'] != 0x498d52 or raw != expected:
        raise ValueError('Bounded exit callee bytes changed')
    for offset, opcode, target in ((17, 0xe8, 0xfb680a), (29, 0xe8, 0xfb6816), (45, 0xe9, 0xfb67b0)):
        destination = region['start'] + offset + 5 + int.from_bytes(raw[offset+1:offset+5], 'little', signed=True)
        if raw[offset] != opcode or destination != target:
            raise ValueError('Exit callee transfer differs')
    if route['wrapper_call_target'] != region['start']:
        raise ValueError('Wrapper to callee association differs')
    return route


def diagnose():
    verify_pins(HERE / 'input-sha256.json')
    replay()
    verify_pins(HERE / 'route-sha256.json')
    route = audit_route()
    attempt = json.loads((HERE / 'binding-attempt.json').read_text())
    audit_attempt(attempt)
    return dict(
        slice='s348', scope='AFTER-s344 rank #4 only',
        production_admitted=False, native_parity_proven=False, m0_02_status='pending',
        locked_s339_reproduced=True, replay_is_new_progress=False,
        repeated_static_or_interface_audit_is_new_proof=False,
        attempt=attempt, native_route=route, independent_native_observations=0,
        mechanism_obligations_closed=0, product_obligations_closed=0,
        gates={g: dict(proved=False, code='S348_' + g.upper().replace('-', '_') + '_UNPROVED')
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
        parser.exit(1, 'S348_EVIDENCE_INVALID: ' + str(exc) + '\n')
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    failed = [result['gates'][g]['code'] for g in GATES
              if getattr(args, 'require_' + g.replace('-', '_'))]
    print('; '.join(failed) if failed else
          'S348_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')
    return int(bool(failed))


if __name__ == '__main__':
    raise SystemExit(main())
