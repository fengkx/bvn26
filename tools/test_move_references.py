"""Run fresh native Flash fights and compare every observed state exactly.

The dynamic probe is analysis-only. Its fixed instrumented SWFs are reused;
each run retains its external fixture, build metadata, input tape and trace.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).parent / 'probes'))
from move_cases import encode_case
from compare_mode_reference import compare, source_rows, compare_root_position, cancellation_observation

ROOT = Path(__file__).resolve().parents[1]


def resolve_fixture_directory(fixture_id, directories):
    matches = [path for path in directories
               if path.is_dir() and path.name.casefold() == fixture_id.casefold()]
    if len(matches) != 1:
        raise ValueError(f'Unknown or ambiguous fixture fighter directory: {fixture_id}')
    return matches[0]


def resolve_fixture_character(fixture_id, catalog, fighters_root=None):
    """Resolve a normalized generated role directory to its exact source role."""
    fighters_root = fighters_root or ROOT / 'godot/generated/fighters'
    directory = resolve_fixture_directory(fixture_id, fighters_root.iterdir())
    fighter = json.loads((directory / 'fighter.json').read_text())
    character_id = fighter.get('fighter_id')
    if not character_id or character_id not in catalog:
        raise ValueError(f'Fixture fighter has no manifest role: {directory.name}')
    record = catalog[character_id]
    source = fighter.get('source', {})
    source_path = source.get('swf_path', '')
    source_hash = source.get('swf_sha256', '')
    expected_path = 'game/fighter/' + record.get('url', '')
    manifest_hash = json.loads((ROOT / 'manifest.json').read_text()).get('file_sha256', {}).get(source_path)
    if source_path != expected_path or not source_hash or manifest_hash != source_hash:
        raise ValueError(f'Fixture source identity differs from manifest: {directory.name}')
    return character_id


def resolve_fixture_helper(selection, catalog):
    """Resolve a helper id or SWF stem to its exact manifest source identity."""
    if selection in catalog and catalog[selection].get('fzurl'):
        character_id = selection
    else:
        matches = [character_id for character_id, record in catalog.items()
                   if record.get('fzurl') and Path(record['fzurl']).stem == selection]
        if len(matches) != 1:
            raise ValueError(f'Unknown or ambiguous fixture helper source: {selection}')
        character_id = matches[0]
    source_path = 'game/fighter/fz/' + catalog[character_id]['fzurl']
    manifest = json.loads((ROOT / 'manifest.json').read_text())
    source_hash = manifest.get('file_sha256', {}).get(source_path)
    if not source_hash or hashlib.sha256((ROOT / source_path).read_bytes()).hexdigest() != source_hash:
        raise ValueError(f'Fixture helper source identity differs from manifest: {source_path}')
    return {'id': character_id, 'swf': source_path, 'sha256': source_hash}


def assert_fixture_helper_configuration(case, template, catalog):
    """Reject source/port comparisons whose selected helper SWFs differ."""
    defaults = {'p1': '我爱罗', 'p2': '魂'}
    configuration = template.get('configuration', {})
    probe_case = template.get('move_case', {})
    for slot in ('p1', 'p2'):
        original_selection = (template.get(slot + '_helper') or
                              probe_case.get(slot + '_helper') or
                              configuration.get(slot + 'sf'))
        fixture_selection = case.get(slot + '_helper') or defaults[slot]
        if not original_selection:
            raise ValueError(f'Original probe has no selected helper for {slot}')
        original = resolve_fixture_helper(original_selection, catalog)
        fixture = resolve_fixture_helper(fixture_selection, catalog)
        if (fixture['id'], fixture['swf']) != (original['id'], original['swf']):
            raise ValueError(
                f'Fixture/probe helper mismatch: {slot} '
                f'{fixture_selection} resolves to {fixture["swf"]}, '
                f'original {original_selection} resolves to {original["swf"]}'
            )
        declared = case.get('source_helpers', {}).get(slot)
        if declared is not None and (declared.get('id'), declared.get('swf'), declared.get('sha256')) != (
                fixture['id'], fixture['swf'], fixture['sha256']):
            raise ValueError(f'Fixture helper metadata mismatch: {slot}')


def assert_capture_identity(case, template, fixture, probe, manifest):
    """Reject a malformed capture before it can launch the original player."""
    encoded = parse_qs(fixture, strict_parsing=True)
    if template.get('run_id') != encoded.get('run_id', [None])[0]:
        raise ValueError('Capture build/fixture run_id mismatch')
    if case.get('id') != encoded.get('case_id', [None])[0]:
        raise ValueError('Capture build/fixture case_id mismatch')
    if int(case.get('frames', -1)) != int(template.get('frames_after_ready', -2)):
        raise ValueError('Capture fixture/build frame count mismatch')
    if template.get('move_case') != case:
        raise ValueError('Capture build/fixture move_case mismatch')
    instrumentation = (probe / 'instrumentation.diff').read_text()
    urls = re.findall(r'_root\.aiFixtureLoader\.load\("(file://[^"\\]+)"\)', instrumentation)
    if len(urls) != 1:
        raise ValueError('Capture SWF must contain exactly one recorded LoadVars fixture URL')
    embedded_fixture_url = urls[0]
    embedded_fixture_path = Path(urlparse(embedded_fixture_url).path).resolve()
    probe_fixture_path = (probe / 'case.txt').resolve()
    if embedded_fixture_path != probe_fixture_path:
        raise ValueError(
            f'Capture SWF LoadVars URL binds {embedded_fixture_path}, '
            f'but this run writes {probe_fixture_path}'
        )
    if template.get('fixture_url') and template['fixture_url'] != embedded_fixture_url:
        raise ValueError('Capture build/embedded SWF fixture URL mismatch')
    expected_fixture = encode_case(case, str(template['run_id']))
    if fixture != expected_fixture:
        raise ValueError('Capture LoadVars URL differs from the selected case')
    if template.get('fixture_sha256') and hashlib.sha256(fixture.encode()).hexdigest() != template['fixture_sha256']:
        raise ValueError('Capture build/fixture URL hash mismatch')
    for slot, setup in case['setup'].items():
        for suffix, expected in [('x', setup['x']), ('energy', setup['energy'])]:
            key = slot + suffix
            values = encoded.get(key, [])
            if len(values) != 1 or float(values[0]) != float(expected):
                raise ValueError(f'Capture fixture setup mismatch: {key}')
    source_hashes = template.get('sources_sha256', {})
    locked_hashes = manifest.get('file_sha256', {})
    for source_path, source_hash in source_hashes.items():
        if locked_hashes.get(source_path) != source_hash:
            raise ValueError(f'Capture source hash/manifest mismatch: {source_path}')
        source_file = ROOT / source_path
        if not source_file.is_file() or hashlib.sha256(source_file.read_bytes()).hexdigest() != source_hash:
            raise ValueError(f'Capture source differs from locked input: {source_path}')
    for output_path, output_hash in template.get('outputs_sha256', {}).items():
        output_file = probe / output_path
        if not output_file.is_file() or hashlib.sha256(output_file.read_bytes()).hexdigest() != output_hash:
            raise ValueError(f'Capture build output hash mismatch: {output_path}')
    instrumentation = probe / 'instrumentation.diff'
    if hashlib.sha256(instrumentation.read_bytes()).hexdigest() != template.get('instrumentation_sha256'):
        raise ValueError('Capture instrumentation hash mismatch')
    if int(template.get('move_case', {}).get('frames', -1)) != int(case['frames']):
        raise ValueError('Capture embedded move_case frame count mismatch')
    helper_sources = template.get('helper_sources', {})
    defaults = {'p1': '我爱罗', 'p2': '魂'}
    for slot in ('p1', 'p2'):
        selection = case.get(slot + '_helper') or defaults[slot]
        resolved = resolve_fixture_helper(selection, manifest['fighter_catalog'])
        declared = helper_sources.get(slot, {})
        if (declared.get('character_id') != resolved['id'] or
                declared.get('url') != Path(resolved['swf']).name or
                declared.get('asset') != Path(resolved['swf']).stem):
            raise ValueError(f'Capture build/helper source mismatch: {slot}')


def capture_template_for_case(template, run_id, case, fixture):
    """Bind metadata to the exact per-case LoadVars payload being written."""
    return dict(template, run_id=run_id, move_case=case,
                fixture_sha256=hashlib.sha256(fixture.encode()).hexdigest())


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    from capture_native_player import APP, preflight
    parser.add_argument('--probe',type=Path,required=True)
    parser.add_argument('--cases',type=Path,required=True)
    parser.add_argument('--native',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--capture-runner',type=Path,required=True)
    parser.add_argument('--scenario',action='append')
    parser.add_argument('--case-id',action='append', help='Capture only these exact case ids')
    parser.add_argument('--limit',type=int)
    parser.add_argument('--capture-only', action='store_true',
                        help='Capture original traces without comparing to a prior native baseline')
    parser.add_argument('--allow-window-activation', action='store_true',
                        help='Explicitly allow native Flash to raise windows')
    parser.add_argument('--player-app', type=Path, default=APP,
                        help='Standalone Flash Player Debugger app bundle')
    args=parser.parse_args()
    if not args.allow_window_activation:
        parser.error('Flash sampling is disabled: the player can raise windows despite background launch')
    for name in ('probe', 'cases', 'native', 'output', 'capture_runner', 'player_app'):
        setattr(args, name, getattr(args, name).resolve())
    preflight(args.player_app)
    template=json.loads((args.probe/'build.json').read_text())
    if not template.get('dynamic_move_case'): raise ValueError('Dynamic fixture probe required')
    args.output.mkdir(parents=True,exist_ok=True)
    cases=[json.loads(p.read_text()) for p in sorted(args.cases.glob('*.json'))]
    cases=[c for c in cases if not args.scenario or c['scenario'] in args.scenario]
    if args.case_id:
        selected = set(args.case_id)
        cases = [c for c in cases if c['id'] in selected]
        if {c['id'] for c in cases} != selected:
            raise ValueError('One or more requested case ids were not found')
    if args.limit: cases=cases[:args.limit]
    manifest = json.loads((ROOT / 'manifest.json').read_text())
    catalog = manifest['fighter_catalog']
    for case in cases:
        assert_fixture_helper_configuration(case, template, catalog)
    results=[]
    for index,case in enumerate(cases):
        if 'fighters' in case:
            for slot, fighter in case['fighters'].items():
                selected = template['configuration'][slot]
                if resolve_fixture_character(fighter, catalog) != selected:
                    raise ValueError(f'Fixture/probe fighter mismatch: {slot} {fighter} != {selected}')
        folder=args.output/case['id']
        if folder.exists(): raise ValueError(f'Reference must not be overwritten: {folder}')
        scratch=args.output/('build-'+case['id']);scratch.mkdir()
        run_tag = hashlib.sha256(str(args.output.resolve()).encode()).hexdigest()[:10]
        run_id='moves-'+case['id']+'-'+run_tag
        fixture=encode_case(case,run_id)
        capture_template = capture_template_for_case(template, run_id, case, fixture)
        assert_capture_identity(case, capture_template, fixture, args.probe, manifest)
        for fixture_path in (args.probe/'case.txt', scratch/'case.txt'):
            fixture_path.write_text(fixture)
            if hashlib.sha256(fixture_path.read_bytes()).hexdigest() != capture_template['fixture_sha256']:
                raise ValueError(f'Written LoadVars fixture differs from capture metadata: {fixture_path}')
        (scratch/'game').symlink_to((args.probe/'game').resolve(),target_is_directory=True)
        (scratch/'instrumentation.diff').write_bytes((args.probe/'instrumentation.diff').read_bytes())
        build=dict(capture_template,fixture_sha256=hashlib.sha256(fixture.encode()).hexdigest())
        (scratch/'build.json').write_text(json.dumps(build,ensure_ascii=False,indent=2)+'\n')
        capture=scratch/'original.log'
        commands=[
            [sys.executable,str(args.capture_runner),str(scratch),str(capture),
             '--player-app',str(args.player_app),'--allow-window-activation'],
            [sys.executable,str(ROOT/'tools/probes/collect_ai_reference.py'),'--build',str(scratch),'--capture',str(capture),'--output',str(folder),'--retain-post-done-frames'],
        ]
        failure=None
        for command in commands:
            # Lock waiting is not player execution time. The capture runner starts
            # its own deadline only after acquiring the account-wide log lock.
            timeout = None if command == commands[0] else 150
            run=subprocess.run(command,capture_output=True,text=True,timeout=timeout)
            (scratch/('capture.log' if command==commands[0] else 'collect.log')).write_text(run.stdout+run.stderr)
            if run.returncode:
                failure=run.stdout+run.stderr
                break
        if failure:
            result={'id':case['id'],'status':'capture_failed','detail':failure[-2000:]}
        elif args.capture_only:
            captured_rows = source_rows(folder/'events.jsonl')
            (folder/'native.json').write_text(json.dumps(captured_rows, separators=(',', ':')) + '\n')
            frames=case['target_frames']
            seen=any(r['slot']==case['slot'] and frames[0] is not None and frames[0]<=r['frame']<=frames[1]
                     for r in captured_rows)
            result={'id':case['id'],'status':'captured_source_only','source_states':len(captured_rows),
                    'source_target_seen':seen,'run_id':run_id}
            (folder/'capture-summary.json').write_text(json.dumps(result,indent=2)+'\n')
        else:
            (folder/'case.txt').write_text(fixture)
            (folder/'case.json').write_text(json.dumps(case,ensure_ascii=False,indent=2)+'\n')
            native=args.native/(case['id']+'.json')
            (folder/'native.json').write_bytes(native.read_bytes())
            result=compare(folder/'events.jsonl',folder/'native.json')
            if template.get('presentation_probe'):
                presentation = folder / 'native.presentation.json'
                presentation.write_bytes(Path(str(native) + '.presentation.json').read_bytes())
                root_result = compare_root_position(folder/'events.jsonl', presentation)
                (folder/'root-position-comparison.json').write_text(json.dumps(root_result, indent=2)+'\n')
                result['root_position'] = root_result['status']
                if root_result['status'] != 'matched':
                    result['status'] = 'different'
            frames=case['target_frames']
            rows=json.loads(native.read_text())
            result['target_seen']=any(r['slot']==case['slot'] and frames[0] is not None and frames[0]<=r['frame']<=frames[1] for r in rows)
            expected=source_rows(folder/'events.jsonl')
            if 'window_boundary' in case:
                result['cancellation'] = cancellation_observation(expected, case)
                if result['cancellation']['status'] != 'calibrated':
                    result['status'] = 'invalid_calibration'
            result['source_target_seen']=any(r['slot']==case['slot'] and frames[0] is not None and frames[0]<=r['frame']<=frames[1] for r in expected)
            if result['status']=='matched' and not result['source_target_seen'] and case['scenario']!='energy_below' and frames[0] is not None:
                result['status']='unexercised'
            result['id']=case['id']
            (folder/'comparison.json').write_text(json.dumps(result,indent=2)+'\n')
            result={k:v for k,v in result.items() if k!='differences'}|{'different_states':len(result['differences'])}
        results.append(result)
        (args.output/'results.json').write_text(json.dumps(results,indent=2)+'\n')
        print(json.dumps({'progress':f'{index+1}/{len(cases)}',**result}),flush=True)
    success_status = 'captured_source_only' if args.capture_only else 'matched'
    raise SystemExit(0 if all(r['status']==success_status for r in results) else 1)


if __name__=='__main__':main()
