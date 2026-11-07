"""Fail closed on the unfulfilled AFTER-s353 rank-5 consumer binding prerequisite."""
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
    spec = importlib.util.spec_from_file_location('locked_s348', HERE.parent / 's348/diagnose.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def replay():
    result = load_prior().diagnose()
    if result != json.loads((HERE.parent / 's348/diagnosis.json').read_text()):
        raise ValueError('Complete locked s348 replay changed')
    return result


def expected_attempt():
    # This is a blocked measurement record, not an interface accepting proof claims.
    return dict(
        slice='s358', scope='AFTER-s353 rank #5 only',
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
        reason='Locked s348 supplies no independent executed-consumer/request resolver. '
               'The independent first-call import association names _pthread_mutex_lock, not a live request resolver. '
               'Normal remains unqualified; wrong-resource control was not executed.')


def audit_attempt(record):
    if record != expected_attempt():
        raise ValueError('Unobserved consumer/request/range record changed; new proof requires independent review')


def audit_route():
    import struct
    route = json.loads((HERE / 'native-route.json').read_text())
    spans = route['spans']
    def raw(name):
        row = spans[name]
        data = bytes.fromhex(row['hex'])
        if len(data) != row['size']:
            raise ValueError('span size differs')
        return data
    section = raw('stub_section')
    address, size = struct.unpack_from('<QQ', section, 32)
    fileoff, _, _, _, flags, first, stride, _ = struct.unpack_from('<8I', section, 48)
    target = route['first_call_target']
    base = route['image_base']
    if target != 0xfb680a or base != 0x100000000 or flags & 0xff != 8 or stride != 6:
        raise ValueError('stub metadata differs')
    delta = base + target - address
    if not 0 <= delta < size or delta % stride:
        raise ValueError('unaligned stub')
    index = delta // stride
    indirect = struct.unpack('<I', raw('indirect_entry'))[0]
    symoff, nsyms, stroff, strsize = struct.unpack_from('<4I', raw('symtab_command'), 8)
    dysym = struct.unpack_from('<18I', raw('dysymtab_command'), 8)
    string, kind, sect, desc, value = struct.unpack('<IBBHQ', raw('symbol_entry'))
    stub = raw('first_stub')
    checks = [
        index == route['stub_index'] == 684,
        first + index == route['indirect_index'] < dysym[13],
        spans['indirect_entry']['file_offset'] == dysym[12] + 4 * (first + index),
        indirect == route['symbol_index'] == 936 and indirect < nsyms,
        spans['symbol_entry']['file_offset'] == symoff + 16 * indirect,
        spans['symbol_string']['file_offset'] == stroff + string and string < strsize,
        raw('symbol_string') == b'_pthread_mutex_lock\0',
        route['symbol'] == '_pthread_mutex_lock',
        (kind, sect, desc, value) == (1, 0, 5376, 0),
        (route['symbol_type'], route['symbol_section'], route['symbol_description'], route['symbol_value']) == (kind, sect, desc, value),
        spans['first_stub']['file_offset'] == fileoff + delta,
        stub == bytes.fromhex('ff25d0ce4f00'),
        route['pointer_slot_module_relative'] == target + 6 + struct.unpack_from('<i', stub, 2)[0],
        all(route[k] is None for k in ('live_pointer_value', 'loaded_provider', 'live_request_resolver')),
    ]
    if not all(checks):
        raise ValueError('import association differs or static route promoted')
    return route


def diagnose():
    verify_pins(HERE / 'input-sha256.json')
    retained = replay()
    verify_pins(HERE / 'route-sha256.json')
    route = audit_route()
    attempt = json.loads((HERE / 'binding-attempt.json').read_text())
    audit_attempt(attempt)
    return dict(
        slice='s358', scope='AFTER-s353 rank #5 only',
        production_admitted=False, native_parity_proven=False, m0_02_status='pending',
        locked_s348_reproduced=True, locked_s348_diagnosis=retained, replay_is_new_progress=False,
        repeated_static_or_interface_audit_is_new_proof=False,
        attempt=attempt, native_route=route, independent_native_observations=0,
        mechanism_obligations_closed=0, product_obligations_closed=0,
        gates={g: dict(proved=False, code='S358_' + g.upper().replace('-', '_') + '_UNPROVED')
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
        parser.exit(1, 'S358_EVIDENCE_INVALID: ' + str(exc) + '\n')
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    failed = [result['gates'][g]['code'] for g in GATES
              if getattr(args, 'require_' + g.replace('-', '_'))]
    print('; '.join(failed) if failed else
          'S358_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')
    return int(bool(failed))


if __name__ == '__main__':
    raise SystemExit(main())
