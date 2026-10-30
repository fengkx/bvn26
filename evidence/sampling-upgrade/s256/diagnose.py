"""Recompute one P1 receiver boundary from locked source and native evidence."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import tarfile
import tempfile
from urllib.parse import unquote
import xml.etree.ElementTree as ET

from tools.sampling_geometry import collect
from tools.sampling_native import sha, validate_capture

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
FIELDS = ('path', 'type', 'parent', 'depth', 'frame', 'total_frames',
          'getHitObj_type', 'getStgHitObj_type', 'stamp_id', 'stamp_source',
          'stamp_birth', 'fs_type', 'fzfs_type', 'stgks_type')


def observations(raw):
    result = {}
    for line in raw.splitlines():
        p = line.split('|', 7)
        if len(p) != 8:
            raise ValueError('malformed event')
        tick, kind = int(p[5]), p[6]
        if not kind.startswith('s256_'):
            continue
        v = p[7].split(',')
        if tick not in (10, 11, 12):
            raise ValueError('out-of-scope observation')
        if kind == 's256_identity':
            if tick in result or len(v) != 3:
                raise ValueError('duplicate/malformed boundary')
            result[tick] = dict(sequence=int(p[2]), display=int(p[4]), parent_frame=int(v[0]),
                                named_equals_depth=v[1], saved_equals_depth=v[2], objects={})
        elif kind == 's256_object':
            if tick not in result or len(v) != 15 or v[0] not in ('named', 'depth', 'saved_tick10') or v[0] in result[tick]['objects']:
                raise ValueError('missing/duplicate/malformed object')
            result[tick]['objects'][v[0]] = dict(zip(FIELDS, map(unquote, v[1:])))
        else:
            raise ValueError('unknown observer event')
    if list(result) != [10, 11, 12] or any(list(r['objects']) != ['named', 'depth', 'saved_tick10'] for r in result.values()):
        raise ValueError('incomplete observation')
    return result


def source_report(xml):
    root = ET.fromstring(xml)
    sprite = next(x for x in root.iter('item') if x.get('type') == 'DefineSpriteTag' and x.get('spriteId') == '542')
    frame = 1
    changes = []
    labels = []
    for tag in sprite.find('subTags'):
        if tag.get('depth') == '29' and frame <= 841:
            changes.append({'frame': frame, 'tag': ET.tostring(tag, encoding='unicode').strip()})
        if tag.get('type') == 'FrameLabelTag':
            labels.append({'frame': frame, 'name': tag.get('name')})
        if tag.get('type') == 'ShowFrameTag':
            frame += 1
    bundle = json.loads((ROOT / 'scripts/fighter/didala.json').read_text())
    next_label = next(x['frame'] for x in labels if x['frame'] > 840)
    scripts = [s for s in bundle['scripts'] if s['path'].startswith('DefineSprite_542/frame_')
               and 840 <= int(s['path'].split('/')[1][6:]) < next_label]
    receiver = next(s for s in bundle['scripts'] if s['path'] == 'DefineSprite_2/frame_1/DoAction.as')
    return {'sprite': 542, 'authored_depth': 29, 'runtime_depth': -16355,
            'depth_history_through_841': changes, 'label': next(x for x in labels if x['frame'] == 840),
            'next_label': next_label, 'label_scripts': scripts, 'receiver_script': receiver}


def diagnose():
    for name, expected in json.loads((HERE / 'artifact-sha256.json').read_text()).items():
        if sha(ROOT / name) != expected:
            raise ValueError('changed evidence: ' + name)
    metadata = json.loads((HERE / 'native-build.json').read_text())
    prior = json.loads((HERE.parent / 's251/native-build.json').read_text())
    case = json.loads((HERE.parent / 's64/didala__summon__neutral__ground__near.json').read_text())
    if metadata['move_case'] != prior['move_case'] or any(
            digest != prior['outputs_sha256'][name]
            for name, digest in metadata['outputs_sha256'].items() if name != 'game/main.swf'):
        raise ValueError('changed tape or non-main instrumentation')
    raw = gzip.decompress((HERE / 'native-capture.log.gz').read_bytes()).decode()
    for name, expected in metadata['sources_sha256'].items():
        if sha(ROOT / name) != expected:
            raise ValueError('changed source: ' + name)
    with tarfile.open(HERE / 'native-build.tar.gz') as archive:
        if json.loads(archive.extractfile('build.json').read()) != metadata:
            raise ValueError('changed build metadata')
        for name, expected in {**metadata['outputs_sha256'], 'instrumentation.diff': metadata['instrumentation_sha256']}.items():
            if hashlib.sha256(archive.extractfile(name).read()).hexdigest() != expected:
                raise ValueError('changed compiled output: ' + name)
        root_script = archive.extractfile('patches/main/frame_10/DoAction.as').read().decode()
        if root_script.count('   _root.s256Observe();\n   _root.aiGeometrySample();') != 1:
            raise ValueError('observer not at the selected geometry boundary')
    with tempfile.TemporaryDirectory() as temp:
        trace = Path(temp) / 'native.log'
        trace.write_text(raw)
        validate_capture(case, metadata, trace)
    with tarfile.open(HERE.parent / 's30/source-exports.tar.gz') as archive:
        xml = archive.extractfile('bvn-s30-source/fighter-didala.xml').read()
    source_pin = json.loads((HERE.parent / 's30/source-exports.json').read_text())['game/fighter/didala.swf']
    if hashlib.sha256(xml).hexdigest() != source_pin['xml_sha256'] or sha(ROOT / 'game/fighter/didala.swf') != source_pin['source_sha256']:
        raise ValueError('changed source XML')
    sources = set()
    for name in metadata['sources_sha256']:
        if name.startswith('scripts/'):
            b = json.loads((ROOT / name).read_text())
            sources.update(b['game_file'] + '#' + s['path'] for s in b['scripts'])
    geometry = collect(raw.splitlines(), metadata['run_id'], case['frames'], sources)
    def actors(text):
        return [(int(p[5]), p[7]) for line in text.splitlines()
                if len(p := line.split('|', 7)) == 8 and p[6] == 'state' and int(p[5]) >= 0]
    old = gzip.decompress((HERE.parent / 's251/native-capture.log.gz').read_bytes()).decode()
    return {'production_admitted': False, 'native_parity_proven': False, 'eligibility_fix_proved': False,
            'observations': {str(k): v for k, v in observations(raw).items()}, 'source': source_report(xml),
            'geometry_samples': len(geometry['samples']),
            'selected_geometry': [s for s in geometry['samples'] if 10 <= s['tick'] <= 12],
            'actor_comparison': {'rows': len(actors(raw)), 'exact_tick_payload_equal_s251': actors(raw) == actors(old)},
            'events': len(raw.splitlines()), 'new_native_captures': 1}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(json.dumps(diagnose(), indent=2, ensure_ascii=False) + '\n')
    print('RECEIVER_DIAGNOSIS_OK; no eligibility fix or admission')
