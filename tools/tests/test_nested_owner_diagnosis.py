"""Source and retained-evidence negatives for the exclusive s270 diagnosis."""
import gzip
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('s270', ROOT / 'evidence/sampling-upgrade/s270/diagnose.py')
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class NestedOwnerDiagnosisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = audit.diagnose()
        cls.lines = gzip.decompress((ROOT / 'evidence/sampling-upgrade/s247/native-capture.log.gz').read_bytes()).decode().splitlines()

    def test_source_preserves_distinct_fourth_receiver(self):
        sites = self.report['ordered_authored_hit_test_sites']
        self.assertEqual([s['receiver_expression'] for s in sites],
                         ['mian', 'mian', 'mian', 'hitmc.mian', 'mian'])
        source = self.report['outer_clip_actions'][audit.ENTER]
        with self.assertRaisesRegex(ValueError, 'operand chain'):
            audit.operand_sites(source.replace('hitmc.mian', 'mian'))
        with self.assertRaisesRegex(ValueError, 'operand chain'):
            audit.operand_sites(source.replace('_parent.pn', '_parent._parent.pn'))

    def test_full_authored_child_lifetime(self):
        frames = self.report['sprite104_complete_frame_inventory']
        self.assertEqual([f['frame'] for f in frames], list(range(1, 11)))
        self.assertEqual([f['frame'] for f in frames if f['scripts']], [1, 5, 10])
        changes = [(f['frame'], t['attributes']) for f in frames for t in f['tags']
                   if t['attributes'].get('depth') == '2']
        self.assertEqual([(f, t['type']) for f, t in changes],
                         [(1, 'PlaceObject2Tag'), (5, 'RemoveObject2Tag')])
        self.assertEqual(changes[0][1]['placeFlagMove'], 'false')
        self.assertEqual(changes[0][1]['placeFlagHasClipActions'], 'false')

    def test_absent_child_does_not_remove_parent(self):
        observed = self.report['observed']
        root19 = next(r for r in observed['provenance']['observations']
                      if r['phase'] == 'root_sample' and r['tick'] == 19)
        self.assertEqual(root19['present'], 'false')
        parent19 = next(b for b in observed['chain_boxes'] if b['tick'] == 19)
        self.assertEqual((parent19['path'], parent19['frame']), (audit.OUTER, 5))
        self.assertFalse(self.report['runtime_binding_proved'])
        self.assertIsNone(observed['exact_parent_rename_observation'])
        self.assertIsNone(observed['exact_operand_call_observation'])

    def test_missing_parent_boundary_rejects(self):
        changed = [line for line in self.lines if not (
            '|19|geometry_box|attack,' + audit.OUTER + ',' in line)]
        with self.assertRaisesRegex(ValueError, 'outer sampled lifetime'):
            audit.observe(changed)

    def test_wrong_parent_source_rejects(self):
        changed = [line.replace('DefineSprite_104/frame_1', 'DefineSprite_2/frame_1')
                   if '|geometry_box|attack,' + audit.OUTER + ',' in line else line
                   for line in self.lines]
        with self.assertRaisesRegex(ValueError, 'owner provenance'):
            audit.observe(changed)

    def test_changed_locked_bytes_reject(self):
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            audit.check_hash(b'wrong source', '0' * 64)


if __name__ == '__main__':
    unittest.main()
