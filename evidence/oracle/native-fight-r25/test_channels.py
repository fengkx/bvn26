"""Synthetic four-prefix tests are protocol tests, never live observations."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

import analyze
import channels
import capture_observer as capture

HERE = Path(__file__).resolve().parent
TAG = 'm002-r24-synthetic-test'


class FourPrefixTests(unittest.TestCase):
    def fixture(self):
        root = ('M002|' + TAG + '|1|0|0|boot|boot|test\n').encode()
        rest = ('M002SIDE|' + TAG + ',helper,1,doAllAction|before\n'
                'M002LITERAL|' + TAG + '|doAllAction|before\n'
                'M002TARGET|' + TAG + '|yihu638-frame174|%2Fgame%2Fp1%2Fmc|174\n').encode()
        return root, root + b'\xff unknown barrier\n' + rest

    def test_four_fresh_channels_byte_original(self):
        root, final = self.fixture()
        analyze.validate_combined_bytes(b'old non-tag bytes', b'', final, final, root, TAG)
        counts, targets = channels.validate_channels(b'', final, TAG)
        self.assertEqual(counts, dict(root=1, side=1, literal=1, target=1))
        self.assertFalse(targets[0]['initiating_call_join_proven'])
        self.assertFalse(targets[0]['helper_lifetime_proven'])

    def test_stale_each_channel_capture_and_analysis(self):
        root, final = self.fixture()
        prefixes = capture.tag_prefixes(TAG)
        self.assertEqual(set(prefixes), {'root', 'side', 'literal', 'target'})
        for prefix in prefixes.values():
            with self.subTest(prefix=prefix):
                with self.assertRaisesRegex(ValueError, 'already present'):
                    capture.reject_stale_prelaunch(prefix, prefixes)
                with self.assertRaisesRegex(ValueError, 'already present'):
                    analyze.validate_combined_bytes(prefix, b'', final, final, root, TAG)

    def test_foreign_each_channel_refused(self):
        root, final = self.fixture()
        for prefix in channels.tag_prefixes('foreign-tag').values():
            bad = final + prefix + b'noise\n'
            with self.assertRaisesRegex(ValueError, 'Foreign'):
                analyze.validate_combined_bytes(b'', b'', bad, bad, root, TAG)

    def test_dropped_target_or_reordered_bytes_refused(self):
        root, final = self.fixture()
        for changed in [root, b'\n'.join(reversed(final.splitlines())) + b'\n']:
            with self.assertRaisesRegex(ValueError, 'Combined raw order'):
                analyze.validate_combined_bytes(b'', b'', final, changed, root, TAG)

    def test_target_body_frame_and_shape_refused(self):
        _, final = self.fixture()
        for changed in [final.replace(b'|174\n', b'|173\n'),
                        final.replace(b'%2Fgame%2Fp1%2Fmc', b'%2Fhelper'),
                        final.replace(b'|yihu638-frame174|', b'|other-site|')]:
            with self.assertRaises(ValueError):
                channels.validate_channels(b'', changed, TAG)

    def test_append_and_root_selection_refused(self):
        root, final = self.fixture()
        with self.assertRaisesRegex(ValueError, 'append mismatch'):
            analyze.validate_combined_bytes(b'', b'not the baseline', final, final, root, TAG)
        with self.assertRaisesRegex(ValueError, 'Raw/tag selection'):
            analyze.validate_combined_bytes(b'', b'', final, final, b'', TAG)

    def test_r23_receipt_shape_required(self):
        build = json.loads((HERE / 'build.json').read_text())
        channels.validate_build(build)
        for field, value in [('facility', 'r21'), ('target_site', 'other'),
                             ('target_builder_sha256', '0' * 64),
                             ('changed_tag_paths_by_asset', {})]:
            altered = copy.deepcopy(build)
            altered[field] = value
            with self.assertRaisesRegex(ValueError, 'r23 target build'):
                channels.validate_build(altered)

    def test_r22_live_session_is_not_r23(self):
        old = HERE.parent / 'native-fight-r22-live-03/run-01/session.json'
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / 'session.json').write_bytes(old.read_bytes())
            with self.assertRaisesRegex(ValueError, 'Build/session mismatch'):
                analyze.analyze(directory)

    def test_target_is_barrier_not_literal_bridge(self):
        old = HERE.parent / 'native-fight-r22-live-03'
        tag = json.loads((old / 'build.json').read_text())['run_id']
        raw = (old / 'run-01/combined.log').read_bytes()
        before = ('M002LITERAL|' + tag + '|doAllAction|before').encode()
        after = before.replace(b'|before', b'|after')
        target = ('M002TARGET|' + tag + '|yihu638-frame174|%2Fgame%2Fp1%2Fmc|174').encode()
        synthetic = raw.replace(before, before + b'\n' + target + b'\n' + after)
        records, rows = channels.r23.r21.parse(synthetic, tag)
        result = channels.r23.r21.classify(records, rows, tag)
        self.assertTrue(any(r['classification'] == 'ambiguous' for r in result['outcomes']))
        self.assertFalse(any(r['source_continuation_observed'] for r in result['outcomes']))
        self.assertEqual(len(channels.validate_channels(b'', synthetic, tag)[1]), 1)

    def test_historical_structural_refusal_unchanged(self):
        result = channels.r23.replay()
        self.assertEqual(result['structural_refusal'], 'Incomplete actor state at clock boundary')
        self.assertEqual(result['target_observations'], [])
        for flag in channels.r23.FLAGS:
            self.assertIs(result[flag], False)
