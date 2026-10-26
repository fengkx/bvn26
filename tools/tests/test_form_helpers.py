import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/importer'))
from compile_ai_body import compile_body
from compile_ai_predicates import normalize, expression


class FormHelperTests(unittest.TestCase):
    def test_all_seven_fixtures_compile_from_source(self):
        directory = ROOT / 'godot/tests/fixtures/form_helpers'
        for row in json.loads((directory / 'sources.json').read_text()):
            metadata = row['metadata']
            bundle = json.loads((ROOT / metadata['source_swf'].replace('game/', 'scripts/', 1).replace('.swf', '.json')).read_text())
            sprite = int(metadata['path'].split('/')[0].split('_')[1])
            code, actual = compile_body(bundle, sprite, player=True, form_helpers=True)
            self.assertEqual(code, (directory / row['script']).read_text())
            self.assertEqual(actual, metadata)
            self.assertTrue({'wankai', 'doWanKai', 'initCtrl', 'randAI'}.issubset(actual['functions']))
            self.assertIn('if truth((not truth(form_next_frame()))):', code)

    def test_form_source_mutations_fail_with_location(self):
        original = json.loads((ROOT / 'scripts/fighter/daitu.json').read_text())
        for before, after in [('setInterval(feixue,1000)', 'setInterval(feixue,500)'),
                              ('_parent.nextFrame();', '_parent.gotoAndStop(9);'),
                              ('_parent.中转.ql = ql;', '_parent.中转.unknown = ql;'),
                              ('AImain.unloadMovie();', 'AImain.unknown();'),
                              ('_this.上 = _root.w;', '_this.unknown = _root.w;'),
                              ('_root.airanset = setInterval(randAI,500);', '_root.airanset = setInterval(randAI,1000);')]:
            bundle = copy.deepcopy(original)
            script = next(s for s in bundle['scripts'] if s['path'] == 'DefineSprite_458/frame_1/DoAction.as')
            self.assertIn(before, script['source'])
            script['source'] = script['source'].replace(before, after)
            with self.assertRaisesRegex(ValueError, r'daitu.swf:DefineSprite_458/frame_1/DoAction.as#form_helpers'):
                compile_body(bundle, 458, player=True, form_helpers=True)

    def test_cpu_helpers_preserve_undefined_and_player_branches(self):
        bundle = json.loads((ROOT / 'scripts/fighter/daitu.json').read_text())
        code, _ = compile_body(bundle, 458, form_helpers=True)
        self.assertIn('equal(value("useAI"), null)', code)
        self.assertIn('form_effect("AImain.unloadMovie()")', code)
        self.assertIn('form_interval("airanset", "randAI", 500)', code)


class PredicateBoundaryTests(unittest.TestCase):
    def test_known_field_prefix_does_not_corrupt_unknown_field(self):
        self.assertEqual(normalize('_parent.khitn < 3'), '_parent.khitn < 3')
        self.assertEqual(normalize('"_parent.khit"'), '"_parent.khit"')
        self.assertEqual(normalize('_parent.khit < 3'), 'value("khit") < 3')
        with self.assertRaisesRegex(ValueError, 'Unsupported'):
            expression('_parent.khitn < 3', set())

    def test_controller_error_names_swf_and_child_frame(self):
        from compile_ai_controller import compile_controller
        bundle = json.loads((ROOT / 'scripts/fighter/Byakuya.json').read_text())
        timeline = json.loads((ROOT / 'data/slices/Byakuya-base.timeline.json').read_text())
        path = 'DefineSprite_631/frame_134/PlaceObject2_69_34/CLIPACTIONRECORD onClipEvent(enterFrame).as'
        script = next(s for s in bundle['scripts'] if s['path'] == path)
        script['source'] = script['source'].replace('if(', 'if(_parent.uncompiled && ', 1)
        with self.assertRaises(ValueError) as failure:
            compile_controller(bundle, 631, timeline)
        self.assertIn('game/fighter/Byakuya.swf:' + path, str(failure.exception))
