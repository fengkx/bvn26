"""Negative gates and source-bound invariants; synthetic markers are not live proof."""
import gzip
import json
import unittest
from analyze import HERE, ROOT, replay, target_observations, timeline
from build_observer import ORIGINAL, patch

TAG = 'm002-r23-offline-20261111'

class FacilityTests(unittest.TestCase):
    def test_patch_retains_original_assignment(self):
        result = patch(ORIGINAL, TAG)
        self.assertEqual(result.split('\n', 1)[1], ORIGINAL)
        self.assertNotIn('_parent', result)
        self.assertNotIn('_root', result)
        self.assertNotIn('gotoAndPlay', result)

    def test_source_and_tag_mismatch_refused(self):
        for source, tag in [(ORIGINAL + 'stop();', TAG), (ORIGINAL, 'bad|tag'), (patch(ORIGINAL, TAG), TAG)]:
            with self.assertRaises(ValueError):
                patch(source, tag)

    def test_encoded_timeline_edges(self):
        rows = timeline((ROOT / 'game/fighter/yihu.swf').read_bytes())
        self.assertTrue(any(r.get('label') == '砍1' and r['frame'] == 173 for r in rows))
        for frame, depth in [(1, 31), (173, 34)]:
            self.assertTrue(any(r['frame'] == frame and r.get('character_id') == 16 and r.get('depth') == depth and not r['move'] for r in rows))
        self.assertTrue(any(r['frame'] == 13 and r['tag'] == 28 and r['depth'] == 31 for r in rows))
        self.assertTrue(any(r['frame'] == 174 and r['tag'] == 12 for r in rows))

    def test_truncated_timeline_refused(self):
        with self.assertRaises(ValueError):
            timeline(b'not-a-swf')

    def test_synthetic_target_never_joins_invocation(self):
        raw = ('M002TARGET|' + TAG + '|yihu638-frame174|%2Fgame%2Fp1%2Fmc|174\n').encode()
        rows = target_observations(raw * 2, TAG)
        self.assertEqual(len(rows), 2)
        self.assertFalse(rows[0]['initiating_call_join_proven'])
        self.assertFalse(rows[0]['helper_lifetime_proven'])

    def test_foreign_and_wrong_context_refused(self):
        for line in ['M002TARGET|foreign|yihu638-frame174|%2Fgame%2Fp1%2Fmc|174',
                     'M002TARGET|' + TAG + '|yihu638-frame174|%2Fgame%2Fp1%2Fmc|173',
                     'M002TARGET|' + TAG + '|yihu638-frame174|%2Fhelper|174']:
            with self.assertRaises(ValueError):
                target_observations(line.encode(), TAG)

    def test_compiled_target_preserves_write_after_trace(self):
        code = gzip.decompress((HERE / 'r23.pcode.gz').read_bytes()).decode()
        self.assertEqual(code.count('\nTrace\r\n'), 1)
        self.assertTrue(code.endswith('Trace\r\nPush "动作"\r\nPush 1\r\nSetVariable\r\n'))
        self.assertNotIn('CallMethod', code)

    def test_e84a_encoded_after_and_replay_remain_unproved(self):
        code = gzip.decompress((HERE / 'e84a.pcode.gz').read_bytes()).decode()
        for site in ('doStand', 'doAllAction'):
            before = 'Push "M002LITERAL|m002-r22-live-20261111-e84a|' + site + '|before"'
            after = 'Push "M002LITERAL|m002-r22-live-20261111-e84a|' + site + '|after"'
            interval = code[code.index(before):code.index(after) + len(after)]
            self.assertEqual(interval.count('CallMethod'), 1)
            self.assertIn('"gotoAndPlay"', interval)
            self.assertNotIn('Return', interval)
        report = replay()
        self.assertEqual(report['target_observations'], [])
        self.assertEqual(report['structural_refusal'], 'Incomplete actor state at clock boundary')
        self.assertEqual(report['literal']['outcomes'][0]['classification'], 'literal-before-without-after')
        self.assertEqual(report['cause'], 'unproved')
