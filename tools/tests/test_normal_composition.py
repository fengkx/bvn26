import copy
import hashlib
import json
from pathlib import Path
import unittest
from PIL import Image

from tools.probes.normal_composition import analyze, decode, over, predict
from tools.probes.run_production_wrapper import analyze_stages, path_passed
from tools.probes.run_yulong_wrapper import compare, fixture

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT/'evidence/importer-loud-fail/r36'


class NormalCompositionTests(unittest.TestCase):
    def test_native_controls_and_gpu_are_byte_exact(self):
        expected = []
        for kind in ('vector', 'bitmap'):
            result = analyze(EVIDENCE/kind, kind == 'vector')
            self.assertEqual((result['exact'], result['samples']), (2016, 2016))
            self.assertEqual(result['max_channel_delta'], 0)
            self.assertFalse(result['production_admitted'])
            expected.extend(tuple(row['pixels'][-1]) for row in result['rows'])
        image = Image.open(EVIDENCE/'composition/gpu.png').convert('RGBA')
        self.assertEqual(image.size, (64, 63))
        self.assertEqual(list(image.getdata()), expected)

    def test_missing_reordered_duplicate_and_corrupt_native_events_reject(self):
        build = json.loads((EVIDENCE/'bitmap/build.json').read_text())
        lines = (EVIDENCE/'bitmap/native.log').read_text().splitlines()
        for changed in (lines[:-1], lines[1:], [lines[1], lines[0], *lines[2:]],
                        [*lines, lines[-1]], [lines[0].replace('|normal|', '|unexpected|'), *lines[1:]],
                        [lines[0]+',123', *lines[1:]]):
            with self.subTest(first=changed[0][:100]):
                with self.assertRaises(ValueError):
                    decode(build, '\n'.join(changed))

    def test_one_channel_native_mutation_is_not_a_pass(self):
        build = json.loads((EVIDENCE/'bitmap/build.json').read_text())
        lines = (EVIDENCE/'bitmap/native.log').read_text().splitlines()
        fields = lines[0].split('|')
        values = fields[-1].split(',')
        values[-1] = str(int(values[-1]) + 1)
        fields[-1] = ','.join(values)
        lines[0] = '|'.join(fields)
        rows = decode(build, '\n'.join(lines))
        self.assertNotEqual(predict(rows[0], False), rows[0]['pixels'][-1])

    def test_vector_and_bitmap_opacity_have_distinct_input_semantics(self):
        vector = analyze(EVIDENCE/'vector', True)['rows']
        bitmap = analyze(EVIDENCE/'bitmap', False)['rows']
        # Vector alpha is transformed before RGB premultiplication.
        key = [0, 0, 0, 63, 99, 100]
        v = next(r for r in vector if r['key'] == key)
        b = next(r for r in bitmap if r['key'] == key)
        self.assertEqual(v['pixels'][-1], [17, 48, 58, 62])
        self.assertEqual(b['pixels'][-1], [16, 47, 57, 62])
        self.assertNotEqual(predict(v, False), v['pixels'][-1])

    def test_wrapper_uses_same_pinned_native_with_zero_tolerance(self):
        output = EVIDENCE/'composition/wrapper'
        report = compare(fixture(), output)
        stages = analyze_stages(fixture(), output)
        self.assertEqual((report['exact'], report['images']), (4, 4))
        self.assertTrue(path_passed(report, stages))
        self.assertFalse(report['production_admitted'])
        changed = copy.deepcopy(report)
        changed.update(exact=3, wrapper_passed=False)
        self.assertFalse(path_passed(changed, stages))

    def test_provenance_and_nonassociative_byte_order(self):
        provenance = json.loads((EVIDENCE/'composition/provenance.json').read_text())
        for path, expected in provenance['source_sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(), expected, path)
        for path, expected in provenance['native_sha256'].items():
            self.assertEqual(hashlib.sha256((EVIDENCE/path).read_bytes()).hexdigest(), expected, path)
        self.assertEqual(hashlib.sha256((EVIDENCE/'composition/gpu.png').read_bytes()).hexdigest(),
                         provenance['gpu_sha256'])
        back, middle, front = [48]*3+[128], [32]*3+[64], [7]*3+[15]
        self.assertNotEqual(over(back, over(middle, front)), over(over(back, middle), front))
