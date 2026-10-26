"""Complete post-scaled images retain measured constructions and native bounds."""
from bisect import bisect_left, bisect_right
import gzip
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from tools.probes.analyze_cxform_scaled_image import analyze, decode, DOMAINS, NAMES


class ScaledImageTests(unittest.TestCase):
    def test_exhaustive_runs_and_independent_controls(self):
        root = Path(__file__).resolve().parents[2]
        evidence = root/'evidence/importer-loud-fail/r57'
        env = json.loads((evidence/'environment.json').read_text())
        self.assertEqual(hashlib.sha256((root/'tools/probes/cxform_scaled_reciprocal_image.c').read_bytes()).hexdigest(),env['source_sha256'])
        pinned = json.loads(gzip.decompress((evidence/'analysis.json.gz').read_bytes()))
        with tempfile.TemporaryDirectory() as directory:
            for i,(first,last) in enumerate(DOMAINS):
                raw = gzip.decompress((evidence/f'hardware-{i}.txt.gz').read_bytes())
                self.assertEqual(hashlib.sha256(raw).hexdigest(),env['output_sha256'][str(i)])
                runs = decode(raw.decode(),i)
                self.assertEqual(sum(end-start+1 for start,end,_ in runs),last-first+1)
                Path(directory,f'hardware-{i}.txt').write_bytes(raw)
                with self.assertRaises(ValueError):
                    decode(raw.decode(),(i+1)%4)
            self.assertEqual(analyze(Path(directory)),pinned)

    def test_alpha204_unreachable_for_all_source_paths(self):
        root = Path(__file__).resolve().parents[2]/'evidence/importer-loud-fail/r57'
        report = json.loads(gzip.decompress((root/'analysis.json.gz').read_bytes()))
        for i,name in enumerate(NAMES):
            runs = decode(gzip.decompress((root/f'hardware-{i}.txt.gz').read_bytes()).decode(),i)
            outputs = sorted(v[2] for v in runs)
            image = report['images'][name]
            self.assertEqual(image['old_construction_controls_exact'],255)
            for model in image['models'].values():
                self.assertIn(204,model['unreachable_alphas'])
                for row in model['alphas'].values():
                    self.assertEqual(row['reachable_output_count'],bisect_right(outputs,row['high_bits'])-bisect_left(outputs,row['low_bits']))
        for flag in ('coefficients_selected','hardware_instruction_inference','candidate_admitted','gpu_advance_allowed','production_admitted'):
            self.assertFalse(report[flag])


if __name__=='__main__':
    unittest.main()
