"""Reject evidence promotion, container mutation and incomplete retained replay."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent


def load(name):
    spec = importlib.util.spec_from_file_location('s364_' + name, HERE / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


d = load('diagnose')
e = load('extract_native')


class DiagnosisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prior = d.replay()
        cls.route = json.loads((HERE / 'native-route.json').read_text())

    def test_packed_member_is_not_a_registration(self):
        record = d.audit(self.route)
        self.assertEqual(record['container']['method_member_index'], 17)
        self.assertEqual(record['container']['removal_name_member_index'], 19)
        self.assertEqual(record['reference_search']['rip_lea_candidates'], [])
        self.assertEqual(record['reference_search']['exact_u64_file_offsets'], [])
        self.assertIsNone(record['method_registration'])
        self.assertIsNone(record['independent_outer_lifetime'])

    def test_every_rehashed_container_byte_rejected(self):
        for i in range(328):
            row = copy.deepcopy(self.route)
            raw = bytearray.fromhex(row['container']['hex'])
            raw[i] ^= 1
            row['container'].update(hex=raw.hex(), sha256=d.sha(raw))
            with self.subTest(i=i), self.assertRaises(ValueError):
                d.audit(row)

    def test_provenance_scope_and_fabricated_live_binding_rejected(self):
        for key in self.route:
            row = copy.deepcopy(self.route)
            row[key] = 'fabricated'
            with self.subTest(key=key), self.assertRaises(ValueError):
                d.audit(row)
        with self.assertRaises(ValueError):
            d.audit(self.route | {'production_admitted': True})

    def test_complete_prior_replay_required(self):
        for key in ('production_admitted', 'qualification_matrix', 'blocker'):
            with patch.object(d, 'load_prior') as loader:
                loader.return_value.diagnose.return_value = self.prior | {key: 'changed'}
                with self.assertRaises(ValueError):
                    d.replay()

    def test_pin_change_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'pins.json'
            p.write_text(json.dumps({'evidence/sampling-upgrade/s355/diagnosis.json': 'wrong'}))
            with self.assertRaises(ValueError):
                d.verify_pins(p)

    def test_binary_substitution_rejected(self):
        with self.assertRaises(ValueError):
            e.extract(b'not the receipt-matching binary')

    def test_search_keeps_embedded_and_overlapping_matches(self):
        self.assertEqual(e.occurrences(b'xgotoAndStop,y', b'gotoAndStop'), [1])
        self.assertEqual(e.occurrences(b'aaaa', b'aa'), [0, 1, 2])

    def test_all_ten_targets_and_controls_remain_unproved(self):
        report = d.diagnose()
        self.assertEqual(report['retained'], self.prior)
        self.assertEqual(report['qualification_matrix'], self.prior['qualification_matrix'])
        self.assertEqual([r['frame'] for r in report['qualification_matrix']], list(range(1, 11)))
        self.assertTrue(all(r['independent_entry'] is None for r in report['qualification_matrix']))
        self.assertTrue(all(v is None for v in report['observations'].values()))
        self.assertTrue(all(not g['proved'] for g in report['gates'].values()))
        self.assertTrue(all(not c['executed'] and c['qualified'] is None for c in report['controls'].values()))
        self.assertFalse(report['production_admitted'])
        self.assertFalse(report['native_parity_proven'])
        self.assertFalse(report['fresh_capture_eligible'])
        self.assertEqual(report['m0_02_status'], 'pending')
        self.assertEqual(report['other_ranks_executed'], [])


if __name__ == '__main__':
    unittest.main()
