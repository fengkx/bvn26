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
from compare_mode_reference import compare, FIELDS


class MoveCasesTest(unittest.TestCase):
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
