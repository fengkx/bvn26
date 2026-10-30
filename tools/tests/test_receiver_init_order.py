"""Lock source-backed receiver initialization order and reject missing evidence."""
import gzip
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'evidence/sampling-upgrade/s260'


def load(name):
    spec = importlib.util.spec_from_file_location('s260_' + name, HERE / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ReceiverInitOrderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load('diagnose')
        cls.builder = load('build_probe')
        cls.raw = gzip.decompress((HERE / 'native-capture.log.gz').read_bytes()).decode()
        cls.report = cls.module.diagnose()

    def test_portable_evidence_and_controls(self):
        self.assertEqual(self.report, json.loads((HERE / 'diagnosis.json').read_text()))
        for flag in ('production_admitted', 'native_parity_proven', 'eligibility_fix_proved'):
            self.assertFalse(self.report[flag])
        self.assertEqual(self.report['comparison']['state'], {'rows': 122, 'exact_tick_payload_equal_s256': True})
        for kind in ('input_next_display', 'key_read'):
            self.assertTrue(self.report['comparison'][kind]['exact_tick_payload_equal_s256'])
        self.assertEqual(self.report['geometry_samples'], 61)

    def test_observed_order_not_inferred_tick_order(self):
        rows = self.report['observations']
        self.assertEqual([(r['tick'], r['phase'], r['parent_frame']) for r in rows], [
            (10, 'root_before_geometry', '1'), (10, 'jump_before', '2'),
            (11, 'root_before_geometry', '840'), (11, 'frame840_entry', '840'),
            (11, 'frame1_entry', '840'), (11, 'frame1_exit', '840'),
            (11, 'enterFrame_before', '841'), (11, 'enterFrame_after', '841'),
            (12, 'root_before_geometry', '841'),
            (12, 'enterFrame_before', '842'), (12, 'enterFrame_after', '842')])
        for row in rows[2:5]:
            for field in self.module.FIELDS[3:]:
                self.assertEqual(row[field], 'undefined')
        for row in rows[5:]:
            self.assertEqual([row[f] for f in self.module.FIELDS[3:11]],
                             ['function', 'function', 'object', 'object', 'object', '96', '5', '10'])
            self.assertEqual(row['stamp_id'], rows[5]['stamp_id'])
        self.assertEqual(int(rows[5]['stamp_birth']), rows[2]['display'])
        # aiFight/display are root counters: callback at parent841 still carries tick11.
        self.assertEqual(rows[5]['display'], rows[6]['display'])

    def test_sample_finishes_before_frame1_entry(self):
        rows = self.report['observations']
        boundary = [r for r in self.report['geometry_boundaries'] if r['tick'] == 11]
        self.assertEqual([r['kind'] for r in boundary], ['geometry_begin', 'geometry_end'])
        self.assertLess(rows[2]['sequence'], boundary[0]['sequence'])
        self.assertLess(boundary[0]['sequence'], boundary[1]['sequence'])
        self.assertLess(boundary[1]['sequence'], rows[3]['sequence'])
        self.assertLess(rows[3]['sequence'], rows[4]['sequence'])

    def test_unchanged_geometry_gap(self):
        for sample in self.report['selected_geometry']:
            present = any(b['role'] == 'hurt' and '.game.p1.' in b['path'] for b in sample['boxes'])
            self.assertEqual(present, sample['tick'] != 11)

    def test_each_required_marker_missing_or_duplicated_rejects(self):
        lines = self.raw.splitlines()
        for line in lines:
            if '|s260_order|' not in line:
                continue
            with self.subTest(line=line):
                with self.assertRaises(ValueError):
                    self.module.observations('\n'.join(l for l in lines if l != line))
                with self.assertRaises(ValueError):
                    self.module.observations(self.raw + '\n' + line)

    def test_foreign_phase_scope_and_order_reject(self):
        marker = next(l for l in self.raw.splitlines() if '|s260_order|' in l)
        for changed in (marker.replace('root_before_geometry', 'unknown'),
                        marker.replace('|10|s260_order|', '|41|s260_order|'),
                        marker.replace('%2Ep1%2E', '%2Ep2%2E')):
            with self.assertRaises(ValueError):
                self.module.observations(self.raw.replace(marker, changed))
        lines = self.raw.splitlines()
        indices = [i for i, l in enumerate(lines) if '|s260_order|' in l]
        a, b = indices[:2]
        lines[a], lines[b] = lines[b], lines[a]
        with self.assertRaises(ValueError):
            self.module.observations('\n'.join(lines))

    def test_insertions_preserve_authored_instructions(self):
        builder = self.builder
        source = 'before\n   _root.aiGeometrySample();\nafter\n'
        self.assertEqual(builder.patch_root(source).replace('   ' + builder.observe('root_before_geometry', '_root.game.p1.mc.bdmn') + '\n', ''), source)
        bundle = {s['path']: s['source'] for s in json.loads((ROOT / 'scripts/fighter/didala.json').read_text())['scripts']}
        for path, transform in [(builder.CONTROLLER, builder.patch_controller),
                                (builder.RECEIVER, builder.patch_receiver),
                                (builder.ENTER_FRAME, builder.patch_enter_frame)]:
            before = bundle[path].replace('\r\n', '\n')
            patched = transform(before)
            stripped = ''.join(l for l in patched.splitlines(True) if '_root.s260Observe(' not in l)
            self.assertEqual(stripped.rstrip(), before.rstrip())
        for transform, valid in ((builder.patch_root, source),
                                 (builder.patch_controller, bundle[builder.CONTROLLER]),
                                 (builder.patch_enter_frame, bundle[builder.ENTER_FRAME])):
            for invalid in ('', valid + valid):
                with self.assertRaises(ValueError):
                    transform(invalid)


if __name__ == '__main__':
    unittest.main()
