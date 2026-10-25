import gzip
import json
import unittest
from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.analyze_original_jpeg import analyze


class OriginalJpegProbeTests(unittest.TestCase):
    def test_original_source_alpha_and_decoder_rejection(self):
        evidence = ROOT / 'evidence/importer-loud-fail/r210'
        result = analyze(evidence / 'native')
        expected = json.loads(gzip.decompress((evidence / 'summary.json.gz').read_bytes()))
        self.assertEqual(json.loads(json.dumps(result)), expected)
        self.assertEqual(result['alpha_exact'], 70308)
        self.assertEqual(result['exact'], 37022)
        self.assertFalse(result['decoder_parity_proved'])
        self.assertFalse(result['production_admitted'])
