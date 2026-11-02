"""Audit a byte-derived Chad dispatch candidate; fail closed before live proof."""
import argparse
import importlib.util
import json
from pathlib import Path
import struct

from audit_native import file_offset, macho, sha

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
GATES = {name: 'S303_' + name.upper().replace('-', '_') + '_UNPROVED' for name in (
    'native-resolver', 'loaded-buffer', 'cursor-convention', 'retained-activation',
    'instruction-boundaries')}


def locked_s295():
    spec = importlib.util.spec_from_file_location('s295_locked', HERE.parent / 's295/diagnose.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.diagnose()
    if result != json.loads((HERE.parent / 's295/diagnosis.json').read_text()):
        raise ValueError('locked s295 diagnosis changed')
    return result


def derive(native):
    """Decode only this pinned machine-code corridor, not an AVM interpreter."""
    header = bytes.fromhex(native['module']['header_hex'])
    module = macho(header)
    if module != native['module']:
        raise ValueError('module metadata differs from header')
    base = next(s['vmaddr'] for s in module['segments'] if s['name'] == '__TEXT')
    if base != native['image_base']:
        raise ValueError('image base differs')
    regions = native['regions']
    for region in regions.values():
        raw = bytes.fromhex(region['hex'])
        if len(raw) != region['size'] or sha(raw) != region['sha256']:
            raise ValueError('region bytes differ')
        if file_offset(module, base + region['module_relative'], len(raw)) != region['file_offset']:
            raise ValueError('region mapping differs')

    def read(address, size):
        matches = [r for r in regions.values() if r['module_relative'] <= address
                   and address + size <= r['module_relative'] + r['size']]
        if len(matches) != 1:
            raise ValueError('uncovered native bytes')
        r = matches[0]
        offset = address - r['module_relative']
        return bytes.fromhex(r['hex'])[offset:offset + size]

    def expect(address, hex_bytes):
        if read(address, len(bytes.fromhex(hex_bytes))) != bytes.fromhex(hex_bytes):
            raise ValueError('native derivation bytes changed at ' + hex(address))

    # Each candidate field is tied to a concrete load/store, not a symbol guess.
    expect(0x124726, '486385a8feffff')  # signed cursor load
    expect(0x12474d, '488b95a0feffff')  # candidate buffer descriptor
    expect(0x12475f, '488b0a')
    expect(0x124774, '8b520883faff740839d00f8d186f0000')
    expect(0x124784, '8d50018995a8feffff440fb63c01')
    expect(0x124830, '4584ff781b4531ed448b85a8feffffe984000000')
    expect(0x12488b, '488b084863d2448d4202448985a8feffff0fb63411440fb66c110141c1e5084109f5')
    expect(0x1248c8, '4501e8')
    expect(0x124a77, '4489f883c0fc3d9b0000000f8765feffff488d0db5840000486304814801c8ffe0')
    expect(0x125cab, '488b8da8faffff8b812005000085c00f842decffffffc8898120050000488b892805000048c704c102000000e911ecffff')
    expect(0x124c2b, '4c8bada8faffff418b8520050000')
    expect(0x125294, '488bbda8faffff4c89ce4c89c3e8aac1ffff4989d8e93ff6ffff')
    displacement = struct.unpack('<i', read(0x124a8b, 4))[0]
    table = 0x124a8f + displacement
    if table != regions['dispatch_table']['module_relative']:
        raise ValueError('dispatch table target differs')
    targets = []
    for opcode, label, region_name in [(0x52, 'CallMethod', 'callmethod_candidate'),
                                      (0x17, 'Pop', 'pop_candidate'),
                                      (0x4f, 'SetMember', 'setmember_candidate')]:
        entry = table + 4 * (opcode - 4)
        raw = read(entry, 4)
        target = table + struct.unpack('<i', raw)[0]
        if target != regions[region_name]['module_relative']:
            raise ValueError('dispatch target differs')
        targets.append(dict(opcode=opcode, authored_opcode_name=label, table_entry_relative=entry,
                            entry_hex=raw.hex(), target_relative=target,
                            status='static candidate, not executed instruction observation'))
    return dict(module_uuid=module['uuid'], image_base=base,
        coordinate_kind='Unslid module-relative machine-code offsets; NOT SWF offsets or live PCs',
        fetch_relative=0x12478d, dispatch_relative=0x124a96,
        dispatch_table_relative=table, index_expression='unsigned(opcode - 4) <= 0x9b',
        targets=targets,
        candidate_layout=dict(descriptor='qword [rbp-0x160]', data='qword [descriptor+0]',
            extent='signed dword [descriptor+8]; -1 bypasses finite extent check',
            cursor='signed dword [rbp-0x158]', opcode='r15d',
            stack_owner='qword [rbp-0x558]', stack_count='dword [owner+0x520]',
            stack_storage='qword [owner+0x528]; eight-byte slots',
            defining_scope=None, register4_location=None, activation_identity=None),
        static_cursor_relation='Before fetch, slot is incremented from c to c+1; fetch uses old c. '
            'For short opcodes, r8d receives c+1. This is a local static path relation, '
            'not a measured convention for the retained invocation or all native paths.',
        long_action_relation='High-bit path reads a little-endian 16-bit length, advances slot '
            'by two and adds payload length to r8d. Slot and r8d need not denote the same cursor.',
        semantic_limit='Opcode range/length format and Pop-like stack mutation support an AVM1 '
            'dispatch candidate. No complete activation resolver, tagged-value decoder, helper '
            'preservation proof, loaded buffer binding or native execution is established.')


def diagnose():
    for path, digest in json.loads((HERE / 'input-sha256.json').read_text()).items():
        if sha((ROOT / path).read_bytes()) != digest:
            raise ValueError('locked input changed: ' + path)
    prior = locked_s295()
    native = json.loads((HERE / 'native-audit.json').read_text())
    receipt = json.loads((HERE.parent / 's266/native-receipt.json').read_text())
    if native['binary_sha256'] != receipt['files'][native['binary']]:
        raise ValueError('native binary receipt mismatch')
    for check in native['checks']:
        if check['exit_code'] != 0 or sha((HERE / check['log']).read_bytes()) != check['sha256']:
            raise ValueError('native disassembly custody mismatch')
    return dict(base='27f70be588e72bcc0e260ce1d827559dc322b002', scope='AFTER-s299 rank #4 only',
        production_admitted=False, native_parity_proven=False, product_obligations_closed=0,
        exact_continuation_proved=False, locked_s295_reproduced=True,
        historical=prior['historical'], retained_worker=prior['retained_worker'],
        native_candidate=derive(native), observations=prior['observations'],
        gates={name: dict(proved=False, code=code) for name, code in GATES.items()},
        new_builds=0, new_player_launches=0, new_captures=0, new_name_queries=0,
        exclusions=prior['exclusions'],
        blocker='Static dispatch candidate has no defining-scope/register4/activation identity resolver. '
            'No loaded worker bytes/extent, measured cursor or retained invocation join exists. '
            'Three instruction observations remain blocked.',
        next_observation='Derive and independently qualify the candidate activation/scope/value layout; '
            'relocate using a live module UUID/slide and verify code bytes, bind loaded worker bytes '
            'and finite extent, measure cursor at fetch and dispatch, identify one retained authored '
            'invocation with defining scope, stack and register4 witness before three boundaries. '
            'Keep removed and root-defined controls separate; no silence/removal-as-return.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    for gate in GATES:
        parser.add_argument('--require-' + gate, action='store_true')
    args = parser.parse_args()
    report = diagnose()
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    failed = [code for gate, code in GATES.items() if getattr(args, 'require_' + gate.replace('-', '_'))]
    if failed:
        parser.exit(1, '; '.join(failed) + ': ' + report['blocker'] + '\n')
    print('S303_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')


if __name__ == '__main__':
    main()
