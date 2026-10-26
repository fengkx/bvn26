import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

from tools.probes.build_bound_bitmap_component import validate_fixture
from tools.probes.compare_bound_bitmap_component import compare, native_images

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT/'evidence/importer-loud-fail/r33'


class BoundBitmapComponentTests(unittest.TestCase):
    def setUp(self):
        self.fixture = json.loads((EVIDENCE/'native/fixture.json').read_text())

    def test_source_bytes_masks_and_gpu_images_are_exact(self):
        validate_fixture(self.fixture)
        with tempfile.TemporaryDirectory() as directory:
            report = compare(EVIDENCE/'native', EVIDENCE/'render', Path(directory))
        self.assertEqual((report['images_exact'], report['images']), (6, 6))
        self.assertEqual((report['exact_pixels'], report['pixels']), (69120, 69120))
        self.assertTrue(report['diagnostic_passed'])
        self.assertFalse(report['production_admitted'])
        provenance = json.loads((EVIDENCE/'render/provenance.json').read_text())
        for path, digest in provenance['source_sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(), digest, path)
        for path, digest in provenance['readback_sha256'].items():
            self.assertEqual(hashlib.sha256((EVIDENCE/'render'/path).read_bytes()).hexdigest(), digest)

    def test_dropped_mask_and_rewritten_texels_reject(self):
        for field, value in [('fill_masks', []), ('fill_matrix', {}), ('pixels_premultiplied', []),
                             ('raw_tag_sha256', {}), ('source_sha256', 'bad'), ('production_admitted', True)]:
            fixture = copy.deepcopy(self.fixture)
            fixture[field] = value
            with self.assertRaises(ValueError, msg=field):
                validate_fixture(fixture)

    def test_unproven_coverage_transform_and_fill_reject(self):
        for key, value in [('sx', -1), ('sy', 1.5), ('tx', .5), ('rotate', 1), ('sx', float('nan'))]:
            fixture = copy.deepcopy(self.fixture)
            fixture['cases'][0][key] = value
            with self.assertRaises(ValueError, msg=key):
                validate_fixture(fixture)
        fixture = copy.deepcopy(self.fixture)
        shape = ET.fromstring(fixture['shape_xml'])
        shape.find('.//fillStyles/item').set('fillStyleType', '67')
        fixture['shape_xml'] = ET.tostring(shape, encoding='unicode')
        with self.assertRaises(ValueError):
            validate_fixture(fixture)

    def test_incomplete_duplicate_or_reordered_native_reject(self):
        text = (EVIDENCE/'native/native.log').read_text()
        run = json.loads((EVIDENCE/'native/build.json').read_text())['run_id']
        for bad in (text+text, text.replace('|done|ok', '|done|bad'), text.replace('|row|0,0,', '|row|0,1,', 1)):
            with self.assertRaises(ValueError):
                native_images(bad, run, 6, 288, 40)

    def test_one_channel_mismatch_cannot_admit(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            for i in range(6):
                image = Image.open(EVIDENCE/f'render/case-{i}.png').convert('RGBA')
                if i == 0:
                    image.putpixel((0, 0), (1, 0, 0, 0))
                image.save(output/f'case-{i}.png')
            report = compare(EVIDENCE/'native', output, output)
            self.assertFalse(report['diagnostic_passed'])
            self.assertFalse(report['production_admitted'])
            self.assertEqual(report['images_exact'], 5)
            self.assertEqual(report['results'][0]['max_delta'], [1, 0, 0, 0])

    def test_empty_native_component_cannot_pass(self):
        import shutil
        with tempfile.TemporaryDirectory() as directory:
            build = Path(directory)/'native'
            shutil.copytree(EVIDENCE/'native', build)
            lines = []
            for line in (build/'native.log').read_text().splitlines():
                fields = line.split('|')
                if len(fields) == 8 and fields[6] == 'row':
                    values = fields[7].split(',')
                    fields[7] = ','.join(values[:2]+['0']*288)
                    line = '|'.join(fields)
                lines.append(line)
            (build/'native.log').write_text('\n'.join(lines)+'\n')
            with self.assertRaisesRegex(ValueError, 'visible pixels'):
                compare(build, EVIDENCE/'render', Path(directory)/'comparison')
