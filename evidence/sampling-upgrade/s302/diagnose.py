"""Audit only the locked Yulong getHitObj bytes and frame188 observer effects."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tarfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = 'a866246aa4e1deedd0b802bb584b0ebc20ea31d8'
# Parameter names come from the headers; local names come from the locked source.
ROLES = {
    'original': {0: 'enumeration_item', 1: 'this', 2: '_loc2_', 3: 'ppw',
                 4: '_loc4_', 9: 'array', 12: 'afterFix', 13: 'player', 14: '_loc14_'},
    's275_archive': {0: 'enumeration_item', 1: 'this', 2: 'array', 3: 'player',
                     4: 'afterFix', 5: 'ppw', 6: '_loc2_', 7: '_loc4_', 8: '_loc14_'},
}
OPS = {0x49: 'Equals2', 0x12: 'Not', 0x17: 'Pop', 0x55: 'Enumerate2',
       0x4e: 'GetMember', 0x47: 'Add2', 0x52: 'CallMethod', 0x43: 'InitObject',
       0x3e: 'Return', 0x87: 'StoreRegister', 0x99: 'Jump', 0x9d: 'If', 0x96: 'Push'}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def prior_module():
    spec = importlib.util.spec_from_file_location('s302_locked_s294', HERE.parent / 's294/diagnose.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def decode(function, roles):
    """Expand Push packets without reordering values; reject unhandled operands."""
    nodes, boundaries = [], {}
    body = bytes.fromhex(function['body_hex'])
    if len(body) != function['body_length'] or sha(body) != function['body_sha256']:
        raise ValueError('body custody mismatch')
    cursor = function['body_offset']
    for row in function['instructions']:
        raw = bytes.fromhex(row['hex'])
        if row['offset'] != cursor or row['end'] != cursor + len(raw):
            raise ValueError('instruction coverage mismatch')
        if raw != body[cursor - function['body_offset']:row['end'] - function['body_offset']]:
            raise ValueError('instruction bytes mismatch')
        op = raw[0]
        if op != row['opcode'] or op not in OPS:
            raise ValueError('unsupported opcode')
        payload = raw[3:] if op >= 128 else b''
        if op >= 128 and struct.unpack_from('<H', raw, 1)[0] != len(payload):
            raise ValueError('invalid action length')
        boundaries[cursor] = len(nodes)
        operands = []
        if op == 0x96:
            pos = 0
            while pos < len(payload):
                kind = payload[pos]
                pos += 1
                if kind in (2, 3):
                    value = ['null' if kind == 2 else 'undefined']
                elif kind in (4, 8):
                    number = payload[pos]
                    pos += 1
                    if kind == 4:
                        if number not in roles:
                            raise ValueError('unmapped register')
                        value = ['register', roles[number]]
                    else:
                        value = ['string', function['constant_pool'][number]]
                elif kind == 7:
                    value = ['integer', struct.unpack_from('<i', payload, pos)[0]]
                    pos += 4
                else:
                    raise ValueError('unsupported Push type')
                operands.append(value)
        elif op == 0x87:
            if len(payload) != 1 or payload[0] not in roles:
                raise ValueError('unmapped StoreRegister')
            operands = [[roles[payload[0]]]]
        elif op in (0x99, 0x9d):
            target = row['end'] + struct.unpack('<h', payload)[0]
            if target != row.get('branch_target'):
                raise ValueError('branch bytes mismatch')
        elif payload or len(raw) != 1:
            raise ValueError('unexpected opcode payload')
        for part, operand in enumerate(operands or [[]]):
            nodes.append({'id': len(nodes), 'offset': cursor, 'push_part': part,
                          'op': OPS[op], 'operand': operand,
                          'raw_hex': row['hex'], 'target_offset': row.get('branch_target')})
        cursor = row['end']
    if cursor != function['body_offset'] + len(body):
        raise ValueError('incomplete body coverage')
    boundaries[cursor] = len(nodes)
    for n in nodes:
        if n['op'] in ('Jump', 'If'):
            if n['target_offset'] not in boundaries:
                raise ValueError('branch outside instruction boundary')
            n['target'] = boundaries[n['target_offset']]
    return nodes


def graph(nodes, erase_initializers=False):
    """Conditional projection only: retain every bypass and its premise."""
    removed, rewrites = {}, []
    if erase_initializers:
        for role in ('_loc2_', '_loc4_'):
            hits = [i for i in range(len(nodes) - 2)
                    if [(n['op'], n['operand']) for n in nodes[i:i + 3]] ==
                    [('Push', ['undefined']), ('StoreRegister', [role]), ('Pop', [])]]
            if len(hits) != 1:
                raise ValueError('missing or ambiguous initializer')
            i = hits[0]
            removed.update({j: i + 3 for j in range(i, i + 3)})
            rewrites.append({'kind': 'conditional_initializer_erasure', 'nodes': list(range(i, i + 3)),
                             'role': role, 'activation_visible_erasure_proved': False})
    branches = {}
    for n in nodes:
        if n['op'] == 'Jump':
            removed[n['id']] = n['target']
            rewrites.append({'kind': 'jump_bypass', 'nodes': [n['id']], 'target': n['target']})
        if n['op'] == 'If':
            i, count = n['id'] - 1, 0
            while i >= 0 and nodes[i]['op'] == 'Not':
                count += 1
                i -= 1
            for j in range(i + 1, n['id']):
                removed[j] = n['id']
            if count:
                # No branch may enter the middle of a Boolean-normalization chain.
                if any(x.get('target') in range(i + 2, n['id'] + 1) for x in nodes):
                    raise ValueError('branch enters normalization interior')
                rewrites.append({'kind': 'boolean_branch_polarity', 'nodes': list(range(i + 1, n['id'] + 1)), 'not_count': count})
            edges = [n['target'], n['id'] + 1]
            branches[n['id']] = edges[::-1] if count % 2 else edges

    def resolve(i):
        seen = set()
        while i in removed:
            if i in seen:
                raise ValueError('epsilon cycle')
            seen.add(i)
            i = removed[i]
        return i

    result = {}
    for n in nodes:
        i = n['id']
        if i in removed:
            continue
        edges = branches.get(i, [] if n['op'] == 'Return' else [i + 1])
        result[i] = {'op': 'BranchTruthy' if n['op'] == 'If' else n['op'],
                     'operand': n['operand'], 'edges': [resolve(e) for e in edges]}
    if any(e not in result for n in result.values() for e in n['edges']):
        raise ValueError('unhandled function-end edge')
    return {'entry': resolve(0), 'nodes': result, 'rewrites': rewrites}


def correspondence(original, archived):
    left = decode(original, ROLES['original'])
    right = decode(archived, ROLES['s275_archive'])
    a, b = graph(left), graph(right, erase_initializers=True)
    pending, pairs, reverse = [(a['entry'], b['entry'])], {}, {}
    while pending:
        x, y = pending.pop()
        if x in pairs:
            if pairs[x] != y:
                raise ValueError('inconsistent graph mapping')
            continue
        if y in reverse:
            raise ValueError('non-bijective graph mapping')
        u, v = a['nodes'][x], b['nodes'][y]
        if (u['op'], u['operand'], len(u['edges'])) != (v['op'], v['operand'], len(v['edges'])):
            raise ValueError('operand or branch correspondence mismatch')
        pairs[x], reverse[y] = y, x
        pending.extend(zip(u['edges'], v['edges'], strict=True))
    if set(pairs) != set(a['nodes']) or set(reverse) != set(b['nodes']):
        raise ValueError('uncovered projected nodes')
    return {'original': left, 's275_archive': right,
            'register_roles': ROLES, 'original_projection': a, 'archived_projection': b,
            'node_pairs': [{'original': x, 'archived': y} for x, y in sorted(pairs.items())],
            'conditional_graph_equal': True, 'complete_correspondence_proved': False,
            'premises': ['Register roles are a static correspondence, not an executed activation binding.',
                         'Two added undefined local writes are conditionally erased; activation-visible erasure is unproved.',
                         'Push splitting preserves ordered values only; instruction dispatch/timing equality is not claimed.',
                         'Jump bypass and Boolean polarity preserve graph predicates, not native cursor or scheduling.']}


def observer_effects():
    """Expose exact retained helper bodies; do not execute or silently erase them."""
    archive_path = HERE.parent / 's275/native-build.tar.gz'
    with tarfile.open(archive_path) as archive:
        main_path = 's275-patches/main/frame_1/DoAction.as'
        main = archive.extractfile(main_path).read().decode()
        selected = {}
        for name in ('aiGeoStamp', 'aiK1Observe', 'aiEvent'):
            start = main.index(name + ' = function(')
            end = main.index('\n};', start) + 3
            body = main[start:end]
            selected[name] = {'archive_member': main_path, 'source': body,
                              'source_sha256': sha(body.encode()),
                              'start_line': main[:start].count('\n') + 1}
        for member in ('s275-patches/main/frame_10/DoAction.as',
                       'patches/fighter/yulong/DefineSprite_104/frame_1/DoAction.as',
                       'patches/fighter/yulong/DefineSprite_104/frame_10/DoAction.as',
                       's275-patches/fighter/yulong/DefineSprite_345/frame_188/PlaceObject2_104_28/CLIPACTIONRECORD onClipEvent(enterFrame).as',
                       's275-patches/fighter/yulong/DefineSprite_104/frame_5/DoAction.as',
                       'patches/fighter/yulong/DefineSprite_2/frame_1/DoAction.as'):
            raw = archive.extractfile(member).read()
            selected[member] = {'archive_member': member, 'source_sha256': sha(raw),
                                'source': raw.decode()}
    selected['s275_helpers'] = {'path': 'evidence/sampling-upgrade/s275/observer.as',
                               'source': (HERE.parent / 's275/observer.as').read_text()}
    return {'sources': selected,
            'effects': [
                {'site': 'Sprite2 initialization suffix / aiGeoStamp',
                 'effects': ['reads mc.__aiGeoId; conditionally increments root.aiGeoSerial',
                             'writes mc.__aiGeoId, mc.__aiGeoSource, mc.__aiGeoBirth',
                             'adds observable own properties; not assumed invisible to enumeration']},
                {'site': 'Sprite2 initialization suffix / aiK1Observe',
                 'effects': ['String(this) path guard and direct-parent pn target lookup',
                             'reads parent, lists, function properties and historical grandparent.pn for logging only',
                             'String/escape conversions and aiEvent call; no nested function entry hook',
                             'historical ancestor read is disclosed, never used as a pn substitute or eligibility rule']},
                {'site': 'frame188 enterFrame / s275Value',
                 'effects': ['wraps pause, five original receiver/target/results and played expressions',
                             'reads value parent/frame/stamp properties, coerces values, invokes aiEvent, returns supplied value',
                             'source pass-through does not prove getter/conversion/activation/timing neutrality']},
                {'site': 'before/after goto, before/after rename / s275Boundary',
                 'effects': ['reads slots and stamps; calls getInstanceAtDepth, String, escape and aiEvent',
                             'helper after goto is not a direct removal dispatch or invalidated-continuation witness']},
                {'site': 'root frame10 sampling and Sprite104 frame1/frame10 stamps',
                 'effects': ['root_sample and root_slot calls add reads outside the nested function',
                             'Sprite104 initialization/stop frames also call aiGeoStamp; exact archived sources retained',
                             'no independent direct dispatch channel is supplied by root sampling']},
                {'site': 'aiEvent shared logging dependency',
                 'effects': ['exact retained source exposes aiSeq increment, getTimer, string concatenation and trace work',
                             'logging cost and callback scheduling perturbation have no independent off/on bound']},
            ],
            'complete_compiled_helper_preservation_proved': False,
            'independent_observer_off_on': None, 'perturbation_bound': None,
            'limit': 'Source effect inventory, not complete transitive compiled equivalence or measured runtime effects.'}


def diagnose():
    for name, digest in json.loads((HERE / 'input-sha256.json').read_text()).items():
        if sha((ROOT / name).read_bytes()) != digest:
            raise ValueError('locked input changed: ' + name)
    historical = prior_module().diagnose()
    if historical != json.loads((HERE.parent / 's294/diagnosis.json').read_text()):
        raise ValueError('locked s294 diagnosis changed')
    functions = historical['compiled_nested_functions']
    original, archived = [functions[k]['functions'][4] for k in ('original', 's275_archive')]
    if any(f['name'] != 'getHitObj' or f['flags'] != 41 for f in (original, archived)):
        raise ValueError('changed activation header')
    for side, f in [('original', original), ('s275_archive', archived)]:
        if [(p['name'], ROLES[side].get(p['register'])) for p in f['parameters']] != [(x, x) for x in ('array', 'player', 'afterFix', 'ppw')]:
            raise ValueError('parameter role mismatch')
    audit = correspondence(original, archived)
    return {'slice': 's302', 'base': BASE, 'scope': 'AFTER-s299 rank #3 only; Sprite345 frame188 depth28 Sprite104/depth2 Sprite2; ticks15-22',
            'production_admitted': False, 'native_parity_proven': False,
            'complete_correspondence_proved': False, 'observer_qualified': False,
            'direct_removal_dispatch_proved': False, 'nested_entry_proved': False,
            'new_builds': 0, 'new_player_launches': 0, 'new_captures': 0,
            'paired_controls': 0, 'product_obligations_closed': 0,
            'locked_s294_reproduced': True, 'retained_events': historical['retained_events'],
            'activation_headers': {side: {k: f[k] for k in ('opcode', 'header_hex', 'register_count', 'flags', 'parameters', 'body_sha256', 'body_offset', 'body_length')}
                                   for side, f in [('original', original), ('s275_archive', archived)]},
            'getHitObj_audit': audit, 'observer_effects': observer_effects(),
            'observations': historical['observations'],
            'removal_tag_binding': historical['removal_tag_binding'],
            'exclusions': historical['exclusions'] + ['s254-s301 edits', 'ranks 1-2 or 4+ execution', 'runtime/contracts/shared sampler/threshold/validator changes'],
            'blocker': 'Activation-visible initializer erasure and helper effects remain unproved; no loaded activation/operand binding or independent observer-off/on control. Direct removal and natural nested-entry paired controls remain blocked.',
            'coordinates': 'Uncompressed file offsets and expanded audit node IDs, never native PCs or live action cursors.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    fields = {'correspondence': ('complete_correspondence_proved', 'S302_COMPLETE_CORRESPONDENCE_UNPROVED'),
              'observer': ('observer_qualified', 'S302_OBSERVER_EFFECTS_UNPROVED'),
              'parent-removal': ('direct_removal_dispatch_proved', 'S302_REMOVAL_DISPATCH_UNPROVED'),
              'nested-entry': ('nested_entry_proved', 'S302_NESTED_ENTRY_UNPROVED')}
    for flag in fields:
        parser.add_argument('--require-' + flag, action='store_true')
    args = parser.parse_args()
    result = diagnose()
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    missing = [code for flag, (field, code) in fields.items()
               if getattr(args, 'require_' + flag.replace('-', '_')) and not result[field]]
    if missing:
        print('; '.join(missing) + ': ' + result['blocker'])
        return 1
    print('S302_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
