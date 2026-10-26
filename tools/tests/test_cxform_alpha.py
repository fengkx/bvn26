import gzip
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tools.probes.analyze_cxform_alpha import analyze, capture_rows, load_precision

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT/'evidence/importer-loud-fail/r40'


class CxformAlphaTests(unittest.TestCase):
    def test_improved_local_fit_cannot_replace_exact_prior_controls(self):
        report = analyze(EVIDENCE)
        expected = json.loads(gzip.decompress((EVIDENCE/'analysis.json.gz').read_bytes()))
        self.assertEqual(report, expected)
        for flag in ('candidate_admitted','gpu_advance_allowed','production_admitted'):
            self.assertFalse(report[flag])
        self.assertEqual(report['all_alpha']['r39']['exact'],23288)
        self.assertEqual(report['all_alpha']['normalized_divide']['exact'],23902)
        self.assertEqual(report['native_boundaries']['normalized_divide']['exact'],43176)
        self.assertEqual(report['normalized_prior']['rows']['exact'],24239)
        self.assertEqual(report['prior_regressions']['rows']['exact'],25920)
        self.assertEqual(report['prior_regressions']['scalar']['exact'],3072)
        self.assertEqual(report['geometry']['intersection_control_135']['exact'],192000)
        self.assertEqual(report['geometry']['unchanged_selector_135']['exact'],191860)
        self.assertEqual(report['nonbinary_opacity']['normalized_divide/source_8_8_opacity']['exact'],32610)

    def test_incomplete_trace_rejects_even_with_consistent_archive_hashes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            shutil.copy(EVIDENCE/'alpha/build.json',path/'build.json')
            raw = gzip.decompress((EVIDENCE/'alpha/native.log.gz').read_bytes())
            lines = raw.decode().splitlines()
            raw = ('\n'.join(line for line in lines if '|done|ok' not in line)+'\n').encode()
            compressed = gzip.compress(raw,mtime=0)
            (path/'native.log.gz').write_bytes(compressed)
            (path/'trace-sha256.json').write_text(json.dumps({
                'native.log':hashlib.sha256(raw).hexdigest(),
                'native.log.gz':hashlib.sha256(compressed).hexdigest()}))
            identities = [[a*3+i,a,op] for a in range(256) for i,op in enumerate((25,50,100))]
            with self.assertRaisesRegex(ValueError,'Incomplete'):
                capture_rows(path,identities)

    def test_reciprocal_measurement_columns_must_be_complete(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'precision.txt'
            path.write_text('1 3f800000\n')
            with self.assertRaisesRegex(ValueError,'Incomplete'):
                load_precision(path)
