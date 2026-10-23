"""The acceptance harness must reject incomplete or unexercised evidence."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

PROBES=Path(__file__).resolve().parents[1]/'probes'
sys.path.insert(0,str(PROBES))
sys.path.insert(0, str(PROBES.parent))
from move_cases import generate, source_fixture, encode_case, encode_resource_interventions, source_state_preconditions, KEYS
from compare_mode_reference import (compare, FIELDS, cancellation_observation,
                                    validate_probe_provenance)
from cancel_cases import apply_source_target, same_window_route
from test_move_cases import validate_timer_contract


class MoveCasesTest(unittest.TestCase):
    def test_batch_rejects_source_timer_requirement_when_field_is_dropped(self):
        fixture = {
            'id': 'timer-contract',
            'source_build': str(Path(__file__).resolve().parents[2] /
                                'evidence/characters/lee/original/'
                                'lee-574-bisha-625-dead-clean-r01/parsed/build.json'),
            'drive_source_timers': False,
        }
        with self.assertRaisesRegex(ValueError, 'source_timer_required'):
            validate_timer_contract(fixture)

    def test_batch_validates_before_starting_godot(self):
        from test_move_cases import execute_batch
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            case = root / 'case.json'
            case.write_text(json.dumps({
                'id': 'timer-contract-before-run',
                'source_build': str(Path(__file__).resolve().parents[2] /
                                    'evidence/characters/lee/original/'
                                    'lee-574-bisha-625-dead-clean-r01/parsed/build.json'),
                'drive_source_timers': False,
            }))
            output = root / 'out'
            output.mkdir()
            with patch('test_move_cases.subprocess.run') as run:
                with self.assertRaisesRegex(ValueError, 'source_timer_required'):
                    execute_batch(Path('/tmp/godot'), [case], output)
                run.assert_not_called()

    def test_ai_provenance_discovers_legacy_build_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build_dir = root / 'build'
            build_dir.mkdir()
            events = build_dir / 'events.gz'
            events.write_bytes(b'')
            metadata = build_dir / 'build.json'
            metadata.write_text(json.dumps({'configuration': {}}))
            result = validate_probe_provenance(events)
            self.assertEqual(result['status'], 'unknown')
            self.assertEqual(Path(result['source_build']), metadata)

    def test_ai_provenance_missing_source_is_unknown(self):
        with tempfile.TemporaryDirectory() as tmp:
            events = Path(tmp) / 'events.jsonl'
            events.write_text('')
            result = validate_probe_provenance(events)
            self.assertEqual(result['status'], 'unknown')
            self.assertIsNone(result['source_build'])

    def test_ai_provenance_explicit_missing_source_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            events = Path(tmp) / 'events.jsonl'
            events.write_text('')
            with self.assertRaises(FileNotFoundError):
                validate_probe_provenance(events, source_build=Path(tmp) / 'missing.json')

    def test_ai_provenance_intervention_is_experimental(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            events = root / 'events.jsonl'
            events.write_text('')
            metadata = root / 'native-build.json'
            metadata.write_text(json.dumps({'frame_order_probe': True}))
            with self.assertRaisesRegex(ValueError, 'intervention probes'):
                validate_probe_provenance(events)
            result = validate_probe_provenance(events, allow_intervention=True)
            self.assertEqual(result['status'], 'experimental')

    def test_cancel_edge_cannot_use_an_unrelated_action_entry(self):
        window = {'start_frame': 234, 'end_frame': 247}
        self.assertFalse(same_window_route([{'frame': 4}, {'frame': 248}], 1, window))
        self.assertTrue(same_window_route([{'frame': 247}, {'frame': 248}], 1, window))

    def test_cancel_probe_requires_observed_calibration_frame(self):
        case = {'slot': 'p1', 'window_boundary': {
            'input_tick': 19, 'source_frame': 194, 'destination_frames': [206, 225]}}
        rows = [{'slot': 'p1', 'tick': 19, 'frame': 194},
                {'slot': 'p1', 'tick': 20, 'frame': 206}]
        result = cancellation_observation(rows, case)
        self.assertEqual(result['status'], 'calibrated')
        self.assertEqual(result['destination_first_observed_tick'], 20)
        rows[0]['frame'] = 193
        self.assertEqual(cancellation_observation(rows, case)['status'], 'invalid_calibration')

    def test_cancel_fixture_target_is_bound_to_window_source_action(self):
        case = {'label': '砍技1', 'target_frames': [309, 365],
                'source_target': {'label': '砍技1', 'start_frame': 309, 'end_frame': 365}}
        window = {'from': '防御2', 'start_frame': 867, 'end_frame': 873}
        source_action = {'label': '防御2', 'start_frame': 867, 'end_frame': 877,
                         'has_timeline': True, 'source_dispatch': ['onDefence'],
                         'contexts': ['guard'], 'energy_min': 0, 'implementation': 'wired'}
        frames = apply_source_target(case, window, source_action)
        self.assertEqual(frames, [867, 877])
        self.assertEqual(case['label'], '防御2')
        self.assertEqual(case['target_frames'], frames)
        self.assertEqual(case['source_target']['label'], '防御2')
        with self.assertRaisesRegex(ValueError, 'does not belong'):
            apply_source_target(case, {'from': '防御2', 'start_frame': 866, 'end_frame': 878}, source_action)

    def test_base_fighter_suite_explicitly_defers_transformation(self):
        cases = generate([('rifagu', 'p1')], ['wankai'])
        self.assertTrue(cases)
        self.assertTrue(all(c['fighters'] == {'p1': 'rifagu', 'p2': 'yihu'} for c in cases))
        self.assertFalse(any(c['label'] == '万解' for c in cases))
        self.assertTrue(any(c['label'] == '超必杀' and c['scenario'] == 'energy_exact' for c in cases))
        from tools.audit_move_acceptance import audit
        report = audit(cases, [], [], deferred_labels=['万解'])
        bankai = next(row for row in report['labels'] if row['label'] == '万解')
        self.assertEqual(bankai['status'], 'deferred_by_scope')
        self.assertEqual(report['status'], 'not_accepted')
        self.assertFalse(any('Form-switch' in item for item in report['additional_required_boundaries']))

    def test_every_catalog_dispatch_has_cases(self):
        cases=generate()
        self.assertEqual(len({c['id'] for c in cases}),len(cases))
        for fighter in ['minren','yihu']:
            catalog=json.loads((PROBES.parents[1]/f'godot/generated/fighters/{fighter}/combat.json').read_text())['command_catalog']
            for entry in catalog['entries']:
                if entry.get('slot'):
                    rows=[c for c in cases if c['fighter']==fighter and c['label']==entry['label']]
                    self.assertTrue(rows,entry['label'])
                    self.assertTrue(all(c['status']=='not_run' for c in rows))
                    if entry.get('energy_min'):
                        minimum=entry['energy_min']
                        for name,energy in [('energy_below',minimum-1),('energy_exact',minimum),('energy_above',minimum+1)]:
                            self.assertEqual(next(c for c in rows if c['scenario']==name)['setup'][rows[0]['slot']]['energy'],energy)

    def test_dynamic_and_static_inputs_describe_same_keys(self):
        from urllib.parse import parse_qs
        for case in generate():
            static=source_fixture(case)
            dynamic=parse_qs(encode_case(case,'test'))
            self.assertEqual(dynamic['case_id'],[case['id']])
            for item in case['inputs']:
                for key in item['keys']:
                    name=KEYS[item['slot']][key]
                    self.assertIn(f'aiHeld[{name}] = true',static)
                    self.assertIn(f'{item["start"]}:{item["end"]}:{name}',dynamic['windows'][0])

    def test_controlled_resource_intervention_is_opt_in_and_same_tick(self):
        base = generate([('sakura', 'p1')], ['wankai'])[0]
        ordinary_encoding = encode_case(base, 'test')
        ordinary_fixture = source_fixture(base)
        case = dict(base)
        case['resource_interventions'] = [{
            'id': 'sakura-overlap-refill', 'tick': 55, 'slot': 'p1',
            'resource': 'energy', 'value': 300,
        }]
        query = encode_case(case, 'test')
        self.assertIn('resource_interventions=55%3Ap1%3Aenergy%3A300%3Asakura-overlap-refill', query)
        self.assertEqual(query.replace('&resource_interventions=55%3Ap1%3Aenergy%3A300%3Asakura-overlap-refill', ''),
                         ordinary_encoding)
        self.assertIn('if(aiFight == 55)', source_fixture(case))
        self.assertNotIn('resource_intervention', ordinary_fixture)
        self.assertEqual(encode_resource_interventions(case), '55:p1:energy:300:sakura-overlap-refill')

    def test_source_state_preconditions_are_applied_before_first_frame(self):
        case = generate([('lee', 'p1')], ['wankai'])[0]
        case['source_state_preconditions'] = {
            'p1': {'health': 301, 'wudi': False},
            'p2': {'health': 1000, 'wudi': True},
        }
        static = source_fixture(case)
        self.assertIn('_root.game.p1.mc.hp = 301.0;', static)
        self.assertIn('_root.game.p1.mc.wudi = false;', static)
        self.assertIn('source_state_precondition', static)
        self.assertEqual(source_state_preconditions(case)['p1']['health'], 301)
        with self.assertRaisesRegex(ValueError, 'unsupported source state'):
            source_state_preconditions({'source_state_preconditions': {'p1': {'hp': 1}}})

    def test_resource_interventions_reject_ambiguous_or_unsupported_fields(self):
        case = generate([('sakura', 'p1')], ['wankai'])[0]
        case['resource_interventions'] = [
            {'id': 'same', 'tick': 55, 'slot': 'p1', 'resource': 'energy', 'value': 300},
            {'id': 'same', 'tick': 60, 'slot': 'p1', 'resource': 'energy', 'value': 300},
        ]
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            encode_case(case, 'test')
        case['resource_interventions'] = [
            {'id': 'hp', 'tick': 55, 'slot': 'p1', 'resource': 'health', 'value': 300},
        ]
        with self.assertRaisesRegex(ValueError, 'only p1/p2 energy'):
            encode_case(case, 'test')

    def test_conditional_jump_cannot_be_silently_dropped(self):
        compiler_path = PROBES.parent / 'importer/compile_ai_context.py'
        spec = importlib.util.spec_from_file_location('context_for_acceptance_test', compiler_path)
        compiler = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(compiler)
        root = PROBES.parents[1]
        bundle = json.loads((root / 'scripts/fighter/minren.json').read_text())
        timeline = json.loads((root / 'data/slices/minren-base.timeline.json').read_text())
        with self.assertRaisesRegex(ValueError, r'minren.swf.*frame_1379.*uncompiled wrapper transfer'):
            compiler.compile_context(bundle, timeline)
        # This unit checks frame 538, not the unsupported parent transformation.
        timeline = {**timeline, 'frames': [f for f in timeline['frames'] if f['frame'] in (1, 538)]}
        compiled = compiler.compile_context(bundle, timeline)
        event = compiled['frame_calls']['538'][0]
        self.assertEqual(event['conditions'], [
            {'field':'opponent_hp','operator':'gt','value':0},
            {'field':'opponent_action','operator':'eq','value':-1}])
        self.assertEqual(event['calls'], [
            {'op':'timeline_goto','label':'必杀1','play':False}, {'op':'timeline_play'}])
        script = next(s for s in bundle['scripts'] if s['path']=='DefineSprite_764/frame_538/DoAction.as')
        script['source'] = script['source'].replace(' && ', ' || ')
        with self.assertRaisesRegex(ValueError, 'Uncompiled conditional frame jump'):
            compiler.compile_context(bundle, timeline)

    def test_transform_start_keeps_second_cost_and_pause_order(self):
        compiler_path = PROBES.parent / 'importer/compile_ai_context.py'
        spec = importlib.util.spec_from_file_location('context_transform_test', compiler_path)
        compiler = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(compiler)
        bundle = json.loads((PROBES.parents[1] / 'scripts/fighter/yihu.json').read_text())
        timeline = json.loads((PROBES.parents[1] / 'data/slices/yihu-base.timeline.json').read_text())
        with self.assertRaisesRegex(ValueError, r'yihu.swf.*frame_1052.*uncompiled form replacement call'):
            compiler.compile_context(bundle, timeline)
        # Keep the preparation FIFO unit separate from the rejected form switch.
        timeline = {**timeline, 'frames': [f for f in timeline['frames'] if f['frame'] in (1, 967)]}
        frame = compiler.compile_context(bundle, timeline)['frame_calls']['967']
        calls = frame[0]['calls']
        self.assertEqual([(c['field_name'], c['operator'], c['value']) for c in calls[:4]],
                         [('动作', '=', 3), ('bs', '=', 1), ('ql', '-=', 300), ('jump', '=', 1)])
        self.assertEqual(calls[4]['kind'], 'cbsd')
        self.assertEqual(frame[1]['op'], 'show_face')
        with self.assertRaisesRegex(ValueError, 'Uncompiled frame function statement'):
            compiler.inline_frame_function('function test() { ql *= 2; }', 'synthetic', 1)

    def test_empty_reference_is_not_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            events=Path(directory)/'events';native=Path(directory)/'native'
            events.write_text('');native.write_text('[]')
            self.assertEqual(compare(events,native)['status'],'different')

    def test_missing_tail_is_not_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            events=Path(directory)/'events';native=Path(directory)/'native'
            event={'kind':'state','fight_tick':0,'value':'p1,'+','.join(['0']*len(FIELDS))}
            events.write_text(json.dumps(event)+'\n');native.write_text('[]')
            self.assertFalse(compare(events,native)['complete'])


if __name__=='__main__':unittest.main()
