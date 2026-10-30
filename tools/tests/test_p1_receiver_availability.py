"""Lock native observations and authored placement, never invent eligibility."""
import gzip
import importlib.util
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'evidence/sampling-upgrade/s256'


def load(name):
    spec = importlib.util.spec_from_file_location('s256_' + name, HERE / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class P1ReceiverAvailabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load('diagnose')
        cls.builder = load('build_probe')
        cls.raw = gzip.decompress((HERE / 'native-capture.log.gz').read_bytes()).decode()
        cls.report = cls.module.diagnose()

    def test_portable_evidence_recomputes(self):
        self.assertEqual(self.report, json.loads((HERE / 'diagnosis.json').read_text()))
        for flag in ('production_admitted', 'native_parity_proven', 'eligibility_fix_proved'):
            self.assertFalse(self.report[flag])
        self.assertEqual(self.report['actor_comparison'], {'rows': 122, 'exact_tick_payload_equal_s251': True})

    def test_live_slot_exists_before_receiver_initialization(self):
        rows = self.report['observations']
        self.assertEqual([r['parent_frame'] for r in rows.values()], [1, 840, 841])
        for tick, row in rows.items():
            self.assertEqual(row['named_equals_depth'], 'true')
            self.assertEqual(row['saved_equals_depth'], 'true')
            for obj in row['objects'].values():
                self.assertEqual(obj, row['objects']['named'])
                self.assertEqual((obj['type'], obj['depth'], obj['frame'], obj['total_frames']),
                                 ('movieclip', '-16355', '1', '1'))
                for field in ('getHitObj_type', 'getStgHitObj_type'):
                    self.assertEqual(obj[field], 'undefined' if tick == '11' else 'function')
                for field in ('fs_type', 'fzfs_type', 'stgks_type'):
                    self.assertEqual(obj[field], 'undefined' if tick == '11' else 'object')
        self.assertEqual(rows['11']['objects']['named']['stamp_id'], 'undefined')
        self.assertNotEqual(rows['10']['objects']['named']['stamp_id'], rows['12']['objects']['named']['stamp_id'])
        self.assertEqual(int(rows['12']['objects']['named']['stamp_birth']), rows['11']['display'])

    def test_authored_new_placement_and_no_next_frame_change(self):
        changes = self.report['source']['depth_history_through_841']
        selected = [c for c in changes if c['frame'] >= 826]
        self.assertEqual([c['frame'] for c in selected], [826, 840])
        self.assertEqual(ET.fromstring(selected[0]['tag']).get('type'), 'RemoveObject2Tag')
        placement = ET.fromstring(selected[1]['tag'])
        for key, value in {'type': 'PlaceObject2Tag', 'depth': '29', 'characterId': '2',
                           'name': 'bdmn', 'placeFlagMove': 'false'}.items():
            self.assertEqual(placement.get(key), value)
        # Frame 826 is linear source history, not a claim that the jump executed it.
        self.assertEqual(self.report['source']['label'], {'frame': 840, 'name': '招换'})

    def test_geometry_still_has_no_p1_receiver_at_11(self):
        samples = self.report['selected_geometry']
        for sample in samples:
            present = any(b['role'] == 'hurt' and '.game.p1.' in b['path'] for b in sample['boxes'])
            self.assertEqual(present, sample['tick'] != 11)

    def test_incomplete_or_duplicate_observation_rejects(self):
        for marker in ('|s256_identity|840,', '|s256_object|depth,'):
            broken = '\n'.join(line for line in self.raw.splitlines() if marker not in line)
            with self.assertRaises(ValueError):
                self.module.observations(broken)
        line = next(line for line in self.raw.splitlines() if '|s256_identity|' in line)
        with self.assertRaises(ValueError):
            self.module.observations(self.raw + '\n' + line)

    def test_root_insertion_preserves_existing_sampler(self):
        source = 'before\n   _root.aiGeometrySample();\nafter\n'
        patched = self.builder.patch_root(source)
        self.assertEqual(patched.replace('   _root.s256Observe();\n', ''), source)
        for invalid in ('', source + source):
            with self.assertRaises(ValueError):
                self.builder.patch_root(invalid)


if __name__ == '__main__':
    unittest.main()
