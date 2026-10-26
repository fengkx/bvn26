import gzip
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.analyze_jpeg_controls import analyze


class JpegControlTests(unittest.TestCase):
    def test_independent_gray_and_color_controls(self):
        evidence=ROOT/'evidence/importer-loud-fail/r212'
        expected=json.loads(gzip.decompress((evidence/'summary.json.gz').read_bytes()))
        executable=shutil.which('djpeg')
        if executable is None or hashlib.sha256(Path(executable).resolve().read_bytes()).hexdigest()!=expected['decoder_executable_sha256']:
            self.skipTest('Pinned djpeg unavailable')
        with tempfile.TemporaryDirectory() as scratch:
            actual=analyze(evidence/'native',Path(executable),Path(scratch))
        self.assertEqual(actual,expected)
        gray=[r for r in actual['rows'] if r['case']['mode']=='L' and r['dct']=='int' and r['smooth']]
        self.assertEqual(sum(r['exact'] for r in gray),4096)
        self.assertFalse(actual['production_admitted'])
