import gzip
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
from PIL import Image

from tools.probes.run_native_cxform_controls import compare, dataset

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/importer-loud-fail/r60/render'


class NativeCxformGpuTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.keys, cls.groups = dataset()

    def test_all_old_and_signed_controls_exact(self):
        report = compare(EVIDENCE / 'gpu.png', self.keys, self.groups)
        self.assertTrue(report['passed'])
        self.assertFalse(report['production_admitted'])
        self.assertEqual(report['unique_controls'], 136774)
        for name, total in [('old', 1284192), ('signed', 18720)]:
            self.assertEqual(report['scores'][name]['exact'], total)
            self.assertEqual(report['scores'][name]['channels'], total)

    def test_single_channel_mismatch_and_bad_extent_reject(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'wrong.png'
            image = Image.open(EVIDENCE / 'gpu.png').convert('RGBA')
            pixel = image.getpixel((0, 0))
            image.putpixel((0, 0), ((pixel[0] + 1) % 256, *pixel[1:]))
            image.save(path)
            self.assertFalse(compare(path, self.keys, self.groups)['passed'])
            image.crop((0, 0, 1023, image.height)).save(path)
            with self.assertRaisesRegex(ValueError, 'dimensions'):
                compare(path, self.keys, self.groups)

    def test_consumed_controls_and_gpu_bytes_are_pinned(self):
        provenance = json.loads((EVIDENCE / 'provenance.json').read_text())
        self.assertEqual(hashlib.sha256(json.dumps(self.keys).encode()).hexdigest(),
                         provenance['native_controls_sha256'])
        for name, expected in provenance['source_sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), expected)
        for name, expected in provenance['readback_sha256'].items():
            raw = (gzip.decompress((EVIDENCE / (name + '.gz')).read_bytes())
                   if name.endswith('.bin') else (EVIDENCE / name).read_bytes())
            self.assertEqual(hashlib.sha256(raw).hexdigest(), expected)
        inputs = gzip.decompress((EVIDENCE / 'inputs.bin.gz').read_bytes())
        opacities = gzip.decompress((EVIDENCE / 'opacities.bin.gz').read_bytes())
        for i, (args, _) in enumerate(self.keys):
            self.assertEqual(struct.unpack_from('<4f', inputs, i * 16), tuple(args[:4]))
            self.assertEqual(struct.unpack_from('<f', opacities, i * 4)[0], args[4] * 256 // 100)
