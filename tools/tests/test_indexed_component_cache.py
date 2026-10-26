import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_indexed_component_cache import analyze

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r151'

class IndexedComponentCacheTests(unittest.TestCase):
    def test_original_source_boundaries_and_coverage_rejection(self):
        r=analyze(ROOT/'evidence/importer-loud-fail/r142/fixture.json',ROOT/'evidence/importer-loud-fail/r141/native')
        self.assertEqual(json.loads(json.dumps(r)),json.loads((EVIDENCE/'summary.json').read_text()))
        for row in r['rows']:
            if row['tick']==4:
                self.assertEqual(row['error'],'Unproven fractional coverage')
                self.assertEqual(len(row['diagnosis']['nontransparent_fringe']),8)
            else:
                for key in ('cache','authored','pinned'):self.assertEqual(row[key]['exact'],240000)
        self.assertFalse(r['source_cpu_exact'])
        self.assertFalse(r['production_admitted'])
        self.assertFalse(r['gpu_binding_verified'])

    def test_provenance(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
