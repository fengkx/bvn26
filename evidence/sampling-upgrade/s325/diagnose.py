"""Audit s325 on-disk resolver prerequisites; never promote symbols to live identity."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import struct

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = '93c306d177cc8f2dbafb52be73c049df5f9c0cd3'
REQUIREMENTS = {
    'slot-reference': 'S325_SLOT_REFERENCE_UNPROVED',
    'content-clearing': 'S325_CONTENT_CLEARING_UNPROVED',
    'replacement': 'S325_REPLACEMENT_UNPROVED',
    'allocation-identity': 'S325_POOL_GENERATIONS_UNPROVED',
}


def audit_inventory(table, symbols, commands, facility):
    if table['binary_sha256'] != facility['binary_sha256']:
        raise ValueError('binary provenance mismatch')
    if table['live_module_binding'] is not None or table['object_layout'] is not None or facility['live_binding'] is not None:
        raise ValueError('on-disk inventory cannot assert live binding or layout')
    if facility['process_attaches'] != 0 or facility['player_launches'] != 0:
        raise ValueError('unexpected live operation')
    for check in facility['checks']:
        if check['exit_code'] != 0:
            raise ValueError('inventory command failed')
    t = table['symbol_table']
    entries = t['entries']
    count = int(re.search(r'^\s+nsyms (\d+)$', commands, re.M)[1])
    if len(entries) != t['count'] or count != len(entries):
        raise ValueError('symbol table count mismatch')
    for i, e in enumerate(entries):
        if e['index'] != i or e['file_offset'] != t['symbol_offset'] + i * 16:
            raise ValueError('symbol table order mismatch')
        _, kind, section, desc, value = struct.unpack('<IBBHQ', bytes.fromhex(e['entry_hex']))
        if (kind, section, desc, value) != (e['n_type'], e['n_sect'], e['n_desc'], e['n_value']):
            raise ValueError('symbol entry byte mismatch')
    debug = [e for e in entries if e['n_type'] & 0xe0]
    defined = [e for e in entries if not e['n_type'] & 0xe0 and e['n_type'] & 0x0e == 0x0e]
    undefined = [e for e in entries if not e['n_type'] & 0xe0 and e['n_type'] & 0x0e == 0]
    if len(debug) + len(defined) + len(undefined) != len(entries):
        raise ValueError('unclassified symbols')
    lines = symbols.splitlines()
    defined_lines = [line for line in lines if '(undefined)' not in line]
    if len(lines) != len(defined) + len(undefined):
        raise ValueError('nm/table visible count mismatch')
    if {line.split()[-1] for line in defined_lines} != {e['name'] for e in defined}:
        raise ValueError('nm/table defined names mismatch')
    for e in undefined:
        if not any(re.search(r' external ' + re.escape(e['name']) + r'(?: |$)', line) for line in lines if '(undefined)' in line):
            raise ValueError('nm/table import mismatch')
    return {'symbol_table_entries': len(entries), 'nm_visible_entries': len(lines),
            'defined_symbols': defined, 'undefined_symbol_count': len(undefined),
            'debug_entries_omitted_by_nm': debug,
            'dwarf_segment_present': bool(re.search(r'^\s+segname __DWARF$', commands, re.M)),
            'module_uuid': re.search(r'^\s+uuid (\S+)$', commands, re.M)[1],
            'independent_slot_layout': None, 'independent_reference_layout': None,
            'live_binding': None, 'pool_generation_coverage': None,
            'limitation': 'Complete on-disk symbol inventory, not complete machine-code analysis. Defined names and imported allocators establish no object layout, live referent or pool lifetime.'}


def diagnose():
    for path, expected in json.loads((HERE / 'input-sha256.json').read_text()).items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != expected:
            raise ValueError('locked input changed: ' + path)
    spec = importlib.util.spec_from_file_location('s316_locked', HERE.parent / 's316/diagnose.py')
    prior = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prior)
    replay = prior.diagnose()
    if replay != json.loads((HERE.parent / 's316/diagnosis.json').read_text()):
        raise ValueError('locked s316 diagnosis mismatch')
    read = lambda name: json.loads((HERE / name).read_text())
    audit = audit_inventory(read('native-symbol-table.json'), (HERE / 'native-symbols.txt').read_text(),
                            (HERE / 'native-load-commands.txt').read_text(), read('native-inventory.json'))
    return {'base': BASE, 'scope': 'AFTER-s317 rank #8 only', 'status': 'honest_unproved',
            'production_admitted': False, 'native_parity_proven': False,
            'm0_02_status': 'pending', 'product_obligations_closed': 0,
            'locked_s316_reproduced': True, 'locked_s316_diagnosis': replay,
            'fresh_on_disk_inventory_audit': audit,
            'native_observations': replay['native_observations'],
            'slot_reference_proved': False, 'content_clearing_proved': False,
            'replacement_proved': False, 'allocation_identity_proved': False,
            'actual_native_controls_executed': False, 'new_builds': 0,
            'new_captures': 0, 'new_player_launches': 0, 'new_process_attaches': 0,
            'other_ranks_executed': [], 'rank_9_status': 'planning',
            'requirement_failure_codes': REQUIREMENTS,
            'blocker': 'No independently derived native slot/reference layouts or live binding; actual clearing/replacement/free/reuse with uninterrupted pool generations remain unproved.',
            'next_discriminator': replay['next_discriminator']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    for name in REQUIREMENTS:
        parser.add_argument('--require-' + name, action='store_true')
    args = parser.parse_args()
    try:
        report = diagnose()
    except (ValueError, KeyError, OSError, TypeError, struct.error) as exc:
        parser.exit(1, 'S325_EVIDENCE_INVALID: ' + str(exc) + '\n')
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    failures = [code for name, code in REQUIREMENTS.items() if getattr(args, 'require_' + name.replace('-', '_'))]
    if failures:
        parser.exit(1, '\n'.join(failures) + ': ' + report['blocker'] + '\n')
    print('S325_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')


if __name__ == '__main__':
    main()
