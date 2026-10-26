import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/importer'))
from compile_ai_body import compile_body


class FormCallbackTests(unittest.TestCase):
    def test_fixtures_are_compiled_from_each_actual_body(self):
        directory = ROOT / 'godot/tests/fixtures/form_callbacks'
        for row in json.loads((directory / 'sources.json').read_text()):
            metadata = row['metadata']
            bundle = json.loads((ROOT / metadata['source_swf'].replace('game/', 'scripts/', 1).replace('.swf', '.json')).read_text())
            sprite = int(metadata['path'].split('/')[0].split('_')[1])
            code, actual = compile_body(bundle, sprite, player=True, form_callbacks=True)
            self.assertEqual(code, (directory / row['script']).read_text())
            self.assertEqual(actual, metadata)
            self.assertIn('func feixue()', code)
            self.assertIn('func loseHp(', code)

    def test_callback_and_receiver_changes_are_rejected_with_source(self):
        original = json.loads((ROOT / 'scripts/fighter/daitu.json').read_text())
        for before, after in [('loseHp(10);', 'unknownCall(10);'),
                              ('var _this = this;', 'var _this = _parent;'),
                              ('var _this = this;', 'var _this = this;\n_this = _parent;'),
                              ('feixue = function()', 'otherCallback = function()')]:
            bundle = copy.deepcopy(original)
            script = next(s for s in bundle['scripts'] if s['path'] == 'DefineSprite_458/frame_1/DoAction.as')
            self.assertIn(before, script['source'])
            script['source'] = script['source'].replace(before, after)
            with self.assertRaisesRegex(ValueError, r'daitu.swf:DefineSprite_458/frame_1/DoAction.as'):
                compile_body(bundle, 458, player=True, form_callbacks=True)

    def test_default_compilation_does_not_enable_form_entry(self):
        bundle = json.loads((ROOT / 'scripts/fighter/daitu.json').read_text())
        code, _ = compile_body(bundle, 458, player=True)
        self.assertNotIn('func feixue()', code)
        self.assertNotIn('func wankai()', code)
