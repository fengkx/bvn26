"""Audit fixed Chad helper/exit frontiers without promoting static paths to live proof."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import struct

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = '3f64b5fdefbc47fec73c3005db145aa0127db50a'
GATES = {name: 'S320_' + name.upper().replace('-', '_') + '_UNPROVED'
         for name in ('external-effects', 'value-ownership', 'live-binding',
                      'cursor-convention', 'retained-invocation')}
# Fixed disassembly bounds were selected from the six locked s311 targets.
PINS = {
    'stack_join': (0x1264b9, 195, '630fadb6f4afba91f309102fe80942ab7bd24c5b58031afa3cc7447616bb4fa5', 'f2e8a86cd9c1e311cdce6a3a203a4556158430ea320418b61e8ec191e5fdefb3'),
    'stack_call_frontier': (0x12696b, 34, 'd69eb21ddaf59f0c1f6825f2066eef11addf599ed87fae811331592dcf91067e', 'c2071c17dd695fdf660efbdfec663ec812805ca2443f38ce515f5736c13eda16'),
    'carrier_lookup': (0x98b8e0, 428, 'ae141350f9603298e961aaec4e09aa9b815ad1d7541a9485c419f777b233094d', 'af21046b5895aaf14f098550aa97e24c7a16bbfebcc422f63ffce448d087c2f3'),
    'carrier_store': (0x12f580, 392, 'a5f5de502929afb3b10a82b6a2a69ca3c3d1dd440979f5d28bc53acb9b8dcd98', 'ea9247fd3e7b9888194f6f572b4e05453c448b2ab6766a712a99e5cff3b83722'),
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load_prior():
    spec = importlib.util.spec_from_file_location('s320_locked_s311', HERE.parent / 's311/diagnose.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def audit_paths(native):
    locked = json.loads((HERE.parent / 's303/native-audit.json').read_text())
    for key, expected in (('binary_sha256', locked['binary_sha256']),
                          ('binary_size', locked['binary_size']),
                          ('module_uuid', locked['module']['uuid']),
                          ('image_base', locked['image_base'])):
        if native[key] != expected:
            raise ValueError('native custody changed: ' + key)
    if set(native['regions']) != set(PINS):
        raise ValueError('region scope changed')
    nodes = {}
    for name, (start, size, digest, log_digest) in PINS.items():
        region = native['regions'][name]
        raw = bytes.fromhex(region['hex'])
        if (region['module_relative'], region['file_offset'], region['size'], len(raw),
            region['sha256'], sha(raw)) != (start, start, size, size, digest, digest):
            raise ValueError('fixed region bytes changed: ' + name)
        log = (HERE / (name + '.txt')).read_bytes()
        if sha(log) != log_digest or region['disassembly_sha256'] != log_digest:
            raise ValueError('disassembly changed: ' + name)
        cursor = start
        for line in log.decode().splitlines():
            match = re.match(r'^([0-9a-f]+):\s+((?:[0-9a-f]{2} )+)\s*\t(\w+)\s*(.*)$', line)
            if not match:
                continue
            address = int(match[1], 16) - native['image_base']
            encoded = bytes.fromhex(match[2])
            if address != cursor or raw[address-start:address-start+len(encoded)] != encoded:
                raise ValueError('disassembly byte coverage differs')
            cursor += len(encoded)
            mnemonic, operands = match[3], match[4]
            node = dict(address=address, hex=encoded.hex(), mnemonic=mnemonic,
                        operands=operands, region=name, successors=[])
            if mnemonic.startswith('j') or mnemonic == 'call':
                if encoded[0] in (0xe8, 0xe9) or encoded[:1] == b'\x0f':
                    displacement = struct.unpack('<i', encoded[-4:])[0]
                elif encoded[0] == 0xeb or 0x70 <= encoded[0] <= 0x7f:
                    displacement = struct.unpack('b', encoded[-1:])[0]
                else:
                    raise ValueError('unsupported control transfer')
                target = cursor + displacement
                if int(operands.split()[0], 16) != native['image_base'] + target:
                    raise ValueError('control operand disagrees with bytes')
                node['target'] = target
                if mnemonic == 'call':
                    node['opaque_call'] = True
                    node['conditional_return_successor'] = cursor
                else:
                    node['successors'].append(target)
                    if mnemonic != 'jmp':
                        node['successors'].append(cursor)
            elif mnemonic == 'ret':
                node['machine_return_only'] = True
            else:
                node['successors'].append(cursor)
            nodes[address] = node
        if cursor != start + size:
            raise ValueError('incomplete disassembly')
    # Every non-call successor must resolve; no silent truncation of branches.
    for node in nodes.values():
        if any(target not in nodes for target in node['successors']):
            raise ValueError('unbounded non-call successor')
    prior_edges = load_prior().bound_layout(locked)['external_edges']
    frontiers = []
    for edge in prior_edges:
        entry = edge['target']
        queue, paths, stops = [entry], {entry: [entry]}, []
        while queue:
            address = queue.pop(0)
            node = nodes[address]
            if node.get('opaque_call') or node.get('machine_return_only'):
                stops.append(dict(address=address, kind='opaque_call' if node.get('opaque_call') else 'machine_ret',
                                  target=node.get('target'), witness_path=paths[address]))
                continue
            for target in node['successors']:
                if target not in paths:
                    paths[target] = paths[address] + [target]
                    queue.append(target)
        frontiers.append(dict(s311_site=edge['site'], entry=entry,
                              visited=sorted(paths), first_boundaries=stops))
    return dict(coordinates='Unslid module-relative machine code; not SWF offsets or live PCs',
                bytes_audited=sum(p[1] for p in PINS.values()),
                instructions=[nodes[a] for a in sorted(nodes)], first_frontiers=frontiers,
                calls=[dict(site=a, target=n['target'], conditional_return_successor=n['conditional_return_successor'],
                            successor_covered=n['conditional_return_successor'] in nodes)
                       for a, n in sorted(nodes.items()) if n.get('opaque_call')],
                machine_returns=[a for a, n in sorted(nodes.items()) if n.get('machine_return_only')],
                backward_edges=[dict(site=a, target=t) for a, n in sorted(nodes.items())
                                for t in n['successors'] if t <= a],
                path_feasibility_proven=False, termination_proven=False,
                nested_callee_effects=None, exceptional_exits=None,
                limit='Calls stop first-frontier traversal. Code after calls is conditional on normal machine return, not proved execution. Structural branch paths may be infeasible; a loop has no proven iteration bound.')


def diagnose():
    for path, digest in json.loads((HERE / 'input-sha256.json').read_text()).items():
        if sha((ROOT / path).read_bytes()) != digest:
            raise ValueError('locked input changed: ' + path)
    prior = load_prior().diagnose()
    if prior != json.loads((HERE.parent / 's311/diagnosis.json').read_text()):
        raise ValueError('locked s311 diagnosis changed')
    paths = audit_paths(json.loads((HERE / 'native-audit.json').read_text()))
    relations = json.loads((HERE / 'relations.json').read_text())
    return dict(base=BASE, scope='AFTER-s317 rank #3 only', production_admitted=False,
                native_parity_proven=False, m0_02_status='pending', product_obligations_closed=0,
                locked_s311_reproduced=True, historical=prior['historical'],
                prior_results_are_new_progress=False, path_audit=paths, relations=relations,
                activation_identity=None, defining_scope=None, register4_location=None,
                stack_carrier_descriptor_alias_relation=None, allocation_generation=None,
                helper_preservation=None, live_module_binding=None, loaded_worker_binding=None,
                measured_cursor=None, retained_invocation=None, exact_continuation_proved=False,
                gates={name: dict(proved=False, code=code) for name, code in GATES.items()},
                new_builds=0, new_player_launches=0, new_captures=0, new_memory_reads=0,
                other_ranks_executed=[],
                blocker='Nested call effects, exceptional exits and ownership/lifetime joins remain unproved. Static helper RET is not an authored return. Live module/worker, cursor and retained invocation remain blocked before capture.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    for flag in GATES:
        parser.add_argument('--require-' + flag, action='store_true')
    args = parser.parse_args()
    report = diagnose()
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    failures = [code for flag, code in GATES.items() if getattr(args, 'require_' + flag.replace('-', '_'))]
    if failures:
        print('; '.join(failures) + ': ' + report['blocker'])
        return 1
    print('S320_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
