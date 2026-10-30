"""Recompute the bounded AImain diagnosis without changing samples or joins.

Run from the repository root with PYTHONPATH=.; restore XML exports at the
paths recorded by each earlier slice's source-exports.json first.
"""
import gzip
import json
from pathlib import Path
import re
import tempfile

from tools.sampling_display import collect, enrich, source_timelines
from tools.sampling_native import sha, validate_capture

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def diagnose():
    manifest = json.loads((ROOT / 'manifest.json').read_text())
    results = []
    for slice_id in ('s86', 's93', 's100', 's248', 's249'):
        base = HERE.parent / slice_id
        metadata = json.loads((base / 'native-build.json').read_text())
        raw = gzip.decompress((base / 'native-capture.log.gz').read_bytes())
        with tempfile.TemporaryDirectory() as temp:
            trace = Path(temp) / 'native.log'
            trace.write_bytes(raw)
            validate_capture(metadata['move_case'], metadata, trace)
        samples = collect(raw.decode().splitlines(), metadata['run_id'], 60)
        exports = json.loads((base / 'source-exports.json').read_text())
        paths = {}
        for source, entry in exports.items():
            path = Path(entry['xml'])
            assert sha(path) == entry['xml_sha256'], path
            assert sha(ROOT / source) == entry['source_sha256'] == metadata['sources_sha256'][source]
            paths[source] = path
        gaps = enrich(samples, paths)
        retained = json.loads(gzip.decompress((base / 'display.json.gz').read_bytes()))
        assert samples == retained['samples']
        assert gaps == retained['source_gaps']
        families = []
        for actor in ('p1', 'p2'):
            path = f'_level0.game.{actor}.mc.AImain'
            records = []
            for sample in samples:
                node = sample['nodes'][path]
                parent = sample['nodes'][node['parent']]
                placement = parent['authored_children'][str(node['depth'] + 16384)]
                assert placement['attributes']['name'] == 'AImain'
                assert placement['attributes']['characterId'] == '3'
                assert node['symbol'] == 3 and node['source_swf'] == parent['source_swf']
                records.append({'tick': sample['tick'], 'parent_frame': parent['frame'],
                                'native_frame': node['frame'], 'instance_id': node['instance_id'],
                                'source_script': node['source_script'], 'child_count': node['child_count'],
                                'placement': placement})
            source = node['source_swf']
            bundle_path = 'scripts/' + source.removeprefix('game/').removesuffix('.swf') + '.json'
            assert sha(ROOT / bundle_path) == manifest['file_sha256'][bundle_path]
            bundle = json.loads((ROOT / bundle_path).read_text())
            assert bundle['swf_sha256'] == exports[source]['source_sha256']
            parent_script = parent['source_script'].split('#', 1)[1]
            script = next(s['source'] for s in bundle['scripts'] if s['path'] == parent_script)
            init_ctrl = re.search(r'function initCtrl\(\).*?\n}', script, re.S).group(0)
            frames, _ = source_timelines(paths[source])
            family_scripts = [s for s in bundle['scripts'] if s['path'].startswith('DefineSprite_3/')]
            families.append({'path': path, 'source_swf': source, 'source_sha256': exports[source]['source_sha256'],
                             'source_xml_sha256': exports[source]['xml_sha256'], 'parent_script': parent_script,
                             'script_bundle': bundle_path, 'script_bundle_sha256': sha(ROOT / bundle_path),
                             'initCtrl': init_ctrl, 'authored_sprite': 3, 'authored_frame_count': len(frames[3]),
                             'authored_child_depths': [sorted(frame) for frame in frames[3]],
                             'sprite_scripts': family_scripts, 'observations': records})
        results.append({'slice': slice_id, 'raw_archive_sha256': sha(base / 'native-capture.log.gz'),
                        'display_archive_sha256': sha(base / 'display.json.gz'),
                        'build_metadata_sha256': sha(base / 'native-build.json'),
                        'configuration': metadata['configuration'], 'raw_capture_validation_exit': 0,
                        'structure_exit': 0, 'sample_count': len(samples),
                        'recomputed_report_matches_retained': True, 'source_gaps': gaps, 'families': families})
    return {'production_admitted': False, 'native_parity_proven': False,
            'mapping_fix_proved': False, 'new_native_capture': False, 'results': results}


if __name__ == '__main__':
    payload = (json.dumps(diagnose(), indent=2, ensure_ascii=False) + '\n').encode()
    (HERE / 'diagnosis.json.gz').write_bytes(gzip.compress(payload, mtime=0))
