"""Frame movement arguments retain source fields and statement order."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/importer'))
from compile_ai_context import compile_context, movement_expression


class FrameMovementTests(unittest.TestCase):
    def compile(self, source=None):
        bundle = json.loads((ROOT / 'scripts/fighter/didala.json').read_text())
        timeline = json.loads((ROOT / 'data/slices/didala-base.timeline.json').read_text())
        if source is not None:
            next(s for s in bundle['scripts'] if s['path'] ==
                 'DefineSprite_542/frame_34/DoAction.as')['source'] = source
        return compile_context(bundle, timeline)

    def test_retained_dash_and_recovery_read_speed(self):
        model = self.compile()
        for frame, multiplier in [('34', 18), ('970', 6)]:
            event = model['frame_calls'][frame][0]
            self.assertEqual(event['axis'], 'moveX')
            self.assertNotIn('pixels', event)
            expression = event['pixels_expression']
            self.assertEqual(expression['op'], 'multiply')
            self.assertEqual(expression['right'], {'op': 'constant', 'value': multiplier})
            left = expression['left']
            if frame == '970':
                self.assertEqual(left['op'], 'negate')
                left = left['operand']
            self.assertEqual(left, {'op': 'read', 'field_name': 'speed'})
        self.assertEqual(model['frame_calls']['826'][-1]['pixels'], -250)

    def test_frame_order_and_vertical_expression(self):
        model = self.compile('speed = 7;\n_parent.moveX(speed * 18);\n'
                             '_parent.moveY(-(speed + 2) / 3);\nspeed = 10;\n')
        events = model['frame_writes']['34'] + model['frame_calls']['34']
        self.assertEqual([e['line'] for e in sorted(events, key=lambda e: e['line'])], [1, 2, 3, 4])
        self.assertEqual(model['frame_calls']['34'][1]['axis'], 'moveY')

    def test_unsupported_movement_fails_instead_of_disappearing(self):
        for argument in ['unknown * 18', 'speed ** 2', 'Math.random()', '_parent._x', 'speed, 2']:
            with self.subTest(argument=argument), self.assertRaisesRegex(ValueError, 'movement expression'):
                self.compile('_parent.moveX(' + argument + ');')
        with self.assertRaisesRegex(ValueError, 'Uncompiled wrapper movement'):
            self.compile('if(touch)\n{\n   _parent.moveX(speed);\n}\n')
        self.assertEqual(movement_expression('+speed - 2', {'speed'})['op'], 'subtract')


if __name__ == '__main__':
    unittest.main()
