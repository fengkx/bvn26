import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/importer'))
from compile_ai_controller import compile_body


class ControllerCompoundAssignmentTests(unittest.TestCase):
    def test_original_wrapper_flip_precedes_original_goto(self):
        bundle = json.loads((ROOT / 'scripts/fighter/yihu.json').read_text())
        path = 'DefineSprite_1672/frame_390/PlaceObject2_16_34/CLIPACTIONRECORD onClipEvent(enterFrame).as'
        source = next(s['source'] for s in bundle['scripts'] if s['path'] == path)
        body = source.split('\n', 1)[1].rsplit('}', 1)[0]
        result = compile_body('source_callback', '', body)
        self.assertIn('number(value("xscale")) * number((-number(1)))', result)
        self.assertLess(result.index('write_value("xscale"'), result.index('adapter.goto_label'))

    def test_numeric_compound_assignment_is_generic(self):
        result = compile_body('callback', '', 'var factor = 3;\nfactor *= -2;')
        self.assertIn('factor = (number(factor) * number((-number(2))))', result)

    def test_unknown_target_and_expression_stay_errors(self):
        for line in ('_parent.unknown *= 2;', '_parent._parent._xscale *= unknown();'):
            with self.subTest(line=line), self.assertRaises(ValueError):
                compile_body('callback', '', line)


if __name__ == '__main__':
    unittest.main()
