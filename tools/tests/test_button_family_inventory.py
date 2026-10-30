"""Source-bound s271 inventory and fail-closed coverage negatives."""
import copy
import importlib.util
import unittest
from pathlib import Path
import xml.etree.ElementTree as ET
import tarfile
import json

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('s271', ROOT / 'evidence/sampling-upgrade/s271/diagnose.py')
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class ButtonFamilyInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = audit.diagnose()
        cls.scripts = {s['path']: s['source'] for s in json.loads((ROOT / 'scripts/main.json').read_text())['scripts']}

    def test_two_uninstrumented_source_events(self):
        family = self.report['family']
        self.assertEqual(len(family), 2)
        self.assertTrue(all(not r['instrumented'] for r in family))
        self.assertTrue(all('gotoAndStop(1);' in r['source'] for r in family))

    def test_missing_family_member_rejected(self):
        with self.assertRaisesRegex(ValueError, 'button family'):
            audit.select_family(self.report['family'][:1], self.scripts)

    def test_instrumentation_whitening_rejected(self):
        records = copy.deepcopy(self.report['family'])
        records[0]['instrumented'] = True
        with self.assertRaisesRegex(ValueError, 'unexpectedly instrumented'):
            audit.select_family(records, self.scripts)

    def test_source_mutation_rejected(self):
        scripts = dict(self.scripts)
        scripts[self.report['family'][0]['path']] = 'gotoAndStop(2);'
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            audit.select_family(self.report['family'], scripts)

    def test_complete_menu_frames_and_stops(self):
        frames = self.report['source']['menu_frames']
        self.assertEqual([f['frame'] for f in frames], list(range(1, 11)))
        self.assertEqual([f['frame'] for f in frames if f['scripts']], [1, 10])
        self.assertEqual([f['frame'] for f in frames for t in f['tags']
                          if t.get('characterId') == '2009'], [10])

    def test_wrong_placement_rejected(self):
        with tarfile.open(ROOT / 'evidence/sampling-upgrade/s30/source-exports.tar.gz') as archive:
            xml = ET.fromstring(archive.extractfile(audit.MEMBER).read())
        for item in xml.iter('item'):
            if item.get('characterId') == '2009':
                item.set('placeFlagMove', 'true')
        with self.assertRaisesRegex(ValueError, 'placement chain'):
            audit.source_inventory(xml, self.scripts)

    def test_entry_absence_is_not_nonexecution_or_return(self):
        self.assertIsNone(self.report['button_dispatch_observed'])
        self.assertIsNone(self.report['button_return_observed'])
        self.assertFalse(self.report['thin_coverage_cut_proved'])
        self.assertFalse(self.report['production_admitted'])
        self.assertFalse(self.report['native_parity_proven'])
        self.assertEqual(self.report['product_obligations_closed'], 0)
        self.assertFalse(self.report['continuation_context']['exit_model_fix_proved'])

    def test_locked_full_stream_and_strict_gate(self):
        self.assertEqual((self.report['events'], self.report['root_samples']), (9774, 61))
        self.assertEqual((self.report['unvisited'], self.report['uninstrumented']), (594, 415))
        self.assertEqual(self.report['strict_full_as_exit'], 1)


if __name__ == '__main__':
    unittest.main()
