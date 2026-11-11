"""Static review regressions; no simulated response is treated as a receipt."""
import gzip
import json
from pathlib import Path
import tempfile
import unittest
import analyze


class ReviewTests(unittest.TestCase):
    def changed_source(self, name, before, after):
        sources = analyze.r29.read_sources()
        key = analyze.PREFIX + name + '.java'
        self.assertIn(before, sources[key])
        sources[key] = sources[key].replace(before, after)
        with self.assertRaises(ValueError):
            analyze.audit(sources, analyze.read_counter())

    def test_changed_response_rule_requires_review(self):
        self.changed_source('PlayerSession', 'long expect = num+1;', 'long expect = num+2;')

    def test_changed_option_cache_requires_review(self):
        self.changed_source('DManager', 'm_options.put(s, v);', 'm_options.put(v, s);')

    def test_changed_progress_reply_requires_review(self):
        self.changed_source('PlayerSession', 'sendMessageIsolate(DMessage.OutProcessedTag, msg.getTargetIsolate());', '')

    def test_changed_counter_requires_review(self):
        with self.assertRaises(ValueError):
            analyze.audit(analyze.r29.read_sources(), analyze.read_counter().replace('m_inCounts[type] += 1;', ''))

    def test_source_corruption_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            receipt = json.loads((analyze.HERE / 'source-receipts.json').read_text())
            receipt['sources'][0]['snapshot'] = 'source.gz'
            (p / 'source-receipts.json').write_text(json.dumps(receipt))
            (p / 'source.gz').write_bytes(gzip.compress(b'changed source'))
            with self.assertRaises(ValueError):
                analyze.read_counter(p)

    def test_static_review_cannot_admit_or_invent_failure(self):
        report = analyze.analyze()
        for flag in analyze.r29.FLAGS:
            self.assertIs(report[flag], False)
        self.assertFalse(report['observed_response_mismatch'])
        self.assertFalse(report['reset_semantics_qualified'])
        self.assertIsNone(report['native_boundary'])
        self.assertEqual(report['historical_structural_refusal'], 'Incomplete actor state at clock boundary')


if __name__ == '__main__':
    unittest.main()
