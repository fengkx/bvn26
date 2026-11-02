"""Reject missing evidence and conflation of sampled frames with target entry."""
import copy
import gzip
import importlib.util
import json
from pathlib import Path
import tarfile
import unittest

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('s282', HERE / 'diagnose.py')
s282 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(s282)


class ChildClockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.events = s282.locked.events_from(gzip.decompress((HERE.parent / 's274/native-capture.log.gz').read_bytes()))
        cls.contract = json.loads((HERE.parent / 's262/source-contract.json').read_text())
        cls.scripts = json.loads((s282.ROOT / 'scripts/main.json').read_text())
        with tarfile.open(HERE.parent / 's274/native-build.tar.gz') as archive:
            cls.patch = archive.extractfile('s274-patches/DefineSprite_1810/frame_1/DoAction.as').read().decode()

    def frames(self):
        return s282.source_frames(self.contract, self.scripts, self.patch)

    def test_full_replay_and_observability(self):
        r = s282.diagnose()
        self.assertEqual((r['events_revalidated'], r['callback_count']), (26828, 63))
        self.assertEqual(r['uninstrumented_target_windows'], 45)
        self.assertEqual(r['natural_encoding_entry_joins'], 4)
        self.assertFalse(r['independent_child_clock_proved'])
        self.assertFalse(r['production_admitted'])
        self.assertFalse(r['native_parity_proven'])
        for row in r['callback_windows']:
            if row['classification'] != 'entry_observed':
                self.assertIsNone(row['independent_target_entry_observed'])

    def test_empty_authored_frame_not_inferred_stop(self):
        frames = self.frames()
        self.assertEqual(frames[0]['authored_script'], 'stop();')
        self.assertTrue(all(f['authored_script'] is None for f in frames[1:]))
        self.assertTrue(all(f['glyph_move'] for f in frames[1:]))

    def test_added_source_script_rejected(self):
        scripts = copy.deepcopy(self.scripts)
        scripts['scripts'].append({'path': 'DefineSprite_1810/frame_2/DoAction.as', 'source': 'stop();'})
        with self.assertRaisesRegex(ValueError, 'authored digit'):
            s282.source_frames(self.contract, scripts, self.patch)

    def test_changed_glyph_placement_rejected(self):
        contract = copy.deepcopy(self.contract)
        contract['symbols']['1810']['changes'][1]['tag'] = contract['symbols']['1810']['changes'][1]['tag'].replace('1801', '1800')
        with self.assertRaisesRegex(ValueError, 'digit placement'):
            s282.source_frames(contract, self.scripts, self.patch)

    def test_added_observer_rejected(self):
        with self.assertRaisesRegex(ValueError, 'entry hook'):
            s282.source_frames(self.contract, self.scripts, self.patch + 'play();\n')

    def test_missing_callback_rejected(self):
        events = copy.deepcopy(self.events)
        del events[next(i for i, e in enumerate(events) if e['kind'] == 's258_countdown' and e['value'].startswith('fire_after,'))]
        with self.assertRaisesRegex(ValueError, 'sequence'):
            s282.audit(events, self.frames())

    def test_wrong_generation_rejected(self):
        events = copy.deepcopy(self.events)
        entry = next(e for e in events if e['kind'] == 's274_entry' and '.个,' in e['value'] and e['tick'] == 17)
        entry['value'] = entry['value'].replace(',-16381,1,1', ',-16381,3,1')
        with self.assertRaisesRegex(ValueError, 'generation'):
            s282.audit(events, self.frames())

    def test_mixed_run_rejected(self):
        events = copy.deepcopy(self.events)
        events[-1]['run'] = 'another-run'
        with self.assertRaisesRegex(ValueError, 'mixed capture'):
            s282.audit(events, self.frames())

    def test_synchronous_frame_reads_do_not_fill_missing_entries(self):
        r = s282.audit(self.events, self.frames())
        self.assertEqual(sum(f['callback_selections'] for f in r['frames']), 63)
        self.assertTrue(all(f['windows_with_entry'] == 0 for f in r['frames'][1:]))
        self.assertFalse(r['scene_state_admitted'])


if __name__ == '__main__':
    unittest.main()
