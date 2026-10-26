from pathlib import Path
import unittest

from tools.probes.analyze_bitmap_inverse import analyze

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/importer-loud-fail/r23'


class BitmapInverseAnalysisTests(unittest.TestCase):
    def test_independent_probes_reject_general_sampler_admission(self):
        for kind, folder, count in [('repeat', 'inverse', 1008),
                                    ('clipped', 'inverse-clipped', 1008), ('row', 'row', 6048)]:
            report = analyze((EVIDENCE / folder / 'native.log').read_text(), kind)
            self.assertEqual(report['samples'], count)
            self.assertFalse(report['passed'])
            self.assertFalse(report['production_admitted'])
            self.assertEqual(report['exact'], sum(row['native_rgb'] == row['candidate_rgb']
                                                  for row in report['rows']))

    def test_size_control_does_not_explain_distance_failures(self):
        report = analyze((EVIDENCE / 'size/native.log').read_text(), 'size')
        self.assertEqual((report['samples'], report['exact']), (240, 240))
        self.assertEqual((report['size_control_groups'], report['size_control_exact']), (40, 40))
        self.assertFalse(report['production_admitted'])

    def test_incomplete_mixed_or_wrong_identity_cannot_pass(self):
        text = (EVIDENCE / 'row/native.log').read_text()
        for invalid in (text + text, text.replace('|done|ok', '|done|failed'),
                        text.replace('|inverse|255,1.01,-224,', '|inverse|255,1.02,-224,'),
                        text.replace('|filter-bitmap-row-r23-', '|other-', 1)):
            with self.assertRaises(ValueError):
                analyze(invalid, 'row')


if __name__ == '__main__':
    unittest.main()
