"""Audit one external body-push callsite against the locked s264 capture."""
import argparse
from collections import Counter
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import tarfile
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
LOCKED = HERE.parent / 's264'
BODY = 'DefineSprite_638/frame_1/DoAction.as'
CALLER = 'frame_1/PlaceObject2_638_1/CLIPACTIONRECORD onClipEvent(enterFrame).as'
SITE = 'bdmn.hitTest(_root.game["p" + pn].mc.bdmn)'
GUARD = 'if(airBody == false && _root.game["p" + pn].mc.airBody == false)'


def check_hash(data, expected):
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError('locked input hash mismatch')


def function_source(source):
    # Exact named-function boundaries are sufficient for this pinned source only.
    source = source.replace('\r\n', '\n')
    marker = 'function on_enterframe()'
    if source.count(marker) != 1:
        raise ValueError('ambiguous body callback')
    start = source.index(marker)
    end = source.index('\nfunction ', start + len(marker))
    return source[start:end]


def audit_site(source, archived):
    original = function_source(source)
    if function_source(archived) != original:
        raise ValueError('archived callback differs from original')
    if original.count(SITE) != 1 or GUARD not in original or 'if(_loc3_ >= 0 && ' + SITE + ')' not in original:
        raise ValueError('changed callsite operands or short-circuit guards')
    return {'path': BODY, 'function': 'on_enterframe', 'source': original,
            'callsite_line': next(i for i, line in enumerate(source.splitlines(), 1) if SITE in line),
            'receiver_expression': 'bdmn', 'target_expression': '_root.game["p" + pn].mc.bdmn',
            'outer_guard': GUARD, 'short_circuit_left': '_loc3_ >= 0',
            'archived_function_identical': True,
            'callsite_instrumented': False,
            'execution_observed': None, 'evaluated_operands': None, 'native_result': None}


def source_timeline(xml):
    result = {}
    body = next(t for t in xml.iter('item') if t.get('type') == 'DefineSpriteTag' and t.get('spriteId') == '638')
    for label, tags, maximum in (('wrapper', xml.find('tags'), 1), ('body', body.find('subTags'), 7)):
        frame = 1
        rows = []
        for tag in tags:
            if tag.get('type') == 'ShowFrameTag':
                frame += 1
                if frame > maximum:
                    break
            elif tag.get('type') in ('PlaceObject2Tag', 'PlaceObject3Tag', 'RemoveObject2Tag', 'DoActionTag', 'FrameLabelTag'):
                # Preserve actions and clip actions as well as placement attributes.
                rows.append({'frame': frame, 'tag': ET.tostring(tag, encoding='unicode')})
        result[label] = rows
    placements = [ET.fromstring(r['tag']) for r in result['wrapper']]
    if not any(t.get('characterId') == '638' and t.get('depth') == '1'
               and t.get('placeFlagMove') == 'false' for t in placements):
        raise ValueError('base body placement missing')
    return result


def observe(raw, prior):
    rows = [line.split('|', 7) for line in raw.splitlines()]
    begin = prior['unready_interval']['begin_sequence']
    end = prior['unready_interval']['initialized_sequence']
    if (begin, end) != (4055, 4062):
        raise ValueError('changed initialization boundary')
    states = [{'sequence': int(p[2]), 'tick': int(p[5]), 'body_frame': int(p[7].split(',')[1])}
              for p in rows if p[6] == 'state' and p[7].startswith('p2,') and 10 <= int(p[5]) <= 12]
    if [(r['tick'], r['body_frame']) for r in states] != [(10, 4), (11, 5), (12, 6)]:
        raise ValueError('changed P2 sampled frames')
    window = ['|'.join(p) for p in rows if begin <= int(p[2]) <= end]
    if len(window) != end - begin + 1:
        raise ValueError('incomplete boundary window')
    return {'events': len(rows), 'event_kind_counts': dict(sorted(Counter(p[6] for p in rows).items())),
            'p2_body_samples': states, 'unready_window_inclusive': window,
            'post_init_query_rows': len(prior['query_rows']),
            'external_callsite_dispatch': None, 'guards_at_callsite': None,
            'operand_lifetime_join': None,
            'limit': 'Sampled frames, key reads and absent function-entry events do not locate this native hitTest or prove its nonexecution.'}


