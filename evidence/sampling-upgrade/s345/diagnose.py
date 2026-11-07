"""Audit only the two immediate s336 successor windows; no live proof."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = '92454e214aacca893b52032659bd8d5bd903f131'
WINDOWS = {
    0xd226d: (0xd227d,
               'bf5d698f5f059f4f5bcc2ba2b1643b2efc50f6fcce8c007f7a9d2f9ecfcf4869',
               '42e7366b9523e03b156896974cdd4858bd1d566377102d1f6ad33c24c6ba888f', 4),
    0xd2482: (0xd248c,
               '528a228b33cde74f4f58eeb7499b0f669a00ebfa00f1479974a9e5fef4bafd24',
               '1070e94107ec8bf7321266da3727553f94d07b09739be0891f9ed34917985d97', 4),
}
GATES = {name: 'S345_' + name.upper().replace('-', '_') + '_UNPROVED'
         for name in ('external-effects', 'value-ownership', 'live-binding',
                      'cursor-convention', 'retained-invocation')}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load_prior():
    spec = importlib.util.spec_from_file_location('s345_locked_s336', HERE.parent / 's336/diagnose.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_pins(path):
    for name, digest in json.loads(path.read_text()).items():
        if sha((ROOT / name).read_bytes()) != digest:
            raise ValueError('Locked input changed: ' + name)


def replay():
    prior = load_prior().diagnose()
    if prior != json.loads((HERE.parent / 's336/diagnosis.json').read_text()):
        raise ValueError('Locked s336 replay changed')
    return prior


def audit(native, logs, prior):
    locked = json.loads((HERE.parent / 's336/native-audit.json').read_text())
    for key in ('binary_sha256', 'binary_size', 'module_uuid', 'image_base'):
        if native[key] != locked[key]:
            raise ValueError('Native provenance differs: ' + key)
    retained = json.loads((HERE.parent / 's336/diagnosis.json').read_text())
    if prior['audit'] != retained['audit']:
        raise ValueError('Retained frontier or argument relation changed')
    frontier = prior['audit']['next_frontier']
    if (frontier['fallthrough'], frontier['target']) != tuple(WINDOWS):
        raise ValueError('Successor starts differ')
    if [w['start'] for w in native['windows']] != list(WINDOWS):
        raise ValueError('Missing, duplicate or extra successor window')
    decoded = []
    for window in native['windows']:
        start = window['start']
        end, byte_sha, log_sha, count = WINDOWS[start]
        raw = bytes.fromhex(window['hex'])
        log = logs[start]
        if (window['end_exclusive'], window['file_offset'], len(raw), window['sha256'],
            sha(raw), window['disassembly_sha256'], sha(log), window['exit_code']) != (
                end, start, end-start, byte_sha, byte_sha, log_sha, log_sha, 0):
            raise ValueError('Fixed successor bytes/bounds/disassembly changed')
        nodes, cursor = [], start
        for line in log.decode().splitlines():
            match = re.match(r'^([0-9a-f]+):\s+((?:[0-9a-f]{2} )+)\s*\t(\w+)\s*(.*)$', line)
            if not match:
                continue
            address = int(match[1], 16) - native['image_base']
            encoded = bytes.fromhex(match[2])
            if address != cursor or raw[address-start:address-start+len(encoded)] != encoded:
                raise ValueError('Incomplete instruction coverage')
            cursor += len(encoded)
            nodes.append(dict(address=address, hex=encoded.hex(), mnemonic=match[3], operands=match[4]))
        if cursor != end or len(nodes) != count:
            raise ValueError('Instruction boundary changed')
        transfers = [n for n in nodes if n['mnemonic'].startswith('j') or n['mnemonic'] in ('call', 'ret')]
        expected = ('jmp', 'ffe2') if start == 0xd226d else ('jne', '750d')
        if transfers != [nodes[-1]] or (nodes[-1]['mnemonic'], nodes[-1]['hex']) != expected:
            raise ValueError('First transfer boundary changed')
        if start == 0xd226d:
            table = nodes[0]['address'] + 7 + int.from_bytes(bytes.fromhex(nodes[0]['hex'])[3:], 'little', signed=True)
            if table != 0xd2540 or nodes[-1]['operands'] != 'rdx':
                raise ValueError('RIP-relative base or indirect register changed')
        else:
            target = end + int.from_bytes(bytes.fromhex(nodes[-1]['hex'])[1:], 'little', signed=True)
            if target != 0xd2499 or int(nodes[-1]['operands'].split()[0], 16) != native['image_base'] + target:
                raise ValueError('Conditional displacement changed')
        decoded.append(dict(start=start, end_exclusive=end, instructions=nodes))
    return dict(
        coordinates='Unslid module-relative machine addresses, not SWF offsets or live PCs',
        windows=decoded, unique_bytes_audited=26, unique_instructions=8, overlap_bytes=0,
        incoming_argument_relations=prior['audit']['incoming_argument_relations'],
        incoming_register_relation='s336 sets ecx=2, edx=eax before unsigned compare eax with 18; r12/r14/r15 retain saved arguments; rbx retains loaded qword.',
        routes=[
            dict(entry=0xd226d, condition='s336 unsigned eax <= 18',
                 operations='rax = module_base + 0xd2540; rdx = sign_extend_32(dword[rax + 4*rdx]); rdx += rax; jump rdx',
                 read_site=0xd2274, read_width_bytes=4, read_value=None,
                 index_bound=[0, 18], table_base=0xd2540, table_contents=None,
                 limit='EDX write zero-extends index. This is an address computation and indirect transfer; no table bytes, destinations or AVM types are derived.'),
            dict(entry=0xd2482, condition='s336 unsigned eax > 18',
                 operations='eax = ecx; eax &= 7; compare eax with 7; jump if unequal',
                 incoming_ecx=2, local_comparison_equal=False,
                 static_direct_route_target=0xd2499, actual_target_observed=None,
                 limit='Taken follows only for this direct predecessor with ecx=2 and reaching the instructions. Other incoming paths are not analyzed.')],
        next_frontiers=[dict(site=0xd227b, kind='indirect_jump', target=None, target_expression='table base + signed dword indexed by incoming edx', successors_expanded=False),
                        dict(site=0xd248a, kind='not_equal', target=0xd2499, fallthrough=0xd248c, successors_expanded=False)],
        explicit_calls=0, machine_returns=0, direct_memory_writes=0,
        live_values=None, alias_relations=None, exceptional_exits=None,
        actual_execution_proven=False, callee_return_proven=False,
        limit='Conditional on reaching instructions without fault. No table, transfer target, AVM tag names, pointer contents, external effects, ownership or live identity are proved.')


def diagnose():
    verify_pins(HERE / 'input-sha256.json')
    verify_pins(HERE / 'ranking-basis-sha256.json')
    prior = replay()
    native = json.loads((HERE / 'native-audit.json').read_text())
    logs = {w['start']: (HERE / w['log']).read_bytes() for w in native['windows']}
    return dict(slice='s345', base=BASE, scope='AFTER-s344 rank #1 only',
                production_admitted=False, native_parity_proven=False,
                m0_02_status='pending', product_obligations_closed=0,
                locked_s336_reproduced=True, prior_results_are_new_progress=False,
                historical=prior['historical'], audit=audit(native, logs, prior),
                observations=prior['observations'],
                gates={name: dict(proved=False, code=code) for name, code in GATES.items()},
                new_builds=0, new_player_launches=0, new_memory_reads=0, new_captures=0,
                other_ranks_executed=[],
                blocker='One successor stops at a signed-offset indirect jump; the other at a conditional branch. Table contents, destinations, read values, faults, external effects and ownership remain unproved. No live module/worker, cursor or retained invocation binding exists.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    for flag in GATES:
        parser.add_argument('--require-' + flag, action='store_true')
    args = parser.parse_args()
    try:
        report = diagnose()
    except (ValueError, KeyError, OSError, IndexError) as exc:
        parser.exit(1, 'S345_EVIDENCE_INVALID: ' + str(exc) + '\n')
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    failures = [code for flag, code in GATES.items() if getattr(args, 'require_' + flag.replace('-', '_'))]
    if failures:
        print('; '.join(failures) + ': ' + report['blocker'])
        return 1
    print('S345_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
