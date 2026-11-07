"""Audit only nineteen bounded Chad table entries; no destination code or live proof."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = '60dcfbd11953cbb107028a964cfd0a7b739091dd'
TABLE_SHA = '15ea184626ca687d394780faa6eddd7d1252b20ec0a8dbbd7c593106a2f10c2e'
GATES = {name: 'S354_' + name.upper().replace('-', '_') + '_UNPROVED'
         for name in ('external-effects', 'value-ownership', 'live-binding',
                      'cursor-convention', 'retained-invocation')}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load_prior():
    spec = importlib.util.spec_from_file_location('s354_locked_s345', HERE.parent / 's345/diagnose.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_pins(path):
    for name, digest in json.loads(path.read_text()).items():
        if sha((ROOT / name).read_bytes()) != digest:
            raise ValueError('Locked input changed: ' + name)


def replay():
    prior = load_prior().diagnose()
    if prior != json.loads((HERE.parent / 's345/diagnosis.json').read_text()):
        raise ValueError('Locked s345 replay changed')
    return prior


def audit(native, prior):
    retained = json.loads((HERE.parent / 's345/diagnosis.json').read_text())
    if prior != retained:
        raise ValueError('Complete retained diagnosis differs')
    route = prior['audit']['routes'][0]
    if (route['table_base'], route['index_bound']) != (0xd2540, [0, 18]):
        raise ValueError('Predecessor table bounds differ')
    locked = json.loads((HERE.parent / 's345/native-audit.json').read_text())
    raw = bytes.fromhex(native['hex'])
    expected = dict(binary_sha256=locked['binary_sha256'], binary_size=locked['binary_size'],
                    module_uuid=locked['module_uuid'], image_base=locked['image_base'],
                    start=0xd2540, end_exclusive=0xd258c, file_offset=0xd2540,
                    hex=raw.hex(), sha256=TABLE_SHA, new_player_launches=0,
                    new_memory_reads=0, destination_bytes_read=0)
    if native != expected or len(raw) != 76 or sha(raw) != TABLE_SHA:
        raise ValueError('Fixed table provenance, bytes or bounds differ')
    rows, groups = [], {}
    for index in range(19):
        value = raw[index * 4:index * 4 + 4]
        displacement = int.from_bytes(value, 'little', signed=True)
        target = native['start'] + displacement
        rows.append(dict(index=index, entry=native['start'] + index * 4,
                         hex=value.hex(), signed_displacement=displacement,
                         destination=target, actual_execution=None))
        groups.setdefault(hex(target), []).append(index)
    return dict(coordinates='Unslid module-relative addresses, not SWF offsets or live PCs',
                rows=rows, destination_groups=groups, unique_destinations=len(groups),
                new_table_bytes=76, destination_bytes_read=0,
                rule='destination = 0xd2540 + sign_extend_32(table[index]); index 0..18',
                destination_code_expanded=False, actual_index=None, actual_target=None,
                live_values=None, alias_relations=None, exceptional_exits=None,
                actual_execution_proven=False, callee_return_proven=False,
                limit='Static destinations only; no target instructions, types, effects, ownership or live identities.')


def diagnose():
    verify_pins(HERE / 'input-sha256.json')
    verify_pins(HERE / 'ranking-basis-sha256.json')
    prior = replay()
    native = json.loads((HERE / 'native-table.json').read_text())
    return dict(slice='s354', base=BASE, scope='AFTER-s353 rank #1 only',
                production_admitted=False, native_parity_proven=False,
                m0_02_status='pending', product_obligations_closed=0,
                locked_s345_reproduced=True, prior_results_are_new_progress=False,
                historical=prior['historical'], retained=prior, audit=audit(native, prior),
                observations=prior['observations'],
                gates={name: dict(proved=False, code=code) for name, code in GATES.items()},
                new_builds=0, new_player_launches=0, new_memory_reads=0, new_captures=0,
                other_ranks_executed=[],
                blocker='Static table destinations do not prove destination behavior, external effects, ownership or live module/worker/cursor/invocation binding.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    for flag in GATES:
        parser.add_argument('--require-' + flag, action='store_true')
    args = parser.parse_args()
    try:
        report = diagnose()
    except (ValueError, KeyError, OSError, IndexError) as exc:
        parser.exit(1, 'S354_EVIDENCE_INVALID: ' + str(exc) + '\n')
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    failures = [code for flag, code in GATES.items() if getattr(args, 'require_' + flag.replace('-', '_'))]
    if failures:
        print('; '.join(failures) + ': ' + report['blocker'])
        return 1
    print('S354_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
