import unittest

from tools.probes.doaction_observer import inventory, instrument
from tools.sampling_doaction import collect, require_full_coverage


class ClipActionTests(unittest.TestCase):
    def bundle(self, event='enterFrame'):
        return {'game_file': 'game/fighter/test.swf', 'swf_sha256': 'locked', 'scripts': [{
            'path': f'DefineSprite_10/frame_2/PlaceObject2_16_31/CLIPACTIONRECORD onClipEvent({event}).as',
            'source': f'onClipEvent({event}){{\n if(active) {{ unsupportedCall(speed*18); }}\n}}'}]}

    def rows(self, record):
        return [f"AIREF|test|1|0|2|0|clipaction_entry|{record['id']},_level0.game.p1.mc.AImain,1",
                'AIREF|test|2|0|2|0|doaction_sample|root-observer']

    def test_load_and_enterframe_preserve_body_and_source_event(self):
        for event in ('load', 'enterFrame'):
            bundle = self.bundle(event)
            record = inventory(bundle, include_clip=True)[0]
            source = bundle['scripts'][0]['source']
            injected = instrument(source, record)
            self.assertIn('unsupportedCall(speed*18);', injected)
            self.assertTrue(injected.startswith(f'onClipEvent({event}){{'))
            self.assertEqual(record['event'], event)
            self.assertEqual(record['placement_path'], 'PlaceObject2_16_31')
            result = collect(self.rows(record), 'test', 0, [record])
            self.assertEqual(result['visited'][0]['executions'], 1)
            with self.assertRaisesRegex(ValueError, 'ownership unproven'):
                require_full_coverage(result)

    def test_unobserved_clip_and_unsupported_handler_remain_obligations(self):
        bundle = self.bundle()
        other = self.bundle('load')['scripts'][0]
        bundle['scripts'].append(other)
        bundle['scripts'].append(self.bundle('keyDown')['scripts'][0])
        records = inventory(bundle, include_clip=True)
        result = collect(self.rows(records[0]), 'test', 0, records)
        self.assertEqual(len(result['unvisited']), 1)
        self.assertEqual(len(result['uninstrumented']), 1)
        self.assertIn('keyDown', result['uninstrumented'][0]['path'])

    def test_unsupported_or_mismatched_wrapper_rejects(self):
        record = inventory(self.bundle(), include_clip=True)[0]
        for source in ['onClipEvent(load) {}', 'onClipEvent(enterFrame) {', 'unknown();']:
            with self.assertRaisesRegex(ValueError, 'wrapper'):
                instrument(source, record)
        rows = [s.replace('clipaction_entry', 'doaction_entry') for s in self.rows(record)]
        with self.assertRaisesRegex(ValueError, 'kind mismatch'):
            collect(rows, 'test', 0, [record])

    def test_missing_clip_event_and_changed_source_reject(self):
        bundle = self.bundle()
        record = inventory(bundle, include_clip=True)[0]
        with self.assertRaises(ValueError): collect(self.rows(record)[1:], 'test', 0, [record])
        bundle['scripts'][0]['source'] = 'onClipEvent(enterFrame) {}'
        changed = inventory(bundle, include_clip=True)[0]
        with self.assertRaisesRegex(ValueError, 'unbound'):
            collect(self.rows(record), 'test', 0, [changed])

    def test_all_clip_observations_dropped_cannot_pass_via_doaction_entries(self):
        bundle = self.bundle()
        bundle['scripts'].append({'path': 'frame_1/DoAction.as', 'source': 'stop();'})
        records = inventory(bundle, include_clip=True)
        rows = [row.replace('clipaction_entry', 'doaction_entry') for row in self.rows(records[1])]
        with self.assertRaisesRegex(ValueError, 'missing all clip-action'):
            collect(rows, 'test', 0, records)

    def test_main_scope_and_old_doaction_mode_do_not_silently_admit_clips(self):
        bundle = self.bundle()
        self.assertFalse(inventory(bundle)[0]['instrumented'])
        bundle['game_file'] = 'game/main.swf'
        record = inventory(bundle, include_clip=True)[0]
        self.assertEqual(record['kind'], 'clip_action')
        self.assertFalse(record['instrumented'])
        with self.assertRaises(ValueError): collect(self.rows(record), 'test', 0, [record])


if __name__ == '__main__':
    unittest.main()
