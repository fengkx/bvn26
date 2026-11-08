"""Audit one Chad destination prefix; no successor expansion or live proof."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = 'f222cce04f72c71d59ce81dac1dbe556f4951576'
PREFIX = bytes.fromhex('89d883e0074883f8077508')
GATES = {name: 'S363_' + name.upper().replace('-', '_') + '_UNPROVED'
         for name in ('external-effects', 'value-ownership', 'live-binding',
                      'cursor-convention', 'retained-invocation')}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load_prior():
    spec = importlib.util.spec_from_file_location('s363_locked_s354', HERE.parent / 's354/diagnose.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_pins(path):
    for name, digest in json.loads(path.read_text()).items():
        if sha((ROOT / name).read_bytes()) != digest:
            raise ValueError('Locked input changed: ' + name)


def replay():
    prior = load_prior().diagnose()
    if prior != json.loads((HERE.parent / 's354/diagnosis.json').read_text()):
        raise ValueError('Locked s354 replay changed')
    return prior


def audit(native, prior):
    retained = json.loads((HERE.parent / 's354/diagnosis.json').read_text())
    if prior != retained:
        raise ValueError('Complete retained diagnosis differs')
    row = prior['audit']['rows'][0]
    if (row['index'], row['destination']) != (0, 0xd227d):
        raise ValueError('Selected predecessor destination differs')
    locked = json.loads((HERE.parent / 's354/native-table.json').read_text())
    expected = dict(binary_sha256=locked['binary_sha256'], binary_size=locked['binary_size'],
                    module_uuid=locked['module_uuid'], image_base=locked['image_base'],
                    index=0, start=0xd227d, end_exclusive=0xd2288, file_offset=0xd227d,
                    hex=PREFIX.hex(), sha256=sha(PREFIX), successor_bytes_read=0,
                    new_player_launches=0, new_memory_reads=0)
    if native != expected:
        raise ValueError('Fixed prefix provenance, bytes or bounds differ')
    # Exact encodings and sequential boundaries were independently checked by LLDB.
    displacement = int.from_bytes(PREFIX[-1:], 'little', signed=True)
    return dict(coordinates='Unslid module-relative addresses; not live PCs',
                selected_index=0, start=0xd227d, end_exclusive=0xd2288,
                instructions=[
                    dict(address=0xd227d, hex='89d8', operation='EAX = EBX; zero-extend RAX'),
                    dict(address=0xd227f, hex='83e007', operation='EAX &= 7; zero-extend RAX'),
                    dict(address=0xd2282, hex='4883f807', operation='compare RAX with 7'),
                    dict(address=0xd2286, hex='7508', operation='JNE rel8')],
                taken_target=0xd2288 + displacement, fallthrough=0xd2288,
                condition='(incoming RBX & 7) != 7',
                new_prefix_bytes=len(PREFIX), successor_bytes_read=0,
                successor_code_expanded=False, actual_index=None, actual_target=None,
                incoming_rbx=None, avm_type=None, live_values=None, alias_relations=None,
                exceptional_exits=None, actual_execution_proven=False,
                callee_return_proven=False,
                limit='Static low-three-bit predicate only; no value type, effect, ownership or live identity.')


def diagnose():
    verify_pins(HERE / 'input-sha256.json')
    verify_pins(HERE / 'ranking-basis-sha256.json')
    verify_pins(HERE / 'route-sha256.json')
    prior = replay()
    native = json.loads((HERE / 'native-prefix.json').read_text())
    return dict(slice='s363', base=BASE, scope='AFTER-s362 rank #1 only',
                production_admitted=False, native_parity_proven=False,
                m0_02_status='pending', product_obligations_closed=0,
                locked_s354_reproduced=True, prior_results_are_new_progress=False,
                historical=prior['historical'], retained=prior, audit=audit(native, prior),
                observations=prior['observations'],
                gates={name: dict(proved=False, code=code) for name, code in GATES.items()},
                new_builds=0, new_player_launches=0, new_memory_reads=0, new_captures=0,
                other_ranks_executed=[],
                blocker='Static prefix operands do not prove execution, effects, ownership or live module/worker/cursor/invocation binding.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    for flag in GATES:
        parser.add_argument('--require-' + flag, action='store_true')
    args = parser.parse_args()
    try:
        report = diagnose()
    except (ValueError, KeyError, OSError, IndexError) as exc:
        parser.exit(1, 'S363_EVIDENCE_INVALID: ' + str(exc) + '\n')
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    failures = [code for flag, code in GATES.items() if getattr(args, 'require_' + flag.replace('-', '_'))]
    if failures:
        print('; '.join(failures) + ': ' + report['blocker'])
        return 1
    print('S363_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
