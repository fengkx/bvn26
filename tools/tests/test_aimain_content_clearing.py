"""Bounded native content-clearing evidence and discriminator falsification."""
import gzip
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'evidence/sampling-upgrade/s261'


def load(name):
    spec = importlib.util.spec_from_file_location('s261_' + name, HERE / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ContentClearingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load('diagnose')
        cls.builder = load('build_probe')
        cls.raw = gzip.decompress((HERE / 'native-capture.log.gz').read_bytes()).decode()
        cls.report = cls.module.diagnose()

    def test_portable_report(self):
        self.assertEqual(self.report, json.loads((HERE / 'diagnosis.json').read_text()))
        for key in ('mapping_fix_proved', 'production_admitted', 'native_parity_proven',
                    'identity_discriminator_valid_for_cleared_content'):
            self.assertFalse(self.report[key])
        self.assertEqual(self.report['actor_comparison']['rows'], 122)
        self.assertTrue(self.report['actor_comparison']['all_14_fields_equal'])
        self.assertEqual(self.report['source_gap_count'], 169)

    def test_contiguous_roots_bound_first_zero(self):
        rows = self.report['observations']
        self.assertEqual([r['display'] for r in rows[:4]], [7, 7, 8, 9])
        for index, row in enumerate(rows):
            for role in self.module.ROLES[1:]:
                obj = row['objects'][role]
                self.assertEqual((obj['frame'], obj['total_frames']),
                                 ('1', '2') if index < 3 else ('0', '0'))
                self.assertEqual(obj['token'], 's261-receiver-1' if index < 3 else 'undefined')
            self.assertEqual(row['objects']['parent']['token'], 's261-parent-1')
        self.assertEqual(rows[3]['objects']['parent']['frame'], '2')
        self.assertEqual(self.report['authored_slot']['placement'],
                         self.report['authored_slot']['parent_frame2_aimain_slot'])

    def test_independent_controls_falsify_identity_shortcuts(self):
        controls = self.report['controls']
        self.assertEqual(controls['retained'], ['true', 'true'])
        self.assertEqual(controls['replaced'], ['true', 'false'])
        self.assertEqual(controls['retained_content_deleted'], controls['replaced'])

    def test_missing_root_or_control_rejected(self):
        for marker in ('|8|-1|aimain_', '|s261_control|replaced,',
                       '|aimain_object|root,depth_occupant,'):
            with self.subTest(marker=marker), self.assertRaises(ValueError):
                self.module.parse_lifetime('\n'.join(l for l in self.raw.splitlines() if marker not in l))

    def test_duplicate_root_rejected(self):
        lines = self.raw.splitlines()
        index = next(i for i, l in enumerate(lines) if '|8|-1|aimain_identity|' in l)
        with self.assertRaises(ValueError):
            self.module.parse_lifetime('\n'.join(lines[:index] + lines[index:index+5] + lines[index:]))

    def test_authored_unload_preserved(self):
        bundle = json.loads((ROOT / 'scripts/fighter/yijiao.json').read_text())
        source = next(s['source'] for s in bundle['scripts'] if s['path'] == self.builder.SCRIPT).replace('\r\n', '\n')
        patched = self.builder.patch_fighter(source)
        for phase in ('before_unload', 'after_unload'):
            patched = patched.replace(f'      _global.s261Observe("{phase}", AImain);\n', '')
        self.assertEqual(patched, source)
        for invalid in ('', source + source):
            with self.assertRaises(ValueError):
                self.builder.patch_fighter(invalid)
        for transform in (self.builder.patch_root, self.builder.patch_hooks):
            with self.assertRaises(ValueError):
                transform('')


if __name__ == '__main__':
    unittest.main()
