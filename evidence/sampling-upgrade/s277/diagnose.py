"""Bound the s259 P1 read/request/callback gap without manufacturing live proof."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import tarfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def loader_order(source):
    source = source.replace('\r\n', '\n')
    steps = re.search(r'var loadSteps = \[(.*?)\];', source, re.S)
    if steps is None:
        raise ValueError('missing source load steps')
    calls = re.findall(r'(loadman|loadfz|loadSound)\(([^)]*)\);', steps[1])
    expected = [('loadman', '"p1"'), ('loadman', '"p2"'),
                ('loadfz', '"p1"'), ('loadfz', '"p2"'), ('loadSound', '')]
    if calls != expected:
        raise ValueError('changed source load order')
    callback = 'LO.onLoadComplete = function(target)\n{\n   loadStep++;\n   loadSteps[loadStep]();\n};'
    if callback not in source or source.count('new MovieClipLoader()') != 1:
        raise ValueError('changed shared loader/callback')
    if 'LO.onLoadInit' in source:
        raise ValueError('unexpected initialization observer')
    return {'authored_request_order': [f'{a}({b})' for a, b in calls],
            'movie_clip_loader_instances_in_script': 1,
            'completion_calls_next_step_inline': True,
            'on_load_init_listener_present': False,
            'callback_target_consumed': False,
            'actual_callback_order': None,
            'limitation': 'Source order is not an observed callback schedule. A mutable current-request field can be advanced before a later initialization event; use a qualified per-request association.'}


def diagnose():
    pins = json.loads((HERE / 'input-sha256.json').read_text())
    for path, expected in pins.items():
        if digest((ROOT / path).read_bytes()) != expected:
            raise ValueError('changed evidence: ' + path)
    spec = importlib.util.spec_from_file_location('s268_loader', HERE.parent / 's268/diagnose.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    run = module.audit_run('s259/normal')
    directory = HERE.parent / 's259/normal'
    with tarfile.open(directory / 'native-build.tar.gz') as archive:
        source = archive.extractfile('patches/main/' + module.LOADER).read().decode()
    original = next(s['source'] for s in json.loads((ROOT / 'scripts/main.json').read_text())['scripts'] if s['path'] == module.LOADER)
    order = loader_order(source)
    if order != loader_order(original):
        raise ValueError('archived/original loader order differs')
    facility = json.loads((HERE / 'facility.json').read_text())
    receipt = json.loads((directory / 'native-receipt.json').read_text())
    if facility['binary_sha256'] != receipt['files'][facility['binary']]:
        raise ValueError('facility executable differs from receipt')
    for check in facility['checks'].values():
        if digest((HERE / check['log']).read_bytes()) != check['sha256']:
            raise ValueError('changed facility transcript')
    imports = set((HERE / 'imports.txt').read_text().splitlines())
    candidates = sorted(imports & {'_read', '_fread', '_mmap', '_open', '_fopen',
                                  '_CFReadStreamRead', '_CFReadStreamCreateWithFile',
                                  '_CFReadStreamCreateForHTTPRequest'})
    if not candidates:
        raise ValueError('no retained candidate read imports')
    return {'scope': 'AFTER-s272 rank 5 only', 'base': 'bab9d85693b5a4343dc20f7f8a7ce7f88e4e20a8',
            'production_admitted': False, 'native_parity_proven': False,
            'loader_attestation_proved': False, 'product_obligations_closed': 0,
            'historical_normal': run, 'source_loader_order': order,
            'native_read_import_candidates': candidates,
            'facility': facility,
            'independent_read_request_callback_observation': None,
            'actual_wrong_resource_load_control': None,
            'bounded_target_lifetime': None,
            'new_builds': 0, 'new_player_launches': 0,
            'missing': ['native returned-byte buffer to loader request association',
                        'same-request callback target observation',
                        'actual Yihu-for-Yijiao load with expected Yijiao identity unchanged',
                        'callback target initialization/use/unload or replacement boundary'],
            'next_discriminator': 'Resolve one actual P1 read-return call chain (including buffering/mmap if used), retain returned bytes and request identity through complete/init callbacks before inline loadStep advance; qualify with a real wrong-resource run and target end-of-lifetime observations. Imported APIs and transport delivery alone do not establish loader consumption.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--require-loader-attestation', action='store_true')
    args = parser.parse_args()
    report = diagnose()
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    if args.require_loader_attestation:
        print('S277_LOADER_ATTESTATION_UNPROVED: ' + '; '.join(report['missing']))
        return 1
    print('S277_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
