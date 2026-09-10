"""The acceptance harness must reject incomplete or unexercised evidence."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

PROBES=Path(__file__).resolve().parents[1]/'probes'
sys.path.insert(0,str(PROBES))
from move_cases import generate, source_fixture, encode_case, KEYS
from compare_mode_reference import compare, FIELDS, cancellation_observation
from cancel_cases import same_window_route


class MoveCasesTest(unittest.TestCase):
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

    def test_conditional_jump_cannot_be_silently_dropped(self):
        compiler_path = PROBES.parent / 'importer/compile_ai_context.py'
        spec = importlib.util.spec_from_file_location('context_for_acceptance_test', compiler_path)
        compiler = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(compiler)
        root = PROBES.parents[1]
        bundle = json.loads((root / 'scripts/fighter/minren.json').read_text())
        timeline = json.loads((root / 'data/slices/minren-base.timeline.json').read_text())
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