def diagnose():
    for path, expected in json.loads((HERE / 'input-sha256.json').read_text()).items():
        check_hash((ROOT / path).read_bytes(), expected)
    spec = importlib.util.spec_from_file_location('s273_s264', LOCKED / 'diagnose.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    prior = module.diagnose()
    if prior != json.loads((LOCKED / 'diagnosis.json').read_text()):
        raise ValueError('locked replay changed')
    bundle = json.loads((ROOT / 'scripts/fighter/yihu.json').read_text())
    scripts = {s['path']: s['source'] for s in bundle['scripts']}
    if scripts[CALLER].replace('\r\n', '\n').strip() != 'onClipEvent(enterFrame){\n   on_enterframe();\n}':
        raise ValueError('changed authored caller')
    with tarfile.open(LOCKED / 'native-build.tar.gz') as archive:
        archived = archive.extractfile('patches/fighter/yihu/' + BODY).read().decode()
    site = audit_site(scripts[BODY], archived)
    exports = json.loads((HERE.parent / 's30/source-exports.json').read_text())['game/fighter/yihu.swf']
    check_hash((ROOT / 'game/fighter/yihu.swf').read_bytes(), exports['source_sha256'])
    with tarfile.open(HERE.parent / 's30/source-exports.tar.gz') as archive:
        xml = archive.extractfile('bvn-s30-source/fighter-yihu.xml').read()
    check_hash(xml, exports['xml_sha256'])
    raw_bytes = gzip.decompress((LOCKED / 'native-capture.log.gz').read_bytes())
    receipt = json.loads((LOCKED / 'native-receipt.json').read_text())
    check_hash(raw_bytes, receipt['files'][receipt['trace']])
    selected = next(s for s in prior['selected_geometry'] if s['tick'] == 11)
    if any(b['role'] == 'hurt' and '.game.p1.' in b['path'] for b in selected['boxes']):
        raise ValueError('retained geometry gap changed')
    return {'base': '68136e5efd64160e7a2bd94a8b57ef4abf4f566f', 'rank': 1,
            'production_admitted': False, 'native_parity_proven': False,
            'eligibility_fix_proved': False, 'external_callsite_execution_proved': False,
            'all_collision_paths_observed': False, 'product_obligations_closed': 0,
            'new_builds': 0, 'new_player_launches': 0,
            'site': site, 'caller': {'path': CALLER, 'source': scripts[CALLER]},
            'source_timeline': source_timeline(ET.fromstring(xml)),
            'body_frame_scripts_4_through_7': {str(f): {p: s for p, s in scripts.items()
                if p.startswith(f'DefineSprite_638/frame_{f}/')} for f in range(4, 8)},
            'observed': observe(raw_bytes.decode(), prior),
            'retained_tick11_geometry': selected,
            'next_discriminator': 'Observe only P2 base Sprite638 on_enterframe in ticks10–12: entry/early exits, actual short-circuit guard outcomes, once-evaluated hitTest operands/result and their placement boundaries, alongside s260/s264 initialization markers. Preserve source evaluation order and original inputs; no extra hitTest or forced branch. Require same-site natural positive and skipped-site controls. Missing execution or lifetime evidence keeps eligibility false; this site alone cannot prove all collision paths.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--require-external-callsite', action='store_true')
    args = parser.parse_args()
    report = diagnose()
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print('EXTERNAL_CALLSITE_DIAGNOSIS_OK; external_callsite_execution_proved=false; eligibility_fix_proved=false')
    return int(args.require_external_callsite and not report['external_callsite_execution_proved'])


if __name__ == '__main__':
    raise SystemExit(main())
