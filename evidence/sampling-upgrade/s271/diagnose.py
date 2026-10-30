"""Inventory one uninstrumented button family without inferring event execution."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import tarfile
import tempfile
import xml.etree.ElementTree as ET

from tools.sampling_doaction import check_inventory, collect, require_full_coverage
from tools.sampling_native import validate_capture

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PREFIX = 'DefineButton2_2009/'
MEMBER = 'bvn-s30-source/main.xml'


def check_hash(data, expected):
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError('locked input hash mismatch')


def select_family(records, scripts):
    family = [r for r in records if r['swf'] == 'game/main.swf' and r['path'].startswith(PREFIX)]
    if [r['path'] for r in family] != [PREFIX + 'BUTTONCONDACTION on(keyPress Enter).as',
                                     PREFIX + 'BUTTONCONDACTION on(release).as']:
        raise ValueError('missing or changed button family')
    for record in family:
        if record['instrumented'] or record['kind'] != 'other_action':
            raise ValueError('button family unexpectedly instrumented')
        check_hash(scripts[record['path']].encode(), record['source_sha256'])
    return [dict(r, source=scripts[r['path']]) for r in family]


def timeline(tags):
    frames, current = [], []
    for tag in tags:
        if tag.get('type') == 'ShowFrameTag':
            frames.append(current)
            current = []
        else:
            current.append(dict(tag.attrib))
    return frames


def source_inventory(xml, scripts):
    button = next(e for e in xml.iter('item') if e.get('buttonId') == '2009')
    sprite = next(e for e in xml.iter('item') if e.get('spriteId') == '2010')
    frames = timeline(sprite.find('subTags'))
    if len(frames) != 10:
        raise ValueError('changed menu timeline')
    placements = []
    for owner in [xml] + list(xml.iter('item')):
        tags = owner.find('tags') if owner is xml else owner.find('subTags')
        if tags is None:
            continue
        for frame, items in enumerate(timeline(tags), 1):
            for tag in items:
                if tag.get('characterId') in ('2009', '2010'):
                    placements.append({'owner': owner.get('spriteId', 'root'), 'frame': frame, **tag})
    actual = {(p['owner'], p['frame'], p['characterId'], p['depth'], p['placeFlagMove']) for p in placements}
    if actual != {('root', 56, '2010', '157', 'false'), ('2010', 10, '2009', '5', 'false')}:
        raise ValueError('changed authored placement chain')
    listener_path = 'DefineSprite_1991/frame_1/DoAction.as'
    listener = scripts[listener_path]
    listener = listener[listener.index('var _kn = 0;'):]
    paths = [p for p in scripts if p.startswith('DefineSprite_2010/') or 'PlaceObject2_2010_157/' in p]
    return {'button_definition_xml': ET.tostring(button, encoding='unicode'),
            'placements': placements,
            'menu_frames': [{'frame': i, 'tags': tags,
                             'scripts': {p: s for p, s in scripts.items()
                                         if p.startswith(f'DefineSprite_2010/frame_{i}/')}}
                            for i, tags in enumerate(frames, 1)],
            'load_and_frame_scripts': {p: scripts[p] for p in paths},
            'menu_key_listener': {'path': listener_path, 'source_suffix': listener}}


def diagnose():
    pins = json.loads((HERE / 'input-sha256.json').read_text())
    for path, expected in pins.items():
        check_hash((ROOT / path).read_bytes(), expected)
    old = HERE.parent / 's263'
    metadata = json.loads((old / 'native-build.json').read_text())
    receipt = json.loads((old / 'native-receipt.json').read_text())
    for path, expected in metadata['sources_sha256'].items():
        check_hash((ROOT / path).read_bytes(), expected)
    records = check_inventory(metadata)
    raw = gzip.decompress((old / 'native-capture.log.gz').read_bytes())
    check_hash(raw, receipt['files'][receipt['trace']])
    with tempfile.TemporaryDirectory() as directory:
        trace = Path(directory) / 'native.log'
        trace.write_bytes(raw)
        validate_capture(metadata['move_case'], metadata, trace)
    coverage = collect(raw.decode().splitlines(), metadata['run_id'], metadata['move_case']['frames'], records)
    historical = json.load(gzip.open(old / 'full_as.json.gz', 'rt'))
    if any(coverage[key] != historical[key] for key in coverage):
        raise ValueError('recomputed coverage differs from locked report')
    scripts = {s['path']: s['source'] for s in json.loads((ROOT / 'scripts/main.json').read_text())['scripts']}
    family = select_family(coverage['uninstrumented'], scripts)
    with tarfile.open(HERE.parent / 's30/source-exports.tar.gz') as archive:
        xml_bytes = archive.extractfile(MEMBER).read()
    export = json.loads((HERE.parent / 's30/source-exports.json').read_text())['game/main.swf']
    check_hash(xml_bytes, export['xml_sha256'])
    check_hash((ROOT / 'game/main.swf').read_bytes(), export['source_sha256'])
    xml = ET.fromstring(xml_bytes)
    source = source_inventory(xml, scripts)
    continuation = json.loads((HERE.parent / 's266/diagnosis.json').read_text())
    if continuation['exit_model_fix_proved'] or continuation['executed_pc_trace']:
        raise ValueError('changed continuation prerequisite')
    try:
        require_full_coverage(coverage)
    except ValueError as error:
        full_as_error = str(error)
    else:
        raise ValueError('strict full AS gate unexpectedly admitted')
    return {'scope': 'AFTER-s263 rank 8 only', 'base': '8cf880db',
            'production_admitted': False, 'native_parity_proven': False,
            'thin_coverage_cut_proved': False, 'product_obligations_closed': 0,
            'family': family, 'source': source,
            'xml_member': MEMBER, 'xml_member_sha256': hashlib.sha256(xml_bytes).hexdigest(),
            'raw_capture_structure_exit': 0, 'events': len(raw.decode().splitlines()),
            'root_samples': len(coverage['samples']), 'unvisited': len(coverage['unvisited']),
            'uninstrumented': len(coverage['uninstrumented']),
            'strict_full_as_exit': 1, 'strict_full_as_error': full_as_error,
            'case': metadata['move_case'], 'input_injection': metadata['input_injection'],
            'button_dispatch_observed': None, 'button_return_observed': None,
            'continuation_context': {k: continuation[k] for k in (
                'exit_model_fix_proved', 'executed_pc_trace',
                'authored_retained_register_write_observed', 'authored_removed_register_write_observed')},
            'missing': ['Native menu visibility/frame and button placement lifetime at dispatch',
                        'Actual Enter/release event and source-bound BUTTONCONDACTION entry',
                        'Executed target/continuation across gotoAndStop(1), which can remove the button'],
            'next_discriminator': [
                'Use a separate native UI-input case; preserve the s76 combat tape and s263 baseline.',
                'Observe the existing Sprite1991 onKeyUp menu-enabled guard, visibility, selection and play branch. Reach game_menu frame10 naturally; do not force its frame or call the button handler.',
                'For this button only, correlate native Enter dispatch and separately mouse press/release with its actual placement, owning menu frame and exact handler entry. Keep no-dispatch and frame1/no-button controls. Record Key listener and button dispatch order rather than assuming it.',
                'Observe the owner frame1 boundary and slot removal independently. Entry or a target frame change proves no handler return. Exact continuation requires executed-PC/activation evidence or a separately proved equivalent facility; never synthesize after-events.',
                'First prove a bounded entry probe preserves source behavior and event ordering. Missing dispatch/lifetime/continuation evidence leaves full AS coverage false.'],
            'new_builds': 0, 'new_player_launches': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--require-thin-coverage', action='store_true')
    parser.add_argument('--require-full-as', action='store_true')
    args = parser.parse_args()
    report = diagnose()
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    if args.require_full_as:
        parser.exit(1, report['strict_full_as_error'] + '\n')
    if args.require_thin_coverage:
        parser.exit(1, 'Unproved button dispatch/lifetime/continuation; no coverage cut admitted\n')
    print('s271 source inventory verified; no coverage obligation closed')


if __name__ == '__main__':
    main()
