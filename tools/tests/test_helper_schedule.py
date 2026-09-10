"""Retain original helper frame settlement between newer clips and BODY."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/probes'))
from build_ai_reference import instrument_schedule


class HelperScheduleTests(unittest.TestCase):
    def test_probe_keeps_clip_event_body_and_observes_inside_handler(self):
        source = 'onClipEvent(load){\n   _X = _parent._x;\n}\n'
        result = instrument_schedule(source, 'helper/load')
        self.assertTrue(result.startswith('onClipEvent(load){'))
        self.assertEqual(result.count('_X = _parent._x;'), 1)
        self.assertLess(result.index('helper/load,enter,'), result.index('_X ='))
        self.assertGreater(result.index('helper/load,exit,'), result.index('_X ='))

    def test_original_pause_and_resume_precede_body_but_follow_action_clips(self):
        rows = json.loads((ROOT / 'evidence/combat/rifagu-base/helper-registry/boundary-events.json').read_text())
        for tick, frame in [(29, 16), (51, 38), (57, 44)]:
            events = [r['value'] for r in rows if r['fight_tick'] == tick and ',enter,' in r['value']]
            helper = next(i for i, value in enumerate(events) if f'woailuo#frame_{frame}/DoAction.as' in value)
            body = next(i for i, value in enumerate(events) if 'yihu#frame_1/PlaceObject2_638_1/' in value)
            controller = next(i for i, value in enumerate(events) if 'yihu#DefineSprite_638/' in value and 'onClipEvent(enterFrame)' in value)
            self.assertLess(controller, helper)
            self.assertLess(helper, body)


if __name__ == '__main__':
    unittest.main()
