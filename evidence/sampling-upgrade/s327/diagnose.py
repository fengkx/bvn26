"""Audit one Chad callee entry block; no live execution or AVM ownership claim."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = '3b37d8a62bd1dbe5abe5760c4765fe77126881ce'
START, END = 0xd2200, 0xd2244
BYTE_SHA = '2e7f1e73a295f61b090aeb5a41a9f1e1c897d184f5ffc37523fd9eaf18e08961'
LOG_SHA = 'c30766119a38e747318fc1526f5366b8445e6b147b47fc9e2fde38553690885b'
GATES = {name: 'S327_' + name.upper().replace('-', '_') + '_UNPROVED'
         for name in ('external-effects', 'value-ownership', 'live-binding',
                      'cursor-convention', 'retained-invocation')}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load_prior():
    spec = importlib.util.spec_from_file_location('s327_locked_s320', HERE.parent / 's320/diagnose.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_pins(path):
    for name, digest in json.loads(path.read_text()).items():
        if sha((ROOT / name).read_bytes()) != digest:
            raise ValueError('Locked input changed: ' + name)


def replay():
    prior = load_prior().diagnose()
    if prior != json.loads((HERE.parent / 's320/diagnosis.json').read_text()):
        raise ValueError('Locked s320 replay changed')
    return prior


def audit(native, log, prior):
    locked = json.loads((HERE.parent / 's303/native-audit.json').read_text())
    for key, expected in (('binary_sha256', locked['binary_sha256']),
                          ('binary_size', locked['binary_size']),
                          ('module_uuid', locked['module']['uuid']),
                          ('image_base', locked['image_base'])):
        if native[key] != expected:
            raise ValueError('Native provenance differs: ' + key)
    raw = bytes.fromhex(native['hex'])
    if (native['start'], native['end_exclusive'], native['file_offset'], len(raw),
        native['sha256'], sha(raw), native['disassembly_sha256'], sha(log)) != (
            START, END, START, END - START, BYTE_SHA, BYTE_SHA, LOG_SHA, LOG_SHA):
        raise ValueError('Fixed block bytes/bounds/disassembly changed')
    nodes, cursor = [], START
    for line in log.decode().splitlines():
        match = re.match(r'^([0-9a-f]+):\s+((?:[0-9a-f]{2} )+)\s*\t(\w+)\s*(.*)$', line)
        if not match:
            continue
        address = int(match[1], 16) - native['image_base']
        encoded = bytes.fromhex(match[2])
        if address != cursor or raw[address-START:address-START+len(encoded)] != encoded:
            raise ValueError('Incomplete instruction coverage')
        cursor += len(encoded)
        nodes.append(dict(address=address, hex=encoded.hex(), mnemonic=match[3], operands=match[4]))
    if cursor != END or len(nodes) != 21:
        raise ValueError('Block instruction boundary changed')
    transfers = [n for n in nodes if n['mnemonic'].startswith('j') or n['mnemonic'] in ('call', 'ret')]
    if transfers != [nodes[-1]] or nodes[-1]['hex'] != '7510' or nodes[-1]['mnemonic'] != 'jne':
        raise ValueError('First control-transfer boundary changed')
    target = END + int.from_bytes(bytes.fromhex(nodes[-1]['hex'])[1:], 'little', signed=True)
    if target != 0xd2254 or int(nodes[-1]['operands'].split()[0], 16) != native['image_base'] + target:
        raise ValueError('Branch displacement changed')
    caller = {n['address']: n for n in prior['path_audit']['instructions']}
    expected = {0x12696b: ('lea', 'rdi, [rbp - 0x550]'),
                0x126972: ('lea', 'rdx, [rbp - 0x60]'),
                0x126976: ('mov', 'rsi, r13')}
    for address, pair in expected.items():
        if (caller[address]['mnemonic'], caller[address]['operands']) != pair:
            raise ValueError('Caller argument binding changed')
    if caller[0x126979]['target'] != START or caller[0x126979]['hex'] != 'e882b8faff':
        raise ValueError('Caller target changed')
    # These relations name raw machine locations, never AVM types or identities.
    relations = [
        dict(argument='rdi', caller='&dispatcher_rbp-0x550', saved_at=0xd221a,
             saved_register='r12', access_at=0xd222c, access='write qword raw 2'),
        dict(argument='rsi', caller='dispatcher_r13', saved_at=0xd2217,
             saved_register='r14', access_at=None, access='no direct dereference of r14 in this block'),
        dict(argument='rdx', caller='&dispatcher_rbp-0x60', saved_at=0xd2214,
             saved_register='r15', access_at=0xd2234, access='read qword into rbx')]
    return dict(coordinates='Unslid module-relative machine addresses, not SWF offsets or live PCs',
                bytes_audited=len(raw), instructions=nodes, caller_site=0x126979,
                incoming_argument_relations=relations,
                first_frontier=dict(site=nodes[-1]['address'], kind='conditional_branch',
                                    target=target, fallthrough=END, successors_expanded=False),
                rip_relative_pointer_cell=0x14b1c58,
                rip_relative_dereference_sites=[0xd221d, 0xd2224],
                local_stack_save=0xd2228,
                predicate='(low 32 bits of the loaded qword & 7) != 7',
                explicit_calls=0, machine_returns=0,
                live_values=None, alias_relations=None, exceptional_exits=None,
                actual_execution_proven=False, callee_return_proven=False,
                limit='Only the first block is decoded. Straight-line order is conditional on reaching each instruction without fault. Pointer-cell contents, aliases, types, scope, ownership, native lifetime and both branch continuations are unproved. Helper rbp is not dispatcher rbp.')


def diagnose():
    verify_pins(HERE / 'input-sha256.json')
    verify_pins(HERE / 'ranking-basis-sha256.json')
    prior = replay()
    return dict(slice='s327', base=BASE, scope='AFTER-s326 rank #1 only',
                production_admitted=False, native_parity_proven=False,
                m0_02_status='pending', product_obligations_closed=0,
                locked_s320_reproduced=True, prior_results_are_new_progress=False,
                historical=prior['historical'],
                audit=audit(json.loads((HERE / 'native-audit.json').read_text()),
                            (HERE / 'callee-entry.txt').read_bytes(), prior),
                observations={key: prior[key] for key in (
                    'activation_identity', 'defining_scope', 'register4_location',
                    'stack_carrier_descriptor_alias_relation', 'allocation_generation',
                    'helper_preservation', 'live_module_binding', 'loaded_worker_binding',
                    'measured_cursor', 'retained_invocation')},
                gates={name: dict(proved=False, code=code) for name, code in GATES.items()},
                new_builds=0, new_player_launches=0, new_memory_reads=0, new_captures=0,
                other_ranks_executed=[],
                blocker='The first callee block has a raw write/read before a conditional branch; both successors, pointer contents, alias/ownership effects and exceptional paths remain unproved. No live module/worker, cursor or retained invocation binding exists.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    for flag in GATES:
        parser.add_argument('--require-' + flag, action='store_true')
    args = parser.parse_args()
    try:
        report = diagnose()
    except (ValueError, KeyError, OSError, IndexError) as exc:
        parser.exit(1, 'S327_EVIDENCE_INVALID: ' + str(exc) + '\n')
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    failures = [code for flag, code in GATES.items() if getattr(args, 'require_' + flag.replace('-', '_'))]
    if failures:
        print('; '.join(failures) + ': ' + report['blocker'])
        return 1
    print('S327_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
