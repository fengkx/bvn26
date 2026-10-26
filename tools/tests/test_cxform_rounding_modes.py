"""Hardware modes must be explicit and preserve every nearest-mode control."""
import gzip
import hashlib
import json
from pathlib import Path
import unittest


class RoundingModeEvidenceTests(unittest.TestCase):
    def test_readback_and_provenance(self):
        root = Path(__file__).resolve().parents[2]
        evidence = root/'evidence/importer-loud-fail/r52'
        env = json.loads((evidence/'environment.json').read_text())
        self.assertEqual(hashlib.sha256((root/'tools/probes/cxform_rounding_modes.c').read_bytes()).hexdigest(),env['source_sha256'])
        raw = gzip.decompress((evidence/'hardware.txt.gz').read_bytes())
        self.assertEqual(hashlib.sha256(raw).hexdigest(),env['output_sha256'])
        source = gzip.decompress((evidence/'inputs.txt.gz').read_bytes())
        self.assertEqual(hashlib.sha256(source).hexdigest(),env['input_sha256'])
        lines = raw.decode().splitlines()
        self.assertEqual(len(lines)-1,len(source.splitlines()))
        for i,line in enumerate(lines[1:]):
            row = line.split()
            self.assertEqual(int(row[0]),i)
            self.assertEqual([row[j] for j in (1,5,9,13)],['0000','2000','4000','6000'])
        self.assertFalse(env['instruction_inference'])

    def test_full_control_counts_and_pair_rejection(self):
        path = Path(__file__).resolve().parents[2]/'evidence/importer-loud-fail/r52/analysis.json.gz'
        r = json.loads(gzip.decompress(path.read_bytes()))
        self.assertEqual(r['nearest_mode_unique_controls_exact'],410322)
        self.assertEqual(len(r['models']),12)
        for model in r['models'].values():
            self.assertEqual(model['pair'][1]['native'],11)
            self.assertEqual(model['pair'][1]['actual'],12)
            for group,total in (('old',1284192),('signed',18720)):
                s = model['scores'][group]
                self.assertEqual(s['total'],total)
                self.assertEqual(s['exact']+sum(v['count'] for v in s['failures']),total)
        for flag in ('candidate_admitted','gpu_advance_allowed','production_admitted'):
            self.assertFalse(r[flag])


if __name__=='__main__':
    unittest.main()
