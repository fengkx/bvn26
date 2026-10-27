import json
import tempfile
from unittest.mock import patch
import unittest
from tools.probes.doaction_observer import inventory, instrument
from tools.sampling_doaction import collect, check_inventory, require_full_coverage
from tools.sampling_native import validate
from pathlib import Path


class DoActionTests(unittest.TestCase):
    def bundle(self):
        return {'game_file': 'game/fighter/test.swf', 'swf_sha256': 'locked',
                'scripts': [{'path': 'DefineSprite_1/frame_2/DoAction.as',
                             'source': 'unsupportedCall(speed * 18);'}]}

    def rows(self, record):
        return [f"AIREF|test|1|0|1|0|doaction_entry|{record['id']},_level0.game.p1.mc,2",
                'AIREF|test|2|0|1|0|doaction_sample|root-observer']

    def test_observed_block_is_not_call_execution_proof(self):
        record = inventory(self.bundle())[0]
        result = collect(self.rows(record), 'test', 0, [record])
        self.assertEqual(result['visited'][0]['executions'], 1)
        self.assertFalse(result['statement_call_ownership_proven'])
        with self.assertRaisesRegex(ValueError, 'ownership unproven'):
            require_full_coverage(result)

    def test_source_call_survives_instrumentation_and_changes_identity(self):
        bundle = self.bundle()
        record = inventory(bundle)[0]
        source = bundle['scripts'][0]['source']
        self.assertTrue(instrument(source, record).endswith(source))
        bundle['scripts'][0]['source'] = ''
        changed = inventory(bundle)[0]
        self.assertNotEqual(record['id'], changed['id'])
        with self.assertRaises(ValueError):
            collect(self.rows(record), 'test', 0, [changed])

    def test_missing_entry_sample_and_sequence_reject(self):
        record = inventory(self.bundle())[0]
        rows = self.rows(record)
        for bad in [rows[:1], rows[1:], rows + rows, [rows[0], rows[1].replace('|2|', '|3|', 1)]]:
            with self.assertRaises(ValueError): collect(bad, 'test', 0, [record])
        with self.assertRaises(ValueError): collect(rows, 'test', 1, [record])

    def test_unvisited_and_uninstrumented_are_retained(self):
        bundle = self.bundle()
        bundle['scripts'].append({'path': 'DefineSprite_1/frame_3/DoAction.as', 'source': 'stop();'})
        bundle['scripts'].append({'path': 'frame_1/clip.as', 'source': 'onClipEvent(load) {}'})
        records = inventory(bundle)
        result = collect(self.rows(records[0]), 'test', 0, records)
        self.assertEqual(len(result['unvisited']), 1)
        self.assertEqual(len(result['uninstrumented']), 1)

    def test_dropped_inventory_obligation_rejects(self):
        bundle = self.bundle()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'scripts').mkdir()
            (root/'scripts/test.json').write_text(json.dumps(bundle))
            metadata = {'sampling_doaction': True, 'sources_sha256': {'scripts/test.json': 'bound-by-receipt'},
                        'doaction_inventory': inventory(bundle)}
            with patch('tools.sampling_doaction.ROOT', root):
                self.assertEqual(len(check_inventory(metadata)), 1)
                metadata['doaction_inventory'] = []
                with self.assertRaisesRegex(ValueError, 'dropped/changed'):
                    check_inventory(metadata)

    def test_duplicate_paths_empty_inventory_and_missing_receipt_reject(self):
        bundle = self.bundle()
        bundle['scripts'] *= 2
        with self.assertRaises(ValueError): inventory(bundle)
        with self.assertRaises(ValueError):
            check_inventory({'sampling_doaction': True, 'sources_sha256': {}, 'doaction_inventory': []})
        with self.assertRaises(OSError): validate(Path('missing-case'), Path('missing-native-receipt'))


if __name__ == '__main__':
    unittest.main()
