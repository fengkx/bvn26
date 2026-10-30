"""Bound one authored Yulong owner chain without inferring receiver eligibility."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import re
import tarfile
import tempfile
import xml.etree.ElementTree as ET

from tools.sampling_k1atm_provenance import collect_provenance
from tools.sampling_native import validate_capture

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUTER = '_level0.game.p1.mc.k1atm'
INNER = OUTER + '.mian'
PREFIX = 'DefineSprite_345/frame_188/PlaceObject2_104_28/'
ENTER = PREFIX + 'CLIPACTIONRECORD onClipEvent(enterFrame).as'


def check_hash(data, expected):
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError('locked input hash mismatch')


def timeline(xml, sprite_id):
    sprite = next(e for e in xml.iter('item')
                  if e.get('type') == 'DefineSpriteTag' and e.get('spriteId') == str(sprite_id))
    frames = [[] for _ in range(int(sprite.get('frameCount')))]
    frame = 0
    for index, tag in enumerate(sprite.find('subTags')):
        if tag.get('type') == 'ShowFrameTag':
            frame += 1
        else:
            frames[frame].append({'tag_index': index, 'attributes': dict(tag.attrib)})
    if frame != len(frames):
        raise ValueError('incomplete authored timeline')
    return frames


def operand_sites(source):
    # This bounded inventory deliberately preserves the fourth receiver's extra hop.
    sites = re.findall(r'(hitmc\.mian|mian)\.hitTest\((_root\.game\["p" \+ _parent\.pn\]\.mc\.\w+)\)', source)
    expected = [('mian', name) for name in ('bdmn', 'zh1atm', 'zh2atm')]
    expected += [('hitmc.mian', 'zh3atm'), ('mian', 'abcd')]
    if sites != [(receiver, '_root.game["p" + _parent.pn].mc.' + name)
                 for receiver, name in expected]:
        raise ValueError('changed authored operand chain')
    return [{'ordinal': i + 1, 'receiver_expression': receiver, 'target_expression': target}
            for i, (receiver, target) in enumerate(sites)]


def observe(lines):
    provenance = collect_provenance(lines)
    boxes, states = [], []
    kinds = Counter()
    for line in lines:
        parts = line.split('|', 7)
        kinds[parts[6]] += 1
        tick, kind, payload = int(parts[5]), parts[6], parts[7].split(',')
        if kind == 'geometry_box' and payload[1] in (OUTER, INNER):
            boxes.append({'sequence': int(parts[2]), 'tick': tick, 'role': payload[0],
                          'path': payload[1], 'stamp_id': payload[2], 'source': payload[3],
                          'birth_display': int(payload[4]), 'depth': int(payload[5]),
                          'frame': int(payload[6])})
        if kind == 'state' and payload[0] == 'p1' and 15 <= tick <= 22:
            states.append({'sequence': int(parts[2]), 'tick': tick, 'body_frame': int(payload[1])})
    outer = [b for b in boxes if b['path'] == OUTER]
    inner = [b for b in boxes if b['path'] == INNER]
    if [(b['tick'], b['frame']) for b in outer] != [(16, 1), (17, 1), (18, 1), (19, 5)]:
        raise ValueError('changed outer sampled lifetime')
    if [(b['tick'], b['frame']) for b in inner] != [(16, 1), (17, 1), (18, 1)]:
        raise ValueError('changed nested sampled lifetime')
    for records, sprite, stamp, depth in ((outer, 104, '70', -16356), (inner, 2, '71', -16382)):
        for row in records:
            if (row['source'], row['stamp_id'], row['depth'], row['birth_display']) != (
                    f'game/fighter/yulong.swf#DefineSprite_{sprite}/frame_1/DoAction.as', stamp, depth, 448):
                raise ValueError('changed sampled owner provenance')
    return {'events': len(lines), 'event_kind_counts': dict(sorted(kinds.items())),
            'provenance': provenance, 'chain_boxes': boxes, 'body_frames': states,
            'exact_operand_call_observation': None, 'exact_child_removal_observation': None,
            'exact_parent_rename_observation': None, 'continuous_allocation_identity': None}


def diagnose():
    for path, expected in json.loads((HERE / 'input-sha256.json').read_text()).items():
        check_hash((ROOT / path).read_bytes(), expected)
    old = HERE.parent / 's247'
    binding = json.loads((old / 'source-binding.json').read_text())
    bundle = json.loads((ROOT / binding['bundle']).read_text())
    scripts = {s['path']: s['source'] for s in bundle['scripts']}
    check_hash((ROOT / binding['swf']).read_bytes(), binding['swf_sha256'])
    check_hash((ROOT / binding['bundle']).read_bytes(), binding['bundle_sha256'])
    with tarfile.open(ROOT / binding['xml_archive']) as archive:
        xml_bytes = archive.extractfile(binding['xml_member']).read()
    check_hash(xml_bytes, binding['xml_sha256'])
    xml = ET.fromstring(xml_bytes)
    child_frames = timeline(xml, 104)
    body_frames = timeline(xml, 345)
    frame_inventory = []
    for frame, tags in enumerate(child_frames, 1):
        source = {p: s for p, s in scripts.items() if p.startswith(f'DefineSprite_104/frame_{frame}/')}
        frame_inventory.append({'frame': frame, 'tags': tags, 'scripts': source})
    body_changes = [{'frame': i, **t} for i in range(188, 195) for t in body_frames[i - 1]
                    if t['attributes'].get('depth') == '28']
    if [(r['frame'], r['attributes']['type']) for r in body_changes] != [
            (188, 'PlaceObject2Tag'), (194, 'RemoveObject2Tag')]:
        raise ValueError('changed parent placement lifetime')
    receipt = json.loads((old / 'native-receipt.json').read_text())
    metadata = json.loads((old / 'native-build.json').read_text())
    with tarfile.open(old / 'native-build.tar.gz') as archive:
        if json.loads(archive.extractfile('build.json').read()) != metadata:
            raise ValueError('archived build metadata mismatch')
        for path, expected in metadata['outputs_sha256'].items():
            data = archive.extractfile(path).read()
            check_hash(data, expected)
            check_hash(data, receipt['files'][receipt['build'] + '/' + path])
    for path, expected in metadata['sources_sha256'].items():
        check_hash((ROOT / path).read_bytes(), expected)
    raw = gzip.decompress((old / 'native-capture.log.gz').read_bytes())
    check_hash(raw, receipt['files'][receipt['trace']])
    with tempfile.TemporaryDirectory() as temp:
        trace = Path(temp) / 'native.log'
        trace.write_bytes(raw)
        validate_capture(metadata['move_case'], metadata, trace)
    observed = observe(raw.decode().splitlines())
    return {'scope': 'AFTER-s263 rank 7 only', 'base': '53dd5222',
            'production_admitted': False, 'native_parity_proven': False,
            'runtime_binding_proved': False, 'product_obligations_closed': 0,
            'new_builds': 0, 'new_player_launches': 0,
            'source_chain': binding['placement_chain'], 'parent_depth_28_changes': body_changes,
            'sprite104_complete_frame_inventory': frame_inventory,
            'outer_clip_actions': {p: s for p, s in scripts.items() if p.startswith(PREFIX)},
            'ordered_authored_hit_test_sites': operand_sites(scripts[ENTER]),
            'source_receiver_context': 'Sprite104 clip action; _parent is Sprite345 body',
            'walker_receiver_context': 'Sprite2 function-bearing mian; _parent is Sprite104 projectile',
            'raw_capture_structure_exit': 0, 'observed': observed,
            'archived_outputs_match_receipt': True,
            'missing': ['executed operand site and actual receiver/target',
                        'child removal versus parent rename at the intra-frame boundary',
                        'source-driven receiver eligibility throughout the bounded lifetime'],
            'next_discriminator': [
                'Use the unchanged s239 tape and only the Sprite345/frame188 placement of Sprite104.',
                'Observe existing outer enterFrame branch/operand sites in authored order, preserving short-circuit evaluation and not evaluating extra hitTest calls; retain the hitmc.mian fourth receiver literally.',
                'Correlate outer and nested source placement/load observations, direct parent, native depth, source stamp, current frame and slot observations through ticks15-22; stamps are not allocation identity.',
                'Record Sprite104 frame5 child depth2 removal and before/after authored rename separately; record body frame194 depth28 removal separately. Do not equate path absence with owner death.',
                'Require an actual observed receiver/target join and preserved full stream before proposing any bounded rule; missing events keep admission false. No ancestor-pn substitution or generic eligibility exemption.'
            ]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--require-runtime-binding', action='store_true')
    parser.add_argument('--require-geometry', action='store_true')
    args = parser.parse_args()
    report = diagnose()
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    if args.require_geometry:
        from tools.sampling_geometry import collect
        metadata = json.loads((HERE.parent / 's247/native-build.json').read_text())
        sources = set()
        for path in metadata['sources_sha256']:
            if path.startswith('scripts/') and path.endswith('.json'):
                bundle = json.loads((ROOT / path).read_text())
                sources.update(bundle['game_file'] + '#' + s['path'] for s in bundle['scripts'])
        raw = gzip.decompress((HERE.parent / 's247/native-capture.log.gz').read_bytes())
        try:
            collect(raw.decode().splitlines(), metadata['run_id'], metadata['move_case']['frames'], sources)
        except ValueError as error:
            print('UNCHANGED_GEOMETRY_COLLECTOR_REJECTED: ' + str(error))
            return 1
    if args.require_runtime_binding:
        print('RUNTIME_BINDING_UNPROVED: ' + '; '.join(report['missing']))
        return 1
    print('S270_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
