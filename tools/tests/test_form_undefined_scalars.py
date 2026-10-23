"""Candidate form fields retain source undefined/AVM1 comparison semantics."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/importer'))
from compile_ai_context import compile_context, controller_scope_fields, implicit_controller_fields, writes
from compile_ai_controller import source_expression, compile_body
from compile_ai_predicates import expression


class FormUndefinedScalarTests(unittest.TestCase):
    def test_generated_callback_fixture_matches_current_source_and_compiler(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location('missing_form_fixture', ROOT / 'tools/probes/build_missing_form_fields_fixture.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.build(), (ROOT / 'godot/tests/fixtures/missing_form_fields.gd').read_text())

    def test_locked_sources_expose_missing_fields_only_for_candidate_forms(self):
        for name, sprite, field in [('Sasuke', 1019, 'khitn'), ('yihu', 1180, 'nn')]:
            bundle = json.loads((ROOT / f'scripts/fighter/{name}.json').read_text())
            self.assertNotIn(field, controller_scope_fields(bundle, sprite))
            self.assertIn(field, controller_scope_fields(bundle, sprite, form_replacement=True))
            self.assertEqual(implicit_controller_fields(bundle, sprite), {field})
        bundle = json.loads((ROOT / 'scripts/fighter/Sasuke.json').read_text())
        source = next(row['source'] for row in bundle['scripts']
                      if row['path'] == 'DefineSprite_1019/frame_128/DoAction.as')
        events = writes(source, 'DefineSprite_1019/frame_128/DoAction.as', controller_scope_fields={'khitn'})
        self.assertEqual(events[-1]['op'], 'increment')
        self.assertNotIn('value', events[-1])

    def test_candidate_context_allocates_undefined_not_zero(self):
        # A deliberately partial timeline fixture isolates declaration emission;
        # complete target compilation is recorded separately in r12 evidence.
        for name, sprite, field in [('Sasuke', 1019, 'khitn'), ('yihu', 1180, 'nn')]:
            bundle = json.loads((ROOT / f'scripts/fighter/{name}.json').read_text())
            timeline = {'sprite_id': sprite,
                        'source_swf': {'path': bundle['game_file'], 'sha256': bundle['swf_sha256']},
                        'frames': [{'frame': 1, 'display_list': [{'name': 'AImain', 'character_id': -1}]},
                                   {'frame': 128, 'display_list': []}],
                        'definitions': [{'character_id': -1, 'frame_count': 2, 'display_list_frames': [[], []]}]}
            context = compile_context(bundle, timeline, form_replacement=True)
            self.assertIn(field, context['undefined_declarations'])
            self.assertFalse(any(event.get('field') == field and 'value' in event
                                 for events in context['frame_writes'].values() for event in events))
            if field == 'khitn':
                self.assertEqual(context['frame_writes']['128'][-1]['op'], 'increment')

    def test_candidate_scope_does_not_admit_arbitrary_parent_objects_or_calls(self):
        bundle = {'scripts': [
            {'path': 'DefineSprite_1/frame_1/DoAction.as', 'source': 'var known;'},
            {'path': 'DefineSprite_1/frame_2/PlaceObject2_3_4/CLIPACTIONRECORD onClipEvent(enterFrame).as',
             'source': 'if(_parent.scalar >= 1) {}\n_parent.object.method();\nif(_parent._x > 0) {}'},
            {'path': 'DefineSprite_1/frame_2/DoAction.as', 'source': 'if(_parent.wrapper > 0) {}'},
        ]}
        self.assertEqual(implicit_controller_fields(bundle, 1), {'scalar'})
        with self.assertRaisesRegex(ValueError, 'Unsupported AI expression'):
            source_expression('_parent.object', set(), {'scalar'}, avm1_comparisons=True)
        with self.assertRaisesRegex(ValueError, 'Unsupported AI expression'):
            source_expression('_parent.scalar >= 1', set(), set())

    def test_candidate_relations_keep_less2_unordered_value_and_not_lowering(self):
        self.assertIn('source_less2(value("nn"), 1)',
                      source_expression('_parent.nn >= 1', set(), {'nn'}, avm1_comparisons=True))
        self.assertIn('not truth(source_less2(value("nn"), 1))',
                      source_expression('_parent.nn >= 1', set(), {'nn'}, avm1_comparisons=True))
        self.assertIn('source_less2(value("khitn"), 3)',
                      source_expression('_parent.khitn < 3', set(), {'khitn'}, avm1_comparisons=True))
        self.assertIn('not truth(source_less2(3, value("n")))',
                      expression('value("n") <= 3', set(), avm1_comparisons=True))
        self.assertNotIn('source_less2', expression('value("n") >= 1', set()))

    def test_original_yihu_callback_compiles_comparison_and_following_goto(self):
        bundle = json.loads((ROOT / 'scripts/fighter/yihu.json').read_text())
        path = 'DefineSprite_1180/frame_143/PlaceObject2_651_32/CLIPACTIONRECORD onClipEvent(enterFrame).as'
        source = next(row['source'] for row in bundle['scripts'] if row['path'] == path)
        body = source[source.index('{') + 1:source.rindex('}')]
        code = compile_body('frame_143_depth_32', '', body, scope_fields={'nn'}, avm1_comparisons=True)
        self.assertIn('not truth(source_less2(value("nn"), 1))', code)
        self.assertIn('adapter.goto_label("跳招2", true)', code)
        with self.assertRaisesRegex(ValueError, 'Unsupported AI expression'):
            compile_body('frame_143_depth_32', '', body)
