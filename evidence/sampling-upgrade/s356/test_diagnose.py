"""Provenance and fail-closed tests; synthetic SWFs test parsing, not behavior."""
import copy
import importlib.util
import json
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import probe_debug_route as route
spec = importlib.util.spec_from_file_location('s356_diagnose', HERE / 'diagnose.py')
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)


def movie(tags):
    payload = b'\x08\x00\x00\x1e\x01\x00' + tags
    return b'FWS\x08' + struct.pack('<I', len(payload) + 8) + payload


class EvidenceTests(unittest.TestCase):
    def test_complete_replay_and_false_admission(self):
        result = d.diagnose()
        self.assertTrue(result['locked_s347_reproduced'])
        self.assertFalse(result['production_admitted'])
        self.assertFalse(result['native_parity_proven'])
        self.assertTrue(all(not v['proved'] for v in result['gates'].values()))

    def test_changed_prior_replay_rejected(self):
        prior = d.load_prior()
        result = prior.diagnose()
        result['production_admitted'] = True
        with patch.object(prior, 'diagnose', return_value=result), patch.object(d, 'load_prior', return_value=prior):
            with self.assertRaisesRegex(ValueError, 'Complete locked'):
                d.replay()

    def test_forged_identity_rejected(self):
        for field in ('original_defining_scope', 'candidate_activation', 'original_loaded_body', 'same_input_tape'):
            record = d.expected_attempt()
            record[field] = 'stack-or-file-identity'
            with self.subTest(field=field), self.assertRaises(ValueError):
                d.audit_attempt(record)

    def test_false_zero_and_missing_boundary_rejected(self):
        record = d.expected_attempt()
        record['boundaries'][0]['erasure_measurement'] = 0
        with self.assertRaises(ValueError):
            d.audit_attempt(record)
        record = d.expected_attempt()
        record['boundaries'].pop()
        with self.assertRaises(ValueError):
            d.audit_attempt(record)

    def test_wrong_movie_hash_rejected(self):
        with self.assertRaisesRegex(ValueError, 'pinned build receipt'):
            route.inspect(b'wrong', '0' * 64)

    def test_debug_tag_detection(self):
        raw = movie(struct.pack('<H', (63 << 6) | 16) + bytes(16) + bytes(2))
        result = route.inspect(raw, route.sha(raw))
        self.assertEqual(result['debug_tag_counts']['DebugID'], 1)
        self.assertEqual(result['debug_tags'][0]['offset'], 14)

    def test_malformed_movies_rejected(self):
        for raw in (movie(b''), movie(b'\xff'), movie(struct.pack('<H', (64 << 6) | 63)),
                    movie(struct.pack('<H', (39 << 6) | 2) + bytes(2)),
                    movie(bytes(4))):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                route.inspect(raw, route.sha(raw))

    def test_reextraction_and_unknown_live_identity(self):
        result = route.probe()
        self.assertEqual(result, json.loads((HERE / 'debug-route.json').read_text()))
        for key in ('loaded_definition_pair', 'same_input_activation_pair', 'defining_scope_pair'):
            self.assertIsNone(result[key])

    def test_fabricated_route_rejected(self):
        record = route.probe()
        record['defining_scope_pair'] = ['original', 'candidate']
        with patch.object(route, 'probe', return_value=record):
            with self.assertRaisesRegex(ValueError, 'Independent debug route'):
                d.diagnose()


if __name__ == '__main__':
    unittest.main()
