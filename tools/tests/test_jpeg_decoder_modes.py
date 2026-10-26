import gzip
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.compare_jpeg_decoder_modes import compare


class JpegDecoderModeTests(unittest.TestCase):
    def test_global_modes_retain_all_native_counterexamples(self):
        executable = shutil.which('djpeg')
        if executable is None:
            self.skipTest('djpeg unavailable')
        evidence = ROOT / 'evidence/importer-loud-fail/r211/decoder'
        expected = json.loads((evidence/'summary.json').read_text())
        if hashlib.sha256(Path(executable).resolve().read_bytes()).hexdigest() != expected['decoder_executable_sha256']:
            self.skipTest('Different decoder executable; recapture required')
        with tempfile.TemporaryDirectory() as scratch:
            actual = compare(ROOT/'evidence/importer-loud-fail/r210/native',Path(executable),Path(scratch))
            for result, old in zip(actual['modes'],expected['modes']):
                self.assertEqual(result['exact'],old['exact'])
                self.assertEqual(result['decoded_rgb_sha256'],old['decoded_rgb_sha256'])
                self.assertEqual((Path(scratch)/(result['name']+'.json')).read_bytes(),
                                 gzip.decompress((evidence/(result['name']+'.json.gz')).read_bytes()))
            self.assertFalse(actual['production_admitted'])
