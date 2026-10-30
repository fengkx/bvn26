"""Retained native observations, bounded insertion, and missing-evidence negatives."""
import gzip
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'evidence/sampling-upgrade/s255'


def load(name):
    spec = importlib.util.spec_from_file_location('s255_' + name, HERE / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AImainUnloadIdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.diagnosis = load('diagnose')
        cls.builder = load('build_probe')
        cls.raw = gzip.decompress((HERE / 'native-capture.log.gz').read_bytes()).decode()
        cls.report = cls.diagnosis.diagnose()

    def test_retained_report_recomputes_without_external_cache(self):
        self.assertEqual(self.report, json.loads((HERE / 'diagnosis.json').read_text()))
        self.assertFalse(self.report['mapping_fix_proved'])
        self.assertFalse(self.report['production_admitted'])
        self.assertFalse(self.report['native_parity_proven'])
        self.assertEqual(self.report['actor_comparison']['rows'], 122)
        self.assertTrue(self.report['actor_comparison']['all_14_fields_equal'])

    def test_native_boundary_observations_preserve_content_loss(self):
        phases = self.report['phases']
        for phase in self.diagnosis.PHASES:
            row = phases[phase]
            self.assertEqual(row['saved_equals_occupant'], 'true')
            self.assertEqual(row['named_equals_occupant'], 'true')
            parent = row['objects']['parent']
            self.assertEqual(parent['token'], 's255-parent-1')
            for role in ('saved_receiver', 'depth_occupant', 'named_receiver'):
                node = row['objects'][role]
                self.assertEqual(node['depth'], '-16383')
                self.assertEqual(node['child_count'], '0')
                if phase == 'first_sample':
                    self.assertEqual((node['frame'], node['total_frames']), ('0', '0'))
                    self.assertEqual((node['source_stamp'], node['token']), ('undefined', 'undefined'))
                    self.assertEqual(node['display_id'], self.report['first_sample_node']['instance_id'])
                else:
                    self.assertEqual((node['frame'], node['total_frames']), ('1', '2'))
                    self.assertEqual(node['token'], 's255-receiver-1')
        self.assertEqual(phases['after_unload']['display'], phases['before_unload']['display'])
        self.assertEqual(phases['next_root']['display'], phases['after_unload']['display'] + 1)
        self.assertEqual(phases['first_sample']['tick'], 0)

    def test_unloaded_content_is_not_an_authored_frame_or_gate_exception(self):
        node = self.report['first_sample_node']
        self.assertEqual((node['symbol'], node['frame']), (3, 0))
        self.assertNotIn('authored_children', node)
        self.assertEqual(self.report['source_gap_count'], 169)
        self.assertIn({'tick': 0, 'path': '_level0.game.p1.mc.AImain',
                       'reason': 'missing source frame'}, self.report['source_gaps'])
        self.assertEqual(self.report['authored_slot']['frame_child_depths'][0], [])
        self.assertTrue(self.report['authored_slot']['frame_child_depths'][1])

    def test_missing_phase_or_object_cannot_prove_a_lifetime(self):
        for marker in ('|aimain_identity|after_unload,', '|aimain_object|first_sample,depth_occupant,'):
            with self.subTest(marker=marker):
                text = '\n'.join(line for line in self.raw.splitlines() if marker not in line)
                with self.assertRaises(ValueError):
                    self.diagnosis.parse_lifetime(text)

    def test_duplicate_identity_is_rejected(self):
        line = next(line for line in self.raw.splitlines() if '|aimain_identity|before_unload,' in line)
        with self.assertRaises(ValueError):
            self.diagnosis.parse_lifetime(self.raw + '\n' + line)

    def test_insertion_keeps_authored_unload_and_refuses_ambiguous_sites(self):
        bundle = json.loads((ROOT / 'scripts/fighter/yijiao.json').read_text())
        source = next(s['source'] for s in bundle['scripts'] if s['path'] == self.builder.SCRIPT).replace('\r\n', '\n')
        patched = self.builder.patch_fighter(source)
        for phase in ('before_unload', 'after_unload'):
            patched = patched.replace(f'      _global.s255Observe("{phase}", AImain);\n', '')
        self.assertEqual(patched, source)
        for invalid in ('', source + source):
            with self.assertRaises(ValueError):
                self.builder.patch_fighter(invalid)
        for transform in (self.builder.patch_root, self.builder.patch_hooks):
            with self.assertRaises(ValueError):
                transform('')


if __name__ == '__main__':
    unittest.main()
