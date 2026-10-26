"""Failed native candidates must remain failed, and capture IDs must be fresh."""
import copy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'probes'))
from compare_placement_candidates import compare
from build_flash_filter_probe import build


class PlacementCandidateOracleTests(unittest.TestCase):
    def test_one_channel_difference_rejects_both_candidate_families(self):
        for kind, native, actual in [('blend', [{'premultiplied': [0, 1, 2, 3]}], [[0, 1, 2, 3]]),
                                     ('shadow', [{'pixels': [[0, 1, 2, 3]]}], [[[0, 1, 2, 3]]])]:
            self.assertTrue(compare(native, actual, kind)['passed'])
            wrong = copy.deepcopy(actual)
            if kind == 'blend':
                wrong[0][0] += 1
            else:
                wrong[0][0][3] += 1
            result = compare(native, wrong, kind)
            self.assertFalse(result['passed'])
            self.assertEqual(result['cases'][0]['different'], 1)
            with self.assertRaises(ValueError):
                compare(native, [], kind)

    def test_repeated_probe_builds_get_distinct_capture_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            ffdec = directory / 'ffdec.jar'
            ffdec.write_bytes(b'test compiler')
            def compile_fixture(command, **kwargs):
                Path(command[-2]).write_bytes(b'test movie')
            with patch('build_flash_filter_probe.subprocess.run', side_effect=compile_fixture):
                first = build('drop-shadow', directory / 'first', ffdec)
                second = build('drop-shadow', directory / 'second', ffdec)
            self.assertNotEqual(first['run_id'], second['run_id'])
            self.assertEqual(first['source_sha256'], second['source_sha256'])
            self.assertNotEqual(first['instrumented_sha256'], second['instrumented_sha256'])


class PlacementArithmeticTests(unittest.TestCase):
    def test_decoder_preserves_authored_colors_and_requires_complete_samples(self):
        from decode_placement_blend_capture import decode
        build = {'run_id': 'test', 'cases': [{'back': 0x3366cc, 'front': 0xcc80aa}]}
        samples = [('back', 0x993266cb), ('front', 0xb2cb7fa9),
                   ('pixel', 0xe094496f), ('black', 0xff824062)]
        trace = '\n'.join(f'AIREF|test|{i}|0|0|0|{kind}|0,{value}'
                          for i, (kind, value) in enumerate(samples))
        trace += '\nAIREF|test|4|0|0|0|done|ok'
        row = decode(build, trace)[0]
        self.assertEqual(row['back'], 0x3366cc)
        self.assertEqual(row['front'], 0xcc80aa)
        self.assertEqual(row['observed_back'], [50, 102, 203, 153])
        self.assertEqual(row['premultiplied'], [130, 64, 98, 224])
        with self.assertRaises(ValueError):
            decode(build, trace.replace('AIREF|test|1|', 'AIREF|test|2|'))
        with self.assertRaises(ValueError):
            decode(build, trace.rsplit('\n', 1)[0])

    def test_opaque_overlay_model_matches_every_native_byte_pair(self):
        import json
        from analyze_placement_arithmetic import grid_report
        root = Path(__file__).resolve().parents[1] / 'probes' / 'flash_filters'
        rows = json.loads((root / 'placement-overlay-grid-native.json').read_text())
        self.assertEqual(len(rows), 256)
        self.assertTrue(all(len(row) == 256 for row in rows))
        report = grid_report(rows)
        self.assertEqual(report['pixels'], 65536)
        self.assertEqual(report['model_differences'], [])
        rows[170][204] += 1
        self.assertEqual(grid_report(rows)['model_differences'], [[204, 170, 221, 220]])

    def test_packaged_blend_inputs_are_not_native_readback(self):
        import json
        from build_placement_blend_probe import cases
        root = Path(__file__).resolve().parents[1] / 'probes' / 'flash_filters'
        rows = json.loads((root / 'placement-blend-native.json').read_text())
        self.assertEqual(len(rows), len(cases()))
        for row, authored in zip(rows, cases()):
            self.assertEqual({key: row[key] for key in authored}, authored)
            self.assertEqual(row['premultiplied'], row['on_black'][:3] + row['output_pixel'][3:])
