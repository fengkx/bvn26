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
