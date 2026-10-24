"""Exhaustive image rejection must not select a coefficient from an interval."""
from bisect import bisect_left, bisect_right
import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_cxform_reciprocal_image import decode


class ReciprocalImageTests(unittest.TestCase):
    def test_complete_hardware_domain_and_hashes(self):
        root = Path(__file__).resolve().parents[2]
        evidence = root/'evidence/importer-loud-fail/r56'
        raw = gzip.decompress((evidence/'hardware.txt.gz').read_bytes())
        env = json.loads((evidence/'environment.json').read_text())
        self.assertEqual(hashlib.sha256(raw).hexdigest(),env['output_sha256'])
        self.assertEqual(hashlib.sha256((root/'tools/probes/cxform_reciprocal_image.c').read_bytes()).hexdigest(),env['source_sha256'])
        runs = decode(raw.decode())
        self.assertEqual(sum(end-start+1 for start,end,_ in runs),67108865)
        self.assertEqual(len(runs),27153)
        lines = raw.decode().splitlines()
        with self.assertRaises(ValueError):
            decode('\n'.join(lines[:1]+lines[2:]))
        with self.assertRaises(ValueError):
            decode(raw.decode().replace('rises 0','rises 1'))

    def test_every_interval_against_complete_output_image(self):
        root = Path(__file__).resolve().parents[2]/'evidence/importer-loud-fail/r56'
        runs = decode(gzip.decompress((root/'hardware.txt.gz').read_bytes()).decode())
        outputs = sorted(v[2] for v in runs)
        r = json.loads(gzip.decompress((root/'analysis.json.gz').read_bytes()))
        for mode,model in r['models'].items():
            for row in model['alphas'].values():
                self.assertEqual(row['reachable_output_count'],
                    bisect_right(outputs,row['high_bits'])-bisect_left(outputs,row['low_bits']))
            self.assertIn(204,model['unreachable_alphas'])
        self.assertEqual(len(r['models']['multiply_estimated']['unreachable_alphas']),48)
        for flag in ('coefficients_selected','candidate_admitted','gpu_advance_allowed','production_admitted','hardware_instruction_inference'):
            self.assertFalse(r[flag])


if __name__=='__main__':
    unittest.main()
