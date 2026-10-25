import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_indexed_bitmap_spans import analyze

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r150'

class IndexedBitmapSpanTests(unittest.TestCase):
    def test_fixed_api_routes_and_materialization_controls(self):
        r=analyze(EVIDENCE/'native');failures={k:v.pop('failures') for k,v in r['scores'].items()}
        self.assertEqual(r,json.loads((EVIDENCE/'summary.json').read_text()))
        self.assertEqual(failures,json.loads(gzip.decompress((EVIDENCE/'failures.json.gz').read_bytes())))
        self.assertEqual(r['native_source_exact'],2275)
        self.assertEqual(r['before_after'],{'samples':37248,'exact':37248})
        for key in ['api0-byte_all','api1-admitted_vertical_bulk']:
            self.assertEqual(r['scores'][key]['exact'],36832)
            self.assertEqual(r['scores'][key]['max_channel_delta'],0)
        self.assertLess(r['scores']['api0-admitted_vertical_bulk']['exact'],36832)
        self.assertFalse(r['production_admitted'])
        self.assertFalse(r['indexed_continuous_sampler_admitted'])

    def test_provenance(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
