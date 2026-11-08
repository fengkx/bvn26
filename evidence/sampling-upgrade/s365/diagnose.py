"""Audit the selected AImain candidate prefix without promoting it to a resolver."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = 'e3133e94c741a868a3a05ef595158ffd34c68b4d'
PREFIX = bytes.fromhex('554889e531c04885ff7449')
GATES = ('parent-depth-resolver', 'saved-reference', 'slot-reference',
         'content-clearing', 'replacement', 'allocation-identity')


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verify_pins(path):
    for name, digest in json.loads(path.read_text()).items():
        if sha((ROOT / name).read_bytes()) != digest:
            raise ValueError('Locked input changed: ' + name)


def replay():
    prior = load('s365_locked_s360', HERE.parent / 's360/diagnose.py').diagnose()
    if prior != json.loads((HERE.parent / 's360/diagnosis.json').read_text()):
        raise ValueError('Complete locked s360 replay changed')
    return prior


def audit(native, prior):
    if prior != json.loads((HERE.parent / 's360/diagnosis.json').read_text()):
        raise ValueError('Complete retained diagnosis differs')
    edge = prior['reference_attempt']['relative_code_association']
    if (edge['call_address'], edge['call_target']) != (0x1000bfcfd, 0x10005d960):
        raise ValueError('Selected direct call differs')
    locked = json.loads((HERE.parent / 's303/native-audit.json').read_text())
    expected = dict(binary_sha256=locked['binary_sha256'], binary_size=24120048,
                    module_uuid=locked['module']['uuid'], image_base=locked['image_base'],
                    caller=0xbfcfd, start=0x5d960, end_exclusive=0x5d96b,
                    file_offset=0x5d960, function_start=0x10005d960,
                    next_function_start=0x10005d9c0,
                    hex=PREFIX.hex(), sha256=sha(PREFIX), successor_bytes_read=0,
                    new_player_launches=0, new_memory_reads=0)
    if native != expected:
        raise ValueError('Prefix bytes, boundary or provenance differ')
    return dict(coordinates='Unslid image addresses; not live PCs',
                start=0x10005d960, end_exclusive=0x10005d96b,
                instructions=[
                    dict(address=0x10005d960, hex='55', operation='push RBP'),
                    dict(address=0x10005d961, hex='4889e5', operation='RBP = RSP'),
                    dict(address=0x10005d964, hex='31c0', operation='EAX = 0; zero-extend RAX'),
                    dict(address=0x10005d966, hex='4885ff', operation='test RDI & RDI'),
                    dict(address=0x10005d969, hex='7449', operation='JE rel8')],
                taken_target=0x10005d96b + int.from_bytes(PREFIX[-1:], 'little', signed=True),
                fallthrough=0x10005d96b, condition='incoming RDI == 0',
                prefix_bytes=11, prefix_instructions=5, rdi_dereferenced_in_prefix=False,
                rsi_used_in_prefix=False, parent_resolver=None, actual_execution=None,
                incoming_rdi=None, loaded_module_generation=None, result_generation=None,
                successor_code_expanded=False, other_candidates_expanded=0,
                limitation='Register-zero predicate only; stack prologue is not a saved AS2 referent. No resolver semantics, return value or native generation proved.')


def audit_saved(saved):
    expected = dict(source_route='_global.s261Receiver -> saved', source_is_retained_only=True,
                    value_location=None, representation=None, dereference_instructions=None,
                    result_allocation_generation=None, new_native_measurement=None,
                    slot_result_borrowed=False, parent_text_argument_is_saved_referent=False,
                    stack_prologue_is_saved_referent=False,
                    attempt_status='blocked_before_native_dereference')
    if saved != expected:
        raise ValueError('Saved reference representation/dereference remains independently unproved')
    return saved


def diagnose():
    verify_pins(HERE / 'input-sha256.json')
    verify_pins(HERE / 'route-sha256.json')
    prior = replay()
    return dict(slice='s365', base=BASE, scope='AFTER-s362 rank #3 only',
                production_admitted=False, native_parity_proven=False, m0_02_status='pending',
                retained=prior, complete_s360_replayed=True, prior_results_are_new_progress=False,
                audit=audit(json.loads((HERE / 'native-prefix.json').read_text()), prior),
                saved_reference=audit_saved(json.loads((HERE / 'saved-reference-attempt.json').read_text())),
                lookup_paths=prior['lookup_paths'], observations=prior['observations'],
                gates={g: dict(proved=False, code='S365_' + g.upper().replace('-', '_') + '_UNPROVED') for g in GATES},
                independent_static_prefix_observed=True, independent_native_observations=0,
                actual_native_controls_executed=False, new_builds=0, new_player_launches=0,
                new_attaches=0, new_memory_reads=0, new_captures=0,
                mechanism_obligations_closed=0, product_obligations_closed=0,
                other_ranks_executed=[], ranks_1_2='delivered', ranks_4_plus='planning only',
                blocker='Parent/depth resolver and separate saved-value representation/dereference unproved; live generations and clearing/replacement/free/reuse/pool controls not attempted.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    for gate in GATES:
        parser.add_argument('--require-' + gate, action='store_true')
    args = parser.parse_args()
    try:
        report = diagnose()
    except (ValueError, OSError, KeyError, IndexError) as exc:
        parser.exit(1, 'S365_EVIDENCE_INVALID: ' + str(exc) + '\n')
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    failures = [report['gates'][g]['code'] for g in GATES
                if getattr(args, 'require_' + g.replace('-', '_'))]
    print('; '.join(failures) if failures else 'S365_DIAGNOSIS_OK production_admitted=false native_parity_proven=false M0-02=pending')
    return int(bool(failures))


if __name__ == '__main__':
    raise SystemExit(main())
