"""Audit only the two immediate s327 successor windows; no live proof."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = '6e0c9b4ad6c588274cc4299a4725396963c764de'
END = 0xd226d
WINDOWS = {
    0xd2244: ('42dd42ca267e820e19cb108495cff37dbbae2c434cb65732fbdedffba0c61068',
               'df3ba393f16ba197efa7c6f080fc8b26a153042615aad8d47cb583d11743f0c8', 12),
    0xd2254: ('a1c8bf9581cbd2b7cef111d04a2670fea1e5c9283aded963492e3d8883e3fdf3',
               '2ff1a55287570bf46ed8ea713eab1491f3a6a531fcb707fe2025e1e9818fe395', 7),
}
GATES = {name: 'S336_' + name.upper().replace('-', '_') + '_UNPROVED'
         for name in ('external-effects', 'value-ownership', 'live-binding',
                      'cursor-convention', 'retained-invocation')}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load_prior():
    spec = importlib.util.spec_from_file_location('s336_locked_s327', HERE.parent / 's327/diagnose.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_pins(path):
    for name, digest in json.loads(path.read_text()).items():
        if sha((ROOT / name).read_bytes()) != digest:
            raise ValueError('Locked input changed: ' + name)


def replay():
    prior = load_prior().diagnose()
    if prior != json.loads((HERE.parent / 's327/diagnosis.json').read_text()):
        raise ValueError('Locked s327 replay changed')
    return prior


def audit(native, logs, prior):
    locked = json.loads((HERE.parent / 's327/native-audit.json').read_text())
    for key in ('binary_sha256', 'binary_size', 'module_uuid', 'image_base'):
        if native[key] != locked[key]:
            raise ValueError('Native provenance differs: ' + key)
    retained = json.loads((HERE.parent / 's327/diagnosis.json').read_text())
    if prior['audit'] != retained['audit']:
        raise ValueError('Retained frontier or argument relation changed')
    frontier = prior['audit']['first_frontier']
    if (frontier['fallthrough'], frontier['target']) != tuple(WINDOWS):
        raise ValueError('Successor starts differ')
    if [w['start'] for w in native['windows']] != list(WINDOWS):
        raise ValueError('Missing, duplicate or extra successor window')
    decoded = []
    for window in native['windows']:
        start = window['start']
        byte_sha, log_sha, count = WINDOWS[start]
        raw = bytes.fromhex(window['hex'])
        log = logs[start]
        if (window['end_exclusive'], window['file_offset'], len(raw), window['sha256'],
            sha(raw), window['disassembly_sha256'], sha(log), window['exit_code']) != (
                END, start, END-start, byte_sha, byte_sha, log_sha, log_sha, 0):
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
        if cursor != END or len(nodes) != count:
            raise ValueError('Instruction boundary changed')
        transfers = [n for n in nodes if n['mnemonic'].startswith('j') or n['mnemonic'] in ('call', 'ret')]
        if transfers != [nodes[-1]] or nodes[-1]['hex'] != '0f8715020000' or nodes[-1]['mnemonic'] != 'ja':
            raise ValueError('First transfer boundary changed')
        target = END + int.from_bytes(bytes.fromhex(nodes[-1]['hex'])[2:], 'little', signed=True)
        if target != 0xd2482 or int(nodes[-1]['operands'].split()[0], 16) != native['image_base'] + target:
            raise ValueError('Branch displacement changed')
        decoded.append(dict(start=start, end_exclusive=END, instructions=nodes))
    if decoded[0]['instructions'][5:] != decoded[1]['instructions']:
        raise ValueError('Overlapping join differs')
    return dict(
        coordinates='Unslid module-relative machine addresses, not SWF offsets or live PCs',
        windows=decoded, unique_bytes_audited=41, unique_instructions=12,
        overlap_bytes=25, join=0xd2254,
        basic_blocks=[dict(start=0xd2244, end_exclusive=0xd2254, exit='fallthrough to known join'),
                      dict(start=0xd2254, end_exclusive=END, exit='conditional branch')],
        incoming_argument_relations=prior['audit']['incoming_argument_relations'],
        routes=[
            dict(entry=0xd2244, condition='s327 loaded qword low bits equal 7',
                 operations='rax = rbx & ~7; rax = qword[rax + 0x18]; ecx = low32(rax) & 7',
                 read_site=0xd224b, read_width_bytes=8, read_value=None,
                 limit='Masked value plus displacement is only a machine address expression; no AVM object, type, validity or ownership follows.'),
            dict(entry=0xd2254, condition='s327 loaded qword low bits differ from 7',
                 operations='Entry rax remains the loaded rbx; ecx remains low32(rbx) & 7',
                 read_site=None, read_width_bytes=None, read_value=None,
                 limit='No additional direct memory read on this local route; absence here does not prove harmlessness.')],
        shared_operations='eax &= 0x1f; if ecx != 2 then eax = ecx; ecx = 2; edx = eax; unsigned compare eax with 0x12',
        next_frontier=dict(site=0xd2267, kind='unsigned_above', target=0xd2482,
                           fallthrough=END, successors_expanded=False),
        explicit_calls=0, machine_returns=0, direct_memory_writes=0,
        live_values=None, alias_relations=None, exceptional_exits=None,
        actual_execution_proven=False, callee_return_proven=False,
        limit='Conditional on reaching each instruction without fault. No AVM tag names, pointer contents, external effects, ownership or live identity are proved. Both new frontier successors are excluded.')


def diagnose():
    verify_pins(HERE / 'input-sha256.json')
    verify_pins(HERE / 'ranking-basis-sha256.json')
    prior = replay()
    native = json.loads((HERE / 'native-audit.json').read_text())
    logs = {w['start']: (HERE / w['log']).read_bytes() for w in native['windows']}
    return dict(slice='s336', base=BASE, scope='AFTER-s335 rank #1 only',
                production_admitted=False, native_parity_proven=False,
                m0_02_status='pending', product_obligations_closed=0,
                locked_s327_reproduced=True, prior_results_are_new_progress=False,
                historical=prior['historical'], audit=audit(native, logs, prior),
                observations=prior['observations'],
                gates={name: dict(proved=False, code=code) for name, code in GATES.items()},
                new_builds=0, new_player_launches=0, new_memory_reads=0, new_captures=0,
                other_ranks_executed=[],
                blocker='Two immediate successor windows join before another branch. Its successors, indirect read value, faults, external effects and ownership remain unproved. No live module/worker, cursor or retained invocation binding exists.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    for flag in GATES:
        parser.add_argument('--require-' + flag, action='store_true')
    args = parser.parse_args()
    try:
        report = diagnose()
    except (ValueError, KeyError, OSError, IndexError) as exc:
        parser.exit(1, 'S336_EVIDENCE_INVALID: ' + str(exc) + '\n')
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    failures = [code for flag, code in GATES.items() if getattr(args, 'require_' + flag.replace('-', '_'))]
    if failures:
        print('; '.join(failures) + ': ' + report['blocker'])
        return 1
    print('S336_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
