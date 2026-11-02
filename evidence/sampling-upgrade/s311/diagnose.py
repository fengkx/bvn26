"""Bound archived Chad native value/owner candidates without live admission."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = 'f246bfccdae6e3ea62ec2b701d4d349a01905c7d'
GATES = {name: 'S311_' + name.upper().replace('-', '_') + '_UNPROVED'
         for name in ('activation-layout', 'value-ownership', 'live-binding',
                      'cursor-convention', 'retained-invocation')}


def load_prior():
    # The locked predecessor uses its sibling audit_native module.
    sys.path.insert(0, str(HERE.parent / 's303'))
    try:
        spec = importlib.util.spec_from_file_location('s311_locked_s303', HERE.parent / 's303/diagnose.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


def bound_layout(native):
    """Validate exact local corridors; do not assign AS types to raw values."""
    load_prior().derive(native)
    regions = native['regions']
    witnesses = []

    def expect(address, encoded, relation):
        raw = bytes.fromhex(encoded)
        matches = [r for r in regions.values() if r['module_relative'] <= address
                   and address + len(raw) <= r['module_relative'] + r['size']]
        if len(matches) != 1:
            raise ValueError('uncovered layout witness')
        region = matches[0]
        offset = address - region['module_relative']
        if bytes.fromhex(region['hex'])[offset:offset + len(raw)] != raw:
            raise ValueError('layout bytes changed at ' + hex(address))
        witnesses.append({'module_relative': address, 'hex': encoded, 'relation': relation})

    expect(0x12479b, '488b8588faffff488b40084885c041bc0000000074044c8b6008',
           'r12 = 0 if [frame-0x578]->+8 is null; otherwise r12 = that pointer->+8')
    expect(0x124960, '488b8598faffff80786a004d89e174044c8b48284d85c9bb000000000f84ee000000',
           'r9 starts as r12; nonzero byte at [frame-0x568]->+0x6a selects qword +0x28 instead; null r9 bypasses value path')
    expect(0x124982, '498b4148498b99b800000089c183e10783f9074889c275104889c14883e1f8488b511889d183e10783e21f83f9020f45d183fa0a0f84b4000000',
           'read r9+0x48 and +0xb8; low3==7 selects [(value & ~7)+0x18]; low3==2 selects low5, otherwise low3; compare with 10')
    expect(0x1249bc, '8b8d78faffff0fb6c981f9960000000f849f00000083f91c0f849600000083f94e0f848d000000',
           'low byte at frame-0x588 is compared with 0x96, 0x1c, 0x4e before second value test')
    expect(0x1249e3, '89c183e1074883f90775084883e0f8488b40184883f80a7474',
           'independently unwrap original value when low3==7; compare full qword with 10')
    expect(0x1249fc, '4c898578faffff4489bd68faffff4d8d79484c898de8f9ffff4c89f8482500f0ffff4c8b700831d24c89f74c89fee8b16e860048c745a80a0000004c89f74889c64c89fa488d4da8e837ab000048c745a800000000448bbd68faffff4c8b8578faffff4c8b8de8f9ffff',
           'save r8/r15d/r9; derive page-aligned address from r9+0x48, read +8; two external calls use field address; raw temporary 10 then 0; restore registers')
    expect(0x124c2b, '4c8bada8faffff418b852005000085c00f847818000089c1ffc941898d20050000498b9528050000488b34ca488975a048c704ca020000004c8bbd90faffff0f845818000089c183c1fe41898d20050000498b9528050000488b34ca4889759848c704ca020000000f843718000083c0fd41898520050000498b8d28050000488b14c1488995b8faffff48c704c102000000e919180000',
           'full retained CallMethod candidate: guard count, decrement, copy three eight-byte slots to frame temporaries and replace each with raw 2; external exits remain uncovered')

    def target(address, size):
        region = next(r for r in regions.values() if r['module_relative'] <= address
                      and address + size <= r['module_relative'] + r['size'])
        offset = address - region['module_relative']
        raw = bytes.fromhex(region['hex'])[offset:offset + size]
        return address + size + struct.unpack('<i', raw[-4:])[0]

    exits = [{'site': site, 'target': target(site, size), 'condition': condition,
              'target_body_covered': False}
             for site, size, condition in (
                 (0x124c3b, 6, 'initial count == 0'),
                 (0x124c6a, 6, 'count - 1 == 0; flags survive intervening MOVs'),
                 (0x124c93, 6, 'count - 2 == 0; flags survive intervening MOVs'),
                 (0x124cbd, 5, 'after third slot copy'),
                 (0x124a2a, 5, 'first external call on selected value path'),
                 (0x124a44, 5, 'second external call on selected value path'))]
    return {
        'coordinate_kind': 'Unslid module-relative machine code, not SWF offsets or live PCs',
        'witnesses': witnesses,
        'slot_transfers': [
            {'guard': 'initial count >= ' + str(n), 'index': 'initial count - ' + str(n),
             'width_bytes': 8, 'destination_frame_offset': dest, 'cleared_raw_value': 2}
            for n, dest in ((1, -0x60), (2, -0x68), (3, -0x548))],
        'external_edges': exits,
        'ownership_boundaries': [
            {'role': 'candidate operand stack', 'origin': '[frame-0x558]',
             'fields': ['count +0x520', 'storage +0x528'], 'activation_owner': None},
            {'role': 'selected value carrier',
             'origin': 'conditional r12 chain from [frame-0x578] or [frame-0x568]->+0x28',
             'fields': ['value +0x48', 'additional qword +0xb8'], 'activation_owner': None},
            {'role': 'loaded byte descriptor', 'origin': '[frame-0x160]',
             'fields': ['data +0', 'signed extent +8; -1 sentinel'], 'activation_owner': None}],
        'raw_constants': [0, 2, 7, 10, 31],
        'avm_type_names': None, 'defining_scope': None, 'register4_location': None,
        'allocation_generation': None, 'activation_identity': None,
        'stack_carrier_alias_relation': None, 'helper_preservation': None,
        'limit': 'Local copying/clearing and bit tests do not identify AS types, defining scope, register4, allocation ownership or activation lifetime. The page-derived helper arguments do not prove GC/barrier semantics. No claim covers external target bodies.'}


def diagnose():
    for path, digest in json.loads((HERE / 'input-sha256.json').read_text()).items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != digest:
            raise ValueError('locked input changed: ' + path)
    prior = load_prior().diagnose()
    if prior != json.loads((HERE.parent / 's303/diagnosis.json').read_text()):
        raise ValueError('locked s303 diagnosis changed')
    native = json.loads((HERE.parent / 's303/native-audit.json').read_text())
    return {
        'base': BASE, 'scope': 'AFTER-s308 rank #3 only',
        'production_admitted': False, 'native_parity_proven': False,
        'product_obligations_closed': 0, 'm0_02_status': 'pending',
        'exact_continuation_proved': False, 'locked_s303_reproduced': True,
        'historical': prior['historical'], 'retained_worker': prior['retained_worker'],
        'native_candidate': prior['native_candidate'], 'layout_audit': bound_layout(native),
        'observations': prior['observations'],
        'live_module_binding': None, 'loaded_worker_binding': None,
        'measured_cursor': None, 'retained_invocation': None,
        'gates': {name: {'proved': False, 'code': code} for name, code in GATES.items()},
        'new_builds': 0, 'new_player_launches': 0, 'new_captures': 0,
        'new_memory_reads': 0, 'other_ranks_executed': [],
        'exclusions': ['CPU-entry-as-AVM proof', 'pointer-only binding',
                       'silence/removal-as-return', 'root-worker equivalence', 'broad interpreter',
                       's254-s310 edits', 'game/scripts/runtime/contracts/shared sampler/threshold/validator changes'],
        'blocker': 'Candidate value carrier is not joined to the operand-stack owner or defining scope/register4/activation identity. External helper and exit bodies, allocation lifetime and value semantics remain unqualified. Live module/worker binding, cursor measurement and one retained authored invocation are blocked before capture.',
        'next_observation': 'Resolve provenance and lifetime of the three distinct candidate origins and external helper/exit effects without naming raw tags by analogy. Only after activation/value ownership qualification, verify live module UUID/slide/code bytes, finite loaded worker bytes, measured cursor, and one retained invocation with scope/register4. Keep removed and root-defined controls separate.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    for flag in GATES:
        parser.add_argument('--require-' + flag, action='store_true')
    args = parser.parse_args()
    report = diagnose()
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    failures = [code for flag, code in GATES.items()
                if getattr(args, 'require_' + flag.replace('-', '_'))]
    if failures:
        print('; '.join(failures) + ': ' + report['blocker'])
        return 1
    print('S311_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
