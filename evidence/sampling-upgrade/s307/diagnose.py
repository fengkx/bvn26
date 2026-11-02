"""Bound archived reference routes and control ordering; never invent native generations."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import tarfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = '87b844c6'
MEMBER = 'patches/main/frame_1/DoAction.as'
REQUIREMENTS = {
    'slot-reference': 'S307_SLOT_REFERENCE_UNPROVED',
    'content-clearing': 'S307_CONTENT_CLEARING_UNPROVED',
    'replacement': 'S307_REPLACEMENT_UNPROVED',
    'allocation-identity': 'S307_POOL_GENERATIONS_UNPROVED',
}
EXCLUSIONS = ['pointer-only identity', '0->1 alias', 'token-loss identity',
              'unloaded exemption', 'import inventory as runtime proof',
              'property deletion as content clearing', 'ranks 1-7 and 9',
              's254-s306 edits', 'runtime/contracts/shared sampler/threshold/validator changes']


def sha(data):
    return hashlib.sha256(data).hexdigest()


def audit_source(source, bounds):
    if bounds['kind'] != 'archived_AS2_source_not_native_execution' or bounds['member'] != MEMBER:
        raise ValueError('source is not a native resolver')
    if sha(source.encode()) != bounds['member_sha256']:
        raise ValueError('changed archived source')
    lines = source.splitlines()
    expected = [('s261Describe', 4, 15), ('s261Observe', 16, 42), ('s261Controls', 45, 61)]
    if [(r['name'], r['first_line'], r['last_line']) for r in bounds['functions']] != expected:
        raise ValueError('incomplete function boundaries')
    functions = []
    for row in bounds['functions']:
        body = lines[row['first_line'] - 1:row['last_line']]
        if (not body[0].startswith('_global.' + row['name'] + ' = function(')
                or body[-1] != '};' or sha(('\n'.join(body) + '\n').encode()) != row['sha256']):
            raise ValueError('changed complete function')
        functions.append(dict(row, lines=[{'line': i, 'text': text}
                         for i, text in enumerate(body, row['first_line'])]))

    def bind(statement):
        hits = [i for i, line in enumerate(lines, 1) if line.strip() == statement]
        if len(hits) != 1:
            raise ValueError('missing or ambiguous statement: ' + statement)
        return {'line': hits[0], 'statement': statement}

    routes = {
        'saved_reference': [bind('_global.s261Receiver = receiver;'),
                            bind('var saved = _global.s261Receiver;')],
        'depth_slot': [bind('_global.s261Parent = receiver._parent;'),
                       bind('_global.s261Depth = receiver.getDepth();'),
                       bind('var parent = _global.s261Parent;'),
                       bind('var occupant = parent.getInstanceAtDepth(_global.s261Depth);')],
        'named_slot': [bind('var named = parent.AImain;')],
    }
    writes = {name: [i for i, line in enumerate(lines, 1)
                    if re.search(r'_global\.' + name + r'\s*=(?!=)', line)]
              for name in ('s261Receiver', 's261Parent', 's261Depth')}
    if list(writes.values()) != [[23], [24], [25]]:
        raise ValueError('changed explicit reference writes')
    statements = ['var host = _root.createEmptyMovieClip("__s261Control", 100001);',
                  'var saved = host.createEmptyMovieClip("slot", 1);',
                  'saved.identity = token;', 'saved.removeMovieClip();',
                  'var replacement = host.createEmptyMovieClip("slot", 1);',
                  'replacement.identity = {};', 'var retained = replacement;',
                  'var secondToken = replacement.identity;', 'delete replacement.identity;',
                  'host.removeMovieClip();']
    operations = [bind(s) for s in statements]
    if [r['line'] for r in operations] != [47, 48, 50, 52, 53, 54, 56, 57, 58, 60]:
        raise ValueError('changed control order')
    logs = [{'line': i, 'statement': line.strip()} for i, line in enumerate(lines, 1)
            if '_root.aiEvent("s261_control",' in line]
    if [r['line'] for r in logs] != [51, 55, 59]:
        raise ValueError('changed control log coverage')
    return {'functions': functions, 'reference_routes': routes,
            'explicit_reference_writes_in_member': writes,
            'control_operations_in_source_order': operations, 'control_logs': logs,
            'source_order_only': True, 'independent_native_resolvers_derived': False,
            'findings': [
                'Saved global and parent/depth query are distinct AS2 expression routes, not independent native referent resolvers.',
                'Parent and depth are saved from the same receiver before controls; no explicit reassignment of these three globals occurs in this member. Dynamic/native mutation is not excluded.',
                'Control remove/create occurs between logs 51 and 55. No log occurs at native destruction, free, pool checkout or reuse.',
                'The final control aliases retained to replacement, saves its property, then deletes only replacement.identity before log 59.',
                'Describe enumerates and sorts children, coerces strings, and reads properties sequentially. Four object logs are not one atomic native snapshot.',
            ],
            'native_layout': None, 'loaded_module_binding': None,
            'ordered_pool_generations': None}


def diagnose():
    for path, expected in json.loads((HERE / 'input-sha256.json').read_text()).items():
        if sha((ROOT / path).read_bytes()) != expected:
            raise ValueError('locked input changed: ' + path)
    spec = importlib.util.spec_from_file_location('s298_locked', HERE.parent / 's298/diagnose.py')
    prior = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prior)
    replay = prior.diagnose()
    if replay != json.loads((HERE.parent / 's298/diagnosis.json').read_text()):
        raise ValueError('locked s298 diagnosis mismatch')
    with tarfile.open(HERE.parent / 's261/native-build.tar.gz') as archive:
        source = archive.extractfile(MEMBER).read().decode()
    audit = audit_source(source, json.loads((HERE / 'source-bounds.json').read_text()))
    return {
        'base': BASE, 'scope': 's307 / AFTER-s299 rank #8 only',
        'status': 'honest_unproved', 'production_admitted': False, 'native_parity_proven': False,
        'product_obligations_closed': 0, 'm0_02_status': 'pending', 'locked_s298_reproduced': True,
        'retained_capture': replay['retained_capture'], 'source_audit': audit,
        'reference_window': replay['reference_window'], 'target_sites': replay['target_sites'],
        'native_observations': replay['native_observations'],
        'control_obligations': replay['control_obligations'],
        'slot_reference_proved': False, 'allocation_identity_proved': False,
        'actual_native_controls_executed': False, 'absence_of_possible_resolver_proved': False,
        'new_builds': 0, 'new_player_launches': 0, 'new_process_attaches': 0,
        'new_captures': 0, 'new_symbol_queries': 0,
        'exclusions_enforced': EXCLUSIONS, 'requirement_failure_codes': REQUIREMENTS,
        'blocker': 'Independent native slot/saved-reference layouts and live bindings remain missing. AS2 routes cannot supply actual content clearing, destruction/free or complete ordered pool generations; replacement and reuse remain unqualified.',
        'next_discriminator': replay['next_discriminator'],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    for name in REQUIREMENTS:
        parser.add_argument('--require-' + name, action='store_true')
    args = parser.parse_args()
    try:
        report = diagnose()
    except (ValueError, KeyError, OSError, TypeError, tarfile.TarError) as exc:
        parser.exit(1, 'S307_EVIDENCE_INVALID: ' + str(exc) + '\n')
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    failures = [code + ': ' + report['blocker'] for name, code in REQUIREMENTS.items()
                if getattr(args, 'require_' + name.replace('-', '_'))]
    if failures:
        parser.exit(1, '\n'.join(failures) + '\n')
    print('S307_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')


if __name__ == '__main__':
    main()
