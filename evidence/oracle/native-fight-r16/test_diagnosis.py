import copy
import gzip
import json
import unittest

import analyze


class DiagnosisTests(unittest.TestCase):
    def setUp(self):
        old = analyze.HERE.parent / 'native-fight-r15'
        build = json.loads((old / 'build.json').read_text())
        self.rows = analyze.r05.base.parse((old / 'run-01/tagged.log').read_bytes(), build['run_id'])

    def test_actual_missing_after_remains_unjoined(self):
        report = analyze.analyze()
        self.assertEqual((report['validated_count'], report['refused_count']), (223, 1))
        gap, = report['missing_post_goto']
        self.assertEqual(gap['goto_before']['seq'], 6979)
        self.assertEqual(gap['query']['seq'], 6973)
        self.assertEqual(gap['cause'], 'unproved')
        self.assertEqual(gap['key_join_status'], 'not-joined')
        self.assertEqual([r['seq'] for r in gap['predicate_prefix']], list(range(6973, 6980)))
        self.assertEqual(gap['next_events'][0]['seq'], 6980)
        self.assertEqual(gap['later_installations'][0]['seq'], 6986)
        self.assertEqual(report['structural_refusal'], 'Incomplete actor state at clock boundary')
        for flag in ['production_admitted', 'native_parity_proven', 'oracle_accepted', 'certified_global_tick', 'os_input_join_proven']:
            self.assertIs(report[flag], False)

    def test_eof_silence_does_not_prove_abort(self):
        gap, = analyze.classify(self.rows[:6979])['missing_post_goto']
        self.assertEqual(gap['later_event_count'], 0)
        self.assertEqual(gap['cause'], 'unproved')
        self.assertEqual(gap['key_join_status'], 'not-joined')

    def test_later_activity_does_not_close_candidate(self):
        report = analyze.classify(self.rows)
        self.assertGreater(report['missing_post_goto'][0]['later_event_count'], 0)
        self.assertEqual(report['refused_count'], 1)

    def test_wrong_identity_after_never_validates(self):
        rows = copy.deepcopy(self.rows[:6979])
        row = dict(rows[-1], seq=6980, kind='consumer-goto-after')
        row['data'] = row['data'].replace('instance2901', 'another-helper')
        rows.append(row)
        report = analyze.classify(rows)
        self.assertEqual(report['validated_count'], 186)
        self.assertEqual(report['refused_count'], 1)

    def test_source_reconstruction_retains_dynamic_post_call_reads(self):
        source = analyze.r14.r07.patch_fighter(analyze.r14.r07.sources('scripts/fighter/yihu.json'))[0]
        patched, changes = analyze.r14.patch_fighter(source)
        recorded = json.loads((analyze.HERE / 'source-reconstruction.json').read_text())
        self.assertEqual(recorded['changes'], changes)
        self.assertEqual(analyze.hashlib.sha256(patched.encode()).hexdigest(), recorded['reconstructed_sha256'])
        diff = gzip.decompress((analyze.HERE.parent / 'native-fight-r15/consumer.diff.gz').read_bytes()).decode()
        for change in changes:
            before, after = change['replacement'].split('      _parent.gotoAndPlay("砍1");', 1)
            self.assertIn('consumer-goto-before', before)
            self.assertIn('consumer-goto-after', after)
            for expression in ['this._target', '_parent._target', '_root.__m002Value(_parent._currentframe)', '_parent._parent.useAI']:
                self.assertIn(expression, after)
            self.assertIn(analyze.r14.marker('consumer-goto-after', change['site']).strip(), diff)


if __name__ == '__main__':
    unittest.main()
