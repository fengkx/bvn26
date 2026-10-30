"""Source-bound query evidence must not become an unready-receiver exemption."""
import gzip
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'evidence/sampling-upgrade/s264'


def load(name):
    spec = importlib.util.spec_from_file_location('s264_' + name, HERE / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ReceiverAuthoredQueryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load('diagnose')
        cls.builder = load('build_probe')
        cls.raw = gzip.decompress((HERE / 'native-capture.log.gz').read_bytes()).decode()
        cls.report = cls.module.diagnose()

    def test_recompute_and_preserve_limits(self):
        self.assertEqual(self.report, json.loads((HERE / 'diagnosis.json').read_text()))
        for flag in ('production_admitted', 'native_parity_proven', 'eligibility_fix_proved',
                     'pre_init_authored_query_proved', 'all_collision_paths_observed'):
            self.assertFalse(self.report[flag])
        for kind in ('state', 'input_next_display', 'key_read'):
            self.assertTrue(self.report['comparison'][kind]['exact_tick_payload_equal_s260'])
        self.assertEqual(self.report['comparison']['state']['rows'], 122)
        self.assertEqual(self.report['geometry_samples'], 61)

    def test_observed_queries_follow_initialization(self):
        interval = self.report['unready_interval']
        self.assertEqual(interval['observed_query_rows'], [])
        rows = self.report['query_rows']
        self.assertEqual(len(rows), 12)
        self.assertTrue(all(r['sequence'] > interval['initialized_sequence'] for r in rows))
        for tick, parent in ((11, '841'), (12, '842')):
            selected = [r for r in rows if r['tick'] == tick]
            self.assertEqual({r['parent_frame'] for r in selected}, {parent})
            queries = [r for r in selected if r['phase'] == 'getHitObj_entry']
            self.assertEqual([(r['operand_path'], r['suffix'], r['array_length']) for r in queries],
                             [('_level0.game.p2.mc', 'atm', '96'), ('_level0.game.p2fz', '', '5')])
            result = selected[-1]
            self.assertEqual((result['phase'], result['result_type'], result['result_value']),
                             ('checkHit_result', 'undefined', 'undefined'))
        self.assertNotIn('fighter_helper_operand', self.report['query_phase_counts'])
        self.assertNotIn('stage_operand', self.report['query_phase_counts'])

    def test_missing_duplicate_and_foreign_query_rejected(self):
        lines = self.raw.splitlines()
        for line in lines:
            if '|s264_query|' not in line:
                continue
            with self.subTest(line=line):
                with self.assertRaises(ValueError):
                    self.module.query_rows('\n'.join(l for l in lines if l != line))
                with self.assertRaises(ValueError):
                    self.module.query_rows(self.raw + '\n' + line)
        marker = next(l for l in lines if '|s264_query|' in l)
        for changed in (marker.replace('beida_entry', 'invented'), marker.replace('|11|s264_query|', '|41|s264_query|'), marker.replace('%2Ep1%2E', '%2Ep2%2E')):
            with self.assertRaises(ValueError):
                self.module.query_rows(self.raw.replace(marker, changed))

    def test_strict_geometry_gap_preserved(self):
        for sample in self.report['selected_geometry']:
            present = any(b['role'] == 'hurt' and '.game.p1.' in b['path'] for b in sample['boxes'])
            self.assertEqual(present, sample['tick'] != 11)

    def test_authored_instructions_unchanged_and_boundaries_unique(self):
        bundle = json.loads((ROOT / 'scripts/fighter/didala.json').read_text())
        source = next(s['source'] for s in bundle['scripts'] if s['path'] == self.builder.RECEIVER).replace('\r\n', '\n')
        patched = self.builder.patch_receiver(source)
        stripped = ''.join(line for line in patched.splitlines(True) if '_root.s264Query(' not in line)
        self.assertEqual(stripped, source)
        for invalid in ('', source + source):
            with self.assertRaises(ValueError):
                self.builder.patch_receiver(invalid)
        observer = (HERE / 'observer.as').read_text()
        for call in ('.getHitObj(', '.getStgHitObj(', '.hitTest(', '.beida('):
            self.assertNotIn(call, observer)


if __name__ == '__main__':
    unittest.main()
