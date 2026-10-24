import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools.probes.nested_composition import cases, predicted, decode, compare, read_atlases

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT/'evidence/importer-loud-fail/r37'


class NestedCompositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = decode(EVIDENCE/'native')

    def test_explicit_native_buffers_and_actual_production_nodes_are_exact(self):
        for actual in ([predicted(c) for c in cases()], read_atlases(EVIDENCE/'fresh')):
            result = compare(self.native, actual)
            self.assertTrue(result['passed'])
            self.assertFalse(result['production_admitted'])
            for stage, count in (('child',27648), ('parent',41472), ('final',55296)):
                self.assertEqual(result['scores'][stage]['pixels'], count)
                self.assertEqual(result['scores'][stage]['exact'], count)
                self.assertEqual(result['scores'][stage]['max_delta'], 0)

    def test_premature_destination_copy_is_a_real_pixel_failure(self):
        result = compare(self.native, read_atlases(EVIDENCE/'stale'))
        self.assertFalse(result['passed'])
        self.assertEqual(result['scores']['child']['exact'], 27648)
        self.assertEqual(result['scores']['parent']['exact'], 13824)
        self.assertEqual(result['scores']['final']['exact'], 33152)
        self.assertEqual(result['scores']['final']['max_delta'], 128)
        log = (EVIDENCE/'stale/godot.log').read_text()
        self.assertNotIn('ERROR', log)
        self.assertIn('NESTED_BUFFER_DIAGNOSTIC_OK cases=432 order=stale', log)

    def test_single_channel_error_and_missing_boundaries_fail(self):
        actual = copy.deepcopy(self.native)
        actual[0]['final'][0][0] ^= 1
        self.assertFalse(compare(self.native, actual)['passed'])
        for changed in (actual[:-1], copy.deepcopy(self.native)):
            if len(changed) == 432:
                del changed[0]['parent']
            with self.assertRaises(ValueError):
                compare(self.native, changed)

    def test_native_missing_completion_duplicate_or_wrong_stage_reject(self):
        lines = (EVIDENCE/'native/native.log').read_text().splitlines()
        build = (EVIDENCE/'native/build.json').read_text()
        corrupt = lines.copy()
        corrupt[2] = corrupt[2].replace(',child,', ',unknown,')
        for changed in (lines[:-1], [*lines, lines[-1]], corrupt):
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory)
                (path/'build.json').write_text(build)
                (path/'native.log').write_text('\n'.join(changed))
                with self.assertRaises(ValueError):
                    decode(path)

    def test_materialized_input_premultiplication_is_independently_checked(self):
        lines = (EVIDENCE/'native/native.log').read_text().splitlines()
        fields = lines[1].split('|')
        pixel = fields[-1].split(',')
        pixel[-1] = str(int(pixel[-1])+1)
        fields[-1] = ','.join(pixel)
        lines[1] = '|'.join(fields)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path/'build.json').write_bytes((EVIDENCE/'native/build.json').read_bytes())
            (path/'native.log').write_text('\n'.join(lines))
            with self.assertRaisesRegex(ValueError, 'premultiplication'):
                decode(path)

    def test_provenance_preserves_production_nodes_and_readbacks(self):
        for order in ('fresh','stale'):
            provenance = json.loads((EVIDENCE/order/'provenance.json').read_text())
            self.assertFalse(provenance['production_admitted'])
            for path, digest in provenance['source_sha256'].items():
                self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(), digest, path)
            for path, digest in provenance['readback_sha256'].items():
                self.assertEqual(hashlib.sha256((EVIDENCE/order/path).read_bytes()).hexdigest(), digest, path)
            for path, digest in provenance['native_sha256'].items():
                self.assertEqual(hashlib.sha256((EVIDENCE/'native'/path).read_bytes()).hexdigest(), digest, path)
            records = json.loads((EVIDENCE/order/'buffers.json').read_text())
            self.assertEqual(len(records), 432)
            for i, record in enumerate(records):
                self.assertEqual(record, {'case':i,'sizes':[[8,8],[12,8]],'origins':[[2,0],[2,0]],
                                          'copy_order':order,'production_admitted':False})
